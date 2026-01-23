/**
 * Base Sequence Class
 * 
 * Base class for all test sequences in the UVM testbench.
 * Provides common functionality and utilities for sequence generation.
 */

class base_sequence extends uvm_sequence#(uvm_sequence_item);
    
    `uvm_object_utils(base_sequence)
    
    // Configuration object reference
    test_config cfg;
    
    // Constructor
    function new(string name = "base_sequence");
        super.new(name);
    endfunction
    
    // Pre-body: Get configuration from config database
    task pre_body();
        if (!uvm_config_db#(test_config)::get(null, get_full_name(), "cfg", cfg)) begin
            `uvm_fatal("CONFIG", "Failed to get test_config from config_db")
        end
    endtask
    
    // Body: To be overridden by derived sequences
    task body();
        `uvm_info("SEQ", "Base sequence body - override in derived classes", UVM_MEDIUM)
    endtask

endclass
