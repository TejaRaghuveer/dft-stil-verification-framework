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

    function new(string name = "atpg_select_patterns_test", uvm_component parent = null);
        super.new(name, parent);
        pattern_file_path = "patterns/stuck_at.stil";
        max_patterns_to_run = 10;
        // Example: select specific patterns by name (uncomment and add names):
        // pattern_names.push_back("pat_1");
        // pattern_names.push_back("pat_2");
        // pattern_names.push_back("pat_5");
        // pattern_names.push_back("pat_7");
        // pattern_names.push_back("pat_10");
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        parser_cfg = atpg_parser_config::type_id::create("parser_cfg");
        parser_cfg.dry_run = 0;
        uvm_config_db#(atpg_parser_config)::set(this, "*", "atpg_parser_cfg", parser_cfg);
        parser = atpg_pattern_parser::type_id::create("atpg_parser", this);
        seq_cfg = atpg_seq_config::type_id::create("atpg_seq_cfg");
        seq_cfg.dr_length = (cfg != null && cfg.num_scan_chains > 0) ? cfg.scan_chain_lengths[0] : 256;
        seq_cfg.ir_length = 4;
        seq_cfg.test_mode_ir = 32'h00;
        seq_cfg.reset_between_patterns = 0;
        seq_cfg.log_file_path = "atpg_pattern_results.csv";
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

        `uvm_info("ATPG_SEL", $sformatf("Parsing pattern file: %s", pattern_file_path), UVM_MEDIUM)
        parsed = parser.parse_atpg_file(pattern_file_path);
        if (parsed <= 0) begin
            `uvm_warning("ATPG_SEL", "No patterns parsed; running with empty queue (no pattern execution)")
            return;
        end

        if (pattern_names.size() > 0) begin
            foreach (pattern_names[i]) begin
                pat = parser.get_pattern_by_name(pattern_names[i]);
                if (pat != null) begin
                    pattern_queue.push_back(pat);
                    selected++;
                end else
                    `uvm_warning("ATPG_SEL", $sformatf("Pattern not found: %s", pattern_names[i]))
                if (selected >= max_patterns_to_run) break;
            end
        end else begin
            parser.export_patterns_to_uvm(pattern_queue);
            if (pattern_queue.size() > max_patterns_to_run) begin
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
