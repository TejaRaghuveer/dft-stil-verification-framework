# Design Document

This document captures technical rationale and long-term design choices for maintainability.

## 1) System Goals

- Unify ATPG parsing, execution orchestration, STIL generation, and reporting.
- Keep modules composable so teams can adopt features incrementally.
- Support GPU-focused verification (single-core and multi-core).

## 2) Core Layers

- **Pattern ingestion**: ATPG parser + Pattern DB
- **Execution orchestration**: integrated flow scripts
- **Verification enrichment**: timing/formal/DRC/multi-domain
- **Reporting**: structured JSON + HTML/CSV/XML exports
- **Specialization modules**: GPU + multi-core + ML optimization

## 3) Design Decisions

### JSON-first artifacts

All major outputs are exported as JSON for machine parsing and reproducibility.

### Dry-run support

Most flows can run without EDA tools using placeholders, enabling CI gating.

### Extension-by-module

New domains are introduced as independent Python packages (e.g., `gpu_shader`, `ml_pattern_optimization`) and then integrated into `week3_production.py`.

## 4) Maintainability Strategy

- Keep feature flags explicit in CLI arguments.
- Ensure each feature emits its own artifacts in `Reports/`.
- Keep backward compatibility of manifest keys where possible.

## 5) Known Trade-offs

- Lightweight ML models are chosen for portability over absolute predictive power.
- Some reports use proxy metrics in dry-run mode and must be calibrated with real simulation data.

## 6) Future Improvements

- Add optional scikit-learn backend for richer model families.
- Add schema validation for all report JSON files.
- Add docs linting and broken-link checks in CI.

