# JTAG Agent Documentation (IEEE 1149.1 Compliant)

## Overview

This document describes the complete JTAG (IEEE 1149.1) UVM agent implementation for DFT testing. The agent provides comprehensive support for all standard JTAG TAP controller operations including instruction register (IR) and data register (DR) operations, scan shift sequences, and TDI/TDO verification.

## Architecture

### Components

1. **jtag_xtn** - Enhanced transaction class
2. **jtag_sequences** - Complete set of JTAG sequences
3. **jtag_driver_enhanced** - Enhanced driver with full TAP state machine
4. **jtag_monitor_enhanced** - Enhanced monitor that reconstructs transactions
5. **jtag_coverage** - Functional coverage collector
6. **jtag_agent_enhanced** - Complete agent assembly

## Transaction Class (jtag_xtn)

### Fields

#### Signal Vectors
- `tms_vector[]` - TMS sequence for state transitions
- `tdi_vector[]` - TDI data to shift in
- `expected_tdo[]` - Expected TDO response
- `actual_tdo[]` - Actual TDO captured from DUT

#### Sequence Type
- `sequence_type` - Enum: `LOAD_IR`, `LOAD_DR`, `SCAN_SHIFT`, `BYPASS`, `TDI_TDO_CHECK`

#### Instruction Register (IR)
- `ir_code` - Instruction code (e.g., EXTEST=0x00, SAMPLE=0x01)
- `ir_length` - IR length in bits (default 4 for standard JTAG)

#### Data Register (DR)
- `dr_length` - DR length in bits
- `dr_type` - Type: `DR_BYPASS`, `DR_IDCODE`, `DR_BSR`, `DR_DEVICE_ID`, `DR_USER`

#### Timing
- `cycle_count` - Number of TCK cycles
- `start_time` / `end_time` - Transaction timing
- `setup_time_ns` - TMS/TDI setup time (default 10ns)
- `hold_time_ns` - TMS/TDI hold time (default 10ns)

#### State Tracking
- `start_state` / `end_state` / `current_state` - TAP state tracking

#### Verification
- `tdo_match` - TDO comparison result
- `tdo_mismatch_count` - Number of mismatched bits

### Methods

#### Utility Methods
- `get_instruction()` - Get instruction code from IR
- `set_ir_code(code, length)` - Set IR instruction code
- `get_dr_length()` - Get DR length based on type
- `set_dr_data(data, length)` - Set DR data vector
- `set_expected_tdo(expected)` - Set expected TDO response
- `compare_tdo()` - Compare actual vs expected TDO

#### UVM Standard Methods
- `convert2string()` - Convert to string for logging
- `do_copy(rhs)` - Copy transaction
- `do_compare(rhs, comparer)` - Compare transactions

## Sequences

### 1. jtag_reset_sequence

Resets the TAP controller to Test-Logic-Reset state.

**TAP State Path:**
```
Any State -> ... -> Test-Logic-Reset
```

**TMS Pattern:** `11111` (minimum 5 cycles with TMS=1)

**Usage:**
```systemverilog
jtag_reset_sequence reset_seq;
reset_seq = jtag_reset_sequence::type_id::create("reset_seq");
reset_seq.reset_cycles = 5;
reset_seq.start(sequencer);
```

### 2. load_instruction_sequence

Loads an instruction code into the Instruction Register.

**TAP State Path:**
```
Run-Test/Idle -> Select-DR-Scan -> Select-IR-Scan -> Capture-IR -> 
Shift-IR (N cycles) -> Exit1-IR -> Update-IR -> Run-Test/Idle
```

**TMS Pattern:**
- `0` (RTI) -> `1` (SelDR) -> `1` (SelIR) -> `0` (CapIR) -> 
- `0...0` (Shift-IR, N cycles) -> `1` (Exit1-IR) -> `1` (UpdIR) -> `0` (RTI)

**Usage:**
```systemverilog
load_instruction_sequence load_ir_seq;
load_ir_seq = load_instruction_sequence::type_id::create("load_ir_seq");
load_ir_seq.ir_code = 8'h00;  // EXTEST instruction
load_ir_seq.ir_length = 4;
load_ir_seq.start(sequencer);
```

### 3. load_data_register_sequence

Loads data into a Data Register (BSR, Bypass, IDCODE, etc.).

**TAP State Path:**
```
Run-Test/Idle -> Select-DR-Scan -> Capture-DR -> Shift-DR (N cycles) -> 
Exit1-DR -> Update-DR -> Run-Test/Idle
```

**TMS Pattern:**
- `0` (RTI) -> `1` (SelDR) -> `0` (CapDR) -> 
- `0...0` (Shift-DR, N cycles) -> `1` (Exit1-DR) -> `1` (UpdDR) -> `0` (RTI)

**Usage:**
```systemverilog
load_data_register_sequence load_dr_seq;
load_dr_seq = load_data_register_sequence::type_id::create("load_dr_seq");
load_dr_seq.dr_data = 32'h12345678;
load_dr_seq.dr_length = 32;
load_dr_seq.dr_type = DR_IDCODE;
load_dr_seq.start(sequencer);
```

### 4. scan_shift_sequence

Shifts data through the scan chain without capture/update.

**TAP State Path:**
- IR Shift: `Shift-IR` (stay for N cycles)
- DR Shift: `Shift-DR` (stay for N cycles)

**Usage:**
```systemverilog
scan_shift_sequence shift_seq;
shift_seq = scan_shift_sequence::type_id::create("shift_seq");
shift_seq.shift_data = 32'hDEADBEEF;
shift_seq.shift_length = 32;
shift_seq.is_ir = 0;  // 0 for DR, 1 for IR
shift_seq.start(sequencer);
```

### 5. tdi_tdo_check_sequence

Shifts data and verifies TDO response.

**Usage:**
```systemverilog
tdi_tdo_check_sequence check_seq;
check_seq = tdi_tdo_check_sequence::type_id::create("check_seq");
check_seq.input_data = 32'h12345678;
check_seq.expected_output = 32'h87654321;
check_seq.length = 32;
check_seq.is_ir = 0;
check_seq.start(sequencer);
```

## Driver (jtag_driver_enhanced)

### TAP State Machine

The driver implements the complete IEEE 1149.1 TAP state machine with 16 states:

#### States
1. **Test-Logic-Reset (TLR)** - Reset state
2. **Run-Test/Idle (RTI)** - Idle state
3. **Select-DR-Scan (SelDR)** - Route to DR path
4. **Select-IR-Scan (SelIR)** - Route to IR path
5. **Capture-DR/IR** - Capture parallel data
6. **Shift-DR/IR** - Shift serial data
7. **Exit1-DR/IR** - First exit point
8. **Pause-DR/IR** - Pause state (optional)
9. **Exit2-DR/IR** - Second exit point
10. **Update-DR/IR** - Update parallel output

### Timing Constraints

The driver implements IEEE 1149.1 timing constraints:

- **Setup Time:** TMS/TDI must be stable before TCK rising edge
- **Hold Time:** TMS/TDI must remain stable after TCK falling edge
- **TDO Sampling:** TDO is sampled on TCK falling edge

### Key Methods

- `initialize_jtag()` - Initialize interface and enter Test-Logic-Reset
- `drive_transaction(txn)` - Drive a complete transaction
- `drive_generic_sequence(txn)` - Drive TMS/TDI vectors
- `update_tap_state(tms)` - Update TAP state machine
- `is_shift_state(state)` - Check if state is a shift state

## Monitor (jtag_monitor_enhanced)

### Functionality

The monitor:
1. Observes TCK, TMS, TDI, TDO signal transitions
2. Tracks TAP state machine state
3. Reconstructs transactions based on state transitions
4. Publishes transactions via analysis port

### Transaction Reconstruction

The monitor reconstructs transactions when:
- Completed an IR load (Update-IR state)
- Completed a DR load (Update-DR state)
- Completed a scan shift (Exit from shift state)
- Entered Test-Logic-Reset (reset sequence)

### Key Methods

- `monitor_jtag()` - Main monitoring loop
- `update_monitor_tap_state(tms)` - Track TAP state
- `detect_sequence_type()` - Detect sequence type from state transitions
- `reconstruct_transaction(cycles)` - Reconstruct transaction from signals

## Coverage (jtag_coverage)

### Coverage Groups

1. **jtag_tap_state_cg** - TAP state and state transition coverage
2. **jtag_sequence_cg** - Sequence type, IR instruction, DR type coverage
3. **jtag_timing_cg** - Cycle count and transaction duration coverage
4. **jtag_verification_cg** - TDO verification coverage

### Coverage Metrics

- TAP state coverage: All 16 states
- State transition coverage: All valid transitions
- Sequence type coverage: All 5 sequence types
- IR instruction coverage: Standard instructions (EXTEST, SAMPLE, etc.)
- DR type coverage: All DR types
- TDO verification coverage: Match/mismatch scenarios

## Agent (jtag_agent_enhanced)

### Configuration

The agent can be configured for:
- **Active Mode:** Drives signals (driver + sequencer)
- **Passive Mode:** Monitors only (monitor only)
- **Coverage:** Enable/disable coverage collection

### Usage

```systemverilog
// In test environment
jtag_agent_enhanced jtag_agent;

// Build phase
jtag_agent = jtag_agent_enhanced::type_id::create("jtag_agent", this);

// Connect to interface
uvm_config_db#(virtual jtag_if)::set(this, "jtag_agent*", "vif", jtag_if_inst);

// Run sequences
load_instruction_sequence load_ir;
load_ir = load_instruction_sequence::type_id::create("load_ir");
load_ir.ir_code = 8'h00;
load_ir.start(jtag_agent.sequencer);
```

## TAP State Machine Diagram

```
                    Test-Logic-Reset
                         /|\
                          | TMS=1
                          |
                    [Any State]
                          |
                          | TMS=0 (5+ cycles)
                          |
                    Run-Test/Idle
                    /           \
            TMS=0 /             \ TMS=1
                /               \
         [Stay]          Select-DR-Scan
                            /       \
                    TMS=0 /         \ TMS=1
                        /           \
                Capture-DR    Select-IR-Scan
                    /               \
            TMS=0 /                 \ TMS=1
                /                   \
         Shift-DR              Capture-IR
            /                       \
    TMS=0 /                         \ TMS=0
        /                             \
[Stay]                           Shift-IR
    |                                 |
    | TMS=1                           | TMS=1
    |                                 |
Exit1-DR                        Exit1-IR
    / \                             / \
TMS=0|1                         TMS=0|1
   /   \                           /   \
Pause-DR Update-DR          Pause-IR Update-IR
   |       |                       |       |
   |       |                       |       |
Exit2-DR   |                   Exit2-IR   |
   |       |                       |       |
   |       |                       |       |
   \-------/                       \-------/
```

## Timing Diagram

```
TCK:  _|‾|_|‾|_|‾|_|‾|_|‾|_
      |   |   |   |   |   |
TMS:  ___|‾‾‾|___|‾‾‾|___
      setup|hold|setup|hold
TDI:  ___|‾‾‾|___|‾‾‾|___
      setup|hold|setup|hold
TDO:  ________|‾‾‾|___|‾‾‾
              valid
```

## Example Usage

### Complete JTAG Test Flow

```systemverilog
class jtag_test_sequence extends uvm_sequence#(jtag_xtn);
    task body();
        // 1. Reset TAP controller
        jtag_reset_sequence reset_seq;
        reset_seq = jtag_reset_sequence::type_id::create("reset_seq");
        reset_seq.start(m_sequencer);
        
        // 2. Load EXTEST instruction
        load_instruction_sequence load_ir;
        load_ir = load_instruction_sequence::type_id::create("load_ir");
        load_ir.ir_code = 8'h00;  // EXTEST
        load_ir.ir_length = 4;
        load_ir.start(m_sequencer);
        
        // 3. Load boundary scan data
        load_data_register_sequence load_dr;
        load_dr = load_data_register_sequence::type_id::create("load_dr");
        load_dr.dr_data = 32'hFFFFFFFF;
        load_dr.dr_length = 32;
        load_dr.dr_type = DR_BSR;
        load_dr.start(m_sequencer);
        
        // 4. Shift and verify
        tdi_tdo_check_sequence check_seq;
        check_seq = tdi_tdo_check_sequence::type_id::create("check_seq");
        check_seq.input_data = 32'h12345678;
        check_seq.expected_output = 32'h87654321;
        check_seq.length = 32;
        check_seq.start(m_sequencer);
    endtask
endclass
```

## References

- IEEE 1149.1-2013: Standard for Test Access Port and Boundary-Scan Architecture
- UVM 1.2 User's Guide
- SystemVerilog LRM

## Revision History

- Version 1.0: Initial implementation with full IEEE 1149.1 support
