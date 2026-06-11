#!/usr/bin/env python3
"""
Generate a PDF report of the NBA home court advantage analysis.
Run after nba_home_court_advantage.py — all PNGs and RESULTS.md must exist.

Narrative prose is read from FINDINGS.md (## sections). Charts and tables are
injected by the section functions below. To update report text, edit FINDINGS.md.

    python3 generate_report.py
"""

import os
import re
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    KeepTogether,
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

PAGE_W, PAGE_H = letter
MARGIN    = 0.85 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

DARK   = "#2c2c2a"
MID    = "#666666"
BLUE   = "#1f77b4"
ACCENT = BLUE

FINDINGS_PATH = "FINDINGS.md"
RESULTS_PATH  = "RESULTS.md"


# ── Styles (built once at import) ─────────────────────────────────────────────

def _build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        **{k: base[k] for k in base.byName},
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Title"],
            fontSize=30, textColor=colors.HexColor(DARK),
            spaceAfter=10, alignment=TA_CENTER,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", parent=base["Normal"],
            fontSize=13, textColor=colors.HexColor(MID),
            spaceAfter=5, alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"],
            fontSize=17, textColor=colors.HexColor(DARK),
            spaceBefore=16, spaceAfter=6,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"],
            fontSize=12, textColor=colors.HexColor(ACCENT),
            spaceBefore=10, spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontSize=10, leading=15,
            textColor=colors.HexColor(DARK),
            alignment=TA_JUSTIFY, spaceAfter=7,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base["Normal"],
            fontSize=8.5, leading=12,
            textColor=colors.HexColor(MID),
            alignment=TA_CENTER, spaceAfter=14,
        ),
        "toc_num": ParagraphStyle(
            "toc_num", parent=base["Normal"],
            fontSize=11, textColor=colors.HexColor(ACCENT),
            alignment=TA_CENTER,
        ),
        "toc_title": ParagraphStyle(
            "toc_title", parent=base["Normal"],
            fontSize=11, textColor=colors.HexColor(DARK),
            leading=18,
        ),
        "note": ParagraphStyle(
            "note", parent=base["Normal"],
            fontSize=8.5, leading=12,
            textColor=colors.HexColor(MID),
            spaceAfter=5,
        ),
        "code": ParagraphStyle(
            "code", parent=base["Code"],
            fontSize=6.5, leading=9,
            textColor=colors.HexColor(DARK),
            fontName="Courier",
            spaceAfter=0,
        ),
        "table_header": ParagraphStyle(
            "table_header", parent=base["Normal"],
            fontSize=9, leading=12,
            textColor=colors.white,
            fontName="Helvetica-Bold",
        ),
        "table_body": ParagraphStyle(
            "table_body", parent=base["Normal"],
            fontSize=9, leading=12,
            textColor=colors.HexColor(DARK),
        ),
    }


_STYLES = _build_styles()


# ── FINDINGS.md parser ────────────────────────────────────────────────────────

def _parse_findings(path=FINDINGS_PATH) -> dict[str, str]:
    """Return {heading: body} for each ## section in FINDINGS.md."""
    if not os.path.exists(path):
        return {}
    with open(path) as f:
        content = f.read()
    sections = {}
    for part in re.split(r'^## ', content, flags=re.MULTILINE)[1:]:
        newline = part.find('\n')
        heading = part[:newline].strip()
        body = part[newline:].strip()
        body = re.sub(r'\n?---\s*$', '', body).strip()
        sections[heading] = body
    return sections


def _md_inline(text: str) -> str:
    """Convert inline markdown to reportlab XML markup."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*([^*\n]+?)\*', r'<i>\1</i>', text)
    text = re.sub(r'`([^`]+)`', r'<font name="Courier">\1</font>', text)
    return text


def _md_to_flowables(text: str) -> list:
    """Convert a FINDINGS.md section body to a list of reportlab flowables."""
    flowables = []
    for block in re.split(r'\n{2,}', text):
        block = block.strip()
        if not block:
            continue
        if block.startswith('### '):
            flowables.append(Paragraph(_md_inline(block[4:]), _STYLES['h2']))
        elif block.startswith('!['):
            m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', block)
            if m:
                flowables.append(Spacer(1, 0.1 * inch))
                flowables.append(_chart(m.group(2), m.group(1)))
        elif block.startswith('- '):
            for line in block.splitlines():
                if line.startswith('- '):
                    flowables.append(Paragraph('• ' + _md_inline(line[2:]), _STYLES['body']))
        elif block.startswith('|'):
            rows = []
            is_header = True
            for line in block.splitlines():
                line = line.strip()
                if not line:
                    continue
                if re.match(r'^\|[\s\-:|]+\|$', line):
                    is_header = False
                    continue
                style = _STYLES['table_header'] if is_header else _STYLES['table_body']
                cells = [Paragraph(_md_inline(c.strip()), style)
                         for c in line.split('|')[1:-1]]
                rows.append(cells)
                is_header = False
            if rows:
                n_cols = max(len(r) for r in rows)
                col_w = CONTENT_W / n_cols
                flowables.append(Spacer(1, 0.1 * inch))
                flowables.append(_table(rows, [col_w] * n_cols))
        else:
            joined = ' '.join(ln.strip() for ln in block.splitlines() if ln.strip())
            flowables.append(Paragraph(_md_inline(joined), _STYLES['body']))
    return flowables


# ── Layout helpers ────────────────────────────────────────────────────────────

def _img(path, width=None):
    if not os.path.exists(path):
        return Paragraph(f"[Missing image: {path}]", _STYLES["note"])
    if width is None:
        width = CONTENT_W
    ri = Image(path)
    aspect = ri.imageHeight / ri.imageWidth
    ri.drawWidth  = width
    ri.drawHeight = width * aspect
    ri.hAlign = "CENTER"
    return ri


def _hr():
    return HRFlowable(width="100%", thickness=0.5,
                      color=colors.HexColor("#dddddd"), spaceAfter=8)


def _table(data, col_widths, header_rows=1):
    style = [
        ("BACKGROUND",     (0, 0), (-1, header_rows - 1), colors.HexColor(ACCENT)),
        ("TEXTCOLOR",      (0, 0), (-1, header_rows - 1), colors.white),
        ("FONTNAME",       (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, header_rows), (-1, -1),
         [colors.HexColor("#f7f7f5"), colors.white]),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
    ]
    return Table(data, colWidths=col_widths, style=TableStyle(style))


def _chart(path, caption_text, width=None):
    return KeepTogether([
        _img(path, width=width),
        Spacer(1, 4),
        Paragraph(caption_text, _STYLES["caption"]),
    ])


def _results_text() -> str:
    """Read RESULTS.md and return the raw regression output (strips markdown fences)."""
    if not os.path.exists(RESULTS_PATH):
        return "[RESULTS.md not found — run nba_home_court_advantage.py first]"
    with open(RESULTS_PATH) as f:
        lines = f.readlines()
    content, in_block = [], False
    for line in lines:
        if line.strip() == "```":
            in_block = not in_block
            continue
        if in_block:
            content.append(line.rstrip("\n"))
    return "\n".join(content)


# ── Special section builders ──────────────────────────────────────────────────

def _cover(sections: dict) -> list:
    toc_data = []
    for heading in sections:
        parts = heading.split('. ', 1)
        if len(parts) == 2 and parts[0].isdigit():
            toc_data.append([parts[0] + '.', parts[1]])
    toc_data.append(['A.', 'Appendix: Full Regression Output'])

    return [
        Spacer(1, 1.2 * inch),
        Paragraph("NBA Home Court Advantage", _STYLES["cover_title"]),
        Paragraph("A 40-Year Decline", _STYLES["cover_sub"]),
        Spacer(1, 0.25 * inch),
        _hr(),
        Spacer(1, 0.15 * inch),
        Paragraph(
            "Data: NBA.com  ·  1983–84 through 2024–25  ·  51,089 games",
            _STYLES["cover_sub"],
        ),
        Paragraph(
            f"Generated {datetime.now().strftime('%B %d, %Y at %H:%M')}",
            _STYLES["cover_sub"],
        ),
        Spacer(1, 0.8 * inch),
        Paragraph("Contents", _STYLES["h2"]),
        Table(
            [[Paragraph(num, _STYLES["toc_num"]), Paragraph(title, _STYLES["toc_title"])]
             for num, title in toc_data],
            colWidths=[CONTENT_W * 0.10, CONTENT_W * 0.90],
            style=TableStyle([
                ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING",    (0, 0), (-1, -1), 5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
                ("LINEBELOW",     (0, -1), (-1, -1), 0.5, colors.HexColor("#dddddd")),
            ]),
        ),
        PageBreak(),
    ]


def _appendix_results() -> list:
    return [
        PageBreak(),
        Paragraph("Appendix A: Full Regression Output", _STYLES["h1"]),
        _hr(),
        Paragraph(
            "Auto-generated by <font name=\"Courier\">nba_home_court_regression.py</font> "
            "each time the analysis is run. Contains the sequential R² decomposition, "
            "pre/post-2014 coefficient stability check, bivariate factor significance table, "
            "and foul/shooting differential trends by era.",
            _STYLES["body"],
        ),
        Spacer(1, 0.1 * inch),
        Preformatted(_results_text(), _STYLES["code"]),
    ]


# ── Main ──────────────────────────────────────────────────────────────────────

def build_report(output_path="nba_home_court_advantage_report.pdf"):
    sections = _parse_findings()

    story = [*_cover(sections)]
    for heading, body in sections.items():
        num_str = heading.split('.')[0]
        if num_str.isdigit() and int(num_str) >= 4:
            story.append(PageBreak())
        story += [Paragraph(heading, _STYLES["h1"]), _hr(), *_md_to_flowables(body)]
    story += [
        Spacer(1, 0.3 * inch),
        _hr(),
        Paragraph(
            "Data: NBA.com. Analysis covers 1983–84 through 2024–25. "
            "Shot zone data available from 1996–97. "
            "Logistic regression uses McFadden R²; marginal effects at the mean. "
            "See Appendix A for full tables and coefficient values.",
            _STYLES["note"],
        ),
    ]
    story += _appendix_results()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title="NBA Home Court Advantage — A 40-Year Decline",
        author="Justin Pietsch",
    )
    doc.build(story)
    print(f"Saved → {output_path}")


if __name__ == "__main__":
    build_report()
