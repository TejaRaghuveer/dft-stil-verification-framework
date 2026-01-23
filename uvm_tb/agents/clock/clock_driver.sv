/**
 * Clock Driver
 * 
 * Generates clock signals based on configuration.
 * Supports multiple clock domains and configurable frequency/duty cycle.
 */

class clock_driver extends uvm_driver#(uvm_sequence_item);
    
    `uvm_component_utils(clock_driver)
    
    // Virtual interface
    virtual clock_if vif;
    
    // Configuration
    test_config cfg;
    
    // Constructor
    function new(string name = "clock_driver", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        if (!uvm_config_db#(virtual clock_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("NO_VIF", "Failed to get clock_if from config_db")
        end
        
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config, using defaults")
        end
    endfunction
    
    // Run phase - generate clock
    task run_phase(uvm_phase phase);
        generate_clock();
    endtask
    
    // Generate clock signal
    task generate_clock();
        real high_time, low_time;
        real jitter;
        
        // Calculate timing based on period and duty cycle
        high_time = (cfg.clock_period_ns * cfg.clock_duty_cycle) / 100.0;
        low_time = cfg.clock_period_ns - high_time;
        
        `uvm_info("CLK_DRV", $sformatf("Generating clock: Period=%0dns, Duty=%0d%%", 
                  cfg.clock_period_ns, cfg.clock_duty_cycle), UVM_MEDIUM)
        
        vif.clk <= 0;
        
        forever begin
            // Low phase
            if (cfg.clock_enable_random_jitter) begin
                jitter = ($urandom_range(-10, 10)) / 10.0;  // ±1ns jitter
                #(low_time + jitter);
            end else begin
                #(low_time);
            end
            
            vif.clk <= 1;
            
            // High phase
            if (cfg.clock_enable_random_jitter) begin
                jitter = ($urandom_range(-10, 10)) / 10.0;
                #(high_time + jitter);
            end else begin
                #(high_time);
            end
            
            vif.clk <= 0;
        end
    endtask

endclass
