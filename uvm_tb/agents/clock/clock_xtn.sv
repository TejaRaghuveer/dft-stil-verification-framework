/**
 * Clock Transaction Class
 * 
 * Enhanced transaction class for clock control in DFT test mode.
 * Supports multiple clock domains, configurable timing, and edge capture.
 */

class clock_xtn extends uvm_sequence_item;
    
    `uvm_object_utils(clock_xtn)
    
    // ============================================
    // Clock Identification
    // ============================================
    
    // Clock domain identifier (e.g., "TCK", "SYSCLK", "TESTCLK")
    string clock_id;
    
    // ============================================
    // Timing Parameters
    // ============================================
    
    // Clock frequency in MHz
    real frequency;
    
    // Duty cycle percentage (0-100)
    real duty_cycle = 50.0;
    
    // Start and stop times for clock generation
    time start_time;
    time stop_time;
    
    // Period in nanoseconds (calculated from frequency)
    real period_ns;
    
    // High and low times (calculated from period and duty cycle)
    real high_time_ns;
    real low_time_ns;
    
    // ============================================
    // Edge Control
    // ============================================
    
    // Edge event type: LEADING (rising), TRAILING (falling), BOTH
    clock_edge_type_e edge_event = BOTH;
    
    // Capture edge for data sampling
    clock_edge_type_e capture_edge = LEADING;
    
    // ============================================
    // Control
    // ============================================
    
    // Enable/disable clock
    bit clock_enable = 1;
    
    // Number of half-period clocks to generate
    int half_period_clocks = 0;
    
    // Total number of cycles generated
    int total_cycles = 0;
    
    // ============================================
    // Timing Information
    // ============================================
    
    // Transaction timing
    time transaction_start_time;
    time transaction_end_time;
    
    // ============================================
    // Constructor
    // ============================================
    
    function new(string name = "clock_xtn");
        super.new(name);
        clock_id = "DEFAULT_CLK";
        frequency = 100.0;  // Default 100MHz
        duty_cycle = 50.0;
        clock_enable = 1;
    endfunction
    
    // ============================================
    // Utility Methods
    // ============================================
    
    /**
     * Calculate period from frequency
     */
    function void calculate_period();
        if (frequency > 0) begin
            period_ns = 1000.0 / frequency;  // Convert MHz to ns
        end else begin
            `uvm_error("CLK_XTN", "Invalid frequency: must be > 0")
            period_ns = 10.0;  // Default 10ns
        end
    endfunction
    
    /**
     * Calculate high and low times from period and duty cycle
     */
    function void calculate_timing();
        calculate_period();
        high_time_ns = (period_ns * duty_cycle) / 100.0;
        low_time_ns = period_ns - high_time_ns;
    endfunction
    
    /**
     * Set number of half-period clocks
     * @param n Number of half-period clocks
     */
    function void set_half_period_clocks(int n);
        half_period_clocks = n;
    endfunction
    
    /**
     * Get total number of cycles
     * @return Total cycles (half_period_clocks / 2)
     */
    function int get_total_cycles();
        if (half_period_clocks > 0) begin
            return (half_period_clocks + 1) / 2;  // Round up
        end else begin
            return total_cycles;
        end
    endfunction
    
    /**
     * Enable clock
     */
    function void enable_clock();
        clock_enable = 1;
    endfunction
    
    /**
     * Disable clock
     */
    function void disable_clock();
        clock_enable = 0;
    endfunction
    
    // ============================================
    // UVM Standard Methods
    // ============================================
    
    /**
     * Convert to string for logging
     */
    function string convert2string();
        string s;
        s = $sformatf("Clock_XTN [ID: %s]", clock_id);
        s = $sformatf("%s\n  Frequency: %0.2f MHz", s, frequency);
        s = $sformatf("%s\n  Period: %0.2f ns", s, period_ns);
        s = $sformatf("%s\n  Duty Cycle: %0.1f%%", s, duty_cycle);
        s = $sformatf("%s\n  Edge Event: %s", s, edge_event.name());
        s = $sformatf("%s\n  Capture Edge: %s", s, capture_edge.name());
        s = $sformatf("%s\n  Enable: %0d", s, clock_enable);
        if (half_period_clocks > 0) begin
            s = $sformatf("%s\n  Half-Period Clocks: %0d", s, half_period_clocks);
        end
        s = $sformatf("%s\n  Total Cycles: %0d", s, get_total_cycles());
        return s;
    endfunction
    
    /**
     * Copy transaction
     */
    function void do_copy(uvm_object rhs);
        clock_xtn rhs_;
        if (!$cast(rhs_, rhs)) begin
            `uvm_fatal("COPY", "Type mismatch in clock_xtn::do_copy")
        end
        super.do_copy(rhs);
        
        this.clock_id = rhs_.clock_id;
        this.frequency = rhs_.frequency;
        this.duty_cycle = rhs_.duty_cycle;
        this.start_time = rhs_.start_time;
        this.stop_time = rhs_.stop_time;
        this.period_ns = rhs_.period_ns;
        this.high_time_ns = rhs_.high_time_ns;
        this.low_time_ns = rhs_.low_time_ns;
        this.edge_event = rhs_.edge_event;
        this.capture_edge = rhs_.capture_edge;
        this.clock_enable = rhs_.clock_enable;
        this.half_period_clocks = rhs_.half_period_clocks;
        this.total_cycles = rhs_.total_cycles;
    endfunction
    
    /**
     * Compare transactions
     */
    function bit do_compare(uvm_object rhs, uvm_comparer comparer);
        clock_xtn rhs_;
        if (!$cast(rhs_, rhs)) return 0;
        
        return (this.clock_id == rhs_.clock_id) &&
               (this.frequency == rhs_.frequency) &&
               (this.duty_cycle == rhs_.duty_cycle) &&
               (this.clock_enable == rhs_.clock_enable);
    endfunction

endclass

// Clock edge type enumeration
typedef enum {
    LEADING,    // Rising edge
    TRAILING,   // Falling edge
    BOTH        // Both edges
} clock_edge_type_e;
