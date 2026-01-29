/**
 * Enhanced Clock Driver for DFT Test Mode Control
 * 
 * Advanced clock driver with support for:
 * - Multiple clock domains (TCK, system clock, test clock)
 * - Half-period TCK toggling for JTAG compliance
 * - Edge capture on specified edges
 * - Precise timing logging
 * - Clock-stop-on-demand for timing margin analysis
 * 
 * Timing Constraints:
 * - Setup time: Data must be stable before clock edge
 * - Hold time: Data must remain stable after clock edge
 * - Clock-to-Q delay: Output valid after clock edge
 */

class clock_driver_enhanced extends uvm_driver#(clock_xtn);
    
    `uvm_component_utils(clock_driver_enhanced)
    
    // Virtual interfaces for multiple clock domains
    virtual clock_if sysclk_vif;      // System clock
    virtual clock_if tck_vif;         // JTAG clock (TCK)
    virtual clock_if testclk_vif;     // Test clock
    
    // Configuration
    test_config cfg;
    
    // Clock control
    bit clock_stop_requested = 0;
    bit clock_running = 0;
    
    // Clock statistics
    int clock_transition_count[$];
    time clock_transition_times[$];
    clock_edge_type_e clock_transition_types[$];
    
    // Active clock domains
    clock_xtn active_clocks[string];  // Map of clock_id -> transaction
    
    // Constructor
    function new(string name = "clock_driver_enhanced", uvm_component parent = null);
        super.new(name, parent);
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        // Get virtual interfaces (can be multiple clock domains)
        if (!uvm_config_db#(virtual clock_if)::get(this, "", "sysclk_vif", sysclk_vif)) begin
            `uvm_warning("NO_VIF", "System clock interface not found")
        end
        
        if (!uvm_config_db#(virtual clock_if)::get(this, "", "tck_vif", tck_vif)) begin
            `uvm_warning("NO_VIF", "TCK interface not found")
        end
        
        if (!uvm_config_db#(virtual clock_if)::get(this, "", "testclk_vif", testclk_vif)) begin
            `uvm_warning("NO_VIF", "Test clock interface not found")
        end
        
        // Get configuration
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config, using defaults")
        end
    endfunction
    
    // Run phase - main driver loop
    task run_phase(uvm_phase phase);
        clock_xtn txn;
        
        // Initialize all clock domains
        initialize_clocks();
        
        forever begin
            seq_item_port.get_next_item(req);
            drive_clock_transaction(req);
            seq_item_port.item_done();
        end
    endtask
    
    // ============================================
    // Initialization
    // ============================================
    
    /**
     * Initialize all clock domains
     */
    task initialize_clocks();
        if (sysclk_vif != null) begin
            sysclk_vif.clk <= 0;
        end
        if (tck_vif != null) begin
            tck_vif.clk <= 0;
        end
        if (testclk_vif != null) begin
            testclk_vif.clk <= 0;
        end
        
        clock_running = 1;
        `uvm_info("CLK_DRV", "All clock domains initialized", UVM_MEDIUM)
    endtask
    
    // ============================================
    // Clock Driving
    // ============================================
    
    /**
     * Drive clock transaction
     * @param txn Clock transaction to drive
     */
    task drive_clock_transaction(clock_xtn txn);
        `uvm_info("CLK_DRV", $sformatf("Driving clock transaction:\n%s", txn.convert2string()), UVM_HIGH)
        
        txn.transaction_start_time = $time;
        txn.calculate_timing();
        
        // Store active clock
        active_clocks[txn.clock_id] = txn;
        
        // Get appropriate interface based on clock_id
        virtual clock_if clk_vif = get_clock_interface(txn.clock_id);
        
        if (clk_vif == null) begin
            `uvm_error("CLK_DRV", $sformatf("No interface found for clock: %s", txn.clock_id))
            return;
        end
        
        // Check for clock stop request
        if (clock_stop_requested) begin
            `uvm_info("CLK_DRV", "Clock stop requested, pausing...", UVM_MEDIUM)
            wait(clock_stop_requested == 0);
        end
        
        // Drive clock based on transaction
        if (txn.clock_enable) begin
            if (txn.half_period_clocks > 0) begin
                drive_half_period_clocks(clk_vif, txn);
            end else if (txn.stop_time > 0) begin
                drive_clock_with_stop_time(clk_vif, txn);
            end else begin
                drive_continuous_clock(clk_vif, txn);
            end
        end else begin
            // Disable clock (hold at current state or low)
            clk_vif.clk <= 0;
            `uvm_info("CLK_DRV", $sformatf("Clock %s disabled", txn.clock_id), UVM_MEDIUM)
        end
        
        txn.transaction_end_time = $time;
        txn.total_cycles = get_clock_cycle_count(txn.clock_id);
    endtask
    
    /**
     * Drive half-period clocks (for JTAG TCK compliance)
     * @param vif Clock interface
     * @param txn Clock transaction
     */
    task drive_half_period_clocks(virtual clock_if vif, clock_xtn txn);
        int half_periods = txn.half_period_clocks;
        bit current_state = 0;
        
        `uvm_info("CLK_DRV", $sformatf("Driving %0d half-period clocks for %s", 
                  half_periods, txn.clock_id), UVM_MEDIUM)
        
        for (int i = 0; i < half_periods; i++) begin
            // Check for stop request
            if (clock_stop_requested) begin
                `uvm_info("CLK_DRV", "Clock stop requested during half-period generation", UVM_MEDIUM)
                wait(clock_stop_requested == 0);
            end
            
            // Toggle clock
            current_state = ~current_state;
            vif.clk <= current_state;
            
            // Log transition
            log_clock_transition(txn.clock_id, current_state ? LEADING : TRAILING);
            
            // Wait half period
            #(txn.period_ns / 2.0);
        end
        
        `uvm_info("CLK_DRV", $sformatf("Completed %0d half-period clocks", half_periods), UVM_MEDIUM)
    endtask
    
    /**
     * Drive clock with stop time
     * @param vif Clock interface
     * @param txn Clock transaction
     */
    task drive_clock_with_stop_time(virtual clock_if vif, clock_xtn txn);
        time current_time = $time;
        time stop_time = txn.start_time + txn.stop_time;
        int cycle_count = 0;
        
        `uvm_info("CLK_DRV", $sformatf("Driving clock until stop time: %0t", stop_time), UVM_MEDIUM)
        
        while ($time < stop_time && clock_running && !clock_stop_requested) begin
            // Leading edge
            vif.clk <= 1;
            log_clock_transition(txn.clock_id, LEADING);
            #(txn.high_time_ns);
            
            // Trailing edge
            vif.clk <= 0;
            log_clock_transition(txn.clock_id, TRAILING);
            #(txn.low_time_ns);
            
            cycle_count++;
        end
        
        txn.total_cycles = cycle_count;
        `uvm_info("CLK_DRV", $sformatf("Stopped clock after %0d cycles", cycle_count), UVM_MEDIUM)
    endtask
    
    /**
     * Drive continuous clock
     * @param vif Clock interface
     * @param txn Clock transaction
     */
    task drive_continuous_clock(virtual clock_if vif, clock_xtn txn);
        int cycle_count = 0;
        
        `uvm_info("CLK_DRV", $sformatf("Driving continuous clock: %s", txn.clock_id), UVM_MEDIUM)
        
        forever begin
            // Check for stop request
            if (clock_stop_requested) begin
                `uvm_info("CLK_DRV", "Clock stop requested", UVM_MEDIUM)
                wait(clock_stop_requested == 0);
            end
            
            // Leading edge
            vif.clk <= 1;
            log_clock_transition(txn.clock_id, LEADING);
            
            // Capture on leading edge if configured
            if (txn.capture_edge == LEADING || txn.capture_edge == BOTH) begin
                capture_data_on_edge(txn.clock_id, LEADING);
            end
            
            #(txn.high_time_ns);
            
            // Trailing edge
            vif.clk <= 0;
            log_clock_transition(txn.clock_id, TRAILING);
            
            // Capture on trailing edge if configured
            if (txn.capture_edge == TRAILING || txn.capture_edge == BOTH) begin
                capture_data_on_edge(txn.clock_id, TRAILING);
            end
            
            #(txn.low_time_ns);
            
            cycle_count++;
        end
    endtask
    
    // ============================================
    // Clock Control
    // ============================================
    
    /**
     * Request clock stop (for timing margin analysis)
     */
    function void request_clock_stop();
        clock_stop_requested = 1;
        `uvm_info("CLK_DRV", "Clock stop requested", UVM_MEDIUM)
    endfunction
    
    /**
     * Resume clock after stop
     */
    function void resume_clock();
        clock_stop_requested = 0;
        `uvm_info("CLK_DRV", "Clock resumed", UVM_MEDIUM)
    endfunction
    
    /**
     * Stop all clocks
     */
    function void stop_all_clocks();
        clock_running = 0;
        if (sysclk_vif != null) sysclk_vif.clk <= 0;
        if (tck_vif != null) tck_vif.clk <= 0;
        if (testclk_vif != null) testclk_vif.clk <= 0;
        `uvm_info("CLK_DRV", "All clocks stopped", UVM_MEDIUM)
    endfunction
    
    // ============================================
    // Utility Methods
    // ============================================
    
    /**
     * Get clock interface based on clock_id
     * @param clock_id Clock identifier
     * @return Virtual interface pointer
     */
    function virtual clock_if get_clock_interface(string clock_id);
        case (clock_id)
            "TCK", "tck": return tck_vif;
            "SYSCLK", "sysclk", "CLK": return sysclk_vif;
            "TESTCLK", "testclk": return testclk_vif;
            default: begin
                `uvm_warning("CLK_DRV", $sformatf("Unknown clock_id: %s, using sysclk", clock_id))
                return sysclk_vif;
            end
        endcase
    endfunction
    
    /**
     * Log clock transition
     * @param clock_id Clock identifier
     * @param edge_type Edge type (LEADING/TRAILING)
     */
    function void log_clock_transition(string clock_id, clock_edge_type_e edge_type);
        clock_transition_times.push_back($time);
        clock_transition_types.push_back(edge_type);
        clock_transition_count.push_back(clock_transition_count.size());
        
        `uvm_info("CLK_DRV", $sformatf("[%0t] Clock %s: %s edge", 
                  $time, clock_id, edge_type.name()), UVM_HIGH)
    endfunction
    
    /**
     * Capture data on clock edge
     * @param clock_id Clock identifier
     * @param edge_type Edge type
     */
    function void capture_data_on_edge(string clock_id, clock_edge_type_e edge_type);
        // This would be extended to capture actual data from DUT
        // For now, just log the capture event
        `uvm_info("CLK_DRV", $sformatf("Capturing data on %s %s edge", 
                  clock_id, edge_type.name()), UVM_HIGH)
    endfunction
    
    /**
     * Get clock cycle count for a clock domain
     * @param clock_id Clock identifier
     * @return Cycle count
     */
    function int get_clock_cycle_count(string clock_id);
        int count = 0;
        foreach (clock_transition_types[i]) begin
            if (clock_transition_types[i] == LEADING) begin
                count++;
            end
        end
        return count;
    endfunction

endclass
