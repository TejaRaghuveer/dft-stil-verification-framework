/**
 * full_regression_test
 *
 * Top–level regression that can sweep multiple DFT modes/pattern sets.
 * For now this simply calls env.run_scan_test() once per configured mode;
 * users can extend it to iterate over external pattern lists.
 */

class full_regression_test extends dft_base_test;

    `uvm_component_utils(full_regression_test)

    function new(string name = "full_regression_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void configure_test();
        super.configure_test();
        // Default to stuck–at; individual runs can override via plusargs or
        // factory overrides if needed.
        cfg.test_mode = DFT_MODE_STUCK_AT;
    endfunction

    virtual task run_test_sequence();
        `uvm_info("DFT_REG", "Starting full DFT regression (mode–based stub)", UVM_MEDIUM)

        // Example: run once for the configured mode
        case (cfg.test_mode)
            DFT_MODE_STUCK_AT:          env.run_scan_test("reg_stuck_at");
            DFT_MODE_TRANSITION_DELAY:  env.run_scan_test("reg_transition_delay");
            DFT_MODE_PATH_DELAY:        env.run_scan_test("reg_path_delay");
            DFT_MODE_BOUNDARY_SCAN:     env.run_scan_test("reg_boundary_scan");
            default: begin
                `uvm_warning("DFT_REG", "Unknown test_mode – running generic scan test")
                env.run_scan_test("reg_generic");
            end
        endcase
    endtask

endclass

