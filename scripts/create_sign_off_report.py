#!/usr/bin/env python3
"""Create human-readable sign-off report from sign-off check JSON."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="Create sign-off report.")
    ap.add_argument("--input", default="reports/signoff_check.json")
    ap.add_argument("--output", default="reports/signoff_report.json")
    ap.add_argument("--output-md", default="reports/signoff_report.md")
    args = ap.parse_args()

    src = Path(args.input)
    if not src.exists():
        raise FileNotFoundError(f"Missing sign-off input: {src}")
    payload = json.loads(src.read_text(encoding="utf-8"))
    payload["generated_at_utc"] = datetime.now(timezone.utc).isoformat()

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    lines = [
        "# Sign-off Report",
        "",
        f"- Generated at: `{payload['generated_at_utc']}`",
        f"- Overall status: `{'PASS' if payload.get('passed') else 'FAIL'}`",
        "",
        "## Criteria",
    ]
    for key, value in payload.get("checks", {}).items():
        lines.append(f"- {'✓' if value else 'x'} {key}")
    Path(args.output_md).write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"Wrote sign-off report: {args.output}, {args.output_md}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
