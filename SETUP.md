# Setup Guide - DFT-STIL Verification Framework

## Prerequisites

### 1. Simulator Installation

Install one of the following simulators:

- **Synopsys VCS** (2020.03 or later)
- **Mentor Graphics QuestaSim** (2020.1 or later)  
- **Cadence Xcelium** (20.03 or later)

### 2. UVM Library

UVM 1.2 or later is required. It's typically included with simulators:
- VCS: Usually in `$VCS_HOME/etc/uvm-1.2`
- QuestaSim: Usually in `$QUESTA_HOME/verilog_src/uvm-1.2`
- Xcelium: Usually in `$CDS_HOME/tools/uvm-1.2`

### 3. Python Environment

Install Python 3.6 or later:

```bash
# Check Python version
python3 --version

# Install required packages
pip install -r requirements.txt
```

Or install manually:
```bash
pip install pyyaml
```

### 4. Environment Variables

Set environment variables based on your simulator:

#### For VCS:
```bash
export VCS_HOME=/path/to/vcs
export PATH=$VCS_HOME/bin:$PATH
```

#### For QuestaSim:
```bash
export QUESTA_HOME=/path/to/questa
export PATH=$QUESTA_HOME/bin:$PATH
```

#### For Xcelium:
```bash
export CDS_HOME=/path/to/xcelium
export PATH=$CDS_HOME/tools/bin:$PATH
```

#### UVM Home (if needed):
```bash
# For QuestaSim
export UVM_HOME=$QUESTA_HOME/verilog_src/uvm-1.2

# For VCS
export UVM_HOME=$VCS_HOME/etc/uvm-1.2

# For Xcelium
export UVM_HOME=$CDS_HOME/tools/uvm-1.2
```

## Setup Steps

### 1. Clone/Download Project

```bash
cd /path/to/project
```

### 2. Validate Project Structure

```bash
# From project root
python python/validators/file_validator.py
```

Or using Makefile:
```bash
make validate
```

### 3. Install Python Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

Source the setup script (Linux/Mac):
```bash
source scripts/setup_env.sh
```

Or set environment variables manually (Windows):
```powershell
$env:VCS_HOME = "C:\path\to\vcs"
$env:PATH = "$env:VCS_HOME\bin;$env:PATH"
```

### 5. Generate Example STIL File

```bash
make stil_example
```

This creates `examples/example_pattern.stil`.

### 6. Verify Setup

Try compiling the testbench:
```bash
make compile
```

## Windows-Specific Setup

### PowerShell Environment Variables

```powershell
# Set VCS_HOME
$env:VCS_HOME = "C:\Synopsys\VCS_2020.03"
$env:PATH = "$env:VCS_HOME\bin;$env:PATH"

# Set UVM_HOME
$env:UVM_HOME = "$env:VCS_HOME\etc\uvm-1.2"
```

### Makefile on Windows

If you don't have `make` on Windows:
- Install **GNU Make** for Windows
- Or use **MinGW/MSYS2**
- Or use simulator-specific scripts instead

Alternatively, use the simulation script directly:
```bash
python scripts/run_simulation.py  # If you create a Python version
```

## Verification

### Test 1: Validate Project Structure

```bash
python python/validators/file_validator.py
```

Expected output:
```
✓ Project structure validation passed
```

### Test 2: Generate Example STIL

```bash
python python/stil_generator/stil_template_generator.py examples/test.stil
```

Check that `examples/test.stil` was created.

### Test 3: Parse Example ATPG (if you have one)

```bash
python python/atpg_parser/atpg_parser.py tetramax examples/patterns.tmax
```

### Test 4: Compile Testbench

```bash
make compile
```

This should compile without errors (warnings are OK).

## Troubleshooting

### Issue: "UVM library not found"

**Solution**: Set `UVM_HOME` environment variable to point to UVM library location.

### Issue: "Simulator not found"

**Solution**: 
1. Verify simulator is installed
2. Set appropriate `*_HOME` environment variable
3. Add simulator bin directory to `PATH`

### Issue: "Python module not found"

**Solution**: 
```bash
pip install -r requirements.txt
```

### Issue: "Makefile not working on Windows"

**Solution**: 
- Install GNU Make for Windows
- Or use simulator-specific commands directly
- Or create batch/PowerShell scripts

### Issue: "Compilation errors"

**Solution**:
1. Check UVM library path in Makefile
2. Verify all source files are included
3. Check for missing dependencies

### Issue: "STIL file not generated"

**Solution**:
1. Check `cfg.stil_enable_generation = 1` in test
2. Verify file path is writable
3. Check simulation completed successfully

## Next Steps

After setup:
1. Review `README.md` for usage
2. Check `docs/USER_GUIDE.md` for examples
3. Integrate your DUT (replace `example_dut_wrapper.sv`)
4. Create custom tests for your design

## Support

For setup issues:
- Check simulator documentation
- Review error messages carefully
- Validate project structure with `make validate`
- Check environment variables are set correctly
- Contact maintainer **Raghuveer**
  - GitHub / LinkedIn: [https://github.com/TejaRaghuveer](https://github.com/TejaRaghuveer)
  - Email: `tejaraghuveer@gmail.com`
