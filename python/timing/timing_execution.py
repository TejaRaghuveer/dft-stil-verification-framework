"""
At-speed execution modeling, edge optimization, violation detection, multi-domain sequencing,
and operational frequency capability analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Tuple

from .timing_config import TimingConfig


class CaptureEdge(str, Enum):
    LEADING = "leading"
    TRAILING = "trailing"
    BOTH = "both"


@dataclass
class PatternTimingProfile:
    """Per-pattern sensitivity used by optimizers (higher = more timing-critical)."""

    pattern_id: str
    pattern_type: Literal["stuck_at", "transition_delay", "path_delay", "unknown"] = "unknown"
    estimated_path_depth: int = 1
    launch_capture_separation_cycles: int = 1
    notes: str = ""


@dataclass
class ExecutionStepResult:
    pattern_id: str
    capture_edge: CaptureEdge
    passed_functional: bool
    setup_margin_ns: float
    hold_margin_ns: float
    metastability_risk: float  # 0..1 simplified
    clock_to_output_budget_ns: float


@dataclass
class TimingViolation:
    pattern_id: str
    kind: str  # setup, hold, metastability, cdc
    detail: str
    suggested_remedy: str


@dataclass
class AtSpeedExecutionEngine:
    """
    Model pattern execution at operational (at-speed) conditions vs relaxed scan shift.

    This is an analytical engine: it does not drive RTL. Use margins from TimingConfig
    and per-pattern profiles to estimate pass/fail and violations.
    """

    config: TimingConfig
    capture_edge_default: CaptureEdge = CaptureEdge.TRAILING

    def effective_capture_period_ns(self, use_system_clk: bool = True) -> float:
        return self.config.system_period_ns() if use_system_clk else self.config.tck_period_ns()

    def compute_margins(
        self,
        data_arrival_ns: float,
        clock_edge_ns: float,
        capture_edge: CaptureEdge,
    ) -> Tuple[float, float]:
        """
        Return (setup_margin_ns, hold_margin_ns) relative to ideal sampling window.
        Simplified: arrival vs edge with setup/hold requirements from config.
        For BOTH, returns the worst (minimum) setup and hold slacks across edges.
        """
        period = self.config.system_period_ns()

        def one_edge(use_leading: bool) -> Tuple[float, float]:
            if use_leading:
                edge = clock_edge_ns % period
            else:
                edge = (clock_edge_ns + period / 2) % period
            setup_slack = edge - data_arrival_ns - self.config.setup_time_ns
            hold_slack = (
                data_arrival_ns + self.config.propagation_delay_comb_ns - edge - self.config.hold_time_ns
            )
            return setup_slack, hold_slack

        if capture_edge == CaptureEdge.LEADING:
            return one_edge(True)
        if capture_edge == CaptureEdge.TRAILING:
            return one_edge(False)
        s1, h1 = one_edge(True)
        s2, h2 = one_edge(False)
        return min(s1, s2), min(h1, h2)

    def execute_pattern(
        self,
        profile: PatternTimingProfile,
        capture_edge: Optional[CaptureEdge] = None,
        data_arrival_ns: Optional[float] = None,
        clock_edge_ns: float = 0.0,
    ) -> ExecutionStepResult:
        ce = capture_edge or self.capture_edge_default
        if data_arrival_ns is None:
            data_arrival_ns = (
                profile.estimated_path_depth * self.config.propagation_delay_comb_ns
                + self.config.clock_to_output_delay_ns * 0.5
            )
        setup_m, hold_m = self.compute_margins(data_arrival_ns, clock_edge_ns, ce)
        period = self.config.system_period_ns()
        meta = max(
            0.0,
            min(
                1.0,
                self.config.metastability_window_ns / max(period * 0.01, 1e-6),
            ),
        )
        co_budget = period - self.config.clock_to_output_delay_ns - self.config.setup_time_ns
        passed = setup_m >= 0 and hold_m >= 0
        return ExecutionStepResult(
            pattern_id=profile.pattern_id,
            capture_edge=ce,
            passed_functional=passed,
            setup_margin_ns=setup_m,
            hold_margin_ns=hold_m,
            metastability_risk=meta,
            clock_to_output_budget_ns=co_budget,
        )


@dataclass
class EdgeSelectionOptimizer:
    """
    Choose capture edge / timing to maximize fault detection likelihood for TDF vs path delay.
    """

    engine: AtSpeedExecutionEngine

    def score_edge(self, profile: PatternTimingProfile, edge: CaptureEdge) -> float:
        r = self.engine.execute_pattern(profile, capture_edge=edge)
        # Higher score = better for detection: need positive margins but stress path
        margin_term = min(r.setup_margin_ns, r.hold_margin_ns)
        stress = profile.estimated_path_depth * 0.1
        if profile.pattern_type == "transition_delay":
            # Prefer edge that minimizes slack slightly (detect slow transitions) while >= 0
            return stress - abs(min(margin_term, 0)) * 10 + (1.0 if margin_term > 0 else -5)
        if profile.pattern_type == "path_delay":
            return margin_term * 0.5 + stress * 2.0 - r.metastability_risk
        return margin_term - r.metastability_risk

    def recommend(self, profile: PatternTimingProfile) -> Tuple[CaptureEdge, Dict[str, Any]]:
        scores = {e: self.score_edge(profile, e) for e in (CaptureEdge.LEADING, CaptureEdge.TRAILING)}
        best = max(scores, key=scores.get)  # type: ignore
        report = {
            "pattern_id": profile.pattern_id,
            "pattern_type": profile.pattern_type,
            "scores": {k.value: v for k, v in scores.items()},
            "recommended_edge": best.value,
            "timing_sensitivity": profile.estimated_path_depth / max(
                self.engine.config.system_period_ns(), 1e-6
            ),
        }
        return best, report


@dataclass
class TimingViolationDetector:
    """Monitor margins during modeled execution; produce reports and remedies."""

    engine: AtSpeedExecutionEngine
    violations: List[TimingViolation] = field(default_factory=list)

    def clear(self) -> None:
        self.violations.clear()

    def check(self, result: ExecutionStepResult) -> List[TimingViolation]:
        found: List[TimingViolation] = []
        if result.setup_margin_ns < 0:
            found.append(
                TimingViolation(
                    result.pattern_id,
                    "setup",
                    f"setup slack {result.setup_margin_ns:.3f} ns",
                    "Reduce TCK/system frequency, shorten paths, or use trailing capture edge",
                )
            )
        if result.hold_margin_ns < 0:
            found.append(
                TimingViolation(
                    result.pattern_id,
                    "hold",
                    f"hold slack {result.hold_margin_ns:.3f} ns",
                    "Insert delay cells, relax launch/capture, or slow scan/capture clock",
                )
            )
        if result.metastability_risk > 0.5:
            found.append(
                TimingViolation(
                    result.pattern_id,
                    "metastability",
                    f"estimated metastability risk {result.metastability_risk:.2f}",
                    "Synchronize CDC paths; align domain phases; avoid capturing async data",
                )
            )
        self.violations.extend(found)
        return found

    def report_dict(self) -> Dict[str, Any]:
        return {
            "violation_count": len(self.violations),
            "violations": [
                {
                    "pattern_id": v.pattern_id,
                    "kind": v.kind,
                    "detail": v.detail,
                    "remedy": v.suggested_remedy,
                }
                for v in self.violations
            ],
        }


@dataclass
class ClockEvent:
    domain: str
    time_ns: float
    edge: Literal["rise", "fall"]


@dataclass
class MultiDomainClockSequencer:
    """
    Schedule aligned edges across TCK, system_clk, and optional domains.
    Flags potential CDC issues when unrelated phases cross.
    """

    config: TimingConfig

    def schedule_window(self, duration_ns: float) -> List[ClockEvent]:
        """Emit rising/falling edges for TCK and system clock over [0, duration_ns]."""
        events: List[ClockEvent] = []
        t_period = self.config.tck_period_ns()
        s_period = self.config.system_period_ns()
        phase = 0.0
        for rel in self.config.relationships:
            if rel.domain_a == "tclock" and rel.domain_b == "sysclock":
                phase = rel.phase_offset_ns
        t_ns = 0.0
        while t_ns <= duration_ns:
            events.append(ClockEvent("tclock", t_ns, "rise"))
            events.append(ClockEvent("tclock", t_ns + t_period / 2, "fall"))
            t_ns += t_period
        t_ns = phase
        while t_ns <= duration_ns:
            events.append(ClockEvent("sysclock", t_ns, "rise"))
            events.append(ClockEvent("sysclock", t_ns + s_period / 2, "fall"))
            t_ns += s_period
        events.sort(key=lambda e: (e.time_ns, e.domain))
        return events

    def cdc_safe(self, launch_domain: str, capture_domain: str, setup_margin_ns: float) -> Tuple[bool, str]:
        if launch_domain == capture_domain:
            return True, "same domain"
        if setup_margin_ns < self.config.setup_time_ns:
            return False, "insufficient margin for CDC sampling"
        return True, "margins OK for modeled CDC (still verify synchronizers in RTL)"


@dataclass
class OperationalSpeedAnalyzer:
    """
    Sweep TCK (and optionally system) frequency to build coverage-vs-frequency capability curve.
    """

    base_config: TimingConfig

    def capability_curve(
        self,
        profiles: List[PatternTimingProfile],
        tck_mhz_list: List[float],
    ) -> Dict[str, Any]:
        curves: Dict[str, List[Dict[str, Any]]] = {}
        reduced_only: List[str] = []
        ordered = sorted(tck_mhz_list)
        if not ordered:
            return {
                "tck_sweep_mhz": [],
                "curve": [],
                "patterns_reduced_speed_only": [],
                "design_timing_headroom": self._headroom_report(profiles),
                "sweep_skipped_reason": "tck_mhz_list is empty; no min/max TCK comparison",
            }
        for tck in ordered:
            cfg = TimingConfig(
                tck_frequency_mhz=tck,
                system_clock_mhz=self.base_config.system_clock_mhz,
                setup_time_ns=self.base_config.setup_time_ns,
                hold_time_ns=self.base_config.hold_time_ns,
                propagation_delay_comb_ns=self.base_config.propagation_delay_comb_ns,
                propagation_delay_seq_ns=self.base_config.propagation_delay_seq_ns,
                clock_slew_rate_v_per_ns=self.base_config.clock_slew_rate_v_per_ns,
                data_slew_rate_v_per_ns=self.base_config.data_slew_rate_v_per_ns,
                clock_to_output_delay_ns=self.base_config.clock_to_output_delay_ns,
                domains=self.base_config.domains,
                relationships=self.base_config.relationships,
                metastability_window_ns=self.base_config.metastability_window_ns,
            )
            eng = AtSpeedExecutionEngine(cfg)
            det = TimingViolationDetector(eng)
            passed = 0
            for p in profiles:
                res = eng.execute_pattern(p)
                v = det.check(res)
                if not v and res.passed_functional:
                    passed += 1
            frac = passed / max(len(profiles), 1)
            curves.setdefault("points", []).append({"tck_mhz": tck, "pass_fraction": frac})
        # Patterns that fail at max TCK but pass at min
        hi = ordered[-1]
        lo = ordered[0]
        for p in profiles:
            c_hi = self._with_tck(self.base_config, hi)
            c_lo = self._with_tck(self.base_config, lo)
            r_hi = AtSpeedExecutionEngine(c_hi).execute_pattern(p)
            r_lo = AtSpeedExecutionEngine(c_lo).execute_pattern(p)
            if not r_hi.passed_functional and r_lo.passed_functional:
                reduced_only.append(p.pattern_id)

        headroom = self._headroom_report(profiles)

        return {
            "tck_sweep_mhz": ordered,
            "curve": curves.get("points", []),
            "patterns_reduced_speed_only": reduced_only,
            "design_timing_headroom": headroom,
        }

    @staticmethod
    def _with_tck(base: TimingConfig, tck_mhz: float) -> TimingConfig:
        return TimingConfig(
            tck_frequency_mhz=tck_mhz,
            system_clock_mhz=base.system_clock_mhz,
            setup_time_ns=base.setup_time_ns,
            hold_time_ns=base.hold_time_ns,
            propagation_delay_comb_ns=base.propagation_delay_comb_ns,
            propagation_delay_seq_ns=base.propagation_delay_seq_ns,
            clock_slew_rate_v_per_ns=base.clock_slew_rate_v_per_ns,
            data_slew_rate_v_per_ns=base.data_slew_rate_v_per_ns,
            clock_to_output_delay_ns=base.clock_to_output_delay_ns,
            domains=base.domains,
            relationships=base.relationships,
            metastability_window_ns=base.metastability_window_ns,
        )

    def _headroom_report(self, profiles: List[PatternTimingProfile]) -> Dict[str, Any]:
        eng = AtSpeedExecutionEngine(self.base_config)
        margins = []
        for p in profiles:
            r = eng.execute_pattern(p)
            margins.append(min(r.setup_margin_ns, r.hold_margin_ns))
        worst = min(margins) if margins else 0.0
        return {
            "worst_min_margin_ns": worst,
            "recommended_max_tck_mhz_note": "Increase TCK until worst margin approaches 0; "
            "validate with SDF-annotated sim or STA.",
        }


def build_full_timing_report(
    config: TimingConfig,
    profiles: List[PatternTimingProfile],
    tck_sweep: Optional[List[float]] = None,
) -> Dict[str, Any]:
    """Aggregate execution results, violations, edge recommendations, and capability curve."""
    engine = AtSpeedExecutionEngine(config)
    detector = TimingViolationDetector(engine)
    optimizer = EdgeSelectionOptimizer(engine)
    sequencer = MultiDomainClockSequencer(config)
    exec_rows: List[Dict[str, Any]] = []
    edge_reports: List[Dict[str, Any]] = []
    for p in profiles:
        res = engine.execute_pattern(p)
        detector.check(res)
        _, er = optimizer.recommend(p)
        edge_reports.append(er)
        exec_rows.append(
            {
                "pattern_id": p.pattern_id,
                "passed": res.passed_functional,
                "setup_margin_ns": res.setup_margin_ns,
                "hold_margin_ns": res.hold_margin_ns,
                "capture_edge_used": res.capture_edge.value,
                "metastability_risk": res.metastability_risk,
            }
        )
    if tck_sweep is None:
        sweep = [config.tck_frequency_mhz * f for f in (0.25, 0.5, 1.0, 1.5)]
    else:
        sweep = list(tck_sweep)
    analyzer = OperationalSpeedAnalyzer(config)
    curve = analyzer.capability_curve(profiles, sorted(set(sweep)))
    return {
        "timing_config_summary": {
            "tck_mhz": config.tck_frequency_mhz,
            "system_mhz": config.system_clock_mhz,
            "setup_ns": config.setup_time_ns,
            "hold_ns": config.hold_time_ns,
        },
        "pattern_results": exec_rows,
        "edge_selection": edge_reports,
        "violations": detector.report_dict(),
        "multi_domain_sample_events": [
            {"domain": e.domain, "time_ns": e.time_ns, "edge": e.edge}
            for e in sequencer.schedule_window(min(50.0, config.tck_period_ns() * 8))
        ][:40],
        "operational_analysis": curve,
        "recommendations": _recommendations(config, detector, curve),
    }


def _recommendations(
    config: TimingConfig,
    detector: TimingViolationDetector,
    curve: Dict[str, Any],
) -> List[str]:
    rec: List[str] = []
    if detector.violations:
        rec.append("Address timing violations before signing off at-speed patterns.")
    if curve.get("patterns_reduced_speed_only"):
        rec.append(
            f"Review patterns only passing at reduced TCK: {curve['patterns_reduced_speed_only']}"
        )
    rec.append(
        f"Operational frequency starting point: TCK={config.tck_frequency_mhz} MHz with "
        f"system={config.system_clock_mhz} MHz; tighten only after STA correlation."
    )
    return rec
