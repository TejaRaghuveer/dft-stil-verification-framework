/**
 * scan_shift_test
 *
 * Basic scan–shift–only test (no functional capture).
 */

class scan_shift_test extends dft_base_test;

    `uvm_component_utils(scan_shift_test)

    function new(string name = "scan_shift_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void configure_test();
        super.configure_test();
        cfg.test_mode = DFT_MODE_STUCK_AT;
    endfunction

    virtual task run_test_sequence();
        `uvm_info("SCAN_SHIFT", "Running basic scan–shift test", UVM_MEDIUM)
        env.run_scan_test("scan_shift");
    endtask

endclass

