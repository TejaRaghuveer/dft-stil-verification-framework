/**
 * transition_delay_test
 *
 * At–speed transition delay DFT test.
 */

class transition_delay_test extends dft_base_test;

    `uvm_component_utils(transition_delay_test)

    function new(string name = "transition_delay_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void configure_test();
        super.configure_test();
        cfg.test_mode = DFT_MODE_TRANSITION_DELAY;
    endfunction

    virtual task run_test_sequence();
        `uvm_info("TRANS_DELAY", "Running transition–delay DFT test", UVM_MEDIUM)
        env.run_scan_test("transition_delay");
    endtask

endclass

