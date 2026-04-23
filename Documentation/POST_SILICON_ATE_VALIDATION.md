# Post-Silicon ATE Integration and Validation Guide

This guide explains how to move from pre-silicon pattern generation into tester-oriented post-silicon execution, with compatibility checks, conversion, validation, and correlation workflows.

## Scope

The post-silicon toolkit is implemented in:

- `python/post_silicon/ate_validation.py`
- `python/post_silicon/__main__.py`
- `scripts/generate_ate_program.py`
- `config/ate_config.example.txt`

## Implemented Components

### 1) ATE Pattern Converter

Class: `ATEPatternConverter`

- Converts STIL-derived patterns into vendor-specific exports:
  - Teradyne V93000 (TRF-like textual export)
  - LTX Credence (pattern export)
  - Xcerra (pattern export)
- Preserves vector count fidelity and emits conversion reports.
- Output report includes pattern and vector counts plus fidelity percentage.

### 2) ATE Compatibility Checker

Class: `ATECompatibilityChecker`

Checks:

- TCK frequency against tester maximum
- Required channel count against tester channels
- Pattern memory estimate against tester memory capacity
- Pattern execution rate against tester throughput

Output:

- `compatible` status
- `violations` and `warnings`
- requested vs estimated utilization

### 3) Pattern Validation for ATE

Class: `PatternValidationForATE`

- Validates pin mapping completeness (`DUT_* -> ATE_CH*`)
- Checks setup/hold/TCO margins against clock period
- Produces a validation report with pass/fail and violation details
- Includes ATE simulator result placeholder (`PASS/FAIL/SKIPPED`)

### 4) Expected Response Database

Class: `ExpectedResponseDatabase`

- Generates a golden response DB per pattern
- Stores test limits/tolerances for pass/fail compare on tester
- Output format is JSON for portability and toolchain adaptation

### 5) Debug Pattern Generation

Class: `DebugPatternGeneration`

Produces diagnostic pattern groups for:

- module-level isolation (ALU/register/interconnect)
- power margin sensitivity
- clock path verification

### 6) ATE Test Program Template

Class: `ATEProgramBuilder`, script: `scripts/generate_ate_program.py`

- Builds a test-program template with pattern list and procedure flow
- Includes startup, execution, and shutdown procedure hooks
- Generates an executable template that can be adapted per tester API

### 7) Yield Prediction Model

Class: `YieldPredictionModel`

- Uses fault coverage, defect density (faults/mm^2), and die area
- Generates predicted yield percentage
- Highlights critical focus areas for design/test improvement

### 8) Post-Silicon Correlation Framework

Class: `PostSiliconCorrelationFramework`

- Compares post-silicon pass rate against pre-silicon expectations
- Flags large correlation deltas as discrepancy candidates
- Produces correlation report for design/test feedback loops

### 9) Failure Analysis Tools

Class: `FailureAnalysisTools`

- Aggregates top failing pattern families
- Recommends focused yield-improvement actions
- Bridges tester failures back into pre-silicon debug workflow

## Configuration

Use:

- `config/ate_config.example.txt`

It includes tester specs, timing specs, and procedure mapping.

## End-to-End Usage

From repo root:

```bash
set PYTHONPATH=python
python -m post_silicon --config config/ate_config.example.txt --stil-file patterns/stuck_at.stil --out-dir out/post_silicon --tck-mhz 200 --required-channels 64
```

Generated outputs include:

- conversion report
- compatibility report
- ATE validation report
- expected responses DB
- debug pattern DB
- ATE test program template
- yield forecast
- correlation report
- failure analysis report
- post-silicon manifest

## ATE Integration Strategy

1. Validate compatibility before conversion to avoid late-stage tester failures.
2. Run pattern validation with pin mapping and timing constraints before first lot.
3. Load expected response DB and limits for robust pass/fail determination.
4. Use debug patterns for immediate root-cause narrowing on tester failures.
5. Feed failure/correlation reports back into DFT pattern tuning and design closure.

## Production Notes

- The converter output is intentionally textual and traceable for review.
- Vendor-specific binary/program compilation can be layered on top as a next-step integration.
- Keep tester specs and timing margins versioned with each silicon lot and test program release.

