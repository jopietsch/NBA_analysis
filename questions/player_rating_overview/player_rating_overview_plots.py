"""
player_rating_overview_plots.py — all visualizations for the player rating overview.

Each plot_* function saves an SVG to generated/images/ and returns the path.
No data logic lives here; all computation is done by player_rating_overview_data.py.

Color semantics (consistent across all charts in this project):
  - Recomputed systems (box-score): BLUE (#378add)
  - Results-only systems (impact metrics): GREEN (#1d9e75)
  - Human/reputation rankings: RED (#e24b4a)
  - Consensus uber rating: BLUE
  - Wins-predictive uber rating: GREEN
  - Highlighted player / series of interest: BLUE
  - Muted context: GRAY (#888780)
  - Positive/higher value: GREEN, negative/lower: RED
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import pandas as pd
from scipy import stats

from nbakit.viz import BLUE, GREEN, RED, GRAY, LGRAY, BG, PANEL, save_chart, style_axes, new_fig
from player_rating_overview_data import playoff_weighted_value, PLAYOFF_VALUE_WEIGHT

plt.rcParams["svg.fonttype"] = "path"

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated", "images")

SYSTEM_COLORS = {
    # Recomputed box-score systems
    "GAME_SCORE": BLUE,
    "PER": BLUE,
    "WS": BLUE,
    "WS48": BLUE,
    "BPM": BLUE,
    "OBPM": BLUE,
    "DBPM": BLUE,
    "VORP": BLUE,
    # Results-only impact metrics
    "RAPTOR": GREEN,
    "RAPTOR_WAR": GREEN,
    "DARKO_DPM": GREEN,
    "EPM": GREEN,
    "LEBRON": GREEN,
    "ESPN_RPM": GREEN,
    "RAPM": GREEN,
    "RAPM_MY": GREEN,
    # Human / reputation
    "MVP_SHARE": RED,
    "ALL_NBA_PTS": RED,
    # Uber ratings
    "CONSENSUS": BLUE,
    "WINS_PRED": GREEN,
}

# Human-readable labels for each system column
SYSTEM_LABELS = {
    "GAME_SCORE": "Game Score",
    "PER": "PER",
    "TS_PCT": "TS%",
    "EFG_PCT": "eFG%",
    "USG_PCT": "USG%",
    "WS": "Win Shares",
    "WS48": "WS/48",
    "OWS": "Off Win Shares",
    "DWS": "Def Win Shares",
    "BPM": "BPM",
    "OBPM": "Off BPM",
    "DBPM": "Def BPM",
    "VORP": "VORP",
    "RAPTOR": "RAPTOR",
    "RAPTOR_O": "RAPTOR-O",
    "RAPTOR_D": "RAPTOR-D",
    "RAPTOR_WAR": "RAPTOR WAR",
    "DARKO_DPM": "DARKO DPM",
    "EPM": "EPM",
    "LEBRON": "LEBRON",
    "ESPN_RPM": "ESPN RPM",
    "RAPM": "RAPM",
    "O_RAPM": "O-RAPM",
    "D_RAPM": "D-RAPM",
    "RAPM_MY": "RAPM+prior",
    "O_RAPM_MY": "O-RAPM+prior",
    "D_RAPM_MY": "D-RAPM+prior",
    "MVP_SHARE": "MVP Vote Share",
    "ALL_NBA_PTS": "All-NBA Points",
    "CONSENSUS": "Consensus Rating",
    "WINS_PRED": "Wins-Predictive",
}


def _output(name: str) -> str:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, name)


# ── Chart 1: System agreement heatmap ────────────────────────────────────────

def plot_rank_agreement_heatmap(df: pd.DataFrame,
                                 systems: list[str]) -> str:
    """Spearman rank-correlation matrix across rating systems.

    Title: 'Rating systems mostly agree at the top, diverge in the middle.'
    """
    qual = df[df.get("QUALIFIED", pd.Series(True, index=df.index))].copy()
    present = [s for s in systems if s in qual.columns and qual[s].notna().sum() > 10]
    if len(present) < 2:
        fig, ax = new_fig(figsize=(6, 5))
        ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                transform=ax.transAxes, color=GRAY)
        return save_chart("rank_agreement_heatmap.svg", OUTPUT_DIR)

    corr_data = qual[present].rank(pct=True)
    corr = corr_data.corr(method="spearman")
    labels = [SYSTEM_LABELS.get(s, s) for s in present]
    n = len(present)

    fig, ax = plt.subplots(figsize=(max(6, n * 0.8), max(5, n * 0.75)), facecolor=BG)
    ax.set_facecolor(PANEL)

    im = ax.imshow(corr.values, cmap="RdYlGn", vmin=-1, vmax=1, aspect="auto")
    plt.colorbar(im, ax=ax, shrink=0.8, label="Spearman rank correlation")

    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9)
    ax.set_yticklabels(labels, fontsize=9)

    for i in range(n):
        for j in range(n):
            val = corr.values[i, j]
            color = "white" if abs(val) > 0.6 else "#333"
            ax.text(j, i, f"{val:.2f}", ha="center", va="center",
                    fontsize=7, color=color)

    ax.set_title("Rating systems mostly agree at the top, diverge in the middle",
                 fontsize=11, pad=12, color="#222")
    ax.set_xlabel("", fontsize=9, color=GRAY)
    fig.tight_layout()
    return save_chart("rank_agreement_heatmap.svg", OUTPUT_DIR, fig=fig)


# ── Chart 2: Who each system loves vs. consensus ──────────────────────────────

def plot_system_outliers(df: pd.DataFrame,
                          systems: list[str],
                          n_players: int = 8) -> str:
    """For each system, show the players it ranks highest above consensus.

    Title: 'What each system sees that the others miss.'
    """
    qual = df[df.get("QUALIFIED", pd.Series(True, index=df.index)) == True].copy()

    # Consensus = mean z-score across all present systems
    present = [s for s in systems if s in qual.columns and qual[s].notna().sum() > 10]
    if len(present) < 2 or "PLAYER_NAME" not in qual.columns:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                transform=ax.transAxes)
        return save_chart("system_outliers.svg", OUTPUT_DIR, fig=fig)

    for s in present:
        col = qual[s]
        std = col.std()
        qual[f"_z_{s}"] = (col - col.mean()) / std if std > 0 else 0

    z_cols = [f"_z_{s}" for s in present]
    qual["_consensus"] = qual[z_cols].mean(axis=1)

    n_sys = min(len(present), 4)
    fig, axes = plt.subplots(1, n_sys, figsize=(n_sys * 3.5, 5), facecolor=BG,
                              sharey=False)
    if n_sys == 1:
        axes = [axes]

    for ax, sys in zip(axes, present[:n_sys]):
        qual[f"_resid_{sys}"] = qual[f"_z_{sys}"] - qual["_consensus"]
        top = qual.nlargest(n_players, f"_resid_{sys}")[["PLAYER_NAME", f"_resid_{sys}"]]
        color = SYSTEM_COLORS.get(sys, BLUE)
        ax.barh(range(len(top)), top[f"_resid_{sys}"].values[::-1], color=color, alpha=0.85)
        ax.set_yticks(range(len(top)))
        ax.set_yticklabels(top["PLAYER_NAME"].values[::-1], fontsize=8)
        ax.set_title(SYSTEM_LABELS.get(sys, sys), fontsize=10, color="#222")
        ax.axvline(0, color=GRAY, linewidth=0.8)
        ax.set_xlabel("vs. consensus (z)", fontsize=8, color=GRAY)
        style_axes(ax)
        ax.set_facecolor(PANEL)

    fig.suptitle("What each system sees that the others miss",
                 fontsize=12, y=1.01, color="#222")
    fig.tight_layout()
    return save_chart("system_outliers.svg", OUTPUT_DIR, fig=fig)


# ── Chart 3: Distribution shapes (log-scale rank-value) ──────────────────────

def plot_rank_value_distributions(df: pd.DataFrame,
                                   systems: list[str],
                                   top_n: int = 50) -> str:
    """Value-vs-rank drop-off chart, normalized to % of the rank-1 player's value.

    All systems start at 100% (rank 1) and the y-axis shows how quickly value
    falls as rank increases. Cumulative metrics (WS, VORP) plunge steeply;
    rate metrics (PER, Game Score, BPM) stay much flatter. Single panel so
    all curves are directly comparable on the same scale.
    """
    qual = df[df.get("QUALIFIED", pd.Series(True, index=df.index)) == True].copy()

    # Distinct colors for this chart — override the category palette so individual
    # systems are distinguishable. Ordered to alternate between cumulative and rate.
    _per_system_colors = [
        "#2196F3",  # blue
        "#F44336",  # red
        "#4CAF50",  # green
        "#FF9800",  # orange
        "#9C27B0",  # purple
        "#00BCD4",  # cyan
        "#795548",  # brown
        "#607D8B",  # blue-grey
    ]

    fig, ax = plt.subplots(figsize=(10, 6), facecolor=BG)
    ax.set_facecolor(PANEL)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    color_idx = 0
    for sys in systems:
        if sys not in qual.columns:
            continue
        vals = qual[sys].dropna().sort_values(ascending=False).reset_index(drop=True)
        if len(vals) < top_n or vals.iloc[0] <= 0:
            continue
        pct = (vals.iloc[:top_n] / vals.iloc[0] * 100).values
        color = _per_system_colors[color_idx % len(_per_system_colors)]
        ax.plot(np.arange(1, top_n + 1), pct,
                color=color, linewidth=1.8, alpha=0.85,
                label=SYSTEM_LABELS.get(sys, sys))
        color_idx += 1

    if color_idx == 0:
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                transform=ax.transAxes, color=GRAY)
    else:
        ax.legend(fontsize=8, frameon=False, loc="upper right", ncol=2)

    ax.set_xlabel(f"Player rank (1 = best, up to {top_n})", fontsize=9, color=GRAY)
    ax.set_ylabel("Value as % of rank-1 player", fontsize=9, color=GRAY)
    ax.yaxis.set_major_formatter(mticker.PercentFormatter())
    ax.set_title(
        "Cumulative metrics (Win Shares, VORP) plunge steeply;\nrate metrics stay much flatter",
        fontsize=11, color="#222"
    )
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)
    fig.tight_layout()
    return save_chart("rank_value_distributions.svg", OUTPUT_DIR, fig=fig)


# ── Chart 4: Top-player ordinal vs. actual gap ───────────────────────────────

def plot_ordinal_vs_value_gap(df: pd.DataFrame,
                               metric: str = "VORP",
                               top_n: int = 25) -> str:
    """Show that ordinal rank flattens real value gaps.

    Bar chart of top-N player values, with rank labeled.
    Title: 'Rank 1 and Rank 10 are one line apart, but not one step apart in value.'
    """
    qual = df[df.get("QUALIFIED", pd.Series(True, index=df.index)) == True].copy()
    if metric not in qual.columns or "PLAYER_NAME" not in qual.columns:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "Insufficient data", ha="center", va="center",
                transform=ax.transAxes)
        return save_chart("ordinal_vs_value_gap.svg", OUTPUT_DIR, fig=fig)

    top = qual.nlargest(top_n, metric).reset_index(drop=True)
    ranks = np.arange(1, len(top) + 1)
    vals = top[metric].values
    names = top["PLAYER_NAME"].values

    fig, ax = plt.subplots(figsize=(10, 5), facecolor=BG)
    ax.set_facecolor(PANEL)

    # Continuous color gradient: map bar value to blue intensity so the
    # visual emphasis tracks the actual value, not an arbitrary rank cutoff.
    norm_vals = (vals - vals.min()) / (vals.max() - vals.min() + 1e-9)
    cmap = plt.get_cmap("Blues")
    colors = [cmap(0.35 + 0.55 * v) for v in norm_vals]
    bars = ax.bar(ranks, vals, color=colors, alpha=0.9, width=0.8, zorder=3)

    # Label all bars with the player's last name
    for bar, name in zip(bars, names):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(vals) * 0.01,
                name.split()[-1], ha="center", va="bottom",
                fontsize=7, color="#333", rotation=45)

    ax.set_xlabel("Player rank", fontsize=9, color=GRAY)
    ax.set_ylabel(SYSTEM_LABELS.get(metric, metric), fontsize=9, color=GRAY)
    ax.set_title(
        "Rank 1 and Rank 10 are one line apart, but not one step apart in value",
        fontsize=11, color="#222"
    )
    ax.set_xticks(ranks[::5])
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return save_chart("ordinal_vs_value_gap.svg", OUTPUT_DIR, fig=fig)


# ── Chart 5: Uber rating comparison (consensus vs. wins-predictive) ───────────

def plot_uber_rating_comparison(df: pd.DataFrame,
                                 top_n: int = 20) -> str:
    """Scatter: consensus z-score vs. wins-predictive z-score, top-N labeled.

    Shows where the two approaches agree and where they diverge.
    Title: 'Consensus and wins-predictive ratings agree on stars, diverge on role players.'
    """
    for col in ("CONSENSUS", "WINS_PRED", "PLAYER_NAME"):
        if col not in df.columns:
            fig, ax = new_fig()
            ax.text(0.5, 0.5, f"Missing column: {col}", ha="center", va="center",
                    transform=ax.transAxes)
            return save_chart("uber_rating_comparison.svg", OUTPUT_DIR, fig=fig)

    qual = df[df.get("QUALIFIED", pd.Series(True, index=df.index)) == True].copy()
    qual = qual.dropna(subset=["CONSENSUS", "WINS_PRED"])

    fig, ax = plt.subplots(figsize=(8, 7), facecolor=BG)
    ax.set_facecolor(PANEL)

    # All players: muted
    ax.scatter(qual["WINS_PRED"], qual["CONSENSUS"],
               color=GRAY, alpha=0.35, s=18, zorder=2)

    # Top-N by consensus: highlighted
    top = qual.nlargest(top_n, "CONSENSUS")
    ax.scatter(top["WINS_PRED"], top["CONSENSUS"],
               color=BLUE, alpha=0.85, s=40, zorder=3)

    for _, row in top.iterrows():
        ax.annotate(row["PLAYER_NAME"].split()[-1],
                    (row["WINS_PRED"], row["CONSENSUS"]),
                    fontsize=7, color=BLUE, xytext=(3, 3), textcoords="offset points")

    # Diagonal reference (agreement line)
    lo = min(qual[["WINS_PRED", "CONSENSUS"]].min())
    hi = max(qual[["WINS_PRED", "CONSENSUS"]].max())
    ax.plot([lo, hi], [lo, hi], "--", color=GRAY, linewidth=1, alpha=0.6, label="1:1 line")

    ax.set_xlabel("Wins-predictive rating (z)", fontsize=9, color=GRAY)
    ax.set_ylabel("Consensus rating (z)", fontsize=9, color=GRAY)
    ax.set_title(
        "Consensus and wins-predictive ratings agree on stars,\ndiverge on role players",
        fontsize=11, color="#222"
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(color="#e0dfd8", linewidth=0.7, zorder=0)
    ax.legend(fontsize=8, frameon=False)

    fig.tight_layout()
    return save_chart("uber_rating_comparison.svg", OUTPUT_DIR, fig=fig)


# ── Chart 6: System unique signal (residual variance) ────────────────────────

def plot_unique_signal(unique_r2: dict[str, float]) -> str:
    """Horizontal bar chart: fraction of unique variance each system adds.

    Title: 'How much does each system add beyond what the others already capture?'
    """
    if not unique_r2:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return save_chart("unique_signal.svg", OUTPUT_DIR, fig=fig)

    systems = list(unique_r2.keys())
    vals = [unique_r2[s] for s in systems]
    colors = [SYSTEM_COLORS.get(s, GRAY) for s in systems]
    labels = [SYSTEM_LABELS.get(s, s) for s in systems]

    order = np.argsort(vals)
    fig, ax = plt.subplots(figsize=(8, max(4, len(systems) * 0.45)), facecolor=BG)
    ax.set_facecolor(PANEL)

    bars = ax.barh(range(len(systems)),
                   [vals[i] for i in order],
                   color=[colors[i] for i in order],
                   alpha=0.85)
    ax.set_yticks(range(len(systems)))
    ax.set_yticklabels([labels[i] for i in order], fontsize=9)
    ax.set_xlabel("Unique variance explained (R²)", fontsize=9, color=GRAY)
    ax.set_title(
        "How much does each system add beyond what the others already capture?",
        fontsize=11, color="#222"
    )
    ax.axvline(0, color=GRAY, linewidth=0.8)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="x", color="#e0dfd8", linewidth=0.7, zorder=0)

    fig.tight_layout()
    return save_chart("unique_signal.svg", OUTPUT_DIR, fig=fig)


# ── Chart 7: Gini coefficients (inequality of player value) ──────────────────

def plot_gini_by_system(gini_scores: dict[str, float],
                        highlight: list[str] | None = None) -> str:
    """Bar chart of Gini coefficients across systems.

    A high Gini means value is concentrated at the top, but only for metrics that
    accumulate a non-negative quantity. Gini clips negatives to zero, which
    inflates 0-centered metrics (the BPM family and the uber ratings); the
    subtitle and the findings text flag this. Systems in `highlight` (the uber
    ratings) are drawn with a dark edge so they read as the combined ratings.
    """
    if not gini_scores:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return save_chart("gini_by_system.svg", OUTPUT_DIR, fig=fig)

    highlight = set(highlight or [])
    systems = list(gini_scores.keys())
    vals = [gini_scores[s] for s in systems]
    colors = [SYSTEM_COLORS.get(s, GRAY) for s in systems]
    labels = [SYSTEM_LABELS.get(s, s) for s in systems]

    order = np.argsort(vals)[::-1]
    fig, ax = plt.subplots(figsize=(max(6, len(systems) * 0.9), 5), facecolor=BG)
    ax.set_facecolor(PANEL)

    edgecolors = ["#111111" if systems[i] in highlight else "none" for i in order]
    linewidths = [1.6 if systems[i] in highlight else 0 for i in order]
    ax.bar(range(len(systems)),
           [vals[i] for i in order],
           color=[colors[i] for i in order],
           edgecolor=edgecolors, linewidth=linewidths,
           alpha=0.85)
    ax.set_xticks(range(len(systems)))
    ax.set_xticklabels([labels[i] for i in order], rotation=40, ha="right", fontsize=9)
    ax.set_ylabel("Gini coefficient", fontsize=9, color=GRAY)
    ax.set_title(
        "Where each system concentrates value, by Gini",
        fontsize=11, color="#222", pad=26
    )
    ax.text(0.5, 1.015,
            "Gini over-states 0-centered metrics (BPM family and combined ratings, outlined); "
            "see the steepness read in the text",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=8, color=GRAY)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)

    fig.tight_layout()
    return save_chart("gini_by_system.svg", OUTPUT_DIR, fig=fig)


# ── Chart 8: All systems on one normalized distribution line ─────────────────

def plot_all_systems_distributions(df: pd.DataFrame, systems: list[str],
                                   top_n: int = 50,
                                   highlight: list[str] | None = None) -> str:
    """Normalized rank-value lines for every present system on one chart.

    Each system's values are z-scored (mean 0, std 1) across qualified players,
    then sorted descending. Plots rank 1–top_n on the x-axis vs z-score on y.
    Puts all methodologies on a common scale so their shapes can be compared.
    Systems in `highlight` are drawn last with heavier styling so they read as
    summaries on top of the individual system lines.
    """
    qual = df[df.get("QUALIFIED", pd.Series(True, index=df.index)) == True].copy()
    highlight = set(highlight or [])

    fig, ax = plt.subplots(figsize=(11, 6), facecolor=BG)
    ax.set_facecolor(PANEL)

    _colors = [
        "#2196F3", "#F44336", "#4CAF50", "#FF9800",
        "#9C27B0", "#00BCD4", "#795548", "#607D8B",
    ]
    # Fixed colors for uber ratings so they never collide with the cycle
    _highlight_colors = {"CONSENSUS": "#111111", "WINS_PRED": "#E67E22"}

    plotted = []

    def _plot_system(sys: str) -> None:
        if sys not in qual.columns:
            return
        vals = qual[sys].dropna().sort_values(ascending=False).reset_index(drop=True)
        if len(vals) < top_n:
            return
        vals = vals.iloc[:top_n]
        mean, std = vals.mean(), vals.std()
        if std == 0:
            return
        z = (vals - mean) / std
        if sys in highlight:
            color = _highlight_colors.get(sys, "#333333")
            lw, alpha, zorder = 2.5, 1.0, 3
        else:
            color = _colors[sum(1 for s in plotted if s not in highlight) % len(_colors)]
            lw, alpha, zorder = 1.5, 0.65, 2
        ax.plot(np.arange(1, top_n + 1), z.values,
                color=color, linewidth=lw, alpha=alpha, zorder=zorder,
                label=SYSTEM_LABELS.get(sys, sys))
        plotted.append(sys)

    # Draw regular systems first, then highlighted (so they land on top)
    for sys in systems:
        if sys not in highlight:
            _plot_system(sys)
    for sys in systems:
        if sys in highlight:
            _plot_system(sys)

    if not plotted:
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                transform=ax.transAxes, color=GRAY)
        fig.tight_layout()
        return save_chart("all_systems_distributions.svg", OUTPUT_DIR, fig=fig)

    ax.axhline(0, color=GRAY, linewidth=0.8, linestyle="--", alpha=0.5)
    ax.set_xlabel(f"Player rank (top {top_n} by each system)", fontsize=9, color=GRAY)
    ax.set_ylabel("Standard deviations above/below the qualified-player mean",
                  fontsize=9, color=GRAY)
    ax.set_title(
        "Every system's value falls off steeply in the top tier",
        fontsize=11, color="#222"
    )
    ax.legend(fontsize=8, frameon=False, loc="upper right", ncol=2)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return save_chart("all_systems_distributions.svg", OUTPUT_DIR, fig=fig)


# ── Chart 8b: Power-law check (log-log value vs rank) ─────────────────────────

def plot_powerlaw_fits(df: pd.DataFrame, systems: list[str],
                       top_n: int = 50) -> str:
    """Log-log value-vs-rank for each system, with a straight power-law fit.

    A power law (value proportional to rank^-alpha) is a straight line on
    log-log axes. Systems whose fit clears POWERLAW_R2_THRESHOLD are drawn in
    color with their fitted line; the rest are muted grey, since their curve
    bends rather than holding a constant slope.
    """
    from player_rating_overview_data import powerlaw_fit, POWERLAW_R2_THRESHOLD

    qual = df[df.get("QUALIFIED", pd.Series(True, index=df.index)) == True].copy()

    _colors = [
        "#2196F3", "#F44336", "#4CAF50", "#FF9800",
        "#9C27B0", "#00BCD4", "#795548", "#607D8B",
    ]

    fig, ax = plt.subplots(figsize=(11, 6), facecolor=BG)
    ax.set_facecolor(PANEL)

    color_idx = 0
    n_power = 0
    for sys in systems:
        if sys not in qual.columns:
            continue
        vals = qual[sys].dropna().sort_values(ascending=False).reset_index(drop=True)
        fit = powerlaw_fit(vals.values, top_n=top_n)
        if fit is None:
            continue
        rank = np.arange(1, fit["n_points"] + 1)
        obs = vals.iloc[:fit["n_points"]].values
        is_power = fit["r2"] >= POWERLAW_R2_THRESHOLD
        label = (f"{SYSTEM_LABELS.get(sys, sys)} "
                 f"(α={fit['alpha']:.2f}, R²={fit['r2']:.2f})")
        if is_power:
            color = _colors[color_idx % len(_colors)]
            color_idx += 1
            n_power += 1
            ax.plot(rank, obs, "o", color=color, markersize=4, alpha=0.85,
                    zorder=3, label=label)
            fit_line = np.exp(fit["log_c"]) * rank ** (-fit["alpha"])
            ax.plot(rank, fit_line, "-", color=color, linewidth=1.3,
                    alpha=0.9, zorder=2)
        else:
            ax.plot(rank, obs, "o", color=GRAY, markersize=3, alpha=0.4,
                    zorder=1, label=label)

    ax.set_xscale("log")
    ax.set_yscale("log")
    ax.set_xlabel(f"Player rank, log scale (top {top_n} by each system)",
                  fontsize=9, color=GRAY)
    ax.set_ylabel("Value, log scale", fontsize=9, color=GRAY)
    ax.set_title(
        "On log-log axes, a power law is a straight line:\n"
        f"{n_power} of the box-score systems qualify, the rest bend",
        fontsize=11, color="#222"
    )
    ax.legend(fontsize=7.5, frameon=False, loc="lower left", ncol=2)
    ax.grid(True, which="both", color="#e0dfd8", linewidth=0.6, zorder=0)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.tight_layout()
    return save_chart("powerlaw_fits.svg", OUTPUT_DIR, fig=fig)


# ── Chart 8c: Power-law small multiples (one panel per system) ────────────────

def plot_powerlaw_small_multiples(df: pd.DataFrame, systems: list[str],
                                  top_n: int = 50) -> str:
    """One small log-log panel per system so straight vs bent is obvious.

    Each panel plots a system's top-N value-vs-rank (dots) against its fitted
    power law (line) on log-log axes. Power-law systems (fit clears
    POWERLAW_R2_THRESHOLD) are blue; the benders are grey. Panels are ordered by
    exponent, steepest first, so the concentration ordering reads left to right.
    """
    from player_rating_overview_data import powerlaw_fit, POWERLAW_R2_THRESHOLD

    qual = df[df.get("QUALIFIED", pd.Series(True, index=df.index)) == True].copy()

    # Fit every present system, keep those with a fit, order by steepness.
    fits = []
    for sys in systems:
        if sys not in qual.columns:
            continue
        vals = qual[sys].dropna().sort_values(ascending=False).reset_index(drop=True)
        fit = powerlaw_fit(vals.values, top_n=top_n)
        if fit is not None:
            fits.append((sys, vals, fit))
    fits.sort(key=lambda t: t[2]["alpha"], reverse=True)

    n = len(fits)
    if n == 0:
        fig, ax = plt.subplots(figsize=(6, 4), facecolor=BG)
        ax.text(0.5, 0.5, "No data", ha="center", va="center",
                transform=ax.transAxes, color=GRAY)
        return save_chart("powerlaw_small_multiples.svg", OUTPUT_DIR, fig=fig)

    ncols = 4
    nrows = (n + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols, figsize=(11, 3.0 * nrows),
                             facecolor=BG, squeeze=False)

    for idx, (sys, vals, fit) in enumerate(fits):
        ax = axes[idx // ncols][idx % ncols]
        ax.set_facecolor(PANEL)
        rank = np.arange(1, fit["n_points"] + 1)
        obs = vals.iloc[:fit["n_points"]].values
        is_power = fit["r2"] >= POWERLAW_R2_THRESHOLD
        color = BLUE if is_power else GRAY
        ax.plot(rank, obs, "o", color=color, markersize=3.5, alpha=0.85, zorder=3)
        fit_line = np.exp(fit["log_c"]) * rank ** (-fit["alpha"])
        ax.plot(rank, fit_line, "-", color=color, linewidth=1.3, alpha=0.9, zorder=2)
        ax.set_xscale("log")
        ax.set_yscale("log")
        verdict = "power law" if is_power else "bends"
        ax.set_title(f"{SYSTEM_LABELS.get(sys, sys)}: {verdict}\n"
                     f"α={fit['alpha']:.2f}, straight-line fit {fit['r2']:.2f}",
                     fontsize=9, color="#222")
        ax.grid(True, which="both", color="#e0dfd8", linewidth=0.5, zorder=0)
        ax.tick_params(labelsize=7, colors=GRAY)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    # Blank any unused panels in the grid.
    for idx in range(n, nrows * ncols):
        axes[idx // ncols][idx % ncols].axis("off")

    fig.suptitle("A power law is a straight line; a bent line has a natural size to its top tier",
                 fontsize=11, color="#222", y=1.0)
    fig.supxlabel("Player rank, log scale", fontsize=9, color=GRAY)
    fig.supylabel("Value, log scale", fontsize=9, color=GRAY)
    fig.tight_layout()
    return save_chart("powerlaw_small_multiples.svg", OUTPUT_DIR, fig=fig)


# ── Chart 8d: Distribution shape (rate metric vs accumulation metric) ─────────

def plot_distribution_shape(df: pd.DataFrame, rate_sys: str = "RAPM",
                            accum_sys: str = "VORP") -> str:
    """Full-distribution histograms contrasting a rate metric with an accumulation metric.

    The power-law charts (8b/8c) only look at the positive top-50 tail. This
    panel shows the whole distribution, which is where the difference in shape
    lives. RAPM (a per-100 rate) is a near-symmetric bell, so its top and bottom
    are mirror images and there is no heavy tail for a power law to sit in. VORP
    (a rate times minutes) is right-skewed: a long tail of high-value stars. That
    skew, not the sign, is the power-law signature. A normal curve is overlaid on
    each so "symmetric" vs "skewed" reads at a glance.
    """
    qual = df[df.get("QUALIFIED", pd.Series(True, index=df.index)) == True].copy()

    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), facecolor=BG)

    panels = [
        (rate_sys, BLUE, "near-symmetric bell, no heavy tail"),
        (accum_sys, GRAY, "right-skewed, a long tail of stars"),
    ]
    for ax, (sys, color, blurb) in zip(axes, panels):
        ax.set_facecolor(PANEL)
        if sys not in qual.columns or qual[sys].dropna().shape[0] < 5:
            ax.text(0.5, 0.5, f"No {sys} data", ha="center", va="center",
                    transform=ax.transAxes, color=GRAY)
            continue
        vals = qual[sys].dropna().values
        mean, std = float(vals.mean()), float(vals.std())
        ax.hist(vals, bins=30, density=True, color=color, alpha=0.55,
                edgecolor="white", linewidth=0.4, zorder=2)
        if std > 0:
            xs = np.linspace(vals.min(), vals.max(), 200)
            ax.plot(xs, stats.norm.pdf(xs, mean, std), color="#222",
                    linewidth=1.3, alpha=0.8, zorder=3, label="normal curve")
        skew = float(stats.skew(vals))
        exkurt = float(stats.kurtosis(vals))
        ax.set_title(f"{SYSTEM_LABELS.get(sys, sys)}: {blurb}", fontsize=10, color="#222")
        ax.text(0.97, 0.95,
                f"skew {skew:+.2f}\nexcess kurtosis {exkurt:+.2f}",
                transform=ax.transAxes, ha="right", va="top", fontsize=8,
                color=GRAY,
                bbox=dict(boxstyle="round", fc="white", ec="#ddd", alpha=0.85))
        ax.set_xlabel("Value", fontsize=9, color=GRAY)
        ax.tick_params(labelsize=8, colors=GRAY)
        ax.grid(axis="y", color="#e0dfd8", linewidth=0.6, zorder=0)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        ax.legend(fontsize=7.5, frameon=False, loc="upper left")

    axes[0].set_ylabel("Share of qualified player-seasons", fontsize=9, color=GRAY)
    fig.suptitle(
        "RAPM is symmetric, so it has no heavy tail to be a power law; VORP is right-skewed",
        fontsize=11, color="#222", y=1.0)
    fig.tight_layout()
    return save_chart("distribution_shape.svg", OUTPUT_DIR, fig=fig)


# ── Chart 9: Top-20 per system table ─────────────────────────────────────────

def _score_fmt(val: float, sys: str) -> str:
    """Format a raw score for display in the top-20 table."""
    if sys in ("MVP_SHARE", "WS48"):
        return f"{val:.3f}"
    if sys == "ALL_NBA_PTS":
        return f"{val:.0f}"
    if sys in ("CONSENSUS", "WINS_PRED"):
        return f"{val:.2f}"
    return f"{val:.1f}"


def plot_top20_table(df: pd.DataFrame, systems: list[str]) -> str:
    """Grid of mini-tables: top-20 players and their raw score for each system.

    One row per category group; systems within the group fill columns left to right.
    Groups: Rate/Efficiency · Accumulated Value · Directional · RAPM · RAPM+prior · Uber.
    Highlights rank 1 (blue) and rank 20 (red). The # column appears only in
    the leftmost table of each row.
    """
    qual = df[df.get("QUALIFIED", pd.Series(True, index=df.index)) == True].copy()
    present_set = {s for s in systems if s in qual.columns and qual[s].notna().sum() >= 20}

    if not present_set:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return save_chart("top20_by_system.svg", OUTPUT_DIR, fig=fig)

    GROUPS = [
        ("Rate / Efficiency", ["GAME_SCORE", "PER", "WS48"],   "#2176ae"),
        ("Accumulated Value", ["WS", "BPM", "VORP"],           "#2e9e6e"),
        ("Directional",       ["OBPM", "DBPM"],                "#8c5e99"),
        ("RAPM",              ["RAPM", "O_RAPM", "D_RAPM"],    "#1f8a5b"),
        ("RAPM + prior",      ["RAPM_MY", "O_RAPM_MY", "D_RAPM_MY"], "#3fae84"),
        ("Uber Ratings",      ["CONSENSUS", "WINS_PRED"],      "#5d6d7e"),
    ]

    # Keep only groups that have at least one present system; add ungrouped at end
    grouped = set()
    active_groups = []
    for gname, gsystems, gcolor in GROUPS:
        members = [s for s in gsystems if s in present_set]
        if members:
            active_groups.append((gname, members, gcolor))
            grouped.update(members)
    leftover = [s for s in systems if s in present_set and s not in grouped]
    if leftover:
        active_groups.append(("Other", leftover, BLUE))

    nrows = len(active_groups)
    ncols = max(len(g[1]) for g in active_groups)

    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(ncols * 4.0, nrows * 5.5),
                             facecolor=BG)
    # Normalize axes to 2-D array shape [nrows][ncols]
    if nrows == 1 and ncols == 1:
        axes = [[axes]]
    elif nrows == 1:
        axes = [list(axes)]
    elif ncols == 1:
        axes = [[ax] for ax in axes]
    else:
        axes = [list(row) for row in axes]

    RANK1_COLOR = "#d4e8fb"
    RANK20_COLOR = "#fdecea"
    HEADER_FG = "white"

    for row_idx, (gname, gsystems, gcolor) in enumerate(active_groups):
        for col_idx in range(ncols):
            ax = axes[row_idx][col_idx]
            ax.axis("off")
            if col_idx >= len(gsystems):
                continue

            sys = gsystems[col_idx]
            top20 = (qual[["PLAYER_NAME", sys]]
                     .dropna()
                     .nlargest(20, sys)
                     .reset_index(drop=True))

            col_label = SYSTEM_LABELS.get(sys, sys)
            show_rank = (col_idx == 0)
            if show_rank:
                cell_text = [
                    [str(idx + 1), row["PLAYER_NAME"].split()[-1], _score_fmt(row[sys], sys)]
                    for idx, row in top20.iterrows()
                ]
                col_labels = ["#", "Player", col_label]
                ncell = 3
            else:
                cell_text = [
                    [row["PLAYER_NAME"].split()[-1], _score_fmt(row[sys], sys)]
                    for idx, row in top20.iterrows()
                ]
                col_labels = ["Player", col_label]
                ncell = 2

            table = ax.table(
                cellText=cell_text,
                colLabels=col_labels,
                loc="center",
                cellLoc="left",
            )
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1.0, 1.2)

            for col in range(ncell):
                cell = table[(0, col)]
                cell.set_facecolor(gcolor)
                cell.set_text_props(color=HEADER_FG, fontweight="bold")

            for col in range(ncell):
                table[(1, col)].set_facecolor(RANK1_COLOR)
            if len(cell_text) >= 20:
                for col in range(ncell):
                    table[(20, col)].set_facecolor(RANK20_COLOR)

            # Group label above the first table in each row
            if col_idx == 0:
                ax.set_title(gname, fontsize=10, color=gcolor, fontweight="bold",
                             pad=6, loc="left")

    fig.suptitle("Top 20 players by each rating system — 2025-26",
                 fontsize=12, color="#222", y=1.01)
    fig.tight_layout()
    return save_chart("top20_by_system.svg", OUTPUT_DIR, fig=fig)


# ── Chart: retrodiction — which rating rebuilds team results ─────────────────

def plot_retrodiction(retro: dict, outcome_calibrated: set) -> str:
    """Bar chart of each system's leave-one-team-out retrodiction R².

    retro is {system: {"r2", "cv_r2", "n"}}. Bars are the cross-validated R²,
    sorted high to low. Outcome-blind systems (the genuine test) are drawn in
    blue; team-fit systems (built from team/lineup results, so a high score is
    partly mechanical) are muted grey. A faint tick marks each system's
    in-sample R² so the overfit gap is visible.
    """
    if not retro:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "No retrodiction data", ha="center", va="center",
                transform=ax.transAxes)
        return save_chart("retrodiction.svg", OUTPUT_DIR, fig=fig)

    ranked = sorted(retro.items(), key=lambda kv: -kv[1]["cv_r2"])
    systems = [s for s, _ in ranked]
    cv = [retro[s]["cv_r2"] for s in systems]
    insample = [retro[s]["r2"] for s in systems]
    labels = [SYSTEM_LABELS.get(s, s) for s in systems]
    colors = [GRAY if s in outcome_calibrated else BLUE for s in systems]

    fig, ax = plt.subplots(figsize=(max(6, len(systems) * 0.95), 5), facecolor=BG)
    ax.set_facecolor(PANEL)
    x = np.arange(len(systems))
    ax.bar(x, cv, color=colors, alpha=0.85, zorder=3)
    # In-sample R² ticks (overfit gap above each bar)
    ax.scatter(x, insample, marker="_", s=220, color="#444", linewidths=1.4,
               zorder=4, label="in-sample R²")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=9)
    ax.set_ylabel("Out-of-sample R² (leave-one-team-out)", fontsize=9, color=GRAY)
    ax.set_ylim(0, 1)
    ax.set_title(
        "An outcome-blind rating rebuilds team results best",
        fontsize=12, color="#222", pad=26
    )
    ax.text(0.5, 1.015,
            "How well each system, summed to the team, rebuilds 2025-26 point "
            "differential. Blue = never uses who won; grey = built from team/lineup results",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=7.5, color=GRAY)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)
    ax.legend(loc="upper right", fontsize=8, frameon=False)

    fig.tight_layout()
    return save_chart("retrodiction.svg", OUTPUT_DIR, fig=fig)


# ── Chart: describe vs predict (same-season vs next-season retrodiction) ─────

def plot_next_season_retrodiction(same: dict, nxt: dict) -> str:
    """Grouped bars: each system's same-season fit vs its next-season forecast.

    `same` is the same-season retrodiction dict ({system: {cv_r2, ...}}); `nxt`
    is the next-season dict ({system: {r2, ...}}). Bars are paired per system,
    sorted by next-season R². The muted grey bar is how well the system
    describes the season just played; the blue bar is how well last season's
    version forecasts this one. The gap is the overfit/descriptive premium.
    """
    if not nxt or not same:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "No next-season data", ha="center", va="center",
                transform=ax.transAxes)
        return save_chart("next_season_retrodiction.svg", OUTPUT_DIR, fig=fig)

    systems = [s for s, _ in sorted(nxt.items(), key=lambda kv: -kv[1]["r2"])
               if s in same]
    describe = [same[s]["cv_r2"] for s in systems]
    predict = [nxt[s]["r2"] for s in systems]
    labels = [SYSTEM_LABELS.get(s, s) for s in systems]

    fig, ax = plt.subplots(figsize=(max(6, len(systems) * 1.0), 5), facecolor=BG)
    ax.set_facecolor(PANEL)
    x = np.arange(len(systems))
    w = 0.4
    ax.bar(x - w / 2, describe, w, color=LGRAY, alpha=0.95,
           label="describes the season (same year)", zorder=3)
    ax.bar(x + w / 2, predict, w, color=BLUE, alpha=0.9,
           label="forecasts the next season", zorder=3)

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=9)
    ax.set_ylabel("R² for team point differential", fontsize=9, color=GRAY)
    ax.set_ylim(0, 1)
    ax.set_title(
        "The best description of a season is not the best forecast of the next",
        fontsize=11.5, color="#222", pad=26
    )
    ax.text(0.5, 1.015,
            "Grey: how well each system rebuilds the same season. Blue: how well last "
            "season's version predicts this one (2024-25 to 2025-26)",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=7.5, color=GRAY)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)
    ax.legend(loc="upper right", fontsize=8, frameon=False)

    fig.tight_layout()
    return save_chart("next_season_retrodiction.svg", OUTPUT_DIR, fig=fig)


def plot_panel_describe_vs_forecast(
        panel: dict,
        out_name: str = "panel_describe_vs_forecast.svg") -> str:
    """Pooled describe-vs-forecast across every season-pair in the cache.

    `panel` is the dict from analysis.panel_retrodiction: {"describe": {sys:
    [r2,...]}, "forecast": {sys: [r2,...]}, "seasons": [...], "pairs": [...]}.
    Each system gets a paired bar: grey is its average same-season fit (describe)
    over all seasons, blue is its average next-season forecast over all pairs.
    Whiskers span the season-to-season range, so a reader sees the flip is the
    standing pattern, not one year's bounce. Systems are sorted by forecast mean.
    """
    describe, forecast = panel.get("describe", {}), panel.get("forecast", {})
    systems = [s for s in forecast
               if forecast[s] and describe.get(s)]
    if not systems:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "No panel data", ha="center", va="center",
                transform=ax.transAxes)
        return save_chart(out_name, OUTPUT_DIR, fig=fig)

    f_mean = {s: float(np.mean(forecast[s])) for s in systems}
    systems.sort(key=lambda s: -f_mean[s])
    d_mean = [float(np.mean(describe[s])) for s in systems]
    p_mean = [f_mean[s] for s in systems]
    d_err = [[m - min(describe[s]) for s, m in zip(systems, d_mean)],
             [max(describe[s]) - m for s, m in zip(systems, d_mean)]]
    p_err = [[m - min(forecast[s]) for s, m in zip(systems, p_mean)],
             [max(forecast[s]) - m for s, m in zip(systems, p_mean)]]
    labels = [SYSTEM_LABELS.get(s, s) for s in systems]

    fig, ax = plt.subplots(figsize=(max(6, len(systems) * 1.0), 5), facecolor=BG)
    ax.set_facecolor(PANEL)
    x = np.arange(len(systems))
    w = 0.4
    ax.bar(x - w / 2, d_mean, w, yerr=d_err, color=LGRAY, alpha=0.95,
           ecolor=GRAY, capsize=3, error_kw={"linewidth": 0.8},
           label="describes the season (same year)", zorder=3)
    ax.bar(x + w / 2, p_mean, w, yerr=p_err, color=BLUE, alpha=0.9,
           ecolor="#1f5fa6", capsize=3, error_kw={"linewidth": 0.8},
           label="forecasts the next season", zorder=3)

    seasons = panel.get("seasons", [])
    n_seasons = len(seasons)
    n_pairs = len(panel.get("pairs", []))

    def _season_label(y: int) -> str:
        return f"{y - 1}-{str(y)[-2:]}"
    span = (f"{_season_label(min(seasons))} to {_season_label(max(seasons))}"
            if seasons else "")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=40, ha="right", fontsize=9)
    ax.set_ylabel("R² for team point differential", fontsize=9, color=GRAY)
    ax.set_ylim(0, 1)
    ax.set_title(
        "Describing a season and forecasting the next reward different metrics",
        fontsize=11.5, color="#222", pad=26
    )
    ax.text(0.5, 1.015,
            f"Averages across {n_seasons} seasons (describe) and {n_pairs} season-pairs "
            f"(forecast), {span}. Whiskers span the season-to-season range",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=7.5, color=GRAY)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)
    ax.legend(loc="upper right", fontsize=8, frameon=False)

    fig.tight_layout()
    return save_chart(out_name, OUTPUT_DIR, fig=fig)


def plot_rating_stability(stab: dict, top_n: int = 20, chance: float | None = None) -> str:
    """Two panels of year-over-year stability, one bar per box-score system.

    `stab` is the dict from analysis.rating_stability: {"corr": {sys: [r,...]},
    "retention": {sys: [share,...]}, "pairs": [...]}. Left panel is each
    system's average season-to-season rating correlation (whiskers span the
    pair-to-pair range); right panel is the share of its top-`top_n` players who
    stay top-`top_n` the next season, with a dashed line at the chance level.
    Systems are sorted by correlation, steadiest on top.
    """
    corr, ret = stab.get("corr", {}), stab.get("retention", {})
    systems = [s for s in corr if corr[s] and ret.get(s)]
    if not systems:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "No stability data", ha="center", va="center",
                transform=ax.transAxes)
        return save_chart("rating_stability.svg", OUTPUT_DIR, fig=fig)

    c_mean = {s: float(np.mean(corr[s])) for s in systems}
    systems.sort(key=lambda s: c_mean[s])  # ascending so steadiest ends on top
    labels = [SYSTEM_LABELS.get(s, s) for s in systems]
    cm = [c_mean[s] for s in systems]
    c_err = [[m - min(corr[s]) for s, m in zip(systems, cm)],
             [max(corr[s]) - m for s, m in zip(systems, cm)]]
    rm = [float(np.mean(ret[s])) for s in systems]
    y = np.arange(len(systems))

    fig, (axc, axr) = plt.subplots(
        1, 2, figsize=(10, max(3.5, len(systems) * 0.55)),
        facecolor=BG, sharey=True)
    for ax in (axc, axr):
        ax.set_facecolor(PANEL)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

    axc.barh(y, cm, color=BLUE, alpha=0.9, xerr=c_err, ecolor=GRAY,
             capsize=3, error_kw={"linewidth": 0.8}, zorder=3)
    axc.set_yticks(y)
    axc.set_yticklabels(labels, fontsize=9)
    axc.set_xlim(0, 1)
    axc.set_xlabel("year-to-year rating correlation", fontsize=8.5, color=GRAY)
    axc.set_title("How sticky each rating is", fontsize=10, color="#222")
    axc.grid(axis="x", color="#e0dfd8", linewidth=0.7, zorder=0)

    axr.barh(y, [v * 100 for v in rm], color=GRAY, alpha=0.85, zorder=3)
    axr.set_xlim(0, 100)
    axr.set_xlabel(f"top-{top_n} players kept the next season (%)", fontsize=8.5, color=GRAY)
    axr.set_title(f"Same names in the top {top_n}", fontsize=10, color="#222")
    axr.grid(axis="x", color="#e0dfd8", linewidth=0.7, zorder=0)
    if chance is not None:
        axr.axvline(chance * 100, color=RED, linestyle="--", linewidth=1, zorder=4)
        axr.text(chance * 100 + 1.5, len(systems) - 0.4, "chance",
                 color=RED, fontsize=7.5, va="center")

    prs = stab.get("pairs", [])
    n_pairs = len(prs)
    span = ""
    if prs:
        first, last = min(p[0] for p in prs), max(p[1] for p in prs)
        span = f" ({first - 1}-{str(first)[-2:]} to {last - 1}-{str(last)[-2:]})"
    fig.suptitle("Simple box scores are the steadiest player ratings season to season",
                 fontsize=11.5, color="#222", x=0.5, y=1.0)
    fig.text(0.5, 0.965,
             f"Across {n_pairs} season-pairs{span}, among players who qualified in "
             f"both. Whiskers span the pair-to-pair range",
             ha="center", va="bottom", fontsize=7.5, color=GRAY)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    return save_chart("rating_stability.svg", OUTPUT_DIR, fig=fig)


# ── Chart: regular-season vs playoff risers and fallers ──────────────────────

def plot_playoff_shift(deltas: pd.DataFrame, top_n: int = 10) -> str:
    """Diverging bar chart of the biggest playoff risers and fallers.

    Expects the frame from load_playoff_deltas(), which carries the composite
    SHIFT_Z column. Shows the top_n risers (green) and top_n fallers (red) by
    that score. The bar length is the composite shift z; the players who agreed
    across PER, WS/48, and BPM the most sit at the ends.
    """
    if deltas is None or deltas.empty or "SHIFT_Z" not in deltas.columns:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "No playoff data", ha="center", va="center",
                transform=ax.transAxes)
        return save_chart("playoff_shift.svg", OUTPUT_DIR, fig=fig)

    risers = deltas.nlargest(top_n, "SHIFT_Z")
    fallers = deltas.nsmallest(top_n, "SHIFT_Z")
    sel = pd.concat([fallers, risers]).drop_duplicates(subset="PLAYER_NAME")
    sel = sel.sort_values("SHIFT_Z")

    names = sel["PLAYER_NAME"].tolist()
    teams = sel.get("TEAM_ABBREVIATION", pd.Series([""] * len(sel))).tolist()
    vals = sel["SHIFT_Z"].tolist()
    colors = [GREEN if v > 0 else RED for v in vals]

    fig, ax = plt.subplots(figsize=(7.5, max(5, len(sel) * 0.34)), facecolor=BG)
    ax.set_facecolor(PANEL)
    y = np.arange(len(sel))
    ax.barh(y, vals, color=colors, alpha=0.85, zorder=3)
    ax.axvline(0, color="#444", linewidth=0.9, zorder=4)

    ax.set_yticks(y)
    ax.set_yticklabels([f"{n}  ({t})" if t else n for n, t in zip(names, teams)],
                       fontsize=8)
    ax.set_xlabel("Composite playoff shift (z-score; agreement of PER, WS/48, BPM)",
                  fontsize=9, color=GRAY)
    ax.set_title(
        "Who rose and who fell in the 2025-26 playoffs",
        fontsize=12, color="#222", pad=24
    )
    ax.text(0.5, 1.01,
            "Box-score rate metrics, playoff vs regular season, "
            "players with 150+ playoff minutes",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=8, color=GRAY)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color="#e0dfd8", linewidth=0.7, zorder=0)

    fig.tight_layout()
    return save_chart("playoff_shift.svg", OUTPUT_DIR, fig=fig)


# ── Chart: season-over-season consensus movers ───────────────────────────────

def plot_season_comparison(comp: dict, top_n: int = 8) -> str:
    """Diverging bars of the biggest consensus risers and fallers between two seasons.

    Expects the dict from season_comparison(): a `movers` frame carrying the
    per-player consensus change (`delta`) between the two seasons. Shows the
    top_n climbers (green) and top_n sliders (red) by that change, read as a
    snapshot of how much the single-season order moves year to year.
    """
    movers = comp.get("movers") if comp else None
    if movers is None or len(movers) == 0:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "No comparison data", ha="center", va="center",
                transform=ax.transAxes)
        return save_chart("season_comparison.svg", OUTPUT_DIR, fig=fig)

    risers = movers.nlargest(top_n, "delta")
    fallers = movers.nsmallest(top_n, "delta")
    sel = (pd.concat([fallers, risers]).drop_duplicates(subset="player_id")
           .sort_values("delta"))
    names = sel["PLAYER_NAME"].tolist()
    vals = sel["delta"].tolist()
    colors = [GREEN if v > 0 else RED for v in vals]
    la, lb = comp.get("label_a", ""), comp.get("label_b", "")

    fig, ax = plt.subplots(figsize=(7.5, max(5, len(sel) * 0.34)), facecolor=BG)
    ax.set_facecolor(PANEL)
    y = np.arange(len(sel))
    ax.barh(y, vals, color=colors, alpha=0.85, zorder=3)
    ax.axvline(0, color="#444", linewidth=0.9, zorder=4)
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8)
    ax.set_xlabel(f"Change in consensus rating (z-score), {la} → {lb}",
                  fontsize=9, color=GRAY)
    ax.set_title(
        f"Who climbed and who slid in the consensus, {la} to {lb}",
        fontsize=12, color="#222", pad=24
    )
    ax.text(0.5, 1.01,
            "Players qualified in both seasons; change in standardized consensus standing",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=8, color=GRAY)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color="#e0dfd8", linewidth=0.7, zorder=0)

    fig.tight_layout()
    return save_chart("season_comparison.svg", OUTPUT_DIR, fig=fig)


# ── Chart: playoff-weighted value dumbbell (regular season vs playoff BPM) ────

BRUNSON_PLAYER_ID = 1628973


def plot_playoff_weighted_value(deltas: pd.DataFrame, top_n: int = 12,
                                highlight_id: int = BRUNSON_PLAYER_ID) -> str:
    """Dumbbell of regular-season vs playoff BPM for the top playoff-weighted-value players.

    Expects the frame from load_playoff_deltas() (BPM_reg, BPM_po, MIN_reg, MIN_po).
    Computes playoff_weighted_value(), the minutes-weighted blend of regular-season
    and playoff BPM in which a playoff minute counts PLAYOFF_VALUE_WEIGHT times a
    regular-season minute, and shows the top_n players by that blend. Each row is a
    line from the regular-season BPM (blue dot) to the playoff BPM (green dot), so
    a rightward line reads as a player who raised his game in the postseason.
    Jalen Brunson (highlight_id) is called out in bold; every other label is muted
    grey, since he is the argument: the playoff weighting lifts him into this top
    class without vaulting him past the league's clear top tier.
    """
    if deltas is None or deltas.empty or "BPM_reg" not in deltas.columns:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "No playoff data", ha="center", va="center",
                transform=ax.transAxes)
        return save_chart("playoff_weighted_value.svg", OUTPUT_DIR, fig=fig)

    df = deltas.copy()
    df["PWV"] = playoff_weighted_value(df)
    ranked = df.sort_values("PWV", ascending=False).reset_index(drop=True)
    sel = ranked.head(top_n).sort_values("PWV")  # ascending so the best plots at top

    names = sel["PLAYER_NAME"].tolist()
    reg = sel["BPM_reg"].tolist()
    po = sel["BPM_po"].tolist()
    ids = sel["PLAYER_ID"].tolist()

    fig, ax = plt.subplots(figsize=(7.5, max(5, len(sel) * 0.4)), facecolor=BG)
    ax.set_facecolor(PANEL)
    y = np.arange(len(sel))

    for yi, r, p in zip(y, reg, po):
        ax.plot([r, p], [yi, yi], color=GRAY, linewidth=1.6, alpha=0.6, zorder=2)
    ax.scatter(reg, y, color=BLUE, s=55, zorder=3, label="Regular-season BPM")
    ax.scatter(po, y, color=GREEN, s=55, zorder=3, label="Playoff BPM")

    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=8.5)
    for tick, pid in zip(ax.get_yticklabels(), ids):
        if pid == highlight_id:
            tick.set_color("#222")
            tick.set_fontweight("bold")
        else:
            tick.set_color(GRAY)

    ax.axvline(0, color="#ccc", linewidth=0.8, zorder=1)
    ax.set_xlabel("BPM (points per 100 possessions vs. an average player)",
                  fontsize=9, color=GRAY)
    ax.set_title(
        "Brunson raised his game in the playoffs, but not into the top five",
        fontsize=12, color="#222", pad=26
    )
    ax.text(0.5, 1.01,
            "Regular-season vs playoff BPM, top "
            f"{len(sel)} players by playoff-weighted value "
            f"(postseason minutes count {PLAYOFF_VALUE_WEIGHT}x toward the blend)",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=8, color=GRAY)
    ax.legend(loc="lower right", fontsize=8, frameon=False)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.grid(axis="x", color="#e0dfd8", linewidth=0.7, zorder=0)

    fig.tight_layout()
    return save_chart("playoff_weighted_value.svg", OUTPUT_DIR, fig=fig)


# ── Chart: RAPM split-half reliability by minutes ────────────────────────────

def plot_rapm_reliability(rel: dict) -> str:
    """Split-half reliability of our computed RAPM, by minutes played.

    Expects the dict from data.rapm_reliability(): {"by_bin": [{"lo", "hi",
    "n", "r"}, ...], "splithalf": r, "min_minutes": int, "n_splithalf": int,
    "yoy": {"RAPM": r, "RAPM_MY": r, "BPM": r}}. Plots split-half r (correlating
    RAPM fit independently on two halves of the same pooled possessions)
    against each minutes bin, against a reference line at 0.5 for what a
    reliable metric looks like. A real player-quality signal should climb
    toward that line as more minutes accumulate; here it does not.
    """
    by_bin = rel.get("by_bin", [])
    if not by_bin:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "No RAPM reliability data", ha="center", va="center",
                transform=ax.transAxes)
        return save_chart("rapm_reliability.svg", OUTPUT_DIR, fig=fig)

    labels = [f"{b['lo']}-{b['hi']}" for b in by_bin]
    mids = np.arange(len(by_bin))
    rs = [b["r"] for b in by_bin]

    fig, ax = new_fig(figsize=(8.5, 5))
    style_axes(ax)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)
    ax.grid(axis="x", visible=False)

    ax.axhline(0.5, color=GRAY, linestyle="--", linewidth=1.2, zorder=2)
    ax.text(len(by_bin) - 1, 0.52, "what a reliable metric looks like",
            ha="right", va="bottom", fontsize=8, color=GRAY)
    ax.axhline(0, color="#ccc", linewidth=0.8, zorder=1)

    ax.plot(mids, rs, color=BLUE, linewidth=2, marker="o", markersize=6,
            zorder=3)
    for x, r, b in zip(mids, rs, by_bin):
        if not np.isnan(r):
            ax.text(x, r - 0.06, f"{r:.2f}", ha="center", va="top",
                    fontsize=8, color=BLUE)

    ax.set_xticks(mids)
    ax.set_xticklabels(labels, fontsize=9)
    ax.set_xlabel("season minutes played", fontsize=9, color=GRAY)
    ax.set_ylabel("split-half reliability (r)", fontsize=9, color=GRAY)
    ax.set_ylim(-0.1, 1.0)

    ax.set_title(
        "Our RAPM barely reproduces itself: reliability stays near zero at "
        "every minute level",
        fontsize=11.5, color="#222", pad=30
    )
    yoy = rel.get("yoy", {})
    yoy_note = ""
    if "RAPM" in yoy and "BPM" in yoy:
        yoy_note = (f" Year over year, RAPM tracks itself at r={yoy['RAPM']:.2f} "
                    f"vs. BPM's r={yoy['BPM']:.2f}.")
    ax.text(0.5, 1.01,
            "Two independent halves of the same possession data, correlation "
            "of the resulting player ratings; a real metric climbs with "
            f"minutes.{yoy_note}",
            transform=ax.transAxes, ha="center", va="bottom", fontsize=8, color=GRAY)

    fig.tight_layout()
    return save_chart("rapm_reliability.svg", OUTPUT_DIR, fig=fig)
