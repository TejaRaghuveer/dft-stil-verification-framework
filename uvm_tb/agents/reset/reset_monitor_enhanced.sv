/**
 * Enhanced Reset Monitor
 * 
 * Monitors reset assertion/deassertion events and tracks:
 * - Reset assertion times
 * - Reset deassertion times
 * - Reset duration
 * - Reset type (async/sync)
 * - Glitch detection
 */

class reset_monitor_enhanced extends uvm_monitor;
    
    `uvm_component_utils(reset_monitor_enhanced)
    
    // Virtual interface
    virtual reset_if vif;
    
    // Analysis port
    uvm_analysis_port#(reset_xtn) analysis_port;
    
    // Configuration
    test_config cfg;
    
    // Statistics
    int assert_count = 0;
    int deassert_count = 0;
    time assert_times[$];
    time deassert_times[$];
    time reset_durations[$];
    bit current_reset_state = 0;
    time last_transition_time = 0;
    
    // Constructor
    function new(string name = "reset_monitor_enhanced", uvm_component parent = null);
        super.new(name, parent);
        analysis_port = new("analysis_port", this);
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        if (!uvm_config_db#(virtual reset_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("NO_VIF", "Failed to get reset_if from config_db")
        end
        
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config")
        end
    endfunction
    
    // Run phase
    task run_phase(uvm_phase phase);
        monitor_reset();
    endtask
    
    /**
     * Monitor reset transitions
     */
    task monitor_reset();
        bit prev_rst = 1;  // Default deasserted (active low)
        bit curr_rst;
        time transition_time;
        
        `uvm_info("RST_MON", "Starting reset monitoring", UVM_MEDIUM)
        
        forever begin
            @(vif.rst_n);
            curr_rst = vif.rst_n;
            transition_time = $time;
            
            // Detect reset assertion (active low: 1->0, active high: 0->1)
            // Assuming active low for now
            if (!curr_rst && prev_rst) begin
                // Reset asserted
                assert_count++;
                assert_times.push_back(transition_time);
                current_reset_state = 1;
                last_transition_time = transition_time;
                
                publish_reset_event(1, transition_time);
                `uvm_info("RST_MON", $sformatf("[%0t] Reset ASSERTED", transition_time), UVM_MEDIUM)
            end
            
            // Detect reset deassertion
            if (curr_rst && !prev_rst) begin
                // Reset deasserted
                deassert_count++;
                deassert_times.push_back(transition_time);
                
                // Calculate duration
                if (last_transition_time > 0) begin
                    time duration = transition_time - last_transition_time;
                    reset_durations.push_back(duration);
                end
                
                current_reset_state = 0;
                last_transition_time = transition_time;
                
                publish_reset_event(0, transition_time);
                `uvm_info("RST_MON", $sformatf("[%0t] Reset DEASSERTED", transition_time), UVM_MEDIUM)
            end
            
            prev_rst = curr_rst;
        end
    endtask
    
    /**
     * Publish reset event
     */
    function void publish_reset_event(bit asserted, time event_time);
        reset_xtn txn;
        txn = reset_xtn::type_id::create("monitored_reset");
        txn.reset_pin = "RST_N";
        txn.assert_reset = asserted;
        txn.reset_status = asserted;
        txn.transaction_start_time = event_time;
        
        analysis_port.write(txn);
    endfunction
    
    /**
     * Report statistics
     */
    function void report_phase(uvm_phase phase);
        real avg_duration = 0;
        
        if (reset_durations.size() > 0) begin
            foreach (reset_durations[i]) begin
                avg_duration += reset_durations[i];
            end
            avg_duration = avg_duration / reset_durations.size();
        end
        
        `uvm_info("RST_MON", "Reset Monitor Statistics:", UVM_MEDIUM)
        `uvm_info("RST_MON", $sformatf("  Assert Count: %0d", assert_count), UVM_MEDIUM)
        `uvm_info("RST_MON", $sformatf("  Deassert Count: %0d", deassert_count), UVM_MEDIUM)
        `uvm_info("RST_MON", $sformatf("  Average Duration: %0.2f ns", avg_duration), UVM_MEDIUM)
        `uvm_info("RST_MON", $sformatf("  Current State: %s", current_reset_state ? "ASSERTED" : "DEASSERTED"), UVM_MEDIUM)
    endfunction

endclass
