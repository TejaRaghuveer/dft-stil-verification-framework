/**
 * Enhanced Pad Driver for DFT Primary I/O Control
 *
 * Drives primary inputs with configurable timing, stores expected outputs,
 * supports combinational and sequential stimulus, multi-bit vectors with
 * per-pin timing, drive strength, and activity logging.
 */

class pad_driver_enhanced extends uvm_driver#(pad_xtn);

    `uvm_component_utils(pad_driver_enhanced)

    virtual pad_if vif;
    test_config cfg;
    pad_config pcfg;  // Pad-specific config (signal list, timing)

    uvm_analysis_port#(pad_xtn) ap_expected;

    logic [63:0] expected_outputs[$];
    time expected_output_times[$];

    // Activity log: timestamp, pin/vector, value, direction
    struct { time t; string msg; } activity_log[$];
    int max_log_entries = 1000;

    // Reference clock for setup/hold (optional)
    bit use_clock_ref = 0;

    function new(string name = "pad_driver_enhanced", uvm_component parent = null);
        super.new(name, parent);
    endfunction

    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        if (!uvm_config_db#(virtual pad_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("NO_VIF", "Failed to get pad_if from config_db")
        end
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config")
        end
        if (!uvm_config_db#(pad_config)::get(this, "", "pad_cfg", pcfg))
            pcfg = null;
        ap_expected = new("ap_expected", this);
    endfunction

    task run_phase(uvm_phase phase);
        initialize_pads();
        forever begin
            seq_item_port.get_next_item(req);
            drive_pad_transaction(req);
            seq_item_port.item_done();
        end
    endtask

    task initialize_pads();
        if (vif == null) return;
        vif.pad_out <= '0;
        vif.pad_oe  <= '0;  // All as input (observing) by default
        log_activity($time, "Pad driver initialized: all OE=0");
    endtask

    task drive_pad_transaction(uvm_sequence_item item);
        pad_xtn txn;
        if (!$cast(txn, item)) begin
            `uvm_error("PAD_DRV", "Expected pad_xtn transaction")
            return;
        end

        log_activity($time, $sformatf("Drive %s: %s", txn.signal_name, txn.convert2string()));

        if (txn.drive_strength == TRI_STATE) begin
            drive_tri_state(txn);
            return;
        end

        if (txn.is_input()) begin
            if (txn.stimulus_type == SEQUENTIAL && use_clock_ref && vif.clk !== 1'bx)
                drive_with_setup_hold(txn);
            else
                drive_immediate(txn);
        end

        if (txn.is_output()) begin
            store_expected_output(txn);
        end
    endtask

    task drive_immediate(pad_xtn txn);
        time t0 = $time;
        int id = (txn.signal_id >= 0) ? txn.signal_id : 0;
        int w = (txn.data_width > 0 && txn.data_width <= 64) ? txn.data_width : 1;
        logic [63:0] val = txn.data_value;

        int num_pads = (cfg != null) ? cfg.num_pads : ((pcfg != null) ? pcfg.num_pads : 32);
        if (id < num_pads) begin
            #(txn.timing_offset);
            for (int i = 0; i < w && (id+i) < num_pads; i++) begin
                vif.pad_out[id+i] <= val[i];
                vif.pad_oe[id+i]  <= 1'b1;  // Driving
            end
            log_activity($time, $sformatf("Drive PI[%0d:%0d]=0x%x", id, id+w-1, val));
            if (txn.hold_time_ns > 0) #(txn.hold_time_ns);
        end
    endtask

    task drive_with_setup_hold(pad_xtn txn);
        int id = (txn.signal_id >= 0) ? txn.signal_id : 0;
        int w = (txn.data_width > 0 && txn.data_width <= 64) ? txn.data_width : 1;
        logic [63:0] val = txn.data_value;
        int num_pads = (cfg != null) ? cfg.num_pads : ((pcfg != null) ? pcfg.num_pads : 32);

        @(posedge vif.clk);
        #(txn.setup_time_ns);
        for (int i = 0; i < w && (id+i) < num_pads; i++) begin
            vif.pad_out[id+i] <= val[i];
            vif.pad_oe[id+i]  <= 1'b1;
        end
        #(txn.hold_time_ns);
        log_activity($time, $sformatf("Drive PI[%0d] (sync) =0x%x", id, val));
    endtask

    task drive_tri_state(pad_xtn txn);
        int id = (txn.signal_id >= 0) ? txn.signal_id : 0;
        int w = (txn.data_width > 0 && txn.data_width <= 64) ? txn.data_width : 1;
        int num_pads = (cfg != null) ? cfg.num_pads : ((pcfg != null) ? pcfg.num_pads : 32);
        if (num_pads > 0)
            for (int i = 0; i < w && (id+i) < num_pads; i++)
                vif.pad_oe[id+i] <= 1'b0;  // Release drive
        log_activity($time, $sformatf("Tri-state PI[%0d:%0d]", id, id+w-1));
    endtask

    function void store_expected_output(pad_xtn txn);
        expected_outputs.push_back(txn.get_expected_response());
        expected_output_times.push_back($time);
        if (ap_expected != null)
            ap_expected.write(txn);
    endfunction

    function void log_activity(time t, string msg);
        if (activity_log.size() >= max_log_entries) return;
        activity_log.push_back('{ t, msg });
        `uvm_info("PAD_DRV", $sformatf("[%0t] %s", t, msg), UVM_HIGH)
    endfunction

    // --- Format pad data (delegate to pad_utils) ---
    static function void format_pad_data_from_int(input longint val, input int width, ref logic pad_bits[]);
        pad_utils::format_pad_data_from_int(val, width, pad_bits);
    endfunction
    static function longint format_pad_data_to_int(const ref logic pad_bits[], input int width);
        return pad_utils::format_pad_data_to_int(pad_bits, width);
    endfunction
    static function void format_pad_data_hex_to_vec(input string hex_str, ref logic vec[]);
        pad_utils::hex_string_to_logic_vec(hex_str, vec);
    endfunction
    static function string format_pad_data_vec_to_hex(const ref logic vec[]);
        return pad_utils::logic_vec_to_hex_string(vec);
    endfunction

endclass
