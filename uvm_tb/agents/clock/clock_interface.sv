/**
 * Clock Interface
 * 
 * SystemVerilog interface for clock signals.
 */

interface clock_if;
    
    logic clk;
    
    // Clocking block
    clocking cb @(posedge clk);
        default input #1step output #2ns;
    endclocking
    
    // Modport for driver
    modport DRIVER(output clk);
    
    // Modport for monitor
    modport MONITOR(input clk, clocking cb);
    
    // Modport for DUT
    modport DUT(input clk);

endinterface
