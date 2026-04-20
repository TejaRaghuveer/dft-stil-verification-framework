#!/usr/bin/env python3
"""
Basic documentation audit:
- Python classes/functions missing docstrings
- SystemVerilog classes missing leading comment block
"""

from __future__ import annotations

import ast
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def audit_python() -> list[str]:
    issues: list[str] = []
    for p in (ROOT / "python").rglob("*.py"):
        try:
            tree = ast.parse(p.read_text(encoding="utf-8"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
                if ast.get_docstring(node) is None:
                    issues.append(f"[PY] Missing docstring: {p.relative_to(ROOT)}::{node.name}")
    return issues


def audit_systemverilog() -> list[str]:
    issues: list[str] = []
    class_re = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)")
    for p in (ROOT / "uvm_tb").rglob("*.sv"):
        lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
        for i, line in enumerate(lines):
            m = class_re.match(line)
            if not m:
                continue
            prev = lines[max(0, i - 3) : i]
            if not any(x.strip().startswith("//") or x.strip().startswith("/*") for x in prev):
                issues.append(f"[SV] Missing class comment: {p.relative_to(ROOT)}::{m.group(1)}")
    return issues


def main() -> None:
    issues = audit_python() + audit_systemverilog()
    if not issues:
        print("No documentation issues found.")
        return
    print("Documentation audit issues:")
    for item in issues:
        print(f"- {item}")


if __name__ == "__main__":
    main()

