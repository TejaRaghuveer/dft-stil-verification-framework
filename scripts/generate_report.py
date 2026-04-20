#!/usr/bin/env python3
"""Generate CI dashboard JSON/Markdown from analysis and performance files."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Generate CI report bundle.")
    ap.add_argument("--analysis", default="reports/analysis_summary.json")
    ap.add_argument("--coverage", default="reports/coverage_check.json")
    ap.add_argument("--performance", default="reports/performance_report.json")
    ap.add_argument("--out-json", default="reports/regression_report.json")
    ap.add_argument("--out-md", default="reports/regression_dashboard.md")
    args = ap.parse_args()

    analysis = _read_json(Path(args.analysis))
    coverage = _read_json(Path(args.coverage))
    perf = _read_json(Path(args.performance))

    payload = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "analysis": analysis,
        "coverage": coverage,
        "performance": perf,
        "status": "PASSED" if coverage.get("passed", False) and not perf.get("alerts") else "FAILED",
    }

    out_json = Path(args.out_json)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    md = [
        "# CI/CD Pipeline Dashboard",
        "",
        f"- Latest run: `{payload['generated_at_utc']}`",
        f"- Status: **{payload['status']}**",
        "",
        "## Metrics",
        f"- Fault coverage: `{coverage.get('actual', 'n/a')}%` (target `{coverage.get('target', 'n/a')}%`)",
        f"- Coverage check: `{'PASS' if coverage.get('passed') else 'FAIL'}`",
        f"- Performance alerts: `{len(perf.get('alerts', []))}`",
    ]
    if perf.get("alerts"):
        md.append("")
        md.append("## Alerts")
        md.extend([f"- {a}" for a in perf["alerts"]])

    Path(args.out_md).write_text("\n".join(md) + "\n", encoding="utf-8")
    print(f"Wrote report files: {args.out_json}, {args.out_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
