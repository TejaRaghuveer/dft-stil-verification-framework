"""
Multi-domain test execution: domains, TAM/shared access, conflict resolution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple


class ExecutionMode(str, Enum):
    SINGLE_DOMAIN = "single_domain"
    MULTI_DOMAIN = "multi_domain"


@dataclass
class ResourceClaim:
    resource_id: str
    bandwidth_units: int = 1


@dataclass
class TestDomain:
    domain_id: str
    name: str
    clock_domain: str = "default"
    submodule_path: str = ""
    resources: List[ResourceClaim] = field(default_factory=list)
    conflicts_with_domain_ids: Set[str] = field(default_factory=set)
    tam_shared: bool = True


@dataclass
class TestDomainManager:
    domains: Dict[str, TestDomain] = field(default_factory=dict)
    mode: ExecutionMode = ExecutionMode.MULTI_DOMAIN
    active_domain_id: Optional[str] = None

    def register_domain(self, domain: TestDomain) -> None:
        self.domains[domain.domain_id] = domain

    def set_mode(self, mode: ExecutionMode, primary_domain_id: Optional[str] = None) -> None:
        self.mode = mode
        self.active_domain_id = primary_domain_id

    def domains_for_parallel_run(self) -> List[List[str]]:
        ids = list(self.domains.keys())
        resource_users: Dict[str, Set[str]] = {}
        for did, d in self.domains.items():
            for r in d.resources:
                resource_users.setdefault(r.resource_id, set()).add(did)
        conflicts: Dict[str, Set[str]] = {i: set() for i in ids}
        for users in resource_users.values():
            if len(users) < 2:
                continue
            for a in users:
                for b in users:
                    if a != b:
                        conflicts[a].add(b)
        for did, d in self.domains.items():
            for other in d.conflicts_with_domain_ids:
                if other in self.domains:
                    conflicts[did].add(other)
                    conflicts[other].add(did)
        color: Dict[str, int] = {}
        for did in sorted(ids):
            used = {color.get(nb, -1) for nb in conflicts[did] if nb in color}
            c = 0
            while c in used:
                c += 1
            color[did] = c
        max_c = max(color.values(), default=0)
        groups: List[List[str]] = [[] for _ in range(max_c + 1)]
        for did, c in color.items():
            groups[c].append(did)
        return [g for g in groups if g]

    def assert_tam_access(self, domain_id: str, tam_slice: Tuple[int, int]) -> Tuple[bool, str]:
        if domain_id not in self.domains:
            return False, "unknown domain"
        return True, "ok"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "mode": self.mode.value,
            "active_domain_id": self.active_domain_id,
            "domains": {
                k: {
                    "name": v.name,
                    "clock_domain": v.clock_domain,
                    "submodule_path": v.submodule_path,
                    "resources": [{"id": r.resource_id, "units": r.bandwidth_units} for r in v.resources],
                    "conflicts_with": sorted(v.conflicts_with_domain_ids),
                }
                for k, v in self.domains.items()
            },
            "parallel_groups": self.domains_for_parallel_run(),
        }
