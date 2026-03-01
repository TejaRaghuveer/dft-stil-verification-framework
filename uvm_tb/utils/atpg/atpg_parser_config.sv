/**
 * ATPG Parser Configuration
 *
 * Input paths, pattern type filter, max count, vector length expectations,
 * fault coverage thresholds, logging and dry-run options.
 */

class atpg_parser_config extends uvm_object;
    `uvm_object_utils(atpg_parser_config)

    string input_file_paths[$];
    string input_file_path;   // single file (convenience)

    // Load only these pattern types (empty = load all)
    atpg_pattern_type_e pattern_type_filter[$];

    int max_pattern_count;    // 0 = no limit
    int expected_scan_length; // 0 = do not enforce
    int expected_pi_length;
    int expected_po_length;

    real fault_coverage_threshold; // min 0.0-100.0 to accept pattern; 0 = no filter

    int verbosity;
    string report_file_path;  // "" = no report file
    bit dry_run;             // parse but do not load into memory (still validate)

    function new(string name = "atpg_parser_config");
        super.new(name);
        max_pattern_count = 0;
        expected_scan_length = 0;
        expected_pi_length = 0;
        expected_po_length = 0;
        fault_coverage_threshold = 0.0;
        verbosity = UVM_MEDIUM;
        report_file_path = "";
        dry_run = 0;
    endfunction

    function void add_input_file(string path);
        input_file_paths.push_back(path);
        input_file_path = path;
    endfunction

    function void set_pattern_type_filter(atpg_pattern_type_e t);
        pattern_type_filter.delete();
        pattern_type_filter.push_back(t);
    endfunction

    function bit passes_type_filter(atpg_pattern_type_e t);
        if (pattern_type_filter.size() == 0) return 1;
        foreach (pattern_type_filter[i])
            if (pattern_type_filter[i] == t) return 1;
        return 0;
    endfunction
endclass
