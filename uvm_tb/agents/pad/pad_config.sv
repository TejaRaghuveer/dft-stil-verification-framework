/**
 * Pad Agent Configuration
 *
 * Signal list, timing constraints, response matching tolerance, logging level.
 */

class pad_config extends uvm_object;

    `uvm_object_utils(pad_config)

    int num_primary_inputs = 16;
    int num_primary_outputs = 16;
    int num_pads = 32;  // Total pads (PI + PO + bidir)

    string signal_names[];   // Ordered list of pad names
    pad_signal_type_e signal_types[];  // Type per pad

    time setup_time_ns = 1;
    time hold_time_ns = 1;
    time propagation_delay_ns = 0;

    real response_match_tolerance = 0.0;  // For analog or timing tolerance
    bit response_immediate_check = 0;     // 1 = check each cycle, 0 = end-of-test

    int logging_detail_level = 1;  // 0=minimal, 1=normal, 2=verbose

    function new(string name = "pad_config");
        super.new(name);
    endfunction

endclass
