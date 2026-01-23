/**
 * Reset Agent
 * 
 * UVM agent for reset control.
 */

class reset_agent extends uvm_agent;
    
    `uvm_component_utils(reset_agent)
    
    reset_driver driver;
    test_config cfg;
    
    function new(string name = "reset_agent", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config")
        end
        
        if (cfg != null && cfg.reset_agent_active) begin
            driver = reset_driver::type_id::create("driver", this);
        end
    endfunction

endclass
