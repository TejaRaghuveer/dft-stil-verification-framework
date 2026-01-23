/**
 * Test Environment
 * 
 * Top-level UVM environment that instantiates and connects all agents,
 * subscribers, and other testbench components.
 */

class test_env extends uvm_env;
    
    `uvm_component_utils(test_env)
    
    // Agents
    jtag_agent jtag_agent_inst;
    clock_agent clock_agent_inst;
    reset_agent reset_agent_inst;
    pad_agent pad_agent_inst;
    
    // Subscribers
    stil_subscriber stil_sub_inst;
    
    // Configuration
    test_config cfg;
    
    // Constructor
    function new(string name = "test_env", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        // Get configuration
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config, creating default")
            cfg = test_config::type_id::create("cfg");
        end
        
        // Create agents
        if (cfg.jtag_agent_active) begin
            jtag_agent_inst = jtag_agent::type_id::create("jtag_agent_inst", this);
        end
        
        if (cfg.clock_agent_active) begin
            clock_agent_inst = clock_agent::type_id::create("clock_agent_inst", this);
        end
        
        if (cfg.reset_agent_active) begin
            reset_agent_inst = reset_agent::type_id::create("reset_agent_inst", this);
        end
        
        if (cfg.pad_agent_active) begin
            pad_agent_inst = pad_agent::type_id::create("pad_agent_inst", this);
        end
        
        // Create subscribers
        if (cfg.stil_enable_generation) begin
            stil_sub_inst = stil_subscriber::type_id::create("stil_sub_inst", this);
        end
    endfunction
    
    // Connect phase
    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        
        // Connect subscriber to agent analysis ports
        if (cfg.stil_enable_generation && jtag_agent_inst != null) begin
            jtag_agent_inst.monitor.analysis_port.connect(stil_sub_inst.analysis_export);
        end
    endfunction
    
    // End of elaboration
    function void end_of_elaboration_phase(uvm_phase phase);
        super.end_of_elaboration_phase(phase);
        `uvm_info("ENV", "Test environment elaborated", UVM_MEDIUM)
        `uvm_info("ENV", cfg.convert2string(), UVM_MEDIUM)
    endfunction

endclass
