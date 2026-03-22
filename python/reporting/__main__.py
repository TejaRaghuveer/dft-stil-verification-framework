"""Demo comprehensive report + multi-domain sample."""

from __future__ import annotations

import json
import tempfile
from pathlib import Path

from .comprehensive_reporting import ComprehensiveReportingSystem
from .report_generator import ReportInputData
from .templates import ReportTemplateId


def main() -> None:
    data = ReportInputData(
        design_name="GPU_Shader_Core",
        duration_seconds=12.5 * 3600,
        patterns_total=1000,
        patterns_pass=1000,
        patterns_fail=0,
        fault_coverage_pct=96.2,
        test_coverage_pct=96.8,
        target_coverage_pct=95.0,
        defect_level_ppm=4.1,
        total_faults=50000,
        coverage_by_fault_type={
            "Stuck-at-0": 96.8,
            "Stuck-at-1": 95.6,
            "Transition Delay": 96.5,
            "Path Delay": 95.0,
        },
        coverage_by_module={
            "ALU": 97.8,
            "Register File": 96.2,
            "Cache Interface": 95.1,
            "Control Logic": 94.5,
        },
        undetected_breakdown={
            "Untestable": 1500,
            "Undetectable": 200,
            "Retry Needed": 100,
        },
        recommendations=[
            "Coverage meets tapeout requirement (96.2% > 95% target)",
            "Control_Logic at 94.5% — review observability",
            "Path delay at target minimum — consider more at-speed patterns",
        ],
        coverage_convergence=[(100, 70), (250, 82), (500, 90), (750, 94), (1000, 96.2)],
        per_pattern_results=[{"pattern": "p%04d" % i, "pass": True} for i in range(5)],
    )
    sys = ComprehensiveReportingSystem()
    sys.data = data
    sys.set_template(ReportTemplateId.DETAILED)
    with tempfile.TemporaryDirectory() as d:
        paths = sys.export_all(d, "demo_dft")
        print(json.dumps(paths, indent=2))
        print(Path(paths["html"]).read_text(encoding="utf-8")[:500])


if __name__ == "__main__":
    main()
