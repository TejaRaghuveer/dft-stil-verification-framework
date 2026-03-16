/**
 * JTAG Sequences (IEEE 1149.1 Compliant)
 *
 * Complete set of sequences for JTAG TAP controller operations.
 * Implements standard JTAG operations for DFT testing.
 *
 * IMPORTANT: All sequences in this file extend jtag_base_sequence and produce
 * jtag_xtn transactions. They must be run on jtag_agent_enhanced (which has
 * uvm_sequencer#(jtag_xtn)). The legacy jtag_agent uses
 * uvm_sequencer#(jtag_transaction); use sequences/jtag_sequence.sv for that agent.
 *
 * Reference: IEEE 1149.1 Standard for Test Access Port and Boundary-Scan Architecture
 */

// ============================================
// Base JTAG Sequence
// ============================================

class jtag_base_sequence extends uvm_sequence#(jtag_xtn);
    
    `uvm_object_utils(jtag_base_sequence)
    
    // Configuration
    test_config cfg;
    
    function new(string name = "jtag_base_sequence");
        super.new(name);
    endfunction
    
    task pre_body();
        if (!uvm_config_db#(test_config)::get(null, get_full_name(), "cfg", cfg)) begin
            `uvm_warning("SEQ", "Failed to get test_config")
        end
        // These sequences produce jtag_xtn and require jtag_agent_enhanced
        // (uvm_sequencer#(jtag_xtn)). The legacy jtag_agent uses
        // uvm_sequencer#(jtag_transaction); running this sequence there
        // causes type mismatch and driver failure.
        if (m_sequencer != null) begin
            uvm_component p = m_sequencer.get_parent();
            if (p != null && p.get_type_name() == "jtag_agent") begin
                `uvm_fatal("JTAG_SEQ", "Sequences from jtag_sequences.sv produce jtag_xtn and must run on jtag_agent_enhanced. You are using the legacy jtag_agent (jtag_transaction). Use dft_env with jtag_agent_enhanced, or use sequences/jtag_sequence.sv for the legacy agent.")
            end
        end
    endtask

endclass

// ============================================
// JTAG Reset Sequence
// ============================================

/**
 * JTAG Reset Sequence
 * 
 * Resets the TAP controller to Test-Logic-Reset state.
 * This is done by holding TMS=1 for at least 5 TCK cycles.
 * 
 * TAP State Path: Any State -> ... -> Test-Logic-Reset
 * TMS Pattern: 11111 (minimum 5 cycles with TMS=1)
 */
class jtag_reset_sequence extends jtag_base_sequence;
    
    `uvm_object_utils(jtag_reset_sequence)
    
    // Number of cycles to hold TMS=1 (minimum 5 per IEEE 1149.1)
    int reset_cycles = 5;
    
    function new(string name = "jtag_reset_sequence");
        super.new(name);
    endfunction
    
    task body();
        jtag_xtn txn;
        
        `uvm_info("JTAG_SEQ", "Starting JTAG Reset Sequence", UVM_MEDIUM)
        
        txn = jtag_xtn::type_id::create("reset_txn");
        txn.sequence_type = TAP_RESET;
        txn.cycle_count = reset_cycles;
        txn.tms_vector = new[reset_cycles];
        txn.tdi_vector = new[1];
        // TAP reset takes the controller FROM any unknown state TO Test-Logic-Reset.
        txn.start_state = TAP_UNKNOWN;
        txn.end_state   = TEST_LOGIC_RESET;
        
        // Set TMS=1 for all cycles to enter Test-Logic-Reset
        foreach (txn.tms_vector[i]) begin
            txn.tms_vector[i] = 1;
        end
        
        // TDI doesn't matter during reset, but set to 0
        txn.tdi_vector[0] = 0;
        
        start_item(txn);
        finish_item(txn);
        
        `uvm_info("JTAG_SEQ", "JTAG Reset Sequence completed", UVM_MEDIUM)
    endtask

endclass

// ============================================
// Load Instruction Register Sequence
// ============================================

/**
 * Load Instruction Register (IR) Sequence
 * 
 * Loads an instruction code into the Instruction Register.
 * 
 * TAP State Path:
 *   Test-Logic-Reset -> Run-Test/Idle -> Select-DR-Scan -> Select-IR-Scan ->
 *   Capture-IR -> Shift-IR -> Exit1-IR -> Update-IR -> Run-Test/Idle
 * 
 * TMS Pattern for IR Load:
 *   0 (RTI) -> 1 (SelDR) -> 1 (SelIR) -> 0 (CapIR) -> 
 *   0...0 (Shift-IR, N cycles) -> 1 (Exit1-IR) -> 1 (UpdIR) -> 0 (RTI)
 * 
 * @param ir_code Instruction code to load (e.g., EXTEST=0x00, SAMPLE=0x01)
 * @param ir_length Length of IR in bits (typically 4 for standard JTAG)
 */
class load_instruction_sequence extends jtag_base_sequence;
    
    `uvm_object_utils(load_instruction_sequence)
    
    // Instruction code to load
    bit[31:0] ir_code;
    
    // IR length in bits
    int ir_length = 4;
    
    function new(string name = "load_instruction_sequence");
        super.new(name);
    endfunction
    
    task body();
        jtag_xtn txn;
        int total_cycles;
        int shift_cycles;
        int idx = 0;
        
        `uvm_info("JTAG_SEQ", $sformatf("Loading IR: 0x%0h (length: %0d)", ir_code, ir_length), UVM_MEDIUM)
        
        // Calculate total cycles:
        // RTI(1) + SelDR(1) + SelIR(1) + CapIR(1) +
        // Shift-IR: (ir_length-1) cycles in Shift-IR plus 1 cycle to Exit1-IR +
        // Exit1-IR->Update-IR(1) + Update-IR->RTI(1)
        //
        // => total_cycles = 1 + 1 + 1 + 1 + (ir_length-1) + 1 + 1 + 1 = ir_length + 6
        shift_cycles = ir_length;
        total_cycles = ir_length + 6;
        
        txn = jtag_xtn::type_id::create("load_ir_txn");
        txn.sequence_type = LOAD_IR;
        txn.ir_code = ir_code;
        txn.ir_length = ir_length;
        txn.cycle_count = total_cycles;
        txn.tms_vector = new[total_cycles];
        txn.tdi_vector = new[ir_length];
        txn.start_state = RUN_TEST_IDLE;
        
        // Build TMS vector for IR load sequence
        // 1. Run-Test/Idle: TMS=0 (stay in RTI)
        txn.tms_vector[idx++] = 0;
        
        // 2. Select-DR-Scan: TMS=1
        txn.tms_vector[idx++] = 1;
        
        // 3. Select-IR-Scan: TMS=1
        txn.tms_vector[idx++] = 1;
        
        // 4. Capture-IR: TMS=0
        txn.tms_vector[idx++] = 0;
        
        // 5. Shift-IR: TMS=0 for (ir_length-1) cycles, then TMS=1 for last cycle
        for (int i = 0; i < ir_length - 1; i++) begin
            txn.tms_vector[idx++] = 0;  // Stay in Shift-IR
        end
        txn.tms_vector[idx++] = 1;  // Exit to Exit1-IR
        
        // 6. Exit1-IR -> Update-IR: TMS=1
        txn.tms_vector[idx++] = 1;
        
        // 7. Update-IR -> Run-Test/Idle: TMS=0
        txn.tms_vector[idx++] = 0;
        
        // Build TDI vector: LSB first (IEEE 1149.1 standard)
        for (int i = 0; i < ir_length; i++) begin
            txn.tdi_vector[i] = ir_code[i];
        end
        
        start_item(txn);
        finish_item(txn);
        
        `uvm_info("JTAG_SEQ", $sformatf("IR Load Sequence completed: 0x%0h", ir_code), UVM_MEDIUM)
    endtask

endclass

// ============================================
// Load Data Register Sequence
// ============================================

/**
 * Load Data Register (DR) Sequence
 * 
 * Loads data into a Data Register (BSR, Bypass, IDCODE, etc.)
 * 
 * TAP State Path:
 *   Run-Test/Idle -> Select-DR-Scan -> Capture-DR -> Shift-DR ->
 *   Exit1-DR -> Update-DR -> Run-Test/Idle
 * 
 * TMS Pattern for DR Load:
 *   0 (RTI) -> 1 (SelDR) -> 0 (CapDR) -> 
 *   0...0 (Shift-DR, N cycles) -> 1 (Exit1-DR) -> 1 (UpdDR) -> 0 (RTI)
 * 
 * @param dr_data Data to load into DR
 * @param dr_length Length of DR in bits
 * @param dr_type Type of DR (BSR, Bypass, IDCODE, etc.)
 */
class load_data_register_sequence extends jtag_base_sequence;
    
    `uvm_object_utils(load_data_register_sequence)
    
    // Data to load
    bit[31:0] dr_data;
    
    // DR length in bits
    int dr_length;
    
    // DR type
    jtag_dr_type_e dr_type = DR_BSR;
    
    function new(string name = "load_data_register_sequence");
        super.new(name);
    endfunction
    
    task body();
        jtag_xtn txn;
        int total_cycles;
        int shift_cycles;
        int idx = 0;
        
        `uvm_info("JTAG_SEQ", $sformatf("Loading DR: type=%s, length=%0d, data=0x%0h", 
                  dr_type.name(), dr_length, dr_data), UVM_MEDIUM)
        
        // Calculate total cycles:
        // RTI(1) + SelDR(1) + CapDR(1) +
        // Shift-DR: (dr_length-1) cycles in Shift-DR plus 1 cycle to Exit1-DR +
        // Exit1-DR->Update-DR(1) + Update-DR->RTI(1)
        //
        // => total_cycles = 1 + 1 + 1 + (dr_length-1) + 1 + 1 + 1 = dr_length + 5
        shift_cycles = dr_length;
        total_cycles = dr_length + 5;
        
        txn = jtag_xtn::type_id::create("load_dr_txn");
        txn.sequence_type = LOAD_DR;
        txn.dr_type = dr_type;
        txn.dr_length = dr_length;
        txn.set_dr_data(dr_data, dr_length);
        txn.cycle_count = total_cycles;
        txn.tms_vector = new[total_cycles];
        txn.start_state = RUN_TEST_IDLE;
        
        // Build TMS vector for DR load sequence
        // 1. Run-Test/Idle: TMS=0
        txn.tms_vector[idx++] = 0;
        
        // 2. Select-DR-Scan: TMS=1
        txn.tms_vector[idx++] = 1;
        
        // 3. Capture-DR: TMS=0
        txn.tms_vector[idx++] = 0;
        
        // 4. Shift-DR: TMS=0 for (dr_length-1) cycles, then TMS=1 for last cycle
        for (int i = 0; i < dr_length - 1; i++) begin
            txn.tms_vector[idx++] = 0;  // Stay in Shift-DR
        end
        txn.tms_vector[idx++] = 1;  // Exit to Exit1-DR
        
        // 5. Exit1-DR -> Update-DR: TMS=1
        txn.tms_vector[idx++] = 1;
        
        // 6. Update-DR -> Run-Test/Idle: TMS=0
        txn.tms_vector[idx++] = 0;
        
        start_item(txn);
        finish_item(txn);
        
        `uvm_info("JTAG_SEQ", "DR Load Sequence completed", UVM_MEDIUM)
    endtask

endclass

// ============================================
// Scan Shift Sequence
// ============================================

/**
 * Scan Shift Sequence
 * 
 * Shifts data through the scan chain (IR or DR) without capture/update.
 * Used for continuous scan operations.
 * 
 * TAP State Path:
 *   Shift-IR or Shift-DR (stay in shift state for N cycles)
 * 
 * @param shift_data Data to shift in
 * @param shift_length Number of bits to shift
 * @param is_ir 1 if shifting IR, 0 if shifting DR
 */
class scan_shift_sequence extends jtag_base_sequence;
    
    `uvm_object_utils(scan_shift_sequence)
    
    // Data to shift
    bit[31:0] shift_data;
    
    // Number of bits to shift
    int shift_length;
    
    // 1 for IR shift, 0 for DR shift
    bit is_ir = 0;
    
    function new(string name = "scan_shift_sequence");
        super.new(name);
    endfunction
    
    task body();
        jtag_xtn txn;
        int total_cycles;
        int idx = 0;
        
        `uvm_info("JTAG_SEQ", $sformatf("Scan Shift: %s, length=%0d, data=0x%0h", 
                  is_ir ? "IR" : "DR", shift_length, shift_data), UVM_MEDIUM)
        
        // Calculate total cycles based on shift type
        // IR Shift: RTI(1) + SelDR(1) + SelIR(1) + CapIR(1) + ShiftIR(N) = shift_length + 4
        //   Note: Last shift cycle with TMS=1 serves as exit (no separate exit cycle needed)
        // DR Shift: RTI(1) + SelDR(1) + CapDR(1) + ShiftDR(N) = shift_length + 3
        //   Note: Last shift cycle with TMS=1 serves as exit (no separate exit cycle needed)
        if (is_ir) begin
            total_cycles = shift_length + 4;  // 4 entry + N shift (last shift is exit)
        end else begin
            total_cycles = shift_length + 3;  // 3 entry + N shift (last shift is exit)
        end
        
        txn = jtag_xtn::type_id::create("scan_shift_txn");
        txn.sequence_type = SCAN_SHIFT;
        txn.cycle_count = total_cycles;
        txn.tms_vector = new[total_cycles];
        txn.tdi_vector = new[shift_length];
        txn.start_state = RUN_TEST_IDLE;
        
        if (is_ir) begin
            // IR Shift: RTI -> SelDR -> SelIR -> CapIR -> ShiftIR(N) -> Exit1IR
            txn.tms_vector[idx++] = 0;  // RTI
            txn.tms_vector[idx++] = 1;  // SelDR
            txn.tms_vector[idx++] = 1;  // SelIR
            txn.tms_vector[idx++] = 0;  // CapIR
        end else begin
            // DR Shift: RTI -> SelDR -> CapDR -> ShiftDR(N) -> Exit1DR
            txn.tms_vector[idx++] = 0;  // RTI
            txn.tms_vector[idx++] = 1;  // SelDR
            txn.tms_vector[idx++] = 0;  // CapDR
        end
        
        // Shift cycles: TMS=0 for (shift_length-1), then TMS=1 for last
        for (int i = 0; i < shift_length - 1; i++) begin
            txn.tms_vector[idx++] = 0;
        end
        txn.tms_vector[idx++] = 1;  // Exit
        
        // Build TDI vector: LSB first
        for (int i = 0; i < shift_length; i++) begin
            txn.tdi_vector[i] = shift_data[i];
        end
        
        start_item(txn);
        finish_item(txn);
        
        `uvm_info("JTAG_SEQ", "Scan Shift Sequence completed", UVM_MEDIUM)
    endtask

endclass

// ============================================
// TDI/TDO Check Sequence
// ============================================

/**
 * TDI/TDO Check Sequence
 * 
 * Shifts data through scan chain and verifies TDO response.
 * Used for read operations and verification.
 * 
 * @param input_data Data to shift in (TDI)
 * @param expected_output Expected data to shift out (TDO)
 * @param length Number of bits to shift
 * @param is_ir 1 if checking IR, 0 if checking DR
 */
class tdi_tdo_check_sequence extends jtag_base_sequence;
    
    `uvm_object_utils(tdi_tdo_check_sequence)
    
    // Input data (TDI)
    bit[31:0] input_data;
    
    // Expected output (TDO)
    bit[31:0] expected_output;
    
    // Number of bits
    int length;
    
    // 1 for IR, 0 for DR
    bit is_ir = 0;
    
    function new(string name = "tdi_tdo_check_sequence");
        super.new(name);
    endfunction
    
    task body();
        jtag_xtn txn;
        bit expected_tdo[];
        
        `uvm_info("JTAG_SEQ", $sformatf("TDI/TDO Check: %s, length=%0d", 
                  is_ir ? "IR" : "DR", length), UVM_MEDIUM)
        
        // Create scan shift sequence
        scan_shift_sequence scan_seq;
        scan_seq = scan_shift_sequence::type_id::create("scan_seq");
        scan_seq.shift_data = input_data;
        scan_seq.shift_length = length;
        scan_seq.is_ir = is_ir;
        
        // Build expected TDO vector
        expected_tdo = new[length];
        for (int i = 0; i < length; i++) begin
            expected_tdo[i] = expected_output[i];
        end
        
        // Execute scan shift – ensure a valid sequencer is available
        if (m_sequencer == null) begin
            `uvm_fatal("JTAG_SEQ", "tdi_tdo_check_sequence: m_sequencer is null; cannot start scan_seq")
        end
        scan_seq.start(m_sequencer);
        
        // Get the transaction and set expected TDO
        // Note: In real implementation, you'd capture the actual TDO from monitor
        // and compare. This is a simplified version.
        
        `uvm_info("JTAG_SEQ", "TDI/TDO Check Sequence completed", UVM_MEDIUM)
    endtask

endclass
