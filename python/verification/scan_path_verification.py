"""
Scan chain path reachability: TDI to cells, cells to TDO (graph model).
"""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field
from typing import Any, Dict, List, Set


@dataclass
class ScanPathVerification:
    """
    ``chain`` is ordered list of cell names (SI chain order).
    ``cell_inputs`` maps cell -> source (``TDI`` or previous cell name).
    """

    chain: List[str] = field(default_factory=list)
    tdi_source: str = "TDI"
    tdo_sink: str = "TDO"

    def verify_linear_chain(self) -> Dict[str, Any]:
        unreachable: List[str] = []
        if not self.chain:
            return {
                "scan_path_ok": True,
                "tdi_reaches_all": True,
                "all_observable_at_tdo": True,
                "unreachable_cells": [],
                "chain_length": 0,
            }
        seen: Set[str] = set()
        for c in self.chain:
            if c in seen:
                unreachable.append(c)
            seen.add(c)
        return {
            "scan_path_ok": len(unreachable) == 0,
            "tdi_reaches_all": len(self.chain) == len(seen),
            "all_observable_at_tdo": True,
            "unreachable_cells": unreachable,
            "chain_length": len(self.chain),
        }

    def verify_graph(self, cells: List[str], edges: List[tuple]) -> Dict[str, Any]:
        """
        edges: (from_node, to_node) scan shift direction (data flows from -> to).
        Nodes include 'TDI' and 'TDO'.
        """
        adj: Dict[str, List[str]] = {c: [] for c in cells}
        adj[self.tdi_source] = []
        adj[self.tdo_sink] = []
        for a, b in edges:
            if a not in adj:
                adj[a] = []
            adj[a].append(b)
        reachable = self._bfs(self.tdi_source, adj)
        reverse = self._reverse_adj(adj)
        can_reach_tdo = self._bfs_reverse(self.tdo_sink, reverse)
        unr = [c for c in cells if c not in reachable]
        not_obs = [c for c in cells if c not in can_reach_tdo]
        return {
            "scan_path_coverage_report": True,
            "tdi_reaches_all": len(unr) == 0,
            "all_observable_at_tdo": len(not_obs) == 0,
            "unreachable_from_tdi": unr,
            "not_observable_at_tdo": not_obs,
        }

    @staticmethod
    def _bfs(start: str, adj: Dict[str, List[str]]) -> Set[str]:
        q = deque([start])
        seen = {start}
        while q:
            u = q.popleft()
            for v in adj.get(u, []):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        return seen

    @staticmethod
    def _reverse_adj(adj: Dict[str, List[str]]) -> Dict[str, List[str]]:
        rev: Dict[str, List[str]] = {}
        for u, vs in adj.items():
            for v in vs:
                rev.setdefault(v, []).append(u)
        return rev

    def _bfs_reverse(self, target: str, rev: Dict[str, List[str]]) -> Set[str]:
        q = deque([target])
        seen = {target}
        while q:
            u = q.popleft()
            for v in rev.get(u, []):
                if v not in seen:
                    seen.add(v)
                    q.append(v)
        return seen
