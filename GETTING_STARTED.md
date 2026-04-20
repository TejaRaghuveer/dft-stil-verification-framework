# Getting Started

This guide helps a new team member get productive with the DFT verification project in under 30 minutes.

## 1) Environment Setup

- Install Python 3.9+ and run:
  - `pip install -r requirements.txt`
- Ensure one simulator is installed (VCS / Questa / Xcelium).
- From repo root, validate the setup:
  - `make validate`

## 2) First Successful Run

Run a lightweight production flow dry-run:

```bash
set PYTHONPATH=python
python python/integrated_flow/week3_production.py --dry-run --out deliverables_quickstart
```

Expected outputs:

- `deliverables_quickstart/Reports/week3_comprehensive.html`
- `deliverables_quickstart/Reports/fault_coverage_week3.json`
- `deliverables_quickstart/week3_manifest.json`

## 3) Optional: GPU + Multi-Core + ML extensions

```bash
python python/integrated_flow/week3_production.py \
  --dry-run \
  --out deliverables_quickstart \
  --gpu-shader-config config/gpu_shader_config.example.txt \
  --multi-core-config config/multi_core_config.example.txt \
  --ml-pattern-optimize --ml-target-coverage 95 --ml-max-patterns 300
```

## 4) Where to Look Next

- User workflows: `docs/USER_GUIDE.md`
- Architecture: `docs/ARCHITECTURE.md`
- API-level details: `docs/API_REFERENCE.md`
- Design rationale: `docs/DESIGN_DOCUMENT.md`
- Common issues: `docs/TROUBLESHOOTING.md`

## 5) Team Contact

- Maintainer: **Raghuveer**
- GitHub / LinkedIn: [https://github.com/TejaRaghuveer](https://github.com/TejaRaghuveer)
- Email: `tejaraghuveer@gmail.com`

