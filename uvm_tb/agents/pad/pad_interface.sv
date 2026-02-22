/**
 * Pad Interface
 * 
 * SystemVerilog interface for pad signals.
 * Supports bidirectional pads with output enable control.
 */

interface pad_if;
    
    parameter NUM_PADS = 32;
    
    // Reference clock for setup/hold timing (optional, can be driven by testbench)
    logic clk;
    
    // Pad signals
    logic [NUM_PADS-1:0] pad_in;   // Pad input (from DUT perspective)
    logic [NUM_PADS-1:0] pad_out;  // Pad output (to DUT)
    logic [NUM_PADS-1:0] pad_oe;   // Output enable (1=output, 0=input)
    
    // Clocking block
    clocking cb @(posedge clk);
        default input #1step output #2ns;
        output pad_out, pad_oe;
        input pad_in;
    endclocking
    
    // Modport for driver
    modport DRIVER(clocking cb, output pad_out, pad_oe, input pad_in);
    
    // Modport for monitor
    modport MONITOR(input pad_in, pad_out, pad_oe);
    
    // Modport for DUT
    modport DUT(input pad_out, pad_oe, output pad_in);

endinterface
