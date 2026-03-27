#!/usr/bin/env python3
"""Suggest pattern fixes based on failure response file."""

import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from pattern_debug.pattern_modification_suggester import PatternModificationSuggester  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-pattern", required=True)
    ap.add_argument("-failure", required=True)
    ap.add_argument("-output", required=True)
    args = ap.parse_args()

    fail_text = Path(args.failure).read_text(encoding="utf-8") if Path(args.failure).exists() else ""
    rec = {
        "expected_tdo": "",
        "actual_tdo": fail_text.strip(),
        "setup_margin_ns": -0.1 if "TIMING" in fail_text.upper() else 0.0,
        "hold_margin_ns": 0.0,
        "skew_ns": 0.4 if "SKEW" in fail_text.upper() else 0.0,
    }
    out = PatternModificationSuggester().suggest(rec)
    Path(args.output).write_text(json.dumps(out, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
