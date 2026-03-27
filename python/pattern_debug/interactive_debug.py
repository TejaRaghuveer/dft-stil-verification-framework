"""Debug framework orchestration helpers and report assembly."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from .comparative_analysis import ComparativeAnalysis
from .failure_analyzer import FailureAnalyzer
from .pattern_debugger import Breakpoint, PatternDebugger, PatternVector
from .pattern_modification_suggester import PatternModificationSuggester
from .response_comparer import ResponseComparer
from .signal_analysis_tools import SignalAnalysisTools
from .waveform_viewer_integration import WaveformViewerIntegration


@dataclass
class DebugRunResult:
    payload: Dict[str, Any]


class PatternDebugOrchestrator:
    def __init__(self) -> None:
        self.debugger = PatternDebugger()
        self.failure_analyzer = FailureAnalyzer()
        self.wave = WaveformViewerIntegration()
        self.comparer = ResponseComparer()
        self.suggester = PatternModificationSuggester()
        self.signal_tools = SignalAnalysisTools()
        self.comp = ComparativeAnalysis()

    def run_single_pattern(
        self,
        pattern_name: str,
        vectors: List[PatternVector],
        observed_values: List[Dict[str, str]],
        expected_tdo: str,
        actual_tdo: str,
        breakpoints: List[Breakpoint],
    ) -> DebugRunResult:
        self.debugger.load_vectors(vectors)
        event = self.debugger.run_until_breakpoint(observed_values, breakpoints)
        cmp_res = self.comparer.compare(expected_tdo, actual_tdo)
        failure_record = {
            "expected_tdo": expected_tdo,
            "actual_tdo": actual_tdo,
        }
        analysis = self.failure_analyzer.analyze(failure_record)
        suggest = self.suggester.suggest(failure_record)
        sig_report = self.signal_tools.signal_statistics(observed_values)
        wf = self.wave.generate_waveform_manifest(
            pattern_name,
            cmp_res.first_diff_index,
            [v.stimulus for v in vectors],
            observed_values,
        )
        payload = {
            "pattern": pattern_name,
            "break_event": event.__dict__ if event else None,
            "response_comparison": cmp_res.__dict__,
            "failure_analysis": analysis,
            "suggestions": suggest,
            "signal_report": sig_report,
            "waveform": wf,
            "history": self.debugger.transaction_history_replay(),
        }
        return DebugRunResult(payload)
