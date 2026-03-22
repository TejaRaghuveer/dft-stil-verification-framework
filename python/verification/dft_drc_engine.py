"""
Post-insertion DFT design rule checks (structural / rule-based reports).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class DRCSeverity(str, Enum):
    CRITICAL = "critical"
    WARNING = "warning"
    INFO = "info"


@dataclass
class DRCViolation:
    rule_id: str
    message: str
    severity: DRCSeverity
    cell_or_hier: str = ""
    suggestion: str = ""


@dataclass
class DFTDRCEngine:
    """
    Check scan/DFT structural rules. Pass netlist-like dicts or use ``run_default_template``.

    Expected optional keys on a design dict:
      - ``scan_cells``: list of {name, scan_in, scan_out, scan_enable_port, clock_domain}
      - ``sequential_elements``: list of {name, is_scan, ...}
      - ``clock_gating``: list of {name, test_mode_pin, observable}
      - ``async_resets``: list of {name, clocked_domain, in_scan_path}
    """

    violations: List[DRCViolation] = field(default_factory=list)

    def clear(self) -> None:
        self.violations.clear()

    def add(self, v: DRCViolation) -> None:
        self.violations.append(v)

    def check_scan_connectivity(self, scan_cells: List[Dict[str, Any]]) -> None:
        """Verify each cell has scan_in/out names (structural)."""
        for c in scan_cells:
            name = c.get("name", "?")
            if not c.get("scan_in"):
                self.add(
                    DRCViolation(
                        "SCAN_SI",
                        "Missing scan data input connection",
                        DRCSeverity.CRITICAL,
                        name,
                        "Tie SI to previous SO or TDI",
                    )
                )
            if not c.get("scan_out"):
                self.add(
                    DRCViolation(
                        "SCAN_SO",
                        "Missing scan data output connection",
                        DRCSeverity.CRITICAL,
                        name,
                        "Connect SO to next SI or TDO mux",
                    )
                )

    def check_scan_enables(self, scan_cells: List[Dict[str, Any]]) -> None:
        for c in scan_cells:
            if not c.get("scan_enable_port") and not c.get("se"):
                self.add(
                    DRCViolation(
                        "SCAN_SE",
                        "No scan enable on scan cell",
                        DRCSeverity.WARNING,
                        c.get("name", "?"),
                        "Ensure SE driven in shift/capture modes",
                    )
                )

    def check_non_scan_sequentials(self, sequentials: List[Dict[str, Any]]) -> None:
        for s in sequentials:
            if not s.get("is_scan", True):
                self.add(
                    DRCViolation(
                        "SEQ_NONSCAN",
                        "Sequential element not replaced with scan cell",
                        DRCSeverity.CRITICAL,
                        s.get("name", "?"),
                        "Use scan flop or add test point / wrapper",
                    )
                )

    def check_reset_controllability(self, resets: List[Dict[str, Any]]) -> None:
        for r in resets:
            if r.get("async") and r.get("in_scan_path"):
                self.add(
                    DRCViolation(
                        "ASYNC_RESET_GLITCH",
                        "Async reset on synchronous scan path — glitch hazard",
                        DRCSeverity.WARNING,
                        r.get("name", "?"),
                        "Synchronize reset or block during capture",
                    )
                )
            if not r.get("controllable_in_scan_mode", True):
                self.add(
                    DRCViolation(
                        "RESET_SCAN",
                        "Reset not controllable during scan mode",
                        DRCSeverity.CRITICAL,
                        r.get("name", "?"),
                        "Gate reset with test_mode or scan_en",
                    )
                )

    def check_clock_gating(self, cg_cells: List[Dict[str, Any]]) -> None:
        for g in cg_cells:
            if not g.get("test_mode_pin") and not g.get("observable"):
                self.add(
                    DRCViolation(
                        "CG_DFT",
                        "Clock gating not observable/controllable for DFT",
                        DRCSeverity.WARNING,
                        g.get("name", "?"),
                        "Provide TE/TM pin or observability for ATPG",
                    )
                )

    def run_on_design(self, design: Dict[str, Any]) -> Dict[str, Any]:
        self.clear()
        if "scan_cells" in design:
            self.check_scan_connectivity(design["scan_cells"])
            self.check_scan_enables(design["scan_cells"])
        if "sequential_elements" in design:
            self.check_non_scan_sequentials(design["sequential_elements"])
        if "async_resets" in design:
            self.check_reset_controllability(design["async_resets"])
        if "clock_gating" in design:
            self.check_clock_gating(design["clock_gating"])
        return self.report()

    def report(self) -> Dict[str, Any]:
        by_sev = {"critical": 0, "warning": 0, "info": 0}
        for v in self.violations:
            by_sev[v.severity.value] = by_sev.get(v.severity.value, 0) + 1
        return {
            "dft_drc_report": True,
            "summary": by_sev,
            "violations": [
                {
                    "rule_id": v.rule_id,
                    "message": v.message,
                    "severity": v.severity.value,
                    "hierarchy": v.cell_or_hier,
                    "suggestion": v.suggestion,
                }
                for v in self.violations
            ],
        }
