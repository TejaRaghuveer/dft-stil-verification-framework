/**
 * Enhanced Pad Monitor for DFT Primary I/O Observation
 *
 * Captures primary output changes, records timing/waveform, compares to expected
 * (immediate or end-of-test), detects X/Z, alerts on unexpected transitions,
 * and provides statistics (transitions per pin, timing variance).
 */

class pad_monitor_enhanced extends uvm_monitor;

    `uvm_component_utils(pad_monitor_enhanced)

    virtual pad_if vif;
    pad_config pcfg;
    test_config cfg;

    uvm_analysis_port#(pad_xtn) ap_captured;
    uvm_analysis_port#(pad_xtn) ap_alert;

    // Waveform: time, value per sample
    struct { time t; logic [63:0] val; int width; } waveform[$];
    int max_waveform_entries = 5000;

    // Expected values for comparison (index -> queue of {time, expected_value, mask})
    struct { time t; logic [63:0] exp; logic [63:0] mask; } expected_queue[$];

    // Statistics
    int transition_count[int];   // pin index -> number of transitions
    time last_transition_time[int];
    real timing_variance[int];   // variance of delta-T per pin
    int sample_count[int];       // for variance calculation
    time sum_delta[int];
    time sum_delta_sq[int];

    // Alerts
    int unexpected_count = 0;
    int x_detected_count = 0;
    int z_detected_count = 0;

    bit check_immediate = 0;     // 1 = compare each sample, 0 = end-of-test
    bit capture_enabled = 1;
    int num_pads_monitored = 32;

    function new(string name = "pad_monitor_enhanced", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        ap_captured = new("ap_captured", this);
        ap_alert = new("ap_alert", this);
        if (!uvm_config_db#(virtual pad_if)::get(this, "", "vif", vif))
            `uvm_fatal("NO_VIF", "pad_monitor_enhanced: no pad_if")
        if (!uvm_config_db#(pad_config)::get(this, "", "pad_cfg", pcfg))
            pcfg = null;
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg))
            cfg = null;
        if (pcfg != null) begin
            check_immediate = pcfg.response_immediate_check;
            num_pads_monitored = pcfg.num_pads;
        end else if (cfg != null)
            num_pads_monitored = cfg.num_pads;
    endfunction

    task run_phase(uvm_phase phase);
        fork
            capture_primary_outputs();
        join_none
    endtask

    task capture_primary_outputs();
        logic [63:0] prev = '0;
        logic [63:0] curr;
        forever begin
            @(vif.pad_in or vif.pad_out);
            if (!capture_enabled) continue;
            curr = sample_primary_outputs();
            if (curr !== prev) begin
                record_transition(prev, curr);
                check_xz(curr);
                if (check_immediate)
                    compare_expected($time, curr);
                prev = curr;
            end
        end
    endtask

    function logic [63:0] sample_primary_outputs();
        logic [63:0] val = 0;
        int n = (num_pads_monitored < 64) ? num_pads_monitored : 64;
        for (int i = 0; i < n; i++)
            val[i] = vif.pad_in[i];
        return val;
    endfunction

    function void record_transition(logic [63:0] prev, logic [63:0] curr);
        time now = $time;
        int n = (num_pads_monitored < 64) ? num_pads_monitored : 64;
        for (int i = 0; i < n; i++) begin
            if (curr[i] !== prev[i]) begin
                if (!transition_count.exists(i)) begin
                    transition_count[i] = 0;
                    last_transition_time[i] = 0;
                    sum_delta[i] = 0;
                    sum_delta_sq[i] = 0;
                    sample_count[i] = 0;
                end
                transition_count[i]++;
                if (last_transition_time[i] > 0) begin
                    time dt = now - last_transition_time[i];
                    sum_delta[i] += dt;
                    sum_delta_sq[i] += dt * dt;
                    sample_count[i]++;
                end
                last_transition_time[i] = now;
            end
        end
        if (waveform.size() < max_waveform_entries) begin
            waveform.push_back('{now, curr, n});
        end
        pad_xtn txn = pad_xtn::type_id::create("captured");
        txn.signal_type = OUTPUT;
        txn.data_value = curr;
        txn.data_width = n;
        txn.transaction_time = now;
        ap_captured.write(txn);
    endfunction

    function void check_xz(logic [63:0] val);
        int n = (num_pads_monitored < 64) ? num_pads_monitored : 64;
        for (int i = 0; i < n; i++) begin
            if (val[i] === 1'bx) begin
                x_detected_count++;
                raise_alert("X detected", i, val);
            end
            if (val[i] === 1'bz) begin
                z_detected_count++;
                raise_alert("Z detected", i, val);
            end
        end
    endfunction

    function void raise_alert(string msg, int pin, logic [63:0] val);
        pad_xtn txn = pad_xtn::type_id::create("alert");
        txn.signal_name = $sformatf("PO_%0d", pin);
        txn.signal_type = OUTPUT;
        txn.data_value = val;
        txn.transaction_time = $time;
        ap_alert.write(txn);
        `uvm_warning("PAD_MON", $sformatf("%s at pin %0d at %0t: 0x%x", msg, pin, $time, val))
    endfunction

    function void add_expected(time t, logic [63:0] exp, logic [63:0] mask);
        if (expected_queue.size() >= 10000) return;
        expected_queue.push_back('{t, exp, mask});
    endfunction

    function void compare_expected(time now, logic [63:0] observed);
        foreach (expected_queue[i]) begin
            if (expected_queue[i].t != now) continue;
            logic [63:0] exp = expected_queue[i].exp;
            logic [63:0] mask = expected_queue[i].mask;
            logic [63:0] masked_obs = observed & mask;
            logic [63:0] masked_exp = exp & mask;
            if (masked_obs !== masked_exp) begin
                unexpected_count++;
                `uvm_error("PAD_MON", $sformatf("Mismatch at %0t: expected 0x%x got 0x%x (mask 0x%x)", now, exp, observed, mask))
                raise_alert("Unexpected value", 0, observed);
            end
            expected_queue.delete(i);
            return;
        end
    endfunction

    function void end_of_elaboration_phase(uvm_phase phase);
        super.end_of_elaboration_phase(phase);
    endfunction

    function void report_phase(uvm_phase phase);
        super.report_phase(phase);
        `uvm_info("PAD_MON", $sformatf("Pad Monitor Statistics: transitions (sample) per pin, X count=%0d Z count=%0d unexpected=%0d",
            x_detected_count, z_detected_count, unexpected_count), UVM_LOW)
        foreach (transition_count[i])
            `uvm_info("PAD_MON", $sformatf("  Pin %0d: transitions=%0d", i, transition_count[i]), UVM_HIGH)
        foreach (timing_variance[i])
            `uvm_info("PAD_MON", $sformatf("  Pin %0d timing variance (computed): %f", i, timing_variance[i]), UVM_HIGH)
    endfunction

    function void compute_timing_variance();
        foreach (sample_count[i]) begin
            if (sample_count[i] < 2) continue;
            real mean = real'(sum_delta[i]) / sample_count[i];
            real mean_sq = real'(sum_delta_sq[i]) / sample_count[i];
            timing_variance[i] = mean_sq - (mean * mean);
        end
    endfunction

    function void check_expected_at_eot();
        compute_timing_variance();
        foreach (expected_queue[i]) begin
            logic [63:0] exp = expected_queue[i].exp;
            logic [63:0] mask = expected_queue[i].mask;
            logic [63:0] observed = 0;
            if (waveform.size() > 0)
                observed = waveform[waveform.size()-1].val;
            if ((observed & mask) !== (exp & mask))
                unexpected_count++;
        end
        expected_queue.delete();
    endfunction

endclass
