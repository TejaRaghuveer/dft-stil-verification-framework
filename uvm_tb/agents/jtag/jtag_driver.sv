/**
 * JTAG Driver
 * 
 * Drives JTAG signals (TCK, TMS, TDI) based on transactions received
 * from the sequencer. Handles JTAG TAP state machine transitions.
 */

class jtag_driver extends uvm_driver#(jtag_transaction);
    
    `uvm_component_utils(jtag_driver)
    
    // Virtual interface
    virtual jtag_if vif;
    
    // Configuration
    test_config cfg;
    
    // Current JTAG state
    jtag_state_t current_state;
    
    // Constructor
    function new(string name = "jtag_driver", uvm_component parent = null);
        super.new(name, parent);
        current_state = TEST_LOGIC_RESET;
    endfunction
    
    // Build phase
    function void build_phase(uvm_phase phase);
        super.build_phase(phase);
        
        // Get virtual interface
        if (!uvm_config_db#(virtual jtag_if)::get(this, "", "vif", vif)) begin
            `uvm_fatal("NO_VIF", "Failed to get jtag_if from config_db")
        end
        
        // Get configuration
        if (!uvm_config_db#(test_config)::get(this, "", "cfg", cfg)) begin
            `uvm_warning("NO_CFG", "Failed to get test_config, using defaults")
        end
    endfunction
    
    // Run phase - main driver loop
    task run_phase(uvm_phase phase);
        // Initialize JTAG interface
        initialize_jtag();
        
        forever begin
            seq_item_port.get_next_item(req);
            drive_transaction(req);
            seq_item_port.item_done();
        end
    endtask
    
    // Initialize JTAG interface
    task initialize_jtag();
        vif.tck <= 0;
        vif.tms <= 1;  // Enter Test-Logic-Reset
        vif.tdi <= 0;
        vif.trst_n <= 0;
        
        // Hold reset for configured cycles
        // Generate clock directly (don't wait for posedge that we generate)
        repeat(cfg.jtag_reset_cycles) begin
            #(cfg.jtag_clock_period_ns / 2);
            vif.tck <= 1;
            #(cfg.jtag_clock_period_ns / 2);
            vif.tck <= 0;
        end
        
        vif.trst_n <= 1;
        current_state = TEST_LOGIC_RESET;
        `uvm_info("JTAG_DRV", "JTAG interface initialized", UVM_MEDIUM)
    endtask
    
    // Drive a single transaction
    task drive_transaction(jtag_transaction txn);
        `uvm_info("JTAG_DRV", $sformatf("Driving: %s", txn.convert2string()), UVM_HIGH)
        
        txn.start_time = $time;
        
        // Drive transaction for specified number of cycles
        repeat(txn.cycle_count) begin
            // Set TMS and TDI before rising edge
            vif.tms <= txn.tms;
            vif.tdi <= txn.tdi;
            
            // Generate rising edge
            #(cfg.jtag_clock_period_ns / 2);
            vif.tck <= 1;
            #(cfg.jtag_clock_period_ns / 2);
            
            // Sample TDO on falling edge (before driving clock low)
            txn.tdo = vif.tdo;
            
            // Generate falling edge
            vif.tck <= 0;
            
            // Update state machine
            update_jtag_state(txn.tms);
        end
        
        txn.end_time = $time;
    endtask
    
    // Update JTAG TAP state machine
    function void update_jtag_state(bit tms);
        case (current_state)
            TEST_LOGIC_RESET: current_state = tms ? TEST_LOGIC_RESET : RUN_TEST_IDLE;
            RUN_TEST_IDLE: current_state = tms ? SELECT_DR_SCAN : RUN_TEST_IDLE;
            SELECT_DR_SCAN: current_state = tms ? SELECT_IR_SCAN : CAPTURE_DR;
            CAPTURE_DR: current_state = tms ? EXIT1_DR : SHIFT_DR;
            SHIFT_DR: current_state = tms ? EXIT1_DR : SHIFT_DR;
            EXIT1_DR: current_state = tms ? UPDATE_DR : PAUSE_DR;
            PAUSE_DR: current_state = tms ? EXIT2_DR : PAUSE_DR;
            EXIT2_DR: current_state = tms ? UPDATE_DR : SHIFT_DR;
            UPDATE_DR: current_state = tms ? SELECT_DR_SCAN : RUN_TEST_IDLE;
            SELECT_IR_SCAN: current_state = tms ? TEST_LOGIC_RESET : CAPTURE_IR;
            CAPTURE_IR: current_state = tms ? EXIT1_IR : SHIFT_IR;
            SHIFT_IR: current_state = tms ? EXIT1_IR : SHIFT_IR;
            EXIT1_IR: current_state = tms ? UPDATE_IR : PAUSE_IR;
            PAUSE_IR: current_state = tms ? EXIT2_IR : PAUSE_IR;
            EXIT2_IR: current_state = tms ? UPDATE_IR : SHIFT_IR;
            UPDATE_IR: current_state = tms ? SELECT_DR_SCAN : RUN_TEST_IDLE;
        endcase
    endfunction

endclass
