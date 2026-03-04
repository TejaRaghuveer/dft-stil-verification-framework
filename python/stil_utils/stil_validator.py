"""
STIL Validator and Parser
-------------------------

High-level goals:
- Validate generated STIL files against the IEEE 1450 standard (syntax + basic semantics).
- Provide a structured parser and accessors so STIL data can be consumed by other tools.
- Enable portability by converting between STIL and simpler ATPG text formats.

NOTE: This implementation focuses on a pragmatic subset of IEEE 1450:
- Required top-level sections: Signals, SignalGroups, Timing/WaveformTable, PatternExec, Patterns.
- Basic signal properties (name, direction).
- WaveformTable structure (names, period, waveform entries).
- Pattern and vector syntax (V { ... };).
It is designed to catch real-world errors in generated STIL, not to be a full language
reference implementation.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any


# ---------------------------------------------------------------------------
# Core data types
# ---------------------------------------------------------------------------


class Severity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"


@dataclass
class ValidationMessage:
    severity: Severity
    code: str
    message: str
    line: Optional[int] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "severity": self.severity.value,
            "code": self.code,
            "message": self.message,
            "line": self.line,
        }


@dataclass
class ValidationResult:
    ok: bool
    messages: List[ValidationMessage] = field(default_factory=list)

    def add(self, msg: ValidationMessage) -> None:
        self.messages.append(msg)
        if msg.severity == Severity.ERROR:
            self.ok = False

    @property
    def errors(self) -> List[ValidationMessage]:
        return [m for m in self.messages if m.severity == Severity.ERROR]

    @property
    def warnings(self) -> List[ValidationMessage]:
        return [m for m in self.messages if m.severity == Severity.WARNING]

    @property
    def infos(self) -> List[ValidationMessage]:
        return [m for m in self.messages if m.severity == Severity.INFO]


@dataclass
class STILSignal:
    name: str
    direction: str  # In, Out, InOut, etc.
    attributes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class STILWaveformTable:
    name: str
    period_ns: Optional[float] = None
    drive_waveforms: Dict[str, str] = field(default_factory=dict)
    compare_waveforms: Dict[str, str] = field(default_factory=dict)


@dataclass
class STILPattern:
    name: str
    wft: Optional[str] = None
    vectors: List[str] = field(default_factory=list)


@dataclass
class STILProcedure:
    name: str
    body_lines: List[str] = field(default_factory=list)


@dataclass
class STILModel:
    path: str
    signals: Dict[str, STILSignal] = field(default_factory=dict)
    waveform_tables: Dict[str, STILWaveformTable] = field(default_factory=dict)
    patterns: Dict[str, STILPattern] = field(default_factory=dict)
    procedures: Dict[str, STILProcedure] = field(default_factory=dict)
    pattern_exec_blocks: List[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# STIL Parser (lightweight, line-oriented)
# ---------------------------------------------------------------------------


class STILParser:
    """
    Minimal STIL parser that extracts signals, waveform tables, patterns, and
    procedures into a STILModel. It is deliberately conservative; anything it
    does not recognize is left as raw text for the validator to inspect.
    """

    _cache: Dict[str, Tuple[float, STILModel]] = {}

    def parse_file(self, path: str, use_cache: bool = True) -> STILModel:
        abspath = os.path.abspath(path)
        mtime = os.path.getmtime(abspath)
        if use_cache and abspath in self._cache:
            cached_mtime, model = self._cache[abspath]
            if cached_mtime == mtime:
                return model

        with open(abspath, "r") as f:
            lines = f.readlines()

        model = STILModel(path=abspath)
        self._parse_lines(lines, model)
        if use_cache:
            self._cache[abspath] = (mtime, model)
        return model

    # Section patterns
    _signals_re = re.compile(r"^\s*Signals\s*{", re.IGNORECASE)
    _pattern_re = re.compile(r"^\s*Pattern\s+\"?([\w.$]+)\"?\s*{", re.IGNORECASE)
    _wft_re = re.compile(r"^\s*WaveformTable\s+\"?([\w.$]+)\"?\s*{", re.IGNORECASE)
    _timing_re = re.compile(r"^\s*Timing\s*{", re.IGNORECASE)
    _proc_re = re.compile(r"^\s*Procedure\s+\"?([\w.$]+)\"?\s*{", re.IGNORECASE)
    _pattern_exec_re = re.compile(r"^\s*PatternExec\b", re.IGNORECASE)

    def _parse_lines(self, lines: List[str], model: STILModel) -> None:
        i = 0
        n = len(lines)
        while i < n:
            line = lines[i]
            if self._signals_re.match(line):
                i = self._parse_signals_block(lines, i, model)
            elif self._timing_re.match(line):
                i = self._parse_timing_block(lines, i, model)
            elif self._wft_re.match(line):
                # Standalone WaveformTable (rare – usually inside Timing)
                i = self._parse_waveform_table_block(lines, i, model)
            elif self._pattern_re.match(line):
                i = self._parse_pattern_block(lines, i, model)
            elif self._proc_re.match(line):
                i = self._parse_procedure_block(lines, i, model)
            elif self._pattern_exec_re.match(line):
                i = self._parse_pattern_exec_block(lines, i, model)
            else:
                i += 1

    def _parse_block(self, lines: List[str], start_idx: int) -> Tuple[List[str], int]:
        """Return block lines and index past closing '}'."""
        block_lines = [lines[start_idx]]
        depth = lines[start_idx].count("{") - lines[start_idx].count("}")
        i = start_idx + 1
        while i < len(lines) and depth > 0:
            block_lines.append(lines[i])
            depth += lines[i].count("{") - lines[i].count("}")
            i += 1
        return block_lines, i

    def _parse_signals_block(self, lines: List[str], start_idx: int, model: STILModel) -> int:
        block, idx = self._parse_block(lines, start_idx)
        for line in block[1:]:
            m = re.match(r'\s*"?([\w.$\[\]]+)"?\s+(\w+)\s+Digital', line)
            if m:
                name, direction = m.group(1), m.group(2)
                model.signals[name] = STILSignal(name=name, direction=direction)
        return idx

    def _parse_timing_block(self, lines: List[str], start_idx: int, model: STILModel) -> int:
        block, idx = self._parse_block(lines, start_idx)
        # Look for nested WaveformTable definitions
        for j, line in enumerate(block):
            m = self._wft_re.match(line)
            if m:
                sub_block, _ = self._parse_block(block, j)
                self._parse_waveform_table_block(sub_block, 0, model, in_sub_block=True)
        return idx

    def _parse_waveform_table_block(
        self, lines: List[str], start_idx: int, model: STILModel, in_sub_block: bool = False
    ) -> int:
        block, idx = self._parse_block(lines, start_idx)
        header = block[0]
        m = self._wft_re.match(header)
        if not m:
            return idx if not in_sub_block else len(lines)
        name = m.group(1)
        wft = STILWaveformTable(name=name)
        for line in block[1:]:
            m_per = re.search(r"Period\s+([\d.]+)\s*ns", line, re.IGNORECASE)
            if m_per:
                try:
                    wft.period_ns = float(m_per.group(1))
                except ValueError:
                    pass
            if "Waveforms" in line:
                # Very lightweight parsing of named drive/compare entries
                # e.g. Waveforms { "drive" { ... } "compare" { ... } }
                for wf_name in re.findall(r'"([\w.$]+)"', line):
                    if "drive" in wf_name.lower():
                        wft.drive_waveforms[wf_name] = line.strip()
                    elif "compare" in wf_name.lower():
                        wft.compare_waveforms[wf_name] = line.strip()
        model.waveform_tables[name] = wft
        return idx if not in_sub_block else len(lines)

    def _parse_pattern_block(self, lines: List[str], start_idx: int, model: STILModel) -> int:
        header = lines[start_idx]
        m = self._pattern_re.match(header)
        if not m:
            return start_idx + 1
        name = m.group(1)
        block, idx = self._parse_block(lines, start_idx)
        pat = STILPattern(name=name)
        for line in block[1:]:
            m_wft = re.search(r'\bWFT\s+"?([\w.$]+)"?', line)
            if m_wft:
                pat.wft = m_wft.group(1)
            if re.search(r"\bV\s*{", line):
                # Capture vector body inside V { ... };
                vec = line.strip()
                # If vector spills across lines, keep raw form; validator will
                # enforce width consistency later.
                pat.vectors.append(vec)
        model.patterns[name] = pat
        return idx

    def _parse_procedure_block(self, lines: List[str], start_idx: int, model: STILModel) -> int:
        header = lines[start_idx]
        m = self._proc_re.match(header)
        if not m:
            return start_idx + 1
        name = m.group(1)
        block, idx = self._parse_block(lines, start_idx)
        proc = STILProcedure(name=name, body_lines=[l.rstrip("\n") for l in block[1:-1]])
        model.procedures[name] = proc
        return idx

    def _parse_pattern_exec_block(self, lines: List[str], start_idx: int, model: STILModel) -> int:
        block, idx = self._parse_block(lines, start_idx)
        model.pattern_exec_blocks.append("".join(block))
        return idx

    # ------------------------------------------------------------------
    # Data accessors (used directly or via STILDataAccessor)
    # ------------------------------------------------------------------

    @staticmethod
    def get_signal_list(model: STILModel) -> List[str]:
        return list(model.signals.keys())

    @staticmethod
    def get_signal_type(model: STILModel, signal_name: str) -> Optional[str]:
        sig = model.signals.get(signal_name)
        return sig.direction if sig else None

    @staticmethod
    def get_pattern_vector(model: STILModel, pattern_name: str, index: int) -> Optional[str]:
        pat = model.patterns.get(pattern_name)
        if pat is None or index < 0 or index >= len(pat.vectors):
            return None
        return pat.vectors[index]


# ---------------------------------------------------------------------------
# STIL Validator
# ---------------------------------------------------------------------------


class STILFileValidator:
    """
    Performs syntax and basic semantic checks on a STILModel corresponding to
    a STIL file.
    """

    def __init__(self, strict: bool = True) -> None:
        self.strict = strict

    def validate_stil_file(self, path: str) -> ValidationResult:
        parser = STILParser()
        model = parser.parse_file(path)
        result = ValidationResult(ok=True)

        # Existence of required sections
        self._check_required_sections(model, result)

        # Signal definitions
        self._check_signals(model, result)

        # Waveform tables
        self._check_waveform_tables(model, result)

        # Patterns and vectors
        self._check_patterns(path, model, result)

        # Procedures and pattern exec blocks (lightweight checks)
        self._check_procedures(model, result)
        self._check_pattern_exec(model, result)

        return result

    def _check_required_sections(self, model: STILModel, result: ValidationResult) -> None:
        if not model.signals:
            result.add(ValidationMessage(Severity.ERROR, "STIL_NO_SIGNALS", "No Signals section found"))
        if not model.waveform_tables:
            result.add(ValidationMessage(Severity.ERROR, "STIL_NO_WFT", "No WaveformTable found in Timing section"))
        if not model.patterns:
            result.add(ValidationMessage(Severity.ERROR, "STIL_NO_PATTERNS", "No Patterns section found"))
        if not model.pattern_exec_blocks:
            result.add(ValidationMessage(Severity.WARNING, "STIL_NO_PATTERNEXEC", "No PatternExec block found"))

    def _check_signals(self, model: STILModel, result: ValidationResult) -> None:
        for name, sig in model.signals.items():
            if not re.match(r"^[A-Za-z_][\w.$\[\]]*$", name):
                result.add(
                    ValidationMessage(
                        Severity.ERROR,
                        "STIL_BAD_SIGNAL_NAME",
                        f"Invalid signal name '{name}'",
                    )
                )
            if sig.direction not in {"In", "Out", "InOut", "Clock"}:
                result.add(
                    ValidationMessage(
                        Severity.WARNING,
                        "STIL_UNKNOWN_DIR",
                        f"Signal '{name}' has non-standard direction '{sig.direction}'",
                    )
                )

    def _check_waveform_tables(self, model: STILModel, result: ValidationResult) -> None:
        for name, wft in model.waveform_tables.items():
            if wft.period_ns is None:
                result.add(
                    ValidationMessage(
                        Severity.ERROR,
                        "STIL_WFT_NO_PERIOD",
                        f"WaveformTable '{name}' missing Period specification",
                    )
                )
            if not wft.drive_waveforms:
                result.add(
                    ValidationMessage(
                        Severity.WARNING,
                        "STIL_WFT_NO_DRIVE",
                        f"WaveformTable '{name}' has no drive waveforms defined",
                    )
                )
            if not wft.compare_waveforms:
                result.add(
                    ValidationMessage(
                        Severity.WARNING,
                        "STIL_WFT_NO_COMPARE",
                        f"WaveformTable '{name}' has no compare waveforms defined",
                    )
                )

    def _check_patterns(self, path: str, model: STILModel, result: ValidationResult) -> None:
        # Load raw lines for line-number reporting
        try:
            with open(path, "r") as f:
                lines = f.readlines()
        except OSError:
            lines = []

        seen_names = set()
        for pat_name, pat in model.patterns.items():
            if pat_name in seen_names:
                result.add(
                    ValidationMessage(
                        Severity.ERROR,
                        "STIL_DUP_PATTERN",
                        f"Duplicate pattern name '{pat_name}'",
                    )
                )
            seen_names.add(pat_name)
            if not pat.vectors:
                result.add(
                    ValidationMessage(
                        Severity.WARNING,
                        "STIL_EMPTY_PATTERN",
                        f"Pattern '{pat_name}' has no vectors",
                    )
                )
            # Vector width consistency: check that all V { ... } lines have the
            # same number of tokens.
            expected_width: Optional[int] = None
            for v in pat.vectors:
                m = re.search(r"V\s*{([^}]*)}", v)
                if not m:
                    continue
                body = m.group(1).strip()
                tokens = body.split()
                width = len(tokens)
                if expected_width is None:
                    expected_width = width
                elif width != expected_width:
                    # Attempt to find line number for this vector
                    line_no = None
                    if lines:
                        for idx, line in enumerate(lines, start=1):
                            if v.strip() in line:
                                line_no = idx
                                break
                    result.add(
                        ValidationMessage(
                            Severity.ERROR,
                            "STIL_VEC_WIDTH_MISMATCH",
                            f"Pattern '{pat_name}' vector width {width} "
                            f"does not match expected {expected_width}",
                            line=line_no,
                        )
                    )

    def _check_procedures(self, model: STILModel, result: ValidationResult) -> None:
        # Basic sanity: ensure we can parse names and that bodies are non-empty
        for name, proc in model.procedures.items():
            if not proc.body_lines:
                result.add(
                    ValidationMessage(
                        Severity.WARNING,
                        "STIL_EMPTY_PROC",
                        f"Procedure '{name}' has no body",
                    )
                )

    def _check_pattern_exec(self, model: STILModel, result: ValidationResult) -> None:
        # Ensure that any pattern names mentioned in PatternExec exist in Patterns.
        for block in model.pattern_exec_blocks:
            for m in re.finditer(r'"([\w.$]+)"', block):
                pat_name = m.group(1)
                if pat_name not in model.patterns:
                    result.add(
                        ValidationMessage(
                            Severity.WARNING,
                            "STIL_EXEC_UNKNOWN_PATTERN",
                            f"PatternExec references unknown pattern '{pat_name}'",
                        )
                    )


# ---------------------------------------------------------------------------
# STIL to ATPG converters / diff utilities (pattern portability helpers)
# ---------------------------------------------------------------------------


def stil_model_to_atpg_vectors(model: STILModel) -> Dict[str, List[str]]:
    """
    Convert STIL patterns into a simple map:
        pattern_name -> list of raw vector strings (V { ... }).
    The existing SystemVerilog ATPG parser can then ingest these via a small
    text export step if desired.
    """
    out: Dict[str, List[str]] = {}
    for name, pat in model.patterns.items():
        out[name] = list(pat.vectors)
    return out


def stil_diff(a: STILModel, b: STILModel) -> Dict[str, Any]:
    """
    Compare two STIL models and return a high-level diff:
    - added/removed/modified patterns
    - added/removed signals
    """
    diff: Dict[str, Any] = {}

    a_pats = set(a.patterns.keys())
    b_pats = set(b.patterns.keys())
    diff["patterns_added"] = sorted(b_pats - a_pats)
    diff["patterns_removed"] = sorted(a_pats - b_pats)
    common = a_pats & b_pats
    modified = []
    for name in common:
        if a.patterns[name].vectors != b.patterns[name].vectors:
            modified.append(name)
    diff["patterns_modified"] = sorted(modified)

    a_sigs = set(a.signals.keys())
    b_sigs = set(b.signals.keys())
    diff["signals_added"] = sorted(b_sigs - a_sigs)
    diff["signals_removed"] = sorted(a_sigs - b_sigs)

    return diff


# ---------------------------------------------------------------------------
# CLI entry point (batch validation / diff)
# ---------------------------------------------------------------------------


def _run_cli() -> None:
    parser = argparse.ArgumentParser(description="STIL file validator and parser")
    parser.add_argument("stil_files", nargs="+", help="STIL files to validate")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Enable strict validation (treat more issues as errors)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format for validation report",
    )
    parser.add_argument(
        "--diff",
        metavar="OTHER_STIL",
        help="Optional second STIL file to diff against the first",
    )
    args = parser.parse_args()

    validator = STILFileValidator(strict=args.strict)
    all_results: Dict[str, ValidationResult] = {}

    for path in args.stil_files:
        res = validator.validate_stil_file(path)
        all_results[path] = res
        if args.format == "text":
            print(f"=== {path} ===")
            print(f"OK: {res.ok}")
            for m in res.messages:
                loc = f" (line {m.line})" if m.line is not None else ""
                print(f"[{m.severity.value}] {m.code}{loc}: {m.message}")
            print()

    if args.diff and len(args.stil_files) >= 1:
        sp = STILParser()
        base = sp.parse_file(args.stil_files[0])
        other = sp.parse_file(args.diff)
        d = stil_diff(base, other)
        if args.format == "text":
            print("=== STIL DIFF ===")
            print(json.dumps(d, indent=2))

    if args.format == "json":
        out = {
            "results": {
                path: {
                    "ok": res.ok,
                    "messages": [m.to_dict() for m in res.messages],
                }
                for path, res in all_results.items()
            }
        }
        if args.diff and len(args.stil_files) >= 1:
            sp = STILParser()
            base = sp.parse_file(args.stil_files[0])
            other = sp.parse_file(args.diff)
            out["diff"] = stil_diff(base, other)
        print(json.dumps(out, indent=2))


if __name__ == "__main__":
    _run_cli()

