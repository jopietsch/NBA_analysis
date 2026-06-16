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
import re
import sys
import time
import pandas as pd
import numpy as np

import nbakit.data as _nba

# ── ESPN API constants ────────────────────────────────────────────────────────
_ESPN_SCOREBOARD = (
    "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
)
_ESPN_ODDS_BASE = (
    "https://sports.core.api.espn.com/v2/sports/basketball/leagues/nba/events"
)
_ESPN_SLEEP = 0.5  # polite pause between ESPN API calls

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
    logs = _nba._fill_plus_minus(playoff_logs)
    df = logs[logs["TEAM_ID"] == team_id]
    return float(df["PLUS_MINUS"].mean())


def compute_clutch_rate(playoff_logs: pd.DataFrame,
                        team_id: int,
                        threshold: int = 5) -> float:
    """Fraction of games decided by <= threshold points (clutch games)."""
    df = _nba._fill_plus_minus(playoff_logs)[playoff_logs["TEAM_ID"] == team_id].copy()
    df["ABS_MARGIN"] = df["PLUS_MINUS"].abs()
    n = len(df)
    return float((df["ABS_MARGIN"] <= threshold).sum() / n) if n > 0 else 0.0


def compute_home_away_split(playoff_logs: pd.DataFrame,
                            team_id: int) -> tuple[float, float]:
    """Return (home_win_rate, away_win_rate) for a team's playoff games."""
    df = playoff_logs[playoff_logs["TEAM_ID"] == team_id].copy()
    home = df[df["MATCHUP"].str.contains(r" vs\.", na=False)]
    away = df[df["MATCHUP"].str.contains(r" @ ", na=False)]

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
    logs = _nba._fill_plus_minus(playoff_logs)
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
    logs = _nba._fill_plus_minus(po_logs)
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
    conf_map = standings.set_index("TeamID")["Conference"].to_dict()
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
    conf_map = standings.set_index("TeamID")["Conference"].to_dict()
    reg_logs = reg_logs.copy()
    reg_logs["TEAM_ID"] = reg_logs["TEAM_ID"].astype(int)
    reg_logs["CONF"] = reg_logs["TEAM_ID"].map(conf_map)

    # Each game is 2 rows; keep only one row per team and look at cross-conf games
    by_game = reg_logs.groupby("GAME_ID")
    east_wins = 0
    total = 0
    for _, grp in by_game:
        if len(grp) != 2:
            continue
        row_a, row_b = grp.iloc[0], grp.iloc[1]
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

def _home_abbr(matchup: str) -> str:
    """Extract home team abbreviation from nba_api MATCHUP string.

    'NYK vs. ATL' → 'NYK' (NYK is home)
    'NYK @ ATL'   → 'ATL' (ATL is home)
    """
    if " vs. " in matchup:
        return matchup.split(" vs. ")[0].strip()
    return matchup.split(" @ ")[1].strip()


def _parse_vegas_line(text: str, home_abbr: str) -> tuple[str | None, float | None]:
    """Parse a 'ABBR ±X.X' Vegas line string.

    Returns (line_team, line_value) where line_value < 0 means that team is
    favored. Returns ('PICK', 0.0) for even lines, (None, None) on failure.
    """
    text = text.strip()
    if not text or text.lower() in ("pick", "pick 'em", "n/a", ""):
        return ("PICK", 0.0)
    m = re.match(r"([A-Z]+)\s*([+-]?\d+\.?\d*)", text)
    if not m:
        return (None, None)
    return (m.group(1), float(m.group(2)))


def _espn_game_spread(game_date: str, knicks_home: bool) -> float | None:
    """Fetch the opening point spread for a Knicks game from ESPN's core API.

    Returns the spread from NYK's perspective:
      negative → Knicks are favorites (e.g. -5.5 = NYK -5.5)
      positive → Knicks are underdogs (e.g. +3.0 = NYK +3)
    Returns None if the spread is unavailable.
    """
    import requests
    date_str = game_date.replace("-", "")

    # Step 1: Find the ESPN event ID for the Knicks game on this date
    try:
        r = requests.get(
            _ESPN_SCOREBOARD,
            params={"dates": date_str, "groups": "5"},
            timeout=15,
        )
        time.sleep(_ESPN_SLEEP)
        if r.status_code != 200:
            return None
        data = r.json()
    except Exception as exc:
        print(f"  ESPN scoreboard error {game_date}: {exc}", file=sys.stderr)
        return None

    event_id = None
    for event in data.get("events", []):
        if "Knick" in event.get("name", ""):
            event_id = event["id"]
            break
    if event_id is None:
        return None

    # Step 2: Fetch odds for the event
    odds_url = f"{_ESPN_ODDS_BASE}/{event_id}/competitions/{event_id}/odds"
    try:
        r = requests.get(odds_url, timeout=15)
        time.sleep(_ESPN_SLEEP)
        if r.status_code != 200:
            return None
        items = r.json().get("items", [])
    except Exception as exc:
        print(f"  ESPN odds error {game_date}: {exc}", file=sys.stderr)
        return None

    if not items:
        return None

    # ESPN spread is the home team's spread (negative = home favored)
    spread = items[0].get("spread")
    if spread is None:
        return None

    return float(spread) if knicks_home else -float(spread)


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
        knicks_home = _home_abbr(matchup) == "NYK"
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
        po = _nba._fill_plus_minus(pd.read_csv(po_path))
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
        avg_opp_playoff = compute_games_weighted_opponent_srs(po, po_srs_series, champ)
        adj_playoff = compute_adjusted_margin(margin, avg_opp_playoff)
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
