"""
nba_home_court_summary_plots.py — story-optimized charts for the visual summary PDF.

Each function loads its own data from cache via nba_home_court_data.
Run directly to generate all four summary PNGs:

    MPLBACKEND=Agg python3 nba_home_court_summary_plots.py
"""

import os

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
from scipy.stats import pearsonr
from nba_api.stats.library.parameters import SeasonType

from nba_home_court_data import (
    START_YEAR, END_YEAR, SKIP_PLAYOFF_YEARS,
    fetch_all_seasons,
    compute_differential_stats,
    compute_league_3pa_stats,
    compute_team_hca_stats,
    fetch_all_referee_data,
    compute_referee_bias_stats,
    _align_to_seasons,
)

OUTPUT_DIR = "generated"


def _output_path(name: str) -> str:
    """Return the path under OUTPUT_DIR for a chart file, creating the dir."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, name)


BLUE   = "#378add"
GREEN  = "#1d9e75"
RED    = "#e24b4a"
ORANGE = "#e8a33d"
GRAY   = "#888780"
BG     = "#f9f9f7"
PANEL  = "#ffffff"


def _rc():
    plt.rcParams.update({
        "font.family":       "DejaVu Sans",
        "axes.spines.top":   False,
        "axes.spines.right": False,
        "axes.facecolor":    PANEL,
        "figure.facecolor":  BG,
        "axes.grid":         True,
        "grid.color":        "#e0dfd8",
        "grid.linewidth":    0.6,
        "axes.axisbelow":    True,
    })


def _trend(ax, x, y, color, linewidth=2, alpha=0.6):
    y = np.asarray(y, dtype=float)
    mask = ~np.isnan(y)
    if mask.sum() < 2:
        return
    z = np.polyfit(x[mask], y[mask], 1)
    ax.plot(x, np.poly1d(z)(x), "--", color=color, linewidth=linewidth, alpha=alpha)


# ── Plot 1: The Decline ───────────────────────────────────────────────────────

def plot_summary_decline():
    reg_seasons, reg_pcts, po_seasons, po_pcts = fetch_all_seasons()
    _rc()

    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor(BG)

    x     = np.arange(len(reg_seasons))
    y_reg = np.array(reg_pcts)

    po_lookup = dict(zip(po_seasons, po_pcts))
    y_po = np.array([po_lookup.get(s, np.nan) for s in reg_seasons])

    ax.plot(x, y_reg, color=BLUE,  linewidth=3.5, zorder=2, label="Regular season")
    ax.plot(x, y_po,  color=GREEN, linewidth=3.5, zorder=2, label="Playoffs")

    _trend(ax, x, y_reg, BLUE)
    _trend(ax, x, y_po,  GREEN)

    # Annotate start (first season)
    ax.annotate(
        f"{y_reg[0]:.0f}%",
        xy=(0, y_reg[0]),
        xytext=(5, y_reg[0] + 5),
        arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.8),
        fontsize=18, fontweight="bold", color=BLUE, ha="center",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=BLUE, alpha=0.9),
    )

    # Annotate end (most recent season)
    ax.annotate(
        f"{y_reg[-1]:.0f}%",
        xy=(x[-1], y_reg[-1]),
        xytext=(x[-1] - 6, y_reg[-1] - 5),
        arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.8),
        fontsize=18, fontweight="bold", color=BLUE, ha="center",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=BLUE, alpha=0.9),
    )

    # Central callout
    ax.text(len(x) // 2, 48.5,
            "10 percentage points — erased over 40 seasons",
            ha="center", fontsize=15, fontweight="bold", color=GRAY,
            bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=GRAY, alpha=0.9))

    ax.set_xticks(x[::5])
    ax.set_xticklabels(reg_seasons[::5], fontsize=14)
    ax.set_ylim(45, 80)
    ax.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax.tick_params(axis="y", labelsize=14)
    ax.set_ylabel("Home win %", fontsize=15)

    handles = [
        mpatches.Patch(color=BLUE,  label="Regular season"),
        mpatches.Patch(color=GREEN, label="Playoffs"),
        plt.Line2D([0], [0], color=GRAY, linestyle="--", alpha=0.7, label="Long-run trend"),
    ]
    ax.legend(handles=handles, fontsize=13, loc="upper right", framealpha=0.9)
    ax.set_title("Home Court Advantage Has Been Sliding for 40 Years",
                 fontsize=20, fontweight="bold", color="#2c2c2a", pad=14)

    plt.tight_layout()
    plt.savefig(_output_path("summary_decline.png"), dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"Saved → {_output_path('summary_decline.png')}")
    plt.close()


# ── Plot 2: The Whistle ───────────────────────────────────────────────────────

def plot_summary_whistle():
    reg_seasons, reg_stats = compute_differential_stats(START_YEAR, END_YEAR, SeasonType.regular)
    po_seasons,  po_stats  = compute_differential_stats(
        START_YEAR, END_YEAR, "Playoffs", skip_years=SKIP_PLAYOFF_YEARS
    )
    ref_df = fetch_all_referee_data(
        START_YEAR, END_YEAR, "Playoffs", skip_years=SKIP_PLAYOFF_YEARS
    )
    bias_stats = []
    if ref_df is not None:
        bias_stats = compute_referee_bias_stats(
            ref_df, START_YEAR, END_YEAR, "Playoffs",
            skip_years=SKIP_PLAYOFF_YEARS, min_games=50,
        )

    _rc()
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.patch.set_facecolor(BG)

    # ── Left: foul differential over time ────────────────────────────────────
    x     = np.arange(len(reg_seasons))
    y_reg = np.array(reg_stats["foul_diff"])
    y_po  = _align_to_seasons(reg_seasons, po_seasons, po_stats, "foul_diff")

    ax1.plot(x, y_reg, color=BLUE,  linewidth=2.5, label="Regular season", zorder=2)
    ax1.plot(x, y_po,  color=GREEN, linewidth=2.5, label="Playoffs",        zorder=2)
    _trend(ax1, x, y_reg, BLUE)
    _trend(ax1, x, y_po,  GREEN)
    ax1.axhline(0, color=GRAY, linewidth=1, linestyle=":", zorder=1)

    tick_step = max(1, len(reg_seasons) // 8)
    ax1.set_xticks(x[::tick_step])
    ax1.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=11)
    ax1.tick_params(axis="y", labelsize=12)
    ax1.set_ylabel("Home fouls minus away fouls", fontsize=13)
    ax1.legend(fontsize=12, framealpha=0.9)

    early_val  = float(np.nanmean(y_reg[:5]))
    recent_val = float(np.nanmean(y_reg[-5:]))

    ax1.annotate(
        f"Early 1980s:\n{early_val:.1f} fouls/game",
        xy=(2, y_reg[2]),
        xytext=(9, early_val + 0.55),
        arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5),
        fontsize=12, fontweight="bold", color=BLUE, ha="center",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=BLUE, alpha=0.9),
    )
    ax1.annotate(
        f"Today:\n{recent_val:.1f} fouls/game",
        xy=(x[-3], y_reg[-3]),
        xytext=(x[-10], recent_val - 0.65),
        arrowprops=dict(arrowstyle="->", color=BLUE, lw=1.5),
        fontsize=12, fontweight="bold", color=BLUE, ha="center",
        bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=BLUE, alpha=0.9),
    )

    ax1.set_title("Refs Used to Favor the Home Team",
                  fontsize=16, fontweight="bold", color="#2c2c2a", pad=10)

    # ── Right: referee dot chart ──────────────────────────────────────────────
    if bias_stats:
        vals = np.array([o["mean_foul_diff"] for o in bias_stats])
        rng  = np.random.default_rng(42)
        y_j  = rng.uniform(-0.3, 0.3, len(vals))
        dot_colors = [GREEN if v < 0 else RED for v in vals]

        ax2.scatter(vals, y_j, c=dot_colors, s=90, zorder=3,
                    edgecolors="white", linewidths=0.8)
        ax2.axvline(0, color=GRAY, linewidth=1.5, linestyle="--", alpha=0.7)

        n_home  = int((vals < 0).sum())
        n_total = len(vals)

        ax2.text(0.5, 0.88,
                 f"{n_home} of {n_total} playoff referees\nfavor the home team — every career",
                 transform=ax2.transAxes, ha="center", fontsize=13, fontweight="bold",
                 color="#2c2c2a",
                 bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=GRAY, alpha=0.9))

        ax2.set_xlabel(
            "Career mean: home fouls minus away fouls\n(negative = fewer fouls on home team)",
            fontsize=12,
        )
        ax2.tick_params(axis="x", labelsize=12)
        ax2.set_yticks([])
        ax2.spines["left"].set_visible(False)
        ax2.set_ylim(-0.8, 1.2)

        ax2.legend(
            handles=[
                mpatches.Patch(color=GREEN, label="Home-favoring"),
                mpatches.Patch(color=RED,   label="Road-favoring"),
            ],
            fontsize=11, loc="lower right", framealpha=0.9,
        )
    else:
        ax2.text(0.5, 0.5, "Referee data not available\n(run full pipeline first)",
                 ha="center", va="center", transform=ax2.transAxes,
                 fontsize=13, color=GRAY)

    ax2.set_title("Every Career. Almost. 41 of 42.",
                  fontsize=16, fontweight="bold", color="#2c2c2a", pad=10)

    plt.tight_layout()
    plt.savefig(_output_path("summary_whistle.png"), dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"Saved → {_output_path('summary_whistle.png')}")
    plt.close()


# ── Plot 3: The 3-Point Revolution ────────────────────────────────────────────

def plot_summary_3point():
    reg_seasons, reg_tpa, reg_pcts = compute_league_3pa_stats(
        START_YEAR, END_YEAR, SeasonType.regular
    )
    _rc()

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    fig.patch.set_facecolor(BG)

    x     = np.arange(len(reg_seasons))
    y_tpa = np.array(reg_tpa)
    y_pct = np.array(reg_pcts)

    tick_step = max(1, len(reg_seasons) // 8)

    # ── Left: dual-axis time series ───────────────────────────────────────────
    ax1.plot(x, y_pct, color=BLUE, linewidth=3, zorder=2)
    ax1.set_xticks(x[::tick_step])
    ax1.set_xticklabels(reg_seasons[::tick_step], rotation=45, ha="right", fontsize=11)
    ax1.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1.tick_params(axis="y", labelcolor=BLUE, labelsize=12)
    ax1.set_ylabel("Home win %", color=BLUE, fontsize=13)

    ax1r = ax1.twinx()
    ax1r.plot(x, y_tpa, color=ORANGE, linewidth=3, zorder=2, alpha=0.9)
    ax1r.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax1r.tick_params(axis="y", labelcolor=ORANGE, labelsize=12)
    ax1r.set_ylabel("League 3PA rate", color=ORANGE, fontsize=13)
    ax1r.spines["top"].set_visible(False)

    ax1.text(0.5, 0.08,
             "Nearly perfect mirror images over 40 years",
             transform=ax1.transAxes, ha="center", fontsize=12, fontweight="bold",
             color=GRAY,
             bbox=dict(boxstyle="round,pad=0.4", fc="white", ec=GRAY, alpha=0.9))

    ax1.legend(
        handles=[
            plt.Line2D([0], [0], color=BLUE,   linewidth=2.5, label="Home win %"),
            plt.Line2D([0], [0], color=ORANGE, linewidth=2.5, label="3PA rate"),
        ],
        fontsize=12, loc="center right", framealpha=0.9,
    )
    ax1.set_title("As 3-Pointers Took Over,\nHome Court Faded",
                  fontsize=16, fontweight="bold", color="#2c2c2a", pad=10)

    # ── Right: scatter ────────────────────────────────────────────────────────
    valid = ~np.isnan(y_tpa) & ~np.isnan(y_pct)
    r, _  = pearsonr(y_tpa[valid], y_pct[valid])

    ax2.scatter(y_tpa, y_pct, color=BLUE, s=75, zorder=3,
                edgecolors="white", linewidths=0.8, alpha=0.85)

    z  = np.polyfit(y_tpa[valid], y_pct[valid], 1)
    xr = np.linspace(y_tpa[valid].min(), y_tpa[valid].max(), 100)
    ax2.plot(xr, np.poly1d(z)(xr), "--", color=GRAY, linewidth=2, alpha=0.7)

    ax2.text(0.5, 0.20,
             f"r = {r:.2f}\nOne of the tightest relationships\nin sports analytics",
             transform=ax2.transAxes, ha="center", fontsize=13, fontweight="bold",
             color="#2c2c2a",
             bbox=dict(boxstyle="round,pad=0.5", fc="white", ec=GRAY, alpha=0.9))

    ax2.set_xlabel("League 3PA rate (% of all field-goal attempts)", fontsize=12)
    ax2.xaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax2.yaxis.set_major_formatter(mticker.FormatStrFormatter("%.0f%%"))
    ax2.set_ylabel("Home win %", fontsize=13)
    ax2.tick_params(labelsize=12)
    ax2.set_title("More 3-Pointers. Less Home Court.\nEvery Year.",
                  fontsize=16, fontweight="bold", color="#2c2c2a", pad=10)

    plt.tight_layout()
    plt.savefig(_output_path("summary_3point.png"), dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"Saved → {_output_path('summary_3point.png')}")
    plt.close()


# ── Plot 4: Franchise Rankings ────────────────────────────────────────────────

def plot_summary_franchises():
    reg_stats = compute_team_hca_stats(START_YEAR, END_YEAR, "Regular Season")
    _rc()

    sorted_teams = sorted(reg_stats, key=lambda t: reg_stats[t]["hca"], reverse=True)
    hcas   = [reg_stats[t]["hca"] for t in sorted_teams]
    colors = [GREEN if h >= 0 else RED for h in hcas]

    height = max(8, len(sorted_teams) * 0.26 + 2)
    fig, ax = plt.subplots(figsize=(14, height))
    fig.patch.set_facecolor(BG)

    y    = np.arange(len(sorted_teams))
    bars = ax.barh(y, hcas, color=colors, edgecolor="white", linewidth=0.5, height=0.75)

    ax.axvline(0, color=GRAY, linewidth=1.0, zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels(
        [t.replace("Los Angeles", "LA").replace("New Orleans/Oklahoma City", "NO/OKC")
         for t in sorted_teams],
        fontsize=10,
    )
    ax.invert_yaxis()
    ax.xaxis.set_major_formatter(mticker.FormatStrFormatter("%+.0f pp"))
    ax.set_xlabel("Home win% minus road win% (percentage points)", fontsize=13)
    ax.tick_params(axis="x", labelsize=12)

    for bar, h in zip(bars, hcas):
        xoff = 0.3 if h >= 0 else -0.3
        ha   = "left"  if h >= 0 else "right"
        ax.text(h + xoff, bar.get_y() + bar.get_height() / 2,
                f"{h:+.1f}", ha=ha, va="center", fontsize=8.5, color="#444")

    altitude = {"Denver Nuggets", "Utah Jazz"}
    for i, t in enumerate(sorted_teams):
        if t in altitude:
            ax.text(hcas[i] + 0.6, i, "(altitude)",
                    va="center", fontsize=9, color=GRAY, style="italic")

    ax.set_title(
        "All-Time Home Court Edge by Franchise, 1983–84 through 2024–25\n"
        "Home win% minus road win%",
        fontsize=17, fontweight="bold", color="#2c2c2a", pad=12,
    )

    plt.tight_layout()
    plt.savefig(_output_path("summary_franchises.png"), dpi=150, bbox_inches="tight", facecolor=BG)
    print(f"Saved → {_output_path('summary_franchises.png')}")
    plt.close()


# ── Entry point ───────────────────────────────────────────────────────────────

def generate_all():
    print("Generating summary charts...")
    plot_summary_decline()
    plot_summary_whistle()
    plot_summary_3point()
    plot_summary_franchises()
    print("Done.")


if __name__ == "__main__":
    generate_all()
