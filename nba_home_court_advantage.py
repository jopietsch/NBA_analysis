"""
NBA Home Court Advantage — orchestrates the full analysis pipeline.

Run this module to fetch data (cached under cache/), generate all PNG charts,
run regression analysis, and print results to stdout.

  MPLBACKEND=Agg python3 nba_home_court_advantage.py

Data pipeline:  nba_home_court_data.py
Visualization:  nba_home_court_plots.py
Regression:     nba_home_court_regression.py
"""

import numpy as np
from nba_api.stats.library.parameters import SeasonType

from nba_home_court_data import (
    START_YEAR, END_YEAR, SKIP_PLAYOFF_YEARS, TRAVEL_BUCKETS,
    fetch_all_seasons,
    compute_era_averages, compute_playoff_format_averages,
    compute_rest_stats, compute_differential_stats, compute_margin_stats,
    compute_parity_stats, compute_series_stats, compute_series_stats_by_era,
    compute_travel_stats, compute_shot_zone_stats, compute_league_3pa_stats,
    compute_league_pace_stats,
)
from nba_home_court_plots import (
    TRAVEL_COLORS, TRAVEL_LABELS,
    plot_results, plot_rest_analysis, plot_category_road_win_analysis,
    plot_differential_analysis, plot_margin_analysis, plot_parity_analysis,
    plot_series_breakdown, plot_shot_zone_analysis, plot_3pa_hca_analysis,
    plot_pace_hca_analysis,
)


def main() -> None:
    reg_seasons, reg_pcts, po_seasons, po_pcts = fetch_all_seasons()
    era_reg_avg, era_po_avg, era_labels_short = compute_era_averages(
        reg_seasons, reg_pcts, po_seasons, po_pcts
    )
    format_reg_avg, format_po_avg, format_labels_short = compute_playoff_format_averages(
        reg_seasons, reg_pcts, po_seasons, po_pcts
    )
    plot_results(
        reg_seasons, reg_pcts, po_seasons, po_pcts,
        era_reg_avg, era_po_avg, era_labels_short,
        format_reg_avg, format_po_avg, format_labels_short,
    )

    rest_seasons, rest_stats = compute_rest_stats(START_YEAR, END_YEAR, SeasonType.regular)
    plot_rest_analysis(rest_seasons, rest_stats,
                       season_label="Regular season",
                       output_path="nba_home_court_advantage_rest.png")

    po_rest_seasons, po_rest_stats = compute_rest_stats(
        START_YEAR, END_YEAR, "Playoffs", skip_years=SKIP_PLAYOFF_YEARS
    )
    plot_rest_analysis(po_rest_seasons, po_rest_stats,
                       season_label="Playoffs",
                       output_path="nba_home_court_advantage_rest_playoffs.png",
                       extra_subtitle="; first round each year dropped (no prior playoff game for rest calc)")

    reg_diff_seasons, reg_diff_stats = compute_differential_stats(START_YEAR, END_YEAR, SeasonType.regular)
    po_diff_seasons, po_diff_stats = compute_differential_stats(
        START_YEAR, END_YEAR, "Playoffs", skip_years=SKIP_PLAYOFF_YEARS
    )
    plot_differential_analysis(reg_diff_seasons, reg_diff_stats, po_diff_seasons, po_diff_stats)

    reg_margin_seasons, reg_margin_stats = compute_margin_stats(START_YEAR, END_YEAR, SeasonType.regular)
    po_margin_seasons, po_margin_stats = compute_margin_stats(
        START_YEAR, END_YEAR, "Playoffs", skip_years=SKIP_PLAYOFF_YEARS
    )
    plot_margin_analysis(reg_margin_seasons, reg_margin_stats, po_margin_seasons, po_margin_stats)

    parity_seasons, parity_std = compute_parity_stats(START_YEAR, END_YEAR, SeasonType.regular)
    plot_parity_analysis(parity_seasons, parity_std, reg_seasons, reg_pcts)

    game_nums, series_pcts, game_counts = compute_series_stats(
        START_YEAR, END_YEAR, skip_years=SKIP_PLAYOFF_YEARS
    )
    era_series_data = compute_series_stats_by_era(
        START_YEAR, END_YEAR, skip_years=SKIP_PLAYOFF_YEARS
    )
    overall_po_pct = float(np.mean(po_pcts)) if po_pcts else 60.0
    plot_series_breakdown(game_nums, series_pcts, game_counts, era_series_data, overall_po_pct)

    travel_seasons, travel_stats = compute_travel_stats(START_YEAR, END_YEAR, SeasonType.regular)
    if travel_seasons:
        plot_category_road_win_analysis(
            travel_seasons, travel_stats,
            category_order=TRAVEL_BUCKETS,
            colors=TRAVEL_COLORS,
            labels=TRAVEL_LABELS,
            title="Home Court Advantage by Away Team Travel Distance",
            season_label="Regular season",
            output_path="nba_home_court_travel.png",
            road_win_desc="home win % grouped by away team flight distance",
            y_label="Home win %",
        )

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

    import nba_home_court_regression
    nba_home_court_regression.run()


if __name__ == "__main__":
    main()
