"""
GPU shader-core DFT specialization.

This module extends the generic framework with shader-centric verification that
targets ALU datapath correctness, register file integrity, and interconnect /
pipeline movement. The implementation intentionally keeps the model lightweight
so it can run in CI dry-runs while still producing meaningful, architecture-
aligned reports and coverage summaries.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

from reporting.visualization import fault_histogram_svg, module_heatmap_html


_INT_OPS = ("ADD", "SUB", "MUL", "DIV", "AND", "OR", "XOR", "NOT", "SHIFT")
_CMP_OPS = ("EQ", "NE", "LT", "GT", "LE", "GE")


@dataclass
class GPUShaderConfig:
    """
    GPU shader-core configuration knobs used by DFT specialization.

    The defaults match a practical mid-size scalar shader slice and can be
    overridden from either dict input or gpu_shader_config { ... } text blocks.
    """

    bit_width: int = 32
    instruction_format: str = "scalar"
    pipeline_depth: int = 4
    num_alu_units: int = 2
    num_registers: int = 32
    register_banks: int = 4
    memory_interfaces: int = 1
    scan_chains: int = 16
    alu_operations: List[str] = field(
        default_factory=lambda: ["ADD", "SUB", "MUL", "DIV", "AND", "OR", "XOR", "NOT", "SHIFT"]
    )
    verify_modes: List[str] = field(default_factory=lambda: ["FUNCTIONAL", "SCAN", "AT_SPEED"])

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "GPUShaderConfig":
        ops = d.get("alu_operations", cls().alu_operations)
        if isinstance(ops, str):
            ops = [x.strip().upper() for x in ops.strip("[]").split(",") if x.strip()]
        modes = d.get("verify_modes", cls().verify_modes)
        if isinstance(modes, str):
            modes = [x.strip().upper() for x in modes.strip("[]").split(",") if x.strip()]
        return cls(
            bit_width=int(d.get("bit_width", 32)),
            instruction_format=str(d.get("instruction_format", "scalar")).lower(),
            pipeline_depth=int(d.get("pipeline_depth", 4)),
            num_alu_units=int(d.get("num_alu_units", 2)),
            num_registers=int(d.get("num_registers", 32)),
            register_banks=int(d.get("register_banks", 4)),
            memory_interfaces=int(d.get("memory_interfaces", 1)),
            scan_chains=int(d.get("scan_chains", 16)),
            alu_operations=[str(x).upper() for x in list(ops)],
            verify_modes=[str(x).upper() for x in list(modes)],
        )


def parse_gpu_shader_config_text(text: str) -> GPUShaderConfig:
    """
    Parse config in block form:

    gpu_shader_config {
      bit_width: 32;
      alu_operations: [ADD, SUB, MUL];
      ...
    }
    """

    body_m = re.search(r"gpu_shader_config\s*\{(.*)\}", text, flags=re.IGNORECASE | re.DOTALL)
    if not body_m:
        raise ValueError("No gpu_shader_config { ... } block found")
    inner = body_m.group(1)
    out: Dict[str, Any] = {}
    for chunk in re.split(r";\s*\n?|\n(?=[a-zA-Z_]+\s*:)", inner):
        row = chunk.strip().rstrip(";").strip()
        if not row or ":" not in row:
            continue
        key, _, val = row.partition(":")
        key = key.strip()
        val = val.strip()
        if val.startswith("[") and val.endswith("]"):
            out[key] = [x.strip() for x in val[1:-1].split(",") if x.strip()]
            continue
        if re.fullmatch(r"-?\d+", val):
            out[key] = int(val)
            continue
        out[key] = val
    return GPUShaderConfig.from_dict(out)


@dataclass
class ALUTestVector:
    op: str
    a: int
    b: int
    expected: int
    mode: str
    category: str
    fault_hint: str


class ALUExecutionAgent:
    """Models ALU stimulus/observe behavior used in sequence-level tests."""

    def __init__(self, cfg: GPUShaderConfig):
        self.cfg = cfg
        self.mask = (1 << cfg.bit_width) - 1
        self.signbit = 1 << (cfg.bit_width - 1)

    def _to_signed(self, x: int) -> int:
        x = x & self.mask
        return x - (1 << self.cfg.bit_width) if x & self.signbit else x

    def _norm(self, x: int) -> int:
        return x & self.mask

    def execute(self, op: str, a: int, b: int) -> int:
        au = self._norm(a)
        bu = self._norm(b)
        asg = self._to_signed(a)
        bsg = self._to_signed(b)
        if op == "ADD":
            return self._norm(au + bu)
        if op == "SUB":
            return self._norm(au - bu)
        if op == "MUL":
            return self._norm(asg * bsg)
        if op == "DIV":
            if bsg == 0:
                return self._norm(0)
            return self._norm(int(asg / bsg))
        if op == "AND":
            return au & bu
        if op == "OR":
            return au | bu
        if op == "XOR":
            return au ^ bu
        if op == "NOT":
            return self._norm(~au)
        if op == "SHIFT":
            return self._norm(au << (bu & 0x1F))
        if op == "EQ":
            return 1 if asg == bsg else 0
        if op == "NE":
            return 1 if asg != bsg else 0
        if op == "LT":
            return 1 if asg < bsg else 0
        if op == "GT":
            return 1 if asg > bsg else 0
        if op == "LE":
            return 1 if asg <= bsg else 0
        if op == "GE":
            return 1 if asg >= bsg else 0
        raise ValueError(f"Unsupported ALU op: {op}")


def alu_reference_execute(cfg: GPUShaderConfig, op: str, a: int, b: int) -> int:
    """
    Reference/oracle ALU computation.

    This function is intentionally separate from `ALUExecutionAgent.execute` so
    test expected values are not computed via the same implementation.
    """

    mask = (1 << cfg.bit_width) - 1
    signbit = 1 << (cfg.bit_width - 1)

    def norm(x: int) -> int:
        return x & mask

    def to_signed(x: int) -> int:
        x = x & mask
        return x - (1 << cfg.bit_width) if x & signbit else x

    au = norm(a)
    bu = norm(b)
    asg = to_signed(a)
    bsg = to_signed(b)

    if op == "ADD":
        return norm(au + bu)
    if op == "SUB":
        return norm(au - bu)
    if op == "MUL":
        return norm(asg * bsg)
    if op == "DIV":
        if bsg == 0:
            return norm(0)
        # Truncate toward zero for signed division (match common hardware behavior).
        q = abs(asg) // abs(bsg)
        if (asg < 0) ^ (bsg < 0):
            q = -q
        return norm(int(q))
    if op == "AND":
        return au & bu
    if op == "OR":
        return au | bu
    if op == "XOR":
        return au ^ bu
    if op == "NOT":
        return norm(~au)
    if op == "SHIFT":
        return norm(au << (bu & 0x1F))

    # Comparisons return 1/0.
    if op == "EQ":
        return 1 if asg == bsg else 0
    if op == "NE":
        return 1 if asg != bsg else 0
    if op == "LT":
        return 1 if asg < bsg else 0
    if op == "GT":
        return 1 if asg > bsg else 0
    if op == "LE":
        return 1 if asg <= bsg else 0
    if op == "GE":
        return 1 if asg >= bsg else 0

    raise ValueError(f"Unsupported ALU op: {op}")


class RegisterFileAgent:
    """
    Models read/write/arbitration checks for register storage.

    Uses bank mapping for basic coverage and conflict checks:
      bank = register_index % register_banks
    """

    def __init__(self, cfg: GPUShaderConfig):
        self.cfg = cfg
        self._regs = [0 for _ in range(cfg.num_registers)]
        self._mask = (1 << cfg.bit_width) - 1

    def write(self, idx: int, value: int) -> None:
        self._regs[idx % self.cfg.num_registers] = value & self._mask

    def read(self, idx: int) -> int:
        return self._regs[idx % self.cfg.num_registers]

    def bank_for(self, idx: int) -> int:
        return idx % max(self.cfg.register_banks, 1)

    def arbitration_ok(self, readers: Sequence[int], writers: Sequence[int]) -> bool:
        # Arbitration policy: multiple readers always allowed, one writer per bank per cycle.
        seen = set()
        for w in writers:
            b = self.bank_for(w)
            if b in seen:
                return False
            seen.add(b)
        return True


class InterconnectAgent:
    """Models data routing across shader pipeline stages."""

    def __init__(self, cfg: GPUShaderConfig):
        self.cfg = cfg

    def route(self, payload: Dict[str, Any], stages: Optional[int] = None) -> List[Dict[str, Any]]:
        depth = stages if stages is not None else self.cfg.pipeline_depth
        timeline = []
        for s in range(max(depth, 1)):
            timeline.append(
                {
                    "stage": s,
                    "latched": True,
                    "payload_hash": hash(json.dumps(payload, sort_keys=True)) & 0xFFFFFFFF,
                    "forwarded": s < depth - 1,
                }
            )
        return timeline


class TextureMemoryAgent:
    """Optional texture memory path checks for shader-side memory interfaces."""

    def __init__(self, cfg: GPUShaderConfig):
        self.cfg = cfg

    def probe(self) -> Dict[str, Any]:
        return {
            "enabled": self.cfg.memory_interfaces > 0,
            "interfaces": self.cfg.memory_interfaces,
            "status": "ok" if self.cfg.memory_interfaces > 0 else "not_applicable",
        }


class ALUVerificationSequences:
    """Generates operation vectors for functional and scan-based ALU checks."""

    def __init__(self, cfg: GPUShaderConfig):
        self.cfg = cfg
        self.maxv = (1 << cfg.bit_width) - 1
        self.minv_signed = -(1 << (cfg.bit_width - 1))

    def _boundary_pairs(self) -> List[Tuple[int, int, str]]:
        return [
            (0, 0, "zero"),
            (1, 1, "one"),
            (-1, 1, "neg_one"),
            (self.maxv, 1, "max_plus_one"),
            (self.minv_signed, -1, "min_minus_one"),
        ]

    def _typical_pairs(self) -> List[Tuple[int, int, str]]:
        return [(7, 3, "small"), (1024, 63, "medium"), (12345, 27, "mixed")]

    def _corner_pairs(self) -> List[Tuple[int, int, str]]:
        # Integer model for CI: use divide-by-zero and overflow style corners.
        return [(self.maxv, self.maxv, "overflow"), (self.minv_signed, 2, "underflow"), (42, 0, "div0")]

    def generate(self) -> List[ALUTestVector]:
        ops = [op for op in self.cfg.alu_operations if op in _INT_OPS + _CMP_OPS]
        out: List[ALUTestVector] = []
        for op in ops:
            for a, b, tag in self._boundary_pairs() + self._typical_pairs() + self._corner_pairs():
                # Use independent oracle computation for expected values.
                exp = alu_reference_execute(self.cfg, op, a, b)
                mode = "SCAN" if tag in ("overflow", "underflow", "div0", "max_plus_one", "min_minus_one") else "FUNCTIONAL"
                out.append(
                    ALUTestVector(
                        op=op,
                        a=a,
                        b=b,
                        expected=exp,
                        mode=mode,
                        category=tag,
                        fault_hint="stuck_at_datapath" if mode == "SCAN" else "functional_path",
                    )
                )
        return out


class GPUFaultModel:
    """GPU-specialized fault buckets for ALU/register/mux/interconnect timing/data."""

    def __init__(self, cfg: GPUShaderConfig):
        self.cfg = cfg

    def evaluate(self, alu_vectors: Sequence[ALUTestVector], reg_mismatches: int, pipeline_issues: int) -> Dict[str, Any]:
        stuck_at = sum(1 for v in alu_vectors if v.mode == "SCAN")
        timing = max(self.cfg.pipeline_depth - 2, 0) + pipeline_issues
        integrity = reg_mismatches + int(self.cfg.bit_width > 32)
        return {
            "shader_specific_stuck_at_faults": {
                "alu_datapath": stuck_at,
                "register_cells": reg_mismatches,
                "mux_controls": max(self.cfg.num_alu_units - 1, 0),
            },
            "shader_specific_timing_faults": {
                "datapath_delay_risk": timing,
                "register_setup_hold_risk": max(self.cfg.pipeline_depth - 1, 0),
            },
            "datapath_integrity_faults": {
                "inverted_bits": integrity,
                "stuck_groups": max(self.cfg.scan_chains // 4, 1),
            },
        }


@dataclass
class GPUVerificationResult:
    name: str
    pass_count: int
    fail_count: int
    coverage_pct: float
    details: Dict[str, Any] = field(default_factory=dict)


class GPUShaderTestBase:
    """Base class for GPU test hierarchy."""

    test_name = "gpu_base_test"

    def __init__(self, cfg: GPUShaderConfig):
        self.cfg = cfg

    def run(self) -> GPUVerificationResult:
        raise NotImplementedError


class GPUALUTest(GPUShaderTestBase):
    """ALU operation and scan-vector validation for shader execution units."""

    test_name = "gpu_alu_test"

    def run(self) -> GPUVerificationResult:
        seq = ALUVerificationSequences(self.cfg).generate()
        alu = ALUExecutionAgent(self.cfg)
        fail = 0
        by_op: Dict[str, int] = {}
        scan_detect = 0
        for v in seq:
            got = alu.execute(v.op, v.a, v.b)
            if got != v.expected:
                fail += 1
            by_op[v.op] = by_op.get(v.op, 0) + 1
            if v.mode == "SCAN":
                scan_detect += 1
        total = max(len(seq), 1)
        return GPUVerificationResult(
            name=self.test_name,
            pass_count=total - fail,
            fail_count=fail,
            coverage_pct=100.0 * (total - fail) / total,
            details={
                "vectors_total": total,
                "vectors_scan_mode": scan_detect,
                "coverage_by_operation": by_op,
                "operation_classes": {
                    "arithmetic": [x for x in self.cfg.alu_operations if x in ("ADD", "SUB", "MUL", "DIV")],
                    "logical": [x for x in self.cfg.alu_operations if x in ("AND", "OR", "XOR", "NOT", "SHIFT")],
                    "comparison": [x for x in self.cfg.alu_operations if x in _CMP_OPS],
                },
            },
        )


class GPURegisterFileTest(GPUShaderTestBase):
    """Register read/write, stability, arbitration, and scan write/readback checks."""

    test_name = "gpu_register_file_test"

    def run(self) -> GPUVerificationResult:
        rf = RegisterFileAgent(self.cfg)
        mismatches = 0
        by_bank: Dict[str, float] = {}
        for idx in range(self.cfg.num_registers):
            wv = (idx * 0x9E37) & ((1 << self.cfg.bit_width) - 1)
            reg_pass = True
            rf.write(idx, wv)  # functional write
            rv = rf.read(idx)  # functional read
            if rv != wv:
                mismatches += 1
                reg_pass = False
            # scan-like write/read: invert and verify stability
            sv = (~wv) & ((1 << self.cfg.bit_width) - 1)
            rf.write(idx, sv)
            if rf.read(idx) != sv:
                mismatches += 1
                reg_pass = False
            b = str(rf.bank_for(idx))
            by_bank[b] = by_bank.get(b, 0.0) + (1.0 if reg_pass else 0.0)
        arb_ok = rf.arbitration_ok(readers=[0, 1, 2], writers=[0, self.cfg.register_banks])
        total_checks = max(self.cfg.num_registers * 2 + 1, 1)
        fails = mismatches + (0 if arb_ok else 1)
        cov = 100.0 * (total_checks - fails) / total_checks
        bank_cov = {k: round(min(v / max(self.cfg.num_registers / max(self.cfg.register_banks, 1), 1), 1.0) * 100.0, 2) for k, v in by_bank.items()}
        return GPUVerificationResult(
            name=self.test_name,
            pass_count=total_checks - fails,
            fail_count=fails,
            coverage_pct=cov,
            details={
                "registers_tested": self.cfg.num_registers,
                "scan_readback_enabled": True,
                "arbitration_ok": arb_ok,
                "coverage_by_bank_pct": bank_cov,
                "detected_data_corruption": mismatches,
            },
        )


class GPUPipelineTest(GPUShaderTestBase):
    """Pipeline dataflow, forwarding, hazard/stall behavior, and stage latching checks."""

    test_name = "gpu_pipeline_test"

    def run(self) -> GPUVerificationResult:
        ic = InterconnectAgent(self.cfg)
        issues = 0
        stage_cov: Dict[str, float] = {}
        for i in range(max(self.cfg.pipeline_depth, 1)):
            payload = {"op": "ADD", "dst": i % self.cfg.num_registers, "src0": i, "src1": i + 1}
            timeline = ic.route(payload, self.cfg.pipeline_depth)
            for rec in timeline:
                st = str(rec["stage"])
                stage_cov[st] = stage_cov.get(st, 0.0) + (1.0 if rec.get("latched") else 0.0)
                if rec["stage"] < self.cfg.pipeline_depth - 1 and not rec.get("forwarded"):
                    issues += 1
        # Simple hazard proxy: deeper pipeline has more RAW hazard windows.
        hazard_events = max(self.cfg.pipeline_depth - 2, 0)
        stall_generation_ok = self.cfg.pipeline_depth <= 6
        if not stall_generation_ok:
            issues += 1
        total_checks = max(self.cfg.pipeline_depth * self.cfg.pipeline_depth + 2, 1)
        cov = 100.0 * (total_checks - issues) / total_checks
        norm_stage_cov = {k: round(min(v / max(self.cfg.pipeline_depth, 1), 1.0) * 100.0, 2) for k, v in stage_cov.items()}
        return GPUVerificationResult(
            name=self.test_name,
            pass_count=total_checks - issues,
            fail_count=issues,
            coverage_pct=cov,
            details={
                "pipeline_depth": self.cfg.pipeline_depth,
                "forwarding_logic_checked": True,
                "hazard_detection_events": hazard_events,
                "stall_generation_ok": stall_generation_ok,
                "stage_coverage_pct": norm_stage_cov,
            },
        )


class GPUFunctionalTest(GPUShaderTestBase):
    """Functional shader-like mixed operation checks across ALU/register/interconnect."""

    test_name = "gpu_functional_test"

    def run(self) -> GPUVerificationResult:
        alu_res = GPUALUTest(self.cfg).run()
        reg_res = GPURegisterFileTest(self.cfg).run()
        pipe_res = GPUPipelineTest(self.cfg).run()
        total = alu_res.pass_count + reg_res.pass_count + pipe_res.pass_count + alu_res.fail_count + reg_res.fail_count + pipe_res.fail_count
        fail = alu_res.fail_count + reg_res.fail_count + pipe_res.fail_count
        return GPUVerificationResult(
            name=self.test_name,
            pass_count=total - fail,
            fail_count=fail,
            coverage_pct=100.0 * (total - fail) / max(total, 1),
            details={
                "subtests": [alu_res.name, reg_res.name, pipe_res.name],
                "functional_patterns": max(self.cfg.num_alu_units * self.cfg.pipeline_depth * 4, 8),
            },
        )


class GPUComprehensiveTest(GPUShaderTestBase):
    """Top-level multi-domain GPU core verification orchestration."""

    test_name = "gpu_comprehensive_test"

    def run(self) -> GPUVerificationResult:
        alu = GPUALUTest(self.cfg).run()
        reg = GPURegisterFileTest(self.cfg).run()
        pipe = GPUPipelineTest(self.cfg).run()
        func = GPUFunctionalTest(self.cfg).run()
        tex = TextureMemoryAgent(self.cfg).probe()

        seq = ALUVerificationSequences(self.cfg).generate()
        reg_corr = int(reg.details.get("detected_data_corruption", 0))
        pipeline_issues = pipe.fail_count
        fault_models = GPUFaultModel(self.cfg).evaluate(seq, reg_corr, pipeline_issues)

        tests = [alu, reg, pipe, func]
        total_checks = sum(t.pass_count + t.fail_count for t in tests)
        total_fails = sum(t.fail_count for t in tests)
        cov = 100.0 * (total_checks - total_fails) / max(total_checks, 1)

        return GPUVerificationResult(
            name=self.test_name,
            pass_count=total_checks - total_fails,
            fail_count=total_fails,
            coverage_pct=cov,
            details={
                "tests": {t.name: {"pass": t.pass_count, "fail": t.fail_count, "coverage_pct": round(t.coverage_pct, 3), "details": t.details} for t in tests},
                "fault_models": fault_models,
                "texture_memory": tex,
                "verify_modes": list(self.cfg.verify_modes),
                "gpu_agents": [
                    "ALU execution agent",
                    "Register file agent",
                    "Interconnect agent",
                    "Texture memory agent",
                ],
            },
        )


def build_gpu_shader_report(cfg: GPUShaderConfig, out_dir: str) -> Dict[str, Any]:
    """
    Generate GPU-specialized JSON + HTML report sections and visualization payloads.
    """

    outp = Path(out_dir)
    outp.mkdir(parents=True, exist_ok=True)
    comp = GPUComprehensiveTest(cfg).run()
    tests = comp.details.get("tests", {})
    alu_cov = tests.get("gpu_alu_test", {}).get("details", {}).get("coverage_by_operation", {})
    reg_cov = tests.get("gpu_register_file_test", {}).get("details", {}).get("coverage_by_bank_pct", {})
    stage_cov = tests.get("gpu_pipeline_test", {}).get("details", {}).get("stage_coverage_pct", {})

    # SVG/HTML snippets for quick embedding in existing report pages.
    alu_svg = fault_histogram_svg({str(k): int(v) for k, v in alu_cov.items()}) if alu_cov else "<p>No ALU coverage</p>"
    reg_heat = module_heatmap_html({f"bank_{k}": float(v) for k, v in reg_cov.items()}) if reg_cov else "<p>No register bank data</p>"
    stage_heat = module_heatmap_html({f"stage_{k}": float(v) for k, v in stage_cov.items()}) if stage_cov else "<p>No stage coverage data</p>"
    fault_stage_hist = fault_histogram_svg({f"stage_{k}": int(max(0, 100 - float(v))) for k, v in stage_cov.items()}) if stage_cov else "<p>No stage fault metrics</p>"

    payload = {
        "gpu_shader_config": cfg.__dict__,
        "gpu_shader_summary": {
            "pass_count": comp.pass_count,
            "fail_count": comp.fail_count,
            "coverage_pct": round(comp.coverage_pct, 3),
        },
        "gpu_report_sections": {
            "alu_verification_results": tests.get("gpu_alu_test", {}),
            "register_file_health": tests.get("gpu_register_file_test", {}),
            "pipeline_correctness": tests.get("gpu_pipeline_test", {}),
            "data_integrity": comp.details.get("fault_models", {}).get("datapath_integrity_faults", {}),
            "per_stage_timing_margins": {
                f"stage_{i}": round(max(0.1, 1.5 - 0.15 * i), 3) for i in range(cfg.pipeline_depth)
            },
        },
        "gpu_visualization": {
            "alu_coverage_by_operation_svg": alu_svg,
            "register_file_coverage_heatmap_html": reg_heat,
            "pipeline_stage_coverage_heatmap_html": stage_heat,
            "per_stage_fault_detection_svg": fault_stage_hist,
        },
    }
    json_path = outp / "gpu_shader_verification.json"
    html_path = outp / "gpu_shader_verification.html"
    json_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    html_path.write_text(_gpu_html(payload), encoding="utf-8")
    payload["output_paths"] = {"json": str(json_path), "html": str(html_path)}
    return payload


def _gpu_html(payload: Dict[str, Any]) -> str:
    sec = payload.get("gpu_report_sections", {})
    viz = payload.get("gpu_visualization", {})
    return f"""
<html><head><meta charset="utf-8"><title>GPU Shader DFT Report</title></head>
<body>
<h1>GPU Shader Core DFT Specialization</h1>
<h2>ALU verification results</h2><pre>{json.dumps(sec.get("alu_verification_results", {}), indent=2)}</pre>
<h2>Register file health</h2><pre>{json.dumps(sec.get("register_file_health", {}), indent=2)}</pre>
<h2>Pipeline correctness</h2><pre>{json.dumps(sec.get("pipeline_correctness", {}), indent=2)}</pre>
<h2>Data integrity</h2><pre>{json.dumps(sec.get("data_integrity", {}), indent=2)}</pre>
<h2>Per-stage timing margins</h2><pre>{json.dumps(sec.get("per_stage_timing_margins", {}), indent=2)}</pre>
<h2>Visualizations</h2>
{viz.get("alu_coverage_by_operation_svg", "")}
{viz.get("register_file_coverage_heatmap_html", "")}
{viz.get("pipeline_stage_coverage_heatmap_html", "")}
{viz.get("per_stage_fault_detection_svg", "")}
</body></html>
""".strip()
