/**
 * JTAG Coverage Collector (IEEE 1149.1)
 * 
 * Functional coverage for JTAG TAP controller operations.
 * Tracks:
 * - TAP state transitions
 * - Instruction register operations
 * - Data register operations
 * - Sequence type coverage
 * - TDO verification coverage
 * 
 * Reference: IEEE 1149.1 Standard for Test Access Port and Boundary-Scan Architecture
 */

class jtag_coverage extends uvm_subscriber#(jtag_xtn);
    
    `uvm_component_utils(jtag_coverage)
    
    // Item for coverage sampling
    jtag_xtn item;
    
    // Coverage events
    covergroup jtag_tap_state_cg;
        // TAP state coverage
        tap_state: coverpoint item.current_state {
            bins test_logic_reset = {TEST_LOGIC_RESET};
            bins run_test_idle = {RUN_TEST_IDLE};
            bins select_dr_scan = {SELECT_DR_SCAN};
            bins capture_dr = {CAPTURE_DR};
            bins shift_dr = {SHIFT_DR};
            bins exit1_dr = {EXIT1_DR};
            bins pause_dr = {PAUSE_DR};
            bins exit2_dr = {EXIT2_DR};
            bins update_dr = {UPDATE_DR};
            bins select_ir_scan = {SELECT_IR_SCAN};
            bins capture_ir = {CAPTURE_IR};
            bins shift_ir = {SHIFT_IR};
            bins exit1_ir = {EXIT1_IR};
            bins pause_ir = {PAUSE_IR};
            bins exit2_ir = {EXIT2_IR};
            bins update_ir = {UPDATE_IR};
        }
        
        // State transitions
        state_transition: coverpoint item.current_state {
            bins transitions[] = ([TEST_LOGIC_RESET:UPDATE_IR] => [TEST_LOGIC_RESET:UPDATE_IR]);
        }
    endgroup
    
    covergroup jtag_sequence_cg;
        // Sequence type coverage
        seq_type: coverpoint item.sequence_type {
            bins load_ir = {LOAD_IR};
            bins load_dr = {LOAD_DR};
            bins scan_shift = {SCAN_SHIFT};
            bins bypass = {BYPASS};
            bins tdi_tdo_check = {TDI_TDO_CHECK};
        }
        
        // IR instruction coverage
        ir_instruction: coverpoint item.ir_code {
            bins extest = {8'h00};      // EXTEST
            bins sample = {8'h01};      // SAMPLE/PRELOAD
            bins idcode = {8'h02};     // IDCODE (if supported)
            bins bypass_cmd = {8'hFF};  // BYPASS
            bins others = default;
        }
        
        // DR type coverage
        dr_type: coverpoint item.dr_type {
            bins bypass_reg = {DR_BYPASS};
            bins idcode_reg = {DR_IDCODE};
            bins bsr_reg = {DR_BSR};
            bins device_id_reg = {DR_DEVICE_ID};
            bins user_reg = {DR_USER};
        }
        
        // DR length coverage
        dr_length_cp: coverpoint item.dr_length {
            bins small = {[1:8]};
            bins medium = {[9:32]};
            bins large = {[33:128]};
            bins very_large = {[129:$]};
        }
        
        // IR length coverage
        ir_length_cp: coverpoint item.ir_length {
            bins standard = {4};
            bins extended = {[5:16]};
            bins long = {[17:32]};
        }
        
        // Cross coverage: Sequence type vs DR type
        seq_dr_cross: cross seq_type, dr_type;
    endgroup
    
    covergroup jtag_timing_cg;
        // Cycle count coverage
        cycle_count: coverpoint item.cycle_count {
            bins short = {[1:10]};
            bins medium = {[11:50]};
            bins long = {[51:100]};
            bins very_long = {[101:$]};
        }
        
        // Transaction duration
        transaction_duration: coverpoint (item.end_time - item.start_time) {
            bins fast = {[0:100ns]};
            bins normal = {[100ns:1000ns]};
            bins slow = {[1000ns:$]};
        }
    endgroup
    
    covergroup jtag_verification_cg;
        // TDO verification coverage
        tdo_match: coverpoint item.tdo_match {
            bins match = {1};
            bins mismatch = {0};
        }
        
        // TDO mismatch count
        tdo_mismatch: coverpoint item.tdo_mismatch_count {
            bins no_mismatch = {0};
            bins few_mismatches = {[1:5]};
            bins many_mismatches = {[6:$]};
        }
        
        // Cross: Sequence type vs TDO match
        seq_tdo_cross: cross item.sequence_type, tdo_match;
    endgroup
    
    // Constructor
    function new(string name = "jtag_coverage", uvm_component parent = null);
        super.new(name, parent);
        jtag_tap_state_cg = new();
        jtag_sequence_cg = new();
        jtag_timing_cg = new();
        jtag_verification_cg = new();
    endfunction
    
    // Write method - called when transaction is received
    function void write(jtag_xtn t);
        item = t;
        jtag_tap_state_cg.sample();
        jtag_sequence_cg.sample();
        jtag_timing_cg.sample();
        jtag_verification_cg.sample();
    endfunction
    
    // Report coverage
    function void report_phase(uvm_phase phase);
        `uvm_info("JTAG_COV", "JTAG Coverage Report:", UVM_MEDIUM)
        `uvm_info("JTAG_COV", $sformatf("  TAP State Coverage: %0.2f%%", 
                  jtag_tap_state_cg.get_coverage()), UVM_MEDIUM)
        `uvm_info("JTAG_COV", $sformatf("  Sequence Coverage: %0.2f%%", 
                  jtag_sequence_cg.get_coverage()), UVM_MEDIUM)
        `uvm_info("JTAG_COV", $sformatf("  Timing Coverage: %0.2f%%", 
                  jtag_timing_cg.get_coverage()), UVM_MEDIUM)
        `uvm_info("JTAG_COV", $sformatf("  Verification Coverage: %0.2f%%", 
                  jtag_verification_cg.get_coverage()), UVM_MEDIUM)
    endfunction

endclass
