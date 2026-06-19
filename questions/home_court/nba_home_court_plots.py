"""
nba_home_court_plots.py — visualization for NBA home court advantage analysis.

All plot_* functions that generate and save PNG charts. Data is provided
by nba_home_court_data; this module adds only matplotlib rendering.
"""

import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from scipy.stats import pearsonr

from nba_home_court_data import (
    ERA_DEFS, COVID_SEASONS,
    label_to_year, bucket_stats_by_era, _align_to_seasons, season_range_label,
)
from nbakit.viz import (
    BLUE, GREEN, RED, GRAY, BG, PANEL,
    output_path,
    annotate_bars as _annotate_bars,
    add_trend_line as _add_trend_line,
)

# All generated PNG charts are written here.
OUTPUT_DIR = "generated"


def _output_path(name: str) -> str:
    """Return the path under OUTPUT_DIR for a chart file, creating the dir."""
    return output_path(name, OUTPUT_DIR)


# ── Colors ────────────────────────────────────────────────────────────────────
# Base palette (BLUE/GREEN/RED/GRAY/BG/PANEL) comes from nbakit.viz.
# One background shade per era (matches order of ERA_DEFS)
ERA_COLORS = ["#7c6fce", "#378add", "#1d9e75", "#e8a33d", "#c2538a", "#5a8f29"]

# Display metadata for shot zone analysis
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

# Canonical order and colors for the four box-score categories, used across
# mediation, 3PA-control, and any other category-breakdown charts.
CATEGORY_ORDER: list[str] = ["Shooting", "Rebounding", "Fouls", "Turnovers"]
CATEGORY_COLORS: dict[str, str] = {
    "Shooting":   BLUE,
    "Rebounding": GREEN,
    "Fouls":      RED,
    "Turnovers":  "#e8a33d",
}

# Panel descriptors for the box-score differential time-series chart.
# Each entry: (data_key, panel_title, y_label, footnote)
DIFF_PANELS: list[tuple[str, str, str, str]] = [
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

# Panel descriptors for the player-tracking rebounding chart.
# Each entry: (data_key, panel_title, y_label, footnote)
TRACKING_PANELS: list[tuple[str, str, str, str]] = [
    ("oreb_chance_pct_edge",
     "Offensive-rebound conversion edge",
     "Percentage points", "home minus road: share of O-reb chances converted"),
    ("boxout_edge",
     "Box-out edge",
     "Box-outs per game", "home minus road (tracked from ~2016)"),
    ("second_chance_edge",
     "Second-chance points edge",
     "Points per game", "home minus road"),
]


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

    # Single overall trend lines across all seasons.
    zs_reg = np.polyfit(x, reg_pcts, 1)
    ax.plot(x, np.poly1d(zs_reg)(x), "--", color=BLUE, linewidth=1.4, alpha=0.5)

    po_arr = np.array(po_pcts_aligned, dtype=float)
    po_mask = np.isfinite(po_arr)
    if po_mask.sum() >= 2:
        zs_po = np.polyfit(x[po_mask], po_arr[po_mask], 1)
        ax.plot(x, np.poly1d(zs_po)(x), "--", color=GREEN, linewidth=1.4, alpha=0.5)

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
        plt.Line2D([0], [0], color=BLUE,  linestyle="--", alpha=0.5, label="Overall trend (regular season)"),
        plt.Line2D([0], [0], color=GREEN, linestyle="--", alpha=0.5, label="Overall trend (playoffs)"),
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


# ── Plot functions ────────────────────────────────────────────────────────────
def plot_results(
    reg_seasons: list[str], reg_pcts: list[float],
    po_seasons: list[str], po_pcts: list[float],
    format_reg_avg: list[float], format_po_avg: list[float], format_labels_short: list[str],
) -> None:
    """Save the standalone season and format-period panels."""
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

    # ── Save individual panels ────────────────────────────────────────────────
    def _save(path: str, draw_fn, figsize: tuple) -> None:
        fig_, ax_ = plt.subplots(1, 1, figsize=figsize)
        fig_.patch.set_facecolor(BG)
        draw_fn(ax_)
        plt.tight_layout()
        plt.savefig(path, dpi=150, bbox_inches="tight", facecolor=BG)
        print(f"Saved → {path}")
        plt.close()

    _save(_output_path("nba_home_court_advantage_season.png"),
          lambda ax: _draw_season_overview(ax, reg_seasons, reg_pcts, po_seasons, po_pcts),
          (14, 7))
    _save(_output_path("nba_home_court_advantage_format_bars.png"),
          lambda ax: _draw_paired_bars(ax, format_reg_avg, format_po_avg, format_labels_short,
                                       "Regular season vs playoffs\nhome win % by playoff format period"),
          (5, 3))


def plot_rest_altitude(data: dict) -> None:
    """
    Two-panel view of the two situational edges from Section 2: rest and
    altitude. Left: home win % by rest situation (away more rested / equal /
    home more rested), regular season vs playoffs. Right: home win % for the
    two high-altitude franchises (Denver, Utah) against the league baseline,
    regular season vs playoffs — the altitude edge is real in the regular
    season and largely gone in the playoffs.

    `data` comes from regression.compute_rest_altitude_plotdata(); same
    numbers RESULTS.md prints, no new data.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("The Situational Edges: Rest and Altitude",
                 fontsize=14, fontweight="bold", y=1.0, color="#2c2c2a")
    fig.text(0.5, 0.95,
             f"Data: NBA.com  |  home win % by situation  |  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    ctx_styles = [("reg", "Regular season", GREEN), ("po", "Playoffs", BLUE)]

    # ── Panel 1: rest buckets ────────────────────────────────────────────────
    bucket_order = ["Away more rested", "Equal rest", "Home more rested"]
    x = np.arange(len(bucket_order))
    width = 0.38
    for i, (ctx, label, color) in enumerate(ctx_styles):
        rest = data["rest"][ctx]["buckets"]
        vals = [rest.get(b, (np.nan, 0))[0] for b in bucket_order]
        offset = (i - 0.5) * width
        bars = ax1.bar(x + offset, vals, width, color=color, label=label,
                       edgecolor="white", linewidth=0.6)
        for bar, v in zip(bars, vals):
            if np.isfinite(v):
                ax1.text(bar.get_x() + bar.get_width() / 2, v + 0.4,
                         f"{v:.0f}%", ha="center", va="bottom", fontsize=8, color="#333")
    ax1.axhline(50, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
    ax1.set_xticks(x)
    ax1.set_xticklabels(bucket_order, fontsize=9)
    ax1.set_ylabel("Home win %", fontsize=10)
    ax1.set_ylim(45, 80)
    ax1.set_title("Home win % by rest situation", fontsize=11, fontweight="bold",
                  color="#2c2c2a", pad=6)
    ax1.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    # ── Panel 2: altitude teams vs league ────────────────────────────────────
    team_order = ["League", "Denver Nuggets", "Utah Jazz"]
    labels2 = ["League avg", "Denver", "Utah"]
    x2 = np.arange(len(team_order))
    for i, (ctx, label, color) in enumerate(ctx_styles):
        alt = data["altitude"][ctx]
        vals = [alt.get(t, (np.nan, 0))[0] for t in team_order]
        offset = (i - 0.5) * width
        bars = ax2.bar(x2 + offset, vals, width, color=color, label=label,
                       edgecolor="white", linewidth=0.6)
        for bar, v in zip(bars, vals):
            if np.isfinite(v):
                ax2.text(bar.get_x() + bar.get_width() / 2, v + 0.4,
                         f"{v:.0f}%", ha="center", va="bottom", fontsize=8, color="#333")
    ax2.axhline(50, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
    ax2.set_xticks(x2)
    ax2.set_xticklabels(labels2, fontsize=9)
    ax2.set_ylabel("Home win %", fontsize=10)
    ax2.set_ylim(45, 80)
    ax2.set_title("Altitude teams vs. league (home win %)", fontsize=11,
                  fontweight="bold", color="#2c2c2a", pad=6)
    ax2.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    plt.tight_layout()
    output_path = _output_path("nba_home_court_rest_altitude.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


def plot_channel_3pa_control(data: dict) -> None:
    """
    Does each box-score channel's fade survive holding three-point volume
    constant? Per channel, the bar is the share of that channel's yearly decline
    trend that remains after controlling for the game's 3PA rate: 100% = the fade
    is unrelated to the three-point shift, 0% = it is fully the three-point story,
    below 0 = the trend reverses once threes are held constant. The regular-season
    panel is the clean test; the playoff panel is mostly small-sample noise (only
    rebounding stays significant), so non-significant bars are greyed.

    `data` comes from regression.compute_channel_3pa_control().
    """
    order = CATEGORY_ORDER
    ctxs = [("Regular season", GREEN), ("Playoffs", BLUE)]
    fig, axes = plt.subplots(1, 2, figsize=(15, 6), sharey=True)
    fig.suptitle("Does Each Category's Decline Survive Controlling for Threes?",
                 fontsize=14, fontweight="bold", y=1.0, color="#2c2c2a")
    fig.text(0.5, 0.95,
             "Share of each category's yearly decline left after holding 3-point volume constant  |  "
             "100% = unrelated to threes, 0% = fully the three-point story",
             ha="center", fontsize=9, color=GRAY)

    for ax, (ctx, color) in zip(axes, ctxs):
        blk = data.get(ctx)
        if not blk:
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                    transform=ax.transAxes, color=GRAY)
            continue
        rows = {r["chart_label"]: r for r in blk["channels"]}
        labels = [l for l in order if l in rows]
        x = np.arange(len(labels))
        vals = [rows[l]["surviving"] for l in labels]
        colors = [color if rows[l]["p_ctrl"] < 0.05 else GRAY for l in labels]
        bars = ax.bar(x, vals, color=colors, edgecolor="white", linewidth=0.6, width=0.62)
        ax.axhline(100, color=GRAY, linewidth=1.0, linestyle="--", zorder=1)
        ax.axhline(0, color="#444", linewidth=1.0, zorder=1)
        for bar, l in zip(bars, labels):
            v = rows[l]["surviving"]
            note = "" if rows[l]["p_ctrl"] < 0.05 else " n.s."
            ax.text(bar.get_x() + bar.get_width() / 2, v + (4 if v >= 0 else -4),
                    f"{v:.0f}%{note}", ha="center",
                    va="bottom" if v >= 0 else "top", fontsize=8, color="#333")
        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=9)
        ax.set_title(f"{ctx}  (n = {blk['n']:,} games)", fontsize=11,
                     fontweight="bold", color="#2c2c2a", pad=6)
        ax.set_ylim(-150, 180)

    axes[0].set_ylabel("Decline trend surviving the 3PA control (%)", fontsize=10)
    axes[0].text(-0.45, 104, "unrelated to threes", fontsize=7.5, color=GRAY, va="bottom")
    axes[0].text(-0.45, 4, "fully the three-point story", fontsize=7.5, color="#444", va="bottom")

    plt.tight_layout()
    output_path = _output_path("nba_home_court_3pa_control.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


def plot_mediation(decomp: dict) -> None:
    """
    Two-panel decomposition: each box-score channel's share of the home-court
    level (left) and of its 40-year decline (right), regular season vs playoffs.

    Renders the same numbers RESULTS.md prints — the dict comes from
    nba_home_court_analysis.compute_mediation_decomposition(). Bars are
    normalized to 100% (the shares sum to 100 by accounting identity); the
    headline at each bar's end is how much of the level/decline the four
    channels capture.
    """
    seg_order  = CATEGORY_ORDER
    seg_colors = CATEGORY_COLORS
    RESID = GRAY
    contexts = ["Regular season", "Playoffs"]
    y_pos = {"Regular season": 1.0, "Playoffs": 0.0}

    def shares(ctx_key: str, which: str):
        ctx  = decomp[ctx_key]
        rows = {r["chart_label"]: r["pct"] for r in ctx[which]}
        seq  = [(lbl, rows[lbl]) for lbl in seg_order]
        resid = "Unexplained" if which == "level" else "Unmediated"
        seq.append((resid, ctx[f"{which}_{'unexplained' if which == 'level' else 'unmediated'}"]["pct"]))
        return seq

    def draw_panel(ax, which: str, title: str, headline_key: str, verb: str):
        for ctx_key in contexts:
            y, left = y_pos[ctx_key], 0.0
            for lbl, pct in shares(ctx_key, which):
                color = RESID if lbl in ("Unexplained", "Unmediated") else seg_colors[lbl]
                ax.barh(y, pct, left=left, height=0.5, color=color,
                        edgecolor="white", linewidth=1.0, zorder=2)
                if pct >= 6:
                    ax.text(left + pct / 2, y, f"{pct:.0f}%", ha="center", va="center",
                            fontsize=9, color="white", fontweight="bold", zorder=3)
                left += pct
            ax.text(102, y, f"{decomp[ctx_key][headline_key]:.0f}% {verb}",
                    ha="left", va="center", fontsize=9.5, color="#2c2c2a", fontweight="bold")
        ax.set_yticks([y_pos[c] for c in contexts])
        ax.set_yticklabels(contexts, fontsize=10)
        ax.set_xlim(0, 118)
        ax.set_ylim(-0.6, 1.6)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
        ax.set_title(title, fontsize=11, fontweight="bold", color="#2c2c2a", pad=8)
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 5.5))
    fig.patch.set_facecolor(BG)
    fig.suptitle("Where Home Court Comes From — and Where It's Going",
                 fontsize=14, fontweight="bold", y=1.05, color="#2c2c2a")
    fig.text(0.5, 0.965,
             "Box-score category shares of the home-court edge (left) and of its 40-year decline (right)  |  "
             "shares sum to 100% by accounting identity",
             ha="center", fontsize=9, color=GRAY)

    draw_panel(ax1, "level", "What creates the home edge",   "pct_level", "explained")
    draw_panel(ax2, "trend", "What's driving the decline",   "pct_trend", "mediated")

    handles = [mpatches.Patch(color=seg_colors[l], label=l) for l in seg_order]
    handles.append(mpatches.Patch(color=RESID, label="Unexplained / unmediated"))
    fig.legend(handles=handles, fontsize=9, ncol=5, loc="lower center",
               framealpha=0.85, edgecolor="#ddd", bbox_to_anchor=(0.5, -0.04))

    plt.tight_layout(rect=(0, 0.05, 1, 0.95))
    output_path = _output_path("nba_home_court_mediation.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


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

    panels = DIFF_PANELS

    fig, axes = plt.subplots(2, 3, figsize=(22, 10))
    fig.suptitle("Home vs Away Box-Score Differentials — Are the Gaps Closing?",
                 fontsize=15, fontweight="bold", y=0.99, color="#2c2c2a")
    fig.text(0.5, 0.955,
             f"Data: NBA.com  |  Positive = home team higher  |  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    for ax, (key, title, ylabel, note) in zip(axes.flat, panels):
        y_reg = np.array(reg_stats[key], dtype=float)
        y_po  = _align_to_seasons(reg_seasons, po_seasons, po_stats, key)

        for y, color, label in [(y_reg, BLUE, "Regular season"), (y_po, GREEN, "Playoffs")]:
            ax.plot(x, y, color=color, linewidth=1.5, alpha=0.7, label=label, zorder=2)
            _add_trend_line(ax, x, y, color, linewidth=1.8, alpha=0.9, zorder=3)

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
    output_path = _output_path("nba_home_court_advantage_differentials.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


def plot_rebound_decomposition(
    reg_seasons: list[str], reg_stats: dict,
    po_seasons: list[str], po_stats: dict,
    win_seasons: list[str] | None = None,
    win_pcts: list[float] | None = None,
) -> None:
    """
    3-panel figure on why the home rebounding edge faded.

    Panel 1: home OREB rate vs away OREB rate over time (regular season) —
             the cleaner rate-based measure of offensive-rebounding aggressiveness,
             not confounded by how well either team shoots.
    Panel 2: raw OREB diff and DREB diff (home minus away per game) over time —
             shows both sides of the glass declining, with DREB declining more
             in absolute terms.
    Panel 3: total rebound differential vs home win % scatter — connects the
             full rebounding picture to HCA (association, not causation).
    """
    x = np.arange(len(reg_seasons))
    tick_step = max(1, len(reg_seasons) // 14)

    fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, figsize=(28, 7))
    fig.suptitle("Why the Home Rebounding and Turnover Edges Faded",
                 fontsize=15, fontweight="bold", y=1.0, color="#2c2c2a")
    fig.text(0.5, 0.955,
             f"Data: NBA.com  |  Regular season  |  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    # ── Panel 1: home vs away OREB rate over time ─────────────────────────────
    y_home = np.array(reg_stats["oreb_rate_home"], dtype=float)
    y_away = np.array(reg_stats["oreb_rate_away"], dtype=float)
    for y, color, label in [
        (y_home, BLUE, "Home OREB rate"),
        (y_away, RED,  "Away OREB rate"),
    ]:
        ax1.plot(x, y, color=color, linewidth=1.5, alpha=0.7, label=label, zorder=2)
        _add_trend_line(ax1, x, y, color, linewidth=1.8, alpha=0.9, zorder=3)
    _shade_eras(ax1, reg_seasons, label_y=None)
    ax1.set_xticks(x[::tick_step])
    ax1.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax1.set_ylabel("Offensive rebound rate (% of available)", fontsize=10)
    ax1.set_title("Both teams stopped crashing the glass,\nbut home teams fell further",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=8)
    ax1.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    # ── Panel 2: raw OREB diff and DREB diff over time ───────────────────────
    y_oreb_diff = np.array(reg_stats["oreb_diff"], dtype=float)
    y_dreb_diff = np.array(reg_stats["dreb_diff"], dtype=float)
    for y, color, label in [
        (y_oreb_diff, BLUE, "OREB diff (home − away)"),
        (y_dreb_diff, RED,  "DREB diff (home − away)"),
    ]:
        ax2.plot(x, y, color=color, linewidth=1.5, alpha=0.7, label=label, zorder=2)
        _add_trend_line(ax2, x, y, color, linewidth=1.8, alpha=0.9, zorder=3)
    _shade_eras(ax2, reg_seasons, label_y=None)
    ax2.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
    ax2.set_xticks(x[::tick_step])
    ax2.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax2.set_ylabel("Home minus away rebounds per game", fontsize=10)
    ax2.set_title("Both rebounding edges declined;\ndefensive edge fell more in raw counts",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=8)
    ax2.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    # ── Panel 3: total rebound differential vs home win % ────────────────────
    y_reb_diff = np.array(reg_stats["reb_diff"], dtype=float)
    if win_seasons is not None and win_pcts is not None:
        win_map = dict(zip(win_seasons, win_pcts))
        aligned_diff, aligned_win = [], []
        for s, d in zip(reg_seasons, y_reb_diff):
            if s in win_map and np.isfinite(d):
                aligned_diff.append(d)
                aligned_win.append(win_map[s])
        if len(aligned_diff) >= 2:
            xd = np.array(aligned_diff)
            yw = np.array(aligned_win)
            ax3.scatter(xd, yw, color=BLUE, s=30, alpha=0.75, zorder=2)
            z = np.polyfit(xd, yw, 1)
            xs = np.linspace(xd.min(), xd.max(), 50)
            ax3.plot(xs, np.poly1d(z)(xs), "--", color=RED, linewidth=1.8, alpha=0.9, zorder=3)
            r, p = pearsonr(xd, yw)
            ax3.text(0.05, 0.95, f"r = {r:+.2f}\np {'< 0.001' if p < 0.001 else f'= {p:.3f}'}",
                     transform=ax3.transAxes, va="top", fontsize=10, color="#2c2c2a",
                     bbox=dict(boxstyle="round", facecolor="white", alpha=0.8, edgecolor="#ddd"))
    ax3.set_xlabel("Total rebound differential (home − away per game)", fontsize=10)
    ax3.set_ylabel("Home win % (regular season)", fontsize=10)
    ax3.set_title("Seasons with a larger home rebounding edge\ntend to be seasons where home teams win more",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=8)

    # ── Panel 4: TOV differential over time ──────────────────────────────────
    # Plot away − home TOVs so positive = home advantage (home commits fewer)
    y_tov = -np.array(reg_stats.get("tov_diff", [np.nan] * len(reg_seasons)), dtype=float)
    ax4.plot(x, y_tov, color=BLUE, linewidth=1.5, alpha=0.7, zorder=2)
    _add_trend_line(ax4, x, y_tov, BLUE, linewidth=1.8, alpha=0.9, zorder=3)
    _shade_eras(ax4, reg_seasons, label_y=None)
    ax4.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
    ax4.set_xticks(x[::tick_step])
    ax4.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax4.set_ylabel("Away minus home turnovers per game", fontsize=10)
    ax4.set_title("Home turnover edge has eroded\n(positive = home commits fewer TOVs)",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=8)

    plt.tight_layout()
    output_path = _output_path("nba_home_court_rebounding.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


def plot_tracking_rebounding(seasons: list[str], stats: dict) -> None:
    """
    Player-tracking confirmation of the rebounding mechanism (tracking era only).

    One panel each for the home-minus-road edge in: offensive-rebound chance
    conversion, box-outs, and second-chance points. A short window (~2014 on;
    box-outs ~2016 on) — these corroborate the modern mechanism, not the full
    40-year decline.
    """
    x = np.arange(len(seasons))
    panels = TRACKING_PANELS

    fig, axes = plt.subplots(1, 3, figsize=(20, 6))
    fig.suptitle("Player-Tracking View of the Home Rebounding Edge (tracking era)",
                 fontsize=14, fontweight="bold", y=1.0, color="#2c2c2a")
    fig.text(0.5, 0.95,
             "Data: NBA.com player tracking & hustle stats  |  "
             "Positive = home team higher  |  short window — corroborates the modern mechanism",
             ha="center", fontsize=9, color=GRAY)

    for ax, (key, title, ylabel, note) in zip(axes, panels):
        y = np.array(stats[key], dtype=float)
        ax.plot(x, y, color=BLUE, linewidth=1.6, marker="o", markersize=4, alpha=0.8, zorder=2)
        _add_trend_line(ax, x, y, RED, linewidth=1.8, alpha=0.9, zorder=3)
        ax.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
        ax.set_xticks(x)
        ax.set_xticklabels(seasons, rotation=45, ha="right", fontsize=8)
        ax.set_title(title, fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.set_xlabel(note, fontsize=8, color=GRAY)

    plt.tight_layout()
    output_path = _output_path("nba_home_court_rebounding_tracking.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


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
             f"Data: NBA.com  |  Positive = home team winning by more  |  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    # Panel 1: all-game mean margin per season (reg + playoffs aligned)
    y_reg = np.array(reg_stats["all_games_mean"], dtype=float)
    y_po  = _align_to_seasons(reg_seasons, po_seasons, po_stats, "all_games_mean")

    for y, color, label in [(y_reg, BLUE, "Regular season"), (y_po, GREEN, "Playoffs")]:
        ax1.plot(x, y, color=color, linewidth=1.5, alpha=0.8, label=label, zorder=2)
        _add_trend_line(ax1, x, y, color, linewidth=1.8, alpha=0.9, zorder=3)

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
        ax2.plot(x, y, color=color, linewidth=1.5, alpha=0.8, label=label, zorder=2)
        _add_trend_line(ax2, x, y, color, linewidth=1.8, alpha=0.9, zorder=3)

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

    # bucket_stats_by_era returns 0 for eras with no underlying data (margin
    # data starts 1996–97, so the 1984–94 era is empty). Mask those to NaN so
    # no bar is drawn rather than a misleading ~0 bar.
    def _mask_empty_eras(seasons, values):
        out = []
        for _, y1, y2, _ in ERA_DEFS:
            has = any(y1 <= label_to_year(s) <= y2 and not np.isnan(v)
                      for s, v in zip(seasons, values))
            out.append(not has)
        return np.array(out)

    reg_vals = np.array(reg_era["reg"], dtype=float)
    po_vals  = np.array(po_era["po"],   dtype=float)
    reg_vals[_mask_empty_eras(reg_seasons, reg_stats["all_games_mean"])] = np.nan
    po_vals[_mask_empty_eras(po_seasons,  po_stats["all_games_mean"])]  = np.nan

    xi = np.arange(len(era_labels))
    w  = 0.35
    bars1 = ax3.bar(xi - w / 2, reg_vals, width=w, color=BLUE,  label="Regular season", zorder=2)
    bars2 = ax3.bar(xi + w / 2, po_vals,  width=w, color=GREEN, label="Playoffs",        zorder=2)
    for bars, color in [(bars1, BLUE), (bars2, GREEN)]:
        for bar in bars:
            h  = bar.get_height()
            if np.isnan(h):
                continue
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
    output_path = _output_path("nba_home_court_margin.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


def plot_back_to_back(data: dict) -> None:
    """
    Two-panel test of the 'load management' story. Left: the share of games in
    which the visitor is on a back-to-back has fallen sharply by era — the
    premise is true. Right: a shift-share split of the regular-season home win %
    decline shows only a small slice comes from that schedule change (fewer tired
    visitors); the rest is the home edge eroding within every rest situation
    alike. Scheduling nudged home court; it didn't drive it down.

    `data` comes from regression.compute_back_to_back_plotdata().
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Did Fewer Tired Visitors Drive the Decline?",
                 fontsize=14, fontweight="bold", y=1.0, color="#2c2c2a")
    fig.text(0.5, 0.95,
             f"Data: NBA.com  |  back-to-back = game on zero days' rest  |  regular season  |  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    # ── Panel 1: visitor B2B rate by era ─────────────────────────────────────
    eras, vis = data["eras"], data["vis_b2b"]
    x = np.arange(len(eras))
    bars = ax1.bar(x, vis, color=BLUE, width=0.66, edgecolor="white", linewidth=0.6)
    for b, v in zip(bars, vis):
        ax1.text(b.get_x() + b.get_width() / 2, v + 0.4, f"{v:.0f}%",
                 ha="center", va="bottom", fontsize=8, color="#333")
    ax1.set_xticks(x)
    ax1.set_xticklabels(eras, fontsize=8, rotation=30, ha="right")
    ax1.set_ylabel("Share of games with visitor on a back-to-back", fontsize=10)
    ax1.set_ylim(0, max(vis) * 1.18)
    ax1.set_title("The premise is true: tired visitors grew rarer", fontsize=10.5,
                  fontweight="bold", color="#2c2c2a", pad=6)

    # ── Panel 2: shift-share of the decline ──────────────────────────────────
    labels2 = ["Fewer tired\nvisitors\n(schedule)", "Home edge eroding\nin every rest\nsituation"]
    vals2 = [data["freq_comp"], data["rate_comp"]]
    # Fold the tiny interaction term into the win-rate share so the two parts
    # read as a clean 100% split (matches the FINDINGS "8% vs the other 92%").
    shares = [data["freq_share"], 100.0 - data["freq_share"]]
    x2 = np.arange(2)
    bars2 = ax2.bar(x2, vals2, color=[GRAY, RED], width=0.5, edgecolor="white", linewidth=0.6)
    ax2.axhline(0, color="#444", linewidth=1.0)
    for b, v, s in zip(bars2, vals2, shares):
        ax2.text(b.get_x() + b.get_width() / 2, v - 0.2,
                 f"{v:+.2f} pp\n({s:.0f}% of\nthe decline)", ha="center", va="top",
                 fontsize=8.5, color="#333")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(labels2, fontsize=9)
    ax2.set_ylabel("Contribution to the home win % decline (pp)", fontsize=10)
    ax2.set_ylim(min(vals2) * 1.25, 1.2)
    ax2.set_title(f"Schedule explains only {data['freq_share']:.0f}% of the {data['total']:+.1f} pp decline",
                  fontsize=10.5, fontweight="bold", color="#2c2c2a", pad=6)

    plt.tight_layout()
    output_path = _output_path("nba_home_court_back_to_back.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


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
    ax1r.plot(x, y_parity, color=RED, linewidth=2, label="Win% std dev", zorder=2, alpha=0.8)
    _add_trend_line(ax1r, x, y_parity, RED)
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
    output_path = _output_path("nba_home_court_parity.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


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
             f"Data: NBA.com  |  Playoffs {season_range_label()}  |  2020 bubble excluded  |  "
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
    output_path = _output_path("nba_home_court_series_breakdown.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


def plot_playoff_quality(data: dict) -> None:
    """
    Two-panel proof that the playoff decline is genuine home-court weakening, not
    weaker seeds. Left: the playoff home win % decline rate (pp/year) before and
    after removing the seed-quality gap — the two are nearly identical, so team
    quality explains essentially none of the decline. Right: home win % by who
    hosts — even the objectively weaker team wins when it hosts Games 3–4, a pure
    venue effect.

    `data` comes from regression.compute_playoff_quality_plotdata().
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("The Playoff Decline Is Real Home-Court Weakening, Not Weaker Seeds",
                 fontsize=14, fontweight="bold", y=1.0, color="#2c2c2a")
    fig.text(0.5, 0.95,
             f"Data: NBA.com  |  quality gap = home minus away regular-season win %  |  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    # ── Panel 1: decline rate, raw vs quality-adjusted ───────────────────────
    labels1 = ["Raw\n(year only)", "After removing\nteam-quality gap"]
    vals1 = [data["pp_raw"], data["pp_adj"]]
    x1 = np.arange(2)
    bars = ax1.bar(x1, vals1, color=[BLUE, GREEN], width=0.5, edgecolor="white", linewidth=0.6)
    ax1.axhline(0, color="#444", linewidth=1.0)
    for b, v in zip(bars, vals1):
        ax1.text(b.get_x() + b.get_width() / 2, v - 0.004,
                 f"{v:+.3f}", ha="center", va="top", fontsize=10, color="#333")
    ax1.set_xticks(x1)
    ax1.set_xticklabels(labels1, fontsize=9)
    ax1.set_ylabel("Playoff home win % decline (pp per year)", fontsize=10)
    ax1.set_ylim(min(vals1) - 0.07, 0.03)
    ax1.set_title(f"Decline rate barely moves — {data['retained']:.0f}% survives quality control",
                  fontsize=10.5, fontweight="bold", color="#2c2c2a", pad=6)

    # ── Panel 2: home win % by who hosts ─────────────────────────────────────
    labels2 = [b[0] for b in data["seed_bars"]]
    vals2   = [b[1] for b in data["seed_bars"]]
    ns      = [b[2] for b in data["seed_bars"]]
    x2 = np.arange(len(labels2))
    colors2 = [BLUE, BLUE, GREEN]
    bars2 = ax2.bar(x2, vals2, color=colors2, width=0.62, edgecolor="white", linewidth=0.6)
    ax2.axhline(50, color=GRAY, linewidth=1.0, linestyle=":")
    ax2.text(len(labels2) - 0.5, 50.3, "50% — coin flip", fontsize=7.5, color=GRAY, va="bottom", ha="right")
    for b, v, n in zip(bars2, vals2, ns):
        ax2.text(b.get_x() + b.get_width() / 2, v + 0.4,
                 f"{v:.1f}%\n(n={n:,})", ha="center", va="bottom", fontsize=8, color="#333")
    ax2.set_xticks(x2)
    ax2.set_xticklabels(labels2, fontsize=9)
    ax2.set_ylabel("Home win %", fontsize=10)
    ax2.set_ylim(45, 78)
    ax2.set_title("Even the weaker team wins when it hosts",
                  fontsize=10.5, fontweight="bold", color="#2c2c2a", pad=6)

    plt.tight_layout()
    output_path = _output_path("nba_home_court_playoff_quality.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


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
             f"Data: NBA.com  |  Positive = home team higher share of FGA  |  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    for ax, (zone, label) in zip(axes.flat, SHOT_ZONE_LABELS.items()):
        color = SHOT_ZONE_COLORS[zone]
        y_reg = np.array(reg_stats[zone], dtype=float)
        y_po  = _align_to_seasons(reg_seasons, po_seasons, po_stats, zone)

        for y, lcolor, llabel in [(y_reg, color, "Regular season"),
                                   (y_po, color, "Playoffs")]:
            ls = "-" if llabel == "Regular season" else "--"
            alpha = 0.9 if llabel == "Regular season" else 0.6
            ax.plot(x, y, color=lcolor, linewidth=2, linestyle=ls,
                    alpha=alpha, label=llabel, zorder=2)
            _add_trend_line(ax, x, y, lcolor, linestyle=":", linewidth=1.5,
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
    output_path = _output_path("nba_home_court_shot_zones.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


def _scatter_panel(
    ax: plt.Axes,
    seasons: list[str],
    x_vals: list[float],
    y_vals: list[float],
    title: str,
    xlabel: str,
    *,
    fmt_x: bool = False,
) -> None:
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
    ax.set_xlabel(xlabel, fontsize=10)
    ax.set_ylabel("Home win %", fontsize=10)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    if fmt_x:
        ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.set_title(title, fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)


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
             f"Data: NBA.com  |  3PA rate = share of all field-goal attempts that are 3-pointers  "
             f"|  {season_range_label()}",
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
    _scatter_panel(ax2, reg_seasons, list(y_tpa_reg), list(y_pct_reg),
                   "Regular season: 3PA rate vs. home win %\n(one point per season)",
                   "League 3PA rate (% of FGA)", fmt_x=True)
    _scatter_panel(ax3, po_seasons,  list(y_tpa_po),  list(y_pct_po),
                   "Playoffs: 3PA rate vs. home win %\n(one point per season)",
                   "League 3PA rate (% of FGA)", fmt_x=True)

    plt.tight_layout()
    output_path = _output_path("nba_home_court_3pa.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


def plot_pace_hca_analysis(
    reg_seasons: list[str], reg_pace: list[float], reg_pcts: list[float],
    po_seasons:  list[str], po_pace:  list[float], po_pcts:  list[float],
) -> None:
    """
    3-panel figure: does league-wide pace (possessions per 48 min) drive the
    decline in home court advantage?

    Panel 1: dual-axis time series — regular-season pace (right axis, purple)
             vs. home win % (left axis, blue), era-shaded.
    Panel 2: scatter regular season — x = pace, y = home win %, era-colored.
    Panel 3: scatter playoffs — same layout.
    """
    PURPLE = "#9467bd"

    x_reg = np.arange(len(reg_seasons))
    tick_step = max(1, len(reg_seasons) // 14)
    y_pace_reg = np.array(reg_pace, dtype=float)
    y_pct_reg  = np.array(reg_pcts, dtype=float)
    y_pace_po  = np.array(po_pace,  dtype=float)
    y_pct_po   = np.array(po_pcts,  dtype=float)

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(20, 6))
    fig.suptitle("Does League-Wide Pace Explain the Decline in Home Court Advantage?",
                 fontsize=14, fontweight="bold", y=1.03, color="#2c2c2a")
    fig.text(0.5, 0.965,
             f"Data: NBA.com  |  Pace = estimated possessions per 48 min per team  "
             f"|  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    # ── Panel 1: dual-axis time series (regular season) ─────────────────────
    _shade_eras(ax1, reg_seasons, label_y=None)
    ax1.plot(x_reg, y_pct_reg, color=BLUE, linewidth=2, label="Home win %", zorder=2)
    ax1.set_xticks(x_reg[::tick_step])
    ax1.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.set_ylabel("Home win %", color=BLUE, fontsize=10)
    ax1.tick_params(axis="y", labelcolor=BLUE)
    ax1.set_title("Regular-season pace vs. home win %\nover time",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)

    ax1r = ax1.twinx()
    ax1r.plot(x_reg, y_pace_reg, color=PURPLE, linewidth=2,
              label="Pace (poss/48 min)", zorder=2, alpha=0.85)
    ax1r.set_ylabel("Pace (possessions per 48 min)", color=PURPLE, fontsize=10)
    ax1r.tick_params(axis="y", labelcolor=PURPLE)

    lines1, labs1 = ax1.get_legend_handles_labels()
    lines2, labs2 = ax1r.get_legend_handles_labels()
    ax1.legend(lines1 + lines2, labs1 + labs2, fontsize=9, framealpha=0.85, edgecolor="#ddd")

    # ── Panels 2 & 3: scatter (one point per season) ─────────────────────────
    _scatter_panel(ax2, reg_seasons, list(y_pace_reg), list(y_pct_reg),
                   "Regular season: pace vs. home win %\n(one point per season)",
                   "Pace (possessions per 48 min)")
    _scatter_panel(ax3, po_seasons,  list(y_pace_po),  list(y_pct_po),
                   "Playoffs: pace vs. home win %\n(one point per season)",
                   "Pace (possessions per 48 min)")

    plt.tight_layout()
    output_path = _output_path("nba_home_court_pace.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


def plot_team_hca_analysis(
    reg_stats: dict,
    po_stats:  dict,
) -> None:
    """
    2-panel figure: which franchises have the biggest home court advantage?

    Panel 1: Horizontal bar chart of regular-season HCA by franchise, sorted
             largest to smallest.
    Panel 2: Scatter of regular-season HCA vs. playoff HCA per franchise,
             with a y=x diagonal reference line.
    """
    def _ci_hw(s: dict) -> float:
        """95% CI half-width (pp) for a franchise's HCA — binomial variance,
        same formula as the regression module's _shrink_hca."""
        ph, pr = s["home_pct"] / 100.0, s["road_pct"] / 100.0
        var = 1e4 * (ph * (1.0 - ph) / s["n_home"] + pr * (1.0 - pr) / s["n_road"])
        return 1.96 * float(np.sqrt(var))

    def _shrunken_hca(stats: dict) -> dict:
        """Empirical-Bayes shrinkage of each franchise's HCA toward the league
        mean — mirrors the regression module's _shrink_hca so the chart ranks
        franchises the way RESULTS.md does (Denver/Utah on top), instead of
        letting small-sample defunct franchises top the raw list."""
        teams = list(stats)
        hcas = np.array([stats[t]["hca"] for t in teams], dtype=float)
        league_mean = float(hcas.mean())
        samp_vars = np.array([
            1e4 * (
                (stats[t]["home_pct"] / 100.0) * (1.0 - stats[t]["home_pct"] / 100.0) / stats[t]["n_home"]
                + (stats[t]["road_pct"] / 100.0) * (1.0 - stats[t]["road_pct"] / 100.0) / stats[t]["n_road"]
            )
            for t in teams
        ])
        true_var = max(0.0, float(np.var(hcas, ddof=1)) - float(samp_vars.mean()))
        return {
            t: (true_var / (true_var + samp_vars[i]) if true_var > 0 else 0.0) * stats[t]["hca"]
               + (1.0 - (true_var / (true_var + samp_vars[i]) if true_var > 0 else 0.0)) * league_mean
            for i, t in enumerate(teams)
        }

    reg_shrunk   = _shrunken_hca(reg_stats)
    sorted_teams = sorted(reg_stats, key=lambda t: reg_shrunk[t], reverse=True)
    hcas   = [reg_shrunk[t] for t in sorted_teams]
    errs   = [_ci_hw(reg_stats[t]) for t in sorted_teams]
    colors = [GREEN if h >= 0 else RED for h in hcas]

    height = max(10, len(sorted_teams) * 0.33 + 2)
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(20, height),
        gridspec_kw={"width_ratios": [3, 2]},
    )
    fig.suptitle("Franchise Home Court Advantage — Regular Season vs. Playoffs (All-Time)",
                 fontsize=14, fontweight="bold", y=1.02, color="#2c2c2a")
    fig.text(
        0.5, 0.965,
        f"Data: NBA.com  |  HCA = home win% − road win%  |  {season_range_label()}  |"
        "  Historical franchises shown separately",
        ha="center", fontsize=9, color=GRAY,
    )

    # ── Panel 1: horizontal bar chart (regular season) ────────────────────────
    y = np.arange(len(sorted_teams))
    bars = ax1.barh(y, hcas, color=colors, edgecolor="white", linewidth=0.5, height=0.7,
                    xerr=errs, error_kw={"ecolor": "#888", "elinewidth": 0.8, "capsize": 2})
    ax1.axvline(0, color=GRAY, linewidth=1.0, zorder=1)
    ax1.set_yticks(y)
    ax1.set_yticklabels(sorted_teams, fontsize=8)
    ax1.invert_yaxis()
    ax1.xaxis.set_major_formatter(mticker.FormatStrFormatter("%+.0f pp"))
    ax1.set_xlabel("Home court advantage (home win% − road win%)", fontsize=10)
    ax1.set_title("Regular-season HCA by franchise (sample-size adjusted)",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    for bar, h in zip(bars, hcas):
        xoff = 0.25 if h >= 0 else -0.25
        ha   = "left" if h >= 0 else "right"
        ax1.text(h + xoff, bar.get_y() + bar.get_height() / 2,
                 f"{h:+.1f}", ha=ha, va="center", fontsize=7, color="#333")

    # ── Panel 2: reg vs. playoff HCA scatter ─────────────────────────────────
    common = sorted(set(reg_stats) & set(po_stats))
    if common:
        x_vals = [reg_stats[t]["hca"] for t in common]
        y_vals = [po_stats[t]["hca"]  for t in common]

        all_vals = x_vals + y_vals
        vmin, vmax = min(all_vals) - 3, max(all_vals) + 3
        ax2.plot([vmin, vmax], [vmin, vmax], ":", color=GRAY, linewidth=1.2, alpha=0.5,
                 label="y = x (equal HCA in both)")
        ax2.axhline(0, color=GRAY, linewidth=0.7, linestyle="--", alpha=0.4)
        ax2.axvline(0, color=GRAY, linewidth=0.7, linestyle="--", alpha=0.4)

        x_err = [_ci_hw(reg_stats[t]) for t in common]
        y_err = [_ci_hw(po_stats[t])  for t in common]
        ax2.errorbar(x_vals, y_vals, xerr=x_err, yerr=y_err, fmt="none",
                     ecolor="#bbb", elinewidth=0.7, capsize=0, zorder=2)
        ax2.scatter(x_vals, y_vals, color=BLUE, s=55, zorder=3,
                    edgecolors="white", linewidths=0.8)

        # label top/bottom 3 by regular-season HCA + any obvious outliers
        sorted_by_reg = sorted(common, key=lambda t: reg_shrunk[t], reverse=True)
        to_label = set(sorted_by_reg[:3]) | set(sorted_by_reg[-2:])
        for t in common:
            if t not in to_label:
                continue
            rv, pv = reg_stats[t]["hca"], po_stats[t]["hca"]
            short = t.replace("Portland Trail Blazers", "Portland")
            ax2.annotate(short, (rv, pv), fontsize=7, ha="center", va="bottom",
                         xytext=(0, 5), textcoords="offset points", color="#333")

        ax2.set_xlim(vmin, vmax)
        ax2.set_ylim(vmin, vmax)
        ax2.xaxis.set_major_formatter(mticker.FormatStrFormatter("%+.0f"))
        ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%+.0f"))
        ax2.set_xlabel("Regular-season HCA (pp)", fontsize=10)
        ax2.set_ylabel("Playoff HCA (pp)", fontsize=10)
        ax2.set_title("Regular-season vs. playoff HCA\n(one point per franchise)",
                      fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
        ax2.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")
    else:
        ax2.text(0.5, 0.5, "Insufficient playoff data",
                 ha="center", va="center", transform=ax2.transAxes,
                 fontsize=12, color=GRAY)

    plt.tight_layout()
    output_path = _output_path("nba_home_court_team_hca.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


def plot_team_hca_by_era(
    early_stats: dict,
    late_stats: dict,
    early_label: str = "1984–2001",
    late_label: str = "2002–24",
    min_games: int = 400,
) -> None:
    """
    Dumbbell chart: per-franchise HCA in the early era vs the recent era.
    Sorted by early-era HCA so teams that started highest appear at the top.
    Merges within-city name changes (Bullets→Wizards, LA/Los Angeles Clippers).
    Saves → nba_home_court_team_hca_era.png
    """
    _NAME_MAP = {
        "Washington Bullets": "Washington Wizards",
        "LA Clippers": "Los Angeles Clippers",
    }

    def _normalize(stats: dict) -> dict:
        raw: dict = {}
        for name, s in stats.items():
            key = _NAME_MAP.get(name, name)
            if key not in raw:
                raw[key] = {"hw": 0, "hn": 0, "rw": 0, "rn": 0}
            raw[key]["hw"] += round(s["home_pct"] * s["n_home"] / 100)
            raw[key]["hn"] += s["n_home"]
            raw[key]["rw"] += round(s["road_pct"] * s["n_road"] / 100)
            raw[key]["rn"] += s["n_road"]
        out = {}
        for name, c in raw.items():
            if not c["hn"] or not c["rn"]:
                continue
            h = 100.0 * c["hw"] / c["hn"]
            r = 100.0 * c["rw"] / c["rn"]
            out[name] = {"home_pct": h, "road_pct": r, "hca": h - r,
                         "n_home": c["hn"], "n_road": c["rn"]}
        return out

    early_n = _normalize(early_stats)
    late_n  = _normalize(late_stats)

    common = {
        t for t in set(early_n) & set(late_n)
        if early_n[t]["n_home"] >= min_games and late_n[t]["n_home"] >= min_games
    }
    sorted_teams = sorted(common, key=lambda t: early_n[t]["hca"], reverse=True)
    early_hcas = [early_n[t]["hca"] for t in sorted_teams]
    late_hcas  = [late_n[t]["hca"]  for t in sorted_teams]

    league_early = sum(early_hcas) / len(early_hcas)
    league_late  = sum(late_hcas)  / len(late_hcas)

    height = max(8, len(sorted_teams) * 0.42 + 2)
    fig, ax = plt.subplots(figsize=(12, height), facecolor=BG)
    ax.set_facecolor(BG)
    fig.suptitle(
        f"Franchise HCA: {early_label} vs. {late_label}",
        fontsize=14, fontweight="bold", color="#2c2c2a",
    )
    fig.text(
        0.5, 0.965,
        f"Data: NBA.com  |  HCA = home win% − road win%  |"
        f"  Franchises with ≥{min_games} home games in each era",
        ha="center", fontsize=9, color=GRAY,
    )

    y = np.arange(len(sorted_teams))
    for i, (eh, lh) in enumerate(zip(early_hcas, late_hcas)):
        ax.plot([eh, lh], [i, i], color=GRAY, linewidth=1.2, alpha=0.5, zorder=1)

    ax.scatter(early_hcas, y, color=BLUE, s=65, zorder=3,
               label=f"Early era ({early_label})", edgecolors="white", linewidths=0.8)
    ax.scatter(late_hcas, y, color=GREEN, s=65, zorder=3,
               label=f"Recent era ({late_label})", edgecolors="white", linewidths=0.8)

    ax.axvline(league_early, color=BLUE, linewidth=1.2, linestyle="--", alpha=0.45,
               label=f"League avg {early_label}: {league_early:.1f} pp")
    ax.axvline(league_late, color=GREEN, linewidth=1.2, linestyle="--", alpha=0.45,
               label=f"League avg {late_label}: {league_late:.1f} pp")

    ax.set_yticks(y)
    ax.set_yticklabels(sorted_teams, fontsize=9)
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%+.0f pp"))
    ax.set_xlabel("Home court advantage (home win% − road win%)", fontsize=11)
    ax.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd", loc="lower right")
    ax.grid(axis="x", alpha=0.3, linewidth=0.6)

    plt.tight_layout()
    out = _output_path("nba_home_court_team_hca_era.png")
    plt.savefig(out, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {out}")
    plt.close()


def plot_referee_era_distribution(bias_stats: list[dict]) -> None:
    """
    Single-panel: box plots of per-official era-mean foul_diff by era.
    Shows whether the distribution of referee biases has compressed over time.
    Saves → nba_home_court_referee_era.png
    """
    if not bias_stats:
        print("plot_referee_era_distribution: no bias stats, skipping.")
        return

    era_order = [e[0] for e in ERA_DEFS]
    era_data: dict[str, list[float]] = {e: [] for e in era_order}
    for o in bias_stats:
        for era, mean in o["era_means"].items():
            if era in era_data:
                era_data[era].append(mean)
    era_labels_present = [e for e in era_order if era_data[e]]
    box_data = [era_data[e] for e in era_labels_present]

    fig, ax = plt.subplots(figsize=(9, 3.5), facecolor=BG)
    ax.set_facecolor(PANEL)

    if box_data:
        bp = ax.boxplot(
            box_data,
            labels=era_labels_present,
            patch_artist=True,
            medianprops={"color": "#2c2c2a", "linewidth": 1.5},
            whiskerprops={"linewidth": 0.8},
            capprops={"linewidth": 0.8},
            flierprops={"marker": "o", "markersize": 4, "alpha": 0.5,
                        "markerfacecolor": GRAY},
        )
        for patch, era in zip(bp["boxes"], era_labels_present):
            idx = next(i for i, e in enumerate(era_order) if e == era)
            patch.set_facecolor(ERA_COLORS[idx % len(ERA_COLORS)])
            patch.set_alpha(0.55)

        ax.axhline(0, color=GRAY, linewidth=0.8, linestyle="--", alpha=0.6)
        ax.set_xlabel("Era", fontsize=10)
        ax.set_ylabel("Per-official era-mean foul diff (home − away)", fontsize=9)
        ax.set_title(
            "Distribution of per-official home foul bias by era\n(each point = one referee, playoffs)",
            fontsize=11, fontweight="bold", color="#2c2c2a", pad=6,
        )
        ax.tick_params(axis="x", labelsize=8)
    else:
        ax.text(0.5, 0.5, "Insufficient data for era breakdown",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=12, color=GRAY)

    plt.tight_layout()
    output_path = _output_path("nba_home_court_referee_era.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


def plot_referee_rankings(bias_stats: list[dict]) -> None:
    """
    Single-panel: top/bottom officials ranked by career mean home foul_diff.
    Saves → nba_home_court_referee_rankings.png
    """
    if not bias_stats:
        print("plot_referee_rankings: no bias stats, skipping.")
        return

    n_show = min(15, len(bias_stats) // 2)
    top    = list(reversed(bias_stats[-n_show:]))   # most home-favoring (most negative)
    bottom = bias_stats[:n_show]                     # least home-favoring (most positive)
    show   = bottom + top
    names  = [o["name"].split()[-1] for o in show]  # last name only for brevity
    vals   = [o["mean_foul_diff"] for o in show]
    bar_colors = [GREEN if v < 0 else RED for v in vals]

    fig, ax = plt.subplots(
        figsize=(8, min(7, max(5, n_show * 0.35 + 2))),
        facecolor=BG,
    )
    ax.set_facecolor(PANEL)

    y_pos = range(len(show))
    bars = ax.barh(list(y_pos), vals, color=bar_colors, edgecolor="white",
                   linewidth=0.5, height=0.7)
    ax.set_yticks(list(y_pos))
    ax.set_yticklabels(names, fontsize=8)
    ax.axvline(0, color=GRAY, linewidth=0.8, linestyle="--", alpha=0.6)
    ax.axhline(n_show - 0.5, color=GRAY, linewidth=0.6, linestyle=":", alpha=0.5)

    for bar, v in zip(bars, vals):
        xoff = -0.05 if v < 0 else 0.05
        ha   = "right" if v < 0 else "left"
        ax.text(v + xoff, bar.get_y() + bar.get_height() / 2,
                f"{v:+.2f}", ha=ha, va="center", fontsize=7, color="#333")

    ax.set_xlabel("Mean home − away fouls per game", fontsize=10)
    ax.set_title(
        f"Top/bottom {n_show} referees by home foul differential\n(≥50 playoff games, shrunken estimates)",
        fontsize=11, fontweight="bold", color="#2c2c2a", pad=6,
    )
    neg = mpatches.Patch(color=GREEN, label="Home-favoring (fewer home fouls)")
    pos = mpatches.Patch(color=RED,   label="Visitor-favoring (more home fouls)")
    ax.legend(handles=[neg, pos], fontsize=8, framealpha=0.85, edgecolor="#ddd")
    ax.invert_yaxis()

    plt.suptitle("Referee Home Foul Bias — Playoffs", fontsize=13,
                 fontweight="bold", color="#2c2c2a", y=1.01)
    plt.tight_layout()
    output_path = _output_path("nba_home_court_referee_rankings.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


def plot_attendance(
    att_seasons: list[str], att_avg: list[float],
    reg_seasons: list[str], reg_pcts: list[float],
    dose_df,
) -> None:
    """
    2-panel figure on the crowd as an ingredient of home court advantage.

    Panel 1: dual-axis time series — league average attendance per game
             (right axis) vs. regular-season home win % (left axis), ~2000–2025.
             Attendance sits near capacity and flat while HCA falls → crowd
             *size* is not behind the decline. COVID seasons marked in red.
    Panel 2: 2020-21 dose-response — home win % by attendance bucket, the
             accidental experiment in what the crowd alone is worth.
    """
    ORANGE = "#e8a33d"

    # Align attendance seasons to those with a home-win % value.
    pct_map = dict(zip(reg_seasons, reg_pcts))
    seasons = [s for s in att_seasons if s in pct_map]
    att = np.array([att_avg[att_seasons.index(s)] for s in seasons], dtype=float)
    pct = np.array([pct_map[s] for s in seasons], dtype=float)
    x = np.arange(len(seasons))
    tick_step = max(1, len(seasons) // 12)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("The Crowd and Home Court Advantage: Size vs. Presence",
                 fontsize=14, fontweight="bold", y=1.02, color="#2c2c2a")
    fig.text(0.5, 0.96,
             "Attendance: Basketball-Reference  |  Home win %: NBA.com  "
             "|  Dose-response: 2020–21, crowds limited by local rule",
             ha="center", fontsize=9, color=GRAY)

    # ── Panel 1: attendance vs. home win % over time ────────────────────────
    pt_colors = [RED if s in COVID_SEASONS else BLUE for s in seasons]
    ax1.plot(x, pct, color=BLUE, linewidth=2, zorder=2)
    ax1.scatter(x, pct, c=pt_colors, s=28, zorder=3)
    ax1.set_xticks(x[::tick_step])
    ax1.set_xticklabels(seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.set_ylabel("Regular-season home win %", color=BLUE, fontsize=10)
    ax1.tick_params(axis="y", labelcolor=BLUE)
    ax1.set_title("Crowd size held flat while home court advantage fell",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)

    ax1r = ax1.twinx()
    ax1r.plot(x, att / 1000.0, color=ORANGE, linewidth=2, zorder=2, alpha=0.9)
    ax1r.set_ylabel("Avg. attendance per game (thousands)", color=ORANGE, fontsize=10)
    ax1r.tick_params(axis="y", labelcolor=ORANGE)
    ax1r.set_ylim(0, max(att / 1000.0) * 1.15)
    ax1.legend(handles=[
        mpatches.Patch(color=BLUE,   label="Home win % (left)"),
        mpatches.Patch(color=ORANGE, label="Attendance (right)"),
        mpatches.Patch(color=RED,    label="COVID seasons"),
    ], fontsize=9, framealpha=0.85, edgecolor="#ddd", loc="lower left")

    # ── Panel 2: 2020-21 dose-response ──────────────────────────────────────
    edges  = [-1, 0, 2500, 5000, 10000, np.inf]
    labels = ["Empty\n(0)", "1–2.5k", "2.5–5k", "5–10k", "10k+"]
    win_pct, ns = [], []
    for lo, hi in zip(edges[:-1], edges[1:]):
        grp = dose_df[(dose_df["attendance"] > lo) & (dose_df["attendance"] <= hi)]
        win_pct.append(100 * grp["home_win"].mean() if len(grp) else np.nan)
        ns.append(len(grp))
    xb = np.arange(len(labels))
    bar_colors = [RED] + [BLUE] * (len(labels) - 1)
    bars = ax2.bar(xb, win_pct, color=bar_colors, width=0.7, zorder=2)
    ax2.axhline(50, color=GRAY, linestyle="--", linewidth=1, zorder=1)
    ax2.text(len(labels) - 0.5, 50.4, "coin flip", ha="right", va="bottom",
             fontsize=8, color=GRAY)
    for bar, wp, n in zip(bars, win_pct, ns):
        if not np.isnan(wp):
            ax2.text(bar.get_x() + bar.get_width() / 2, wp + 0.4,
                     f"{wp:.0f}%\nn={n:,}", ha="center", va="bottom",
                     fontsize=8, color="#2c2c2a")
    ax2.set_xticks(xb)
    ax2.set_xticklabels(labels, fontsize=9)
    ax2.set_xlabel("2020–21 game attendance", fontsize=10)
    ax2.set_ylabel("Home win %", fontsize=10)
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax2.set_ylim(0, max(w for w in win_pct if not np.isnan(w)) * 1.18)
    ax2.set_title("Empty arenas erased home court — fans restored it",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)

    plt.tight_layout()
    output_path = _output_path("nba_home_court_attendance.png")
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()
