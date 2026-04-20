#!/usr/bin/env python3
"""Aggregate execution metrics from deliverable reports into CI-friendly JSON."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def _load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Analyze DFT run outputs.")
    ap.add_argument("--out", default="deliverables_ci", help="Deliverables output directory")
    ap.add_argument("--report", default="reports/analysis_summary.json", help="Summary JSON output")
    args = ap.parse_args()

    out = Path(args.out)
    manifest = _load_json(out / "week3_manifest.json")
    fc = _load_json(out / "Reports" / "fault_coverage_week3.json")

    summary = {
        "deliverables_dir": str(out),
        "manifest_present": bool(manifest),
        "fault_coverage_present": bool(fc),
        "achieved_fault_coverage": fc.get("summary", {}).get("overall_coverage", 0.0),
        "execution_summary": manifest.get("execution_summary", {}),
    }

    report = Path(args.report)
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"Wrote analysis summary: {report}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
