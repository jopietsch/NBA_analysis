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
) -> None:
    """Build the 3-panel figure and save/show it."""
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
    ax2 = fig.add_subplot(gs[3, 1:3])
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


def main() -> None:
    reg_seasons, reg_pcts, po_seasons, po_pcts = fetch_all_seasons()
    era_reg_avg, era_po_avg, era_labels_short = compute_era_averages(
        reg_seasons, reg_pcts, po_seasons, po_pcts
    )
    plot_results(
        reg_seasons, reg_pcts, po_seasons, po_pcts,
        era_reg_avg, era_po_avg, era_labels_short,
    )


if __name__ == "__main__":
    main()
