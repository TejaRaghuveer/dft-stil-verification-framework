# Advanced Analytics and Intelligence for DFT Verification

This module adds deeper statistical analysis, design intelligence, and optimization guidance on top of the baseline DFT flow.

## Implemented Engines

The implementation lives in:

- `python/advanced_analytics/engine.py`
- `python/advanced_analytics/__main__.py`

### 1) Statistical Analysis Engine

- Coverage distribution (min/max/mean/median)
- Fault-to-pattern ratio
- Pattern efficiency (faults/second and coverage/second)
- Significance proxy (top-quartile vs median spread)
- Output section: `statistical_analysis`

### 2) Design Health Analyzer

- Testability assessment across design modules
- Weak point identification (low coverage / high untestable)
- Design health scorecard (0-10)
- Improvement recommendations
- Output section: `design_health`

### 3) Failure Prediction Engine

- High-risk pattern prediction for post-silicon failure likelihood
- Risk scoring and level classification
- Improvement guidance for high-risk patterns
- Output section: `failure_prediction`

### 4) Design Modification Recommender

- Targets untestable/undetectable pressure points
- Recommends design-side DFT improvements
- Quantifies potential improvement and ROI score
- Output section: `design_modification`

### 5) Competitive Analysis

- Compares project metrics against benchmark baselines
- Produces competitiveness deltas and rank estimate
- Suggests best-practice focus areas
- Output section: `competitive_analysis`

### 6) Real-Time Dashboard

- Generates interactive HTML snapshot dashboard
- Includes current execution insight payload for quick review
- Output file: `advanced_dashboard.html`

### 7) Pattern Recommendation Engine

- Time-budget-aware subset recommendation
- Coverage-oriented selection by efficiency
- Priority ranking and confidence estimate
- Output section: `pattern_recommendation`

### 8) Design Comparison Framework

- Pre-fix vs post-fix comparison
- Delta tracking across revisions
- Output section: `design_comparison`

### 9) Sensitivity Analysis

- Parameter sensitivity curves and slope analysis
- Critical tuning-parameter identification
- Design tuning recommendations
- Output section: `sensitivity_analysis`

### 10) Root Cause Analysis Engine

- Failure signature classification
- Correlation-style root-cause distribution (design/test/timing)
- Actionable follow-up recommendations
- Output section: `root_cause_analysis`

## Statistical and ML Method Notes

- Statistical summaries use deterministic aggregate methods (`mean`, `median`, slope-based sensitivity).
- Risk and recommendation engines use explainable heuristic scoring designed for traceability in sign-off discussions.
- Confidence values are intentionally bounded and transparent to avoid opaque black-box ranking behavior.

## How to Run

From repository root:

```bash
set PYTHONPATH=python
python -m advanced_analytics --out-dir out/advanced_analytics --budget-sec 7200
```

Outputs:

- `out/advanced_analytics/advanced_analysis_report.json`
- `out/advanced_analytics/advanced_analysis_manifest.json`
- `out/advanced_analytics/advanced_dashboard.html`

## Integration Guidance

- Start with `advanced_analysis_report.json` for machine-consumable decisions.
- Use `advanced_dashboard.html` for interactive team reviews.
- Feed recommendations into pattern scheduling, DFT closure, and post-silicon debug loops.

