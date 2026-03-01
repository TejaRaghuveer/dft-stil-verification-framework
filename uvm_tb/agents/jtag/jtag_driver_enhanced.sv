/**
 * Enhanced JTAG Driver (IEEE 1149.1 Compliant)
 * 
 * Complete JTAG driver implementation with full TAP state machine support.
 * Converts JTAG transactions to pin-level TCK, TMS, TDI, TDO toggles.
 * 
 * TAP State Machine (IEEE 1149.1):
 *   - Test-Logic-Reset (TLR): Reset state, entered when TMS=1 for 5+ cycles
 *   - Run-Test/Idle (RTI): Idle state
 *   - Select-DR-Scan (SelDR): Route to DR path
 *   - Select-IR-Scan (SelIR): Route to IR path
 *   - Capture-DR/IR: Capture parallel data
 *   - Shift-DR/IR: Shift serial data
 *   - Exit1-DR/IR: First exit point
 *   - Pause-DR/IR: Pause state (optional)
 *   - Exit2-DR/IR: Second exit point
 *   - Update-DR/IR: Update parallel output
 * 
 * Timing Constraints (IEEE 1149.1):
 *   - TMS/TDI setup before TCK rising edge: t_setup
 *   - TMS/TDI hold after TCK falling edge: t_hold
 *   - TDO valid after TCK falling edge: t_valid
 * 
 * Reference: IEEE 1149.1 Standard for Test Access Port and Boundary-Scan Architecture
 */

class jtag_driver_enhanced extends uvm_driver#(jtag_xtn);
    
    `uvm_component_utils(jtag_driver_enhanced)
    
    // Virtual interface
    virtual jtag_if vif;
    
    // Configuration
    test_config cfg;
    
    // Current TAP state
    jtag_state_t current_state;
    
    // Transaction logging
    jtag_xtn transaction_log[$];
    int transaction_count = 0;
    
    // Constructor
    function new(string name = "jtag_driver_enhanced", uvm_component parent = null);
        super.new(name, parent);
        current_state = TEST_LOGIC_RESET;
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        // Get virtual interface
        if (!uvm_config_db#(virtual jtag_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("NO_VIF", "Failed to get jtag_if from config_db")
        end
        
        // Get configuration
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config, using defaults")
        end
    endfunction
    
    // Run phase - main driver loop
    task run_phase(uvm_phase phase);
        // Initialize JTAG interface
        initialize_jtag();
        
        forever begin
            seq_item_port.get_next_item(req);
            drive_transaction(req);
            seq_item_port.item_done();
        end
    endtask
    
    // ============================================
    // Initialization
    // ============================================
    
    /**
     * Initialize JTAG interface
     * 
     * Sets initial signal values and enters Test-Logic-Reset state.
     * Per IEEE 1149.1, TMS must be held high for at least 5 TCK cycles.
     */
    task initialize_jtag();
        int reset_cycles = (cfg != null) ? cfg.jtag_reset_cycles : 5;
        int period_ns    = (cfg != null) ? cfg.jtag_clock_period_ns : 100;
        
        `uvm_info("JTAG_DRV", "Initializing JTAG interface", UVM_MEDIUM)
        
        // Initialize signals
        vif.tck <= 0;
        vif.tms <= 1;      // TMS=1 to enter Test-Logic-Reset
        vif.tdi <= 0;
        vif.trst_n <= 0;   // Assert TRST (if available)
        
        // Hold reset for configured cycles (minimum 5 per IEEE 1149.1)
        // Generate clock directly to avoid deadlock
        repeat(reset_cycles) begin
            #(period_ns / 2);
            vif.tck <= 1;
            #(period_ns / 2);
            vif.tck <= 0;
        end
        
        // Deassert TRST
        vif.trst_n <= 1;
        
        // Update state
        current_state = TEST_LOGIC_RESET;
        
        `uvm_info("JTAG_DRV", $sformatf("JTAG initialized: State=%s", 
                  current_state.name()), UVM_MEDIUM)
    endtask
    
    // ============================================
    // Transaction Driving
    // ============================================
    
    /**
     * Drive a JTAG transaction
     * 
     * Converts transaction to pin-level signals and drives them according to
     * IEEE 1149.1 timing constraints.
     * 
     * @param txn JTAG transaction to drive
     */
    task drive_transaction(jtag_xtn txn);
        `uvm_info("JTAG_DRV", $sformatf("Driving transaction:\n%s", txn.convert2string()), UVM_HIGH)
        
        txn.start_time = $time;
        txn.start_state = current_state;
        
        // Log transaction
        transaction_log.push_back(txn);
        transaction_count++;
        
        // Drive transaction based on sequence type
        case (txn.sequence_type)
            LOAD_IR:    drive_load_ir(txn);
            LOAD_DR:   drive_load_dr(txn);
            SCAN_SHIFT: drive_scan_shift(txn);
            BYPASS:    drive_bypass(txn);
            TAP_RESET: drive_bypass(txn);  // Same TMS/TDI vector drive as bypass
            TDI_TDO_CHECK: drive_tdi_tdo_check(txn);
            default:   `uvm_error("JTAG_DRV", $sformatf("Unknown sequence type: %s", txn.sequence_type.name()))
        endcase
        
        txn.end_time = $time;
        txn.end_state = current_state;
        
        `uvm_info("JTAG_DRV", $sformatf("Transaction completed: %0d cycles, duration=%0t ns", 
                  txn.cycle_count, txn.end_time - txn.start_time), UVM_MEDIUM)
    endtask
    
    // ============================================
    // Sequence-Specific Drive Methods
    // ============================================
    
    /**
     * Drive generic JTAG sequence
     * 
     * Drives TMS and TDI vectors according to transaction specification.
     * Samples TDO at appropriate timing edges.
     * 
     * @param txn Transaction with TMS/TDI vectors
     */
    task drive_generic_sequence(jtag_xtn txn);
        bit tdo_captured[];
        int tdi_idx = 0;
        
        // Allocate TDO capture array
        tdo_captured = new[txn.cycle_count];
        
        // Derive period from configuration (with safe default)
        int period_ns = (cfg != null) ? cfg.jtag_clock_period_ns : 100;

        // Drive each cycle
        for (int i = 0; i < txn.cycle_count; i++) begin
            // Setup phase: Set TMS and TDI before rising edge
            // Timing: t_setup before TCK rising edge
            #(txn.setup_time_ns);
            
            // Set TMS
            vif.tms <= txn.tms_vector[i];
            
            // Set TDI (if TDI vector is available and we're in shift state)
            if (txn.tdi_vector.size() > 0 && tdi_idx < txn.tdi_vector.size()) begin
                // Only drive TDI during shift states (Shift-DR or Shift-IR)
                if (is_shift_state(current_state)) begin
                    vif.tdi <= txn.tdi_vector[tdi_idx];
                    tdi_idx++;
                end else begin
                    vif.tdi <= 0;  // TDI doesn't matter in non-shift states
                end
            end else begin
                vif.tdi <= 0;
            end
            
            // Generate TCK rising edge
            #((period_ns / 2) - txn.setup_time_ns);
            vif.tck <= 1;
            
            // Update TAP state machine based on TMS
            update_tap_state(txn.tms_vector[i]);
            
            // Generate TCK falling edge
            #(period_ns / 2);
            vif.tck <= 0;
            
            // Sample TDO on falling edge (TDO is valid after falling edge)
            // Timing: TDO is valid t_valid after TCK falling edge
            #(1ns);  // Small delay to ensure TDO is stable
            tdo_captured[i] = vif.tdo;
            
            // Hold phase: Maintain TMS/TDI after falling edge
            // Timing: t_hold after TCK falling edge
            #(txn.hold_time_ns);
        end
        
        // Store captured TDO in transaction
        txn.actual_tdo = new[tdo_captured.size()];
        foreach (tdo_captured[i]) begin
            txn.actual_tdo[i] = tdo_captured[i];
        end
        
        // Extract TDO bits from shift states only
        extract_shift_tdo(txn);
    endtask
    
    /**
     * Drive Load IR sequence
     */
    task drive_load_ir(jtag_xtn txn);
        `uvm_info("JTAG_DRV", $sformatf("Driving Load IR: code=0x%0h, length=%0d", 
                  txn.ir_code, txn.ir_length), UVM_MEDIUM)
        drive_generic_sequence(txn);
    endtask
    
    /**
     * Drive Load DR sequence
     */
    task drive_load_dr(jtag_xtn txn);
        `uvm_info("JTAG_DRV", $sformatf("Driving Load DR: type=%s, length=%0d", 
                  txn.dr_type.name(), txn.dr_length), UVM_MEDIUM)
        drive_generic_sequence(txn);
    endtask
    
    /**
     * Drive Scan Shift sequence
     */
    task drive_scan_shift(jtag_xtn txn);
        `uvm_info("JTAG_DRV", $sformatf("Driving Scan Shift: length=%0d", 
                  txn.tdi_vector.size()), UVM_MEDIUM)
        drive_generic_sequence(txn);
    endtask
    
    /**
     * Drive Bypass sequence
     */
    task drive_bypass(jtag_xtn txn);
        `uvm_info("JTAG_DRV", "Driving Bypass sequence", UVM_MEDIUM)
        drive_generic_sequence(txn);
    endtask
    
    /**
     * Drive TDI/TDO Check sequence
     */
    task drive_tdi_tdo_check(jtag_xtn txn);
        `uvm_info("JTAG_DRV", "Driving TDI/TDO Check sequence", UVM_MEDIUM)
        drive_generic_sequence(txn);
        
        // Compare TDO after capture
        if (txn.expected_tdo.size() > 0) begin
            bit match = txn.compare_tdo();
            if (match) begin
                `uvm_info("JTAG_DRV", "TDO check PASSED", UVM_MEDIUM)
            end else begin
                `uvm_error("JTAG_DRV", $sformatf("TDO check FAILED: %0d mismatches", 
                          txn.tdo_mismatch_count))
            end
        end
    endtask
    
    // ============================================
    // TAP State Machine
    // ============================================
    
    /**
     * Update TAP state machine based on TMS value
     * 
     * Implements the complete IEEE 1149.1 TAP state machine.
     * State transitions occur on TCK rising edge when TMS is sampled.
     * 
     * @param tms TMS value sampled on rising edge
     */
    function void update_tap_state(bit tms);
        jtag_state_t next_state;
        
        case (current_state)
            // Test-Logic-Reset state
            TEST_LOGIC_RESET: begin
                // TMS=1: Stay in Test-Logic-Reset
                // TMS=0: Go to Run-Test/Idle
                next_state = tms ? TEST_LOGIC_RESET : RUN_TEST_IDLE;
            end
            
            // Run-Test/Idle state
            RUN_TEST_IDLE: begin
                // TMS=0: Stay in Run-Test/Idle
                // TMS=1: Go to Select-DR-Scan
                next_state = tms ? SELECT_DR_SCAN : RUN_TEST_IDLE;
            end
            
            // Select-DR-Scan state
            SELECT_DR_SCAN: begin
                // TMS=0: Go to Capture-DR
                // TMS=1: Go to Select-IR-Scan
                next_state = tms ? SELECT_IR_SCAN : CAPTURE_DR;
            end
            
            // Capture-DR state
            CAPTURE_DR: begin
                // TMS=0: Go to Shift-DR
                // TMS=1: Go to Exit1-DR
                next_state = tms ? EXIT1_DR : SHIFT_DR;
            end
            
            // Shift-DR state
            SHIFT_DR: begin
                // TMS=0: Stay in Shift-DR (continue shifting)
                // TMS=1: Go to Exit1-DR (end shifting)
                next_state = tms ? EXIT1_DR : SHIFT_DR;
            end
            
            // Exit1-DR state
            EXIT1_DR: begin
                // TMS=0: Go to Pause-DR
                // TMS=1: Go to Update-DR
                next_state = tms ? UPDATE_DR : PAUSE_DR;
            end
            
            // Pause-DR state
            PAUSE_DR: begin
                // TMS=0: Stay in Pause-DR
                // TMS=1: Go to Exit2-DR
                next_state = tms ? EXIT2_DR : PAUSE_DR;
            end
            
            // Exit2-DR state
            EXIT2_DR: begin
                // TMS=0: Go to Shift-DR (resume shifting)
                // TMS=1: Go to Update-DR
                next_state = tms ? UPDATE_DR : SHIFT_DR;
            end
            
            // Update-DR state
            UPDATE_DR: begin
                // TMS=0: Go to Run-Test/Idle
                // TMS=1: Go to Select-DR-Scan
                next_state = tms ? SELECT_DR_SCAN : RUN_TEST_IDLE;
            end
            
            // Select-IR-Scan state
            SELECT_IR_SCAN: begin
                // TMS=0: Go to Capture-IR
                // TMS=1: Go to Test-Logic-Reset
                next_state = tms ? TEST_LOGIC_RESET : CAPTURE_IR;
            end
            
            // Capture-IR state
            CAPTURE_IR: begin
                // TMS=0: Go to Shift-IR
                // TMS=1: Go to Exit1-IR
                next_state = tms ? EXIT1_IR : SHIFT_IR;
            end
            
            // Shift-IR state
            SHIFT_IR: begin
                // TMS=0: Stay in Shift-IR (continue shifting)
                // TMS=1: Go to Exit1-IR (end shifting)
                next_state = tms ? EXIT1_IR : SHIFT_IR;
            end
            
            // Exit1-IR state
            EXIT1_IR: begin
                // TMS=0: Go to Pause-IR
                // TMS=1: Go to Update-IR
                next_state = tms ? UPDATE_IR : PAUSE_IR;
            end
            
            // Pause-IR state
            PAUSE_IR: begin
                // TMS=0: Stay in Pause-IR
                // TMS=1: Go to Exit2-IR
                next_state = tms ? EXIT2_IR : PAUSE_IR;
            end
            
            // Exit2-IR state
            EXIT2_IR: begin
                // TMS=0: Go to Shift-IR (resume shifting)
                // TMS=1: Go to Update-IR
                next_state = tms ? UPDATE_IR : SHIFT_IR;
            end
            
            // Update-IR state
            UPDATE_IR: begin
                // TMS=0: Go to Run-Test/Idle
                // TMS=1: Go to Select-DR-Scan
                next_state = tms ? SELECT_DR_SCAN : RUN_TEST_IDLE;
            end
            
            default: begin
                `uvm_error("JTAG_DRV", $sformatf("Unknown TAP state: %s", current_state.name()))
                next_state = TEST_LOGIC_RESET;
            end
        endcase
        
        // Update current state
        if (current_state != next_state) begin
            `uvm_info("JTAG_DRV", $sformatf("TAP State: %s -> %s (TMS=%b)", 
                      current_state.name(), next_state.name(), tms), UVM_HIGH)
        end
        current_state = next_state;
    endfunction
    
    /**
     * Check if current state is a shift state
     */
    function bit is_shift_state(jtag_state_t state);
        return (state == SHIFT_DR || state == SHIFT_IR);
    endfunction
    
    /**
     * Extract TDO bits captured during shift states only
     */
    function void extract_shift_tdo(jtag_xtn txn);
        // This would extract only TDO bits from shift states
        // For now, we capture all TDO bits
        // In a more sophisticated implementation, we'd track which cycles
        // were in shift states and extract only those
    endfunction

endclass
