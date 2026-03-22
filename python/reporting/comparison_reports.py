"""Compare two report JSON blobs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict


def _get(d: Dict[str, Any], key: str, default=None):
    if key in d:
        return d[key]
    return default


@dataclass
class ComparisonReport:
    label_a: str
    label_b: str
    delta: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {"compare_a": self.label_a, "compare_b": self.label_b, "delta": self.delta}


def compare_reports(
    report_a: Dict[str, Any],
    report_b: Dict[str, Any],
    label_a: str = "A",
    label_b: str = "B",
) -> ComparisonReport:
    delta: Dict[str, Any] = {}
    for k in ("patterns_total", "patterns_pass", "fault_coverage_pct", "test_coverage_pct"):
        va = _get(report_a, k)
        vb = _get(report_b, k)
        if va is not None and vb is not None:
            try:
                delta[k] = {"a": va, "b": vb, "diff": float(vb) - float(va)}
            except (TypeError, ValueError):
                delta[k] = {"a": va, "b": vb}
    ca = report_a.get("coverage_by_module") or {}
    cb = report_b.get("coverage_by_module") or {}
    mods = set(ca.keys()) | set(cb.keys())
    delta["module_coverage_delta"] = {
        m: {"a": ca.get(m), "b": cb.get(m), "diff": (cb.get(m) or 0) - (ca.get(m) or 0)} for m in mods
    }
    return ComparisonReport(label_a, label_b, delta)
