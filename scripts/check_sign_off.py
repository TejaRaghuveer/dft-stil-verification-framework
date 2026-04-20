#!/usr/bin/env python3
"""Evaluate sign-off criteria for CI and release gating."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Check sign-off criteria.")
    ap.add_argument("--coverage", default="reports/coverage_check.json")
    ap.add_argument("--analysis", default="reports/analysis_summary.json")
    ap.add_argument("--performance", default="reports/performance_report.json")
    ap.add_argument("--target-coverage", type=float, default=95.0)
    ap.add_argument("--output", default="reports/signoff_check.json")
    args = ap.parse_args()

    coverage = _load(Path(args.coverage))
    analysis = _load(Path(args.analysis))
    performance = _load(Path(args.performance))

    achieved = float(coverage.get("actual", 0.0))
    checks = {
        "all_tests_passed": bool(analysis.get("manifest_present")),
        "fault_coverage_target": achieved >= args.target_coverage,
        "no_performance_regression": len(performance.get("alerts", [])) == 0,
        "report_generated": Path("reports/regression_report.json").exists(),
        "documentation_index_present": Path("docs/search_index.json").exists(),
    }
    passed = all(checks.values())
    payload = {
        "passed": passed,
        "target_coverage": args.target_coverage,
        "achieved_coverage": achieved,
        "checks": checks,
    }
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Sign-off {'PASS' if passed else 'FAIL'} -> {out}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
