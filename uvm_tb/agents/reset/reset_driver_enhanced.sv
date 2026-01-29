/**
 * Enhanced Reset Driver for DFT Test Mode Control
 * 
 * Advanced reset driver with support for:
 * - Asynchronous and synchronous resets
 * - Multiple reset pins with sequencing
 * - Glitch prevention during scan mode
 * - Reset status feedback
 * - Precise timing control
 * 
 * Timing Constraints for Async Reset:
 * - Recovery time: Time from reset deassertion to clock edge
 * - Removal time: Time from clock edge to reset deassertion
 * - Reset pulse width: Minimum assertion duration
 * 
 * Glitch Prevention:
 * - During scan mode, resets must not toggle
 * - Reset changes synchronized to avoid metastability
 */

class reset_driver_enhanced extends uvm_driver#(reset_xtn);
    
    `uvm_component_utils(reset_driver_enhanced)
    
    // Virtual interface
    virtual reset_if vif;
    
    // Configuration
    test_config cfg;
    
    // Reset control
    bit scan_mode_active = 0;  // Prevents glitches during scan
    bit reset_sequence_active = 0;
    
    // Reset status tracking
    reset_xtn active_resets[string];  // Map of reset_pin -> transaction
    bit reset_status[string];          // Current reset status per pin
    
    // Reset statistics
    int reset_assert_count[string];
    int reset_deassert_count[string];
    time reset_assert_times[string][$];
    time reset_deassert_times[string][$];
    
    // Constructor
    function new(string name = "reset_driver_enhanced", uvm_component parent = null);
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
    
    // Run phase - main driver loop
    task run_phase(uvm_phase phase);
        reset_xtn txn;
        
        // Initialize reset
        initialize_reset();
        
        forever begin
            seq_item_port.get_next_item(req);
            drive_reset_transaction(req);
            seq_item_port.item_done();
        end
    endtask
    
    // ============================================
    // Initialization
    // ============================================
    
    /**
     * Initialize reset interface
     */
    task initialize_reset();
        // Deassert reset (active low, so set to 1)
        vif.rst_n <= 1;
        reset_status["RST_N"] = 0;  // Not asserted
        
        `uvm_info("RST_DRV", "Reset interface initialized (deasserted)", UVM_MEDIUM)
    endtask
    
    // ============================================
    // Reset Driving
    // ============================================
    
    /**
     * Drive reset transaction
     * @param txn Reset transaction to drive
     */
    task drive_reset_transaction(reset_xtn txn);
        `uvm_info("RST_DRV", $sformatf("Driving reset transaction:\n%s", txn.convert2string()), UVM_HIGH)
        
        txn.transaction_start_time = $time;
        
        // Check for scan mode (prevent glitches)
        if (scan_mode_active && txn.prevent_glitches) begin
            `uvm_warning("RST_DRV", "Reset change blocked during scan mode to prevent glitches")
            return;
        end
        
        // Store active reset
        active_resets[txn.reset_pin] = txn;
        
        if (txn.assert_reset) begin
            apply_reset(txn);
        end else begin
            release_reset(txn);
        end
        
        txn.transaction_end_time = $time;
    endtask
    
    /**
     * Apply reset
     * @param txn Reset transaction
     */
    task apply_reset(reset_xtn txn);
        bit reset_value = txn.get_reset_value();
        
        `uvm_info("RST_DRV", $sformatf("Asserting reset: %s (value=%0d)", 
                  txn.reset_pin, reset_value), UVM_MEDIUM)
        
        if (txn.reset_type == ASYNC) begin
            apply_async_reset(txn, reset_value);
        end else begin
            apply_sync_reset(txn, reset_value);
        end
        
        // Update status
        reset_status[txn.reset_pin] = 1;
        reset_assert_count[txn.reset_pin]++;
        reset_assert_times[txn.reset_pin].push_back($time);
    endtask
    
    /**
     * Apply asynchronous reset
     * @param txn Reset transaction
     * @param reset_value Reset signal value
     */
    task apply_async_reset(reset_xtn txn, bit reset_value);
        // Assert reset immediately (asynchronous)
        vif.rst_n <= reset_value;
        
        // Wait for specified duration
        #(txn.duration);
        
        `uvm_info("RST_DRV", $sformatf("Async reset %s asserted for %0t ns", 
                  txn.reset_pin, txn.duration), UVM_MEDIUM)
    endtask
    
    /**
     * Apply synchronous reset
     * @param txn Reset transaction
     * @param reset_value Reset signal value
     */
    task apply_sync_reset(reset_xtn txn, bit reset_value);
        // Wait for clock edge (synchronous)
        @(posedge vif.clk);
        
        // Apply delay from clock edge if specified
        if (txn.delay_from_clock > 0) begin
            #(txn.delay_from_clock);
        end
        
        // Assert reset on clock edge
        vif.rst_n <= reset_value;
        
        // Hold for specified duration (in clock cycles)
        int cycles = txn.duration / cfg.clock_period_ns;
        repeat(cycles) begin
            @(posedge vif.clk);
        end
        
        `uvm_info("RST_DRV", $sformatf("Sync reset %s asserted for %0d cycles", 
                  txn.reset_pin, cycles), UVM_MEDIUM)
    endtask
    
    /**
     * Release reset
     * @param txn Reset transaction
     */
    task release_reset(reset_xtn txn);
        bit deassert_value = txn.get_deassert_value();
        
        `uvm_info("RST_DRV", $sformatf("Releasing reset: %s (value=%0d)", 
                  txn.reset_pin, deassert_value), UVM_MEDIUM)
        
        if (txn.reset_type == ASYNC) begin
            release_async_reset(txn, deassert_value);
        end else begin
            release_sync_reset(txn, deassert_value);
        end
        
        // Update status
        reset_status[txn.reset_pin] = 0;
        reset_deassert_count[txn.reset_pin]++;
        reset_deassert_times[txn.reset_pin].push_back($time);
    endtask
    
    /**
     * Release asynchronous reset
     * @param txn Reset transaction
     * @param deassert_value Deassert signal value
     */
    task release_async_reset(reset_xtn txn, bit deassert_value);
        // Deassert reset immediately (asynchronous)
        vif.rst_n <= deassert_value;
        
        // Wait for recovery time (time from deassertion to clock edge)
        // This ensures proper recovery from reset
        #(txn.duration);  // Use duration as recovery time
        
        `uvm_info("RST_DRV", $sformatf("Async reset %s deasserted", txn.reset_pin), UVM_MEDIUM)
    endtask
    
    /**
     * Release synchronous reset
     * @param txn Reset transaction
     * @param deassert_value Deassert signal value
     */
    task release_sync_reset(reset_xtn txn, bit deassert_value);
        // Wait for clock edge (synchronous)
        @(posedge vif.clk);
        
        // Apply delay from clock edge if specified
        if (txn.delay_from_clock > 0) begin
            #(txn.delay_from_clock);
        end
        
        // Deassert reset on clock edge
        vif.rst_n <= deassert_value;
        
        `uvm_info("RST_DRV", $sformatf("Sync reset %s deasserted", txn.reset_pin), UVM_MEDIUM)
    endtask
    
    // ============================================
    // Reset Sequencing
    // ============================================
    
    /**
     * Apply reset sequence (multiple resets in order)
     * @param reset_sequence Array of reset transactions
     */
    task apply_reset_sequence(reset_xtn reset_sequence[]);
        reset_sequence_active = 1;
        
        `uvm_info("RST_DRV", $sformatf("Starting reset sequence with %0d resets", 
                  reset_sequence.size()), UVM_MEDIUM)
        
        foreach (reset_sequence[i]) begin
            drive_reset_transaction(reset_sequence[i]);
            
            // Wait between resets if not last
            if (i < reset_sequence.size() - 1) begin
                #(10ns);  // Small delay between resets
            end
        end
        
        reset_sequence_active = 0;
        `uvm_info("RST_DRV", "Reset sequence completed", UVM_MEDIUM)
    endtask
    
    // ============================================
    // Scan Mode Control
    // ============================================
    
    /**
     * Enable scan mode (prevents reset glitches)
     */
    function void enable_scan_mode();
        scan_mode_active = 1;
        `uvm_info("RST_DRV", "Scan mode enabled - reset glitches prevented", UVM_MEDIUM)
    endfunction
    
    /**
     * Disable scan mode
     */
    function void disable_scan_mode();
        scan_mode_active = 0;
        `uvm_info("RST_DRV", "Scan mode disabled", UVM_MEDIUM)
    endfunction
    
    // ============================================
    // Status Feedback
    // ============================================
    
    /**
     * Get reset status for a pin
     * @param reset_pin Reset pin identifier
     * @return 1 if asserted, 0 if deasserted
     */
    function bit get_reset_status(string reset_pin);
        if (reset_status.exists(reset_pin)) begin
            return reset_status[reset_pin];
        end else begin
            return 0;  // Default: not asserted
        end
    endfunction
    
    /**
     * Get reset statistics
     * @param reset_pin Reset pin identifier
     * @return Statistics string
     */
    function string get_reset_statistics(string reset_pin);
        string s;
        s = $sformatf("Reset Statistics for %s:\n", reset_pin);
        s = $sformatf("%s  Assert Count: %0d\n", s, reset_assert_count.exists(reset_pin) ? reset_assert_count[reset_pin] : 0);
        s = $sformatf("%s  Deassert Count: %0d\n", s, reset_deassert_count.exists(reset_pin) ? reset_deassert_count[reset_pin] : 0);
        s = $sformatf("%s  Current Status: %s", s, reset_status.exists(reset_pin) && reset_status[reset_pin] ? "ASSERTED" : "DEASSERTED");
        return s;
    endfunction

endclass
