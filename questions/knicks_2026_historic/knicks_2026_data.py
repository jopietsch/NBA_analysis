"""
knicks_2026_data.py — data pipeline for the "Did the 2026 Knicks have a
historic playoff run?" analysis.

All data fetching delegates to nbakit.data (shared monorepo cache at
nba_analysis/cache/).  This module adds the Knicks-specific config and all
compute_* functions consumed by knicks_2026_analysis and knicks_2026_plots.

No I/O inside compute_* — callers fetch the DataFrames, pass them in, and get
tidy frames/values back.
"""

import os
import sys
import pandas as pd
import numpy as np

import nbakit.data as _nba
from nbakit import espn as _espn
from nbakit.stats import t_interval
from nbakit.espn import parse_vegas_line as _parse_vegas_line  # noqa: F401  (used in tests)

# Re-export shared helpers so callers import from one place
from nbakit.data import (
    PLAYOFFS,
    REGULAR_SEASON,
    season_str,
    short_label,
    season_range_label,
    cache_path,
    fetch_game_logs,
    fetch_player_game_logs,
    fetch_standings,
    parse_min,
    compute_srs,
    identify_champion,
    is_home,
    home_abbr,
    merge_home_away_rows,
    team_conference_map,
    iter_game_pairs,
)

# ── Knicks-specific config ────────────────────────────────────────────────────
KNICKS_TEAM_ID = 1610612752   # New York Knicks franchise id
SUBJECT_YEAR   = 2026         # season under study (2025-26)
START_YEAR     = 1984         # first comparison season (1983-84)
END_YEAR       = 2026         # last season (same as SUBJECT_YEAR but explicit)

# NBA rounds — round numbers encoded in nba_api GAME_ID digits 7-8 are not
# reliable across eras.  We infer rounds from elimination games instead.
ROUND_NAMES = ["First Round", "Second Round", "Conference Finals", "Finals"]


# ── Per-season playoff summary ───────────────────────────────────────────────

def compute_playoff_record(playoff_logs: pd.DataFrame,
                           team_id: int) -> tuple[int, int, float]:
    """Return (wins, losses, win_rate) for a team's playoff run."""
    df = playoff_logs[playoff_logs["TEAM_ID"] == team_id]
    wins   = (df["WL"] == "W").sum()
    losses = (df["WL"] == "L").sum()
    rate   = wins / (wins + losses) if (wins + losses) > 0 else 0.0
    return int(wins), int(losses), float(rate)


def compute_playoff_margin(playoff_logs: pd.DataFrame,
                           team_id: int) -> float:
    """Return average point differential for a team's playoff run.

    Fills PLUS_MINUS from PTS for pre-1997 seasons where nba_api returns NaN.
    """
    logs = _nba.fill_plus_minus(playoff_logs)
    df = logs[logs["TEAM_ID"] == team_id]
    return float(df["PLUS_MINUS"].mean())


def compute_clutch_rate(playoff_logs: pd.DataFrame,
                        team_id: int,
                        threshold: int = 5) -> float:
    """Fraction of games decided by <= threshold points (clutch games)."""
    df = _nba.fill_plus_minus(playoff_logs)[playoff_logs["TEAM_ID"] == team_id].copy()
    df["ABS_MARGIN"] = df["PLUS_MINUS"].abs()
    n = len(df)
    return float((df["ABS_MARGIN"] <= threshold).sum() / n) if n > 0 else 0.0


def compute_home_away_split(playoff_logs: pd.DataFrame,
                            team_id: int) -> tuple[float, float]:
    """Return (home_win_rate, away_win_rate) for a team's playoff games."""
    df = playoff_logs[playoff_logs["TEAM_ID"] == team_id].copy()
    is_home_mask = df["MATCHUP"].apply(is_home)
    home = df[is_home_mask]
    away = df[~is_home_mask]

    def _rate(sub: pd.DataFrame) -> float:
        if len(sub) == 0:
            return float("nan")
        return float((sub["WL"] == "W").sum() / len(sub))

    return _rate(home), _rate(away)


# ── Opponent-quality metrics ─────────────────────────────────────────────────

def compute_opponent_srs(playoff_logs: pd.DataFrame,
                         reg_srs: pd.Series,
                         team_id: int) -> pd.Series:
    """Return SRS of each opponent faced by team_id in the playoffs.

    reg_srs is indexed by TEAM_ID (from compute_srs on the regular-season logs).
    Returns a Series indexed by opponent TEAM_ID, values = their regular-season SRS.
    Each opponent appears once (their SRS, not per-game).
    """
    df = playoff_logs[playoff_logs["TEAM_ID"] == team_id].copy()
    # Opponent ids: find the other team in each game
    game_teams = (
        playoff_logs.groupby("GAME_ID")["TEAM_ID"]
        .apply(list)
        .reset_index()
    )
    opp_ids: set[int] = set()
    for gid, grp in playoff_logs[playoff_logs["TEAM_ID"] == team_id].groupby("GAME_ID"):
        game_row = game_teams[game_teams["GAME_ID"] == gid]["TEAM_ID"].values[0]
        for tid in game_row:
            if tid != team_id:
                opp_ids.add(int(tid))

    result = {}
    for oid in opp_ids:
        result[oid] = float(reg_srs.get(oid, float("nan")))
    return pd.Series(result, name="OPP_SRS")


def compute_avg_opponent_srs(playoff_logs: pd.DataFrame,
                             reg_srs: pd.Series,
                             team_id: int) -> float:
    """Average regular-season SRS of all unique opponents faced in the playoffs."""
    opp = compute_opponent_srs(playoff_logs, reg_srs, team_id)
    return float(opp.mean()) if len(opp) > 0 else float("nan")


def compute_games_weighted_opponent_srs(playoff_logs: pd.DataFrame,
                                        reg_srs: pd.Series,
                                        team_id: int) -> float:
    """Games-weighted average opponent SRS.

    Unlike compute_avg_opponent_srs (unique-opponent average), weights each
    opponent's SRS by the number of games played against them.  A Finals
    opponent appearing in 5 games contributes 5 data points; a sweep opponent
    appearing in 4 games contributes 4.  This makes the metric consistent with
    how the raw margin is computed (also a per-game average), so:
        adj_margin = raw_margin − games_weighted_opp_srs
    correctly answers "how dominant per game after accounting for per-game
    opponent quality?"
    """
    team_logs = playoff_logs[playoff_logs["TEAM_ID"] == team_id]
    if team_logs.empty:
        return float("nan")

    gid_to_teams = (
        playoff_logs.groupby("GAME_ID")["TEAM_ID"]
        .apply(list)
        .to_dict()
    )

    srs_vals: list[float] = []
    for gid in team_logs["GAME_ID"].unique():
        for t in gid_to_teams.get(gid, []):
            if t != team_id:
                v = float(reg_srs.get(t, float("nan")))
                if not np.isnan(v):
                    srs_vals.append(v)
    return float(np.mean(srs_vals)) if srs_vals else float("nan")


def compute_expected_margin_overperformance(playoff_logs: pd.DataFrame,
                                            reg_srs: pd.Series,
                                            team_id: int) -> float:
    """Per-game overperformance vs. regular-season SRS prediction.

    For each game: expected_margin = team_SRS − opponent_SRS
    Returns mean(actual_margin − expected_margin).

    Positive = outperformed what the regular-season SRS would predict;
    negative = underperformed.  Measures "playoff elevation" — how much better
    or worse a champion ran compared to a team of their quality expected to
    perform against those opponents.

    Algebraically equivalent to:
        raw_margin − champion_SRS + games_weighted_opp_SRS
    """
    logs = _nba.fill_plus_minus(playoff_logs)
    team_srs = float(reg_srs.get(team_id, float("nan")))
    if np.isnan(team_srs):
        return float("nan")

    team_logs = logs[logs["TEAM_ID"] == team_id]
    if team_logs.empty:
        return float("nan")

    gid_to_teams = (
        playoff_logs.groupby("GAME_ID")["TEAM_ID"]
        .apply(list)
        .to_dict()
    )

    residuals: list[float] = []
    for _, row in team_logs.iterrows():
        actual = float(row["PLUS_MINUS"])
        if np.isnan(actual):
            continue
        gid = row["GAME_ID"]
        opp_srs_list = [
            float(reg_srs.get(t, float("nan")))
            for t in gid_to_teams.get(gid, [])
            if t != team_id
        ]
        opp_srs_list = [v for v in opp_srs_list if not np.isnan(v)]
        if not opp_srs_list:
            continue
        residuals.append(actual - (team_srs - opp_srs_list[0]))
    return float(np.mean(residuals)) if residuals else float("nan")


def compute_adjusted_margin(raw_margin: float, avg_opp_srs: float) -> float:
    """Opponent-adjusted margin: raw_margin - avg_opp_SRS.

    Positive = performed better than a 0-SRS schedule would predict.
    """
    return raw_margin - avg_opp_srs


def compute_opponent_playoff_srs_excl(po_logs: pd.DataFrame,
                                      team_id: int) -> pd.Series:
    """Playoff SRS for each opponent of team_id, computed from games NOT involving team_id.

    Removes the circularity in compute_playoff_srs: an opponent's SRS is no
    longer influenced by their series against the focal team, so it's an
    independent measure of their playoff form against other opponents.

    Opponents who only played the focal team (e.g. a first-round loser with no
    other playoff games) return NaN — they have no independent data.
    """
    focal_gids = set(po_logs[po_logs["TEAM_ID"] == team_id]["GAME_ID"].unique())
    indep_logs  = po_logs[~po_logs["GAME_ID"].isin(focal_gids)].copy()

    indep_srs = compute_srs(indep_logs) if not indep_logs.empty else pd.Series(dtype=float)

    gid_to_teams = po_logs.groupby("GAME_ID")["TEAM_ID"].apply(list).to_dict()
    opp_ids: set[int] = set()
    for gid in focal_gids:
        for tid in gid_to_teams.get(gid, []):
            if tid != team_id:
                opp_ids.add(int(tid))

    return pd.Series(
        {oid: float(indep_srs.get(oid, float("nan"))) for oid in opp_ids}
    )


def compute_margin_ci(po_logs: pd.DataFrame,
                      team_id: int,
                      confidence: float = 0.95) -> tuple[float, float]:
    """t-interval on the mean playoff margin (per game).

    Returns (lower, upper).  With 19 games the interval is wide — this is
    the honest uncertainty in the point estimate.
    """
    logs    = _nba.fill_plus_minus(po_logs)
    margins = logs[logs["TEAM_ID"] == team_id]["PLUS_MINUS"].dropna()
    n = len(margins)
    if n < 2:
        return float("nan"), float("nan")
    return t_interval(float(margins.mean()), float(margins.std(ddof=1)), n, confidence)


def per_game_adjusted_margins(po_logs: pd.DataFrame,
                              reg_srs: pd.Series,
                              team_id: int) -> np.ndarray:
    """Per-game opponent-adjusted margin for one team's playoff run.

    For each game i: g_i = actual_margin_i − opponent_reg_SRS_i.
    The opponent-adjusted margin reported elsewhere is mean(g_i); returning the
    per-game array lets callers bootstrap or shrink it.  Games whose opponent has
    no SRS (or a NaN margin) are dropped.
    """
    logs = _nba.fill_plus_minus(po_logs)
    team_logs = logs[logs["TEAM_ID"] == team_id]
    if team_logs.empty:
        return np.array([], dtype=float)

    gid_to_teams = po_logs.groupby("GAME_ID")["TEAM_ID"].apply(list).to_dict()
    vals: list[float] = []
    for _, row in team_logs.iterrows():
        margin = float(row["PLUS_MINUS"])
        if np.isnan(margin):
            continue
        opp = [t for t in gid_to_teams.get(row["GAME_ID"], []) if t != team_id]
        if not opp:
            continue
        osrs = float(reg_srs.get(opp[0], float("nan")))
        if np.isnan(osrs):
            continue
        vals.append(margin - osrs)
    return np.asarray(vals, dtype=float)


def bootstrap_adjusted_margin_rank(po_logs: pd.DataFrame,
                                   reg_srs: pd.Series,
                                   team_id: int,
                                   other_champ_adj,
                                   n_boot: int = 20000,
                                   confidence: float = 0.90,
                                   seed: int = 0) -> dict:
    """Bootstrap the team's opponent-adjusted margin and its all-time rank.

    Resamples the team's playoff games with replacement (iid game-level
    bootstrap) and recomputes the opponent-adjusted margin each time.  Each
    resample is then ranked against ``other_champ_adj`` (the adjusted margins of
    every OTHER champion — exclude the team's own season so the rank is not
    self-referential).  Rank 1 = best.

    Game-level resampling treats games as independent; games within a series are
    correlated, so the true spread is somewhat wider than this reports.

    Returns a dict with the point estimate, a credible interval on the adjusted
    margin, and the probability of finishing 1st / top-3 / top-5.
    """
    g = per_game_adjusted_margins(po_logs, reg_srs, team_id)
    other = np.asarray([float(a) for a in other_champ_adj], dtype=float)
    other = other[~np.isnan(other)]
    if g.size < 2 or other.size == 0:
        return {}

    rng   = np.random.default_rng(seed)
    draws = rng.choice(g, size=(n_boot, g.size), replace=True).mean(axis=1)
    ranks = 1 + (other[None, :] > draws[:, None]).sum(axis=1)

    lo_q, hi_q = (1 - confidence) / 2, (1 + confidence) / 2
    return {
        "adj_point":  float(g.mean()),
        "n_games":    int(g.size),
        "n_other":    int(other.size),
        "ci_lo":      float(np.quantile(draws, lo_q)),
        "ci_hi":      float(np.quantile(draws, hi_q)),
        "confidence": confidence,
        "p_rank1":    float((ranks == 1).mean()),
        "p_top3":     float((ranks <= 3).mean()),
        "p_top5":     float((ranks <= 5).mean()),
        "rank_median": float(np.median(ranks)),
        "rank_lo":    float(np.quantile(ranks, lo_q)),
        "rank_hi":    float(np.quantile(ranks, hi_q)),
        "draws":      draws,
    }


def compute_srs_se(reg_logs: pd.DataFrame) -> pd.Series:
    """Approximate standard error of each team's regular-season SRS.

    A team's SRS is dominated by its own average point margin; the schedule
    term (average opponent strength) is comparatively stable across a full
    season.  We therefore approximate SE(SRS) by the sampling error of the mean
    margin, sd(margin) / sqrt(n_games), indexed by TEAM_ID.  This understates
    total uncertainty slightly by ignoring schedule-term error, but captures the
    dominant source — enough to ask whether not knowing opponents' exact
    strength changes the ranking.
    """
    logs = _nba.fill_plus_minus(reg_logs)
    out = {}
    for tid, grp in logs.groupby("TEAM_ID"):
        m = grp["PLUS_MINUS"].dropna()
        n = len(m)
        out[int(tid)] = float(m.std(ddof=1) / np.sqrt(n)) if n >= 2 else float("nan")
    return pd.Series(out, name="SRS_SE")


def bootstrap_adjusted_margin_rank_srs_error(po_logs: pd.DataFrame,
                                             reg_srs: pd.Series,
                                             srs_se: pd.Series,
                                             team_id: int,
                                             other_champ_adj,
                                             n_boot: int = 20000,
                                             confidence: float = 0.90,
                                             seed: int = 0) -> dict:
    """Bootstrap the adjusted-margin rank while ALSO perturbing each opponent's
    SRS by its standard error.

    Same game-level resampling as ``bootstrap_adjusted_margin_rank``, but each
    iteration additionally draws a Normal(0, SE) shock for every opponent's SRS
    (one shock per opponent per iteration, shared across that opponent's games).
    The resulting interval reflects both game-to-game variance and the fact that
    the opponents' true strength is itself estimated.  The other champions are
    held at their point estimates, so this is a stress test of the subject's
    number, not a full re-ranking.
    """
    logs = _nba.fill_plus_minus(po_logs)
    team_logs = logs[logs["TEAM_ID"] == team_id]
    gid_to_teams = po_logs.groupby("GAME_ID")["TEAM_ID"].apply(list).to_dict()

    margins, opp_ids = [], []
    for _, row in team_logs.iterrows():
        margin = float(row["PLUS_MINUS"])
        if np.isnan(margin):
            continue
        opp = [t for t in gid_to_teams.get(row["GAME_ID"], []) if t != team_id]
        if not opp:
            continue
        osrs = float(reg_srs.get(opp[0], float("nan")))
        if np.isnan(osrs):
            continue
        margins.append(margin)
        opp_ids.append(int(opp[0]))

    other = np.asarray([float(a) for a in other_champ_adj], dtype=float)
    other = other[~np.isnan(other)]
    if len(margins) < 2 or other.size == 0:
        return {}

    m = np.asarray(margins, dtype=float)
    uniq = list(dict.fromkeys(opp_ids))
    opp_pos = {oid: i for i, oid in enumerate(uniq)}
    oi = np.asarray([opp_pos[o] for o in opp_ids])
    s = np.asarray([float(reg_srs.get(o)) for o in opp_ids])
    se_vec = np.asarray([float(srs_se.get(o, 0.0)) for o in uniq])
    se_vec = np.nan_to_num(se_vec, nan=0.0)

    n = m.size
    rng  = np.random.default_rng(seed)
    idx  = rng.integers(0, n, size=(n_boot, n))
    deltas = rng.normal(0.0, 1.0, size=(n_boot, len(uniq))) * se_vec[None, :]
    rows = np.arange(n_boot)[:, None]
    gd   = deltas[rows, oi[idx]]
    draws = (m[idx] - s[idx] - gd).mean(axis=1)
    ranks = 1 + (other[None, :] > draws[:, None]).sum(axis=1)

    lo_q, hi_q = (1 - confidence) / 2, (1 + confidence) / 2
    return {
        "adj_point":  float((m - s).mean()),
        "ci_lo":      float(np.quantile(draws, lo_q)),
        "ci_hi":      float(np.quantile(draws, hi_q)),
        "confidence": confidence,
        "p_rank1":    float((ranks == 1).mean()),
        "p_top3":     float((ranks <= 3).mean()),
        "p_top5":     float((ranks <= 5).mean()),
        "rank_median": float(np.median(ranks)),
    }


def shrink_adjusted_margin(po_logs: pd.DataFrame,
                           reg_srs: pd.Series,
                           team_id: int,
                           champ_adj_values,
                           confidence: float = 0.95) -> dict:
    """Normal-normal posterior for the team's TRUE opponent-adjusted margin.

    A 19-game margin selected because it is extreme overstates true strength.
    This pulls it back toward how dominant championship runs typically are.

    Prior : the other champions' adjusted-margin distribution, N(prior_mean,
            prior_var) with prior_var the observed between-champion variance.
            That variance still carries each champion's own small-sample noise,
            so it shrinks a little less than a noise-free prior would — i.e. the
            shrinkage here is conservative.
    Data  : the team's per-game adjusted margins, summarized by their sample mean
            with sampling variance s^2 / n.

    Returns the precision-weighted posterior mean, its credible interval, and the
    weight the data carries (vs. the prior).
    """
    from scipy.stats import norm

    g = per_game_adjusted_margins(po_logs, reg_srs, team_id)
    prior = np.asarray([float(v) for v in champ_adj_values], dtype=float)
    prior = prior[~np.isnan(prior)]
    if g.size < 2 or prior.size < 2:
        return {}

    data_mean    = float(g.mean())
    sampling_var = float(g.var(ddof=1)) / g.size
    prior_mean   = float(prior.mean())
    prior_var    = float(prior.var(ddof=1))
    if sampling_var <= 0 or prior_var <= 0:
        return {}

    post_prec  = 1.0 / prior_var + 1.0 / sampling_var
    post_var   = 1.0 / post_prec
    post_mean  = post_var * (prior_mean / prior_var + data_mean / sampling_var)
    weight_data = (1.0 / sampling_var) / post_prec

    z = float(norm.ppf((1.0 + confidence) / 2.0))
    half = z * float(np.sqrt(post_var))
    return {
        "data_mean":   data_mean,
        "prior_mean":  prior_mean,
        "post_mean":   post_mean,
        "post_sd":     float(np.sqrt(post_var)),
        "ci_lo":       post_mean - half,
        "ci_hi":       post_mean + half,
        "weight_data": float(weight_data),
        "confidence":  confidence,
    }


def compute_series_margins(po_logs: pd.DataFrame,
                           team_id: int,
                           reg_srs: pd.Series,
                           playoff_srs: pd.Series | None = None) -> pd.DataFrame:
    """Per-series breakdown of margins for a team's playoff run.

    Returns one row per opponent series in chronological order (R1 first,
    Finals last) with columns:
      opp_id, n_games, raw_margin, opp_reg_srs, reg_adj_margin
    and, if playoff_srs is provided:
      opp_playoff_srs, playoff_adj_margin

    Playoff SRS for opponents who only played the focal team is circular (their
    series against us determines their SRS).  Use playoff_adj_margin cautiously
    for opponents who played few games outside the focal team's series.
    """
    logs = _nba.fill_plus_minus(po_logs)
    team_logs = logs[logs["TEAM_ID"] == team_id].copy()
    if team_logs.empty:
        return pd.DataFrame()

    gid_to_opp: dict[str, int] = {}
    for gid, grp in po_logs.groupby("GAME_ID"):
        for tid in grp["TEAM_ID"].tolist():
            if tid != team_id:
                gid_to_opp[str(gid)] = int(tid)

    team_logs["OPP_ID"] = team_logs["GAME_ID"].astype(str).map(gid_to_opp)
    team_logs = team_logs.sort_values("GAME_DATE")
    opp_order = team_logs.drop_duplicates("OPP_ID")["OPP_ID"].tolist()

    rows = []
    for opp_id in opp_order:
        grp = team_logs[team_logs["OPP_ID"] == opp_id]
        raw = float(grp["PLUS_MINUS"].mean())
        opp_reg = float(reg_srs.get(opp_id, float("nan")))
        row: dict = {
            "opp_id":        int(opp_id),
            "n_games":       len(grp),
            "raw_margin":    raw,
            "opp_reg_srs":   opp_reg,
            "reg_adj_margin": raw - opp_reg if not np.isnan(opp_reg) else float("nan"),
        }
        if playoff_srs is not None:
            opp_po = float(playoff_srs.get(opp_id, float("nan")))
            row["opp_playoff_srs"]    = opp_po
            row["playoff_adj_margin"] = raw - opp_po if not np.isnan(opp_po) else float("nan")
        rows.append(row)

    return pd.DataFrame(rows).reset_index(drop=True)


# ── Era / pace normalization ──────────────────────────────────────────────────

def compute_league_scoring_avg(reg_logs: pd.DataFrame) -> float:
    """Average points per game per team across the regular season.

    Used to normalize margins across eras: a +10 margin in a 230-pts/team/game
    season is a different feat than +10 in a 200-pts/team/game season.
    """
    return float(reg_logs["PTS"].mean())


def compute_possessions_per_game(reg_logs: pd.DataFrame) -> float:
    """Estimated possessions per team per game for a season.

    Uses the standard box-score estimator on each team-game row,
        poss = FGA − OREB + TOV + 0.44·FTA,
    and averages over all team-games.  Unlike points-per-game, this isolates PACE
    (how many possessions) from EFFICIENCY (points per possession), so it is the
    right denominator for an era adjustment: the 3-point era scores more per
    possession without necessarily playing faster.
    """
    needed = {"FGA", "OREB", "TOV", "FTA"}
    if not needed.issubset(reg_logs.columns):
        return float("nan")
    poss = (reg_logs["FGA"] - reg_logs["OREB"]
            + reg_logs["TOV"] + 0.44 * reg_logs["FTA"])
    return float(poss.mean())


def compute_per100_margin(raw_margin: float, season_poss_per_game: float) -> float:
    """Convert a per-game point margin to points per 100 possessions.

    margin_per100 = raw_margin · 100 / poss_per_game.  This is the pace-neutral
    form of a margin: a +10 per game in a 100-possession era and a +10 in a
    92-possession era represent different per-possession dominance, and dividing
    by pace puts them on one scale.
    """
    if not season_poss_per_game or np.isnan(season_poss_per_game):
        return float("nan")
    return raw_margin * 100.0 / season_poss_per_game


def build_possession_table(start_year: int = START_YEAR,
                           end_year: int = END_YEAR,
                           cache_dir: str | None = None) -> pd.DataFrame:
    """Estimated regular-season possessions/team/game for every season.

    Columns: year, poss_per_game.
    """
    rows = []
    for year in range(start_year, end_year + 1):
        rs_path = cache_path(year, REGULAR_SEASON, cache_dir)
        if not os.path.exists(rs_path):
            continue
        rs = pd.read_csv(rs_path)
        rows.append({"year": year, "poss_per_game": compute_possessions_per_game(rs)})
    return pd.DataFrame(rows)


def compute_pace_adjusted_margin(raw_margin: float,
                                 season_scoring_avg: float,
                                 reference_scoring_avg: float) -> float:
    """Scale margin to a common scoring environment.

    pace_adj_margin = raw_margin * (reference_avg / season_avg)

    A team whose era had higher scoring gets a slight discount; a low-scoring
    era gets a slight boost.  The reference is the historical mean across all
    seasons in the dataset.
    """
    if season_scoring_avg == 0:
        return float("nan")
    return raw_margin * (reference_scoring_avg / season_scoring_avg)


# ── Conference strength ───────────────────────────────────────────────────────

def compute_conference_avg_srs(reg_srs: pd.Series,
                               standings: pd.DataFrame) -> dict[str, float]:
    """Average SRS by conference for one season.

    standings must have TeamID and Conference columns (from fetch_standings).
    Returns {'East': float, 'West': float}.
    """
    conf_map = team_conference_map(standings)
    east, west = [], []
    for tid, srs_val in reg_srs.items():
        conf = conf_map.get(int(tid))
        if conf == "East":
            east.append(srs_val)
        elif conf == "West":
            west.append(srs_val)
    return {
        "East": float(np.mean(east)) if east else float("nan"),
        "West": float(np.mean(west)) if west else float("nan"),
    }


def compute_srs_gap(conf_avgs: dict[str, float]) -> float:
    """West avg SRS - East avg SRS (positive = West stronger)."""
    return conf_avgs["West"] - conf_avgs["East"]


def compute_inter_conference_h2h(reg_logs: pd.DataFrame,
                                 standings: pd.DataFrame) -> float:
    """East inter-conference win rate (East wins / all E-vs-W games).

    Identifies cross-conference games from standings data.
    """
    conf_map = team_conference_map(standings)
    reg_logs = reg_logs.copy()
    reg_logs["TEAM_ID"] = reg_logs["TEAM_ID"].astype(int)
    reg_logs["CONF"] = reg_logs["TEAM_ID"].map(conf_map)

    east_wins = 0
    total = 0
    for row_a, row_b in iter_game_pairs(reg_logs):
        if {row_a["CONF"], row_b["CONF"]} != {"East", "West"}:
            continue
        total += 1
        winner = row_a if row_a["WL"] == "W" else row_b
        if winner["CONF"] == "East":
            east_wins += 1
    return float(east_wins / total) if total > 0 else float("nan")


# ── Playoff SRS (champion elevation) ─────────────────────────────────────────

def compute_playoff_srs(playoff_logs: pd.DataFrame) -> pd.Series:
    """Solve SRS from playoff game logs.

    Same algorithm as compute_srs (from nbakit) but applied to playoff games
    only.  Returns a Series indexed by TEAM_ID.  Because the playoff bracket is
    unbalanced (not every team plays every other team), the solution is a
    least-squares approximation rather than an exact system.
    """
    return compute_srs(playoff_logs)


def compute_playoff_elevation(po_logs: pd.DataFrame,
                               rs_logs: pd.DataFrame,
                               team_id: int) -> float:
    """Playoff SRS minus regular-season SRS for a single team.

    Positive = team was better in the playoffs than their regular-season
    rating predicted; negative = underperformed.
    """
    po_srs = compute_playoff_srs(po_logs)
    rs_srs = compute_srs(rs_logs)
    p = float(po_srs.get(team_id, float("nan")))
    r = float(rs_srs.get(team_id, float("nan")))
    if np.isnan(p) or np.isnan(r):
        return float("nan")
    return p - r


def compute_playoff_field_elevation(po_logs: pd.DataFrame,
                                    rs_logs: pd.DataFrame) -> pd.DataFrame:
    """Reg-season → playoff SRS elevation for every team that made the playoffs.

    For each playoff team: regular-season SRS, full playoff SRS (all of that
    team's playoff games), the elevation (playoff − regular), and playoff games
    played.  Uses the same full-playoff-SRS definition as
    compute_playoff_elevation, so the number is comparable across the whole
    field.  Sorted most-improved first.
    """
    rs_srs = compute_srs(rs_logs)
    po_srs = compute_playoff_srs(po_logs)
    games  = po_logs.groupby("TEAM_ID")["GAME_ID"].nunique()

    rows = []
    for tid in po_logs["TEAM_ID"].unique():
        r = float(rs_srs.get(tid, float("nan")))
        p = float(po_srs.get(tid, float("nan")))
        rows.append({
            "team_id":   int(tid),
            "reg_srs":   r,
            "po_srs":    p,
            "elevation": p - r,
            "po_games":  int(games.get(tid, 0)),
        })
    return (pd.DataFrame(rows)
            .sort_values("elevation", ascending=False)
            .reset_index(drop=True))


# ── Opponent health / player availability ─────────────────────────────────────

def compute_opponent_health(
    player_po_logs: pd.DataFrame,
    po_2026: pd.DataFrame,
    knicks_team_id: int,
    standings: pd.DataFrame,
    min_avg_threshold: float = 15.0,
) -> pd.DataFrame:
    """Measure key-player availability for each Knicks playoff opponent.

    For each opponent:
      - 'Core' players = those averaging >= min_avg_threshold minutes across
        ALL their 2026 playoff appearances (so injured players who missed the
        whole series are excluded if they appear nowhere; those who got hurt
        mid-series show as partially available).
      - health_score = avg(core players appearing per Knicks-series game) /
                       total_core  [0.0–1.0; 1.0 = fully healthy]

    Returns DataFrame ordered by series start date with columns:
      team_id, team_name, games_in_series, total_core,
      avg_core_per_game, missing_core_avg, health_score
    """
    logs = player_po_logs.copy()
    logs["MIN_FLOAT"] = logs["MIN"].apply(parse_min)

    # Map each Knicks playoff game to the opposing team id
    game_teams = (
        po_2026.groupby("GAME_ID")["TEAM_ID"]
        .apply(lambda s: [x for x in s.tolist() if x != knicks_team_id])
        .reset_index()
    )
    knicks_games = (
        po_2026[po_2026["TEAM_ID"] == knicks_team_id]
        .merge(game_teams.rename(columns={"TEAM_ID": "OPP_LIST"}), on="GAME_ID")
        .copy()
    )
    knicks_games["OPP_ID"] = knicks_games["OPP_LIST"].apply(
        lambda x: int(x[0]) if x else None
    )
    knicks_games = knicks_games.dropna(subset=["OPP_ID"])
    knicks_games["OPP_ID"] = knicks_games["OPP_ID"].astype(int)

    name_map = standings.set_index("TeamID").apply(
        lambda r: f"{r['TeamCity']} {r['TeamName']}", axis=1
    ).to_dict()

    rows = []
    for opp_id, series_games in knicks_games.groupby("OPP_ID"):
        opp_game_ids = set(series_games["GAME_ID"])
        opp_logs = logs[logs["TEAM_ID"] == opp_id].copy()
        if opp_logs.empty:
            continue

        # Core = players averaging >= threshold across their full playoff run
        avg_min = opp_logs.groupby("PLAYER_ID")["MIN_FLOAT"].mean()
        core_ids = set(avg_min[avg_min >= min_avg_threshold].index)
        total_core = len(core_ids)
        if total_core == 0:
            continue

        # Per Knicks-series game: count how many core players appeared
        series_logs = opp_logs[opp_logs["GAME_ID"].isin(opp_game_ids)]
        core_per_game = (
            series_logs[series_logs["PLAYER_ID"].isin(core_ids)]
            .groupby("GAME_ID")["PLAYER_ID"].nunique()
        )
        all_counts = core_per_game.reindex(list(opp_game_ids), fill_value=0)
        avg_core = float(all_counts.mean())

        rows.append({
            "team_id":           int(opp_id),
            "team_name":         name_map.get(int(opp_id), f"Team {int(opp_id)}"),
            "games_in_series":   len(opp_game_ids),
            "total_core":        total_core,
            "avg_core_per_game": avg_core,
            "missing_core_avg":  total_core - avg_core,
            "health_score":      avg_core / total_core,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        first_dates = (
            knicks_games.sort_values("GAME_DATE")
            .groupby("OPP_ID")["GAME_DATE"].first()
        )
        df["first_game_date"] = df["team_id"].map(first_dates)
        df = df.sort_values("first_game_date").reset_index(drop=True)
    return df


# ── Betting-market odds (ESPN core API) ───────────────────────────────────────


def _espn_game_spread(game_date: str, knicks_home: bool) -> float | None:
    """Opening point spread for a Knicks game, from NYK's perspective.

    negative → Knicks favored (e.g. -5.5 = NYK -5.5); positive → underdog.
    None if unavailable. ESPN reports the home team's spread, so flip the sign
    when the Knicks are on the road.
    """
    spread = _espn.home_spread(game_date, "Knick")
    if spread is None:
        return None
    return spread if knicks_home else -spread


def fetch_game_odds(po_2026: pd.DataFrame,
                    knicks_team_id: int,
                    cache_dir: str | None = None) -> pd.DataFrame:
    """Fetch Vegas point spreads for each Knicks 2026 playoff game via ESPN's API.

    Returns a DataFrame with one row per game:
      GAME_ID, GAME_DATE, knicks_home, knicks_spread
    where knicks_spread < 0 means Knicks were favored by that amount.
    Cached as 2025-26_Playoffs_odds.csv after the first fetch.
    """
    d = cache_dir or _nba.default_cache_dir()
    cache_file = os.path.join(d, "2025-26_Playoffs_odds.csv")
    if os.path.exists(cache_file):
        return pd.read_csv(cache_file)

    knicks_games = (
        po_2026[po_2026["TEAM_ID"] == knicks_team_id]
        .sort_values("GAME_DATE")
        .copy()
    )

    rows = []
    for _, game in knicks_games.iterrows():
        matchup     = str(game["MATCHUP"])
        knicks_home = home_abbr(matchup) == "NYK"
        date        = str(game["GAME_DATE"])

        print(f"  Fetching odds: {date} {matchup}…", file=sys.stderr, flush=True)
        spread = _espn_game_spread(date, knicks_home)

        rows.append({
            "GAME_ID":       game["GAME_ID"],
            "GAME_DATE":     date,
            "knicks_home":   knicks_home,
            "knicks_spread": spread,
        })

    df = pd.DataFrame(rows)
    os.makedirs(d, exist_ok=True)
    df.to_csv(cache_file, index=False)
    return df


def clustered_cover_significance(covered,
                                 clusters,
                                 p_null: float = 0.5) -> dict:
    """One-tailed test that the cover rate beats ``p_null``, adjusted for the
    clustering of games within playoff series.

    Games inside one series share a matchup and correlated spread errors, so
    treating them as independent coin flips overstates the evidence.  This
    inflates the variance by the design effect ``deff = 1 + (m0 − 1)·ICC``,
    where ICC is the one-way-ANOVA intraclass correlation of the cover outcomes
    within series and ``m0`` is the average cluster size.  The result is an
    effective sample size ``N / deff`` and a p-value computed on it.

    Returns a dict with the game-weighted cover rate, ICC, design effect,
    effective N, z and the adjusted p-value.
    """
    from scipy.stats import norm

    x = np.asarray(list(covered), dtype=float)
    c = np.asarray(list(clusters))
    N = x.size
    labels = pd.unique(c)
    k = len(labels)
    if N < 2 or k < 2 or k >= N:
        return {}

    grand = float(x.mean())
    sizes, means = [], []
    ss_within = 0.0
    for lab in labels:
        xi = x[c == lab]
        sizes.append(xi.size)
        means.append(float(xi.mean()))
        ss_within += float(((xi - xi.mean()) ** 2).sum())
    sizes = np.asarray(sizes, dtype=float)
    means = np.asarray(means, dtype=float)

    ss_between = float((sizes * (means - grand) ** 2).sum())
    msb = ss_between / (k - 1)
    msw = ss_within / (N - k)
    m0  = (N - (sizes ** 2).sum() / N) / (k - 1)

    denom = msb + (m0 - 1) * msw
    icc = (msb - msw) / denom if denom > 0 else 0.0
    icc = float(min(1.0, max(0.0, icc)))
    deff = 1.0 + (m0 - 1) * icc
    n_eff = N / deff

    se = float(np.sqrt(p_null * (1 - p_null) / n_eff))
    z  = (grand - p_null) / se if se > 0 else float("nan")
    p  = float(norm.sf(z)) if not np.isnan(z) else float("nan")
    return {
        "cover_rate": grand,
        "n_games":    int(N),
        "n_series":   int(k),
        "icc":        icc,
        "deff":       float(deff),
        "n_eff":      float(n_eff),
        "z":          float(z),
        "p_value":    p,
    }


def compute_ats_stats(odds_df: pd.DataFrame,
                      po_2026: pd.DataFrame,
                      knicks_team_id: int) -> pd.DataFrame:
    """Merge odds with actual margins and compute ATS (against-the-spread) stats.

    Returns a DataFrame with one row per game:
      GAME_ID, GAME_DATE, WL, actual_margin, knicks_spread,
      ats_margin (actual − spread), covered (bool)
    Only includes games where knicks_spread is not null.
    """
    knicks_margin = (
        po_2026[po_2026["TEAM_ID"] == knicks_team_id][["GAME_ID", "PLUS_MINUS", "WL"]]
        .copy()
    )
    knicks_margin.columns = ["GAME_ID", "actual_margin", "WL"]

    merged = odds_df.merge(knicks_margin, on="GAME_ID")
    merged = merged.dropna(subset=["knicks_spread", "actual_margin"])
    merged["ats_margin"] = merged["actual_margin"] - merged["knicks_spread"]
    merged["covered"] = merged["ats_margin"] > 0
    return merged.reset_index(drop=True)


# ── Season-range aggregation ──────────────────────────────────────────────────

def build_champions_table(start_year: int = START_YEAR,
                          end_year: int = END_YEAR,
                          cache_dir: str | None = None) -> pd.DataFrame:
    """Build a table of champion stats for every season in [start_year, end_year].

    Columns: year, champion_id, wins, losses, win_rate, avg_margin,
             avg_opp_srs, adj_margin, clutch_rate, home_wr, away_wr.

    Loads from shared cache; does NOT fetch from API — call fetch_game_logs
    first for all seasons you care about.
    """
    rows = []
    for year in range(start_year, end_year + 1):
        po_path = cache_path(year, PLAYOFFS, cache_dir)
        rs_path = cache_path(year, REGULAR_SEASON, cache_dir)
        if not os.path.exists(po_path) or not os.path.exists(rs_path):
            continue
        po = _nba.fill_plus_minus(pd.read_csv(po_path))
        rs = pd.read_csv(rs_path)

        champ = identify_champion(po)
        srs = compute_srs(rs)
        wins, losses, wr = compute_playoff_record(po, champ)
        margin = compute_playoff_margin(po, champ)
        avg_opp = compute_games_weighted_opponent_srs(po, srs, champ)
        adj = compute_adjusted_margin(margin, avg_opp)
        champ_srs = float(srs.get(champ, float("nan")))
        overperf = compute_expected_margin_overperformance(po, srs, champ)
        po_srs_series = compute_playoff_srs(po)
        champ_po_srs = float(po_srs_series.get(champ, float("nan")))
        elevation = champ_po_srs - champ_srs if not (np.isnan(champ_po_srs) or np.isnan(champ_srs)) else float("nan")
        opp_po_excl     = compute_opponent_playoff_srs_excl(po, champ)
        avg_opp_playoff = compute_games_weighted_opponent_srs(po, opp_po_excl, champ)
        adj_playoff     = compute_adjusted_margin(margin, avg_opp_playoff)
        clutch = compute_clutch_rate(po, champ)
        h_wr, a_wr = compute_home_away_split(po, champ)
        league_scoring = compute_league_scoring_avg(rs)

        rows.append({
            "year":                year,
            "champion_id":         champ,
            "wins":                wins,
            "losses":              losses,
            "win_rate":            wr,
            "avg_margin":          margin,
            "avg_opp_srs":         avg_opp,
            "adj_margin":          adj,
            "champion_reg_srs":    champ_srs,
            "champion_po_srs":     champ_po_srs,
            "playoff_elevation":   elevation,
            "overperformance":     overperf,
            "clutch_rate":         clutch,
            "home_wr":             h_wr,
            "away_wr":             a_wr,
            "league_scoring":      league_scoring,
            "avg_opp_playoff_srs": avg_opp_playoff,
            "adj_playoff_margin":  adj_playoff,
        })

    df = pd.DataFrame(rows)
    if not df.empty:
        ref_scoring = float(df["league_scoring"].mean())
        df["pace_adj_margin"] = df.apply(
            lambda r: compute_pace_adjusted_margin(
                r["avg_margin"], r["league_scoring"], ref_scoring
            ),
            axis=1,
        )
        # Pace-adjust the opponent-adjusted margin too: since both raw_margin and
        # opp_SRS are expressed in the same era's point-differential units, their
        # difference (adj_margin) inherits the same era inflation. Scaling by
        # (ref / season_scoring) puts it in a common unit across all eras.
        df["pace_adj_adj_margin"] = df.apply(
            lambda r: compute_pace_adjusted_margin(
                r["adj_margin"], r["league_scoring"], ref_scoring
            ),
            axis=1,
        )
    return df


def build_conference_gap_table(start_year: int = START_YEAR,
                               end_year: int = END_YEAR,
                               cache_dir: str | None = None) -> pd.DataFrame:
    """SRS gap (West - East) for every season in [start_year, end_year].

    Columns: year, east_srs, west_srs, srs_gap, east_h2h_wr.
    """
    rows = []
    for year in range(start_year, end_year + 1):
        rs_path = cache_path(year, REGULAR_SEASON, cache_dir)
        st_path = os.path.join(
            cache_dir or _nba.default_cache_dir(),
            f"{season_str(year)}_standings.csv",
        )
        if not os.path.exists(rs_path) or not os.path.exists(st_path):
            continue
        rs = pd.read_csv(rs_path)
        standings = pd.read_csv(st_path)
        srs = compute_srs(rs)
        conf_avgs = compute_conference_avg_srs(srs, standings)
        gap = compute_srs_gap(conf_avgs)
        h2h = compute_inter_conference_h2h(rs, standings)

        rows.append({
            "year":      year,
            "east_srs":  conf_avgs["East"],
            "west_srs":  conf_avgs["West"],
            "srs_gap":   gap,
            "east_h2h_wr": h2h,
        })
    return pd.DataFrame(rows)


# ── Alternative opponent ratings (Elo, wins-only) ────────────────────────────

def compute_elo_ratings(reg_logs: pd.DataFrame,
                        k: float = 20.0,
                        home_adv: float = 100.0,
                        elo_per_point: float = 28.0) -> pd.Series:
    """End-of-season MOV-adjusted Elo for each team, expressed in points/game.

    A sequential, recency-weighted alternative to SRS.  Every team starts the
    season at 1500; games are processed in date order with the FiveThirtyEight
    NBA update:

        expected_home = 1 / (1 + 10^(-(elo_home + home_adv − elo_away)/400))
        mult          = ln(|margin| + 1) · 2.2 / (0.001·elo_diff_winner + 2.2)
        change        = k · mult · (result_home − expected_home)

    where ``elo_diff_winner`` is the winner's pre-game Elo (incl. home edge) minus
    the loser's; the margin-of-victory multiplier with that autocorrelation term
    is what stops favorites from running up the score.

    The final Elo is converted to points above league average by centering at the
    mean and dividing by ``elo_per_point`` (≈28 Elo per point of margin), so the
    result is on the same scale as SRS and can be dropped into the same
    games-weighted opponent-rating machinery.
    """
    logs = _nba.fill_plus_minus(reg_logs).copy()
    logs = logs.sort_values("GAME_DATE")
    elo = {int(t): 1500.0 for t in logs["TEAM_ID"].unique()}

    for _, grp in logs.groupby("GAME_ID", sort=False):
        if len(grp) != 2:
            continue
        rows = grp.to_dict("records")
        if is_home(rows[0]["MATCHUP"]):
            home, away = rows[0], rows[1]
        else:
            home, away = rows[1], rows[0]
        margin = float(home["PLUS_MINUS"])
        if np.isnan(margin):
            continue
        hid, aid = int(home["TEAM_ID"]), int(away["TEAM_ID"])
        eh, ea = elo[hid], elo[aid]
        eh_adj = eh + home_adv
        exp_home = 1.0 / (1.0 + 10.0 ** (-(eh_adj - ea) / 400.0))
        result_home = 1.0 if margin > 0 else (0.5 if margin == 0 else 0.0)
        elo_diff_w = (eh_adj - ea) if margin > 0 else (ea - eh_adj)
        mult = np.log(abs(margin) + 1.0) * (2.2 / (0.001 * elo_diff_w + 2.2))
        change = k * mult * (result_home - exp_home)
        elo[hid] = eh + change
        elo[aid] = ea - change

    s = pd.Series(elo, dtype=float)
    return (s - s.mean()) / elo_per_point


def compute_bradley_terry_ratings(reg_logs: pd.DataFrame,
                                  reg: float = 1.0,
                                  points_scale: float = 6.2,
                                  max_iter: int = 500,
                                  tol: float = 1e-10) -> pd.Series:
    """Wins-only Bradley–Terry strength ratings, converted to a points scale.

    Bradley–Terry models P(i beats j) = pi_i / (pi_i + pi_j) and is fit by
    maximum likelihood from win/loss ONLY — it never sees a point margin, making
    it the most independent cross-check on SRS (which is built entirely from
    margins).  Fit by the standard minorization–maximization iteration
    (Hunter 2004):

        pi_i ← (W_i + reg) / ( Σ_{j≠i} n_ij/(pi_i+pi_j) + 2·reg/(pi_i + 1) )

    The ``reg`` term adds one phantom win and one phantom loss against a
    league-average anchor (strength 1), which keeps undefeated or winless teams
    finite.  ``pi`` is renormalized to mean 1 each step.

    The raw rating is the centered log-strength ``log(pi)`` (natural-log-odds).
    To make it subtractable from a point margin it is multiplied by
    ``points_scale`` ≈ 6.2 points per log-odds — the conversion implied purely by
    the Elo convention (400 Elo per base-10 odds, 28 Elo per point), NOT fit to
    any margins.  So only the UNITS borrow a constant; the ordering stays
    100% wins-based.
    """
    logs = reg_logs.copy()
    teams = sorted(int(t) for t in logs["TEAM_ID"].unique())
    idx = {t: i for i, t in enumerate(teams)}
    n = len(teams)

    W = np.zeros(n, dtype=float)
    N = np.zeros((n, n), dtype=float)
    for _, grp in logs.groupby("GAME_ID", sort=False):
        if len(grp) != 2:
            continue
        rows = grp.to_dict("records")
        a, b = int(rows[0]["TEAM_ID"]), int(rows[1]["TEAM_ID"])
        ia, ib = idx[a], idx[b]
        N[ia, ib] += 1.0
        N[ib, ia] += 1.0
        if rows[0]["WL"] == "W":
            W[ia] += 1.0
        else:
            W[ib] += 1.0

    pi = np.ones(n, dtype=float)
    for _ in range(max_iter):
        pi_old = pi.copy()
        denom = np.zeros(n, dtype=float)
        for i in range(n):
            s = N[i] / (pi[i] + pi)
            s[i] = 0.0
            denom[i] = s.sum() + 2.0 * reg / (pi[i] + 1.0)
        pi = (W + reg) / np.where(denom > 0, denom, 1e-12)
        pi *= n / pi.sum()
        if np.max(np.abs(pi - pi_old)) < tol:
            break

    rating = np.log(pi)
    rating -= rating.mean()
    return pd.Series(rating * points_scale, index=teams, dtype=float)


def build_alt_rating_adjusted_table(rating_fn,
                                    start_year: int = START_YEAR,
                                    end_year: int = END_YEAR,
                                    cache_dir: str | None = None) -> pd.DataFrame:
    """Opponent-adjusted margin for every champion using an ALTERNATIVE rating.

    ``rating_fn(reg_logs) -> Series`` supplies the opponent rating (Elo points,
    Bradley–Terry log-strength, ...).  For each champion it computes
    ``adj = raw_margin − games_weighted_opponent_rating`` exactly as the SRS path
    does, so the only thing that changes is the rating system.

    Columns: year, champion_id, avg_margin, avg_opp_rating, adj_margin.
    """
    rows = []
    for year in range(start_year, end_year + 1):
        po_path = cache_path(year, PLAYOFFS, cache_dir)
        rs_path = cache_path(year, REGULAR_SEASON, cache_dir)
        if not os.path.exists(po_path) or not os.path.exists(rs_path):
            continue
        po = _nba.fill_plus_minus(pd.read_csv(po_path))
        rs = pd.read_csv(rs_path)
        champ = identify_champion(po)
        rating = rating_fn(rs)
        margin = compute_playoff_margin(po, champ)
        avg_opp = compute_games_weighted_opponent_srs(po, rating, champ)
        rows.append({
            "year":           year,
            "champion_id":    champ,
            "avg_margin":     margin,
            "avg_opp_rating": avg_opp,
            "adj_margin":     compute_adjusted_margin(margin, avg_opp),
        })
    return pd.DataFrame(rows)


# ── Series-level win-probability model ───────────────────────────────────────

_BO7_HOME_PATTERN = (True, True, False, False, True, False, True)  # 2-2-1-1-1


def build_title_run_specs(po_2026: pd.DataFrame,
                          reg_2026: pd.DataFrame,
                          standings_2026: pd.DataFrame) -> tuple:
    """Build the four-round bracket for the forward title-run simulation.

    Returns ``(champ_srs, series_specs, meta, name_map)``: the Knicks'
    regular-season SRS, the per-round ``series_specs`` for ``simulate_title_run``
    (opponent SRS + Knicks home-court), round metadata, and a team-id→name map.
    Shared by the analysis writeup and the rarity chart so both simulate the
    identical bracket.
    """
    srs = compute_srs(reg_2026)
    champ_srs = float(srs.get(KNICKS_TEAM_ID, float("nan")))

    gid_to_opp = {}
    for gid, grp in po_2026.groupby("GAME_ID"):
        for tid in grp["TEAM_ID"].tolist():
            if tid != KNICKS_TEAM_ID:
                gid_to_opp[gid] = int(tid)
    kn = po_2026[po_2026["TEAM_ID"] == KNICKS_TEAM_ID].copy()
    kn["OPP_ID"] = kn["GAME_ID"].map(gid_to_opp)
    kn = kn.dropna(subset=["OPP_ID"]).sort_values("GAME_DATE")

    name_map = standings_2026.set_index("TeamID").apply(
        lambda r: f"{r['TeamCity']} {r['TeamName']}", axis=1).to_dict()

    specs, meta = [], []
    for opp_id in kn.drop_duplicates("OPP_ID")["OPP_ID"]:
        grp = kn[kn["OPP_ID"] == opp_id].sort_values("GAME_DATE")
        opener = grp.iloc[0]
        knicks_home = " vs." in str(opener["MATCHUP"]) or " vs " in str(opener["MATCHUP"])
        opp_srs = float(srs.get(int(opp_id), float("nan")))
        specs.append({"opp_srs": opp_srs, "knicks_home": knicks_home})
        meta.append((int(opp_id), opp_srs, knicks_home))
    return champ_srs, specs, meta, name_map


def simulate_title_run(champ_srs: float,
                       series_specs: list,
                       sigma: float = 12.0,
                       hca: float = 3.0,
                       n_sims: int = 40000,
                       seed: int = 0) -> dict:
    """Monte-Carlo a champion's playoff path from regular-season strength.

    A forward model: it knows only each team's regular-season SRS and the venues,
    NOT that the champion would elevate in the playoffs.  So it answers "what
    should this bracket have produced?" and lets us measure how far the actual
    16-3 beat the forecast.

    Per game the champion's win probability is
        p = Phi( (champ_srs − opp_srs ± hca) / sigma ),
    with +hca at home and −hca on the road, ``sigma`` the single-game margin SD
    (~12 pts).  Each round is a best-of-7 with the 2-2-1-1-1 home pattern; the
    champion holds home court in a series when ``knicks_home`` is True.  Because
    the bracket is four best-of-7 rounds, every title run is exactly 16 wins, so
    the run's "cleanliness" is entirely its loss count (16-3 = 3 losses).

    ``series_specs`` is a list of dicts with keys ``opp_srs`` and ``knicks_home``,
    in round order.  Returns title probability, per-series win probabilities, the
    expected losses in a title run, and how often a title run is as clean as the
    actual one.
    """
    from scipy.stats import norm

    rng = np.random.default_rng(seed)
    n_series = len(series_specs)
    won = np.zeros((n_sims, n_series), dtype=bool)
    losses = np.zeros((n_sims, n_series), dtype=int)
    per_series_p = []

    for s, spec in enumerate(series_specs):
        opp_srs = float(spec["opp_srs"])
        pattern = _BO7_HOME_PATTERN if spec["knicks_home"] else tuple(
            not h for h in _BO7_HOME_PATTERN)
        p_slot = np.array([
            float(norm.cdf((champ_srs - opp_srs + (hca if home else -hca)) / sigma))
            for home in pattern
        ])
        per_series_p.append(float(np.mean(p_slot)))  # rough series-avg game prob

        u = rng.random((n_sims, 7))
        w = u < p_slot                       # champion wins that game slot
        cum_w = np.cumsum(w, axis=1)
        cum_l = np.cumsum(~w, axis=1)
        kn_has = cum_w[:, -1] >= 4
        op_has = cum_l[:, -1] >= 4
        kn_reach = np.where(kn_has, np.argmax(cum_w >= 4, axis=1), 99)
        op_reach = np.where(op_has, np.argmax(cum_l >= 4, axis=1), 99)
        clinch = np.minimum(kn_reach, op_reach)
        won[:, s] = kn_reach < op_reach
        losses[:, s] = cum_l[np.arange(n_sims), clinch]

    title = won.all(axis=1)
    title_losses = losses[title].sum(axis=1) if title.any() else np.array([])
    p_title = float(title.mean())

    # series-level win probabilities computed marginally (each round independent)
    series_winprob = [float(won[:, s].mean()) for s in range(n_series)]

    return {
        "p_title": p_title,
        "title_losses": title_losses,   # total losses in each simulated title run
        "series_winprob": series_winprob,
        "exp_losses_given_title": float(title_losses.mean()) if title_losses.size else float("nan"),
        "p_title_and_le3_losses": float((title & (losses.sum(axis=1) <= 3)).mean()),
        "p_le3_losses_given_title": float((title_losses <= 3).mean()) if title_losses.size else float("nan"),
        "sigma": sigma,
        "hca": hca,
        "n_sims": n_sims,
    }


def simulate_full_field_title_odds(po_2026: pd.DataFrame,
                                   reg_2026: pd.DataFrame,
                                   standings_2026: pd.DataFrame,
                                   sigma: float = 12.0,
                                   hca: float = 3.0,
                                   n_sims: int = 50000,
                                   seed: int = 0) -> pd.DataFrame:
    """Forward Monte-Carlo of the whole 2026 bracket from regular-season SRS.

    Generalizes ``simulate_title_run``: instead of following one team's realized
    path, it seeds all 16 playoff teams into the fixed NBA bracket (1v8, 4v5,
    3v6, 2v7 per conference; the better seed hosts in-conference; the better SRS
    hosts the Finals) and plays every best-of-7 forward with the same per-game
    model, ``p = Phi((SRS_a − SRS_b ± hca)/sigma)`` on the 2-2-1-1-1 home pattern.
    Every team therefore gets a title probability the realized-path model never
    assigns.  Returns a DataFrame (team_id, name, conference, seed, reg_srs,
    p_title) sorted by p_title descending.
    """
    from scipy.stats import norm

    rng = np.random.default_rng(seed)
    srs = compute_srs(reg_2026)
    playoff_ids = [int(t) for t in po_2026["TEAM_ID"].unique()]
    st = standings_2026[standings_2026["TeamID"].isin(playoff_ids)].copy()
    name_map = standings_2026.set_index("TeamID").apply(
        lambda r: f"{r['TeamCity']} {r['TeamName']}", axis=1).to_dict()

    teams = [int(t) for t in st["TeamID"]]
    idx_of = {tid: i for i, tid in enumerate(teams)}
    srs_arr = np.array([float(srs.get(t, float("nan"))) for t in teams])
    seed_of = {int(r["TeamID"]): int(r["PlayoffRank"]) for _, r in st.iterrows()}
    seed_arr = np.array([seed_of[t] for t in teams])
    conf_of = {int(r["TeamID"]): r["Conference"] for _, r in st.iterrows()}
    home_pat = np.array(_BO7_HOME_PATTERN)

    def battle(idx_a: np.ndarray, idx_b: np.ndarray, cross_conf: bool) -> np.ndarray:
        sa, sb = srs_arr[idx_a], srs_arr[idx_b]
        a_home = (sa >= sb) if cross_conf else (seed_arr[idx_a] <= seed_arr[idx_b])
        a_home_games = np.where(a_home[:, None], home_pat[None, :], ~home_pat[None, :])
        sign = np.where(a_home_games, hca, -hca)
        p = norm.cdf(((sa - sb)[:, None] + sign) / sigma)
        w = rng.random((n_sims, 7)) < p
        cum_w = np.cumsum(w, axis=1)
        cum_l = np.cumsum(~w, axis=1)
        a_reach = np.where(cum_w[:, -1] >= 4, np.argmax(cum_w >= 4, axis=1), 99)
        b_reach = np.where(cum_l[:, -1] >= 4, np.argmax(cum_l >= 4, axis=1), 99)
        return np.where(a_reach < b_reach, idx_a, idx_b)

    conf_champ = {}
    for conf in ("East", "West"):
        cst = st[st["Conference"] == conf]
        s = {int(r["PlayoffRank"]): idx_of[int(r["TeamID"])] for _, r in cst.iterrows()}
        const = lambda i: np.full(n_sims, i, dtype=int)
        sf1 = battle(battle(const(s[1]), const(s[8]), False),
                     battle(const(s[4]), const(s[5]), False), False)
        sf2 = battle(battle(const(s[3]), const(s[6]), False),
                     battle(const(s[2]), const(s[7]), False), False)
        conf_champ[conf] = battle(sf1, sf2, False)
    champ = battle(conf_champ["East"], conf_champ["West"], True)

    p_title = np.bincount(champ, minlength=len(teams)) / n_sims
    rows = [{
        "team_id":    tid,
        "name":       name_map.get(tid, f"Team {tid}"),
        "conference": conf_of[tid],
        "seed":       int(seed_arr[i]),
        "reg_srs":    float(srs_arr[i]),
        "p_title":    float(p_title[i]),
    } for i, tid in enumerate(teams)]
    return (pd.DataFrame(rows)
            .sort_values("p_title", ascending=False)
            .reset_index(drop=True))


# ── Hierarchical (partial-pooling) ranking ───────────────────────────────────

def build_adjusted_margin_samples(start_year: int = START_YEAR,
                                  end_year: int = END_YEAR,
                                  cache_dir: str | None = None) -> pd.DataFrame:
    """Per-champion opponent-adjusted margin with its sampling variance.

    For each season's champion, computes the per-game adjusted margins
    g_i = margin_i − opp_reg_SRS_i and summarizes them by their mean, game
    count, and sampling variance var(g)/n.  This is the input for the
    hierarchical model: the mean is the point estimate, the sampling variance
    says how trustworthy each champion's mean is given how many games it rests on.

    Columns: year, champion_id, adj_mean, n_games, samp_var.
    """
    rows = []
    for year in range(start_year, end_year + 1):
        po_path = cache_path(year, PLAYOFFS, cache_dir)
        rs_path = cache_path(year, REGULAR_SEASON, cache_dir)
        if not os.path.exists(po_path) or not os.path.exists(rs_path):
            continue
        po = _nba.fill_plus_minus(pd.read_csv(po_path))
        rs = pd.read_csv(rs_path)
        champ = identify_champion(po)
        srs = compute_srs(rs)
        g = per_game_adjusted_margins(po, srs, champ)
        if g.size < 2:
            continue
        rows.append({
            "year":        year,
            "champion_id": champ,
            "adj_mean":    float(g.mean()),
            "n_games":     int(g.size),
            "samp_var":    float(g.var(ddof=1) / g.size),
        })
    return pd.DataFrame(rows)


def hierarchical_adjusted_margin_rank(samples_df: pd.DataFrame,
                                      subject_year: int,
                                      n_draws: int = 40000,
                                      confidence: float = 0.90,
                                      seed: int = 0) -> dict:
    """Partial-pool every champion's true adjusted margin, then rank by posterior.

    A Gaussian hierarchical (random-effects) model:
        y_c  | theta_c ~ Normal(theta_c, v_c)       # observed mean, sampling var v_c
        theta_c        ~ Normal(mu, tau^2)          # population of true dominance

    The between-champion variance tau^2 is estimated by DerSimonian-Laird (the
    standard method-of-moments estimator from random-effects meta-analysis), and
    mu by inverse-variance weighting with (v_c + tau^2).  Each champion's
    posterior is then Normal(post_mean_c, post_var_c) with
        post_var_c  = 1 / (1/v_c + 1/tau^2)
        post_mean_c = post_var_c * (y_c/v_c + mu/tau^2),
    i.e. small-sample champions are pulled toward mu more strongly.

    Unlike the single-team shrinkage (`shrink_adjusted_margin`), EVERY champion
    is shrunk and carries its own posterior uncertainty, so the rank is a fair
    fight: a noisy rival can still come out on top in a given draw.  We simulate
    all champions jointly and report how often the subject is the true #1.

    Hyperparameters are treated as fixed (empirical Bayes); this ignores
    hyperparameter uncertainty, which is modest with 43 seasons.
    """
    df = samples_df.dropna(subset=["adj_mean", "samp_var"]).reset_index(drop=True)
    if len(df) < 3 or subject_year not in set(df["year"]):
        return {}

    y = df["adj_mean"].to_numpy(dtype=float)
    v = df["samp_var"].to_numpy(dtype=float)
    v = np.where(v <= 0, np.nanmin(v[v > 0]) if np.any(v > 0) else 1e-6, v)
    k = len(y)

    # DerSimonian-Laird tau^2
    w_fixed = 1.0 / v
    mu_fixed = float(np.sum(w_fixed * y) / np.sum(w_fixed))
    Q = float(np.sum(w_fixed * (y - mu_fixed) ** 2))
    c = float(np.sum(w_fixed) - np.sum(w_fixed ** 2) / np.sum(w_fixed))
    tau2 = max(0.0, (Q - (k - 1)) / c) if c > 0 else 0.0

    # Random-effects mu and per-champion posteriors
    w_re = 1.0 / (v + tau2)
    mu = float(np.sum(w_re * y) / np.sum(w_re))
    if tau2 > 0:
        post_var = 1.0 / (1.0 / v + 1.0 / tau2)
        post_mean = post_var * (y / v + mu / tau2)
    else:
        # No between-champion variance detected → full pooling (all equal to mu)
        post_var = np.zeros_like(v)
        post_mean = np.full_like(y, mu)

    rng = np.random.default_rng(seed)
    draws = rng.normal(post_mean[None, :], np.sqrt(post_var)[None, :],
                       size=(n_draws, k))
    subj_idx = int(np.where(df["year"].to_numpy() == subject_year)[0][0])
    subj = draws[:, subj_idx]
    ranks = 1 + (draws > subj[:, None]).sum(axis=1)

    from scipy.stats import norm
    z = float(norm.ppf((1 + confidence) / 2))
    lo_q, hi_q = (1 - confidence) / 2, (1 + confidence) / 2
    order = np.argsort(-post_mean)
    posterior = df.assign(
        post_mean=post_mean,
        post_sd=np.sqrt(post_var),
    ).iloc[order].reset_index(drop=True)

    return {
        "tau": float(np.sqrt(tau2)),
        "mu": mu,
        "n_champions": k,
        "subj_post_mean": float(post_mean[subj_idx]),
        "subj_post_sd": float(np.sqrt(post_var[subj_idx])),
        "subj_ci_lo": float(post_mean[subj_idx] - z * np.sqrt(post_var[subj_idx])),
        "subj_ci_hi": float(post_mean[subj_idx] + z * np.sqrt(post_var[subj_idx])),
        "confidence": confidence,
        "p_rank1": float((ranks == 1).mean()),
        "p_top3": float((ranks <= 3).mean()),
        "p_top5": float((ranks <= 5).mean()),
        "rank_median": float(np.median(ranks)),
        "rank_lo": float(np.quantile(ranks, lo_q)),
        "rank_hi": float(np.quantile(ranks, hi_q)),
        "posterior": posterior,
    }
