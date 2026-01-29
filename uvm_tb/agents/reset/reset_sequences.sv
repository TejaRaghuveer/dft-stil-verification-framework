/**
 * Reset Sequences
 * 
 * Pre-defined sequences for reset control in DFT test mode.
 */

class reset_base_sequence extends uvm_sequence#(reset_xtn);
    
    `uvm_object_utils(reset_base_sequence)
    
    test_config cfg;
    
    function new(string name = "reset_base_sequence");
        super.new(name);
    endfunction
    
    task pre_body();
        if (!uvm_config_db#(test_config)::get(null, get_full_name(), "cfg", cfg)) begin
            `uvm_warning("SEQ", "Failed to get test_config")
        end
    endtask

endclass

/**
 * Async Reset Sequence
 * Applies asynchronous reset
 */
class async_reset_sequence extends reset_base_sequence;
    
    `uvm_object_utils(async_reset_sequence)
    
    string reset_pin = "RST_N";
    reset_polarity_e polarity = ACTIVE_LOW;
    time duration = 100ns;
    
    task body();
        reset_xtn txn;
        txn = reset_xtn::type_id::create("async_rst_txn");
        txn.reset_pin = reset_pin;
        txn.reset_type = ASYNC;
        txn.polarity = polarity;
        txn.duration = duration;
        txn.assert_reset = 1;
        
        start_item(txn);
        finish_item(txn);
    endtask

endclass

/**
 * Sync Reset Sequence
 * Applies synchronous reset
 */
class sync_reset_sequence extends reset_base_sequence;
    
    `uvm_object_utils(sync_reset_sequence)
    
    string reset_pin = "RST_N";
    reset_polarity_e polarity = ACTIVE_LOW;
    int cycles = 10;
    time delay_from_clock = 0;
    
    task body();
        reset_xtn txn;
        txn = reset_xtn::type_id::create("sync_rst_txn");
        txn.reset_pin = reset_pin;
        txn.reset_type = SYNC;
        txn.polarity = polarity;
        txn.duration = cycles * cfg.clock_period_ns;
        txn.delay_from_clock = delay_from_clock;
        txn.assert_reset = 1;
        
        start_item(txn);
        finish_item(txn);
    endtask

endclass

/**
 * Reset Release Sequence
 * Releases reset
 */
class reset_release_sequence extends reset_base_sequence;
    
    `uvm_object_utils(reset_release_sequence)
    
    string reset_pin = "RST_N";
    reset_type_e reset_type = SYNC;
    
    task body();
        reset_xtn txn;
        txn = reset_xtn::type_id::create("release_rst_txn");
        txn.reset_pin = reset_pin;
        txn.reset_type = reset_type;
        txn.assert_reset = 0;  // Release
        
        start_item(txn);
        finish_item(txn);
    endtask

endclass

/**
 * Reset Sequence Sequence
 * Applies multiple resets in order
 */
class reset_sequence_sequence extends reset_base_sequence;
    
    `uvm_object_utils(reset_sequence_sequence)
    
    reset_xtn reset_list[];
    
    task body();
        foreach (reset_list[i]) begin
            start_item(reset_list[i]);
            finish_item(reset_list[i]);
            
            // Small delay between resets
            if (i < reset_list.size() - 1) begin
                #(10ns);
            end
        end
    endtask

endclass
