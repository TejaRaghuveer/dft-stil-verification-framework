"""Failure categorization and root-cause analysis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional


class FailureCategory(str, Enum):
    TIMING_VIOLATION = "timing_violation"
    DATA_MISMATCH = "data_mismatch"
    NO_RESPONSE = "no_response"
    INITIALIZATION_FAILURE = "initialization_failure"
    UNKNOWN = "unknown"


@dataclass
class FailureAnalyzer:
    def analyze(self, record: Dict[str, Any]) -> Dict[str, Any]:
        category = self._categorize(record)
        return {
            "category": category.value,
            "root_cause": self._root_cause(record, category),
            "remedies": self._remedies(category),
        }

    def _categorize(self, rec: Dict[str, Any]) -> FailureCategory:
        if rec.get("setup_margin_ns", 0) < 0 or rec.get("hold_margin_ns", 0) < 0:
            return FailureCategory.TIMING_VIOLATION
        if rec.get("actual_tdo") is None or rec.get("actual_tdo", "").strip("XZ") == "":
            return FailureCategory.NO_RESPONSE
        if rec.get("init_ok") is False:
            return FailureCategory.INITIALIZATION_FAILURE
        if rec.get("expected_tdo") != rec.get("actual_tdo"):
            return FailureCategory.DATA_MISMATCH
        return FailureCategory.UNKNOWN

    @staticmethod
    def _root_cause(rec: Dict[str, Any], cat: FailureCategory) -> str:
        if cat == FailureCategory.TIMING_VIOLATION:
            return "Negative setup/hold margin indicates capture timing failure"
        if cat == FailureCategory.NO_RESPONSE:
            return "TDO appears stuck/floating or not sampled in shift window"
        if cat == FailureCategory.INITIALIZATION_FAILURE:
            return "Reset/TAP initialization not in expected state before pattern"
        if cat == FailureCategory.DATA_MISMATCH:
            return "Expected and actual response diverge"
        return "Insufficient evidence"

    @staticmethod
    def _remedies(cat: FailureCategory) -> List[str]:
        if cat == FailureCategory.TIMING_VIOLATION:
            return [
                "Lower TCK/system frequency",
                "Use alternate capture edge",
                "Add capture cycle or relax IO timing",
            ]
        if cat == FailureCategory.NO_RESPONSE:
            return ["Check TDO drive enable", "Verify shift state", "Check chain continuity"]
        if cat == FailureCategory.INITIALIZATION_FAILURE:
            return ["Enforce TAP reset", "Add init sequence", "Validate TRST and mode pins"]
        if cat == FailureCategory.DATA_MISMATCH:
            return ["Inspect first mismatch vector", "Correlate waveform", "Adjust pattern timing/stimulus"]
        return ["Capture more debug context"]
