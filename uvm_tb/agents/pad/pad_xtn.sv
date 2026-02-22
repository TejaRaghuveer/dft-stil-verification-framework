/**
 * Pad Transaction Class
 *
 * Transaction class for DFT primary input/output control and observation.
 * Supports configurable timing, drive strength, and multi-bit vectors.
 */

class pad_xtn extends uvm_sequence_item;

    `uvm_object_utils(pad_xtn)

    // ============================================
    // Signal Identification
    // ============================================

    // Signal/pad name (e.g., "PI_0", "PO_1", "PIO_2")
    string signal_name;

    // Signal direction: INPUT, OUTPUT, BIDIR
    pad_signal_type_e signal_type = INPUT;

    // ============================================
    // Data and Timing
    // ============================================

    // Data value (single-bit or packed for multi-bit)
    logic [63:0] data_value;

    // Width of valid data (1 to 64 bits)
    int data_width = 1;

    // Timing offset from reference (e.g., clock edge) in ns
    time timing_offset = 0;

    // Setup time before reference edge (ns)
    time setup_time_ns = 1;

    // Hold time after reference edge (ns)
    time hold_time_ns = 1;

    // Propagation delay for output (ns)
    time delay_ns = 0;

    // ============================================
    // Drive Characteristics
    // ============================================

    // Drive strength: STRONG, WEAK, TRI_STATE
    pad_drive_strength_e drive_strength = STRONG;

    // Slew rate: SLOW, NORMAL, FAST (for timing modeling)
    pad_slew_rate_e slew_rate = NORMAL;

    // ============================================
    // Stimulus Type
    // ============================================

    // COMBINATIONAL or SEQUENTIAL (scan)
    pad_stimulus_type_e stimulus_type = COMBINATIONAL;

    // ============================================
    // Expected Response (for outputs)
    // ============================================

    // Expected value for comparison
    logic [63:0] expected_response;

    // Mask for comparison (1 = compare, 0 = don't care)
    logic [63:0] compare_mask = '1;

    // ============================================
    // Metadata
    // ============================================

    time transaction_time;
    int signal_id = -1;  // Index from signal list

    // ============================================
    // Constructor
    // ============================================

    function new(string name = "pad_xtn");
        super.new(name);
        signal_name = "PAD";
    endfunction

    // ============================================
    // Utility Methods
    // ============================================

    /**
     * Get signal identifier (index). Set by agent from config.
     */
    function int get_signal_id();
        return signal_id;
    endfunction

    /**
     * Set signal ID
     */
    function void set_signal_id(int id);
        signal_id = id;
    endfunction

    /**
     * Return 1 if this pad is an input (drive from TB to DUT).
     */
    function bit is_input();
        return (signal_type == INPUT || signal_type == BIDIR);
    endfunction

    /**
     * Return 1 if this pad is an output (observe from DUT).
     */
    function bit is_output();
        return (signal_type == OUTPUT || signal_type == BIDIR);
    endfunction

    /**
     * Set drive timing (setup/hold/delay).
     */
    function void set_drive_timing(time setup_ns, time hold_ns, time prop_delay_ns);
        setup_time_ns = setup_ns;
        hold_time_ns = hold_ns;
        delay_ns = prop_delay_ns;
    endfunction

    /**
     * Get expected response value (for output comparison).
     */
    function logic[63:0] get_expected_response();
        return expected_response;
    endfunction

    /**
     * Set expected response and optional mask.
     */
    function void set_expected_response(logic[63:0] expected, logic[63:0] mask);
        expected_response = expected;
        if (mask != 0) compare_mask = mask;
    endfunction

    // ============================================
    // UVM Standard Methods
    // ============================================

    function string convert2string();
        string s;
        s = $sformatf("Pad_XTN [%s] type=%s", signal_name, signal_type.name());
        s = $sformatf("%s data=0x%x (width=%0d)", s, data_value, data_width);
        s = $sformatf("%s drive=%s slew=%s", s, drive_strength.name(), slew_rate.name());
        s = $sformatf("%s stimulus=%s", s, stimulus_type.name());
        if (is_output())
            s = $sformatf("%s expected=0x%x", s, expected_response);
        return s;
    endfunction

    function void do_copy(uvm_object rhs);
        pad_xtn rhs_;
        if (!$cast(rhs_, rhs)) begin
            `uvm_fatal("COPY", "Type mismatch in pad_xtn::do_copy")
        end
        super.do_copy(rhs);
        this.signal_name = rhs_.signal_name;
        this.signal_type = rhs_.signal_type;
        this.data_value = rhs_.data_value;
        this.data_width = rhs_.data_width;
        this.timing_offset = rhs_.timing_offset;
        this.setup_time_ns = rhs_.setup_time_ns;
        this.hold_time_ns = rhs_.hold_time_ns;
        this.delay_ns = rhs_.delay_ns;
        this.drive_strength = rhs_.drive_strength;
        this.slew_rate = rhs_.slew_rate;
        this.stimulus_type = rhs_.stimulus_type;
        this.expected_response = rhs_.expected_response;
        this.compare_mask = rhs_.compare_mask;
        this.signal_id = rhs_.signal_id;
    endfunction

    function bit do_compare(uvm_object rhs, uvm_comparer comparer);
        pad_xtn rhs_;
        if (!$cast(rhs_, rhs)) return 0;
        if (this.signal_name != rhs_.signal_name) return 0;
        if (this.data_value != rhs_.data_value) return 0;
        if (this.expected_response != rhs_.expected_response) return 0;
        return 1;
    endfunction

endclass

// Signal type enumeration
typedef enum { INPUT, OUTPUT, BIDIR } pad_signal_type_e;

// Drive strength enumeration
typedef enum { STRONG, WEAK, TRI_STATE } pad_drive_strength_e;

// Slew rate enumeration
typedef enum { SLOW, NORMAL, FAST } pad_slew_rate_e;

// Stimulus type enumeration
typedef enum { COMBINATIONAL, SEQUENTIAL } pad_stimulus_type_e;
