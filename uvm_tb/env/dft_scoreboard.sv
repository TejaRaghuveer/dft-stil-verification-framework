/**
 * DFT Scoreboard
 *
 * Comprehensive scoreboard for DFT–oriented tests. It consumes transactions
 * from the enhanced JTAG driver (which contain both expected and actual TDO)
 * and primary–I/O activity from the pad agent, and produces:
 *
 * - Real–time mismatch logging with full context
 * - Post–test statistics and coverage–style summaries
 * - Per–pattern integration via atpg_pattern_exec_logger
 *
 * Match criteria and timing considerations
 * ----------------------------------------
 * JTAG scan:
 *   - The driver captures TDO at every TCK falling edge into txn.actual_tdo[]
 *     and, when expected_tdo[] is provided, calls compare_tdo() to populate
 *     txn.tdo_match and txn.tdo_mismatch_count.
 *   - The scoreboard treats the driver as the reference implementation for
 *     low–level timing; it does not re–simulate TAP timing. Instead, it
 *     aggregates and cross–checks the driver's results, computing:
 *       * total bits compared
 *       * total mismatches
 *       * bit–match percentage
 *   - Because the same transaction carries expected and actual data, the
 *     “predicted” and “observed” streams are available without duplicating
 *     the TAP timing model.
 *
 * Primary outputs:
 *   - pad_monitor_enhanced publishes captured pad_xtn items via ap_captured.
 *   - response_collector gathers expected pad_xtn items (from sequences) and
 *     performs tolerant numeric comparisons, with an optional mask.
 *   - The scoreboard subscribes to both the expected and actual pad_xtn
 *     streams and mirrors the comparison with richer reporting focused on
 *     DFT diagnostics (which patterns / signals are problematic).
 *
 * Debugging strategies
 * --------------------
 * - For hard failures (completely wrong data), focus on the first mismatch
 *   reported per transaction/pattern – this often pinpoints the first broken
 *   shift or capture cycle.
 * - For timing issues, compare the timestamps of expected vs actual pad
 *   events and the duration of JTAG transactions; large skew usually hints
 *   at clocking or reset problems.
 * - For near–misses (e.g., 95–98% bit–match), look for systematic bit
 *   offsets (one–bit slip) or consistent errors on specific chains or pads.
 */

`uvm_analysis_imp_decl(_jtag)
`uvm_analysis_imp_decl(_pad_exp)
`uvm_analysis_imp_decl(_pad_act)

class dft_scoreboard extends uvm_scoreboard;

    `uvm_component_utils(dft_scoreboard)

    // Configuration
    dft_test_config        cfg;
    atpg_seq_config        atpg_cfg;
    atpg_pattern_exec_logger pattern_logger;

    // Analysis imps:
    //  - JTAG transactions from driver (expected + actual)
    //  - Expected primary–I/O responses
    //  - Actual primary–I/O responses
    uvm_analysis_imp_jtag#(jtag_xtn,   dft_scoreboard) jtag_txn_imp;
    uvm_analysis_imp_pad_exp#(pad_xtn, dft_scoreboard) pad_expected_imp;
    uvm_analysis_imp_pad_act#(pad_xtn, dft_scoreboard) pad_actual_imp;

    // ------------------------------
    // JTAG scan statistics
    // ------------------------------
    int   jtag_total_txn;
    int   jtag_failed_txn;
    longint jtag_total_bits;
    longint jtag_mismatched_bits;

    // ------------------------------
    // Primary–I/O statistics
    // ------------------------------
    typedef struct {
        time   t_exp;
        time   t_act;
        logic [63:0] exp;
        logic [63:0] act;
        logic [63:0] mask;
        bit    matched;
    } pad_compare_event_t;

    pad_xtn pad_expected_q[$];
    pad_xtn pad_actual_q[$];
    pad_compare_event_t pad_events[$];

    int pad_match_count;
    int pad_mismatch_count;

    // Coverage–style counters
    int total_patterns;
    int passed_patterns;
    int failed_patterns;
    int error_patterns;

    // Report configuration
    bit enable_detailed_fail_log = 1;
    string report_file_path = "";
    int report_fd;

    function new(string name = "dft_scoreboard", uvm_component parent = null);
        super.new(name, parent);
        jtag_txn_imp    = new("jtag_txn_imp", this);
        pad_expected_imp = new("pad_expected_imp", this);
        pad_actual_imp   = new("pad_actual_imp", this);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        void'(uvm_config_db#(dft_test_config)::get(this, "", "cfg", cfg));
        void'(uvm_config_db#(atpg_seq_config)::get(this, "", "atpg_seq_cfg", atpg_cfg));
        void'(uvm_config_db#(atpg_pattern_exec_logger)::get(this, "*", "atpg_logger", pattern_logger));

        if (atpg_cfg != null) begin
            enable_detailed_fail_log = (atpg_cfg.result_check != ATPG_CHECK_END_OF_TEST);
            report_file_path = atpg_cfg.log_file_path;
        end
    endfunction

    // ============================================================
    // JTAG transaction handling (matching_engine for scan)
    // ============================================================

    /**
     * JTAG write–side of the scoreboard.
     *
     * This is fed by jtag_driver_enhanced.ap_txn *after* the driver has:
     *   - Driven the TAP state machine and TDI
     *   - Captured TDO into actual_tdo[]
     *   - Optionally populated expected_tdo[] and tdo_mismatch_count
     *
     * The scoreboard:
     *   - Accumulates bit–level statistics
     *   - Logs mismatches with transaction context
     *   - Contributes to pattern–level coverage via pattern_logger
     */
    function void write_jtag(jtag_xtn txn);
        int n_bits;
        int mismatches;

        jtag_total_txn++;

        // If no expected data, treat as informational only.
        if (txn.expected_tdo.size() == 0 || txn.actual_tdo.size() == 0) begin
            return;
        end

        n_bits = (txn.expected_tdo.size() <= txn.actual_tdo.size())
                   ? txn.expected_tdo.size() : txn.actual_tdo.size();

        // Recompute bit-level mismatches here so we are independent of when
        // compare_tdo() is called elsewhere.
        mismatches = 0;
        for (int i = 0; i < n_bits; i++) begin
            if (txn.expected_tdo[i] !== txn.actual_tdo[i])
                mismatches++;
        end

        jtag_total_bits += n_bits;
        jtag_mismatched_bits += mismatches;

        if (mismatches > 0) begin
            jtag_failed_txn++;
            if (enable_detailed_fail_log) begin
                `uvm_error("DFT_SCB",
                           $sformatf("JTAG TDO mismatch: type=%s mismatches=%0d\nExpected: %s\nActual  : %s",
                                     txn.sequence_type.name(),
                                     mismatches,
                                     tdo_bits_to_string(txn.expected_tdo),
                                     tdo_bits_to_string(txn.actual_tdo)))
            end
        end
    endfunction

    // Helper: convert bit[] to printable string (LSB->MSB)
    function string tdo_bits_to_string(bit bits[]);
        string s = "";
        for (int i = 0; i < bits.size(); i++)
            s = { (bits[i] ? "1" : "0"), s };
        return s;
    endfunction

    // ============================================================
    // Pad expected / actual handling
    // ============================================================

    /**
     * Expected primary–I/O values.
     *
     * These usually originate from ATPG pattern–driven sequences pushing
     * pad_xtn with expected_response/mask through response_collector.
     */
    function void write_pad_exp(pad_xtn t);
        pad_expected_q.push_back(t);
    endfunction

    /**
     * Actual primary–I/O values captured by pad_monitor_enhanced.
     */
    function void write_pad_act(pad_xtn t);
        pad_actual_q.push_back(t);
        compare_next_pad();
    endfunction

    // Compare the next expected vs actual pad_xtn pair and record a
    // comparison event (used for detailed failure reporting).
    function void compare_next_pad();
        if (pad_expected_q.size() == 0 || pad_actual_q.size() == 0)
            return;

        pad_xtn exp_t = pad_expected_q[0];
        pad_expected_q.pop_front();
        pad_xtn act_t = pad_actual_q[0];
        pad_actual_q.pop_front();

        pad_compare_event_t ev;
        ev.t_exp = exp_t.transaction_time;
        ev.t_act = act_t.transaction_time;
        ev.exp   = exp_t.expected_response;
        ev.act   = act_t.data_value;
        ev.mask  = exp_t.compare_mask;

        logic [63:0] exp_masked = ev.exp & ev.mask;
        logic [63:0] act_masked = ev.act & ev.mask;

        if (act_masked === exp_masked) begin
            ev.matched = 1;
            pad_match_count++;
        end else begin
            ev.matched = 0;
            pad_mismatch_count++;
            if (enable_detailed_fail_log) begin
                `uvm_error("DFT_SCB_PAD",
                           $sformatf("Pad mismatch: exp=0x%x act=0x%x mask=0x%x",
                                     exp_masked, act_masked, ev.mask))
            end
        end

        pad_events.push_back(ev);
    endfunction

    // ============================================================
    // Coverage & reporting
    // ============================================================

    function void end_of_elaboration_phase(uvm_phase phase);
        super.end_of_elaboration_phase(phase);
        if (pattern_logger != null) begin
            pattern_logger.get_coverage_stats(passed_patterns,
                                              failed_patterns,
                                              error_patterns);
            total_patterns = passed_patterns + failed_patterns + error_patterns;
        end
        if (report_file_path != "") begin
            report_fd = $fopen(report_file_path, "a");
        end
    endfunction

    function void report_phase(uvm_phase phase);
        super.report_phase(phase);

        real jtag_match_pct = (jtag_total_bits > 0)
                                ? 100.0 * real'(jtag_total_bits - jtag_mismatched_bits)
                                          / real'(jtag_total_bits)
                                : 0.0;

        `uvm_info("DFT_SCB_SUMMARY",
                  $sformatf("DFT Scoreboard Summary:\n  JTAG: txn=%0d failed=%0d bits=%0d mismatched=%0d (match=%.2f%%)\n  PAD : expected=%0d actual=%0d match=%0d mismatch=%0d\n  Patterns: total=%0d pass=%0d fail=%0d error=%0d",
                            jtag_total_txn, jtag_failed_txn,
                            jtag_total_bits, jtag_mismatched_bits, jtag_match_pct,
                            pad_expected_q.size() + pad_match_count + pad_mismatch_count,
                            pad_actual_q.size() + pad_match_count + pad_mismatch_count,
                            pad_match_count, pad_mismatch_count,
                            total_patterns, passed_patterns, failed_patterns, error_patterns),
                  UVM_LOW)

        if (report_fd != 0) begin
            $fwrite(report_fd,
                    "DFT_SCOREBOARD_SUMMARY,JTAG_TXN=%0d,FAILED=%0d,BITS=%0d,MISMATCH=%0d,MATCH_PCT=%.2f,PAD_MATCH=%0d,PAD_MISMATCH=%0d,PATTERNS=%0d,PASS=%0d,FAIL=%0d,ERROR=%0d\n",
                    jtag_total_txn, jtag_failed_txn,
                    jtag_total_bits, jtag_mismatched_bits, jtag_match_pct,
                    pad_match_count, pad_mismatch_count,
                    total_patterns, passed_patterns, failed_patterns, error_patterns);
            $fclose(report_fd);
        end
    endfunction

endclass

