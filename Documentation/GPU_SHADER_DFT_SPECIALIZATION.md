# GPU Shader Core DFT Specialization

This extension adds GPU shader-core specific verification on top of the base DFT flow, with direct emphasis on ALU correctness, register file reliability, and pipeline/interconnect behavior.

## Scope and architecture notes

- Shader ALUs have mixed arithmetic/logic/compare operations and wide datapaths, so boundary and corner vectors are required to expose datapath faults quickly.
- Register files are multi-banked with concurrent access patterns, so read/write integrity and simple arbitration behavior are included.
- Pipeline testing is stage-aware and checks latching/forwarding behavior, with hazard and stall checks as structural proxies.
- Scan-mode checks are included in ALU and register flows so stuck-at style observability is represented in CI-friendly dry-runs.

## Added GPU-specific agents

- `ALUExecutionAgent`:
  - Drives ALU operand/opcode stimulus.
  - Captures operation result and compares against expected model output.
- `RegisterFileAgent`:
  - Performs read/write access and state verification.
  - Tracks bank mapping and simple writer arbitration policy.
- `InterconnectAgent`:
  - Routes payloads through shader pipeline stages.
  - Verifies forwarding and stage-latch behavior.
- `TextureMemoryAgent`:
  - Optional interface-health probe if memory interfaces are present.

## ALU verification sequences

- Arithmetic: `ADD`, `SUB`, `MUL`, `DIV`
- Logical: `AND`, `OR`, `XOR`, `NOT`, `SHIFT`
- Comparison: `EQ`, `NE`, `LT`, `GT`, `LE`, `GE`

Vector classes generated for each operation:

- Boundary: `0`, `1`, `-1`, `MAX`, `MIN`
- Typical: medium-range values
- Corner: overflow, underflow, divide-by-zero proxy

Scan-based ALU checks:

- Use corner and boundary subsets as scan-mode vectors.
- Drive ALU input equivalents and validate expected output signatures.
- Tag vectors with fault hints for stuck-at datapath diagnosis.

## Register file verification

- Tests read/write data path and storage stability.
- Performs scan-like write/readback (inverted-pattern readback).
- Checks simple multi-reader/multi-writer arbitration policy.
- Reports per-bank coverage and mismatch counts.

## Pipeline/interconnect checks

- Data flow through all configured stages.
- Forwarding behavior across stage boundaries.
- Hazard/stall proxy checks (depth-based risk model).
- Per-stage output latching status.

## GPU-specific fault model buckets

- Shader stuck-at faults: ALU datapath, register cells, mux controls.
- Shader timing faults: datapath delay risk, setup/hold risk.
- Datapath integrity faults: inverted bits, stuck groups.

## Test class hierarchy

- `gpu_alu_test`
- `gpu_register_file_test`
- `gpu_pipeline_test`
- `gpu_functional_test`
- `gpu_comprehensive_test`

All classes are implemented in `python/gpu_shader/gpu_shader_verification.py`.

## Configuring GPU shader core

Use text block config:

```text
gpu_shader_config {
  bit_width: 32;
  alu_operations: [ADD, SUB, MUL, DIV, AND, OR, XOR];
  num_registers: 32;
  pipeline_depth: 4;
  num_alu_units: 2;
  scan_chains: 16;
  verify_modes: [FUNCTIONAL, SCAN, AT_SPEED];
}
```

You can also use JSON mapping via `--gpu-shader-config-json`.

## Running with Week 3 integration

From repo root:

```bash
set PYTHONPATH=python
python python/integrated_flow/week3_production.py --dry-run --out deliverables --gpu-shader-config config/gpu_shader_config.example.txt
```

Generated files:

- `Reports/gpu_shader_verification.json`
- `Reports/gpu_shader_verification.html`

## Visualization outputs

- ALU coverage by operation type (SVG bar chart)
- Register-file coverage by bank (heatmap table)
- Pipeline stage coverage (heatmap table)
- Per-stage fault detection proxy (SVG bar chart)

## GPU report sections

- ALU verification results
- Register file health
- Pipeline correctness
- Data integrity
- Per-stage timing margins
