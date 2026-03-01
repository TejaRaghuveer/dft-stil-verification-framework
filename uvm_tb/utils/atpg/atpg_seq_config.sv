/**
 * ATPG Sequence Configuration
 *
 * Configuration options for converting ATPG patterns into executable UVM sequences:
 * - Scan shift timing (TCK frequency, duty cycle)
 * - Capture edge and primary I/O timing
 * - Pattern execution mode and result checking
 */

typedef enum {
    ATPG_CAPTURE_LEADING_EDGE,
    ATPG_CAPTURE_TRAILING_EDGE
} atpg_capture_edge_e;

typedef enum {
    ATPG_ORDER_SEQUENTIAL,
    ATPG_ORDER_RANDOM
} atpg_pattern_order_e;

typedef enum {
    ATPG_CHECK_ON_THE_FLY,
    ATPG_CHECK_END_OF_TEST
} atpg_result_check_e;

class atpg_seq_config extends uvm_object;
    `uvm_object_utils(atpg_seq_config)

    // Scan shift timing
    int scan_tck_period_ns     = 100;   // TCK period for scan shift (default 10 MHz)
    int scan_tck_duty_cycle_pct = 50;  // Duty cycle percentage
    int scan_setup_ns          = 10;   // TMS/TDI setup before TCK
    int scan_hold_ns           = 10;   // TMS/TDI hold after TCK

    // Capture
    atpg_capture_edge_e capture_edge = ATPG_CAPTURE_TRAILING_EDGE;
    int capture_cycles         = 1;    // Operational clock cycles during capture

    // Primary I/O timing (relative to clock edge)
    int primary_setup_ns       = 2;    // PI setup before clock
    int primary_hold_ns        = 2;    // PI hold after clock
    int primary_capture_delay_ns = 5;  // Delay before sampling PO

    // Pattern execution
    atpg_pattern_order_e pattern_order = ATPG_ORDER_SEQUENTIAL;
    atpg_result_check_e result_check   = ATPG_CHECK_ON_THE_FLY;
    bit reset_between_patterns  = 0;   // Apply TAP reset between patterns
    bit restart_on_failure       = 0;   // Restart pattern on mismatch (debug)

    // Test mode instruction (e.g. EXTEST = 0)
    bit [31:0] test_mode_ir    = 32'h00;  // EXTEST
    int ir_length              = 4;
    int dr_length              = 256;    // BSR length; set from DUT

    // Logging / report
    string log_file_path       = "";   // CSV report path; empty = disabled
    int verbosity              = UVM_MEDIUM;

    function new(string name = "atpg_seq_config");
        super.new(name);
    endfunction
endclass
