"""
JTAG / TAP protocol compliance checker (IEEE 1149.1) — offline from cycle logs.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

from .tap_fsm_reference import TAPState, next_tap_state


class ViolationKind(str, Enum):
    ILLEGAL_TRANSITION = "illegal_transition"
    TIMING = "timing"
    TDO_SHIFT = "tdo_shift"
    RESET = "reset"


@dataclass
class ProtocolViolation:
    cycle: int
    kind: ViolationKind
    message: str
    expected_state: Optional[str] = None
    actual_state: Optional[str] = None
    severity: str = "error"


@dataclass
class ProtocolChecker:
    """
    Verify TMS-driven TAP transitions and basic shift-window TDO rules.

    Feed rows from simulation export: each row needs at least ``tms`` (0/1).
    Optional: ``cycle``, ``tdi``, ``tdo``, ``trst_n``, ``setup_margin_ns``, ``hold_margin_ns``.
    """

    violations: List[ProtocolViolation] = field(default_factory=list)
    current_state: TAPState = TAPState.TAP_UNKNOWN
    tck_period_ns: float = 100.0
    min_setup_ns: float = 0.0
    min_hold_ns: float = 0.0

    def reset(self) -> None:
        self.violations.clear()
        self.current_state = TAPState.TAP_UNKNOWN

    def check_cycle(self, row: Dict[str, Any]) -> None:
        cyc = int(row.get("cycle", -1))
        tms = int(row["tms"]) if "tms" in row else int(row.get("TMS", 0))
        trst = row.get("trst_n", row.get("TRST_N", 1))
        if trst == 0 or trst is False:
            self.current_state = TAPState.TEST_LOGIC_RESET
            return

        expected_next = next_tap_state(self.current_state, tms)
        obs = row.get("tap_state") or row.get("state")
        if obs is not None:
            try:
                obs_e = TAPState[str(obs).upper()] if isinstance(obs, str) else TAPState(int(obs))
            except (KeyError, ValueError):
                obs_e = None
            if obs_e is not None and obs_e != expected_next:
                self.violations.append(
                    ProtocolViolation(
                        cyc,
                        ViolationKind.ILLEGAL_TRANSITION,
                        "TAP state mismatch: after TMS=%s expected %s, saw %s"
                        % (tms, expected_next.name, obs_e.name),
                        expected_state=expected_next.name,
                        actual_state=obs_e.name,
                    )
                )

        in_shift = self.current_state in (TAPState.SHIFT_DR, TAPState.SHIFT_IR) or expected_next in (
            TAPState.SHIFT_DR,
            TAPState.SHIFT_IR,
        )
        self.current_state = expected_next

        if row.get("tdo_is_x") or row.get("TDO_X"):
            if in_shift:
                self.violations.append(
                    ProtocolViolation(
                        cyc,
                        ViolationKind.TDO_SHIFT,
                        "TDO is X during Shift-DR/IR",
                        severity="error",
                    )
                )

        su = row.get("setup_margin_ns")
        ho = row.get("hold_margin_ns")
        if su is not None and float(su) < self.min_setup_ns:
            self.violations.append(
                ProtocolViolation(cyc, ViolationKind.TIMING, "setup margin %s < %s" % (su, self.min_setup_ns))
            )
        if ho is not None and float(ho) < self.min_hold_ns:
            self.violations.append(
                ProtocolViolation(cyc, ViolationKind.TIMING, "hold margin %s < %s" % (ho, self.min_hold_ns))
            )

    def check_trace(self, rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        self.reset()
        for r in rows:
            self.check_cycle(r)
        return self.compliance_report()

    def compliance_report(self) -> Dict[str, Any]:
        return {
            "protocol": "IEEE 1149.1 TAP",
            "violation_count": len(self.violations),
            "compliant": len(self.violations) == 0,
            "violations": [
                {
                    "cycle": v.cycle,
                    "kind": v.kind.value,
                    "message": v.message,
                    "expected_state": v.expected_state,
                    "actual_state": v.actual_state,
                    "severity": v.severity,
                }
                for v in self.violations
            ],
            "final_tap_state": self.current_state.name,
        }
