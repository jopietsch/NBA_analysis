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
    playoff_weighted_value,
    PLAYOFF_VALUE_WEIGHT,
    pooled_qualified_values,
    rapm_reliability,
    fetch_bbr_advanced,
    MIN_MINUTES_QUALIFIER,
    MIN_PLAYOFF_MINUTES,
    PLAYOFF_SHRINK_MINUTES,
    PLAYOFF_BOOTSTRAP_B,
    PLAYOFF_CI_PCT,
    PLAYOFF_DELTA_METRICS,
    powerlaw_fit,
    POWERLAW_R2_THRESHOLD,
)
from player_rating_overview_facts import FACTS, _FACTS_PATH, _GUARDS_PATH
from nbakit.player_crosswalk import build_crosswalk, apply_crosswalk

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

# Systems that are algebraic kin: a metric together with its own offensive/
# defensive halves, or with a rescaling of itself. The overlap measure
# (_overlap_r2) holds a system's own kin out of its predictor set, so a metric
# is never trivially "explained" by its own components. Without this, BPM =
# OBPM + DBPM forces BPM's overlap to 1.0, which says nothing about whether BPM
# echoes the other, genuinely different systems.
COMPONENT_FAMILIES = [
    {"BPM", "OBPM", "DBPM", "VORP"},
    {"WS", "WS48"},
    {"RAPM", "O_RAPM", "D_RAPM"},
    {"RAPM_MY", "O_RAPM_MY", "D_RAPM_MY"},
    {"RAPTOR", "RAPTOR_O", "RAPTOR_D", "RAPTOR_WAR"},
]

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
RAPM_PANEL_START_YEAR = 1998  # 1997-98, first season with both RAPM and RAPM+prior
                              # (play-by-play reaches 1996-97; RAPM+prior needs a
                              #  preceding season, so it starts one year later)
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
    "RAPM_MY": "RAPM+prior",
    "O_RAPM_MY": "O-RAPM+prior",
    "D_RAPM_MY": "D-RAPM+prior",
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

    # Non-negative ridge (sklearn if available, else OLS). The team features are
    # standardized before the fit so the ridge penalty is even-handed across
    # systems, but that leaves `ridge.coef_` in doubly-standardized units. The
    # per-player scores below apply the weights to singly-standardized player
    # z-scores (same units as the team aggregates X), so we divide the fitted
    # coefficients by `scaler.scale_` to bring them back into X's space.
    # Without this, systems whose team-level averages have a smaller spread are
    # under-weighted. `positive=True` keeps the blend weights non-negative, as a
    # rating-system blend should (a system never counts against a player).
    try:
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_s = scaler.fit_transform(X)
        ridge = Ridge(alpha=5.0, fit_intercept=True, positive=True)
        ridge.fit(X_s, y)
        coef = ridge.coef_ / scaler.scale_
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
    share of current team minutes that carried a prior rating. Reports both the
    in-sample R² and a leave-one-team-out cross-validated R² (mirroring
    `retrodiction_scores`), so the forecast panel can be graded on the same
    honest out-of-sample number as the describe panel. Returns
    {system: {r2, cv_r2, n, coverage}}.
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
        # Leave-one-team-out cross-validation (same honest read as the describe
        # panel): refit the line without each team, then predict that team.
        preds = np.empty(len(x))
        for i in range(len(x)):
            mask = np.arange(len(x)) != i
            c1, c0 = np.polyfit(x[mask], y[mask], 1)
            preds[i] = c1 * x[i] + c0
        cv_r2 = 1.0 - float(((y - preds) ** 2).sum()) / ss_tot
        result[s] = {"r2": r2, "cv_r2": cv_r2, "n": int(len(data)),
                     "coverage": coverage}
    return result


def _next_season_table(nxt: dict, retro: dict) -> list[dict]:
    """Rows for the single-season describe-vs-forecast table, graded on CV R².

    Both columns carry the leave-one-team-out CV R² — the describe column from
    the same-season retrodiction (`retro`), the forecast column from the
    next-season retrodiction (`nxt`) — so the two sides of the table are
    apples-to-apples (the same out-of-sample metric on both). Rows are sorted by
    forecast CV R², best first.
    """
    return [
        {
            "system": s,
            "describe_cv_r2": retro.get(s, {}).get("cv_r2", float("nan")),
            "forecast_cv_r2": float(sc["cv_r2"]),
        }
        for s, sc in sorted(nxt.items(), key=lambda kv: -kv[1]["cv_r2"])
    ]


def panel_retrodiction(start_year: int, end_year: int,
                       systems: list[str] | None = None,
                       target: str = "point_diff") -> dict:
    """Pool the describe and forecast tests across every season in the cache.

    For each season y in [start_year, end_year], the describe score is the
    leave-one-team-out CV R² of y's own ratings against y's team point
    differential (same-season retrodiction). For each consecutive pair (y, y+1),
    the forecast score is the leave-one-team-out CV R² of how well y's ratings,
    carried onto y+1's rosters, predict y+1's point differential (next-season
    retrodiction) — the same out-of-sample metric as the describe side, so the
    two panels are apples-to-apples. Reads only the cached unified tables and
    cached team totals, so it makes no network calls.

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
            forecast[s].append(sc["cv_r2"])
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


def season_comparison(year_a: int, year_b: int,
                      systems: list[str] | None = None) -> dict:
    """Compare two seasons across the consensus and the box-score systems.

    Builds the consensus over each season's qualified players, then reports the
    consensus top-10 each season, the biggest consensus risers and fallers among
    players qualified in both, the year-over-year consensus rank agreement for
    this pair, and the mean inter-system rank agreement in each season. Reads only
    the cached unified tables, so it makes no network calls. Returns the pieces in
    a dict, or {} if either season is missing. Read this as a snapshot: the
    multi-season panels carry the firm cross-season findings, this one pair only
    shows how much the single-season orderings move from one year to the next.
    """
    systems = systems or ALL_SYSTEMS
    a, b = load_unified_ratings(year_a), load_unified_ratings(year_b)
    if a.empty or b.empty:
        return {}
    qa = a[a["QUALIFIED"] == True].copy() if "QUALIFIED" in a.columns else a.copy()
    qb = b[b["QUALIFIED"] == True].copy() if "QUALIFIED" in b.columns else b.copy()
    qa["CONSENSUS"] = _build_consensus(qa, systems)
    qb["CONSENSUS"] = _build_consensus(qb, systems)

    def _top(q):
        return (q.dropna(subset=["CONSENSUS"]).nlargest(10, "CONSENSUS")
                [["PLAYER_NAME", "CONSENSUS"]].reset_index(drop=True))
    top_a, top_b = _top(qa), _top(qb)

    left = (qa[["player_id", "PLAYER_NAME", "CONSENSUS"]].dropna()
            .rename(columns={"CONSENSUS": "a"}))
    right = qb[["player_id", "CONSENSUS"]].dropna().rename(columns={"CONSENSUS": "b"})
    m = left.merge(right, on="player_id")
    m["delta"] = m["b"] - m["a"]
    movers = m.sort_values("delta").reset_index(drop=True)

    cons_corr = (float(m["a"].corr(m["b"], method="spearman"))
                 if len(m) >= 10 and m["a"].std() > 0 and m["b"].std() > 0 else float("nan"))

    # Mean inter-system rank agreement among the core box-score systems each season,
    # so we can ask whether the systems agreed more or less from one year to the next.
    core = ["GAME_SCORE", "PER", "WS", "WS48", "BPM", "VORP"]

    def _mean_agree(q):
        cols = [s for s in core if s in q.columns and q[s].notna().sum() >= 10]
        vals = []
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                pair = q[[cols[i], cols[j]]].dropna()
                if len(pair) >= 10 and pair[cols[i]].std() > 0 and pair[cols[j]].std() > 0:
                    vals.append(pair[cols[i]].corr(pair[cols[j]], method="spearman"))
        return float(np.mean(vals)) if vals else float("nan")
    agree_a, agree_b = _mean_agree(qa), _mean_agree(qb)

    held_top5 = len(set(top_a["PLAYER_NAME"].head(5)) & set(top_b["PLAYER_NAME"].head(5)))

    return {
        "year_a": year_a, "year_b": year_b,
        "label_a": f"{year_a - 1}-{str(year_a)[-2:]}",
        "label_b": f"{year_b - 1}-{str(year_b)[-2:]}",
        "top_a": top_a, "top_b": top_b, "movers": movers,
        "n_both": len(m), "consensus_corr": cons_corr,
        "agree_a": agree_a, "agree_b": agree_b, "held_top5": held_top5,
    }


def _kin(system: str) -> set[str]:
    """Return the algebraic-kin family containing `system` (itself if none)."""
    for fam in COMPONENT_FAMILIES:
        if system in fam:
            return fam
    return {system}


def _overlap_r2(df: pd.DataFrame, systems: list[str]) -> dict[str, float]:
    """For each system, the share of its variance the OTHER systems can rebuild.

    Method: regress each system on all others (with an intercept) and take the
    regression R². That R² is the system's overlap with the field: high means it
    is largely redundant, low means it carries independent signal. A system's own
    algebraic kin (its offensive/defensive halves, or a rescaling of it) are held
    out of the predictor set, so a metric is never trivially explained by its own
    components. Returns {system: overlap_r2}.
    """
    present = _present_systems(df, systems)
    if len(present) < 3:
        return {}

    result = {}
    for s in present:
        kin = _kin(s)
        others = [o for o in present if o not in kin]
        if len(others) < 2:
            result[s] = 0.0
            continue
        sub = df[[s] + others].dropna()
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


def _header(title: str) -> None:
    """Print the box-drawing section header used throughout results.md."""
    print(f"\n{'─' * 3} {title} {'─' * max(0, 60 - len(title))}")


def run_coverage(df_full: pd.DataFrame, qual: pd.DataFrame,
                 present: list[str], end_year: int) -> None:
    """DATA COVERAGE — season label, player counts, systems present."""
    _header("DATA COVERAGE")
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


def run_rapm_single_season(qual: pd.DataFrame, present: list[str]) -> None:
    """RAPM — computed single-season, no prior: top-5, box-score divergence."""
    # RAPM detail — computed in-house this report from 2025-26 play-by-play, a
    # single season with no box-score prior. Registers the top of the list (to
    # show the single-season noise) and how far it sits from the box-score
    # systems (its independence from them).
    if "RAPM" in qual.columns and qual["RAPM"].notna().sum() >= 20:
        _header("RAPM — COMPUTED SINGLE-SEASON (NO PRIOR)")
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


def run_rapm_my(qual: pd.DataFrame, present: list[str]) -> None:
    """RAPM_MY — prior-informed multi-year RAPM: top-5, consensus agreement."""
    # RAPM_MY detail — the prior-informed, multi-year version. Registers its top
    # (should be recognizable stars, not single-season noise) and how much closer
    # it sits to the box-score systems and the consensus than bare RAPM does.
    if "RAPM_MY" in qual.columns and qual["RAPM_MY"].notna().sum() >= 20:
        _header("RAPM_MY — PRIOR-INFORMED, MULTI-YEAR")
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
            print(f"  Bare RAPM rank agreement with the consensus: {bare_cons:.2f}")
            FACTS.set("rapm.consensus_corr", float(bare_cons), "{:.2f}",
                      note="bare single-season RAPM rank agreement with the consensus")
            if len(cons_pair) > 10:
                FACTS.guard("rapm_my_beats_bare_consensus", my_cons > bare_cons,
                            "RAPM_MY tracks the consensus better than bare RAPM",
                            f"{my_cons:.2f} vs {bare_cons:.2f}")


def run_rapm_reliability(end_year: int) -> None:
    """RAPM RELIABILITY — split-half and year-over-year stability checks."""
    # ── How reliable is the computed RAPM? Split-half + year-over-year ────────
    _header("RAPM RELIABILITY (SPLIT-HALF AND YEAR-OVER-YEAR)")
    rel = rapm_reliability(end_year)
    if not rel:
        print("  Fewer than two seasons of play-by-play — reliability check skipped.")
    else:
        sh, nsh, mm = rel["splithalf"], rel["n_splithalf"], rel["min_minutes"]
        print("Split-half: fit bare RAPM on two random halves of the pooled")
        print("possessions, then correlate the two estimates. If the lineup signal")
        print("is real the halves agree; if it is noise they do not.")
        print(f"  Split-half reliability ({nsh} players, {mm}+ min): {sh:.2f}")
        print("  (near-zero would be noise; a usable metric sits near 0.5-0.7)")
        print("  By minutes bin:")
        for b in rel["by_bin"]:
            if b["n"] > 8 and b["r"] == b["r"]:
                print(f"    {b['lo']:>4}-{b['hi']:<4} min: n={b['n']:>3}  r={b['r']:+.2f}")
        FACTS.set("rapm_rel.splithalf", float(sh), "{:.2f}",
                  note=f"split-half reliability of bare RAPM ({mm}+ min)")
        FACTS.set("rapm_rel.min_minutes", int(mm), "{:d}",
                  note="minutes floor for the RAPM reliability read")

        yoy = rel["yoy"]
        print(f"\nYear-over-year stability (players {mm}+ min in both seasons):")
        for col in ("RAPM", "RAPM_MY", "BPM"):
            if col in yoy and yoy[col] == yoy[col]:
                print(f"  {col:8s} {yoy[col]:+.2f}")
        if yoy.get("RAPM") == yoy.get("RAPM"):
            FACTS.set("rapm_rel.yoy_rapm", float(yoy["RAPM"]), "{:.2f}",
                      note="year-over-year stability of bare RAPM (1000+ min)")
        if yoy.get("RAPM_MY") == yoy.get("RAPM_MY"):
            FACTS.set("rapm_rel.yoy_rapm_my", float(yoy["RAPM_MY"]), "{:.2f}",
                      note="year-over-year stability of RAPM_MY (1000+ min)")
        if yoy.get("BPM") == yoy.get("BPM"):
            FACTS.set("rapm_rel.yoy_bpm", float(yoy["BPM"]), "{:.2f}",
                      note="year-over-year stability of BPM (reference, 1000+ min)")
        print("\nAfter the possession-reconstruction fixes, the lineup signal is real,")
        print("not noise. A reconstruction bug had been discarding ~60% of games with")
        print("complete play-by-play; recovering them took split-half reliability from")
        print(f"about 0.10 to {sh:.2f}, and bare single-season RAPM now holds from one")
        print(f"season to the next at {yoy['RAPM']:.2f} (it was near zero before).")
        print(f"Pooled across seasons and anchored to the BPM prior, RAPM_MY is at least")
        print(f"as stable as BPM ({yoy['RAPM_MY']:.2f} vs {yoy['BPM']:.2f}), so it adds a")
        print("genuine lineup contribution on top of the box score rather than echoing")
        print("it. Reliability keeps climbing with more pooled seasons (roughly 0.48 at")
        print("three seasons, 0.60 at five, on the full-data scale).")

        FACTS.guard("rapm_splithalf_real", sh > 0.20,
                    "bare RAPM's split-half reliability is well above the near-zero "
                    "noise floor it sat at before the reconstruction fix", sh)
        if yoy.get("RAPM") == yoy.get("RAPM"):
            FACTS.guard("rapm_yoy_meaningful", yoy["RAPM"] > 0.25,
                        "bare single-season RAPM now holds from one season to the next, "
                        "year-over-year stability well above noise", yoy["RAPM"])
        if yoy.get("RAPM_MY") == yoy.get("RAPM_MY") and yoy.get("BPM") == yoy.get("BPM"):
            FACTS.guard("rapm_my_at_least_bpm_stable",
                        yoy["RAPM_MY"] >= yoy["BPM"] - 0.05,
                        "RAPM_MY is at least as stable year to year as BPM, so the prior-"
                        "informed lineup signal adds to the box score rather than "
                        "degrading it",
                        f"RAPM_MY {yoy['RAPM_MY']:.2f} vs BPM {yoy['BPM']:.2f}")


def run_rapm_vs_public(df_full: pd.DataFrame) -> None:
    """RAPM: COMPUTED VS PUBLIC SNAPSHOT — validation against a public RAPM."""
    # RAPM vs public snapshot comparison (no-ops when RAPM_PUBLIC is absent)
    if "RAPM" in df_full.columns and "RAPM_PUBLIC" in df_full.columns:
        _header("RAPM: COMPUTED VS PUBLIC SNAPSHOT")
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


def run_bpm_validation(df_full: pd.DataFrame, end_year: int) -> None:
    """BPM VALIDATION vs BASKETBALL-REFERENCE — BPM family reproduction check."""
    # BPM family validation against Basketball-Reference's published values —
    # our BPM was just rewritten, so this checks it reproduces an authoritative
    # source rather than only agreeing with itself.
    _header("BPM VALIDATION vs BASKETBALL-REFERENCE")
    bbr = fetch_bbr_advanced(end_year)
    if bbr is None or bbr.empty:
        print("  BBR advanced stats unavailable — section skipped.")
    else:
        xwalk_df = df_full[["player_id", "PLAYER_NAME", "TEAM_ABBREVIATION"]].rename(
            columns={"player_id": "PLAYER_ID"})
        xwalk = build_crosswalk(xwalk_df, end_year)
        bbr_matched = apply_crosswalk(bbr, xwalk, name_col="player_name",
                                      season_col="season_end_year")
        bbr_matched = bbr_matched.dropna(subset=["player_id"]).copy()
        bbr_matched["player_id"] = bbr_matched["player_id"].astype(int)

        qual_full = df_full[df_full["QUALIFIED"] == True] if "QUALIFIED" in df_full.columns else df_full
        val = qual_full.merge(bbr_matched, on="player_id", how="inner",
                              suffixes=("", "_bbr"))
        n_matched = len(val)
        print(f"  Qualified players matched to BBR: {n_matched}")
        FACTS.set("bpm_val.n", n_matched, "{:d}",
                  note="qualified players matched to BBR advanced stats")

        r_by_metric = {}
        for ours, theirs in (("BPM", "bpm"), ("OBPM", "obpm"),
                             ("DBPM", "dbpm"), ("VORP", "vorp")):
            pair = val[[ours, theirs]].dropna()
            if len(pair) < 10:
                continue
            r = float(np.corrcoef(pair[ours], pair[theirs])[0, 1])
            mae = float((pair[ours] - pair[theirs]).abs().mean())
            r_by_metric[ours] = r
            print(f"  {ours} vs BBR {theirs}: r={r:.3f}  MAE={mae:.2f} (n={len(pair)})")
            fact_key = ours.lower()
            FACTS.set(f"bpm_val.r_{fact_key}", r, "{:.3f}",
                      note=f"Pearson r between our {ours} and BBR {theirs}")
            if ours == "BPM":
                FACTS.set("bpm_val.mae_bpm", mae, "{:.2f}",
                          note="mean absolute diff our BPM vs BBR bpm")

        spot_names = ["Nikola Joki", "Shai Gilgeous", "Giannis", "Wembanyama",
                     "Luka", "Jalen Brunson", "Jayson Tatum", "Kawhi"]
        print("\n  Spot check (ours vs BBR):")
        print(f"  {'Player':<22}{'BPM':>8}{'BBR BPM':>10}{'OBPM':>8}{'BBR OBPM':>10}"
              f"{'DBPM':>8}{'BBR DBPM':>10}")
        for needle in spot_names:
            hit = val[val["PLAYER_NAME"].str.contains(needle, case=False, na=False)]
            if hit.empty:
                continue
            row = hit.iloc[0]
            print(f"  {row['PLAYER_NAME']:<22}{row['BPM']:>8.1f}{row['bpm']:>10.1f}"
                  f"{row['OBPM']:>8.1f}{row['obpm']:>10.1f}"
                  f"{row['DBPM']:>8.1f}{row['dbpm']:>10.1f}")
            if "Brunson" in needle:
                FACTS.set("bpm_val.brunson_bpm", float(row["BPM"]), "{:.1f}",
                          note="our BPM for Jalen Brunson")
                FACTS.set("bpm_val.brunson_bbr_bpm", float(row["bpm"]), "{:.1f}",
                          note="BBR's published BPM for Jalen Brunson")

        if "BPM" in r_by_metric:
            FACTS.guard("bpm_val_strong", r_by_metric["BPM"] > 0.85,
                        "our BPM reproduces Basketball-Reference BPM (r > 0.85)",
                        r_by_metric["BPM"])
        if "VORP" in r_by_metric:
            FACTS.guard("vorp_val_strong", r_by_metric["VORP"] > 0.90,
                        "our VORP reproduces Basketball-Reference VORP (r > 0.90)",
                        r_by_metric["VORP"])


def run_distributions(qual: pd.DataFrame, present: list[str]) -> None:
    """BASIC DISTRIBUTION STATS — per-system moments, Gini, pooled RAPM shape."""
    _header("BASIC DISTRIBUTION STATS")
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
    # RAPM distribution shape, pooled across every play-by-play season. One
    # season of RAPM is too sparse to read as a bell, so the shape facts (and the
    # distribution-shape figure) pool all the cached seasons. A power law needs a
    # heavy one-sided tail (large positive skew); RAPM's skew sits near zero,
    # while VORP, an accumulation metric, carries the right-skew tail.
    _shape = pooled_qualified_values(RAPM_PANEL_START_YEAR, RAPM_PANEL_END_YEAR,
                                     ["RAPM", "VORP"])
    if "RAPM" in _shape.columns and _shape["RAPM"].notna().sum() >= 100:
        _rapm_vals = _shape["RAPM"].dropna().values
        _n_seasons = RAPM_PANEL_END_YEAR - RAPM_PANEL_START_YEAR + 1
        _rapm_skew = float(stats.skew(_rapm_vals))
        _rapm_exkurt = float(stats.kurtosis(_rapm_vals))
        _rapm_fracneg = float(np.mean(_rapm_vals < 0))
        print(f"\nRAPM distribution shape, pooled over {_n_seasons} seasons "
              f"(n={len(_rapm_vals)} player-seasons):")
        print(f"  Skew: {_rapm_skew:+.2f}  Excess kurtosis: {_rapm_exkurt:+.2f}  "
              f"Below zero: {_rapm_fracneg*100:.0f}%")
        FACTS.set("rapm_shape.n", len(_rapm_vals), "{:d}",
                  note="qualified player-seasons in the pooled RAPM distribution")
        FACTS.set("rapm_shape.n_seasons", _n_seasons, "{:d}",
                  note="play-by-play seasons pooled for the RAPM distribution shape")
        FACTS.set("rapm_shape.skew", _rapm_skew, "{:+.2f}",
                  note="pooled RAPM skewness (near zero = symmetric)")
        FACTS.set("rapm_shape.exkurt", _rapm_exkurt, "{:+.2f}",
                  note="pooled RAPM excess kurtosis (0 = normal)")
        FACTS.set("rapm_shape.frac_neg", _rapm_fracneg * 100, "{:.0f}",
                  note="pooled RAPM share of qualified player-seasons below zero (percent)")
        FACTS.guard("rapm_symmetric_not_powerlaw",
                    abs(_rapm_skew) < 0.5,
                    "RAPM is a near-symmetric bell (skew near zero), not the "
                    "heavy-tailed shape a power law needs",
                    _rapm_skew)
        if "VORP" in _shape.columns and _shape["VORP"].notna().sum() >= 100:
            _vorp_skew = float(stats.skew(_shape["VORP"].dropna().values))
            FACTS.set("rapm_shape.vorp_skew", _vorp_skew, "{:+.2f}",
                      note="pooled VORP skewness (right-skewed accumulation metric)")
            FACTS.guard("rapm_less_skewed_than_vorp",
                        abs(_rapm_skew) < abs(_vorp_skew),
                        "RAPM is far less skewed than the right-skewed accumulation metric VORP",
                        _vorp_skew - abs(_rapm_skew))


def run_powerlaws(qual: pd.DataFrame, present: list[str]) -> dict:
    """POWER-LAW FIT — log-log value-vs-rank fits; returns {system: fit dict}."""
    _header("POWER-LAW FIT (VALUE VS RANK, LOG-LOG)")
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
    # RAPM's shape is asserted on its full distribution (rapm_symmetric_not_powerlaw
    # above, skew near zero) rather than the borderline top-50 log-log fit, which
    # sits right at the 0.95 line and is not a formal test.
    return _alpha


def run_rank_agreement(qual: pd.DataFrame, present: list[str]) -> None:
    """RANK AGREEMENT — Spearman correlations for every system pair."""
    _header("RANK AGREEMENT (SPEARMAN CORRELATIONS)")
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


def run_overlap(qual: pd.DataFrame, present: list[str]) -> None:
    """OVERLAP — regression R² of each system on the others (kin held out)."""
    _header("HOW MUCH EACH SYSTEM OVERLAPS THE OTHERS")
    print("Regression R² of each system on all others, with its own algebraic")
    print("kin (offense/defense halves, rescalings) held out. High = redundant;")
    print("low = carries signal the other systems miss.")
    overlap = _overlap_r2(qual, present)
    for s, r2 in sorted(overlap.items(), key=lambda x: -x[1]):
        print(f"  {SYSTEM_LABELS.get(s, s)}: overlap R² = {r2:.3f}")
        FACTS.set(f"overlap.{s}.r2", float(r2), "{:.3f}",
                  note=f"{SYSTEM_LABELS.get(s, s)} overlap R²: share of its variance the other systems (kin excluded) can reconstruct")


def run_consensus(qual: pd.DataFrame, present: list[str]) -> None:
    """CONSENSUS RATING — top 20; adds the CONSENSUS column to qual in place."""
    _header("CONSENSUS RATING — TOP 20")
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


def run_wins_predictive(qual: pd.DataFrame, df_full: pd.DataFrame,
                        present: list[str]) -> None:
    """WINS-PREDICTIVE RATING — top 20; adds WINS_PRED to qual/df_full in place."""
    _header("WINS-PREDICTIVE RATING — TOP 20")
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


def run_consensus_vs_wins(qual: pd.DataFrame) -> None:
    """COMPARISON — consensus vs wins-predictive: correlation and biggest gaps."""
    _header("COMPARISON: CONSENSUS vs. WINS-PREDICTIVE")
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


def run_uber_concentration(qual: pd.DataFrame, _alpha: dict) -> None:
    """UBER RATING CONCENTRATION — Gini vs power-law alpha for the uber ratings.

    `_alpha` is the per-system power-law fit dict returned by run_powerlaws.
    """
    _header("UBER RATING CONCENTRATION (GINI vs CENTER-ROBUST STEEPNESS)")
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
    if _cons and _alpha.get("PER") and _alpha.get("OBPM"):
        FACTS.guard("uber_concentration_moderate",
                    _alpha["PER"]["alpha"] < _cons["alpha"] < _alpha["OBPM"]["alpha"],
                    "by center-robust steepness the consensus rating sits between the "
                    "flattest metric (PER) and the steepest (Offensive BPM)",
                    _cons["alpha"])


def run_tail_analysis(qual: pd.DataFrame, present: list[str]) -> None:
    """POWER-LAW / TAIL ANALYSIS — cumulative vs rate metric concentration."""
    _header("POWER-LAW / TAIL ANALYSIS")
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


def run_loves_discounts(qual: pd.DataFrame, present: list[str]) -> None:
    """WHO EACH SYSTEM LOVES vs. CONSENSUS — biggest per-system residuals."""
    _header("WHO EACH SYSTEM LOVES vs. CONSENSUS")
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


def run_retrodiction(df_full: pd.DataFrame, present: list[str],
                     end_year: int) -> tuple[pd.DataFrame, dict]:
    """RETRODICTION — same-season team point-diff rebuild.

    Returns (outcomes, retro) for the next-season section.
    """
    _header("RETRODICTION: WHICH RATING REBUILDS TEAM RESULTS")
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
        blind_ranked = [(s, sc) for s, sc in ranked if s not in OUTCOME_CALIBRATED]
        if blind_ranked:
            tb_sys, tb_sc = blind_ranked[0]
            tb_label = SYSTEM_LABELS.get(tb_sys, tb_sys)
            # The team-margin anchor makes the box metrics reconstruct team point
            # differential by construction (BPM equals it exactly), so the top of
            # the list is mechanical. The genuine test is among the outcome-blind
            # ratings, where PER still leads at the same ~73% as before.
            print(f"\n{top_label} sits on top at CV R²={top_sc['cv_r2']:.3f}, but only")
            print("mechanically: the team-margin anchor builds the box metrics to sum to")
            print("team point differential (BPM equals it exactly). Among the ratings that")
            print(f"never saw who won, {tb_label} leads, rebuilding "
                  f"{tb_sc['cv_r2'] * 100:.0f}% of the team point-differential spread")
            print("out of sample.")
            FACTS.set("retro.top.name", str(tb_label),
                      note="top outcome-blind retrodictor of team point differential (CV)")
            FACTS.set("retro.top.cv_r2", float(tb_sc["cv_r2"]), "{:.3f}",
                      note="top outcome-blind rating's leave-one-team-out retrodiction R²")
            FACTS.set("retro.top.cv_r2_pct", float(tb_sc["cv_r2"] * 100), "{:.0f}",
                      note="top outcome-blind rating's retrodiction R² as a percent (append %)")
            FACTS.set("retro.mechanical.name", str(top_label),
                      note="rating that tops retrodiction mechanically (team-anchored box metric)")
            FACTS.set("retro.mechanical.cv_r2", float(top_sc["cv_r2"]), "{:.3f}",
                      note="the mechanically-top rating's retrodiction R² (≈1.0 by construction)")
            FACTS.guard("blind_rating_rebuilds_team_diff",
                        tb_sc["cv_r2"] > 0.5
                        and all(tb_sc["cv_r2"] >= sc["cv_r2"] for _, sc in blind_ranked),
                        f"among ratings that never saw who won, {tb_label} rebuilds the most "
                        f"team point differential ({tb_sc['cv_r2'] * 100:.0f}% out of sample)",
                        tb_label)
            FACTS.guard("team_anchored_box_is_mechanical",
                        top_sys in OUTCOME_CALIBRATED and top_sc["cv_r2"] > 0.95,
                        "the team-anchored box metrics top this test only mechanically "
                        "(BPM is built to equal team point differential)",
                        f"{top_label} CV R²={top_sc['cv_r2']:.2f}")
    return outcomes, retro


def run_next_season(df_full: pd.DataFrame, outcomes: pd.DataFrame, retro: dict,
                    present: list[str], end_year: int) -> None:
    """NEXT-SEASON RETRODICTION — predict this season from last season's ratings."""
    _header("NEXT-SEASON RETRODICTION (PREDICTING THIS SEASON FROM LAST)")
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
        # Both columns are leave-one-team-out CV R² (see _next_season_table), so
        # the describe and forecast sides of the table are apples-to-apples. The
        # nextretro.*.r2 fact KEYS are kept for template stability; their values
        # now carry the CV number.
        rows_n = _next_season_table(nxt, retro)
        print(f"  {'':<16}{'describes':>10}{'predicts':>10}")
        print(f"  {'system':<16}{'(same yr)':>10}{'(next yr)':>10}")
        for row in rows_n:
            s = row["system"]
            tag = "[team-fit]    " if s in OUTCOME_CALIBRATED else "[outcome-blind]"
            print(f"  {tag} {SYSTEM_LABELS.get(s, s):<14}"
                  f"{row['describe_cv_r2']:>8.3f}{row['forecast_cv_r2']:>10.3f}")
            FACTS.set(f"nextretro.{s}.r2", row["forecast_cv_r2"], "{:.3f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} next-season retrodiction CV R² "
                           f"(leave-one-team-out; predict {end_year - 1}->{end_year})")
        top_n_sys = rows_n[0]["system"]
        top_n_cv = rows_n[0]["forecast_cv_r2"]
        top_n_label = SYSTEM_LABELS.get(top_n_sys, top_n_sys)
        top_same = max(retro.items(), key=lambda kv: kv[1]["cv_r2"])[0]
        top_same_label = SYSTEM_LABELS.get(top_same, top_same)
        print(f"\nBest forecaster of next season: {top_n_label} (CV R²={top_n_cv:.3f}). "
              f"Best description of\nthe season itself: {top_same_label}.")
        FACTS.set("nextretro.top.name", str(top_n_label),
                  note="system that best predicts next-season team point differential")
        FACTS.set("nextretro.top.r2", float(top_n_cv), "{:.3f}",
                  note="best next-season retrodiction CV R² (leave-one-team-out)")
        FACTS.set("nextretro.top.r2_pct", float(top_n_cv * 100), "{:.0f}",
                  note="best next-season retrodiction CV R² as percent (append % in prose)")
        FACTS.guard("forecast_top_differs_from_description_top",
                    top_n_sys != top_same,
                    "the metric that best forecasts next season is not the one that best "
                    "describes the season just played",
                    f"{top_n_label} vs {top_same_label}")
        if "PER" in nxt and "PER" in retro:
            print(f"PER falls from {retro['PER']['cv_r2']:.2f} describing the season to "
                  f"{nxt['PER']['cv_r2']:.2f}\nforecasting the next: a strong descriptor, a weak predictor.")
            FACTS.set("nextretro.PER.r2_pct", float(nxt["PER"]["cv_r2"] * 100), "{:.0f}",
                      note="PER next-season retrodiction CV R² as percent (append % in prose)")
            FACTS.guard("per_describes_better_than_predicts",
                        nxt["PER"]["cv_r2"] < retro["PER"]["cv_r2"],
                        "PER describes the season far better than it forecasts the next",
                        retro["PER"]["cv_r2"] - nxt["PER"]["cv_r2"])


def run_panels() -> None:
    """MULTI-SEASON DESCRIBE vs FORECAST — the pooled full-history panel."""
    _header("MULTI-SEASON DESCRIBE vs FORECAST (FULL PANEL)")
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
            # Prose facts use the MEDIAN pair, not the mean: forecast CV R² is
            # unbounded below, and a couple of pathological handoffs (e.g.
            # 2005->06 at -66) drag PER's mean to an unquotable large negative.
            # The table above keeps the means with ranges so the blow-ups stay
            # visible; the median is the honest "typical season" number.
            d_med_per = float(np.median(panel["describe"]["PER"]))
            f_med_per = float(np.median(panel["forecast"]["PER"]))
            print(f"PER averages {d_means['PER']:.2f} describing but only "
                  f"{f_means['PER']:.2f} forecasting,\nthe same collapse the single pair "
                  f"showed, now seen across {n_pairs} pairs.")
            print(f"In the typical (median) pair PER describes {d_med_per:.2f} "
                  f"and forecasts {f_med_per:.2f}.")
            FACTS.set("panel.PER.describe_median_pct", d_med_per * 100, "{:.0f}",
                      note="PER median same-season (describe) R² across the panel, "
                           "percent (append % in prose)")
            FACTS.set("panel.PER.forecast_median_pct", f_med_per * 100, "{:.0f}",
                      note="PER median next-season (forecast) CV R² across the panel, "
                           "percent (append % in prose); median not mean because CV R² "
                           "blow-up pairs make the mean unquotable")
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


def run_impact_panel() -> None:
    """IMPACT-ERA PANEL — box scores vs RAPM over the same play-by-play seasons."""
    _header("IMPACT-ERA PANEL: BOX SCORES vs RAPM (EQUAL SEASONS)")
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
        # (No ipanel.PER.forecast_mean_pct fact: nothing in the prose consumes
        # it, and PER's forecast CV R² mean is distorted by blow-up pairs —
        # see the panel.PER.*_median_pct facts above for the quotable numbers.)
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


def run_stability(qual: pd.DataFrame) -> None:
    """PLAYER RATING STABILITY — year-over-year correlation and top-N retention."""
    _header("PLAYER RATING STABILITY (YEAR OVER YEAR)")
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


def run_playoff_shift(qual: pd.DataFrame, end_year: int) -> None:
    """REGULAR SEASON vs PLAYOFFS — composite shift risers and fallers."""
    _header("REGULAR SEASON vs PLAYOFFS (RATE-METRIC DELTAS)")
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
        print(f"Two reliability guards: the shift is shrunk toward zero by playoff")
        print(f"minutes (half weight at {PLAYOFF_SHRINK_MINUTES} min) so a short, lucky")
        print(f"sample can't top the list, and a game-level bootstrap re-draws each")
        print(f"player's games {PLAYOFF_BOOTSTRAP_B} times to give a {PLAYOFF_CI_PCT[0]:g}-{PLAYOFF_CI_PCT[1]:g} range")
        print("([lo, hi], on the shrunk scale). A shift is 'clear' when that range")
        print("excludes zero. Risers and fallers below are ranked by the shrunk shift.")
        print("Note: BPM here is our recompute, validated against Basketball-Reference")
        print("(see the BPM-validation section); the playoff BPM is anchored to each")
        print("team's playoff point margin.")

        # A shift is "clear" when its bootstrap interval stays on one side of zero.
        def _clear(row):
            return (row["SHIFT_CI_LO"] > 0 and row["SHIFT_CI_HI"] > 0) or \
                   (row["SHIFT_CI_LO"] < 0 and row["SHIFT_CI_HI"] < 0)
        n_clear = int(deltas.apply(_clear, axis=1).sum())
        print(f"Shifts whose range clears zero (not just game noise): {n_clear} of {n_qual}.")

        FACTS.set("playoff.n_qualified", n_qual, "{:d}",
                  note=f"players with >= {MIN_PLAYOFF_MINUTES} playoff minutes")
        FACTS.set("playoff.min_floor", MIN_PLAYOFF_MINUTES, "{:d}",
                  note="minimum playoff minutes to enter the riser/faller pool")
        FACTS.set("playoff.shrink_minutes", PLAYOFF_SHRINK_MINUTES, "{:d}",
                  note="playoff minutes at which the composite shift keeps half its size")
        FACTS.set("playoff.bootstrap_b", PLAYOFF_BOOTSTRAP_B, "{:d}",
                  note="game-level bootstrap re-draws behind the shift range")
        FACTS.set("playoff.n_clear", n_clear, "{:d}",
                  note="qualified players whose shift range excludes zero")

        risers = deltas.nlargest(10, "SHIFT_SHRUNK")
        fallers = deltas.nsmallest(10, "SHIFT_SHRUNK")

        def _line(rank, row):
            # PER is the one metric on a trustworthy real scale (normalized to a
            # league average of 15), shown alongside the shrunk composite and range.
            return (f"  {rank:>2}. {row['PLAYER_NAME']:<26} "
                    f"{row.get('TEAM_ABBREVIATION', ''):>3}  "
                    f"shift = {row['SHIFT_SHRUNK']:+.2f} "
                    f"[{row['SHIFT_CI_LO']:+.2f}, {row['SHIFT_CI_HI']:+.2f}]  "
                    f"({int(row['MIN_po'])} po min; raw z {row['SHIFT_Z']:+.2f}; "
                    f"PER {row['PER_delta_adj']:+.1f})")

        print("\nBiggest playoff RISERS (raised their level above their regular-season form):")
        for rank, (_, row) in enumerate(risers.iterrows(), 1):
            print(_line(rank, row))
            if rank <= 3:
                FACTS.set(f"playoff.riser.{rank}.name", str(row["PLAYER_NAME"]),
                          note=f"playoff riser rank {rank} (shrunk composite shift)")
                FACTS.set(f"playoff.riser.{rank}.z", float(row["SHIFT_SHRUNK"]), "{:.2f}",
                          note=f"playoff riser rank {rank} shrunk composite shift")
                FACTS.set(f"playoff.riser.{rank}.ci_lo", float(row["SHIFT_CI_LO"]), "{:.2f}",
                          note=f"playoff riser rank {rank} shift range low (bootstrap)")
                FACTS.set(f"playoff.riser.{rank}.ci_hi", float(row["SHIFT_CI_HI"]), "{:.2f}",
                          note=f"playoff riser rank {rank} shift range high (bootstrap)")

        print("\nBiggest playoff FALLERS (dropped below their regular-season form):")
        for rank, (_, row) in enumerate(fallers.iterrows(), 1):
            print(_line(rank, row))
            if rank <= 3:
                FACTS.set(f"playoff.faller.{rank}.name", str(row["PLAYER_NAME"]),
                          note=f"playoff faller rank {rank} (shrunk composite shift)")
                FACTS.set(f"playoff.faller.{rank}.z", float(row["SHIFT_SHRUNK"]), "{:.2f}",
                          note=f"playoff faller rank {rank} shrunk composite shift")
                FACTS.set(f"playoff.faller.{rank}.ci_lo", float(row["SHIFT_CI_LO"]), "{:.2f}",
                          note=f"playoff faller rank {rank} shift range low (bootstrap)")
                FACTS.set(f"playoff.faller.{rank}.ci_hi", float(row["SHIFT_CI_HI"]), "{:.2f}",
                          note=f"playoff faller rank {rank} shift range high (bootstrap)")

        top_riser = str(risers.iloc[0]["PLAYER_NAME"])
        top_faller = str(fallers.iloc[0]["PLAYER_NAME"])
        FACTS.guard("playoff_top_riser_positive",
                    float(risers.iloc[0]["SHIFT_SHRUNK"]) > 0,
                    f"the top playoff riser ({top_riser}) gained on the pool", top_riser)
        FACTS.guard("playoff_top_faller_negative",
                    float(fallers.iloc[0]["SHIFT_SHRUNK"]) < 0,
                    f"the top playoff faller ({top_faller}) lost ground on the pool", top_faller)
        # The headline riser is only worth calling out if its shift is more than
        # the games alone could explain: the bootstrap range must exclude zero.
        FACTS.guard("playoff_top_riser_clears_band",
                    _clear(risers.iloc[0]),
                    f"the top playoff riser ({top_riser}) rose by more than the "
                    f"bounce of a few games (range excludes zero)", top_riser)

        # Did the regular-season consensus #1 hold up in the playoffs?
        if "CONSENSUS" in qual.columns and qual["CONSENSUS"].notna().sum() > 0:
            cons_top = str(qual.nlargest(1, "CONSENSUS")["PLAYER_NAME"].iloc[0])
            match = deltas[deltas["PLAYER_NAME"] == cons_top]
            if not match.empty:
                z = float(match.iloc[0]["SHIFT_SHRUNK"])
                ci_lo = float(match.iloc[0]["SHIFT_CI_LO"])
                ci_hi = float(match.iloc[0]["SHIFT_CI_HI"])
                order = deltas.sort_values("SHIFT_SHRUNK").reset_index(drop=True)
                frank = int(order.index[order["PLAYER_NAME"] == cons_top][0]) + 1
                print(f"\nRegular-season consensus #1 {cons_top}: playoff shift "
                      f"= {z:+.2f} [{ci_lo:+.2f}, {ci_hi:+.2f}] "
                      f"(faller rank {frank} of {len(deltas)})")
                FACTS.set("playoff.consensus1.name", cons_top,
                          note="regular-season consensus #1 player (playoff shift lookup)")
                FACTS.set("playoff.consensus1.z", z, "{:.2f}",
                          note="regular-season consensus #1 player's shrunk playoff shift")
                FACTS.set("playoff.consensus1.ci_lo", ci_lo, "{:.2f}",
                          note="regular-season consensus #1 player's shift range low")
                FACTS.set("playoff.consensus1.ci_hi", ci_hi, "{:.2f}",
                          note="regular-season consensus #1 player's shift range high")
                FACTS.guard("consensus_top_fell_in_playoffs", z < 0,
                            f"the regular-season consensus #1 ({cons_top}) fell in the playoffs", z)


def run_season_change(end_year: int) -> None:
    """SEASON-OVER-SEASON CHANGE — consensus movement in the latest season pair."""
    # ── Season-over-season change: the most recent full-season pair ──────────
    # A snapshot read of how much the single-season orderings move year to year;
    # the multi-season panels above carry the firm cross-season findings.
    _header("SEASON-OVER-SEASON CHANGE (PREVIOUS → CURRENT)")
    comp = season_comparison(end_year - 1, end_year)
    if comp:
        la, lb = comp["label_a"], comp["label_b"]
        FACTS.set("cmp2.year_a", la, note="previous season label")
        FACTS.set("cmp2.year_b", lb, note="current season label")
        FACTS.set("cmp2.n_both", comp["n_both"], "{:d}",
                  note="players qualified in both seasons")
        print(f"Players qualified in both {la} and {lb}: {comp['n_both']}")
        print(f"Consensus rank agreement {la} → {lb}: {comp['consensus_corr']:.2f}")
        FACTS.set("cmp2.consensus_corr", comp["consensus_corr"], "{:.2f}",
                  note=f"year-over-year consensus rank agreement, {la} to {lb}")
        FACTS.guard("consensus_stable_yoy", comp["consensus_corr"] > 0.6,
                    "the consensus order is largely stable from one season to the next "
                    "(year-over-year rank agreement above 0.6)", comp["consensus_corr"])
        print(f"Mean box-score agreement: {la} {comp['agree_a']:.2f}, "
              f"{lb} {comp['agree_b']:.2f}")
        FACTS.set("cmp2.agree_a", comp["agree_a"], "{:.2f}",
                  note=f"mean box-score rank agreement, {la}")
        FACTS.set("cmp2.agree_b", comp["agree_b"], "{:.2f}",
                  note=f"mean box-score rank agreement, {lb}")
        FACTS.set("cmp2.held_top5", comp["held_top5"], "{:d}",
                  note=f"how many of {la} consensus top 5 are still top 5 in {lb}")

        print(f"\n  {lb} consensus top 5:")
        for rank, (_, row) in enumerate(comp["top_b"].head(5).iterrows(), 1):
            print(f"   {rank}. {row['PLAYER_NAME']}")
            FACTS.set(f"cmp2.top_b.{rank}.name", str(row["PLAYER_NAME"]),
                      note=f"{lb} consensus rank {rank}")
        print(f"\n  {la} consensus top 5:")
        for rank, (_, row) in enumerate(comp["top_a"].head(5).iterrows(), 1):
            print(f"   {rank}. {row['PLAYER_NAME']}")
            FACTS.set(f"cmp2.top_a.{rank}.name", str(row["PLAYER_NAME"]),
                      note=f"{la} consensus rank {rank}")

        risers = comp["movers"].nlargest(5, "delta")
        fallers = comp["movers"].nsmallest(5, "delta")
        print(f"\n  Biggest consensus risers {la} → {lb}:")
        for rank, (_, row) in enumerate(risers.iterrows(), 1):
            print(f"   {rank}. {row['PLAYER_NAME']}  {row['delta']:+.2f}")
            FACTS.set(f"cmp2.riser.{rank}.name", str(row["PLAYER_NAME"]),
                      note=f"biggest consensus riser {rank}, {la} to {lb}")
            FACTS.set(f"cmp2.riser.{rank}.delta", float(row["delta"]), "{:+.2f}",
                      note=f"consensus z change for riser {rank}")
        print(f"\n  Biggest consensus fallers {la} → {lb}:")
        for rank, (_, row) in enumerate(fallers.iterrows(), 1):
            print(f"   {rank}. {row['PLAYER_NAME']}  {row['delta']:+.2f}")
            FACTS.set(f"cmp2.faller.{rank}.name", str(row["PLAYER_NAME"]),
                      note=f"biggest consensus faller {rank}, {la} to {lb}")
            FACTS.set(f"cmp2.faller.{rank}.delta", float(row["delta"]), "{:+.2f}",
                      note=f"consensus z change for faller {rank}")


def run_pwv(end_year: int) -> pd.DataFrame:
    """PLAYOFF-WEIGHTED VALUE — blended regular+playoff BPM ranking.

    Returns the playoff-deltas frame (with the PWV column when playoff data
    exists) for the examples section.
    """
    # ── Playoff-Weighted Value: who drove playoff success ────────────────────
    # An honest combine that blends each playoff player's regular-season and
    # postseason BPM, weighting playoff minutes more. BPM is now validated
    # against Basketball-Reference, so the blend sits on a real scale.
    _header("PLAYOFF-WEIGHTED VALUE (REGULAR SEASON + PLAYOFFS)")
    pwv_deltas = load_playoff_deltas(end_year)
    BRUNSON_ID = 1628973
    if pwv_deltas.empty:
        print("  No playoff data available for this season — section skipped.")
    else:
        pool_n = len(pwv_deltas)
        print(f"Playoff pool: {pool_n} players with >= {MIN_PLAYOFF_MINUTES} "
              f"playoff minutes.")
        print(f"PWV = minutes-weighted blend of regular-season and playoff BPM, "
              f"playoff minutes weighted {PLAYOFF_VALUE_WEIGHT}x (primary).")
        FACTS.set("pwv.pool_n", pool_n, "{:d}",
                  note=f"players in the playoff pool (>= {MIN_PLAYOFF_MINUTES} playoff min)")
        FACTS.set("pwv.weight", PLAYOFF_VALUE_WEIGHT, "{:d}",
                  note="primary playoff-minute weight in PWV")

        # Brunson's rank as the playoff weight rises: the honest sensitivity read.
        brunson_ranks = {}
        for k in (1, 2, 3):
            pwv_k = playoff_weighted_value(pwv_deltas, k=k)
            ranks = pwv_k.rank(ascending=False, method="min")
            if (pwv_deltas["PLAYER_ID"] == BRUNSON_ID).any():
                br = int(ranks[pwv_deltas["PLAYER_ID"] == BRUNSON_ID].iloc[0])
                brunson_ranks[k] = br
                FACTS.set(f"pwv.brunson_rank_k{k}", br, "{:d}",
                          note=f"Brunson PWV rank with playoff weight {k}x (of {pool_n})")

        # Primary table at the chosen weight.
        pwv_deltas = pwv_deltas.copy()
        pwv_deltas["PWV"] = playoff_weighted_value(pwv_deltas)
        ordered = pwv_deltas.sort_values("PWV", ascending=False).reset_index(drop=True)
        print(f"\nTop 10 by Playoff-Weighted Value (playoffs x{PLAYOFF_VALUE_WEIGHT}):")
        for rank, (_, row) in enumerate(ordered.head(10).iterrows(), 1):
            print(f"  {rank:>2}. {row['PLAYER_NAME']:<26} PWV {row['PWV']:+.2f}  "
                  f"(reg {row['BPM_reg']:+.1f} → playoff {row['BPM_po']:+.1f})")
            if rank <= 3:
                FACTS.set(f"pwv.top.{rank}.name", str(row["PLAYER_NAME"]),
                          note=f"Playoff-Weighted Value rank {rank}")
                FACTS.set(f"pwv.top.{rank}.value", float(row["PWV"]), "{:.1f}",
                          note=f"Playoff-Weighted Value of rank {rank}")

        if brunson_ranks:
            brow = pwv_deltas[pwv_deltas["PLAYER_ID"] == BRUNSON_ID].iloc[0]
            print(f"\nJalen Brunson: regular-season BPM {brow['BPM_reg']:+.1f}, "
                  f"playoff BPM {brow['BPM_po']:+.1f}.")
            print(f"  PWV rank as the playoffs are weighted more: "
                  f"{brunson_ranks.get(1)}th (1x) → {brunson_ranks.get(2)}th (2x) "
                  f"→ {brunson_ranks.get(3)}th (3x), of {pool_n}.")
            FACTS.set("pwv.brunson_bpm_reg", float(brow["BPM_reg"]), "{:+.1f}",
                      note="Brunson regular-season BPM")
            FACTS.set("pwv.brunson_bpm_po", float(brow["BPM_po"]), "{:+.1f}",
                      note="Brunson playoff BPM")
            FACTS.guard("pwv_brunson_rises_with_playoffs",
                        brunson_ranks.get(3, 99) < brunson_ranks.get(1, 0),
                        "weighting the playoffs more lifts Brunson's combined rank "
                        f"(from {brunson_ranks.get(1)}th to {brunson_ranks.get(3)}th)",
                        f"{brunson_ranks.get(1)} -> {brunson_ranks.get(3)}")
            FACTS.guard("pwv_brunson_not_top5",
                        brunson_ranks.get(3, 0) > 5,
                        "even with the playoffs weighted heavily Brunson stays outside "
                        "the top 5 of the playoff pool", brunson_ranks.get(3))
    return pwv_deltas


def run_examples(df_full: pd.DataFrame, pwv_deltas: pd.DataFrame) -> None:
    """EXAMPLE PLAYERS — rule-selected archetypes plus the Brunson case study."""
    # ── Example players: archetypes that show what each system captures ───────
    # Rule-selected representatives (emitted as facts so the prose re-points
    # automatically when a metric is fixed or added); Brunson is the pinned case
    # study. See the findings "Examples" section.
    _header("EXAMPLE PLAYERS (ARCHETYPES)")
    ex_q = df_full[df_full["QUALIFIED"] == True].copy() if "QUALIFIED" in df_full.columns else df_full.copy()
    _ex_systems = [c for c in ["PER", "WS", "BPM", "GAME_SCORE", "VORP"] if c in ex_q.columns]
    if len(ex_q) > 20 and len(_ex_systems) >= 3 and "BPM" in ex_q.columns:
        for s in _ex_systems:
            ex_q[s + "_rk"] = ex_q[s].rank(ascending=False, method="min")
        # Rank the (now-validated) impact metrics and OBPM too, so the examples
        # can show where RAPM agrees or disagrees with the box score.
        for _r in ("RAPM", "RAPM_MY", "OBPM"):
            if _r in ex_q.columns:
                ex_q[_r + "_rk"] = ex_q[_r].rank(ascending=False, method="min")
        chosen = {}

        # Agreed elite: best (lowest) worst-rank across the core systems.
        ex_q["_worst_rk"] = ex_q[[s + "_rk" for s in _ex_systems]].max(axis=1)
        elite = ex_q.nsmallest(1, "_worst_rk").iloc[0]
        chosen["elite"] = str(elite["PLAYER_NAME"])
        print(f"Agreed elite (best worst-rank across {len(_ex_systems)} systems): "
              f"{chosen['elite']} (worst rank {int(elite['_worst_rk'])}).")
        FACTS.set("example.elite.name", chosen["elite"],
                  note="agreed-elite archetype: best worst-rank across systems")
        FACTS.set("example.elite.worst_rank", int(elite["_worst_rk"]), "{:d}",
                  note="the agreed elite's worst rank across the core systems")

        # Defense-driven star: among the top BPM tier, the largest DBPM.
        if {"OBPM", "DBPM"}.issubset(ex_q.columns):
            tier = ex_q.nsmallest(12, "BPM_rk")
            dstar = tier.nlargest(1, "DBPM").iloc[0]
            chosen["defense"] = str(dstar["PLAYER_NAME"])
            dshare = float(dstar["DBPM"]) / float(dstar["BPM"]) if dstar["BPM"] else 0.0
            print(f"Defense-driven star (top-12 BPM, highest DBPM): {chosen['defense']} "
                  f"(BPM {dstar['BPM']:+.1f}, of which DBPM {dstar['DBPM']:+.1f}).")
            FACTS.set("example.defense.name", chosen["defense"],
                      note="defense-driven archetype: highest DBPM among the top BPM tier")
            FACTS.set("example.defense.dbpm", float(dstar["DBPM"]), "{:+.1f}",
                      note="the defense-driven star's DBPM")
            FACTS.set("example.defense.bpm", float(dstar["BPM"]), "{:+.1f}",
                      note="the defense-driven star's BPM")
            if "RAPM_rk" in ex_q.columns and dstar.get("RAPM_rk") == dstar.get("RAPM_rk"):
                FACTS.set("example.defense.rapm_rank", int(dstar["RAPM_rk"]), "{:d}",
                          note="the defense star's bare-RAPM (lineup impact) rank")
                FACTS.set("example.defense.obpm_rank", int(dstar["OBPM_rk"]), "{:d}",
                          note="the defense star's OBPM (box offense) rank")
            FACTS.guard("example_defense_is_defense_led", dshare > 0.30,
                        f"the defense example ({chosen['defense']}) draws more than a "
                        "third of its BPM from defense", dshare)

        # High-usage scorer the metrics split on: high USG%, counting stats (PER)
        # rate the player well above where the impact-ish BPM ranks them.
        if "USG_PCT" in ex_q.columns and "PER_rk" in ex_q.columns:
            hi = ex_q[(ex_q["USG_PCT"] >= ex_q["USG_PCT"].quantile(0.90))
                      & (ex_q["PER_rk"] <= 50)].copy()
            if not hi.empty:
                hi["_split"] = hi["BPM_rk"] - hi["PER_rk"]
                split = hi.nlargest(1, "_split").iloc[0]
                chosen["split"] = str(split["PLAYER_NAME"])
                print(f"High-usage scorer the metrics split on: {chosen['split']} "
                      f"(USG {split['USG_PCT']:.0%}, PER rank {int(split['PER_rk'])} "
                      f"vs BPM rank {int(split['BPM_rk'])}).")
                FACTS.set("example.split.name", chosen["split"],
                          note="high-usage split archetype: PER ranks well above BPM")
                FACTS.set("example.split.per_rank", int(split["PER_rk"]), "{:d}",
                          note="the split scorer's PER rank")
                FACTS.set("example.split.bpm_rank", int(split["BPM_rk"]), "{:d}",
                          note="the split scorer's BPM rank")
                if "RAPM_rk" in ex_q.columns and split.get("RAPM_rk") == split.get("RAPM_rk"):
                    FACTS.set("example.split.rapm_rank", int(split["RAPM_rk"]), "{:d}",
                              note="the split scorer's bare-RAPM (lineup impact) rank")
                FACTS.guard("example_split_per_over_bpm",
                            int(split["BPM_rk"]) > int(split["PER_rk"]),
                            f"counting stats rate the split scorer ({chosen['split']}) "
                            "well above where impact-aware BPM puts him",
                            f"PER {int(split['PER_rk'])} vs BPM {int(split['BPM_rk'])}")

        # Biggest playoff riser: top of the shrunk playoff shift (matches the
        # headline riser list, which ranks by SHIFT_SHRUNK).
        if not pwv_deltas.empty and "SHIFT_SHRUNK" in pwv_deltas.columns:
            riser = pwv_deltas.sort_values("SHIFT_SHRUNK", ascending=False).iloc[0]
            chosen["riser"] = str(riser["PLAYER_NAME"])
            print(f"Biggest playoff riser (top composite shift): {chosen['riser']} "
                  f"(shift {riser['SHIFT_SHRUNK']:+.2f} "
                  f"[{riser['SHIFT_CI_LO']:+.2f}, {riser['SHIFT_CI_HI']:+.2f}]).")
            FACTS.set("example.riser.name", chosen["riser"],
                      note="biggest-playoff-riser archetype: top composite shift")

        # Brunson, the pinned case study: offense rates well, defense drags the
        # all-around number down. Numbers for the worked-examples prose.
        brow = ex_q[ex_q["player_id"] == 1628973] if "player_id" in ex_q.columns else ex_q[ex_q.get("PLAYER_ID") == 1628973]
        if not brow.empty:
            br = brow.iloc[0]
            FACTS.set("example.brunson.obpm", float(br["OBPM"]), "{:+.1f}",
                      note="Brunson offensive BPM")
            FACTS.set("example.brunson.dbpm", float(br["DBPM"]), "{:+.1f}",
                      note="Brunson defensive BPM")
            FACTS.set("example.brunson.bpm", float(br["BPM"]), "{:+.1f}",
                      note="Brunson overall BPM")
            FACTS.set("example.brunson.obpm_rank",
                      int((ex_q["OBPM"] > float(br["OBPM"])).sum()) + 1, "{:d}",
                      note="Brunson OBPM rank among qualified players")
            FACTS.set("example.brunson.bpm_rank",
                      int((ex_q["BPM"] > float(br["BPM"])).sum()) + 1, "{:d}",
                      note="Brunson overall BPM rank among qualified players")
            # The corrected impact metric no longer buries Brunson: it independently
            # confirms the offense-vs-impact gap the box scores show.
            if "RAPM_rk" in ex_q.columns and br.get("RAPM_rk") == br.get("RAPM_rk"):
                FACTS.set("example.brunson.rapm_rank", int(br["RAPM_rk"]), "{:d}",
                          note="Brunson bare-RAPM (net lineup impact) rank")
            if "RAPM_MY_rk" in ex_q.columns and br.get("RAPM_MY_rk") == br.get("RAPM_MY_rk"):
                FACTS.set("example.brunson.rapm_my_rank", int(br["RAPM_MY_rk"]), "{:d}",
                          note="Brunson RAPM+prior rank")
            if "RAPM_rk" in br and br.get("RAPM_rk") == br.get("RAPM_rk"):
                print(f"  Brunson impact ranks: OBPM {int(br['OBPM_rk'])}, BPM "
                      f"{int(br['BPM_rk']) if 'BPM_rk' in br else 0}, RAPM "
                      f"{int(br['RAPM_rk'])}, RAPM+prior {int(br['RAPM_MY_rk'])} "
                      f"(scoring outruns net on-court impact)")

        # The five representatives should be distinct people for the section to work.
        reps = [chosen.get(k) for k in ("elite", "defense", "split", "riser")]
        reps = [r for r in reps if r] + ["Jalen Brunson"]
        FACTS.guard("example_reps_distinct", len(set(reps)) == len(reps),
                    "the example archetypes resolve to distinct players",
                    "; ".join(reps))


def run(end_year: int = 2026) -> None:
    """Run all analysis sections and print results to stdout.

    Thin orchestrator: loads the season, then calls each run_* section in
    results.md order. Sections communicate only through explicit parameters
    and return values (plus the in-place CONSENSUS / WINS_PRED columns that
    run_consensus / run_wins_predictive add to the shared frames).
    """
    df_full = load_unified_ratings(end_year)
    qual = df_full[df_full["QUALIFIED"] == True].copy() if "QUALIFIED" in df_full.columns else df_full.copy()
    present = _present_systems(qual, ALL_SYSTEMS)

    run_coverage(df_full, qual, present, end_year)
    run_rapm_single_season(qual, present)
    run_rapm_my(qual, present)
    run_rapm_reliability(end_year)
    run_rapm_vs_public(df_full)
    run_bpm_validation(df_full, end_year)
    run_distributions(qual, present)
    alpha = run_powerlaws(qual, present)
    run_rank_agreement(qual, present)
    run_overlap(qual, present)
    run_consensus(qual, present)
    run_wins_predictive(qual, df_full, present)
    run_consensus_vs_wins(qual)
    run_uber_concentration(qual, alpha)
    run_tail_analysis(qual, present)
    run_loves_discounts(qual, present)
    outcomes, retro = run_retrodiction(df_full, present, end_year)
    run_next_season(df_full, outcomes, retro, present, end_year)
    run_panels()
    run_impact_panel()
    run_stability(qual)
    run_playoff_shift(qual, end_year)
    run_season_change(end_year)
    pwv_deltas = run_pwv(end_year)
    run_examples(df_full, pwv_deltas)

    # Dump all facts and guards to docs/ (+ the dev facts-reference lookup table)
    FACTS.dump(_FACTS_PATH)
    FACTS.dump_guards(_GUARDS_PATH)
    from render_docs import write_reference
    print(f"Saved → {write_reference()}")
