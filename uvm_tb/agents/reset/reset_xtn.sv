/**
 * Reset Transaction Class
 * 
 * Enhanced transaction class for reset control in DFT test mode.
 * Supports asynchronous and synchronous resets with glitch prevention.
 */

class reset_xtn extends uvm_sequence_item;
    
    `uvm_object_utils(reset_xtn)
    
    // ============================================
    // Reset Type
    // ============================================
    
    // Reset type: ASYNC or SYNC
    reset_type_e reset_type = SYNC;
    
    // Reset pin identifier (e.g., "RST_N", "POR", "TRST_N")
    string reset_pin;
    
    // ============================================
    // Timing Parameters
    // ============================================
    
    // Reset duration in nanoseconds
    time duration;
    
    // Delay from clock edge for synchronous reset
    time delay_from_clock = 0;
    
    // ============================================
    // Polarity
    // ============================================
    
    // Reset polarity: ACTIVE_HIGH or ACTIVE_LOW
    reset_polarity_e polarity = ACTIVE_LOW;
    
    // ============================================
    // Control
    // ============================================
    
    // Assert reset flag
    bit assert_reset = 1;
    
    // Prevent glitches during scan mode
    bit prevent_glitches = 1;
    
    // ============================================
    // Status
    // ============================================
    
    // Reset status: asserted or deasserted
    bit reset_status = 0;
    
    // Transaction timing
    time transaction_start_time;
    time transaction_end_time;
    
    // ============================================
    // Constructor
    // ============================================
    
    function new(string name = "reset_xtn");
        super.new(name);
        reset_pin = "RST_N";
        reset_type = SYNC;
        polarity = ACTIVE_LOW;
        duration = 100ns;
        assert_reset = 1;
        prevent_glitches = 1;
    endfunction
    
    // ============================================
    // Utility Methods
    // ============================================
    
    /**
     * Get reset value based on polarity
     * @return Reset value (1 for active high, 0 for active low)
     */
    function bit get_reset_value();
        return (polarity == ACTIVE_HIGH) ? 1 : 0;
    endfunction
    
    /**
     * Get deassert value based on polarity
     * @return Deassert value (0 for active high, 1 for active low)
     */
    function bit get_deassert_value();
        return (polarity == ACTIVE_HIGH) ? 0 : 1;
    endfunction
    
    /**
     * Check if reset is active
     * @param current_value Current reset signal value
     * @return 1 if reset is active, 0 otherwise
     */
    function bit is_reset_active(bit current_value);
        if (polarity == ACTIVE_HIGH) begin
            return (current_value == 1);
        end else begin
            return (current_value == 0);
        end
    endfunction
    
    // ============================================
    // UVM Standard Methods
    // ============================================
    
    /**
     * Convert to string for logging
     */
    function string convert2string();
        string s;
        s = $sformatf("Reset_XTN [Pin: %s]", reset_pin);
        s = $sformatf("%s\n  Type: %s", s, reset_type.name());
        s = $sformatf("%s\n  Polarity: %s", s, polarity.name());
        s = $sformatf("%s\n  Duration: %0t ns", s, duration);
        s = $sformatf("%s\n  Assert: %0d", s, assert_reset);
        s = $sformatf("%s\n  Prevent Glitches: %0d", s, prevent_glitches);
        if (reset_type == SYNC) begin
            s = $sformatf("%s\n  Delay from Clock: %0t ns", s, delay_from_clock);
        end
        return s;
    endfunction
    
    /**
     * Copy transaction
     */
    function void do_copy(uvm_object rhs);
        reset_xtn rhs_;
        if (!$cast(rhs_, rhs)) begin
            `uvm_fatal("COPY", "Type mismatch in reset_xtn::do_copy")
        end
        super.do_copy(rhs);
        
        this.reset_type = rhs_.reset_type;
        this.reset_pin = rhs_.reset_pin;
        this.duration = rhs_.duration;
        this.delay_from_clock = rhs_.delay_from_clock;
        this.polarity = rhs_.polarity;
        this.assert_reset = rhs_.assert_reset;
        this.prevent_glitches = rhs_.prevent_glitches;
        this.reset_status = rhs_.reset_status;
    endfunction
    
    /**
     * Compare transactions
     */
    function bit do_compare(uvm_object rhs, uvm_comparer comparer);
        reset_xtn rhs_;
        if (!$cast(rhs_, rhs)) return 0;
        
        return (this.reset_pin == rhs_.reset_pin) &&
               (this.reset_type == rhs_.reset_type) &&
               (this.polarity == rhs_.polarity) &&
               (this.duration == rhs_.duration) &&
               (this.assert_reset == rhs_.assert_reset);
    endfunction

endclass

// Reset type enumeration
typedef enum {
    ASYNC,  // Asynchronous reset
    SYNC    // Synchronous reset
} reset_type_e;

// Reset polarity enumeration
typedef enum {
    ACTIVE_HIGH,  // Reset active when signal is high
    ACTIVE_LOW    // Reset active when signal is low
} reset_polarity_e;
