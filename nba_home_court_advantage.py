"""
NBA Home Court Advantage — fetches data via nba_api, then plots.

Data source: NBA.com via the nba_api package
  - LeagueGameFinder: pulls every game result for a given season
  - Computes home win % per season (regular season + playoffs)
  - Covers 1983-84 through 2024-25
"""

import os
import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker

from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.library.parameters import SeasonType


# ── Config ────────────────────────────────────────────────────────────────────
START_YEAR = 1984   # season ending in this year = 1983-84
END_YEAR   = 2025   # season ending in this year = 2024-25
SLEEP_SEC  = 1.0    # polite pause between API calls

# 2020 bubble playoffs: all games at neutral site — exclude from playoff stats
SKIP_PLAYOFF_YEARS = {2020}

# Seasons with limited/no fans (COVID) — highlighted in the chart
COVID_SEASONS = {"19–20", "20–21"}

# Raw game logs are cached here as CSVs to avoid re-fetching from NBA.com
CACHE_DIR = "cache"


def season_str(end_year: int) -> str:
    """2024 -> '2023-24'  (NBA API format)"""
    return f"{end_year - 1}-{str(end_year)[-2:]}"


def short_label(end_year: int) -> str:
    """2024 -> '23–24'  (chart axis label)"""
    return f"{str(end_year - 1)[-2:]}–{str(end_year)[-2:]}"


def cache_path(end_year: int, season_type: str) -> str:
    season = season_str(end_year)
    return os.path.join(CACHE_DIR, f"{season}_{season_type.replace(' ', '_')}.csv")


def fetch_season_home_pct(end_year: int, season_type: str) -> float | None:
    """
    Pull every game log for one season/type, keep only home games,
    and return the fraction won.

    nba_api returns one row per team per game.  For a home game the
    MATCHUP field looks like  'BOS vs. MIA'  (vs. = home)
    and for away games        'BOS @ MIA'    (@ = away).
    WL is 'W' or 'L'.

    Game logs are cached as CSVs under CACHE_DIR so repeat runs don't
    re-fetch from NBA.com.
    """
    season = season_str(end_year)
    path = cache_path(end_year, season_type)

    if os.path.exists(path):
        df = pd.read_csv(path)
    else:
        try:
            finder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season,
                season_type_nullable=season_type,
                timeout=60,
            )
            df = finder.get_data_frames()[0]
        except Exception as e:
            print(f"    ERROR fetching {season} {season_type}: {e}")
            return None

        os.makedirs(CACHE_DIR, exist_ok=True)
        df.to_csv(path, index=False)
        time.sleep(SLEEP_SEC)  # polite pause, only needed after a real API call

    if df.empty:
        return None

    # Home games have 'vs.' in MATCHUP
    home = df[df["MATCHUP"].str.contains(" vs. ", regex=False, na=False)].copy()
    if home.empty:
        return None

    wins  = (home["WL"] == "W").sum()
    total = len(home)
    return round(100 * wins / total, 1)


# ── Era definitions ───────────────────────────────────────────────────────────
# Eras are bounded by major NBA rule changes affecting pace/defense. Sources:
#   - Hand-checking restrictions (1994-95): https://theballzone.com/when-was-hand-checking-banned-in-the-nba/
#   - Illegal defense eliminated / zone legalized / defensive 3-sec (2001-02):
#       https://en.wikipedia.org/wiki/Defensive_three-second_violation
#   - Perimeter hand-checking ban (2004-05):
#       https://www.basketballnetwork.net/old-school/how-removing-the-hand-check-rule-changed-the-nba-forever
#   - Freedom-of-movement emphasis (2017-18) / transition take-foul rule (2022-23):
#       https://videorulebook.nba.com/rule/transition-take-fouls/
ERA_DEFS = [
    ("1984–94", 1984, 1994, "Illegal defense rules (no zone defense)"),
    ("1995–01", 1995, 2001, "Hand-checking restrictions; zone still illegal"),
    ("2002–04", 2002, 2004, "Zone defense legalized, defensive 3-sec added"),
    ("2005–17", 2005, 2017, "Perimeter hand-checking banned (pace-and-space)"),
    ("2018–22", 2018, 2022, "Freedom-of-movement emphasis"),
    ("2023–25", 2023, 2025, "Transition take-foul rule added"),
]

# Playoff series-format / scheduling changes (separate from the defensive-rule
# eras above — these only affect the playoff data). Marked as vertical lines
# on the playoffs panel rather than background shading to avoid clutter.
# Sources:
#   - 1985: Finals move to 2-3-2 format; home-court advantage based on
#       regular-season record instead of alternating by conference:
#       https://en.wikipedia.org/wiki/2%E2%80%933%E2%80%932_format
#   - 2003: First round expanded from best-of-5 to best-of-7:
#       https://en.wikipedia.org/wiki/NBA_playoffs
#   - 2014: Finals revert to 2-2-1-1-1 (same format as all other rounds):
#       https://en.wikipedia.org/wiki/2%E2%80%933%E2%80%932_format
PLAYOFF_FORMAT_CHANGES = [
    (1985, "'85: Finals → 2-3-2,\nhome court by record"),
    (2003, "'03: Round 1 →\nbest-of-7"),
    (2014, "'14: Finals →\n2-2-1-1-1"),
]

# Playoff format "periods" — the spans of seasons between the format changes
# above, used to bucket playoff home win % by which format was in effect.
PLAYOFF_FORMAT_PERIODS = [
    ("1984",     1984, 1984, "Best-of-5 R1, 2-2-1-1-1 Finals (alternating home court)"),
    ("1985–02",  1985, 2002, "Best-of-5 R1, 2-3-2 Finals (home court by record)"),
    ("2003–13",  2003, 2013, "Best-of-7 R1, 2-3-2 Finals"),
    ("2014–25",  2014, 2025, "Best-of-7 R1, 2-2-1-1-1 Finals"),
]


def label_to_year(lbl: str) -> int:
    suffix = int(lbl.split("–")[1])
    return (2000 + suffix) if suffix < 50 else (1900 + suffix)


def fetch_all_seasons() -> tuple[list[str], list[float], list[str], list[float]]:
    """Fetch home win % for every season/type in [START_YEAR, END_YEAR]."""
    print("Fetching NBA data via nba_api (NBA.com)...")
    print(f"Seasons: {season_str(START_YEAR)} → {season_str(END_YEAR)}")
    print("(~2 API calls per season, should take 2–4 minutes)\n")

    reg_seasons:  list[str]   = []
    reg_pcts:     list[float] = []
    po_seasons:   list[str]   = []
    po_pcts:      list[float] = []

    for year in range(START_YEAR, END_YEAR + 1):
        label = short_label(year)

        # Regular season
        print(f"  {label} regular season ... ", end="", flush=True)
        pct = fetch_season_home_pct(year, SeasonType.regular)
        if pct is not None:
            reg_seasons.append(label)
            reg_pcts.append(pct)
            print(f"{pct:.1f}%")
        else:
            print("no data")

        # Playoffs
        if year not in SKIP_PLAYOFF_YEARS:
            print(f"  {label} playoffs      ... ", end="", flush=True)
            pct_po = fetch_season_home_pct(year, "Playoffs")
            if pct_po is not None:
                po_seasons.append(label)
                po_pcts.append(pct_po)
                print(f"{pct_po:.1f}%")
            else:
                print("no data")

    print(f"\nRegular season: {len(reg_seasons)} seasons fetched")
    print(f"Playoffs:       {len(po_seasons)} seasons fetched")

    return reg_seasons, reg_pcts, po_seasons, po_pcts


def compute_era_averages(
    reg_seasons: list[str], reg_pcts: list[float],
    po_seasons: list[str], po_pcts: list[float],
) -> tuple[list[float], list[float], list[str]]:
    """Average regular-season and playoff home win % within each era."""
    era_reg_avg, era_po_avg = [], []
    for _, y1, y2, _ in ERA_DEFS:
        rv = [p for s, p in zip(reg_seasons, reg_pcts) if y1 <= label_to_year(s) <= y2]
        pv = [p for s, p in zip(po_seasons,  po_pcts)  if y1 <= label_to_year(s) <= y2]
        era_reg_avg.append(round(np.mean(rv), 1) if rv else 0)
        era_po_avg.append( round(np.mean(pv), 1) if pv else 0)

    era_labels_short = [e[0] for e in ERA_DEFS]
    return era_reg_avg, era_po_avg, era_labels_short


def compute_playoff_format_averages(
    reg_seasons: list[str], reg_pcts: list[float],
    po_seasons: list[str], po_pcts: list[float],
) -> tuple[list[float], list[float], list[str]]:
    """Average regular-season and playoff home win % within each playoff-format period."""
    format_reg_avg, format_po_avg = [], []
    for _, y1, y2, _ in PLAYOFF_FORMAT_PERIODS:
        rv = [p for s, p in zip(reg_seasons, reg_pcts) if y1 <= label_to_year(s) <= y2]
        pv = [p for s, p in zip(po_seasons,  po_pcts)  if y1 <= label_to_year(s) <= y2]
        format_reg_avg.append(round(np.mean(rv), 1) if rv else 0)
        format_po_avg.append( round(np.mean(pv), 1) if pv else 0)

    format_labels_short = [p[0] for p in PLAYOFF_FORMAT_PERIODS]
    return format_reg_avg, format_po_avg, format_labels_short


# ── Plot ──────────────────────────────────────────────────────────────────────
BLUE  = "#378add"
GREEN = "#1d9e75"
RED   = "#e24b4a"
GRAY  = "#888780"
BG    = "#f9f9f7"
PANEL = "#ffffff"

# One background shade per era (matches order of ERA_DEFS)
ERA_COLORS = ["#7c6fce", "#378add", "#1d9e75", "#e8a33d", "#c2538a", "#5a8f29"]

def plot_results(
    reg_seasons: list[str], reg_pcts: list[float],
    po_seasons: list[str], po_pcts: list[float],
    era_reg_avg: list[float], era_po_avg: list[float], era_labels_short: list[str],
    format_reg_avg: list[float], format_po_avg: list[float], format_labels_short: list[str],
) -> None:
    """Build the 5-panel figure and save/show it."""
    plt.rcParams.update({
        "font.family":        "DejaVu Sans",
        "axes.spines.top":    False,
        "axes.spines.right":  False,
        "axes.facecolor":     PANEL,
        "figure.facecolor":   BG,
        "axes.grid":          True,
        "grid.color":         "#e0dfd8",
        "grid.linewidth":     0.6,
        "axes.axisbelow":     True,
    })

    fig = plt.figure(figsize=(22.5, 17.5))
    fig.suptitle("NBA Home Court Advantage — A 40-Year Decline",
                 fontsize=18, fontweight="bold", y=0.995, color="#2c2c2a")
    fig.text(0.5, 0.965,
             "Data: NBA.com  |  Regular season & playoffs  |  1983-84 through 2024-25",
             ha="center", fontsize=9, color=GRAY)

    gs = fig.add_gridspec(4, 4, hspace=0.4, wspace=0.32,
                          height_ratios=[1, 0.45, 0.45, 1],
                          left=0.07, right=0.97, top=0.94, bottom=0.09)

    # ── Panel 1: season-by-season regular season vs playoffs ─────────────────
    ax1 = fig.add_subplot(gs[0, 1:3])
    x = np.arange(len(reg_seasons))
    pt_colors = [RED if s in COVID_SEASONS else BLUE for s in reg_seasons]

    ax1.plot(x, reg_pcts, color=BLUE, linewidth=2, zorder=2)
    ax1.scatter(x, reg_pcts, c=pt_colors, s=40, zorder=3,
                edgecolors="white", linewidths=0.8)

    # Playoffs, aligned to the same x positions (gap where no playoff data, e.g. 2020 bubble)
    po_pct_by_season = dict(zip(po_seasons, po_pcts))
    po_pcts_aligned = [po_pct_by_season.get(s, np.nan) for s in reg_seasons]
    ax1.plot(x, po_pcts_aligned, color=GREEN, linewidth=2, zorder=2)
    ax1.scatter(x, po_pcts_aligned, color=GREEN, s=40, zorder=3,
                edgecolors="white", linewidths=0.8)

    # Trend lines
    z = np.polyfit(x, reg_pcts, 1)
    ax1.plot(x, np.poly1d(z)(x), "--", color=BLUE, linewidth=1.4, alpha=0.5)

    po_pcts_arr = np.array(po_pcts_aligned, dtype=float)
    po_mask = ~np.isnan(po_pcts_arr)
    zp = np.polyfit(x[po_mask], po_pcts_arr[po_mask], 1)
    ax1.plot(x, np.poly1d(zp)(x), "--", color=GREEN, linewidth=1.4, alpha=0.5)

    # Shade era boundaries (rule-change eras), labeled above the plot area
    for (label, y1, y2, _), era_color in zip(ERA_DEFS, ERA_COLORS):
        era_idx = [i for i, s in enumerate(reg_seasons) if y1 <= label_to_year(s) <= y2]
        if not era_idx:
            continue
        ax1.axvspan(min(era_idx) - 0.5, max(era_idx) + 0.5,
                    alpha=0.08, color=era_color, zorder=0)
        if min(era_idx) > 0:
            ax1.axvline(min(era_idx) - 0.5, color=GRAY, linestyle=":", linewidth=0.8, alpha=0.6)
        mid = (min(era_idx) + max(era_idx)) / 2
        ax1.text(mid, 46, label, ha="center", va="bottom", fontsize=7.5, color=GRAY)

    # Shade COVID seasons (drawn on top of era shading)
    covid_idx = [i for i, s in enumerate(reg_seasons) if s in COVID_SEASONS]
    if covid_idx:
        ax1.axvspan(min(covid_idx) - 0.5, max(covid_idx) + 0.5,
                    alpha=0.12, color=RED, zorder=1)

    ax1.set_title("Regular season vs playoffs: home win % per season",
                  fontsize=12, fontweight="bold", color="#2c2c2a", pad=8)
    tick_step = max(1, len(reg_seasons) // 14)
    ax1.set_xticks(x[::tick_step])
    ax1.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax1.set_ylim(45, 80)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.set_ylabel("Home win %", fontsize=10)

    handles1 = [
        mpatches.Patch(color=BLUE,  label="Regular season"),
        mpatches.Patch(color=GREEN, label="Playoffs"),
        mpatches.Patch(color=RED,   label="COVID-impacted seasons"),
        plt.Line2D([0], [0], color=BLUE,  linestyle="--", alpha=0.5, label="Trend (regular season)"),
        plt.Line2D([0], [0], color=GREEN, linestyle="--", alpha=0.5, label="Trend (playoffs)"),
    ]
    ax1.legend(handles=handles1, fontsize=9, loc="upper right",
               framealpha=0.85, edgecolor="#ddd")

    if reg_pcts:
        peak_i = int(np.argmax(reg_pcts))
        low_i  = int(np.argmin(reg_pcts))
        ax1.annotate(f"Peak: {reg_pcts[peak_i]:.1f}%\n({reg_seasons[peak_i]})",
                     xy=(peak_i, reg_pcts[peak_i]),
                     xytext=(peak_i + 2, reg_pcts[peak_i] + 1.5),
                     arrowprops=dict(arrowstyle="->", color=GRAY, lw=1),
                     fontsize=8, color=GRAY)
        ax1.annotate(f"Low: {reg_pcts[low_i]:.1f}%\n({reg_seasons[low_i]})",
                     xy=(low_i, reg_pcts[low_i]),
                     xytext=(max(low_i - 6, 1), reg_pcts[low_i] - 2.5),
                     arrowprops=dict(arrowstyle="->", color=GRAY, lw=1),
                     fontsize=8, color=GRAY)

    # ── Panel 2: playoffs only, with a trend line per era ────────────────────
    ax3 = fig.add_subplot(gs[1, 1:3])
    xp = np.arange(len(po_seasons))
    pt_colors_po = [RED if s in COVID_SEASONS else GREEN for s in po_seasons]

    ax3.plot(xp, po_pcts, color=GREEN, linewidth=2, zorder=2)
    ax3.scatter(xp, po_pcts, c=pt_colors_po, s=40, zorder=3,
                edgecolors="white", linewidths=0.8)

    po_pcts_arr2 = np.array(po_pcts, dtype=float)

    for (label, y1, y2, _), era_color in zip(ERA_DEFS, ERA_COLORS):
        era_idx = [i for i, s in enumerate(po_seasons) if y1 <= label_to_year(s) <= y2]
        if not era_idx:
            continue

        ax3.axvspan(min(era_idx) - 0.5, max(era_idx) + 0.5,
                    alpha=0.08, color=era_color, zorder=0)
        if min(era_idx) > 0:
            ax3.axvline(min(era_idx) - 0.5, color=GRAY, linestyle=":", linewidth=0.8, alpha=0.6)
        mid = (min(era_idx) + max(era_idx)) / 2
        ax3.text(mid, 46, label, ha="center", va="bottom", fontsize=7.5, color=GRAY)

        # Per-era trend line
        if len(era_idx) >= 2:
            era_x = np.array(era_idx)
            ze = np.polyfit(era_x, po_pcts_arr2[era_x], 1)
            ax3.plot(era_x, np.poly1d(ze)(era_x), "--", color=era_color, linewidth=1.8, alpha=0.8)

    # Shade COVID seasons (drawn on top of era shading)
    covid_idx_po = [i for i, s in enumerate(po_seasons) if s in COVID_SEASONS]
    if covid_idx_po:
        ax3.axvspan(min(covid_idx_po) - 0.5, max(covid_idx_po) + 0.5,
                    alpha=0.12, color=RED, zorder=1)

    # Mark playoff format/scheduling changes (distinct from the rule-change
    # era shading: dash-dot vertical lines, labeled near the top of the panel)
    for change_year, change_label in PLAYOFF_FORMAT_CHANGES:
        idx = next((i for i, s in enumerate(po_seasons) if label_to_year(s) == change_year), None)
        if idx is None:
            continue
        ax3.axvline(idx - 0.5, color="#444444", linestyle="-.", linewidth=1, alpha=0.6, zorder=1)
        ax3.text(idx - 0.4, 79, change_label, rotation=90, ha="left", va="top",
                 fontsize=6.5, color="#444444", linespacing=1.2)

    ax3.set_title("Playoffs: home win % per season, with a trend line per era",
                  fontsize=12, fontweight="bold", color="#2c2c2a", pad=8)
    tick_step_po = max(1, len(po_seasons) // 14)
    ax3.set_xticks(xp[::tick_step_po])
    ax3.set_xticklabels(po_seasons[::tick_step_po], rotation=45, ha="right", fontsize=8)
    ax3.set_ylim(45, 80)
    ax3.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax3.set_ylabel("Home win %", fontsize=10)

    # ── Panel 3: regular season only, with a trend line per era ──────────────
    ax4 = fig.add_subplot(gs[2, 1:3])
    pt_colors_reg = [RED if s in COVID_SEASONS else BLUE for s in reg_seasons]

    ax4.plot(x, reg_pcts, color=BLUE, linewidth=2, zorder=2)
    ax4.scatter(x, reg_pcts, c=pt_colors_reg, s=40, zorder=3,
                edgecolors="white", linewidths=0.8)

    reg_pcts_arr = np.array(reg_pcts, dtype=float)

    for (label, y1, y2, _), era_color in zip(ERA_DEFS, ERA_COLORS):
        era_idx = [i for i, s in enumerate(reg_seasons) if y1 <= label_to_year(s) <= y2]
        if not era_idx:
            continue

        ax4.axvspan(min(era_idx) - 0.5, max(era_idx) + 0.5,
                    alpha=0.08, color=era_color, zorder=0)
        if min(era_idx) > 0:
            ax4.axvline(min(era_idx) - 0.5, color=GRAY, linestyle=":", linewidth=0.8, alpha=0.6)
        mid = (min(era_idx) + max(era_idx)) / 2
        ax4.text(mid, 46, label, ha="center", va="bottom", fontsize=7.5, color=GRAY)

        # Per-era trend line
        if len(era_idx) >= 2:
            era_x = np.array(era_idx)
            ze = np.polyfit(era_x, reg_pcts_arr[era_x], 1)
            ax4.plot(era_x, np.poly1d(ze)(era_x), "--", color=era_color, linewidth=1.8, alpha=0.8)

    # Shade COVID seasons (drawn on top of era shading)
    if covid_idx:
        ax4.axvspan(min(covid_idx) - 0.5, max(covid_idx) + 0.5,
                    alpha=0.12, color=RED, zorder=1)

    ax4.set_title("Regular season: home win % per season, with a trend line per era",
                  fontsize=12, fontweight="bold", color="#2c2c2a", pad=8)
    ax4.set_xticks(x[::tick_step])
    ax4.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax4.set_ylim(45, 80)
    ax4.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax4.set_ylabel("Home win %", fontsize=10)

    # ── Panel 4: era grouped bar chart ────────────────────────────────────────
    ax2 = fig.add_subplot(gs[3, 0:2])
    xi = np.arange(len(era_labels_short))
    w  = 0.35
    bars1 = ax2.bar(xi - w/2, era_reg_avg, width=w, color=BLUE,  label="Regular season", zorder=2)
    bars2 = ax2.bar(xi + w/2, era_po_avg,  width=w, color=GREEN, label="Playoffs",        zorder=2)

    for bar in list(bars1) + list(bars2):
        clr = BLUE if bar in bars1 else GREEN
        ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                 f"{bar.get_height():.1f}%",
                 ha="center", va="bottom", fontsize=7.5, color=clr)

    ax2.set_xticks(xi)
    ax2.set_xticklabels(era_labels_short, rotation=30, ha="right", fontsize=9)
    ax2.set_ylim(50, 70)
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax2.set_title("Regular season vs playoffs\nhome win % by era",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=8)
    ax2.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    # ── Panel 5: home win % by playoff-format period ──────────────────────────
    ax5 = fig.add_subplot(gs[3, 2:4])
    xf = np.arange(len(format_labels_short))
    bars5_reg = ax5.bar(xf - w/2, format_reg_avg, width=w, color=BLUE,  label="Regular season", zorder=2)
    bars5_po  = ax5.bar(xf + w/2, format_po_avg,  width=w, color=GREEN, label="Playoffs",        zorder=2)

    for bar in list(bars5_reg) + list(bars5_po):
        clr = BLUE if bar in bars5_reg else GREEN
        ax5.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                 f"{bar.get_height():.1f}%",
                 ha="center", va="bottom", fontsize=7.5, color=clr)

    ax5.set_xticks(xf)
    ax5.set_xticklabels(format_labels_short, rotation=30, ha="right", fontsize=9)
    ax5.set_ylim(50, 70)
    ax5.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax5.set_title("Regular season vs playoffs\nhome win % by playoff format period",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=8)
    ax5.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    # Footnote: explain what each era represents
    era_notes = "\n".join(f"{label}: {desc}" for label, _, _, desc in ERA_DEFS)
    fig.text(0.5, 0.045, era_notes, ha="center", va="top",
             fontsize=7.5, color=GRAY, linespacing=1.6)

    # Footnote: explain the playoff format changes marked on the playoffs panel
    format_notes = "  |  ".join(
        change_label.replace("\n", " ") for _, change_label in PLAYOFF_FORMAT_CHANGES
    )
    fig.text(0.5, -0.01, format_notes, ha="center", va="top",
             fontsize=7.5, color="#444444", linespacing=1.6)

    # ── Save ──────────────────────────────────────────────────────────────────
    output_path = "nba_home_court_advantage.png"
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.show()


# ── Shared helpers for per-game analyses ────────────────────────────────────
def _load_game_log(end_year: int, season_type: str) -> pd.DataFrame | None:
    """Load one season/type's cached game log (one row per team per game)."""
    path = cache_path(end_year, season_type)
    if not os.path.exists(path):
        return None

    df = pd.read_csv(path)
    if df.empty:
        return None
    return df


def _merge_home_away_rows(df: pd.DataFrame) -> pd.DataFrame | None:
    """
    Collapse a per-team-per-game log into one row per game by joining each
    game's home and away rows on GAME_ID (columns get '_home'/'_away'
    suffixes). Returns None if either side has no rows.
    """
    home = df[df["MATCHUP"].str.contains(" vs. ", regex=False, na=False)]
    away = df[df["MATCHUP"].str.contains(" @ ", regex=False, na=False)]
    if home.empty or away.empty:
        return None

    merged = home.merge(away, on="GAME_ID", suffixes=("_home", "_away"))
    if merged.empty:
        return None
    return merged


def bucket_stats_by_era(seasons: list[str], stats: dict) -> tuple[dict, list[str]]:
    """
    Average each per-season stat series within each rule-change era
    (ERA_DEFS). Works for any stats dict of the form {category: [per-season
    values]} — used by both the altitude and time-zone analyses.
    """
    era_avgs: dict[str, list[float]] = {key: [] for key in stats}
    for _, y1, y2, _ in ERA_DEFS:
        idx = [i for i, s in enumerate(seasons) if y1 <= label_to_year(s) <= y2]
        for key, values in stats.items():
            vals = [values[i] for i in idx if not np.isnan(values[i])]
            era_avgs[key].append(round(np.mean(vals), 1) if vals else 0)

    era_labels_short = [e[0] for e in ERA_DEFS]
    return era_avgs, era_labels_short


# ── Rest-day analysis (prototype) ──────────────────────────────────────────
def fetch_rest_data(end_year: int, season_type: str) -> pd.DataFrame | None:
    """
    Compute per-game rest-day info for one season/type from the cached game
    log (one row per team per game). REST = days between a team's
    consecutive games minus 1 (0 = back-to-back). Games where either team's
    rest is unknown (their first game in this cached log) are dropped.

    Note: for playoffs, "first game" means the team's first playoff game of
    that year, since the cache only contains playoff games — so first-round
    games are dropped (no prior playoff game to compute rest from).
    """
    df = _load_game_log(end_year, season_type)
    if df is None:
        return None

    df = df.copy()
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df = df.sort_values(["TEAM_ID", "GAME_DATE"])
    df["PREV_DATE"] = df.groupby("TEAM_ID")["GAME_DATE"].shift(1)
    df["REST"] = (df["GAME_DATE"] - df["PREV_DATE"]).dt.days - 1

    merged = _merge_home_away_rows(df)
    if merged is None:
        return None

    merged = merged.dropna(subset=["REST_home", "REST_away"])
    if merged.empty:
        return None

    merged["REST_DIFF"] = merged["REST_home"] - merged["REST_away"]
    merged["HOME_WIN"] = (merged["WL_home"] == "W").astype(int)
    return merged[["REST_home", "REST_away", "REST_DIFF", "HOME_WIN"]]


def compute_rest_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], dict]:
    """Per-season back-to-back rates and home win % by rest differential."""
    seasons: list[str] = []
    stats: dict[str, list[float]] = {
        "b2b_home_pct": [], "b2b_away_pct": [],
        "win_home_more_rest": [], "win_equal_rest": [], "win_away_more_rest": [],
    }

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        g = fetch_rest_data(year, season_type)
        if g is None or g.empty:
            continue

        seasons.append(short_label(year))
        stats["b2b_home_pct"].append(100 * (g["REST_home"] == 0).mean())
        stats["b2b_away_pct"].append(100 * (g["REST_away"] == 0).mean())

        more  = g[g["REST_DIFF"] > 0]
        equal = g[g["REST_DIFF"] == 0]
        less  = g[g["REST_DIFF"] < 0]
        stats["win_home_more_rest"].append(100 * more["HOME_WIN"].mean()  if len(more)  else np.nan)
        stats["win_equal_rest"].append(    100 * equal["HOME_WIN"].mean() if len(equal) else np.nan)
        stats["win_away_more_rest"].append(100 * less["HOME_WIN"].mean()  if len(less)  else np.nan)

    return seasons, stats


def plot_rest_analysis(
    seasons: list[str], stats: dict,
    season_label: str, output_path: str, extra_subtitle: str = "",
) -> None:
    """
    2-panel chart exploring whether schedule-driven rest disparities help
    explain the decline in home court advantage.

    Panel 1: back-to-back rate for home vs away teams, per season — shows
    whether the league's schedule has gotten more balanced over time.
    Panel 2: home win % split by which team had more rest, per season —
    shows whether the rest-advantage effect on home win % has shrunk.
    """
    x = np.arange(len(seasons))
    tick_step = max(1, len(seasons) // 14)

    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
    fig.suptitle("Does Schedule Balance Explain the Decline in Home Court Advantage?",
                 fontsize=15, fontweight="bold", y=0.99, color="#2c2c2a")
    fig.text(0.5, 0.955,
             f"Data: NBA.com  |  {season_label}  |  "
             f"rest days = days between games − 1 (0 = back-to-back){extra_subtitle}",
             ha="center", fontsize=9, color=GRAY)

    # Panel 1: back-to-back rates
    ax1.plot(x, stats["b2b_home_pct"], color=BLUE, linewidth=2, label="Home team on back-to-back")
    ax1.plot(x, stats["b2b_away_pct"], color=GREEN, linewidth=2, label="Away team on back-to-back")
    ax1.set_xticks(x[::tick_step])
    ax1.set_xticklabels(seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.set_ylabel("% of games")
    ax1.set_title("Back-to-back rate, home vs away teams",
                  fontsize=12, fontweight="bold", color="#2c2c2a", pad=8)
    ax1.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    # Panel 2: home win % by rest differential, with trend lines
    ax2.plot(x, stats["win_home_more_rest"], color=BLUE, linewidth=2, label="Home team more rested")
    ax2.plot(x, stats["win_equal_rest"],     color=GRAY, linewidth=2, label="Equal rest")
    ax2.plot(x, stats["win_away_more_rest"], color=RED,  linewidth=2, label="Away team more rested")

    for series, color in [("win_home_more_rest", BLUE), ("win_away_more_rest", RED)]:
        y = np.array(stats[series], dtype=float)
        mask = ~np.isnan(y)
        if mask.sum() >= 2:
            z = np.polyfit(x[mask], y[mask], 1)
            ax2.plot(x, np.poly1d(z)(x), "--", color=color, linewidth=1.4, alpha=0.5)

    ax2.set_xticks(x[::tick_step])
    ax2.set_xticklabels(seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax2.set_ylabel("Home win %")
    ax2.set_title("Home win % depending on which team had more rest",
                  fontsize=12, fontweight="bold", color="#2c2c2a", pad=8)
    ax2.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.show()


# ── Altitude analysis (prototype) ──────────────────────────────────────────
# Home arenas at significant elevation, used to test whether visiting teams
# are specifically disadvantaged at altitude (vs. just facing good teams).
# Matched on TEAM_NAME since the Jazz's abbreviation changed (UTH -> UTA)
# partway through the dataset, but TEAM_NAME has stayed constant.
# Source: https://en.wikipedia.org/wiki/List_of_NBA_arenas
ALTITUDE_TEAMS = {
    "Denver Nuggets": 5280,
    "Utah Jazz": 4226,
}

ALTITUDE_COLORS = {
    "Denver Nuggets": "#e8a33d",
    "Utah Jazz": "#7c6fce",
    "other": GRAY,
}

ALTITUDE_LABELS = {
    "Denver Nuggets": "Denver (5,280 ft)",
    "Utah Jazz": "Utah (4,226 ft)",
    "other": "All other arenas (avg)",
}


def fetch_altitude_data(end_year: int, season_type: str) -> pd.DataFrame | None:
    """
    Per-home-game result from the cached game log, tagged with whether the
    home team plays at elevation (Denver, Utah). HOME_WIN = 1 if the home
    team won that game.
    """
    df = _load_game_log(end_year, season_type)
    if df is None:
        return None

    home = df[df["MATCHUP"].str.contains(" vs. ", regex=False, na=False)].copy()
    if home.empty:
        return None

    home["HOME_WIN"] = (home["WL"] == "W").astype(int)
    home["ALTITUDE"] = home["TEAM_NAME"].isin(ALTITUDE_TEAMS)
    return home[["TEAM_NAME", "HOME_WIN", "ALTITUDE"]]


def compute_altitude_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], dict]:
    """Per-season home win % at each altitude city vs elsewhere."""
    seasons: list[str] = []
    stats: dict[str, list[float]] = {name: [] for name in ALTITUDE_TEAMS}
    stats["other"] = []

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        g = fetch_altitude_data(year, season_type)
        if g is None or g.empty:
            continue

        seasons.append(short_label(year))
        other = g[~g["ALTITUDE"]]
        stats["other"].append(100 * other["HOME_WIN"].mean() if len(other) else np.nan)
        for name in ALTITUDE_TEAMS:
            team_g = g[g["TEAM_NAME"] == name]
            stats[name].append(100 * team_g["HOME_WIN"].mean() if len(team_g) else np.nan)

    return seasons, stats


def plot_category_road_win_analysis(
    seasons: list[str], stats: dict, category_order: list[str],
    colors: dict, labels: dict, title: str, season_label: str,
    output_path: str, road_win_desc: str,
    y_label: str = "Road (visiting team) win %",
) -> None:
    """
    Generic 2-panel chart comparing win % across a set of game categories
    (e.g. altitude city, time zones crossed).

    Panel 1: win % per season for each category, with trend lines.
    Panel 2: the same, averaged within each rule-change era.
    y_label controls the axis label and panel titles (use "Home win %" for
    altitude, "Road (visiting team) win %" for time-zone analysis).
    """
    x = np.arange(len(seasons))
    tick_step = max(1, len(seasons) // 14)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6), gridspec_kw={"width_ratios": [2, 1]})
    fig.suptitle(title, fontsize=15, fontweight="bold", y=1.03, color="#2c2c2a")
    fig.text(0.5, 0.965,
             f"Data: NBA.com  |  {season_label}  |  {road_win_desc}",
             ha="center", fontsize=9, color=GRAY)

    # Panel 1: per-season trend
    for key in category_order:
        y = np.array(stats[key], dtype=float)
        ax1.plot(x, y, color=colors[key], linewidth=2, label=labels[key])
        mask = ~np.isnan(y)
        if mask.sum() >= 2:
            z = np.polyfit(x[mask], y[mask], 1)
            ax1.plot(x, np.poly1d(z)(x), "--", color=colors[key], linewidth=1.4, alpha=0.5)

    ax1.set_xticks(x[::tick_step])
    ax1.set_xticklabels(seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.set_ylabel(y_label)
    ax1.set_title(f"{y_label} by season", fontsize=12, fontweight="bold", color="#2c2c2a", pad=8)
    ax1.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    # Panel 2: era-grouped bar chart
    era_avgs, era_labels = bucket_stats_by_era(seasons, stats)
    xi = np.arange(len(era_labels))
    n = len(category_order)
    w = 0.8 / n
    offsets = [(-(n - 1) / 2 + i) * w for i in range(n)]
    for offset, key in zip(offsets, category_order):
        bars = ax2.bar(xi + offset, era_avgs[key], width=w, color=colors[key],
                       label=labels[key], zorder=2)
        for bar in bars:
            ax2.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                     f"{bar.get_height():.0f}%", ha="center", va="bottom",
                     fontsize=6.5, color=colors[key])

    ax2.set_xticks(xi)
    ax2.set_xticklabels(era_labels, rotation=30, ha="right", fontsize=8)
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax2.set_title(f"{y_label} by era", fontsize=12, fontweight="bold", color="#2c2c2a", pad=8)
    ax2.legend(fontsize=8, framealpha=0.85, edgecolor="#ddd")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.show()


# ── Time-zone analysis (prototype) ──────────────────────────────────────────
# Time zone for each franchise that has appeared in the dataset, numbered
# 0 (Eastern) through 3 (Pacific). Used to measure how many time zones a
# visiting team crossed to play a given game. DST is ignored, and Arizona
# (no DST) is grouped with Mountain — both approximations are fine for a
# zones-crossed count.
# Source: https://en.wikipedia.org/wiki/Time_in_the_United_States
TEAM_TIMEZONES = {
    # Eastern
    "Atlanta Hawks": 0, "Boston Celtics": 0, "Brooklyn Nets": 0,
    "Charlotte Bobcats": 0, "Charlotte Hornets": 0, "Cleveland Cavaliers": 0,
    "Detroit Pistons": 0, "Indiana Pacers": 0, "Miami Heat": 0,
    "New Jersey Nets": 0, "New York Knicks": 0, "Orlando Magic": 0,
    "Philadelphia 76ers": 0, "Toronto Raptors": 0, "Washington Bullets": 0,
    "Washington Wizards": 0,
    # Central
    "Chicago Bulls": 1, "Dallas Mavericks": 1, "Houston Rockets": 1,
    "Kansas City Kings": 1, "Memphis Grizzlies": 1, "Milwaukee Bucks": 1,
    "Minnesota Timberwolves": 1, "New Orleans Hornets": 1,
    "New Orleans Pelicans": 1, "New Orleans/Oklahoma City Hornets": 1,
    "Oklahoma City Thunder": 1, "San Antonio Spurs": 1,
    # Mountain (incl. Arizona, which doesn't observe DST)
    "Denver Nuggets": 2, "Phoenix Suns": 2, "Utah Jazz": 2,
    # Pacific
    "Golden State Warriors": 3, "LA Clippers": 3, "Los Angeles Clippers": 3,
    "Los Angeles Lakers": 3, "Portland Trail Blazers": 3,
    "Sacramento Kings": 3, "San Diego Clippers": 3, "Seattle SuperSonics": 3,
    "Vancouver Grizzlies": 3,
}

TZ_CATEGORIES = ["0", "1", "2", "3"]
TZ_COLORS = {"0": GRAY, "1": "#378add", "2": "#e8a33d", "3": "#e24b4a"}
TZ_LABELS = {
    "0": "Same time zone",
    "1": "1 time zone crossed",
    "2": "2 time zones crossed",
    "3": "3 time zones crossed (coast-to-coast)",
}


def fetch_timezone_data(end_year: int, season_type: str) -> pd.DataFrame | None:
    """
    Per-game result from the cached game log, tagged with how many time
    zones the visiting team crossed. AWAY_WIN = 1 if the visiting team won.
    Games involving a team not in TEAM_TIMEZONES are dropped.
    """
    df = _load_game_log(end_year, season_type)
    if df is None:
        return None

    merged = _merge_home_away_rows(df)
    if merged is None:
        return None

    home_tz = merged["TEAM_NAME_home"].map(TEAM_TIMEZONES)
    away_tz = merged["TEAM_NAME_away"].map(TEAM_TIMEZONES)
    merged = merged[home_tz.notna() & away_tz.notna()].copy()
    if merged.empty:
        return None

    home_tz = merged["TEAM_NAME_home"].map(TEAM_TIMEZONES)
    away_tz = merged["TEAM_NAME_away"].map(TEAM_TIMEZONES)
    merged["TZ_DIFF"] = (home_tz - away_tz).abs().astype(int)
    merged["HOME_WIN"] = (merged["WL_home"] == "W").astype(int)
    return merged[["TZ_DIFF", "HOME_WIN"]]


def compute_timezone_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], dict]:
    """Per-season home win % grouped by time zones the visiting team crossed."""
    seasons: list[str] = []
    stats: dict[str, list[float]] = {cat: [] for cat in TZ_CATEGORIES}

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        g = fetch_timezone_data(year, season_type)
        if g is None or g.empty:
            continue

        seasons.append(short_label(year))
        for cat in TZ_CATEGORIES:
            sub = g[g["TZ_DIFF"] == int(cat)]
            stats[cat].append(100 * sub["HOME_WIN"].mean() if len(sub) else np.nan)

    return seasons, stats


def main() -> None:
    reg_seasons, reg_pcts, po_seasons, po_pcts = fetch_all_seasons()
    era_reg_avg, era_po_avg, era_labels_short = compute_era_averages(
        reg_seasons, reg_pcts, po_seasons, po_pcts
    )
    format_reg_avg, format_po_avg, format_labels_short = compute_playoff_format_averages(
        reg_seasons, reg_pcts, po_seasons, po_pcts
    )
    plot_results(
        reg_seasons, reg_pcts, po_seasons, po_pcts,
        era_reg_avg, era_po_avg, era_labels_short,
        format_reg_avg, format_po_avg, format_labels_short,
    )

    rest_seasons, rest_stats = compute_rest_stats(START_YEAR, END_YEAR, SeasonType.regular)
    plot_rest_analysis(rest_seasons, rest_stats,
                        season_label="Regular season",
                        output_path="nba_home_court_advantage_rest.png")

    po_rest_seasons, po_rest_stats = compute_rest_stats(
        START_YEAR, END_YEAR, "Playoffs", skip_years=SKIP_PLAYOFF_YEARS
    )
    plot_rest_analysis(po_rest_seasons, po_rest_stats,
                        season_label="Playoffs",
                        output_path="nba_home_court_advantage_rest_playoffs.png",
                        extra_subtitle="; first round each year dropped (no prior playoff game for rest calc)")

    import nba_home_court_regression
    nba_home_court_regression.run()


if __name__ == "__main__":
    main()
