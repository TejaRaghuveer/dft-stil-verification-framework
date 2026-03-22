"""Comprehensive DFT reporting: HTML/JSON/XML/CSV/PDF, templates, sign-off, comparisons."""

from .comparison_reports import ComparisonReport, compare_reports
from .comprehensive_reporting import ComprehensiveReportingSystem
from .export_system import export_csv, export_html, export_json, export_pdf_simple, export_xml
from .multidomain_bridge import report_input_from_aggregate
from .report_generator import ReportGenerator, ReportInputData
from .sign_off_report import SignOffReport
from .templates import ReportBranding, ReportTemplate, ReportTemplateId, default_template

__all__ = [
    "ComprehensiveReportingSystem",
    "ReportGenerator",
    "ReportInputData",
    "ReportTemplate",
    "ReportTemplateId",
    "ReportBranding",
    "default_template",
    "SignOffReport",
    "compare_reports",
    "ComparisonReport",
    "export_json",
    "export_csv",
    "export_xml",
    "export_html",
    "export_pdf_simple",
    "report_input_from_aggregate",
]
