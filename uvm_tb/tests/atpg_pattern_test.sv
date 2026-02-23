/**
 * atpg_pattern_test
 *
 * Executes ATPG pattern sequences (STIL or similar).
 * Concrete pattern application should be implemented in env.run_scan_test()
 * and associated sequences.
 */

class atpg_pattern_test extends dft_base_test;

    `uvm_component_utils(atpg_pattern_test)

    function new(string name = "atpg_pattern_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    virtual function void configure_test();
        super.configure_test();
        cfg.test_mode = DFT_MODE_STUCK_AT;
    endfunction

    virtual task run_test_sequence();
        `uvm_info("ATPG", "Running generic ATPG pattern test", UVM_MEDIUM)
        env.run_scan_test("atpg_patterns");
    endtask

endclass

