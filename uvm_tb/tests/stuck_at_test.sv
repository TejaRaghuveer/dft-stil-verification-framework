/**
 * stuck_at_test
 *
 * Stuck–at fault–oriented DFT test.
 */

class stuck_at_test extends dft_base_test;

    `uvm_component_utils(stuck_at_test)

    function new(string name = "stuck_at_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void configure_test();
        super.configure_test();
        cfg.test_mode = DFT_MODE_STUCK_AT;
    endfunction

    virtual task run_test_sequence();
        `uvm_info("STUCK_AT", "Running stuck–at DFT test", UVM_MEDIUM)
        env.run_scan_test("stuck_at");
    endtask

endclass

