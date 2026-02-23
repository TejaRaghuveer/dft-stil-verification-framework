/**
 * DFT Test Configuration Class
 *
 * Extends the generic test_config with DFT–specific parameters:
 * - Per–agent configuration (JTAG, clock, reset, pad)
 * - DUT scan/DFT parameters
 * - Test mode selection
 * - Pattern file configuration
 * - Logging and coverage controls
 */

typedef enum {
    DFT_MODE_STUCK_AT,
    DFT_MODE_TRANSITION_DELAY,
    DFT_MODE_PATH_DELAY,
    DFT_MODE_BOUNDARY_SCAN
} dft_test_mode_e;

class dft_test_config extends test_config;

    `uvm_object_utils(dft_test_config)

    // ============================================
    // DUT / DFT Structure
    // ============================================

    int num_scan_chains        = 4;
    int scan_chain_lengths[];          // [num_scan_chains]

    int num_clock_domains      = 1;
    string clock_domain_names[];       // Optional labels for domains

    int num_primary_inputs     = 32;
    int num_primary_outputs    = 32;

    // ============================================
    // Test Modes / Pattern Types
    // ============================================

    dft_test_mode_e test_mode  = DFT_MODE_STUCK_AT;

    // Pattern file configuration
    string pattern_root_dir    = "patterns";
    string stuck_at_pattern_file       = "stuck_at.stil";
    string transition_delay_pattern_file = "transition_delay.stil";
    string path_delay_pattern_file     = "path_delay.stil";
    string boundary_scan_pattern_file  = "boundary_scan.stil";

    // ============================================
    // Logging / Coverage / Scoreboard
    // ============================================

    bit enable_scoreboard      = 1;
    bit enable_functional_coverage = 1;
    bit enable_protocol_assertions  = 1;

    // Detail level for DFT–specific logs
    int dft_log_verbosity      = UVM_MEDIUM;

    // ============================================
    // Constructor
    // ============================================

    function new(string name = "dft_test_config");
        super.new(name);

        // Reasonable defaults for 32/64–bit designs:
        //  - 4 scan chains of 256 bits each
        scan_chain_lengths = new[num_scan_chains];
        foreach (scan_chain_lengths[i]) begin
            scan_chain_lengths[i] = 256;
        end

        clock_domain_names = new[num_clock_domains];
        if (num_clock_domains > 0)
            clock_domain_names[0] = "core_clk";
    endfunction

    // Pretty–printer
    virtual function string convert2string();
        string s;
        s = super.convert2string();
        s = {s, $sformatf("DFT config:\n")};
        s = {s, $sformatf("  Test mode              : %s\n", test_mode.name())};
        s = {s, $sformatf("  Scan chains            : %0d\n", num_scan_chains)};
        foreach (scan_chain_lengths[i])
            s = {s, $sformatf("    chain[%0d] length    : %0d\n", i, scan_chain_lengths[i])};
        s = {s, $sformatf("  Clock domains          : %0d\n", num_clock_domains)};
        foreach (clock_domain_names[i])
            s = {s, $sformatf("    domain[%0d]          : %s\n", i, clock_domain_names[i])};
        s = {s, $sformatf("  PIs / POs              : %0d / %0d\n",
                           num_primary_inputs, num_primary_outputs)};
        s = {s, $sformatf("  Patterns root          : %s\n", pattern_root_dir)};
        s = {s, $sformatf("  Scoreboard / coverage  : %0d / %0d\n",
                           enable_scoreboard, enable_functional_coverage)};
        return s;
    endfunction

endclass

