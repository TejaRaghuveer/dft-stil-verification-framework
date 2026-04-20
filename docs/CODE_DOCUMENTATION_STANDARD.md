# Code Documentation Standard

This standard supports long-term maintainability without over-commenting obvious code.

## Inline Comments

- Comment non-obvious intent, assumptions, and hardware-specific constraints.
- Do not comment trivial assignments or control flow.

## Class and Method Docstrings

For each SystemVerilog/Python class or method, include:

- Purpose
- Parameters and valid ranges
- Return value / side-effects
- Usage example (when externally consumed)

## Parameter Documentation Format

- Name
- Type
- Valid range / allowed values
- Default value
- Failure behavior for invalid inputs

## Complex Algorithm Notes

For compression, timing, and ML logic:

- Add a short explanation of algorithm choice.
- Link to deep dive docs under `docs/deep_dives/`.
- Mention known limitations and calibration assumptions.

