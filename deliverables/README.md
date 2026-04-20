# Week 3 Production Deliverables

The `python/integrated_flow/week3_production.py` flow writes artifacts into this tree:

| Folder | Contents |
|--------|----------|
| **STIL_Patterns/** | `patterns_generated.stil`, `patterns_compressed_annotated.stil` |
| **Reports/** | Compression, timing at-speed, formal, DRC, STIL validation, HTML/JSON/XML/CSV reports, failure analysis |
| **Artifacts/** | Placeholder for golden responses, netlist pointers, TB configs |
| **Archive/** | Version snapshots (copy tagged release trees here) |

## Generate Deliverables

From repository root (Windows PowerShell):

```powershell
$env:PYTHONPATH="python"
python python/integrated_flow/week3_production.py --atpg patterns/stuck_at.stil --out deliverables --tck-mhz 200
```

With simulation results:

```powershell
python python/integrated_flow/week3_production.py --pattern-db out/integrated/pattern_db.json --results-csv out/integrated/results/full_results.csv --out deliverables
```

Dry-run (minimal placeholder pattern DB):

```powershell
python python/integrated_flow/week3_production.py --dry-run --out deliverables
```

## Changes Made in This Deliverables Flow

- Consolidated outputs into a predictable structure (`STIL_Patterns`, `Reports`, `Artifacts`, `Archive`).
- Added support for dry-run and full-result modes using the same flow entry point.
- Documented command examples for quick local verification and CI usage.

## Challenges

- Deliverable artifacts can vary depending on whether real simulation results are available.
- It was easy to lose track of which report came from which execution mode.

## Resolution Approach

- I kept one flow (`week3_production.py`) as the single source of artifact generation.
- I documented both dry-run and results-driven commands so output expectations are clear.
- I aligned folder naming with report consumption needs for easier review and archiving.

## Maintainer Contact

- **Raghuveer**
- GitHub / LinkedIn: [https://github.com/TejaRaghuveer](https://github.com/TejaRaghuveer)
- Email: `tejaraghuveer@gmail.com`
