/**
 * JTAG Agent
 * 
 * Complete UVM agent for JTAG interface including driver, monitor,
 * and sequencer. Can operate in active or passive mode.
 */

class jtag_agent extends uvm_agent;
    
    `uvm_component_utils(jtag_agent)
    
    // Agent components
    jtag_driver driver;
    jtag_monitor monitor;
    uvm_sequencer#(jtag_transaction) sequencer;
    
    // Configuration
    test_config cfg;
    bit is_active = 1;
    
    // Constructor
    function new(string name = "jtag_agent", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        // Get configuration
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config")
        end
        
        // Create monitor (always created)
        monitor = jtag_monitor::type_id::create("monitor", this);
        
        // Create driver and sequencer only if active
        if (cfg != null && cfg.jtag_agent_active) begin
            is_active = 1;
            driver = jtag_driver::type_id::create("driver", this);
            sequencer = uvm_sequencer#(jtag_transaction)::type_id::create("sequencer", this);
        end else begin
            is_active = 0;
        end
    endfunction
    
    // Connect phase
    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        
        if (is_active) begin
            driver.seq_item_port.connect(sequencer.seq_item_export);
        end
    endfunction

endclass
