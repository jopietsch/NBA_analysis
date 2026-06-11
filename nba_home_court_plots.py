"""
nba_home_court_plots.py — visualization for NBA home court advantage analysis.

All plot_* functions that generate and save PNG charts. Data is provided
by nba_home_court_data; this module adds only matplotlib rendering.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker

from nba_home_court_data import (
    ERA_DEFS, PLAYOFF_FORMAT_CHANGES, COVID_SEASONS, SHOT_ZONE_GROUPS,
    label_to_year, bucket_stats_by_era, _align_to_seasons,
)


# ── Colors ────────────────────────────────────────────────────────────────────
BLUE  = "#378add"
GREEN = "#1d9e75"
RED   = "#e24b4a"
GRAY  = "#888780"
BG    = "#f9f9f7"
PANEL = "#ffffff"

# One background shade per era (matches order of ERA_DEFS)
ERA_COLORS = ["#7c6fce", "#378add", "#1d9e75", "#e8a33d", "#c2538a", "#5a8f29"]

# Display metadata for altitude, timezone, travel, and shot zone analyses
ALTITUDE_COLORS = {
    "Denver Nuggets": "#e8a33d",
    "Utah Jazz":      "#7c6fce",
    "other":          GRAY,
}
ALTITUDE_LABELS = {
    "Denver Nuggets": "Denver (5,280 ft)",
    "Utah Jazz":      "Utah (4,226 ft)",
    "other":          "All other arenas (avg)",
}

TZ_COLORS = {"0": GRAY, "1": "#378add", "2": "#e8a33d", "3": "#e24b4a"}
TZ_LABELS = {
    "0": "Same time zone",
    "1": "1 time zone crossed",
    "2": "2 time zones crossed",
    "3": "3 time zones crossed (coast-to-coast)",
}

TRAVEL_COLORS = {
    "0–500":     GRAY,
    "500–1000":  BLUE,
    "1000–1500": "#e8a33d",
    "1500+":     RED,
}
TRAVEL_LABELS = {
    "0–500":     "< 500 mi",
    "500–1000":  "500–1,000 mi",
    "1000–1500": "1,000–1,500 mi",
    "1500+":     "1,500+ mi (long haul)",
}

SHOT_ZONE_LABELS: dict[str, str] = {
    "paint":    "Paint (RA + Non-RA)",
    "midrange": "Mid-Range",
    "corner3":  "Corner 3",
    "above3":   "Above Break 3",
}
SHOT_ZONE_COLORS: dict[str, str] = {
    "paint":    BLUE,
    "midrange": GRAY,
    "corner3":  GREEN,
    "above3":   RED,
}


# ── Drawing helpers ───────────────────────────────────────────────────────────
def _shade_eras(ax: plt.Axes, seasons: list[str], label_y: float | None = 46) -> None:
    for (label, y1, y2, _), era_color in zip(ERA_DEFS, ERA_COLORS):
        era_idx = [i for i, s in enumerate(seasons) if y1 <= label_to_year(s) <= y2]
        if not era_idx:
            continue
        ax.axvspan(min(era_idx) - 0.5, max(era_idx) + 0.5, alpha=0.08, color=era_color, zorder=0)
        if min(era_idx) > 0:
            ax.axvline(min(era_idx) - 0.5, color=GRAY, linestyle=":", linewidth=0.8, alpha=0.6)
        if label_y is not None:
            mid = (min(era_idx) + max(era_idx)) / 2
            ax.text(mid, label_y, label, ha="center", va="bottom", fontsize=7.5, color=GRAY)


def _annotate_bars(ax: plt.Axes, bars, color: str) -> None:
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.3,
                f"{bar.get_height():.1f}%",
                ha="center", va="bottom", fontsize=7.5, color=color)


def _draw_season_overview(
    ax: plt.Axes,
    reg_seasons: list[str], reg_pcts: list[float],
    po_seasons: list[str], po_pcts: list[float],
) -> None:
    x = np.arange(len(reg_seasons))
    pt_colors = [RED if s in COVID_SEASONS else BLUE for s in reg_seasons]

    ax.plot(x, reg_pcts, color=BLUE, linewidth=2, zorder=2)
    ax.scatter(x, reg_pcts, c=pt_colors, s=40, zorder=3, edgecolors="white", linewidths=0.8)

    po_pct_by_season = dict(zip(po_seasons, po_pcts))
    po_pcts_aligned = [po_pct_by_season.get(s, np.nan) for s in reg_seasons]
    ax.plot(x, po_pcts_aligned, color=GREEN, linewidth=2, zorder=2)
    ax.scatter(x, po_pcts_aligned, color=GREEN, s=40, zorder=3, edgecolors="white", linewidths=0.8)

    z = np.polyfit(x, reg_pcts, 1)
    ax.plot(x, np.poly1d(z)(x), "--", color=BLUE, linewidth=1.4, alpha=0.5)

    po_pcts_arr = np.array(po_pcts_aligned, dtype=float)
    po_mask = ~np.isnan(po_pcts_arr)
    zp = np.polyfit(x[po_mask], po_pcts_arr[po_mask], 1)
    ax.plot(x, np.poly1d(zp)(x), "--", color=GREEN, linewidth=1.4, alpha=0.5)

    _shade_eras(ax, reg_seasons)
    covid_idx = [i for i, s in enumerate(reg_seasons) if s in COVID_SEASONS]
    if covid_idx:
        ax.axvspan(min(covid_idx) - 0.5, max(covid_idx) + 0.5, alpha=0.12, color=RED, zorder=1)

    ax.set_title("Regular season vs playoffs: home win % per season",
                 fontsize=12, fontweight="bold", color="#2c2c2a", pad=8)
    tick_step = max(1, len(reg_seasons) // 14)
    ax.set_xticks(x[::tick_step])
    ax.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax.set_ylim(45, 80)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.set_ylabel("Home win %", fontsize=10)

    handles = [
        mpatches.Patch(color=BLUE,  label="Regular season"),
        mpatches.Patch(color=GREEN, label="Playoffs"),
        mpatches.Patch(color=RED,   label="COVID-impacted seasons"),
        plt.Line2D([0], [0], color=BLUE,  linestyle="--", alpha=0.5, label="Trend (regular season)"),
        plt.Line2D([0], [0], color=GREEN, linestyle="--", alpha=0.5, label="Trend (playoffs)"),
    ]
    ax.legend(handles=handles, fontsize=9, loc="upper right", framealpha=0.85, edgecolor="#ddd")

    if reg_pcts:
        peak_i = int(np.argmax(reg_pcts))
        low_i  = int(np.argmin(reg_pcts))
        ax.annotate(f"Peak: {reg_pcts[peak_i]:.1f}%\n({reg_seasons[peak_i]})",
                    xy=(peak_i, reg_pcts[peak_i]),
                    xytext=(peak_i + 2, reg_pcts[peak_i] + 1.5),
                    arrowprops=dict(arrowstyle="->", color=GRAY, lw=1),
                    fontsize=8, color=GRAY)
        ax.annotate(f"Low: {reg_pcts[low_i]:.1f}%\n({reg_seasons[low_i]})",
                    xy=(low_i, reg_pcts[low_i]),
                    xytext=(max(low_i - 6, 1), reg_pcts[low_i] - 2.5),
                    arrowprops=dict(arrowstyle="->", color=GRAY, lw=1),
                    fontsize=8, color=GRAY)


def _draw_paired_bars(
    ax: plt.Axes,
    reg_avg: list[float], po_avg: list[float], labels: list[str], title: str,
) -> None:
    xi = np.arange(len(labels))
    w = 0.35
    bars1 = ax.bar(xi - w/2, reg_avg, width=w, color=BLUE,  label="Regular season", zorder=2)
    bars2 = ax.bar(xi + w/2, po_avg,  width=w, color=GREEN, label="Playoffs",        zorder=2)
    _annotate_bars(ax, bars1, BLUE)
    _annotate_bars(ax, bars2, GREEN)
    ax.set_xticks(xi)
    ax.set_xticklabels(labels, rotation=30, ha="right", fontsize=9)
    ax.set_ylim(50, 70)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.set_title(title, fontsize=11, fontweight="bold", color="#2c2c2a", pad=8)
    ax.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")


def _plot_season_era_panel(
    ax: plt.Axes,
    seasons: list[str],
    pcts: list[float],
    color: str,
    title: str,
    format_markers: bool = False,
) -> None:
    x = np.arange(len(seasons))
    tick_step = max(1, len(seasons) // 14)
    pt_colors = [RED if s in COVID_SEASONS else color for s in seasons]

    ax.plot(x, pcts, color=color, linewidth=2, zorder=2)
    ax.scatter(x, pcts, c=pt_colors, s=40, zorder=3, edgecolors="white", linewidths=0.8)

    pcts_arr = np.array(pcts, dtype=float)
    _shade_eras(ax, seasons)

    for (_, y1, y2, _), era_color in zip(ERA_DEFS, ERA_COLORS):
        era_idx = [i for i, s in enumerate(seasons) if y1 <= label_to_year(s) <= y2]
        if len(era_idx) >= 2:
            era_x = np.array(era_idx)
            ze = np.polyfit(era_x, pcts_arr[era_x], 1)
            ax.plot(era_x, np.poly1d(ze)(era_x), "--", color=era_color, linewidth=1.8, alpha=0.8)

    covid_idx = [i for i, s in enumerate(seasons) if s in COVID_SEASONS]
    if covid_idx:
        ax.axvspan(min(covid_idx) - 0.5, max(covid_idx) + 0.5, alpha=0.12, color=RED, zorder=1)

    if format_markers:
        for change_year, change_label in PLAYOFF_FORMAT_CHANGES:
            idx = next((i for i, s in enumerate(seasons) if label_to_year(s) == change_year), None)
            if idx is None:
                continue
            ax.axvline(idx - 0.5, color="#444444", linestyle="-.", linewidth=1, alpha=0.6, zorder=1)
            ax.text(idx - 0.4, 79, change_label, rotation=90, ha="left", va="top",
                    fontsize=6.5, color="#444444", linespacing=1.2)

    ax.set_title(title, fontsize=12, fontweight="bold", color="#2c2c2a", pad=8)
    ax.set_xticks(x[::tick_step])
    ax.set_xticklabels(seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax.set_ylim(45, 80)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.set_ylabel("Home win %", fontsize=10)


# ── Plot functions ────────────────────────────────────────────────────────────
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
    _draw_season_overview(ax1, reg_seasons, reg_pcts, po_seasons, po_pcts)

    # ── Panel 2: playoffs only, with a trend line per era ────────────────────
    ax3 = fig.add_subplot(gs[1, 1:3])
    _plot_season_era_panel(
        ax3, po_seasons, po_pcts, GREEN,
        "Playoffs: home win % per season, with a trend line per era",
        format_markers=True,
    )

    # ── Panel 3: regular season only, with a trend line per era ──────────────
    ax4 = fig.add_subplot(gs[2, 1:3])
    _plot_season_era_panel(
        ax4, reg_seasons, reg_pcts, BLUE,
        "Regular season: home win % per season, with a trend line per era",
    )

    # ── Panel 4: era grouped bar chart ────────────────────────────────────────
    ax2 = fig.add_subplot(gs[3, 0:2])
    _draw_paired_bars(ax2, era_reg_avg, era_po_avg, era_labels_short,
                      "Regular season vs playoffs\nhome win % by era")

    # ── Panel 5: home win % by playoff-format period ──────────────────────────
    ax5 = fig.add_subplot(gs[3, 2:4])
    _draw_paired_bars(ax5, format_reg_avg, format_po_avg, format_labels_short,
                      "Regular season vs playoffs\nhome win % by playoff format period")

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

    # ── Save combined ─────────────────────────────────────────────────────────
    plt.tight_layout()
    plt.savefig("nba_home_court_advantage.png", dpi=150, bbox_inches="tight", facecolor=BG)
    print("\nSaved → nba_home_court_advantage.png")
    plt.close()

    # ── Save individual panels ────────────────────────────────────────────────
    def _save(path: str, draw_fn, figsize: tuple) -> None:
        fig_, ax_ = plt.subplots(1, 1, figsize=figsize)
        fig_.patch.set_facecolor(BG)
        draw_fn(ax_)
        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
        print(f"Saved → {path}")
        plt.close()

    _save("nba_home_court_advantage_season.png",
          lambda ax: _draw_season_overview(ax, reg_seasons, reg_pcts, po_seasons, po_pcts),
          (14, 7))
    _save("nba_home_court_advantage_playoffs_era.png",
          lambda ax: _plot_season_era_panel(
              ax, po_seasons, po_pcts, GREEN,
              "Playoffs: home win % per season, with a trend line per era",
              format_markers=True),
          (14, 6))
    _save("nba_home_court_advantage_regular_era.png",
          lambda ax: _plot_season_era_panel(
              ax, reg_seasons, reg_pcts, BLUE,
              "Regular season: home win % per season, with a trend line per era"),
          (14, 6))
    _save("nba_home_court_advantage_era_bars.png",
          lambda ax: _draw_paired_bars(ax, era_reg_avg, era_po_avg, era_labels_short,
                                       "Regular season vs playoffs\nhome win % by era"),
          (10, 6))
    _save("nba_home_court_advantage_format_bars.png",
          lambda ax: _draw_paired_bars(ax, format_reg_avg, format_po_avg, format_labels_short,
                                       "Regular season vs playoffs\nhome win % by playoff format period"),
          (10, 6))


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


def plot_differential_analysis(
    reg_seasons: list[str], reg_stats: dict,
    po_seasons: list[str], po_stats: dict,
) -> None:
    """
    4-panel figure showing per-season home-minus-away differentials for fouls
    and shooting %, with regular season and playoffs on the same axes.
    A trend toward zero indicates the home-team advantage in that metric is shrinking.
    """
    x = np.arange(len(reg_seasons))
    tick_step = max(1, len(reg_seasons) // 14)

    panels = [
        ("foul_diff",     "Foul differential (home PF − away PF)",
         "Fouls per game",    "negative = refs call fewer fouls on home team"),
        ("fg_pct_diff",   "FG% differential (home − away)",
         "Percentage points", ""),
        ("efg_pct_diff",  "eFG% differential (home − away)",
         "Percentage points", "weights 3-pointers at 1.5×"),
        ("tpa_rate_diff", "3PA rate differential (home − away)",
         "Percentage points", "share of shots that are 3-point attempts"),
        ("fg3_pct_diff",  "3P% differential (home − away)",
         "Percentage points", ""),
        ("ft_pct_diff",   "FT% differential (home − away)",
         "Percentage points", ""),
    ]

    fig, axes = plt.subplots(2, 3, figsize=(22, 10))
    fig.suptitle("Home vs Away Box-Score Differentials — Are the Gaps Closing?",
                 fontsize=15, fontweight="bold", y=0.99, color="#2c2c2a")
    fig.text(0.5, 0.955,
             "Data: NBA.com  |  Positive = home team higher  |  1983-84 through 2024-25",
             ha="center", fontsize=9, color=GRAY)

    for ax, (key, title, ylabel, note) in zip(axes.flat, panels):
        y_reg = np.array(reg_stats[key], dtype=float)
        y_po  = _align_to_seasons(reg_seasons, po_seasons, po_stats, key)

        for y, color, label in [(y_reg, BLUE, "Regular season"), (y_po, GREEN, "Playoffs")]:
            mask = ~np.isnan(y)
            ax.plot(x, y, color=color, linewidth=1.5, alpha=0.7, label=label, zorder=2)
            if mask.sum() >= 2:
                z = np.polyfit(x[mask], y[mask], 1)
                ax.plot(x, np.poly1d(z)(x), "--", color=color, linewidth=1.8, alpha=0.9, zorder=3)

        _shade_eras(ax, reg_seasons, label_y=None)
        ax.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
        ax.set_xticks(x[::tick_step])
        ax.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
        ax.set_title(title, fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")
        if note:
            ax.set_xlabel(note, fontsize=8, color=GRAY)

    plt.tight_layout()
    output_path = "nba_home_court_advantage_differentials.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.show()


def plot_margin_analysis(
    reg_seasons: list[str], reg_stats: dict,
    po_seasons: list[str], po_stats: dict,
) -> None:
    """
    3-panel chart: has the home team's point margin compressed alongside the
    decline in home win percentage?

    Panel 1: mean all-game margin per season (reg + playoffs) with trend lines.
    Panel 2: mean win-only vs loss-only margin per season (regular season).
    Panel 3: era-bucketed bar chart of mean margin, reg vs playoffs.
    """
    x = np.arange(len(reg_seasons))
    tick_step = max(1, len(reg_seasons) // 14)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(22, 7))
    fig.suptitle("Home Team Point Margin — Are Wins Getting Closer?",
                 fontsize=15, fontweight="bold", y=1.03, color="#2c2c2a")
    fig.text(0.5, 0.965,
             "Data: NBA.com  |  Positive = home team winning by more  |  1983-84 through 2024-25",
             ha="center", fontsize=9, color=GRAY)

    # Panel 1: all-game mean margin per season (reg + playoffs aligned)
    y_reg = np.array(reg_stats["all_games_mean"], dtype=float)
    y_po  = _align_to_seasons(reg_seasons, po_seasons, po_stats, "all_games_mean")

    for y, color, label in [(y_reg, BLUE, "Regular season"), (y_po, GREEN, "Playoffs")]:
        mask = ~np.isnan(y)
        ax1.plot(x, y, color=color, linewidth=1.5, alpha=0.8, label=label, zorder=2)
        if mask.sum() >= 2:
            z = np.polyfit(x[mask], y[mask], 1)
            ax1.plot(x, np.poly1d(z)(x), "--", color=color, linewidth=1.8, alpha=0.9, zorder=3)

    _shade_eras(ax1, reg_seasons, label_y=None)
    ax1.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
    ax1.set_xticks(x[::tick_step])
    ax1.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax1.set_title("Mean margin per season (all games)",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    ax1.set_ylabel("Home point margin (home − away pts)", fontsize=10)
    ax1.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    # Panel 2: win-only vs loss-only margin per season (regular season)
    y_wins   = np.array(reg_stats["home_wins_mean"],   dtype=float)
    y_losses = np.array(reg_stats["home_losses_mean"], dtype=float)

    for y, color, label in [
        (y_wins,   BLUE, "Home wins"),
        (y_losses, RED,  "Home losses"),
    ]:
        mask = ~np.isnan(y)
        ax2.plot(x, y, color=color, linewidth=1.5, alpha=0.8, label=label, zorder=2)
        if mask.sum() >= 2:
            z = np.polyfit(x[mask], y[mask], 1)
            ax2.plot(x, np.poly1d(z)(x), "--", color=color, linewidth=1.8, alpha=0.9, zorder=3)

    _shade_eras(ax2, reg_seasons, label_y=None)
    ax2.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
    ax2.set_xticks(x[::tick_step])
    ax2.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax2.set_title("Win/loss margin by season (regular season)",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    ax2.set_ylabel("Home point margin (home − away pts)", fontsize=10)
    ax2.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    # Panel 3: era-bucketed bar chart (reg vs playoff mean all-game margin)
    reg_era, era_labels = bucket_stats_by_era(reg_seasons, {"reg": reg_stats["all_games_mean"]})
    po_era,  _          = bucket_stats_by_era(po_seasons,  {"po":  po_stats["all_games_mean"]})

    xi = np.arange(len(era_labels))
    w  = 0.35
    bars1 = ax3.bar(xi - w / 2, reg_era["reg"], width=w, color=BLUE,  label="Regular season", zorder=2)
    bars2 = ax3.bar(xi + w / 2, po_era["po"],   width=w, color=GREEN, label="Playoffs",        zorder=2)
    for bars, color in [(bars1, BLUE), (bars2, GREEN)]:
        for bar in bars:
            h  = bar.get_height()
            va = "bottom" if h >= 0 else "top"
            ax3.text(bar.get_x() + bar.get_width() / 2, h + (0.1 if h >= 0 else -0.1),
                     f"{h:+.1f}", ha="center", va=va, fontsize=7.5, color=color)

    ax3.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
    ax3.set_xticks(xi)
    ax3.set_xticklabels(era_labels, rotation=30, ha="right", fontsize=9)
    ax3.set_title("Mean margin by era",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    ax3.set_ylabel("Home point margin (home − away pts)", fontsize=10)
    ax3.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    plt.tight_layout()
    output_path = "nba_home_court_margin.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.show()


def plot_parity_analysis(
    parity_seasons: list[str], parity_std: list[float],
    reg_seasons: list[str], reg_pcts: list[float],
) -> None:
    """
    2-panel chart: does competitive balance track with home court advantage?

    Panel 1: dual-axis time series — home win % and team win% std dev over seasons.
    Panel 2: scatter of parity std dev vs. home win %, era-colored with trend line.
    """
    parity_lookup = dict(zip(parity_seasons, parity_std))
    y_parity = np.array([parity_lookup.get(s, np.nan) for s in reg_seasons], dtype=float)
    y_reg    = np.array(reg_pcts, dtype=float)
    x        = np.arange(len(reg_seasons))
    tick_step = max(1, len(reg_seasons) // 14)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Does Competitive Balance Explain the Decline in Home Court Advantage?",
                 fontsize=14, fontweight="bold", y=1.03, color="#2c2c2a")
    fig.text(0.5, 0.965,
             "Data: NBA.com  |  Regular season  |  Parity = std dev of team win % per season  "
             "(lower = more equal league)",
             ha="center", fontsize=9, color=GRAY)

    # Panel 1: dual-axis time series
    _shade_eras(ax1, reg_seasons, label_y=None)
    ax1.plot(x, y_reg, color=BLUE, linewidth=2, label="Home win %", zorder=2)
    ax1.set_xticks(x[::tick_step])
    ax1.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.set_ylabel("Home win %", color=BLUE, fontsize=10)
    ax1.tick_params(axis="y", labelcolor=BLUE)
    ax1.set_title("Home win % and competitive parity over time",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)

    ax1r = ax1.twinx()
    mask_p = ~np.isnan(y_parity)
    ax1r.plot(x, y_parity, color=RED, linewidth=2, label="Win% std dev", zorder=2, alpha=0.8)
    if mask_p.sum() >= 2:
        z = np.polyfit(x[mask_p], y_parity[mask_p], 1)
        ax1r.plot(x, np.poly1d(z)(x), "--", color=RED, linewidth=1.4, alpha=0.5)
    ax1r.set_ylabel("Team win% std dev\n(lower = more parity)", color=RED, fontsize=9)
    ax1r.tick_params(axis="y", labelcolor=RED)

    lines1, labs1 = ax1.get_legend_handles_labels()
    lines2, labs2 = ax1r.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labs1 + labs2, fontsize=9, framealpha=0.85, edgecolor="#ddd")

    # Panel 2: scatter (one point per season), era-colored, with trend line
    for s, px, py in zip(reg_seasons, y_parity, y_reg):
        if np.isnan(px) or np.isnan(py):
            continue
        yr = label_to_year(s)
        color = GRAY
        for (_, y1, y2, _), era_color in zip(ERA_DEFS, ERA_COLORS):
            if y1 <= yr <= y2:
                color = era_color
                break
        ax2.scatter(px, py, color=color, s=60, zorder=3, edgecolors="white", linewidths=0.8)

    both_valid = ~np.isnan(y_parity) & ~np.isnan(y_reg)
    if both_valid.sum() >= 2:
        z_sc = np.polyfit(y_parity[both_valid], y_reg[both_valid], 1)
        px_range = np.linspace(y_parity[both_valid].min(), y_parity[both_valid].max(), 100)
        ax2.plot(px_range, np.poly1d(z_sc)(px_range), "--", color=GRAY, linewidth=1.8, alpha=0.7)

    era_patches = [mpatches.Patch(color=c, label=e[0]) for e, c in zip(ERA_DEFS, ERA_COLORS)]
    ax2.legend(handles=era_patches, fontsize=8, framealpha=0.85, edgecolor="#ddd",
               title="Era", title_fontsize=8)
    ax2.set_xlabel("Team win% std dev (parity)", fontsize=10)
    ax2.set_ylabel("Home win %", fontsize=10)
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax2.set_title("Parity vs. home court advantage\n(one point per season)",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)

    plt.tight_layout()
    output_path = "nba_home_court_parity.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.show()


def plot_series_breakdown(
    game_nums: list[int],
    home_win_pcts: list[float],
    game_counts: list[int],
    era_data: dict[str, dict[int, float]],
    overall_po_pct: float,
) -> None:
    """
    2-panel chart: home win % by game-within-series number.

    Panel 1: bar chart of overall home win % by G1–G7, sample size labels,
             reference line at the overall playoff home win average.
    Panel 2: G1–G7 home win % per era (one line per era, era-colored).
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle("Playoff Series Structure — Home Win % by Game Number",
                 fontsize=14, fontweight="bold", y=1.03, color="#2c2c2a")
    fig.text(0.5, 0.965,
             "Data: NBA.com  |  Playoffs 1983–84 through 2024–25  |  2020 bubble excluded  |  "
             "G1/G2 at higher seed; G3/G4 at lower seed (2-2-1-1-1 format)",
             ha="center", fontsize=9, color=GRAY)

    # Panel 1: overall bar chart
    x     = np.arange(len(game_nums))
    xlbls = [f"G{g}" for g in game_nums]
    bars  = ax1.bar(x, home_win_pcts, color=GREEN, width=0.6, zorder=2,
                    edgecolor="white", linewidth=0.8)
    ax1.axhline(overall_po_pct, color=GRAY, linewidth=1.5, linestyle="--",
                label=f"Overall playoff avg ({overall_po_pct:.1f}%)", zorder=3)
    for bar, pct, count in zip(bars, home_win_pcts, game_counts):
        ax1.text(bar.get_x() + bar.get_width() / 2, pct + 0.6,
                 f"{pct:.1f}%", ha="center", va="bottom", fontsize=8.5,
                 color=GREEN, fontweight="bold")
        ax1.text(bar.get_x() + bar.get_width() / 2, 1,
                 f"n={count:,}", ha="center", va="bottom", fontsize=7, color=GRAY)
    ax1.set_xticks(x)
    ax1.set_xticklabels(xlbls, fontsize=10)
    ax1.set_ylim(0, 85)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.set_ylabel("Home win %", fontsize=10)
    ax1.set_title("Home win % by game within series (all eras)",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    ax1.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    # Panel 2: by-era lines
    for (era_label, _, _, _), era_color in zip(ERA_DEFS, ERA_COLORS):
        pcts = era_data.get(era_label, {})
        if not pcts:
            continue
        gx = sorted(pcts.keys())
        gy = [pcts[g] for g in gx]
        ax2.plot([g - 1 for g in gx], gy, color=era_color, linewidth=2,
                 label=era_label, marker="o", markersize=5,
                 markeredgecolor="white", markeredgewidth=0.8)

    ax2.axhline(overall_po_pct, color=GRAY, linewidth=1.2, linestyle="--", alpha=0.6,
                label=f"Overall avg ({overall_po_pct:.1f}%)")
    ax2.set_xticks(range(7))
    ax2.set_xticklabels([f"G{g}" for g in range(1, 8)], fontsize=10)
    ax2.set_ylim(30, 90)
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax2.set_ylabel("Home win %", fontsize=10)
    ax2.set_title("Home win % by game number, per era",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    ax2.legend(fontsize=8, framealpha=0.85, edgecolor="#ddd",
               title="Era", title_fontsize=8)

    plt.tight_layout()
    output_path = "nba_home_court_series_breakdown.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.show()


def plot_shot_zone_analysis(
    reg_seasons: list[str], reg_stats: dict,
    po_seasons: list[str], po_stats: dict,
) -> None:
    """
    4-panel figure: home-minus-road shot zone % differentials over time,
    regular season and playoffs on the same axes.
    A trend toward zero = away teams gaining access to the same shot quality.
    """
    x = np.arange(len(reg_seasons))
    tick_step = max(1, len(reg_seasons) // 14)

    fig, axes = plt.subplots(2, 2, figsize=(16, 10))
    fig.suptitle("Shot Zone Differentials: Home vs Road — Are Away Teams Getting Better Looks?",
                 fontsize=14, fontweight="bold", y=0.99, color="#2c2c2a")
    fig.text(0.5, 0.955,
             "Data: NBA.com  |  Positive = home team higher share of FGA  |  1983-84 through 2024-25",
             ha="center", fontsize=9, color=GRAY)

    for ax, (zone, label) in zip(axes.flat, SHOT_ZONE_LABELS.items()):
        color = SHOT_ZONE_COLORS[zone]
        y_reg = np.array(reg_stats[zone], dtype=float)
        y_po  = _align_to_seasons(reg_seasons, po_seasons, po_stats, zone)

        for y, lcolor, llabel in [(y_reg, color, "Regular season"),
                                   (y_po, color, "Playoffs")]:
            ls = "-" if llabel == "Regular season" else "--"
            alpha = 0.9 if llabel == "Regular season" else 0.6
            mask = ~np.isnan(y)
            ax.plot(x, y, color=lcolor, linewidth=2, linestyle=ls,
                    alpha=alpha, label=llabel, zorder=2)
            if mask.sum() >= 2:
                z = np.polyfit(x[mask], y[mask], 1)
                ax.plot(x, np.poly1d(z)(x), ":", color=lcolor, linewidth=1.5,
                        alpha=alpha * 0.7, zorder=3)

        _shade_eras(ax, reg_seasons, label_y=None)
        ax.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
        ax.set_title(f"{label} % differential (home − road)",
                     fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
        ax.set_ylabel("Percentage points", fontsize=10)
        ax.set_xticks(x[::tick_step])
        ax.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
        ax.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    plt.tight_layout()
    output_path = "nba_home_court_shot_zones.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.show()


def plot_3pa_hca_analysis(
    reg_seasons: list[str], reg_tpa: list[float], reg_pcts: list[float],
    po_seasons:  list[str], po_tpa:  list[float], po_pcts:  list[float],
) -> None:
    """
    3-panel figure: does the league-wide 3-point shooting rate drive the decline
    in home court advantage?

    Panel 1: dual-axis time series — regular-season 3PA rate (right axis, orange)
             vs. home win % (left axis, blue), era-shaded.
    Panel 2: scatter regular season — x = 3PA rate, y = home win %, era-colored,
             trend line, Pearson r annotation.
    Panel 3: scatter playoffs — same layout.
    """
    from scipy.stats import pearsonr

    ORANGE = "#e8a33d"

    x_reg = np.arange(len(reg_seasons))
    tick_step = max(1, len(reg_seasons) // 14)
    y_tpa_reg = np.array(reg_tpa, dtype=float)
    y_pct_reg = np.array(reg_pcts, dtype=float)
    y_tpa_po  = np.array(po_tpa,  dtype=float)
    y_pct_po  = np.array(po_pcts, dtype=float)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 6))
    fig.suptitle("Does League-Wide 3-Point Shooting Explain the Decline in Home Court Advantage?",
                 fontsize=14, fontweight="bold", y=1.03, color="#2c2c2a")
    fig.text(0.5, 0.965,
             "Data: NBA.com  |  3PA rate = share of all field-goal attempts that are 3-pointers  "
             "|  1983–84 through 2024–25",
             ha="center", fontsize=9, color=GRAY)

    # ── Panel 1: dual-axis time series (regular season) ─────────────────────
    _shade_eras(ax1, reg_seasons, label_y=None)
    ax1.plot(x_reg, y_pct_reg, color=BLUE, linewidth=2, label="Home win %", zorder=2)
    ax1.set_xticks(x_reg[::tick_step])
    ax1.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.set_ylabel("Home win %", color=BLUE, fontsize=10)
    ax1.tick_params(axis="y", labelcolor=BLUE)
    ax1.set_title("Regular-season 3PA rate vs. home win %\nover time",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)

    ax1r = ax1.twinx()
    ax1r.plot(x_reg, y_tpa_reg, color=ORANGE, linewidth=2, label="3PA rate %", zorder=2, alpha=0.85)
    ax1r.set_ylabel("League 3PA rate (% of FGA)", color=ORANGE, fontsize=10)
    ax1r.tick_params(axis="y", labelcolor=ORANGE)
    ax1r.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))

    lines1, labs1 = ax1.get_legend_handles_labels()
    lines2, labs2 = ax1r.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labs1 + labs2, fontsize=9, framealpha=0.85, edgecolor="#ddd")

    # ── Panels 2 & 3: scatter (one point per season) ─────────────────────────
    def _scatter_panel(ax, seasons, x_vals, y_vals, title):
        for s, xv, yv in zip(seasons, x_vals, y_vals):
            if np.isnan(xv) or np.isnan(yv):
                continue
            yr = label_to_year(s)
            color = GRAY
            for (_, y1, y2, _), era_color in zip(ERA_DEFS, ERA_COLORS):
                if y1 <= yr <= y2:
                    color = era_color
                    break
            ax.scatter(xv, yv, color=color, s=60, zorder=3, edgecolors="white", linewidths=0.8)

        valid = ~np.isnan(np.array(x_vals)) & ~np.isnan(np.array(y_vals))
        xv_arr = np.array(x_vals)[valid]
        yv_arr = np.array(y_vals)[valid]
        if valid.sum() >= 4:
            z = np.polyfit(xv_arr, yv_arr, 1)
            xr = np.linspace(xv_arr.min(), xv_arr.max(), 100)
            ax.plot(xr, np.poly1d(z)(xr), "--", color=GRAY, linewidth=1.8, alpha=0.7)
            r, p = pearsonr(xv_arr, yv_arr)
            p_str = "<0.001" if p < 0.001 else f"{p:.3f}"
            ax.text(0.05, 0.05, f"Pearson r = {r:+.2f}  (p = {p_str})",
                    transform=ax.transAxes, fontsize=9, color="#444",
                    bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.7))

        era_patches = [mpatches.Patch(color=c, label=e[0]) for e, c in zip(ERA_DEFS, ERA_COLORS)]
        ax.legend(handles=era_patches, fontsize=8, framealpha=0.85, edgecolor="#ddd",
                  title="Era", title_fontsize=8)
        ax.set_xlabel("League 3PA rate (% of FGA)", fontsize=10)
        ax.set_ylabel("Home win %", fontsize=10)
        ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        ax.set_title(title, fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)

    _scatter_panel(ax2, reg_seasons, list(y_tpa_reg), list(y_pct_reg),
                   "Regular season: 3PA rate vs. home win %\n(one point per season)")
    _scatter_panel(ax3, po_seasons,  list(y_tpa_po),  list(y_pct_po),
                   "Playoffs: 3PA rate vs. home win %\n(one point per season)")

    plt.tight_layout()
    output_path = "nba_home_court_3pa.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.show()
