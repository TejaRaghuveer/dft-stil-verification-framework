# Quick Reference - DFT-STIL Verification Framework

## Common Commands

### Project Validation
```bash
make validate
# or
python python/validators/file_validator.py
```

### Generate Example STIL
```bash
make stil_example
# or
python python/stil_generator/stil_template_generator.py examples/example.stil
```

### Compile Testbench
```bash
make compile                    # VCS (default)
make SIMULATOR=questa compile   # QuestaSim
make SIMULATOR=xcelium compile  # Xcelium
```

### Run Simulation
```bash
make run                        # Default test
make TEST_NAME=simple_jtag_test run
./scripts/run_simulation.sh -s vcs -t base_test
```

### Parse ATPG File
```bash
make parse_atpg ATPG_FILE=patterns.tmax ATPG_FORMAT=tetramax
# or
python python/atpg_parser/atpg_parser.py tetramax patterns.tmax
```

### Clean Build Artifacts
```bash
make clean
```

## File Locations

### Key Files
- **Testbench Top**: `uvm_tb/tb_top.sv`
- **Package**: `uvm_tb/dft_tb_pkg.sv`
- **Config**: `uvm_tb/env/test_config.sv`
- **Environment**: `uvm_tb/env/test_env.sv`
- **Base Test**: `uvm_tb/tests/base_test.sv`

### Agents
- **JTAG**: `uvm_tb/agents/jtag/`
- **Clock**: `uvm_tb/agents/clock/`
- **Reset**: `uvm_tb/agents/reset/`
- **Pad**: `uvm_tb/agents/pad/`

### Python Scripts
- **STIL Generator**: `python/stil_generator/stil_template_generator.py`
- **ATPG Parser**: `python/atpg_parser/atpg_parser.py`
- **Validator**: `python/validators/file_validator.py`

## Configuration

### Test Configuration (test_config.sv)
```systemverilog
cfg.jtag_clock_period_ns = 100;      // 10MHz
cfg.clock_period_ns = 10;             // 100MHz
cfg.num_test_patterns = 100;
cfg.stil_enable_generation = 1;
cfg.stil_output_file = "output.stil";
cfg.verbosity = UVM_MEDIUM;
```

### JSON Configuration (test_config.json)
```json
{
  "test_config": {
    "agents": {
      "jtag": {
        "clock_period_ns": 100
      }
    },
    "stil": {
      "output_file": "output.stil",
      "enable_generation": true
    }
  }
}
```

## Creating Tests

### 1. Create Sequence
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

### 2. Create Test
```systemverilog
class my_test extends base_test;
    function void configure_test();
        super.configure_test();
        cfg.num_test_patterns = 50;
    endfunction
    
    task run_test_sequence();
        my_sequence seq = my_sequence::type_id::create("seq");
        seq.start(env.jtag_agent_inst.sequencer);
    endtask
endclass
```

### 3. Run Test
```bash
make TEST_NAME=my_test
```

## STIL Generation

### Automatic (During Simulation)
```systemverilog
cfg.stil_enable_generation = 1;
cfg.stil_output_file = "patterns.stil";
```

### Manual (Python)
```python
from python.stil_generator import STILTemplateGenerator, STILSignal

generator = STILTemplateGenerator("output.stil")
generator.add_signal(STILSignal("TCK", "In", "Digital"))
generator.write_file()
```

## ATPG Formats

Supported formats:
- `tetramax` - Synopsys TetraMAX
- `fastscan` - Mentor Graphics FastScan
- `encounter` - Cadence Encounter Test

## Environment Variables

### VCS
```bash
export VCS_HOME=/path/to/vcs
export PATH=$VCS_HOME/bin:$PATH
```

### QuestaSim
```bash
export QUESTA_HOME=/path/to/questa
export PATH=$QUESTA_HOME/bin:$PATH
export UVM_HOME=$QUESTA_HOME/verilog_src/uvm-1.2
```

### Xcelium
```bash
export CDS_HOME=/path/to/xcelium
export PATH=$CDS_HOME/tools/bin:$PATH
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| UVM not found | Set `UVM_HOME` environment variable |
| Simulator not found | Set `*_HOME` and add to `PATH` |
| Python module error | Run `pip install -r requirements.txt` |
| Compilation error | Check UVM path in Makefile |
| STIL not generated | Check `cfg.stil_enable_generation = 1` |

## Documentation

- **README.md**: Overview and quick start
- **SETUP.md**: Detailed setup instructions
- **docs/ARCHITECTURE.md**: Architecture details
- **docs/USER_GUIDE.md**: Comprehensive user guide
- **docs/API_REFERENCE.md**: Complete API reference
- **PROJECT_SUMMARY.md**: Project summary

## Project Structure

```
.
├── uvm_tb/          # UVM testbench
├── python/          # Python scripts
├── config/          # Configuration files
├── examples/        # Example files
├── docs/            # Documentation
└── scripts/         # Build scripts
```

## Quick Links

- [README](README.md)
- [Setup Guide](SETUP.md)
- [Architecture](docs/ARCHITECTURE.md)
- [User Guide](docs/USER_GUIDE.md)
- [API Reference](docs/API_REFERENCE.md)
