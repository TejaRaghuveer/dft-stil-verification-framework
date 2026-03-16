#!/usr/bin/env python3
"""
Integrated DFT test flow runner
-------------------------------

Connects:
  ATPG pattern parser -> pattern database
  Pattern database -> test suite builder
  Test suite -> UVM (pattern list file + plusargs)
  UVM results (CSV) -> execution summary + performance
  Executed patterns -> fault coverage analyzer
  STIL generation -> STIL validator -> comparison vs input vectors
  All outputs -> comprehensive report bundle
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import subprocess
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from atpg_parser.atpg_parser import ATPGParser, ATPGFormat
from pattern_db.pattern_database import (
    PatternDatabase,
    PatternDatabaseConfig,
    PatternRecord,
    PatternType,
    TestSuiteBuilder,
    TestSuiteConfiguration,
    TestSelectionStrategy,
)
from fault_coverage.fault_coverage_engine import FaultCoverageAnalyzer, FaultCoverageConfig, run_full_analysis
from stil_generator.stil_template_generator import STILTemplateGenerator, STILSignal, STILTiming, STILPattern
from stil_utils.stil_validator import STILFileValidator, STILParser


@dataclass
class ExecutionResult:
    pattern_name: str
    index: int
    status: str  # PASS/FAIL/ERROR
    start_time: int
    end_time: int
    duration_ns: int
    vector_fail: int
    mismatches: int
    total_vectors: int


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def parse_atpg_to_pattern_db(atpg_file: str, out_db_path: str, pattern_type: PatternType) -> PatternDatabase:
    parser = ATPGParser(ATPGFormat.GENERIC)
    parser.parse_generic(atpg_file)

    db = PatternDatabase(PatternDatabaseConfig(storage_path=out_db_path))
    db.metadata = {"source": "python.atpg_parser", "input_file": atpg_file}

    for i, p in enumerate(parser.patterns, start=1):
        # vector-per-line is stored in scan_inputs['vec'] as concatenation; split into single line
        vec = ""
        if "vec" in p.scan_inputs:
            vec = p.scan_inputs["vec"]
        # If parser produced multiple vectors, we treat each line as a vector line
        vector_lines = []
        if vec:
            vector_lines.append(vec)

        size_bits = len(vector_lines[0]) if vector_lines else 0
        rec = PatternRecord(
            pattern_id=i,
            pattern_name=p.pattern_id,
            pattern_type=pattern_type,
            vector_lines=vector_lines,
            fault_list=[],
            fault_count=0,
            size_bits=size_bits,
        )
        db.add_pattern(rec)

    db.save_to_file(out_db_path)
    return db


def build_suite_and_write_list(
    db: PatternDatabase,
    strategy: TestSelectionStrategy,
    target_coverage: float,
    max_patterns: Optional[int],
    out_dir: str,
    suite_name: str,
) -> Tuple[str, List[PatternRecord]]:
    ensure_dir(out_dir)
    builder = TestSuiteBuilder(db)
    cfg = TestSuiteConfiguration(
        strategy=strategy,
        target_coverage=target_coverage,
        max_pattern_count=max_patterns,
    )
    suite = builder.build_suite(cfg)

    list_path = os.path.join(out_dir, f"{suite_name}_pattern_list.txt")
    with open(list_path, "w", newline="\n") as f:
        for p in suite:
            f.write(p.pattern_name + "\n")
    return list_path, suite


def run_uvm_sim(make_sim: str, test_name: str, plusargs: List[str], cwd: str) -> int:
    cmd = ["make", f"SIM={make_sim}", f"TEST={test_name}", f"PLUSARGS={' '.join(plusargs)}"]
    return subprocess.call(cmd, cwd=cwd)


def parse_results_csv(path: str) -> List[ExecutionResult]:
    if not os.path.exists(path):
        return []
    out: List[ExecutionResult] = []
    with open(path, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            out.append(
                ExecutionResult(
                    pattern_name=row["pattern_name"],
                    index=int(row["index"]),
                    status=row["status"],
                    start_time=int(row["start_time"]),
                    end_time=int(row["end_time"]),
                    duration_ns=int(row["duration_ns"]),
                    vector_fail=int(row["vector_fail"]),
                    mismatches=int(row["mismatches"]),
                    total_vectors=int(row["total_vectors"]),
                )
            )
    return out


def execution_summary(results: List[ExecutionResult]) -> Dict[str, Any]:
    total = len(results)
    pass_n = sum(1 for r in results if r.status == "ATPG_PATTERN_PASS" or r.status == "PASS")
    fail_n = sum(1 for r in results if r.status == "ATPG_PATTERN_FAIL" or r.status == "FAIL")
    err_n = total - pass_n - fail_n
    return {"total_patterns": total, "pass": pass_n, "fail": fail_n, "error": err_n}


def performance_report(results: List[ExecutionResult]) -> Dict[str, Any]:
    durations = [r.duration_ns for r in results if r.duration_ns > 0]
    total_ns = sum(durations)
    total_s = total_ns / 1e9 if total_ns else 0.0
    patterns_per_sec = (len(durations) / total_s) if total_s > 0 else 0.0
    slowest = sorted(results, key=lambda r: r.duration_ns, reverse=True)[:10]
    return {
        "total_duration_s": round(total_s, 3),
        "patterns_per_second": round(patterns_per_sec, 3),
        "slowest_patterns": [
            {"pattern": r.pattern_name, "duration_ns": r.duration_ns, "status": r.status} for r in slowest
        ],
    }


def achieved_fault_coverage(db: PatternDatabase, results: List[ExecutionResult], out_path: str) -> Dict[str, Any]:
    executed = {r.pattern_name for r in results if r.status != "ATPG_PATTERN_ERROR" and r.status != "ERROR"}
    analyzer = FaultCoverageAnalyzer()

    # Populate detected faults only from executed patterns
    for p in db._patterns.values():
        if p.pattern_name in executed and p.fault_list:
            analyzer.link_pattern_to_faults(p.pattern_name, p.fault_list)
        else:
            # ensure pattern present in mapping for contribution reporting
            analyzer.pattern_to_faults[p.pattern_name] = list(p.fault_list)

    cfg = FaultCoverageConfig(report_format="json", report_file_path=out_path)
    return run_full_analysis(analyzer, cfg)


def generate_stil_from_db(db: PatternDatabase, out_stil: str) -> None:
    gen = STILTemplateGenerator(out_stil)
    # Minimal scan-only STIL: one pseudo-signal 'SCAN' whose width equals vector length
    # For validator compatibility we still need Signals + Timing + Patterns + PatternExec.
    gen.add_signal(STILSignal("SCAN", "In", "Digital", "Scan vector bits"))
    gen.set_timing(
        STILTiming(
            period=100.0,
            waveforms={"scan": [("C", 0), ("D", 50)]},
        )
    )
    for p in db._patterns.values():
        # Store the whole vector line as one signal value; generator concatenates in signal order
        vec = p.vector_lines[0] if p.vector_lines else "X"
        gen.add_pattern(STILPattern(vector_id=p.pattern_name, signals={"SCAN": vec}, comment="ATPG import"))
    gen.write_file()


def validate_and_compare_stil(stil_path: str, db: PatternDatabase) -> Dict[str, Any]:
    v = STILFileValidator(strict=False)
    res = v.validate_stil_file(stil_path)

    # Compare vectors vs DB (basic: first vector line per pattern)
    sp = STILParser()
    model = sp.parse_file(stil_path)
    mismatches = []
    for p in db._patterns.values():
        if p.pattern_name not in model.patterns:
            mismatches.append({"pattern": p.pattern_name, "reason": "missing_in_stil"})
            continue
        vecs = model.patterns[p.pattern_name].vectors
        if not vecs:
            mismatches.append({"pattern": p.pattern_name, "reason": "no_vectors"})
            continue
        expected = (p.vector_lines[0] if p.vector_lines else "").strip()
        # vec line is like 'V { .... };' so extract inside braces
        raw = vecs[0]
        inside = raw
        if "{" in raw and "}" in raw:
            inside = raw.split("{", 1)[1].rsplit("}", 1)[0].strip()
        if expected and inside != expected:
            mismatches.append({"pattern": p.pattern_name, "expected": expected, "actual": inside})

    return {
        "ok": res.ok,
        "messages": [m.to_dict() for m in res.messages],
        "compare_mismatches": mismatches[:200],
        "compare_mismatch_count": len(mismatches),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Integrated DFT-STIL flow runner")
    ap.add_argument("--design", default="GPU_Shader_Core")
    ap.add_argument("--atpg", required=True, help="Input ATPG ASCII pattern file")
    ap.add_argument("--sim", default="vcs", choices=["vcs", "xrun"])
    ap.add_argument("--uvm_test", default="atpg_select_patterns_test")
    ap.add_argument("--out", default="out/integrated")
    ap.add_argument("--smoke_n", type=int, default=30)
    ap.add_argument("--coverage_target", type=float, default=95.0)
    ap.add_argument("--run_full", action="store_true", help="Also run full pattern set")
    args = ap.parse_args()

    root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    out_dir = os.path.abspath(args.out)
    ensure_dir(out_dir)

    db_path = os.path.join(out_dir, "pattern_db.json")
    db = parse_atpg_to_pattern_db(args.atpg, db_path, PatternType.STUCK_AT)

    suites_dir = os.path.join(out_dir, "suites")
    smoke_list, smoke_suite = build_suite_and_write_list(
        db, TestSelectionStrategy.SMOKE, args.coverage_target, args.smoke_n, suites_dir, "smoke"
    )

    results_dir = os.path.join(out_dir, "results")
    ensure_dir(results_dir)

    def run_one(name: str, pattern_list: str, max_patterns: int) -> Dict[str, Any]:
        csv_path = os.path.join(results_dir, f"{name}_results.csv")
        plusargs = [
            f"+PATTERN_FILE={args.atpg}",
            f"+PATTERN_LIST_FILE={pattern_list}",
            f"+MAX_PATTERNS={max_patterns}",
            f"+RESULT_CSV={csv_path}",
        ]
        t0 = time.time()
        rc = run_uvm_sim(args.sim, args.uvm_test, plusargs, cwd=root)
        t1 = time.time()
        results = parse_results_csv(csv_path)
        return {
            "return_code": rc,
            "wall_time_s": round(t1 - t0, 3),
            "csv_path": csv_path,
            "summary": execution_summary(results),
            "performance": performance_report(results),
            "raw_results": [r.__dict__ for r in results],
        }

    smoke_exec = run_one("smoke", smoke_list, len(smoke_suite))

    full_exec = None
    if args.run_full:
        full_list, full_suite = build_suite_and_write_list(
            db, TestSelectionStrategy.COMPREHENSIVE, args.coverage_target, None, suites_dir, "full"
        )
        full_exec = run_one("full", full_list, 0)

    # Fault coverage: treat executed patterns as \"achieved\" coverage contributors
    fc_path = os.path.join(out_dir, "fault_coverage.json")
    fc = achieved_fault_coverage(db, [ExecutionResult(**r) for r in smoke_exec["raw_results"]], fc_path)

    # STIL generation + validation + compare
    stil_path = os.path.join(out_dir, "generated.stil")
    generate_stil_from_db(db, stil_path)
    stil_report = validate_and_compare_stil(stil_path, db)
    stil_report_path = os.path.join(out_dir, "stil_validation.json")
    with open(stil_report_path, "w") as f:
        json.dump(stil_report, f, indent=2)

    # Integrated report
    integrated = {
        "design": args.design,
        "inputs": {"atpg_file": args.atpg, "pattern_db": db_path, "generated_stil": stil_path},
        "smoke": smoke_exec,
        "full": full_exec,
        "fault_coverage": fc,
        "stil_validation": stil_report,
    }
    integrated_path = os.path.join(out_dir, "integrated_report.json")
    with open(integrated_path, "w") as f:
        json.dump(integrated, f, indent=2)

    print(f"Wrote: {integrated_path}")


if __name__ == "__main__":
    main()

