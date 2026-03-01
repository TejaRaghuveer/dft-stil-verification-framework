/**
 * ATPG Pattern Execution Logger
 *
 * Logs start/end time per pattern, actual vs expected for failures,
 * coverage statistics, and exports to CSV for post-processing.
 */

typedef enum {
    ATPG_PATTERN_PASS,
    ATPG_PATTERN_FAIL,
    ATPG_PATTERN_ERROR
} atpg_pattern_status_e;

class atpg_pattern_result_t;
    string pattern_name;
    int pattern_index;
    atpg_pattern_status_e status;
    time start_time;
    time end_time;
    int vector_index_fail;   // First failing vector index (-1 if none)
    string expected_str;    // Expected value at failure (abbreviated)
    string actual_str;      // Actual value at failure (abbreviated)
    int total_vectors;
    int mismatch_count;
endclass

class atpg_pattern_exec_logger extends uvm_component;
    `uvm_component_utils(atpg_pattern_exec_logger)

    atpg_seq_config cfg;
    atpg_pattern_result_t results[$];
    int total_patterns_run;
    int total_pass, total_fail, total_error;
    int fd_csv;
    bit csv_open;

    function new(string name = "atpg_pattern_exec_logger", uvm_component parent = null);
        super.new(name, parent);
        total_patterns_run = 0;
        total_pass = 0;
        total_fail = 0;
        total_error = 0;
        csv_open = 0;
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(atpg_seq_config)::get(this, "", "atpg_seq_cfg", cfg))
            cfg = atpg_seq_config::type_id::create("atpg_seq_cfg");
    endfunction

    function void open_csv(string path);
        if (path == "") return;
        fd_csv = $fopen(path, "w");
        csv_open = (fd_csv != 0);
        if (csv_open)
            $fwrite(fd_csv, "pattern_name,index,status,start_time,end_time,duration_ns,vector_fail,mismatches,total_vectors\n");
    endfunction

    function void log_pattern_start(string pattern_name, int index);
        atpg_pattern_result_t r;
        r = new();
        r.pattern_name = pattern_name;
        r.pattern_index = index;
        r.status = ATPG_PATTERN_ERROR;
        r.start_time = $time;
        r.end_time = 0;
        r.vector_index_fail = -1;
        r.mismatch_count = 0;
        r.total_vectors = 0;
        results.push_back(r);
        total_patterns_run++;
        `uvm_info("ATPG_LOG", $sformatf("Pattern start: %s [%0d] @ %0t", pattern_name, index, $time), (cfg != null) ? cfg.verbosity : UVM_MEDIUM)
    endfunction

    function void log_pattern_end(string pattern_name, atpg_pattern_status_e status, int total_vectors, int vector_index_fail = -1, string expected_str = "", string actual_str = "", int mismatch_count = 0);
        atpg_pattern_result_t r;
        if (results.size() == 0) return;
        r = results[results.size()-1];
        r.pattern_name = pattern_name;
        r.status = status;
        r.end_time = $time;
        r.total_vectors = total_vectors;
        r.vector_index_fail = vector_index_fail;
        r.expected_str = expected_str;
        r.actual_str = actual_str;
        r.mismatch_count = mismatch_count;
        case (status)
            ATPG_PATTERN_PASS: total_pass++;
            ATPG_PATTERN_FAIL: total_fail++;
            default: total_error++;
        endcase
        if (csv_open) begin
            $fwrite(fd_csv, "%s,%0d,%s,%0t,%0t,%0t", pattern_name, r.pattern_index, status.name(), r.start_time, r.end_time, r.end_time - r.start_time);
            $fwrite(fd_csv, ",%0d,%0d,%0d\n", vector_index_fail, mismatch_count, total_vectors);
        end
        if (status != ATPG_PATTERN_PASS)
            `uvm_error("ATPG_LOG", $sformatf("Pattern %s %s: vector_fail=%0d expected=%s actual=%s mismatches=%0d", pattern_name, status.name(), vector_index_fail, expected_str, actual_str, mismatch_count))
        else
            `uvm_info("ATPG_LOG", $sformatf("Pattern end: %s %s @ %0t", pattern_name, status.name(), $time), (cfg != null) ? cfg.verbosity : UVM_MEDIUM)
    endfunction

    function void log_mismatch(string pattern_name, int vector_idx, string expected, string actual);
        `uvm_error("ATPG_LOG", $sformatf("Mismatch %s vector[%0d]: expected=%s actual=%s", pattern_name, vector_idx, expected, actual))
    endfunction

    function void get_coverage_stats(ref int pass, ref int fail, ref int error);
        pass = total_pass;
        fail = total_fail;
        error = total_error;
    endfunction

    function void report_phase(uvm_phase phase);
        super.report_phase(phase);
        if (csv_open) $fclose(fd_csv);
        `uvm_info("ATPG_LOG", $sformatf("Pattern execution: total=%0d PASS=%0d FAIL=%0d ERROR=%0d", total_patterns_run, total_pass, total_fail, total_error), UVM_LOW)
    endfunction
endclass
