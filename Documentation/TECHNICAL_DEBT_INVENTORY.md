# Technical Debt Inventory

## Debt Register

| Item | Impact | Effort | Priority | Next Action |
|---|---|---:|---|---|
| Report schema validation not fully enforced | High | M | P1 | Add JSON schema checks in CI |
| Workflow schedule logic test coverage gaps | High | M | P1 | Add workflow simulation tests |
| Large orchestration methods in integrated flow | Medium | M | P2 | Stage-based refactor |
| Repeated pattern parsing in some paths | Medium | S | P2 | Add parsing cache helper |
| Limited formalization of analytics assumptions | Medium | S | P2 | Add assumptions appendix per engine |
| Incomplete automation for commit trailer hygiene | Low | S | P3 | Add commit-msg hook policy |

## Backlog Plan (Next Version)

- P1 items in first 2 sprints
- P2 items in parallel with feature work
- P3 items bundled with tooling maintenance sprint

## Estimated Effort

- P1 total: ~2-3 weeks
- P2 total: ~2 weeks
- P3 total: ~3-4 days

