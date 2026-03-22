"""
Comprehensive reporting: orchestrates templates, generator, exports, visualizations, multi-domain data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from .export_system import export_csv, export_html, export_json, export_pdf_simple, export_xml
from .report_generator import ReportGenerator, ReportInputData
from .sign_off_report import SignOffReport
from .templates import ReportTemplate, ReportTemplateId, default_template
from . import visualization as viz


@dataclass
class ComprehensiveReportingSystem:
    template: ReportTemplate = field(default_factory=lambda: default_template(ReportTemplateId.TECHNICAL))
    data: ReportInputData = field(default_factory=ReportInputData)

    def set_template(self, tid: ReportTemplateId) -> None:
        self.template = default_template(tid)

    def build_payload(self) -> Dict[str, Any]:
        gen = ReportGenerator(self.data)
        sec = self.template.include_sections
        payload: Dict[str, Any] = {
            "meta": {
                "design": self.data.design_name,
                "detail_level": self.template.detail_level,
                "template": self.template.template_id.value,
            },
        }
        if "executive_summary" in sec:
            payload["executive_summary"] = gen.executive_summary()
        if "key_metrics" in sec:
            payload["key_metrics"] = gen.key_metrics()
        if "coverage_by_type" in sec:
            payload["coverage_by_type"] = gen.coverage_by_type_section()
        if "module_coverage" in sec:
            payload["module_coverage"] = gen.module_coverage_section()
        if "failures_gaps" in sec:
            payload["failures_gaps"] = gen.failures_gaps_section()
        if "recommendations" in sec:
            payload["recommendations"] = gen.recommendations_section()
        if "detailed_results" in sec:
            payload["detailed_results"] = gen.detailed_results()
        if "statistical_analysis" in sec:
            payload["statistical_analysis"] = gen.statistical_analysis()
        if "quality_metrics" in sec:
            payload["quality_metrics"] = gen.quality_metrics()
        if "visualizations" in sec:
            payload["visualizations"] = self._viz_html()
        if "sign_off" in sec:
            so = SignOffReport(
                design_name=self.data.design_name,
                achieved_fault_coverage_pct=self.data.fault_coverage_pct,
                coverage_target_pct=self.data.target_coverage_pct,
                open_issues=[x for x in self.data.critical_findings],
                recommendations=list(self.data.recommendations),
                traceability=list(self.data.traceability),
            )
            payload["sign_off"] = so.to_dict()
        payload["text_report"] = gen.build_text_report(sorted(sec))
        return payload

    def _viz_html(self) -> Dict[str, str]:
        d = self.data
        conv = viz.coverage_convergence_svg(d.coverage_convergence)
        hist = viz.fault_histogram_svg(
            {k: int(v) for k, v in d.undetected_breakdown.items()} if d.undetected_breakdown else {"stuck_at": 1}
        )
        heat = viz.module_heatmap_html(d.coverage_by_module)
        pie = viz.pass_fail_pie_svg(d.patterns_pass, d.patterns_fail)
        return {
            "convergence_svg": conv,
            "fault_histogram_svg": hist,
            "module_heatmap_html": heat,
            "pass_fail_pie_svg": pie,
        }

    def export_all(self, out_dir: str, basename: str = "dft_report") -> Dict[str, str]:
        Path(out_dir).mkdir(parents=True, exist_ok=True)
        payload = self.build_payload()
        paths = {}
        jp = str(Path(out_dir) / (basename + ".json"))
        export_json(payload, jp)
        paths["json"] = jp

        xp = str(Path(out_dir) / (basename + ".xml"))
        export_xml(payload, xp)
        paths["xml"] = xp

        rows = self.data.per_pattern_results or [{"pattern": "summary", "pass": self.data.patterns_fail == 0}]
        cp = str(Path(out_dir) / (basename + "_patterns.csv"))
        export_csv(rows, cp)
        paths["csv"] = cp

        body = self._html_body(payload)
        nav = [
            ("summary", "Summary"),
            ("metrics", "Metrics"),
            ("coverage", "Coverage"),
            ("viz", "Charts"),
            ("signoff", "Sign-off"),
        ]
        hp = str(Path(out_dir) / (basename + ".html"))
        export_html("DFT Report: %s" % self.data.design_name, nav, body, hp)
        paths["html"] = hp

        pdf_msg = export_pdf_simple(hp, str(Path(out_dir) / (basename + ".pdf")))
        paths["pdf_note"] = pdf_msg or "ok"
        return paths

    def _html_body(self, payload: Dict[str, Any]) -> str:
        parts = []
        if "executive_summary" in payload:
            es = payload["executive_summary"]
            parts.append("<section id='summary'><h1>%s</h1><ul>" % es["title"])
            for b in es.get("bullets", []):
                parts.append("<li>%s</li>" % b)
            parts.append("</ul></section>")
        if "key_metrics" in payload:
            km = payload["key_metrics"]
            parts.append("<section id='metrics'><h1>%s</h1>" % km["title"])
            parts.append("<p class='metric'>Fault coverage: %.2f%%</p>" % km["fault_coverage_pct"])
            parts.append("<p>Patterns: %s — Time: %s</p></section>" % (km["pattern_count"], km["execution_time"]))
        if "coverage_by_type" in payload:
            ct = payload["coverage_by_type"]["rows"]
            parts.append("<section id='coverage'><h1>COVERAGE BY TYPE</h1><table>")
            for k, v in ct.items():
                parts.append("<tr><td>%s</td><td>%.2f%%</td></tr>" % (k, v))
            parts.append("</table>")
        if "visualizations" in payload:
            vz = payload["visualizations"]
            parts.append("<section id='viz'><h1>Visualizations</h1>")
            parts.append(vz.get("convergence_svg", ""))
            parts.append(vz.get("pass_fail_pie_svg", ""))
            parts.append(vz.get("module_heatmap_html", ""))
            parts.append("</section>")
        if "sign_off" in payload:
            parts.append("<section id='signoff'><h1>Sign-off</h1><pre>%s</pre></section>" % payload["text_report"][-800:])
        return "\n".join(parts)
