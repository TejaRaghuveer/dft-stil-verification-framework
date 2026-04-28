from __future__ import annotations

import argparse

from .engine import DesignMetric, PatternRecord, build_advanced_analysis_bundle


def main() -> None:
    ap = argparse.ArgumentParser(description="Run advanced analytics and intelligence bundle")
    ap.add_argument("--out-dir", default="out/advanced_analytics")
    ap.add_argument("--budget-sec", type=float, default=7200.0)
    args = ap.parse_args()

    patterns = [
        PatternRecord("PAT_001", duration_sec=18.0, coverage_contribution=0.004, fault_count=32, fail_count=0),
        PatternRecord("PAT_002", duration_sec=31.0, coverage_contribution=0.0032, fault_count=28, fail_count=1),
        PatternRecord("PAT_003", duration_sec=12.5, coverage_contribution=0.0046, fault_count=35, fail_count=0),
        PatternRecord("PAT_004", duration_sec=27.0, coverage_contribution=0.0025, fault_count=20, fail_count=2),
        PatternRecord("PAT_005", duration_sec=21.0, coverage_contribution=0.0038, fault_count=27, fail_count=1),
    ]

    modules = [
        DesignMetric("Control_Logic", coverage_percent=94.5, untestable_percent=1.2, sequential_depth=8, scan_access_percent=100.0),
        DesignMetric("Cache_Coherence", coverage_percent=91.5, untestable_percent=1.8, sequential_depth=11, scan_access_percent=99.0),
        DesignMetric("ALU", coverage_percent=97.4, untestable_percent=0.6, sequential_depth=7, scan_access_percent=100.0),
    ]

    build_advanced_analysis_bundle(patterns, modules, out_dir=args.out_dir, budget_sec=args.budget_sec)
    print(f"Advanced analytics bundle generated at: {args.out_dir}")


if __name__ == "__main__":
    main()

