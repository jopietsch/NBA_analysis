import warnings

import numpy as np
import pandas as pd
import pytest

import nba_home_court_data as nba
import nba_home_court_regression as reg


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_game_df(n=300, seed=0, include_quality_diff=False):
    """Synthetic game-level DataFrame covering the required regression columns."""
    rng = np.random.default_rng(seed)
    era_labels = [e[0] for e in nba.ERA_DEFS]
    df = pd.DataFrame({
        "year":          rng.integers(nba.START_YEAR, nba.END_YEAR + 1, n),
        "is_playoff":    rng.integers(0, 2, n),
        "home_win":      rng.integers(0, 2, n),
        "rest_diff":     rng.choice([-2, -1, 0, 1, 2], n).astype(float),
        "tz_diff":       rng.integers(0, 4, n).astype(float),
        "altitude_home": rng.integers(0, 2, n),
        "covid":         rng.integers(0, 2, n),
        "margin":        rng.normal(3.0, 10.0, n),
        "foul_diff":     rng.normal(-1.0, 2.0, n),
        "fg_pct_diff":   rng.normal(1.0, 3.0, n),
        "efg_pct_diff":  rng.normal(1.0, 3.0, n),
        "tpa_rate_diff": rng.normal(0.0, 1.0, n),
        "fg3_pct_diff":  rng.normal(0.5, 2.0, n),
        "ft_pct_diff":   rng.normal(0.2, 1.5, n),
        "tpa_rate_avg":  rng.uniform(15.0, 45.0, n),
        "pace_avg":      rng.uniform(88.0, 105.0, n),
        "expected_pace": rng.uniform(88.0, 105.0, n),
        "distance_miles": rng.uniform(100.0, 2500.0, n),
        "game_in_series": rng.choice([np.nan, 1, 2, 3, 4, 5, 6, 7], n),
        "TEAM_NAME_home": rng.choice(["Alpha", "Beta", "Gamma", "Delta"], n),
        "TEAM_NAME_away": rng.choice(["Alpha", "Beta", "Gamma", "Delta"], n),
    })
    df["era"]           = df["year"].apply(reg._era_for_year)
    df["format_period"] = df["year"].apply(reg._format_period_for_year)
    if include_quality_diff:
        df["quality_diff"] = np.where(df["is_playoff"] == 1,
                                      rng.uniform(-0.3, 0.3, n),
                                      np.nan)
    return df


# ── Pure helper functions ─────────────────────────────────────────────────────

class TestEraForYear:
    def test_first_year_of_first_era(self):
        label, y1, y2, _ = nba.ERA_DEFS[0]
        assert reg._era_for_year(y1) == label

    def test_last_year_of_first_era(self):
        label, y1, y2, _ = nba.ERA_DEFS[0]
        assert reg._era_for_year(y2) == label

    def test_first_year_of_second_era(self):
        label, y1, y2, _ = nba.ERA_DEFS[1]
        assert reg._era_for_year(y1) == label

    def test_all_dataset_years_covered(self):
        for year in range(nba.START_YEAR, nba.END_YEAR + 1):
            assert reg._era_for_year(year) != "other", f"Year {year} not in any era"

    def test_out_of_range_returns_other(self):
        assert reg._era_for_year(1900) == "other"


class TestFormatPeriodForYear:
    def test_all_dataset_years_covered(self):
        for year in range(nba.START_YEAR, nba.END_YEAR + 1):
            assert reg._format_period_for_year(year) != "other", \
                f"Year {year} not in any format period"

    def test_out_of_range_returns_other(self):
        assert reg._format_period_for_year(1900) == "other"


class TestStars:
    @pytest.mark.parametrize("p,expected", [
        (0.0001, "***"),
        (0.001,  " **"),   # boundary: 0.001 is not < 0.001
        (0.005,  " **"),
        (0.01,   "  *"),   # boundary: 0.01 is not < 0.01
        (0.03,   "  *"),
        (0.05,   "   "),   # boundary: 0.05 is not < 0.05
        (0.5,    "   "),
    ])
    def test_star_thresholds(self, p, expected):
        assert reg._stars(p) == expected


class TestFmtP:
    def test_very_small_p_formatted_as_less_than(self):
        assert reg._fmt_p(0.0001) == "<0.001"
        assert reg._fmt_p(0.0) == "<0.001"

    def test_boundary_not_formatted_as_less_than(self):
        assert reg._fmt_p(0.001) == "0.001"

    def test_larger_p_three_decimal_places(self):
        assert reg._fmt_p(0.045) == "0.045"
        assert reg._fmt_p(0.5) == "0.500"

    def test_nan_returns_na(self):
        assert reg._fmt_p(float("nan")) == "n/a"


class TestPp:
    def test_zero_coef_gives_zero(self):
        assert reg._pp(0.0, 0.6) == pytest.approx(0.0)

    def test_at_half_pbar_factor_is_25_percent(self):
        # p*(1-p) at 0.5 = 0.25; coef * 0.25 * 100 = 25
        assert reg._pp(1.0, 0.5) == pytest.approx(25.0)

    def test_matches_manual_calculation(self):
        # coef=0.061, p_bar=0.603 → 0.061 * 0.603 * 0.397 * 100 ≈ 1.46
        assert reg._pp(0.061, 0.603) == pytest.approx(0.061 * 0.603 * 0.397 * 100, rel=1e-6)

    def test_symmetric_coef_sign(self):
        assert reg._pp(0.1, 0.6) == pytest.approx(-reg._pp(-0.1, 0.6))


class TestClean:
    def test_era_label_extracted(self):
        era_ref = nba.ERA_DEFS[0][0]
        second_era = nba.ERA_DEFS[1][0]
        name = f"C(era, Treatment('{era_ref}'))[T.{second_era}]"
        cleaned = reg._clean(name, era_ref, "1984")
        assert cleaned == f"era: {second_era}"

    def test_altitude_renamed(self):
        cleaned = reg._clean("altitude_home", "1984–94", "1984")
        assert cleaned == "altitude home (DEN/UTA)"

    def test_rest_diff_renamed(self):
        cleaned = reg._clean("rest_diff", "1984–94", "1984")
        assert cleaned == "rest diff (per day)"

    def test_tz_diff_renamed(self):
        cleaned = reg._clean("tz_diff", "1984–94", "1984")
        assert cleaned == "time zone diff (per zone)"

    def test_covid_renamed(self):
        cleaned = reg._clean("covid", "1984–94", "1984")
        assert cleaned == "COVID seasons"


# ── Empirical-Bayes shrinkage ─────────────────────────────────────────────────

class TestShrinkHca:
    def _stats(self, teams_data):
        return {
            t: {"hca": hca, "home_pct": hp, "road_pct": rp, "n_home": nh, "n_road": nr}
            for t, hca, hp, rp, nh, nr in teams_data
        }

    def test_shrunken_values_between_raw_and_league_mean(self):
        stats = self._stats([
            ("High", 30.0, 65.0, 35.0, 500, 500),
            ("Low",  10.0, 55.0, 45.0, 500, 500),
        ])
        shrunken, _ = reg._shrink_hca(stats)
        league_mean = 20.0
        assert shrunken["High"] < 30.0
        assert shrunken["High"] > league_mean
        assert shrunken["Low"]  > 10.0
        assert shrunken["Low"]  < league_mean

    def test_small_sample_shrinks_more_than_large_sample(self):
        stats = self._stats([
            ("Large", 30.0, 65.0, 35.0, 2000, 2000),
            ("Small", 30.0, 65.0, 35.0, 50,   50),
            ("Other", 10.0, 55.0, 45.0, 500,  500),
        ])
        shrunken, _ = reg._shrink_hca(stats)
        # Same raw HCA; small sample pulled harder toward league mean
        assert shrunken["Small"] < shrunken["Large"]

    def test_zero_true_variance_collapses_all_to_league_mean(self):
        stats = self._stats([
            ("A", 20.0, 60.0, 40.0, 100, 100),
            ("B", 20.0, 60.0, 40.0, 100, 100),
            ("C", 20.0, 60.0, 40.0, 100, 100),
        ])
        shrunken, _ = reg._shrink_hca(stats)
        for v in shrunken.values():
            assert v == pytest.approx(20.0, abs=1e-6)

    def test_ci_halfwidth_always_positive(self):
        stats = self._stats([
            ("A", 25.0, 62.0, 37.0, 300, 300),
            ("B", 15.0, 57.0, 43.0, 200, 200),
        ])
        _, ci_hw = reg._shrink_hca(stats)
        for v in ci_hw.values():
            assert v > 0.0

    def test_larger_sample_has_narrower_ci(self):
        stats = self._stats([
            ("Large", 20.0, 60.0, 40.0, 1000, 1000),
            ("Small", 20.0, 60.0, 40.0, 50,   50),
        ])
        _, ci_hw = reg._shrink_hca(stats)
        assert ci_hw["Large"] < ci_hw["Small"]

    def test_single_team_shrunken_equals_its_hca(self):
        stats = self._stats([("Only", 22.0, 61.0, 39.0, 200, 200)])
        shrunken, _ = reg._shrink_hca(stats)
        # true_var = 0 when there's one team; shrinks to league mean = its own hca
        assert shrunken["Only"] == pytest.approx(22.0, abs=1e-6)


# ── Quality diff ──────────────────────────────────────────────────────────────

class TestAddQualityDiff:
    def _make_df(self):
        # Alpha home wins 2/2, loses 0/2 away → winpct = 3/4 = 0.75? No:
        # Alpha home: rows 0,1 → wins=2, games=2
        # Alpha away: rows 2,3 → home_win col: 0 means Beta (home) lost so Alpha won → wins=1
        #                        home_win col: 1 means Beta won → Alpha lost → wins=1, losses=1
        # So Alpha total: 2+1=3 wins, 4 games → 0.75
        # Beta home: rows 2,3 → wins: home_win=0 → 0, home_win=1 → 1, total=1/2 home games
        # Beta away: rows 0,1 → home_win=1 both → Beta lost both → 0 away wins
        # Beta total: 1 win, 4 games → 0.25
        rs = pd.DataFrame([
            {"year": 2020, "is_playoff": 0, "home_win": 1, "TEAM_NAME_home": "Alpha", "TEAM_NAME_away": "Beta"},
            {"year": 2020, "is_playoff": 0, "home_win": 1, "TEAM_NAME_home": "Alpha", "TEAM_NAME_away": "Beta"},
            {"year": 2020, "is_playoff": 0, "home_win": 0, "TEAM_NAME_home": "Beta",  "TEAM_NAME_away": "Alpha"},
            {"year": 2020, "is_playoff": 0, "home_win": 1, "TEAM_NAME_home": "Beta",  "TEAM_NAME_away": "Alpha"},
        ])
        po = pd.DataFrame([
            {"year": 2020, "is_playoff": 1, "home_win": 1, "TEAM_NAME_home": "Alpha", "TEAM_NAME_away": "Beta"},
        ])
        return pd.concat([rs, po], ignore_index=True)

    def test_quality_diff_column_exists_after_call(self):
        df = reg._add_quality_diff(self._make_df())
        assert "quality_diff" in df.columns

    def test_playoff_rows_have_non_null_quality_diff(self):
        df = reg._add_quality_diff(self._make_df())
        po = df[df["is_playoff"] == 1]
        assert po["quality_diff"].notna().all()

    def test_regular_season_rows_have_null_quality_diff(self):
        df = reg._add_quality_diff(self._make_df())
        rs = df[df["is_playoff"] == 0]
        assert rs["quality_diff"].isna().all()

    def test_quality_diff_positive_when_home_team_stronger(self):
        # Alpha RS winpct (0.75) > Beta RS winpct (0.25), Alpha is home in playoff row
        df = reg._add_quality_diff(self._make_df())
        po = df[df["is_playoff"] == 1]
        assert float(po["quality_diff"].iloc[0]) > 0.0

    def test_quality_diff_magnitude_correct(self):
        df = reg._add_quality_diff(self._make_df())
        po = df[df["is_playoff"] == 1]
        assert float(po["quality_diff"].iloc[0]) == pytest.approx(0.75 - 0.25, abs=1e-6)

    def test_does_not_mutate_input(self):
        df_orig = self._make_df()
        assert "quality_diff" not in df_orig.columns
        reg._add_quality_diff(df_orig)
        assert "quality_diff" not in df_orig.columns


# ── Shapley decomposition ─────────────────────────────────────────────────────

class TestComputeShapleyShares:
    def _make_reg_df(self, n=400, seed=42):
        rng = np.random.default_rng(seed)
        era_ref = nba.ERA_DEFS[0][0]
        eras = [e[0] for e in nba.ERA_DEFS]
        return pd.DataFrame({
            "home_win":      rng.integers(0, 2, n),
            "rest_diff":     rng.uniform(-3, 3, n),
            "altitude_home": rng.integers(0, 2, n),
            "tz_diff":       rng.integers(0, 4, n).astype(float),
            "covid":         rng.integers(0, 2, n),
            "era":           rng.choice(eras, n),
        }), era_ref

    def test_shares_sum_to_100(self):
        df, era_ref = self._make_reg_df()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            shares = reg._compute_shapley_shares(df, era_ref)
        assert sum(shares.values()) == pytest.approx(100.0, abs=0.5)

    def test_returns_all_five_block_keys(self):
        df, era_ref = self._make_reg_df()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            shares = reg._compute_shapley_shares(df, era_ref)
        assert set(shares.keys()) == {"era", "rest", "altitude", "tz", "covid"}

    def test_all_shares_finite(self):
        df, era_ref = self._make_reg_df()
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            shares = reg._compute_shapley_shares(df, era_ref)
        for k, v in shares.items():
            assert np.isfinite(v), f"Share for '{k}' is not finite: {v}"

    def test_dominant_predictor_gets_highest_share(self):
        # Use logistic probability from rest_diff so there's no perfect separation
        rng = np.random.default_rng(0)
        n = 600
        era_ref = nba.ERA_DEFS[0][0]
        eras = [e[0] for e in nba.ERA_DEFS]
        rest = rng.uniform(-3, 3, n)
        prob = 1.0 / (1.0 + np.exp(-2.0 * rest))
        df = pd.DataFrame({
            "home_win":      rng.binomial(1, prob, n),
            "rest_diff":     rest,
            "altitude_home": rng.integers(0, 2, n),
            "tz_diff":       rng.integers(0, 4, n).astype(float),
            "covid":         rng.integers(0, 2, n),
            "era":           rng.choice(eras, n),
        })
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            shares = reg._compute_shapley_shares(df, era_ref)
        assert shares["rest"] > shares["altitude"]
        assert shares["rest"] > shares["tz"]
        assert shares["rest"] > shares["covid"]

    def test_empty_model_returns_zero_shares(self):
        # If the model has no variation in outcome, R² ≈ 0 and all shares → 0
        era_ref = nba.ERA_DEFS[0][0]
        df = pd.DataFrame({
            "home_win":      np.ones(100, dtype=int),   # constant — no variation
            "rest_diff":     np.zeros(100),
            "altitude_home": np.zeros(100, dtype=int),
            "tz_diff":       np.zeros(100),
            "covid":         np.zeros(100, dtype=int),
            "era":           [era_ref] * 100,
        })
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            shares = reg._compute_shapley_shares(df, era_ref)
        # All shares should be 0 when total R² = 0
        for v in shares.values():
            assert v == pytest.approx(0.0, abs=1e-6)


# ── Smoke tests for run_* functions ──────────────────────────────────────────

class TestRunDeclineTrend:
    def test_does_not_raise(self, capsys):
        df = _make_game_df(n=500)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reg.run_decline_trend(df)

    def test_empty_df_does_not_raise(self, capsys):
        df = pd.DataFrame(columns=["year", "is_playoff", "home_win", "era"])
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reg.run_decline_trend(df)


class TestRunRestBucketAnalysis:
    def test_does_not_raise(self, capsys):
        df = _make_game_df(n=500)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reg.run_rest_bucket_analysis(df)


class TestRunMarginAnalysis:
    def test_does_not_raise(self, capsys):
        df = _make_game_df(n=400)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reg.run_margin_analysis(df)


class TestRunDifferentialAnalysis:
    def test_does_not_raise(self, capsys):
        df = _make_game_df(n=400)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reg.run_differential_analysis(df)


class TestRunQuantileMarginAnalysis:
    def test_does_not_raise(self, capsys):
        # Needs ≥100 rows per context; use a larger synthetic df
        df = _make_game_df(n=600)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reg.run_quantile_margin_analysis(df)


class TestRunTravelAnalysis:
    def test_does_not_raise(self, capsys):
        df = _make_game_df(n=400)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reg.run_travel_analysis(df)

    def test_no_distance_data_does_not_raise(self, capsys):
        df = _make_game_df(n=100)
        df["distance_miles"] = np.nan
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reg.run_travel_analysis(df)


class TestRunFactorSummary:
    def test_does_not_raise(self, capsys):
        df = _make_game_df(n=500, include_quality_diff=True)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reg.run_factor_summary(df)


class TestRunSeriesBreakdown:
    def test_does_not_raise(self, capsys):
        df = _make_game_df(n=400)
        # Make sure playoff rows have game_in_series as integers 1-7
        df.loc[df["is_playoff"] == 1, "game_in_series"] = np.random.default_rng(0).integers(1, 8, (df["is_playoff"] == 1).sum()).astype(float)
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            reg.run_series_breakdown(df)
