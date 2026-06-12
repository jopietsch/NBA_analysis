#!/usr/bin/env python3
"""
generate_summary.py — 3-page visual summary PDF for general sports fans.

Run after generating the summary PNGs:
    MPLBACKEND=Agg python3 nba_home_court_summary_plots.py
    python3 generate_summary.py
"""

import os
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
        "verdict_bullet": ParagraphStyle(
            "verdict_bullet", parent=base["Normal"],
            fontSize=11, leading=16,
            textColor=colors.HexColor(DARK),
            leftIndent=14, spaceAfter=3,
        ),
        "source": ParagraphStyle(
            "source", parent=base["Normal"],
            fontSize=8.5, leading=12,
            textColor=colors.HexColor(MID),
            spaceBefore=8, spaceAfter=0, alignment=TA_CENTER,
        ),
    }


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


def _draw_footer(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor(MID))
    canvas.drawCentredString(PAGE_W / 2.0, 0.45 * inch, str(canvas.getPageNumber()))
    canvas.restoreState()


def build_summary(output="nba_home_court_advantage_summary.pdf"):
    _check_prerequisites()
    S = _build_styles()

    story = []

    # ── Page 1: Cover + The Decline ───────────────────────────────────────────
    story += [
        Spacer(1, 0.2 * inch),
        Paragraph("NBA Home Court Advantage", S["cover_title"]),
        Paragraph("A 40-Year Decline", S["cover_stat"]),
        Spacer(1, 0.05 * inch),
        Paragraph(
            "Home teams used to win nearly two-thirds of their games. "
            "Now they barely win more than half. "
            "Here is where that 10-point edge went.",
            S["cover_hook"],
        ),
        Spacer(1, 0.15 * inch),
        _hr(),
        Spacer(1, 0.1 * inch),
        _img("summary_decline.png", max_height=PAGE_H * 0.50),
        Spacer(1, 4),
        Paragraph(
            "Regular season (blue) and playoffs (green), 1983–84 through 2024–25. "
            "Dashed lines are long-run trend fits.",
            S["caption"],
        ),
        PageBreak(),
    ]

    # ── Page 2: The Two Causes ────────────────────────────────────────────────
    story += [
        Paragraph("THE WHISTLE MOVED — AND THEN IT STOPPED", S["page_headline"]),
        Spacer(1, 0.05 * inch),
        _img("summary_whistle.png", max_height=PAGE_H * 0.34),
        Spacer(1, 4),
        Paragraph(
            "Left: home team's foul-call edge per season (regular season and playoffs). "
            "Right: each dot is one career playoff official — green means that referee "
            "called fewer fouls on home teams across their entire career.",
            S["caption"],
        ),
        Spacer(1, 0.1 * inch),
        _hr(),
        Spacer(1, 0.06 * inch),
        Paragraph("THE 3-POINT REVOLUTION CHANGED EVERYTHING", S["page_headline"]),
        Spacer(1, 0.05 * inch),
        _img("summary_3point.png", max_height=PAGE_H * 0.34),
        Spacer(1, 4),
        Paragraph(
            "Left: 3-point attempt rate (orange) and home win % (blue) over 40 years — "
            "near-perfect mirror images. "
            "Right: one dot per season; as 3PA rate rose, home court fell.",
            S["caption"],
        ),
        PageBreak(),
    ]

    # ── Page 3: Franchise Rankings + Verdict ─────────────────────────────────
    story += [
        Paragraph("SOME ARENAS ARE STILL FORTRESSES", S["page_headline"]),
        Spacer(1, 0.05 * inch),
        _img("summary_franchises.png", max_height=PAGE_H * 0.39),
        Spacer(1, 4),
        Paragraph(
            "All-time regular-season home win% minus road win% per franchise. "
            "Every franchise has a positive gap — home court always helps. "
            "Denver and Utah lead, boosted by altitude.",
            S["caption"],
        ),
        Spacer(1, 0.04 * inch),
        _hr(),
        Spacer(1, 0.03 * inch),
        Paragraph("THE SHORT VERSION", S["verdict_head"]),
        Paragraph(
            "The crowd used to move the whistle. Refs would call a foul on the road player "
            "where they might let it go at home — and that 1.2-foul-per-game edge, night "
            "after night, added up to a 10-point win-rate advantage across a full season. "
            "Now refs call it almost dead even. The crowd is still loud. It just doesn't "
            "move the whistle the way it once did.",
            S["verdict_body"],
        ),
        Paragraph(
            "The 3-point revolution made it worse. The crowd's influence mattered most at "
            "the rim, where the foul-or-no-call is most subjective. As offenses moved "
            "outside the arc, those moments became rarer — and every possession became "
            "higher-variance, which favors the underdog (usually the road team).",
            S["verdict_body"],
        ),
        Paragraph(
            "Two popular explanations the data rules out: faster pace (the 1984 NBA played "
            "at today's speed — home court was 10 points higher) and a more equal league "
            "(the Jordan-era 1990s were highly unequal, and the decline was already "
            "well underway).",
            S["verdict_body"],
        ),
        Paragraph(
            f"Data: NBA.com  ·  51,089 games  ·  1983–84 through 2024–25  "
            f"·  Generated {datetime.now().strftime('%B %d, %Y')}",
            S["source"],
        ),
    ]

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
