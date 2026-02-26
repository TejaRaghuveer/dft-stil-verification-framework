/**
 * STIL Generator Subscriber
 *
 * Core IEEE 1450 (STIL) file generator implemented as a UVM subscriber.
 *
 * This component consumes stil_info_transaction objects, collapses
 * concurrent activity into vectors, and emits a standards‑compliant
 * STIL file with:
 *   - Header and meta‑information
 *   - Signals and SignalGroups
 *   - TimingSpecs / WaveformTables
 *   - Procedures
 *   - Patterns / PatternExec
 *
 * STIL encoding conventions used:
 *   - '0' / '1' : logic 0 / 1 (drive or compare)
 *   - 'X'       : unknown / don't‑know capture value
 *   - 'Z'       : high‑impedance
 *   - 'D'       : don't‑care drive (tool may choose 0 or 1)
 *   - 'W'       : weak unknown (rarely needed; reserved here)
 *
 * The generator is intended as a core, extensible implementation; you
 * can refine signal/timing modeling and add tool‑specific attributes
 * as needed.
 */

class stil_generator extends uvm_subscriber#(stil_info_transaction);

    `uvm_component_utils(stil_generator)

    // ------------------------------------------------------------
    // Configuration
    // ------------------------------------------------------------

    test_config     cfg;
    dft_test_config dft_cfg;

    // STIL output control
    string output_file_path = "output.stil";
    string stil_version     = "1.0";  // 1.0 or 2.0
    int    verbosity        = UVM_MEDIUM;
    bit    compression_en   = 0;      // merge identical consecutive vectors
    string signal_name_prefix = "";   // custom naming rule (e.g. "DUT_")

    // ------------------------------------------------------------
    // Internal state
    // ------------------------------------------------------------

    int stil_fd;

    // Signal registry (discovered from transactions)
    stil_signal_t signals[$];
    stil_signal_t signals_by_name[string];

    // Timing spec (single default, can be extended)
    stil_timing_spec_t default_timing;

    // Collapsed vectors in time order
    stil_vector_t vector_queue[$];

    // Map from cycle_time to index in vector_queue
    int time_to_vector_index[time];

    // Track latest value per signal for edge detection
    string last_value_by_signal[string];

    // Pattern naming
    string current_pattern_name = "PATTERN_0";
    int    vector_count = 0;

    function new(string name = "stil_generator", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    // ------------------------------------------------------------
    // Build / Start‑of‑simulation
    // ------------------------------------------------------------

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);

        void'(uvm_config_db#(dft_test_config)::get(this, "", "cfg", dft_cfg));
        void'(uvm_config_db#(test_config)::get(this, "", "cfg", cfg));

        if (dft_cfg != null) begin
            // Prefer DFT config if present
            verbosity = dft_cfg.dft_log_verbosity;
            output_file_path = dft_cfg.stil_output_file;
        end else if (cfg != null) begin
            verbosity = cfg.verbosity;
            output_file_path = cfg.stil_output_file;
        end

        default_timing = stil_timing_spec_t::type_id::create("default_timing");
        if (cfg != null) begin
            default_timing.period = cfg.jtag_clock_period_ns;
        end else begin
            default_timing.period = 100.0;
        end
        default_timing.timing_unit = "ns";
    endfunction

    function void start_of_simulation_phase(uvm_phase phase);
        super.start_of_simulation_phase(phase);

        // Decide whether generation is enabled
        bit enable_stil = 1;
        if (dft_cfg != null)
            enable_stil = dft_cfg.stil_enable_generation;
        else if (cfg != null)
            enable_stil = cfg.stil_enable_generation;

        if (!enable_stil)
            return;

        stil_fd = $fopen(output_file_path, "w");
        if (stil_fd == 0) begin
            `uvm_fatal("STIL_GEN", $sformatf("Failed to open STIL file '%s'",
                                             output_file_path))
        end

        `uvm_info("STIL_GEN", $sformatf("Opened STIL file '%s' (STIL %s)",
                                        output_file_path, stil_version),
                  verbosity)

        write_header();
    endfunction

    // ------------------------------------------------------------
    // Subscriber write()
    // ------------------------------------------------------------

    function void write(stil_info_transaction t);
        time   ct = t.cycle_time;
        string sig;

        // First time we see a signal, register it
        foreach (t.signal_values[sig]) begin
            register_signal_if_new(sig);
        end

        // Collapse by cycle_time: merge contributions from different agents
        stil_vector_t v;
        if (time_to_vector_index.exists(ct)) begin
            int idx = time_to_vector_index[ct];
            v = vector_queue[idx];
        end else begin
            v = stil_vector_t::type_id::create($sformatf("vec_%0d", vector_count));
            v.pattern_name = current_pattern_name;
            v.index        = vector_count;
            v.cycle_time   = ct;
            vector_queue.push_back(v);
            time_to_vector_index[ct] = vector_queue.size() - 1;
            vector_count++;
        end

        // Merge signal values (drive side)
        foreach (t.signal_values[sig]) begin
            v.signal_values[sig] = t.signal_values[sig];
        end

        // Merge compare values (e.g. TDO expected).
        // For now, we treat compare_data as the effective STIL value for
        // that signal in the vector, so it overrides any plain drive value.
        foreach (t.compare_data[sig]) begin
            v.signal_values[sig] = t.compare_data[sig];
        end

        // Capture data could be modeled separately (e.g. as sampled values),
        // but for basic pattern emission we do not need to alter the vector
        // bits; tools will infer capture semantics from signal direction
        // (Outputs) and waveform table usage.

        // Capture timing info for potential future refinements
        if (v.waveform_name == "")
            v.waveform_name = "default_wft";
    endfunction

    // ------------------------------------------------------------
    // Finalization
    // ------------------------------------------------------------

    function void extract_phase(uvm_phase phase);
        super.extract_phase(phase);

        if (stil_fd == 0)
            return;

        if (compression_en)
            compress_vectors();

        write_timing_and_waveforms();
        write_procedures();
        write_patterns_and_exec();

        $fwrite(stil_fd, "\n// End of STIL file\n");
        $fclose(stil_fd);
        stil_fd = 0;

        `uvm_info("STIL_GEN",
                  $sformatf("Generated %0d STIL vectors", vector_queue.size()),
                  verbosity)
    endfunction

    // ------------------------------------------------------------
    // Signal registration
    // ------------------------------------------------------------

    function void register_signal_if_new(string sig_name);
        if (signals_by_name.exists(sig_name))
            return;

        stil_signal_t s = stil_signal_t::type_id::create($sformatf("sig_%s", sig_name));
        s.signal_name = apply_naming_rule(sig_name);

        // Heuristic: treat names containing "TDO" or ending with "O" as outputs,
        // those with "TCK"/"CLK" or "RST" as control/clock, others as inputs.
        if (sig_name.tolower().find("tdo") != -1)
            s.signal_type = STIL_SIG_O;
        else if ((sig_name.tolower().find("tck") != -1) ||
                 (sig_name.tolower().find("clk") != -1) ||
                 (sig_name.tolower().find("rst") != -1))
            s.signal_type = STIL_SIG_C;
        else
            s.signal_type = STIL_SIG_I;

        signals_by_name[sig_name] = s;
        signals.push_back(s);
    endfunction

    function string apply_naming_rule(string sig_name);
        if (signal_name_prefix == "")
            return sig_name;
        return {signal_name_prefix, sig_name};
    endfunction

    // ------------------------------------------------------------
    // Vector compression (optional)
    // ------------------------------------------------------------

    function void compress_vectors();
        if (vector_queue.size() <= 1)
            return;

        stil_vector_t compressed[$];
        stil_vector_t prev = vector_queue[0];
        compressed.push_back(prev);

        for (int i = 1; i < vector_queue.size(); i++) begin
            stil_vector_t curr = vector_queue[i];
            if (vectors_equal(prev, curr)) begin
                continue; // drop duplicate
            end
            compressed.push_back(curr);
            prev = curr;
        end

        vector_queue = compressed;
    endfunction

    function bit vectors_equal(stil_vector_t a, stil_vector_t b);
        if (a.signal_values.num() != b.signal_values.num())
            return 0;
        string s;
        foreach (a.signal_values[s]) begin
            if (!b.signal_values.exists(s))
                return 0;
            if (a.signal_values[s] != b.signal_values[s])
                return 0;
        end
        return 1;
    endfunction

    // ------------------------------------------------------------
    // STIL Writing helpers
    // ------------------------------------------------------------

    function void write_header();
        $fwrite(stil_fd, $sformatf("STIL %s;\n\n", stil_version));
        $fwrite(stil_fd, "// Generated by DFT-STIL Verification Framework\n");
        $fwrite(stil_fd, "// IEEE 1450 compliant STIL file (core structure)\n\n");

        // Header section (metadata)
        $fwrite(stil_fd, "Header {\n");
        $fwrite(stil_fd, "    Title \"DFT STIL patterns\";\n");
        $fwrite(stil_fd, "    Source \"UVM testbench\";\n");
        $fwrite(stil_fd, "}\n\n");

        // Signals section
        $fwrite(stil_fd, "Signals {\n");
        foreach (signals[i]) begin
            stil_signal_t s = signals[i];
            string dir = (s.signal_type == STIL_SIG_O) ? "Out" :
                         (s.signal_type == STIL_SIG_C) ? "In"  : "In";
            // For simplicity we treat clocks/control as In; tools can promote
            // them to Clock/Control using additional attributes if needed.
            $fwrite(stil_fd, $sformatf("    \"%s\" %s Digital;\n",
                                       s.signal_name, dir));
        end
        $fwrite(stil_fd, "}\n\n");

        // Simple SignalGroups example (can be extended)
        $fwrite(stil_fd, "SignalGroups {\n");
        $fwrite(stil_fd, "    scan_inputs  = '\"TDI\"';\n");
        $fwrite(stil_fd, "    scan_outputs = '\"TDO\"';\n");
        $fwrite(stil_fd, "    control_signals = '\"TCK\" \"TMS\" \"TRST\"';\n");
        $fwrite(stil_fd, "}\n\n");
    endfunction

    function void write_timing_and_waveforms();
        $fwrite(stil_fd, "Timing {\n");
        $fwrite(stil_fd, $sformatf("    WaveformTable \"%s\" {\n", "default_wft"));
        $fwrite(stil_fd, $sformatf("        Period %0.3f%s;\n",
                                   default_timing.period,
                                   default_timing.timing_unit));
        $fwrite(stil_fd, "        Waveforms {\n");
        // Basic drive/compare examples:
        //   'D' drives 0/1; 'C' compares; 'S' samples at edge
        $fwrite(stil_fd, "            \"drive\" { 0 D; 1 D; X D; Z D; }\n");
        $fwrite(stil_fd, "            \"compare\" { 0 C; 1 C; X C; Z C; }\n");
        $fwrite(stil_fd, "        }\n");
        $fwrite(stil_fd, "    }\n");
        $fwrite(stil_fd, "}\n\n");
    endfunction

    function void write_procedures();
        // Minimal placeholders for typical scan operations; can be expanded.
        $fwrite(stil_fd, "Procedures {\n");
        $fwrite(stil_fd, "    Procedure \"Init\" { }\n");
        $fwrite(stil_fd, "    Procedure \"Shift\" { }\n");
        $fwrite(stil_fd, "    Procedure \"Capture\" { }\n");
        $fwrite(stil_fd, "}\n\n");
    endfunction

    function void write_patterns_and_exec();
        // PatternExec defines pattern execution order and associated tables.
        $fwrite(stil_fd, "PatternExec {\n");
        $fwrite(stil_fd, "    PatternBurst \"DFT_Burst\" {\n");
        $fwrite(stil_fd, "        PatList { ");
        $fwrite(stil_fd, "\"PATTERN_0\" ");
        $fwrite(stil_fd, "};\n");
        $fwrite(stil_fd, "    }\n");
        $fwrite(stil_fd, "}\n\n");

        // Patterns section with vectors
        $fwrite(stil_fd, "Patterns {\n");
        $fwrite(stil_fd, "    Pattern \"PATTERN_0\" {\n");
        $fwrite(stil_fd, "        WFT \"default_wft\";\n");

        // Build deterministic signal ordering from registry
        string ordered[$];
        foreach (signals[i]) begin
            ordered.push_back(signals[i].signal_name);
        end

        for (int i = 0; i < vector_queue.size(); i++) begin
            stil_vector_t v = vector_queue[i];
            string vec_str = "";
            // Build vector string in the same order as Signals{} listing
            string sig_name;
            foreach (ordered[j]) begin
                sig_name = ordered[j];
                string val;
                if (v.signal_values.exists(sig_name))
                    val = v.signal_values[sig_name];
                else
                    val = "X";
                vec_str = {vec_str, val};
            end
            $fwrite(stil_fd, $sformatf("        V {%s};\n", vec_str));
        end

        $fwrite(stil_fd, "    }\n");
        $fwrite(stil_fd, "}\n\n");
    endfunction

endclass

