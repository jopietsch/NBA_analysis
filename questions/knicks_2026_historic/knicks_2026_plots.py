"""
knicks_2026_plots.py — visualization for the 2026 Knicks playoff analysis.

Each plot_* function takes pre-computed frames/values, draws one figure,
and saves to generated/knicks_2026_*.png.

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
    output_path,
    style_axes as _style,
    new_fig as _fig,
)

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "generated")

# ── Team accent colors (Knicks-specific) ──────────────────────────────────────
KNICKS_BLUE   = "#006BB6"
KNICKS_ORANGE = "#F58426"

SUBJECT_LABEL = short_label(SUBJECT_YEAR)   # "25-26"


def _out(name: str) -> str:
    return output_path(name, OUTPUT_DIR)


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
    path = _out("knicks_2026_win_rate_ranking.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
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
    path = _out("knicks_2026_margin_ranking.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
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
    path = _out("knicks_2026_conference_gap.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
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
    path = _out("knicks_2026_team_srs_2026.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
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
    path = _out("knicks_2026_opponent_srs_ranking.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
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
    path = _out("knicks_2026_adjusted_margin_ranking.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
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
    path = _out("knicks_2026_game_margins.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
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
    path = _out("knicks_2026_opponent_by_round.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
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
    path = _out("knicks_2026_market_vs_actual.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
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

    path = _out("knicks_2026_round_split.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
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
    path = _out("knicks_2026_opponent_health.png")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ── Orchestrator ─────────────────────────────────────────────────────────────

def plot_all(po_2026: pd.DataFrame, reg_2026: pd.DataFrame,
             standings_2026: pd.DataFrame, champions: pd.DataFrame,
             gap_table: pd.DataFrame,
             health_df: pd.DataFrame | None = None,
             ats_df: pd.DataFrame | None = None,
             series_df: pd.DataFrame | None = None) -> list:
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
    return paths
