"""Charts for HTML reports: matplotlib optional; SVG fallbacks."""

from __future__ import annotations

import base64
import io
import math
from typing import Dict, List, Tuple


def coverage_convergence_svg(points: List[Tuple[int, float]], width: int = 480, height: int = 220) -> str:
    """Simple polyline SVG (pattern index vs coverage %%)."""
    if not points:
        return "<p>No convergence data</p>"
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    xmin, xmax = min(xs), max(xs) or 1
    ymin, ymax = 0.0, max(100.0, max(ys) * 1.05)
    pad = 40
    def sx(x):
        return pad + (x - xmin) / (xmax - xmin + 1e-9) * (width - 2 * pad)

    def sy(y):
        return height - pad - (y - ymin) / (ymax - ymin + 1e-9) * (height - 2 * pad)

    pts = " ".join("%.1f,%.1f" % (sx(x), sy(y)) for x, y in points)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">'
        '<rect fill="#f8fafc" width="100%%" height="100%%"/>'
        '<polyline fill="none" stroke="#0369a1" stroke-width="2" points="%s"/>'
        '<text x="%d" y="%d" font-size="12">Coverage %%</text></svg>'
        % (width, height, pts, pad, 18)
    )


def fault_histogram_svg(counts: Dict[str, int], width: int = 400, height: int = 200) -> str:
    if not counts:
        return "<p>No fault distribution</p>"
    keys = list(counts.keys())
    vals = [counts[k] for k in keys]
    vmax = max(vals) or 1
    bw = (width - 60) // max(len(keys), 1)
    bars = []
    x0 = 40
    for i, v in enumerate(vals):
        h = int((height - 50) * v / vmax)
        x = x0 + i * (bw + 4)
        y = height - 30 - h
        bars.append('<rect x="%d" y="%d" width="%d" height="%d" fill="#0ea5e9"/>' % (x, y, bw, h))
    return '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">%s</svg>' % (
        width,
        height,
        "".join(bars),
    )


def module_heatmap_html(module_cov: Dict[str, float]) -> str:
    rows = []
    for mod, pct in sorted(module_cov.items()):
        hue = int(120 * pct / 100)
        bg = "hsl(%d, 70%%, 85%%)" % hue
        rows.append(
            "<tr><td>%s</td><td style='background:%s'>%.1f%%</td></tr>" % (mod, bg, pct)
        )
    return "<table><tr><th>Module</th><th>Coverage</th></tr>%s</table>" % "".join(rows)


def pass_fail_pie_svg(pass_n: int, fail_n: int, size: int = 160) -> str:
    total = pass_n + fail_n
    if total == 0:
        return "<p>No pattern results</p>"
    pass_angle = 360.0 * pass_n / total
    cx, cy = size // 2, size // 2
    r = size // 2 - 4

    def arc(a0, a1):
        x1 = cx + r * math.cos(math.radians(a0 - 90))
        y1 = cy + r * math.sin(math.radians(a0 - 90))
        x2 = cx + r * math.cos(math.radians(a1 - 90))
        y2 = cy + r * math.sin(math.radians(a1 - 90))
        large = 1 if (a1 - a0) > 180 else 0
        return "M %d %d L %.2f %.2f A %d %d 0 %d 1 %.2f %.2f Z" % (cx, cy, x1, y1, r, r, large, x2, y2)

    p1 = arc(0, pass_angle)
    p2 = arc(pass_angle, 360)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">'
        '<path d="%s" fill="#22c55e"/><path d="%s" fill="#ef4444"/>'
        '<text x="%d" y="%d" font-size="11">PASS %d / FAIL %d</text></svg>'
        % (size, size, p1, p2, 10, size - 8, pass_n, fail_n)
    )


def defect_level_vs_coverage_svg(points: List[Tuple[float, float]], width: int = 400, height: int = 200) -> str:
    """Scatter (coverage %, defect level ppm) as SVG circles."""
    if not points:
        return "<p>No DL vs coverage data</p>"
    pad = 30
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    xmin, xmax = min(xs), max(xs)
    ymin, ymax = min(ys), max(ys)
    xr = (xmax - xmin) or 1
    yr = (ymax - ymin) or 1

    def sx(x):
        return pad + (x - xmin) / xr * (width - 2 * pad)

    def sy(y):
        return height - pad - (y - ymin) / yr * (height - 2 * pad)

    circs = "".join(
        '<circle cx="%.1f" cy="%.1f" r="4" fill="#8b5cf6"/>' % (sx(a), sy(b)) for a, b in points
    )
    return '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d">%s</svg>' % (width, height, circs)


def pattern_efficiency_scatter(points: List[Tuple[int, float]], width: int = 400, height: int = 200) -> str:
    """(patterns, faults_detected) efficiency scatter."""
    return defect_level_vs_coverage_svg([(float(a), float(b)) for a, b in points], width, height)


def matplotlib_figure_to_base64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("ascii")
