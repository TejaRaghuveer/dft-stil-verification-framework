# Week 3 production deliverables

The `python/integrated_flow/week3_production.py` flow writes artifacts into this tree:

| Folder | Contents |
|--------|----------|
| **STIL_Patterns/** | `patterns_generated.stil`, `patterns_compressed_annotated.stil` |
| **Reports/** | Compression, timing at-speed, formal, DRC, STIL validation, HTML/JSON/XML/CSV reports, failure analysis |
| **Artifacts/** | Placeholder for golden responses, netlist pointers, TB configs |
| **Archive/** | Version snapshots (copy tagged release trees here) |

## Generate

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

## Maintainer

- **Raghuveer**
- GitHub / LinkedIn: [https://github.com/TejaRaghuveer](https://github.com/TejaRaghuveer)
- Email: `tejaraghuveer@gmail.com`
