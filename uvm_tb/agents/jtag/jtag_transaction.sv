/**
 * JTAG Transaction Class
 * 
 * Represents a JTAG transaction with TMS, TDI, and expected TDO values.
 * Used for JTAG TAP controller operations and boundary scan testing.
 */

class jtag_transaction extends uvm_sequence_item;
    
    `uvm_object_utils(jtag_transaction)
    
    // JTAG Signal Values
    rand bit tms;           // Test Mode Select
    rand bit tdi;           // Test Data Input
    bit tdo;                // Test Data Output (expected or actual)
    bit tdo_expected;        // Expected TDO value for checking
    bit tdo_valid;          // Valid bit for TDO checking
    
    // Transaction Metadata
    jtag_state_t current_state;     // Current JTAG TAP state
    jtag_state_t next_state;        // Next JTAG TAP state
    jtag_instruction_t instruction;  // JTAG instruction being executed
    int cycle_count;                // Number of clock cycles for this transaction
    
    // Timing Information
    time start_time;        // Transaction start time
    time end_time;          // Transaction end time
    
    // Constraints
    constraint default_tms_c {
        // Default constraint - can be overridden
    }
    
    // Constructor
    function new(string name = "jtag_transaction");
        super.new(name);
        tdo_valid = 0;
        cycle_count = 1;
    endfunction
    
    // Convert to string for logging
    function string convert2string();
        string s;
        s = $sformatf("JTAG Transaction: TMS=%b, TDI=%b, TDO=%b", tms, tdi, tdo);
        if (tdo_valid) begin
            s = $sformatf("%s (Expected TDO=%b)", s, tdo_expected);
        end
        s = $sformatf("%s [State: %s, Cycles: %0d]", s, current_state.name(), cycle_count);
        return s;
    endfunction
    
    // Copy function
    function void do_copy(uvm_object rhs);
        jtag_transaction rhs_;
        if (!$cast(rhs_, rhs)) begin
            `uvm_fatal("COPY", "Type mismatch in jtag_transaction::do_copy")
        end
        super.do_copy(rhs);
        this.tms = rhs_.tms;
        this.tdi = rhs_.tdi;
        this.tdo = rhs_.tdo;
        this.tdo_expected = rhs_.tdo_expected;
        this.tdo_valid = rhs_.tdo_valid;
        this.current_state = rhs_.current_state;
        this.next_state = rhs_.next_state;
        this.instruction = rhs_.instruction;
        this.cycle_count = rhs_.cycle_count;
    endfunction
    
    // Compare function
    function bit do_compare(uvm_object rhs, uvm_comparer comparer);
        jtag_transaction rhs_;
        if (!$cast(rhs_, rhs)) return 0;
        return (this.tms == rhs_.tms) &&
               (this.tdi == rhs_.tdi) &&
               (this.tdo == rhs_.tdo) &&
               (this.current_state == rhs_.current_state);
    endfunction

endclass

// JTAG State Enumeration
typedef enum {
    TEST_LOGIC_RESET,
    RUN_TEST_IDLE,
    SELECT_DR_SCAN,
    CAPTURE_DR,
    SHIFT_DR,
    EXIT1_DR,
    PAUSE_DR,
    EXIT2_DR,
    UPDATE_DR,
    SELECT_IR_SCAN,
    CAPTURE_IR,
    SHIFT_IR,
    EXIT1_IR,
    PAUSE_IR,
    EXIT2_IR,
    UPDATE_IR
} jtag_state_t;

// JTAG Instruction Enumeration
typedef enum {
    BYPASS,
    IDCODE,
    SAMPLE_PRELOAD,
    EXTEST,
    INTEST,
    RUNBIST,
    CLAMP,
    HIGHZ,
    USERCODE
} jtag_instruction_t;
