/**
 * Enhanced JTAG Transaction Class (IEEE 1149.1 Compliant)
 * 
 * Comprehensive transaction class for JTAG TAP controller operations.
 * Supports instruction register (IR) and data register (DR) operations,
 * scan shift sequences, and TDI/TDO verification.
 * 
 * Reference: IEEE 1149.1 Standard for Test Access Port and Boundary-Scan Architecture
 */

class jtag_xtn extends uvm_sequence_item;
    
    `uvm_object_utils(jtag_xtn)
    
    // ============================================
    // JTAG Signal Vectors
    // ============================================
    
    // TMS (Test Mode Select) vector - controls TAP state machine
    // Each bit represents TMS value for one TCK cycle
    rand bit tms_vector[];           // TMS sequence for state transitions
    
    // TDI (Test Data Input) vector - data to be shifted in
    // Length must match the register being accessed (IR or DR)
    rand bit tdi_vector[];           // TDI data to shift in
    
    // Expected TDO (Test Data Output) vector - expected response
    // Used for verification during scan operations
    bit expected_tdo[];              // Expected TDO response
    
    // Actual TDO captured during transaction
    bit actual_tdo[];                // Actual TDO captured from DUT
    
    // ============================================
    // Sequence Type
    // ============================================
    
    // Type of JTAG sequence being executed
    rand jtag_sequence_type_e sequence_type;
    
    // ============================================
    // Instruction Register (IR) Fields
    // ============================================
    
    // IR instruction code (e.g., EXTEST=0x00, SAMPLE=0x01, etc.)
    bit [31:0] ir_code;             // Instruction code to load into IR
    int ir_length = 4;               // IR length in bits (default 4 for standard JTAG)
    
    // ============================================
    // Data Register (DR) Fields
    // ============================================
    
    // DR length in bits (varies by instruction: BSR, Bypass, IDCODE, etc.)
    int dr_length = 1;                // DR length (default 1 for Bypass)
    
    // DR type identifier
    jtag_dr_type_e dr_type = DR_BYPASS;  // Type of DR being accessed
    
    // ============================================
    // Timing and Control
    // ============================================
    
    // Number of TCK cycles for this transaction
    int cycle_count;                 // Total clock cycles
    
    // Timing information structure
    time start_time;                 // Transaction start simulation time
    time end_time;                   // Transaction end simulation time
    time setup_time_ns = 10;         // TMS/TDI setup time before TCK rising edge
    time hold_time_ns = 10;          // TMS/TDI hold time after TCK falling edge
    
    // ============================================
    // State Tracking
    // ============================================
    
    // Current and next TAP controller states
    jtag_state_t start_state;        // Starting TAP state
    jtag_state_t end_state;          // Ending TAP state
    jtag_state_t current_state;      // Current state during execution
    
    // ============================================
    // Verification
    // ============================================
    
    // TDO comparison result
    bit tdo_match;                   // 1 if actual_tdo matches expected_tdo
    int tdo_mismatch_count;          // Number of mismatched bits
    
    // ============================================
    // Constraints
    // ============================================
    
    // Constraint: TMS vector length must match cycle count
    constraint tms_vector_length_c {
        tms_vector.size() == cycle_count;
    }
    
    // Constraint: TDI vector length must match DR/IR length for shift operations
    constraint tdi_vector_length_c {
        if (sequence_type == LOAD_IR) {
            // For LOAD_IR, TDI vector must match IR length
            tdi_vector.size() == ir_length;
        } else if (sequence_type == LOAD_DR) {
            // For LOAD_DR, TDI vector must match DR length
            tdi_vector.size() == dr_length;
        } else if (sequence_type == SCAN_SHIFT) {
            // For SCAN_SHIFT, TDI vector must match either DR or IR length
            // (actual length determined by is_ir flag in sequence)
            tdi_vector.size() == dr_length || tdi_vector.size() == ir_length;
        } else if (sequence_type == BYPASS || sequence_type == TAP_RESET) {
            // For BYPASS, TDI vector is typically empty or minimal (1 bit for bypass register)
            // For TAP_RESET, TDI is don't-care; 0 or 1 element is valid
            tdi_vector.size() == 0 || tdi_vector.size() == 1;
        } else if (sequence_type == TDI_TDO_CHECK) {
            // For TDI_TDO_CHECK, TDI vector length should match expected TDO length
            tdi_vector.size() == expected_tdo.size() || expected_tdo.size() == 0;
        }
    }
    
    // Constraint: Valid sequence type
    constraint valid_sequence_type_c {
        sequence_type inside {LOAD_IR, LOAD_DR, SCAN_SHIFT, BYPASS, TDI_TDO_CHECK, TAP_RESET};
    }
    
    // ============================================
    // Constructor
    // ============================================
    
    function new(string name = "jtag_xtn");
        super.new(name);
        tdo_match = 0;
        tdo_mismatch_count = 0;
        cycle_count = 1;  // Default to 1 cycle if not explicitly set
        start_state = TEST_LOGIC_RESET;
        current_state = TEST_LOGIC_RESET;
    endfunction
    
    // ============================================
    // Utility Methods
    // ============================================
    
    /**
     * Get the instruction code from IR
     * @return Instruction code as 32-bit value
     */
    function bit[31:0] get_instruction();
        bit[31:0] instr = 0;
        if (tdi_vector.size() > 0) begin
            for (int i = 0; i < tdi_vector.size() && i < 32; i++) begin
                instr[i] = tdi_vector[i];
            end
        end
        return instr;
    endfunction
    
    /**
     * Set IR instruction code
     * @param code Instruction code to set
     * @param length IR length in bits
     */
    function void set_ir_code(bit[31:0] code, int length = 4);
        ir_code = code;
        ir_length = length;
        // Allocate and populate TDI vector
        tdi_vector = new[ir_length];
        for (int i = 0; i < ir_length; i++) begin
            tdi_vector[i] = code[i];
        end
    endfunction
    
    /**
     * Get DR length based on instruction type
     * @return DR length in bits
     */
    function int get_dr_length();
        case (dr_type)
            DR_BYPASS:    return 1;
            DR_IDCODE:    return 32;
            DR_BSR:       return dr_length;  // Boundary Scan Register - variable
            DR_DEVICE_ID: return 32;
            default:      return 1;
        endcase
    endfunction
    
    /**
     * Set DR data vector
     * @param data Data to load into DR
     * @param length DR length in bits
     */
    function void set_dr_data(bit[31:0] data, int length);
        dr_length = length;
        tdi_vector = new[length];
        for (int i = 0; i < length; i++) begin
            tdi_vector[i] = data[i];
        end
    endfunction
    
    /**
     * Set expected TDO response
     * @param expected Expected TDO vector
     */
    function void set_expected_tdo(bit expected[]);
        expected_tdo = new[expected.size()];
        foreach (expected[i]) begin
            expected_tdo[i] = expected[i];
        end
    endfunction
    
    /**
     * Compare actual TDO with expected TDO
     * @return 1 if match, 0 if mismatch
     */
    function bit compare_tdo();
        tdo_match = 1;
        tdo_mismatch_count = 0;
        
        if (expected_tdo.size() == 0 || actual_tdo.size() == 0) begin
            return 0;  // No expected data to compare
        end
        
        if (expected_tdo.size() != actual_tdo.size()) begin
            `uvm_warning("JTAG_XTN", $sformatf("TDO size mismatch: expected %0d, got %0d", 
                      expected_tdo.size(), actual_tdo.size()))
            return 0;
        end
        
        foreach (expected_tdo[i]) begin
            if (expected_tdo[i] !== actual_tdo[i]) begin
                tdo_match = 0;
                tdo_mismatch_count++;
                `uvm_error("JTAG_XTN", $sformatf("TDO mismatch at bit %0d: expected %b, got %b", 
                          i, expected_tdo[i], actual_tdo[i]))
            end
        end
        
        return tdo_match;
    endfunction
    
    // ============================================
    // UVM Standard Methods
    // ============================================
    
    /**
     * Convert transaction to string for logging
     */
    function string convert2string();
        string s;
        s = $sformatf("JTAG_XTN [Type: %s]", sequence_type.name());
        s = $sformatf("%s\n  State: %s -> %s", s, start_state.name(), end_state.name());
        s = $sformatf("%s\n  Cycles: %0d", s, cycle_count);
        
        if (sequence_type == LOAD_IR) begin
            s = $sformatf("%s\n  IR Code: 0x%0h (length: %0d)", s, ir_code, ir_length);
        end
        
        if (sequence_type == LOAD_DR || sequence_type == SCAN_SHIFT) begin
            s = $sformatf("%s\n  DR Type: %s (length: %0d)", s, dr_type.name(), dr_length);
        end
        
        if (tdi_vector.size() > 0) begin
            s = $sformatf("%s\n  TDI[%0d]: ", s, tdi_vector.size());
            for (int i = tdi_vector.size()-1; i >= 0 && i >= tdi_vector.size()-8; i--) begin
                s = $sformatf("%s%b", s, tdi_vector[i]);
            end
            if (tdi_vector.size() > 8) s = $sformatf("%s...", s);
        end
        
        if (actual_tdo.size() > 0) begin
            s = $sformatf("%s\n  TDO[%0d]: ", s, actual_tdo.size());
            for (int i = actual_tdo.size()-1; i >= 0 && i >= actual_tdo.size()-8; i--) begin
                s = $sformatf("%s%b", s, actual_tdo[i]);
            end
            if (actual_tdo.size() > 8) s = $sformatf("%s...", s);
        end
        
        if (expected_tdo.size() > 0) begin
            s = $sformatf("%s\n  Expected TDO Match: %s (mismatches: %0d)", 
                         s, tdo_match ? "YES" : "NO", tdo_mismatch_count);
        end
        
        return s;
    endfunction
    
    /**
     * Copy transaction
     */
    function void do_copy(uvm_object rhs);
        jtag_xtn rhs_;
        if (!$cast(rhs_, rhs)) begin
            `uvm_fatal("COPY", "Type mismatch in jtag_xtn::do_copy")
        end
        super.do_copy(rhs);
        
        // Copy vectors
        this.tms_vector = new[rhs_.tms_vector.size()];
        foreach (rhs_.tms_vector[i]) this.tms_vector[i] = rhs_.tms_vector[i];
        
        this.tdi_vector = new[rhs_.tdi_vector.size()];
        foreach (rhs_.tdi_vector[i]) this.tdi_vector[i] = rhs_.tdi_vector[i];
        
        if (rhs_.expected_tdo.size() > 0) begin
            this.expected_tdo = new[rhs_.expected_tdo.size()];
            foreach (rhs_.expected_tdo[i]) this.expected_tdo[i] = rhs_.expected_tdo[i];
        end
        
        if (rhs_.actual_tdo.size() > 0) begin
            this.actual_tdo = new[rhs_.actual_tdo.size()];
            foreach (rhs_.actual_tdo[i]) this.actual_tdo[i] = rhs_.actual_tdo[i];
        end
        
        // Copy other fields
        this.sequence_type = rhs_.sequence_type;
        this.ir_code = rhs_.ir_code;
        this.ir_length = rhs_.ir_length;
        this.dr_length = rhs_.dr_length;
        this.dr_type = rhs_.dr_type;
        this.cycle_count = rhs_.cycle_count;
        this.start_time = rhs_.start_time;
        this.end_time = rhs_.end_time;
        this.start_state = rhs_.start_state;
        this.end_state = rhs_.end_state;
        this.current_state = rhs_.current_state;
        this.tdo_match = rhs_.tdo_match;
        this.tdo_mismatch_count = rhs_.tdo_mismatch_count;
    endfunction
    
    /**
     * Compare transactions
     */
    function bit do_compare(uvm_object rhs, uvm_comparer comparer);
        jtag_xtn rhs_;
        if (!$cast(rhs_, rhs)) return 0;
        
        // Compare key fields
        if (this.sequence_type != rhs_.sequence_type) return 0;
        if (this.ir_code != rhs_.ir_code) return 0;
        if (this.dr_length != rhs_.dr_length) return 0;
        if (this.cycle_count != rhs_.cycle_count) return 0;
        
        // Compare vectors
        if (this.tdi_vector.size() != rhs_.tdi_vector.size()) return 0;
        foreach (this.tdi_vector[i]) begin
            if (this.tdi_vector[i] != rhs_.tdi_vector[i]) return 0;
        end
        
        return 1;
    endfunction

endclass

// ============================================
// Enumerations
// ============================================

// JTAG sequence types
typedef enum {
    LOAD_IR,        // Load Instruction Register
    LOAD_DR,        // Load Data Register (BSR, Bypass, IDCODE, etc.)
    SCAN_SHIFT,     // Shift data through scan chain
    BYPASS,         // Bypass register operation
    TDI_TDO_CHECK,  // Verify TDO against expected values
    TAP_RESET       // TAP controller reset (TMS=1 for 5+ cycles)
} jtag_sequence_type_e;

// Data Register types
typedef enum {
    DR_BYPASS,      // Bypass register (1 bit)
    DR_IDCODE,      // Device ID code register (32 bits)
    DR_BSR,         // Boundary Scan Register (variable length)
    DR_DEVICE_ID,   // Device identification register
    DR_USER         // User-defined register
} jtag_dr_type_e;
