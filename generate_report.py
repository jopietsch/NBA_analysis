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
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
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
MARGIN = 0.85 * inch
CONTENT_W = PAGE_W - 2 * MARGIN

DARK   = "#2c2c2a"
MID    = "#666666"
BLUE   = "#1f77b4"
ACCENT = BLUE

FINDINGS_PATH = "FINDINGS.md"
RESULTS_PATH  = "RESULTS.md"


# ── Style sheet ───────────────────────────────────────────────────────────────

def _styles():
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
    }


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


def _md_to_flowables(text: str, s: dict) -> list:
    """Convert a FINDINGS.md section body to a list of reportlab flowables."""
    flowables = []
    for block in re.split(r'\n{2,}', text):
        block = block.strip()
        if not block:
            continue
        if block.startswith('### '):
            flowables.append(Paragraph(_md_inline(block[4:]), s['h2']))
        elif block.startswith('- '):
            for line in block.splitlines():
                if line.startswith('- '):
                    flowables.append(Paragraph('• ' + _md_inline(line[2:]), s['body']))
        else:
            joined = ' '.join(ln.strip() for ln in block.splitlines() if ln.strip())
            flowables.append(Paragraph(_md_inline(joined), s['body']))
    return flowables


# ── Layout helpers ────────────────────────────────────────────────────────────

def _img(path, width=None):
    if not os.path.exists(path):
        return Paragraph(f"[Missing image: {path}]", _styles()["note"])
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
        Paragraph(caption_text, _styles()["caption"]),
    ])


def _section_header(title: str, s: dict, sections: dict) -> list:
    return [
        Paragraph(title, s["h1"]),
        _hr(),
        *_md_to_flowables(sections.get(title, ""), s),
    ]


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


# ── Report sections ───────────────────────────────────────────────────────────

def _cover(s, sections):
    toc_data = []
    for heading in sections:
        parts = heading.split('. ', 1)
        if len(parts) == 2 and parts[0].isdigit():
            toc_data.append([parts[0] + '.', parts[1]])
    toc_data.append(['A.', 'Appendix: Full Regression Output'])

    return [
        Spacer(1, 1.2 * inch),
        Paragraph("NBA Home Court Advantage", s["cover_title"]),
        Paragraph("A 40-Year Decline", s["cover_sub"]),
        Spacer(1, 0.25 * inch),
        _hr(),
        Spacer(1, 0.15 * inch),
        Paragraph(
            "Data: NBA.com via nba_api  ·  1983–84 through 2024–25  ·  51,089 games",
            s["cover_sub"],
        ),
        Paragraph(
            f"Generated {datetime.now().strftime('%B %d, %Y at %H:%M')}",
            s["cover_sub"],
        ),
        Spacer(1, 0.8 * inch),
        Paragraph("Contents", s["h2"]),
        Table(
            [[Paragraph(num, s["toc_num"]), Paragraph(title, s["toc_title"])]
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


def _section_decline(s, sections):
    return [
        *_section_header("1. The Decline", s, sections),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_advantage_season.png",
            "Figure 1. Home win % per season, 1983–84 through 2024–25. "
            "Blue = regular season, green = playoffs. "
            "Dashed lines are overall trend fits. Background shading marks rule-change eras.",
        ),
    ]


def _section_era(s, sections):
    era_img    = _img("nba_home_court_advantage_era_bars.png",    width=CONTENT_W * 0.49)
    format_img = _img("nba_home_court_advantage_format_bars.png", width=CONTENT_W * 0.49)
    side_by_side = Table(
        [[era_img, format_img]],
        colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5],
        style=TableStyle([("ALIGN",  (0, 0), (-1, -1), "CENTER"),
                          ("VALIGN", (0, 0), (-1, -1), "TOP")]),
    )
    return [
        *_section_header("2. Era and Format Period Analysis", s, sections),
        Spacer(1, 0.1 * inch),
        KeepTogether([
            side_by_side,
            Spacer(1, 4),
            Paragraph(
                "Figure 2. Left: average home win % by rule-change era. "
                "Right: average home win % by playoff format period. "
                "Blue = regular season, green = playoffs.",
                s["caption"],
            ),
        ]),
    ]


def _section_era_lines(s, sections):
    return [
        *_section_header("3. Per-Era Trend Lines", s, sections),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_advantage_regular_era.png",
            "Figure 3. Regular-season home win % per season. A separate trend line is fit "
            "within each rule-change era. Background shading identifies each era.",
        ),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_advantage_playoffs_era.png",
            "Figure 4. Playoff home win % per season with a separate trend line per era. "
            "Vertical markers indicate playoff format changes (1985, 2003, 2014).",
        ),
    ]


def _section_regression(s, sections):
    return [
        PageBreak(),
        *_section_header("4. What Explains the Decline?", s, sections),
    ]


def _section_rest(s, sections):
    return [
        PageBreak(),
        *_section_header("5. Rest and Schedule Balance", s, sections),
        _chart(
            "nba_home_court_advantage_rest.png",
            "Figure 5. Regular-season rest analysis. "
            "Top: back-to-back rate per season for home and away teams. "
            "Bottom: home win % split by rest differential — home-more-rest vs equal vs away-more-rest.",
        ),
        _chart(
            "nba_home_court_advantage_rest_playoffs.png",
            "Figure 6. Playoff rest analysis. First-round games are excluded because rest "
            "cannot be computed from a prior playoff game. Rest effects are larger in the playoffs.",
        ),
    ]


def _section_differentials(s, sections):
    return [
        PageBreak(),
        *_section_header("6. Box-Score Differentials", s, sections),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_advantage_differentials.png",
            "Figure 7. Per-season home-minus-away box-score differentials, 1983–84 through 2024–25. "
            "Solid = regular season, dashed = playoffs. Dotted overlays are trend lines. "
            "Negative foul diff = home team called for fewer fouls.",
        ),
    ]


def _section_shot_zones(s, sections):
    return [
        PageBreak(),
        *_section_header("7. Shot Zone Analysis", s, sections),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_shot_zones.png",
            "Figure 8. Home-minus-road shot zone % differentials, 1996–97 through 2024–25. "
            "Solid = regular season, dashed = playoffs. "
            "RA = restricted area (within ~4 ft of the basket).",
        ),
    ]


def _section_series_breakdown(s, sections):
    return [
        PageBreak(),
        *_section_header("8. Playoff Series Structure", s, sections),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_series_breakdown.png",
            "Figure 8. Home win % by game number within playoff series. "
            "Left: pooled G1–G7 home win % with sample sizes and overall playoff baseline. "
            "Right: G1–G7 home win % split by era (six lines, era-colored).",
        ),
    ]


def _section_margin(s, sections):
    return [
        PageBreak(),
        *_section_header("9. Win Margin Trends", s, sections),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_margin.png",
            "Figure 9. Home team point margin per season. "
            "Left: mean margin for all games (regular season and playoffs) with trend lines. "
            "Center: mean margin split by home wins vs. losses (regular season). "
            "Right: era-bucketed average margin, regular season vs. playoffs.",
        ),
    ]


def _section_parity(s, sections):
    return [
        PageBreak(),
        *_section_header("10. Competitive Balance and Parity", s, sections),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_parity.png",
            "Figure 10. Competitive balance and home court advantage. "
            "Left: home win % (blue, left axis) and team win% std dev (red, right axis) "
            "over time — lower std dev = more equal league. "
            "Right: scatter of parity std dev vs. home win % per season, colored by era, "
            "with trend line.",
        ),
    ]


def _section_travel(s, sections):
    return [
        PageBreak(),
        *_section_header("11. Travel Distance", s, sections),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_travel.png",
            "Figure 11. Home win % by away team travel distance (regular season). "
            "Left: per-season home win % for each distance bucket with trend lines. "
            "Right: era-averaged home win % by distance bucket.",
        ),
    ]


def _section_summary(s, sections):
    rank_data = [
        ["Rank", "Factor",                        "Regular season",           "Playoffs"             ],
        ["1",    "Era (structural decline)",       "Dominant — majority of fit", "Larger decline"     ],
        ["2",    "Foul diff (refs more neutral)",  "Significant, *** trend",   "Significant, ** trend"],
        ["3",    "Altitude — DEN / UTA",           "Significant, ***",         "Not significant"      ],
        ["4",    "eFG% edge shrinking",            "Significant, *** trend",   "Smaller decline"      ],
        ["5",    "Rest differential",              "Significant, ***",         "Larger effect, *"     ],
        ["6",    "3PA rate convergence",           "Significant, *** trend",   "Significant, * trend" ],
        ["7",    "Paint access (shot zones)",      "Declining (1996– )",       "Noisy"                ],
        ["8",    "Time zone",                      "Not significant",          "Not significant"      ],
    ]
    cw = [CONTENT_W * f for f in (0.06, 0.33, 0.31, 0.30)]
    return [
        PageBreak(),
        *_section_header("12. Summary", s, sections),
        Spacer(1, 0.1 * inch),
        _table(rank_data, cw),
        Spacer(1, 0.3 * inch),
        _hr(),
        Paragraph(
            "Data: NBA.com via nba_api. Analysis covers 1983–84 through 2024–25. "
            "Shot zone data available from 1996–97. "
            "Logistic regression uses McFadden R²; marginal effects at the mean. "
            "See Appendix A for full tables and coefficient values.",
            s["note"],
        ),
    ]


def _appendix_results(s):
    return [
        PageBreak(),
        Paragraph("Appendix A: Full Regression Output", s["h1"]),
        _hr(),
        Paragraph(
            "Auto-generated by <font name=\"Courier\">nba_home_court_regression.py</font> "
            "each time the analysis is run. Contains the sequential R² decomposition, "
            "pre/post-2014 coefficient stability check, bivariate factor significance table, "
            "and foul/shooting differential trends by era.",
            s["body"],
        ),
        Spacer(1, 0.1 * inch),
        Preformatted(_results_text(), s["code"]),
    ]


# ── Main ──────────────────────────────────────────────────────────────────────

def build_report(output_path="nba_home_court_advantage_report.pdf"):
    s = _styles()
    sections = _parse_findings()

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title="NBA Home Court Advantage — A 40-Year Decline",
        author="Justin Pietsch",
    )

    story = []
    story += _cover(s, sections)
    story += _section_decline(s, sections)
    story += _section_era(s, sections)
    story += _section_era_lines(s, sections)
    story += _section_regression(s, sections)
    story += _section_rest(s, sections)
    story += _section_differentials(s, sections)
    story += _section_shot_zones(s, sections)
    story += _section_series_breakdown(s, sections)
    story += _section_margin(s, sections)
    story += _section_parity(s, sections)
    story += _section_travel(s, sections)
    story += _section_summary(s, sections)
    story += _appendix_results(s)

    doc.build(story)
    print(f"Saved → {output_path}")


if __name__ == "__main__":
    build_report()
