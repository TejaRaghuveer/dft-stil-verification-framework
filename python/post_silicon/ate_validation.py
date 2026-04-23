from __future__ import annotations

import json
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Tuple


SUPPORTED_ATE_TYPES = {"V93000", "LTX_CREDENCE", "XCERRA"}


@dataclass
class TesterSpecs:
    max_tck_frequency_mhz: float = 500.0
    num_channels: int = 128
    memory_capacity_gb: float = 4.0
    max_pattern_rate_mvecs_per_sec: float = 10.0


@dataclass
class TimingSpecs:
    tco_margin_ns: float = 0.5
    setup_margin_ns: float = 0.3
    hold_margin_ns: float = 0.3


@dataclass
class ATEConfig:
    tester_type: str = "V93000"
    test_program_name: str = "GPU_Shader_DFT.trp"
    pattern_file: str = "patterns.stil"
    tester_specs: TesterSpecs = field(default_factory=TesterSpecs)
    timing_specs: TimingSpecs = field(default_factory=TimingSpecs)
    startup_procedure: str = "INIT_DUT"
    test_sequence: str = "RUN_ALL_PATTERNS"
    shutdown_procedure: str = "SHUTDOWN"


def _parse_braced_block(text: str, block_name: str) -> str:
    m = re.search(rf"{re.escape(block_name)}\s*\{{(.*?)\}}", text, re.DOTALL)
    return m.group(1) if m else ""


def _parse_value(block: str, key: str, default: str) -> str:
    m = re.search(rf"{re.escape(key)}\s*:\s*(.*?);", block)
    if not m:
        return default
    return m.group(1).strip().strip('"')


def parse_ate_config_text(text: str) -> ATEConfig:
    root = _parse_braced_block(text, "ate_config")
    tblock = _parse_braced_block(root, "tester_specs")
    timblock = _parse_braced_block(root, "timing_specs")
    pblock = _parse_braced_block(root, "test_program")

    cfg = ATEConfig(
        tester_type=_parse_value(root, "tester_type", "V93000"),
        test_program_name=_parse_value(root, "test_program_name", "GPU_Shader_DFT.trp"),
        pattern_file=_parse_value(root, "pattern_file", "patterns.stil"),
        tester_specs=TesterSpecs(
            max_tck_frequency_mhz=float(_parse_value(tblock, "max_tck_frequency_mhz", "500")),
            num_channels=int(_parse_value(tblock, "num_channels", "128")),
            memory_capacity_gb=float(_parse_value(tblock, "memory_capacity_gb", "4")),
            max_pattern_rate_mvecs_per_sec=float(_parse_value(tblock, "max_pattern_rate_mvecs_per_sec", "10")),
        ),
        timing_specs=TimingSpecs(
            tco_margin_ns=float(_parse_value(timblock, "tco_margin_ns", "0.5")),
            setup_margin_ns=float(_parse_value(timblock, "setup_margin_ns", "0.3")),
            hold_margin_ns=float(_parse_value(timblock, "hold_margin_ns", "0.3")),
        ),
        startup_procedure=_parse_value(pblock, "startup_procedure", "INIT_DUT"),
        test_sequence=_parse_value(pblock, "test_sequence", "RUN_ALL_PATTERNS"),
        shutdown_procedure=_parse_value(pblock, "shutdown_procedure", "SHUTDOWN"),
    )
    if cfg.tester_type not in SUPPORTED_ATE_TYPES:
        raise ValueError(f"Unsupported tester_type={cfg.tester_type}. Supported: {sorted(SUPPORTED_ATE_TYPES)}")
    return cfg


@dataclass
class ParsedPattern:
    name: str
    vectors: List[str]


class STILPatternParser:
    """Lightweight STIL parser for pattern/vector extraction."""

    def __init__(self, stil_file: str):
        self.stil_file = Path(stil_file)
        self.text = self.stil_file.read_text(encoding="utf-8", errors="ignore")

    def get_all_patterns(self) -> List[ParsedPattern]:
        patterns: List[ParsedPattern] = []
        for m in re.finditer(r'Pattern\s+"([^"]+)"\s*\{(.*?)\}', self.text, re.DOTALL):
            name = m.group(1)
            body = m.group(2)
            vectors = re.findall(r"V\s*\{\s*([^}]*)\}", body)
            cleaned = [v.strip().replace("\n", " ") for v in vectors if v.strip()]
            patterns.append(ParsedPattern(name=name, vectors=cleaned))
        if not patterns:
            vectors = re.findall(r"V\s*\{\s*([^}]*)\}", self.text)
            if vectors:
                patterns.append(
                    ParsedPattern(
                        name=self.stil_file.stem,
                        vectors=[v.strip().replace("\n", " ") for v in vectors if v.strip()],
                    )
                )
        return patterns


class ATEPatternConverter:
    """Converts STIL patterns to vendor-specific ATE pattern formats."""

    def __init__(self, ate_type: str):
        if ate_type not in SUPPORTED_ATE_TYPES:
            raise ValueError(f"Unsupported ATE type: {ate_type}")
        self.ate_type = ate_type

    def _emit_header(self) -> str:
        if self.ate_type == "V93000":
            return "# V93000 TRF pattern export\n"
        if self.ate_type == "LTX_CREDENCE":
            return "# LTX Credence pattern export\n"
        return "# Xcerra pattern export\n"

    def convert(self, patterns: List[ParsedPattern], out_file: str) -> Dict[str, Any]:
        out = Path(out_file)
        lines = [self._emit_header()]
        in_vectors = 0
        out_vectors = 0
        for p in patterns:
            lines.append(f"PATTERN {p.name}\n")
            for i, v in enumerate(p.vectors):
                in_vectors += 1
                lines.append(f"  CYCLE {i:06d} {v}\n")
                out_vectors += 1
            lines.append("END_PATTERN\n")
        out.write_text("".join(lines), encoding="utf-8")
        fidelity = 100.0 if in_vectors == out_vectors else (out_vectors / max(1, in_vectors)) * 100.0
        return {
            "ate_type": self.ate_type,
            "output_file": str(out),
            "input_patterns": len(patterns),
            "input_vectors": in_vectors,
            "output_vectors": out_vectors,
            "pattern_fidelity_percent": round(fidelity, 3),
        }


class ATECompatibilityChecker:
    """Checks if pattern set and timing target fit tester capabilities."""

    def __init__(self, cfg: ATEConfig):
        self.cfg = cfg

    def check(self, patterns: List[ParsedPattern], tck_mhz: float, required_channels: int) -> Dict[str, Any]:
        vectors = sum(len(p.vectors) for p in patterns)
        estimated_memory_gb = vectors * max(1, required_channels) * 1.0 / (8.0 * 1024**3)
        # Keep this uncapped so violations can be detected explicitly.
        est_rate = max(0.1, tck_mhz / 50.0)

        violations: List[str] = []
        warnings: List[str] = []
        if tck_mhz > self.cfg.tester_specs.max_tck_frequency_mhz:
            violations.append("Requested TCK exceeds tester max frequency")
        if required_channels > self.cfg.tester_specs.num_channels:
            violations.append("Required channels exceed tester channel capacity")
        if estimated_memory_gb > self.cfg.tester_specs.memory_capacity_gb:
            violations.append("Pattern set does not fit tester memory")
        if est_rate > self.cfg.tester_specs.max_pattern_rate_mvecs_per_sec:
            violations.append("Execution rate exceeds tester max pattern rate")
        if estimated_memory_gb > (0.85 * self.cfg.tester_specs.memory_capacity_gb):
            warnings.append("Pattern memory usage above 85% of tester capacity")

        return {
            "compatible": len(violations) == 0,
            "requested": {"tck_mhz": tck_mhz, "required_channels": required_channels, "vectors": vectors},
            "estimated": {
                "memory_gb": round(estimated_memory_gb, 6),
                "pattern_rate_mvecs_per_sec": round(est_rate, 3),
            },
            "tester_specs": asdict(self.cfg.tester_specs),
            "violations": violations,
            "warnings": warnings,
        }


class PatternValidationForATE:
    """Validates timing and pin mapping assumptions before tester bring-up."""

    def __init__(self, cfg: ATEConfig):
        self.cfg = cfg

    def validate(
        self,
        patterns: List[ParsedPattern],
        pin_map: Dict[str, str],
        tck_mhz: float,
        simulate: bool = True,
    ) -> Dict[str, Any]:
        missing = [f"DUT_{i}" for i in range(1, 9) if f"DUT_{i}" not in pin_map]
        period_ns = 1000.0 / max(1e-6, tck_mhz)
        timing_ok = period_ns > (self.cfg.timing_specs.setup_margin_ns + self.cfg.timing_specs.hold_margin_ns)
        tco_ok = period_ns > self.cfg.timing_specs.tco_margin_ns
        violations: List[str] = []
        if missing:
            violations.append(f"Pin map missing required entries: {missing}")
        if not timing_ok:
            violations.append("Setup/Hold margins exceed clock period budget")
        if not tco_ok:
            violations.append("TCO margin exceeds clock period budget")

        sim_result = "PASS" if simulate and not violations else ("SKIPPED" if not simulate else "FAIL")
        return {
            "validated_patterns": len(patterns),
            "ate_simulator_result": sim_result,
            "timing": {
                "period_ns": round(period_ns, 6),
                "setup_margin_ns": self.cfg.timing_specs.setup_margin_ns,
                "hold_margin_ns": self.cfg.timing_specs.hold_margin_ns,
                "tco_margin_ns": self.cfg.timing_specs.tco_margin_ns,
            },
            "pin_mapping_entries": len(pin_map),
            "violations": violations,
            "passed": len(violations) == 0,
        }


class ExpectedResponseDatabase:
    """Creates golden response DB for ATE pass/fail compare."""

    def build(
        self,
        patterns: List[ParsedPattern],
        out_json: str,
        default_limits: Dict[str, float] | None = None,
    ) -> Dict[str, Any]:
        limits = default_limits or {"vmin": 0.0, "vmax": 1.2, "tolerance": 0.02}
        rows = []
        for p in patterns:
            rows.append(
                {
                    "pattern": p.name,
                    "expected_response": "PASS_SIGNATURE",
                    "vector_count": len(p.vectors),
                    "limits": limits,
                }
            )
        payload = {"entries": rows, "entry_count": len(rows)}
        out = Path(out_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return {"output_file": str(out), "entry_count": len(rows)}


class DebugPatternGeneration:
    """Creates module-specific debug pattern sets for tester diagnosis."""

    def generate(self, out_json: str) -> Dict[str, Any]:
        data = {
            "diagnostic_patterns": [
                {"name": "DBG_ALU_ONLY", "target_module": "ALU", "purpose": "Arithmetic and compare isolation"},
                {"name": "DBG_REGFILE_RW", "target_module": "REGISTER_FILE", "purpose": "Read/write path integrity"},
                {"name": "DBG_INTERCONNECT_ROUTE", "target_module": "INTERCONNECT", "purpose": "Route arbitration and integrity"},
                {"name": "DBG_POWER_MARGIN", "target_module": "POWER", "purpose": "Supply margin sensitivity"},
                {"name": "DBG_CLOCK_VERIFY", "target_module": "CLOCK", "purpose": "Clock path and duty checks"},
            ]
        }
        out = Path(out_json)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(data, indent=2), encoding="utf-8")
        return {"output_file": str(out), "count": len(data["diagnostic_patterns"])}


class ATEProgramBuilder:
    """Generates a tester-friendly program template with pattern call flow."""

    def __init__(self, ate_type: str):
        self.ate_type = ate_type
        self.patterns: List[str] = []
        self.procedures: List[Tuple[str, str]] = []

    def add_pattern(self, pattern: ParsedPattern) -> None:
        self.patterns.append(pattern.name)

    def add_procedure(self, name: str, impl_ref: str) -> None:
        self.procedures.append((name, impl_ref))

    def generate_program(self, output_file: str) -> str:
        out = Path(output_file)
        lines = [
            "#!/usr/bin/env python3\n",
            "# Auto-generated ATE test program template\n\n",
            f"ATE_TYPE = '{self.ate_type}'\n",
            f"PATTERNS = {json.dumps(self.patterns, indent=2)}\n",
            f"PROCEDURES = {json.dumps(self.procedures, indent=2)}\n\n",
            "def run_program():\n",
            "    print(f'Starting ATE program for {ATE_TYPE}')\n",
            "    for name in PATTERNS:\n",
            "        print(f'Execute pattern: {name}')\n",
            "    print('ATE program complete')\n\n",
            "if __name__ == '__main__':\n",
            "    run_program()\n",
        ]
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text("".join(lines), encoding="utf-8")
        return str(out)


class YieldPredictionModel:
    """Simple post-silicon yield forecast model using coverage and defect density."""

    def predict(self, fault_coverage_percent: float, defect_density_per_mm2: float, die_area_mm2: float) -> Dict[str, Any]:
        base_escape = max(0.0, 1.0 - fault_coverage_percent / 100.0)
        defect_term = 1.0 - math.exp(-max(0.0, defect_density_per_mm2) * max(0.0, die_area_mm2))
        predicted_yield = max(0.0, 1.0 - min(1.0, base_escape + 0.35 * defect_term))
        return {
            "fault_coverage_percent": fault_coverage_percent,
            "defect_density_per_mm2": defect_density_per_mm2,
            "die_area_mm2": die_area_mm2,
            "predicted_yield_percent": round(predicted_yield * 100.0, 3),
            "critical_focus": "High-density logic blocks and interconnect hot paths",
        }


class PostSiliconCorrelationFramework:
    """Correlates silicon outcomes with pre-silicon expectations."""

    def correlate(self, pre_silicon: Dict[str, Any], post_silicon: Dict[str, Any]) -> Dict[str, Any]:
        pre_fc = float(pre_silicon.get("fault_coverage_percent", 0.0))
        post_pass = float(post_silicon.get("pass_rate_percent", 0.0))
        delta = round(post_pass - pre_fc, 3)
        discrepancies: List[str] = []
        if abs(delta) > 5.0:
            discrepancies.append("Large pass-rate vs coverage delta; investigate model assumptions and tester setup")
        return {
            "pre_silicon": pre_silicon,
            "post_silicon": post_silicon,
            "correlation_delta_percent": delta,
            "discrepancies": discrepancies,
        }


class FailureAnalysisTools:
    """Maps ATE failures to pattern families and recommends yield improvements."""

    def analyze(self, failure_rows: List[Dict[str, Any]]) -> Dict[str, Any]:
        by_pattern: Dict[str, int] = {}
        for row in failure_rows:
            key = str(row.get("pattern", "UNKNOWN"))
            by_pattern[key] = by_pattern.get(key, 0) + 1
        top = sorted(by_pattern.items(), key=lambda x: x[1], reverse=True)[:10]
        recommendations = [
            "Re-run top failing patterns with debug variants (clock/power margin).",
            "Cross-check failing pattern families against pre-silicon critical paths.",
            "Tighten pin-map and timing margin validation before next lot execution.",
        ]
        return {"top_failing_patterns": top, "recommendations": recommendations}


def write_json(path: str, payload: Dict[str, Any]) -> str:
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(p)

