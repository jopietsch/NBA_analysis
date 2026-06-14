#!/usr/bin/env python3
"""
Render a standalone Markdown document to a styled PDF.

Built for the teaching docs (STATS_TUTORIAL.md, STATS_EXPLAINER.md) — not the
findings report, which has its own generator (generate_report.py). Reuses the
same reportlab look but ships a general Markdown renderer that understands the
constructs those docs use: fenced code blocks, #/##/### headings, ordered and
bulleted lists, blockquotes, tables, and embedded images.

    python3 generate_doc_pdf.py STATS_TUTORIAL.md
    python3 generate_doc_pdf.py STATS_EXPLAINER.md [output.pdf]

Embedded images (![alt](file.png)) must exist relative to the working directory;
the tutorial's figures come from generate_tutorial_figures.py and the analysis
pipeline. Output defaults to <input stem>.pdf.
"""

import os
import re
import sys
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
CODEBG = "#f4f4f2"


# ── Styles ────────────────────────────────────────────────────────────────────

def _build_styles() -> dict:
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Title"],
            fontSize=26, textColor=colors.HexColor(DARK),
            spaceAfter=10, alignment=TA_CENTER, leading=32,
        ),
        "cover_sub": ParagraphStyle(
            "cover_sub", parent=base["Normal"],
            fontSize=12, textColor=colors.HexColor(MID),
            spaceAfter=5, alignment=TA_CENTER, leading=16,
        ),
        "h1": ParagraphStyle(
            "h1", parent=base["Heading1"],
            fontSize=18, textColor=colors.HexColor(DARK),
            spaceBefore=18, spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "h2", parent=base["Heading2"],
            fontSize=13, textColor=colors.HexColor(ACCENT),
            spaceBefore=12, spaceAfter=5,
        ),
        "h3": ParagraphStyle(
            "h3", parent=base["Heading3"],
            fontSize=11, textColor=colors.HexColor(DARK),
            fontName="Helvetica-Bold", spaceBefore=8, spaceAfter=3,
        ),
        "body": ParagraphStyle(
            "body", parent=base["Normal"],
            fontSize=10, leading=15, textColor=colors.HexColor(DARK),
            alignment=TA_JUSTIFY, spaceAfter=7,
        ),
        "list": ParagraphStyle(
            "list", parent=base["Normal"],
            fontSize=10, leading=15, textColor=colors.HexColor(DARK),
            leftIndent=16, spaceAfter=3,
        ),
        "quote": ParagraphStyle(
            "quote", parent=base["Normal"],
            fontSize=10, leading=15, textColor=colors.HexColor(MID),
            leftIndent=14, fontName="Helvetica-Oblique", spaceAfter=7,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base["Normal"],
            fontSize=8.5, leading=12, textColor=colors.HexColor(MID),
            alignment=TA_CENTER, spaceAfter=14,
        ),
        "code": ParagraphStyle(
            "code", parent=base["Code"],
            fontSize=8, leading=10.5, textColor=colors.HexColor(DARK),
            fontName="Courier", spaceAfter=0,
        ),
        "table_header": ParagraphStyle(
            "table_header", parent=base["Normal"],
            fontSize=9, leading=12, textColor=colors.white,
            fontName="Helvetica-Bold",
        ),
        "table_body": ParagraphStyle(
            "table_body", parent=base["Normal"],
            fontSize=9, leading=12, textColor=colors.HexColor(DARK),
        ),
    }


_STYLES = _build_styles()


# ── Inline + helpers ──────────────────────────────────────────────────────────

def _esc(text: str) -> str:
    """Escape characters reportlab's mini-XML parser would choke on."""
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _md_inline(text: str) -> str:
    """Escape, then convert inline markdown (bold/italic/code/links) to markup.

    Code spans are pulled out first so their literal ``*`` characters aren't
    mistaken for bold/italic markers, then reinserted after."""
    text = _esc(text)
    spans: list[str] = []

    def _stash(m):
        spans.append(m.group(1))
        return f"\x00{len(spans) - 1}\x00"

    text = re.sub(r"`([^`]+)`", _stash, text)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"(?<!\*)\*([^*\n]+?)\*(?!\*)", r"<i>\1</i>", text)
    # [text](target) → just the text (these docs link to sibling files, not URLs)
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    text = re.sub(r"\x00(\d+)\x00",
                  lambda m: f'<font name="Courier">{spans[int(m.group(1))]}</font>',
                  text)
    return text


def _img(path, width=None, max_height=None):
    if not os.path.exists(path):
        return Paragraph(f"[Missing image: {_esc(path)}]", _STYLES["caption"])
    if width is None:
        width = CONTENT_W
    ri = Image(path)
    aspect = ri.imageHeight / ri.imageWidth
    ri.drawWidth, ri.drawHeight = width, width * aspect
    if max_height and ri.drawHeight > max_height:
        ri.drawHeight, ri.drawWidth = max_height, max_height / aspect
    ri.hAlign = "CENTER"
    return ri


def _table(rows):
    n_cols = max(len(r) for r in rows)
    col_w = CONTENT_W / n_cols
    style = [
        ("BACKGROUND",     (0, 0), (-1, 0), colors.HexColor(ACCENT)),
        ("FONTSIZE",       (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.HexColor("#f7f7f5"), colors.white]),
        ("GRID",           (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("VALIGN",         (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",     (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",  (0, 0), (-1, -1), 5),
        ("LEFTPADDING",    (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",   (0, 0), (-1, -1), 6),
    ]
    return Table(rows, colWidths=[col_w] * n_cols, style=TableStyle(style))


# ── Markdown → flowables ──────────────────────────────────────────────────────

def _flush_para(buf, out):
    if buf:
        joined = " ".join(line.strip() for line in buf)
        out.append(Paragraph(_md_inline(joined), _STYLES["body"]))
        buf.clear()


def _emit_table(lines, out):
    rows = []
    for i, line in enumerate(lines):
        line = line.strip()
        if re.match(r"^\|[\s\-:|]+\|$", line):   # |---|---| separator
            continue
        style = _STYLES["table_header"] if i == 0 else _STYLES["table_body"]
        cells = [Paragraph(_md_inline(c.strip()), style)
                 for c in line.split("|")[1:-1]]
        rows.append(cells)
    if rows:
        out.append(Spacer(1, 0.08 * inch))
        out.append(_table(rows))
        out.append(Spacer(1, 0.04 * inch))


def md_to_flowables(md: str) -> list:
    """Convert a full Markdown document body to reportlab flowables."""
    out: list = []
    para: list[str] = []
    lines = md.split("\n")
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]
        stripped = line.strip()

        # Fenced code block ---------------------------------------------------
        if stripped.startswith("```"):
            _flush_para(para, out)
            code: list[str] = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # skip closing fence
            block = "\n".join(code) if code else " "
            out.append(Spacer(1, 0.04 * inch))
            out.append(Preformatted(_esc(block), _STYLES["code"]))
            out.append(Spacer(1, 0.06 * inch))
            continue

        # Blank line ----------------------------------------------------------
        if not stripped:
            _flush_para(para, out)
            i += 1
            continue

        # Headings ------------------------------------------------------------
        m = re.match(r"^(#{1,4})\s+(.*)$", stripped)
        if m:
            _flush_para(para, out)
            level = len(m.group(1))
            style = {1: "h1", 2: "h2", 3: "h3", 4: "h3"}[level]
            if level == 1 and out:           # each Part starts a fresh page
                out.append(PageBreak())
            out.append(Paragraph(_md_inline(m.group(2)), _STYLES[style]))
            i += 1
            continue

        # Horizontal rule -----------------------------------------------------
        if re.match(r"^-{3,}$", stripped):
            _flush_para(para, out)
            out.append(Spacer(1, 0.04 * inch))
            out.append(HRFlowable(width="100%", thickness=0.5,
                                  color=colors.HexColor("#dddddd"), spaceAfter=8))
            i += 1
            continue

        # Image (own line) ----------------------------------------------------
        im = re.match(r"^!\[([^\]]*)\]\(([^)]+)\)", stripped)
        if im:
            _flush_para(para, out)
            out.append(Spacer(1, 0.08 * inch))
            out.append(KeepTogether([
                _img(im.group(2)),
                Spacer(1, 4),
                Paragraph(_md_inline(im.group(1)), _STYLES["caption"]),
            ]))
            i += 1
            continue

        # Table ---------------------------------------------------------------
        if stripped.startswith("|"):
            _flush_para(para, out)
            tbl = []
            while i < n and lines[i].strip().startswith("|"):
                tbl.append(lines[i])
                i += 1
            _emit_table(tbl, out)
            continue

        # Blockquote ----------------------------------------------------------
        if stripped.startswith(">"):
            _flush_para(para, out)
            quote = []
            while i < n and lines[i].strip().startswith(">"):
                quote.append(lines[i].strip().lstrip(">").strip())
                i += 1
            out.append(Paragraph(_md_inline(" ".join(quote)), _STYLES["quote"]))
            continue

        # Bulleted list item --------------------------------------------------
        bm = re.match(r"^[-*]\s+(.*)$", stripped)
        if bm:
            _flush_para(para, out)
            out.append(Paragraph("•&nbsp;&nbsp;" + _md_inline(bm.group(1)),
                                 _STYLES["list"]))
            i += 1
            continue

        # Ordered list item ---------------------------------------------------
        om = re.match(r"^(\d+)\.\s+(.*)$", stripped)
        if om:
            _flush_para(para, out)
            out.append(Paragraph(f"{om.group(1)}.&nbsp;&nbsp;"
                                 + _md_inline(om.group(2)), _STYLES["list"]))
            i += 1
            continue

        # Plain paragraph text ------------------------------------------------
        para.append(line)
        i += 1

    _flush_para(para, out)
    return out


# ── Cover + footer ────────────────────────────────────────────────────────────

def _cover(title: str) -> list:
    return [
        Spacer(1, 1.4 * inch),
        Paragraph(_md_inline(title), _STYLES["cover_title"]),
        Spacer(1, 0.2 * inch),
        HRFlowable(width="60%", thickness=0.6, color=colors.HexColor("#dddddd")),
        Spacer(1, 0.2 * inch),
        Paragraph(f"Generated {datetime.now().strftime('%B %d, %Y')}",
                  _STYLES["cover_sub"]),
        PageBreak(),
    ]


def _draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor(MID))
    canvas.drawCentredString(PAGE_W / 2.0, 0.5 * inch, str(canvas.getPageNumber()))
    canvas.restoreState()


# ── Main ──────────────────────────────────────────────────────────────────────

def build(md_path: str, output_path: str | None = None) -> str:
    if not os.path.exists(md_path):
        sys.exit(f"ERROR: {md_path} not found")
    with open(md_path) as f:
        md = f.read()

    # Title = first level-1 heading; drop it from the body so it isn't repeated.
    title_m = re.search(r"^#\s+(.*)$", md, flags=re.MULTILINE)
    title = title_m.group(1).strip() if title_m else os.path.basename(md_path)
    if title_m:
        md = md[:title_m.start()] + md[title_m.end():]

    if output_path is None:
        output_path = os.path.splitext(md_path)[0] + ".pdf"

    story = [*_cover(title), *md_to_flowables(md)]
    SimpleDocTemplate(
        output_path, pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN, bottomMargin=MARGIN,
        title=title, author="Justin Pietsch",
    ).build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    print(f"Saved → {output_path}")
    return output_path


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit("usage: python3 generate_doc_pdf.py <markdown_file> [output.pdf]")
    build(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else None)
