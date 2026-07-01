"""
home_court_plots.py — visualization for NBA home court advantage analysis.

All plot_* functions that generate and save PNG charts. Data is provided
by home_court_data; this module adds only matplotlib rendering.
"""

import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from scipy.stats import pearsonr

from home_court_data import (
    ERA_DEFS, COVID_SEASONS,
    label_to_year, bucket_stats_by_era, _align_to_seasons, season_range_label,
)
from nbakit.viz import (
    BLUE, GREEN, RED, GRAY, BG, PANEL,
    save_chart,
    annotate_bars as _annotate_bars,
    add_trend_line as _add_trend_line,
)
from nbakit.stats import shrink_to_mean

# Charts are saved as SVG via nbakit.viz.save_chart (vector, sharp at any zoom,
# and embedded identically in the HTML and Typst/PDF builds).

# All generated charts are written here.
OUTPUT_DIR = "generated/images"


# ── Colors ────────────────────────────────────────────────────────────────────
# Base palette (BLUE/GREEN/RED/GRAY/BG/PANEL) comes from nbakit.viz.
# Color conventions (see questions/CLAUDE.md, "Chart design"), kept consistent so
# readers build cross-chart intuition:
#   - regular season = BLUE, playoffs = GREEN  (in any chart showing both)
#   - positive / home-favoring = GREEN, negative / visitor-favoring = RED
#   - the emphasized series (highlight-and-mute) = BLUE, muted context = grey
# One background shade per era (matches order of ERA_DEFS)
ERA_COLORS = ["#7c6fce", "#378add", "#1d9e75", "#e8a33d", "#c2538a", "#5a8f29"]

# Display metadata for shot zone analysis
SHOT_ZONE_LABELS: dict[str, str] = {
    "paint":    "Paint (RA + Non-RA)",
    "midrange": "Mid-Range",
    "corner3":  "Corner 3",
    "above3":   "Above Break 3",
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
    ("fta_diff",      "Free throw attempts (home FTA − away FTA)",
     "FTA per game",      "positive = home team took more free throws"),
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


def _annotate_event(ax: plt.Axes, seasons: list[str], end_year: int, label: str, *,
                    y_frac: float = 0.88) -> None:
    """Mark a rule-change year on a time-series axis with a dotted rule and label.

    Uses ax.get_xaxis_transform() so x is in data coordinates and y is in axes
    fraction — label stays inside the panel regardless of y-axis scale.
    """
    idx = next((i for i, s in enumerate(seasons) if label_to_year(s) == end_year), None)
    if idx is None:
        return
    ax.axvline(idx, color=GRAY, linestyle=":", linewidth=1.1, alpha=0.6, zorder=1)
    ax.text(idx, y_frac, label, ha="center", va="top", fontsize=7.5,
            color="#5a5a55", linespacing=1.15, zorder=4,
            transform=ax.get_xaxis_transform())


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

    # Name the two events behind the sharp drops, on the line itself. Each falls
    # on an era-shade boundary, so the label says what that boundary means.
    events = [(1995, 78.5, "top",    "1994–95:\nhand-checking crackdown"),
              (2018, 47.5, "bottom", "2017+:\nthree-point surge")]
    for end_year, y_lab, va, label in events:
        idx = next((i for i, s in enumerate(reg_seasons)
                    if label_to_year(s) == end_year), None)
        if idx is None:
            continue
        ax.axvline(idx, color=GRAY, linestyle=":", linewidth=1.1, alpha=0.6, zorder=1)
        ax.text(idx, y_lab, label, ha="center", va=va, fontsize=7.5,
                color="#5a5a55", linespacing=1.15, zorder=4)

    ax.set_title("Home win % fell about 10 points in 40 years, regular season and playoffs alike",
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
    ax.legend(handles=handles, fontsize=9, loc="lower left", framealpha=0.85, edgecolor="#ddd")

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
    def _save(name: str, draw_fn, figsize: tuple) -> None:
        fig_, ax_ = plt.subplots(1, 1, figsize=figsize)
        fig_.patch.set_facecolor(BG)
        draw_fn(ax_)
        plt.tight_layout()
        save_chart(name, OUTPUT_DIR)

    _save("home_court_advantage_season.svg",
          lambda ax: _draw_season_overview(ax, reg_seasons, reg_pcts, po_seasons, po_pcts),
          (14, 7))
    _save("home_court_advantage_format_bars.svg",
          lambda ax: _draw_paired_bars(ax, format_reg_avg, format_po_avg, format_labels_short,
                                       "Regular season vs playoffs\nhome win % by playoff format period"),
          (5, 3))


def plot_bayesian_changepoint(results: dict) -> None:
    """Two-panel Bayesian change-point chart.

    Left: season-level home win % with fitted lines for zero, one, two, and three
    breaks, labelled with each option's probability and best-fit break years.
    Right: for the one-break option, how likely each year is to be the break.

    Saves → home_court_bayesian_changepoint.svg
    """
    years    = np.array(results["years"])
    pct      = np.array(results["pct"])
    k_probs  = results["k_probs"]
    fit0     = np.array(results["k0_fit"])
    fit1_map = np.array(results["k1_map_fit"])
    map_yr1  = results["k1_map_year"]
    hpd      = results["k1_hpd"]
    tau_post = results["k1_post"]   # {year: prob}
    slopes   = results["k1_slopes"]

    fit2_map    = np.array(results["k2_map_fit"]) if results["k2_map_fit"] else None
    map_yrs2    = results.get("k2_map_years")
    fit3_map    = np.array(results["k3_map_fit"]) if results.get("k3_map_fit") else None
    map_yrs3    = results.get("k3_map_years")

    fig, (ax_l, ax_r) = plt.subplots(1, 2, figsize=(15, 6), facecolor=BG)
    fig.suptitle("The decline bends at least once, near the late 1990s, but the year can't be pinned down",
                 fontsize=13, fontweight="bold", color="#2c2c2a")
    fig.text(0.5, 0.965,
             "Regular season  |  how many times the pace of decline changed, and when",
             ha="center", fontsize=9, color=GRAY)

    # ── Left panel: time series + model fits ─────────────────────────────────
    ax_l.set_facecolor(PANEL)
    x_idx = np.arange(len(years))

    ax_l.scatter(x_idx, pct, color="#aab4bb", s=28, zorder=3, label="Season home win %")
    ax_l.plot(x_idx, fit0, color=GRAY, linewidth=1.5, linestyle="--", alpha=0.7,
              label=f"No break  ({k_probs[0]:.0%})")
    ax_l.plot(x_idx, fit1_map, color=BLUE, linewidth=2.2, zorder=4,
              label=f"One break  ({k_probs[1]:.0%}, ~{map_yr1})")
    if fit2_map is not None and map_yrs2 is not None:
        ax_l.plot(x_idx, fit2_map, color=RED, linewidth=1.8, linestyle="-.",
                  alpha=0.85, zorder=4,
                  label=f"Two breaks  ({k_probs[2]:.0%}, {map_yrs2[0]}/{map_yrs2[1]})")
    if fit3_map is not None and map_yrs3 is not None:
        ax_l.plot(x_idx, fit3_map, color="#2a9d2a", linewidth=1.8, linestyle=":",
                  alpha=0.85, zorder=4,
                  label=f"Three breaks  ({k_probs[3]:.0%}, {map_yrs3[0]}/{map_yrs3[1]}/{map_yrs3[2]})")

    # Mark MAP break year
    break_x = int(np.where(years == map_yr1)[0][0])
    ax_l.axvline(break_x, color=BLUE, linewidth=1.0, linestyle=":", alpha=0.6)

    # Annotate slopes
    sl_txt = (f"Pre-break:  {slopes['pre_mean']:+.2f} pp/yr\n"
              f"Post-break: {slopes['post_mean']:+.2f} pp/yr")
    ax_l.text(0.02, 0.05, sl_txt, transform=ax_l.transAxes, fontsize=8.5,
              color=BLUE, verticalalignment="bottom",
              bbox=dict(boxstyle="round,pad=0.3", facecolor="white", alpha=0.75, edgecolor="#ccc"))

    tick_step = max(1, len(years) // 12)
    ax_l.set_xticks(x_idx[::tick_step])
    ax_l.set_xticklabels(years[::tick_step], rotation=45, ha="right", fontsize=8)
    ax_l.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax_l.set_ylabel("Home win %", fontsize=10)
    ax_l.set_title("Home win % with a fitted line for each number of breaks",
                   fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    ax_l.legend(fontsize=8.5, framealpha=0.88, edgecolor="#ddd", loc="upper right")
    ax_l.grid(axis="y", alpha=0.35, linewidth=0.6)

    # ── Right panel: posterior over break year (k=1) ─────────────────────────
    ax_r.set_facecolor(PANEL)
    sorted_years = sorted(tau_post)
    probs = [tau_post[yr] for yr in sorted_years]
    x_r   = np.arange(len(sorted_years))

    # Color bars: HPD inside = BLUE, outside = light grey
    bar_colors = [BLUE if hpd[0] <= yr <= hpd[1] else "#c0c8cc" for yr in sorted_years]
    ax_r.bar(x_r, probs, color=bar_colors, edgecolor="none", width=0.85)

    map_r_idx = sorted_years.index(map_yr1)
    ax_r.axvline(map_r_idx, color="#1a1a1a", linewidth=1.4, linestyle="--", alpha=0.75,
                 label=f"Most likely: {map_yr1}")
    ax_r.text(map_r_idx + 0.3, max(probs) * 0.92, f"Most likely\n{map_yr1}",
              fontsize=8, color="#1a1a1a")

    hpd_patch = mpatches.Patch(color=BLUE, label=f"Likely range: {hpd[0]}–{hpd[1]}")
    grey_patch = mpatches.Patch(color="#c0c8cc", label="Less likely")
    ax_r.legend(handles=[hpd_patch, grey_patch], fontsize=8.5, framealpha=0.88,
                edgecolor="#ddd")

    tick_step_r = max(1, len(sorted_years) // 10)
    ax_r.set_xticks(x_r[::tick_step_r])
    ax_r.set_xticklabels(sorted_years[::tick_step_r], rotation=45, ha="right", fontsize=8)
    ax_r.yaxis.set_major_formatter(mticker.PercentFormatter(xmax=1, decimals=0))
    ax_r.set_ylabel("Chance it's the break year", fontsize=10)
    ax_r.set_title("If the decline has one break, where it most likely falls",
                   fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    ax_r.grid(axis="y", alpha=0.35, linewidth=0.6)

    plt.tight_layout()
    save_chart("home_court_bayesian_changepoint.svg", OUTPUT_DIR)


def plot_rest_altitude(data: dict) -> None:
    """
    Two-panel view of the two situational edges from Section 2: rest and
    altitude. Left: home win % by rest situation (away more rested / equal /
    home more rested), regular season vs playoffs. Right: home win % for the
    two high-altitude franchises (Denver, Utah) against the league baseline,
    regular season vs playoffs — the altitude edge is real in the regular
    season and largely gone in the playoffs.

    `data` comes from regression.compute_rest_altitude_plotdata(); same
    numbers home_court_results.md prints, no new data.
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("Rest and altitude help home teams, but neither changed enough to drive the decline",
                 fontsize=14, fontweight="bold", y=1.0, color="#2c2c2a")
    fig.text(0.5, 0.95,
             f"Data: NBA.com  |  home win % by situation  |  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    ctx_styles = [("reg", "Regular season", BLUE), ("po", "Playoffs", GREEN)]

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
    save_chart("home_court_rest_altitude.svg", OUTPUT_DIR)


def plot_channel_3pa_control(data: dict) -> None:
    """
    Does each box-score channel's contribution to the home-court decline survive
    holding three-point volume constant? Each channel's per-year slope is scaled
    to win-percentage-points per decade (the mediation chart's currency) so the
    four channels share one axis. Per channel a dumbbell runs from the raw decline
    contribution (open marker) to the contribution after the 3PA control (filled):
    a filled dot pulled to the zero line means the three-point shift fully accounts
    for that channel's decline; one that stays put is an independent driver. The
    regular-season panel is the clean test; the playoff panel is mostly small-
    sample noise (only rebounding stays significant), so non-significant rows are
    greyed.

    `data` comes from regression.compute_channel_3pa_control().
    """
    order = list(reversed(CATEGORY_ORDER))   # Shooting at the top
    ctxs = [("Regular season", BLUE), ("Playoffs", GREEN)]
    fig, axes = plt.subplots(1, 2, figsize=(15, 5.6), sharex=True, sharey=True)
    fig.suptitle("The move to threes explains shooting's decline, but not rebounding's",
                 fontsize=14, fontweight="bold", y=1.0, color="#2c2c2a")
    fig.text(0.5, 0.95,
             "Each category's share of the decline (win % per decade), before (○) and after (●) "
             "games are compared at the same number of threes  |  a dot pulled to zero, or past it, "
             "means the move to threes explains that category's drop; a dot that stays out dropped on its own",
             ha="center", fontsize=9, color=GRAY)

    for ax, (ctx, color) in zip(axes, ctxs):
        blk = data.get(ctx)
        if not blk:
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                    transform=ax.transAxes, color=GRAY)
            continue
        rows = {r["chart_label"]: r for r in blk["channels"]}
        labels = [l for l in order if l in rows]
        ys = np.arange(len(labels))
        ax.axvline(0, color="#444", linewidth=1.1, zorder=1)
        for yi, l in zip(ys, labels):
            r = rows[l]
            sig = r["p_ctrl"] < 0.05
            after_c = color if sig else GRAY
            ax.plot([r["win_raw"], r["win_ctrl"]], [yi, yi], color="#c9c7c0",
                    linewidth=2.5, solid_capstyle="round", zorder=2)
            ax.scatter(r["win_raw"], yi, s=72, facecolors="white",
                       edgecolors=GRAY, linewidths=1.6, zorder=3)
            ax.scatter(r["win_ctrl"], yi, s=72, color=after_c, zorder=4)
            note = "" if sig else " n.s."
            right = r["win_ctrl"] >= r["win_raw"]
            ax.text(r["win_ctrl"] + (0.04 if right else -0.04), yi + 0.24,
                    f"{r['win_ctrl']:+.2f}{note}", ha="left" if right else "right",
                    va="bottom", fontsize=8, color="#333")
        ax.set_yticks(ys)
        ax.set_yticklabels(labels, fontsize=10)
        ax.set_title(f"{ctx}  (n = {blk['n']:,} games)", fontsize=11,
                     fontweight="bold", color="#2c2c2a", pad=6)
        ax.set_ylim(-0.6, len(labels) - 0.4)
        ax.set_xlabel("Contribution to the home-court decline (win % per decade)", fontsize=10)
        for spine in ("top", "right", "left"):
            ax.spines[spine].set_visible(False)

    axes[0].annotate("threes fully\naccount for it", xy=(0, len(order) - 1),
                     xytext=(0.05, len(order) - 0.62), fontsize=7.5, color=GRAY, va="center")
    handles = [
        plt.Line2D([0], [0], marker="o", linestyle="none", markerfacecolor="white",
                   markeredgecolor=GRAY, markersize=9, label="Before control"),
        plt.Line2D([0], [0], marker="o", linestyle="none", markerfacecolor=GRAY,
                   markeredgecolor=GRAY, markersize=9, label="After holding threes constant"),
    ]
    axes[0].legend(handles=handles, loc="lower left", fontsize=8.5,
                   framealpha=0.85, edgecolor="#ddd")

    plt.tight_layout()
    save_chart("home_court_3pa_control.svg", OUTPUT_DIR)


def plot_mediation(decomp: dict, boot: dict | None = None) -> None:
    """
    Two-panel decomposition: each box-score channel's share of the home-court
    level (left) and of its 40-year decline (right), regular season vs playoffs.

    Renders the same numbers home_court_results.md prints; the dict comes from
    home_court_analysis.compute_mediation_decomposition(). Bars are
    normalized to 100%; the headline at each bar's end is how much of the
    level/decline the four channels capture.
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
            head = f"{decomp[ctx_key][headline_key]:.0f}% {verb}"
            if boot and ctx_key in boot:
                lo, hi = boot[ctx_key][f"{headline_key}_ci"]
                head += f"\n95% CI {lo:.0f}–{hi:.0f}%"
            ax.text(102, y, head, ha="left", va="center", fontsize=9.5,
                    color="#2c2c2a", fontweight="bold")
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
    fig.suptitle("Four box-score factors explain about 95% of home court, and most of its decline",
                 fontsize=14, fontweight="bold", y=1.05, color="#2c2c2a")
    fig.text(0.5, 0.965,
             "Box-score category shares of the home-court edge (left) and of its 40-year decline (right)",
             ha="center", fontsize=9, color=GRAY)

    draw_panel(ax1, "level", "What creates the home edge",   "pct_level", "explained")
    draw_panel(ax2, "trend", "What's driving the decline",   "pct_trend", "mediated")

    handles = [mpatches.Patch(color=seg_colors[l], label=l) for l in seg_order]
    handles.append(mpatches.Patch(color=RESID, label="Unexplained / unmediated"))
    fig.legend(handles=handles, fontsize=9, ncol=5, loc="lower center",
               framealpha=0.85, edgecolor="#ddd", bbox_to_anchor=(0.5, -0.04))

    plt.tight_layout(rect=(0, 0.05, 1, 0.95))
    save_chart("home_court_mediation.svg", OUTPUT_DIR)

    # Individual panels for use in separate sections.
    for which, title, headline_key, verb, suffix, resid_label in [
        ("level", "What creates the home edge",  "pct_level", "explained", "level",   "Unexplained"),
        ("trend", "What's driving the decline",  "pct_trend", "mediated",  "decline", "Unmediated"),
    ]:
        fig_s, ax_s = plt.subplots(1, 1, figsize=(8, 5.5))
        fig_s.patch.set_facecolor(BG)
        draw_panel(ax_s, which, title, headline_key, verb)
        h = [mpatches.Patch(color=seg_colors[l], label=l) for l in seg_order]
        h.append(mpatches.Patch(color=RESID, label=resid_label))
        fig_s.legend(handles=h, fontsize=9, ncol=3, loc="lower center",
                     framealpha=0.85, edgecolor="#ddd", bbox_to_anchor=(0.5, -0.04))
        plt.tight_layout(rect=(0, 0.08, 1, 1))
        save_chart(f"home_court_mediation_{suffix}.svg", OUTPUT_DIR)


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
    fig.suptitle("The home foul and shooting edges are shrinking toward zero",
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

        ax.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
        ax.set_xticks(x[::tick_step])
        ax.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
        ax.set_title(title, fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
        ax.set_ylabel(ylabel, fontsize=10)
        ax.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")
        if note:
            ax.set_xlabel(note, fontsize=8, color=GRAY)
        if key == "fta_diff":
            _annotate_event(ax, reg_seasons, 1995, "1994–95:\nhand-checking\ncrackdown")

    plt.tight_layout()
    save_chart("home_court_advantage_differentials.svg", OUTPUT_DIR)


def plot_fta_distribution(
    season_label: str, season_vals: np.ndarray,
    era_labels: tuple[str, str],
    reg_early: np.ndarray, reg_late: np.ndarray,
    po_early: np.ndarray, po_late: np.ndarray,
) -> None:
    """
    Two panels showing the per-game FTA differential (home minus away) is
    noisy game to game even though its average is a real, shrinking edge.

    Panel 1: histogram of one season's per-game values — shows the average
    sitting deep inside ordinary game-to-game spread.
    Panel 2: box plots (whiskers = 10th/90th percentile) for regular season
    and playoffs, earliest era vs. latest — the average edge slides toward
    zero while the box width barely narrows.
    Saves -> home_court_fta_distribution.svg
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(13, 5), facecolor=BG)
    for ax in (ax1, ax2):
        ax.set_facecolor(PANEL)
    fig.suptitle("A ~2-attempt average edge sits inside a much wider nightly swing",
                 fontsize=14, fontweight="bold", y=1.0, color="#2c2c2a")
    fig.text(0.5, 0.945,
             "Data: NBA.com  |  Home minus away free-throw attempts per game  |  positive = home team more",
             ha="center", fontsize=9, color=GRAY)

    # ── Panel 1: one season's histogram ───────────────────────────────────
    mean_val = float(np.mean(season_vals))
    lo, hi = int(np.min(season_vals)), int(np.max(season_vals))
    ax1.hist(season_vals, bins=np.arange(lo - 0.5, hi + 1.5, 1),
             color=BLUE, alpha=0.75, edgecolor="white", linewidth=0.4)
    ax1.axvline(0, color=GRAY, linewidth=1, linestyle=":")
    ax1.axvline(mean_val, color=RED, linewidth=2, zorder=3)
    ax1.text(mean_val, ax1.get_ylim()[1] * 0.94, f"  season average {mean_val:+.1f}",
             color=RED, fontsize=9, fontweight="bold", ha="left" if mean_val >= 0 else "right")
    ax1.set_title("One season looks like noise, not a pattern",
                   fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    ax1.set_xlabel(f"{season_label} regular season, one point per game", fontsize=8, color=GRAY)
    ax1.set_ylabel("Number of games", fontsize=10)

    # ── Panel 2: box plots by context and era ─────────────────────────────
    groups = [reg_early, reg_late, po_early, po_late]
    positions = [1, 2, 3.5, 4.5]
    colors = [BLUE, BLUE, GREEN, GREEN]
    alphas = [0.35, 0.85, 0.35, 0.85]
    bp = ax2.boxplot(
        groups, positions=positions, widths=0.7, whis=(10, 90), showfliers=False,
        patch_artist=True, showmeans=True,
        medianprops={"color": "#2c2c2a", "linewidth": 1.5},
        whiskerprops={"linewidth": 0.9}, capprops={"linewidth": 0.9},
        meanprops={"marker": "D", "markerfacecolor": "white",
                   "markeredgecolor": "#2c2c2a", "markersize": 6, "zorder": 4},
    )
    for patch, color, alpha in zip(bp["boxes"], colors, alphas):
        patch.set_facecolor(color)
        patch.set_alpha(alpha)
    ax2.axhline(0, color=GRAY, linewidth=0.8, linestyle="--", alpha=0.7)
    ax2.set_xticks(positions)
    ax2.set_xticklabels([f"RS\n{era_labels[0]}", f"RS\n{era_labels[1]}",
                          f"PO\n{era_labels[0]}", f"PO\n{era_labels[1]}"], fontsize=9)
    ax2.set_title("The average slides to zero; the swing barely narrows",
                   fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    ax2.set_ylabel("Home minus away FTA per game", fontsize=10)
    ax2.set_xlabel("Diamond = average; box = 25th-75th percentile; whiskers = 10th-90th (typical range)",
                    fontsize=8, color=GRAY)

    plt.tight_layout()
    save_chart("home_court_fta_distribution.svg", OUTPUT_DIR)


def plot_rebound_decomposition(
    reg_seasons: list[str], reg_stats: dict,
    po_seasons: list[str], po_stats: dict,
    win_seasons: list[str] | None = None,
    win_pcts: list[float] | None = None,
) -> None:
    """
    3-panel figure on why the home rebounding edge faded.

    Panel 1: home vs away OREB rate (left axis, solid) and DREB rate (right axis,
             dotted) over time — DREB rate = 100 − opponent OREB rate by identity.
             Symmetric y-limits so convergence reads the same on both axes.
    Panel 2: raw OREB diff and DREB diff (home minus away per game) over time —
             shows both sides of the glass declining, with DREB declining more
             in absolute terms.
    Panel 3: total rebound differential vs home win % scatter — connects the
             full rebounding picture to HCA (association, not causation).
    """
    x = np.arange(len(reg_seasons))
    tick_step = max(1, len(reg_seasons) // 14)

    fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, figsize=(28, 7))
    fig.suptitle("The home rebounding edge died on the offensive glass",
                 fontsize=15, fontweight="bold", y=1.0, color="#2c2c2a")
    fig.text(0.5, 0.955,
             f"Data: NBA.com  |  Regular season  |  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    # ── Panel 1: home vs away OREB rate over time ────────────────────────────────
    y_home = np.array(reg_stats["oreb_rate_home"], dtype=float)
    y_away = np.array(reg_stats["oreb_rate_away"], dtype=float)
    for y, color, label in [
        (y_home, BLUE, "Home OREB rate"),
        (y_away, RED,  "Away OREB rate"),
    ]:
        ax1.plot(x, y, color=color, linewidth=1.5, alpha=0.7, label=label, zorder=2)
        _add_trend_line(ax1, x, y, color, linewidth=1.8, alpha=0.9, zorder=3)
    ax1.set_xticks(x[::tick_step])
    ax1.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax1.set_ylabel("Offensive rebound rate (% of available)", fontsize=10)
    ax1.set_ylim(17, 37)
    ax1.set_title("Home offensive-rebound edge converged\nand crossed below away",
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
    ax4.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
    ax4.set_xticks(x[::tick_step])
    ax4.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax4.set_ylabel("Away minus home turnovers per game", fontsize=10)
    ax4.set_title("Home turnover edge has faded\n(positive = home commits fewer TOVs)",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=8)

    plt.tight_layout()
    save_chart("home_court_rebounding.svg", OUTPUT_DIR)


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
    fig.suptitle("By the tracking era, the home rebounding edge was already nearly gone",
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
    save_chart("home_court_rebounding_tracking.svg", OUTPUT_DIR)


def plot_margin_analysis(
    reg_seasons: list[str], reg_stats: dict,
    po_seasons: list[str], po_stats: dict,
    reg_nr_seasons: list[str] | None = None, reg_nr_stats: dict | None = None,
    po_nr_seasons: list[str] | None = None, po_nr_stats: dict | None = None,
) -> None:
    """
    2-panel chart (1×2).

    Panel 1: mean all-game margin per season (reg + playoffs, left axis) with
             net rating overlaid on a right axis (dashed, when data available).
    Panel 2: win-only vs loss-only margin per season (regular season).
    """
    has_nr = reg_nr_seasons is not None and reg_nr_stats is not None

    x = np.arange(len(reg_seasons))
    tick_step = max(1, len(reg_seasons) // 14)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))

    fig.suptitle("Home games are polarizing: bigger home wins and bigger home losses",
                 fontsize=15, fontweight="bold", y=1.03, color="#2c2c2a")
    fig.text(0.5, 0.965,
             f"Data: NBA.com  |  Positive = home team winning by more  |  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    # Panel 1: mean all-game margin (left axis) + net rating (right axis, dashed)
    y_reg = np.array(reg_stats["all_games_mean"], dtype=float)
    y_po  = _align_to_seasons(reg_seasons, po_seasons, po_stats, "all_games_mean")

    for y, color, label in [(y_reg, BLUE, "Reg season (pts)"), (y_po, GREEN, "Playoffs (pts)")]:
        ax1.plot(x, y, color=color, linewidth=1.5, alpha=0.8, label=label, zorder=2)
        _add_trend_line(ax1, x, y, color, linewidth=1.8, alpha=0.9, zorder=3)

    ax1.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
    ax1.set_xticks(x[::tick_step])
    ax1.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax1.set_title("Mean margin per season (all games)",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    ax1.set_ylabel("Home point margin (pts)", fontsize=10)

    if has_nr:
        # Align net rating values to the reg_seasons x-axis (NaN where unavailable)
        season_to_idx = {s: i for i, s in enumerate(reg_seasons)}
        nr_reg = np.full(len(reg_seasons), np.nan)
        nr_po  = np.full(len(reg_seasons), np.nan)
        for i, s in enumerate(reg_nr_seasons):
            if s in season_to_idx:
                nr_reg[season_to_idx[s]] = reg_nr_stats["net_rating_mean"][i]
        if po_nr_seasons is not None:
            for i, s in enumerate(po_nr_seasons):
                if s in season_to_idx:
                    nr_po[season_to_idx[s]] = po_nr_stats["net_rating_mean"][i]

        ax1r = ax1.twinx()
        for y, color, label in [
            (nr_reg, BLUE,  "Reg season (net rtg)"),
            (nr_po,  GREEN, "Playoffs (net rtg)"),
        ]:
            mask = ~np.isnan(y)
            xm = x[mask]
            ax1r.plot(xm, y[mask], color=color, linewidth=1.5, alpha=0.5,
                      linestyle="--", label=label, zorder=2)
            _add_trend_line(ax1r, xm, y[mask], color, linewidth=1.8, alpha=0.6,
                            linestyle="--", zorder=3)

        ax1r.set_ylabel("Home net rating (pts/100 poss)", fontsize=10)
        ax1r.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)

        # Combine legends from both axes
        h1, l1 = ax1.get_legend_handles_labels()
        h2, l2 = ax1r.get_legend_handles_labels()
        ax1.legend(h1 + h2, l1 + l2, fontsize=8, framealpha=0.85, edgecolor="#ddd")
    else:
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

    ax2.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
    ax2.set_xticks(x[::tick_step])
    ax2.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax2.set_title("Win/loss margin by season (regular season)",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    ax2.set_ylabel("Home point margin (pts)", fontsize=10)
    ax2.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    plt.tight_layout()
    save_chart("home_court_margin.svg", OUTPUT_DIR)


def plot_back_to_back(data: dict) -> None:
    """
    Two-panel test of the 'load management' story. Left: the share of games in
    which the visitor is on a back-to-back has fallen sharply by era — the
    premise is true. Right: a shift-share split of the regular-season home win %
    decline shows only a small slice comes from that schedule change (fewer tired
    visitors); the rest is the home edge fading within every rest situation
    alike. Scheduling nudged home court; it didn't drive it down.

    `data` comes from regression.compute_back_to_back_plotdata().
    """
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    fig.suptitle("Fewer back-to-backs explain only about 8% of the decline",
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
    labels2 = ["Fewer tired\nvisitors\n(schedule)", "Home edge fading\nin every rest\nsituation"]
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
    save_chart("home_court_back_to_back.svg", OUTPUT_DIR)


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
    fig.suptitle("Competitive balance does not track the home-court decline",
                 fontsize=14, fontweight="bold", y=1.03, color="#2c2c2a")
    fig.text(0.5, 0.965,
             "Data: NBA.com  |  Regular season  |  Parity = std dev of team win % per season  "
             "(lower = more equal league)",
             ha="center", fontsize=9, color=GRAY)

    # Panel 1: dual-axis time series
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
    save_chart("home_court_parity.svg", OUTPUT_DIR)


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
    fig.suptitle("Playoff results follow the arena, not series momentum",
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
    save_chart("home_court_series_breakdown.svg", OUTPUT_DIR)


def plot_series_simulation(data: dict) -> None:
    """
    Two panels showing that a best-of-7 absorbs most of home court, and most of
    its decline.

    Left: the transfer curve. A single-game home edge (x) maps to a much smaller
    series edge (y); the gap to the dashed 1:1 line is the compression. Era dots
    sit on the curve, drifting down toward the 50% coin flip over time.
    Right: the series-level home edge by era for the regular season and the
    playoffs, with the per-game edge shown muted for contrast.
    """
    eras   = data["era_labels"]
    n_sims = data["n_sims"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle("A best-of-7 absorbs most of home court — and most of its decline",
                 fontsize=14, fontweight="bold", y=1.02, color="#2c2c2a")
    fig.text(0.5, 0.955,
             f"Monte Carlo: {n_sims:,} simulated 2-2-1-1-1 series between two equal teams  |  "
             f"home win % per game from NBA.com, {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    # ── Panel 1: the transfer curve ──────────────────────────────────────────
    cx = data["curve_pgame"]
    cy = data["curve_series"]
    ax1.plot(cx, cx, color=GRAY, linewidth=1.2, linestyle="--", alpha=0.7,
             label="If it transferred 1:1")
    ax1.plot(cx, cy, color="#2c2c2a", linewidth=2.4, label="Best-of-7 series")
    ax1.axhline(50, color=GRAY, linewidth=1.0, linestyle=":", alpha=0.7)

    # Era dots on the curve: regular season (blue) and playoffs (green).
    for pgame, series, color in (
        (data["reg_pgame"], data["reg_series"], BLUE),
        (data["po_pgame"],  data["po_series"],  GREEN),
    ):
        xs = [p for p in pgame if p is not None]
        ys = [s for s in series if s is not None]
        ax1.scatter(xs, ys, s=34, color=color, zorder=4,
                    edgecolor="white", linewidth=0.8)

    # Annotate the drift for the regular-season points (cleaner venue measure).
    reg_pts = [(p, s, e) for p, s, e in
               zip(data["reg_pgame"], data["reg_series"], eras) if p is not None]
    if reg_pts:
        for idx, lbl in ((0, "oldest era"), (-1, "newest era")):
            px, py, era = reg_pts[idx]
            ax1.annotate(f"{era}\n({px:.0f}% → {py:.0f}%)", (px, py),
                         textcoords="offset points", xytext=(8, -14 if idx else 6),
                         fontsize=7.5, color=BLUE)
    ax1.set_xlabel("Home win % in a single game", fontsize=10)
    ax1.set_ylabel("Home-court team's series win %", fontsize=10)
    ax1.set_xlim(50, 70)
    ax1.set_ylim(48, 72)
    ax1.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.set_title("A per-game edge shrinks to a much smaller series edge",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    ax1.legend(fontsize=8.5, framealpha=0.85, edgecolor="#ddd", loc="upper left")

    # ── Panel 2: series edge by era, regular season vs playoffs ───────────────
    x = np.arange(len(eras))

    def _line(vals, color, label, **kw):
        xs = [i for i, v in zip(x, vals) if v is not None]
        ys = [v for v in vals if v is not None]
        ax2.plot(xs, ys, color=color, label=label, **kw)

    # Per-game edge muted for context; series edge emphasized.
    _line(data["reg_pgame"], "#b9c6d6", "Reg. season, per game",
          linewidth=1.6, linestyle="--", marker="o", markersize=4)
    _line(data["po_pgame"],  "#bcd6c4", "Playoffs, per game",
          linewidth=1.6, linestyle="--", marker="o", markersize=4)
    _line(data["reg_series"], BLUE, "Reg. season, series",
          linewidth=2.4, marker="o", markersize=6, markeredgecolor="white", markeredgewidth=0.8)
    _line(data["po_series"],  GREEN, "Playoffs, series",
          linewidth=2.4, marker="o", markersize=6, markeredgecolor="white", markeredgewidth=0.8)

    ax2.axhline(50, color=GRAY, linewidth=1.0, linestyle=":", alpha=0.8)
    ax2.text(len(eras) - 0.5, 50.4, "50% — coin flip", fontsize=7.5,
             color=GRAY, va="bottom", ha="right")
    ax2.set_xticks(x)
    ax2.set_xticklabels(eras, fontsize=8.5, rotation=20, ha="right")
    ax2.set_ylim(48, 72)
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax2.set_ylabel("Home win %", fontsize=10)
    ax2.set_title("At the series level, today's home court is barely a coin flip",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    ax2.legend(fontsize=8, framealpha=0.85, edgecolor="#ddd", ncol=2)

    plt.tight_layout()
    save_chart("home_court_series_simulation.svg", OUTPUT_DIR)


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
    save_chart("home_court_playoff_quality.svg", OUTPUT_DIR)


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
    fig.suptitle("Away teams have closed the home team's paint-shot edge",
                 fontsize=14, fontweight="bold", y=0.99, color="#2c2c2a")
    fig.text(0.5, 0.955,
             f"Data: NBA.com  |  Positive = home team higher share of FGA  |  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    # Highlight-and-mute: the finding is the paint panel, so color it and grey
    # the other three zones (they are context for the one that carries the title).
    for ax, (zone, label) in zip(axes.flat, SHOT_ZONE_LABELS.items()):
        is_focus = zone == "paint"
        color = BLUE if is_focus else "#c4c2bb"
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

        ax.axhline(0, color=GRAY, linewidth=0.8, linestyle=":", zorder=1)
        ax.set_title(f"{label} % differential (home − road)",
                     fontsize=11, fontweight="bold",
                     color="#2c2c2a" if is_focus else GRAY, pad=6)
        ax.set_ylabel("Percentage points", fontsize=10)
        ax.set_xticks(x[::tick_step])
        ax.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
        ax.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")

    plt.tight_layout()
    save_chart("home_court_shot_zones.svg", OUTPUT_DIR)


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
    fig.suptitle("Games with more threes go against home teams, even within the same era",
                 fontsize=14, fontweight="bold", y=1.03, color="#2c2c2a")
    fig.text(0.5, 0.965,
             f"Data: NBA.com  |  3PA rate = share of all field-goal attempts that are 3-pointers  "
             f"|  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    # ── Panel 1: dual-axis time series (regular season) ─────────────────────
    ax1.plot(x_reg, y_pct_reg, color=BLUE, linewidth=2, label="Home win %", zorder=2)
    ax1.set_xticks(x_reg[::tick_step])
    ax1.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=8)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.set_ylabel("Home win %", color=BLUE, fontsize=10)
    ax1.tick_params(axis="y", labelcolor=BLUE)
    ax1.set_title("Regular-season 3PA rate vs. home win %\nover time",
                  fontsize=11, fontweight="bold", color="#2c2c2a", pad=6)
    _annotate_event(ax1, reg_seasons, 2018, "2017+:\nthree-point\nsurge")

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
    save_chart("home_court_3pa.svg", OUTPUT_DIR)


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
    fig.suptitle("Pace of play does not explain the home-court decline",
                 fontsize=14, fontweight="bold", y=1.03, color="#2c2c2a")
    fig.text(0.5, 0.965,
             f"Data: NBA.com  |  Pace = estimated possessions per 48 min per team  "
             f"|  {season_range_label()}",
             ha="center", fontsize=9, color=GRAY)

    # ── Panel 1: dual-axis time series (regular season) ─────────────────────
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
    save_chart("home_court_pace.svg", OUTPUT_DIR)


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
        franchises the way home_court_results.md does (Denver/Utah on top), instead of
        letting small-sample defunct franchises top the raw list."""
        teams = list(stats)
        hcas = np.array([stats[t]["hca"] for t in teams], dtype=float)
        samp_vars = np.array([
            1e4 * (
                (stats[t]["home_pct"] / 100.0) * (1.0 - stats[t]["home_pct"] / 100.0) / stats[t]["n_home"]
                + (stats[t]["road_pct"] / 100.0) * (1.0 - stats[t]["road_pct"] / 100.0) / stats[t]["n_road"]
            )
            for t in teams
        ])
        shrunk, _ = shrink_to_mean(hcas, samp_vars)
        return {t: float(shrunk[i]) for i, t in enumerate(teams)}

    reg_shrunk   = _shrunken_hca(reg_stats)
    sorted_teams = sorted(reg_stats, key=lambda t: reg_shrunk[t], reverse=True)
    hcas   = [reg_shrunk[t] for t in sorted_teams]
    errs   = [_ci_hw(reg_stats[t]) for t in sorted_teams]
    # Highlight-and-mute: the headline is the top two, so color Denver/Utah and
    # mute the rest of the pack to neutral grey (bar lengths still show the spread).
    HIGHLIGHT = {"Denver Nuggets", "Utah Jazz"}
    colors = [BLUE if t in HIGHLIGHT else "#cdcbc4" for t in sorted_teams]

    height = max(10, len(sorted_teams) * 0.33 + 2)
    fig, (ax1, ax2) = plt.subplots(
        1, 2, figsize=(20, height),
        gridspec_kw={"width_ratios": [3, 2]},
    )
    fig.suptitle("Denver and Utah hold the biggest home-court edge (altitude, most likely)",
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
    for lbl, t in zip(ax1.get_yticklabels(), sorted_teams):
        if t in HIGHLIGHT:
            lbl.set_fontweight("bold")
            lbl.set_color("#2c2c2a")
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
    save_chart("home_court_team_hca.svg", OUTPUT_DIR)


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
    Saves → home_court_team_hca_era.svg
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
        f"Home court advantage shrank for most franchises: {early_label} vs. {late_label}",
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
    save_chart("home_court_team_hca_era.svg", OUTPUT_DIR)


def plot_team_season_hca(stats: dict, end_year: int) -> None:
    """
    Single-season snapshot: each team's home vs. road win% for one season,
    as a dumbbell (road dot, home dot, connecting bar), sorted by home win%.
    A "find your team" engagement chart, not an estimate — one season of ~41
    home games per team is noisy, so the figure reads the spread as a snapshot.
    Saves → home_court_team_season_hca.svg
    """
    season = f"{end_year - 1}-{str(end_year)[2:]}"
    teams = sorted(stats, key=lambda t: stats[t]["home_pct"])  # bottom-to-top
    home = np.array([stats[t]["home_pct"] for t in teams])
    road = np.array([stats[t]["road_pct"] for t in teams])
    y = np.arange(len(teams))
    n_pos = int(sum(1 for t in teams if stats[t]["hca"] > 0))

    avg_home = float(home.mean())
    avg_road = float(road.mean())

    fig, ax = plt.subplots(figsize=(11, max(8, len(teams) * 0.33 + 2)))
    fig.suptitle(
        f"In {season}, {n_pos} of {len(teams)} teams won more at home than on the road",
        fontsize=13, fontweight="bold", y=0.99, color="#2c2c2a",
    )
    fig.text(
        0.5, 0.945,
        f"Data: NBA.com  |  one dot per team for home and road win%, "
        f"sorted by home win%  |  {season} regular season (~41 home games each)",
        ha="center", fontsize=9, color=GRAY,
    )

    # Connecting bar per team; red marks a team that did NOT hold home court.
    for yi, h, r in zip(y, home, road):
        seg = RED if h < r else "#cdcbc4"
        ax.plot([r, h], [yi, yi], color=seg, linewidth=2.4, zorder=2,
                solid_capstyle="round")
    ax.scatter(road, y, color=GRAY, s=42, zorder=3, label="Road win%",
               edgecolors="white", linewidths=0.8)
    ax.scatter(home, y, color=BLUE, s=46, zorder=3, label="Home win%",
               edgecolors="white", linewidths=0.8)

    ax.axvline(avg_home, color=BLUE, linestyle="--", linewidth=1.1, alpha=0.5, zorder=1)
    ax.axvline(avg_road, color=GRAY, linestyle="--", linewidth=1.1, alpha=0.5, zorder=1)
    ax.text(avg_home + 0.5, len(teams) - 0.4, f"avg home {avg_home:.0f}%",
            ha="left", va="bottom", fontsize=7.5, color=BLUE)
    ax.text(avg_road - 0.5, len(teams) - 0.4, f"avg road {avg_road:.0f}%",
            ha="right", va="bottom", fontsize=7.5, color=GRAY)

    ax.set_yticks(y)
    ax.set_yticklabels(teams, fontsize=8)
    ax.set_ylim(-0.7, len(teams) - 0.1)
    ax.set_xlabel("Win %", fontsize=10)
    ax.xaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
    ax.grid(axis="x", alpha=0.3, linewidth=0.6)
    ax.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd", loc="upper left")

    plt.tight_layout(rect=(0, 0, 1, 0.94))
    save_chart("home_court_team_season_hca.svg", OUTPUT_DIR)


def plot_referee_era_distribution(bias_stats: list[dict]) -> None:
    """
    Single-panel: box plots of per-official era-mean foul_diff by era.
    Shows whether the distribution of referee biases has compressed over time.
    Saves → home_court_referee_era.svg
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
            "Referee home-foul bias has shrunk and grown more uniform over time\n(each point = one referee, playoffs)",
            fontsize=11, fontweight="bold", color="#2c2c2a", pad=6,
        )
        ax.tick_params(axis="x", labelsize=8)
    else:
        ax.text(0.5, 0.5, "Insufficient data for era breakdown",
                ha="center", va="center", transform=ax.transAxes,
                fontsize=12, color=GRAY)

    plt.tight_layout()
    save_chart("home_court_referee_era.svg", OUTPUT_DIR)


def plot_referee_rankings(bias_stats: list[dict]) -> None:
    """
    Single-panel: top/bottom officials ranked by career mean home foul_diff.
    Saves → home_court_referee_rankings.svg
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

    plt.suptitle("Nearly every playoff referee favors the home team, but the spread is mostly noise", fontsize=13,
                 fontweight="bold", color="#2c2c2a", y=1.01)
    plt.tight_layout()
    save_chart("home_court_referee_rankings.svg", OUTPUT_DIR)


def plot_team_decline_slopes(data: dict) -> None:
    """
    Caterpillar plot: each franchise's regular-season HCA-gap year-slope with its
    95% CI, sorted, against the league-wide slope. Shows that every team's CI
    overlaps the league line — the decline is league-wide, the spread is noise.
    Saves → home_court_team_decline_slopes.svg
    """
    teams = data.get("teams", [])
    if not teams:
        print("plot_team_decline_slopes: no data, skipping.")
        return

    names  = [r["team"] for r in teams]
    slopes = np.array([r["slope"] for r in teams])
    cis    = np.array([1.96 * r["se"] for r in teams])
    league = data["league_slope"]
    y      = np.arange(len(teams))
    # A franchise "stands out" only if its 95% CI excludes the league slope.
    stands_out = np.abs(slopes - league) > cis

    fig, ax = plt.subplots(figsize=(8.5, max(7, len(teams) * 0.26 + 2)), facecolor=BG)
    ax.set_facecolor(PANEL)

    ax.axvline(league, color=BLUE, linestyle="--", linewidth=1.4, zorder=2,
               label=f"League-wide slope ({league:+.2f} pp/yr)")
    ax.axvline(0, color=GRAY, linestyle=":", linewidth=1.0, alpha=0.7, zorder=1)
    ax.text(0, len(teams) - 0.5, "no change", fontsize=7.5, color=GRAY,
            ha="center", va="top")

    dot_colors = [RED if s else GRAY for s in stands_out]
    ax.errorbar(slopes, y, xerr=cis, fmt="none", ecolor="#cdcbc4",
                elinewidth=1.2, capsize=2, zorder=3)
    ax.scatter(slopes, y, c=dot_colors, s=40, zorder=4,
               edgecolors="white", linewidths=0.7)

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=7.5)
    ax.set_ylim(-0.7, len(teams) - 0.3)
    ax.set_xlabel("Change in home-court advantage per year (percentage points;"
                  " negative = declining)", fontsize=10)
    ax.grid(axis="x", alpha=0.3, linewidth=0.6)
    ax.legend(fontsize=8.5, framealpha=0.85, edgecolor="#ddd", loc="lower left")
    ax.set_title(
        f"Each franchise fit separately; bars are 95% CIs  |  "
        f"{int(stands_out.sum())} of {len(teams)} clear the league line  |  "
        f"true between-team SD ≈ {data['true_sd']:.2f} pp/yr  |  active franchises only",
        fontsize=9, color=GRAY, pad=4,
    )

    fig.suptitle(
        "Every franchise's home-court advantage has declined at the same league-wide rate",
        fontsize=13, fontweight="bold", color="#2c2c2a", y=1.005,
    )
    plt.tight_layout(rect=(0, 0, 1, 0.97))
    save_chart("home_court_team_decline_slopes.svg", OUTPUT_DIR)


def plot_oos_forecast(data: dict) -> None:
    """
    Two panels (regular season, playoffs): actual home win % across all seasons,
    with the channel-model forecast and the trend extrapolation drawn over the
    held-out test window. A frozen early model that tracks the held-out decline
    means the box-score mechanism isn't fitted to hindsight.
    Saves → home_court_oos_forecast.svg
    """
    panels = [("reg", "Regular season", BLUE), ("po", "Playoffs", GREEN)]
    if not any(data.get(k) for k, *_ in panels):
        print("plot_oos_forecast: no data, skipping.")
        return

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), facecolor=BG)

    for ax, (key, title, actual_c) in zip(axes, panels):
        d = data.get(key) or {}
        ax.set_facecolor(PANEL)
        if not d:
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=11, color=GRAY)
            ax.set_title(title, fontsize=11, color="#2c2c2a")
            continue

        full_years = [y for y, _ in d["actual_full"]]
        full_pcts  = [p for _, p in d["actual_full"]]
        ax.plot(full_years, full_pcts, color=actual_c, linewidth=1.8,
                marker="o", markersize=3, zorder=3, label="Actual")

        test_years = [r[0] for r in d["rows"]]
        pred_ch    = [r[2] for r in d["rows"]]
        pred_tr    = [r[3] for r in d["rows"]]
        ax.plot(test_years, pred_ch, color="#c2538a", linewidth=2.0,
                marker="s", markersize=3.5, zorder=4,
                label=f"Channel forecast (RMSE {d['rmse_channel']:.1f})")
        ax.plot(test_years, pred_tr, color=GRAY, linewidth=1.4, linestyle="--",
                zorder=2, label=f"Trend extrapolation (RMSE {d['rmse_trend']:.1f})")

        cut = d["cut_year"]
        ax.axvline(cut - 0.5, color="#2c2c2a", linewidth=1.0, linestyle=":",
                   alpha=0.6, zorder=1)
        ax.text(cut - 0.5, ax.get_ylim()[1], "  trained ←  → held out",
                ha="center", va="bottom", fontsize=7.5, color="#2c2c2a")

        ax.set_title(title, fontsize=11, fontweight="bold", color="#2c2c2a")
        ax.set_xlabel("Season ending", fontsize=9)
        ax.set_ylabel("Home win %", fontsize=9)
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
        ax.grid(alpha=0.3, linewidth=0.6)
        ax.legend(fontsize=7.8, framealpha=0.85, edgecolor="#ddd", loc="lower left")

    fig.suptitle(
        "The box-score channels, frozen on early seasons, forecast the later decline",
        fontsize=13, fontweight="bold", color="#2c2c2a", y=1.0,
    )
    fig.text(
        0.5, 0.93,
        "Win model trained only on pre-2014 games, then used to predict each "
        "later season from its box-score edges  |  the mechanism isn't fitted to hindsight",
        ha="center", fontsize=8.5, color=GRAY,
    )
    plt.tight_layout(rect=(0, 0, 1, 0.9))
    save_chart("home_court_oos_forecast.svg", OUTPUT_DIR)


def plot_mediation_sensitivity(data: dict) -> None:
    """
    How robust each box-score channel's link to home winning is to a hidden,
    unmeasured cause (Cinelli & Hazlett robustness value), regular season and
    playoffs. Each bar is the share of the residual variation a confounder would
    have to explain in BOTH that channel and home_win to zero out its
    coefficient: taller = harder to explain away. Channel colors match the
    mediation chart. Mirrors home_court_results.md.
    Saves → home_court_mediation_sensitivity.svg
    """
    if not data or all(k not in data for k in ("Regular season", "Playoffs")):
        print("plot_mediation_sensitivity: no data, skipping.")
        return

    labels = [lbl for _, lbl in data["channels"]]
    contexts = [("Regular season", "RS"), ("Playoffs", "PO")]
    avail = [(ctx, short) for ctx, short in contexts if data.get(ctx)]

    y = np.arange(len(labels))
    h = 0.38
    fig, ax = plt.subplots(figsize=(9, 4.6), facecolor=BG)
    ax.set_facecolor(PANEL)

    for off, (ctx, short) in zip((h / 2, -h / 2), avail):
        rv = {r["label"]: r["robustness_value"] for r in data[ctx]["channels"]}
        vals = [rv[lbl] for lbl in labels]
        bars = ax.barh(
            y + off, vals, height=h,
            color=[CATEGORY_COLORS[lbl] for lbl in labels],
            edgecolor="white", linewidth=0.6,
            alpha=1.0 if short == "RS" else 0.55, zorder=2,
        )
        for bar, v in zip(bars, vals):
            ax.text(bar.get_width() + 0.7, bar.get_y() + bar.get_height() / 2,
                    f"{v:.0f}%  {short}", va="center", ha="left",
                    fontsize=7.6, color="#2c2c2a")

    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=9)
    ax.invert_yaxis()
    ax.set_xlabel("Robustness value: share a hidden cause must explain in both the "
                  "channel and home wins (%)", fontsize=8.5)
    ax.set_xlim(0, max(70, ax.get_xlim()[1]))
    ax.grid(axis="x", alpha=0.3, linewidth=0.6)

    ax.annotate(
        "higher = harder to explain away",
        xy=(0.99, 0.04), xycoords="axes fraction", ha="right", va="bottom",
        fontsize=8, color=GRAY, style="italic",
    )

    fig.suptitle(
        "It would take a strong hidden cause to explain away the box-score links",
        fontsize=12.5, fontweight="bold", color="#2c2c2a", y=0.99,
    )
    fig.text(
        0.5, 0.9,
        "Cinelli & Hazlett robustness value per channel  |  solid = regular "
        "season, faded = playoffs  |  taller bars resist an unmeasured confounder",
        ha="center", fontsize=8.3, color=GRAY,
    )
    plt.tight_layout(rect=(0, 0, 1, 0.88))
    save_chart("home_court_mediation_sensitivity.svg", OUTPUT_DIR)


def plot_shap_channels(data: dict) -> None:
    """
    Non-parametric channel decomposition (gradient boosting + SHAP), regular
    season and playoffs. Per era, the signed SHAP contribution of each box-score
    channel, stacked, summing to that era's gap from the overall home win rate.
    The tall early-era stack collapses toward zero in the recent eras: that
    shrinking stack is the home-court decline, split by channel with no
    straight-line assumption. Mirrors home_court_results.md.
    Saves → home_court_shap_channels.svg
    """
    panels = [("Regular season", BLUE), ("Playoffs", GREEN)]
    if not data or not any(data.get(k) for k, _ in panels):
        print("plot_shap_channels: no data, skipping.")
        return

    # channels: list[(key, label)] — colors from the shared category palette.
    labels = [lbl for _, lbl in data["channels"]]
    fig, axes = plt.subplots(1, 2, figsize=(14, 5.2), facecolor=BG)

    for ax, (ctx_key, _c) in zip(axes, panels):
        d = data.get(ctx_key)
        ax.set_facecolor(PANEL)
        if not d:
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=11, color=GRAY)
            ax.set_title(ctx_key, fontsize=11, color="#2c2c2a")
            continue

        eras = d["eras"]
        x = np.arange(len(eras))
        contrib = {e: d["era_contrib_pp"][e] for e in eras}
        for i, lbl in enumerate(labels):
            vals = np.array([contrib[e][i] for e in eras])
            # Stack positives upward and negatives downward from zero separately.
            pos_base = np.zeros(len(eras))
            neg_base = np.zeros(len(eras))
            for j in range(len(eras)):
                v = vals[j]
                if v >= 0:
                    base, pos_base[j] = pos_base[j], pos_base[j] + v
                else:
                    neg_base[j] += v
                    base = neg_base[j]
                ax.bar(x[j], v, bottom=base, width=0.7,
                       color=CATEGORY_COLORS[lbl], edgecolor="white", linewidth=0.6,
                       zorder=2, label=lbl if j == 0 else None)

        # Era totals (= gap from overall home win rate) as a marker line.
        totals = np.array([sum(contrib[e]) for e in eras])
        ax.plot(x, totals, color="#2c2c2a", marker="o", markersize=4,
                linewidth=1.2, zorder=4, label="Era total")
        ax.axhline(0, color=GRAY, linewidth=0.9, zorder=1)

        ax.set_xticks(x)
        ax.set_xticklabels(eras, rotation=45, ha="right", fontsize=8)
        ax.set_ylabel("Contribution to home edge (pp vs. league mean)", fontsize=9)
        ax.set_title(ctx_key, fontsize=11, fontweight="bold", color="#2c2c2a")
        ax.grid(axis="y", alpha=0.3, linewidth=0.6)
        if ctx_key == "Regular season":
            handles, lab = ax.get_legend_handles_labels()
            seen: dict = {}
            for h, l in zip(handles, lab):
                seen.setdefault(l, h)
            ax.legend(seen.values(), seen.keys(), fontsize=7.8,
                      framealpha=0.85, edgecolor="#ddd", loc="upper right")

    fig.suptitle(
        "A model with no straight-line assumption splits the decline across the same channels",
        fontsize=13, fontweight="bold", color="#2c2c2a", y=1.0,
    )
    fig.text(
        0.5, 0.93,
        "Gradient-boosted win model + SHAP  |  each era's stacked channel "
        "contributions sum to its gap from the overall home win rate  |  the "
        "shrinking stack is the decline",
        ha="center", fontsize=8.5, color=GRAY,
    )
    plt.tight_layout(rect=(0, 0, 1, 0.9))
    save_chart("home_court_shap_channels.svg", OUTPUT_DIR)


def plot_hca_forecast(data: dict) -> None:
    """
    Two panels (regular season blue, playoffs green): the season-by-season home
    win %, its smoothed underlying trend, and a multi-season forecast with shaded
    80% and 95% prediction bands — the fan that widens with the horizon. The
    central line keeps sliding while the fan shows how much it could still move.
    Saves → home_court_hca_forecast.svg
    """
    panels = [("Regular season", BLUE), ("Playoffs", GREEN)]
    if not data or not any(data.get(k) for k, _ in panels):
        print("plot_hca_forecast: no data, skipping.")
        return

    fig, axes = plt.subplots(1, 2, figsize=(13, 4.8), facecolor=BG)

    for ax, (label, color) in zip(axes, panels):
        d = data.get(label)
        ax.set_facecolor(PANEL)
        if not d:
            ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                    transform=ax.transAxes, fontsize=11, color=GRAY)
            ax.set_title(label, fontsize=11, color="#2c2c2a")
            continue

        years = d["years"]
        ax.plot(years, d["pcts"], color=color, linewidth=1.0, marker="o",
                markersize=2.5, alpha=0.55, zorder=2, label="Actual")
        ax.plot(years, d["level"], color=color, linewidth=2.0, zorder=3,
                label="Smoothed trend")

        # Forecast fan: dashed central path bridged from the last smoothed level,
        # with 80% and 95% prediction bands.
        fy = d["forecast_years"]
        bx = [years[-1]] + list(fy)
        ax.plot(bx, [d["level"][-1]] + d["mean"], color=color, linewidth=1.8,
                linestyle="--", zorder=3, label="Forecast")
        ax.fill_between(fy, d["ci95_lo"], d["ci95_hi"], color=color, alpha=0.12,
                        linewidth=0, zorder=1, label="95% range")
        ax.fill_between(fy, d["ci80_lo"], d["ci80_hi"], color=color, alpha=0.22,
                        linewidth=0, zorder=1, label="80% range")
        ax.axvline(years[-1] + 0.5, color=GRAY, linewidth=1.0, linestyle=":",
                   alpha=0.7, zorder=1)
        ax.axhline(50.0, color=GRAY, linewidth=0.8, alpha=0.6, zorder=1)

        ax.set_title(label, fontsize=11, fontweight="bold", color="#2c2c2a")
        ax.set_xlabel("Season ending", fontsize=9)
        ax.set_ylabel("Home win %", fontsize=9)
        ax.yaxis.set_major_formatter(mticker.PercentFormatter(decimals=0))
        ax.grid(alpha=0.3, linewidth=0.6)
        ax.legend(fontsize=7.6, framealpha=0.85, edgecolor="#ddd", loc="lower left")

    fig.suptitle(
        "The home win rate is forecast to keep sliding, with a wide range of outcomes",
        fontsize=13, fontweight="bold", color="#2c2c2a", y=1.0,
    )
    fig.text(
        0.5, 0.93,
        "Local-linear-trend state-space model on the season home win %  |  dashed "
        "central forecast with 80% and 95% prediction bands  |  the band widens "
        "with the horizon",
        ha="center", fontsize=8.5, color=GRAY,
    )
    plt.tight_layout(rect=(0, 0, 1, 0.9))
    save_chart("home_court_hca_forecast.svg", OUTPUT_DIR)


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
    fig.suptitle("A crowd's presence matters; its size does not",
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
    save_chart("home_court_attendance.svg", OUTPUT_DIR)
