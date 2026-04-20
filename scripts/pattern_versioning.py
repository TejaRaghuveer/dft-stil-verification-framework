#!/usr/bin/env python3
"""Maintain pattern sign-off/version metadata with rollback pointers."""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path


def load(path: Path) -> dict:
    if not path.exists():
        return {"history": []}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description="Pattern version/sign-off tracker.")
    ap.add_argument("--db", default="patterns/signoff/pattern_versions.json")
    ap.add_argument("--pattern-set", required=True)
    ap.add_argument("--version", required=True)
    ap.add_argument("--approved-by", required=True)
    ap.add_argument("--reason", required=True)
    ap.add_argument("--rollback-to", default="")
    args = ap.parse_args()

    db = Path(args.db)
    db.parent.mkdir(parents=True, exist_ok=True)
    data = load(db)
    entry = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "pattern_set": args.pattern_set,
        "version": args.version,
        "approved_by": args.approved_by,
        "reason": args.reason,
        "rollback_to": args.rollback_to,
    }
    data["history"].append(entry)
    db.write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"Updated pattern version DB: {db}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
