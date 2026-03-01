/**
 * ATPG Pattern Data Structures
 *
 * Defines pattern type enum, vector representation, and atpg_pattern_t
 * for storing parsed ATPG pattern data (scan in/out, primary I/O, faults, metadata).
 */

// ---------------------------------------------------------------------------
// Pattern type (test mode)
// ---------------------------------------------------------------------------
typedef enum {
    ATPG_STUCK_AT,
    ATPG_TRANSITION_DELAY,
    ATPG_PATH_DELAY,
    ATPG_CUSTOM
} atpg_pattern_type_e;

// ---------------------------------------------------------------------------
// atpg_vector_t - single vector of logic values (0/1/X/Z)
// Stored as string for flexibility; convert to logic[] via parser utilities.
// ---------------------------------------------------------------------------
class atpg_vector_t extends uvm_object;
    `uvm_object_utils(atpg_vector_t)
    string vec_str;  // e.g. "1010X1ZX"
    function new(string name = "atpg_vector_t");
        super.new(name);
    endfunction
endclass

// ---------------------------------------------------------------------------
// atpg_pattern_t - one ATPG pattern (scan + PI/PO + faults + metadata)
// ---------------------------------------------------------------------------
class atpg_pattern_t extends uvm_object;
    `uvm_object_utils(atpg_pattern_t)

    string             pattern_name;
    atpg_pattern_type_e pattern_type;
    string             scan_in_vectors[$];
    string             scan_out_vectors[$];
    string             primary_in_vectors[$];
    string             expected_primary_out[$];
    string             fault_list[$];
    int                capture_cycles;
    string             comments[$];
    string             metadata[string];  // key-value: "test_type", "fault_coverage", etc.

    function new(string name = "atpg_pattern_t");
        super.new(name);
        pattern_type = ATPG_STUCK_AT;
        capture_cycles = 0;
    endfunction

    function void add_scan_in(string v);
        scan_in_vectors.push_back(v);
    endfunction
    function void add_scan_out(string v);
        scan_out_vectors.push_back(v);
    endfunction
    function void add_primary_in(string v);
        primary_in_vectors.push_back(v);
    endfunction
    function void add_expected_primary_out(string v);
        expected_primary_out.push_back(v);
    endfunction
    function void add_fault(string f);
        fault_list.push_back(f);
    endfunction
    function void add_comment(string c);
        comments.push_back(c);
    endfunction
    function void set_metadata(string key, string value);
        metadata[key] = value;
    endfunction
    function string get_metadata(string key);
        if (metadata.exists(key)) return metadata[key];
        return "";
    endfunction

    function int get_scan_vector_count();
        return scan_in_vectors.size();
    endfunction
endclass
