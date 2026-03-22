"""Demo: protocol trace + DRC + formal stub."""

from __future__ import annotations

import json

from .dft_drc_engine import DFTDRCEngine
from .formal_config import FormalVerificationConfig
from .formal_verification_module import FormalVerificationModule
from .protocol_checker import ProtocolChecker


def main() -> None:
    rows = [
        {"cycle": 0, "tms": 1, "trst_n": 1},
        {"cycle": 1, "tms": 1},
        {"cycle": 2, "tms": 1},
        {"cycle": 3, "tms": 1},
        {"cycle": 4, "tms": 1},
        {"cycle": 5, "tms": 0},
    ]
    pc = ProtocolChecker()
    rep = pc.check_trace(rows)

    drc = DFTDRCEngine()
    drep = drc.run_on_design(
        {
            "scan_cells": [{"name": "ff0", "scan_in": "tdi", "scan_out": "n1", "scan_enable_port": "se"}],
            "sequential_elements": [],
        }
    )

    fv = FormalVerificationModule(FormalVerificationConfig())
    out = {
        "protocol": rep,
        "dft_drc": drep,
        "formal_stub": fv.run_assertion_based_stub(),
    }
    print(json.dumps(out, indent=2))


if __name__ == "__main__":
    main()
