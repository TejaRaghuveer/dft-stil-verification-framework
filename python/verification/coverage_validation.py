"""
Cross-check functional / protocol coverage expectations vs collected bins.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Set


@dataclass
class CoverageValidation:
    """
    ``expected`` maps category -> set or list of required items.
    ``collected`` maps category -> set or count of hit items.
    """

    gaps: List[Dict[str, Any]] = field(default_factory=list)

    def validate_protocol_coverage(
        self,
        tap_states_required: Set[str],
        tap_states_hit: Set[str],
        operations_hit: Set[str],
        operations_required: Set[str],
    ) -> Dict[str, Any]:
        self.gaps.clear()
        missing_states = tap_states_required - tap_states_hit
        missing_ops = operations_required - operations_hit
        for s in missing_states:
            self.gaps.append({"category": "tap_state", "item": s, "severity": "warning"})
        for o in missing_ops:
            self.gaps.append({"category": "jtag_operation", "item": o, "severity": "info"})
        return self._report("protocol")

    def validate_data_patterns(
        self,
        patterns_required: Dict[str, bool],
        patterns_hit: Dict[str, bool],
    ) -> Dict[str, Any]:
        self.gaps.clear()
        for name, req in patterns_required.items():
            if req and not patterns_hit.get(name, False):
                self.gaps.append({"category": "data_pattern", "item": name, "severity": "info"})
        return self._report("data_patterns")

    def _report(self, kind: str) -> Dict[str, Any]:
        return {
            "coverage_validation": True,
            "kind": kind,
            "complete": len(self.gaps) == 0,
            "gap_count": len(self.gaps),
            "gaps": list(self.gaps),
        }
