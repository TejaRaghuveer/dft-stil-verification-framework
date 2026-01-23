/**
 * Clock Agent
 * 
 * UVM agent for clock generation.
 */

class clock_agent extends uvm_agent;
    
    `uvm_component_utils(clock_agent)
    
    clock_driver driver;
    test_config cfg;
    
    function new(string name = "clock_agent", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config")
        end
        
        if (cfg != null && cfg.clock_agent_active) begin
            driver = clock_driver::type_id::create("driver", this);
        end
    endfunction

endclass
