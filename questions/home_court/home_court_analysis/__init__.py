"""
home_court_analysis — statistical analysis of home court advantage.

Game-level statistical analyses on all cached data — one run_* function per
home_court_findings.md section that needs numbers: decline trend, format periods,
sequential R² decomposition, coefficient stability, rest/altitude/time zone,
rest buckets, margins, box-score and shot-zone differentials, referees,
travel, parity, 3PA rate, pace, series structure, and franchise HCA.

Called from home_court.main() after the plots.

This package is a themed split of what used to be a single ~5,900-line
home_court_analysis.py module. Every public and private name that used to
live directly in that module is re-exported here so `import home_court_analysis
as X; X.whatever` keeps working unchanged — see _features.py (feature
construction), _helpers.py (shared print/stat helpers), decline.py, mediation.py,
mechanisms.py, team_effects.py, and playoffs.py for the actual analysis code.
"""

from __future__ import annotations

import contextlib
import io
import sys
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from statsmodels.tools import sm_exceptions
from nba_api.stats.library.parameters import SeasonType

from nbakit.textfmt import section as _section_str, stars as _stars, p_value as _fmt_p
from nbakit.stats import shrink_to_mean, possessions as _possessions
from nbakit.data import normalize_game_id

import home_court_data as nba
from home_court_facts import FACTS

from ._features import (
    _classify_year, _era_for_year, _format_period_for_year,
    build_game_dataset, _add_quality_diff,
)
from ._helpers import (
    suppress_noisy_fit_warnings, _warn_if_not_converged,
    _header, _section, _mcfadden, _pp, _clean, _ci_lo_hi, _shrink_hca,
    _run_cointegration, _run_league_metric_analysis,
    _NOISY_FIT_WARNINGS, _W,
)
from .decline import (
    run_decline_trend, run_structural_break_test, run_cusum_test,
    compute_bayesian_changepoint, run_bayesian_changepoint,
    compute_multilevel_decline, run_multilevel_decline,
    compute_hca_forecast, run_hca_forecast,
    run_era_analysis, run_its_test, run_placebo_tests,
)
from .mediation import (
    compute_mediation_decomposition, _mediation_shares_np,
    compute_mediation_bootstrap, compute_channel_3pa_control,
    run_mediation_analysis, compute_mediation_sensitivity,
    run_mediation_sensitivity, compute_shap_channels, run_shap_channels,
    _oos_forecast, compute_oos_forecast, run_oos_forecast,
    _compute_shapley_shares, run_sequential_decomposition,
    run_stability_analysis, run_factor_summary,
    run_channel_event_study, run_multiple_comparisons_summary,
    _MED_KEYS, _SENS_CHANNELS, _SHAP_CHANNELS, _OOS_CHANNELS,
)
from .mechanisms import (
    run_differential_analysis, run_fta_distribution_analysis,
    run_referee_analysis, run_shot_zone_analysis,
    compute_rest_altitude_plotdata, run_rest_bucket_analysis,
    run_rebounding_decomposition, run_tracking_rebound_analysis,
    run_3pa_analysis, _run_granger_3pa, run_pace_analysis,
    run_travel_analysis, compute_back_to_back_plotdata,
    run_back_to_back_analysis, run_attendance_analysis,
    run_parity_correlation,
)
from .team_effects import (
    run_team_hca_analysis, run_franchise_era_comparison,
    run_hca_consistency_analysis, run_margin_analysis,
    run_quantile_margin_analysis, run_net_rating_analysis,
)
from .playoffs import (
    run_series_breakdown, run_series_era_split, run_series_simulation,
    compute_playoff_quality_plotdata, run_playoff_quality_decomposition,
    run_team_quality_robustness, run_format_period_analysis,
)


_RESULTS_PATH: str = "docs/home_court_results.md"
_FACTS_PATH = "docs/home_court_facts.json"
_GUARDS_PATH = "docs/home_court_guards.json"


def generate_results_text(df: pd.DataFrame | None = None) -> str:
    """Run every analysis and return the captured report body (no file I/O).

    Split out of run() so tests can regenerate the results in-memory and
    compare against the committed home_court_results.md without overwriting it.
    """
    buf = io.StringIO()

    with contextlib.redirect_stdout(buf):
        _header("NBA HOME COURT ADVANTAGE — REGRESSION ANALYSIS")
        print("Game-level logistic regression. Outcome: home_win (1/0) per game.")
        print("All data from cache/ — same source as the plots above.\n")

        if df is None:
            df = build_game_dataset()
        if df.empty:
            print("No game data found in cache/. Run the main script first to populate it.")
            return buf.getvalue()
        df = _add_quality_diff(df)

        parity_seasons, parity_std = nba.compute_parity_stats(
            nba.START_YEAR, nba.END_YEAR, "Regular Season"
        )
        att_seasons, att_avg = nba.compute_attendance_season_stats(
            nba.BBR_START_YEAR, nba.END_YEAR
        )
        dose_df = nba.compute_attendance_covid_doseresponse(2021)
        reg_by_year = df[df["is_playoff"] == 0].groupby("year")["home_win"].mean() * 100
        reg_pcts_by_season = {nba.short_label(y): float(pct) for y, pct in reg_by_year.items()}
        reg_seasons_sorted = sorted(reg_pcts_by_season)
        reg_pcts_sorted    = [reg_pcts_by_season[s] for s in reg_seasons_sorted]

        reg_zone_seasons, reg_zone_stats = nba.compute_shot_zone_stats(
            nba.START_YEAR, nba.END_YEAR, "Regular Season"
        )
        po_zone_seasons, po_zone_stats = nba.compute_shot_zone_stats(
            nba.START_YEAR, nba.END_YEAR, "Playoffs", skip_years=nba.SKIP_PLAYOFF_YEARS
        )

        results: dict = {}

        # Section order mirrors how home_court_findings.md uses the data
        # (first appearance, top-to-bottom).

        # §1 The 40-Year Decline (magnitude, then shape/timing of the drop)
        run_decline_trend(df)
        run_structural_break_test(df, results)
        run_cusum_test(df, results)
        results["bayesian_cp"] = run_bayesian_changepoint(df)
        run_multilevel_decline(df)
        run_hca_forecast(df)

        # §2 What Creates Home Court Advantage
        run_differential_analysis(df)
        run_fta_distribution_analysis(df)
        ref_df = nba.fetch_all_referee_data(
            nba.START_YEAR, nba.END_YEAR, "Playoffs",
            skip_years=nba.SKIP_PLAYOFF_YEARS,
        )
        if ref_df is not None:
            ref_bias_stats = nba.compute_referee_bias_stats(
                ref_df, nba.START_YEAR, nba.END_YEAR, "Playoffs",
                skip_years=nba.SKIP_PLAYOFF_YEARS, min_games=50,
            )
            if ref_bias_stats:
                run_referee_analysis(ref_bias_stats)
            else:
                print("   No officials met the minimum-games threshold.\n")
        else:
            print("   No cached referee data — run the analysis first to fetch it.\n")
        run_shot_zone_analysis(reg_zone_seasons, reg_zone_stats, po_zone_seasons, po_zone_stats)
        run_mediation_analysis(df)
        run_mediation_sensitivity(df)
        run_rest_bucket_analysis(df)
        run_factor_summary(df)

        # §3 What's Driving the Decline
        run_3pa_analysis(df)
        _run_granger_3pa(df)
        run_rebounding_decomposition(df)
        track_seasons, track_stats = nba.compute_tracking_rebound_stats(
            nba.TRACKING_START_YEAR, nba.END_YEAR,
        )
        if any(np.isfinite(v) for lst in track_stats.values() for v in lst):
            run_tracking_rebound_analysis(track_seasons, track_stats)
        else:
            print("   No cached player-tracking data — run the analysis first to fetch it.\n")
        run_oos_forecast(df)
        run_shap_channels(df)

        # §4 What Didn't Drive the Change (rule changes lead, then the situational
        # suspects, then the combined "put it all together" models)
        run_era_analysis(df)
        run_its_test(df)
        run_placebo_tests(df)
        run_channel_event_study(df)
        run_travel_analysis(df)
        run_back_to_back_analysis(df)
        run_pace_analysis(df)
        run_parity_correlation(parity_seasons, parity_std, reg_seasons_sorted, reg_pcts_sorted)
        run_attendance_analysis(att_seasons, att_avg, reg_seasons_sorted, reg_pcts_sorted, dose_df)
        run_sequential_decomposition(df)
        run_stability_analysis(df)

        # §5 The Playoff Picture
        run_series_breakdown(df)
        run_series_era_split(df)
        run_series_simulation(nba.compute_series_simulation(
            nba.START_YEAR, nba.END_YEAR, skip_years=nba.SKIP_PLAYOFF_YEARS,
        ))
        run_playoff_quality_decomposition(df)
        run_team_quality_robustness(df)
        run_format_period_analysis(df)

        # §6 Other Findings
        reg_hca_stats = nba.compute_team_hca_stats(
            nba.START_YEAR, nba.END_YEAR, "Regular Season", min_games=50,
        )
        po_hca_stats = nba.compute_team_hca_stats(
            nba.START_YEAR, nba.END_YEAR, "Playoffs",
            skip_years=nba.SKIP_PLAYOFF_YEARS, min_games=20,
        )
        run_team_hca_analysis(reg_hca_stats, po_hca_stats)

        early_hca_stats = nba.compute_team_hca_stats(nba.START_YEAR, 2001, "Regular Season")
        late_hca_stats  = nba.compute_team_hca_stats(2002, nba.END_YEAR, "Regular Season")
        run_franchise_era_comparison(early_hca_stats, late_hca_stats)

        run_hca_consistency_analysis(reg_hca_stats, po_hca_stats)
        run_margin_analysis(df)
        run_quantile_margin_analysis(df)
        run_net_rating_analysis(df)

        # Cross-test multiple-comparisons summary (spans every test above)
        run_multiple_comparisons_summary(df)

        print("\n" + "═" * _W + "\n")

    return buf.getvalue()


def run(df: pd.DataFrame | None = None) -> None:
    text = generate_results_text(df)
    with open(_RESULTS_PATH, "w") as f:
        f.write("# NBA Home Court Advantage — Regression Results\n\n")
        f.write("_Auto-generated by `home_court_analysis.py` — do not edit manually._  \n")
        f.write("_Re-run `MPLBACKEND=Agg python3 home_court.py` to refresh._\n\n")
        f.write("```\n")
        f.write(text)
        f.write("```\n")
    sys.stdout.write(f"Saved → {_RESULTS_PATH}\n")

    FACTS.dump(_FACTS_PATH)
    sys.stdout.write(f"Saved → {_FACTS_PATH}  ({len(FACTS)} facts)\n")

    FACTS.dump_guards(_GUARDS_PATH)
    from render_docs import write_reference
    sys.stdout.write(f"Saved → {write_reference()}\n")
    failed = FACTS.failed_guards()
    if failed:
        sys.stdout.write(f"\n⚠ {len(failed)} prose claim(s) no longer hold — update the docs:\n")
        for g in failed:
            sys.stdout.write(f"    {g['name']}: \"{g['claim']}\"  (now: {g['value']})\n")
    else:
        sys.stdout.write(f"Saved → {_GUARDS_PATH}  (all prose claims hold)\n")
