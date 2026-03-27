# Troubleshooting guide (DFT / patterns)

## Pattern mismatches

1. Confirm **first failing vector** (`pattern_debug.response_comparer`).
2. Check **TAP state** vs expected (`verification.protocol_checker` on exported trace).
3. Review **waveform** at mismatch (`pattern_debug.waveform_viewer_integration` manifest).

## Low fault coverage

1. Ensure `fault_list` is populated in `pattern_db.json`.
2. Run **full** suite, not smoke-only.
3. Use `fault_coverage` gap reports for untestable clusters.

## STIL validation errors

1. Regenerate with `stil_generator.stil_template_generator` (PatternExec + `V { }` format).
2. Confirm signal order matches vector width.

## Timing failures

1. Reduce TCK or change capture edge (`timing` + `pattern_modification_suggester`).
2. Re-run STA on critical paths.

## Formal / DRC

- Python DRC is **structural**; tool DRC (TetraMAX/FastScan) is authoritative for tapeout.
- Formal proofs require vendor tool logs—replace stubs in `formal_verification.json`.
