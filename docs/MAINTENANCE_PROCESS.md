# Documentation Maintenance Process

## Review Cadence

- Quarterly documentation review with maintainers and active contributors.
- Release-time fast review for changed modules.

## Ownership

- Primary owner: Raghuveer
- Feature owner: engineer introducing the change
- Reviewer: one peer from a different module

## Update Triggers

- New feature
- Bug fix with behavior impact
- Any CLI/API parameter changes
- User feedback revealing ambiguity

## Change Tracking

- Document updates are committed with the feature branch whenever possible.
- PR descriptions must include a **Docs Impact** section.
- Keep historical changes searchable through git history and release notes.

## Quality Gates

- Validate links and command examples.
- Ensure `scripts/generate_doc_index.py` runs cleanly.
- Confirm updates in:
  - user docs (`docs/USER_GUIDE.md`)
  - API docs (`docs/API_REFERENCE.md`)
  - troubleshooting (`docs/TROUBLESHOOTING.md`) if needed

