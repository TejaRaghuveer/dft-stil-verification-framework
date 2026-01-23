/**
 * Pad Agent
 * 
 * UVM agent for pad interface control.
 */

class pad_agent extends uvm_agent;
    
    `uvm_component_utils(pad_agent)
    
    pad_driver driver;
    test_config cfg;
    
    function new(string name = "pad_agent", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config")
        end
        
        if (cfg != null && cfg.pad_agent_active) begin
            driver = pad_driver::type_id::create("driver", this);
        end
    endfunction

endclass
