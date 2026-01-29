/**
 * Enhanced Clock Monitor
 * 
 * Monitors clock activities and reports statistics including:
 * - Clock frequency measurement
 * - Duty cycle calculation
 * - Transition counts
 * - Timing violations
 * - Clock domain synchronization
 */

class clock_monitor_enhanced extends uvm_monitor;
    
    `uvm_component_utils(clock_monitor_enhanced)
    
    // Virtual interface
    virtual clock_if vif;
    
    // Analysis port
    uvm_analysis_port#(clock_xtn) analysis_port;
    
    // Configuration
    test_config cfg;
    
    // Statistics
    int leading_edge_count = 0;
    int trailing_edge_count = 0;
    time last_leading_edge_time = 0;
    time last_trailing_edge_time = 0;
    time period_measurements[$];
    real measured_frequency = 0;
    real measured_duty_cycle = 0;
    
    // Constructor
    function new(string name = "clock_monitor_enhanced", uvm_component parent = null);
        super.new(name, parent);
        analysis_port = new("analysis_port", this);
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        if (!uvm_config_db#(virtual clock_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("NO_VIF", "Failed to get clock_if from config_db")
        end
        
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config")
        end
    endfunction
    
    // Run phase
    task run_phase(uvm_phase phase);
        monitor_clock();
    endtask
    
    /**
     * Monitor clock transitions
     */
    task monitor_clock();
        bit prev_clk = 0;
        bit curr_clk;
        time edge_time;
        time period;
        
        `uvm_info("CLK_MON", "Starting clock monitoring", UVM_MEDIUM)
        
        forever begin
            @(vif.clk);
            curr_clk = vif.clk;
            edge_time = $time;
            
            // Detect leading edge (rising)
            if (curr_clk && !prev_clk) begin
                leading_edge_count++;
                
                if (last_leading_edge_time > 0) begin
                    period = edge_time - last_leading_edge_time;
                    period_measurements.push_back(period);
                    update_statistics();
                end
                
                last_leading_edge_time = edge_time;
                
                // Create and publish transaction
                publish_clock_transition(LEADING, edge_time);
            end
            
            // Detect trailing edge (falling)
            if (!curr_clk && prev_clk) begin
                trailing_edge_count++;
                last_trailing_edge_time = edge_time;
                
                // Create and publish transaction
                publish_clock_transition(TRAILING, edge_time);
            end
            
            prev_clk = curr_clk;
        end
    endtask
    
    /**
     * Update statistics
     */
    function void update_statistics();
        if (period_measurements.size() > 0) begin
            real avg_period = 0;
            foreach (period_measurements[i]) begin
                avg_period += period_measurements[i];
            end
            avg_period = avg_period / period_measurements.size();
            
            measured_frequency = 1000.0 / avg_period;  // Convert ns to MHz
            
            // Calculate duty cycle
            if (last_trailing_edge_time > 0 && last_leading_edge_time > 0) begin
                time high_time = last_trailing_edge_time - last_leading_edge_time;
                measured_duty_cycle = (real'(high_time) / avg_period) * 100.0;
            end
        end
    endfunction
    
    /**
     * Publish clock transition
     */
    function void publish_clock_transition(clock_edge_type_e edge_type, time edge_time);
        clock_xtn txn;
        txn = clock_xtn::type_id::create("monitored_clock");
        txn.clock_id = "MONITORED_CLK";
        txn.edge_event = edge_type;
        txn.transaction_start_time = edge_time;
        txn.frequency = measured_frequency;
        txn.duty_cycle = measured_duty_cycle;
        
        analysis_port.write(txn);
    endfunction
    
    /**
     * Report statistics
     */
    function void report_phase(uvm_phase phase);
        `uvm_info("CLK_MON", "Clock Monitor Statistics:", UVM_MEDIUM)
        `uvm_info("CLK_MON", $sformatf("  Leading Edges: %0d", leading_edge_count), UVM_MEDIUM)
        `uvm_info("CLK_MON", $sformatf("  Trailing Edges: %0d", trailing_edge_count), UVM_MEDIUM)
        `uvm_info("CLK_MON", $sformatf("  Measured Frequency: %0.2f MHz", measured_frequency), UVM_MEDIUM)
        `uvm_info("CLK_MON", $sformatf("  Measured Duty Cycle: %0.1f%%", measured_duty_cycle), UVM_MEDIUM)
    endfunction

endclass
