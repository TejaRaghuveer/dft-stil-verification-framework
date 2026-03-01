/**
 * ATPG Pattern Parser
 *
 * Reads ATPG tool outputs (TetraMAX, Fastscan, generic ASCII, STIL-like)
 * and converts them to atpg_pattern_t for use in UVM sequences.
 *
 * - parse_atpg_file() dispatches by format
 * - parse_tetramax_file / parse_fastscan_file / parse_generic_ascii
 * - validate_pattern_data(), get_pattern_count(), get_pattern_by_name()
 * - export_patterns_to_uvm() for test integration
 * - Utilities: parse_vector_line, validate_vector_length, convert_logic_to_bit, get_pattern_statistics
 * - Error handling: file/perm, syntax with line numbers, length/fault/duplicate checks
 * - Logging and optional report file; dry-run mode
 */

class atpg_pattern_parser extends uvm_component;
    `uvm_component_utils(atpg_pattern_parser)

    atpg_parser_config cfg;
    atpg_pattern_t     patterns[$];
    atpg_pattern_t     patterns_by_name[string];

    int                parse_errors;
    int                parse_warnings;
    int                last_error_line;
    string             last_error_msg;
    int                report_fd;

    function new(string name = "atpg_pattern_parser", uvm_component parent = null);
        super.new(name, parent);
        parse_errors = 0;
        parse_warnings = 0;
        last_error_line = 0;
        report_fd = 0;
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(atpg_parser_config)::get(this, "", "atpg_parser_cfg", cfg)) begin
            cfg = atpg_parser_config::type_id::create("atpg_parser_cfg");
        end
    endfunction

    // -------------------------------------------------------------------------
    // Parse entry point: detect format and dispatch
    // -------------------------------------------------------------------------
    function int parse_atpg_file(string filename);
        int fd;
        string line;
        string fmt;
        fd = $fopen(filename, "r");
        if (fd == 0) begin
            `uvm_error("ATPG_PARSER", $sformatf("File not found or no read permission: %s", filename))
            parse_errors++;
            return 0;
        end
        if ($fgets(line, fd) != 0) begin
            fmt = detect_format(line, filename);
            $fclose(fd);
            if (fmt == "tetramax")      return parse_tetramax_file(filename);
            if (fmt == "fastscan")      return parse_fastscan_file(filename);
            if (fmt == "stil")          return parse_generic_ascii(filename);
            return parse_generic_ascii(filename);
        end
        $fclose(fd);
        return parse_generic_ascii(filename);
    endfunction

    function string detect_format(string first_line, string filename);
        string lower = first_line.tolower();
        if (lower.find("stil") != -1) return "stil";
        if (lower.find("tetramax") != -1 || filename.find("tetramax") != -1) return "tetramax";
        if (lower.find("fastscan") != -1 || filename.find("fastscan") != -1) return "fastscan";
        return "generic";
    endfunction

    // -------------------------------------------------------------------------
    // Format-specific parsers (TetraMAX / Fastscan → often ASCII export)
    // --------------------------------------------------------------------------
    function int parse_tetramax_file(string filename);
        `uvm_info("ATPG_PARSER", $sformatf("Parsing TetraMAX-style file: %s", filename), cfg.verbosity)
        // TetraMAX ASCII pattern format: typically header then vectors.
        // Delegate to generic ASCII with format hint; extend with TM-specific tokens if needed.
        return parse_generic_ascii(filename);
    endfunction

    function int parse_fastscan_file(string filename);
        `uvm_info("ATPG_PARSER", $sformatf("Parsing Fastscan-style file: %s", filename), cfg.verbosity)
        return parse_generic_ascii(filename);
    endfunction

    // -------------------------------------------------------------------------
    // Generic ASCII: lines of vectors; # comments; PATTERN <name> blocks
    // -------------------------------------------------------------------------
    function int parse_generic_ascii(string filename);
        int fd;
        string line;
        int line_num;
        atpg_pattern_t pat;
        string pat_name;
        int count_before = patterns.size();
        bit dry_run = (cfg != null) ? cfg.dry_run : 0;
        int max_count = (cfg != null) ? cfg.max_pattern_count : 0;
        int exp_len = (cfg != null) ? cfg.expected_scan_length : 0;
        int pattern_index = 0;  // Count of patterns in this parse (works in dry-run when patterns.size() doesn't increase)

        fd = $fopen(filename, "r");
        if (fd == 0) begin
            `uvm_error("ATPG_PARSER", $sformatf("File not found: %s", filename))
            parse_errors++;
            return 0;
        end

        pat = null;
        line_num = 0;
        while (!$feof(fd)) begin
            if ($fgets(line, fd) == 0) break;
            line_num++;
            trim_line(line);
            if (line == "" || line.substr(0,0) == "#") continue;
            if (line.tolower().find("pattern") == 0) begin
                if (pat != null) begin
                    if (!dry_run) flush_pattern(pat);
                    else if (pat.pattern_name != "" && !patterns_by_name.exists(pat.pattern_name))
                        patterns_by_name[pat.pattern_name] = pat;  // dry-run: register name for duplicate check
                end
                pat_name = parse_pattern_name(line);
                if (pat_name != "" && patterns_by_name.exists(pat_name)) begin
                    set_error(line_num, $sformatf("Duplicate pattern name: %s", pat_name));
                    parse_errors++;
                end
                pattern_index++;
                pat = atpg_pattern_t::type_id::create(pat_name != "" ? pat_name : "pat");
                pat.pattern_name = (pat_name != "") ? pat_name : $sformatf("pat_%0d", count_before + pattern_index);
                pat.pattern_type = ATPG_STUCK_AT;
                if (!dry_run && (cfg == null || cfg.passes_type_filter(ATPG_STUCK_AT))) begin
                    patterns.push_back(pat);
                    flush_pattern(pat);  // register so get_pattern_by_name() finds it
                end else if (dry_run && pat.pattern_name != "" && !patterns_by_name.exists(pat.pattern_name))
                    patterns_by_name[pat.pattern_name] = pat;  // dry-run: register so next duplicate is detected
                continue;
            end
            if (pat == null && line != "") begin
                pattern_index++;
                pat = atpg_pattern_t::type_id::create("anonymous");
                pat.pattern_name = $sformatf("pat_%0d", count_before + pattern_index);
                if (!dry_run && (cfg == null || cfg.passes_type_filter(ATPG_STUCK_AT))) begin
                    patterns.push_back(pat);
                    flush_pattern(pat);  // register so get_pattern_by_name() finds it
                end
            end
            if (pat != null && is_vector_line(line)) begin
                if (exp_len > 0) begin
                    if (!validate_vector_length(line, exp_len)) begin
                        set_error(line_num, $sformatf("Vector length mismatch: got %0d expected %0d", line.len(), exp_len));
                        parse_errors++;
                    end
                end
                if (!dry_run) pat.add_scan_in(line);
            end
        end
        if (pat != null) begin
            if (!dry_run) flush_pattern(pat);
            else if (pat.pattern_name != "" && !patterns_by_name.exists(pat.pattern_name))
                patterns_by_name[pat.pattern_name] = pat;  // dry-run: register last pattern name
        end
        $fclose(fd);

        if (max_count > 0 && patterns.size() > count_before + max_count) begin
            while (patterns.size() > count_before + max_count)
                patterns.pop_back();
            `uvm_warning("ATPG_PARSER", $sformatf("Limited to %0d patterns", max_count))
        end
        `uvm_info("ATPG_PARSER", $sformatf("Parsed %0d patterns from %s (errors=%0d warnings=%0d)",
                  patterns.size() - count_before, filename, parse_errors, parse_warnings),
                  (cfg != null) ? cfg.verbosity : UVM_MEDIUM)
        return patterns.size() - count_before;
    endfunction

    function string parse_pattern_name(string line);
        int i;
        string s = line.tolower();
        i = s.find("pattern");
        if (i == -1) return "";
        i += 7;
        while (i < line.len() && (line.substr(i,i) == " " || line.substr(i,i) == "\t")) i++;
        return line.substr(i, line.len()-1);
    endfunction

    function void flush_pattern(atpg_pattern_t p);
        if (p.pattern_name != "" && !patterns_by_name.exists(p.pattern_name))
            patterns_by_name[p.pattern_name] = p;
    endfunction

    function void trim_line(ref string line);
        int i, j;
        int len = line.len();
        for (i = 0; i < len; i++)
            if (line.substr(i,i) != " " && line.substr(i,i) != "\t") break;
        for (j = len - 1; j >= 0; j--)
            if (line.substr(j,j) != " " && line.substr(j,j) != "\n" && line.substr(j,j) != "\r") break;
        if (i <= j && j >= 0) line = line.substr(i, j); else line = "";
    endfunction

    function bit is_vector_line(string line);
        int i;
        string c;
        for (i = 0; i < line.len(); i++) begin
            c = line.substr(i,i);
            if (c != "0" && c != "1" && c != "x" && c != "X" && c != "z" && c != "Z") return 0;
        end
        return (line.len() > 0);
    endfunction

    function void set_error(int line_num, string msg);
        last_error_line = line_num;
        last_error_msg = msg;
    endfunction

    // -------------------------------------------------------------------------
    // Utilities
    // -------------------------------------------------------------------------
    function int parse_vector_line(string line, ref logic vec[]);
        int n = line.len();
        logic ch;
        vec = new[n];
        for (int i = 0; i < n; i++) begin
            string c = line.substr(i, i);
            if (c == "1") vec[i] = 1;
            else if (c == "0") vec[i] = 0;
            else if (c == "x" || c == "X") vec[i] = 1'bx;
            else if (c == "z" || c == "Z") vec[i] = 1'bz;
            else vec[i] = 1'bx;
        end
        return n;
    endfunction

    function bit validate_vector_length(string vector_str, int expected_length);
        if (expected_length <= 0) return 1;
        return (vector_str.len() == expected_length);
    endfunction

    function bit convert_logic_to_bit(logic l);
        if (l === 1'b1) return 1;
        return 0;
    endfunction

    function void get_pattern_statistics(ref int total_patterns, ref int total_vectors, ref real avg_length);
        total_patterns = patterns.size();
        total_vectors = 0;
        avg_length = 0.0;
        foreach (patterns[i]) begin
            total_vectors += patterns[i].get_scan_vector_count();
            avg_length += real'(patterns[i].get_scan_vector_count());
        end
        if (total_patterns > 0) avg_length = avg_length / total_patterns;
    endfunction

    // -------------------------------------------------------------------------
    // Validation and lookup
    // -------------------------------------------------------------------------
    function bit validate_pattern_data();
        bit ok = 1;
        foreach (patterns[i]) begin
            atpg_pattern_t p = patterns[i];
            if (p.scan_in_vectors.size() == 0) begin
                `uvm_warning("ATPG_PARSER", $sformatf("Pattern %s has no scan-in vectors", p.pattern_name))
                parse_warnings++;
            end
            foreach (p.scan_in_vectors[j]) begin
                if (is_suspicious_vector(p.scan_in_vectors[j]))
                    parse_warnings++;
            end
        end
        return ok;
    endfunction

    function bit is_suspicious_vector(string v);
        int ones = 0, zeros = 0, xx = 0;
        for (int i = 0; i < v.len(); i++) begin
            string c = v.substr(i,i);
            if (c == "1") ones++;
            else if (c == "0") zeros++;
            else xx++;
        end
        if (xx == 0 && zeros == v.len()) begin
            `uvm_warning("ATPG_PARSER", "Suspicious: vector is all zeros")
            return 1;
        end
        if (xx == 0 && ones == v.len()) begin
            `uvm_warning("ATPG_PARSER", "Suspicious: vector is all ones")
            return 1;
        end
        if (xx == v.len()) begin
            `uvm_warning("ATPG_PARSER", "Suspicious: vector is all X")
            return 1;
        end
        return 0;
    endfunction

    function int get_pattern_count();
        return patterns.size();
    endfunction

    function atpg_pattern_t get_pattern_by_name(string name);
        if (patterns_by_name.exists(name)) return patterns_by_name[name];
        return null;
    endfunction

    function void export_patterns_to_uvm(ref atpg_pattern_t q[$]);
        q = patterns;
    endfunction

    function void report_phase(uvm_phase phase);
        super.report_phase(phase);
        if (cfg != null && cfg.report_file_path != "") begin
            report_fd = $fopen(cfg.report_file_path, "w");
            if (report_fd != 0) begin
                $fwrite(report_fd, "ATPG Parser Report\n");
                $fwrite(report_fd, "Patterns: %0d\n", patterns.size());
                $fwrite(report_fd, "Errors: %0d Warnings: %0d\n", parse_errors, parse_warnings);
                $fclose(report_fd);
            end
        end
    endfunction
endclass
