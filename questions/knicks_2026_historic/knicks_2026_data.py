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
import pandas as pd
import numpy as np

import nbakit.data as _nba

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


def compute_adjusted_margin(raw_margin: float, avg_opp_srs: float) -> float:
    """Opponent-adjusted margin: raw_margin - avg_opp_SRS.

    Positive = performed better than a 0-SRS schedule would predict.
    """
    return raw_margin - avg_opp_srs


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
        avg_opp = compute_avg_opponent_srs(po, srs, champ)
        adj = compute_adjusted_margin(margin, avg_opp)
        clutch = compute_clutch_rate(po, champ)
        h_wr, a_wr = compute_home_away_split(po, champ)

        rows.append({
            "year":        year,
            "champion_id": champ,
            "wins":        wins,
            "losses":      losses,
            "win_rate":    wr,
            "avg_margin":  margin,
            "avg_opp_srs": avg_opp,
            "adj_margin":  adj,
            "clutch_rate": clutch,
            "home_wr":     h_wr,
            "away_wr":     a_wr,
        })
    return pd.DataFrame(rows)


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
