"""Waveform generation metadata and viewer-link helpers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class WaveformViewerIntegration:
    output_dir: str = "out/debug"

    def generate_waveform_manifest(
        self,
        pattern_name: str,
        failure_vector: Optional[int],
        stimulus: List[Dict[str, str]],
        response: List[Dict[str, str]],
        format_hint: str = "vcd",
    ) -> Dict[str, Any]:
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
        wf_path = str(Path(self.output_dir) / f"{pattern_name}.{format_hint}")
        manifest = {
            "pattern": pattern_name,
            "waveform_path": wf_path,
            "format": format_hint,
            "failure_vector": failure_vector,
            "highlight_window": [max((failure_vector or 0) - 5, 0), (failure_vector or 0) + 5],
            "stimulus_samples": stimulus[:20],
            "response_samples": response[:20],
        }
        mpath = Path(self.output_dir) / f"{pattern_name}.waveform_manifest.json"
        mpath.write_text(__import__("json").dumps(manifest, indent=2), encoding="utf-8")
        return manifest

    @staticmethod
    def compare_expected_actual_waveforms(
        expected_points: List[Dict[str, Any]],
        actual_points: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        n = min(len(expected_points), len(actual_points))
        diffs = []
        for i in range(n):
            if expected_points[i].get("value") != actual_points[i].get("value"):
                diffs.append({"index": i, "expected": expected_points[i], "actual": actual_points[i]})
        return {"difference_count": len(diffs), "first_difference": diffs[0] if diffs else None}
