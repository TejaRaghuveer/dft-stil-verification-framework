#!/usr/bin/env python3
"""
Build a searchable documentation index for local use.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOTS = [ROOT / "docs", ROOT / "training", ROOT]
ALLOWED = {".md", ".py", ".sv", ".txt"}
SKIP_DIRS = {".git", "__pycache__", "deliverables", "deliverables_ci", "venv", ".venv"}


def extract_title(lines: List[str], fallback: str) -> str:
    for line in lines:
        s = line.strip()
        if s.startswith("# "):
            return s[2:].strip()
    return fallback


def build_index() -> List[Dict[str, object]]:
    index: List[Dict[str, object]] = []
    for root in SEARCH_ROOTS:
        if not root.exists():
            continue
        for p in root.rglob("*"):
            if not p.is_file() or p.suffix.lower() not in ALLOWED:
                continue
            if any(part in SKIP_DIRS for part in p.parts):
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            lines = text.splitlines()
            rel = str(p.relative_to(ROOT)).replace("\\", "/")
            index.append(
                {
                    "path": rel,
                    "title": extract_title(lines, p.name),
                    "line_count": len(lines),
                    "preview": text[:300],
                }
            )
    return sorted(index, key=lambda x: x["path"])


def main() -> None:
    index = build_index()
    out = ROOT / "docs" / "search_index.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(index, indent=2), encoding="utf-8")
    print(f"Wrote {len(index)} entries to {out}")


if __name__ == "__main__":
    main()

