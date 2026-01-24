# JTAG Agent (IEEE 1149.1) - Quick Start

## Overview

This directory contains a complete IEEE 1149.1 compliant JTAG agent implementation for DFT testing. The agent provides comprehensive support for all standard JTAG TAP controller operations.

## Files

### Enhanced Implementation (Recommended)
- **jtag_xtn.sv** - Enhanced transaction class with full feature set
- **jtag_sequences.sv** - Complete set of JTAG sequences
- **jtag_driver_enhanced.sv** - Enhanced driver with full TAP state machine
- **jtag_monitor_enhanced.sv** - Enhanced monitor with transaction reconstruction
- **jtag_coverage.sv** - Functional coverage collector
- **jtag_agent_enhanced.sv** - Complete enhanced agent

### Original Implementation (Backward Compatibility)
- **jtag_transaction.sv** - Basic transaction class
- **jtag_driver.sv** - Basic driver
- **jtag_monitor.sv** - Basic monitor
- **jtag_agent.sv** - Basic agent

### Common Files
- **jtag_interface.sv** - SystemVerilog interface
- **JTAG_AGENT_DOCUMENTATION.md** - Complete documentation
- **README.md** - This file

## Quick Start

### 1. Use Enhanced Agent

```systemverilog
// In test environment
jtag_agent_enhanced jtag_agent;

// Build phase
jtag_agent = jtag_agent_enhanced::type_id::create("jtag_agent", this);

// Connect interface
uvm_config_db#(virtual jtag_if)::set(this, "jtag_agent*", "vif", jtag_if_inst);
```

### 2. Run Sequences

```systemverilog
// Reset TAP controller
jtag_reset_sequence reset_seq;
reset_seq = jtag_reset_sequence::type_id::create("reset_seq");
reset_seq.start(jtag_agent.sequencer);

// Load instruction
load_instruction_sequence load_ir;
load_ir = load_instruction_sequence::type_id::create("load_ir");
load_ir.ir_code = 8'h00;  // EXTEST
load_ir.ir_length = 4;
load_ir.start(jtag_agent.sequencer);

// Load data register
load_data_register_sequence load_dr;
load_dr = load_data_register_sequence::type_id::create("load_dr");
load_dr.dr_data = 32'h12345678;
load_dr.dr_length = 32;
load_dr.dr_type = DR_IDCODE;
load_dr.start(jtag_agent.sequencer);
```

## Features

✅ Full IEEE 1149.1 TAP state machine (16 states)  
✅ Instruction Register (IR) operations  
✅ Data Register (DR) operations  
✅ Scan shift sequences  
✅ TDI/TDO verification  
✅ Transaction reconstruction in monitor  
✅ Functional coverage  
✅ Comprehensive documentation  

## Documentation

See **JTAG_AGENT_DOCUMENTATION.md** for complete documentation including:
- Transaction class reference
- Sequence reference
- TAP state machine diagram
- Timing diagrams
- Example usage

## References

- IEEE 1149.1-2013: Standard for Test Access Port and Boundary-Scan Architecture
- UVM 1.2 User's Guide
