"""
Fetch and cache playoff referee data for all seasons.
Reads game IDs from the existing game-log cache and calls BoxScoreSummaryV3
once per game. Results land in cache/referee_<season>_Playoffs.csv.

Run time: ~40 minutes (one API call per game, 1s sleep between calls).
"""
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from nba_home_court_data import (
    START_YEAR, END_YEAR, SKIP_PLAYOFF_YEARS, fetch_referee_data
)

season_type = "Playoffs"

for year in range(START_YEAR, END_YEAR + 1):
    if year in SKIP_PLAYOFF_YEARS:
        print(f"  Skipping {year} (no playoffs)")
        continue
    fetch_referee_data(year, season_type)

print("Done.")
