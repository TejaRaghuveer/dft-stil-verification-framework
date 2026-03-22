"""Export report payloads to CSV, JSON, XML, HTML, PDF (optional)."""

from __future__ import annotations

import csv
import json
from typing import Any, Dict, List, Optional
from xml.etree import ElementTree as ET


def export_json(data: Dict[str, Any], path: str, indent: int = 2) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=indent)


def export_csv(rows: List[Dict[str, Any]], path: str) -> None:
    if not rows:
        open(path, "w", encoding="utf-8").close()
        return
    keys = list(rows[0].keys())
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(rows)


def export_xml(data: Dict[str, Any], path: str, root_tag: str = "dft_report") -> None:
    def to_el(parent: ET.Element, key: str, val: Any) -> None:
        safe = key.replace(" ", "_")
        if isinstance(val, dict):
            sub = ET.SubElement(parent, safe)
            for k, v in val.items():
                to_el(sub, k, v)
        elif isinstance(val, list):
            sub = ET.SubElement(parent, safe)
            for i, item in enumerate(val):
                if isinstance(item, dict):
                    row = ET.SubElement(sub, "item")
                    row.set("index", str(i))
                    for k, v in item.items():
                        to_el(row, k, v)
                else:
                    e = ET.SubElement(sub, "item")
                    e.text = str(item)
        else:
            e = ET.SubElement(parent, safe)
            e.text = str(val)

    root = ET.Element(root_tag)
    for k, v in data.items():
        to_el(root, k, v)
    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(path, encoding="utf-8", xml_declaration=True)


def export_html(title: str, nav_items: List[tuple], body_html: str, path: str, extra_head: str = "") -> None:
    nav = "\n".join('<a href="#%s">%s</a>' % (aid, label) for aid, label in nav_items)
    doc = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8"/>
<title>%s</title>
<style>
body { font-family: Segoe UI, system-ui, sans-serif; margin: 0; display: flex; }
nav { width: 220px; background: #1a1a2e; color: #eee; padding: 1rem; position: sticky; top: 0; height: 100vh; }
nav a { color: #7dd3fc; display: block; margin: 0.4rem 0; text-decoration: none; }
main { flex: 1; padding: 2rem; max-width: 900px; }
table { border-collapse: collapse; width: 100%%; margin: 1rem 0; }
th, td { border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }
th { background: #f0f9ff; }
section { margin-bottom: 2rem; }
h1 { color: #0c4a6e; }
</style>
%s
</head>
<body>
<nav>%s</nav>
<main>%s</main>
</body>
</html>""" % (title, extra_head, nav, body_html)
    with open(path, "w", encoding="utf-8") as f:
        f.write(doc)


def export_pdf_simple(html_path: str, pdf_path: str) -> Optional[str]:
    try:
        import weasyprint  # type: ignore

        weasyprint.HTML(filename=html_path).write_pdf(pdf_path)
        return None
    except ImportError:
        pass
    try:
        from reportlab.lib.pagesizes import letter  # type: ignore
        from reportlab.pdfgen import canvas  # type: ignore

        c = canvas.Canvas(pdf_path, pagesize=letter)
        c.drawString(72, 720, "DFT Report (install weasyprint for full HTML to PDF)")
        c.save()
        return "minimal_pdf_placeholder"
    except ImportError:
        return "install weasyprint or reportlab for PDF export"
