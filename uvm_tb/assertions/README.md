# DFT / JTAG assertion components

| File | Purpose |
|------|---------|
| `jtag_tap_formal_sva.sv` | Shadow TAP FSM + `p_tap_step`, TDO known during shift |
| `scan_chain_connectivity_sva.sv` | Template for scan serial propagation properties |
| `dft_assertion_macros.svh` | UVM-friendly assertion logging with pattern/vector context |

Enable in your compile filelist **after** `jtag_transaction.sv` so enum ordering matches (or keep the duplicate `tap_state_e` in sync).

Example instantiation:

```systemverilog
jtag_tap_formal_props u_jtag_chk (
  .tck    (vif.tck),
  .tms    (vif.tms),
  .tdi    (vif.tdi),
  .tdo    (vif.tdo),
  .trst_n (vif.trst_n)
);
```

For formal builds, define `DFT_FORMAL` and add constraints/assumptions in a separate file.
