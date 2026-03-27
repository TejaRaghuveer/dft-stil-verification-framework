"""Signal statistics and anomaly detection."""

from __future__ import annotations

from typing import Any, Dict, List


class SignalAnalysisTools:
    def signal_statistics(self, snapshots: List[Dict[str, str]]) -> Dict[str, Any]:
        if not snapshots:
            return {"signals": {}, "sample_count": 0}
        names = sorted({k for s in snapshots for k in s.keys()})
        stats: Dict[str, Any] = {}
        for n in names:
            vals = [s.get(n, "X") for s in snapshots]
            transitions = sum(1 for i in range(1, len(vals)) if vals[i] != vals[i - 1])
            ones = sum(1 for v in vals if v == "1")
            zeros = sum(1 for v in vals if v == "0")
            stats[n] = {
                "transitions": transitions,
                "activity": transitions / max(len(vals) - 1, 1),
                "ones": ones,
                "zeros": zeros,
                "stuck_at": "1" if zeros == 0 and ones > 0 else "0" if ones == 0 and zeros > 0 else None,
            }
        return {"signals": stats, "sample_count": len(snapshots)}

    def anomalies(self, snapshots: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        st = self.signal_statistics(snapshots)
        out: List[Dict[str, Any]] = []
        for sig, m in st["signals"].items():
            if m["stuck_at"] is not None:
                out.append({"signal": sig, "kind": "stuck", "value": m["stuck_at"]})
            if m["activity"] == 0 and m["stuck_at"] is None:
                out.append({"signal": sig, "kind": "no_transitions"})
            if m["activity"] > 0.9:
                out.append({"signal": sig, "kind": "unexpected_toggle_rate", "activity": m["activity"]})
        return out
