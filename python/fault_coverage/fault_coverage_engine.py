"""
Fault Coverage Analysis System
------------------------------

Tracks achieved fault coverage, identifies gaps, and provides insights for
pattern optimization. Integrates with the pattern database (pattern_db) and
can be fed from ATPG tool reports or atpg_pattern_t fault_list data.

Concepts:
- Fault Coverage = Detected / (Total - Undetectable) * 100%
- Test Coverage = Detected / (Total - Undetectable - Untestable) * 100%
- Defect Level, Pattern Efficiency, Coverage Contribution
"""

from __future__ import annotations

import argparse
import json
import math
import os
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any, Set

# Optional: use pattern_db types if available
try:
    from pattern_db.pattern_database import PatternDatabase, PatternRecord, PatternType
except ImportError:
    PatternDatabase = None
    PatternRecord = None
    PatternType = None


# ---------------------------------------------------------------------------
# Fault status and fault record
# ---------------------------------------------------------------------------


class FaultCoverageStatus(str, Enum):
    DETECTED = "DETECTED"
    UNDETECTABLE = "UNDETECTABLE"
    UNTESTABLE = "UNTESTABLE"
    RETRY_NEEDED = "RETRY_NEEDED"
    UNKNOWN = "UNKNOWN"


class UndetectedReason(str, Enum):
    UNTESTABLE = "UNTESTABLE"
    UNDETECTABLE = "UNDETECTABLE"
    RETRY_NEEDED = "RETRY_NEEDED"


@dataclass
class FaultRecord:
    fault_id: str
    fault_type: str  # e.g. "STUCK_AT", "TDF", "PATH"
    location: str
    detected_by_patterns: List[str] = field(default_factory=list)
    coverage_status: FaultCoverageStatus = FaultCoverageStatus.UNKNOWN
    undetected_reason: Optional[UndetectedReason] = None
    module: str = ""
    coverage_contribution_pct: float = 0.0
    # Optional detail for coverage analysis report (e.g. "sequential depth = 12 >> 8")
    category_detail: str = ""
    # Optional recommendation text (e.g. "Re-target with deeper sequential depth allowed")
    recommendation: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "fault_id": self.fault_id,
            "fault_type": self.fault_type,
            "location": self.location,
            "detected_by_patterns": self.detected_by_patterns,
            "coverage_status": self.coverage_status.value,
            "undetected_reason": self.undetected_reason.value if self.undetected_reason else None,
            "module": self.module,
            "coverage_contribution_pct": self.coverage_contribution_pct,
            "category_detail": self.category_detail,
            "recommendation": self.recommendation,
        }


# ---------------------------------------------------------------------------
# Fault coverage analyzer
# ---------------------------------------------------------------------------


class FaultCoverageAnalyzer:
    """
    Tracks which faults are detected by which patterns and maintains
    fault database with coverage status. Builds from pattern→fault_list
    mapping (e.g. from PatternDatabase or ATPG report).
    """

    def __init__(self) -> None:
        self.fault_db: Dict[str, FaultRecord] = {}
        self.pattern_to_faults: Dict[str, List[str]] = defaultdict(list)
        self._total_faults = 0
        self._detected = 0
        self._undetectable = 0
        self._untestable = 0
        self._retry_needed = 0

    def register_fault(
        self,
        fault_id: str,
        fault_type: str = "STUCK_AT",
        location: str = "",
        module: str = "",
        status: FaultCoverageStatus = FaultCoverageStatus.UNKNOWN,
        undetected_reason: Optional[UndetectedReason] = None,
    ) -> None:
        if fault_id not in self.fault_db:
            self.fault_db[fault_id] = FaultRecord(
                fault_id=fault_id,
                fault_type=fault_type,
                location=location,
                module=module,
                coverage_status=status,
                undetected_reason=undetected_reason,
            )
            self._total_faults += 1
            if status == FaultCoverageStatus.DETECTED:
                self._detected += 1
            elif status == FaultCoverageStatus.UNDETECTABLE:
                self._undetectable += 1
            elif status == FaultCoverageStatus.UNTESTABLE:
                self._untestable += 1
            elif status == FaultCoverageStatus.RETRY_NEEDED:
                self._retry_needed += 1

    def link_pattern_to_faults(self, pattern_name: str, fault_ids: List[str]) -> None:
        self.pattern_to_faults[pattern_name] = list(fault_ids)
        for fid in fault_ids:
            if fid not in self.fault_db:
                self.register_fault(fid, status=FaultCoverageStatus.DETECTED)
            rec = self.fault_db[fid]
            if pattern_name not in rec.detected_by_patterns:
                rec.detected_by_patterns.append(pattern_name)
            rec.coverage_status = FaultCoverageStatus.DETECTED
            rec.undetected_reason = None
        self._recompute_counts()

    def set_fault_status(
        self,
        fault_id: str,
        status: FaultCoverageStatus,
        undetected_reason: Optional[UndetectedReason] = None,
    ) -> None:
        if fault_id not in self.fault_db:
            self.register_fault(fault_id, status=status, undetected_reason=undetected_reason)
            return
        rec = self.fault_db[fault_id]
        old = rec.coverage_status
        rec.coverage_status = status
        rec.undetected_reason = undetected_reason
        self._recompute_counts()

    def load_from_pattern_db(self, pattern_records: List[Any]) -> None:
        """Populate fault DB from list of pattern records with fault_list (e.g. PatternRecord)."""
        for p in pattern_records:
            name = getattr(p, "pattern_name", str(getattr(p, "pattern_id", "")))
            flist = getattr(p, "fault_list", [])
            if flist:
                self.link_pattern_to_faults(name, flist)
        # Any fault not yet seen can be registered as UNKNOWN; typically
        # we only have "detected" from pattern lists; undetectable/untestable
        # come from ATPG reports.
        self._recompute_counts()

    def _recompute_counts(self) -> None:
        self._detected = sum(1 for r in self.fault_db.values() if r.coverage_status == FaultCoverageStatus.DETECTED)
        self._undetectable = sum(1 for r in self.fault_db.values() if r.coverage_status == FaultCoverageStatus.UNDETECTABLE)
        self._untestable = sum(1 for r in self.fault_db.values() if r.coverage_status == FaultCoverageStatus.UNTESTABLE)
        self._retry_needed = sum(1 for r in self.fault_db.values() if r.coverage_status == FaultCoverageStatus.RETRY_NEEDED)
        self._total_faults = len(self.fault_db)

    # -------------------- Coverage metrics --------------------

    def fault_coverage_pct(self) -> float:
        """Fault Coverage = Detected / (Total - Undetectable) * 100%."""
        denom = self._total_faults - self._undetectable
        if denom <= 0:
            return 0.0
        return 100.0 * self._detected / denom

    def test_coverage_pct(self) -> float:
        """Test Coverage = Detected / (Total - Undetectable - Untestable) * 100%."""
        denom = self._total_faults - self._undetectable - self._untestable
        if denom <= 0:
            return 0.0
        return 100.0 * self._detected / denom

    def defect_level(self) -> float:
        """Defect Level = (1 - Fault_Coverage/100) ^ fault_count (simplified: 1 - coverage as fraction)."""
        fc = self.fault_coverage_pct() / 100.0
        return (1.0 - fc)  # fraction of defects escaping

    def pattern_efficiency(self) -> float:
        """Average faults detected per pattern (patterns that detect at least one fault)."""
        patterns_with_faults = [p for p, flist in self.pattern_to_faults.items() if flist]
        if not patterns_with_faults:
            return 0.0
        total = sum(len(self.pattern_to_faults[p]) for p in patterns_with_faults)
        return total / len(patterns_with_faults)

    def coverage_contribution_by_pattern(self) -> Dict[str, Dict[str, Any]]:
        """For each pattern: faults detected, unique fault count, coverage contribution %."""
        total_detectable = self._total_faults - self._undetectable
        if total_detectable <= 0:
            total_detectable = 1
        out: Dict[str, Dict[str, Any]] = {}
        for pattern_name, fault_ids in self.pattern_to_faults.items():
            unique = len(set(fault_ids))
            contrib_pct = 100.0 * unique / total_detectable
            out[pattern_name] = {
                "faults_detected": fault_ids,
                "unique_fault_count": unique,
                "coverage_contribution_pct": round(contrib_pct, 4),
            }
        return out

    def get_detected_faults(self) -> List[FaultRecord]:
        return [r for r in self.fault_db.values() if r.coverage_status == FaultCoverageStatus.DETECTED]

    def get_undetected_faults(self) -> List[FaultRecord]:
        return [
            r
            for r in self.fault_db.values()
            if r.coverage_status
            in (
                FaultCoverageStatus.UNDETECTABLE,
                FaultCoverageStatus.UNTESTABLE,
                FaultCoverageStatus.RETRY_NEEDED,
                FaultCoverageStatus.UNKNOWN,
            )
        ]


# ---------------------------------------------------------------------------
# Coverage report generator
# ---------------------------------------------------------------------------


class CoverageReportGenerator:
    """Produces summary, fault list, pattern contribution, by-type, and by-module sections."""

    def __init__(self, analyzer: FaultCoverageAnalyzer) -> None:
        self.analyzer = analyzer

    def generate_summary(self) -> Dict[str, Any]:
        total = self.analyzer._total_faults
        det = self.analyzer._detected
        undet = self.analyzer._undetectable
        untest = self.analyzer._untestable
        retry = self.analyzer._retry_needed
        return {
            "total_faults": total,
            "detected": det,
            "undetectable": undet,
            "untestable": untest,
            "retry_needed": retry,
            "fault_coverage_pct": round(self.analyzer.fault_coverage_pct(), 2),
            "test_coverage_pct": round(self.analyzer.test_coverage_pct(), 2),
            "defect_level": round(self.analyzer.defect_level(), 4),
            "pattern_efficiency": round(self.analyzer.pattern_efficiency(), 2),
        }

    def generate_fault_list_section(self) -> List[Dict[str, Any]]:
        """For each undetected fault: location, type, reason, category_detail, recommendation."""
        out = []
        for r in self.analyzer.get_undetected_faults():
            out.append({
                "fault_id": r.fault_id,
                "fault_type": r.fault_type,
                "location": r.location,
                "module": r.module,
                "status": r.coverage_status.value,
                "reason": r.undetected_reason.value if r.undetected_reason else "UNKNOWN",
                "category_detail": r.category_detail,
                "recommendation": r.recommendation,
            })
        return out

    def generate_pattern_contribution_table(self) -> List[Dict[str, Any]]:
        """For each pattern: faults detected, unique count, coverage contribution %."""
        return [
            {"pattern": name, **data}
            for name, data in self.analyzer.coverage_contribution_by_pattern().items()
        ]

    def generate_coverage_by_type(self) -> Dict[str, Dict[str, int]]:
        """Coverage counts per fault_type (e.g. STUCK_AT, TDF)."""
        by_type: Dict[str, Dict[str, int]] = defaultdict(lambda: {"detected": 0, "total": 0})
        for r in self.analyzer.fault_db.values():
            by_type[r.fault_type]["total"] += 1
            if r.coverage_status == FaultCoverageStatus.DETECTED:
                by_type[r.fault_type]["detected"] += 1
        return dict(by_type)

    def generate_coverage_by_module(self) -> Dict[str, Dict[str, Any]]:
        """Coverage per module (if module field set)."""
        by_mod: Dict[str, Dict[str, Any]] = defaultdict(lambda: {"detected": 0, "total": 0})
        for r in self.analyzer.fault_db.values():
            mod = r.module or "_unknown"
            by_mod[mod]["total"] += 1
            if r.coverage_status == FaultCoverageStatus.DETECTED:
                by_mod[mod]["detected"] += 1
        for mod, d in by_mod.items():
            d["coverage_pct"] = round(100.0 * d["detected"] / d["total"], 2) if d["total"] else 0.0
        return dict(by_mod)

    def module_pattern_matrix(self) -> Dict[str, Dict[str, List[str]]]:
        """Which patterns cover which modules: module -> { 'patterns': list, 'fault_ids': list }."""
        mod_patterns: Dict[str, Set[str]] = defaultdict(set)
        mod_faults: Dict[str, Set[str]] = defaultdict(set)
        for pname, fault_ids in self.analyzer.pattern_to_faults.items():
            for fid in fault_ids:
                rec = self.analyzer.fault_db.get(fid)
                if rec:
                    mod = rec.module or "_unknown"
                    mod_patterns[mod].add(pname)
                    mod_faults[mod].add(fid)
        return {
            mod: {"patterns": sorted(mod_patterns[mod]), "fault_ids": sorted(mod_faults[mod])}
            for mod in sorted(set(mod_patterns.keys()) | set(mod_faults.keys()))
        }

    def low_coverage_modules(self, threshold_pct: float = 80.0) -> List[Tuple[str, float]]:
        """List (module, coverage_pct) for modules below threshold."""
        by_mod = self.generate_coverage_by_module()
        return [(m, d["coverage_pct"]) for m, d in by_mod.items() if d["coverage_pct"] < threshold_pct and d["total"] > 0]

    def suggested_targeted_patterns_for_modules(self, low_coverage_threshold_pct: float = 80.0) -> Dict[str, Any]:
        """Suggest targeting low-coverage modules with additional ATPG; list poorly covered modules and pattern counts."""
        low = self.low_coverage_modules(low_coverage_threshold_pct)
        matrix = self.module_pattern_matrix()
        suggestions = []
        for mod, pct in low:
            patterns = matrix.get(mod, {}).get("patterns", [])
            suggestions.append({
                "module": mod,
                "coverage_pct": pct,
                "patterns_covering": len(patterns),
                "suggestion": "Run ATPG with aborted-fault list for this module or increase pattern count.",
            })
        return {"low_coverage_modules": low, "suggestions": suggestions}

    def generate_full_report(self) -> Dict[str, Any]:
        full = {
            "summary": self.generate_summary(),
            "undetected_fault_list": self.generate_fault_list_section(),
            "pattern_contribution_table": self.generate_pattern_contribution_table(),
            "coverage_by_type": self.generate_coverage_by_type(),
            "coverage_by_module": self.generate_coverage_by_module(),
        }
        full["module_pattern_matrix"] = self.module_pattern_matrix()
        full["targeted_pattern_suggestions"] = self.suggested_targeted_patterns_for_modules()
        return full


# ---------------------------------------------------------------------------
# Undetected fault analyzer
# ---------------------------------------------------------------------------


class UndetectedFaultAnalyzer:
    """Categorizes undetected faults and suggests pattern modifications for RETRY_NEEDED."""

    def __init__(self, analyzer: FaultCoverageAnalyzer) -> None:
        self.analyzer = analyzer

    def categorize_undetected(
        self,
        untestable_ids: Optional[Set[str]] = None,
        undetectable_ids: Optional[Set[str]] = None,
        retry_ids: Optional[Set[str]] = None,
    ) -> None:
        """Apply categories to current undetected faults by ID sets (e.g. from ATPG report)."""
        untestable_ids = untestable_ids or set()
        undetectable_ids = undetectable_ids or set()
        retry_ids = retry_ids or set()
        for fid, rec in self.analyzer.fault_db.items():
            if rec.coverage_status == FaultCoverageStatus.DETECTED:
                continue
            if fid in undetectable_ids:
                rec.coverage_status = FaultCoverageStatus.UNDETECTABLE
                rec.undetected_reason = UndetectedReason.UNDETECTABLE
            elif fid in untestable_ids:
                rec.coverage_status = FaultCoverageStatus.UNTESTABLE
                rec.undetected_reason = UndetectedReason.UNTESTABLE
            elif fid in retry_ids:
                rec.coverage_status = FaultCoverageStatus.RETRY_NEEDED
                rec.undetected_reason = UndetectedReason.RETRY_NEEDED
        self.analyzer._recompute_counts()

    def get_recommendations_report(self) -> Dict[str, Any]:
        """Suggest pattern modifications for RETRY_NEEDED faults."""
        retry = [r for r in self.analyzer.get_undetected_faults() if r.coverage_status == FaultCoverageStatus.RETRY_NEEDED]
        suggestions = []
        for r in retry:
            suggestions.append({
                "fault_id": r.fault_id,
                "location": r.location,
                "suggestions": [
                    "Try at-speed capture (transition delay pattern).",
                    "Try different capture edge (leading/trailing).",
                    "Increase sequential depth or add scan path for initialization.",
                ],
            })
        return {
            "retry_needed_count": len(retry),
            "faults": [r.fault_id for r in retry],
            "recommendations": suggestions,
            "summary": "For RETRY_NEEDED faults, re-run ATPG with at-speed option or different capture; check scan access and init.",
        }


# ---------------------------------------------------------------------------
# Pattern gap analyzer
# ---------------------------------------------------------------------------


class PatternGapAnalyzer:
    """Identifies groups of similar undetected faults and estimates effort to improve coverage."""

    def __init__(self, analyzer: FaultCoverageAnalyzer) -> None:
        self.analyzer = analyzer

    def group_undetected_by_type(self) -> Dict[str, List[FaultRecord]]:
        by_type: Dict[str, List[FaultRecord]] = defaultdict(list)
        for r in self.analyzer.get_undetected_faults():
            by_type[r.fault_type].append(r)
        return dict(by_type)

    def group_undetected_by_module(self) -> Dict[str, List[FaultRecord]]:
        by_mod: Dict[str, List[FaultRecord]] = defaultdict(list)
        for r in self.analyzer.get_undetected_faults():
            by_mod[r.module or "_unknown"].append(r)
        return dict(by_mod)

    def suggest_atpg_parameters(self) -> Dict[str, Any]:
        """Suggest ATPG parameters to target undetected fault groups."""
        by_type = self.group_undetected_by_type()
        suggestions = []
        if "TDF" in by_type or "TRANSITION" in by_type:
            suggestions.append("Enable transition delay fault (TDF) patterns; set at-speed capture.")
        if "PATH" in by_type:
            suggestions.append("Enable path delay patterns; increase path count or slack.")
        suggestions.append("Re-run ATPG with aborted fault list targeting undetected IDs.")
        return {"atpg_suggestions": suggestions, "undetected_by_type": {k: len(v) for k, v in by_type.items()}}

    def estimate_patterns_for_target_coverage(self, target_pct: float) -> int:
        """
        Rough estimate: assume linear marginal coverage per pattern (diminishing).
        current_cov = fault_coverage_pct(); need (target - current) / 100 * (total - undetectable) more faults.
        Patterns needed ≈ (faults_to_detect) / pattern_efficiency, capped by remaining undetected.
        """
        current = self.analyzer.fault_coverage_pct()
        if current >= target_pct:
            return 0
        total = self.analyzer._total_faults - self.analyzer._undetectable
        if total <= 0:
            return 0
        faults_to_detect = (target_pct / 100.0 - current / 100.0) * total
        eff = self.analyzer.pattern_efficiency()
        if eff <= 0:
            return 0
        return max(0, int(math.ceil(faults_to_detect / eff)))

    def generate_gap_report(self) -> Dict[str, Any]:
        out: Dict[str, Any] = {
            "undetected_by_type": {k: len(v) for k, v in self.group_undetected_by_type().items()},
            "undetected_by_module": {k: len(v) for k, v in self.group_undetected_by_module().items()},
            "atpg_suggestions": self.suggest_atpg_parameters().get("atpg_suggestions", []),
        }
        for target in [95.0, 98.0, 99.0]:
            out[f"estimated_patterns_for_{target}%"] = self.estimate_patterns_for_target_coverage(target)
        return out


# ---------------------------------------------------------------------------
# Fault distribution analyzer
# ---------------------------------------------------------------------------


class FaultDistributionAnalyzer:
    """Histogram, essential/redundant patterns, Pareto (top 20% patterns → 80% faults)."""

    def __init__(self, analyzer: FaultCoverageAnalyzer) -> None:
        self.analyzer = analyzer

    def faults_per_pattern_histogram(self) -> Dict[int, int]:
        """Count of patterns that detect exactly N faults."""
        hist: Dict[int, int] = defaultdict(int)
        for fault_ids in self.analyzer.pattern_to_faults.values():
            n = len(set(fault_ids))
            hist[n] += 1
        return dict(hist)

    def essential_patterns(self) -> List[str]:
        """Patterns that detect at least one fault not detected by any other pattern."""
        fault_to_patterns: Dict[str, List[str]] = defaultdict(list)
        for pname, flist in self.analyzer.pattern_to_faults.items():
            for f in set(flist):
                fault_to_patterns[f].append(pname)
        essential = set()
        for f, plist in fault_to_patterns.items():
            if len(plist) == 1:
                essential.add(plist[0])
        return sorted(essential)

    def redundant_patterns(self) -> List[Tuple[str, str]]:
        """Pairs (pattern_a, pattern_b) where pattern_b's faults are a subset of pattern_a's."""
        redundant: List[Tuple[str, str]] = []
        pat_faults = {p: set(flist) for p, flist in self.analyzer.pattern_to_faults.items()}
        for pa, fa in pat_faults.items():
            for pb, fb in pat_faults.items():
                if pa == pb:
                    continue
                if fb <= fa and len(fb) > 0:
                    redundant.append((pa, pb))
        return redundant

    def pareto_top_patterns(self, fraction: float = 0.2) -> List[str]:
        """Top fraction of patterns that contribute to (approximately) 80% of detected faults."""
        contrib = self.analyzer.coverage_contribution_by_pattern()
        sorted_pat = sorted(contrib.keys(), key=lambda p: contrib[p]["unique_fault_count"], reverse=True)
        total_unique = sum(contrib[p]["unique_fault_count"] for p in sorted_pat)
        if total_unique <= 0:
            return []
        target = 0.8 * total_unique
        cum = 0
        top = []
        for p in sorted_pat:
            top.append(p)
            cum += contrib[p]["unique_fault_count"]
            if cum >= target:
                break
        return top

    def pareto_tiers(self, pattern_counts: Optional[List[int]] = None) -> List[Tuple[int, float]]:
        """
        For each pattern count N (e.g. 100, 200, 500), return (N, cumulative_coverage_pct) when
        patterns are ordered by unique fault contribution. Used for "Top N patterns detect X% of faults".
        """
        contrib = self.analyzer.coverage_contribution_by_pattern()
        sorted_pat = sorted(contrib.keys(), key=lambda p: contrib[p]["unique_fault_count"], reverse=True)
        total_detectable = self.analyzer._total_faults - self.analyzer._undetectable
        if total_detectable <= 0:
            return []
        n_pat = len(sorted_pat)
        if pattern_counts is None:
            pattern_counts = [max(1, n_pat // 5), max(1, n_pat // 2), n_pat]
        tiers: List[Tuple[int, float]] = []
        cum = 0
        idx = 0
        for nc in sorted(pattern_counts):
            while idx < min(nc, n_pat):
                cum += contrib[sorted_pat[idx]]["unique_fault_count"]
                idx += 1
            pct = 100.0 * cum / total_detectable
            tiers.append((nc, round(pct, 1)))
        return tiers

    def generate_distribution_report(self) -> Dict[str, Any]:
        return {
            "faults_per_pattern_histogram": self.faults_per_pattern_histogram(),
            "essential_pattern_count": len(self.essential_patterns()),
            "essential_patterns": self.essential_patterns(),
            "redundant_pairs_count": len(self.redundant_patterns()),
            "pareto_top_20_percent_patterns": self.pareto_top_patterns(0.2),
        }


# ---------------------------------------------------------------------------
# Coverage trendline (convergence)
# ---------------------------------------------------------------------------


class CoverageTrendline:
    """Coverage vs. pattern count; saturation point; extrapolation for 99%."""

    def __init__(self, analyzer: FaultCoverageAnalyzer) -> None:
        self.analyzer = analyzer

    def build_curve(self, pattern_order: Optional[List[str]] = None) -> List[Tuple[int, float]]:
        """
        (pattern_count, cumulative_fault_coverage_pct).
        pattern_order: list of pattern names in execution order; default = by contribution descending.
        """
        contrib = self.analyzer.coverage_contribution_by_pattern()
        if pattern_order is None:
            pattern_order = sorted(
                contrib.keys(),
                key=lambda p: contrib[p]["unique_fault_count"],
                reverse=True,
            )
        total_detectable = self.analyzer._total_faults - self.analyzer._undetectable
        if total_detectable <= 0:
            return [(0, 0.0)]
        seen: Set[str] = set()
        curve: List[Tuple[int, float]] = [(0, 0.0)]
        for i, p in enumerate(pattern_order):
            for f in self.analyzer.pattern_to_faults.get(p, []):
                seen.add(f)
            cov_pct = 100.0 * len(seen) / total_detectable
            curve.append((i + 1, round(cov_pct, 2)))
        return curve

    def saturation_point(self, curve: List[Tuple[int, float]], threshold_delta: float = 0.5) -> int:
        """First pattern index after which adding a pattern increases coverage by less than threshold_delta%."""
        for i in range(1, len(curve)):
            if curve[i][1] - curve[i - 1][1] < threshold_delta:
                return curve[i][0]
        return curve[-1][0] if curve else 0

    def extrapolate_patterns_for_coverage(self, target_pct: float, curve: List[Tuple[int, float]]) -> int:
        """Linear extrapolation: patterns needed to reach target_pct given current curve."""
        if not curve or curve[-1][1] >= target_pct:
            return 0
        n, c = curve[-1][0], curve[-1][1]
        if n == 0:
            return 0
        # slope ≈ (c - 0) / n
        slope = c / n
        if slope <= 0:
            return 0
        return int(math.ceil((target_pct - c) / slope)) + n

    def convergence_report(self) -> Dict[str, Any]:
        curve = self.build_curve()
        sat = self.saturation_point(curve)
        est_99 = self.extrapolate_patterns_for_coverage(99.0, curve)
        return {
            "coverage_curve_sample": curve[:: max(1, len(curve) // 20)] if len(curve) > 20 else curve,
            "saturation_pattern_count": sat,
            "estimated_patterns_for_99_pct": est_99,
            "current_coverage_pct": curve[-1][1] if curve else 0.0,
        }


# ---------------------------------------------------------------------------
# Fault browser (CLI)
# ---------------------------------------------------------------------------


class FaultBrowser:
    """CLI search and export for faults and patterns."""

    def __init__(self, analyzer: FaultCoverageAnalyzer) -> None:
        self.analyzer = analyzer

    def search_faults(
        self,
        location_substr: Optional[str] = None,
        fault_type: Optional[str] = None,
        status: Optional[FaultCoverageStatus] = None,
    ) -> List[FaultRecord]:
        out = list(self.analyzer.fault_db.values())
        if location_substr:
            out = [r for r in out if location_substr.lower() in (r.location or "").lower()]
        if fault_type:
            out = [r for r in out if r.fault_type == fault_type]
        if status is not None:
            out = [r for r in out if r.coverage_status == status]
        return out

    def get_pattern_detected_faults(self, pattern_name: str) -> List[FaultRecord]:
        fault_ids = self.analyzer.pattern_to_faults.get(pattern_name, [])
        return [self.analyzer.fault_db[f] for f in fault_ids if f in self.analyzer.fault_db]

    def export_fault_list_for_atpg(self, fault_ids: List[str], path: str) -> None:
        """Write fault IDs to a text file for ATPG re-targeting."""
        with open(path, "w") as f:
            for fid in fault_ids:
                f.write(fid + "\n")


# ---------------------------------------------------------------------------
# Configuration and reporting
# ---------------------------------------------------------------------------


@dataclass
class FaultCoverageConfig:
    report_format: str = "text"  # text, json, xml, analysis
    report_file_path: str = "fault_coverage_report.txt"
    verbosity: int = 1
    include_recommendations: bool = True
    include_trendline: bool = True
    # For analysis-style report (design header, target, Pareto tiers)
    design_name: str = "Design"
    atpg_pattern_count: int = 0
    coverage_target_pct: float = 95.0
    pareto_pattern_counts: Optional[List[int]] = None  # e.g. [100, 200, 500]


@dataclass
class CoverageAnalysisReportParams:
    """Parameters for the detailed coverage analysis report (example-style layout)."""
    design_name: str = "Design"
    atpg_pattern_count: int = 0
    coverage_target_pct: float = 95.0


def _fault_type_display_name(ft: str) -> str:
    """Map internal fault_type to report display name (Stuck-at-0, Transition delay, etc.)."""
    u = (ft or "").upper()
    if "STUCK" in u and ("0" in ft or "SA0" in u):
        return "Stuck-at-0"
    if "STUCK" in u and ("1" in ft or "SA1" in u):
        return "Stuck-at-1"
    if "STUCK" in u:
        return "Stuck-at"
    if "TDF" in u or "TRANSITION" in u:
        return "Transition delay"
    if "PATH" in u:
        return "Path delay"
    return ft or "Other"


def _default_recommendation(status: str, reason: str, category_detail: str) -> str:
    """Default recommendation text when FaultRecord.recommendation is empty."""
    if status == FaultCoverageStatus.UNTESTABLE.value or reason == "UNTESTABLE":
        return "Re-target with deeper sequential depth allowed" if not category_detail else category_detail
    if status == FaultCoverageStatus.RETRY_NEEDED.value or reason == "RETRY_NEEDED":
        return "Try higher TCK frequency or different capture edge"
    if status == FaultCoverageStatus.UNDETECTABLE.value or reason == "UNDETECTABLE":
        return "Fault redundant or no observable path; design review recommended"
    return "Re-run ATPG with aborted fault list or relax constraints"


def _build_recommendations_bullets(
    full: Dict[str, Any],
    params: CoverageAnalysisReportParams,
) -> List[Tuple[str, str]]:
    """Build (bullet_char, text) for RECOMMENDATIONS section. bullet_char is 'ok' or 'warn' for ✓ vs ⚠."""
    bullets: List[Tuple[str, str]] = []
    s = full.get("summary", {})
    target = params.coverage_target_pct
    fc = s.get("fault_coverage_pct", 0) or 0
    by_type = full.get("coverage_by_type", {})
    undet = full.get("undetected_fault_list", [])
    untestable_count = s.get("untestable", 0)
    total = s.get("total_faults", 1)
    untestable_pct = 100.0 * untestable_count / total if total else 0

    if fc >= target:
        bullets.append(("ok", f"Target {target}% coverage achieved with current {params.atpg_pattern_count} patterns"))
    else:
        bullets.append(("warn", f"Fault coverage {fc}% below target {target}%; consider adding patterns or re-targeting aborted faults"))

    for ft, d in by_type.items():
        total_t = d.get("total", 0)
        if total_t == 0:
            continue
        pct = 100.0 * d.get("detected", 0) / total_t
        display_name = _fault_type_display_name(ft)
        if pct < target:
            bullets.append(("warn", f"{display_name} coverage ({pct}%) slightly below {target}% target"))
            bullets.append(("warn", f"  Suggestion: Generate additional {display_name.lower()} patterns with at-speed capture"))

    if untestable_pct <= 1.0 and untestable_count > 0:
        bullets.append(("ok", "Design appears well-testable (only {:.1f}% untestable faults)".format(untestable_pct)))
    elif untestable_count > 0:
        bullets.append(("warn", f"Recommend design review for {untestable_count} untestable faults"))
        mods = set(u.get("module") for u in undet if u.get("reason") == "UNTESTABLE" and u.get("module"))
        if mods:
            bullets.append(("warn", "  Consider adding scan enable for FSM/sequential elements in: " + ", ".join(sorted(mods))))

    return bullets


def format_coverage_analysis_report(
    full: Dict[str, Any],
    params: Optional[CoverageAnalysisReportParams] = None,
    pareto_pattern_counts: Optional[List[int]] = None,
) -> str:
    """
    Produce the detailed coverage analysis report in the example layout:
    Design header, COVERAGE SUMMARY, PATTERN CONTRIBUTION, UNDETECTED FAULTS,
    COVERAGE BY TYPE, FAULT DISTRIBUTION (Pareto), RECOMMENDATIONS.
    """
    params = params or CoverageAnalysisReportParams()
    lines: List[str] = []
    s = full.get("summary", {})

    total = s.get("total_faults", 0)
    detected = s.get("detected", 0)
    undetectable = s.get("undetectable", 0)
    untestable = s.get("untestable", 0)
    fault_cov_pct = s.get("fault_coverage_pct", 0) or 0
    test_cov_pct = s.get("test_coverage_pct", 0) or 0
    defect_level_frac = 1.0 - (fault_cov_pct / 100.0)
    defect_level_pct = defect_level_frac * 100.0
    defect_level_ppm = defect_level_frac * 1e6

    # Header
    lines.append("Coverage Analysis Report")
    lines.append("=" * 40)
    lines.append("")
    lines.append(f"Design: {params.design_name}")
    lines.append(f"ATPG Patterns: {params.atpg_pattern_count}")
    lines.append(f"Coverage Target: ≥{params.coverage_target_pct}%")
    lines.append("")
    lines.append("COVERAGE SUMMARY:")
    lines.append(f"Total Faults: {total:,}")
    det_pct = (100.0 * detected / total) if total else 0
    undet_pct = (100.0 * undetectable / total) if total else 0
    untest_pct = (100.0 * untestable / total) if total else 0
    lines.append(f"  Detected: {detected:,} ({det_pct:.1f}%)")
    lines.append(f"  Undetectable (Redundant): {undetectable:,} ({undet_pct:.1f}%)")
    lines.append(f"  Untestable (No Path): {untestable:,} ({untest_pct:.1f}%)")
    lines.append("")
    lines.append(f"Fault Coverage (Detected/Total-Undetectable): {fault_cov_pct:.2f}%")
    lines.append(f"Test Coverage (Detected/Testable): {test_cov_pct:.2f}%")
    lines.append(f"Defect Level (DL): {defect_level_pct:.4f}% ({defect_level_ppm:.1f} ppm)")
    lines.append("")
    lines.append("PATTERN CONTRIBUTION:")
    contrib = full.get("pattern_contribution_table", [])
    for i, c in enumerate(sorted(contrib, key=lambda x: x.get("unique_fault_count", 0), reverse=True)[:20]):
        pname = c.get("pattern", "")
        n_faults = len(c.get("faults_detected", []))
        unique = c.get("unique_fault_count", 0)
        pct = c.get("coverage_contribution_pct", 0)
        lines.append(f"Pattern {pname}: {n_faults} faults, {unique} unique, {pct:.3f}% coverage")
    if len(contrib) > 20:
        lines.append(f"... [top 20 of {len(contrib)} patterns by coverage]")
    lines.append("")
    lines.append("UNDETECTED FAULTS:")
    undet_list = full.get("undetected_fault_list", [])
    for i, u in enumerate(undet_list[:50], 1):
        fid = u.get("fault_id", "")
        loc = u.get("location", "")
        ft = u.get("fault_type", "")
        status = u.get("status", u.get("reason", ""))
        detail = u.get("category_detail", "")
        rec = u.get("recommendation", "") or _default_recommendation(status, u.get("reason", ""), detail)
        type_display = _fault_type_display_name(ft)
        cat_text = status
        if detail:
            cat_text = f"{status} ({detail})"
        lines.append(f"{i}. Fault_ID: {fid}")
        lines.append(f"   Location: {loc or '(none)'}")
        lines.append(f"   Type: {type_display}")
        lines.append(f"   Category: {cat_text}")
        lines.append(f"   Recommendation: {rec}")
        lines.append("")
    if len(undet_list) > 50:
        lines.append(f"... and {len(undet_list) - 50} more undetected faults")
        lines.append("")
    lines.append("COVERAGE BY TYPE:")
    by_type = full.get("coverage_by_type", {})
    for ft, d in by_type.items():
        tot = d.get("total", 0)
        det = d.get("detected", 0)
        pct = (100.0 * det / tot) if tot else 0
        lines.append(f"- {_fault_type_display_name(ft)}: {pct:.1f}% coverage")
    lines.append("")
    lines.append("FAULT DISTRIBUTION (Pareto Analysis):")
    dist = full.get("distribution", {})
    # Pareto tiers: need to compute from full report; we need the analyzer. So we accept pareto_tiers in full or compute in caller.
    pareto_tiers = full.get("pareto_tiers", [])
    for nc, pct in pareto_tiers:
        lines.append(f"- Top {nc} patterns detect {pct}% of faults")
    if not pareto_tiers:
        lines.append("- (Pareto tiers not computed; run with distribution analyzer and pass pareto_tiers)")
    lines.append("")
    lines.append("RECOMMENDATIONS:")
    rec_bullets = _build_recommendations_bullets(full, params)
    for bullet_type, text in rec_bullets:
        if bullet_type == "ok":
            lines.append("✓ " + text)
        else:
            lines.append("⚠ " + text)
    return "\n".join(lines)


def format_report_text(full: Dict[str, Any]) -> str:
    """Produce human-readable text report (like STIL/pattern_db style)."""
    lines = []
    s = full.get("summary", {})
    lines.append("=" * 60)
    lines.append("FAULT COVERAGE REPORT - SUMMARY")
    lines.append("=" * 60)
    lines.append(f"Total faults:        {s.get('total_faults', 0)}")
    lines.append(f"Detected:            {s.get('detected', 0)}")
    lines.append(f"Undetectable:        {s.get('undetectable', 0)}")
    lines.append(f"Untestable:          {s.get('untestable', 0)}")
    lines.append(f"Retry needed:        {s.get('retry_needed', 0)}")
    lines.append(f"Fault coverage %:    {s.get('fault_coverage_pct', 0)}")
    lines.append(f"Test coverage %:     {s.get('test_coverage_pct', 0)}")
    lines.append(f"Defect level:        {s.get('defect_level', 0)}")
    lines.append(f"Pattern efficiency:  {s.get('pattern_efficiency', 0)}")
    lines.append("")

    undet = full.get("undetected_fault_list", [])
    if undet:
        lines.append("-" * 60)
        lines.append("UNDETECTED FAULT LIST (location, type, reason)")
        lines.append("-" * 60)
        for u in undet[:100]:  # cap for readability
            lines.append(f"  {u.get('fault_id')} | {u.get('location', '')} | {u.get('fault_type')} | {u.get('reason', '')}")
        if len(undet) > 100:
            lines.append(f"  ... and {len(undet) - 100} more")
        lines.append("")

    contrib = full.get("pattern_contribution_table", [])
    if contrib:
        lines.append("-" * 60)
        lines.append("PATTERN CONTRIBUTION (top 30)")
        lines.append("-" * 60)
        for c in sorted(contrib, key=lambda x: x.get("unique_fault_count", 0), reverse=True)[:30]:
            lines.append(f"  {c.get('pattern', '')} | unique_faults={c.get('unique_fault_count')} | contribution%={c.get('coverage_contribution_pct')}")
        lines.append("")

    by_type = full.get("coverage_by_type", {})
    if by_type:
        lines.append("-" * 60)
        lines.append("COVERAGE BY TYPE")
        lines.append("-" * 60)
        for ft, d in by_type.items():
            lines.append(f"  {ft}: detected={d.get('detected')} total={d.get('total')}")
        lines.append("")

    by_mod = full.get("coverage_by_module", {})
    if by_mod:
        lines.append("-" * 60)
        lines.append("COVERAGE BY MODULE")
        lines.append("-" * 60)
        for mod, d in by_mod.items():
            lines.append(f"  {mod}: {d.get('coverage_pct')}% ({d.get('detected')}/{d.get('total')})")
        lines.append("")

    targeted = full.get("targeted_pattern_suggestions", {})
    if targeted.get("suggestions"):
        lines.append("-" * 60)
        lines.append("TARGETED PATTERN SUGGESTIONS (low-coverage modules)")
        lines.append("-" * 60)
        for s in targeted["suggestions"]:
            lines.append(f"  {s.get('module')}: {s.get('coverage_pct')}% | patterns={s.get('patterns_covering')} | {s.get('suggestion')}")
        lines.append("")

    gap = full.get("gap_analysis", {})
    if gap:
        lines.append("-" * 60)
        lines.append("GAP ANALYSIS")
        lines.append("-" * 60)
        for key in ("estimated_patterns_for_95.0%", "estimated_patterns_for_98.0%", "estimated_patterns_for_99.0%"):
            lines.append(f"  {key}: {gap.get(key, 'N/A')}")
        for sug in gap.get("atpg_suggestions", []):
            lines.append(f"  - {sug}")
        lines.append("")

    conv = full.get("convergence", {})
    if conv:
        lines.append("-" * 60)
        lines.append("CONVERGENCE")
        lines.append("-" * 60)
        lines.append(f"  Saturation pattern count: {conv.get('saturation_pattern_count')}")
        lines.append(f"  Estimated patterns for 99%: {conv.get('estimated_patterns_for_99_pct')}")
        lines.append("")

    dist = full.get("distribution", {})
    if dist:
        lines.append("-" * 60)
        lines.append("DISTRIBUTION")
        lines.append("-" * 60)
        lines.append(f"  Essential patterns: {dist.get('essential_pattern_count')}")
        lines.append(f"  Redundant pairs:    {dist.get('redundant_pairs_count')}")
        lines.append("")

    return "\n".join(lines)


def format_report_xml(full: Dict[str, Any]) -> str:
    """Produce XML report (same structure as JSON, for tool integration)."""
    def escape(s: Any) -> str:
        if s is None:
            return ""
        return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")

    lines = ['<?xml version="1.0" encoding="UTF-8"?>', "<fault_coverage_report>"]
    s = full.get("summary", {})
    lines.append("  <summary>")
    for k, v in s.items():
        lines.append(f"    <{k}>{escape(v)}</{k}>")
    lines.append("  </summary>")
    lines.append("  <undetected_fault_list>")
    for u in full.get("undetected_fault_list", []):
        lines.append('    <fault fault_id="' + escape(u.get("fault_id")) + '" location="' + escape(u.get("location")) + '" type="' + escape(u.get("fault_type")) + '" reason="' + escape(u.get("reason")) + '"/>')
    lines.append("  </undetected_fault_list>")
    lines.append("  <pattern_contribution_table>")
    for c in full.get("pattern_contribution_table", []):
        lines.append(f'    <pattern name="{escape(c.get("pattern"))}" unique_fault_count="{c.get("unique_fault_count")}" contribution_pct="{c.get("coverage_contribution_pct")}"/>')
    lines.append("  </pattern_contribution_table>")
    lines.append("</fault_coverage_report>")
    return "\n".join(lines)


def run_full_analysis(
    analyzer: FaultCoverageAnalyzer,
    config: Optional[FaultCoverageConfig] = None,
) -> Dict[str, Any]:
    config = config or FaultCoverageConfig()
    report_gen = CoverageReportGenerator(analyzer)
    full = report_gen.generate_full_report()
    if config.include_recommendations:
        undet = UndetectedFaultAnalyzer(analyzer)
        full["recommendations"] = undet.get_recommendations_report()
        gap = PatternGapAnalyzer(analyzer)
        full["gap_analysis"] = gap.generate_gap_report()
    if config.include_trendline:
        trend = CoverageTrendline(analyzer)
        full["convergence"] = trend.convergence_report()
    dist = FaultDistributionAnalyzer(analyzer)
    full["distribution"] = dist.generate_distribution_report()
    full["pareto_tiers"] = dist.pareto_tiers(config.pareto_pattern_counts or [100, 200, 500])

    if config.report_file_path:
        fmt = (config.report_format or "text").lower()
        if fmt == "json":
            with open(config.report_file_path, "w") as f:
                json.dump(full, f, indent=2)
        elif fmt == "xml":
            with open(config.report_file_path, "w") as f:
                f.write(format_report_xml(full))
        elif fmt == "analysis":
            params = CoverageAnalysisReportParams(
                design_name=config.design_name,
                atpg_pattern_count=config.atpg_pattern_count or len(analyzer.pattern_to_faults),
                coverage_target_pct=config.coverage_target_pct,
            )
            with open(config.report_file_path, "w") as f:
                f.write(format_coverage_analysis_report(full, params, config.pareto_pattern_counts))
        else:
            with open(config.report_file_path, "w") as f:
                f.write(format_report_text(full))
    return full


# ---------------------------------------------------------------------------
# CLI (report, search, pattern, export - like previous tools)
# ---------------------------------------------------------------------------


def _load_analyzer_from_args(args: Any) -> FaultCoverageAnalyzer:
    analyzer = FaultCoverageAnalyzer()
    path = getattr(args, "pattern_db_path", None) or getattr(args, "input", None)
    if path and os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        patterns = data.get("patterns", [])
        for p in patterns:
            name = p.get("pattern_name", str(p.get("pattern_id", "")))
            flist = p.get("fault_list", [])
            if flist:
                analyzer.link_pattern_to_faults(name, flist)
    else:
        analyzer.link_pattern_to_faults("pat_1", ["f1", "f2", "f3"])
        analyzer.link_pattern_to_faults("pat_2", ["f2", "f4"])
        analyzer.register_fault("f5", status=FaultCoverageStatus.UNTESTABLE, undetected_reason=UndetectedReason.UNTESTABLE)
        analyzer.register_fault("f6", status=FaultCoverageStatus.UNDETECTABLE, undetected_reason=UndetectedReason.UNDETECTABLE)
    return analyzer


def _run_cli() -> None:
    parser = argparse.ArgumentParser(description="Fault coverage analysis")
    parser.add_argument("--format", choices=["text", "json", "xml"], default="text", help="Report output format")
    parser.add_argument("--report", default="", help="Report file path (default: fault_coverage_report.<ext>)")
    parser.add_argument("-v", "--verbosity", type=int, default=1)
    sub = parser.add_subparsers(dest="command", help="Commands")

    # report (default)
    report_p = sub.add_parser("report", help="Generate full coverage report")
    report_p.add_argument("pattern_db_path", nargs="?", help="Input pattern DB JSON (optional)")
    report_p.add_argument("--format", choices=["text", "json", "xml", "analysis"], default="text")
    report_p.add_argument("--report", default="")
    report_p.add_argument("--design", default="", help="Design name (for analysis report)")
    report_p.add_argument("--patterns", type=int, default=0, help="ATPG pattern count (for analysis report)")
    report_p.add_argument("--target", type=float, default=95.0, help="Coverage target %% (default 95)")
    report_p.set_defaults(command="report")

    # search: fault browser - search by location, type, status
    search_p = sub.add_parser("search", help="Search faults by location, type, status")
    search_p.add_argument("input", nargs="?", help="Input pattern DB or fault DB JSON")
    search_p.add_argument("--location", "-l", help="Filter by location substring")
    search_p.add_argument("--type", "-t", dest="fault_type", help="Filter by fault type (e.g. STUCK_AT)")
    search_p.add_argument("--status", "-s", choices=[e.value for e in FaultCoverageStatus], help="Filter by coverage status")
    search_p.add_argument("--format", choices=["text", "json"], default="text")

    # pattern: show faults detected by a pattern
    pattern_p = sub.add_parser("pattern", help="Show faults detected by a pattern")
    pattern_p.add_argument("pattern_name", help="Pattern name")
    pattern_p.add_argument("--input", "-i", help="Input pattern DB JSON (optional)")
    pattern_p.add_argument("--format", choices=["text", "json"], default="text")

    # export: export fault list for ATPG re-targeting
    export_p = sub.add_parser("export", help="Export fault list to file for ATPG")
    export_p.add_argument("input", nargs="?", help="Input pattern DB JSON")
    export_p.add_argument("--output", "-o", required=True, help="Output file path")
    export_p.add_argument("--status", choices=["undetected", "retry_needed", "all"], default="undetected", help="Which faults to export")

    args = parser.parse_args()
    command = getattr(args, "command", None) or "report"

    # Resolve input path (report: pattern_db_path; search/export: input; pattern: input)
    inp = getattr(args, "pattern_db_path", None) if command == "report" else getattr(args, "input", None)
    setattr(args, "pattern_db_path", inp)
    analyzer = _load_analyzer_from_args(args)

    if command == "report":
        report_path = getattr(args, "report", None) or ""
        if not report_path:
            ext = {"text": "txt", "json": "json", "xml": "xml"}.get(getattr(args, "format", "text"), "txt")
            report_path = f"fault_coverage_report.{ext}"
        cfg = FaultCoverageConfig(
            report_format=getattr(args, "format", "text"),
            report_file_path=report_path,
            verbosity=getattr(args, "verbosity", 1),
            design_name=getattr(args, "design", "") or "Design",
            atpg_pattern_count=getattr(args, "patterns", 0),
            coverage_target_pct=getattr(args, "target", 95.0),
        )
        result = run_full_analysis(analyzer, cfg)
        if getattr(args, "format", "text") == "json":
            print(json.dumps(result, indent=2))
        elif getattr(args, "format", "text") == "xml":
            print(format_report_xml(result))
        else:
            print(format_report_text(result))

    elif command == "search":
        browser = FaultBrowser(analyzer)
        status_val = getattr(args, "status", None)
        status_enum = FaultCoverageStatus(status_val) if status_val else None
        hits = browser.search_faults(
            location_substr=getattr(args, "location", None),
            fault_type=getattr(args, "fault_type", None),
            status=status_enum,
        )
        if getattr(args, "format", "text") == "json":
            print(json.dumps([r.to_dict() for r in hits], indent=2))
        else:
            for r in hits:
                print(f"{r.fault_id} | {r.location} | {r.fault_type} | {r.coverage_status.value} | patterns={r.detected_by_patterns}")

    elif command == "pattern":
        browser = FaultBrowser(analyzer)
        faults = browser.get_pattern_detected_faults(getattr(args, "pattern_name", ""))
        if getattr(args, "format", "text") == "json":
            print(json.dumps([r.to_dict() for r in faults], indent=2))
        else:
            print(f"Pattern: {getattr(args, 'pattern_name')}")
            for r in faults:
                print(f"  {r.fault_id} | {r.location} | {r.fault_type}")

    elif command == "export":
        status = getattr(args, "status", "undetected")
        if status == "undetected":
            fault_ids = [r.fault_id for r in analyzer.get_undetected_faults()]
        elif status == "retry_needed":
            fault_ids = [r.fault_id for r in analyzer.fault_db.values() if r.coverage_status == FaultCoverageStatus.RETRY_NEEDED]
        else:
            fault_ids = list(analyzer.fault_db.keys())
        browser = FaultBrowser(analyzer)
        out_path = getattr(args, "output", "faults.txt")
        browser.export_fault_list_for_atpg(fault_ids, out_path)
        print(f"Exported {len(fault_ids)} fault IDs to {out_path}")


if __name__ == "__main__":
    _run_cli()
