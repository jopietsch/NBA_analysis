"""
nbakit.data — shared NBA data primitives.

Season helpers, a CSV cache for nba_api game logs, SRS computation,
conference mapping, and champion identification. Question-specific data modules
import these and add their own compute_* functions on top.

Cache directory: reads NBA_CACHE_DIR env var; defaults to the nba_analysis/cache/
directory at the monorepo root so all questions share downloaded data.
Override: export NBA_CACHE_DIR=/path/to/cache
"""

import os
import time

import numpy as np
import pandas as pd

SLEEP_SEC      = 1.0
PLAYOFFS       = "Playoffs"
REGULAR_SEASON = "Regular Season"


# ── Cache ──────────────────────────────────────────────────────────────────────

def default_cache_dir() -> str:
    """Absolute path to the shared monorepo cache (nba_analysis/cache/)."""
    env = os.environ.get("NBA_CACHE_DIR")
    if env:
        return env
    # nbakit/nbakit/data.py → ../../ = nba_analysis/
    return os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "cache")
    )


# ── Season helpers ─────────────────────────────────────────────────────────────

def season_str(end_year: int) -> str:
    """2026 → '2025-26' (nba_api season format)."""
    return f"{end_year - 1}-{str(end_year)[-2:]}"


def short_label(end_year: int) -> str:
    """2026 → '25–26' (chart axis label)."""
    return f"{str(end_year - 1)[-2:]}–{str(end_year)[-2:]}"


def season_range_label(start_year: int, end_year: int) -> str:
    """(1984, 2026) → '1983–84 through 2025–26'."""
    s = f"{start_year - 1}–{str(start_year)[-2:]}"
    e = f"{end_year - 1}–{str(end_year)[-2:]}"
    return f"{s} through {e}"


def cache_path(end_year: int, season_type: str,
               cache_dir: str | None = None) -> str:
    d = cache_dir or default_cache_dir()
    fname = f"{season_str(end_year)}_{season_type.replace(' ', '_')}.csv"
    return os.path.join(d, fname)


# ── Fetchers ───────────────────────────────────────────────────────────────────

def fetch_game_logs(end_year: int, season_type: str = PLAYOFFS,
                    cache_dir: str | None = None) -> pd.DataFrame:
    """Fetch game logs for one season/type; cache as CSV.

    Returns one row per team per game (nba_api LeagueGameFinder format).
    MATCHUP is 'NYK vs. BOS' (home) or 'NYK @ BOS' (away); WL is 'W'/'L'.

    LeagueGameFinder quirk: uses season_nullable= and season_type_nullable=,
    not the bare season= other endpoints take.
    """
    path = cache_path(end_year, season_type, cache_dir)
    if os.path.exists(path):
        return pd.read_csv(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    from nba_api.stats.endpoints import leaguegamefinder
    df = leaguegamefinder.LeagueGameFinder(
        season_nullable=season_str(end_year),
        season_type_nullable=season_type,
        league_id_nullable="00",
    ).get_data_frames()[0]
    df.to_csv(path, index=False)
    time.sleep(SLEEP_SEC)
    return df


def fetch_standings(end_year: int,
                    cache_dir: str | None = None) -> pd.DataFrame:
    """Fetch team standings for one season; cache as CSV.

    Relevant columns: TeamID, Conference, WINS, LOSSES, DiffPointsPG.
    Uses LeagueStandingsV3 (season= format, not season_nullable=).
    """
    d = cache_dir or default_cache_dir()
    path = os.path.join(d, f"{season_str(end_year)}_standings.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    os.makedirs(d, exist_ok=True)
    from nba_api.stats.endpoints import leaguestandingsv3
    df = leaguestandingsv3.LeagueStandingsV3(
        league_id="00",
        season=season_str(end_year),
        season_type="Regular Season",
    ).get_data_frames()[0]
    df.to_csv(path, index=False)
    time.sleep(SLEEP_SEC)
    return df


# ── SRS ────────────────────────────────────────────────────────────────────────

def compute_srs(game_logs: pd.DataFrame) -> pd.Series:
    """Compute Simple Rating System from regular-season game logs.

    SRS = average point differential adjusted for strength of schedule.
    Solved as a least-squares linear system (I − A) @ srs = mean_margin,
    constrained to sum(srs) = 0 (league average = 0).

    Returns pd.Series indexed by TEAM_ID, values in points per game.
    """
    df = game_logs[["GAME_ID", "TEAM_ID", "PLUS_MINUS"]].dropna().copy()
    df["TEAM_ID"] = df["TEAM_ID"].astype(int)

    # Build opponent map from GAME_ID grouping (each game appears exactly twice)
    opp: dict[tuple, int] = {}
    for gid, grp in df.groupby("GAME_ID"):
        ids = grp["TEAM_ID"].tolist()
        if len(ids) == 2:
            opp[(gid, ids[0])] = ids[1]
            opp[(gid, ids[1])] = ids[0]

    df["OPP_ID"] = [opp.get((r.GAME_ID, r.TEAM_ID)) for r in df.itertuples()]
    df = df.dropna(subset=["OPP_ID"])
    df["OPP_ID"] = df["OPP_ID"].astype(int)

    teams = sorted(df["TEAM_ID"].unique())
    n = len(teams)
    idx = {t: i for i, t in enumerate(teams)}

    # Schedule matrix A[i,j] = fraction of team i's games played vs team j
    A = np.zeros((n, n))
    m = np.zeros(n)
    for tid, grp in df.groupby("TEAM_ID"):
        i = idx[tid]
        m[i] = grp["PLUS_MINUS"].mean()
        for opp_id, cnt in grp["OPP_ID"].value_counts().items():
            if opp_id in idx:
                A[i, idx[opp_id]] = cnt / len(grp)

    # Solve (I − A) @ srs = m  s.t.  sum(srs) = 0
    aug_A = np.vstack([np.eye(n) - A, np.ones((1, n))])
    aug_b = np.append(m, 0.0)
    srs_vals, _, _, _ = np.linalg.lstsq(aug_A, aug_b, rcond=None)

    return pd.Series(srs_vals, index=pd.Index(teams, name="TEAM_ID"), name="SRS")


# ── Champion identification ────────────────────────────────────────────────────

def identify_champion(playoff_logs: pd.DataFrame) -> int:
    """Return TEAM_ID of the season champion (team with most playoff wins).

    Works across formats: pre-2003 champions won 15 games; post-2003 won 16.
    Only the champion reaches 15 or 16 wins, so argmax is unambiguous.
    """
    wins = playoff_logs[playoff_logs["WL"] == "W"]["TEAM_ID"].value_counts()
    return int(wins.idxmax())
