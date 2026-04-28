#!/usr/bin/env python3
"""Lightweight code quality review summary generator."""

from __future__ import annotations

import ast
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def _python_files() -> list[Path]:
    return [p for p in (ROOT / "python").rglob("*.py") if p.is_file()]


def _analyze_file(path: Path) -> dict:
    src = path.read_text(encoding="utf-8-sig", errors="ignore")
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return {
            "file": str(path.relative_to(ROOT)).replace("\\", "/"),
            "functions": 0,
            "classes": 0,
            "branch_nodes": 0,
            "line_count": len(src.splitlines()),
            "parse_skipped": True,
        }
    funcs = sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
    classes = sum(isinstance(n, ast.ClassDef) for n in ast.walk(tree))
    branches = sum(isinstance(n, (ast.If, ast.For, ast.While, ast.Try, ast.Match)) for n in ast.walk(tree))
    return {
        "file": str(path.relative_to(ROOT)).replace("\\", "/"),
        "functions": funcs,
        "classes": classes,
        "branch_nodes": branches,
        "line_count": len(src.splitlines()),
    }


def main() -> None:
    rows = [_analyze_file(p) for p in _python_files()]
    rows.sort(key=lambda r: (r["branch_nodes"], r["line_count"]), reverse=True)
    out = ROOT / "reports" / "code_quality_report.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {"summary_count": len(rows), "top_complex_files": rows[:20]}
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote code quality report: {out}")


if __name__ == "__main__":
    main()

