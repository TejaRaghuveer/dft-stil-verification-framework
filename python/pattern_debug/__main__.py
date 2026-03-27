"""Demo run for pattern debugging framework."""

from __future__ import annotations

import json

from .interactive_debug import PatternDebugOrchestrator
from .pattern_debugger import Breakpoint, PatternVector


def main() -> None:
    vectors = [
        PatternVector(0, {"TMS": "1", "TDI": "0"}),
        PatternVector(1, {"TMS": "0", "TDI": "1"}),
        PatternVector(2, {"TMS": "0", "TDI": "1"}),
    ]
    observed = [
        {"TDO": "0", "TMS": "1", "TDI": "0"},
        {"TDO": "1", "TMS": "0", "TDI": "1"},
        {"TDO": "0", "TMS": "0", "TDI": "1"},
    ]
    o = PatternDebugOrchestrator().run_single_pattern(
        "demo_pat",
        vectors,
        observed,
        expected_tdo="011",
        actual_tdo="010",
        breakpoints=[Breakpoint(vector_index=2)],
    )
    print(json.dumps(o.payload, indent=2))


if __name__ == "__main__":
    main()
