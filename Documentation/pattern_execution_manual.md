# Pattern execution manual

## 1. Inputs

- **ATPG / STIL source:** `--atpg` or pre-built `--pattern-db` (`pattern_db.json`).
- **UVM execution:** `atpg_select_patterns_test` with `+PATTERN_FILE`, `+PATTERN_LIST_FILE`, `+MAX_PATTERNS`, `+RESULT_CSV` (see top-level `Makefile`).

## 2. Integrated flows

| Flow | Command |
|------|---------|
| Week 2 | `python python/integrated_flow/run_flow.py --atpg <file> --smoke_n 30` |
| Week 3 bundle | `python python/integrated_flow/week3_production.py --atpg <file> --out deliverables` |

## 3. Interpreting results

- **CSV:** columns `pattern_name`, `status`, `mismatches`, etc.
- **STIL:** validate with `python -m stil_utils.stil_validator` or embedded validator in `run_flow` / Week 3.
- **Fault coverage:** `fault_coverage_week3.json` when pattern records include `fault_list`.

## 4. At-speed / timing

Timing margin reports are **analytical** (`python/timing/`). Correlate with SDF-annotated simulation and STA for sign-off.
