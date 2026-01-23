# DFT-STIL Verification Framework

A production-grade Design-for-Test (DFT) Verification framework with STIL (Standard Test Interface Language) Pattern Generation using SystemVerilog UVM and Python.

## Overview

This framework provides a complete solution for DFT verification with:
- **UVM Testbench**: Modular, scalable testbench with JTAG, clock, reset, and pad drivers
- **STIL Generation**: IEEE 1450 compliant STIL pattern generation from testbench transactions
- **ATPG Integration**: Parser for ATPG tool outputs (TetraMAX, FastScan, Encounter)
- **GPU Shader Support**: Designed for GPU shader DFT verification context

## Features

- ✅ Complete UVM testbench architecture
- ✅ JTAG TAP controller support
- ✅ Clock and reset management
- ✅ Boundary scan and pad testing
- ✅ IEEE 1450 compliant STIL generation
- ✅ ATPG pattern parsing
- ✅ Project structure validation
- ✅ Multiple simulator support (VCS, QuestaSim, Xcelium)
- ✅ Comprehensive configuration system
- ✅ Example patterns and tests

## Project Structure

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

## Tool Requirements

### Simulators (One of the following)

- **Synopsys VCS** (2020.03 or later)
- **Mentor Graphics QuestaSim** (2020.1 or later)
- **Cadence Xcelium** (20.03 or later)

### UVM Library

- UVM 1.2 or later (typically included with simulators)

### Python

- Python 3.6 or later
- Required packages:
  ```bash
  pip install pyyaml
  ```

### Environment Setup

Set environment variables based on your simulator:

```bash
# For VCS
export VCS_HOME=/path/to/vcs
export PATH=$VCS_HOME/bin:$PATH

# For QuestaSim
export QUESTA_HOME=/path/to/questa
export PATH=$QUESTA_HOME/bin:$PATH

# For Xcelium
export CDS_HOME=/path/to/xcelium
export PATH=$CDS_HOME/tools/bin:$PATH
```

## Quick Start Guide

### 1. Validate Project Structure

```bash
make validate
```

### 2. Generate Example STIL File

```bash
make stil_example
```

This creates `examples/example_pattern.stil` with sample JTAG patterns.

### 3. Compile Testbench

```bash
# Using VCS (default)
make compile

# Using QuestaSim
make SIMULATOR=questa compile

# Using Xcelium
make SIMULATOR=xcelium compile
```

### 4. Run Simulation

```bash
# Run default test
make run

# Run specific test
make TEST_NAME=base_test run

# Using simulation script
./scripts/run_simulation.sh -s vcs -t base_test -v UVM_HIGH
```

### 5. View Results

- **STIL Output**: Check `output.stil` (or configured output file)
- **Waveforms**: Use simulator-specific tools (Verdi, SimVision, etc.)
- **Logs**: Check simulation log files

## Configuration

### Test Configuration

Edit `config/test_config.json` to customize test parameters:

```json
{
  "test_config": {
    "agents": {
      "jtag": {
        "clock_period_ns": 100,
        "reset_cycles": 10
      }
    },
    "stil": {
      "output_file": "output.stil",
      "enable_generation": true
    }
  }
}
```

### UVM Test Configuration

In your test class:

```systemverilog
class my_test extends base_test;
    function void configure_test();
        super.configure_test();
        cfg.jtag_clock_period_ns = 50;  // 20MHz
        cfg.num_test_patterns = 200;
    endfunction
endclass
```

## Creating Custom Tests

### 1. Create a Test Sequence

```systemverilog
class my_sequence extends base_sequence;
    task body();
        jtag_transaction txn;
        repeat(10) begin
            txn = jtag_transaction::type_id::create("txn");
            start_item(txn);
            txn.tms = 0;
            txn.tdi = $urandom();
            finish_item(txn);
        end
    endtask
endclass
```

### 2. Create a Test Case

```systemverilog
class my_test extends base_test;
    task run_test_sequence();
        my_sequence seq = my_sequence::type_id::create("seq");
        seq.start(env.jtag_agent_inst.sequencer);
    endtask
endclass
```

### 3. Run Your Test

```bash
make TEST_NAME=my_test
```

## STIL Pattern Generation

The framework automatically generates STIL patterns during simulation. The STIL subscriber monitors transactions and converts them to IEEE 1450 compliant STIL format.

### Manual STIL Generation

```bash
python python/stil_generator/stil_template_generator.py output.stil
```

## ATPG Pattern Parsing

Parse ATPG tool outputs:

```bash
# TetraMAX
make parse_atpg ATPG_FILE=patterns.tmax ATPG_FORMAT=tetramax

# FastScan
python python/atpg_parser/atpg_parser.py fastscan patterns.fscan

# Encounter
python python/atpg_parser/atpg_parser.py encounter patterns.enc
```

## Documentation

- **[Architecture Guide](docs/ARCHITECTURE.md)**: Detailed architecture documentation
- **[User Guide](docs/USER_GUIDE.md)**: Comprehensive user guide with examples

## Makefile Targets

```bash
make help              # Show all available targets
make compile           # Compile testbench
make run               # Run simulation
make clean             # Clean build artifacts
make stil_example      # Generate example STIL file
make validate          # Validate project structure
make parse_atpg        # Parse ATPG file
```

## GPU Shader Context

The framework is designed for GPU shader DFT verification with:
- Configurable shader core count
- Thread-level testing support
- Scan chain verification
- Boundary scan for I/O pads

Configure in `test_config.sv`:

```systemverilog
cfg.num_shader_cores = 4;
cfg.num_threads_per_core = 64;
cfg.enable_shader_dft_test = 1;
```

## Extension Points

The framework is modular and extensible:

1. **New Agents**: Add under `uvm_tb/agents/`
2. **New Sequences**: Add under `uvm_tb/sequences/`
3. **New Tests**: Extend `base_test` class
4. **New Subscribers**: Add for additional analysis
5. **New ATPG Formats**: Extend `atpg_parser.py`

## Best Practices

1. Always extend base classes rather than modifying them
2. Use configuration objects for test parameters
3. Follow UVM naming conventions
4. Add comprehensive comments for maintainability
5. Validate configurations before use
6. Use proper UVM phases for initialization

## Troubleshooting

### Common Issues

1. **Interface Not Found**: Ensure interfaces are set in config database in `tb_top.sv`
2. **STIL File Not Generated**: Check `cfg.stil_enable_generation = 1`
3. **Compilation Errors**: Verify UVM library path and file includes
4. **Simulation Hangs**: Check for missing objections in test

## Contributing

When extending the framework:
- Follow existing code structure and naming conventions
- Add comprehensive comments
- Update documentation
- Validate with `make validate`

## License

This framework is provided as-is for DFT verification purposes.

## Support

For issues and questions:
- Check documentation in `docs/`
- Review example files in `examples/`
- Validate project structure with `make validate`

---

**Version**: 1.0  
**Last Updated**: 2024
