# Code Documentation Rollout Roadmap

## Goal

Reach full class/method documentation coverage across Python and SystemVerilog without blocking feature velocity.

## Phased Plan

### Phase 1 (Immediate)

- Enforce docstrings/comments on all new code.
- Run `python scripts/doc_audit.py` in local checks.

### Phase 2 (Incremental backfill)

- Prioritize high-change modules:
  - `python/integrated_flow/`
  - `python/gpu_shader/`
  - `uvm_tb/agents/jtag/`

### Phase 3 (Coverage completion)

- Backfill remaining modules.
- Add CI step for documentation audit.

## Acceptance Criteria

- Every public Python class/function has a docstring.
- Every SystemVerilog class has a class-level purpose comment.
- API docs include parameter ranges and examples.

