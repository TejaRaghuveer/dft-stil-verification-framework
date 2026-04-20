# API Reference - DFT-STIL Verification Framework

## UVM Classes

### Configuration Classes

#### `test_config`

Main configuration class for the testbench.

**Key Fields:**
- `jtag_clock_period_ns` (int): JTAG clock period in nanoseconds
- `clock_period_ns` (int): Main clock period in nanoseconds
- `num_pads` (int): Number of pad signals
- `stil_output_file` (string): Path to output STIL file
- `stil_enable_generation` (bit): Enable STIL generation
- `num_test_patterns` (int): Number of test patterns
- `verbosity` (uvm_verbosity): UVM verbosity level

**Methods:**
- `convert2string()`: Returns configuration as string
- `validate()`: Validates configuration parameters

### Transaction Classes

#### `jtag_transaction`

Represents a JTAG transaction.

**Fields:**
- `tms` (bit): Test Mode Select
- `tdi` (bit): Test Data Input
- `tdo` (bit): Test Data Output
- `tdo_expected` (bit): Expected TDO value
- `current_state` (jtag_state_t): Current JTAG TAP state
- `cycle_count` (int): Number of clock cycles

**Methods:**
- `convert2string()`: Returns transaction as string
- `do_copy()`: Copy transaction
- `do_compare()`: Compare transactions

### Agent Classes

#### `jtag_agent`

UVM agent for JTAG interface.

**Components:**
- `driver`: `jtag_driver` - Drives JTAG signals
- `monitor`: `jtag_monitor` - Monitors JTAG interface
- `sequencer`: `uvm_sequencer#(jtag_transaction)` - Manages sequences

#### `clock_agent`

UVM agent for clock generation.

**Components:**
- `driver`: `clock_driver` - Generates clock signals

#### `reset_agent`

UVM agent for reset control.

**Components:**
- `driver`: `reset_driver` - Controls reset signals

#### `pad_agent`

UVM agent for pad interface.

**Components:**
- `driver`: `pad_driver` - Drives pad signals

### Environment Classes

#### `test_env`

Top-level UVM environment.

**Components:**
- `jtag_agent_inst`: JTAG agent instance
- `clock_agent_inst`: Clock agent instance
- `reset_agent_inst`: Reset agent instance
- `pad_agent_inst`: Pad agent instance
- `stil_sub_inst`: STIL subscriber instance

### Subscriber Classes

#### `stil_subscriber`

UVM subscriber that generates STIL patterns.

**Configuration:**
- Subscribes to `jtag_transaction` stream
- Generates IEEE 1450 compliant STIL files
- Output file configured via `test_config.stil_output_file`

### Test Classes

#### `base_test`

Base class for all test cases.

**Methods:**
- `configure_test()`: Configure test parameters (override in derived classes)
- `run_test_sequence()`: Run test sequence (override in derived classes)

**Usage:**
```systemverilog
class my_test extends base_test;
    function void configure_test();
        super.configure_test();
        cfg.num_test_patterns = 100;
    endfunction
    
    task run_test_sequence();
        // Your test sequence here
    endtask
endclass
```

### Sequence Classes

#### `base_sequence`

Base class for all sequences.

**Methods:**
- `pre_body()`: Pre-sequence setup
- `body()`: Sequence body (override in derived classes)

**Usage:**
```systemverilog
class my_sequence extends base_sequence;
    task body();
        jtag_transaction txn;
        // Generate transactions
    endtask
endclass
```

## Python API

### STIL Generator

#### `STILTemplateGenerator`

Main class for STIL file generation.

**Methods:**
- `add_signal(signal: STILSignal)`: Add signal definition
- `add_pattern(pattern: STILPattern)`: Add test pattern
- `set_timing(timing: STILTiming)`: Set timing information
- `generate()`: Generate STIL file content
- `write_file()`: Write STIL file to disk

**Example:**
```python
from python.stil_generator import STILTemplateGenerator, STILSignal, STILPattern

generator = STILTemplateGenerator("output.stil")
generator.add_signal(STILSignal("TCK", "In", "Digital"))
generator.add_pattern(STILPattern("vec_001", {"TCK": "0", "TMS": "0"}))
generator.write_file()
```

#### `STILSignal`

Represents a STIL signal.

**Fields:**
- `name` (str): Signal name
- `direction` (str): 'In', 'Out', 'InOut', 'Supply'
- `signal_type` (str): 'Digital', 'Analog', 'Power', 'Ground'
- `description` (str, optional): Signal description

#### `STILPattern`

Represents a STIL pattern.

**Fields:**
- `vector_id` (str): Vector identifier
- `signals` (Dict[str, str]): Signal name to value mapping
- `comment` (str, optional): Pattern comment

### ATPG Parser

#### `ATPGParser`

Parser for ATPG tool outputs.

**Methods:**
- `parse(file_path: str)`: Parse ATPG file
- `get_patterns()`: Get parsed patterns
- `convert_to_stil_format()`: Convert to STIL format

**Example:**
```python
from python.atpg_parser import ATPGParser, ATPGFormat

parser = ATPGParser(ATPGFormat.TETRAMAX)
parser.parse("patterns.tmax")
patterns = parser.get_patterns()
```

### File Validator

#### `FileStructureValidator`

Validates project structure and files.

**Methods:**
- `validate_directory_structure()`: Validate directories
- `validate_required_files()`: Validate required files
- `validate_stil_file(stil_file: str)`: Validate STIL file
- `validate_config_file(config_file: str)`: Validate config file
- `validate_all()`: Run all validations

**Example:**
```python
from python.validators import FileStructureValidator

validator = FileStructureValidator()
is_valid, errors = validator.validate_all()
```

## Interfaces

### `jtag_if`

SystemVerilog interface for JTAG signals.

**Signals:**
- `tck`: JTAG Clock
- `tms`: JTAG Mode Select
- `tdi`: JTAG Data Input
- `tdo`: JTAG Data Output
- `trst_n`: JTAG Reset (active low)

**Modports:**
- `DRIVER`: For driver connection
- `MONITOR`: For monitor connection
- `DUT`: For DUT connection

### `clock_if`

SystemVerilog interface for clock.

**Signals:**
- `clk`: Clock signal

### `reset_if`

SystemVerilog interface for reset.

**Signals:**
- `rst_n`: Reset signal (active low)
- `clk`: Reference clock

### `pad_if`

SystemVerilog interface for pads.

**Signals:**
- `pad_in[NUM_PADS-1:0]`: Pad inputs
- `pad_out[NUM_PADS-1:0]`: Pad outputs
- `pad_oe[NUM_PADS-1:0]`: Output enables

## Enumerations

### `jtag_state_t`

JTAG TAP controller states:
- `TEST_LOGIC_RESET`
- `RUN_TEST_IDLE`
- `SELECT_DR_SCAN`
- `CAPTURE_DR`
- `SHIFT_DR`
- `EXIT1_DR`
- `PAUSE_DR`
- `EXIT2_DR`
- `UPDATE_DR`
- `SELECT_IR_SCAN`
- `CAPTURE_IR`
- `SHIFT_IR`
- `EXIT1_IR`
- `PAUSE_IR`
- `EXIT2_IR`
- `UPDATE_IR`

### `jtag_instruction_t`

JTAG instructions:
- `BYPASS`
- `IDCODE`
- `SAMPLE_PRELOAD`
- `EXTEST`
- `INTEST`
- `RUNBIST`
- `CLAMP`
- `HIGHZ`
- `USERCODE`

## Constants

### Defines (`defines.sv`)

- `NUM_PADS`: Number of pads (default: 32)
- `DEFAULT_CLK_PERIOD_NS`: Default clock period (10ns)
- `DEFAULT_JTAG_CLK_PERIOD_NS`: Default JTAG clock period (100ns)
- `DEFAULT_RST_CYCLES`: Default reset cycles (100)

## Maintainer

- **Raghuveer**
- GitHub / LinkedIn: [https://github.com/TejaRaghuveer](https://github.com/TejaRaghuveer)
- Email: `tejaraghuveer@gmail.com`
