/**
 * DFT Base Test
 *
 * Base class for all DFT–oriented tests. Uses dft_env and dft_test_config
 * and provides common hooks and utilities.
 */

class dft_base_test extends uvm_test;

    `uvm_component_utils(dft_base_test)

    dft_env        env;
    dft_test_config cfg;

    function new(string name = "dft_base_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    // ------------------------------------------------------------
    // Build
    // ------------------------------------------------------------
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        // Create configuration and allow derived tests to customize
        cfg = dft_test_config::type_id::create("cfg");
        configure_test();

        // Publish config for environment and agents
        uvm_config_db#(dft_test_config)::set(this, "*", "cfg", cfg);

        // Create environment
        env = dft_env::type_id::create("env", this);
    endfunction

    // Default configuration – override in derived tests as needed
    virtual function void configure_test();
        cfg.verbosity               = UVM_MEDIUM;
        cfg.enable_waveform_dump    = 1;
        cfg.test_mode               = DFT_MODE_STUCK_AT;
    endfunction

    // ------------------------------------------------------------
    // Run
    // ------------------------------------------------------------
    virtual task run_phase(uvm_phase phase);
        phase.raise_objection(this);

        `uvm_info("DFT_TEST", "Starting DFT base test", UVM_MEDIUM)

        // Common startup: start clocks and reset
        env.start_clocks_and_reset();

        // Call test–specific body
        run_test_sequence();

        #1000ns;
        phase.drop_objection(this);
    endtask

    // To be overridden by specific DFT tests
    virtual task run_test_sequence();
        `uvm_info("DFT_TEST", "Default DFT base test sequence – override in derived tests",
                  UVM_MEDIUM)
    endtask

endclass

