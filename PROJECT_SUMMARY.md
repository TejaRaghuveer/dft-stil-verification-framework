# DFT-STIL Verification Framework - Project Summary

## Project Overview

This is a complete, production-grade Design-for-Test (DFT) Verification framework with STIL (Standard Test Interface Language) Pattern Generation using SystemVerilog UVM and Python. The framework is designed to be modular, scalable, and adaptable for GPU shader verification contexts.

## Project Structure

```
DFT-STIL verification/
├── uvm_tb/                    # UVM Testbench Components
│   ├── agents/                # UVM Agents
│   │   ├── jtag/             # JTAG Agent (driver, monitor, sequencer)
│   │   ├── clock/            # Clock Agent
│   │   ├── reset/            # Reset Agent
│   │   └── pad/              # Pad Agent
│   ├── env/                  # Test Environment
│   │   ├── test_config.sv   # Configuration class
│   │   └── test_env.sv       # Top-level environment
│   ├── sequences/            # Test Sequences
│   │   ├── base_sequence.sv
│   │   └── jtag_sequence.sv
│   ├── subscribers/          # UVM Subscribers
│   │   └── stil/            # STIL pattern generator
│   ├── tests/                # Test Cases
│   │   ├── base_test.sv
│   │   └── simple_jtag_test.sv
│   ├── utils/                # Utilities
│   │   ├── defines.sv       # Global defines
│   │   └── dft_utils.sv     # DFT utility functions
│   ├── dft_tb_pkg.sv        # Main package file
│   └── tb_top.sv            # Top-level testbench
│
├── python/                   # Python Scripts
│   ├── stil_generator/      # STIL file generation (IEEE 1450)
│   │   ├── __init__.py
│   │   └── stil_template_generator.py
│   ├── atpg_parser/         # ATPG pattern parsing
│   │   ├── __init__.py
│   │   └── atpg_parser.py
│   ├── validators/          # File validation
│   │   ├── __init__.py
│   │   └── file_validator.py
│   └── utils/               # Python utilities
│       └── __init__.py
│
├── config/                  # Configuration Files
│   └── test_config.json    # Default test configuration
│
├── examples/                # Example Files
│   └── example_dut_wrapper.sv
│
├── docs/                    # Documentation
│   ├── ARCHITECTURE.md     # Architecture documentation
│   ├── USER_GUIDE.md       # User guide
│   └── API_REFERENCE.md    # API reference
│
├── scripts/                 # Scripts and Makefiles
│   ├── Makefile           # Build and simulation Makefile
│   ├── run_simulation.sh  # Simulation runner script
│   └── setup_env.sh       # Environment setup script
│
├── README.md               # Main README
├── PROJECT_SUMMARY.md      # This file
└── .gitignore             # Git ignore file
```

## Key Features

### 1. UVM Testbench
- **Complete Agent Architecture**: JTAG, Clock, Reset, and Pad agents
- **Modular Design**: Easy to extend with new agents and components
- **Configuration System**: Centralized configuration via `test_config` class
- **STIL Integration**: Automatic STIL pattern generation from transactions

### 2. STIL Generation
- **IEEE 1450 Compliant**: Generates standard-compliant STIL files
- **Automatic Generation**: UVM subscriber monitors transactions and generates patterns
- **Manual Generation**: Python script for standalone STIL file generation
- **Flexible**: Supports custom signal definitions, timing, and patterns

### 3. ATPG Integration
- **Multi-Format Support**: Parses TetraMAX, FastScan, and Encounter outputs
- **STIL Conversion**: Converts ATPG patterns to STIL format
- **Extensible**: Easy to add support for new ATPG formats

### 4. Validation
- **Structure Validation**: Validates project directory structure
- **File Validation**: Validates STIL and configuration files
- **Syntax Checking**: Basic syntax validation for STIL files

### 5. Multi-Simulator Support
- **VCS**: Synopsys VCS support
- **QuestaSim**: Mentor Graphics QuestaSim support
- **Xcelium**: Cadence Xcelium support
- **Unified Makefile**: Single Makefile for all simulators

## Components Breakdown

### UVM Components

1. **JTAG Agent** (`uvm_tb/agents/jtag/`)
   - `jtag_transaction.sv`: Transaction class with TMS, TDI, TDO
   - `jtag_driver.sv`: Drives JTAG signals with TAP state machine
   - `jtag_monitor.sv`: Monitors JTAG interface
   - `jtag_agent.sv`: Complete agent with driver, monitor, sequencer
   - `jtag_interface.sv`: SystemVerilog interface

2. **Clock Agent** (`uvm_tb/agents/clock/`)
   - `clock_driver.sv`: Generates clock with configurable frequency
   - `clock_agent.sv`: Clock agent wrapper
   - `clock_interface.sv`: Clock interface

3. **Reset Agent** (`uvm_tb/agents/reset/`)
   - `reset_driver.sv`: Controls reset assertion/deassertion
   - `reset_agent.sv`: Reset agent wrapper
   - `reset_interface.sv`: Reset interface

4. **Pad Agent** (`uvm_tb/agents/pad/`)
   - `pad_driver.sv`: Drives pad interface for boundary scan
   - `pad_agent.sv`: Pad agent wrapper
   - `pad_interface.sv`: Pad interface with bidirectional support

5. **STIL Subscriber** (`uvm_tb/subscribers/stil/`)
   - `stil_subscriber.sv`: Monitors transactions and generates STIL files

6. **Test Environment** (`uvm_tb/env/`)
   - `test_env.sv`: Top-level environment connecting all components
   - `test_config.sv`: Comprehensive configuration class

### Python Components

1. **STIL Generator** (`python/stil_generator/`)
   - Generates IEEE 1450 compliant STIL files
   - Supports signal definitions, timing, patterns, procedures
   - Example generator included

2. **ATPG Parser** (`python/atpg_parser/`)
   - Parses TetraMAX, FastScan, Encounter formats
   - Converts to internal format for STIL generation
   - Extensible for new formats

3. **File Validator** (`python/validators/`)
   - Validates project structure
   - Validates STIL syntax
   - Validates configuration files

## Configuration

### Test Configuration

The `test_config` class provides comprehensive configuration:

- **Agent Settings**: Active/passive mode, timing parameters
- **STIL Settings**: Input/output files, generation flags
- **Pattern Settings**: Number of patterns, repeat count
- **Coverage Settings**: Functional/code coverage options
- **Debug Settings**: Verbosity, waveform dumping
- **GPU Shader Settings**: Shader-specific parameters

### Configuration Files

- `config/test_config.json`: JSON configuration file
- Can be extended to support YAML format

## Usage Examples

### Running a Test

```bash
# Using Makefile
make SIMULATOR=vcs TEST_NAME=simple_jtag_test

# Using simulation script
./scripts/run_simulation.sh -s vcs -t simple_jtag_test
```

### Generating STIL File

```bash
# Automatic (during simulation)
# Configure in test_config: stil_enable_generation = 1

# Manual
python python/stil_generator/stil_template_generator.py output.stil
```

### Parsing ATPG File

```bash
make parse_atpg ATPG_FILE=patterns.tmax ATPG_FORMAT=tetramax
```

### Validating Project

```bash
make validate
```

## Documentation

- **README.md**: Quick start guide and overview
- **docs/ARCHITECTURE.md**: Detailed architecture documentation
- **docs/USER_GUIDE.md**: Comprehensive user guide with examples
- **docs/API_REFERENCE.md**: Complete API reference

## Extension Points

The framework is designed for extensibility:

1. **New Agents**: Add under `uvm_tb/agents/`
2. **New Sequences**: Add under `uvm_tb/sequences/`
3. **New Tests**: Extend `base_test` class
4. **New Subscribers**: Add for additional analysis
5. **New ATPG Formats**: Extend `atpg_parser.py`
6. **Custom DUT**: Replace `example_dut_wrapper.sv`

## Best Practices

1. **Extend, Don't Modify**: Always extend base classes
2. **Use Configuration**: Don't hardcode parameters
3. **Follow Conventions**: Use UVM naming conventions
4. **Add Comments**: Document all customizations
5. **Validate**: Use validators before simulation
6. **Version Control**: Use `.gitignore` for build artifacts

## Tool Requirements

- **Simulator**: VCS, QuestaSim, or Xcelium
- **UVM**: UVM 1.2 or later
- **Python**: Python 3.6+ with pyyaml
- **Environment**: Set VCS_HOME, QUESTA_HOME, or CDS_HOME

## GPU Shader Context

The framework is designed for GPU shader DFT verification:

- Configurable shader core count
- Thread-level testing support
- Scan chain verification
- Boundary scan for I/O pads
- Shader-specific DFT test modes

## Status

✅ **Complete**: All core components implemented
✅ **Documented**: Comprehensive documentation provided
✅ **Tested Structure**: Project structure validated
✅ **Examples**: Example files and tests included

## Next Steps

1. **Integrate DUT**: Replace `example_dut_wrapper.sv` with actual DUT
2. **Customize Tests**: Create test cases for your specific requirements
3. **Extend Agents**: Add agents for additional interfaces if needed
4. **Configure**: Adjust configuration for your design
5. **Run Tests**: Execute tests and analyze results

## Support

For questions and issues:
- Review documentation in `docs/`
- Check example files in `examples/`
- Validate project structure with `make validate`
- Review API reference in `docs/API_REFERENCE.md`

---

**Project Version**: 1.0  
**Created**: 2024  
**Framework**: SystemVerilog UVM + Python  
**Standard**: IEEE 1450 (STIL)
