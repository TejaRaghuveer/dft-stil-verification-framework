#!/usr/bin/env python3
"""
Pattern Compression and Optimization
------------------------------------

Implements several test-data compression techniques on top of the PatternDatabase:

- Vector merging (identical consecutive vectors → (vector, repeat_count))
- Bit-wise run-length encoding (RLE) inside a vector
- X-based compression (don't-care masking) hooks
- Waveform/procedure-based compression hooks for STIL
- Fault-aware compression (remove redundant patterns)

This module is intentionally tool-agnostic. It operates on:
- PatternRecord.vector_lines (raw scan/ATPG vectors as ASCII)
- PatternRecord.fault_list / fault_count (where available)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Iterable, List, Optional, Tuple, Any, Set

from .pattern_database import PatternDatabase, PatternRecord, PatternType


class CompressionLevel(str, Enum):
    NONE = "NONE"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    AGGRESSIVE = "AGGRESSIVE"


class CompressionMethod(str, Enum):
    VECTOR_MERGE = "VECTOR_MERGE"
    BITWISE_RLE = "BITWISE_RLE"
    X_BASED = "X_BASED"
    WAVEFORM = "WAVEFORM"
    PROCEDURE = "PROCEDURE"
    FAULT_AWARE = "FAULT_AWARE"


@dataclass
class PatternCompressionConfig:
    level: CompressionLevel = CompressionLevel.NONE
    methods: List[CompressionMethod] = field(default_factory=list)
    target_ratio_pct: float = 0.0  # e.g. 50.0 for 50% size reduction
    min_coverage_pct: float = 95.0
    time_budget_s: float = 0.0  # 0 = no explicit budget
    output_format: str = "STIL_COMPRESSED"

    def is_enabled(self, method: CompressionMethod) -> bool:
        return method in self.methods or self.level in {
            CompressionLevel.MEDIUM,
            CompressionLevel.HIGH,
            CompressionLevel.AGGRESSIVE,
        }


@dataclass
class VectorRun:
    value: str
    repeat: int


class PatternCompressor:
    """
    Performs pattern-level compression (in-memory) and returns compressed
    representations plus statistics. The original PatternDatabase is left intact.
    """

    def __init__(self, db: PatternDatabase, cfg: Optional[PatternCompressionConfig] = None) -> None:
        self.db = db
        self.cfg = cfg or PatternCompressionConfig()

    # ---------------- Vector-level compression ----------------

    @staticmethod
    def merge_identical_vectors(vectors: List[str]) -> List[VectorRun]:
        """Merge identical consecutive vectors into (value, repeat) runs."""
        if not vectors:
            return []
        runs: List[VectorRun] = []
        current = vectors[0]
        count = 1
        for v in vectors[1:]:
            if v == current:
                count += 1
            else:
                runs.append(VectorRun(value=current, repeat=count))
                current = v
                count = 1
        runs.append(VectorRun(value=current, repeat=count))
        return runs

    @staticmethod
    def rle_bits(vec: str) -> List[Tuple[str, int]]:
        """
        Bit-wise run-length encoding of a single vector string.
        Example: '0001110' -> [('0',3), ('1',3), ('0',1)]
        """
        if not vec:
            return []
        out: List[Tuple[str, int]] = []
        cur = vec[0]
        n = 1
        for c in vec[1:]:
            if c == cur:
                n += 1
            else:
                out.append((cur, n))
                cur = c
                n = 1
        out.append((cur, n))
        return out

    # ---------------- X-based compression hooks ----------------

    @staticmethod
    def apply_x_mask(vec: str, care_mask: Optional[List[bool]] = None) -> str:
        """
        Apply an X-mask to a vector: positions where care_mask[i] is False are set to 'X'.
        If care_mask is None, the vector is returned unchanged.
        """
        if care_mask is None or not vec:
            return vec
        out_chars: List[str] = []
        for i, c in enumerate(vec):
            if i < len(care_mask) and not care_mask[i]:
                out_chars.append("X")
            else:
                out_chars.append(c)
        return "".join(out_chars)

    # ---------------- Fault-aware compression ----------------

    def fault_aware_filter(
        self,
        unique_fault_patterns: Optional[Set[str]] = None,
    ) -> List[PatternRecord]:
        """
        Fault-aware compression: keep patterns that detect at least one unique fault.
        unique_fault_patterns: names of patterns that are "essential"
            (e.g., from FaultDistributionAnalyzer.essential_patterns()).
        All other patterns are considered candidates for removal.
        """
        essential = unique_fault_patterns or set()
        kept: List[PatternRecord] = []
        for p in self.db._patterns.values():
            if not p.fault_list:
                # if we know nothing about faults, keep conservatively
                kept.append(p)
            elif p.pattern_name in essential:
                kept.append(p)
            else:
                # candidate for removal; fault coverage must be checked by caller
                continue
        return kept

    # ---------------- High-level compression API ----------------

    def compress_vectors_for_pattern(self, rec: PatternRecord) -> Dict[str, Any]:
        """
        Return compressed representations for a single pattern:
            - 'merged_runs': vector-merging result
            - 'rle': bit-wise RLE per original vector
        Does not mutate the PatternRecord.
        """
        vectors = rec.vector_lines or []
        merged = self.merge_identical_vectors(vectors)
        rle_per_vec = [self.rle_bits(v) for v in vectors]
        orig_bits = sum(len(v) for v in vectors)
        merged_bits_equiv = sum(len(r.value) * r.repeat for r in merged)
        return {
            "pattern_name": rec.pattern_name,
            "original_vector_count": len(vectors),
            "merged_run_count": len(merged),
            "original_bits": orig_bits,
            "merged_bits_equiv": merged_bits_equiv,
            "merged_runs": merged,
            "rle_per_vector": rle_per_vec,
        }

    def compress_all(self) -> Dict[str, Any]:
        """
        Run configured compression methods across all patterns and return summary.
        The database itself is not changed; this is analysis-only by default.
        """
        per_pattern: List[Dict[str, Any]] = []
        total_bits = 0
        total_merged_bits = 0
        for rec in self.db._patterns.values():
            info = self.compress_vectors_for_pattern(rec)
            per_pattern.append(info)
            total_bits += info["original_bits"]
            total_merged_bits += info["merged_bits_equiv"]
        ratio = 100.0 * (1.0 - (total_merged_bits / total_bits)) if total_bits else 0.0
        return {
            "total_original_bits": total_bits,
            "total_merged_bits_equiv": total_merged_bits,
            "vector_merge_savings_pct": round(ratio, 2),
            "per_pattern": per_pattern,
        }


class CompressionAnalyzer:
    """
    Analyze compression opportunities and effectiveness.
    """

    def __init__(self, db: PatternDatabase) -> None:
        self.db = db

    def estimate_vector_merge_savings(self) -> Dict[str, Any]:
        comp = PatternCompressor(self.db)
        res = comp.compress_all()
        return {
            "original_bits": res["total_original_bits"],
            "merged_bits_equiv": res["total_merged_bits_equiv"],
            "savings_pct": res["vector_merge_savings_pct"],
        }

    def identify_heavy_patterns(self, top_n: int = 20) -> List[Dict[str, Any]]:
        """
        Identify patterns with the largest bit volume (size_bits * or vector length).
        These are prime candidates for waveform/procedure compression.
        """
        patterns = sorted(self.db._patterns.values(), key=lambda p: p.size_bits, reverse=True)
        out: List[Dict[str, Any]] = []
        for p in patterns[:top_n]:
            out.append(
                {
                    "pattern_name": p.pattern_name,
                    "size_bits": p.size_bits,
                    "fault_count": p.fault_count,
                }
            )
        return out

    def report_compression_opportunities(self) -> Dict[str, Any]:
        """
        High-level report on where compression is likely to help the most.
        """
        vm = self.estimate_vector_merge_savings()
        heavy = self.identify_heavy_patterns()
        return {
            "vector_merge": vm,
            "heavy_patterns": heavy,
        }


# ---------------------------------------------------------------------------
# Documentation: compression methods and IEEE 1450 notes
# ---------------------------------------------------------------------------

COMPRESSION_NOTES = """
Pattern Compression Methods
---------------------------

1) Vector merging
   - Goal: reduce repeated, identical vectors into (vector, repeat) runs.
   - Implementation: PatternCompressor.merge_identical_vectors().
   - Typical use: long sequences of identical scan-shift vectors or idle cycles.

2) Bit-wise compression (RLE)
   - Goal: compress long runs of identical bits within each vector.
   - Implementation: PatternCompressor.rle_bits().
   - Representation: a list of (value, run_length), e.g. '0001110' → [(0,3),(1,3),(0,1)].
   - This is especially effective for wide scan chains where many bits are 0 or X.

3) X-based compression (don't-care masking)
   - Goal: replace non-critical bits with 'X' so ATE can skip driving them or compress them.
   - Implementation: PatternCompressor.apply_x_mask() with a care_mask per vector.
   - Source of mask: ATPG tools usually output care/don't-care information; this module
     assumes a boolean care_mask[] is available from upstream tools.
   - Effect: reduces switching activity, power, and in some flows enables pattern compaction.

4) Waveform compression
   - Goal: describe patterns as repeated applications of a basic waveform instead of
     enumerating every vector.
   - In STIL (IEEE 1450), WaveformTable + procedurally defined patterns can express
     repeated structures more compactly than raw V-lines.
   - This module provides analysis hooks (CompressionAnalyzer.identify_heavy_patterns());
     the actual ATE-format waveform compression is typically vendor-specific.

5) Procedure-based compression
   - Goal: factor out common sequences (e.g. "Shift and Capture") into reusable procedures.
   - In STIL, Procedures {} plus PatternExec / Call constructs can reference those procedures
     rather than inlining all vectors.
   - Concept: define a procedure that performs "Scan_Shift + Capture", then in patterns
     simply call that procedure N times.

6) Fault-aware compression
   - Goal: remove patterns that do not contribute unique fault coverage.
   - Integration: use FaultDistributionAnalyzer.essential_patterns() from the
     fault_coverage module to identify patterns that detect unique faults; use
     PatternCompressor.fault_aware_filter() to keep only essential patterns.
   - Coverage must be checked to ensure overall fault coverage remains ≥ target
     (e.g. 95%).

IEEE 1450 (STIL) Compression Notes
----------------------------------

- STIL supports higher-level constructs:
  * Timing/WaveformTable for clock and signal shape reuse
  * Procedures {} for named sequences of operations
  * PatternExec and PatternBurst for grouping and repetition

- Many ATE vendors define proprietary STIL extensions or pragmas for:
  * vector-repeat notations
  * scan-compression macros
  * power-aware pattern execution

- This module keeps the compression logic at the vector/PatternRecord level so it can
  be mapped to any specific STIL dialect:
  * Vector merging/RLE → vector-repeat or compressed pattern sections
  * X-based compression → use of 'X' in V { ... } vectors with care bits
  * Procedure-based compression → Procedures + PatternExec calls

"""

