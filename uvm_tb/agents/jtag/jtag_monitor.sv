/**
 * JTAG Monitor
 * 
 * Monitors JTAG interface signals and converts them to transactions.
 * Publishes transactions via analysis port for subscribers.
 */

class jtag_monitor extends uvm_monitor;
    
    `uvm_component_utils(jtag_monitor)
    
    // Virtual interface
    virtual jtag_if vif;
    
    // Analysis port for publishing transactions
    uvm_analysis_port#(jtag_transaction) analysis_port;
    
    // Configuration
    test_config cfg;
    
    // Constructor
    function new(string name = "jtag_monitor", uvm_component parent = null);
        super.new(name, parent);
        analysis_port = new("analysis_port", this);
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        if (!uvm_config_db#(virtual jtag_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("NO_VIF", "Failed to get jtag_if from config_db")
        end
        
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config")
        end
    endfunction
    
    // Run phase - monitor loop
    task run_phase(uvm_phase phase);
        monitor_jtag();
    endtask
    
    // Monitor JTAG interface
    task monitor_jtag();
        jtag_transaction txn;
        
        forever begin
            @(vif.monitor_cb);
            
            txn = jtag_transaction::type_id::create("txn");
            txn.tms = vif.monitor_cb.tms;
            txn.tdi = vif.monitor_cb.tdi;
            txn.tdo = vif.monitor_cb.tdo;
            txn.start_time = $time;
            
            `uvm_info("JTAG_MON", $sformatf("Monitored: %s", txn.convert2string()), UVM_HIGH)
            
            // Publish transaction
            analysis_port.write(txn);
        end
    endtask

endclass
