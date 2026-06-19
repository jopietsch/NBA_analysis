"""
NBA Home Court Advantage — orchestrates the full analysis pipeline.

Run this module to fetch data (cached under cache/), generate all PNG charts,
run regression analysis, and print results to stdout.

  MPLBACKEND=Agg python3 nba_home_court_advantage.py

Data pipeline:  nba_home_court_data.py
Visualization:  nba_home_court_plots.py
Analysis:       nba_home_court_analysis.py
"""

import numpy as np
from nba_api.stats.library.parameters import SeasonType

from nba_home_court_data import (
    START_YEAR, END_YEAR, SKIP_PLAYOFF_YEARS, BBR_START_YEAR,
    fetch_all_seasons,
    compute_playoff_format_averages,
    compute_differential_stats, compute_rebound_stats, compute_margin_stats,
    compute_parity_stats, compute_series_stats, compute_series_stats_by_era,
    compute_shot_zone_stats, compute_league_3pa_stats,
    compute_league_pace_stats, compute_team_hca_stats,
    compute_tracking_rebound_stats, TRACKING_START_YEAR,
    fetch_all_referee_data, compute_referee_bias_stats,
    compute_attendance_season_stats, compute_attendance_covid_doseresponse,
)
from nba_home_court_plots import (
    plot_results, plot_mediation, plot_rest_altitude, plot_channel_3pa_control,
    plot_differential_analysis, plot_rebound_decomposition,
    plot_margin_analysis, plot_parity_analysis,
    plot_series_breakdown, plot_playoff_quality,
    plot_shot_zone_analysis, plot_3pa_hca_analysis,
    plot_pace_hca_analysis, plot_back_to_back, plot_team_hca_analysis,
    plot_attendance, plot_tracking_rebounding,
    plot_referee_era_distribution, plot_referee_rankings,
    plot_team_hca_by_era,
)


def main() -> None:
    reg_seasons, reg_pcts, po_seasons, po_pcts = fetch_all_seasons()
    format_reg_avg, format_po_avg, format_labels_short = compute_playoff_format_averages(
        reg_seasons, reg_pcts, po_seasons, po_pcts
    )
    plot_results(
        reg_seasons, reg_pcts, po_seasons, po_pcts,
        format_reg_avg, format_po_avg, format_labels_short,
    )

    reg_diff_seasons, reg_diff_stats = compute_differential_stats(START_YEAR, END_YEAR, SeasonType.regular)
    po_diff_seasons, po_diff_stats = compute_differential_stats(
        START_YEAR, END_YEAR, "Playoffs", skip_years=SKIP_PLAYOFF_YEARS
    )
    plot_differential_analysis(reg_diff_seasons, reg_diff_stats, po_diff_seasons, po_diff_stats)

    import nba_home_court_analysis as _reg
    game_df = _reg.build_game_dataset()
    plot_mediation(_reg.compute_mediation_decomposition(game_df))
    plot_rest_altitude(_reg.compute_rest_altitude_plotdata(game_df))
    plot_channel_3pa_control(_reg.compute_channel_3pa_control(game_df))

    reg_reb_seasons, reg_reb_stats = compute_rebound_stats(START_YEAR, END_YEAR, SeasonType.regular)
    po_reb_seasons, po_reb_stats = compute_rebound_stats(
        START_YEAR, END_YEAR, "Playoffs", skip_years=SKIP_PLAYOFF_YEARS
    )
    plot_rebound_decomposition(reg_reb_seasons, reg_reb_stats, po_reb_seasons, po_reb_stats,
                               win_seasons=reg_seasons, win_pcts=reg_pcts)

    print("\nFetching player-tracking rebounding data (cached under cache/)...")
    track_seasons, track_stats = compute_tracking_rebound_stats(TRACKING_START_YEAR, END_YEAR)
    if any(np.isfinite(v) for lst in track_stats.values() for v in lst):
        plot_tracking_rebounding(track_seasons, track_stats)
    else:
        print("  No tracking data cached yet — will fetch during next run.")

    reg_margin_seasons, reg_margin_stats = compute_margin_stats(START_YEAR, END_YEAR, SeasonType.regular)
    po_margin_seasons, po_margin_stats = compute_margin_stats(
        START_YEAR, END_YEAR, "Playoffs", skip_years=SKIP_PLAYOFF_YEARS
    )
    plot_margin_analysis(reg_margin_seasons, reg_margin_stats, po_margin_seasons, po_margin_stats)

    parity_seasons, parity_std = compute_parity_stats(START_YEAR, END_YEAR, SeasonType.regular)
    plot_parity_analysis(parity_seasons, parity_std, reg_seasons, reg_pcts)

    print("\nFetching attendance data (Basketball-Reference, cached under cache/)...")
    att_seasons, att_avg = compute_attendance_season_stats(BBR_START_YEAR, END_YEAR)
    att_dose_df = compute_attendance_covid_doseresponse(2021)
    if att_seasons:
        plot_attendance(att_seasons, att_avg, reg_seasons, reg_pcts, att_dose_df)
    else:
        print("  No attendance data returned — check BBR availability.")

    game_nums, series_pcts, game_counts = compute_series_stats(
        START_YEAR, END_YEAR, skip_years=SKIP_PLAYOFF_YEARS
    )
    era_series_data = compute_series_stats_by_era(
        START_YEAR, END_YEAR, skip_years=SKIP_PLAYOFF_YEARS
    )
    overall_po_pct = float(np.mean(po_pcts)) if po_pcts else 60.0
    plot_series_breakdown(game_nums, series_pcts, game_counts, era_series_data, overall_po_pct)
    plot_playoff_quality(_reg.compute_playoff_quality_plotdata(game_df))

    print("\nFetching shot zone data (LeagueDashTeamShotLocations)...")
    reg_zone_seasons, reg_zone_stats = compute_shot_zone_stats(START_YEAR, END_YEAR, SeasonType.regular)
    po_zone_seasons, po_zone_stats = compute_shot_zone_stats(
        START_YEAR, END_YEAR, "Playoffs", skip_years=SKIP_PLAYOFF_YEARS
    )
    if reg_zone_seasons:
        plot_shot_zone_analysis(reg_zone_seasons, reg_zone_stats, po_zone_seasons, po_zone_stats)
    else:
        print("  No shot zone data returned — column names may differ; inspect cached CSVs.")

    reg_tpa_seasons, reg_tpa_rates, reg_tpa_pcts = compute_league_3pa_stats(
        START_YEAR, END_YEAR, SeasonType.regular
    )
    po_tpa_seasons, po_tpa_rates, po_tpa_pcts = compute_league_3pa_stats(
        START_YEAR, END_YEAR, "Playoffs", skip_years=SKIP_PLAYOFF_YEARS
    )
    plot_3pa_hca_analysis(
        reg_tpa_seasons, reg_tpa_rates, reg_tpa_pcts,
        po_tpa_seasons,  po_tpa_rates,  po_tpa_pcts,
    )

    reg_pace_seasons, reg_pace_vals, reg_pace_pcts = compute_league_pace_stats(
        START_YEAR, END_YEAR, SeasonType.regular
    )
    po_pace_seasons, po_pace_vals, po_pace_pcts = compute_league_pace_stats(
        START_YEAR, END_YEAR, "Playoffs", skip_years=SKIP_PLAYOFF_YEARS
    )
    plot_pace_hca_analysis(
        reg_pace_seasons, reg_pace_vals, reg_pace_pcts,
        po_pace_seasons,  po_pace_vals,  po_pace_pcts,
    )
    plot_back_to_back(_reg.compute_back_to_back_plotdata(game_df))

    reg_team_stats = compute_team_hca_stats(START_YEAR, END_YEAR, "Regular Season")
    po_team_stats  = compute_team_hca_stats(
        START_YEAR, END_YEAR, "Playoffs",
        skip_years=SKIP_PLAYOFF_YEARS, min_games=20,
    )
    plot_team_hca_analysis(reg_team_stats, po_team_stats)

    early_team_stats = compute_team_hca_stats(START_YEAR, 2001, "Regular Season")
    late_team_stats  = compute_team_hca_stats(2002, END_YEAR, "Regular Season")
    plot_team_hca_by_era(early_team_stats, late_team_stats, late_label="2002–26")

    print("\nFetching referee data (BoxScoreSummaryV3, cached under cache/)...")
    ref_df = fetch_all_referee_data(
        START_YEAR, END_YEAR, "Playoffs", skip_years=SKIP_PLAYOFF_YEARS,
    )
    if ref_df is not None:
        bias_stats = compute_referee_bias_stats(
            ref_df, START_YEAR, END_YEAR, "Playoffs",
            skip_years=SKIP_PLAYOFF_YEARS, min_games=50,
        )
        plot_referee_era_distribution(bias_stats)
        plot_referee_rankings(bias_stats)
    else:
        print("  No referee data cached yet — will fetch during next run.")

    _reg.run(game_df)


if __name__ == "__main__":
    main()
