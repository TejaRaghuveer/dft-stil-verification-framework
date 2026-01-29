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
    `include "uvm_tb/agents/jtag/jtag_xtn.sv"  // Enhanced transaction class
    
    // Enhanced JTAG Agent Components (IEEE 1149.1)
    `include "uvm_tb/agents/jtag/jtag_sequences.sv"  // JTAG sequences
    `include "uvm_tb/agents/jtag/jtag_driver_enhanced.sv"  // Enhanced driver
    `include "uvm_tb/agents/jtag/jtag_monitor_enhanced.sv"  // Enhanced monitor
    `include "uvm_tb/agents/jtag/jtag_coverage.sv"  // Coverage collector
    `include "uvm_tb/agents/jtag/jtag_agent_enhanced.sv"  // Enhanced agent
    
    // Enhanced Clock Agent Components
    `include "uvm_tb/agents/clock/clock_xtn.sv"
    `include "uvm_tb/agents/clock/clock_sequences.sv"
    `include "uvm_tb/agents/clock/clock_driver_enhanced.sv"
    `include "uvm_tb/agents/clock/clock_monitor_enhanced.sv"
    
    // Enhanced Reset Agent Components
    `include "uvm_tb/agents/reset/reset_xtn.sv"
    `include "uvm_tb/agents/reset/reset_sequences.sv"
    `include "uvm_tb/agents/reset/reset_driver_enhanced.sv"
    `include "uvm_tb/agents/reset/reset_monitor_enhanced.sv"
    
    // Unified Control Agent
    `include "uvm_tb/agents/control/control_agent.sv"
    
    // Original Agent Components (for backward compatibility)
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
