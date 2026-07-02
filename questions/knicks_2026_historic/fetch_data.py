#!/usr/bin/env python3
"""
fetch_data.py — Phase 1 data collection for knicks_2026_historic.

Fetches (if not cached) for all seasons from START_YEAR to END_YEAR:
  - Playoff game logs (via LeagueGameFinder)
  - Regular-season game logs (via LeagueGameFinder)
  - Standings (via LeagueStandingsV3)

All CSVs land in the shared monorepo cache (nba_analysis/cache/).
Re-running is safe: cached files are not re-fetched.
"""

import _bootstrap  # noqa: F401  — use this worktree's nbakit (see questions/_bootstrap.py)

import os
import time
import sys

import pandas as pd

from knicks_2026_data import (
    START_YEAR, END_YEAR, PLAYOFFS, REGULAR_SEASON,
    fetch_game_logs, fetch_standings, season_str,
)
import nbakit.data as _nba
from nbakit.data import cache_exists

def _cache_dir():
    return _nba.default_cache_dir()


def fetch_all(start: int = START_YEAR, end: int = END_YEAR) -> None:
    cache_dir = _cache_dir()
    os.makedirs(cache_dir, exist_ok=True)

    total = (end - start + 1)
    po_fetched = rs_fetched = st_fetched = 0
    po_skip    = rs_skip    = st_skip    = 0

    for year in range(start, end + 1):
        label = season_str(year)
        sys.stdout.write(f"\r{label} ({year - start + 1}/{total})...  ")
        sys.stdout.flush()

        # Playoffs
        po_path = _nba.cache_path(year, PLAYOFFS, cache_dir)
        if cache_exists(po_path):
            po_skip += 1
        else:
            fetch_game_logs(year, PLAYOFFS, cache_dir)
            po_fetched += 1

        # Regular season
        rs_path = _nba.cache_path(year, REGULAR_SEASON, cache_dir)
        if cache_exists(rs_path):
            rs_skip += 1
        else:
            fetch_game_logs(year, REGULAR_SEASON, cache_dir)
            rs_fetched += 1

        # Standings
        st_path = os.path.join(cache_dir, f"{label}_standings.csv")
        if cache_exists(st_path):
            st_skip += 1
        else:
            fetch_standings(year, cache_dir)
            st_fetched += 1

    print(f"\nDone. Fetched: {po_fetched} playoff, {rs_fetched} RS, {st_fetched} standings. "
          f"Cached: {po_skip} playoff, {rs_skip} RS, {st_skip} standings.")


if __name__ == "__main__":
    print(f"Fetching data for {START_YEAR}–{END_YEAR} seasons...")
    print(f"Cache dir: {_cache_dir()}")
    fetch_all()
