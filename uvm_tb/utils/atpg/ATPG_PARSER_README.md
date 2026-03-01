# ATPG Pattern Parser

## Overview

The ATPG pattern parser reads standard ATPG tool outputs and converts them into `atpg_pattern_t` objects for use in UVM sequences. It supports multiple formats (TetraMAX-style, Fastscan-style, generic ASCII, and STIL-like) and provides validation, statistics, and export to the testbench.

---

## Data Structures

### atpg_pattern_type_e

- `ATPG_STUCK_AT` – Stuck-at fault patterns
- `ATPG_TRANSITION_DELAY` – Transition delay (at-speed)
- `ATPG_PATH_DELAY` – Path delay
- `ATPG_CUSTOM` – User-defined

### atpg_pattern_t

| Field | Type | Description |
|-------|------|-------------|
| pattern_name | string | Pattern identifier |
| pattern_type | atpg_pattern_type_e | Test type |
| scan_in_vectors | string queue | Scan-in data per cycle (e.g. `"1010X1ZX"`) |
| scan_out_vectors | string queue | Expected scan-out |
| primary_in_vectors | string queue | Primary input values |
| expected_primary_out | string queue | Expected primary output values |
| fault_list | string queue | Fault names detected by this pattern |
| capture_cycles | int | Number of capture cycles |
| comments | string queue | Free-form comments |
| metadata | string[string] | Key-value (e.g. test_type, fault_coverage) |

Helpers: `add_scan_in()`, `add_scan_out()`, `add_fault()`, `set_metadata()`, `get_metadata()`, `get_scan_vector_count()`.

---

## Parser Class: atpg_pattern_parser

### Methods

- **parse_atpg_file(filename)** – Opens file, detects format (TetraMAX / Fastscan / STIL / generic), calls the appropriate parser. Returns number of patterns loaded. Handles file-not-found and permission errors.
- **parse_tetramax_file(filename)** – Synopsys TetraMAX-style ASCII. Currently delegates to generic ASCII; extend for tool-specific headers/tokens.
- **parse_fastscan_file(filename)** – Mentor Fastscan-style. Delegates to generic ASCII; extend for Fastscan-specific syntax.
- **parse_generic_ascii(filename)** – Main ASCII parser:
  - `#` comment lines ignored
  - `PATTERN <name>` starts a new pattern (optional)
  - Non-comment, non-keyword lines treated as vector lines (only `0`/`1`/`x`/`X`/`z`/`Z`)
  - Consecutive vector lines are added to the current pattern’s scan_in_vectors
- **validate_pattern_data()** – Checks consistency (e.g. non-empty scan-in), flags suspicious vectors (all 0s, all 1s, all X). Increments parse_warnings.
- **get_pattern_count()** – Returns `patterns.size()`.
- **get_pattern_by_name(name)** – Lookup in `patterns_by_name`; returns null if missing.
- **export_patterns_to_uvm(ref atpg_pattern_t q[$])** – Fills `q` with the loaded patterns for use by tests/sequences.

### Utility Functions

- **parse_vector_line(line, ref logic vec[])** – Converts string like `"1010X1ZX"` to `logic[]` (0/1/x/z). Allocates `vec` and returns length.
- **validate_vector_length(vector_str, expected_length)** – Returns 1 if `vector_str.len() == expected_length` (or expected_length ≤ 0).
- **convert_logic_to_bit(logic l)** – Returns 1 for `1'b1`, else 0 (for statistics/counting).
- **get_pattern_statistics(ref total_patterns, ref total_vectors, ref avg_length)** – Fills totals and average scan vector count per pattern.

---

## Error Handling

- **File not found / read permission** – `$fopen` fails; parser logs `uvm_error` and increments `parse_errors`; returns 0.
- **Syntax errors** – `set_error(line_num, msg)` stores last error; duplicate pattern names and vector length mismatches increment `parse_errors` and log.
- **Vector length mismatch** – When `expected_scan_length` is set, each vector line is checked; mismatch increments `parse_errors`.
- **Duplicate pattern names** – Second occurrence of the same name triggers error and is stored.
- **Suspicious patterns** – Vectors that are all 0, all 1, or all X generate warnings and increment `parse_warnings`.

---

## Configuration: atpg_parser_config

- **input_file_path** / **input_file_paths** – File(s) to parse.
- **pattern_type_filter** – If non-empty, only patterns with type in the list are kept.
- **max_pattern_count** – Cap number of patterns loaded (0 = no limit).
- **expected_scan_length**, **expected_pi_length**, **expected_po_length** – Enforced lengths (0 = do not enforce).
- **fault_coverage_threshold** – Min fault coverage to accept (future use).
- **verbosity** – UVM verbosity for parser messages.
- **report_file_path** – If set, `report_phase` writes a short report (pattern count, errors, warnings).
- **dry_run** – If 1, parse and validate but do not push patterns into the internal queue (no load into memory).

---

## Logging and Debugging

- Each parsed file logs a summary: pattern count, errors, warnings.
- Format detection and which parser is used are logged at `cfg.verbosity`.
- Optional report file: set `cfg.report_file_path`; report is written in `report_phase`.

---

## ATPG Tool Output Format Notes

### Generic ASCII (primary supported format)

- One vector per line; characters `0`, `1`, `x`, `X`, `z`, `Z`.
- Optional: `#` comments; `PATTERN <name>` to start a named pattern.
- Example:

```
# ATPG generic format
PATTERN stuck_at_1
0101
1010
PATTERN stuck_at_2
0011
1100
```

### TetraMAX (Synopsys)

- Binary formats are tool-specific; not parsed here.
- ASCII exports are often vector-per-line or similar; use generic ASCII path or extend `parse_tetramax_file()` for known headers (e.g. `"TetraMAX"`, specific keywords).

### Fastscan (Mentor)

- Pattern files are often ASCII with headers; use generic ASCII or extend `parse_fastscan_file()` for known tokens.

### STIL

- If the ATPG tool outputs STIL, the parser can treat STIL pattern sections as text and extract vectors (e.g. `V { ... }`); format detection uses `detect_format()`. Full STIL parsing can be added in a dedicated path or by reusing the STIL generator/reader if available.

---

## Example: Load and Use in a Test

```systemverilog
atpg_parser_config pcfg;
atpg_pattern_parser parser;
atpg_pattern_t q[$];

pcfg = atpg_parser_config::type_id::create("pcfg");
pcfg.add_input_file("patterns/atpg_stuck_at.txt");
pcfg.max_pattern_count = 100;
pcfg.expected_scan_length = 256;
uvm_config_db#(atpg_parser_config)::set(this, "*", "atpg_parser_cfg", pcfg);

parser = atpg_pattern_parser::type_id::create("parser", this);
parser.parse_atpg_file(pcfg.input_file_path);
parser.validate_pattern_data();
parser.export_patterns_to_uvm(q);
// Use q in sequences: iterate and drive JTAG/pad from pattern scan_in_vectors, etc.
```

---

## Files

- `uvm_tb/utils/atpg/atpg_pattern.sv` – atpg_pattern_type_e, atpg_vector_t, atpg_pattern_t
- `uvm_tb/utils/atpg/atpg_parser_config.sv` – Parser configuration
- `uvm_tb/utils/atpg/atpg_pattern_parser.sv` – Parser implementation
- `uvm_tb/utils/atpg/ATPG_PARSER_README.md` – This document
