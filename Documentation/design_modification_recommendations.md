# Design modification recommendations (when FC or timing gaps remain)

1. **Observability:** Add test points or adjust scan ordering for low-coverage modules (see `Reports/` module coverage sections).
2. **Timing:** Re-pipeline long paths; add capture cycles; reduce shift frequency for marginal paths.
3. **Scan architecture:** Fix DFT DRC violations (scan enable, clock gating, async reset) before adding patterns.
4. **Pattern set:** Add ATPG runs targeting `RETRY_NEEDED` / gap faults; avoid over-fitting a single pattern type.

Cross-reference `pattern_improvement_plan.json` and fault coverage gap analysis from `python/fault_coverage/`.
