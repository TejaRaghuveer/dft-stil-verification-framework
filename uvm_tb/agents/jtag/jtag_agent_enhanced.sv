/**
 * Enhanced JTAG Agent (IEEE 1149.1 Compliant)
 * 
 * Complete JTAG agent with enhanced driver, monitor, sequencer, and coverage.
 * Supports both active (drives signals) and passive (monitors only) modes.
 * 
 * Agent Components:
 * - Enhanced Driver: Drives JTAG signals with full TAP state machine
 * - Enhanced Monitor: Monitors and reconstructs JTAG transactions
 * - Sequencer: Manages sequence execution
 * - Coverage: Functional coverage collection
 * 
 * Configuration Options:
 * - Active/Passive mode
 * - Clock period
 * - Reset cycles
 * - Coverage enable/disable
 * 
 * Reference: IEEE 1149.1 Standard for Test Access Port and Boundary-Scan Architecture
 */

class jtag_agent_enhanced extends uvm_agent;
    
    `uvm_component_utils(jtag_agent_enhanced)
    
    // Agent components
    jtag_driver_enhanced driver;
    jtag_monitor_enhanced monitor;
    uvm_sequencer#(jtag_xtn) sequencer;
    jtag_coverage coverage;
    
    // Configuration
    test_config cfg;
    bit is_active = 1;
    bit enable_coverage = 1;
    
    // Analysis ports (for connecting to subscribers)
    uvm_analysis_port#(jtag_xtn) analysis_port;
    
    // Constructor
    function new(string name = "jtag_agent_enhanced", uvm_component parent = null);
        super.new(name, parent);
        analysis_port = new("analysis_port", this);
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        // Get configuration
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config, using defaults")
        end
        
        // Create monitor (always created - monitors DUT activity)
        monitor = jtag_monitor_enhanced::type_id::create("monitor", this);
        
        // Create driver and sequencer only if active
        if (cfg != null && cfg.jtag_agent_active) begin
            is_active = 1;
            driver = jtag_driver_enhanced::type_id::create("driver", this);
            sequencer = uvm_sequencer#(jtag_xtn)::type_id::create("sequencer", this);
        end else begin
            is_active = 0;
        end
        
        // Create coverage collector if enabled
        if (enable_coverage && (cfg == null || cfg.jtag_enable_coverage)) begin
            coverage = jtag_coverage::type_id::create("coverage", this);
        end
    endfunction
    
    // Connect phase
    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        
        // Connect driver to sequencer (active mode only)
        if (is_active) begin
            driver.seq_item_port.connect(sequencer.seq_item_export);
        end
        
        // Connect monitor analysis port to agent analysis port
        monitor.analysis_port.connect(analysis_port);
        
        // Connect monitor to coverage collector
        if (coverage != null) begin
            monitor.analysis_port.connect(coverage.analysis_export);
        end
    endfunction
    
    // End of elaboration
    function void end_of_elaboration_phase(uvm_phase phase);
        super.end_of_elaboration_phase(phase);
        `uvm_info("JTAG_AGENT", $sformatf("JTAG Agent configured: Active=%0d, Coverage=%0d", 
                  is_active, (coverage != null)), UVM_MEDIUM)
    endfunction

endclass
