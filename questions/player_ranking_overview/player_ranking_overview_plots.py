"""
player_ranking_overview_plots.py — all visualizations for the player ranking overview.

Each plot_* function saves an SVG to generated/images/ and returns the path.
No data logic lives here; all computation is done by player_ranking_overview_data.py.

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
                                   systems: list[str]) -> str:
    """Rank-value (log rank vs. value) plot for cumulative-value metrics.

    Shows whether the value distribution has a heavy right tail.
    Title: 'Cumulative metrics have a heavy tail; rate metrics do not.'
    """
    qual = df[df.get("QUALIFIED", pd.Series(True, index=df.index)) == True].copy()

    # Separate rate metrics from cumulative-value metrics
    rate_systems = [s for s in systems if s in ("PER", "BPM", "OBPM", "DBPM",
                                                  "RAPTOR", "DARKO_DPM", "EPM",
                                                  "LEBRON", "ESPN_RPM", "GAME_SCORE")]
    cum_systems = [s for s in systems if s in ("WS", "VORP", "RAPTOR_WAR")]

    groups = [
        ("Cumulative value metrics", cum_systems),
        ("Rate metrics (per 100 possessions or per game)", rate_systems),
    ]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5), facecolor=BG)

    for ax, (title, sys_list) in zip(axes, groups):
        ax.set_facecolor(PANEL)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plotted = 0
        for sys in sys_list:
            if sys not in qual.columns:
                continue
            vals = qual[sys].dropna().sort_values(ascending=False).reset_index(drop=True)
            if len(vals) < 10:
                continue
            ranks = np.arange(1, len(vals) + 1)
            color = SYSTEM_COLORS.get(sys, GRAY)
            ax.plot(np.log10(ranks), vals.values,
                    color=color, linewidth=1.5, alpha=0.75,
                    label=SYSTEM_LABELS.get(sys, sys))
            plotted += 1

        if plotted == 0:
            ax.text(0.5, 0.5, "No data", ha="center", va="center",
                    transform=ax.transAxes, color=GRAY)
        else:
            ax.legend(fontsize=8, frameon=False)

        ax.set_xlabel("Log₁₀ rank", fontsize=9, color=GRAY)
        ax.set_ylabel("Rating value", fontsize=9, color=GRAY)
        ax.set_title(title, fontsize=10, color="#333")
        ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)

    fig.suptitle("Cumulative metrics have a heavy tail; rate metrics do not",
                 fontsize=12, y=1.01, color="#222")
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

    # Color: top-5 highlighted, rest muted
    colors = [BLUE if r <= 5 else GRAY for r in ranks]
    bars = ax.bar(ranks, vals, color=colors, alpha=0.85, width=0.8, zorder=3)

    # Label the top 5 player names
    for i, (bar, name) in enumerate(zip(bars[:5], names[:5])):
        ax.text(bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(vals) * 0.01,
                name.split()[-1], ha="center", va="bottom",
                fontsize=7.5, color=BLUE)

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

def plot_gini_by_system(gini_scores: dict[str, float]) -> str:
    """Bar chart of Gini coefficients across systems.

    A high Gini means value is concentrated at the top (heavy tail).
    Title: 'Cumulative metrics show more concentrated star value than rate metrics.'
    """
    if not gini_scores:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return save_chart("gini_by_system.svg", OUTPUT_DIR, fig=fig)

    systems = list(gini_scores.keys())
    vals = [gini_scores[s] for s in systems]
    colors = [SYSTEM_COLORS.get(s, GRAY) for s in systems]
    labels = [SYSTEM_LABELS.get(s, s) for s in systems]

    order = np.argsort(vals)[::-1]
    fig, ax = plt.subplots(figsize=(max(6, len(systems) * 0.9), 5), facecolor=BG)
    ax.set_facecolor(PANEL)

    ax.bar(range(len(systems)),
           [vals[i] for i in order],
           color=[colors[i] for i in order],
           alpha=0.85)
    ax.set_xticks(range(len(systems)))
    ax.set_xticklabels([labels[i] for i in order], rotation=40, ha="right", fontsize=9)
    ax.set_ylabel("Gini coefficient", fontsize=9, color=GRAY)
    ax.set_title(
        "Cumulative metrics show more concentrated star value than rate metrics",
        fontsize=11, color="#222"
    )
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)

    fig.tight_layout()
    return save_chart("gini_by_system.svg", OUTPUT_DIR, fig=fig)


# ── Chart 8: All systems on one normalized distribution line ─────────────────

def plot_all_systems_distributions(df: pd.DataFrame, systems: list[str],
                                   top_n: int = 50) -> str:
    """Normalized rank-value lines for every present system on one chart.

    Each system's values are z-scored (mean 0, std 1) across qualified players,
    then sorted descending. Plots rank 1–top_n on the x-axis vs z-score on y.
    Puts all methodologies on a common scale so their shapes can be compared.
    """
    qual = df[df.get("QUALIFIED", pd.Series(True, index=df.index)) == True].copy()

    fig, ax = plt.subplots(figsize=(11, 6), facecolor=BG)
    ax.set_facecolor(PANEL)

    plotted = []
    for sys in systems:
        if sys not in qual.columns:
            continue
        vals = qual[sys].dropna().sort_values(ascending=False).reset_index(drop=True)
        if len(vals) < top_n:
            continue
        vals = vals.iloc[:top_n]
        mean, std = vals.mean(), vals.std()
        if std == 0:
            continue
        z = (vals - mean) / std
        color = SYSTEM_COLORS.get(sys, GRAY)
        ax.plot(np.arange(1, top_n + 1), z.values,
                color=color, linewidth=1.5, alpha=0.8,
                label=SYSTEM_LABELS.get(sys, sys))
        plotted.append(sys)

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


# ── Chart 9: Top-20 per system table ─────────────────────────────────────────

def _score_fmt(val: float, sys: str) -> str:
    """Format a raw score for display in the top-20 table."""
    if sys in ("MVP_SHARE", "WS48"):
        return f"{val:.3f}"
    if sys == "ALL_NBA_PTS":
        return f"{val:.0f}"
    return f"{val:.1f}"


def plot_top20_table(df: pd.DataFrame, systems: list[str]) -> str:
    """Grid of mini-tables: top-20 players and their raw score for each system.

    Laid out as ceil(n/5) rows × 5 columns. Highlights rank 1 and rank 20 so
    the gap between them is immediately visible.
    """
    qual = df[df.get("QUALIFIED", pd.Series(True, index=df.index)) == True].copy()
    present = [s for s in systems if s in qual.columns and qual[s].notna().sum() >= 20]

    if not present:
        fig, ax = new_fig()
        ax.text(0.5, 0.5, "No data", ha="center", va="center", transform=ax.transAxes)
        return save_chart("top20_by_system.svg", OUTPUT_DIR, fig=fig)

    ncols = min(5, len(present))
    nrows = (len(present) + ncols - 1) // ncols
    fig, axes = plt.subplots(nrows, ncols,
                             figsize=(ncols * 3.2, nrows * 5.8),
                             facecolor=BG)
    # Flatten axes to a list regardless of shape
    if nrows == 1 and ncols == 1:
        axes_flat = [axes]
    elif nrows == 1:
        axes_flat = list(axes)
    else:
        axes_flat = [ax for row in axes for ax in row]

    RANK1_COLOR = "#d4e8fb"   # light blue highlight for rank 1
    RANK20_COLOR = "#fdecea"  # light red highlight for rank 20
    HEADER_BG = BLUE
    HEADER_FG = "white"

    for i, sys in enumerate(present):
        ax = axes_flat[i]
        ax.axis("off")

        top20 = (qual[["PLAYER_NAME", sys]]
                 .dropna()
                 .nlargest(20, sys)
                 .reset_index(drop=True))

        col_label = SYSTEM_LABELS.get(sys, sys)
        cell_text = [
            [str(idx + 1),
             row["PLAYER_NAME"].split()[-1],
             _score_fmt(row[sys], sys)]
            for idx, row in top20.iterrows()
        ]

        table = ax.table(
            cellText=cell_text,
            colLabels=["#", "Player", col_label],
            loc="center",
            cellLoc="left",
        )
        table.auto_set_font_size(False)
        table.set_fontsize(7.5)
        table.scale(1.0, 1.15)

        # Header row styling
        for col in range(3):
            cell = table[(0, col)]
            cell.set_facecolor(HEADER_BG)
            cell.set_text_props(color=HEADER_FG, fontweight="bold")

        # Rank 1 highlight (table row 1 = data row 0)
        for col in range(3):
            table[(1, col)].set_facecolor(RANK1_COLOR)

        # Rank 20 highlight (table row 20 = data row 19)
        if len(cell_text) >= 20:
            for col in range(3):
                table[(20, col)].set_facecolor(RANK20_COLOR)

    # Hide any unused subplot axes
    for ax in axes_flat[len(present):]:
        ax.axis("off")

    fig.suptitle("Top 20 players by each rating system — 2024-25",
                 fontsize=12, color="#222", y=1.01)
    fig.tight_layout()
    return save_chart("top20_by_system.svg", OUTPUT_DIR, fig=fig)
