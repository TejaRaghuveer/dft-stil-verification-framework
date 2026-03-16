/**
 * ATPG Select Patterns Test
 *
 * Example: select 5-10 specific ATPG patterns from a parsed pattern set
 * and execute them via multi_pattern_seq (ATPG-to-UVM converter).
 *
 * Usage:
 *   +UVM_TESTNAME=atpg_select_patterns_test
 *   Optional plusargs: pattern file path, pattern names, count (see configure_test).
 */
class atpg_select_patterns_test extends dft_base_test;

    `uvm_component_utils(atpg_select_patterns_test)

    atpg_pattern_parser parser;
    atpg_parser_config parser_cfg;
    atpg_seq_config seq_cfg;
    atpg_pattern_exec_logger exec_logger;
    string pattern_file_path;
    string pattern_names[$];
    int max_patterns_to_run;
    string pattern_list_file_path;
    string results_csv_path;
    bit reset_between_patterns;

    function new(string name = "atpg_select_patterns_test", uvm_component parent = null);
        super.new(name, parent);
        pattern_file_path = "patterns/stuck_at.stil";
        max_patterns_to_run = 10;
        pattern_list_file_path = "";
        results_csv_path = "atpg_pattern_results.csv";
        reset_between_patterns = 0;
        // Example: select specific patterns by name (uncomment and add names):
        // pattern_names.push_back("pat_1");
        // pattern_names.push_back("pat_2");
        // pattern_names.push_back("pat_5");
        // pattern_names.push_back("pat_7");
        // pattern_names.push_back("pat_10");
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        // ------------------------------
        // Plusargs overrides (integration)
        // ------------------------------
        void'($value$plusargs("PATTERN_FILE=%s", pattern_file_path));
        void'($value$plusargs("PATTERN_LIST_FILE=%s", pattern_list_file_path));
        void'($value$plusargs("RESULT_CSV=%s", results_csv_path));
        void'($value$plusargs("MAX_PATTERNS=%d", max_patterns_to_run));
        void'($value$plusargs("RESET_BETWEEN=%d", reset_between_patterns));

        parser_cfg = atpg_parser_config::type_id::create("parser_cfg");
        parser_cfg.dry_run = 0;
        uvm_config_db#(atpg_parser_config)::set(this, "*", "atpg_parser_cfg", parser_cfg);
        parser = atpg_pattern_parser::type_id::create("atpg_parser", this);
        seq_cfg = atpg_seq_config::type_id::create("atpg_seq_cfg");
        seq_cfg.dr_length = (cfg != null && cfg.num_scan_chains > 0) ? cfg.scan_chain_lengths[0] : 256;
        seq_cfg.ir_length = 4;
        seq_cfg.test_mode_ir = 32'h00;
        seq_cfg.reset_between_patterns = reset_between_patterns;
        seq_cfg.log_file_path = results_csv_path;
        uvm_config_db#(atpg_seq_config)::set(this, "*", "atpg_seq_cfg", seq_cfg);
        exec_logger = atpg_pattern_exec_logger::type_id::create("atpg_logger", this);
        uvm_config_db#(atpg_pattern_exec_logger)::set(null, "*", "atpg_logger", exec_logger);
    endfunction

    virtual function void configure_test();
        super.configure_test();
        cfg.test_mode = DFT_MODE_STUCK_AT;
    endfunction

    virtual task run_test_sequence();
        atpg_pattern_t pat;
        atpg_pattern_t pattern_queue[$];
        multi_pattern_seq multi_seq;
        int parsed;
        int selected = 0;
        int fd;
        string line;

        `uvm_info("ATPG_SEL", $sformatf("Parsing pattern file: %s", pattern_file_path), UVM_MEDIUM)
        parsed = parser.parse_atpg_file(pattern_file_path);
        if (parsed <= 0) begin
            `uvm_warning("ATPG_SEL", "No patterns parsed; running with empty queue (no pattern execution)")
            return;
        end

        // Optional: load pattern names from a file (one name per line)
        if (pattern_list_file_path != "") begin
            fd = $fopen(pattern_list_file_path, "r");
            if (fd == 0) begin
                `uvm_warning("ATPG_SEL", $sformatf("PATTERN_LIST_FILE not found: %s", pattern_list_file_path))
            end else begin
                while (!$feof(fd)) begin
                    if ($fgets(line, fd) == 0) break;
                    // Trim leading/trailing whitespace + CR/LF without changing case.
                    while (line.len() > 0 && (line.substr(0,0) == " " || line.substr(0,0) == "\t"))
                        line = line.substr(1, line.len()-1);
                    while (line.len() > 0 && (line.substr(line.len()-1,line.len()-1) == "\n" ||
                                             line.substr(line.len()-1,line.len()-1) == "\r" ||
                                             line.substr(line.len()-1,line.len()-1) == " "  ||
                                             line.substr(line.len()-1,line.len()-1) == "\t"))
                        line = line.substr(0, line.len()-1);
                    if (line.len() == 0) continue;
                    pattern_names.push_back(line);
                end
                $fclose(fd);
            end
        end

        if (pattern_names.size() > 0) begin
            foreach (pattern_names[i]) begin
                pat = parser.get_pattern_by_name(pattern_names[i]);
                if (pat != null) begin
                    pattern_queue.push_back(pat);
                    selected++;
                end else
                    `uvm_warning("ATPG_SEL", $sformatf("Pattern not found: %s", pattern_names[i]))
                if (max_patterns_to_run > 0 && selected >= max_patterns_to_run) break;
            end
        end else begin
            parser.export_patterns_to_uvm(pattern_queue);
            if (max_patterns_to_run > 0 && pattern_queue.size() > max_patterns_to_run) begin
                while (pattern_queue.size() > max_patterns_to_run)
                    pattern_queue.pop_back();
            end
            selected = pattern_queue.size();
        end

        `uvm_info("ATPG_SEL", $sformatf("Selected %0d patterns for execution", selected), UVM_MEDIUM)
        if (selected == 0) return;

        multi_seq = multi_pattern_seq::type_id::create("multi_seq");
        multi_seq.pattern_queue = pattern_queue;
        multi_seq.seq_cfg = seq_cfg;
        multi_seq.env = env;
        multi_seq.logger = exec_logger;
        multi_seq.reset_between = seq_cfg.reset_between_patterns;

        // In passive–mode JTAG agent, the sequencer is not created and will be null.
        // Guard against that to avoid runtime errors when starting the sequence.
        if (env != null && env.jtag_ag != null && env.jtag_ag.sequencer != null) begin
            multi_seq.start(env.jtag_ag.sequencer);
        end else begin
            // No sequencer → no patterns will run. Treat this as a configuration
            // error so the test does not appear to pass silently.
            `uvm_error("ATPG_SEL",
                       $sformatf("JTAG sequencer not available; %0d selected patterns were not executed",
                                 selected))
        end
    endtask
endclass
