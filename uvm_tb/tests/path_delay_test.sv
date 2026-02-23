/**
 * path_delay_test
 *
 * Critical–path timing (path delay) DFT test.
 */

class path_delay_test extends dft_base_test;

    `uvm_component_utils(path_delay_test)

    function new(string name = "path_delay_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void configure_test();
        super.configure_test();
        cfg.test_mode = DFT_MODE_PATH_DELAY;
    endfunction

    virtual task run_test_sequence();
        `uvm_info("PATH_DELAY", "Running path–delay DFT test", UVM_MEDIUM)
        env.run_scan_test("path_delay");
    endtask

endclass

