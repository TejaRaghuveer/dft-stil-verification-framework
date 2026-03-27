"""Expected-vs-actual response comparison and timing deltas."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ResponseCompareResult:
    first_diff_index: Optional[int]
    expected: str
    actual: str
    mismatch_count: int
    timing_analysis: Dict[str, float]
    suggestions: List[str]


class ResponseComparer:
    def compare(
        self,
        expected: str,
        actual: str,
        expected_time_ns: Optional[List[float]] = None,
        actual_time_ns: Optional[List[float]] = None,
    ) -> ResponseCompareResult:
        n = min(len(expected), len(actual))
        first = None
        mismatch = 0
        for i in range(n):
            if expected[i] != actual[i]:
                mismatch += 1
                if first is None:
                    first = i
        mismatch += abs(len(expected) - len(actual))

        timing = self._timing(expected_time_ns, actual_time_ns)
        sugg = self._suggest(first, mismatch, timing)
        return ResponseCompareResult(first, expected, actual, mismatch, timing, sugg)

    @staticmethod
    def _timing(exp_t: Optional[List[float]], act_t: Optional[List[float]]) -> Dict[str, float]:
        if not exp_t or not act_t:
            return {"avg_delay_ns": 0.0, "max_skew_ns": 0.0}
        n = min(len(exp_t), len(act_t))
        deltas = [act_t[i] - exp_t[i] for i in range(n)]
        return {
            "avg_delay_ns": sum(deltas) / n if n else 0.0,
            "max_skew_ns": max(abs(d) for d in deltas) if deltas else 0.0,
        }

    @staticmethod
    def _suggest(first: Optional[int], mismatch: int, timing: Dict[str, float]) -> List[str]:
        s: List[str] = []
        if first is not None:
            s.append(f"Inspect vector {first} and surrounding transitions")
        if mismatch > 0 and abs(timing.get("avg_delay_ns", 0.0)) > 0.2:
            s.append("Adjust capture edge or add capture cycle")
        if timing.get("max_skew_ns", 0.0) > 0.5:
            s.append("Reduce clock/data skew or lower TCK")
        if not s:
            s.append("Responses aligned")
        return s
