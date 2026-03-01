# ATPG Pattern to UVM Sequence Converter

Converts ATPG patterns (`atpg_pattern_t`) into executable UVM sequences for the DFT testbench (JTAG, Clock, Reset, Pad agents).

## Components

### Configuration: `atpg_seq_config`
- **Scan shift**: `scan_tck_period_ns`, `scan_tck_duty_cycle_pct`, `scan_setup_ns`, `scan_hold_ns`
- **Capture**: `capture_edge` (leading/trailing), `capture_cycles`
- **Primary I/O**: `primary_setup_ns`, `primary_hold_ns`, `primary_capture_delay_ns`
- **Execution**: `pattern_order` (sequential/random), `result_check` (on-the-fly/end-of-test), `reset_between_patterns`, `restart_on_failure`
- **Test mode**: `test_mode_ir` (e.g. EXTEST=0), `ir_length`, `dr_length`
- **Logging**: `log_file_path` (CSV), `verbosity`

### Sequences

1. **`atpg_pattern_seq`** (single pattern, three phases)
   - **Phase A – Initialization**: TAP reset, load test mode instruction (e.g. EXTEST).
   - **Phase B – Stimulus**: `scan_shift_with_capture_seq` per scan vector; `primary_io_stimulus_seq` for primary inputs.
   - **Phase C – Response**: Shift out and compare (via JTAG monitor/driver TDO check); status reported to logger.

2. **`scan_shift_with_capture_seq`**
   - Shifts `scan_in_str` (LSB to MSB) through JTAG DR.
   - Waits `capture_cycles` at operational speed.
   - Shifts out and compares to `expected_scan_out_str`.

3. **`primary_io_stimulus_seq`**
   - Drives `primary_in_str` as pad input with configurable setup/hold.
   - Optionally posts expected primary output for response checking.

4. **`multi_pattern_seq`**
   - Runs a queue of `atpg_pattern_t`.
   - Optional TAP reset between patterns (`reset_between_patterns`).
   - Uses `atpg_pattern_exec_logger` for start/end time, status, and CSV export.

### Sequence Item Mapping
- `atpg_pattern_t.scan_in_vectors[i]` → `jtag_xtn` with `tdi_vector` from string (0/1/X/Z→drive value).
- `atpg_pattern_t.primary_in_vectors[i]` → `pad_xtn` with `data_value` from string.
- Expected scan/primary outputs → scoreboard/monitor comparison and logger.

### Logger: `atpg_pattern_exec_logger`
- Logs pattern start/end time, status (PASS/FAIL/ERROR), first failing vector index, expected/actual snippets.
- Coverage stats: total run, pass, fail, error.
- CSV export: `pattern_name`, `index`, `status`, `start_time`, `end_time`, `duration_ns`, `vector_fail`, `mismatches`, `total_vectors`.

## Example: Select 5–10 Patterns and Run

**Test:** `atpg_select_patterns_test`

1. **By count (first N)**  
   Leave `pattern_names` empty and set `max_patterns_to_run = 10`. The test parses `pattern_file_path`, then runs the first 10 patterns from the parser’s queue.

2. **By name**  
   Push chosen names into `pattern_names` and set `max_patterns_to_run` as needed:
   ```systemverilog
   pattern_names.push_back("pat_1");
   pattern_names.push_back("pat_2");
   pattern_names.push_back("pat_5");
   pattern_names.push_back("pat_10");
   max_patterns_to_run = 10;
   ```
   Only the listed patterns that exist in the parsed set are executed (up to `max_patterns_to_run`).

3. **Run**
   - Ensure `patterns/stuck_at.stil` (or your file) exists, or set `pattern_file_path` in the test.
   - Run: `+UVM_TESTNAME=atpg_select_patterns_test`
   - Results: `atpg_pattern_results.csv` (if `seq_cfg.log_file_path` is set).

## Integration

- **`dft_env`** is set in `uvm_config_db` from `dft_base_test::connect_phase`, so sequences can get it and start sub-sequences on `env.jtag_ag.sequencer` and `env.pad_ag.sequencer`.
- **Config**: Set `atpg_seq_cfg` and `atpg_logger` in config_db (e.g. in test `build_phase`); sequences read them when running.
- **Parser**: Use `atpg_pattern_parser::parse_atpg_file()`, then `get_pattern_by_name()` or `export_patterns_to_uvm()` to build the queue for `multi_pattern_seq`.
