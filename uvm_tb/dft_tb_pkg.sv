/**
 * DFT Testbench Package
 * 
 * Main package file that includes all UVM testbench components.
 * Import this package in your testbench files.
 */

package dft_tb_pkg;
    
    import uvm_pkg::*;
    `include "uvm_macros.svh"
    
    // Includes
    `include "uvm_tb/utils/defines.sv"
    `include "uvm_tb/env/test_config.sv"
    
    // Interfaces
    `include "uvm_tb/agents/jtag/jtag_interface.sv"
    `include "uvm_tb/agents/clock/clock_interface.sv"
    `include "uvm_tb/agents/reset/reset_interface.sv"
    `include "uvm_tb/agents/pad/pad_interface.sv"
    
    // Transactions
    `include "uvm_tb/agents/jtag/jtag_transaction.sv"
    
    // Agents
    `include "uvm_tb/agents/jtag/jtag_driver.sv"
    `include "uvm_tb/agents/jtag/jtag_monitor.sv"
    `include "uvm_tb/agents/jtag/jtag_agent.sv"
    `include "uvm_tb/agents/clock/clock_driver.sv"
    `include "uvm_tb/agents/clock/clock_agent.sv"
    `include "uvm_tb/agents/reset/reset_driver.sv"
    `include "uvm_tb/agents/reset/reset_agent.sv"
    `include "uvm_tb/agents/pad/pad_driver.sv"
    `include "uvm_tb/agents/pad/pad_agent.sv"
    
    // Environment
    `include "uvm_tb/subscribers/stil/stil_subscriber.sv"
    `include "uvm_tb/env/test_env.sv"
    
    // Sequences
    `include "uvm_tb/sequences/base_sequence.sv"
    `include "uvm_tb/sequences/jtag_sequence.sv"
    
    // Tests
    `include "uvm_tb/tests/base_test.sv"
    `include "uvm_tb/tests/simple_jtag_test.sv"
    
    // Utilities
    `include "uvm_tb/utils/dft_utils.sv"

endpackage
