"""Core pattern debugger with breakpoints and replay."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class PatternVector:
    vector_index: int
    stimulus: Dict[str, str]
    expected: Dict[str, str] = field(default_factory=dict)
    comment: str = ""


@dataclass
class SignalSnapshot:
    vector_index: int
    values: Dict[str, str]


@dataclass
class Breakpoint:
    vector_index: Optional[int] = None
    break_on_fault_detect: bool = False
    signal_name: Optional[str] = None
    signal_value: Optional[str] = None


@dataclass
class DebugEvent:
    vector_index: int
    reason: str
    details: Dict[str, Any] = field(default_factory=dict)


class PatternDebugger:
    """Single-step execution abstraction for pattern vectors."""

    def __init__(self) -> None:
        self.vectors: List[PatternVector] = []
        self.snapshots: List[SignalSnapshot] = []
        self.events: List[DebugEvent] = []
        self.cursor: int = 0

    def load_vectors(self, vectors: List[PatternVector]) -> None:
        self.vectors = list(vectors)
        self.snapshots.clear()
        self.events.clear()
        self.cursor = 0

    def step(self, actual_values: Dict[str, str], fault_detected: bool = False) -> SignalSnapshot:
        if self.cursor >= len(self.vectors):
            raise IndexError("No more vectors")
        vec = self.vectors[self.cursor]
        snap = SignalSnapshot(vec.vector_index, dict(actual_values))
        self.snapshots.append(snap)
        if fault_detected:
            self.events.append(DebugEvent(vec.vector_index, "fault_detected"))
        self.cursor += 1
        return snap

    def run_until_breakpoint(
        self,
        observed_sequence: List[Dict[str, str]],
        breakpoints: List[Breakpoint],
        fault_flags: Optional[List[bool]] = None,
    ) -> Optional[DebugEvent]:
        for i, observed in enumerate(observed_sequence):
            fault = fault_flags[i] if fault_flags and i < len(fault_flags) else False
            snap = self.step(observed, fault_detected=fault)
            event = self._check_breakpoints(snap, breakpoints, fault)
            if event:
                self.events.append(event)
                return event
        return None

    @staticmethod
    def _check_breakpoints(
        snap: SignalSnapshot,
        breakpoints: List[Breakpoint],
        fault_detected: bool,
    ) -> Optional[DebugEvent]:
        for bp in breakpoints:
            if bp.vector_index is not None and bp.vector_index == snap.vector_index:
                return DebugEvent(snap.vector_index, "vector_breakpoint")
            if bp.break_on_fault_detect and fault_detected:
                return DebugEvent(snap.vector_index, "fault_breakpoint")
            if bp.signal_name and bp.signal_name in snap.values:
                if bp.signal_value is None or snap.values[bp.signal_name] == bp.signal_value:
                    return DebugEvent(
                        snap.vector_index,
                        "signal_breakpoint",
                        {"signal": bp.signal_name, "value": snap.values[bp.signal_name]},
                    )
        return None

    def transaction_history_replay(self) -> List[Dict[str, Any]]:
        return [
            {
                "vector_index": s.vector_index,
                "values": s.values,
            }
            for s in self.snapshots
        ]
