#!/usr/bin/env python3
"""
player_rating_overview.py — pipeline orchestrator.

Runs: data fetch → plots → analysis → writes docs/player_rating_overview_results.md

Usage:
    MPLBACKEND=Agg python3 player_rating_overview.py [--year 2025]
"""

import argparse
import io
import os
import sys


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2025,
                        help="Season end year (default: 2025 = 2024-25 season)")
    args = parser.parse_args()
    end_year = args.year

    print(f"=== Player Rating Overview pipeline: {end_year - 1}–{str(end_year)[-2:]} ===")

    # 1. Data
    print("\n[1/3] Building unified ratings table...")
    from player_rating_overview_data import load_unified_ratings
    df = load_unified_ratings(end_year)
    print(f"  {len(df)} players loaded")

    # 2. Plots
    print("\n[2/3] Generating charts...")
    from player_rating_overview_plots import (
        plot_rank_agreement_heatmap,
        plot_system_outliers,
        plot_rank_value_distributions,
        plot_ordinal_vs_value_gap,
        plot_gini_by_system,
        plot_all_systems_distributions,
        plot_powerlaw_fits,
        plot_powerlaw_small_multiples,
        plot_top20_table,
        plot_playoff_shift,
        plot_retrodiction,
        plot_next_season_retrodiction,
        plot_panel_describe_vs_forecast,
        plot_rating_stability,
    )
    from player_rating_overview_analysis import (
        ALL_SYSTEMS,
        _present_systems,
        _gini,
        _top_share,
        _build_consensus,
        _build_wins_predictive,
        retrodiction_scores,
        next_season_retrodiction,
        panel_retrodiction,
        rating_stability,
        STABILITY_TOP_N,
        PANEL_SYSTEMS,
        PANEL_START_YEAR,
        PANEL_END_YEAR,
        RAPM_PANEL_SYSTEMS,
        RAPM_PANEL_START_YEAR,
        RAPM_PANEL_END_YEAR,
        OUTCOME_CALIBRATED,
    )

    present = _present_systems(df, ALL_SYSTEMS)
    qual = df[df["QUALIFIED"] == True].copy() if "QUALIFIED" in df.columns else df.copy()

    plot_rank_agreement_heatmap(qual, present)
    plot_system_outliers(qual, present)
    plot_rank_value_distributions(qual, present)
    plot_ordinal_vs_value_gap(qual)
    plot_powerlaw_fits(qual, present)
    plot_powerlaw_small_multiples(qual, present)

    # Compute uber ratings first so they can be included in the Gini and
    # distribution charts (highlighted, since they are the combined ratings).
    qual["CONSENSUS"] = _build_consensus(qual, present)
    qual["WINS_PRED"] = _build_wins_predictive(qual, present)
    uber_present = [s for s in ("CONSENSUS", "WINS_PRED")
                    if qual[s].notna().sum() >= 20]

    # Gini scores (box-score systems plus the two uber ratings)
    gini_scores = {}
    for s in present + uber_present:
        vals = qual[s].dropna().values
        if len(vals) >= 10:
            gini_scores[s] = _gini(vals)
    plot_gini_by_system(gini_scores, highlight=uber_present)

    plot_all_systems_distributions(qual, present + uber_present,
                                   highlight=uber_present)
    plot_top20_table(qual, present + uber_present)

    if uber_present:
        from player_rating_overview_plots import plot_uber_rating_comparison
        plot_uber_rating_comparison(qual)

    # Retrodiction: which rating rebuilds team point differential
    from player_rating_overview_data import load_team_outcomes, load_playoff_deltas
    outcomes = load_team_outcomes(end_year)
    retro = retrodiction_scores(df, outcomes, present, target="point_diff")
    plot_retrodiction(retro, OUTCOME_CALIBRATED)

    # Next-season retrodiction: predict this season from last season's ratings
    prior = load_unified_ratings(end_year - 1)
    if not prior.empty:
        nxt = next_season_retrodiction(prior, df, outcomes, present, target="point_diff")
        plot_next_season_retrodiction(retro, nxt)

    # Pooled describe-vs-forecast across every cached season-pair
    panel = panel_retrodiction(PANEL_START_YEAR, PANEL_END_YEAR, PANEL_SYSTEMS)
    plot_panel_describe_vs_forecast(panel)

    # Parallel impact-era panel: box scores + RAPM over the same RAPM-coverage seasons
    impact_panel = panel_retrodiction(RAPM_PANEL_START_YEAR, RAPM_PANEL_END_YEAR,
                                      RAPM_PANEL_SYSTEMS)
    plot_panel_describe_vs_forecast(
        impact_panel, out_name="impact_panel_describe_vs_forecast.svg")

    # Year-over-year player-rating stability across every cached season-pair
    stab = rating_stability(PANEL_START_YEAR, PANEL_END_YEAR, PANEL_SYSTEMS)
    _chance = STABILITY_TOP_N / len(qual) if len(qual) else None
    plot_rating_stability(stab, top_n=STABILITY_TOP_N, chance=_chance)

    # Regular-season vs playoff risers/fallers
    plot_playoff_shift(load_playoff_deltas(end_year))

    # 3. Analysis → results doc
    print("\n[3/3] Running analysis...")
    from player_rating_overview_analysis import run
    results_path = os.path.join(os.path.dirname(__file__), "docs",
                                 "player_rating_overview_results.md")
    buf = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buf
    try:
        run(end_year)
    finally:
        sys.stdout = old_stdout
    output = buf.getvalue()

    # Print to console and write to results doc
    print(output)
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, "w") as f:
        f.write(f"# Player Rating Overview: Analysis Results\n\n")
        f.write(f"Season: {end_year - 1}–{str(end_year)[-2:]}\n\n")
        f.write("```\n")
        f.write(output)
        f.write("\n```\n")
    print(f"\nResults written to {results_path}")
    print("=== Done ===")


if __name__ == "__main__":
    main()
