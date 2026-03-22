"""
Timing configuration for at-speed pattern execution and margin analysis.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ClockDomainSpec:
    """One clock domain with optional relationship to others."""

    name: str
    frequency_mhz: float
    phase_offset_ns: float = 0.0
    slew_rate_v_per_ns: Optional[float] = None  # optional; None = inherit default


@dataclass
class MultiDomainRelationship:
    """Explicit ratio and phase between two named domains (e.g. TCK vs system)."""

    domain_a: str
    domain_b: str
    ratio_a_to_b: Tuple[int, int]  # e.g. (1, 2) means f_b = 2 * f_a
    phase_offset_ns: float = 0.0


@dataclass
class TimingConfig:
    """
    Complete timing picture for scan/at-speed analysis (model-level, not SDF back-annotation).
    """

    tck_frequency_mhz: float = 10.0
    system_clock_mhz: float = 100.0
    setup_time_ns: float = 0.5
    hold_time_ns: float = 0.3
    propagation_delay_comb_ns: float = 1.0
    propagation_delay_seq_ns: float = 0.8
    clock_slew_rate_v_per_ns: float = 1.0
    data_slew_rate_v_per_ns: float = 0.8
    clock_to_output_delay_ns: float = 1.2
    domains: List[ClockDomainSpec] = field(default_factory=list)
    relationships: List[MultiDomainRelationship] = field(default_factory=list)
    metastability_window_ns: float = 0.05  # simplified async CDC window

    def tck_period_ns(self) -> float:
        if self.tck_frequency_mhz <= 0:
            raise ValueError("tck_frequency_mhz must be positive")
        return 1000.0 / self.tck_frequency_mhz

    def system_period_ns(self) -> float:
        if self.system_clock_mhz <= 0:
            raise ValueError("system_clock_mhz must be positive")
        return 1000.0 / self.system_clock_mhz


def _parse_ratio(s: str) -> Tuple[int, int]:
    parts = s.replace(" ", "").split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid ratio: {s}")
    return int(parts[0]), int(parts[1])


def load_timing_config_from_dict(data: Dict[str, Any]) -> TimingConfig:
    """
    Load from a dict (JSON/YAML-compatible).

    Example keys:
      tck_frequency_mhz, system_clock_mhz, setup_time_ns, hold_time_ns,
      propagation_delay_ns (applies to comb if seq not set),
      propagation_delay_comb_ns, propagation_delay_seq_ns,
      clock_slew_rate_v_per_ns, data_slew_rate_v_per_ns,
      clock_to_output_delay_ns, metastability_window_ns,
      clock_domains: { tclock: "200 MHz", sysclock: "400 MHz", ratio: "1:2", phase_offset_ns: 0 }
    """
    comb = float(data.get("propagation_delay_comb_ns", data.get("propagation_delay_ns", 1.0)))
    seq = float(data.get("propagation_delay_seq_ns", comb * 0.8))

    domains: List[ClockDomainSpec] = []
    rels: List[MultiDomainRelationship] = []

    t_mhz: Optional[float] = _freq_from_value(data.get("tck_frequency_mhz"))
    s_mhz: Optional[float] = _freq_from_value(data.get("system_clock_mhz"))

    cd = data.get("clock_domains") or {}
    if isinstance(cd, dict):
        t_mhz = _freq_from_value(cd.get("tclock") or cd.get("tck") or t_mhz)
        s_mhz = _freq_from_value(cd.get("sysclock") or cd.get("system") or s_mhz)
        if t_mhz:
            domains.append(ClockDomainSpec("tclock", t_mhz))
        if s_mhz:
            domains.append(ClockDomainSpec("sysclock", s_mhz))
        ratio_s = cd.get("ratio") or cd.get("frequency_ratio")
        phase = float(cd.get("phase_offset_ns", cd.get("phase_offset", 0)))
        if ratio_s and t_mhz and s_mhz:
            ra, rb = _parse_ratio(str(ratio_s))
            rels.append(
                MultiDomainRelationship("tclock", "sysclock", (ra, rb), phase_offset_ns=phase)
            )
        for k, v in cd.items():
            if k in ("tclock", "sysclock", "tck", "system", "ratio", "frequency_ratio", "phase_offset", "phase_offset_ns"):
                continue
            if isinstance(v, (int, float)):
                domains.append(ClockDomainSpec(k, float(v)))
            elif isinstance(v, str) and "MHz" in v:
                domains.append(ClockDomainSpec(k, _freq_from_value(v) or 0.0))

    return TimingConfig(
        tck_frequency_mhz=float(data.get("tck_frequency_mhz", (t_mhz if t_mhz is not None else 10.0))),
        system_clock_mhz=float(data.get("system_clock_mhz", (s_mhz if s_mhz is not None else 100.0))),
        setup_time_ns=float(data.get("setup_time_ns", 0.5)),
        hold_time_ns=float(data.get("hold_time_ns", 0.3)),
        propagation_delay_comb_ns=comb,
        propagation_delay_seq_ns=float(data.get("propagation_delay_seq_ns", seq)),
        clock_slew_rate_v_per_ns=float(data.get("clock_slew_rate_v_per_ns", 1.0)),
        data_slew_rate_v_per_ns=float(data.get("data_slew_rate_v_per_ns", 0.8)),
        clock_to_output_delay_ns=float(data.get("clock_to_output_delay_ns", comb + 0.2)),
        domains=domains or [
            ClockDomainSpec("tclock", float(data.get("tck_frequency_mhz", 10.0))),
            ClockDomainSpec("sysclock", float(data.get("system_clock_mhz", 100.0))),
        ],
        relationships=rels,
        metastability_window_ns=float(data.get("metastability_window_ns", 0.05)),
    )


def _freq_from_value(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip()
    s = s.replace("MHz", "").replace("mhz", "").strip()
    try:
        return float(s)
    except ValueError:
        return None


def load_timing_config_from_yaml(path: str) -> TimingConfig:
    try:
        import yaml  # type: ignore
    except ImportError as e:
        raise ImportError("Install PyYAML for load_timing_config_from_yaml: pip install pyyaml") from e
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    if not isinstance(data, dict):
        raise ValueError("YAML root must be a mapping")
    # Allow top-level timing_constraints: { ... }
    if "timing_constraints" in data and isinstance(data["timing_constraints"], dict):
        data = {**data, **data["timing_constraints"]}
    return load_timing_config_from_dict(data)
