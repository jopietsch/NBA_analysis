#!/usr/bin/env python3
"""
Generate a PDF report of the NBA home court advantage analysis.
Run after nba_home_court_advantage.py — all PNGs must already exist.

    python3 generate_report.py
"""

import os

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
GREEN  = "#2ca02c"
ACCENT = BLUE


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
        "note": ParagraphStyle(
            "note", parent=base["Normal"],
            fontSize=8.5, leading=12,
            textColor=colors.HexColor(MID),
            spaceAfter=5,
        ),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def _img(path, width=None):
    """Load a PNG and scale to `width` preserving aspect ratio."""
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
    """Build a styled table with a blue header row."""
    style = [
        ("BACKGROUND",    (0, 0), (-1, header_rows - 1), colors.HexColor(ACCENT)),
        ("TEXTCOLOR",     (0, 0), (-1, header_rows - 1), colors.white),
        ("FONTNAME",      (0, 0), (-1, header_rows - 1), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS",(0, header_rows), (-1, -1),
         [colors.HexColor("#f7f7f5"), colors.white]),
        ("GRID",          (0, 0), (-1, -1), 0.5, colors.HexColor("#dddddd")),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
    ]
    return Table(data, colWidths=col_widths, style=TableStyle(style))


def _chart(path, caption_text, width=None):
    """Return a KeepTogether block: image + caption."""
    return KeepTogether([
        _img(path, width=width),
        Spacer(1, 4),
        Paragraph(caption_text, _styles()["caption"]),
    ])


# ── Report sections ──────────────────────────────────────────────────────────

def _cover(s):
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
        Spacer(1, 0.8 * inch),
        Paragraph(
            "This report examines how home court advantage has changed over four decades of "
            "NBA basketball, quantifies the size of the decline, and investigates the statistical "
            "mechanisms behind it — including officiating patterns, shooting efficiency, shot "
            "selection, rest, altitude, and travel.",
            s["body"],
        ),
        Spacer(1, 0.2 * inch),
        Paragraph("Contents", s["h2"]),
        Paragraph(
            "1. The Decline &nbsp;&nbsp; 2. Era and Format Period Analysis &nbsp;&nbsp; "
            "3. Per-Era Trend Lines &nbsp;&nbsp; 4. What Explains the Decline? &nbsp;&nbsp; "
            "5. Rest and Schedule Balance &nbsp;&nbsp; 6. Box-Score Differentials &nbsp;&nbsp; "
            "7. Shot Zone Analysis &nbsp;&nbsp; 8. Summary",
            s["body"],
        ),
        PageBreak(),
    ]


def _section_decline(s):
    return [
        Paragraph("1. The Decline", s["h1"]),
        _hr(),
        Paragraph(
            "Home court advantage in the NBA has been falling for 40 years. In the 1984–94 era "
            "home teams won roughly 65% of regular-season games. Today that figure sits at 56–57%. "
            "The decline is even steeper in the playoffs: from roughly 68–70% in the early era to "
            "57–59% in recent seasons.",
            s["body"],
        ),
        Paragraph(
            "The chart below shows home win percentage per season for both the regular season "
            "(blue) and playoffs (green), with overall trend lines and background shading marking "
            "each rule-change era. COVID-impacted seasons (2019–20 and 2020–21) are highlighted "
            "in red. The 2020 bubble playoffs — all neutral-site games — are excluded.",
            s["body"],
        ),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_advantage_season.png",
            "Figure 1. Home win % per season, 1983–84 through 2024–25. "
            "Blue = regular season, green = playoffs. "
            "Dashed lines are overall trend fits. Background shading marks rule-change eras.",
        ),
    ]


def _section_era(s):
    era_img    = _img("nba_home_court_advantage_era_bars.png",    width=CONTENT_W * 0.49)
    format_img = _img("nba_home_court_advantage_format_bars.png", width=CONTENT_W * 0.49)
    side_by_side = Table(
        [[era_img, format_img]],
        colWidths=[CONTENT_W * 0.5, CONTENT_W * 0.5],
        style=TableStyle([("ALIGN", (0, 0), (-1, -1), "CENTER"),
                          ("VALIGN", (0, 0), (-1, -1), "TOP")]),
    )
    return [
        Paragraph("2. Era and Format Period Analysis", s["h1"]),
        _hr(),
        Paragraph(
            "The NBA has gone through six distinct rule-change eras since 1984, each affecting "
            "pace, defense, and officiating. The bar charts below show average home win % within "
            "each era (left) and within each of the four playoff-format periods defined by the "
            "1985, 2003, and 2014 Finals scheduling changes (right).",
            s["body"],
        ),
        Paragraph(
            "Home court advantage has declined in nearly every successive era in both the regular "
            "season and the playoffs. The steepest drops are in the 2018–22 and 2023–25 eras. "
            "The format-period panel shows that the 2014 Finals shift from a 2-3-2 to a 2-2-1-1-1 "
            "series structure coincided with a sharp fall in playoff home win %, though isolating "
            "format effects from the broader secular trend is difficult.",
            s["body"],
        ),
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


def _section_era_lines(s):
    return [
        Paragraph("3. Per-Era Trend Lines", s["h1"]),
        _hr(),
        Paragraph(
            "Fitting a separate trend line within each era reveals that the decline is not a "
            "smooth drift — there are periods of relative stability and periods of sharper change. "
            "Playoff home court advantage has consistently exceeded the regular-season figure but "
            "has converged dramatically in recent years.",
            s["body"],
        ),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_advantage_regular_era.png",
            "Figure 3. Regular-season home win % per season. A separate OLS trend line is fit "
            "within each rule-change era. Background shading identifies each era.",
        ),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_advantage_playoffs_era.png",
            "Figure 4. Playoff home win % per season with a separate OLS trend line per era. "
            "Vertical markers indicate playoff format changes (1985, 2003, 2014).",
        ),
    ]


def _section_regression(s):
    r2_data = [
        ["Factor added",              "McFadden R²", "ΔR²",     "% of fit"],
        ["Era only",                  "0.0028",      "+0.0028",  "55.8%"],
        ["+ Rest differential",       "0.0036",      "+0.0008",  "16.3%"],
        ["+ Altitude (DEN / UTA)",    "0.0049",      "+0.0012",  "24.9%"],
        ["+ Time zone diff",          "0.0050",      "+0.0001",   "2.0%"],
        ["+ COVID flag",              "0.0050",      "+0.0000",   "1.0%"],
    ]
    factor_data = [
        ["Factor",                        "Reg-season effect", "Sig.",    "Playoff effect",   "Sig."],
        ["Rest (per day of advantage)",   "+1.5 pp",           "***",     "+2.3 pp",          "*"  ],
        ["Altitude — Denver / Utah home", "+8.2 pp",           "***",     "−1.8 pp",          "n.s."],
        ["Time zone diff (per zone)",     "−0.4 pp",           "n.s.",    "+1.2 pp",          "n.s."],
    ]
    cw1 = [CONTENT_W * f for f in (0.44, 0.17, 0.17, 0.22)]
    cw2 = [CONTENT_W * f for f in (0.38, 0.17, 0.10, 0.22, 0.13)]
    return [
        PageBreak(),
        Paragraph("4. What Explains the Decline?", s["h1"]),
        _hr(),
        Paragraph(
            "A game-level logistic regression (outcome: home win, N = 47,215 regular-season "
            "games) decomposes the decline into measurable factors: era dummies, rest "
            "differential, altitude (Denver/Utah), time-zone differential, and a COVID flag.",
            s["body"],
        ),
        Paragraph("Sequential R² decomposition", s["h2"]),
        Paragraph(
            "Adding predictors one block at a time reveals which factors account for the most "
            "variance. McFadden R² is the logistic analogue of OLS R²; typical values are much "
            "smaller than OLS and the ΔR² column is the relevant comparison.",
            s["body"],
        ),
        _table(r2_data, cw1),
        Spacer(1, 0.08 * inch),
        Paragraph(
            "Era alone accounts for 56% of total model fit. The structural multi-decade decline "
            "is not explained by rest, altitude, or travel — those factors add incremental "
            "explanatory power on top of an underlying trend that spans every rule-change era.",
            s["body"],
        ),
        Paragraph("Factor effects (bivariate logistic regressions)", s["h2"]),
        _table(factor_data, cw2),
        Spacer(1, 0.08 * inch),
        Paragraph(
            "<b>Rest</b> matters in both contexts and the effect is larger in the playoffs "
            "(+2.3 pp/day vs +1.5 pp/day), consistent with higher stakes amplifying fatigue. "
            "<b>Altitude</b> at Denver and Utah carries a large regular-season edge (+8.2 pp) "
            "that disappears in the playoffs, where team quality confounds it. "
            "<b>Time zone</b> shows no statistically significant effect in either context — "
            "there are too few coast-to-coast playoff matchups (107 across 42 seasons) for "
            "reliable inference.",
            s["body"],
        ),
        Paragraph("Pre/post-2014 coefficient stability", s["h2"]),
        Paragraph(
            "Splitting the sample at the 2014 Finals format change confirms a real level shift: "
            "the baseline home-win probability dropped by 4.7 pp after 2014 (intercept: +0.463 "
            "pre-2014 vs +0.270 post-2014, N = 32,975 / 14,240 games). "
            "The coefficients on rest, altitude, and time zone are broadly stable across the "
            "split, indicating those factors did not drive the post-2014 decline.",
            s["body"],
        ),
    ]


def _section_rest(s):
    return [
        PageBreak(),
        Paragraph("5. Rest and Schedule Balance", s["h1"]),
        _hr(),
        Paragraph(
            "Each team's rest days are computed from the cached game logs as days between "
            "consecutive games minus one (0 = back-to-back, 1 = one rest day, etc.). "
            "The charts below show back-to-back rates for home and away teams over time, "
            "and home win % split by which team had more rest. When the home team is more "
            "rested the advantage is larger; when the away team is more rested the advantage "
            "shrinks significantly.",
            s["body"],
        ),
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


def _section_differentials(s):
    return [
        PageBreak(),
        Paragraph("6. Box-Score Differentials", s["h1"]),
        _hr(),
        Paragraph(
            "The most direct evidence for why home court advantage has declined comes from "
            "box-score differentials — home team minus away team per game, averaged by season. "
            "Solid lines are regular season; dashed lines are playoffs.",
            s["body"],
        ),
        Paragraph("Foul differential (top left)", s["h2"]),
        Paragraph(
            "In 1984–94, home teams were called for 1.23 fewer fouls per game than road teams "
            "in the regular season (−1.58 in the playoffs). By 2023–25 that gap has shrunk to "
            "−0.20 (regular season) and −0.70 (playoffs). Trend: +0.023 fouls/yr in the regular "
            "season (p &lt; 0.001) and +0.020/yr in the playoffs (p &lt; 0.01). "
            "Referees are calling the game more neutrally over time — this is likely the single "
            "most important mechanism behind the decline.",
            s["body"],
        ),
        Paragraph("eFG% differential (top middle)", s["h2"]),
        Paragraph(
            "The home team's effective field goal percentage advantage (which weights 3-pointers "
            "at 1.5×) has narrowed from +1.56 pp in 1984–94 to +0.97 pp in 2023–25 (regular "
            "season). Trend: −0.015 pp/yr (p &lt; 0.001). This reflects both the narrowing foul "
            "advantage and the convergence of shot selection between home and road teams.",
            s["body"],
        ),
        Paragraph("3PA rate differential (top right)", s["h2"]),
        Paragraph(
            "Early in the dataset, road teams took proportionally fewer 3-point attempts than "
            "home teams. As the 3-point revolution normalized high-volume shooting league-wide, "
            "that gap has closed completely — road teams now take roughly the same share of 3s "
            "as home teams at the same venue. Trend: +0.017 pp/yr (p &lt; 0.001). Shot selection "
            "is no longer a meaningful home court edge.",
            s["body"],
        ),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_advantage_differentials.png",
            "Figure 7. Per-season home-minus-away box-score differentials, 1983–84 through 2024–25. "
            "Solid = regular season, dashed = playoffs. Dotted overlays are OLS trend lines. "
            "Negative foul diff = home team called for fewer fouls.",
        ),
    ]


def _section_shot_zones(s):
    return [
        PageBreak(),
        Paragraph("7. Shot Zone Analysis", s["h1"]),
        _hr(),
        Paragraph(
            "Using NBA.com's LeagueDashTeamShotLocations endpoint (available from 1996–97 onward), "
            "each season's home and road shot-zone distributions are compared. Each panel shows the "
            "home-minus-road difference in the share of field goal attempts from that zone "
            "(positive = home teams take a higher proportion from that location). "
            "A trend toward zero means home and road teams are converging in shot location.",
            s["body"],
        ),
        Paragraph("Paint — Restricted Area + Non-RA (top left)", s["h2"]),
        Paragraph(
            "Home teams have historically gotten a disproportionately higher share of their shots "
            "from the paint — the most efficient shots in basketball. That gap was 2–3 percentage "
            "points in the late 1990s and has shrunk to roughly 0.5–1 pp today. This is consistent "
            "with the narrowing eFG% and foul differentials: road teams are accessing the paint "
            "more freely than they used to.",
            s["body"],
        ),
        Paragraph("Mid-range (top right)", s["h2"]),
        Paragraph(
            "Road teams consistently take a higher share of mid-range shots (~1–1.5 pp more) — "
            "the least efficient shot type in modern basketball. This gap has been relatively "
            "stable, suggesting that even as the paint advantage closes, road teams are still "
            "being pushed away from the basket more often.",
            s["body"],
        ),
        Paragraph("Corner 3 and above-break 3 (bottom panels)", s["h2"]),
        Paragraph(
            "No systematic home/road difference in 3-point shot location. Both lines hover near "
            "zero throughout the dataset. Shot quality at the arc is not a home court advantage.",
            s["body"],
        ),
        Spacer(1, 0.1 * inch),
        _chart(
            "nba_home_court_shot_zones.png",
            "Figure 8. Home-minus-road shot zone % differentials, 1996–97 through 2024–25. "
            "Solid = regular season, dashed = playoffs. "
            "RA = restricted area (within ~4 ft of the basket).",
        ),
    ]


def _section_summary(s):
    data = [
        ["Rank", "Factor",                       "Regular season",        "Playoffs"          ],
        ["1",    "Era (structural decline)",      "−8.9 pp over 40 yr",   "Larger decline"    ],
        ["2",    "Foul diff (refs more neutral)", "+0.023 fouls/yr ***",   "+0.020 fouls/yr **"],
        ["3",    "Altitude — DEN / UTA",          "+8.2 pp ***",           "Not significant"   ],
        ["4",    "eFG% edge shrinking",           "−0.015 pp/yr ***",      "Smaller decline"   ],
        ["5",    "Rest differential",             "+1.5 pp/day ***",       "+2.3 pp/day *"     ],
        ["6",    "3PA rate convergence",          "+0.017 pp/yr ***",      "+0.031 pp/yr *"    ],
        ["7",    "Paint access (shot zones)",     "Declining (1996– )",    "Noisy"             ],
        ["8",    "Time zone",                     "Not significant",        "Not significant"   ],
    ]
    cw = [CONTENT_W * f for f in (0.07, 0.35, 0.29, 0.29)]
    return [
        PageBreak(),
        Paragraph("8. Summary", s["h1"]),
        _hr(),
        Paragraph(
            "Home court advantage has declined by roughly 8–9 percentage points in the regular "
            "season and 10–12 pp in the playoffs over the past 40 years. The decline is "
            "structural — it spans every rule-change era and accounts for 56% of all explained "
            "variance in the logistic regression model. The mechanisms, in order of statistical "
            "strength:",
            s["body"],
        ),
        _table(data, cw),
        Spacer(1, 0.15 * inch),
        Paragraph(
            "The core narrative: NBA home court advantage has eroded because <b>referees call the "
            "game more neutrally</b> today than they did 40 years ago, <b>home teams no longer "
            "generate a disproportionate paint-access or shooting edge</b>, and the <b>3-point "
            "revolution has equalized shot selection</b> between home and road teams. Rest remains "
            "a meaningful factor — particularly in the playoffs — but cannot explain the secular "
            "decline. Altitude at Denver and Utah confers a real regular-season edge but is absent "
            "in the playoffs. Time-zone travel shows no statistically reliable effect.",
            s["body"],
        ),
        Spacer(1, 0.3 * inch),
        _hr(),
        Paragraph(
            "Data: NBA.com via nba_api. Analysis covers 1983–84 through 2024–25 (51,089 games). "
            "Shot zone data available from 1996–97. "
            "Logistic regression uses McFadden R²; marginal effects reported as "
            "coef × p̄ × (1−p̄) × 100 (pp at the mean).",
            s["note"],
        ),
    ]


# ── Main ──────────────────────────────────────────────────────────────────────

def build_report(output_path="nba_home_court_advantage_report.pdf"):
    s = _styles()
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=MARGIN, rightMargin=MARGIN,
        topMargin=MARGIN,  bottomMargin=MARGIN,
        title="NBA Home Court Advantage — A 40-Year Decline",
        author="Justin Pietsch",
    )

    story = []
    story += _cover(s)
    story += _section_decline(s)
    story += _section_era(s)
    story += _section_era_lines(s)
    story += _section_regression(s)
    story += _section_rest(s)
    story += _section_differentials(s)
    story += _section_shot_zones(s)
    story += _section_summary(s)

    doc.build(story)
    print(f"Saved → {output_path}")


if __name__ == "__main__":
    build_report()
