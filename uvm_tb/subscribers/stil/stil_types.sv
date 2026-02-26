/**
 * STIL (IEEE 1450) Core Data Structures
 *
 * These classes model key STIL concepts used by the generator:
 *  - Signals and their directions/types
 *  - Timing specifications (period, setup/hold, edge)
 *  - Waveforms and vectors
 *  - Procedures and pattern‑level information
 *
 * They are UVM objects so they can be passed around and, if needed,
 * stored in configuration or analysis components.
 */

// -------------------------------------------------------------------
// Enumerations for STIL modeling
// -------------------------------------------------------------------

// Signal direction in STIL: I (input), O (output), B (bidir), C (clock/control)
typedef enum { STIL_SIG_I, STIL_SIG_O, STIL_SIG_B, STIL_SIG_C } stil_signal_type_e;

// Data type of a signal: single bit, or named enum values
typedef enum { STIL_DATA_BIT, STIL_DATA_ENUM } stil_data_type_e;

// Edge for timing reference: Rising or Falling
typedef enum { STIL_EDGE_R, STIL_EDGE_F } stil_edge_e;

// -------------------------------------------------------------------
// stil_signal_t
// -------------------------------------------------------------------

class stil_signal_t extends uvm_object;

    `uvm_object_utils(stil_signal_t)

    // Logical name of the signal in STIL
    string            signal_name;

    // Direction/type code: I, O, B, or C
    stil_signal_type_e signal_type;

    // Data type (bit or enum)
    stil_data_type_e  data_type;

    // Optional timing reference name (e.g. TimeSet or WaveformTable name)
    string            timing_reference;

    function new(string name = "stil_signal_t");
        super.new(name);
        data_type = STIL_DATA_BIT;
        signal_type = STIL_SIG_I;
    endfunction

    function string dir_char();
        case (signal_type)
            STIL_SIG_I: return "I";
            STIL_SIG_O: return "O";
            STIL_SIG_B: return "B";
            STIL_SIG_C: return "C";
            default:    return "I";
        endcase
    endfunction

endclass

// -------------------------------------------------------------------
// stil_timing_spec_t
// -------------------------------------------------------------------

class stil_timing_spec_t extends uvm_object;

    `uvm_object_utils(stil_timing_spec_t)

    // Clock period
    real   period;

    // Setup and hold times
    real   setup;
    real   hold;

    // Propagation delay
    real   propagation_delay;

    // Reference edge (R/F)
    stil_edge_e edge;

    // Timing unit string (e.g. "ns")
    string timing_unit;

    function new(string name = "stil_timing_spec_t");
        super.new(name);
        period           = 0.0;
        setup            = 0.0;
        hold             = 0.0;
        propagation_delay = 0.0;
        edge             = STIL_EDGE_R;
        timing_unit      = "ns";
    endfunction

endclass

// -------------------------------------------------------------------
// stil_waveform_t
// -------------------------------------------------------------------

class stil_waveform_t extends uvm_object;

    `uvm_object_utils(stil_waveform_t)

    // Waveform table or name
    string name;

    // Free‑form STIL definition string. This can describe:
    //  - TimeSet‑based waveforms
    //  - Simple drive/compare waveforms
    // It is emitted directly into the WaveformTable section.
    string definition;

    function new(string name = "stil_waveform_t");
        super.new(name);
    endfunction

endclass

// -------------------------------------------------------------------
// stil_vector_t
// -------------------------------------------------------------------

class stil_vector_t extends uvm_object;

    `uvm_object_utils(stil_vector_t)

    // Pattern name this vector belongs to
    string pattern_name;

    // Vector index within the pattern
    int    index;

    // Simulation time for this vector (cycle boundary)
    time   cycle_time;

    // Per‑signal STIL values (0/1/X/Z, and extensions like W/D if used)
    //
    // STIL value meanings in context:
    //   '0' : drive or expect logic 0
    //   '1' : drive or expect logic 1
    //   'X' : unknown / don't‑know; used for capture when value is not defined
    //   'Z' : high‑impedance
    //   'W' : weak unknown / "don't care" with weaker semantics in some tools
    //   'D' : drive don't‑care (tool may choose 0 or 1)
    //
    // The exact interpretation is tool‑dependent; we use 'X' and 'D' as
    // primary don't‑care markers, and 'Z' for tri‑state.
    string signal_values[string];  // key = signal_name, value = STIL char as string

    // Optional waveform table reference for this vector
    string waveform_name;

    function new(string name = "stil_vector_t");
        super.new(name);
    endfunction

endclass

// -------------------------------------------------------------------
// stil_procedure_t
// -------------------------------------------------------------------

class stil_procedure_t extends uvm_object;

    `uvm_object_utils(stil_procedure_t)

    // Name of the STIL Procedure
    string name;

    // Parameter list (formal parameter names)
    string parameters[$];

    // Sequence of vectors that conceptually belong to this Procedure
    stil_vector_t vector_sequence[$];

    function new(string name = "stil_procedure_t");
        super.new(name);
        this.name = name;
    endfunction

endclass

// -------------------------------------------------------------------
// stil_info_transaction
// -------------------------------------------------------------------

/**
 * stil_info_transaction
 *
 * Base transaction for the STIL generator. It represents a single
 * logical "cycle" or vector of activity as observed by the testbench.
 *
 * Multiple agents (JTAG, clock, reset, pad) can contribute to a single
 * stil_info_transaction via their analysis ports by populating the
 * associative arrays.
 */
class stil_info_transaction extends uvm_object;

    `uvm_object_utils(stil_info_transaction)

    // Sequential index of the vector
    int   vector_index;

    // Simulation time for this cycle
    time  cycle_time;

    // Per‑signal STIL value (drive/compare) at this cycle
    string signal_values[string];

    // Optional separate capture / compare data stores
    string capture_data[string];
    string compare_data[string];

    // Timing information associated with this vector
    stil_timing_spec_t timing_info;

    function new(string name = "stil_info_transaction");
        super.new(name);
        timing_info = stil_timing_spec_t::type_id::create("timing_info");
    endfunction

    // Add or update a signal value (e.g. from an agent)
    function void add_signal_value(string sig_name, string value);
        signal_values[sig_name] = value;
    endfunction

    // Convenience: add capture / compare values
    function void add_capture_value(string sig_name, string value);
        capture_data[sig_name] = value;
    endfunction

    function void add_compare_value(string sig_name, string value);
        compare_data[sig_name] = value;
    endfunction

    // Return a compact vector string in a deterministic signal order.
    // The caller supplies the signal list to control ordering.
    function string get_vector_as_string(ref string ordered_signals[$]);
        string result = "";
        foreach (ordered_signals[i]) begin
            string s = ordered_signals[i];
            string v;
            if (signal_values.exists(s))
                v = signal_values[s];
            else
                v = "X"; // don't‑care by default
            result = {result, v};
        end
        return result;
    endfunction

    // Simple timing reference (e.g. "Rising" / "Falling" edge with unit)
    function string get_timing_reference();
        string edge_str = (timing_info.edge == STIL_EDGE_R) ? "R" : "F";
        return $sformatf("%s %0.3f%s", edge_str, timing_info.period,
                         timing_info.timing_unit);
    endfunction

endclass

