# CI/CD Pipeline Guide

This document defines the complete CI/CD process for automated DFT verification, regression, reporting, and sign-off.

## 1) Pipeline Overview

Workflow file: `.github/workflows/dft_cicd.yml`

### Triggers

- On commit (`push` to `main`/`develop`): syntax checks + dry-run flow
- On PR to `main`: syntax checks + dry-run flow
- Nightly (`02:00 UTC`): regression run and artifact upload
- Weekly (`Sunday 03:00 UTC`): extended regression + coverage/report refresh
- On merge/push to `main`: full validation + sign-off report

### Job Stages

1. `precommit_checks`
2. `nightly_regression`
3. `weekly_extended`
4. `main_signoff`

## 2) Local Developer Setup

### Install Git Hooks

```bash
chmod +x scripts/install_hooks.sh
./scripts/install_hooks.sh
```

### Manual local regression run

```bash
chmod +x scripts/run_regression.sh
./scripts/run_regression.sh --mode nightly --out deliverables_ci_local
```

## 3) Scripts and Responsibilities

- `scripts/setup.sh`: environment/bootstrap setup
- `scripts/run_regression.sh`: orchestrates regression lifecycle
- `scripts/check_coverage.py`: checks coverage threshold
- `scripts/analyze_results.py`: builds analysis summary JSON
- `scripts/performance_tracker.py`: tracks trend metrics and degradation
- `scripts/generate_report.py`: creates dashboard report outputs
- `scripts/check_sign_off.py`: evaluates release criteria
- `scripts/create_sign_off_report.py`: creates human-readable sign-off report
- `scripts/notify_failure.py`: sends Slack/Teams notifications
- `scripts/pattern_versioning.py`: tracks pattern set approvals and rollback references

## 4) Sign-off Criteria

Release gate passes only if all criteria are true:

- Test execution completed successfully
- Fault coverage >= configured target (default 95%)
- No performance degradation alert above threshold (default 10%)
- Regression report generated
- Documentation index present (`docs/search_index.json`)

## 5) Caching Strategy

### In GitHub Actions

- Pip cache via `actions/setup-python` cache support
- Preserve generated artifacts with `upload-artifact`

### Optional repository-level cache folders

- `.cache/` for temporary preprocessed data
- `performance/` for trend history

## 6) Performance Benchmarking

Tracked metrics include:

- Compilation time
- Smoke test duration
- Full regression duration
- Peak memory usage

Degradation rule:

- Alert when any metric is >10% worse than baseline.

## 7) Failure Notifications

Set these secrets in GitHub repository settings:

- `SLACK_WEBHOOK_URL`
- `TEAMS_WEBHOOK_URL`

Failure notifications include workflow context and direct run URL.

## 8) Pattern Signing and Versioning

Pattern approval metadata is stored at:

- `patterns/signoff/pattern_versions.json`

Record a new signed pattern version:

```bash
python scripts/pattern_versioning.py \
  --pattern-set gpu_smoke_set \
  --version v1.2.0 \
  --approved-by Raghuveer \
  --reason "Coverage stable above 95% with no regressions"
```

## 9) Production Deployment Procedure

1. Run `main_signoff` pipeline successfully.
2. Confirm sign-off report in `reports/signoff_report.json`.
3. Confirm pattern version entry created with approver and reason.
4. Tag release and archive corresponding artifacts.
5. Communicate release metrics to stakeholders.

## 10) Maintenance and Governance

- Review CI settings quarterly.
- Recalibrate benchmark baselines after major toolchain changes.
- Keep hooks and scripts aligned with workflow logic.
- Update this guide whenever jobs or criteria are changed.

