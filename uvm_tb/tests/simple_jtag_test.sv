/**
 * Simple JTAG Test
 * 
 * Example test case that demonstrates basic JTAG testing.
 * Extend this test for your specific verification requirements.
 */

class simple_jtag_test extends base_test;
    
    `uvm_component_utils(simple_jtag_test)
    
    // Constructor
    function new(string name = "simple_jtag_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    // Configure test
    function void configure_test();
        super.configure_test();
        
        // Configure test parameters
        cfg.verbosity = UVM_MEDIUM;
        cfg.jtag_clock_period_ns = 100;  // 10MHz
        cfg.num_test_patterns = 50;
        cfg.stil_enable_generation = 1;
        cfg.stil_output_file = "simple_jtag_test.stil";
        
        `uvm_info("TEST", "Configured simple JTAG test", UVM_MEDIUM)
    endfunction
    
    // Run test sequence
    task run_test_sequence();
        jtag_sequence seq;
        
        `uvm_info("TEST", "Starting simple JTAG test", UVM_MEDIUM)
        
        // Create and start sequence
        seq = jtag_sequence::type_id::create("seq");
        seq.num_vectors = cfg.num_test_patterns;
        
        if (env.jtag_agent_inst != null && env.jtag_agent_inst.sequencer != null) begin
            seq.start(env.jtag_agent_inst.sequencer);
        end else begin
            `uvm_error("TEST", "JTAG agent or sequencer not available")
        end
        
        `uvm_info("TEST", "Simple JTAG test completed", UVM_MEDIUM)
    endtask

endclass
