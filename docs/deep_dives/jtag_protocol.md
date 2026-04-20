# Deep Dive: JTAG Protocol Implementation in UVM

## Scope

Explains how TAP transitions, sequence modeling, and monitor reconstruction are implemented in this project.

## Key Concepts

- TAP state transitions and legal paths
- IR/DR shift semantics
- Reset behavior and synchronization
- Coverage bins for protocol completeness

## Implementation Anchors

- `uvm_tb/agents/jtag/`
- `python/verification/protocol_checker.py`
- `uvm_tb/assertions/jtag_tap_formal_sva.sv`

