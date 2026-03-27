"""Manual fault injection model and detection proof stub."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List


@dataclass
class InjectedFault:
    fault_id: str
    location: str
    fault_type: str
    forced_value: str


class FaultInjectionDebugger:
    def inject(self, signal_values: Dict[str, str], fault: InjectedFault) -> Dict[str, str]:
        out = dict(signal_values)
        out[fault.location] = fault.forced_value
        return out

    def detection_proof(
        self,
        pattern_name: str,
        fault: InjectedFault,
        expected_detect: bool,
        observed_detect: bool,
    ) -> Dict[str, Any]:
        return {
            "pattern": pattern_name,
            "fault_id": fault.fault_id,
            "location": fault.location,
            "fault_type": fault.fault_type,
            "expected_detect": expected_detect,
            "observed_detect": observed_detect,
            "proof": "PASS" if expected_detect == observed_detect else "FAIL",
        }
