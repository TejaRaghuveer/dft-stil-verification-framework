#!/usr/bin/env python3
"""Extract a named pattern block from ATPG/STIL-like text."""

import argparse
import re
from pathlib import Path


def extract(pattern_name: str, text: str) -> str:
    # Try STIL Pattern "name" { ... }
    m = re.search(r'Pattern\s+"?%s"?\s*\{(.*?)\n\}' % re.escape(pattern_name), text, re.DOTALL)
    if m:
        return m.group(0)
    # Fallback: line-start label "name: ..."
    lines = [ln for ln in text.splitlines() if ln.strip().startswith(pattern_name + ":")]
    if lines:
        return "\n".join(lines)
    raise ValueError(f"Pattern not found: {pattern_name}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("pattern_name")
    ap.add_argument("atpg_file")
    args = ap.parse_args()
    txt = Path(args.atpg_file).read_text(encoding="utf-8")
    print(extract(args.pattern_name, txt))


if __name__ == "__main__":
    main()
