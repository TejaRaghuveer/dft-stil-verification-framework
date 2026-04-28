# Best Practices Guide (DFT Verification)

## Do's

- Define measurable quality gates early (coverage, timing, violations, sign-off artifacts).
- Keep pattern generation, validation, and reporting flows deterministic and traceable.
- Maintain a single source of truth for manifests and output contracts.
- Pair every major feature with runnable examples and operator-focused documentation.

## Don'ts

- Do not mix absolute and relative output paths in the same manifest.
- Do not rely on implicit defaults for schedule-sensitive CI behavior.
- Do not treat documentation as a late-stage task.
- Do not optimize without measurable baseline and regression checks.

## Design Tips (Testability)

- Improve controllability/observability on hard-to-reach control logic.
- Keep scan access and reset behavior explicit and verifiable.
- Surface timing-critical paths early for at-speed planning.

## Test Pattern Tips

- Balance high-coverage full suites with fast diagnostic subsets.
- Prioritize patterns by efficiency under time budgets.
- Maintain debug pattern families for targeted failure triage.

## Tooling Tips

- Validate STIL compliance continuously.
- Use CI for repeatability and schedule-driven regressions.
- Preserve artifacts with consistent naming and versioned archives.

## Team Tips

- Define ownership per subsystem (verification, analytics, handoff).
- Keep regular cross-functional review cadence with manufacturing and test teams.
- Maintain a clear escalation matrix for post-silicon issues.

