# DFT-STIL Verification Framework Architecture

## Overview

This document describes the architecture of the DFT-STIL Verification Framework for Design-for-Test (DFT) verification with STIL (Standard Test Interface Language) pattern generation using SystemVerilog UVM and Python.

## Directory Structure

```
.
├── uvm_tb/              # UVM testbench components
│   ├── agents/         # UVM agents (JTAG, clock, reset, pad)
│   ├── env/            # Test environment and configuration
│   ├── sequences/      # Test sequences
│   ├── subscribers/    # UVM subscribers (STIL generator)
│   ├── tests/          # Test cases
│   ├── utils/          # Utility functions
│   └── tb_top.sv       # Top-level testbench
├── python/             # Python scripts
│   ├── stil_generator/ # STIL file generation
│   ├── atpg_parser/    # ATPG pattern parsing
│   ├── validators/     # File validation
│   └── utils/          # Python utilities
├── config/             # Configuration files
├── examples/           # Example files
├── docs/               # Documentation
└── scripts/            # Simulation scripts and Makefiles
```

## UVM Testbench Architecture

### Testbench Top (`tb_top.sv`)

The top-level module that:
- Instantiates the DUT
- Generates clocks and resets
- Instantiates UVM interfaces
- Connects interfaces to the UVM testbench via config database
- Handles waveform dumping

### Test Environment (`test_env.sv`)

The UVM environment that:
- Instantiates all agents (JTAG, clock, reset, pad)
- Instantiates subscribers (STIL generator)
- Connects analysis ports
- Manages configuration

### Agents

#### JTAG Agent
- **Driver**: Drives JTAG signals (TCK, TMS, TDI) based on transactions
- **Monitor**: Monitors JTAG interface and converts to transactions
- **Sequencer**: Manages sequence execution
- **Interface**: `jtag_if` - SystemVerilog interface for JTAG signals

#### Clock Agent
- **Driver**: Generates clock signals with configurable frequency and duty cycle
- **Interface**: `clock_if` - SystemVerilog interface for clock

#### Reset Agent
- **Driver**: Controls reset assertion/deassertion
- **Interface**: `reset_if` - SystemVerilog interface for reset

#### Pad Agent
- **Driver**: Drives pad interface for boundary scan and I/O testing
- **Interface**: `pad_if` - SystemVerilog interface for pads

### STIL Subscriber

The `stil_subscriber` class:
- Subscribes to transaction streams from agents
- Converts transactions to STIL format (IEEE 1450 compliant)
- Writes STIL patterns to file
- Generates complete STIL files with headers, signals, timing, and patterns

## Python Components

### STIL Generator (`stil_template_generator.py`)

Generates IEEE 1450 compliant STIL files with:
- Signal definitions
- Timing information
- Test patterns
- Procedures

### ATPG Parser (`atpg_parser.py`)

Parses ATPG tool output files from:
- Synopsys TetraMAX
- Mentor Graphics FastScan
- Cadence Encounter Test

Converts to internal format for STIL generation.

### File Validator (`file_validator.py`)

Validates:
- Project directory structure
- Required files
- STIL file syntax
- Configuration file format (JSON/YAML)

## Configuration System

### Test Configuration (`test_config.sv`)

Central configuration class with:
- Agent settings (active/passive, timing)
- STIL file paths
- Pattern generation settings
- Coverage configuration
- Debug and logging options
- GPU shader specific settings

### Configuration Files

- `config/test_config.json`: JSON configuration file
- Can be extended to support YAML format

## Data Flow

1. **Test Sequence** → Generates transactions
2. **Agent Sequencer** → Manages sequence execution
3. **Agent Driver** → Drives DUT signals
4. **Agent Monitor** → Captures DUT responses
5. **STIL Subscriber** → Converts transactions to STIL format
6. **STIL File** → Generated output file

## GPU Shader Context

The framework is adaptable for GPU shader verification:
- Configurable number of shader cores
- Thread-level testing support
- Scan chain verification for shader logic
- Boundary scan for I/O pads

## Extension Points

The framework is intentionally extensible:

1. **New Agents**: Add new agent directories under `uvm_tb/agents/`
2. **New Sequences**: Add sequence files under `uvm_tb/sequences/`
3. **New Tests**: Extend `base_test` class
4. **New Subscribers**: Add subscribers for additional analysis
5. **New ATPG Formats**: Extend `atpg_parser.py` with new format parsers

## Best Practices

1. Always extend base classes rather than modifying them
2. Use configuration objects for test parameters
3. Follow UVM naming conventions
4. Add comprehensive comments for maintainability
5. Validate configurations before use
6. Use proper UVM phases for initialization

## Maintainer

- **Raghuveer**
- GitHub / LinkedIn: [https://github.com/TejaRaghuveer](https://github.com/TejaRaghuveer)
- Email: `tejaraghuveer@gmail.com`
