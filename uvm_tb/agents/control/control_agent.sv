/**
 * Unified Control Agent for Clock and Reset
 * 
 * Coordinates clock and reset operations for DFT test mode control.
 * Provides synchronized control of multiple clock domains and reset signals.
 * 
 * Features:
 * - Coordinated clock/reset sequences
 * - Scan mode control
 * - Timing margin analysis support
 * - Comprehensive monitoring and statistics
 */

class control_agent extends uvm_agent;
    
    `uvm_component_utils(control_agent)
    
    // Clock components
    clock_driver_enhanced clock_driver;
    clock_monitor_enhanced clock_monitor;
    uvm_sequencer#(clock_xtn) clock_sequencer;
    
    // Reset components
    reset_driver_enhanced reset_driver;
    reset_monitor_enhanced reset_monitor;
    uvm_sequencer#(reset_xtn) reset_sequencer;
    
    // Configuration
    test_config cfg;
    bit is_active = 1;
    
    // Analysis ports
    uvm_analysis_port#(clock_xtn) clock_analysis_port;
    uvm_analysis_port#(reset_xtn) reset_analysis_port;
    
    // Control state
    bit scan_mode = 0;
    bit clocks_running = 0;
    
    // Constructor
    function new(string name = "control_agent", uvm_component parent = null);
        super.new(name, parent);
        clock_analysis_port = new("clock_analysis_port", this);
        reset_analysis_port = new("reset_analysis_port", this);
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        // Get configuration
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config")
        end
        
        // Create monitors (always created)
        clock_monitor = clock_monitor_enhanced::type_id::create("clock_monitor", this);
        reset_monitor = reset_monitor_enhanced::type_id::create("reset_monitor", this);
        
        // Create drivers and sequencers if active
        if (cfg != null && cfg.clock_agent_active) begin
            clock_driver = clock_driver_enhanced::type_id::create("clock_driver", this);
            clock_sequencer = uvm_sequencer#(clock_xtn)::type_id::create("clock_sequencer", this);
        end
        
        if (cfg != null && cfg.reset_agent_active) begin
            reset_driver = reset_driver_enhanced::type_id::create("reset_driver", this);
            reset_sequencer = uvm_sequencer#(reset_xtn)::type_id::create("reset_sequencer", this);
        end
    endfunction
    
    // Connect phase
    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        
        // Connect clock components
        if (clock_driver != null) begin
            clock_driver.seq_item_port.connect(clock_sequencer.seq_item_export);
        end
        clock_monitor.analysis_port.connect(clock_analysis_port);
        
        // Connect reset components
        if (reset_driver != null) begin
            reset_driver.seq_item_port.connect(reset_sequencer.seq_item_export);
        end
        reset_monitor.analysis_port.connect(reset_analysis_port);
        
        // Coordinate clock and reset drivers
        if (reset_driver != null && clock_driver != null) begin
            coordinate_clock_reset();
        end
    endfunction
    
    // ============================================
    // Coordination Methods
    // ============================================
    
    /**
     * Coordinate clock and reset operations
     */
    function void coordinate_clock_reset();
        // Set up coordination callbacks
        // This allows reset driver to know about scan mode from clock driver
        // and vice versa
    endfunction
    
    /**
     * Enable scan mode (coordinates clock and reset)
     */
    function void enable_scan_mode();
        scan_mode = 1;
        if (clock_driver != null) begin
            clock_driver.request_clock_stop();
        end
        if (reset_driver != null) begin
            reset_driver.enable_scan_mode();
        end
        `uvm_info("CTRL_AGENT", "Scan mode enabled - clocks stopped, resets locked", UVM_MEDIUM)
    endfunction
    
    /**
     * Disable scan mode
     */
    function void disable_scan_mode();
        scan_mode = 0;
        if (clock_driver != null) begin
            clock_driver.resume_clock();
        end
        if (reset_driver != null) begin
            reset_driver.disable_scan_mode();
        end
        `uvm_info("CTRL_AGENT", "Scan mode disabled - clocks resumed", UVM_MEDIUM)
    endfunction
    
    /**
     * Apply reset sequence with clock coordination
     * @param reset_seq Array of reset transactions
     */
    task apply_coordinated_reset_sequence(reset_xtn reset_seq[]);
        // Stop clocks during reset
        if (clock_driver != null) begin
            clock_driver.request_clock_stop();
        end
        
        // Apply reset sequence
        if (reset_driver != null) begin
            reset_driver.apply_reset_sequence(reset_seq);
        end
        
        // Resume clocks after reset
        if (clock_driver != null) begin
            clock_driver.resume_clock();
        end
    endtask
    
    /**
     * Get reset status
     * @param reset_pin Reset pin identifier
     * @return Reset status
     */
    function bit get_reset_status(string reset_pin);
        if (reset_driver != null) begin
            return reset_driver.get_reset_status(reset_pin);
        end
        return 0;
    endfunction
    
    /**
     * Get clock statistics
     * @param clock_id Clock identifier
     * @return Statistics string
     */
    function string get_clock_statistics(string clock_id);
        if (clock_monitor != null) begin
            return $sformatf("Clock %s: Frequency=%0.2f MHz, Duty=%0.1f%%", 
                           clock_id, clock_monitor.measured_frequency, 
                           clock_monitor.measured_duty_cycle);
        end
        return "Clock statistics not available";
    endfunction
    
    /**
     * Get reset statistics
     * @param reset_pin Reset pin identifier
     * @return Statistics string
     */
    function string get_reset_statistics(string reset_pin);
        if (reset_driver != null) begin
            return reset_driver.get_reset_statistics(reset_pin);
        end
        return "Reset statistics not available";
    endfunction

endclass
