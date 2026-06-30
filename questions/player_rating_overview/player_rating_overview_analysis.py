"""
player_rating_overview_analysis.py — statistical analysis for the player rating overview.

run() prints all output; the orchestrator captures it to docs/player_rating_overview_results.md.
Sections use the box-drawing header convention: print("─── SECTION " + "─" * 50).
"""

import numpy as np
import pandas as pd
from scipy import stats

from player_rating_overview_data import (
    load_unified_ratings,
    load_team_outcomes,
    load_playoff_deltas,
    MIN_MINUTES_QUALIFIER,
    MIN_PLAYOFF_MINUTES,
    PLAYOFF_DELTA_METRICS,
    powerlaw_fit,
    POWERLAW_R2_THRESHOLD,
)
from player_rating_overview_facts import FACTS, _FACTS_PATH, _GUARDS_PATH

# Rating systems included in the cross-system comparison
# (all systems that may be present; silently skipped if absent in the data)
ALL_SYSTEMS = [
    "GAME_SCORE", "PER", "WS", "WS48", "BPM", "OBPM", "DBPM", "VORP",
    "RAPTOR", "RAPTOR_WAR", "RAPTOR_O", "RAPTOR_D",
    "DARKO_DPM", "EPM", "LEBRON", "ESPN_RPM",
    "RAPM", "O_RAPM", "D_RAPM",
    "RAPM_MY", "O_RAPM_MY", "D_RAPM_MY",
]

# Systems kept out of the consensus average. Two RAPM families are computed: the
# bare single-season RAPM (noisy, kept for the demonstration) and the prior-
# informed multi-year RAPM_MY (the headline impact metric). Only the combined
# RAPM_MY enters the consensus. Bare RAPM and every offense/defense split are
# excluded so the RAPM family gets a single, stabilized vote rather than several
# noisy ones. (The BPM/RAPTOR splits predate this and stay in the consensus to
# keep the rest of the report's numbers unchanged.)
CONSENSUS_EXCLUDE = {"RAPM", "O_RAPM", "D_RAPM", "O_RAPM_MY", "D_RAPM_MY"}

# Box-score systems recomputed for every season in the cache (2010-11 onward),
# so the multi-season panel compares the same set across all season-pairs. The
# third-party impact metrics (RAPTOR etc.) cover only some years, so they are
# left out of the pooled panel to keep each system's sample even.
PANEL_SYSTEMS = ["GAME_SCORE", "PER", "WS", "WS48", "BPM", "OBPM", "DBPM", "VORP"]

# Span of complete seasons held in the shared cache (end-years). The panel
# describes each season in this range and forecasts each consecutive pair.
# 1996-97 is the floor: the oldest season nba_api serves advanced splits for.
PANEL_START_YEAR = 1997  # 1996-97
PANEL_END_YEAR = 2026    # 2025-26

# A second, parallel panel restricted to the seasons where RAPM can be computed
# from play-by-play. It scores the box-score systems AND RAPM over the SAME
# window, so RAPM is compared against the box scores on equal seasons rather
# than against their full 30-season history. Only the combined RAPM is included
# (not its offensive/defensive halves), matching the consensus treatment.
RAPM_PANEL_SYSTEMS = PANEL_SYSTEMS + ["RAPM", "RAPM_MY"]
RAPM_PANEL_START_YEAR = 2014  # 2013-14, first season with cached play-by-play
RAPM_PANEL_END_YEAR = 2026    # 2025-26

SYSTEM_LABELS = {
    "GAME_SCORE": "Game Score",
    "PER": "PER",
    "TS_PCT": "TS%",
    "EFG_PCT": "eFG%",
    "USG_PCT": "USG%",
    "WS": "Win Shares",
    "WS48": "WS/48",
    "OWS": "Offensive Win Shares",
    "DWS": "Defensive Win Shares",
    "BPM": "BPM",
    "OBPM": "OBPM",
    "DBPM": "DBPM",
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
    "RAPM_MY": "RAPM (multi-yr+prior)",
    "O_RAPM_MY": "O-RAPM (MY)",
    "D_RAPM_MY": "D-RAPM (MY)",
    "MVP_SHARE": "MVP Vote Share",
    "ALL_NBA_PTS": "All-NBA Points",
    "CONSENSUS": "Consensus",
    "WINS_PRED": "Wins-Predictive",
}


def _present_systems(df: pd.DataFrame, systems: list[str]) -> list[str]:
    """Return the subset of `systems` that have at least 10 non-null values in df."""
    return [s for s in systems if s in df.columns and df[s].notna().sum() >= 10]


def _gini(values: np.ndarray) -> float:
    """Gini coefficient for a 1-D array of non-negative values."""
    v = np.sort(np.maximum(values, 0))
    n = len(v)
    if n == 0 or v.sum() == 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2 * np.dot(idx, v) / (n * v.sum())) - (n + 1) / n)


def _top_share(values: np.ndarray, top_pct: float = 0.05) -> float:
    """Fraction of total (positive) value held by the top_pct of players."""
    v = np.sort(values)[::-1]
    total = v[v > 0].sum()
    if total == 0:
        return 0.0
    top_n = max(1, int(np.ceil(len(v) * top_pct)))
    return float(v[:top_n].sum() / total)


def _build_consensus(df: pd.DataFrame, systems: list[str]) -> pd.Series:
    """Mean z-score across all present systems (qualified players only)."""
    present = [s for s in _present_systems(df, systems) if s not in CONSENSUS_EXCLUDE]
    if not present:
        return pd.Series(np.nan, index=df.index)
    z_cols = []
    for s in present:
        col = df[s].copy()
        std = col.std()
        if std > 0:
            df[f"_z_{s}"] = (col - col.mean()) / std
            z_cols.append(f"_z_{s}")
    if not z_cols:
        return pd.Series(np.nan, index=df.index)
    consensus = df[z_cols].mean(axis=1)
    # Clean up temp columns
    df.drop(columns=z_cols, inplace=True)
    return consensus


def _build_wins_predictive(df: pd.DataFrame, systems: list[str]) -> pd.Series:
    """Wins-predictive rating: ridge regression of system z-scores onto team wins.

    Aggregates player ratings to team level (minutes-weighted), fits a
    non-negative constrained ridge to predict team W (from MIN and TEAM_ID),
    then reads back per-player weights.

    Falls back to consensus if not enough team-win data.
    """
    present = _present_systems(df, systems)
    if len(present) < 2 or "TEAM_ID" not in df.columns or "MIN" not in df.columns:
        return _build_consensus(df, present)

    # Z-score each system
    z_df = pd.DataFrame(index=df.index)
    for s in present:
        col = df[s].copy()
        std = col.std()
        z_df[s] = (col - col.mean()) / std if std > 0 else 0

    # Minutes-weighted team average for each system
    df2 = df[["TEAM_ID", "MIN"]].copy()
    for s in present:
        df2[s] = z_df[s]

    team_ratings = (
        df2.groupby("TEAM_ID")
        .apply(lambda g: pd.Series(
            {s: np.average(g[s].fillna(0), weights=g["MIN"].clip(lower=0).fillna(0) + 1)
             for s in present}
        ))
        .reset_index()
    )

    # Team wins: look for TEAM_W (merged from team_totals) or W column
    win_col = "TEAM_W" if "TEAM_W" in df.columns else ("W" if "W" in df.columns else None)
    if win_col is None:
        return _build_consensus(df, present)

    team_wins = df.groupby("TEAM_ID")[win_col].max().reset_index().rename(columns={win_col: "W"})

    team_data = team_ratings.merge(team_wins, on="TEAM_ID", how="inner")
    if len(team_data) < 5:
        return _build_consensus(df, present)

    X = team_data[present].fillna(0).values
    y = team_data["W"].values.astype(float)

    # Non-negative ridge (sklearn if available, else OLS)
    try:
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_s = scaler.fit_transform(X)
        ridge = Ridge(alpha=5.0, fit_intercept=True, positive=False)
        ridge.fit(X_s, y)
        coef = ridge.coef_
    except ImportError:
        coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)

    # Per-player wins-predictive score = weighted combination, then normalize to z-space
    wp = pd.Series(0.0, index=df.index)
    for i, s in enumerate(present):
        std = df[s].std()
        z = (df[s] - df[s].mean()) / std if std > 0 else 0
        wp += coef[i] * z.fillna(0)

    wp_std = wp.std()
    if wp_std > 0:
        wp = (wp - wp.mean()) / wp_std
    return wp


# Systems whose construction uses team or lineup point differential (BPM's team
# adjustment, Win Shares' calibration to team wins, the impact metrics' RAPM
# base). For these, reconstructing team point differential is partly mechanical,
# so a high retrodiction score is not evidence of quality. The outcome-blind
# metrics (PER, Game Score) never saw who won, so their score is a genuine read.
OUTCOME_CALIBRATED = {
    "WS", "WS48", "BPM", "OBPM", "DBPM", "VORP",
    "RAPTOR", "RAPTOR_O", "RAPTOR_D", "RAPTOR_WAR",
    "DARKO_DPM", "EPM", "LEBRON", "ESPN_RPM",
    "RAPM", "O_RAPM", "D_RAPM",
    "RAPM_MY", "O_RAPM_MY", "D_RAPM_MY",
}


def _team_mean_z(df: pd.DataFrame, system: str) -> pd.Series | None:
    """Minutes-weighted team mean of a system's player z-scores.

    Z-scores the system across all players who carry it, then takes the
    minutes-weighted average within each team (a small +1 keeps zero-minute rows
    from vanishing). Returns a Series indexed by TEAM_ID, or None if the system
    has no spread.
    """
    if system not in df.columns or "TEAM_ID" not in df.columns or "MIN" not in df.columns:
        return None
    col = df[system]
    std = col.std()
    if not std > 0:
        return None
    z = (col - col.mean()) / std
    t = pd.DataFrame({
        "TEAM_ID": df["TEAM_ID"],
        "z": z,
        "w": df["MIN"].clip(lower=0).fillna(0) + 1,
    }).dropna(subset=["z"])
    return t.groupby("TEAM_ID").apply(
        lambda d: np.average(d["z"], weights=d["w"]), include_groups=False
    )


def retrodiction_scores(df: pd.DataFrame, outcomes: pd.DataFrame,
                        systems: list[str], target: str = "point_diff") -> dict:
    """Grade each system by how well its team aggregate rebuilds team results.

    For each system: minutes-weighted team mean z-rating, then a single-predictor
    line onto the team outcome (point differential per game by default). Reports
    both the in-sample R² and a leave-one-team-out cross-validated R² (the honest
    out-of-sample read on 30 teams). Returns {system: {r2, cv_r2, n}}.
    """
    y_map = outcomes.set_index("TEAM_ID")[target]
    result = {}
    for s in systems:
        tm = _team_mean_z(df, s)
        if tm is None:
            continue
        data = pd.DataFrame({"x": tm, "y": y_map}).dropna()
        if len(data) < 10:
            continue
        x = data["x"].values
        y = data["y"].values
        ss_tot = float(((y - y.mean()) ** 2).sum())
        if ss_tot <= 0:
            continue
        b1, b0 = np.polyfit(x, y, 1)
        yhat = b1 * x + b0
        r2 = 1.0 - float(((y - yhat) ** 2).sum()) / ss_tot
        # Leave-one-team-out cross-validation
        preds = np.empty(len(x))
        for i in range(len(x)):
            mask = np.arange(len(x)) != i
            c1, c0 = np.polyfit(x[mask], y[mask], 1)
            preds[i] = c1 * x[i] + c0
        cv_r2 = 1.0 - float(((y - preds) ** 2).sum()) / ss_tot
        result[s] = {"r2": r2, "cv_r2": cv_r2, "n": int(len(data))}
    return result


def next_season_retrodiction(df_prior: pd.DataFrame, df_curr: pd.DataFrame,
                             outcomes: pd.DataFrame, systems: list[str],
                             target: str = "point_diff") -> dict:
    """Grade each system by how well last season's ratings predict this season.

    Each current-season player is assigned their PRIOR-season rating; the team
    aggregate is the minutes-weighted (current-season minutes) mean of those
    prior ratings, fit to the current team outcome. Because a metric's team
    adjustment is fit to its own season, predicting the next season removes the
    in-sample circularity that flatters the team-fit metrics. Players with no
    prior rating (rookies, prior non-qualifiers) drop out; `coverage` reports the
    share of current team minutes that carried a prior rating. Returns
    {system: {r2, n, coverage}}.
    """
    pid_p = "player_id" if "player_id" in df_prior.columns else "PLAYER_ID"
    pid_c = "player_id" if "player_id" in df_curr.columns else "PLAYER_ID"
    if "TEAM_ID" not in df_curr.columns or "MIN" not in df_curr.columns:
        return {}
    y_map = outcomes.set_index("TEAM_ID")[target]
    result = {}
    for s in systems:
        if s not in df_prior.columns:   # rating comes from the prior season only
            continue
        col = df_prior[s]
        std = col.std()
        if not std > 0:
            continue
        zmap = (pd.DataFrame({"pid": df_prior[pid_p], "z": (col - col.mean()) / std})
                .dropna().groupby("pid")["z"].mean())
        cur = pd.DataFrame({
            "pid": df_curr[pid_c],
            "TEAM_ID": df_curr["TEAM_ID"],
            "w": df_curr["MIN"].clip(lower=0).fillna(0) + 1,
        }).dropna(subset=["TEAM_ID"])
        cur["z"] = cur["pid"].map(zmap)
        matched = cur.dropna(subset=["z"])
        if matched.empty:
            continue
        coverage = float(matched["w"].sum() / cur["w"].sum())
        team = matched.groupby("TEAM_ID").apply(
            lambda d: np.average(d["z"], weights=d["w"]), include_groups=False)
        data = pd.DataFrame({"x": team, "y": y_map}).dropna()
        if len(data) < 10:
            continue
        x = data["x"].values
        y = data["y"].values
        ss_tot = float(((y - y.mean()) ** 2).sum())
        if ss_tot <= 0:
            continue
        b1, b0 = np.polyfit(x, y, 1)
        yhat = b1 * x + b0
        r2 = 1.0 - float(((y - yhat) ** 2).sum()) / ss_tot
        result[s] = {"r2": r2, "n": int(len(data)), "coverage": coverage}
    return result


def panel_retrodiction(start_year: int, end_year: int,
                       systems: list[str] | None = None,
                       target: str = "point_diff") -> dict:
    """Pool the describe and forecast tests across every season in the cache.

    For each season y in [start_year, end_year], the describe score is the
    leave-one-team-out CV R² of y's own ratings against y's team point
    differential (same-season retrodiction). For each consecutive pair (y, y+1),
    the forecast score is how well y's ratings, carried onto y+1's rosters,
    predict y+1's point differential (next-season retrodiction). Reads only the
    cached unified tables and cached team totals, so it makes no network calls.

    Returns {"describe": {sys: [r2, ...]}, "forecast": {sys: [r2, ...]},
             "seasons": [years], "pairs": [(y, y+1), ...]}.
    """
    systems = systems or PANEL_SYSTEMS
    describe: dict[str, list[float]] = {s: [] for s in systems}
    forecast: dict[str, list[float]] = {s: [] for s in systems}
    seasons: list[int] = []
    pairs: list[tuple[int, int]] = []

    _cache: dict[int, pd.DataFrame] = {}

    def _load(y: int) -> pd.DataFrame:
        if y not in _cache:
            _cache[y] = load_unified_ratings(y)
        return _cache[y]

    for y in range(start_year, end_year + 1):
        df = _load(y)
        if df.empty:
            continue
        out = load_team_outcomes(y)
        pres = _present_systems(df, systems)
        for s, sc in retrodiction_scores(df, out, pres, target=target).items():
            describe[s].append(sc["cv_r2"])
        seasons.append(y)

    for y in range(start_year, end_year):
        df_prior, df_curr = _load(y), _load(y + 1)
        if df_prior.empty or df_curr.empty:
            continue
        out = load_team_outcomes(y + 1)
        pres = _present_systems(df_prior, systems)
        for s, sc in next_season_retrodiction(df_prior, df_curr, out, pres,
                                              target=target).items():
            forecast[s].append(sc["r2"])
        pairs.append((y, y + 1))

    return {"describe": describe, "forecast": forecast,
            "seasons": seasons, "pairs": pairs}


# "Elite tier" size for the year-over-year retention measure: of the top-N
# players by a system one season, how many are still top-N the next.
STABILITY_TOP_N = 20


def rating_stability(start_year: int, end_year: int,
                     systems: list[str] | None = None,
                     top_n: int = STABILITY_TOP_N) -> dict:
    """Year-over-year persistence of each system's player ratings.

    For every consecutive season-pair in [start_year, end_year], match players
    who qualified (>= MIN_MINUTES_QUALIFIER minutes) in BOTH seasons and, per
    system, record two things: the correlation between a player's rating one
    season and the next (reliability, scale-free so league drift cancels), and
    the share of the top-`top_n` players one season still in the top-`top_n` the
    next (elite-tier retention). Reads only the cached unified tables, so it
    makes no network calls. Returns {"corr": {sys: [r, ...]},
    "retention": {sys: [share, ...]}, "pairs": [(y, y+1), ...]}.
    """
    systems = systems or PANEL_SYSTEMS
    corr: dict[str, list[float]] = {s: [] for s in systems}
    retention: dict[str, list[float]] = {s: [] for s in systems}
    pairs: list[tuple[int, int]] = []

    _cache: dict[int, pd.DataFrame] = {}

    def _load(y: int) -> pd.DataFrame:
        if y not in _cache:
            _cache[y] = load_unified_ratings(y)
        return _cache[y]

    for y in range(start_year, end_year):
        a, b = _load(y), _load(y + 1)
        if a.empty or b.empty or "player_id" not in a.columns or "player_id" not in b.columns:
            continue
        qa = a[a["QUALIFIED"] == True] if "QUALIFIED" in a.columns else a
        qb = b[b["QUALIFIED"] == True] if "QUALIFIED" in b.columns else b
        had_pair = False
        for s in systems:
            if s not in qa.columns or s not in qb.columns:
                continue
            left = qa[["player_id", s]].dropna().rename(columns={s: "a"})
            right = qb[["player_id", s]].dropna().rename(columns={s: "b"})
            m = left.merge(right, on="player_id")
            if len(m) >= 10 and m["a"].std() > 0 and m["b"].std() > 0:
                corr[s].append(float(np.corrcoef(m["a"], m["b"])[0, 1]))
                had_pair = True
            if len(left) >= top_n and len(right) >= top_n:
                top_a = set(left.nlargest(top_n, "a")["player_id"])
                top_b = set(right.nlargest(top_n, "b")["player_id"])
                retention[s].append(len(top_a & top_b) / top_n)
        if had_pair:
            pairs.append((y, y + 1))

    return {"corr": corr, "retention": retention, "pairs": pairs}


def _unique_r2(df: pd.DataFrame, systems: list[str]) -> dict[str, float]:
    """For each system, estimate unique variance it explains beyond the others.

    Method: regress each system on all others; the residual R² is the
    unique signal. Returns {system: unique_r2}.
    """
    present = _present_systems(df, systems)
    if len(present) < 3:
        return {}

    result = {}
    for s in present:
        others = [o for o in present if o != s]
        sub = df[present].dropna()
        if len(sub) < 20:
            result[s] = 0.0
            continue
        X = sub[others].values
        y = sub[s].values
        coef, _, _, _ = np.linalg.lstsq(
            np.column_stack([np.ones(len(X)), X]), y, rcond=None
        )
        y_hat = np.column_stack([np.ones(len(X)), X]) @ coef
        ss_res = ((y - y_hat) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        result[s] = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    return result


def run(end_year: int = 2025) -> None:
    """Run all analysis sections and print results to stdout."""
    df_full = load_unified_ratings(end_year)
    qual = df_full[df_full["QUALIFIED"] == True].copy() if "QUALIFIED" in df_full.columns else df_full.copy()
    present = _present_systems(qual, ALL_SYSTEMS)

    header = lambda title: print(f"\n{'─' * 3} {title} {'─' * max(0, 60 - len(title))}")

    header("DATA COVERAGE")
    print(f"Season: {end_year - 1}–{str(end_year)[-2:]}")
    print(f"Total players in unified table: {len(df_full)}")
    print(f"Qualified players (>= {MIN_MINUTES_QUALIFIER} min): {len(qual)}")
    print(f"Rating systems present: {len(present)}")
    FACTS.set("cov.n_total", len(df_full), "{:d}", note="total players in unified table")
    FACTS.set("cov.n_qualified", len(qual), "{:d}", note=f"qualified players (>= {MIN_MINUTES_QUALIFIER} min)")
    FACTS.set("cov.n_systems", len(present), "{:d}", note="rating systems present in data")
    for s in present:
        n_valid = qual[s].notna().sum()
        print(f"  {SYSTEM_LABELS.get(s, s)}: {n_valid} players with data")

    # RAPM games coverage
    if "RAPM" in df_full.columns:
        n_rapm = int(df_full["RAPM"].notna().sum())
        print(f"  RAPM players with computed values: {n_rapm}")
        FACTS.set("cov.rapm_n_players", n_rapm, "{:d}",
                  note="players with computed RAPM values")

    # RAPM detail — computed in-house this report from 2024-25 play-by-play, a
    # single season with no box-score prior. Registers the top of the list (to
    # show the single-season noise) and how far it sits from the box-score
    # systems (its independence from them).
    if "RAPM" in qual.columns and qual["RAPM"].notna().sum() >= 20:
        header("RAPM — COMPUTED SINGLE-SEASON (NO PRIOR)")
        rq = qual[qual["RAPM"].notna()].copy()
        top5 = rq.nlargest(5, "RAPM")
        for rank, (_, row) in enumerate(top5.iterrows(), 1):
            print(f"  {rank}. {row['PLAYER_NAME']}: RAPM {row['RAPM']:+.2f} per 100")
            FACTS.set(f"rapm.top.{rank}.name", str(row["PLAYER_NAME"]),
                      note=f"single-season RAPM rank {rank} (qualified players)")
        box = [b for b in ("GAME_SCORE", "PER", "WS", "WS48", "BPM", "VORP")
               if b in rq.columns]
        box_corrs = []
        for b in box:
            pair = rq[[b, "RAPM"]].dropna()
            if len(pair) > 10:
                box_corrs.append(abs(pair[b].corr(pair["RAPM"], method="spearman")))
        mean_box_corr = float(np.mean(box_corrs)) if box_corrs else float("nan")
        print(f"  Mean rank agreement with box-score systems: {mean_box_corr:.2f}")
        FACTS.set("rapm.box_corr_mean", mean_box_corr, "{:.2f}",
                  note="mean abs rank corr of single-season RAPM with box-score systems")
        FACTS.guard("rapm_diverges_from_box", mean_box_corr < 0.40,
                    "single-season RAPM diverges from the box-score systems "
                    "(mean rank agreement below 0.40)", mean_box_corr)
        # Does the noisy single-season RAPM #1 land anywhere near the consensus
        # top tier? (Illustrates why every public system adds a prior.) The
        # CONSENSUS column is built later in run(), so compute it locally here.
        cons = _build_consensus(qual, present)
        cons_order = (qual.assign(_C=cons).dropna(subset=["_C"])
                      .sort_values("_C", ascending=False).reset_index(drop=True))
        top_name = top5.iloc[0]["PLAYER_NAME"]
        match = cons_order.index[cons_order["PLAYER_NAME"] == top_name]
        if len(match):
            rapm1_consensus_rank = int(match[0]) + 1
            print(f"  RAPM #1 ({top_name}) consensus rank: {rapm1_consensus_rank}")
            FACTS.set("rapm.top1_consensus_rank", rapm1_consensus_rank, "{:d}",
                      note="consensus rank of the single-season RAPM #1 player")

    # RAPM_MY detail — the prior-informed, multi-year version. Registers its top
    # (should be recognizable stars, not single-season noise) and how much closer
    # it sits to the box-score systems and the consensus than bare RAPM does.
    if "RAPM_MY" in qual.columns and qual["RAPM_MY"].notna().sum() >= 20:
        header("RAPM_MY — PRIOR-INFORMED, MULTI-YEAR")
        rq = qual[qual["RAPM_MY"].notna()].copy()
        top5 = rq.nlargest(5, "RAPM_MY")
        for rank, (_, row) in enumerate(top5.iterrows(), 1):
            print(f"  {rank}. {row['PLAYER_NAME']}: RAPM_MY {row['RAPM_MY']:+.2f} per 100")
            FACTS.set(f"rapm_my.top.{rank}.name", str(row["PLAYER_NAME"]),
                      note=f"RAPM_MY rank {rank} (qualified players)")
        box = [b for b in ("GAME_SCORE", "PER", "WS", "WS48", "BPM", "VORP")
               if b in rq.columns]
        box_corrs = []
        for b in box:
            pair = rq[[b, "RAPM_MY"]].dropna()
            if len(pair) > 10:
                box_corrs.append(abs(pair[b].corr(pair["RAPM_MY"], method="spearman")))
        my_box_corr = float(np.mean(box_corrs)) if box_corrs else float("nan")
        print(f"  Mean rank agreement with box-score systems: {my_box_corr:.2f}")
        FACTS.set("rapm_my.box_corr_mean", my_box_corr, "{:.2f}",
                  note="mean abs rank corr of RAPM_MY with box-score systems")
        # Correlation with the consensus, and how it compares to bare RAPM, is the
        # face-validity check that the prior + pooling sharpened the metric.
        cons = _build_consensus(qual, present)
        cons_pair = qual.assign(_C=cons)[["RAPM_MY", "_C"]].dropna()
        if len(cons_pair) > 10:
            my_cons = abs(cons_pair["RAPM_MY"].corr(cons_pair["_C"], method="spearman"))
            print(f"  Rank agreement with the consensus: {my_cons:.2f}")
            FACTS.set("rapm_my.consensus_corr", float(my_cons), "{:.2f}",
                      note="RAPM_MY rank agreement with the consensus rating")
        bare_pair = qual.assign(_C=cons)[["RAPM", "_C"]].dropna() \
            if "RAPM" in qual.columns else None
        if bare_pair is not None and len(bare_pair) > 10:
            bare_cons = abs(bare_pair["RAPM"].corr(bare_pair["_C"], method="spearman"))
            FACTS.set("rapm.consensus_corr", float(bare_cons), "{:.2f}",
                      note="bare single-season RAPM rank agreement with the consensus")
            if len(cons_pair) > 10:
                FACTS.guard("rapm_my_beats_bare_consensus", my_cons > bare_cons,
                            "RAPM_MY tracks the consensus better than bare RAPM",
                            f"{my_cons:.2f} vs {bare_cons:.2f}")

    # RAPM vs public snapshot comparison (no-ops when RAPM_PUBLIC is absent)
    if "RAPM" in df_full.columns and "RAPM_PUBLIC" in df_full.columns:
        header("RAPM: COMPUTED VS PUBLIC SNAPSHOT")
        cmp = df_full[["RAPM", "RAPM_PUBLIC"]].dropna()
        if len(cmp) >= 10:
            r = float(np.corrcoef(cmp["RAPM"], cmp["RAPM_PUBLIC"])[0, 1])
            mad = float((cmp["RAPM"] - cmp["RAPM_PUBLIC"]).abs().mean())
            print(f"  Players with both values: {len(cmp)}")
            print(f"  Pearson r: {r:.3f}")
            print(f"  Mean absolute difference: {mad:.2f} pts/100")
            FACTS.set("rapm_val.r", r, "{:.3f}",
                      note="Pearson r between computed RAPM and public snapshot")
            FACTS.set("rapm_val.mad", mad, "{:.2f}",
                      note="mean absolute diff computed RAPM vs public snapshot (pts/100)")
            FACTS.guard("rapm_val_reasonable", r > 0.70,
                        "computed RAPM correlates with public snapshot (r > 0.70)", r)
        else:
            print(f"  Too few overlapping players ({len(cmp)}) for comparison")

    header("BASIC DISTRIBUTION STATS")
    for s in present:
        vals = qual[s].dropna().values
        if len(vals) < 5:
            continue
        print(f"\n{SYSTEM_LABELS.get(s, s)} (n={len(vals)}):")
        print(f"  Mean: {vals.mean():.2f}  Median: {np.median(vals):.2f}  "
              f"Std: {vals.std():.2f}")
        print(f"  Min: {vals.min():.2f}  Max: {vals.max():.2f}")
        _skew = float(stats.skew(vals))
        _exkurt = float(stats.kurtosis(vals))  # excess kurtosis (0 = normal)
        _frac_neg = float(np.mean(vals < 0))
        print(f"  Gini: {_gini(vals):.3f}  Top-5% share: {_top_share(vals)*100:.1f}%")
        print(f"  Skew: {_skew:+.2f}  Excess kurtosis: {_exkurt:+.2f}  "
              f"Below zero: {_frac_neg*100:.0f}%")
        FACTS.set(f"dist.{s}.skew", _skew, "{:+.2f}", note=f"{SYSTEM_LABELS.get(s, s)} skewness")
        FACTS.set(f"dist.{s}.exkurt", _exkurt, "{:+.2f}", note=f"{SYSTEM_LABELS.get(s, s)} excess kurtosis (0 = normal)")
        FACTS.set(f"dist.{s}.frac_neg", _frac_neg * 100, "{:.0f}",
                  note=f"{SYSTEM_LABELS.get(s, s)} share of qualified players below zero (percent)")
        FACTS.set(f"dist.{s}.mean", float(vals.mean()), "{:.2f}", note=f"{SYSTEM_LABELS.get(s, s)} mean")
        FACTS.set(f"dist.{s}.median", float(np.median(vals)), "{:.2f}", note=f"{SYSTEM_LABELS.get(s, s)} median")
        FACTS.set(f"dist.{s}.std", float(vals.std()), "{:.2f}", note=f"{SYSTEM_LABELS.get(s, s)} std dev")
        FACTS.set(f"dist.{s}.min", float(vals.min()), "{:.2f}", note=f"{SYSTEM_LABELS.get(s, s)} min")
        FACTS.set(f"dist.{s}.max", float(vals.max()), "{:.2f}", note=f"{SYSTEM_LABELS.get(s, s)} max")
        FACTS.set(f"dist.{s}.gini", float(_gini(vals)), "{:.3f}", note=f"{SYSTEM_LABELS.get(s, s)} Gini coefficient")
        FACTS.set(f"dist.{s}.top5pct", float(_top_share(vals) * 100), "{:.1f}", unit="%",
                  note=f"{SYSTEM_LABELS.get(s, s)} top-5% share of total value")
    # Guard: VORP concentrates value more steeply than Win Shares and PER
    if "VORP" in qual.columns and "WS" in qual.columns:
        _vorp_top5 = _top_share(qual["VORP"].dropna().values, 0.05)
        _ws_top5 = _top_share(qual["WS"].dropna().values, 0.05)
        FACTS.guard("vorp_more_concentrated_than_ws", _vorp_top5 > _ws_top5,
                    "VORP concentrates value more steeply than Win Shares", _vorp_top5)
    if "VORP" in qual.columns and "PER" in qual.columns:
        _vorp_top5 = _top_share(qual["VORP"].dropna().values, 0.05)
        _per_top5 = _top_share(qual["PER"].dropna().values, 0.05)
        FACTS.guard("vorp_more_concentrated_than_per", _vorp_top5 > _per_top5,
                    "VORP top-5% share far exceeds PER", _vorp_top5)
    # Guard: RAPM is a near-symmetric, roughly Gaussian rate, not a power law.
    # A power law needs a heavy one-sided tail (large positive skew). RAPM's skew
    # sits near zero; VORP, an accumulation metric, carries the right-skew tail.
    if "RAPM" in qual.columns and qual["RAPM"].notna().sum() >= 20:
        _rapm_vals = qual["RAPM"].dropna().values
        _rapm_skew = float(stats.skew(_rapm_vals))
        FACTS.guard("rapm_symmetric_not_powerlaw",
                    abs(_rapm_skew) < 0.5,
                    "RAPM is a near-symmetric bell (skew near zero), not the "
                    "heavy-tailed shape a power law needs",
                    _rapm_skew)
        if "VORP" in qual.columns:
            _vorp_skew = float(stats.skew(qual["VORP"].dropna().values))
            FACTS.guard("rapm_less_skewed_than_vorp",
                        abs(_rapm_skew) < abs(_vorp_skew),
                        "RAPM is far less skewed than the right-skewed accumulation metric VORP",
                        _vorp_skew - abs(_rapm_skew))

    header("POWER-LAW FIT (VALUE VS RANK, LOG-LOG)")
    print(f"A system's top-{50} value-vs-rank curve is a power law when the")
    print(f"log-log fit clears R^2 >= {POWERLAW_R2_THRESHOLD:.2f} (a straight line on log-log axes).")
    power_law_systems = []
    for s in present:
        vals = qual[s].dropna().sort_values(ascending=False).values
        fit = powerlaw_fit(vals, top_n=50)
        if fit is None:
            continue
        is_power = fit["r2"] >= POWERLAW_R2_THRESHOLD
        verdict = "power law" if is_power else "not a power law (bends)"
        print(f"\n{SYSTEM_LABELS.get(s, s)} (n={fit['n_points']} positive ranks):")
        print(f"  exponent alpha={fit['alpha']:.2f}  R^2={fit['r2']:.3f}  -> {verdict}")
        FACTS.set(f"powerlaw.{s}.alpha", fit["alpha"], "{:.2f}",
                  note=f"{SYSTEM_LABELS.get(s, s)} power-law exponent (value ~ rank^-alpha)")
        FACTS.set(f"powerlaw.{s}.r2", fit["r2"], "{:.2f}",
                  note=f"{SYSTEM_LABELS.get(s, s)} log-log power-law fit R^2")
        if is_power:
            power_law_systems.append(s)
    non_power = [s for s in present
                 if powerlaw_fit(qual[s].dropna().sort_values(ascending=False).values, top_n=50)
                 is not None and s not in power_law_systems]
    label_list = ", ".join(SYSTEM_LABELS.get(s, s) for s in power_law_systems) or "none"
    non_list = ", ".join(SYSTEM_LABELS.get(s, s) for s in non_power) or "none"
    print(f"\nPower-law systems (R^2 >= {POWERLAW_R2_THRESHOLD:.2f}): {label_list}")
    print(f"Bend instead of a straight line: {non_list}")
    FACTS.set("powerlaw.n_systems", len(power_law_systems), "{:d}",
              note="systems whose value-vs-rank curve fits a power law")
    FACTS.set("powerlaw.systems", label_list,
              note="names of systems whose value-vs-rank curve fits a power law")
    FACTS.set("powerlaw.non_systems", non_list,
              note="names of systems whose value-vs-rank curve bends (not a power law)")
    # Guards protecting the findings discussion of which cluster is which.
    _alpha = {s: powerlaw_fit(qual[s].dropna().sort_values(ascending=False).values, top_n=50)
              for s in present}
    if _alpha.get("VORP") and _alpha.get("PER"):
        FACTS.guard("cumulative_steeper_than_rate",
                    _alpha["VORP"]["alpha"] > _alpha["PER"]["alpha"],
                    "cumulative VORP falls off more steeply than rate-metric PER",
                    _alpha["VORP"]["alpha"] - _alpha["PER"]["alpha"])
    if "WS" in power_law_systems and "VORP" in power_law_systems:
        FACTS.guard("cumulative_are_power_laws", True,
                    "the cumulative metrics (Win Shares, VORP) are power laws", non_list)
    if _alpha.get("OBPM"):
        FACTS.guard("obpm_bends", "OBPM" not in power_law_systems,
                    "Offensive BPM bends rather than holding a straight power law",
                    _alpha["OBPM"]["r2"])

    header("RANK AGREEMENT (SPEARMAN CORRELATIONS)")
    if len(present) >= 2:
        ranks = qual[present].rank(pct=True)
        corr = ranks.corr(method="spearman")
        # Guards for key pairs cited in prose
        if "BPM" in corr.index and "VORP" in corr.index:
            bpm_vorp_r = float(corr.loc["BPM", "VORP"])
            FACTS.guard("bpm_vorp_tight", bpm_vorp_r > 0.95,
                        "BPM and VORP are tightly linked (r > 0.95)", bpm_vorp_r)
        if "GAME_SCORE" in corr.index and "PER" in corr.index:
            gs_per_r = float(corr.loc["GAME_SCORE", "PER"])
            FACTS.guard("per_gamescore_close", gs_per_r > 0.75,
                        "PER and Game Score track closely (r > 0.75)", gs_per_r)
        # Print upper triangle and register all correlation facts
        for i, si in enumerate(present):
            for j, sj in enumerate(present):
                if j > i:
                    r = corr.loc[si, sj]
                    label_i = SYSTEM_LABELS.get(si, si)
                    label_j = SYSTEM_LABELS.get(sj, sj)
                    print(f"  {label_i} vs {label_j}: r={r:.3f}")
                    FACTS.set(f"corr.{si}_{sj}", float(r), "{:.3f}",
                              note=f"Spearman rank corr: {label_i} vs {label_j}")

    header("WHAT EACH SYSTEM UNIQUELY CAPTURES")
    uniq = _unique_r2(qual, present)
    for s, r2 in sorted(uniq.items(), key=lambda x: -x[1]):
        print(f"  {SYSTEM_LABELS.get(s, s)}: unique R² = {r2:.3f}")
        FACTS.set(f"uniq.{s}.r2", float(r2), "{:.3f}",
                  note=f"{SYSTEM_LABELS.get(s, s)} unique R²: variance beyond what other systems explain")

    header("CONSENSUS RATING — TOP 20")
    qual["CONSENSUS"] = _build_consensus(qual, present)
    if qual["CONSENSUS"].notna().sum() > 0:
        top = qual.nlargest(20, "CONSENSUS")
        for rank, (_, row) in enumerate(top.iterrows(), 1):
            name = row.get("PLAYER_NAME", "Unknown")
            print(f"  {rank:>2}. {name:<30}  Consensus z = {row['CONSENSUS']:.2f}")
            if rank <= 5:
                FACTS.set(f"consensus.top.{rank}.name", str(name),
                          note=f"consensus rank {rank} player name")
                FACTS.set(f"consensus.top.{rank}.z", float(row["CONSENSUS"]), "{:.2f}",
                          note=f"consensus rank {rank} z-score")
        top_name = top.iloc[0].get("PLAYER_NAME", "") if len(top) > 0 else ""
        FACTS.guard("jokic_tops_consensus", top_name == "Nikola Jokić",
                    "Nikola Jokić tops the consensus rating", top_name)

    header("WINS-PREDICTIVE RATING — TOP 20")
    qual["WINS_PRED"] = _build_wins_predictive(qual, present)
    df_full["WINS_PRED"] = np.nan
    if qual["WINS_PRED"].notna().sum() > 0:
        top = qual.nlargest(20, "WINS_PRED")
        for rank, (_, row) in enumerate(top.iterrows(), 1):
            name = row.get("PLAYER_NAME", "Unknown")
            print(f"  {rank:>2}. {name:<30}  Wins-predictive z = {row['WINS_PRED']:.2f}")
            if rank <= 5:
                FACTS.set(f"wins_pred.top.{rank}.name", str(name),
                          note=f"wins-predictive rank {rank} player name")
                FACTS.set(f"wins_pred.top.{rank}.z", float(row["WINS_PRED"]), "{:.2f}",
                          note=f"wins-predictive rank {rank} z-score")

    header("COMPARISON: CONSENSUS vs. WINS-PREDICTIVE")
    if qual["CONSENSUS"].notna().sum() > 0 and qual["WINS_PRED"].notna().sum() > 0:
        both = qual[["PLAYER_NAME", "CONSENSUS", "WINS_PRED", "MIN"]].dropna()
        if len(both) >= 10:
            r, p = stats.spearmanr(both["CONSENSUS"], both["WINS_PRED"])
            print(f"  Spearman correlation between consensus and wins-predictive: {r:.3f} (p={p:.3f})")
            FACTS.set("cmp.spearman", float(r), "{:.3f}",
                      note="Spearman rank corr between consensus and wins-predictive ratings")
            FACTS.guard("strong_consensus_wins_corr", float(r) > 0.90,
                        "the two ratings agree very closely (r > 0.90)", float(r))
            both["_diff"] = both["WINS_PRED"] - both["CONSENSUS"]
            print("  Players rated much higher by wins-predictive than consensus:")
            for idx, (_, row) in enumerate(both.nlargest(5, "_diff").iterrows(), 1):
                print(f"    {row['PLAYER_NAME']:<30}  diff = +{row['_diff']:.2f}")
                FACTS.set(f"cmp.higher.{idx}.name", str(row["PLAYER_NAME"]),
                          note=f"rank {idx} player rated higher by wins-predictive than consensus")
                FACTS.set(f"cmp.higher.{idx}.diff", float(row["_diff"]), "{:.2f}",
                          note=f"rank {idx} wins-predictive minus consensus diff (positive)")
            print("  Players rated much lower by wins-predictive than consensus:")
            for idx, (_, row) in enumerate(both.nsmallest(5, "_diff").iterrows(), 1):
                print(f"    {row['PLAYER_NAME']:<30}  diff = {row['_diff']:.2f}")
                FACTS.set(f"cmp.lower.{idx}.name", str(row["PLAYER_NAME"]),
                          note=f"rank {idx} player rated lower by wins-predictive than consensus")
                FACTS.set(f"cmp.lower.{idx}.diff", float(row["_diff"]), "{:.2f}",
                          note=f"rank {idx} wins-predictive minus consensus diff (negative)")

    header("UBER RATING CONCENTRATION (GINI vs CENTER-ROBUST STEEPNESS)")
    print("Gini clips negatives to zero, so it inflates 0-centered metrics (the uber")
    print("ratings and the BPM family). The power-law exponent alpha does not depend on")
    print("where zero sits, so it is the fair cross-system concentration read.")
    for s in ("CONSENSUS", "WINS_PRED"):
        if s not in qual.columns or qual[s].notna().sum() < 20:
            continue
        vals = qual[s].dropna().values
        g = _gini(vals)
        t5 = _top_share(vals) * 100
        fit = powerlaw_fit(np.sort(vals)[::-1], top_n=50)
        a = fit["alpha"] if fit else float("nan")
        print(f"\n{SYSTEM_LABELS.get(s, s)}: Gini={g:.3f} (inflated), "
              f"top-5% share={t5:.1f}%, alpha={a:.2f}")
        FACTS.set(f"dist.{s}.gini", float(g), "{:.3f}",
                  note=f"{SYSTEM_LABELS.get(s, s)} Gini coefficient (inflated by centering)")
        FACTS.set(f"dist.{s}.top5pct", float(t5), "{:.1f}", unit="%",
                  note=f"{SYSTEM_LABELS.get(s, s)} top-5% share of positive value")
        if fit:
            FACTS.set(f"powerlaw.{s}.alpha", float(a), "{:.2f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} power-law exponent (center-robust steepness)")
    # Guard: on the center-robust measure the combined ratings sit between the
    # flattest rate metric (PER) and the steepest cumulative metric (VORP).
    _cons = powerlaw_fit(np.sort(qual["CONSENSUS"].dropna().values)[::-1], top_n=50) \
        if "CONSENSUS" in qual.columns and qual["CONSENSUS"].notna().sum() >= 20 else None
    if _cons and _alpha.get("PER") and _alpha.get("VORP"):
        FACTS.guard("uber_concentration_between_rate_and_cumulative",
                    _alpha["PER"]["alpha"] < _cons["alpha"] < _alpha["VORP"]["alpha"],
                    "by center-robust steepness the consensus rating sits between PER and VORP",
                    _cons["alpha"])

    header("POWER-LAW / TAIL ANALYSIS")
    cumulative_metrics = [s for s in present if s in ("WS", "VORP", "RAPTOR_WAR")]
    rate_metrics = [s for s in present if s in ("PER", "BPM", "RAPTOR", "DARKO_DPM", "EPM")]

    for group_label, group in [("Cumulative-value metrics", cumulative_metrics),
                                 ("Rate metrics", rate_metrics)]:
        print(f"\n{group_label}:")
        for s in group:
            vals = qual[s].dropna().values
            if len(vals) < 10:
                continue
            pos_vals = vals[vals > 0]
            gini = _gini(vals)
            top5 = _top_share(vals, 0.05)
            print(f"  {SYSTEM_LABELS.get(s, s)}: Gini={gini:.3f}, top-5% hold {top5*100:.1f}% of value")
            if len(pos_vals) >= 10:
                # Skewness
                skew = float(stats.skew(pos_vals))
                print(f"    Skewness: {skew:.2f} ({'right-skewed' if skew > 0.5 else 'near-symmetric'})")
                FACTS.set(f"tail.{s}.skew", skew, "{:.2f}",
                          note=f"{SYSTEM_LABELS.get(s, s)} skewness (positive values only)")

    header("WHO EACH SYSTEM LOVES vs. CONSENSUS")
    qual["CONSENSUS"] = _build_consensus(qual, present)
    for s in present[:8]:  # top 8 systems only to keep output manageable
        z_s = (qual[s] - qual[s].mean()) / qual[s].std() if qual[s].std() > 0 else 0
        residual = z_s - qual["CONSENSUS"]
        top3 = qual.assign(_res=residual).nlargest(3, "_res")
        bot3 = qual.assign(_res=residual).nsmallest(3, "_res")
        print(f"\n{SYSTEM_LABELS.get(s, s)} loves (vs. consensus):")
        for rank, (_, row) in enumerate(top3.iterrows(), 1):
            print(f"  +{row.get('_res', 0):.2f}  {row.get('PLAYER_NAME', '?')}")
            FACTS.set(f"loves.{s}.{rank}.name", str(row.get("PLAYER_NAME", "?")),
                      note=f"{SYSTEM_LABELS.get(s, s)} loves rank {rank} player vs consensus")
            FACTS.set(f"loves.{s}.{rank}.diff", float(row.get("_res", 0)), "{:.2f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} loves rank {rank} residual vs consensus (positive)")
        print(f"{SYSTEM_LABELS.get(s, s)} discounts (vs. consensus):")
        for rank, (_, row) in enumerate(bot3.iterrows(), 1):
            print(f"  {row.get('_res', 0):.2f}  {row.get('PLAYER_NAME', '?')}")
            FACTS.set(f"discounts.{s}.{rank}.name", str(row.get("PLAYER_NAME", "?")),
                      note=f"{SYSTEM_LABELS.get(s, s)} discounts rank {rank} player vs consensus")
            FACTS.set(f"discounts.{s}.{rank}.diff", float(row.get("_res", 0)), "{:.2f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} discounts rank {rank} residual vs consensus (negative)")

    header("RETRODICTION: WHICH RATING REBUILDS TEAM RESULTS")
    print("Each system's player ratings are minutes-weighted to the team level, then")
    print("fit to team point differential per game across the 30 teams. R² is the")
    print("in-sample fit; CV R² is leave-one-team-out (the honest out-of-sample read).")
    print("Systems marked [team-fit] are built using team or lineup point")
    print("differential, so a high score is partly mechanical. Systems marked")
    print("[outcome-blind] never saw who won; their score is the genuine test.")
    outcomes = load_team_outcomes(end_year)
    retro = retrodiction_scores(df_full, outcomes, present, target="point_diff")
    if retro:
        ranked = sorted(retro.items(), key=lambda kv: -kv[1]["cv_r2"])
        print()
        for s, sc in ranked:
            tag = "[team-fit]    " if s in OUTCOME_CALIBRATED else "[outcome-blind]"
            print(f"  {tag} {SYSTEM_LABELS.get(s, s):<14} "
                  f"R²={sc['r2']:.3f}  CV R²={sc['cv_r2']:.3f}")
            FACTS.set(f"retro.{s}.r2", sc["r2"], "{:.3f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} team point-diff retrodiction R² (in-sample)")
            FACTS.set(f"retro.{s}.cv_r2", sc["cv_r2"], "{:.3f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} retrodiction R² (leave-one-team-out CV)")

        top_sys, top_sc = ranked[0]
        top_label = SYSTEM_LABELS.get(top_sys, top_sys)
        print(f"\nTop retrodictor: {top_label} (CV R²={top_sc['cv_r2']:.3f}); it "
              f"rebuilds {top_sc['cv_r2'] * 100:.0f}% of the team point-differential")
        print("spread out of sample.")
        FACTS.set("retro.top.name", str(top_label),
                  note="system that best retrodicts team point differential (CV)")
        FACTS.set("retro.top.cv_r2", float(top_sc["cv_r2"]), "{:.3f}",
                  note="top system's leave-one-team-out retrodiction R²")
        FACTS.set("retro.top.cv_r2_pct", float(top_sc["cv_r2"] * 100), "{:.0f}",
                  note="top system's retrodiction R² as a percent (append % in prose)")
        if top_sys not in OUTCOME_CALIBRATED:
            print(f"{top_label} never uses who won, yet it beats the team-adjusted box")
            print("metrics (BPM, VORP, Win Shares) here. Caveat: this project's BPM and")
            print("VORP are approximate recomputes, so their lower scores partly reflect a")
            print("noisy recompute, not proof PER is the better rating. Rerun once exactly")
            print("computed or published impact metrics (EPM, DARKO, RAPTOR) are loaded.")
        FACTS.guard("blind_rating_tops_retrodiction",
                    top_sys not in OUTCOME_CALIBRATED,
                    "an outcome-blind box rating tops the team point-differential "
                    "retrodiction, ahead of the team-adjusted metrics",
                    top_label)

    header("NEXT-SEASON RETRODICTION (PREDICTING THIS SEASON FROM LAST)")
    print(f"Last season's ({end_year - 2}-{str(end_year - 1)[-2:]}) player ratings are")
    print("distributed across this season's rosters (weighted by this season's minutes)")
    print("and fit to this season's team point differential. Because each metric's team")
    print("adjustment is fit to its own season, predicting the next season removes the")
    print("in-sample circularity. Describing the season just played and forecasting the")
    print("next are different tests, and they reward different metrics.")
    prior = load_unified_ratings(end_year - 1)
    nxt = (next_season_retrodiction(prior, df_full, outcomes, present, target="point_diff")
           if not prior.empty else {})
    if nxt and retro:
        cover = float(np.mean([v["coverage"] for v in nxt.values()]))
        print(f"\nPrior-rating coverage: {cover * 100:.0f}% of this season's team minutes")
        print("were played by players who also carried a rating last season.\n")
        FACTS.set("nextretro.coverage_pct", cover * 100, "{:.0f}",
                  note="share of current-season team minutes with a prior-season rating")
        ranked_n = sorted(nxt.items(), key=lambda kv: -kv[1]["r2"])
        print(f"  {'':<16}{'describes':>10}{'predicts':>10}")
        print(f"  {'system':<16}{'(same yr)':>10}{'(next yr)':>10}")
        for s, sc in ranked_n:
            same_cv = retro.get(s, {}).get("cv_r2", float("nan"))
            tag = "[team-fit]    " if s in OUTCOME_CALIBRATED else "[outcome-blind]"
            print(f"  {tag} {SYSTEM_LABELS.get(s, s):<14}{same_cv:>8.3f}{sc['r2']:>10.3f}")
            FACTS.set(f"nextretro.{s}.r2", sc["r2"], "{:.3f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} next-season retrodiction R² "
                           f"(predict {end_year - 1}->{end_year})")
        top_n_sys, top_n_sc = ranked_n[0]
        top_n_label = SYSTEM_LABELS.get(top_n_sys, top_n_sys)
        top_same = max(retro.items(), key=lambda kv: kv[1]["cv_r2"])[0]
        top_same_label = SYSTEM_LABELS.get(top_same, top_same)
        print(f"\nBest forecaster of next season: {top_n_label} (R²={top_n_sc['r2']:.3f}). "
              f"Best description of\nthe season itself: {top_same_label}.")
        FACTS.set("nextretro.top.name", str(top_n_label),
                  note="system that best predicts next-season team point differential")
        FACTS.set("nextretro.top.r2", float(top_n_sc["r2"]), "{:.3f}",
                  note="best next-season retrodiction R²")
        FACTS.set("nextretro.top.r2_pct", float(top_n_sc["r2"] * 100), "{:.0f}",
                  note="best next-season retrodiction R² as percent (append % in prose)")
        FACTS.guard("forecast_top_differs_from_description_top",
                    top_n_sys != top_same,
                    "the metric that best forecasts next season is not the one that best "
                    "describes the season just played",
                    f"{top_n_label} vs {top_same_label}")
        if "PER" in nxt and "PER" in retro:
            print(f"PER falls from {retro['PER']['cv_r2']:.2f} describing the season to "
                  f"{nxt['PER']['r2']:.2f}\nforecasting the next: a strong descriptor, a weak predictor.")
            FACTS.set("nextretro.PER.r2_pct", float(nxt["PER"]["r2"] * 100), "{:.0f}",
                      note="PER next-season retrodiction R² as percent (append % in prose)")
            FACTS.guard("per_describes_better_than_predicts",
                        nxt["PER"]["r2"] < retro["PER"]["cv_r2"],
                        "PER describes the season far better than it forecasts the next",
                        retro["PER"]["cv_r2"] - nxt["PER"]["r2"])

    header("MULTI-SEASON DESCRIBE vs FORECAST (FULL PANEL)")
    print(f"The single pair above is one season. This pools the same two tests")
    print(f"across every season in the cache: {PANEL_END_YEAR - PANEL_START_YEAR + 1} seasons")
    print(f"({PANEL_START_YEAR - 1}-{str(PANEL_START_YEAR)[-2:]} through "
          f"{PANEL_END_YEAR - 1}-{str(PANEL_END_YEAR)[-2:]}) for the describe test and")
    print(f"the {PANEL_END_YEAR - PANEL_START_YEAR} consecutive season-pairs for the forecast test.")
    print("Each number below is the average R² across all of those seasons (describe)")
    print("or pairs (forecast), with the season-to-season range in brackets. Pooling")
    print("this way shows whether the one-season flip is a fluke or a standing pattern.")
    panel = panel_retrodiction(PANEL_START_YEAR, PANEL_END_YEAR, PANEL_SYSTEMS)
    d_means = {s: float(np.mean(v)) for s, v in panel["describe"].items() if v}
    f_means = {s: float(np.mean(v)) for s, v in panel["forecast"].items() if v}
    if d_means and f_means:
        n_seasons = len(panel["seasons"])
        n_pairs = len(panel["pairs"])
        FACTS.set("panel.n_seasons", n_seasons, "{:d}", note="seasons in the pooled panel")
        FACTS.set("panel.n_pairs", n_pairs, "{:d}", note="consecutive season-pairs in the panel")
        FACTS.set("panel.first_season", f"{PANEL_START_YEAR - 1}-{str(PANEL_START_YEAR)[-2:]}",
                  note="first season in the pooled panel")
        FACTS.set("panel.last_season", f"{PANEL_END_YEAR - 1}-{str(PANEL_END_YEAR)[-2:]}",
                  note="last season in the pooled panel")

        ranked_f = sorted(f_means.items(), key=lambda kv: -kv[1])
        print(f"\n  {'':<16}{'describes':>12}{'predicts':>12}")
        print(f"  {'system':<16}{'(same yr)':>12}{'(next yr)':>12}")
        for s, fmean in ranked_f:
            dmean = d_means.get(s, float("nan"))
            d_lo, d_hi = min(panel["describe"][s]), max(panel["describe"][s])
            f_lo, f_hi = min(panel["forecast"][s]), max(panel["forecast"][s])
            tag = "[team-fit]    " if s in OUTCOME_CALIBRATED else "[outcome-blind]"
            print(f"  {tag} {SYSTEM_LABELS.get(s, s):<14}"
                  f"{dmean:>7.3f} [{d_lo:.2f},{d_hi:.2f}]  "
                  f"{fmean:>6.3f} [{f_lo:.2f},{f_hi:.2f}]")
            FACTS.set(f"panel.{s}.describe_mean", dmean, "{:.3f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} mean same-season (describe) R² across the panel")
            FACTS.set(f"panel.{s}.forecast_mean", fmean, "{:.3f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} mean next-season (forecast) R² across the panel")

        describe_top = max(d_means.items(), key=lambda kv: kv[1])[0]
        forecast_top = max(f_means.items(), key=lambda kv: kv[1])[0]
        d_top_label = SYSTEM_LABELS.get(describe_top, describe_top)
        f_top_label = SYSTEM_LABELS.get(forecast_top, forecast_top)
        print(f"\nAcross {n_seasons} seasons the best description is {d_top_label}; across")
        print(f"{n_pairs} pairs the best forecast is {f_top_label}.")
        FACTS.set("panel.describe_top.name", str(d_top_label),
                  note="system with the best average same-season (describe) R² across the panel")
        FACTS.set("panel.forecast_top.name", str(f_top_label),
                  note="system with the best average next-season (forecast) R² across the panel")

        if "PER" in d_means and "PER" in f_means:
            print(f"PER averages {d_means['PER']:.2f} describing but only "
                  f"{f_means['PER']:.2f} forecasting,\nthe same collapse the single pair "
                  f"showed, now seen across {n_pairs} pairs.")
            FACTS.set("panel.PER.describe_mean_pct", d_means["PER"] * 100, "{:.0f}",
                      note="PER mean describe R² across the panel, percent (append % in prose)")
            FACTS.set("panel.PER.forecast_mean_pct", f_means["PER"] * 100, "{:.0f}",
                      note="PER mean forecast R² across the panel, percent (append % in prose)")
        if forecast_top in f_means:
            FACTS.set("panel.forecast_top.mean_pct", f_means[forecast_top] * 100, "{:.0f}",
                      note="best forecaster's mean forecast R² across the panel, percent (append % in prose)")

        # Per-pair robustness: in how many pairs does the team-fit BPM forecast
        # beat outcome-blind PER? Firms up that the flip is the standing pattern.
        if "BPM" in panel["forecast"] and "PER" in panel["forecast"]:
            bpm_f = panel["forecast"]["BPM"]
            per_f = panel["forecast"]["PER"]
            n_cmp = min(len(bpm_f), len(per_f))
            n_bpm_wins = sum(1 for i in range(n_cmp) if bpm_f[i] > per_f[i])
            print(f"BPM forecasts better than PER in {n_bpm_wins} of {n_cmp} pairs.")
            FACTS.set("panel.bpm_beats_per_pairs", n_bpm_wins, "{:d}",
                      note="season-pairs where BPM forecasts better than PER")
            FACTS.set("panel.n_cmp_pairs", n_cmp, "{:d}",
                      note="season-pairs with both BPM and PER forecast scores")

        FACTS.guard("panel_forecast_top_differs_from_describe_top",
                    forecast_top != describe_top,
                    "across the full panel the best forecaster is not the best describer",
                    f"{f_top_label} vs {d_top_label}")
        if "PER" in d_means and "PER" in f_means:
            FACTS.guard("panel_per_describes_better_than_forecasts",
                        d_means["PER"] > f_means["PER"],
                        "across the full panel PER describes better than it forecasts",
                        d_means["PER"] - f_means["PER"])

    header("IMPACT-ERA PANEL: BOX SCORES vs RAPM (EQUAL SEASONS)")
    print("The panel above runs 30 seasons, but RAPM can only be computed for the")
    print(f"{RAPM_PANEL_END_YEAR - RAPM_PANEL_START_YEAR + 1} seasons with cached play-by-play "
          f"({RAPM_PANEL_START_YEAR - 1}-{str(RAPM_PANEL_START_YEAR)[-2:]} through "
          f"{RAPM_PANEL_END_YEAR - 1}-{str(RAPM_PANEL_END_YEAR)[-2:]}).")
    print("This second panel scores the box-score systems AND RAPM over those same")
    print("seasons, so the comparison is even. RAPM is built from lineup point")
    print("differential, so its DESCRIBE score (rebuilding the same season's team")
    print("margin) is partly mechanical; the FORECAST score (prior-season RAPM onto")
    print("next season's rosters) is the honest read.")
    ipanel = panel_retrodiction(RAPM_PANEL_START_YEAR, RAPM_PANEL_END_YEAR,
                                RAPM_PANEL_SYSTEMS)
    id_means = {s: float(np.mean(v)) for s, v in ipanel["describe"].items() if v}
    if_means = {s: float(np.mean(v)) for s, v in ipanel["forecast"].items() if v}
    if id_means and if_means and "RAPM" in if_means:
        i_n_seasons = len(ipanel["seasons"])
        i_n_pairs = len(ipanel["pairs"])
        FACTS.set("ipanel.n_seasons", i_n_seasons, "{:d}",
                  note="seasons in the impact-era panel")
        FACTS.set("ipanel.n_pairs", i_n_pairs, "{:d}",
                  note="consecutive season-pairs in the impact-era panel")
        FACTS.set("ipanel.first_season",
                  f"{RAPM_PANEL_START_YEAR - 1}-{str(RAPM_PANEL_START_YEAR)[-2:]}",
                  note="first season in the impact-era panel")

        ranked_if = sorted(if_means.items(), key=lambda kv: -kv[1])
        print(f"\n  {'':<16}{'describes':>12}{'predicts':>12}")
        print(f"  {'system':<16}{'(same yr)':>12}{'(next yr)':>12}")
        for s, fmean in ranked_if:
            dmean = id_means.get(s, float("nan"))
            tag = "[team-fit]    " if s in OUTCOME_CALIBRATED else "[outcome-blind]"
            print(f"  {tag} {SYSTEM_LABELS.get(s, s):<14}{dmean:>7.3f}  {fmean:>10.3f}")
            FACTS.set(f"ipanel.{s}.describe_mean", dmean, "{:.3f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} mean describe R² (impact-era panel)")
            FACTS.set(f"ipanel.{s}.forecast_mean", fmean, "{:.3f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} mean forecast R² (impact-era panel)")

        i_forecast_top = ranked_if[0][0]
        i_forecast_top_label = SYSTEM_LABELS.get(i_forecast_top, i_forecast_top)
        rapm_forecast_rank = [s for s, _ in ranked_if].index("RAPM") + 1
        n_ipanel_systems = len(ranked_if)
        FACTS.set("ipanel.forecast_top.name", str(i_forecast_top_label),
                  note="best forecaster in the impact-era panel")
        FACTS.set("ipanel.forecast_top.mean_pct", if_means[i_forecast_top] * 100, "{:.0f}",
                  note="best impact-era forecaster's mean forecast R², percent (append % in prose)")
        FACTS.set("ipanel.RAPM.forecast_rank", rapm_forecast_rank, "{:d}",
                  note="RAPM's rank among systems as a forecaster in the impact-era panel")
        FACTS.set("ipanel.n_systems", n_ipanel_systems, "{:d}",
                  note="systems compared in the impact-era panel")
        FACTS.set("ipanel.RAPM.forecast_mean_pct", if_means["RAPM"] * 100, "{:.0f}",
                  note="RAPM mean forecast R² (impact-era panel), percent (append % in prose)")
        FACTS.set("ipanel.RAPM.describe_mean_pct", id_means["RAPM"] * 100, "{:.0f}",
                  note="RAPM mean describe R² (impact-era panel), percent (append % in prose)")
        if "PER" in if_means:
            FACTS.set("ipanel.PER.forecast_mean_pct", if_means["PER"] * 100, "{:.0f}",
                      note="PER mean forecast R² (impact-era panel), percent (append % in prose)")
        print(f"\nOver these {i_n_pairs} pairs RAPM forecasts {rapm_forecast_rank} of "
              f"{n_ipanel_systems}; the best forecaster is {i_forecast_top_label}.")
        FACTS.guard("rapm_in_impact_panel", i_n_pairs >= 5 and "RAPM" in if_means,
                    "RAPM is scored across the impact-era panel alongside the box scores",
                    f"{i_n_pairs} pairs")

        # RAPM_MY in the panel: the prior + multi-year version should forecast
        # next-season team results better than bare RAPM (the headline upgrade).
        if "RAPM_MY" in if_means:
            my_rank = [s for s, _ in ranked_if].index("RAPM_MY") + 1
            FACTS.set("ipanel.RAPM_MY.forecast_rank", my_rank, "{:d}",
                      note="RAPM_MY's rank among systems as a forecaster in the impact-era panel")
            FACTS.set("ipanel.RAPM_MY.forecast_mean_pct", if_means["RAPM_MY"] * 100, "{:.0f}",
                      note="RAPM_MY mean forecast R² (impact-era panel), percent (append % in prose)")
            print(f"RAPM_MY forecasts {my_rank} of {n_ipanel_systems} "
                  f"(bare RAPM was {rapm_forecast_rank}).")
            FACTS.guard("rapm_my_forecasts_better_than_bare",
                        if_means["RAPM_MY"] > if_means["RAPM"],
                        "RAPM_MY forecasts next-season team results better than bare RAPM",
                        f"{if_means['RAPM_MY']:.3f} vs {if_means['RAPM']:.3f}")

    header("PLAYER RATING STABILITY (YEAR OVER YEAR)")
    print("A different lens: not how well a rating predicts team results, but how")
    print("much a player's own rating carries from one season to the next. For every")
    print(f"pair of seasons, players who qualified ({MIN_MINUTES_QUALIFIER}+ minutes) in both are")
    print("matched, and each system gets two numbers: the correlation between a")
    print("player's rating this season and next (1.0 = perfectly sticky, 0 = a coin")
    print(f"flip), and the share of the top {STABILITY_TOP_N} one season still in the top")
    print(f"{STABILITY_TOP_N} the next. Stability is persistence, not quality: a rating can be")
    print("sticky because it tracks a real, lasting trait or because it is slow to")
    print("move. These box scores also share inputs (points, rebounds, assists), so")
    print("some of the shared stickiness is mechanical.")
    stab = rating_stability(PANEL_START_YEAR, PANEL_END_YEAR, PANEL_SYSTEMS)
    corr_means = {s: float(np.mean(v)) for s, v in stab["corr"].items() if v}
    ret_means = {s: float(np.mean(v)) for s, v in stab["retention"].items() if v}
    if corr_means:
        n_pairs = len(stab["pairs"])
        chance = STABILITY_TOP_N / len(qual) if len(qual) else float("nan")
        FACTS.set("stability.n_pairs", n_pairs, "{:d}",
                  note="consecutive season-pairs in the stability panel")
        FACTS.set("stability.top_n", STABILITY_TOP_N, "{:d}",
                  note="elite-tier size for the year-over-year retention measure")
        FACTS.set("stability.chance_pct", chance * 100, "{:.0f}",
                  note="chance-level top-N retention (top-N / qualified pool), percent")
        ranked = sorted(corr_means.items(), key=lambda kv: -kv[1])
        print(f"\n  {'system':<16}{'year-to-year':>14}{'top-' + str(STABILITY_TOP_N) + ' kept':>14}")
        for s, cm in ranked:
            rm = ret_means.get(s, float("nan"))
            c_lo, c_hi = min(stab["corr"][s]), max(stab["corr"][s])
            print(f"  {SYSTEM_LABELS.get(s, s):<16}{cm:>9.3f} [{c_lo:.2f},{c_hi:.2f}]"
                  f"{rm * 100:>10.0f}%")
            FACTS.set(f"stability.{s}.corr", cm, "{:.3f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} year-over-year rating correlation (mean across pairs)")
            FACTS.set(f"stability.{s}.retention_pct", rm * 100, "{:.0f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} top-{STABILITY_TOP_N} retention, percent (append % in prose)")

        most, least = ranked[0], ranked[-1]
        most_label = SYSTEM_LABELS.get(most[0], most[0])
        least_label = SYSTEM_LABELS.get(least[0], least[0])
        ret_top = max(ret_means.items(), key=lambda kv: kv[1])
        ret_top_label = SYSTEM_LABELS.get(ret_top[0], ret_top[0])
        print(f"\nSteadiest year to year: {most_label} (corr {most[1]:.2f}). "
              f"Jumpiest: {least_label} (corr {least[1]:.2f}).")
        print(f"Best at keeping the same names in the top {STABILITY_TOP_N}: "
              f"{ret_top_label} ({ret_top[1] * 100:.0f}%), "
              f"against a chance level near {chance * 100:.0f}%.")
        FACTS.set("stability.most_stable.name", str(most_label),
                  note="system with the highest year-over-year rating correlation")
        FACTS.set("stability.most_stable.corr", float(most[1]), "{:.2f}",
                  note="highest year-over-year rating correlation")
        FACTS.set("stability.least_stable.name", str(least_label),
                  note="system with the lowest year-over-year rating correlation")
        FACTS.set("stability.least_stable.corr", float(least[1]), "{:.2f}",
                  note="lowest year-over-year rating correlation")
        FACTS.set("stability.top_retention.name", str(ret_top_label),
                  note="system that best keeps the same names in its top tier year to year")

        # Guards. Stability and forecasting are different axes: the steadiest
        # individual rating is not automatically the best team forecaster, and
        # PER (very sticky) is not the jumpiest even though it forecasts worst.
        FACTS.guard("stability_min_retention_beats_chance",
                    min(ret_means.values()) > 4 * chance,
                    "even the lowest elite-tier retention is several times the "
                    "chance level: every system's top tier is far stickier than random",
                    min(ret_means.values()))
        if "PER" in corr_means and "BPM" in corr_means:
            FACTS.guard("stability_per_stickier_than_bpm",
                        corr_means["PER"] > corr_means["BPM"],
                        "PER is more stable year to year than BPM, the opposite of their "
                        "forecasting order",
                        corr_means["PER"] - corr_means["BPM"])

    header("REGULAR SEASON vs PLAYOFFS (RATE-METRIC DELTAS)")
    deltas = load_playoff_deltas(end_year)
    if deltas.empty:
        print("  No playoff data available for this season — section skipped.")
    else:
        n_qual = len(deltas)
        metric_list = ", ".join(SYSTEM_LABELS.get(m, m) for m in PLAYOFF_DELTA_METRICS)
        print(f"Players with >= {MIN_PLAYOFF_MINUTES} playoff minutes: {n_qual}")
        print(f"Rate metrics compared (each normalized within its season type): {metric_list}")
        print("Delta = playoff minus regular season. 'adj' subtracts the average delta")
        print("among this qualified pool, so a riser is measured against the other")
        print("rotation players who also advanced. The composite shift z averages the")
        print("standardized adjusted deltas of PER, WS/48, and BPM, so a riser needs the")
        print("three box formulations to agree.")
        print("Note: this project's BPM scale is approximate; the rankings carry the")
        print("signal, not the raw BPM points.")
        FACTS.set("playoff.n_qualified", n_qual, "{:d}",
                  note=f"players with >= {MIN_PLAYOFF_MINUTES} playoff minutes")
        FACTS.set("playoff.min_floor", MIN_PLAYOFF_MINUTES, "{:d}",
                  note="minimum playoff minutes to enter the riser/faller pool")

        risers = deltas.nlargest(10, "SHIFT_Z")
        fallers = deltas.nsmallest(10, "SHIFT_Z")

        def _line(rank, row):
            # PER is the one metric on a trustworthy real scale (normalized to a
            # league average of 15), shown alongside the composite z.
            return (f"  {rank:>2}. {row['PLAYER_NAME']:<26} "
                    f"{row.get('TEAM_ABBREVIATION', ''):>3}  "
                    f"shift z = {row['SHIFT_Z']:+.2f}  "
                    f"(PER {row['PER_delta_adj']:+.1f} vs regular season)")

        print("\nBiggest playoff RISERS (raised their level above their regular-season form):")
        for rank, (_, row) in enumerate(risers.iterrows(), 1):
            print(_line(rank, row))
            if rank <= 3:
                FACTS.set(f"playoff.riser.{rank}.name", str(row["PLAYER_NAME"]),
                          note=f"playoff riser rank {rank} (composite shift)")
                FACTS.set(f"playoff.riser.{rank}.z", float(row["SHIFT_Z"]), "{:.2f}",
                          note=f"playoff riser rank {rank} composite shift z")

        print("\nBiggest playoff FALLERS (dropped below their regular-season form):")
        for rank, (_, row) in enumerate(fallers.iterrows(), 1):
            print(_line(rank, row))
            if rank <= 3:
                FACTS.set(f"playoff.faller.{rank}.name", str(row["PLAYER_NAME"]),
                          note=f"playoff faller rank {rank} (composite shift)")
                FACTS.set(f"playoff.faller.{rank}.z", float(row["SHIFT_Z"]), "{:.2f}",
                          note=f"playoff faller rank {rank} composite shift z")

        top_riser = str(risers.iloc[0]["PLAYER_NAME"])
        top_faller = str(fallers.iloc[0]["PLAYER_NAME"])
        FACTS.guard("playoff_top_riser_positive",
                    float(risers.iloc[0]["SHIFT_Z"]) > 0,
                    f"the top playoff riser ({top_riser}) gained on the pool", top_riser)
        FACTS.guard("playoff_top_faller_negative",
                    float(fallers.iloc[0]["SHIFT_Z"]) < 0,
                    f"the top playoff faller ({top_faller}) lost ground on the pool", top_faller)

        # Did the regular-season consensus #1 hold up in the playoffs?
        if "CONSENSUS" in qual.columns and qual["CONSENSUS"].notna().sum() > 0:
            cons_top = str(qual.nlargest(1, "CONSENSUS")["PLAYER_NAME"].iloc[0])
            match = deltas[deltas["PLAYER_NAME"] == cons_top]
            if not match.empty:
                z = float(match.iloc[0]["SHIFT_Z"])
                order = deltas.sort_values("SHIFT_Z").reset_index(drop=True)
                frank = int(order.index[order["PLAYER_NAME"] == cons_top][0]) + 1
                print(f"\nRegular-season consensus #1 {cons_top}: playoff shift "
                      f"z = {z:+.2f} (faller rank {frank} of {len(deltas)})")
                FACTS.set("playoff.consensus1.name", cons_top,
                          note="regular-season consensus #1 player (playoff shift lookup)")
                FACTS.set("playoff.consensus1.z", z, "{:.2f}",
                          note="regular-season consensus #1 player's composite playoff shift z")
                FACTS.guard("consensus_top_fell_in_playoffs", z < 0,
                            f"the regular-season consensus #1 ({cons_top}) fell in the playoffs", z)

    # Dump all facts and guards to docs/ (+ the dev facts-reference lookup table)
    FACTS.dump(_FACTS_PATH)
    FACTS.dump_guards(_GUARDS_PATH)
    from render_docs import write_reference
    print(f"Saved → {write_reference()}")
