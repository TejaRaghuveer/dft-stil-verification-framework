# Internal Knowledge Base

## FAQ

See `docs/faq.md` for quick Q&A.

## Common Patterns and Snippets

### Run integrated flow

```bash
set PYTHONPATH=python
python python/integrated_flow/week3_production.py --dry-run --out deliverables_kb
```

### Enable GPU + Multi-Core + ML

```bash
python python/integrated_flow/week3_production.py --dry-run --out deliverables_kb \
  --gpu-shader-config config/gpu_shader_config.example.txt \
  --multi-core-config config/multi_core_config.example.txt \
  --ml-pattern-optimize --ml-target-coverage 95
```

## Design Decisions and Rationale

- JSON artifacts are primary because they are easy to diff and automate.
- Dry-run behavior exists to keep CI reproducible without EDA tool licenses.
- Optional specialization layers avoid blocking core bring-up.

## Lessons Learned

- Tautological checks in verification logic can hide defects.
- Coverage metrics must be per-pattern/per-register scoped, not cumulative state leakage.
- Report quality improves when correlation data is preserved across modules.

## Performance Benchmarks (Template)

Maintain this table each release:

| Release | Pattern Count | Coverage (%) | Runtime (s) | Notes |
|---|---:|---:|---:|---|
| vX.Y | TBD | TBD | TBD | Baseline |

