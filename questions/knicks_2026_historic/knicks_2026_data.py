"""
knicks_2026_data.py — data pipeline for the "Did the 2026 Knicks have a
historic playoff run?" analysis.

Fetches game logs from NBA.com via nba_api, caches them as CSVs, and provides
fetch_* and compute_* functions consumed by knicks_2026_plots and
knicks_2026_analysis. No matplotlib dependency.

Data sources:
  - NBA.com via the nba_api package (LeagueGameFinder etc.): every game result.
    The 2025-26 Knicks playoff run is the subject; historical playoff runs are
    the comparison set, so we pull league-wide playoff game logs back through
    the start year.

The specific comparison metrics (what makes a run "historic" — seed vs. result,
margin, opponent strength, win streaks, etc.) are intentionally not implemented
yet; see the TBD markers below and CLAUDE.md ("Adding a new analysis"). The
season/cache plumbing here is the stable foundation those metrics build on.
"""

import os
import time
import pandas as pd
import numpy as np

from nba_api.stats.endpoints import leaguegamefinder


# ── Config ────────────────────────────────────────────────────────────────────
KNICKS_TEAM_ID = 1610612752   # New York Knicks (nba_api franchise id)
SUBJECT_YEAR   = 2026         # the season under study (2025-26)
START_YEAR     = 1984         # first comparison season (ending year); 1983-84
SLEEP_SEC      = 1.0          # polite pause between API calls

# nba_api season_type_nullable= values (literals — the SeasonType parameter
# class confusingly omits 'Playoffs', so we keep the strings explicit).
PLAYOFFS       = "Playoffs"
REGULAR_SEASON = "Regular Season"

# Raw game logs are cached here as CSVs to avoid re-fetching from NBA.com.
CACHE_DIR = "cache"


def season_str(end_year: int) -> str:
    """2026 -> '2025-26'  (nba_api season format)."""
    return f"{end_year - 1}-{str(end_year)[-2:]}"


def short_label(end_year: int) -> str:
    """2026 -> '25–26'  (chart axis label)."""
    return f"{str(end_year - 1)[-2:]}–{str(end_year)[-2:]}"


def cache_path(end_year: int, season_type: str) -> str:
    season = season_str(end_year)
    return os.path.join(CACHE_DIR, f"{season}_{season_type.replace(' ', '_')}.csv")


def fetch_games(end_year: int, season_type: str = PLAYOFFS) -> pd.DataFrame:
    """Pull every game log for one season/type (one row per team per game).

    nba_api's LeagueGameFinder returns both teams' rows for each game. The
    MATCHUP field is 'NYK vs. BOS' for a home game and 'NYK @ BOS' for an away
    game; WL is 'W' or 'L'. Results are cached as CSVs under CACHE_DIR so repeat
    runs don't re-fetch from NBA.com.

    LeagueGameFinder quirk: it uses ``season_nullable=`` and
    ``season_type_nullable=`` (not the bare ``season=`` other endpoints use).
    """
    path = cache_path(end_year, season_type)
    if os.path.exists(path):
        return pd.read_csv(path)

    os.makedirs(CACHE_DIR, exist_ok=True)
    result = leaguegamefinder.LeagueGameFinder(
        season_nullable=season_str(end_year),
        season_type_nullable=season_type,
        league_id_nullable="00",   # NBA only (exclude G-League / WNBA)
    )
    df = result.get_data_frames()[0]
    df.to_csv(path, index=False)
    time.sleep(SLEEP_SEC)
    return df


# ── Computation ─────────────────────────────────────────────────────────────
# TBD — question-specific metrics. Add compute_* functions here once we settle
# on how to measure "historic" (see CLAUDE.md "Adding a new analysis"). Each
# should take fetched DataFrames and return tidy frames/values; no I/O, no
# plotting. The 2026 Knicks run is the subject; every metric needs the matching
# value computed across the historical comparison set so it can be ranked.
