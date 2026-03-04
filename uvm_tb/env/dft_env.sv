/**
 * DFT Environment
 *
 * Integrates all DFT–relevant agents (JTAG, Clock, Reset, Pad)
 * into a single configurable UVM environment.
 *
 * Responsibilities:
 *  - Instantiate and configure agents
 *  - Provide high–level DFT APIs:
 *       run_scan_test(), run_functional_test()
 *  - Coordinate JTAG / clock / reset / pad timing at test level
 *  - Optional scoreboard hook–up
 */

class dft_env extends uvm_env;

    `uvm_component_utils(dft_env)

    // Configuration
    dft_test_config cfg;

    // Agents (enhanced where available)
    jtag_agent_enhanced   jtag_ag;
    clock_agent           clock_ag;
    reset_agent           reset_ag;
    pad_agent_enhanced    pad_ag;

    // Optional scoreboard (simple placeholder)
    uvm_component         scoreboard;

    function new(string name = "dft_env", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    // ------------------------------------------------------------
    // Build
    // ------------------------------------------------------------
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        // Get or create configuration
        if (!uvm_config_db#(dft_test_config)::get(this, "", "cfg", cfg)) begin
            if (!uvm_config_db#(dft_test_config)::get(null, "", "cfg", cfg)) begin
                `uvm_warning("NO_DFT_CFG",
                             "dft_env: no dft_test_config in config_db, creating default")
                cfg = dft_test_config::type_id::create("cfg");
            end
        end

        // Make cfg also visible as test_config for existing components
        uvm_config_db#(test_config)::set(this, "*", "cfg", cfg);

        // Instantiate agents
        jtag_ag  = jtag_agent_enhanced::type_id::create("jtag_ag",  this);
        clock_ag = clock_agent::type_id::create("clock_ag", this);
        reset_ag = reset_agent::type_id::create("reset_ag", this);
        pad_ag   = pad_agent_enhanced::type_id::create("pad_ag",   this);

        // Optional DFT scoreboard
        if (cfg.enable_scoreboard) begin
            scoreboard = dft_scoreboard::type_id::create("dft_scoreboard", this);
        end
    endfunction

    // ------------------------------------------------------------
    // Connect
    // ------------------------------------------------------------
    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);

        // Hook up analysis paths when the DFT scoreboard is enabled.
        if (scoreboard != null) begin
            dft_scoreboard scb;
            if ($cast(scb, scoreboard)) begin
                // JTAG: completed transactions from driver (expected + actual)
                if (jtag_ag != null && jtag_ag.driver != null) begin
                    jtag_ag.driver.ap_txn.connect(scb.jtag_txn_imp);
                end

                // PAD: expected vs actual primary–I/O values
                if (pad_ag != null) begin
                    if (pad_ag.monitor != null)
                        pad_ag.monitor.ap_captured.connect(scb.pad_actual_imp);
                    if (pad_ag.resp_collector != null)
                        pad_ag.resp_collector.expected_export.connect(scb.pad_expected_imp);
                end
            end
        end
    endfunction

    // ------------------------------------------------------------
    // High–level DFT APIs
    // ------------------------------------------------------------

    // Basic scan test hook – override / extend in tests
    virtual task run_scan_test(string name = "scan_test");
        `uvm_info("DFT_ENV", $sformatf("run_scan_test(%s) – override with concrete pattern "
                                       "sequences (JTAG + PAD)", name),
                  cfg.dft_log_verbosity)
    endtask

    // Functional test placeholder – for non–scan tests
    virtual task run_functional_test(string name = "functional_test");
        `uvm_info("DFT_ENV", $sformatf("run_functional_test(%s) – user–defined sequences",
                                       name),
                  cfg.dft_log_verbosity)
    endtask

    // Utility: coordinated reset + clock start
    virtual task start_clocks_and_reset();
        `uvm_info("DFT_ENV", "Starting clocks and applying reset", cfg.dft_log_verbosity)
        // Clock agent starts clock in its driver run_phase automatically.
        // Reset agent driver should assert/deassert according to cfg.
        // Nothing to do here except waiting for reset to complete in tests, if desired.
    endtask

endclass

