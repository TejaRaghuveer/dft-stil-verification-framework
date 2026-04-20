# My ML-Based Pattern Optimization

This document describes the ML workflow added for ATPG pattern prioritization, fault prediction, and subset optimization.

## What I Implemented

Code location:

- `python/ml_pattern_optimization/pattern_ml_analyzer.py`
- `python/ml_pattern_optimization/__main__.py`

### 1) My `pattern_ml_analyzer`

The analyzer performs:

- feature extraction from pattern vectors and metadata,
- model training for coverage/time/power/timing-risk prediction,
- pattern subset optimization for target coverage,
- anomaly detection for suspicious patterns,
- fault likelihood prediction for selected patterns,
- continuous learning metric tracking.

### 2) How I Extract Features

Extracted features include:

- Hamming distance between consecutive vectors,
- transition count (`0->1`, `1->0`) proxies,
- all-zeros / all-ones / alternating vector ratios,
- scan chain length and estimated shift cycles,
- capture cycle count proxy,
- primary activity ratio (`io_activity_ratio`),
- pattern fault count metadata.

Features are normalized through min-max scaling.

### 3) My Prediction Models

A lightweight k-NN regressor is used for:

- **Fault Coverage Predictor**
- **Execution Time Predictor**
- **Power Consumption Predictor**
- **Timing Violation Probability Predictor**

Model quality is reported as percentage accuracy (MAPE-derived).

### 4) My Pattern Selection Optimizer

`PatternSelectionOptimizer` ranks by predicted coverage efficiency:

- maximize predicted coverage gain,
- penalize long runtime and high power,
- stop when target coverage is reached,
- optionally enforce max-pattern cap.

### 5) How I Detect Anomalies

`AnomalyDetectionEngine` flags:

- high predicted power outliers,
- high predicted execution time outliers,
- low predicted fault-detection patterns.

### 6) My Fault Prediction Engine

`FaultPredictionEngine` builds feature signatures per fault from historical pattern-fault mappings and predicts likely detected faults for a new/selected pattern.

### 7) How I Handle Continuous Learning

`ContinuousLearningTracker` stores model performance snapshots and reports rolling accuracy, so prediction quality can be tracked as new pattern data is added.

## How I Integrated This in Week 3

`python/integrated_flow/week3_production.py` now supports:

- `--ml-pattern-optimize`
- `--ml-target-coverage`
- `--ml-max-patterns`

When enabled, outputs are generated in `Reports/`:

- `ml_pattern_optimization.json`
- `ml_pattern_optimization.txt`
- `ml_learning_history.json`

Manifest includes:

- `outputs.ml_pattern_optimization_json`
- `outputs.ml_pattern_optimization_txt`
- `ml_pattern_optimization_summary`

## How I Run It from CLI

From repo root:

```bash
set PYTHONPATH=python
python -m ml_pattern_optimization --pattern-db deliverables/pattern_db.json --target-coverage 95 --max-patterns 300
```

## My Example Output Style

```text
ML PATTERN OPTIMIZATION RESULTS
================================

Original Pattern Set Size: 1000 patterns
ML-Optimized Set Size: 312 patterns (31% of original)
Coverage Preserved (predicted): 95.8%
Test Time Reduction (predicted): 69.0% faster

ML Model Performance:
- Fault Coverage Predictor: 92.0% accuracy
- Execution Time Predictor: 87.0% accuracy
- Power Predictor: 85.0% accuracy
```

## My Notes

- The implementation is dependency-free (no heavy ML packages), so it can run in CI dry-run contexts.
- For production sign-off, replace/augment with calibrated models trained on larger silicon-accurate datasets.
