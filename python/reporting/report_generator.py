"""Executive, detailed, statistical, and quality sections for DFT reports."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional


@dataclass
class ReportInputData:
    design_name: str = ""
    test_date: str = ""
    duration_seconds: float = 0.0
    patterns_total: int = 0
    patterns_pass: int = 0
    patterns_fail: int = 0
    fault_coverage_pct: float = 0.0
    test_coverage_pct: float = 0.0
    target_coverage_pct: float = 95.0
    defect_level_ppm: Optional[float] = None
    total_faults: int = 0
    coverage_by_fault_type: Dict[str, float] = field(default_factory=dict)
    coverage_by_module: Dict[str, float] = field(default_factory=dict)
    undetected_breakdown: Dict[str, int] = field(default_factory=dict)
    per_pattern_results: List[Dict[str, Any]] = field(default_factory=list)
    execution_times_sec: List[float] = field(default_factory=list)
    coverage_convergence: List[tuple] = field(default_factory=list)  # (pattern_count, fc_pct)
    recommendations: List[str] = field(default_factory=list)
    critical_findings: List[str] = field(default_factory=list)
    traceability: List[Dict[str, str]] = field(default_factory=list)  # pattern, fault, location


def _fmt_duration(sec: float) -> str:
    td = timedelta(seconds=int(sec))
    h, r = divmod(int(sec), 3600)
    m, s = divmod(r, 60)
    return f"{h} hours {m} minutes" if h else f"{m} minutes {s} seconds"


class ReportGenerator:
    def __init__(self, data: ReportInputData):
        self.data = data

    def executive_summary(self) -> Dict[str, Any]:
        d = self.data
        fc_ok = d.fault_coverage_pct >= d.target_coverage_pct
        return {
            "title": "EXECUTIVE SUMMARY",
            "bullets": [
                "%s Achieved %.1f%% fault coverage (target: >=%.1f%%)"
                % ("✓" if fc_ok else "⚠", d.fault_coverage_pct, d.target_coverage_pct),
                "✓ All ATPG patterns executed (%d/%d PASS)"
                % (d.patterns_pass, max(d.patterns_total, 1))
                if d.patterns_fail == 0
                else "⚠ Patterns: %d PASS / %d FAIL of %d"
                % (d.patterns_pass, d.patterns_fail, d.patterns_total),
                "✓ Estimated defect level: %.1f ppm (excellent)" % d.defect_level_ppm
                if d.defect_level_ppm is not None
                else "Defect level: N/A",
                "✓ Design ready for tapeout" if fc_ok and d.patterns_fail == 0 else "Review required before tapeout",
            ],
            "critical_findings": list(d.critical_findings),
        }

    def key_metrics(self) -> Dict[str, Any]:
        d = self.data
        return {
            "title": "KEY METRICS",
            "fault_coverage_pct": d.fault_coverage_pct,
            "test_coverage_pct": d.test_coverage_pct,
            "pattern_count": d.patterns_total,
            "execution_time": _fmt_duration(d.duration_seconds),
            "defect_level_ppm": d.defect_level_ppm,
            "total_faults": d.total_faults,
        }

    def coverage_by_type_section(self) -> Dict[str, Any]:
        return {"title": "COVERAGE BY TYPE", "rows": dict(self.data.coverage_by_fault_type)}

    def module_coverage_section(self) -> Dict[str, Any]:
        return {"title": "MODULE COVERAGE", "rows": dict(self.data.coverage_by_module)}

    def failures_gaps_section(self) -> Dict[str, Any]:
        return {"title": "FAILURES & GAPS", "breakdown": dict(self.data.undetected_breakdown)}

    def recommendations_section(self) -> Dict[str, Any]:
        return {"title": "RECOMMENDATIONS", "items": list(self.data.recommendations)}

    def detailed_results(self) -> Dict[str, Any]:
        return {
            "title": "DETAILED RESULTS",
            "per_pattern": list(self.data.per_pattern_results),
        }

    def statistical_analysis(self) -> Dict[str, Any]:
        d = self.data
        times = d.execution_times_sec
        n = len(times)
        return {
            "title": "STATISTICAL ANALYSIS",
            "pattern_count_distribution": {"count": d.patterns_total},
            "execution_time": {
                "samples": n,
                "mean_sec": sum(times) / n if n else 0,
                "max_sec": max(times) if times else 0,
                "min_sec": min(times) if times else 0,
            },
            "coverage_convergence_points": len(d.coverage_convergence),
        }

    def quality_metrics(self) -> Dict[str, Any]:
        d = self.data
        testable = max(d.total_faults, 1)
        detected_equiv = int(d.fault_coverage_pct / 100.0 * testable)
        return {
            "title": "QUALITY METRICS",
            "fault_coverage_pct": d.fault_coverage_pct,
            "test_coverage_pct": d.test_coverage_pct,
            "defect_level_ppm": d.defect_level_ppm,
            "yield_note": "Use DL models for production yield; values here are illustrative",
            "approx_detected_faults": detected_equiv,
        }

    def build_text_report(self, sections: List[str]) -> str:
        """Plain-text report like the user example."""
        d = self.data
        lines = [
            "DFT VERIFICATION REPORT",
            "",
            "Design: %s" % d.design_name,
            "Test Date: %s" % (d.test_date or datetime.now().strftime("%Y-%m-%d")),
            "Test Duration: %s" % _fmt_duration(d.duration_seconds),
            "",
        ]
        if "executive_summary" in sections:
            es = self.executive_summary()
            lines.extend(["EXECUTIVE SUMMARY", "=" * 16, ""])
            for b in es["bullets"]:
                lines.append(b)
            lines.append("")
        if "key_metrics" in sections:
            km = self.key_metrics()
            lines.extend(["KEY METRICS", "=" * 11, ""])
            lines.append("Fault Coverage: %.1f%%" % km["fault_coverage_pct"])
            lines.append("Test Coverage: %.1f%%" % km["test_coverage_pct"])
            lines.append("Pattern Count: %s" % km["pattern_count"])
            lines.append("Execution Time: %s" % km["execution_time"])
            if km.get("defect_level_ppm") is not None:
                lines.append("Defect Level: %.1f ppm @ %s faults" % (km["defect_level_ppm"], km["total_faults"]))
            lines.append("")
        if "coverage_by_type" in sections:
            lines.extend(["COVERAGE BY TYPE", "=" * 18, ""])
            for k, v in self.data.coverage_by_fault_type.items():
                lines.append("%s: %.1f%%" % (k, v))
            lines.append("")
        if "module_coverage" in sections:
            lines.extend(["MODULE COVERAGE", "=" * 17, ""])
            for k, v in self.data.coverage_by_module.items():
                lines.append("%s: %.1f%%" % (k, v))
            lines.append("")
        if "failures_gaps" in sections:
            lines.extend(["FAILURES & GAPS", "=" * 16, ""])
            for k, v in self.data.undetected_breakdown.items():
                lines.append("%s: %s" % (k, v))
            lines.append("")
        if "recommendations" in sections:
            lines.extend(["RECOMMENDATIONS", "=" * 15, ""])
            for i, r in enumerate(self.data.recommendations, 1):
                lines.append("%d. %s" % (i, r))
            lines.append("")
        if "sign_off" in sections:
            lines.extend(
                [
                    "SIGN-OFF",
                    "=" * 8,
                    "[ ] Design Review Team Approval",
                    "[ ] Test Engineering Team Approval",
                    "[ ] Manufacturing Team Approval",
                    "[ ] Quality Assurance Approval",
                ]
            )
        return "\n".join(lines)
