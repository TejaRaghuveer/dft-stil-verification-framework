/**
 * scan_capture_test
 *
 * Scan shift followed by capture cycle.
 */

class scan_capture_test extends dft_base_test;

    `uvm_component_utils(scan_capture_test)

    function new(string name = "scan_capture_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void configure_test();
        super.configure_test();
        cfg.test_mode = DFT_MODE_STUCK_AT;
    endfunction

    virtual task run_test_sequence();
        `uvm_info("SCAN_CAP", "Running scan + capture test (extend with capture timing)",
                  UVM_MEDIUM)
        env.run_scan_test("scan_capture");
    endtask

endclass

