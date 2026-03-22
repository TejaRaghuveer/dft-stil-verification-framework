"""
CLI demo: load constraints, run timing report.

  python -m timing
  python -m timing path/to/constraints.yaml
"""

from __future__ import annotations

import json
import sys

from .timing_config import load_timing_config_from_dict, load_timing_config_from_yaml
from .timing_execution import PatternTimingProfile, build_full_timing_report


def main() -> None:
    if len(sys.argv) > 1:
        cfg = load_timing_config_from_yaml(sys.argv[1])
    else:
        cfg = load_timing_config_from_dict(
            {
                "tck_frequency_mhz": 200,
                "system_clock_mhz": 400,
                "setup_time_ns": 0.5,
                "hold_time_ns": 0.3,
                "propagation_delay_ns": 1.5,
                "clock_domains": {
                    "tclock": "200 MHz",
                    "sysclock": "400 MHz",
                    "ratio": "1:2",
                    "phase_offset_ns": 0,
                },
            }
        )
    profiles = [
        PatternTimingProfile("p1", "transition_delay", estimated_path_depth=3),
        PatternTimingProfile("p2", "path_delay", estimated_path_depth=8),
        PatternTimingProfile("p3", "stuck_at", estimated_path_depth=1),
    ]
    report = build_full_timing_report(cfg, profiles, tck_sweep=[50, 100, 200, 400])
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
