# Multi-domain execution & comprehensive reporting guide

## 1. Multi-domain test execution (`python/multi_domain/`)

### `TestDomainManager`
- Register `TestDomain` objects with `clock_domain`, optional `ResourceClaim` list (shared TAM, ATE channel IDs), and `conflicts_with_domain_ids` for explicit mutex.
- `ExecutionMode.SINGLE_DOMAIN` vs `MULTI_DOMAIN`; optional `active_domain_id` for single-domain runs.
- `domains_for_parallel_run()` builds **parallel groups** via greedy coloring on a conflict graph (shared resources + explicit conflicts).

### `DomainTestScheduler`
- Attach scheduled jobs with `add_test(domain_id, test_name, est_seconds, tam_channels)`.
- `build()` returns estimated **serial makespan** (sum of per-group maxima), per-test allocation windows, and parallel group indices.

### `MultiDomainResultAggregator`
- Collect `DomainResult` per island/core; `aggregate()` returns per-domain tables, **weighted** fault/test coverage, merged module/type averages, and `cross_domain_notes` for CDC/TAM issues.

### Wiring to reports
Use `reporting.multidomain_bridge.report_input_from_aggregate()` to feed `ComprehensiveReportingSystem`.

---

## 2. Reporting system (`python/reporting/`)

### Templates (`templates.py`)
- **executive** — summary, metrics, coverage types, recommendations, sign-off.
- **technical** — adds detailed results, statistics, quality metrics.
- **detailed** — all sections including visualizations.
- **minimal** — summary + key metrics only.
- `ReportBranding` for HTML header/footer/logo.

### `ComprehensiveReportingSystem`
- `build_payload()` — nested dict for tools.
- `export_all(out_dir, basename)` — writes **JSON, XML, CSV** (pattern table), **HTML** (sidebar nav), attempts **PDF** (WeasyPrint or minimal ReportLab stub).

### `ReportGenerator` / `ReportInputData`
- Executive bullets, key metrics, text report matching tapeout-style sections.
- Statistical block: execution time distribution from `execution_times_sec`.
- Quality metrics: FC, test coverage, DL placeholder note.

### Exports (`export_system.py`)
- **CSV** — flat `per_pattern_results` rows.
- **JSON** — full payload.
- **XML** — recursive `ElementTree` (database-friendly).
- **HTML** — styled layout with anchor navigation.
- **PDF** — `pip install weasyprint` recommended; else tiny ReportLab placeholder.

---

## 3. Visualization (`visualization.py`)

Pure **SVG / HTML** (no matplotlib required):
- Coverage **convergence** polyline.
- Fault distribution **histogram**.
- Module coverage **heatmap** (HSL background).
- **Pass/Fail pie** (two-arc SVG).
- **Defect level vs coverage** and **pattern efficiency** scatter helpers.

For publication charts, optionally generate matplotlib figures and embed via `matplotlib_figure_to_base64()`.

---

## 4. Comparison reports (`comparison_reports.py`)

`compare_reports(dict_a, dict_b, label_a, label_b)` produces numeric **deltas** for pattern counts, coverage %, and per-module shifts — use for **smoke vs full**, **pattern rev A vs B**, or **pre-silicon vs post-silicon** JSON exports.

---

## 5. Sign-off (`sign_off_report.py`)

- `SignOffReport` captures targets, open issues, recommendations, **traceability** rows (`pattern`, `fault`, `location`), approval checkboxes.
- `to_markdown()` for Confluence / Git review.
- `certify_targets_met()` reflects **coverage vs target**; open issues remain visible for waivers.

---

## 6. Professional sign-off practices

1. **Traceability** — every critical pattern linked to fault IDs and RTL hierarchy (from ATPG/Faultlist).
2. **Version control** — store `integrated_report.json` + HTML under `out/` with git tag.
3. **Approvals** — replace checkbox markdown with PLM workflow; PDF/HTML is evidence.
4. **DL / yield** — tie reported ppm to methodology (fault universe size, confidence); do not use demo numbers for production.

---

## 7. Quick start

```bash
cd python
python -m reporting
```

Programmatic:

```python
from reporting import ComprehensiveReportingSystem, ReportInputData, ReportTemplateId

sys = ComprehensiveReportingSystem()
sys.data = ReportInputData(design_name="SoC", patterns_total=500, ...)
sys.set_template(ReportTemplateId.EXECUTIVE)
sys.export_all("out/reports", "tapeout_r1")
```

---

## 8. References

- IEEE 1450 (STIL), IEEE 1149.1 (JTAG)  
- `python/fault_coverage/` for FC definitions  
- `python/integrated_flow/run_flow.py` for end-to-end artifacts feeding this reporting layer
