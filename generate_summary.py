#!/usr/bin/env python3
"""
generate_summary.py — 3-page visual summary PDF for general sports fans.

Narrative text and image placement are read from SUMMARY.md.
Run after generating the summary PNGs:
    MPLBACKEND=Agg python3 nba_home_court_summary_plots.py
    python3 generate_summary.py
"""

import os
import re
import sys
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable,
    Image,
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

PAGE_W, PAGE_H = letter
MARGIN    = 0.85 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

DARK   = "#2c2c2a"
MID    = "#666666"
ORANGE = "#e8a33d"

SUMMARY_PATH = "SUMMARY.md"
SUMMARY_PNGS = [
    "summary_decline.png",
    "summary_whistle.png",
    "summary_3point.png",
    "summary_franchises.png",
]


def _check_prerequisites():
    missing = [p for p in SUMMARY_PNGS if not os.path.exists(p)]
    if missing:
        print("ERROR: Missing PNGs. Run the summary plots generator first:")
        print("  MPLBACKEND=Agg python3 nba_home_court_summary_plots.py")
        print("\nMissing files:")
        for p in missing:
            print(f"  {p}")
        sys.exit(1)
    if not os.path.exists(SUMMARY_PATH):
        print(f"ERROR: {SUMMARY_PATH} not found.")
        sys.exit(1)


def _build_styles():
    base = getSampleStyleSheet()
    return {
        "cover_title": ParagraphStyle(
            "cover_title", parent=base["Normal"],
            fontSize=32, fontName="Helvetica-Bold",
            textColor=colors.HexColor(DARK),
            leading=38, spaceAfter=6, alignment=TA_CENTER,
        ),
        "cover_stat": ParagraphStyle(
            "cover_stat", parent=base["Normal"],
            fontSize=24, fontName="Helvetica-Bold",
            textColor=colors.HexColor(ORANGE),
            leading=30, spaceAfter=8, alignment=TA_CENTER,
        ),
        "cover_hook": ParagraphStyle(
            "cover_hook", parent=base["Normal"],
            fontSize=13, leading=18,
            textColor=colors.HexColor(MID),
            spaceAfter=0, alignment=TA_CENTER,
        ),
        "page_headline": ParagraphStyle(
            "page_headline", parent=base["Normal"],
            fontSize=16, fontName="Helvetica-Bold",
            textColor=colors.HexColor(DARK),
            leading=20, spaceBefore=6, spaceAfter=4,
        ),
        "caption": ParagraphStyle(
            "caption", parent=base["Normal"],
            fontSize=9, leading=13,
            textColor=colors.HexColor(MID),
            spaceAfter=8, alignment=TA_CENTER,
        ),
        "verdict_head": ParagraphStyle(
            "verdict_head", parent=base["Normal"],
            fontSize=14, fontName="Helvetica-Bold",
            textColor=colors.HexColor(DARK),
            leading=18, spaceBefore=8, spaceAfter=5,
        ),
        "verdict_body": ParagraphStyle(
            "verdict_body", parent=base["Normal"],
            fontSize=11, leading=16,
            textColor=colors.HexColor(DARK),
            spaceAfter=6,
        ),
        "source": ParagraphStyle(
            "source", parent=base["Normal"],
            fontSize=8.5, leading=12,
            textColor=colors.HexColor(MID),
            spaceBefore=8, spaceAfter=0, alignment=TA_CENTER,
        ),
    }


def _md_inline(text):
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'\*([^*\n]+?)\*', r'<i>\1</i>', text)
    return text


def _img(path, max_height=None):
    if not os.path.exists(path):
        return Paragraph(f"[Missing image: {path}]", getSampleStyleSheet()["Normal"])
    ri = Image(path)
    aspect = ri.imageHeight / ri.imageWidth
    ri.drawWidth  = CONTENT_W
    ri.drawHeight = CONTENT_W * aspect
    if max_height and ri.drawHeight > max_height:
        ri.drawHeight = max_height
        ri.drawWidth  = max_height / aspect
    ri.hAlign = "CENTER"
    return ri


def _hr():
    return HRFlowable(width="100%", thickness=0.5,
                      color=colors.HexColor("#dddddd"), spaceAfter=6)


def _page_to_flowables(page_text, is_cover, S):
    """Convert one page's markdown text into reportlab flowables."""
    flowables = []
    blocks = re.split(r'\n{2,}', page_text.strip())
    headline_count = 0
    image_seen = False

    for block in blocks:
        block = block.strip()
        if not block:
            continue

        if block.startswith('# '):
            flowables.append(Spacer(1, 0.2 * inch))
            flowables.append(Paragraph(_md_inline(block[2:]), S["cover_title"]))

        elif block.startswith('## '):
            text = _md_inline(block[3:])
            if is_cover:
                flowables.append(Paragraph(text, S["cover_stat"]))
            else:
                if headline_count > 0:
                    flowables += [Spacer(1, 0.1 * inch), _hr(), Spacer(1, 0.06 * inch)]
                flowables.append(Paragraph(text, S["page_headline"] if image_seen or headline_count == 0
                                           else S["verdict_head"]))
                headline_count += 1

        elif block.startswith('!['):
            m = re.match(r'!\[([^\]]*)\]\(([^)]+)\)(?:\{([^}]+)\})?', block)
            if m:
                opts = dict(kv.split('=') for kv in (m.group(3) or '').split() if '=' in kv)
                mh = PAGE_H * float(opts['height']) if 'height' in opts else None
                if is_cover and not image_seen:
                    flowables += [Spacer(1, 0.15 * inch), _hr(), Spacer(1, 0.1 * inch)]
                else:
                    flowables.append(Spacer(1, 0.05 * inch))
                flowables.append(_img(m.group(2), max_height=mh))
                flowables.append(Spacer(1, 4))
                flowables.append(Paragraph(_md_inline(m.group(1)), S["caption"]))
                image_seen = True

        else:
            text = _md_inline(block)
            if is_cover and not image_seen:
                flowables += [Spacer(1, 0.05 * inch),
                              Paragraph(text, S["cover_hook"])]
            else:
                style = S["verdict_head"] if text.isupper() else S["verdict_body"]
                flowables.append(Paragraph(text, style))

    return flowables


def _draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor(MID))
    canvas.drawCentredString(PAGE_W / 2.0, 0.45 * inch, str(canvas.getPageNumber()))
    canvas.restoreState()


def build_summary(output="nba_home_court_advantage_summary.pdf"):
    _check_prerequisites()
    S = _build_styles()

    with open(SUMMARY_PATH) as f:
        content = f.read()

    pages = re.split(r'\n---\n', content)

    story = []
    for i, page_text in enumerate(pages):
        story += _page_to_flowables(page_text, is_cover=(i == 0), S=S)
        if i == 0:
            story.append(Paragraph("Justin Pietsch", S["cover_hook"]))
        if i < len(pages) - 1:
            story.append(PageBreak())

    story.append(Paragraph(
        f"Data: NBA.com  ·  51,089 games  ·  1983–84 through 2024–25  "
        f"·  Generated {datetime.now().strftime('%B %d, %Y')}",
        S["source"],
    ))

    doc = SimpleDocTemplate(
        output,
        pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title="NBA Home Court Advantage — A 40-Year Decline (Visual Summary)",
        author="Justin Pietsch",
    )
    doc.build(story, onFirstPage=_draw_footer, onLaterPages=_draw_footer)
    print(f"Saved → {output}")


if __name__ == "__main__":
    build_summary()
