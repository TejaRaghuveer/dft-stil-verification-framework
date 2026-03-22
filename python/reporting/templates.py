"""Report templates: sections, verbosity, branding."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Set


class ReportTemplateId(str, Enum):
    EXECUTIVE = "executive"
    TECHNICAL = "technical"
    DETAILED = "detailed"
    MINIMAL = "minimal"


@dataclass
class ReportBranding:
    company_name: str = ""
    logo_url: str = ""
    header_html: str = ""
    footer_html: str = ""


@dataclass
class ReportTemplate:
    template_id: ReportTemplateId
    include_sections: Set[str] = field(default_factory=set)
    detail_level: str = "summary"
    branding: ReportBranding = field(default_factory=ReportBranding)


def default_template(tid: ReportTemplateId) -> ReportTemplate:
    all_sections = {
        "executive_summary",
        "key_metrics",
        "coverage_by_type",
        "module_coverage",
        "failures_gaps",
        "recommendations",
        "detailed_results",
        "statistical_analysis",
        "quality_metrics",
        "visualizations",
        "sign_off",
    }
    if tid == ReportTemplateId.EXECUTIVE:
        return ReportTemplate(
            template_id=tid,
            include_sections={
                "executive_summary",
                "key_metrics",
                "coverage_by_type",
                "recommendations",
                "sign_off",
            },
            detail_level="summary",
        )
    if tid == ReportTemplateId.TECHNICAL:
        return ReportTemplate(
            template_id=tid,
            include_sections=all_sections - {"visualizations"},
            detail_level="detailed",
        )
    if tid == ReportTemplateId.DETAILED:
        return ReportTemplate(
            template_id=tid, include_sections=set(all_sections), detail_level="very_detailed"
        )
    return ReportTemplate(
        template_id=tid,
        include_sections={"executive_summary", "key_metrics"},
        detail_level="summary",
    )
