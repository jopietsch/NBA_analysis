"""
knicks_2026_plots.py — visualization for the 2026 Knicks playoff analysis.

Each plot_* function takes pre-computed frames/values, draws one figure,
and saves to generated/knicks_2026_*.svg.

Run via:  MPLBACKEND=Agg python3 knicks_2026_historic.py
"""

import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt        # noqa: E402
import matplotlib.patches as mpatches  # noqa: E402
import numpy as np                     # noqa: E402
import pandas as pd                    # noqa: E402

from knicks_2026_data import SUBJECT_YEAR, short_label, season_range_label, START_YEAR, END_YEAR
from nbakit.viz import (  # noqa: E402
    BLUE, GREEN, RED, GRAY, LGRAY, BG, PANEL,
    save_chart,
    style_axes as _style,
    new_fig as _fig,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated", "images")

# ── Team accent colors (Knicks-specific) ──────────────────────────────────────
KNICKS_BLUE   = "#006BB6"
KNICKS_ORANGE = "#F58426"

SUBJECT_LABEL = short_label(SUBJECT_YEAR)   # "25-26"


# ── 1. Champions ranked by playoff win rate ───────────────────────────────────

def plot_win_rate_ranking(champions: pd.DataFrame) -> str:
    df = champions.sort_values("win_rate").copy()
    df["label"] = df["year"].apply(lambda y: short_label(int(y)))
    colors = [KNICKS_BLUE if lbl == SUBJECT_LABEL else BLUE for lbl in df["label"]]

    fig, ax = _fig(figsize=(8, max(5, len(df) * 0.22)))
    ax.barh(range(len(df)), df["win_rate"], color=colors, edgecolor="none", zorder=2)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["label"], fontsize=7.5)
    ax.set_xlabel("Playoff win rate", fontsize=10)
    ax.set_title(
        f"NBA Champions: Playoff Win Rate  ({season_range_label(START_YEAR, END_YEAR)})",
        fontsize=11, fontweight="bold", color="#2c2c2a", pad=8,
    )
    _style(ax)

    knicks_rows = df[df["year"] == SUBJECT_YEAR]
    if not knicks_rows.empty:
        pos = df.index.get_loc(knicks_rows.index[0])
        val = float(knicks_rows["win_rate"].iloc[0])
        ax.text(val + 0.005, pos, f"{val:.3f}", va="center", fontsize=8,
                color=KNICKS_BLUE, fontweight="bold")

    handles = [
        mpatches.Patch(color=KNICKS_BLUE, label="2025-26 Knicks"),
        mpatches.Patch(color=BLUE, label="Other champions"),
    ]
    ax.legend(handles=handles, fontsize=9, framealpha=0.85, edgecolor="#ddd")
    fig.tight_layout()
    path = save_chart("knicks_2026_win_rate_ranking.svg", OUTPUT_DIR, fig=fig)
    return path


# ── 2. Champions ranked by average playoff margin ────────────────────────────

def plot_margin_ranking(champions: pd.DataFrame) -> str:
    df = champions.sort_values("avg_margin").copy()
    df["label"] = df["year"].apply(lambda y: short_label(int(y)))
    colors = [KNICKS_BLUE if lbl == SUBJECT_LABEL else BLUE for lbl in df["label"]]

    fig, ax = _fig(figsize=(8, max(5, len(df) * 0.22)))
    ax.barh(range(len(df)), df["avg_margin"], color=colors, edgecolor="none", zorder=2)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["label"], fontsize=7.5)
    ax.set_xlabel("Avg point differential (pts/game)", fontsize=10)
    ax.set_title(
        f"NBA Champions: Average Playoff Margin  ({season_range_label(START_YEAR, END_YEAR)})",
        fontsize=11, fontweight="bold", color="#2c2c2a", pad=8,
    )
    _style(ax)

    knicks_rows = df[df["year"] == SUBJECT_YEAR]
    if not knicks_rows.empty:
        pos = df.index.get_loc(knicks_rows.index[0])
        val = float(knicks_rows["avg_margin"].iloc[0])
        ax.text(val + 0.2, pos, f"{val:+.1f}", va="center", fontsize=8,
                color=KNICKS_BLUE, fontweight="bold")

    handles = [
        mpatches.Patch(color=KNICKS_BLUE, label="2025-26 Knicks"),
        mpatches.Patch(color=BLUE, label="Other champions"),
    ]
    ax.legend(handles=handles, fontsize=9, framealpha=0.85, edgecolor="#ddd")
    fig.tight_layout()
    path = save_chart("knicks_2026_margin_ranking.svg", OUTPUT_DIR, fig=fig)
    return path


# ── 3. East/West SRS gap over time ───────────────────────────────────────────

def plot_conference_gap(gap_table: pd.DataFrame) -> str:
    df = gap_table.sort_values("year").copy()
    labels = df["year"].apply(lambda y: short_label(int(y)))
    x = np.arange(len(df))

    fig, ax = _fig(figsize=(11, 4.5))
    ax.plot(x, df["srs_gap"], color=BLUE, linewidth=1.8, zorder=2)
    ax.fill_between(x, 0, df["srs_gap"],
                    where=(df["srs_gap"] > 0), alpha=0.15, color=BLUE, label="West stronger")
    ax.fill_between(x, 0, df["srs_gap"],
                    where=(df["srs_gap"] <= 0), alpha=0.15, color=GREEN, label="East stronger")
    ax.axhline(0, color=GRAY, linewidth=0.8, linestyle="--")

    subj_mask = df["year"] == SUBJECT_YEAR
    if subj_mask.any():
        subj_x = int(x[subj_mask.values][0])
        subj_y = float(df.loc[subj_mask, "srs_gap"].iloc[0])
        ax.scatter([subj_x], [subj_y], color=KNICKS_BLUE, s=60, zorder=4)
        ax.annotate(
            f"2025-26\n{subj_y:+.2f}",
            xy=(subj_x, subj_y), xytext=(subj_x + 1.5, subj_y + 0.4),
            fontsize=8, color=KNICKS_BLUE, fontweight="bold",
            arrowprops=dict(arrowstyle="->", color=KNICKS_BLUE, lw=0.9),
        )

    step = max(1, len(df) // 14)
    ax.set_xticks(x[::step])
    ax.set_xticklabels(labels.iloc[::step], fontsize=7.5, rotation=45, ha="right")
    ax.set_ylabel("West - East avg SRS (pts/game)", fontsize=10)
    ax.set_title(
        f"Conference Strength Gap: West - East SRS  ({season_range_label(START_YEAR, END_YEAR)})",
        fontsize=11, fontweight="bold", color="#2c2c2a", pad=8,
    )
    _style(ax)
    ax.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")
    fig.tight_layout()
    path = save_chart("knicks_2026_conference_gap.svg", OUTPUT_DIR, fig=fig)
    return path


# ── 4. 2025-26 team SRS by conference ────────────────────────────────────────

def plot_team_srs_2026(reg_srs: pd.Series, standings: pd.DataFrame) -> str:
    conf_map = standings.set_index("TeamID")["Conference"].to_dict()
    if "TeamAbbreviation" in standings.columns:
        name_map = standings.set_index("TeamID")["TeamAbbreviation"].to_dict()
    else:
        name_map = {int(tid): f"T{tid}" for tid in standings["TeamID"]}

    srs_df = reg_srs.reset_index()
    srs_df.columns = ["TEAM_ID", "SRS"]
    srs_df["TEAM_ID"] = srs_df["TEAM_ID"].astype(int)
    srs_df["conf"] = srs_df["TEAM_ID"].map(conf_map)
    srs_df["abbr"] = srs_df["TEAM_ID"].map(name_map).fillna("?")
    srs_df = srs_df.sort_values("SRS", ascending=False)

    colors = [GREEN if row["conf"] == "East" else BLUE for _, row in srs_df.iterrows()]

    fig, ax = _fig(figsize=(13, 4.5))
    x = np.arange(len(srs_df))
    ax.bar(x, srs_df["SRS"], color=colors, edgecolor="none", zorder=2)
    ax.axhline(0, color=GRAY, linewidth=0.8)
    ax.set_xticks(x)
    ax.set_xticklabels(srs_df["abbr"], fontsize=7.5, rotation=45, ha="right")
    ax.set_ylabel("Regular-season SRS (pts/game)", fontsize=10)
    ax.set_title("2025-26 Team SRS — East vs. West",
                 fontsize=11, fontweight="bold", color="#2c2c2a", pad=8)
    _style(ax)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)
    ax.grid(axis="x", visible=False)

    handles = [
        mpatches.Patch(color=GREEN, label="Eastern Conference"),
        mpatches.Patch(color=BLUE, label="Western Conference"),
    ]
    ax.legend(handles=handles, fontsize=9, framealpha=0.85, edgecolor="#ddd")
    fig.tight_layout()
    path = save_chart("knicks_2026_team_srs_2026.svg", OUTPUT_DIR, fig=fig)
    return path


# ── 5. Avg opponent SRS faced by each champion ───────────────────────────────

def plot_opponent_srs_ranking(champions: pd.DataFrame) -> str:
    df = champions.dropna(subset=["avg_opp_srs"]).sort_values("avg_opp_srs").copy()
    df["label"] = df["year"].apply(lambda y: short_label(int(y)))
    colors = [KNICKS_BLUE if lbl == SUBJECT_LABEL else BLUE for lbl in df["label"]]

    fig, ax = _fig(figsize=(8, max(5, len(df) * 0.22)))
    ax.barh(range(len(df)), df["avg_opp_srs"], color=colors, edgecolor="none", zorder=2)
    mean_val = df["avg_opp_srs"].mean()
    ax.axvline(mean_val, color=RED, linewidth=1.2, linestyle="--",
               label=f"Mean ({mean_val:+.2f})", zorder=3)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["label"], fontsize=7.5)
    ax.set_xlabel("Average opponent regular-season SRS", fontsize=10)
    ax.set_title(
        f"Strength of Schedule: Avg Opponent SRS  ({season_range_label(START_YEAR, END_YEAR)})",
        fontsize=11, fontweight="bold", color="#2c2c2a", pad=8,
    )
    _style(ax)
    handles = [
        mpatches.Patch(color=KNICKS_BLUE, label="2025-26 Knicks"),
        mpatches.Patch(color=BLUE, label="Other champions"),
        plt.Line2D([0], [0], color=RED, linestyle="--", label="Historical mean"),
    ]
    ax.legend(handles=handles, fontsize=9, framealpha=0.85, edgecolor="#ddd")
    fig.tight_layout()
    path = save_chart("knicks_2026_opponent_srs_ranking.svg", OUTPUT_DIR, fig=fig)
    return path


# ── 6. Opponent-adjusted dominance ranking (headline chart) ──────────────────

def plot_adjusted_margin_ranking(champions: pd.DataFrame) -> str:
    df = champions.dropna(subset=["adj_margin"]).sort_values("adj_margin").copy()
    df["label"] = df["year"].apply(lambda y: short_label(int(y)))
    colors = [KNICKS_BLUE if lbl == SUBJECT_LABEL else BLUE for lbl in df["label"]]

    fig, ax = _fig(figsize=(8, max(5, len(df) * 0.22)))
    ax.barh(range(len(df)), df["adj_margin"], color=colors, edgecolor="none", zorder=2)
    ax.axvline(0, color=GRAY, linewidth=0.8)
    mean_val = df["adj_margin"].mean()
    ax.axvline(mean_val, color=RED, linewidth=1.2, linestyle="--",
               label=f"Mean ({mean_val:+.2f})", zorder=3)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(df["label"], fontsize=7.5)
    ax.set_xlabel("Opponent-adjusted margin (pts/game)", fontsize=10)
    ax.set_title(
        f"Opponent-Adjusted Playoff Dominance  ({season_range_label(START_YEAR, END_YEAR)})",
        fontsize=11, fontweight="bold", color="#2c2c2a", pad=8,
    )
    _style(ax)

    knicks_mask = df["label"] == SUBJECT_LABEL
    if knicks_mask.any():
        pos = int(np.where(knicks_mask.values)[0][0])
        val = float(df.loc[knicks_mask, "adj_margin"].iloc[0])
        ax.text(val + 0.2, pos, f"{val:+.1f}", va="center", fontsize=8,
                color=KNICKS_BLUE, fontweight="bold")

    total = len(df)
    handles = [
        mpatches.Patch(color=KNICKS_BLUE, label=f"2025-26 Knicks (#{total} of {total})"),
        mpatches.Patch(color=BLUE, label="Other champions"),
        plt.Line2D([0], [0], color=RED, linestyle="--", label="Historical mean"),
    ]
    ax.legend(handles=handles, fontsize=9, framealpha=0.85, edgecolor="#ddd")
    fig.tight_layout()
    path = save_chart("knicks_2026_adjusted_margin_ranking.svg", OUTPUT_DIR, fig=fig)
    return path


# ── 7. Knicks per-game margin distribution ───────────────────────────────────

def plot_game_margin_distribution(po_2026: pd.DataFrame) -> str:
    import nbakit.data as _nba
    logs = _nba.fill_plus_minus(po_2026)
    knicks = (
        logs[logs["TEAM_ID"] == 1610612752]
        .sort_values("GAME_DATE")
        .copy()
    )
    margins = knicks["PLUS_MINUS"].tolist()
    n = len(margins)
    x = np.arange(n)
    colors = [KNICKS_BLUE if m >= 0 else RED for m in margins]
    avg = float(np.mean(margins))

    fig, ax = _fig(figsize=(10, 4))
    ax.bar(x, margins, color=colors, edgecolor="none", zorder=2, width=0.7)
    ax.axhline(0, color=GRAY, linewidth=0.8)
    ax.axhline(avg, color=KNICKS_ORANGE, linewidth=1.4, linestyle="--",
               label=f"Avg {avg:+.1f} pts/game", zorder=3)

    for i, m in enumerate(margins):
        if abs(m) <= 5:
            ax.text(i, m + (1 if m >= 0 else -2), f"{m:+.0f}",
                    ha="center", va="bottom" if m >= 0 else "top",
                    fontsize=7.5, color=GRAY, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels([f"G{i+1}" for i in range(n)], fontsize=8)
    ax.set_ylabel("Point differential", fontsize=10)
    ax.set_title("2025-26 Knicks Playoff Run: Game-by-Game Margins",
                 fontsize=11, fontweight="bold", color="#2c2c2a", pad=8)
    _style(ax)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)
    handles = [
        mpatches.Patch(color=KNICKS_BLUE, label="Win"),
        mpatches.Patch(color=RED, label="Loss"),
        plt.Line2D([0], [0], color=KNICKS_ORANGE, linestyle="--", label="Series avg"),
    ]
    ax.legend(handles=handles, fontsize=9, framealpha=0.85, edgecolor="#ddd", loc="upper left")
    fig.tight_layout()
    path = save_chart("knicks_2026_game_margins.svg", OUTPUT_DIR, fig=fig)
    return path


# ── 8. Knicks opponent SRS by round ──────────────────────────────────────────

def plot_opponent_srs_by_round(po_2026: pd.DataFrame, reg_srs: pd.Series,
                               standings: pd.DataFrame) -> str:
    from knicks_2026_data import compute_opponent_srs, KNICKS_TEAM_ID

    if "TeamCity" in standings.columns and "TeamName" in standings.columns:
        name_map = standings.set_index("TeamID").apply(
            lambda r: f"{r['TeamCity']} {r['TeamName']}", axis=1
        ).to_dict()
    elif "TeamAbbreviation" in standings.columns:
        name_map = standings.set_index("TeamID")["TeamAbbreviation"].to_dict()
    else:
        name_map = {}

    opp_srs = compute_opponent_srs(po_2026, reg_srs, KNICKS_TEAM_ID)

    # Determine round order from first game date per opponent
    game_teams = (
        po_2026.groupby("GAME_ID")["TEAM_ID"]
        .apply(lambda s: [x for x in s.tolist() if x != KNICKS_TEAM_ID])
        .reset_index()
    )
    knicks_games = (
        po_2026[po_2026["TEAM_ID"] == KNICKS_TEAM_ID]
        .merge(game_teams.rename(columns={"TEAM_ID": "OPP_LIST"}), on="GAME_ID")
        .copy()
    )
    knicks_games["OPP_ID"] = knicks_games["OPP_LIST"].apply(
        lambda x: int(x[0]) if x else None
    )
    first_game = (
        knicks_games.dropna(subset=["OPP_ID"])
        .sort_values("GAME_DATE")
        .groupby("OPP_ID")["GAME_DATE"].first()
    )
    round_names = ["R1", "R2", "CF", "Finals"]
    opp_order = first_game.sort_values().index.tolist()

    srs_vals  = [float(opp_srs.get(int(oid), float("nan"))) for oid in opp_order]
    raw_names = [name_map.get(int(oid), f"T{oid}") for oid in opp_order]
    bar_names = [n.split()[-1] for n in raw_names]
    x_labels  = [f"{rnd}\n{name}" for rnd, name in zip(round_names[:len(bar_names)], bar_names)]

    colors = [KNICKS_ORANGE if (not np.isnan(s) and s > 0) else LGRAY for s in srs_vals]
    x = np.arange(len(srs_vals))

    fig, ax = _fig(figsize=(7, 4))
    bars = ax.bar(x, srs_vals, color=colors, edgecolor="none", zorder=2, width=0.5)
    ax.axhline(0, color=GRAY, linewidth=0.8)
    mean_opp = float(np.nanmean(srs_vals))
    ax.axhline(mean_opp, color=RED, linewidth=1.2, linestyle="--",
               label=f"Avg opp SRS ({mean_opp:+.2f})", zorder=3)

    for bar, val in zip(bars, srs_vals):
        if not np.isnan(val):
            ax.text(bar.get_x() + bar.get_width() / 2, val + 0.1,
                    f"{val:+.2f}", ha="center", va="bottom", fontsize=9, fontweight="bold")

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=9)
    ax.set_ylabel("Regular-season SRS (pts/game)", fontsize=10)
    ax.set_title("2025-26 Knicks: Playoff Opponent Strength by Round",
                 fontsize=11, fontweight="bold", color="#2c2c2a", pad=8)
    _style(ax)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)
    ax.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")
    fig.tight_layout()
    path = save_chart("knicks_2026_opponent_by_round.svg", OUTPUT_DIR, fig=fig)
    return path


# ── 9. Market expectations vs. actual margin ──────────────────────────────────

def plot_market_vs_actual(ats_df: pd.DataFrame) -> str:
    if ats_df.empty:
        return ""

    ROUND_COLORS = [KNICKS_BLUE, GREEN, KNICKS_ORANGE, RED]
    round_names  = ["R1", "R2", "CF", "Finals"]

    # Determine round for each game from sorted GAME_DATE
    df = ats_df.copy().sort_values("GAME_DATE").reset_index(drop=True)

    # Assign rounds: all games vs same OPP_ID get the same round label
    if "OPP_ID" in df.columns:
        opp_order = df.drop_duplicates("OPP_ID").sort_values("GAME_DATE")["OPP_ID"].tolist()
        opp_round = {oid: i for i, oid in enumerate(opp_order)}
        df["round_idx"] = df["OPP_ID"].map(opp_round)
    else:
        df["round_idx"] = 0

    fig, ax = _fig(figsize=(7, 5))

    lim = max(df["knicks_spread"].abs().max(), df["actual_margin"].abs().max()) + 5
    ax.axline((0, 0), slope=1, color=LGRAY, linewidth=1.0, linestyle="--", zorder=1,
              label="Exactly hit spread")
    ax.axhline(0, color=LGRAY, linewidth=0.6)
    ax.axvline(0, color=LGRAY, linewidth=0.6)

    for rnd_idx, rnd_name in enumerate(round_names):
        sub = df[df["round_idx"] == rnd_idx]
        if sub.empty:
            continue
        color = ROUND_COLORS[rnd_idx % len(ROUND_COLORS)]
        ax.scatter(
            sub["knicks_spread"], sub["actual_margin"],
            color=color, s=60, zorder=3, label=rnd_name, edgecolors="white", linewidths=0.5,
        )

    ax.fill_between([-lim, lim], [-lim, -lim], [0, 0], alpha=0.04, color=RED)
    ax.fill_between([-lim, lim], [0, 0], [lim, lim], alpha=0.04, color=GREEN)
    ax.text(lim * 0.55, lim * 0.85, "Beat spread", color=GREEN, fontsize=8, alpha=0.7)
    ax.text(lim * 0.55, -lim * 0.90, "Missed spread", color=RED, fontsize=8, alpha=0.7)

    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.set_xlabel("Vegas spread (Knicks perspective; – = favored)", fontsize=10)
    ax.set_ylabel("Actual margin (pts)", fontsize=10)
    ax.set_title(
        "2025-26 Knicks Playoffs: Market Expectations vs. Reality",
        fontsize=11, fontweight="bold", color="#2c2c2a", pad=8,
    )
    _style(ax)
    ax.grid(axis="both", color="#e0dfd8", linewidth=0.7, zorder=0)
    ax.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")
    fig.tight_layout()
    path = save_chart("knicks_2026_market_vs_actual.svg", OUTPUT_DIR, fig=fig)
    return path


# ── 10. Round-by-round margin breakdown ──────────────────────────────────────

def plot_round_split(series_df: pd.DataFrame,
                     name_map: dict | None = None) -> str:
    """Grouped bar chart: per-round raw vs. playoff-SRS-adjusted margins.

    series_df is the output of compute_series_margins(..., playoff_srs=...).
    Requires columns: raw_margin, reg_adj_margin, playoff_adj_margin.
    """
    if series_df.empty or "playoff_adj_margin" not in series_df.columns:
        return ""

    round_names = ["R1", "R2", "CF", "Finals"]
    n = len(series_df)
    labels = [round_names[i] if i < len(round_names) else f"R{i+1}"
              for i in range(n)]

    raw_vals    = list(series_df["raw_margin"])
    reg_vals    = list(series_df["reg_adj_margin"])
    po_vals     = list(series_df["playoff_adj_margin"])

    x = np.arange(n)
    width = 0.26

    fig, ax = _fig(figsize=(9, 5))

    bars_raw = ax.bar(x - width, raw_vals,  width, label="Raw margin",
                      color=KNICKS_ORANGE, edgecolor="none", zorder=2)
    bars_reg = ax.bar(x,          reg_vals, width, label="Reg-season SRS adj",
                      color=BLUE,         edgecolor="none", zorder=2)
    bars_po  = ax.bar(x + width,  po_vals,  width, label="Playoff SRS adj",
                      color=GREEN,         edgecolor="none", zorder=2)

    ax.axhline(0, color=GRAY, linewidth=0.8, linestyle="--")

    for bar, val in zip(bars_raw, raw_vals):
        if not np.isnan(val):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    val + (0.5 if val >= 0 else -1.5),
                    f"{val:+.1f}", ha="center", va="bottom" if val >= 0 else "top",
                    fontsize=7.5, color=KNICKS_ORANGE, fontweight="bold")
    for bar, val in zip(bars_po, po_vals):
        if not np.isnan(val):
            ax.text(bar.get_x() + bar.get_width() / 2,
                    val + (0.5 if val >= 0 else -1.5),
                    f"{val:+.1f}", ha="center", va="bottom" if val >= 0 else "top",
                    fontsize=7.5, color=GREEN, fontweight="bold")
        else:
            ax.text(bar.get_x() + bar.get_width() / 2, 1.0,
                    "n/a", ha="center", va="bottom",
                    fontsize=7, color=GRAY, style="italic")

    ax.set_xticks(x)
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_ylabel("Point differential (pts/game)", fontsize=10)
    ax.set_title(
        "2025-26 Knicks Playoffs: Raw vs. Opponent-Adjusted Margin by Round",
        fontsize=11, fontweight="bold", color="#2c2c2a", pad=8,
    )
    _style(ax)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)
    ax.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd")
    fig.tight_layout()

    path = save_chart("knicks_2026_round_split.svg", OUTPUT_DIR, fig=fig)
    return path


# ── 11. Opponent key-player health ─────────────────────────────────────────────

def plot_opponent_health(health_df: pd.DataFrame) -> str:
    if health_df.empty:
        return ""

    round_names = ["R1", "R2", "CF", "Finals"]
    n = len(health_df)
    names = [row["team_name"].split()[-1] for _, row in health_df.iterrows()]
    x_labels = [
        f"{round_names[i] if i < len(round_names) else f'R{i+1}'}\n{names[i]}"
        for i in range(n)
    ]
    scores = list(health_df["health_score"])

    def _color(s):
        if s >= 0.90:
            return GREEN
        if s >= 0.75:
            return KNICKS_ORANGE
        return RED

    colors = [_color(s) for s in scores]
    x = np.arange(n)

    fig, ax = _fig(figsize=(7, 4))
    bars = ax.bar(x, [s * 100 for s in scores], color=colors, edgecolor="none",
                  zorder=2, width=0.5)
    ax.axhline(100, color=LGRAY, linewidth=0.8, linestyle="--")

    for bar, val in zip(bars, scores):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            val * 100 + 1,
            f"{val:.0%}",
            ha="center", va="bottom", fontsize=10, fontweight="bold",
        )

    ax.set_xticks(x)
    ax.set_xticklabels(x_labels, fontsize=9)
    ax.set_ylim(0, 120)
    ax.set_ylabel("Core-player availability (%)", fontsize=10)
    ax.set_title(
        "2025-26 Knicks Playoff: Opponent Key-Player Availability",
        fontsize=11, fontweight="bold", color="#2c2c2a", pad=8,
    )
    _style(ax)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)

    patches = [
        mpatches.Patch(color=GREEN, label="≥90% available"),
        mpatches.Patch(color=KNICKS_ORANGE, label="75–89%"),
        mpatches.Patch(color=RED, label="<75% (depleted)"),
    ]
    ax.legend(handles=patches, fontsize=8, framealpha=0.85, edgecolor="#ddd")
    fig.tight_layout()
    path = save_chart("knicks_2026_opponent_health.svg", OUTPUT_DIR, fig=fig)
    return path


# ── 12. Bootstrapped adjusted-margin distribution vs. the field ──────────────

def plot_bootstrap_margin(po_2026: pd.DataFrame, reg_srs: pd.Series,
                          champions: pd.DataFrame) -> str:
    """Histogram of the bootstrapped opponent-adjusted margin, with the nearest
    rivals' fixed values marked, so the reader sees how often the Knicks fall
    below #2 all-time."""
    from knicks_2026_data import bootstrap_adjusted_margin_rank, KNICKS_TEAM_ID

    other_adj = champions.loc[champions["year"] != SUBJECT_YEAR, "adj_margin"]
    boot = bootstrap_adjusted_margin_rank(po_2026, reg_srs, KNICKS_TEAM_ID, other_adj)
    if not boot:
        return ""

    draws = boot["draws"]
    fig, ax = _fig(figsize=(9, 4.5))
    ax.hist(draws, bins=50, color=KNICKS_BLUE, alpha=0.85, edgecolor="none", zorder=2)

    # Nearest rivals above the field — the top other champions
    rivals = (
        champions.loc[champions["year"] != SUBJECT_YEAR]
        .dropna(subset=["adj_margin"])
        .nlargest(2, "adj_margin")
    )
    for _, r in rivals.iterrows():
        v = float(r["adj_margin"])
        ax.axvline(v, color=RED, linewidth=1.3, linestyle="--", zorder=3)
        ax.text(v, ax.get_ylim()[1] * 0.92, f" {short_label(int(r['year']))} {v:+.1f}",
                color=RED, fontsize=8, rotation=90, va="top", ha="left")

    ax.axvline(boot["adj_point"], color=KNICKS_ORANGE, linewidth=1.6, zorder=4,
               label=f"Point estimate {boot['adj_point']:+.1f}")

    ax.set_xlabel("Opponent-adjusted margin, resampled games (pts/game)", fontsize=10)
    ax.set_ylabel("Resamples", fontsize=10)
    ax.set_title(
        f"The #1 ranking is likely but not certain: P(1st) = {boot['p_rank1']:.0%}",
        fontsize=11, fontweight="bold", color="#2c2c2a", pad=20,
    )
    ax.text(
        0.5, 1.012,
        "20,000 game-level bootstraps of the 2025-26 run vs. the fixed champion field",
        transform=ax.transAxes, ha="center", va="bottom", fontsize=8.5, color=GRAY,
    )
    _style(ax)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)
    ax.legend(fontsize=9, framealpha=0.85, edgecolor="#ddd", loc="upper left")
    fig.tight_layout()
    path = save_chart("knicks_2026_bootstrap_margin.svg", OUTPUT_DIR, fig=fig)
    return path


# ── 13. Hierarchical posterior: the field bunches up ─────────────────────────

def plot_hierarchical_posterior(posterior_df: pd.DataFrame, p_rank1: float,
                                top_n: int = 12) -> str:
    """Posterior (shrunk) adjusted margin ± 90% credible interval for the top
    champions, with each one's raw point estimate shown as a faint tick, so the
    reader sees how partial pooling pulls everyone together and how much the
    credible intervals overlap (which is why no champion is a clear #1)."""
    if posterior_df.empty or "post_mean" not in posterior_df.columns:
        return ""

    df = posterior_df.head(top_n).iloc[::-1].reset_index(drop=True)  # best at top
    z90 = 1.6448536
    y = np.arange(len(df))
    is_knicks = df["year"] == SUBJECT_YEAR
    colors = [KNICKS_BLUE if k else GRAY for k in is_knicks]

    fig, ax = _fig(figsize=(8.5, max(4.5, len(df) * 0.42)))
    for yi, (_, row), col in zip(y, df.iterrows(), colors):
        ax.errorbar(
            row["post_mean"], yi, xerr=z90 * row["post_sd"],
            fmt="none", ecolor=col, elinewidth=2.4, capsize=3, zorder=2,
        )
    ax.scatter(df["post_mean"], y, color=colors, s=42, zorder=3)
    # raw (unshrunk) point estimate as a faint tick, to show the pull
    ax.scatter(df["adj_mean"], y, marker="|", color=RED, s=90, zorder=4,
               label="Raw adj margin (pre-shrink)")

    ax.set_yticks(y)
    ax.set_yticklabels([short_label(int(yr)) for yr in df["year"]], fontsize=8.5)
    ax.set_xlabel("Posterior opponent-adjusted margin (pts/game)", fontsize=10)
    ax.set_title(
        f"After fair shrinkage the field bunches: Knicks ~{p_rank1:.0%} to be the true #1",
        fontsize=11, fontweight="bold", color="#2c2c2a", pad=20,
    )
    ax.text(
        0.5, 1.012,
        "Partial-pooling posterior mean ± 90% credible interval, top champions",
        transform=ax.transAxes, ha="center", va="bottom", fontsize=8.5, color=GRAY,
    )
    _style(ax)
    ax.grid(axis="y", visible=False)
    ax.grid(axis="x", color="#e0dfd8", linewidth=0.7, zorder=0)
    handles = [
        mpatches.Patch(color=KNICKS_BLUE, label="2025-26 Knicks"),
        mpatches.Patch(color=GRAY, label="Other champions"),
        plt.Line2D([0], [0], marker="|", color=RED, linestyle="none",
                   markersize=9, label="Raw margin (pre-shrink)"),
    ]
    ax.legend(handles=handles, fontsize=8.5, framealpha=0.85, edgecolor="#ddd",
              loc="lower right")
    fig.tight_layout()
    path = save_chart("knicks_2026_hierarchical_posterior.svg", OUTPUT_DIR, fig=fig)
    return path


# ── Orchestrator ─────────────────────────────────────────────────────────────

# ── 12. Reg→playoff SRS elevation across the 2025-26 field ───────────────────

def plot_playoff_field_elevation(po_2026: pd.DataFrame, reg_2026: pd.DataFrame,
                                 standings: pd.DataFrame) -> str:
    from knicks_2026_data import compute_playoff_field_elevation, KNICKS_TEAM_ID

    field = compute_playoff_field_elevation(po_2026, reg_2026)
    name_map = standings.set_index("TeamID").apply(
        lambda r: f"{r['TeamCity']} {r['TeamName']}", axis=1).to_dict()
    spurs_id = next((int(t) for t, nm in name_map.items() if "Spurs" in str(nm)), None)

    df = field.sort_values("elevation").reset_index(drop=True)   # smallest at bottom
    labels = [name_map.get(int(t), f"Team {int(t)}") for t in df["team_id"]]

    def _color(tid):
        tid = int(tid)
        if tid == KNICKS_TEAM_ID:
            return KNICKS_BLUE
        if tid == spurs_id:
            return KNICKS_ORANGE
        return LGRAY
    colors = [_color(t) for t in df["team_id"]]

    fig, ax = _fig(figsize=(8, max(5, len(df) * 0.34)))
    ax.barh(range(len(df)), df["elevation"], color=colors, edgecolor="none", zorder=2)
    ax.axvline(0, color=GRAY, linewidth=0.8)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels(labels, fontsize=8)
    ax.set_xlabel("Playoff SRS − regular-season SRS (pts/game)", fontsize=10)
    ax.set_title("The Knicks improved more than any 2025-26 playoff team",
                 fontsize=11, fontweight="bold", color="#2c2c2a", pad=18)
    ax.text(0.0, 1.012,
            "Regular-season to playoff jump in team rating; the Spurs were second",
            transform=ax.transAxes, fontsize=8.5, color=GRAY)
    _style(ax)

    for i, row in df.iterrows():
        tid = int(row["team_id"])
        if tid in (KNICKS_TEAM_ID, spurs_id):
            v = float(row["elevation"])
            ax.text(v + (0.15 if v >= 0 else -0.15), i, f"{v:+.1f}",
                    va="center", ha="left" if v >= 0 else "right", fontsize=8,
                    fontweight="bold",
                    color=KNICKS_BLUE if tid == KNICKS_TEAM_ID else KNICKS_ORANGE)

    handles = [
        mpatches.Patch(color=KNICKS_BLUE, label="Knicks"),
        mpatches.Patch(color=KNICKS_ORANGE, label="Spurs (Finals opponent)"),
        mpatches.Patch(color=LGRAY, label="Other playoff teams"),
    ]
    ax.legend(handles=handles, fontsize=9, framealpha=0.85, edgecolor="#ddd",
              loc="lower right")
    fig.tight_layout()
    return save_chart("knicks_2026_field_elevation.svg", OUTPUT_DIR, fig=fig)


# ── 14. How rare a 16-3 title run was, given the regular season ──────────────

def plot_title_run_rarity(po_2026: pd.DataFrame, reg_2026: pd.DataFrame,
                          standings_2026: pd.DataFrame) -> str:
    """How unlikely the 16-3 run was from the Knicks' regular-season strength.

    A forward simulation of the actual bracket that does NOT know the Knicks
    would elevate in May.  Bars show how many games a simulated title run lost;
    the ≤3-loss zone (this clean or cleaner) is highlighted and the actual 16-3
    flagged.  A text box carries the two headline rarities: winning the title at
    all, and winning it this cleanly.
    """
    from knicks_2026_data import build_title_run_specs, simulate_title_run

    champ_srs, specs, _meta, _name = build_title_run_specs(
        po_2026, reg_2026, standings_2026)
    res = simulate_title_run(champ_srs, specs)
    title_losses = np.asarray(res["title_losses"])
    if title_losses.size == 0:
        return ""

    p_title          = res["p_title"]
    p_le3_given      = res["p_le3_losses_given_title"]
    p_title_and_le3  = res["p_title_and_le3_losses"]
    exp_losses       = res["exp_losses_given_title"]
    ACTUAL = 3

    max_l = int(title_losses.max())
    loss_vals = list(range(max_l + 1))
    # share of TITLE runs that lost exactly k games
    shares = [100.0 * (title_losses == k).sum() / title_losses.size for k in loss_vals]
    colors = [KNICKS_BLUE if k <= ACTUAL else LGRAY for k in loss_vals]

    fig, ax = _fig(figsize=(9, 4.6))
    # highlight the "this clean or cleaner" zone
    ax.axvspan(-0.5, ACTUAL + 0.5, color=KNICKS_BLUE, alpha=0.07, zorder=0)
    ax.bar(loss_vals, shares, width=0.85, color=colors, edgecolor="none", zorder=2)

    # typical title run loses ~exp_losses games
    ax.axvline(exp_losses, color=GRAY, linewidth=1.2, linestyle="--", zorder=3)
    ax.text(exp_losses + 0.15, ax.get_ylim()[1] * 0.96,
            f"Typical title run:\n{exp_losses:.1f} losses",
            color=GRAY, fontsize=8, va="top", ha="left")

    # flag the actual 16-3
    y3 = shares[ACTUAL]
    ax.annotate("Actual: 16-3", xy=(ACTUAL, y3), xytext=(ACTUAL, y3 + ax.get_ylim()[1] * 0.18),
                color=KNICKS_BLUE, fontsize=9, fontweight="bold", ha="center",
                arrowprops=dict(arrowstyle="->", color=KNICKS_BLUE, linewidth=1.4))

    ax.set_xlabel("Losses in a simulated title run", fontsize=10)
    ax.set_ylabel("Share of title runs (%)", fontsize=10)
    ax.set_xticks(loss_vals)
    ax.set_title(
        "A 16-3 run was deep in the rare tail of what the Knicks' season predicted",
        fontsize=11, fontweight="bold", color="#2c2c2a", pad=20,
    )
    ax.text(
        0.5, 1.012,
        "Forward simulation from regular-season strength only; losses among simulated title runs",
        transform=ax.transAxes, ha="center", va="bottom", fontsize=8.5, color=GRAY,
    )
    _style(ax)
    ax.grid(axis="x", visible=False)
    ax.grid(axis="y", color="#e0dfd8", linewidth=0.7, zorder=0)

    box = (
        f"Win the title at all:  {p_title:.0%}\n"
        f"16-3 or cleaner, if a title:  {p_le3_given:.0%}\n"
        f"Both (title AND ≤3 losses):  {p_title_and_le3:.0%}"
    )
    ax.text(0.03, 0.97, box, transform=ax.transAxes, ha="left", va="top",
            fontsize=9, color="#2c2c2a",
            bbox=dict(boxstyle="round,pad=0.5", facecolor="white", edgecolor="#ddd"))

    fig.tight_layout()
    return save_chart("knicks_2026_title_run_rarity.svg", OUTPUT_DIR, fig=fig)


def plot_all(po_2026: pd.DataFrame, reg_2026: pd.DataFrame,
             standings_2026: pd.DataFrame, champions: pd.DataFrame,
             gap_table: pd.DataFrame,
             health_df: pd.DataFrame | None = None,
             ats_df: pd.DataFrame | None = None,
             series_df: pd.DataFrame | None = None,
             posterior_df: pd.DataFrame | None = None,
             p_rank1: float | None = None) -> list:
    from knicks_2026_data import compute_srs
    reg_srs = compute_srs(reg_2026)

    paths = [
        plot_win_rate_ranking(champions),
        plot_margin_ranking(champions),
        plot_conference_gap(gap_table),
        plot_team_srs_2026(reg_srs, standings_2026),
        plot_opponent_srs_ranking(champions),
        plot_adjusted_margin_ranking(champions),
        plot_game_margin_distribution(po_2026),
        plot_opponent_srs_by_round(po_2026, reg_srs, standings_2026),
        plot_bootstrap_margin(po_2026, reg_srs, champions),
        plot_playoff_field_elevation(po_2026, reg_2026, standings_2026),
        plot_title_run_rarity(po_2026, reg_2026, standings_2026),
    ]
    if series_df is not None and not series_df.empty:
        p = plot_round_split(series_df)
        if p:
            paths.append(p)
    if health_df is not None and not health_df.empty:
        p = plot_opponent_health(health_df)
        if p:
            paths.append(p)
    if ats_df is not None and not ats_df.empty:
        p = plot_market_vs_actual(ats_df)
        if p:
            paths.append(p)
    if posterior_df is not None and not posterior_df.empty and p_rank1 is not None:
        p = plot_hierarchical_posterior(posterior_df, p_rank1)
        if p:
            paths.append(p)
    return paths
