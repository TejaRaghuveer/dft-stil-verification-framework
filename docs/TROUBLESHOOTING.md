# Troubleshooting

## Quick Triage

1. Run `make validate` to catch missing files or setup issues.
2. Check latest report artifacts in `deliverables*/Reports/`.
3. Confirm `PYTHONPATH=python` when executing integrated scripts.

## Common Problems

### 1) STIL generation fails

- Verify `python/stil_generator/stil_template_generator.py` is unchanged from main branch.
- Re-run with `--dry-run` to isolate simulator-related issues.
- Check `Reports/stil_validation_baseline.json`.

### 2) Fault coverage appears too low

- Confirm pattern DB contains `fault_list` entries.
- Use `python/fault_coverage` tooling to inspect undetected categories.
- Review `Reports/fault_coverage_week3.json` and gap-analysis sections.

### 3) Multi-core report missing

- Ensure `--multi-core-config config/multi_core_config.example.txt` is passed.
- Check manifest keys:
  - `outputs.multi_core_report_json`
  - `multi_core_specialization`

### 4) ML optimization output missing

- Enable `--ml-pattern-optimize`.
- Confirm generated files:
  - `Reports/ml_pattern_optimization.json`
  - `Reports/ml_pattern_optimization.txt`

### 5) CI run fails but local works

- Confirm dependencies are in `requirements.txt`.
- Avoid local-only assumptions (absolute paths, untracked files).
- Compare workflow logs with local command output.

## Escalation Checklist

- Include command used
- Include exact error trace
- Attach relevant report JSON file
- Mention last known good commit

