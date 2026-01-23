/**
 * Base Test Class
 * 
 * Base class for all test cases. Provides common test setup and
 * configuration that can be extended by specific test cases.
 */

class base_test extends uvm_test;
    
    `uvm_component_utils(base_test)
    
    // Test environment
    test_env env;
    
    // Configuration
    test_config cfg;
    
    // Constructor
    function new(string name = "base_test", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        // Create and configure test configuration
        cfg = test_config::type_id::create("cfg");
        configure_test();
        
        // Set configuration in database
        uvm_config_db#(test_config)::set(this, "*", "cfg", cfg);
        
        // Create environment
        env = test_env::type_id::create("env", this);
    endfunction
    
    // Configure test - override in derived classes
    virtual function void configure_test();
        // Default configuration
        cfg.verbosity = UVM_MEDIUM;
        cfg.enable_waveform_dump = 1;
    endfunction
    
    // Run phase
    virtual task run_phase(uvm_phase phase);
        phase.raise_objection(this);
        
        `uvm_info("TEST", "Starting test", UVM_MEDIUM)
        
        // Run test sequence
        run_test_sequence();
        
        #1000ns;  // Allow time for final transactions
        
        phase.drop_objection(this);
    endtask
    
    // Run test sequence - override in derived classes
    virtual task run_test_sequence();
        `uvm_info("TEST", "Base test sequence - override in derived classes", UVM_MEDIUM)
    endtask

endclass
