"""
Fault Coverage Analysis System
------------------------------

Fault coverage engine, report generator, undetected/gap/distribution analyzers,
trendline, module-level coverage, and interactive fault browser.
"""

from .fault_coverage_engine import (
    FaultCoverageAnalyzer,
    FaultCoverageConfig,
    FaultCoverageStatus,
    FaultRecord,
    FaultBrowser,
    CoverageReportGenerator,
    UndetectedFaultAnalyzer,
    PatternGapAnalyzer,
    FaultDistributionAnalyzer,
    CoverageTrendline,
    UndetectedReason,
    CoverageAnalysisReportParams,
    format_coverage_analysis_report,
    run_full_analysis,
)

__all__ = [
    "FaultCoverageAnalyzer",
    "FaultCoverageConfig",
    "FaultCoverageStatus",
    "FaultRecord",
    "FaultBrowser",
    "CoverageReportGenerator",
    "UndetectedFaultAnalyzer",
    "PatternGapAnalyzer",
    "FaultDistributionAnalyzer",
    "CoverageTrendline",
    "UndetectedReason",
    "CoverageAnalysisReportParams",
    "format_coverage_analysis_report",
    "run_full_analysis",
]
