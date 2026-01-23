/**
 * UVM Testbench Top Module
 * 
 * This is the top-level testbench module that instantiates the DUT
 * and connects it to the UVM testbench environment. It also handles
 * clock generation and global reset.
 * 
 * For GPU shader verification context, this testbench can be adapted
 * to verify DFT logic within GPU shader cores.
 */

`timescale 1ns/1ps

// Import UVM and testbench package
import uvm_pkg::*;
`include "uvm_macros.svh"
import dft_tb_pkg::*;

module tb_top;

    // Clock and Reset signals
    logic clk;
    logic rst_n;
    
    // JTAG Interface signals
    logic tck;      // JTAG Clock
    logic tms;      // JTAG Mode Select
    logic tdi;      // JTAG Data Input
    logic tdo;      // JTAG Data Output
    logic trst_n;   // JTAG Reset (active low)
    
    // Pad Interface signals (for boundary scan and I/O control)
    localparam NUM_PADS = 32;
    logic [NUM_PADS-1:0] pad_in;
    logic [NUM_PADS-1:0] pad_out;
    logic [NUM_PADS-1:0] pad_oe;  // Output enable
    
    // Clock generation - 100MHz default
    initial begin
        clk = 0;
        forever #5ns clk = ~clk;  // 10ns period = 100MHz
    end
    
    // Global reset generation
    initial begin
        rst_n = 0;
        #100ns;
        rst_n = 1;
    end
    
    // DUT Instantiation
    // Replace with actual DUT module name and ports
    // Note: Uncomment and modify when you have your actual DUT
    /*
    dut_wrapper dut_inst (
        .clk(clk),
        .rst_n(rst_n),
        .tck(tck),
        .tms(tms),
        .tdi(tdi),
        .tdo(tdo),
        .trst_n(trst_n),
        .pad_in(pad_in),
        .pad_out(pad_out),
        .pad_oe(pad_oe)
    );
    */
    
    // Temporary: Connect TDO for testing without DUT
    assign tdo = tdi;
    
    // UVM Interface Instantiations
    jtag_if jtag_if_inst (
        .tck(tck),
        .tms(tms),
        .tdi(tdi),
        .tdo(tdo),
        .trst_n(trst_n)
    );
    
    clock_if clock_if_inst (
        .clk(clk)
    );
    
    reset_if reset_if_inst (
        .rst_n(rst_n)
    );
    
    pad_if pad_if_inst (
        .pad_in(pad_in),
        .pad_out(pad_out),
        .pad_oe(pad_oe)
    );
    
    // UVM Initial Block
    initial begin
        // Set interfaces in config database
        uvm_config_db#(virtual jtag_if)::set(null, "uvm_test_top.env.jtag_agent", "vif", jtag_if_inst);
        uvm_config_db#(virtual clock_if)::set(null, "uvm_test_top.env.clock_agent", "vif", clock_if_inst);
        uvm_config_db#(virtual reset_if)::set(null, "uvm_test_top.env.reset_agent", "vif", reset_if_inst);
        uvm_config_db#(virtual pad_if)::set(null, "uvm_test_top.env.pad_agent", "vif", pad_if_inst);
        
        // Run UVM test
        run_test();
    end
    
    // Dump waveforms (VCD/FSDB)
    initial begin
        if ($test$plusargs("vcd")) begin
            $dumpfile("tb_top.vcd");
            $dumpvars(0, tb_top);
        end
    end

endmodule
