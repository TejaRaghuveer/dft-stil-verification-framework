# Fault Coverage Analysis System

Tracks achieved fault coverage, identifies gaps, and provides insights for pattern optimization. Integrates with the pattern database (`pattern_db`) and can be fed from ATPG tool reports or `atpg_pattern_t.fault_list` data.

For **detailed comments on fault coverage metrics, IEEE/IEC standards (e.g. IEC 61149.1, IEEE 1149.1, IEEE 1450), and industry best practices**, see **`fault_coverage_metrics_and_standards.md`**.

## Features

- **Fault Coverage Engine** (`FaultCoverageAnalyzer`): Fault DB (fault_id, fault_type, location, detected_by_patterns[], coverage_status). Categories: DETECTED, UNDETECTABLE, UNTESTABLE, RETRY_NEEDED.
- **Coverage metrics**: Fault Coverage %, Test Coverage %, Defect Level, Pattern Efficiency, Coverage Contribution per pattern.
- **Coverage report**: Summary, undetected fault list, pattern contribution table, coverage by type and by module, module–pattern matrix, targeted suggestions for low-coverage modules.
- **Undetected fault analyzer**: Categorizes UNTESTABLE/UNDETECTABLE/RETRY_NEEDED; recommendations for RETRY_NEEDED (capture edge, at-speed).
- **Pattern gap analyzer**: Groups of similar undetected faults, ATPG parameter suggestions, estimated patterns for 95/98/99% coverage.
- **Fault distribution**: Histogram (faults per pattern), essential vs redundant patterns, Pareto (top 20% patterns).
- **Coverage trendline**: Coverage vs pattern count, saturation point, extrapolation for 99%.
- **Module-level coverage**: Per-module coverage, low-coverage modules, pattern–module matrix, targeted pattern suggestions.
- **Fault browser (CLI)**: Search by location/type/status, show faults per pattern, export fault lists for ATPG.

## Configuration and reporting

- **FaultCoverageConfig**: `report_format` (text/json/xml), `report_file_path`, `verbosity`, `include_recommendations`, `include_trendline`.
- Reports can be written as text (`.txt`), JSON (`.json`), or XML (`.xml`), consistent with STIL validator and pattern_db style.

## Usage

From the `python` directory (or with `PYTHONPATH` including `python`):

```bash
# Full report (default: text to stdout and file)
python -m fault_coverage report [pattern_db.json] --format text --report fault_coverage_report.txt

# Coverage Analysis Report (example-style: Design header, summary, pattern contribution, undetected list, Pareto, recommendations)
python -m fault_coverage report mydb.json --format analysis --report coverage_analysis_report.txt --design "GPU_Shader_Core" --patterns 1000 --target 95

# JSON or XML report
python -m fault_coverage report mydb.json --format json --report fault_coverage_report.json

# Search faults (fault browser)
python -m fault_coverage search [input.json] --location "u_core" --status UNDETECTABLE --format text

# Show faults detected by a pattern
python -m fault_coverage pattern pat_1 [--input pattern_db.json]

# Export fault list for ATPG re-targeting
python -m fault_coverage export [input.json] -o undetected_faults.txt --status undetected
```

## Integration

- **Pattern DB**: Load from `pattern_db.json` (same schema as `pattern_db/pattern_database.py`: `patterns` array with `pattern_name`, `fault_list`, etc.). Use `FaultCoverageAnalyzer.load_from_pattern_db(patterns)` when using the API with `PatternRecord` objects.
- **ATPG / UVM**: `atpg_pattern_t.fault_list` can be exported to the same JSON shape; the analyzer builds the fault DB from pattern→fault links and optional status from ATPG reports (undetectable/untestable/retry).
- **Undetectable/untestable**: Call `UndetectedFaultAnalyzer.categorize_undetected(untestable_ids=..., undetectable_ids=..., retry_ids=...)` with IDs from your ATPG tool to set fault status before generating reports.
