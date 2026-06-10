#!/usr/bin/env python3
"""
Generate a PDF report of the NBA home court advantage analysis.
Run after nba_home_court_advantage.py — all PNGs and RESULTS.md must exist.

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
GREEN  = "#2ca02c"
ACCENT = BLUE

RESULTS_PATH = "RESULTS.md"


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
        "code": ParagraphStyle(
            "code", parent=base["Code"],
            fontSize=6.5, leading=9,
            textColor=colors.HexColor(DARK),
            fontName="Courier",
            spaceAfter=0,
        ),
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

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


def _results_text() -> str:
    """Read RESULTS.md and return the raw regression output (strips markdown fences)."""
    if not os.path.exists(RESULTS_PATH):
        return "[RESULTS.md not found — run nba_home_court_advantage.py first]"
    with open(RESULTS_PATH) as f:
        lines = f.readlines()
    # Strip the header lines and ```code fences, keep the content
    content = []
    in_block = False
    for line in lines:
        if line.strip() == "```":
            in_block = not in_block
            continue
        if in_block:
            content.append(line.rstrip("\n"))
    return "\n".join(content)


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
            "7. Shot Zone Analysis &nbsp;&nbsp; 8. Summary &nbsp;&nbsp; "
            "Appendix A: Full Regression Output",
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
        style=TableStyle([("ALIGN",  (0, 0), (-1, -1), "CENTER"),
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
            "season and the playoffs. The steepest drops are in the most recent eras. "
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
    return [
        PageBreak(),
        Paragraph("4. What Explains the Decline?", s["h1"]),
        _hr(),
        Paragraph(
            "A game-level logistic regression (outcome: home win) decomposes the decline into "
            "measurable factors: era dummies, rest differential, altitude (Denver/Utah), "
            "time-zone differential, and a COVID flag. Full tables are in Appendix A.",
            s["body"],
        ),
        Paragraph("Era dominates the model fit", s["h2"]),
        Paragraph(
            "Adding predictors one block at a time — era first, then rest, altitude, time zone, "
            "and COVID — shows that era dummies alone account for the majority of total model fit. "
            "The structural multi-decade decline is not explained by rest, altitude, or travel; "
            "those factors add incremental explanatory power on top of a trend that spans every "
            "rule-change era.",
            s["body"],
        ),
        Paragraph("Rest, altitude, and time zone", s["h2"]),
        Paragraph(
            "<b>Rest</b> matters in both the regular season and the playoffs. The effect is larger "
            "in the playoffs — higher stakes amplify fatigue. When the home team has more rest than "
            "the road team, the home win probability rises; the reverse is also true.",
            s["body"],
        ),
        Paragraph(
            "<b>Altitude</b> at Denver and Utah carries a significant home edge in the regular "
            "season but the effect disappears in the playoffs. Team quality is a confound: "
            "when those franchises are strong enough to host playoff games, their opponents are "
            "also strong, masking the altitude effect.",
            s["body"],
        ),
        Paragraph(
            "<b>Time zone differences</b> show no statistically significant effect in either "
            "context. There are too few coast-to-coast playoff matchups across 42 seasons for "
            "reliable inference, and the regular-season effect is also not significant.",
            s["body"],
        ),
        Paragraph("Pre/post-2014 level shift", s["h2"]),
        Paragraph(
            "Splitting the sample at the 2014 Finals format change confirms a real drop in the "
            "overall home-win probability after 2014. The coefficients on rest, altitude, and "
            "time zone are broadly stable across the split — those factors did not drive the "
            "post-2014 decline.",
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
            "Solid lines are regular season; dashed lines are playoffs. "
            "For era-by-era averages and OLS trend values, see Appendix A.",
            s["body"],
        ),
        Paragraph("Foul differential (top left)", s["h2"]),
        Paragraph(
            "In the early era, home teams were called for substantially fewer fouls per game than "
            "road teams — a gap that existed in both the regular season and the playoffs. "
            "That advantage has shrunk dramatically over 40 years and is now a fraction of what it "
            "was. The trend is highly significant in both contexts. "
            "Referees are calling the game more neutrally — this is likely the single most "
            "important mechanism behind the decline.",
            s["body"],
        ),
        Paragraph("eFG% differential (top middle)", s["h2"]),
        Paragraph(
            "Home teams used to shoot meaningfully more efficiently than road teams (weighted to "
            "give 3-pointers 1.5× the value of 2-pointers). That shooting edge has narrowed "
            "significantly in the regular season over the dataset. This reflects both the narrowing "
            "foul advantage — fewer free throws for the home team — and a broader convergence in "
            "shot quality between home and road teams.",
            s["body"],
        ),
        Paragraph("3PA rate differential (top right)", s["h2"]),
        Paragraph(
            "Road teams used to take proportionally fewer 3-point attempts than home teams at the "
            "same venue. As the 3-point revolution normalized high-volume shooting league-wide, "
            "that difference has closed completely. Shot selection is no longer a meaningful home "
            "court edge — road teams now arrive with the same offensive game plan as the home team.",
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
            "from the paint — the most efficient shots in basketball. That gap has shrunk "
            "substantially since the late 1990s. This is consistent with both the eFG% narrowing "
            "and the foul differential trend: road teams are accessing the paint more freely.",
            s["body"],
        ),
        Paragraph("Mid-range (top right)", s["h2"]),
        Paragraph(
            "Road teams consistently take a higher share of mid-range shots — the least efficient "
            "shot type in modern basketball. This gap has been relatively stable, suggesting that "
            "even as the paint advantage closes, road teams are still being pushed away from the "
            "basket more often.",
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
        Paragraph("8. Summary", s["h1"]),
        _hr(),
        Paragraph(
            "Home court advantage has declined substantially in both the regular season and the "
            "playoffs over the past 40 years, with the playoff decline steeper than the regular "
            "season. The decline is structural — it spans every rule-change era and the era effect "
            "accounts for the majority of variance explained by the regression model. "
            "The mechanisms, in order of statistical strength:",
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
            "Data: NBA.com via nba_api. Analysis covers 1983–84 through 2024–25. "
            "Shot zone data available from 1996–97. "
            "Logistic regression uses McFadden R²; marginal effects at the mean. "
            "See Appendix A for full tables and coefficient values.",
            s["note"],
        ),
    ]


def _appendix_results(s):
    text = _results_text()
    return [
        PageBreak(),
        Paragraph("Appendix A: Full Regression Output", s["h1"]),
        _hr(),
        Paragraph(
            "Auto-generated by <code>nba_home_court_regression.py</code> each time the analysis "
            "is run. Contains the sequential R² decomposition, pre/post-2014 coefficient stability "
            "check, bivariate factor significance table, and foul/shooting differential trends "
            "by era.",
            s["body"],
        ),
        Spacer(1, 0.1 * inch),
        Preformatted(text, s["code"]),
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
    story += _appendix_results(s)

    doc.build(story)
    print(f"Saved → {output_path}")


if __name__ == "__main__":
    build_report()
