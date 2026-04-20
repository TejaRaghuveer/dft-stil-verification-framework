"""CLI entry for ML pattern optimization."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict

from pattern_db.pattern_database import PatternDatabase, PatternDatabaseConfig
from .pattern_ml_analyzer import analyze_pattern_db_with_ml, PatternMLAnalyzer


def _load_exec_metrics(path: str) -> Dict[str, Dict[str, Any]]:
    p = Path(path)
    if not p.exists():
        return {}
    data = json.loads(p.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return {str(k): v for k, v in data.items() if isinstance(v, dict)}
    return {}


def main() -> None:
    ap = argparse.ArgumentParser(description="ML-based pattern optimization")
    ap.add_argument("--pattern-db", required=True, help="Path to pattern_db.json")
    ap.add_argument("--exec-metrics-json", default=None, help="Optional execution metrics mapping by pattern name")
    ap.add_argument("--target-coverage", type=float, default=95.0)
    ap.add_argument("--max-patterns", type=int, default=None)
    ap.add_argument("--out-json", default="ml_pattern_optimization.json")
    ap.add_argument("--out-txt", default="ml_pattern_optimization.txt")
    ap.add_argument("--learning-history", default="ml_learning_history.json")
    args = ap.parse_args()

    db = PatternDatabase(PatternDatabaseConfig(storage_path=args.pattern_db))
    db.load_from_file(args.pattern_db)
    exec_metrics = _load_exec_metrics(args.exec_metrics_json) if args.exec_metrics_json else {}
    report = analyze_pattern_db_with_ml(
        db,
        execution_metrics_by_pattern=exec_metrics,
        target_coverage=args.target_coverage,
        max_patterns=args.max_patterns,
        out_json=args.out_json,
        out_txt=args.out_txt,
        learning_history_path=args.learning_history,
    )
    print(PatternMLAnalyzer.format_text_report(report))


if __name__ == "__main__":
    main()

