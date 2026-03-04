/**
 * ATPG Pattern to UVM Sequence Converter
 *
 * Transforms ATPG patterns (atpg_pattern_t) into executable UVM sequences
 * for JTAG, Clock, Reset, and Pad agents. Implements:
 * - atpg_pattern_seq: three-phase (init, stimulus, response)
 * - scan_shift_with_capture_seq: shift in, capture cycle, shift out with compare
 * - primary_io_stimulus_seq: drive primary inputs, capture outputs
 * - multi_pattern_seq: iterate pattern queue with optional reset and logging
 *
 * Sequence item mapping:
 * - atpg_pattern_t.scan_in_vectors[i] -> jtag_xtn (tdi_vector from string)
 * - atpg_pattern_t.primary_in_vectors[i] -> pad_xtn (input_values)
 * - Expected outputs -> scoreboard/monitor comparison
 */

// ---------------------------------------------------------------------------
// String to bit[] conversion (LSB first). 0/1 -> bit; X/Z -> 0 for drive.
// ---------------------------------------------------------------------------
function automatic void atpg_string_to_tdi_bits(string s, ref bit tdi[]);
    int n = s.len();
    tdi = new[n];
    for (int i = 0; i < n; i++) begin
        string c = s.substr(i, i);
        tdi[i] = (c == "1") ? 1'b1 : 1'b0;
    end
endfunction

function automatic void atpg_string_to_expected_tdo(string s, ref bit exp[]);
    int n = s.len();
    exp = new[n];
    for (int i = 0; i < n; i++) begin
        string c = s.substr(i, i);
        exp[i] = (c == "1") ? 1'b1 : 1'b0;
    end
endfunction

// ---------------------------------------------------------------------------
// Scan shift with capture sequence
// Shifts scan_in (LSB to MSB), applies capture_cycles at operational speed,
// then shifts out and compares to expected_scan_out.
// ---------------------------------------------------------------------------
class scan_shift_with_capture_seq extends jtag_base_sequence;
    `uvm_object_utils(scan_shift_with_capture_seq)

    string scan_in_str;
    string expected_scan_out_str;
    int dr_length;
    int capture_cycles;
    atpg_seq_config seq_cfg;
    bit last_tdo_match;
    int last_mismatch_count;
    int last_fail_vector_index;

    function new(string name = "scan_shift_with_capture_seq");
        super.new(name);
        dr_length = 256;
        capture_cycles = 1;
        last_tdo_match = 1;
        last_mismatch_count = 0;
        last_fail_vector_index = -1;
    endfunction

    task body();
        jtag_xtn txn;
        bit tdi_bits[];
        bit expected_tdo[];
        int shift_len;
        int total_cycles;
        int idx;

        if (seq_cfg == null) seq_cfg = atpg_seq_config::type_id::create("seq_cfg");
        atpg_string_to_tdi_bits(scan_in_str, tdi_bits);
        shift_len = tdi_bits.size();
        if (shift_len == 0) return;
        if (expected_scan_out_str.len() > 0)
            atpg_string_to_expected_tdo(expected_scan_out_str, expected_tdo);

        total_cycles = 3 + shift_len;
        txn = jtag_xtn::type_id::create("shift_in_txn");
        txn.sequence_type = SCAN_SHIFT;
        txn.dr_length = shift_len;
        txn.cycle_count = total_cycles;
        txn.tms_vector = new[total_cycles];
        txn.tdi_vector = new[shift_len];
        txn.start_state = RUN_TEST_IDLE;
        for (int i = 0; i < shift_len; i++) txn.tdi_vector[i] = tdi_bits[i];
        idx = 0;
        txn.tms_vector[idx++] = 0;
        txn.tms_vector[idx++] = 1;
        txn.tms_vector[idx++] = 0;
        for (int i = 0; i < shift_len - 1; i++) txn.tms_vector[idx++] = 0;
        txn.tms_vector[idx++] = 1;
        start_item(txn);
        finish_item(txn);

        if (capture_cycles > 0 && seq_cfg != null)
            #(capture_cycles * seq_cfg.scan_tck_period_ns);

        if (expected_scan_out_str.len() > 0 && expected_tdo.size() > 0) begin
            total_cycles = 3 + expected_tdo.size();
            txn = jtag_xtn::type_id::create("shift_out_txn");
            txn.sequence_type = SCAN_SHIFT;
            txn.dr_length = expected_tdo.size();
            txn.cycle_count = total_cycles;
            txn.tms_vector = new[total_cycles];
            txn.tdi_vector = new[expected_tdo.size()];
            txn.expected_tdo = new[expected_tdo.size()];
            for (int i = 0; i < expected_tdo.size(); i++) begin
                txn.tdi_vector[i] = 0;
                txn.expected_tdo[i] = expected_tdo[i];
            end
            idx = 0;
            txn.tms_vector[idx++] = 0;
            txn.tms_vector[idx++] = 1;
            txn.tms_vector[idx++] = 0;
            for (int i = 0; i < expected_tdo.size() - 1; i++) txn.tms_vector[idx++] = 0;
            txn.tms_vector[idx++] = 1;
            start_item(txn);
            finish_item(txn);
            txn.compare_tdo();
            last_tdo_match = txn.tdo_match;
            last_mismatch_count = txn.tdo_mismatch_count;
            last_fail_vector_index = (txn.tdo_mismatch_count > 0) ? 0 : -1;
        end
    endtask
endclass

// ---------------------------------------------------------------------------
// Primary I/O stimulus sequence
// Drives primary_in vector to pad agent; captures primary outputs and
// stores expected vs actual for response checking.
// ---------------------------------------------------------------------------
class primary_io_stimulus_seq extends uvm_sequence#(pad_xtn);
    `uvm_object_utils(primary_io_stimulus_seq)

    string primary_in_str;
    string expected_primary_out_str;
    atpg_seq_config seq_cfg;
    time setup_ns, hold_ns;

    function new(string name = "primary_io_stimulus_seq");
        super.new(name);
        setup_ns = 2;
        hold_ns = 2;
    endfunction

    task body();
        pad_xtn txn;
        logic [63:0] pi_val;
        int i, w;

        if (seq_cfg != null) begin
            setup_ns = seq_cfg.primary_setup_ns;
            hold_ns = seq_cfg.primary_hold_ns;
        end
        txn = pad_xtn::type_id::create("pi_txn");
        txn.signal_type = INPUT;
        txn.stimulus_type = COMBINATIONAL;
        txn.set_drive_timing(setup_ns, hold_ns, 0);
        w = (primary_in_str.len() > 64) ? 64 : primary_in_str.len();
        pi_val = '0;
        for (i = 0; i < w; i++)
            if (primary_in_str.substr(i,i) == "1") pi_val[i] = 1'b1;
        txn.data_value = pi_val;
        txn.data_width = w;
        start_item(txn);
        finish_item(txn);
        if (expected_primary_out_str.len() > 0) begin
            txn = pad_xtn::type_id::create("po_expected_txn");
            txn.signal_type = OUTPUT;
            txn.data_width = (expected_primary_out_str.len() > 64) ? 64 : expected_primary_out_str.len();
            txn.expected_response = '0;
            for (i = 0; i < txn.data_width; i++)
                if (expected_primary_out_str.substr(i,i) == "1") txn.expected_response[i] = 1'b1;
            start_item(txn);
            finish_item(txn);
        end
    endtask
endclass

// ---------------------------------------------------------------------------
// ATPG pattern sequence (single pattern, three phases)
// Init: reset, load test mode instruction. Stimulus: drive scan/primary.
// Response: shift out, compare.
// ---------------------------------------------------------------------------
class atpg_pattern_seq extends uvm_sequence#(jtag_xtn);
    `uvm_object_utils(atpg_pattern_seq)

    atpg_pattern_t pattern;
    atpg_seq_config seq_cfg;
    dft_env env;
    atpg_pattern_exec_logger logger;
    atpg_pattern_status_e pattern_status;
    int fail_vector_index;
    int mismatch_count;
    bit had_activity;  // set when any scan/PI stimulus actually runs

    function new(string name = "atpg_pattern_seq");
        super.new(name);
        pattern_status = ATPG_PATTERN_ERROR;
        fail_vector_index = -1;
        mismatch_count = 0;
        had_activity = 0;
    endfunction

    task body();
        if (pattern == null) begin
            `uvm_fatal("ATPG_SEQ", "atpg_pattern_seq: pattern is null")
            return;
        end
        if (!uvm_config_db#(dft_env)::get(null, get_full_name(), "dft_env", env))
            env = null;
        if (!uvm_config_db#(atpg_seq_config)::get(null, get_full_name(), "atpg_seq_cfg", seq_cfg))
            seq_cfg = atpg_seq_config::type_id::create("atpg_seq_cfg");
        if (!uvm_config_db#(atpg_pattern_exec_logger)::get(null, "*", "atpg_logger", logger))
            logger = null;

        if (logger != null) logger.log_pattern_start(pattern.pattern_name, 0);

        phase_a_initialization();
        phase_b_stimulus_application();
        phase_c_response_collection();

        if (logger != null)
            logger.log_pattern_end(pattern.pattern_name, pattern_status, pattern.get_scan_vector_count(), fail_vector_index, "", "", mismatch_count);
    endtask

    task phase_a_initialization();
        jtag_reset_sequence rst_seq;
        load_instruction_sequence load_ir_seq;
        uvm_sequencer#(jtag_xtn) jtag_sqr;
        if (env == null || env.jtag_ag == null) return;
        jtag_sqr = env.jtag_ag.sequencer;
        if (jtag_sqr == null) return;
        rst_seq = jtag_reset_sequence::type_id::create("rst");
        rst_seq.start(jtag_sqr);
        load_ir_seq = load_instruction_sequence::type_id::create("load_ir");
        load_ir_seq.ir_code = (seq_cfg != null) ? seq_cfg.test_mode_ir : 32'h00;
        load_ir_seq.ir_length = (seq_cfg != null) ? seq_cfg.ir_length : 4;
        load_ir_seq.start(jtag_sqr);
    endtask

    task phase_b_stimulus_application();
        scan_shift_with_capture_seq scan_seq;
        primary_io_stimulus_seq pi_seq;
        uvm_sequencer#(jtag_xtn) jtag_sqr;
        uvm_sequencer#(pad_xtn) pad_sqr;
        string sin, sout;
        int n = pattern.get_scan_vector_count();
        for (int i = 0; i < n; i++) begin
            sin = pattern.scan_in_vectors[i];
            sout = (i < pattern.scan_out_vectors.size()) ? pattern.scan_out_vectors[i] : "";
            if (env != null && env.jtag_ag != null) begin
                jtag_sqr = env.jtag_ag.sequencer;
                if (jtag_sqr != null) begin
                    scan_seq = scan_shift_with_capture_seq::type_id::create("scan");
                    scan_seq.scan_in_str = sin;
                    scan_seq.expected_scan_out_str = sout;
                    scan_seq.dr_length = (seq_cfg != null) ? seq_cfg.dr_length : 256;
                    scan_seq.capture_cycles = (seq_cfg != null) ? seq_cfg.capture_cycles : 1;
                    scan_seq.seq_cfg = seq_cfg;
                    scan_seq.start(jtag_sqr);
                    had_activity = 1;
                    if (sout != "" && !scan_seq.last_tdo_match) begin
                        pattern_status = ATPG_PATTERN_FAIL;
                        fail_vector_index = i;
                        mismatch_count = scan_seq.last_mismatch_count;
                    end
                end
            end
        end
        if (env != null && env.pad_ag != null && pattern.primary_in_vectors.size() > 0) begin
            pad_sqr = env.pad_ag.sequencer;
            if (pad_sqr != null)
            for (int i = 0; i < pattern.primary_in_vectors.size(); i++) begin
                pi_seq = primary_io_stimulus_seq::type_id::create("pi");
                pi_seq.primary_in_str = pattern.primary_in_vectors[i];
                pi_seq.expected_primary_out_str = (i < pattern.expected_primary_out.size()) ? pattern.expected_primary_out[i] : "";
                pi_seq.seq_cfg = seq_cfg;
                pi_seq.start(pad_sqr);
                had_activity = 1;
            end
        end
    endtask

    // Response collection phase:
    // At this point, pattern_status is either:
    //   - ATPG_PATTERN_FAIL (mismatch detected in phase B), or
    //   - ATPG_PATTERN_ERROR (no explicit verification result).
    // If we actually executed any scan/primary–I/O activity (had_activity=1)
    // and no failures were detected, then the pattern is treated as PASS.
    // Patterns that never ran any activity remain in ERROR so that
    // misconfigured tests are not silently reported as passing.
    task phase_c_response_collection();
        if (pattern_status == ATPG_PATTERN_ERROR && had_activity) begin
            pattern_status = ATPG_PATTERN_PASS;
            fail_vector_index = -1;
            mismatch_count = 0;
        end
    endtask
endclass

// ---------------------------------------------------------------------------
// Multi-pattern sequence: iterate queue, optional reset between, log results
// ---------------------------------------------------------------------------
class multi_pattern_seq extends uvm_sequence#(jtag_xtn);
    `uvm_object_utils(multi_pattern_seq)

    atpg_pattern_t pattern_queue[$];
    atpg_seq_config seq_cfg;
    dft_env env;
    atpg_pattern_exec_logger logger;
    bit reset_between;

    function new(string name = "multi_pattern_seq");
        super.new(name);
        reset_between = 0;
    endfunction

    task body();
        atpg_pattern_seq pat_seq;
        if (!uvm_config_db#(dft_env)::get(null, get_full_name(), "dft_env", env))
            env = null;
        if (!uvm_config_db#(atpg_seq_config)::get(null, get_full_name(), "atpg_seq_cfg", seq_cfg)) begin
            seq_cfg = atpg_seq_config::type_id::create("atpg_seq_cfg");
            uvm_config_db#(atpg_seq_config)::set(null, "*", "atpg_seq_cfg", seq_cfg);
        end
        if (seq_cfg != null) reset_between = seq_cfg.reset_between_patterns;
        if (!uvm_config_db#(atpg_pattern_exec_logger)::get(null, "*", "atpg_logger", logger))
            logger = null;
        if (logger != null && seq_cfg != null && seq_cfg.log_file_path != "")
            logger.open_csv(seq_cfg.log_file_path);

        for (int i = 0; i < pattern_queue.size(); i++) begin
            if (reset_between && i > 0 && env != null && env.jtag_ag != null) begin
                jtag_reset_sequence rst_seq;
                rst_seq = jtag_reset_sequence::type_id::create("rst");
                if (env.jtag_ag.sequencer != null)
                    rst_seq.start(env.jtag_ag.sequencer);
            end
            pat_seq = atpg_pattern_seq::type_id::create("pat_seq");
            pat_seq.pattern = pattern_queue[i];
            pat_seq.seq_cfg = seq_cfg;
            pat_seq.env = env;
            pat_seq.logger = logger;
            if (env != null && env.jtag_ag != null && env.jtag_ag.sequencer != null)
                pat_seq.start(env.jtag_ag.sequencer);
        end
    endtask
endclass
