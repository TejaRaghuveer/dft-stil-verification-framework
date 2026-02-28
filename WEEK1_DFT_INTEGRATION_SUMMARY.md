## Week 1 – DFT Testbench Integration and First Run Plan

### 1. Components integrated

- **Agents**
  - JTAG: `jtag_agent` (legacy) and `jtag_agent_enhanced` (for DFT env)
  - Clock: `clock_agent` + `clock_driver` / `clock_driver_enhanced`
  - Reset: `reset_agent` + `reset_driver` / `reset_driver_enhanced`
  - Pad: `pad_agent` (legacy) and `pad_agent_enhanced` (primary I/O with driver/monitor/response collector)
- **Environment / Tests**
  - Original env: `test_env` with agents `*_agent_inst`
  - DFT env: `dft_env` + `dft_test_config` + `dft_base_test` + mode-specific tests
- **STIL generation**
  - Core types: `stil_signal_t`, `stil_timing_spec_t`, `stil_waveform_t`, `stil_vector_t`, `stil_procedure_t`, `stil_info_transaction`
  - Core generator: `stil_generator` (subscriber on `stil_info_transaction`)
  - Adapter: `stil_subscriber` (subscribes to `jtag_transaction` from legacy JTAG monitor and feeds `stil_generator`)
- **Top / harness**
  - `tb_top` instantiates DUT stub, interfaces, connects UVM agents via `uvm_config_db`, and supports `+UVM_TESTNAME` and `+vcd` for waveforms.
  - `dft_tb_pkg` includes all agents, envs, tests, and STIL files.
  - `Makefile` drives VCS or Xcelium with `TEST=<uvm_test>` and `+vcd`.

### 2. Recommended first DFT run (simple JTAG + STIL)

- **Test**: `simple_jtag_test`
  - Extends `base_test` / `test_env` and uses legacy `jtag_agent`.
  - Configuration (`configure_test()`):
    - `cfg.jtag_clock_period_ns = 100;` (10 MHz)
    - `cfg.num_test_patterns = 50;` (≥ 10 vectors)
    - `cfg.stil_enable_generation = 1;`
    - `cfg.stil_output_file = "simple_jtag_test.stil";`
  - Behavior:
    - Clock and reset agents run automatically from `test_env`.
    - JTAG driver initializes TAP (reset sequence) then `jtag_sequence` sends randomized vectors.
    - JTAG monitor publishes `jtag_transaction` on its analysis port.
    - `stil_subscriber` adapts to `stil_info_transaction` and calls `stil_generator.write()`.
    - `stil_generator` collapses activity into vectors and writes STIL.

- **Command (on your machine)**:
  - VCS:
    - `make sim SIM=vcs TEST=simple_jtag_test`
  - Xcelium:
    - `make sim SIM=xrun TEST=simple_jtag_test`

> In this environment, `make`/VCS/Xcelium are not available, so compilation and simulation must be run on your local setup. All SV files pass lint here and the Makefile is set up for standard tool flows.

### 3. Expected artifacts from first run

- **Waveforms**
  - `tb_top.vcd` (when `+vcd` is present; Makefile adds `+vcd`).
  - Contains:
    - `clk`, `rst_n`
    - JTAG signals: `tck`, `tms`, `tdi`, `tdo`, `trst_n`
    - Pad signals: `pad_in`, `pad_out`, `pad_oe`

- **Logs**
  - VCS:
    - `vcs_compile.log` – compile / elaborate; should be warning-free.
    - `vcs_sim.log` – runtime; look for:
      - `Starting JTAG monitoring`
      - `Starting simple JTAG test`
      - `STIL_GEN` info about opened file and vector count.
  - Xrun:
    - `xrun.log` – combined compile/sim.

- **STIL file**
  - `simple_jtag_test.stil`
  - Structure:
    - `STIL 1.0;`
    - `Header` with Title/Source
    - `Signals { "TCK" In Digital; "TMS" In Digital; "TDI" In Digital; "TDO" Out Digital; "TRST" In Digital; }`
      - Plus any additional signals registered via `stil_generator`.
    - `SignalGroups { scan_inputs = '"TDI"'; scan_outputs = '"TDO"'; control_signals = '"TCK" "TMS" "TRST"'; }`
    - `Timing { WaveformTable "default_wft" { Period <jtag_clock_period_ns>ns; Waveforms { "drive" {...} "compare" {...} } } }`
    - `Procedures { "Init", "Shift", "Capture" }`
    - `PatternExec { PatternBurst "DFT_Burst" { PatList { "PATTERN_0" }; } }`
    - `Patterns { Pattern "PATTERN_0" { WFT "default_wft"; V { ... } ... } }`
  - At least **50** vectors (`V { ... };`) will be written, satisfying the “≥10 vectors” criterion.

### 4. Validation steps (on your side)

- **Compile / run**
  - Confirm `make sim ...` completes without errors.
  - Check that all 4 agents (JTAG, Clock, Reset, Pad) print their startup messages.

- **STIL validation**
  - Run your STIL checker, e.g.:
    - `STILVerify simple_jtag_test.stil`
  - Verify:
    - File is accepted as IEEE 1450 compliant.
    - All expected signals are present in `Signals` and `SignalGroups`.
    - Vectors (`V { ... };`) have consistent width and only valid symbols (0/1/X/Z/D/W).
    - `default_wft` WaveformTable has correct period and basic drive/compare waveforms.

### 5. Known limitations & next‑steps

- Current STIL generation is driven by **legacy JTAG agent**. Enhanced DFT env (`dft_env` + `jtag_agent_enhanced`) is integrated but not yet wired to STIL; week‑2 work can:
  - Add a `stil_subscriber` adapter for `jtag_xtn`.
  - Extend `dft_env.run_scan_test()` to orchestrate:
    - `jtag_reset_sequence`
    - `load_instruction_sequence` (EXTEST)
    - `load_data_register_sequence` for scan patterns.
  - Feed pad/clock/reset activity into `stil_generator` via additional `stil_info_transaction` publishers.

- Coverage:
  - Functional coverage is available in `jtag_coverage` for the enhanced agent; hooking it into `dft_env` and enabling `enable_functional_coverage` in `dft_test_config` is a natural follow‑up.

### 6. What to capture in your Week 1 report

- Screenshot(s):
  - Waveform view (`tb_top.vcd`) showing:
    - Clock and reset behavior.
    - At least a few JTAG cycles (TCK/TMS/TDI/TDO).
- Logs:
  - Snippets from `vcs_sim.log` (or `xrun.log`) showing:
    - Test start / end.
    - JTAG monitor state changes.
    - STIL generator “Generated N STIL vectors” message.
- STIL:
  - First 10–20 lines of `simple_jtag_test.stil` (header, Signals, Timing, first few `V { ... };`).
- Notes:
  - Any warnings seen (tool or UVM).
  - Approximate runtime for 50 JTAG vectors.
  - Items earmarked for Week‑2 improvements (e.g., full dft_env‑based flow, pad agent integration into STIL).

