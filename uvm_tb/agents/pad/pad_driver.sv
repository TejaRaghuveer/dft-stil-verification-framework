/**
 * Pad Driver
 * 
 * Drives pad interface signals for boundary scan and I/O testing.
 * Handles bidirectional pad control with output enable signals.
 */

class pad_driver extends uvm_driver#(uvm_sequence_item);
    
    `uvm_component_utils(pad_driver)
    
    // Virtual interface
    virtual pad_if vif;
    
    // Configuration
    test_config cfg;
    
    // Constructor
    function new(string name = "pad_driver", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        if (!uvm_config_db#(virtual pad_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("NO_VIF", "Failed to get pad_if from config_db")
        end
        
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config, using defaults")
        end
    endfunction
    
    // Run phase
    task run_phase(uvm_phase phase);
        initialize_pads();
        
        forever begin
            seq_item_port.get_next_item(req);
            drive_pad_transaction(req);
            seq_item_port.item_done();
        end
    endtask
    
    // Initialize pad interface
    task initialize_pads();
        vif.pad_out <= '0;
        vif.pad_oe <= '0;  // All pads as inputs initially
        `uvm_info("PAD_DRV", "Pad interface initialized", UVM_MEDIUM)
    endtask
    
    // Drive pad transaction
    task drive_pad_transaction(uvm_sequence_item item);
        // This would be extended based on specific pad transaction class
        `uvm_info("PAD_DRV", "Driving pad transaction", UVM_HIGH)
    endtask

endclass
