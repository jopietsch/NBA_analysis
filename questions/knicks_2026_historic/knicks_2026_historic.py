#!/usr/bin/env python3
"""
knicks_2026_historic.py — pipeline orchestration for the
"Did the 2026 Knicks have a historic playoff run?" analysis.

Runs the whole thing in order: generate PNGs, then run the analysis which
writes knicks_2026_historic_results.md. Holds no data, plotting, or stats logic of its own.

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
    player_rs_2026   = data.fetch_player_game_logs(data.SUBJECT_YEAR, data.REGULAR_SEASON)

    print("Building champion stats table (all seasons)...")
    champions = data.build_champions_table(data.START_YEAR, data.END_YEAR)

    print("Building conference gap table (all seasons)...")
    gap_table = data.build_conference_gap_table(data.START_YEAR, data.END_YEAR)

    health_df = data.compute_opponent_health(
        player_po_2026, po_2026, data.KNICKS_TEAM_ID, standings_2026
    )
    continuity = data.compute_core_continuity(
        player_po_2026, player_rs_2026, po_2026, reg_2026, data.KNICKS_TEAM_ID
    )

    print("Loading betting odds from cache / BBR...")
    odds_df = data.fetch_game_odds(po_2026, data.KNICKS_TEAM_ID)
    ats_df  = data.compute_ats_stats(odds_df, po_2026, data.KNICKS_TEAM_ID)

    reg_srs_2026  = data.compute_srs(reg_2026)
    opp_po_excl   = data.compute_opponent_playoff_srs_excl(po_2026, data.KNICKS_TEAM_ID)
    series_df     = data.compute_series_margins(
        po_2026, data.KNICKS_TEAM_ID, reg_srs_2026, opp_po_excl
    )

    adj_samples = data.build_adjusted_margin_samples(data.START_YEAR, data.END_YEAR)
    hier = data.hierarchical_adjusted_margin_rank(adj_samples, data.SUBJECT_YEAR)

    elo_table = data.build_alt_rating_adjusted_table(
        data.compute_elo_ratings, data.START_YEAR, data.END_YEAR)
    bt_table = data.build_alt_rating_adjusted_table(
        data.compute_bradley_terry_ratings, data.START_YEAR, data.END_YEAR)
    capped_table = data.build_alt_rating_adjusted_table(
        data.compute_capped_srs, data.START_YEAR, data.END_YEAR)

    print("Generating charts...")
    paths = plots.plot_all(po_2026, reg_2026, standings_2026, champions, gap_table,
                           health_df=health_df, ats_df=ats_df, series_df=series_df,
                           posterior_df=hier.get("posterior"),
                           p_rank1=hier.get("p_rank1"),
                           continuity=continuity,
                           elo_table=elo_table, bt_table=bt_table,
                           capped_table=capped_table)
    for p in paths:
        print(f"  Saved → {os.path.basename(p)}")

    print("Running analysis...")
    analysis.main()


if __name__ == "__main__":
    main()
