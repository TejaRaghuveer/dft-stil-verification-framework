# Formal verification, assertions, and test infrastructure for DFT

This document describes the **Python verification package** (`python/verification/`) and **SystemVerilog Assertions (SVA)** under `uvm_tb/assertions/`, and how they support protocol compliance, DFT DRC-style checks, timing reports, scan-path reasoning, and formal sign-off workflows.

---

## 1. Roles: simulation vs formal vs offline analysis

| Layer | Purpose |
|--------|---------|
| **UVM + SVA (simulation)** | Real-time checks on DUT/TB; waveform debug; coverage |
| **Formal tools** (JasperGold, VC Formal, Questa PropCheck, …) | Exhaustive proofs on bounded/unbounded models; find corner-case failures |
| **Python offline** | Log/trace analysis, DRC reports on structural netlists, merged sign-off JSON |

No single Python call replaces a formal tool: `FormalVerificationModule.run_assertion_based_stub()` returns a **placeholder** until you connect a vendor script.

---

## 2. Protocol compliance (IEEE 1149.1)

### Python: `ProtocolChecker`

- Replays **TMS** (and optional **trst_n**, margins, observed TAP state) cycle-by-cycle.
- Uses `tap_fsm_reference.next_tap_state` aligned with `jtag_driver_enhanced.sv`.
- Flags illegal transitions (if monitor state provided), TDO-X during shift, setup/hold margin violations from exported metrics.

### SVA: `jtag_tap_formal_sva.sv`

- **Shadow TAP FSM** inside `jtag_tap_formal_props` (same transition table as the driver).
- **`p_tap_step`**: after each TCK, state matches `tap_next(prev_state, prev_tms)`.
- **`p_tdo_known_shift`**: during Shift-DR/IR, `!$isunknown(tdo)` (when `REGISTER_TDO_CHECK=1`).

**Formal setup tips**

- Constrain **reset** (`trst_n`) and initial state; add fairness on `tck` if needed.
- For **bounded proofs**, set depth consistent with `FormalVerificationConfig.proof_depth`.
- Use **assumptions** on TMS during shift if the DUT only supports a subset of paths.

---

## 3. Assertion writing guidelines

1. **Disable during reset**: `disable iff (!trst_n)` (or global reset).
2. **One clock domain per property** when possible; CDC paths need synchronizer models.
3. **Avoid vacuity**: cover companion sequences (e.g. reach `SHIFT_DR`).
4. **Bind** checkers at the **lowest accurate boundary** (pad vs core TAP wrapper).
5. Link to requirements: use `dft_assertion_macros.svh` or log `pattern_id` / `vector_index` for post-processing (`assertion_monitoring.py`).

---

## 4. DFT DRC engine (post-insertion)

`DFTDRCEngine` runs **structural** rules on JSON-like design extracts:

- Scan SI/SO presence, scan enable, non-scan flops, async reset on scan paths, clock-gating testability.

Severity: **critical / warning / info**. Replace or augment with TetraMAX/FastScan DRC exports by feeding the same schema.

---

## 5. Timing constraint checking

`TimingConstraintChecker` consumes per-signal or per-cycle **margin** and **skew** records (from SDF-annotated sim or your Python timing model in `python/timing/`). It does not compute STA; it **validates** exported metrics.

---

## 6. Scan path verification

`ScanPathVerification` provides:

- **Linear chain** duplicate detection and reachability flags.
- **Graph mode**: BFS from `TDI`, reverse BFS toward `TDO` to find cells not reachable or not observable.

Formal **“TDI reaches all scan cells”** is design-specific: use `scan_chain_connectivity_sva.sv` as a template and connect real `scan_so` taps or serial equivalence properties.

---

## 7. Coverage validation

`CoverageValidation` compares **required** TAP states / JTAG operations / data patterns (0/1/toggle/random) against **collected** bins from `jtag_coverage` or exported JSON.

---

## 8. Formal proof obligations and certificates

`FormalVerificationModule`:

- `build_obligations()` from `FormalVerificationConfig.properties_to_prove`.
- `export_transition_table_json()` for reviews and tool scripting.
- `fault_testability_certificate()` builds a **hash bundle** over testable/untestable fault lists — **not** a math proof until backed by tool logs.

**Untestable faults**: ATPG “untestable” and formal “unreachable fault” are related but not identical. Use `prove_untestable_stub()` as a documentation hook and attach ATPG UTD reports.

---

## 9. Configuration

- YAML: `config/formal_verification.example.yaml`
- Braced text: `config/formal_verification.example.txt` → `parse_formal_verification_text()`

---

## 10. Compilation notes (SVA modules)

`jtag_tap_formal_sva.sv` is a **module**, not inside `dft_tb_pkg`. Compile with the testbench and **instantiate** next to `jtag_if`, or use `bind` from `tb_top`. Do not `include` modules inside the package if your tool rejects it.

---

## 11. References

- IEEE 1149.1 — Test Access Port and Boundary-Scan  
- IEEE 1800 — SystemVerilog Assertions  
- Accellera SVA methodology guides; vendor formal user guides (JasperGold, VC Formal)
