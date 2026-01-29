/**
 * Clock Sequences
 * 
 * Pre-defined sequences for clock control in DFT test mode.
 */

class clock_base_sequence extends uvm_sequence#(clock_xtn);
    
    `uvm_object_utils(clock_base_sequence)
    
    test_config cfg;
    
    function new(string name = "clock_base_sequence");
        super.new(name);
    endfunction
    
    task pre_body();
        if (!uvm_config_db#(test_config)::get(null, get_full_name(), "cfg", cfg)) begin
            `uvm_warning("SEQ", "Failed to get test_config")
        end
    endtask

endclass

/**
 * Continuous Clock Sequence
 * Generates continuous clock with specified frequency
 */
class continuous_clock_sequence extends clock_base_sequence;
    
    `uvm_object_utils(continuous_clock_sequence)
    
    string clock_id = "SYSCLK";
    real frequency = 100.0;  // MHz
    real duty_cycle = 50.0;
    
    task body();
        clock_xtn txn;
        txn = clock_xtn::type_id::create("clock_txn");
        txn.clock_id = clock_id;
        txn.frequency = frequency;
        txn.duty_cycle = duty_cycle;
        txn.clock_enable = 1;
        txn.calculate_timing();
        
        start_item(txn);
        finish_item(txn);
    endtask

endclass

/**
 * Half-Period Clock Sequence (for JTAG TCK)
 * Generates specified number of half-period clocks
 */
class half_period_clock_sequence extends clock_base_sequence;
    
    `uvm_object_utils(half_period_clock_sequence)
    
    string clock_id = "TCK";
    real frequency = 10.0;  // 10MHz for JTAG
    int num_half_periods = 10;
    
    task body();
        clock_xtn txn;
        txn = clock_xtn::type_id::create("tck_txn");
        txn.clock_id = clock_id;
        txn.frequency = frequency;
        txn.set_half_period_clocks(num_half_periods);
        txn.calculate_timing();
        
        start_item(txn);
        finish_item(txn);
    endtask

endclass

/**
 * Clock Stop Sequence
 * Stops clock for timing margin analysis
 */
class clock_stop_sequence extends clock_base_sequence;
    
    `uvm_object_utils(clock_stop_sequence)
    
    string clock_id = "SYSCLK";
    time stop_duration = 100ns;
    
    task body();
        clock_xtn txn;
        txn = clock_xtn::type_id::create("stop_txn");
        txn.clock_id = clock_id;
        txn.clock_enable = 0;
        txn.start_time = $time;
        txn.stop_time = $time + stop_duration;
        
        start_item(txn);
        finish_item(txn);
    endtask

endclass
