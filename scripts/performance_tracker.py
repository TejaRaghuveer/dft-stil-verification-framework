#!/usr/bin/env python3
"""Track regression performance trends and detect degradations."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean


def _load(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return []


def main() -> int:
    ap = argparse.ArgumentParser(description="Performance trend tracker.")
    ap.add_argument("--history", default="performance/history.json")
    ap.add_argument("--metric", action="append", default=[], help="Metric in key=value format")
    ap.add_argument("--max-degradation", type=float, default=10.0, help="Allowed degradation percent")
    ap.add_argument("--report", default="reports/performance_report.json")
    args = ap.parse_args()

    history_path = Path(args.history)
    history_path.parent.mkdir(parents=True, exist_ok=True)
    history = _load(history_path)

    current: dict[str, float] = {}
    for entry in args.metric:
        if "=" not in entry:
            continue
        key, value = entry.split("=", 1)
        current[key.strip()] = float(value)

    row = {"timestamp": datetime.now(timezone.utc).isoformat(), "metrics": current}
    history.append(row)
    history_path.write_text(json.dumps(history, indent=2), encoding="utf-8")

    baseline = history[0]["metrics"] if history else {}
    alerts: list[str] = []
    for key, cur in current.items():
        base = baseline.get(key, cur)
        if base == 0:
            continue
        delta = ((cur - base) / base) * 100.0
        if delta > args.max_degradation:
            alerts.append(f"{key} degraded by {delta:.2f}% (> {args.max_degradation:.2f}%)")

    report = {
        "samples": len(history),
        "baseline_metrics": baseline,
        "current_metrics": current,
        "rolling_average": {
            key: mean([h.get("metrics", {}).get(key, current[key]) for h in history[-10:]])
            for key in current
        },
        "alerts": alerts,
    }
    report_path = Path(args.report)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Wrote performance report: {report_path}")
    return 1 if alerts else 0


if __name__ == "__main__":
    raise SystemExit(main())
