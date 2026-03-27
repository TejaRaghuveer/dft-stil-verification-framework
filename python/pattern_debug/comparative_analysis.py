"""Compare passing vs failing pattern populations and classify failure traits."""

from __future__ import annotations

from typing import Any, Dict, List


class ComparativeAnalysis:
    def compare(self, passing: List[Dict[str, Any]], failing: List[Dict[str, Any]]) -> Dict[str, Any]:
        def avg(rows: List[Dict[str, Any]], key: str) -> float:
            vals = [float(r.get(key, 0.0)) for r in rows]
            return sum(vals) / len(vals) if vals else 0.0

        features = ["path_depth", "shift_cycles", "capture_cycles", "tck_mhz"]
        deltas = {
            f: {"pass_avg": avg(passing, f), "fail_avg": avg(failing, f), "delta": avg(failing, f) - avg(passing, f)}
            for f in features
        }
        cls = self._classify(deltas)
        return {
            "feature_deltas": deltas,
            "failure_classification": cls,
            "design_modification_suggestion": self._design_suggestion(cls),
        }

    @staticmethod
    def _classify(deltas: Dict[str, Dict[str, float]]) -> str:
        if deltas["tck_mhz"]["delta"] > 20 and deltas["path_depth"]["delta"] > 1:
            return "timing_sensitive_high_speed_paths"
        if deltas["capture_cycles"]["delta"] < 0:
            return "insufficient_capture_window"
        return "mixed_or_data_dependent"

    @staticmethod
    def _design_suggestion(cls: str) -> str:
        if cls == "timing_sensitive_high_speed_paths":
            return "Investigate STA critical paths, add observability, or retime logic"
        if cls == "insufficient_capture_window":
            return "Increase capture cycles or improve scan-capture sequencing"
        return "Review failing clusters and module hotspots"
