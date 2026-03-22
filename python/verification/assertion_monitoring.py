"""
Merge assertion failures with pattern / vector context from simulation logs or JSONL.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class AssertionFailureRecord:
    time_ns: float
    assertion_name: str
    message: str
    pattern_id: str = ""
    vector_index: int = -1
    protocol_ref: str = ""  # e.g. IEEE 1149.1 shift
    timing_ref: str = ""


@dataclass
class AssertionMonitorReport:
    failures: List[AssertionFailureRecord] = field(default_factory=list)

    def add_from_dict(self, row: Dict[str, Any]) -> None:
        self.failures.append(
            AssertionFailureRecord(
                time_ns=float(row.get("time_ns", 0)),
                assertion_name=str(row.get("assertion", row.get("name", ""))),
                message=str(row.get("message", "")),
                pattern_id=str(row.get("pattern_id", "")),
                vector_index=int(row.get("vector", row.get("vector_index", -1))),
                protocol_ref=str(row.get("protocol_ref", "")),
                timing_ref=str(row.get("timing_ref", "")),
            )
        )

    def load_jsonl(self, path: str) -> None:
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            self.add_from_dict(json.loads(line))

    def report(self) -> Dict[str, Any]:
        return {
            "assertion_failure_report": True,
            "count": len(self.failures),
            "failures": [
                {
                    "time_ns": f.time_ns,
                    "assertion": f.assertion_name,
                    "message": f.message,
                    "pattern_id": f.pattern_id,
                    "vector_index": f.vector_index,
                    "protocol_ref": f.protocol_ref,
                    "timing_ref": f.timing_ref,
                }
                for f in self.failures
            ],
        }
