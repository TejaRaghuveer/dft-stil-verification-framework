# At-speed testing, timing violations, and design margin analysis

This package (`python/timing`) provides a **model-level** timing-aware pattern execution framework. It complements RTL simulation and static timing analysis (STA): use it for **planning**, **what-if sweeps**, and **reporting**; sign-off still requires SDF-annotated simulation and/or STA correlation.

## 1. At-speed testing

**At-speed** means scan capture and functional clocks run at (or near) the **operational** frequencies of the device, not only at a slow shift clock.

- **Shift vs capture**: JTAG/scan often shifts at a lower `TCK` while the **system clock** defines capture behavior for internal logic. The framework models both via `TimingConfig.tck_frequency_mhz` and `system_clock_mhz`.
- **Margins**: Setup and hold requirements (`setup_time_ns`, `hold_time_ns`) are checked against simplified **data arrival** models derived from `propagation_delay_*` and `clock_to_output_delay_ns`.
- **`AtSpeedExecutionEngine`**: Executes a `PatternTimingProfile` at the configured speeds and returns margins, metastability risk (qualitative), and clock-to-output budget.

## 2. Timing violation detection

**`TimingViolationDetector`** inspects each `ExecutionStepResult` and records:

| Kind             | Meaning (model)                                      | Typical remedy                          |
|------------------|------------------------------------------------------|-----------------------------------------|
| `setup`          | Negative setup slack                                 | Lower frequency, trailing edge, shorter logic depth |
| `hold`           | Negative hold slack                                  | Delay cells, adjust launch/capture      |
| `metastability`  | High qualitative CDC/async risk                      | Synchronizers, phase alignment          |

**Important**: A pattern can **detect a fault** in logic while still **violating timing** in silicon. The detector **flags violations regardless of functional pass**, matching the requirement to call out unsafe timing even when tests “pass” in a zero-delay sim.

## 3. Edge selection and transition / path delay patterns

**`EdgeSelectionOptimizer`** scores **leading** vs **trailing** capture edges:

- **Transition delay (TDF)**: Favors edges that stress transition timing while keeping modeled slack non-negative where possible.
- **Path delay**: Emphasizes path depth and margin trade-offs, penalizing high metastability risk.

**`CaptureEdge.BOTH`**: `compute_margins` uses the **worst** slack across both edges (conservative).

## 4. Multi-domain clocks and CDC

**`MultiDomainClockSequencer`** schedules TCK and system clock edges with optional **phase offset** from `MultiDomainRelationship`. Use **`cdc_safe()`** as a coarse check: same-domain launches/captures are safe; cross-domain needs sufficient setup margin and real synchronizers in RTL.

## 5. Operational speed / capability curve

**`OperationalSpeedAnalyzer.capability_curve`** sweeps `TCK` frequency and reports:

- `pass_fraction` per frequency (patterns with no violations and positive modeled margins).
- `patterns_reduced_speed_only`: patterns that pass at the **lowest** swept TCK but fail at the **highest** — candidates for **design or timing closure** review.

**`design_timing_headroom`**: Worst minimum margin across profiles; use with STA to set operational limits.

## 6. Constraint specification

- **YAML**: See `examples/timing_constraints.example.yaml` and `load_timing_config_from_yaml()`.
- **Braced text**: See `examples/timing_constraints.example.txt` and `parse_timing_constraints_text()` → `load_timing_config_from_dict()`.

## 7. Full report

```python
from timing import build_full_timing_report, load_timing_config_from_yaml
from timing.timing_execution import PatternTimingProfile

cfg = load_timing_config_from_yaml("examples/timing_constraints.example.yaml")
profiles = [PatternTimingProfile("pat0", "path_delay", estimated_path_depth=6)]
report = build_full_timing_report(cfg, profiles, tck_sweep=[100, 200, 400])
```

The report includes pattern results, edge recommendations, violations, a sample multi-domain schedule, operational analysis, and textual **recommendations**.

## 8. Integration with UVM `atpg_seq_config`

SystemVerilog side: `atpg_seq_config` already exposes `capture_edge`, TCK period, and setup/hold. Align Python `TimingConfig` with those values when correlating **modeled** margins to **simulation** (e.g. export JSON from Python and read as plusargs or `uvm_config_db`).

---

*References*: IEEE 1149.1 (JTAG), IEEE 1450 (STIL), industry practice for at-speed scan and path delay test (consult your STA/sign-off methodology).
