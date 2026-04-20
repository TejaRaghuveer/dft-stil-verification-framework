#!/usr/bin/env python3
"""
Simple local documentation search over docs/search_index.json.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "docs" / "search_index.json"


def load_index() -> List[Dict[str, Any]]:
    if not INDEX.exists():
        raise FileNotFoundError("Run scripts/generate_doc_index.py first.")
    return json.loads(INDEX.read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Search local documentation index.")
    ap.add_argument("query", help="Term to search in title/path/preview")
    ap.add_argument("--limit", type=int, default=10, help="Maximum results")
    args = ap.parse_args()

    q = args.query.lower()
    rows = load_index()
    matches = [
        r
        for r in rows
        if q in str(r.get("title", "")).lower()
        or q in str(r.get("path", "")).lower()
        or q in str(r.get("preview", "")).lower()
    ]
    for row in matches[: args.limit]:
        print(f"- {row['path']} :: {row['title']}")
    print(f"\n{len(matches)} match(es)")


if __name__ == "__main__":
    main()

