/**
 * Enhanced Pad Agent
 *
 * Unified agent combining pad_driver_enhanced, pad_monitor_enhanced,
 * optional response_collector, and pad_config for DFT primary I/O control
 * and observation.
 */

class pad_agent_enhanced extends uvm_agent;

    `uvm_component_utils(pad_agent_enhanced)

    pad_config pcfg;
    pad_driver_enhanced driver;
    pad_monitor_enhanced monitor;
    response_collector resp_collector;
    uvm_sequencer#(pad_xtn) sequencer;

    function new(string name = "pad_agent_enhanced", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(pad_config)::get(this, "", "pad_cfg", pcfg)) begin
            pcfg = pad_config::type_id::create("pad_cfg");
            uvm_config_db#(pad_config)::set(this, "*", "pad_cfg", pcfg);
        end
        monitor = pad_monitor_enhanced::type_id::create("monitor", this);
        if (is_active == UVM_ACTIVE) begin
            driver = pad_driver_enhanced::type_id::create("driver", this);
            sequencer = uvm_sequencer#(pad_xtn)::type_id::create("sequencer", this);
        end
        resp_collector = response_collector::type_id::create("resp_collector", this);
    endfunction

    function void connect_phase(uvm_phase phase);
        super.connect_phase(phase);
        if (is_active == UVM_ACTIVE) begin
            driver.seq_item_port.connect(sequencer.seq_item_export);
        end
        monitor.ap_captured.connect(resp_collector.captured_export);
        if (is_active == UVM_ACTIVE && driver != null)
            resp_collector.expected_export.connect(driver.ap_expected);
    endfunction

endclass
