# Clock and Reset Control Agent Documentation

## Overview

The Control Agent provides unified management of clock and reset signals for DFT test mode control. It coordinates multiple clock domains and reset signals with support for scan mode, timing margin analysis, and comprehensive monitoring.

## Architecture

### Components

1. **Clock Components**
   - `clock_xtn` - Clock transaction class
   - `clock_driver_enhanced` - Enhanced clock driver
   - `clock_monitor_enhanced` - Clock monitor with statistics
   - `clock_sequences` - Pre-defined clock sequences

2. **Reset Components**
   - `reset_xtn` - Reset transaction class
   - `reset_driver_enhanced` - Enhanced reset driver
   - `reset_monitor_enhanced` - Reset monitor
   - `reset_sequences` - Pre-defined reset sequences

3. **Control Agent**
   - `control_agent` - Unified agent coordinating clock and reset

## Clock Transaction (clock_xtn)

### Fields

- `clock_id` (string) - Clock domain identifier ("TCK", "SYSCLK", "TESTCLK")
- `frequency` (real) - Clock frequency in MHz
- `duty_cycle` (real) - Duty cycle percentage (0-100)
- `start_time` / `stop_time` (time) - Clock generation window
- `edge_event` (enum) - LEADING, TRAILING, or BOTH
- `capture_edge` (enum) - Edge for data capture
- `clock_enable` (bit) - Enable/disable clock
- `half_period_clocks` (int) - Number of half-period clocks (for JTAG)

### Methods

- `set_half_period_clocks(n)` - Set number of half-period clocks
- `get_total_cycles()` - Get total clock cycles
- `enable_clock()` / `disable_clock()` - Control clock
- `calculate_period()` - Calculate period from frequency
- `calculate_timing()` - Calculate high/low times

## Reset Transaction (reset_xtn)

### Fields

- `reset_type` (enum) - ASYNC or SYNC
- `reset_pin` (string) - Reset pin identifier
- `duration` (time) - Reset duration
- `delay_from_clock` (time) - Delay from clock edge (sync)
- `polarity` (enum) - ACTIVE_HIGH or ACTIVE_LOW
- `assert_reset` (bit) - Assert or release
- `prevent_glitches` (bit) - Prevent glitches during scan

### Methods

- `get_reset_value()` - Get reset assertion value
- `get_deassert_value()` - Get reset deassertion value
- `is_reset_active(value)` - Check if reset is active

## Clock Driver Features

### Multi-Domain Support

Supports multiple clock domains simultaneously:
- System clock (SYSCLK)
- JTAG clock (TCK)
- Test clock (TESTCLK)

### Half-Period TCK Toggling

For JTAG compliance, supports half-period clock toggling:
```systemverilog
clock_xtn txn;
txn.clock_id = "TCK";
txn.frequency = 10.0;  // 10MHz
txn.set_half_period_clocks(20);  // 10 full cycles
```

### Edge Capture

Captures data on specified edges:
- Leading edge (rising)
- Trailing edge (falling)
- Both edges

### Clock Stop on Demand

For timing margin analysis:
```systemverilog
clock_driver.request_clock_stop();
// Perform timing analysis
clock_driver.resume_clock();
```

### Precise Timing Logging

Logs all clock transitions with precise timing for analysis.

## Reset Driver Features

### Asynchronous Reset

Applies reset immediately without clock synchronization:
```systemverilog
reset_xtn txn;
txn.reset_type = ASYNC;
txn.duration = 100ns;
txn.polarity = ACTIVE_LOW;
```

### Synchronous Reset

Synchronizes reset to clock edges:
```systemverilog
reset_xtn txn;
txn.reset_type = SYNC;
txn.duration = 10 * clock_period;  // 10 cycles
txn.delay_from_clock = 2ns;
```

### Glitch Prevention

Prevents reset glitches during scan mode:
- Automatically blocks reset changes during scan
- Ensures clean reset transitions

### Reset Sequencing

Applies multiple resets in order:
```systemverilog
reset_xtn seq[];
seq = new[2];
seq[0] = reset1;
seq[1] = reset2;
reset_driver.apply_reset_sequence(seq);
```

### Reset Status Feedback

Provides real-time reset status:
```systemverilog
bit status = reset_driver.get_reset_status("RST_N");
string stats = reset_driver.get_reset_statistics("RST_N");
```

## Timing Constraints

### Async Reset Timing

- **Recovery Time**: Time from reset deassertion to clock edge
  - Must be sufficient to avoid metastability
  - Typically 1-2 clock cycles

- **Removal Time**: Time from clock edge to reset deassertion
  - Must be sufficient to avoid race conditions
  - Typically 1-2 clock cycles

- **Reset Pulse Width**: Minimum assertion duration
  - Must be long enough for all flip-flops to reset
  - Typically 2-5 clock cycles

### Sync Reset Timing

- **Setup Time**: Reset must be stable before clock edge
- **Hold Time**: Reset must remain stable after clock edge
- **Clock-to-Reset Delay**: Delay from clock edge to reset assertion

### Edge Cases for Async Reset

1. **Metastability**: Reset deassertion too close to clock edge
   - Solution: Ensure sufficient recovery time

2. **Race Conditions**: Reset and clock changing simultaneously
   - Solution: Synchronize reset deassertion to clock

3. **Partial Reset**: Reset pulse too short
   - Solution: Ensure minimum pulse width

4. **Glitches During Scan**: Reset toggling during scan mode
   - Solution: Enable glitch prevention

## Usage Examples

### Basic Clock Generation

```systemverilog
continuous_clock_sequence clk_seq;
clk_seq = continuous_clock_sequence::type_id::create("clk_seq");
clk_seq.clock_id = "SYSCLK";
clk_seq.frequency = 100.0;  // 100MHz
clk_seq.start(control_agent.clock_sequencer);
```

### JTAG Half-Period Clocks

```systemverilog
half_period_clock_sequence tck_seq;
tck_seq = half_period_clock_sequence::type_id::create("tck_seq");
tck_seq.clock_id = "TCK";
tck_seq.frequency = 10.0;  // 10MHz
tck_seq.num_half_periods = 20;  // 10 full cycles
tck_seq.start(control_agent.clock_sequencer);
```

### Async Reset

```systemverilog
async_reset_sequence rst_seq;
rst_seq = async_reset_sequence::type_id::create("rst_seq");
rst_seq.reset_pin = "RST_N";
rst_seq.polarity = ACTIVE_LOW;
rst_seq.duration = 100ns;
rst_seq.start(control_agent.reset_sequencer);
```

### Sync Reset

```systemverilog
sync_reset_sequence rst_seq;
rst_seq = sync_reset_sequence::type_id::create("rst_seq");
rst_seq.reset_pin = "RST_N";
rst_seq.cycles = 10;
rst_seq.start(control_agent.reset_sequencer);
```

### Coordinated Reset Sequence

```systemverilog
reset_xtn reset_seq[];
reset_seq = new[2];

reset_seq[0] = reset_xtn::type_id::create("rst1");
reset_seq[0].reset_pin = "POR";
reset_seq[0].reset_type = ASYNC;
reset_seq[0].duration = 50ns;

reset_seq[1] = reset_xtn::type_id::create("rst2");
reset_seq[1].reset_pin = "RST_N";
reset_seq[1].reset_type = SYNC;
reset_seq[1].duration = 10 * clock_period;

control_agent.apply_coordinated_reset_sequence(reset_seq);
```

### Scan Mode Control

```systemverilog
// Enable scan mode (stops clocks, locks resets)
control_agent.enable_scan_mode();

// Perform scan operations
// ...

// Disable scan mode (resumes clocks)
control_agent.disable_scan_mode();
```

## Monitoring and Statistics

### Clock Statistics

```systemverilog
string stats = control_agent.get_clock_statistics("SYSCLK");
// Returns: "Clock SYSCLK: Frequency=100.00 MHz, Duty=50.0%"
```

### Reset Statistics

```systemverilog
string stats = control_agent.get_reset_statistics("RST_N");
// Returns detailed reset statistics
```

## Best Practices

1. **Always coordinate clock and reset** during scan mode
2. **Use appropriate reset type** (async for power-on, sync for functional)
3. **Ensure sufficient recovery time** for async reset deassertion
4. **Prevent glitches** during scan mode
5. **Monitor reset status** before critical operations
6. **Use reset sequencing** for complex reset scenarios

## References

- IEEE 1149.1: Standard for Test Access Port
- UVM 1.2 User's Guide
- SystemVerilog LRM
