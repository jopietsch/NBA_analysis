#!/usr/bin/env python3
"""
knicks_2026_historic.py — pipeline orchestration for the
"Did the 2026 Knicks have a historic playoff run?" analysis.

Runs the whole thing in order: generate PNGs, then run the analysis which
writes RESULTS.md. Holds no data, plotting, or stats logic of its own.

    MPLBACKEND=Agg python3 knicks_2026_historic.py
"""

import os

import knicks_2026_data as data
import knicks_2026_plots as plots


def main() -> None:
    import knicks_2026_analysis as analysis

    print("Loading 2025-26 data from cache...")
    po_2026          = data.fetch_game_logs(data.SUBJECT_YEAR, data.PLAYOFFS)
    reg_2026         = data.fetch_game_logs(data.SUBJECT_YEAR, data.REGULAR_SEASON)
    standings_2026   = data.fetch_standings(data.SUBJECT_YEAR)
    player_po_2026   = data.fetch_player_game_logs(data.SUBJECT_YEAR, data.PLAYOFFS)

    print("Building champion stats table (all seasons)...")
    champions = data.build_champions_table(data.START_YEAR, data.END_YEAR)

    print("Building conference gap table (all seasons)...")
    gap_table = data.build_conference_gap_table(data.START_YEAR, data.END_YEAR)

    health_df = data.compute_opponent_health(
        player_po_2026, po_2026, data.KNICKS_TEAM_ID, standings_2026
    )

    print("Generating charts...")
    paths = plots.plot_all(po_2026, reg_2026, standings_2026, champions, gap_table,
                           health_df=health_df)
    for p in paths:
        print(f"  Saved → {os.path.basename(p)}")

    print("Running analysis...")
    analysis.main()


if __name__ == "__main__":
    main()
