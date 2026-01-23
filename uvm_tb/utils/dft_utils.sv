/**
 * DFT Utilities
 * 
 * Utility functions and helper classes for DFT verification.
 * Includes functions for scan chain manipulation, pattern generation,
 * and test result analysis.
 */

package dft_utils_pkg;
    
    // Scan chain configuration
    class scan_chain_config;
        int num_chains;
        int chain_lengths[];
        string chain_names[];
        
        function new(int num_chains);
            this.num_chains = num_chains;
            chain_lengths = new[num_chains];
            chain_names = new[num_chains];
        endfunction
    endclass
    
    // Pattern generator utilities
    class pattern_generator;
        static function bit[31:0] generate_lfsr_seed(int seed);
            return seed;
        endfunction
        
        static function bit[31:0] generate_pseudo_random(int seed, int count);
            bit[31:0] lfsr = seed;
            for (int i = 0; i < count; i++) begin
                lfsr = {lfsr[30:0], lfsr[31] ^ lfsr[21] ^ lfsr[1] ^ lfsr[0]};
            end
            return lfsr;
        endfunction
    endclass
    
    // Test result analyzer
    class test_result_analyzer;
        int total_patterns;
        int passed_patterns;
        int failed_patterns;
        
        function new();
            total_patterns = 0;
            passed_patterns = 0;
            failed_patterns = 0;
        endfunction
        
        function void record_result(bit passed);
            total_patterns++;
            if (passed) begin
                passed_patterns++;
            end else begin
                failed_patterns++;
            end
        endfunction
        
        function real get_pass_rate();
            if (total_patterns == 0) return 0.0;
            return (real'(passed_patterns) / real'(total_patterns)) * 100.0;
        endfunction
    endclass

endpackage
