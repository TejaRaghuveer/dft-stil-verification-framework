/**
 * Test Configuration Class
 * 
 * Central configuration class for the UVM testbench. Contains all
 * configurable parameters for agents, sequences, and test behavior.
 * 
 * This class is used to configure:
 * - Agent behavior (active/passive mode)
 * - Timing parameters
 * - Pattern generation settings
 * - STIL file paths
 * - Debug and verbosity levels
 */

class test_config extends uvm_object;
    
    `uvm_object_utils(test_config)
    
    // ============================================
    // Agent Configuration
    // ============================================
    
    // JTAG Agent Configuration
    bit jtag_agent_active = 1;              // 1=active (drives signals), 0=passive (monitors only)
    int jtag_clock_period_ns = 100;         // JTAG clock period in nanoseconds (default 10MHz)
    int jtag_reset_cycles = 10;             // Number of clock cycles to hold reset
    bit jtag_enable_coverage = 1;           // Enable coverage collection for JTAG agent
    
    // Clock Agent Configuration
    bit clock_agent_active = 1;             // Clock agent is typically always active
    int clock_period_ns = 10;               // Main clock period (default 100MHz)
    int clock_duty_cycle = 50;              // Clock duty cycle percentage
    bit clock_enable_random_jitter = 0;     // Enable random clock jitter for stress testing
    
    // Reset Agent Configuration
    bit reset_agent_active = 1;             // Reset agent configuration
    int reset_assert_cycles = 100;         // Number of cycles to assert reset
    int reset_deassert_delay_ns = 50;      // Delay before deasserting reset
    bit reset_async = 0;                    // 1=asynchronous reset, 0=synchronous
    
    // Pad Agent Configuration
    bit pad_agent_active = 1;               // Pad agent configuration
    int num_pads = 32;                      // Number of pad signals
    bit pad_enable_boundary_scan = 1;       // Enable boundary scan testing
    bit pad_enable_io_test = 1;             // Enable I/O pad testing
    
    // ============================================
    // STIL Configuration
    // ============================================
    
    string stil_input_file = "";            // Path to input STIL pattern file
    string stil_output_file = "output.stil"; // Path to output STIL file (generated patterns)
    bit stil_enable_generation = 1;         // Enable STIL pattern generation
    bit stil_enable_validation = 1;         // Enable STIL pattern validation
    int stil_pattern_timeout_ns = 1000000;  // Timeout for pattern execution (1ms default)
    
    // ============================================
    // Test Pattern Configuration
    // ============================================
    
    int num_test_patterns = 100;            // Number of test patterns to generate/execute
    bit enable_random_patterns = 0;         // Enable random pattern generation
    bit enable_deterministic_patterns = 1;   // Enable deterministic patterns from STIL file
    int pattern_repeat_count = 1;           // Number of times to repeat each pattern
    
    // ============================================
    // Coverage Configuration
    // ============================================
    
    bit enable_functional_coverage = 1;     // Enable functional coverage collection
    bit enable_code_coverage = 0;           // Enable code coverage (requires tool support)
    real coverage_goal = 95.0;              // Coverage goal percentage
    
    // ============================================
    // Debug and Logging Configuration
    // ============================================
    
    uvm_verbosity verbosity = UVM_MEDIUM;   // Default verbosity level
    bit enable_waveform_dump = 1;           // Enable waveform dumping
    string waveform_file = "tb_top.fsdb";   // Waveform file name
    bit enable_transaction_logging = 1;     // Enable transaction-level logging
    
    // ============================================
    // GPU Shader Specific Configuration
    // ============================================
    
    int num_shader_cores = 4;               // Number of shader cores in DUT
    int num_threads_per_core = 64;          // Number of threads per shader core
    bit enable_shader_dft_test = 1;         // Enable shader-specific DFT tests
    bit enable_scan_chain_verification = 1; // Enable scan chain verification
    
    // ============================================
    // Constructor and Methods
    // ============================================
    
    function new(string name = "test_config");
        super.new(name);
    endfunction
    
    // Convert configuration to string for logging
    function string convert2string();
        string s;
        s = $sformatf("Test Configuration:\n");
        s = $sformatf("%s  JTAG Clock Period: %0d ns\n", s, jtag_clock_period_ns);
        s = $sformatf("%s  Main Clock Period: %0d ns\n", s, clock_period_ns);
        s = $sformatf("%s  Number of Pads: %0d\n", s, num_pads);
        s = $sformatf("%s  STIL Input File: %s\n", s, stil_input_file);
        s = $sformatf("%s  Number of Patterns: %0d\n", s, num_test_patterns);
        s = $sformatf("%s  Shader Cores: %0d\n", s, num_shader_cores);
        return s;
    endfunction
    
    // Validate configuration
    function bit validate();
        if (clock_period_ns <= 0) begin
            `uvm_error("CONFIG", "Clock period must be positive")
            return 0;
        end
        if (num_pads <= 0) begin
            `uvm_error("CONFIG", "Number of pads must be positive")
            return 0;
        end
        if (stil_enable_generation && stil_input_file == "") begin
            `uvm_warning("CONFIG", "STIL generation enabled but no input file specified")
        end
        return 1;
    endfunction

endclass
