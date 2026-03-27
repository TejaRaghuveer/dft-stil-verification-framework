"""Pattern fix recommendations from failure signatures and timing stats."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class PatternModificationSuggester:
    def suggest(self, failure_record: Dict[str, Any]) -> Dict[str, Any]:
        recs: List[Dict[str, Any]] = []
        setup = float(failure_record.get("setup_margin_ns", 0.0))
        hold = float(failure_record.get("hold_margin_ns", 0.0))
        skew = abs(float(failure_record.get("skew_ns", 0.0)))

        if setup < 0 or hold < 0:
            recs.append({"change": "reduce_tck_frequency", "likelihood": 0.85})
            recs.append({"change": "switch_capture_edge", "likelihood": 0.65})
            recs.append({"change": "add_capture_cycle", "likelihood": 0.72})
        if skew > 0.3:
            recs.append({"change": "adjust_stimulus_timing", "likelihood": 0.6})
        if not recs:
            recs.append({"change": "no_change_required", "likelihood": 0.2})

        scripts = self._scripts(recs)
        return {"recommendations": recs, "modification_scripts": scripts}

    @staticmethod
    def _scripts(recs: List[Dict[str, Any]]) -> List[str]:
        out: List[str] = []
        for r in recs:
            c = r["change"]
            if c == "reduce_tck_frequency":
                out.append("+TCK_FREQ_MHZ=100")
            elif c == "switch_capture_edge":
                out.append("+CAPTURE_EDGE=leading")
            elif c == "add_capture_cycle":
                out.append("+CAPTURE_CYCLES=2")
            elif c == "adjust_stimulus_timing":
                out.append("+PRIMARY_SETUP_NS=3 +PRIMARY_HOLD_NS=3")
        return out
