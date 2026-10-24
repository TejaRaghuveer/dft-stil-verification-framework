# DFT / STIL verification framework

A learning project on design-for-test (DFT) verification: a UVM testbench for a JTAG (IEEE 1149.1) TAP, plus Python tools that generate and read STIL test patterns and report fault coverage. It is aimed at GPU-style scan and JTAG test, but it runs on small sample data and example patterns, not on a real chip design.

## What is here

**Python tools (`python/`)**

- `stil_generator/` writes an IEEE 1450 style STIL file (signals, timing, patterns)
- `atpg_parser/` reads pattern names from STIL and from TetraMAX/FastScan/Encounter style files
- `fault_coverage/` computes fault coverage, test coverage and pattern contribution from a fault list
- `verification/`, `timing/`, `reporting/`, `pattern_debug/`, `multi_domain/`, `post_silicon/`, `advanced_analytics/` are the later add-ons: protocol and DRC checks, at-speed timing notes, HTML/JSON reports, pattern debug helpers

**UVM testbench (`uvm_tb/`)**: JTAG, clock, reset and pad agents, a test environment, sequences, a STIL subscriber, SVA files for the TAP and scan-chain connectivity, and tests (`simple_jtag_test`, `scan_shift_test`, `stuck_at_test`, and a few more).

## Running the Python side

```
pip install -r requirements.txt
python python/stil_generator/stil_template_generator.py     # writes examples/example_pattern.stil
python python/atpg_parser/atpg_parser.py generic examples/sample_post_silicon_patterns.stil
cd python && python -m fault_coverage                       # demo fault list
```

Run these from the repo root as shown (the generator writes to a relative `examples/` path). The `python -m` entry points in `fault_coverage`, `verification`, `timing` and `reporting` each run a built-in demo with sample numbers.

## Running the UVM side

```
make sim SIM=vcs TEST=simple_jtag_test      # or SIM=xrun
```

I do not have a VCS or Xcelium licence set up here, so I have not run this end to end. A strict open-source parser (slang) reports file-order and packaging problems in `uvm_tb/dft_tb_pkg.sv` (interface files included inside a package, a type used before its declaration in `pad_xtn.sv`), so expect to fix compile issues before the first run.

## What the numbers mean

Any coverage figure you see in the reporting demo (for example 96.2 percent) is sample data hard-coded in `python/reporting/__main__.py`. It is not a measurement of a real design. The only real fault-coverage result in the repo is `python/fault_coverage_report.txt`, from a 6-fault example (4 detected, 80 percent).

## Known gaps

- UVM testbench not yet compiled on a commercial simulator
- ATPG parser reads pattern names only; inputs/outputs are not extracted yet
- No real design under test and no real ATPG output
- Many of the documents under `Documentation/` are short outlines; the code is the source of truth
