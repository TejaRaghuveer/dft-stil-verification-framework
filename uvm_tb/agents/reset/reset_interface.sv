/**
 * Reset Interface
 * 
 * SystemVerilog interface for reset signals.
 */

interface reset_if;
    
    logic rst_n;
    logic clk;  // Reference clock for synchronous reset
    
    // Clocking block
    clocking cb @(posedge clk);
        default input #1step output #2ns;
        output rst_n;
    endclocking
    
    // Modport for driver
    modport DRIVER(output rst_n, input clk, clocking cb);
    
    // Modport for monitor
    modport MONITOR(input rst_n, clk);
    
    // Modport for DUT
    modport DUT(input rst_n);

endinterface
