"""Pattern debugging and failure analysis framework."""

from .pattern_debugger import (
    Breakpoint,
    DebugEvent,
    PatternDebugger,
    PatternVector,
    SignalSnapshot,
)
from .failure_analyzer import FailureAnalyzer, FailureCategory
from .waveform_viewer_integration import WaveformViewerIntegration
from .response_comparer import ResponseComparer, ResponseCompareResult
from .fault_injection_debugger import FaultInjectionDebugger, InjectedFault
from .pattern_modification_suggester import PatternModificationSuggester
from .signal_analysis_tools import SignalAnalysisTools
from .comparative_analysis import ComparativeAnalysis
from .visualization_tools import VisualizationTools

__all__ = [
    "Breakpoint",
    "DebugEvent",
    "PatternDebugger",
    "PatternVector",
    "SignalSnapshot",
    "FailureAnalyzer",
    "FailureCategory",
    "WaveformViewerIntegration",
    "ResponseComparer",
    "ResponseCompareResult",
    "FaultInjectionDebugger",
    "InjectedFault",
    "PatternModificationSuggester",
    "SignalAnalysisTools",
    "ComparativeAnalysis",
    "VisualizationTools",
]
