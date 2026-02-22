/**
 * Response Collector for DFT Pad Agent
 *
 * Aggregates expected outputs from ATPG patterns and compares with
 * monitored primary output signals from pad_monitor_enhanced.
 */

typedef struct {
    time t;
    int pattern_id;
    logic [63:0] exp;
    logic [63:0] mask;
} response_expected_t;

class response_collector extends uvm_component;

    `uvm_component_utils(response_collector)

    response_expected_t expected_list[$];
    pad_xtn captured_list[$];

    uvm_analysis_export#(pad_xtn) expected_export;
    uvm_analysis_export#(pad_xtn) captured_export;
    uvm_tlm_analysis_fifo#(pad_xtn) expected_fifo;
    uvm_tlm_analysis_fifo#(pad_xtn) captured_fifo;

    int match_count = 0;
    int mismatch_count = 0;
    int total_expected = 0;
    real tolerance = 0.0;
    pad_config pcfg;

    function new(string name = "response_collector", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        expected_export = new("expected_export", this);
        captured_export = new("captured_export", this);
        expected_fifo = new("expected_fifo", this);
        captured_fifo = new("captured_fifo", this);
        if (!uvm_config_db#(pad_config)::get(this, "", "pad_cfg", pcfg))
            pcfg = null;
        if (pcfg != null)
            tolerance = pcfg.response_match_tolerance;
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        expected_export.connect(expected_fifo.analysis_export);
        captured_export.connect(captured_fifo.analysis_export);
    endfunction

    task run_phase(uvm_phase phase);
        fork
            collect_expected();
            collect_captured();
            compare_responses();
        join_none
    endtask

    task collect_expected();
        pad_xtn t;
        forever begin
            expected_fifo.get(t);
            if (t.is_output() || t.expected_response !== 0 || t.compare_mask !== 0) begin
                expected_list.push_back('{$time, t.signal_id, t.expected_response, t.compare_mask});
                total_expected++;
            end
        end
    endtask

    task collect_captured();
        pad_xtn t;
        forever begin
            captured_fifo.get(t);
            captured_list.push_back(t);
        end
    endtask

    task compare_responses();
        wait (expected_list.size() > 0 && captured_list.size() > 0);
        forever begin
            if (expected_list.size() == 0 || captured_list.size() == 0) begin
                #1;
                continue;
            end
            void'(compare_next());
        end
    endtask

    function bit compare_next();
        if (expected_list.size() == 0 || captured_list.size() == 0) return 0;
        response_expected_t ex = expected_list[0];
        expected_list.pop_front();
        pad_xtn cap = captured_list[0];
        captured_list.pop_front();
        logic [63:0] exp = ex.exp;
        logic [63:0] mask = ex.mask;
        logic [63:0] obs = cap.data_value;
        if ((obs & mask) === (exp & mask) || within_tolerance(obs, exp, mask)) begin
            match_count++;
            return 1;
        end
        mismatch_count++;
        `uvm_error("RESP_CMP", $sformatf("Response mismatch: expected 0x%x got 0x%x (mask 0x%x)", exp, obs, mask))
        return 0;
    endfunction

    function bit within_tolerance(logic [63:0] obs, logic [63:0] exp, logic [63:0] mask);
        if (tolerance <= 0) return 0;
        logic [63:0] masked_obs = obs & mask;
        logic [63:0] masked_exp = exp & mask;
        logic [63:0] diff = (masked_obs >= masked_exp)
            ? (masked_obs - masked_exp)
            : (masked_exp - masked_obs);
        return (real'(diff) <= tolerance);
    endfunction

    function void report_phase(uvm_phase phase);
        super.report_phase(phase);
        `uvm_info("RESP_COLL", $sformatf("Response comparison: total_expected=%0d match=%0d mismatch=%0d",
            total_expected, match_count, mismatch_count), UVM_LOW)
    endfunction

endclass
