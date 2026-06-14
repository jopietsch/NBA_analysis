"""
nba_home_court_plots.py — visualization for NBA home court advantage analysis.

All plot_* functions that generate and save PNG charts. Data is provided
by nba_home_court_data; this module adds only matplotlib rendering.
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from scipy.stats import pearsonr

from nba_home_court_data import (
    ERA_DEFS, COVID_SEASONS,
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

# Display metadata for timezone, travel, and shot zone analyses
TZ_COLORS = {"0": GRAY, "1": "#378add", "2": "#e8a33d", "3": "#e24b4a"}
TZ_LABELS = {
    "0": "Same time zone",
    "1": "1 time zone crossed",
    "2": "2 time zones crossed",
    "3": "3 time zones crossed (coast-to-coast)",
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


def _add_trend_line(
    ax: plt.Axes,
    x: np.ndarray,
    y: np.ndarray,
    color: str,
    *,
    linestyle: str = "--",
    linewidth: float = 1.4,
    alpha: float = 0.5,
    zorder: int = 3,
    x_plot: np.ndarray | None = None,
) -> None:
    mask = ~np.isnan(y)
    if mask.sum() < 2:
        return
    z = np.polyfit(x[mask], y[mask], 1)
    xp = x if x_plot is None else x_plot
    ax.plot(xp, np.poly1d(z)(xp), linestyle, color=color,
            linewidth=linewidth, alpha=alpha, zorder=zorder)


# ── Plot functions ────────────────────────────────────────────────────────────
def plot_results(
    reg_seasons: list[str], reg_pcts: list[float],
    po_seasons: list[str], po_pcts: list[float],
    era_reg_avg: list[float], era_po_avg: list[float], era_labels_short: list[str],
    format_reg_avg: list[float], format_po_avg: list[float], format_labels_short: list[str],
) -> None:
    """Save the standalone season, era, and format-period panels."""
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

    _save("nba_home_court_advantage_season.png",
          lambda ax: _draw_season_overview(ax, reg_seasons, reg_pcts, po_seasons, po_pcts),
          (14, 7))
    _save("nba_home_court_advantage_era_bars.png",
          lambda ax: _draw_paired_bars(ax, era_reg_avg, era_po_avg, era_labels_short,
                                       "Regular season vs playoffs\nhome win % by era"),
          (5, 3))
    _save("nba_home_court_advantage_format_bars.png",
          lambda ax: _draw_paired_bars(ax, format_reg_avg, format_po_avg, format_labels_short,
                                       "Regular season vs playoffs\nhome win % by playoff format period"),
          (5, 3))


def plot_mediation(decomp: dict) -> None:
    """
    Two-panel decomposition: each box-score channel's share of the home-court
    level (left) and of its 40-year decline (right), regular season vs playoffs.

    Renders the same numbers RESULTS.md prints — the dict comes from
    nba_home_court_regression.compute_mediation_decomposition(). Bars are
    normalized to 100% (the shares sum to 100 by accounting identity); the
    headline at each bar's end is how much of the level/decline the four
    channels capture.
    """
    seg_order  = ["Shooting", "Rebounding", "Fouls", "Turnovers"]
    seg_colors = {"Shooting": BLUE, "Rebounding": GREEN, "Fouls": RED,
                  "Turnovers": "#e8a33d"}
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
             "Box-score channel shares of the home-court edge (left) and of its 40-year decline (right)  |  "
             "shares sum to 100% by accounting identity",
             ha="center", fontsize=9, color=GRAY)

    draw_panel(ax1, "level", "What creates the home edge",   "pct_level", "explained")
    draw_panel(ax2, "trend", "What's driving the decline",   "pct_trend", "mediated")

    handles = [mpatches.Patch(color=seg_colors[l], label=l) for l in seg_order]
    handles.append(mpatches.Patch(color=RESID, label="Unexplained / unmediated"))
    fig.legend(handles=handles, fontsize=9, ncol=5, loc="lower center",
               framealpha=0.85, edgecolor="#ddd", bbox_to_anchor=(0.5, -0.04))

    plt.tight_layout(rect=(0, 0.05, 1, 0.95))
    output_path = "nba_home_court_mediation.png"
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
    output_path = "nba_home_court_advantage_differentials.png"
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
             "Data: NBA.com  |  Positive = home team winning by more  |  1983-84 through 2024-25",
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
    output_path = "nba_home_court_margin.png"
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
    output_path = "nba_home_court_parity.png"
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
    output_path = "nba_home_court_shot_zones.png"
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
    _scatter_panel(ax2, reg_seasons, list(y_tpa_reg), list(y_pct_reg),
                   "Regular season: 3PA rate vs. home win %\n(one point per season)",
                   "League 3PA rate (% of FGA)", fmt_x=True)
    _scatter_panel(ax3, po_seasons,  list(y_tpa_po),  list(y_pct_po),
                   "Playoffs: 3PA rate vs. home win %\n(one point per season)",
                   "League 3PA rate (% of FGA)", fmt_x=True)

    plt.tight_layout()
    output_path = "nba_home_court_3pa.png"
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
             "Data: NBA.com  |  Pace = estimated possessions per 48 min per team  "
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
    output_path = "nba_home_court_pace.png"
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

    sorted_teams = sorted(reg_stats, key=lambda t: reg_stats[t]["hca"], reverse=True)
    hcas   = [reg_stats[t]["hca"] for t in sorted_teams]
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
        "Data: NBA.com  |  HCA = home win% − road win%  |  1983–84 through 2024–25  |"
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
    ax1.set_title("Regular-season HCA by franchise (all-time)",
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
        sorted_by_reg = sorted(common, key=lambda t: reg_stats[t]["hca"], reverse=True)
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
    output_path = "nba_home_court_team_hca.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()


def plot_referee_analysis(bias_stats: list[dict]) -> None:
    """
    Two-panel figure:
      Left  — top/bottom 15 officials ranked by career mean home foul_diff
      Right — box plots of per-official era-mean foul_diff by era (shows whether
              the distribution of referee biases has narrowed over time)
    Saves → nba_home_court_referee.png
    """
    if not bias_stats:
        print("plot_referee_analysis: no bias stats, skipping.")
        return

    era_order = [e[0] for e in ERA_DEFS]
    era_data: dict[str, list[float]] = {e: [] for e in era_order}
    for o in bias_stats:
        for era, mean in o["era_means"].items():
            if era in era_data:
                era_data[era].append(mean)
    era_labels_present = [e for e in era_order if era_data[e]]
    box_data = [era_data[e] for e in era_labels_present]

    n_show = min(15, len(bias_stats) // 2)
    top    = list(reversed(bias_stats[-n_show:]))   # most home-favoring (most negative)
    bottom = bias_stats[:n_show]                     # least home-favoring (most positive)
    show   = bottom + top
    names  = [o["name"].split()[-1] for o in show]  # last name only for brevity
    vals   = [o["mean_foul_diff"] for o in show]
    bar_colors = [GREEN if v < 0 else RED for v in vals]

    fig, (ax1, ax2) = plt.subplots(
        1, 2,
        figsize=(16, max(8, n_show * 0.55 + 3)),
        facecolor=BG,
    )
    for ax in (ax1, ax2):
        ax.set_facecolor(PANEL)

    # ── Panel 1: ranking bar chart ────────────────────────────────────────────
    y_pos = range(len(show))
    bars = ax1.barh(list(y_pos), vals, color=bar_colors, edgecolor="white",
                    linewidth=0.5, height=0.7)
    ax1.set_yticks(list(y_pos))
    ax1.set_yticklabels(names, fontsize=8)
    ax1.axvline(0, color=GRAY, linewidth=0.8, linestyle="--", alpha=0.6)
    ax1.axhline(n_show - 0.5, color=GRAY, linewidth=0.6, linestyle=":", alpha=0.5)

    for bar, v in zip(bars, vals):
        xoff = -0.05 if v < 0 else 0.05
        ha   = "right" if v < 0 else "left"
        ax1.text(v + xoff, bar.get_y() + bar.get_height() / 2,
                 f"{v:+.2f}", ha=ha, va="center", fontsize=7, color="#333")

    ax1.set_xlabel("Mean home − away fouls per game", fontsize=10)
    ax1.set_title(
        f"Top/bottom {n_show} referees by\nhome foul differential (≥50 playoff games)",
        fontsize=11, fontweight="bold", color="#2c2c2a", pad=6,
    )
    neg = mpatches.Patch(color=GREEN, label="Home-favoring (fewer home fouls)")
    pos = mpatches.Patch(color=RED,   label="Visitor-favoring (more home fouls)")
    ax1.legend(handles=[neg, pos], fontsize=8, framealpha=0.85, edgecolor="#ddd")
    ax1.invert_yaxis()

    # ── Panel 2: box plot by era ──────────────────────────────────────────────
    if box_data:
        bp = ax2.boxplot(
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

        ax2.axhline(0, color=GRAY, linewidth=0.8, linestyle="--", alpha=0.6)
        ax2.set_xlabel("Era", fontsize=10)
        ax2.set_ylabel("Per-official era-mean foul diff (home − away)", fontsize=9)
        ax2.set_title(
            "Distribution of per-official home foul bias\nby era (each point = one referee)",
            fontsize=11, fontweight="bold", color="#2c2c2a", pad=6,
        )
        ax2.tick_params(axis="x", labelsize=8)
    else:
        ax2.text(0.5, 0.5, "Insufficient data for era breakdown",
                 ha="center", va="center", transform=ax2.transAxes,
                 fontsize=12, color=GRAY)

    plt.suptitle("Referee Home Foul Bias — Playoffs", fontsize=13,
                 fontweight="bold", color="#2c2c2a", y=1.01)
    plt.tight_layout()
    output_path = "nba_home_court_referee.png"
    plt.savefig(output_path, dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"\nSaved → {output_path}")
    plt.close()
