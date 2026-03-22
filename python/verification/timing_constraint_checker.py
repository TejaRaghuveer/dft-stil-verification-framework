"""
Pattern / vector timing checks against TimingConfig (integrates with python/timing).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

try:
    from ..timing.timing_config import TimingConfig
except ImportError:
    try:
        from timing.timing_config import TimingConfig
    except ImportError:
        TimingConfig = None  # type: ignore


@dataclass
class TimingConstraintChecker:
    """
    Verify per-cycle or per-vector margins and clock-data skew from exported metrics.

    Rows may include: ``time_ns``, ``data_edge_ns``, ``clock_edge_ns``, ``signal``,
    ``setup_margin_ns``, ``hold_margin_ns``, ``skew_ns``.
    """

    config: Any
    skew_limit_ns: float = 0.2
    failures: List[Dict[str, Any]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if TimingConfig is not None and not isinstance(self.config, TimingConfig):
            pass  # allow dict-like for tests

    def check_row(self, row: Dict[str, Any]) -> None:
        idx = row.get("cycle", row.get("vector", -1))
        if "setup_margin_ns" in row and float(row["setup_margin_ns"]) < 0:
            self.failures.append(
                {
                    "index": idx,
                    "kind": "setup",
                    "signal": row.get("signal", ""),
                    "value_ns": float(row["setup_margin_ns"]),
                    "requirement": "setup >= 0",
                }
            )
        if "hold_margin_ns" in row and float(row["hold_margin_ns"]) < 0:
            self.failures.append(
                {
                    "index": idx,
                    "kind": "hold",
                    "signal": row.get("signal", ""),
                    "value_ns": float(row["hold_margin_ns"]),
                    "requirement": "hold >= 0",
                }
            )
        skew = row.get("skew_ns")
        if skew is not None and abs(float(skew)) > self.skew_limit_ns:
            self.failures.append(
                {
                    "index": idx,
                    "kind": "clock_data_skew",
                    "signal": row.get("signal", ""),
                    "skew_ns": float(skew),
                    "limit_ns": self.skew_limit_ns,
                }
            )

    def check_trace(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.failures.clear()
        for r in rows:
            self.check_row(r)
        return self.report()

    def report(self) -> Dict[str, Any]:
        cfg_summary = {}
        if TimingConfig is not None and isinstance(self.config, TimingConfig):
            cfg_summary = {
                "tck_mhz": self.config.tck_frequency_mhz,
                "system_mhz": self.config.system_clock_mhz,
                "setup_ns": self.config.setup_time_ns,
                "hold_ns": self.config.hold_time_ns,
            }
        return {
            "timing_analysis_report": True,
            "constraints_summary": cfg_summary,
            "failure_count": len(self.failures),
            "all_within_constraints": len(self.failures) == 0,
            "failures": list(self.failures),
        }
