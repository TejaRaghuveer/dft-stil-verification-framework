# Testbench user guide (quick reference)

## Structure

- **`uvm_tb/`** — UVM environment, JTAG agent, ATPG pattern execution tests.
- **`atpg_select_patterns_test`** — Loads pattern list + STIL/ATPG file via plusargs; logs CSV results.

## Running simulation

```bash
make SIM=vcs TEST=atpg_select_patterns_test PLUSARGS="+PATTERN_FILE=patterns/stuck_at.stil +PATTERN_LIST_FILE=out/integrated/suites/smoke_pattern_list.txt +MAX_PATTERNS=30 +RESULT_CSV=out/integrated/results/smoke_results.csv"
```

Or:

```bash
./scripts/run_simulation.sh -s vcs -t atpg_select_patterns_test
```

(Configure `PLUSARGS` in `Makefile` or extend `run_simulation.sh`.)

## Configuration

- Central config: `uvm_tb/env/test_config.sv` / `dft_test_config.sv` as applicable.
- JTAG / scan timing: `uvm_tb/utils/atpg/atpg_seq_config.sv`.

## Deeper documentation

- `docs/USER_GUIDE.md`
- `uvm_tb/agents/jtag/JTAG_AGENT_DOCUMENTATION.md`
