"""Map multi-domain aggregate dict into ReportInputData."""

from __future__ import annotations

from typing import Any, Dict

from .report_generator import ReportInputData


def report_input_from_aggregate(aggregated: Dict[str, Any], design_name: str) -> ReportInputData:
    """Build ReportInputData from ``MultiDomainResultAggregator.aggregate()`` output."""
    integ = aggregated.get("integrated") or {}
    fc = float(integ.get("weighted_fault_coverage_pct", 0))
    tc = float(integ.get("weighted_test_coverage_pct", 0))
    return ReportInputData(
        design_name=design_name,
        patterns_total=int(integ.get("total_patterns_run", 0)),
        patterns_pass=int(integ.get("total_pass", 0)),
        patterns_fail=int(integ.get("total_fail", 0)),
        fault_coverage_pct=fc,
        test_coverage_pct=tc,
        coverage_by_fault_type=dict(aggregated.get("merged_fault_type_coverage_avg") or {}),
        coverage_by_module=dict(aggregated.get("merged_module_coverage_avg") or {}),
        critical_findings=list(integ.get("cross_domain_issues") or []),
    )
