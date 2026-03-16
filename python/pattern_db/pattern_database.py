"""
Pattern Database and Test Suite Management
-----------------------------------------

This module provides a pattern database and suite builder for DFT/ATPG
patterns. It is intentionally tool-agnostic and can be populated from:

- SystemVerilog `atpg_pattern_t` exports
- STIL files (via `stil_validator` / STIL→ATPG converters)
- Native ATPG tool exports

The goals are:
- Centralized pattern metadata storage
- Fast querying and filtering
- Intelligent suite construction (smoke, minimal, fault-targeted, etc.)
"""

from __future__ import annotations

import dataclasses
import json
import math
import os
import random
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Iterable, Tuple, Any, Set


# ---------------------------------------------------------------------------
# Core enums and data structures
# ---------------------------------------------------------------------------


class PatternType(str, Enum):
    STUCK_AT = "STUCK_AT"
    TRANSITION_DELAY = "TRANSITION_DELAY"
    PATH_DELAY = "PATH_DELAY"
    CUSTOM = "CUSTOM"


@dataclass
class PatternRecord:
    """Single pattern metadata entry in the pattern database."""

    pattern_id: int
    pattern_name: str
    pattern_type: PatternType
    # Optional: raw scan/ATPG vector lines for STIL generation and comparisons.
    # This is intentionally tool-agnostic (e.g. vector-per-line ASCII).
    vector_lines: List[str] = field(default_factory=list)
    fault_list: List[str] = field(default_factory=list)
    fault_count: int = 0
    coverage_contribution: float = 0.0  # percentage points
    execution_time_ns: float = 0.0
    size_bits: int = 0
    checksum: str = ""

    # Metadata
    source_tool: str = ""
    source_version: str = ""
    generation_date: str = ""
    dut_version: str = ""
    design_revision: str = ""

    # Cached/derived metrics
    efficiency_score: float = 0.0  # faults / size_bits

    def compute_efficiency(self) -> None:
        if self.size_bits > 0:
            self.efficiency_score = float(self.fault_count) / float(self.size_bits)
        else:
            self.efficiency_score = 0.0


@dataclass
class PatternDatabaseConfig:
    """Simple configuration for the database backend."""

    storage_path: str = "pattern_db.json"
    use_sqlite: bool = False  # JSON-based store by default


class TestSelectionStrategy(str, Enum):
    MINIMAL = "MINIMAL"
    COMPREHENSIVE = "COMPREHENSIVE"
    SMOKE = "SMOKE"
    FAULT_TARGETED = "FAULT_TARGETED"
    RANDOM_SAMPLE = "RANDOM_SAMPLE"
    COVERAGE_LADDER = "COVERAGE_LADDER"


@dataclass
class TestSuiteConfiguration:
    pattern_source_file: str = ""
    strategy: TestSelectionStrategy = TestSelectionStrategy.COMPREHENSIVE
    target_coverage: float = 100.0
    max_pattern_count: Optional[int] = None
    pattern_type_filter: Optional[PatternType] = None
    execution_mode_randomized: bool = False
    faults_of_interest: List[str] = field(default_factory=list)
    random_sample_fraction: float = 0.1  # for RANDOM_SAMPLE

    def save_suite_to_file(self, path: str, pattern_ids: List[int]) -> None:
        data = {
            "pattern_source_file": self.pattern_source_file,
            "strategy": self.strategy.value,
            "target_coverage": self.target_coverage,
            "max_pattern_count": self.max_pattern_count,
            "pattern_type_filter": self.pattern_type_filter.value if self.pattern_type_filter else None,
            "execution_mode_randomized": self.execution_mode_randomized,
            "faults_of_interest": self.faults_of_interest,
            "random_sample_fraction": self.random_sample_fraction,
            "pattern_ids": pattern_ids,
        }
        with open(path, "w") as f:
            json.dump(data, f, indent=2)


# ---------------------------------------------------------------------------
# Pattern Database (JSON-based in-memory with on-disk persistence)
# ---------------------------------------------------------------------------


class PatternDatabase:
    """
    JSON-based pattern database.

    Internal representation:
        id -> PatternRecord

    Stored on disk as:
        {
          "patterns": [ { ..pattern fields.. }, ... ],
          "metadata": { "source": ..., "dut_version": ..., ... }
        }
    """

    def __init__(self, config: Optional[PatternDatabaseConfig] = None) -> None:
        self.config = config or PatternDatabaseConfig()
        self._patterns: Dict[int, PatternRecord] = {}
        self._next_id: int = 1
        self.metadata: Dict[str, Any] = {}

    # -------------------- Persistence --------------------

    def load_from_file(self, path: Optional[str] = None) -> None:
        path = path or self.config.storage_path
        if not os.path.exists(path):
            return
        with open(path, "r") as f:
            data = json.load(f)
        self._patterns.clear()
        for p in data.get("patterns", []):
            rec = PatternRecord(
                pattern_id=p["pattern_id"],
                pattern_name=p["pattern_name"],
                pattern_type=PatternType(p["pattern_type"]),
                vector_lines=p.get("vector_lines", []),
                fault_list=p.get("fault_list", []),
                fault_count=p.get("fault_count", 0),
                coverage_contribution=p.get("coverage_contribution", 0.0),
                execution_time_ns=p.get("execution_time_ns", 0.0),
                size_bits=p.get("size_bits", 0),
                checksum=p.get("checksum", ""),
                source_tool=p.get("source_tool", ""),
                source_version=p.get("source_version", ""),
                generation_date=p.get("generation_date", ""),
                dut_version=p.get("dut_version", ""),
                design_revision=p.get("design_revision", ""),
                efficiency_score=p.get("efficiency_score", 0.0),
            )
            self._patterns[rec.pattern_id] = rec
        self._next_id = max(self._patterns.keys(), default=0) + 1
        self.metadata = data.get("metadata", {})

    def save_to_file(self, path: Optional[str] = None) -> None:
        path = path or self.config.storage_path
        payload = {
            "patterns": [dataclasses.asdict(p) for p in self._patterns.values()],
            "metadata": self.metadata,
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)

    # -------------------- Mutation --------------------

    def add_pattern(self, rec: PatternRecord) -> int:
        if rec.pattern_id == 0:
            rec.pattern_id = self._next_id
            self._next_id += 1
        rec.compute_efficiency()
        self._patterns[rec.pattern_id] = rec
        return rec.pattern_id

    def load_patterns_from_file(self, filename: str) -> None:
        """
        Placeholder for importing patterns from a textual ATPG file or
        STIL-derived export. The expectation is that an external parser will
        construct PatternRecord instances and call add_pattern().
        """
        raise NotImplementedError("Integrate with ATPG/STIL parser to populate PatternDatabase")

    # -------------------- Queries --------------------

    def get_pattern_count(self) -> int:
        return len(self._patterns)

    def get_coverage_stats(self) -> Dict[str, Any]:
        total_cov = sum(p.coverage_contribution for p in self._patterns.values())
        total_bits = sum(p.size_bits for p in self._patterns.values())
        total_faults = sum(p.fault_count for p in self._patterns.values())
        return {
            "patterns": self.get_pattern_count(),
            "total_coverage_contribution": total_cov,
            "total_bits": total_bits,
            "total_faults": total_faults,
        }

    def query_patterns_by_type(self, ptype: PatternType) -> List[PatternRecord]:
        return [p for p in self._patterns.values() if p.pattern_type == ptype]

    def query_patterns_by_fault(self, fault_name: str) -> List[PatternRecord]:
        return [p for p in self._patterns.values() if fault_name in p.fault_list]

    def query_patterns_by_coverage_range(self, min_cov: float, max_cov: float) -> List[PatternRecord]:
        return [
            p
            for p in self._patterns.values()
            if min_cov <= p.coverage_contribution <= max_cov
        ]

    def export_pattern_set(self, recs: Iterable[PatternRecord], path: str) -> None:
        """
        Export a subset of patterns to a JSON file that can be consumed by
        other tools (or converted back into ATPG/ STIL patterns).
        """
        payload = {
            "patterns": [dataclasses.asdict(p) for p in recs],
            "metadata": self.metadata,
        }
        with open(path, "w") as f:
            json.dump(payload, f, indent=2)


# ---------------------------------------------------------------------------
# Test Suite Builder and Optimizer
# ---------------------------------------------------------------------------


class TestSuiteBuilder:
    """Constructs suites based on a PatternDatabase and configuration."""

    def __init__(self, db: PatternDatabase) -> None:
        self.db = db

    def build_suite(self, cfg: TestSuiteConfiguration) -> List[PatternRecord]:
        all_patterns = list(self.db._patterns.values())
        if cfg.pattern_type_filter is not None:
            all_patterns = [p for p in all_patterns if p.pattern_type == cfg.pattern_type_filter]

        if cfg.strategy == TestSelectionStrategy.COMPREHENSIVE:
            suite = all_patterns
        elif cfg.strategy == TestSelectionStrategy.SMOKE:
            suite = self._build_smoke_suite(all_patterns, target_count=cfg.max_pattern_count or 30)
        elif cfg.strategy == TestSelectionStrategy.MINIMAL:
            suite = self._build_minimal_suite(all_patterns, cfg.target_coverage, cfg.max_pattern_count)
        elif cfg.strategy == TestSelectionStrategy.FAULT_TARGETED:
            suite = self._build_fault_targeted_suite(all_patterns, cfg.faults_of_interest)
        elif cfg.strategy == TestSelectionStrategy.RANDOM_SAMPLE:
            suite = self._build_random_sample_suite(all_patterns, cfg.random_sample_fraction, cfg.max_pattern_count)
        elif cfg.strategy == TestSelectionStrategy.COVERAGE_LADDER:
            suite = self._build_coverage_ladder_suite(all_patterns)
        else:
            suite = all_patterns

        if cfg.execution_mode_randomized:
            random.shuffle(suite)

        if cfg.max_pattern_count is not None:
            suite = suite[: cfg.max_pattern_count]

        return suite

    def _build_smoke_suite(self, patterns: List[PatternRecord], target_count: int) -> List[PatternRecord]:
        """
        Smoke: 20-30 short, representative patterns.
        - Prefer high-efficiency patterns.
        - Bias towards shorter ones (lower execution time).
        """
        patterns = [p for p in patterns if p.size_bits > 0]
        for p in patterns:
            p.compute_efficiency()
        patterns.sort(key=lambda p: (-p.efficiency_score, p.size_bits))
        return patterns[:target_count]

    def _build_minimal_suite(
        self,
        patterns: List[PatternRecord],
        target_coverage: float,
        max_patterns: Optional[int],
    ) -> List[PatternRecord]:
        """
        Greedy approximation:
        - Sort by coverage_contribution descending.
        - Keep adding patterns until target_coverage reached or max_patterns hit.
        """
        patterns = sorted(patterns, key=lambda p: p.coverage_contribution, reverse=True)
        suite: List[PatternRecord] = []
        cov = 0.0
        for p in patterns:
            if max_patterns is not None and len(suite) >= max_patterns:
                break
            suite.append(p)
            cov += p.coverage_contribution
            if cov >= target_coverage:
                break
        return suite

    def _build_fault_targeted_suite(
        self,
        patterns: List[PatternRecord],
        faults_of_interest: List[str],
    ) -> List[PatternRecord]:
        if not faults_of_interest:
            return []
        fault_set: Set[str] = set(faults_of_interest)
        suite: List[PatternRecord] = []
        covered: Set[str] = set()
        # Greedy set cover: pick the pattern that covers the most remaining faults.
        remaining = patterns[:]
        while fault_set - covered:
            best = None
            best_gain = 0
            for p in remaining:
                gain = len(set(p.fault_list) & (fault_set - covered))
                if gain > best_gain:
                    best_gain = gain
                    best = p
            if best is None or best_gain == 0:
                break
            suite.append(best)
            covered |= set(best.fault_list)
            remaining.remove(best)
        return suite

    def _build_random_sample_suite(
        self,
        patterns: List[PatternRecord],
        fraction: float,
        max_patterns: Optional[int],
    ) -> List[PatternRecord]:
        if fraction <= 0:
            return []
        n = max(1, int(math.ceil(len(patterns) * fraction)))
        if max_patterns is not None:
            n = min(n, max_patterns)
        return random.sample(patterns, min(n, len(patterns)))

    def _build_coverage_ladder_suite(self, patterns: List[PatternRecord]) -> List[PatternRecord]:
        """
        Build a ladder suite: subsets that achieve ~50%, 75%, 90%, 95%, 98%, 100%.
        Implementation: same greedy approach as MINIMAL but record the pattern
        indices at each ladder rung.
        """
        rungs = [50.0, 75.0, 90.0, 95.0, 98.0, 100.0]
        patterns = sorted(patterns, key=lambda p: p.coverage_contribution, reverse=True)
        suite: List[PatternRecord] = []
        cov = 0.0
        for p in patterns:
            suite.append(p)
            cov += p.coverage_contribution
            if cov >= rungs[0]:
                rungs.pop(0)
                if not rungs:
                    break
        return suite


# ---------------------------------------------------------------------------
# Pattern Analyzer and Optimizer
# ---------------------------------------------------------------------------


class PatternAnalyzer:
    """Compute statistics and flag redundant or outlier patterns."""

    def __init__(self, db: PatternDatabase) -> None:
        self.db = db

    def analyze_distribution(self) -> Dict[str, Any]:
        by_type: Dict[str, int] = {}
        for p in self.db._patterns.values():
            by_type[p.pattern_type.value] = by_type.get(p.pattern_type.value, 0) + 1
        return {
            "by_type": by_type,
            "coverage_stats": self.db.get_coverage_stats(),
        }

    def find_redundant_patterns(self) -> List[Tuple[int, int]]:
        """
        Very simple redundancy heuristic:
        - Two patterns are considered redundant if they have identical fault_list
          and pattern_type.
        Returns list of (kept_id, redundant_id).
        """
        seen: Dict[Tuple[str, Tuple[str, ...]], int] = {}
        redundant: List[Tuple[int, int]] = []
        for p in self.db._patterns.values():
            key = (p.pattern_type.value, tuple(sorted(p.fault_list)))
            if key in seen:
                redundant.append((seen[key], p.pattern_id))
            else:
                seen[key] = p.pattern_id
        return redundant

    def find_outliers(self, length_threshold_bits: int) -> List[PatternRecord]:
        return [p for p in self.db._patterns.values() if p.size_bits >= length_threshold_bits]


class TestSuiteOptimizer:
    """Remove redundant patterns and reorder for better coverage convergence."""

    def __init__(self, db: PatternDatabase) -> None:
        self.db = db

    def optimize_suite(self, suite: List[PatternRecord]) -> List[PatternRecord]:
        # Remove exact-redundant patterns (same faults, type) from this suite.
        analyzer = PatternAnalyzer(self.db)
        redundant_pairs = analyzer.find_redundant_patterns()
        redundant_ids = {r for _, r in redundant_pairs}
        filtered = [p for p in suite if p.pattern_id not in redundant_ids]
        # Reorder: high coverage first, then by efficiency.
        for p in filtered:
            p.compute_efficiency()
        filtered.sort(key=lambda p: (-p.coverage_contribution, -p.efficiency_score))
        return filtered


# ---------------------------------------------------------------------------
# Execution Scheduler
# ---------------------------------------------------------------------------


class ExecutionScheduler:
    """
    Estimate execution time and propose an execution manifest.

    Time estimation formula:
        time_ns ≈ size_bits * TCK_period_ns
    where TCK_period_ns is the JTAG clock period used in the environment.
    """

    def __init__(self, tck_period_ns: float = 100.0) -> None:
        self.tck_period_ns = tck_period_ns

    def estimate_pattern_time_ns(self, p: PatternRecord) -> float:
        if p.execution_time_ns > 0:
            return p.execution_time_ns
        return p.size_bits * self.tck_period_ns

    def build_execution_manifest(
        self,
        suite: List[PatternRecord],
        num_jobs: int = 1,
    ) -> Dict[str, Any]:
        """
        Allocate patterns across N jobs and estimate total runtime.
        Returns:
            {
              "jobs": [ { "patterns": [ids...], "est_time_ns": ... }, ... ],
              "total_est_time_ns": ...,
            }
        """
        jobs: List[Dict[str, Any]] = [{"patterns": [], "est_time_ns": 0.0} for _ in range(num_jobs)]
        for p in suite:
            t = self.estimate_pattern_time_ns(p)
            # Greedy load balancing: assign to job with smallest current time.
            j = min(range(num_jobs), key=lambda idx: jobs[idx]["est_time_ns"])
            jobs[j]["patterns"].append(p.pattern_id)
            jobs[j]["est_time_ns"] += t
        total_est = max(job["est_time_ns"] for job in jobs) if jobs else 0.0
        return {"jobs": jobs, "total_est_time_ns": total_est}


# ---------------------------------------------------------------------------
# Documentation: test suite design and time estimation
# ---------------------------------------------------------------------------

TEST_SUITE_DESIGN_NOTES = """
Test Suite Design Principles
----------------------------

1. Smoke tests
   - Purpose: very fast, shallow sanity checks.
   - Size: 20–30 patterns.
   - Selection: high-efficiency patterns (fault_count / size_bits) and
     representative across pattern types (STUCK_AT, TRANSITION_DELAY, etc.).
   - Target use: pre-checkin, quick CI, basic lab bring-up.

2. Minimal coverage suites
   - Purpose: achieve a specified coverage target (e.g. 95%) with as few
     patterns as possible.
   - Size: depends on pattern set; typically a few hundred patterns.
   - Selection: greedy by coverage_contribution, optionally pruned by
     redundancy (identical fault sets).

3. Full regression
   - Purpose: maximum confidence before tapeout or major milestones.
   - Size: all patterns in the database.
   - Selection: COMPREHENSIVE strategy; may be split across many jobs using
     the ExecutionScheduler.

4. Fault-targeted suites
   - Purpose: focus on specific fault lists (new faults, ECO deltas, or
     coverage holes).
   - Size: controlled by the number of faults of interest and redundancy.
   - Selection: greedy set-cover over fault_list.

Execution Time Estimation
-------------------------

Given a JTAG (or scan) clock period TCK_period_ns and pattern length L bits,
the approximate execution time per pattern is:

    t_pattern_ns ≈ L * TCK_period_ns

Ignoring overhead, a suite of N patterns each of length L_i bits has total
time:

    T_total_ns ≈ Σ_i (L_i * TCK_period_ns)

In practice, additional factors may add a constant overhead per pattern:
reset sequences, instruction loads, functional capture time, etc. These are
captured in PatternRecord.execution_time_ns when available; otherwise the
simple formula above is used.
"""

