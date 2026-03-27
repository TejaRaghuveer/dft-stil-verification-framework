# Integrated Flow (Week 2)

This folder provides a single runner that stitches together the Week-2 pipeline:

1. **Parse ATPG patterns** (Python)  
2. **Load into Pattern DB** (`python/pattern_db/`)  
3. **Build suites** (SMOKE then FULL)  
4. **Execute UVM** with `atpg_select_patterns_test` using plusargs:
   - `+PATTERN_FILE=...`
   - `+PATTERN_LIST_FILE=...`
   - `+MAX_PATTERNS=...` (0 means all)
   - `+RESULT_CSV=...`
5. **Parse results CSV** for execution summary + performance  
6. **Fault coverage analysis** from executed patterns (achieved coverage)  
7. **Generate STIL** (Python) and validate with `stil_utils/stil_validator.py`  
8. **Write integrated report** combining everything

## Usage

```bash
python python/integrated_flow/run_flow.py --atpg patterns/stuck_at.stil --design GPU_Shader_Core --smoke_n 30
```

Add `--run_full` to run the full suite.

## Notes

- The current “achieved fault coverage” is computed from **patterns successfully executed** (PASS/FAIL) and their `fault_list` in the pattern DB. If your pattern DB does not include `fault_list`, the analyzer will still produce contribution and execution summaries but coverage will be limited.
- For IEEE 1450 validation, the Python STIL generator emits `V { ... };` vectors compatible with the project validator.

---

## Week 3 production bundle

Single orchestrator: **compression**, **timing-aware report**, **formal/DRC artifacts**, **HTML/JSON reports**, **failure analysis**, and **`deliverables/`** layout.

```bash
set PYTHONPATH=python
python python/integrated_flow/week3_production.py --atpg patterns/stuck_at.stil --out deliverables --tck-mhz 200
```

With simulation CSV:

```bash
python python/integrated_flow/week3_production.py --pattern-db out/integrated/pattern_db.json --results-csv out/integrated/results/full_results.csv --out deliverables
```

See `Documentation/WEEK3_PRODUCTION.md` and `deliverables/README.md`.

