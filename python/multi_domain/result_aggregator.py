"""
Aggregate pass/fail, coverage, and cross-domain flags from multiple domains.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class DomainResult:
    domain_id: str
    patterns_run: int = 0
    patterns_pass: int = 0
    patterns_fail: int = 0
    fault_coverage_pct: float = 0.0
    test_coverage_pct: float = 0.0
    defect_level_ppm: Optional[float] = None
    coverage_by_fault_type: Dict[str, float] = field(default_factory=dict)
    coverage_by_module: Dict[str, float] = field(default_factory=dict)
    cross_domain_notes: List[str] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MultiDomainResultAggregator:
    """Collect DomainResult entries and produce integrated metrics."""

    results: List[DomainResult] = field(default_factory=list)

    def add(self, r: DomainResult) -> None:
        self.results.append(r)

    def aggregate(self) -> Dict[str, Any]:
        total_run = sum(r.patterns_run for r in self.results)
        total_pass = sum(r.patterns_pass for r in self.results)
        total_fail = sum(r.patterns_fail for r in self.results)
        # Weighted coverage by pattern count
        w_cov = 0.0
        w_tc = 0.0
        w = 0.0
        for r in self.results:
            n = max(r.patterns_run, 1)
            w_cov += r.fault_coverage_pct * n
            w_tc += r.test_coverage_pct * n
            w += n
        avg_fc = w_cov / w if w else 0.0
        avg_tc = w_tc / w if w else 0.0

        merged_modules: Dict[str, List[float]] = {}
        merged_types: Dict[str, List[float]] = {}
        for r in self.results:
            for k, v in r.coverage_by_module.items():
                merged_modules.setdefault(k, []).append(v)
            for k, v in r.coverage_by_fault_type.items():
                merged_types.setdefault(k, []).append(v)

        cross: List[str] = []
        for r in self.results:
            cross.extend(r.cross_domain_notes)

        return {
            "per_domain": [self._domain_dict(r) for r in self.results],
            "integrated": {
                "total_patterns_run": total_run,
                "total_pass": total_pass,
                "total_fail": total_fail,
                "weighted_fault_coverage_pct": round(avg_fc, 4),
                "weighted_test_coverage_pct": round(avg_tc, 4),
                "cross_domain_issues": cross,
            },
            "merged_module_coverage_avg": {k: sum(v) / len(v) for k, v in merged_modules.items()},
            "merged_fault_type_coverage_avg": {k: sum(v) / len(v) for k, v in merged_types.items()},
        }

    @staticmethod
    def _domain_dict(r: DomainResult) -> Dict[str, Any]:
        return {
            "domain_id": r.domain_id,
            "patterns_run": r.patterns_run,
            "patterns_pass": r.patterns_pass,
            "patterns_fail": r.patterns_fail,
            "fault_coverage_pct": r.fault_coverage_pct,
            "test_coverage_pct": r.test_coverage_pct,
            "defect_level_ppm": r.defect_level_ppm,
            "coverage_by_fault_type": dict(r.coverage_by_fault_type),
            "coverage_by_module": dict(r.coverage_by_module),
            "cross_domain_notes": list(r.cross_domain_notes),
        }
