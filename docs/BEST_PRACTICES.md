# Best Practices

## Do

- Keep commits small and scoped (code, docs, infra separately).
- Always run a local dry-run before pushing.
- Keep generated artifacts out of commits unless explicitly needed.
- Add configuration examples for each new feature.
- Update both user-facing docs and technical docs for major changes.

## Do Not

- Do not hardcode machine-specific paths.
- Do not skip validation after refactors.
- Do not mix large feature work with unrelated formatting changes.
- Do not force-push shared branches without explicit team approval.

## DFT Flow Recommendations

- Start with smoke/minimal suites for quick iteration.
- Promote to comprehensive suites only after blockers are fixed.
- Track coverage, execution time, and anomalies together.
- Use multi-core and ML extensions as opt-in layers.

## Documentation Recommendations

- Keep one source of truth per topic.
- Add examples with executable commands.
- Prefer concise sections over long narrative blocks.
- Record design decisions and rationale in `docs/DESIGN_DOCUMENT.md`.

