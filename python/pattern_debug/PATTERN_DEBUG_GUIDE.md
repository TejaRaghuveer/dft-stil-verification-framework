# Pattern Debugging and Failure Root-Cause Guide

`python/pattern_debug/` provides a modular debug flow for failed ATPG/STIL patterns.

## Components

- `PatternDebugger` — single-step vector execution, breakpoints (vector/fault/signal), snapshots, replay history.
- `FailureAnalyzer` — classify failures: timing, mismatch, no response, initialization.
- `WaveformViewerIntegration` — waveform manifest generation, failure-window highlighting, expected/actual comparison hooks.
- `ResponseComparer` — first mismatch, sequence diff, timing delay/skew summary.
- `FaultInjectionDebugger` — inject faults and produce detection proof records.
- `PatternModificationSuggester` — propose TCK/capture/timing fixes with likelihood and plusarg scripts.
- `SignalAnalysisTools` — activity/transitions/stuck detection and anomalies.
- `ComparativeAnalysis` — pass-vs-fail feature deltas and failure class suggestions.

## Methodology

1. Reproduce with **single failing pattern**.
2. Enable vector snapshots and response dump.
3. Find first mismatch (`ResponseComparer`).
4. Correlate mismatch vector in waveform (`WaveformViewerIntegration`).
5. Categorize cause (`FailureAnalyzer`).
6. Generate and rank fixes (`PatternModificationSuggester`).
7. Validate with manual fault injection if needed (`FaultInjectionDebugger`).
8. Compare against passing peers (`ComparativeAnalysis`) for systemic root cause.

## Outputs

- JSON debug report with mismatch index, root cause, and recommendations.
- Waveform manifest (`*.waveform_manifest.json`) with highlight window.
- Optional HTML report from scripts under `scripts/`.

## Practical notes

- This framework is analysis-oriented and tool-agnostic.
- For production sign-off, correlate with RTL/SDF simulation and STA.
- FSDB generation depends on simulator setup; manifest supports VCD/FSDB hints.
