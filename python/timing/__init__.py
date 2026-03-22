"""
Timing-aware pattern execution: at-speed modeling, margins, violations, multi-domain clocks.
"""

from .timing_config import (
    ClockDomainSpec,
    TimingConfig,
    load_timing_config_from_dict,
    load_timing_config_from_yaml,
)
from .timing_execution import (
    AtSpeedExecutionEngine,
    EdgeSelectionOptimizer,
    MultiDomainClockSequencer,
    OperationalSpeedAnalyzer,
    TimingViolationDetector,
    build_full_timing_report,
)
from .constraints_parser import parse_timing_constraints_text

__all__ = [
    "ClockDomainSpec",
    "TimingConfig",
    "load_timing_config_from_dict",
    "load_timing_config_from_yaml",
    "AtSpeedExecutionEngine",
    "EdgeSelectionOptimizer",
    "TimingViolationDetector",
    "MultiDomainClockSequencer",
    "OperationalSpeedAnalyzer",
    "parse_timing_constraints_text",
    "build_full_timing_report",
]
