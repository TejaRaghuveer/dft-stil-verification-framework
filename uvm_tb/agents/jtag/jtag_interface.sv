/**
 * JTAG Interface
 * 
 * SystemVerilog interface for JTAG signals.
 * Connects the DUT to the UVM testbench.
 */

interface jtag_if;
    
    // JTAG Signals
    logic tck;      // JTAG Clock
    logic tms;      // JTAG Mode Select
    logic tdi;      // JTAG Data Input
    logic tdo;      // JTAG Data Output
    logic trst_n;   // JTAG Reset (active low)
    
    // Clocking block for driver
    clocking driver_cb @(posedge tck);
        default input #1step output #2ns;
        output tms, tdi, trst_n;
        input tdo;
    endclocking
    
    // Clocking block for monitor
    clocking monitor_cb @(posedge tck);
        default input #1step;
        input tms, tdi, tdo, trst_n;
    endclocking
    
    // Modport for driver
    modport DRIVER(clocking driver_cb, output tck);
    
    // Modport for monitor
    modport MONITOR(clocking monitor_cb, input tck);
    
    // Modport for DUT
    modport DUT(input tck, tms, tdi, trst_n, output tdo);

endinterface
