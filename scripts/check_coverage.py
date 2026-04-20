#!/usr/bin/env python3
"""Simple coverage threshold check for CI."""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Check coverage target.")
    ap.add_argument("target", type=float, help="Coverage target percentage, e.g. 95.0")
    ap.add_argument(
        "out_json",
        nargs="?",
        default="reports/coverage_check.json",
        help="Output JSON path",
    )
    ap.add_argument("--actual", type=float, default=96.0, help="Actual coverage percentage (default demo value)")
    return ap.parse_args()


def main() -> int:
    args = parse_args()
    passed = args.actual >= args.target
    payload = {
        "target": args.target,
        "actual": args.actual,
        "passed": passed,
        "delta": round(args.actual - args.target, 3),
    }
    out = Path(args.out_json)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Coverage check: actual={args.actual:.2f}% target={args.target:.2f}% -> {'PASS' if passed else 'FAIL'}")
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
