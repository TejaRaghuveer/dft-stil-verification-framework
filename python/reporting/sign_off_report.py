"""Formal sign-off document structure and traceability."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List


@dataclass
class SignOffReport:
    design_name: str
    coverage_target_pct: float = 95.0
    achieved_fault_coverage_pct: float = 0.0
    open_issues: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    traceability: List[Dict[str, str]] = field(default_factory=list)
    approvals: Dict[str, bool] = field(
        default_factory=lambda: {
            "design_review": False,
            "test_engineering": False,
            "manufacturing": False,
            "quality_assurance": False,
        }
    )

    def certify_targets_met(self) -> bool:
        """Coverage target met; open issues listed separately for waivers."""
        return self.achieved_fault_coverage_pct >= self.coverage_target_pct

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sign_off": True,
            "design": self.design_name,
            "date": datetime.now().isoformat(),
            "coverage_target_pct": self.coverage_target_pct,
            "achieved_fault_coverage_pct": self.achieved_fault_coverage_pct,
            "targets_met": self.certify_targets_met(),
            "open_issues": list(self.open_issues),
            "recommendations": list(self.recommendations),
            "traceability_pattern_fault_location": list(self.traceability),
            "approvals": dict(self.approvals),
        }

    def to_markdown(self) -> str:
        d = self.to_dict()
        lines = [
            "# DFT Verification Sign-Off",
            "",
            "| Field | Value |",
            "|---|---|",
            "| Design | %s |" % self.design_name,
            "| Achieved FC | %.2f%% |" % self.achieved_fault_coverage_pct,
            "| Target | %.2f%% |" % self.coverage_target_pct,
            "| Targets met | %s |" % str(d["targets_met"]),
            "",
            "## Open issues",
        ]
        lines.extend("- %s" % x for x in self.open_issues or ["None"])
        lines.extend(["", "## Traceability (sample)", ""])
        for t in self.traceability[:20]:
            lines.append("- Pattern `%s` -> Fault `%s` @ `%s`" % (t.get("pattern", ""), t.get("fault", ""), t.get("location", "")))
        lines.extend(["", "## Approvals", ""])
        for k, v in self.approvals.items():
            lines.append("- [x] %s" % k if v else "- [ ] %s" % k)
        return "\n".join(lines)
