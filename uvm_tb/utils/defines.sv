/**
 * Global Defines
 * 
 * Project-wide defines and parameters.
 * Include this file in your testbench files as needed.
 */

`ifndef DFT_DEFINES_SV
`define DFT_DEFINES_SV

// Number of pads (adjust based on your design)
`define NUM_PADS 32

// Default clock periods (in nanoseconds)
`define DEFAULT_CLK_PERIOD_NS 10
`define DEFAULT_JTAG_CLK_PERIOD_NS 100

// Default reset cycles
`define DEFAULT_RST_CYCLES 100

// UVM verbosity levels (if not using UVM defines)
`ifndef UVM_NONE
`define UVM_NONE 0
`endif

`ifndef UVM_LOW
`define UVM_LOW 100
`endif

`ifndef UVM_MEDIUM
`define UVM_MEDIUM 200
`endif

`ifndef UVM_HIGH
`define UVM_HIGH 300
`endif

`ifndef UVM_FULL
`define UVM_FULL 400
`endif

`ifndef UVM_DEBUG
`define UVM_DEBUG 500
`endif

`endif // DFT_DEFINES_SV
