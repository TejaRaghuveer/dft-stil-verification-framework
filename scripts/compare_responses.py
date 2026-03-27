#!/usr/bin/env python3
"""Compare expected vs actual response files and emit HTML summary."""

import argparse
import html
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "python"))

from pattern_debug.response_comparer import ResponseComparer  # noqa: E402


def read_seq(path: str) -> str:
    t = Path(path).read_text(encoding="utf-8").strip().replace("\n", "")
    return "".join(ch for ch in t if ch in "01XZLH")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("-pattern", required=True)
    ap.add_argument("-expected", required=True)
    ap.add_argument("-actual", required=True)
    ap.add_argument("-output", required=True)
    args = ap.parse_args()

    exp = read_seq(args.expected)
    act = read_seq(args.actual)
    res = ResponseComparer().compare(exp, act)

    body = f"""
    <h1>Pattern Debug Report</h1>
    <p>Pattern file: {html.escape(args.pattern)}</p>
    <p>First difference: {res.first_diff_index}</p>
    <p>Mismatch count: {res.mismatch_count}</p>
    <pre>Expected: {html.escape(res.expected)}</pre>
    <pre>Actual:   {html.escape(res.actual)}</pre>
    <pre>Timing: {json.dumps(res.timing_analysis, indent=2)}</pre>
    <ul>{''.join(f'<li>{html.escape(x)}</li>' for x in res.suggestions)}</ul>
    """
    doc = f"<html><body>{body}</body></html>"
    Path(args.output).write_text(doc, encoding="utf-8")


if __name__ == "__main__":
    main()
