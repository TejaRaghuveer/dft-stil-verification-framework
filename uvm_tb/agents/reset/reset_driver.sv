/**
 * Reset Driver
 * 
 * Controls reset signal assertion and deassertion based on configuration.
 * Supports both synchronous and asynchronous reset protocols.
 */

class reset_driver extends uvm_driver#(uvm_sequence_item);
    
    `uvm_component_utils(reset_driver)
    
    // Virtual interface
    virtual reset_if vif;
    
    // Configuration
    test_config cfg;
    
    // Constructor
    function new(string name = "reset_driver", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        if (!uvm_config_db#(virtual reset_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("NO_VIF", "Failed to get reset_if from config_db")
        end
        
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config, using defaults")
        end
    endfunction
    
    // Run phase
    task run_phase(uvm_phase phase);
        apply_reset();
    endtask
    
    // Apply reset sequence
    task apply_reset();
        `uvm_info("RST_DRV", "Applying reset", UVM_MEDIUM)
        
        if (cfg.reset_async) begin
            // Asynchronous reset
            vif.rst_n <= 0;
            #(cfg.reset_assert_cycles * cfg.clock_period_ns);
            #(cfg.reset_deassert_delay_ns);
            vif.rst_n <= 1;
        end else begin
            // Synchronous reset
            vif.rst_n <= 0;
            repeat(cfg.reset_assert_cycles) begin
                @(posedge vif.clk);
            end
            #(cfg.reset_deassert_delay_ns);
            @(posedge vif.clk);
            vif.rst_n <= 1;
        end
        
        `uvm_info("RST_DRV", "Reset deasserted", UVM_MEDIUM)
    endtask

endclass
