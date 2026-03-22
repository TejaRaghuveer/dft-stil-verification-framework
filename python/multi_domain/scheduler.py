"""
Domain test scheduler: parallel groups, TAM/channel allocation, makespan estimate.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

from .domain_manager import TestDomainManager


@dataclass
class ScheduledTest:
    domain_id: str
    test_name: str
    estimated_seconds: float
    tam_channels: int = 1
    parallel_group: int = 0
    start_offset_sec: float = 0.0


@dataclass
class DomainTestScheduler:
    manager: TestDomainManager
    schedule: List[ScheduledTest] = field(default_factory=list)

    def add_test(self, domain_id: str, test_name: str, estimated_seconds: float, tam_channels: int = 1) -> None:
        self.schedule.append(
            ScheduledTest(
                domain_id=domain_id,
                test_name=test_name,
                estimated_seconds=estimated_seconds,
                tam_channels=tam_channels,
            )
        )

    def build(self) -> Dict[str, Any]:
        groups = self.manager.domains_for_parallel_run()
        domain_to_group = {}
        for gi, g in enumerate(groups):
            for did in g:
                domain_to_group[did] = gi
        by_group: Dict[int, List[ScheduledTest]] = {}
        for s in self.schedule:
            g = domain_to_group.get(s.domain_id, 0)
            s.parallel_group = g
            by_group.setdefault(g, []).append(s)
        for tests in by_group.values():
            tests.sort(key=lambda t: -t.estimated_seconds)
        group_span: Dict[int, float] = {}
        for g, tests in by_group.items():
            group_span[g] = max((t.estimated_seconds for t in tests), default=0.0)
        total_serial = sum(group_span.get(i, 0) for i in range(len(groups)))
        alloc: List[Dict[str, Any]] = []
        offset = 0.0
        for gi in range(len(groups)):
            span = group_span.get(gi, 0.0)
            for t in by_group.get(gi, []):
                alloc.append(
                    {
                        "domain_id": t.domain_id,
                        "test": t.test_name,
                        "parallel_group": gi,
                        "tam_channels": t.tam_channels,
                        "duration_sec": t.estimated_seconds,
                        "group_window_start_sec": offset,
                        "group_window_end_sec": offset + span,
                    }
                )
            offset += span
        return {
            "execution_mode": self.manager.mode.value,
            "parallel_domain_groups": groups,
            "estimated_total_seconds": total_serial,
            "allocations": alloc,
        }
