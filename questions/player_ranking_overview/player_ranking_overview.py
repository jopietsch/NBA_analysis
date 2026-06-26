#!/usr/bin/env python3
"""
player_ranking_overview.py — pipeline orchestrator.

Runs: data fetch → plots → analysis → writes docs/player_ranking_overview_results.md

Usage:
    MPLBACKEND=Agg python3 player_ranking_overview.py [--year 2025]
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

    print(f"=== Player Ranking Overview pipeline: {end_year - 1}–{str(end_year)[-2:]} ===")

    # 1. Data
    print("\n[1/3] Building unified ratings table...")
    from player_ranking_overview_data import load_unified_ratings
    df = load_unified_ratings(end_year)
    print(f"  {len(df)} players loaded")

    # 2. Plots
    print("\n[2/3] Generating charts...")
    from player_ranking_overview_plots import (
        plot_rank_agreement_heatmap,
        plot_system_outliers,
        plot_rank_value_distributions,
        plot_ordinal_vs_value_gap,
        plot_gini_by_system,
        plot_all_systems_distributions,
        plot_top20_table,
    )
    from player_ranking_overview_analysis import (
        ALL_SYSTEMS,
        _present_systems,
        _gini,
        _top_share,
        _build_consensus,
        _build_wins_predictive,
    )

    present = _present_systems(df, ALL_SYSTEMS)
    qual = df[df["QUALIFIED"] == True].copy() if "QUALIFIED" in df.columns else df.copy()

    plot_rank_agreement_heatmap(qual, present)
    plot_system_outliers(qual, present)
    plot_rank_value_distributions(qual, present)
    plot_ordinal_vs_value_gap(qual)

    # Gini scores
    gini_scores = {}
    for s in present:
        vals = qual[s].dropna().values
        if len(vals) >= 10:
            gini_scores[s] = _gini(vals)
    plot_gini_by_system(gini_scores)
    # Compute uber ratings before distribution chart so they can be highlighted there
    qual["CONSENSUS"] = _build_consensus(qual, present)
    qual["WINS_PRED"] = _build_wins_predictive(qual, present)
    uber_present = [s for s in ("CONSENSUS", "WINS_PRED")
                    if qual[s].notna().sum() >= 20]

    plot_all_systems_distributions(qual, present + uber_present,
                                   highlight=uber_present)
    plot_top20_table(qual, present + uber_present)

    if uber_present:
        from player_ranking_overview_plots import plot_uber_rating_comparison
        plot_uber_rating_comparison(qual)

    # 3. Analysis → results doc
    print("\n[3/3] Running analysis...")
    from player_ranking_overview_analysis import run
    results_path = os.path.join(os.path.dirname(__file__), "docs",
                                 "player_ranking_overview_results.md")
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
        f.write(f"# Player Ranking Overview: Analysis Results\n\n")
        f.write(f"Season: {end_year - 1}–{str(end_year)[-2:]}\n\n")
        f.write("```\n")
        f.write(output)
        f.write("\n```\n")
    print(f"\nResults written to {results_path}")
    print("=== Done ===")


if __name__ == "__main__":
    main()
