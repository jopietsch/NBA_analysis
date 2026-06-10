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
COVID_SEASONS = {"19-20", "20-21"}

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
# Eras are bounded by major NBA rule changes affecting pace/defense:
ERA_DEFS = [
    ("1984–94", 1984, 1994),  # Illegal defense rules (no zone defense)
    ("1995–01", 1995, 2001),  # 1994 hand-checking restrictions; zone still illegal
    ("2002–04", 2002, 2004),  # 2001: zone defense legalized, defensive 3-sec added
    ("2005–17", 2005, 2017),  # 2004-05: perimeter hand-checking banned (pace-and-space era)
    ("2018–25", 2018, 2025),  # 2017-18: freedom-of-movement / transition take-foul rules
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
        time.sleep(SLEEP_SEC)

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
            time.sleep(SLEEP_SEC)

    print(f"\nRegular season: {len(reg_seasons)} seasons fetched")
    print(f"Playoffs:       {len(po_seasons)} seasons fetched")

    return reg_seasons, reg_pcts, po_seasons, po_pcts


def compute_era_averages(
    reg_seasons: list[str], reg_pcts: list[float],
    po_seasons: list[str], po_pcts: list[float],
) -> tuple[list[float], list[float], list[str]]:
    """Average regular-season and playoff home win % within each era."""
    era_reg_avg, era_po_avg = [], []
    for _, y1, y2 in ERA_DEFS:
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

    fig = plt.figure(figsize=(15, 13))
    fig.suptitle("NBA Home Court Advantage — A 40-Year Decline",
                 fontsize=18, fontweight="bold", y=0.98, color="#2c2c2a")
    fig.text(0.5, 0.955,
             "Data: NBA.com via nba_api  |  Regular season & playoffs  |  1983-84 through 2024-25",
             ha="center", fontsize=9, color=GRAY)

    gs = fig.add_gridspec(2, 2, hspace=0.45, wspace=0.32,
                          left=0.07, right=0.97, top=0.93, bottom=0.06)

    # ── Panel 1: season-by-season regular season line ───────────────────────
    ax1 = fig.add_subplot(gs[0, :])
    x = np.arange(len(reg_seasons))
    pt_colors = [RED if s in COVID_SEASONS else BLUE for s in reg_seasons]

    ax1.plot(x, reg_pcts, color=BLUE, linewidth=2, zorder=2)
    ax1.scatter(x, reg_pcts, c=pt_colors, s=40, zorder=3,
                edgecolors="white", linewidths=0.8)

    # Trend line
    z = np.polyfit(x, reg_pcts, 1)
    ax1.plot(x, np.poly1d(z)(x), "--", color=GRAY, linewidth=1.4, alpha=0.7)

    # Shade COVID seasons
    covid_idx = [i for i, s in enumerate(reg_seasons) if s in COVID_SEASONS]
    if covid_idx:
        ax1.axvspan(min(covid_idx) - 0.5, max(covid_idx) + 0.5,
                    alpha=0.12, color=RED)

    ax1.set_title("Regular season: home win % per season",
                  fontsize=12, fontweight="bold", color="#2c2c2a", pad=8)
    ax1.set_xticks(x)
    ax1.set_xticklabels(reg_seasons, rotation=45, ha="right", fontsize=8)
    ax1.set_ylim(49, 71)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.set_ylabel("Home win %", fontsize=10)

    handles1 = [
        mpatches.Patch(color=BLUE, label="Home win %"),
        mpatches.Patch(color=RED,  label="COVID-impacted seasons"),
        plt.Line2D([0], [0], color=GRAY, linestyle="--", label="Trend line"),
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

    # ── Panel 2: era grouped bar chart ───────────────────────────────────────
    ax2 = fig.add_subplot(gs[1, 0])
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

    # ── Panel 3: playoff season-by-season line ───────────────────────────────
    ax3 = fig.add_subplot(gs[1, 1])
    xp = np.arange(len(po_seasons))
    ax3.plot(xp, po_pcts, color=GREEN, linewidth=2, zorder=2)
    ax3.scatter(xp, po_pcts, color=GREEN, s=35, zorder=3,
                edgecolors="white", linewidths=0.8)

    if len(xp) > 1:
        zp = np.polyfit(xp, po_pcts, 1)
        ax3.plot(xp, np.poly1d(zp)(xp), "--", color=GRAY, linewidth=1.4, alpha=0.7)

    tick_step = max(1, len(po_seasons) // 12)
    ax3.set_xticks(xp[::tick_step])
    ax3.set_xticklabels(po_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax3.set_ylim(45, 80)
    ax3.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax3.set_ylabel("Home win %", fontsize=10)
    ax3.set_title("Playoffs: home win % per season\n(2020 bubble excluded)",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=8)

    handles3 = [
        mpatches.Patch(color=GREEN, label="Playoff home win %"),
        plt.Line2D([0], [0], color=GRAY, linestyle="--", label="Trend line"),
    ]
    ax3.legend(handles=handles3, fontsize=9, framealpha=0.85, edgecolor="#ddd")

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
