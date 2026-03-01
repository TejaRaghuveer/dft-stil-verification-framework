/**
 * Enhanced JTAG Monitor (IEEE 1149.1 Compliant)
 * 
 * Monitors JTAG interface signals and reconstructs JTAG transactions.
 * Tracks TAP state machine transitions and captures TDI/TDO data.
 * 
 * The monitor:
 * 1. Observes TCK, TMS, TDI, TDO signal transitions
 * 2. Tracks TAP state machine state
 * 3. Reconstructs transactions based on state transitions
 * 4. Publishes transactions via analysis port
 * 
 * Reference: IEEE 1149.1 Standard for Test Access Port and Boundary-Scan Architecture
 */

class jtag_monitor_enhanced extends uvm_monitor;
    
    `uvm_component_utils(jtag_monitor_enhanced)
    
    // Virtual interface
    virtual jtag_if vif;
    
    // Analysis port for publishing transactions
    uvm_analysis_port#(jtag_xtn) analysis_port;
    
    // Configuration
    test_config cfg;
    
    // TAP state tracking
    jtag_state_t current_state;
    jtag_state_t prev_state;
    
    // Signal history for transaction reconstruction
    bit tms_history[];
    bit tdi_history[];      // full-cycle TDI history (debug / TMS alignment)
    bit tdo_history[];      // full-cycle TDO history (debug)

    // Shift-only bit histories (aligned TDI/TDO per shift cycle)
    bit shift_tdi_bits[];
    bit shift_tdo_bits[];
    bit last_tdi_sampled;
    
    // Transaction reconstruction state
    bit in_shift_state = 0;
    jtag_sequence_type_e detected_sequence_type;
    int shift_bit_count = 0;
    
    // Constructor
    function new(string name = "jtag_monitor_enhanced", uvm_component parent = null);
        super.new(name, parent);
        analysis_port = new("analysis_port", this);
        current_state = TEST_LOGIC_RESET;
        prev_state = TEST_LOGIC_RESET;
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        if (!uvm_config_db#(virtual jtag_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("NO_VIF", "Failed to get jtag_if from config_db")
        end
        
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config")
        end
    endfunction
    
    // Run phase - monitor loop
    task run_phase(uvm_phase phase);
        monitor_jtag();
    endtask
    
    /**
     * Main monitoring task
     * 
     * Monitors TCK edges and captures TMS, TDI, TDO values.
     * Reconstructs transactions based on TAP state transitions.
     */
    task monitor_jtag();
        bit prev_tck = 0;
        bit curr_tck;
        bit tms_val, tdi_val, tdo_val;
        int cycle_count = 0;
        
        `uvm_info("JTAG_MON", "Starting JTAG monitoring", UVM_MEDIUM)
        
        // Initialize signal history arrays
        tms_history      = new[0];
        tdi_history      = new[0];
        tdo_history      = new[0];
        shift_tdi_bits   = new[0];
        shift_tdo_bits   = new[0];
        last_tdi_sampled = 0;
        
        forever begin
            // Wait for TCK edge (monitor on both edges for complete capture)
            @(vif.tck);
            
            curr_tck = vif.tck;
            
            // Sample signals on TCK rising edge (TMS/TDI sampled, TDO valid)
            if (curr_tck && !prev_tck) begin
                // Rising edge: TMS and TDI are sampled here
                tms_val = vif.tms;
                tdi_val = vif.tdi;
                
                // Update TAP state machine
                prev_state = current_state;
                update_monitor_tap_state(tms_val);
                
                // Record signal values
                tms_history = new[tms_history.size() + 1](tms_history);
                tms_history[tms_history.size() - 1] = tms_val;
                
                tdi_history = new[tdi_history.size() + 1](tdi_history);
                tdi_history[tdi_history.size() - 1] = tdi_val;

                // Remember last TDI value for this cycle; it will be paired
                // with TDO on the subsequent falling edge if in shift state.
                last_tdi_sampled = tdi_val;
                
                cycle_count++;
                
                // Detect sequence type based on state transitions
                detect_sequence_type();
                
                // Check if we should reconstruct a transaction
                if (should_reconstruct_transaction()) begin
                    reconstruct_transaction(cycle_count);
                    cycle_count = 0;
                end
            end
            
            // Sample TDO on TCK falling edge (TDO is valid after falling edge)
            if (!curr_tck && prev_tck) begin
                // Falling edge: TDO is valid here
                #(1ns);  // Small delay to ensure TDO is stable
                tdo_val = vif.tdo;
                
                // Record TDO value
                tdo_history = new[tdo_history.size() + 1](tdo_history);
                tdo_history[tdo_history.size() - 1] = tdo_val;
                
                // Track shift state for TDO capture and build aligned
                // shift-only vectors.
                if (is_shift_state(current_state)) begin
                    in_shift_state = 1;
                    shift_bit_count++;
                    // Capture one aligned bit of TDI/TDO per shift cycle
                    shift_tdi_bits = new[shift_tdi_bits.size() + 1](shift_tdi_bits);
                    shift_tdi_bits[shift_tdi_bits.size() - 1] = last_tdi_sampled;
                    shift_tdo_bits = new[shift_tdo_bits.size() + 1](shift_tdo_bits);
                    shift_tdo_bits[shift_tdo_bits.size() - 1] = tdo_val;
                end else begin
                    if (in_shift_state) begin
                        // Exited shift state, may need to reconstruct
                        in_shift_state = 0;
                    end
                end
            end
            
            prev_tck = curr_tck;
        end
    endtask
    
    /**
     * Update TAP state machine in monitor
     * 
     * Tracks TAP state based on TMS transitions (same logic as driver)
     */
    function void update_monitor_tap_state(bit tms);
        jtag_state_t next_state;
        
        case (current_state)
            TEST_LOGIC_RESET: next_state = tms ? TEST_LOGIC_RESET : RUN_TEST_IDLE;
            RUN_TEST_IDLE: next_state = tms ? SELECT_DR_SCAN : RUN_TEST_IDLE;
            SELECT_DR_SCAN: next_state = tms ? SELECT_IR_SCAN : CAPTURE_DR;
            CAPTURE_DR: next_state = tms ? EXIT1_DR : SHIFT_DR;
            SHIFT_DR: next_state = tms ? EXIT1_DR : SHIFT_DR;
            EXIT1_DR: next_state = tms ? UPDATE_DR : PAUSE_DR;
            PAUSE_DR: next_state = tms ? EXIT2_DR : PAUSE_DR;
            EXIT2_DR: next_state = tms ? UPDATE_DR : SHIFT_DR;
            UPDATE_DR: next_state = tms ? SELECT_DR_SCAN : RUN_TEST_IDLE;
            SELECT_IR_SCAN: next_state = tms ? TEST_LOGIC_RESET : CAPTURE_IR;
            CAPTURE_IR: next_state = tms ? EXIT1_IR : SHIFT_IR;
            SHIFT_IR: next_state = tms ? EXIT1_IR : SHIFT_IR;
            EXIT1_IR: next_state = tms ? UPDATE_IR : PAUSE_IR;
            PAUSE_IR: next_state = tms ? EXIT2_IR : PAUSE_IR;
            EXIT2_IR: next_state = tms ? UPDATE_IR : SHIFT_IR;
            UPDATE_IR: next_state = tms ? SELECT_DR_SCAN : RUN_TEST_IDLE;
            default: next_state = TEST_LOGIC_RESET;
        endcase
        
        if (current_state != next_state) begin
            `uvm_info("JTAG_MON", $sformatf("TAP State: %s -> %s (TMS=%b)", 
                      current_state.name(), next_state.name(), tms), UVM_HIGH)
        end
        current_state = next_state;
    endfunction
    
    /**
     * Detect sequence type based on state transitions
     */
    function void detect_sequence_type();
        // Detect sequence type based on state path
        if (prev_state == SELECT_IR_SCAN && current_state == CAPTURE_IR) begin
            detected_sequence_type = LOAD_IR;
        end else if (prev_state == SELECT_DR_SCAN && current_state == CAPTURE_DR) begin
            detected_sequence_type = LOAD_DR;
        end else if (current_state == SHIFT_DR || current_state == SHIFT_IR) begin
            detected_sequence_type = SCAN_SHIFT;
        end else if (current_state == TEST_LOGIC_RESET && prev_state != TEST_LOGIC_RESET) begin
            // Only classify as TAP_RESET when we have just entered TLR (reset sequence).
            // Excluding prev_state == TEST_LOGIC_RESET avoids misclassifying the exit-from-TLR
            // cycle or leaving detected_sequence_type stuck as TAP_RESET for later sequences.
            detected_sequence_type = TAP_RESET;
        end
    endfunction
    
    /**
     * Check if current state is a shift state
     */
    function bit is_shift_state(jtag_state_t state);
        return (state == SHIFT_DR || state == SHIFT_IR);
    endfunction
    
    /**
     * Determine if we should reconstruct a transaction
     * 
     * Reconstruct when:
     * - Completed an IR load (Update-IR state)
     * - Completed a DR load (Update-DR state)
     * - Completed a scan shift (Exit from shift state)
     * - Entered Test-Logic-Reset (reset sequence)
     */
    function bit should_reconstruct_transaction();
        // Reconstruct on Update states (end of load sequences)
        if (current_state == UPDATE_IR || current_state == UPDATE_DR) begin
            return 1;
        end
        
        // Reconstruct when exiting shift state
        if (prev_state == SHIFT_DR && current_state != SHIFT_DR) begin
            return 1;
        end
        if (prev_state == SHIFT_IR && current_state != SHIFT_IR) begin
            return 1;
        end
        
        // Reconstruct on reset
        if (current_state == TEST_LOGIC_RESET && prev_state != TEST_LOGIC_RESET) begin
            return 1;
        end
        
        return 0;
    endfunction
    
    /**
     * Reconstruct transaction from monitored signals
     */
    function void reconstruct_transaction(int cycles);
        jtag_xtn txn;
        int shift_bits = 0;
        bit tdi_shift_data[];
        bit tdo_shift_data[];
        
        txn = jtag_xtn::type_id::create("monitored_txn");
        txn.sequence_type = detected_sequence_type;
        txn.cycle_count = cycles;
        txn.start_state = prev_state;
        txn.end_state = current_state;
        
        // Copy TMS vector
        txn.tms_vector = new[tms_history.size()];
        foreach (tms_history[i]) begin
            txn.tms_vector[i] = tms_history[i];
        end
        
        // Extract TDI and TDO from shift states
        if (detected_sequence_type == LOAD_IR || detected_sequence_type == SCAN_SHIFT) begin
            // Extract IR length from shift cycles
            // Count consecutive Shift-IR states
            shift_bits = shift_bit_count;
            tdi_shift_data = new[shift_bits];
            tdo_shift_data = new[shift_bits];
            
            // Use aligned shift-only histories so that each index corresponds
            // to a single shift cycle (TDI sampled on rising edge, TDO on
            // the following falling edge of the same cycle).
            for (int i = 0; i < shift_bits && i < shift_tdi_bits.size(); i++) begin
                tdi_shift_data[i] = shift_tdi_bits[i];
            end
            for (int i = 0; i < shift_bits && i < shift_tdo_bits.size(); i++) begin
                tdo_shift_data[i] = shift_tdo_bits[i];
            end
            
            txn.tdi_vector = tdi_shift_data;
            txn.actual_tdo = tdo_shift_data;
            
            if (detected_sequence_type == LOAD_IR) begin
                txn.ir_length = shift_bits;
                txn.ir_code = txn.get_instruction();
            end
        end else if (detected_sequence_type == LOAD_DR) begin
            // Extract DR data using the same aligned shift-only histories
            shift_bits = shift_bit_count;
            tdi_shift_data = new[shift_bits];
            tdo_shift_data = new[shift_bits];
            
            for (int i = 0; i < shift_bits && i < shift_tdi_bits.size(); i++) begin
                tdi_shift_data[i] = shift_tdi_bits[i];
            end
            for (int i = 0; i < shift_bits && i < shift_tdo_bits.size(); i++) begin
                tdo_shift_data[i] = shift_tdo_bits[i];
            end
            
            txn.tdi_vector = tdi_shift_data;
            txn.actual_tdo = tdo_shift_data;
            txn.dr_length = shift_bits;
        end
        
        // Reset shift tracking
        shift_bit_count = 0;
        in_shift_state  = 0;
        shift_tdi_bits.delete();
        shift_tdo_bits.delete();
        
        // Clear history for next transaction
        tms_history.delete();
        tdi_history.delete();
        tdo_history.delete();
        
        `uvm_info("JTAG_MON", $sformatf("Reconstructed transaction:\n%s", txn.convert2string()), UVM_MEDIUM)
        
        // Publish transaction
        analysis_port.write(txn);
    endfunction

endclass
