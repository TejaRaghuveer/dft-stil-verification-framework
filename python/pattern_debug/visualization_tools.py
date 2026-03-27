"""Failure distribution and hotspot visualization data builders."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Dict, List


class VisualizationTools:
    def failure_distribution_map(self, failures: List[Dict[str, Any]]) -> Dict[str, int]:
        by_loc: Dict[str, int] = defaultdict(int)
        for f in failures:
            by_loc[str(f.get("location", "unknown"))] += 1
        return dict(by_loc)

    def fault_distribution_relative_to_failures(
        self,
        faults: List[Dict[str, Any]],
        failures: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        fail_ids = {str(f.get("fault_id", "")) for f in failures}
        by_type: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "failed": 0})
        for ft in faults:
            t = str(ft.get("fault_type", "UNKNOWN"))
            fid = str(ft.get("fault_id", ""))
            by_type[t]["total"] += 1
            if fid in fail_ids:
                by_type[t]["failed"] += 1
        return dict(by_type)

    def pattern_correlation(self, failure_matrix: Dict[str, List[str]]) -> Dict[str, Dict[str, float]]:
        """Input: pattern -> list of failing fault IDs. Output: Jaccard correlation matrix."""
        pats = sorted(failure_matrix.keys())
        out: Dict[str, Dict[str, float]] = {p: {} for p in pats}
        sets = {p: set(failure_matrix[p]) for p in pats}
        for a in pats:
            for b in pats:
                u = len(sets[a] | sets[b])
                i = len(sets[a] & sets[b])
                out[a][b] = (i / u) if u else 1.0
        return out

    def hotspot_analysis(self, failures: List[Dict[str, Any]], top_n: int = 10) -> List[Dict[str, Any]]:
        counts = self.failure_distribution_map(failures)
        hot = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:top_n]
        return [{"location": loc, "count": cnt} for loc, cnt in hot]
