# My Integrated Flow (Week 2)

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

## How I Use It

```bash
python python/integrated_flow/run_flow.py --atpg patterns/stuck_at.stil --design GPU_Shader_Core --smoke_n 30
```

Add `--run_full` to run the full suite.

## My Notes

- The current “achieved fault coverage” is computed from **patterns successfully executed** (PASS/FAIL) and their `fault_list` in the pattern DB. If your pattern DB does not include `fault_list`, the analyzer will still produce contribution and execution summaries but coverage will be limited.
- For IEEE 1450 validation, the Python STIL generator emits `V { ... };` vectors compatible with the project validator.

---

## My Week 3 Production Bundle

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

GPU shader specialization (ALU/register/pipeline focused):

```bash
python python/integrated_flow/week3_production.py --dry-run --out deliverables --gpu-shader-config config/gpu_shader_config.example.txt
```

Outputs include:
- `Reports/gpu_shader_verification.json`
- `Reports/gpu_shader_verification.html`

Multi-core cache coherence + interconnect specialization:

```bash
python python/integrated_flow/week3_production.py --dry-run --out deliverables --multi-core-config config/multi_core_config.example.txt
```

Combined GPU + multi-core:

```bash
python python/integrated_flow/week3_production.py --dry-run --out deliverables --gpu-shader-config config/gpu_shader_config.example.txt --multi-core-config config/multi_core_config.example.txt
```

Outputs include:
- `Reports/multi_core_cache_interconnect_verification.json`
- `Reports/multi_core_cache_interconnect_verification.html`

ML-based pattern optimization:

```bash
python python/integrated_flow/week3_production.py --dry-run --out deliverables --ml-pattern-optimize --ml-target-coverage 95 --ml-max-patterns 300
```

ML outputs:
- `Reports/ml_pattern_optimization.json`
- `Reports/ml_pattern_optimization.txt`
- `Reports/ml_learning_history.json`

