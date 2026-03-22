# Multi-domain test execution

Chip-level DFT often spans **multiple clock domains**, **cores**, or **TAM partitions**. This package models:

- **Who** runs (`TestDomain`)
- **What** shares (`ResourceClaim` on TAM/ATE)
- **When** (`DomainTestScheduler` + conflict groups)
- **Results** (`MultiDomainResultAggregator` → `reporting.report_input_from_aggregate`)

See `python/reporting/REPORTING_GUIDE.md` for integration with HTML/JSON sign-off reports.
