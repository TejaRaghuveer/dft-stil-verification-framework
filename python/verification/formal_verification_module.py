"""
Formal verification orchestration: SVA generation hooks, proof obligation export,
tool integration stubs (JasperGold / VC Formal / Symbiotic ESBMC — user toolchain).
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from .formal_config import FormalVerificationConfig
from .tap_fsm_reference import all_legal_edges, next_tap_state


@dataclass
class ProofObligation:
    property_id: str
    description: str
    status: str  # pending, proven, falsified, timeout, vacuous
    depth: int = 0
    witness: Optional[str] = None


@dataclass
class FormalVerificationModule:
    config: FormalVerificationConfig
    obligations: List[ProofObligation] = field(default_factory=list)

    def build_obligations(self) -> List[ProofObligation]:
        self.obligations.clear()
        for pid in self.config.properties_to_prove:
            self.obligations.append(
                ProofObligation(
                    property_id=pid,
                    description=_describe_property(pid),
                    status="pending",
                    depth=self.config.proof_depth,
                )
            )
        return self.obligations

    def export_transition_table_json(self, path: str) -> None:
        """Export TAP legal edges for formal tools / reviews."""
        data = {
            "tap_legal_edges": [
                {
                    "from": s.name,
                    "tms": tms,
                    "to": next_tap_state(s, tms).name,
                }
                for (s, tms), _ in sorted(
                    all_legal_edges().items(), key=lambda x: (x[0][0].value, x[0][1])
                )
            ]
        }
        Path(path).write_text(json.dumps(data, indent=2), encoding="utf-8")

    def generate_sva_shell(self, output_sv: str) -> None:
        """Emit a wrapper that instantiates jtag_tap_formal_props (see uvm_tb/assertions)."""
        p = Path(output_sv)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(
            "// Auto-generated — bind jtag_if instance in tb_top\n"
            "// jtag_tap_formal_props u_jtag_props(.*);\n"
            "`include \"jtag_tap_formal_sva.sv\"\n",
            encoding="utf-8",
        )

    def run_assertion_based_stub(self) -> Dict[str, Any]:
        """
        Placeholder: real runs invoke vendor CLI. Returns structured result for CI merge.
        """
        self.build_obligations()
        results = []
        for o in self.obligations:
            results.append(
                {
                    "property_id": o.property_id,
                    "status": "not_run",
                    "note": "Connect formal_verification.run to JasperGold/VC Formal script",
                }
            )
        return {
            "formal_engine": "stub",
            "timeout_sec": self.config.timeout_sec,
            "proof_depth": self.config.proof_depth,
            "results": results,
        }

    def fault_testability_certificate(
        self,
        module: str,
        testable_faults: List[str],
        untestable_faults: List[str],
        proof_refs: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Sign-off style bundle: claims + hashes (replace with tool-generated proof logs).
        """
        blob = json.dumps(
            {"module": module, "testable": sorted(testable_faults), "untestable": sorted(untestable_faults)},
            sort_keys=True,
        ).encode()
        digest = hashlib.sha256(blob).hexdigest()
        return {
            "certificate_type": "DFT_fault_testability_summary",
            "module": module,
            "testable_count": len(testable_faults),
            "untestable_count": len(untestable_faults),
            "content_sha256": digest,
            "proof_references": proof_refs or {},
            "disclaimer": "Not a mathematical proof until backed by formal tool output.",
        }

    def prove_untestable_stub(self, fault_id: str, reason: str) -> Dict[str, Any]:
        """Documentation hook: untestable faults require constrained proof or ATPG UTD report."""
        return {
            "fault_id": fault_id,
            "claimed_untestable": True,
            "reason": reason,
            "formal_status": "manual_review_required",
        }


def _describe_property(pid: str) -> str:
    m = {
        "tap_fsm": "All TAP transitions match IEEE 1149.1 TMS table",
        "tdo_validity": "TDO not unknown during Shift-DR/IR",
        "scan_path": "Scan chain SI/SO connectivity from TDI to TDO",
        "timing": "Setup/hold assumptions hold under clocking",
    }
    return m.get(pid, pid)


def generate_scan_connectivity_assertions(scan_cells: List[str]) -> List[str]:
    """Return SVA string fragments for ordered chain (user adapts to hierarchy)."""
    lines = []
    prev = "tdi_pad"
    for c in scan_cells:
        si = f"{c}_si"
        lines.append(f"// assume {si} connects to chain; use bind or hierarchical path")
        prev = f"{c}_so"
    lines.append(f"// last SO should mux to tdo in shift mode")
    return lines
