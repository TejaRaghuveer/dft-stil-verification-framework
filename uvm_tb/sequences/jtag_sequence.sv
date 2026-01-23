/**
 * JTAG Sequence Example
 * 
 * Example sequence for JTAG operations.
 * Demonstrates how to create sequences for JTAG testing.
 */

class jtag_sequence extends base_sequence;
    
    `uvm_object_utils(jtag_sequence)
    
    // Sequence parameters
    int num_vectors = 10;
    
    // Constructor
    function new(string name = "jtag_sequence");
        super.new(name);
    endfunction
    
    // Body task
    task body();
        jtag_transaction txn;
        
        `uvm_info("JTAG_SEQ", $sformatf("Starting JTAG sequence with %0d vectors", num_vectors), UVM_MEDIUM)
        
        // Get sequencer from parent sequence or agent
        if (m_sequencer == null) begin
            `uvm_fatal("JTAG_SEQ", "Sequencer is null")
        end
        
        // Generate JTAG vectors
        repeat(num_vectors) begin
            txn = jtag_transaction::type_id::create("txn");
            
            start_item(txn);
            
            // Randomize transaction
            if (!txn.randomize()) begin
                `uvm_error("JTAG_SEQ", "Failed to randomize transaction")
            end
            
            finish_item(txn);
            
            `uvm_info("JTAG_SEQ", $sformatf("Sent: %s", txn.convert2string()), UVM_HIGH)
        end
        
        `uvm_info("JTAG_SEQ", "JTAG sequence completed", UVM_MEDIUM)
    endtask

endclass
