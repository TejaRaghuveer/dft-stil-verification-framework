from __future__ import annotations

import argparse
import json
from pathlib import Path

from .ate_validation import (
    ATECompatibilityChecker,
    ATEPatternConverter,
    ATEProgramBuilder,
    DebugPatternGeneration,
    ExpectedResponseDatabase,
    FailureAnalysisTools,
    PatternValidationForATE,
    PostSiliconCorrelationFramework,
    STILPatternParser,
    YieldPredictionModel,
    parse_ate_config_text,
    write_json,
)


def _load_cfg(path: str):
    return parse_ate_config_text(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description="Post-silicon ATE integration toolkit")
    ap.add_argument("--config", required=True, help="ATE config text file")
    ap.add_argument("--stil-file", required=True, help="Input STIL pattern file")
    ap.add_argument("--out-dir", default="out/post_silicon", help="Output directory")
    ap.add_argument("--tck-mhz", type=float, default=200.0)
    ap.add_argument("--required-channels", type=int, default=64)
    ap.add_argument("--defect-density", type=float, default=0.1, help="Defects per mm^2")
    ap.add_argument("--die-area-mm2", type=float, default=120.0)
    args = ap.parse_args()

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    cfg = _load_cfg(args.config)
    patterns = STILPatternParser(args.stil_file).get_all_patterns()

    converter = ATEPatternConverter(cfg.tester_type)
    conv = converter.convert(patterns, str(out / f"patterns_{cfg.tester_type.lower()}.pat"))
    write_json(str(out / "conversion_report.json"), conv)

    compat = ATECompatibilityChecker(cfg).check(patterns, tck_mhz=args.tck_mhz, required_channels=args.required_channels)
    write_json(str(out / "compatibility_report.json"), compat)

    pin_upper = min(cfg.tester_specs.num_channels, 16)
    pin_map = {f"DUT_{i}": f"ATE_CH{i}" for i in range(1, pin_upper + 1)}
    val = PatternValidationForATE(cfg).validate(patterns, pin_map=pin_map, tck_mhz=args.tck_mhz, simulate=True)
    write_json(str(out / "ate_validation_report.json"), val)

    erd = ExpectedResponseDatabase().build(patterns, str(out / "expected_responses.json"))
    dbg = DebugPatternGeneration().generate(str(out / "debug_patterns.json"))

    pb = ATEProgramBuilder(cfg.tester_type)
    for p in patterns:
        pb.add_pattern(p)
    pb.add_procedure("initialization", cfg.startup_procedure)
    pb.add_procedure("test_execution", cfg.test_sequence)
    pb.add_procedure("shutdown", cfg.shutdown_procedure)
    prog = pb.generate_program(str(out / cfg.test_program_name.replace(".trp", ".py")))

    fc = 96.0
    y = YieldPredictionModel().predict(fc, args.defect_density, args.die_area_mm2)
    write_json(str(out / "yield_forecast.json"), y)

    corr = PostSiliconCorrelationFramework().correlate(
        {"fault_coverage_percent": fc},
        {"pass_rate_percent": 94.0},
    )
    write_json(str(out / "correlation_report.json"), corr)

    fail = FailureAnalysisTools().analyze(
        [
            {"pattern": "DBG_ALU_ONLY"},
            {"pattern": "DBG_ALU_ONLY"},
            {"pattern": "DBG_CLOCK_VERIFY"},
        ]
    )
    write_json(str(out / "failure_analysis_report.json"), fail)

    def rel_path(value: str) -> str:
        return str(Path(value).resolve().relative_to(out.resolve()))

    manifest = {
        "ate_type": cfg.tester_type,
        "input_patterns": len(patterns),
        "reports": {
            "conversion": "conversion_report.json",
            "compatibility": "compatibility_report.json",
            "validation": "ate_validation_report.json",
            "expected_responses": rel_path(erd["output_file"]),
            "debug_patterns": rel_path(dbg["output_file"]),
            "program_template": rel_path(prog),
            "yield_forecast": "yield_forecast.json",
            "correlation": "correlation_report.json",
            "failure_analysis": "failure_analysis_report.json",
        },
    }
    (out / "post_silicon_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print(f"Post-silicon bundle generated: {out}")


if __name__ == "__main__":
    main()

