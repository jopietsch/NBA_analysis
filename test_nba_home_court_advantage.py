import os

import numpy as np
import pandas as pd
import pytest

import nba_home_court_advantage as nba

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "tests", "data")


class TestSeasonFormatting:
    def test_season_str(self):
        assert nba.season_str(2024) == "2023-24"

    def test_season_str_century_rollover(self):
        assert nba.season_str(2000) == "1999-00"

    def test_short_label(self):
        assert nba.short_label(2024) == "23–24"

    def test_short_label_century_rollover(self):
        assert nba.short_label(2000) == "99–00"


class TestLabelToYear:
    @pytest.mark.parametrize("label, expected", [
        ("23–24", 2024),
        ("1984–94", 1994),
        ("99–00", 2000),   # short_label century rollover
        ("2023–25", 2025),
        ("48–49", 2049),   # suffix < 50 -> 2000s
        ("49–50", 1950),   # suffix == 50 -> 1900s
    ])
    def test_label_to_year(self, label, expected):
        assert nba.label_to_year(label) == expected


class TestCachePath:
    def test_regular_season(self):
        assert nba.cache_path(2024, "Regular Season") == \
            os.path.join(nba.CACHE_DIR, "2023-24_Regular_Season.csv")

    def test_playoffs(self):
        assert nba.cache_path(2024, "Playoffs") == \
            os.path.join(nba.CACHE_DIR, "2023-24_Playoffs.csv")


class TestEraDefsConsistency:
    """ERA_DEFS drives both the chart shading and the era averages, so its
    ranges must be contiguous and line up with the labels/season range."""

    def test_eras_cover_full_season_range_with_no_gaps(self):
        assert nba.ERA_DEFS[0][1] == nba.START_YEAR
        assert nba.ERA_DEFS[-1][2] == nba.END_YEAR
        for (_, _, prev_y2, _), (_, next_y1, _, _) in zip(nba.ERA_DEFS, nba.ERA_DEFS[1:]):
            assert next_y1 == prev_y2 + 1

    def test_era_labels_parse_to_their_end_year(self):
        for label, _, y2, _ in nba.ERA_DEFS:
            assert nba.label_to_year(label) == y2


class TestCovidSeasons:
    def test_covid_season_labels_match_short_label_format(self):
        # Regression test: short_label() uses an en-dash ("–"), so
        # COVID_SEASONS must too or the chart highlighting silently no-ops.
        assert nba.short_label(2020) in nba.COVID_SEASONS
        assert nba.short_label(2021) in nba.COVID_SEASONS


class TestComputeEraAverages:
    def test_buckets_seasons_into_eras_and_averages(self):
        reg_seasons = ["83–84", "93–94", "94–95", "01–02"]
        reg_pcts    = [60.0,    62.0,    64.0,    58.0]
        po_seasons  = ["83–84", "01–02"]
        po_pcts     = [70.0,    66.0]

        era_reg_avg, era_po_avg, era_labels = nba.compute_era_averages(
            reg_seasons, reg_pcts, po_seasons, po_pcts
        )

        # 83–84 -> 1984 and 93–94 -> 1994 both fall in the 1984–94 era
        i = era_labels.index("1984–94")
        assert era_reg_avg[i] == 61.0
        assert era_po_avg[i] == 70.0

        # 94–95 -> 1995 falls in the 1995–01 era (boundary case, no playoff data)
        i = era_labels.index("1995–01")
        assert era_reg_avg[i] == 64.0
        assert era_po_avg[i] == 0

        # 01–02 -> 2002 falls in the 2002–04 era
        i = era_labels.index("2002–04")
        assert era_reg_avg[i] == 58.0
        assert era_po_avg[i] == 66.0

    def test_era_with_no_data_averages_to_zero(self):
        era_reg_avg, era_po_avg, era_labels = nba.compute_era_averages([], [], [], [])
        assert era_reg_avg == [0] * len(nba.ERA_DEFS)
        assert era_po_avg == [0] * len(nba.ERA_DEFS)


class TestComputePlayoffFormatAverages:
    def test_buckets_seasons_into_format_periods_and_averages(self):
        reg_seasons = ["83–84", "84–85", "01–02", "02–03", "13–14"]
        reg_pcts    = [65.0,    61.0,    63.0,    62.0,    57.0]
        po_seasons  = ["83–84", "84–85", "01–02", "02–03", "13–14"]
        po_pcts     = [70.0,    60.0,    66.0,    64.0,    58.0]

        format_reg_avg, format_po_avg, format_labels = nba.compute_playoff_format_averages(
            reg_seasons, reg_pcts, po_seasons, po_pcts
        )

        # 83–84 -> 1984 is its own period
        i = format_labels.index("1984")
        assert format_reg_avg[i] == 65.0
        assert format_po_avg[i] == 70.0

        # 84–85 -> 1985 and 01–02 -> 2002 both fall in 1985–02
        i = format_labels.index("1985–02")
        assert format_reg_avg[i] == 62.0
        assert format_po_avg[i] == 63.0

        # 02–03 -> 2003 falls in 2003–13
        i = format_labels.index("2003–13")
        assert format_reg_avg[i] == 62.0
        assert format_po_avg[i] == 64.0

        # 13–14 -> 2014 falls in 2014–25
        i = format_labels.index("2014–25")
        assert format_reg_avg[i] == 57.0
        assert format_po_avg[i] == 58.0

    def test_period_with_no_data_averages_to_zero(self):
        format_reg_avg, format_po_avg, format_labels = nba.compute_playoff_format_averages([], [], [], [])
        assert format_reg_avg == [0] * len(nba.PLAYOFF_FORMAT_PERIODS)
        assert format_po_avg == [0] * len(nba.PLAYOFF_FORMAT_PERIODS)


class TestFetchSeasonHomePct:
    def test_computes_home_win_pct_from_cache(self, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", TEST_DATA_DIR)

        # Real 1983-84 regular season game log: 640 home wins / 943 home games
        assert nba.fetch_season_home_pct(1984, "Regular Season") == 67.9

    def test_computes_home_win_pct_from_cache_for_playoffs(self, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", TEST_DATA_DIR)

        # Real 2020-21 playoffs game log: 48 home wins / 85 home games
        assert nba.fetch_season_home_pct(2021, "Playoffs") == 56.5

    def test_returns_none_for_empty_dataframe(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        pd.DataFrame(columns=["MATCHUP", "WL"]).to_csv(
            nba.cache_path(2024, "Regular Season"), index=False
        )
        assert nba.fetch_season_home_pct(2024, "Regular Season") is None

    def test_returns_none_when_no_home_games(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        df = pd.DataFrame({
            "MATCHUP": ["BOS @ MIA", "MIA @ BOS"],
            "WL":      ["W",         "L"],
        })
        df.to_csv(nba.cache_path(2024, "Regular Season"), index=False)
        assert nba.fetch_season_home_pct(2024, "Regular Season") is None

    def test_fetches_from_api_and_caches_when_no_cache_exists(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        monkeypatch.setattr(nba.time, "sleep", lambda *_: None)

        api_df = pd.DataFrame({
            "MATCHUP": ["BOS vs. MIA", "BOS @ MIA"],
            "WL":      ["W",           "L"],
        })

        class FakeFinder:
            def __init__(self, **kwargs):
                pass

            def get_data_frames(self):
                return [api_df]

        monkeypatch.setattr(nba.leaguegamefinder, "LeagueGameFinder", FakeFinder)

        # 1 home game, 1 win -> 100.0%
        assert nba.fetch_season_home_pct(2024, "Regular Season") == 100.0
        assert os.path.exists(nba.cache_path(2024, "Regular Season"))

    def test_returns_none_on_api_error_and_does_not_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))

        class FailingFinder:
            def __init__(self, **kwargs):
                raise RuntimeError("boom")

        monkeypatch.setattr(nba.leaguegamefinder, "LeagueGameFinder", FailingFinder)

        assert nba.fetch_season_home_pct(2024, "Regular Season") is None
        assert not os.path.exists(nba.cache_path(2024, "Regular Season"))


class TestFetchRestData:
    def test_returns_none_when_cache_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        assert nba.fetch_rest_data(2024, "Regular Season") is None

    def test_returns_none_for_empty_dataframe(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        pd.DataFrame(columns=["TEAM_ID", "GAME_ID", "GAME_DATE", "MATCHUP", "WL"]).to_csv(
            nba.cache_path(2024, "Regular Season"), index=False
        )
        assert nba.fetch_rest_data(2024, "Regular Season") is None

    def test_computes_rest_days_and_drops_unknown_first_games(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))

        # G1 (Jan 1): A (home) vs C  -- both teams' first game, dropped
        # G2 (Jan 2): B (home) vs D  -- both teams' first game, dropped
        # G3 (Jan 3): A (home) vs B  -- A rested 1 day, B rested 0 days (back-to-back)
        df = pd.DataFrame({
            "TEAM_ID":   [1,   3,   2,   4,   1,   2],
            "GAME_ID":   ["G1", "G1", "G2", "G2", "G3", "G3"],
            "GAME_DATE": ["2024-01-01", "2024-01-01", "2024-01-02", "2024-01-02",
                          "2024-01-03", "2024-01-03"],
            "MATCHUP":   ["A vs. C", "C @ A", "B vs. D", "D @ B", "A vs. B", "B @ A"],
            "WL":        ["W", "L", "W", "L", "L", "W"],
        })
        df.to_csv(nba.cache_path(2024, "Regular Season"), index=False)

        result = nba.fetch_rest_data(2024, "Regular Season")

        assert len(result) == 1
        row = result.iloc[0]
        assert row["REST_home"] == 1
        assert row["REST_away"] == 0
        assert row["REST_DIFF"] == 1
        assert row["HOME_WIN"] == 0  # A (home) lost G3


class TestFetchRestDataFromRealCache:
    def test_returns_expected_columns_for_real_season(self, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", TEST_DATA_DIR)

        result = nba.fetch_rest_data(1985, "Regular Season")

        assert result is not None
        assert list(result.columns) == ["REST_home", "REST_away", "REST_DIFF", "HOME_WIN"]
        assert len(result) > 0
        assert result["HOME_WIN"].isin([0, 1]).all()


class TestComputeRestStats:
    def test_aggregates_b2b_rates_and_win_pct_by_rest(self, monkeypatch):
        def fake_fetch(year, season_type):
            if year != 2024:
                return None
            return pd.DataFrame({
                "REST_home":  [0, 1, 2, 0],
                "REST_away":  [1, 1, 0, 0],
                "REST_DIFF":  [-1, 0, 2, 0],
                "HOME_WIN":   [0, 1, 1, 1],
            })

        monkeypatch.setattr(nba, "fetch_rest_data", fake_fetch)
        seasons, stats = nba.compute_rest_stats(2023, 2025, "Regular Season")

        assert seasons == ["23–24"]
        assert stats["b2b_home_pct"] == [50.0]  # 2 of 4 rows have REST_home == 0
        assert stats["b2b_away_pct"] == [50.0]  # 2 of 4 rows have REST_away == 0

        assert stats["win_home_more_rest"] == [100.0]  # REST_DIFF > 0: row 3 (HOME_WIN=1)
        assert stats["win_equal_rest"]     == [100.0]  # REST_DIFF == 0: rows 2,4 (HOME_WIN=1,1)
        assert stats["win_away_more_rest"] == [0.0]    # REST_DIFF < 0: row 1 (HOME_WIN=0)

    def test_skips_years_with_no_data(self, monkeypatch):
        monkeypatch.setattr(nba, "fetch_rest_data", lambda year, season_type: None)

        seasons, stats = nba.compute_rest_stats(2023, 2025, "Regular Season")

        assert seasons == []
        for values in stats.values():
            assert values == []

    def test_skip_years_param_excludes_years(self, monkeypatch):
        calls = []

        def fake_fetch(year, season_type):
            calls.append(year)
            return None

        monkeypatch.setattr(nba, "fetch_rest_data", fake_fetch)
        nba.compute_rest_stats(2019, 2021, "Playoffs", skip_years={2020})

        assert calls == [2019, 2021]


class TestFetchAltitudeData:
    def test_returns_none_when_cache_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        assert nba.fetch_altitude_data(2024, "Regular Season") is None

    def test_returns_none_for_empty_dataframe(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        pd.DataFrame(columns=["TEAM_NAME", "MATCHUP", "WL"]).to_csv(
            nba.cache_path(2024, "Regular Season"), index=False
        )
        assert nba.fetch_altitude_data(2024, "Regular Season") is None

    def test_returns_none_when_no_home_games(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        df = pd.DataFrame({
            "TEAM_NAME": ["Denver Nuggets"],
            "MATCHUP":   ["DEN @ BOS"],
            "WL":        ["W"],
        })
        df.to_csv(nba.cache_path(2024, "Regular Season"), index=False)
        assert nba.fetch_altitude_data(2024, "Regular Season") is None

    def test_tags_altitude_teams_and_computes_home_win(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        df = pd.DataFrame({
            "TEAM_NAME": ["Denver Nuggets", "Denver Nuggets", "Utah Jazz",   "Boston Celtics", "Boston Celtics"],
            "MATCHUP":   ["DEN vs. BOS",    "DEN vs. LAL",    "UTA vs. PHX", "BOS vs. DEN",    "BOS @ LAL"],
            "WL":        ["W",              "L",              "L",          "W",              "L"],
        })
        df.to_csv(nba.cache_path(2024, "Regular Season"), index=False)

        result = nba.fetch_altitude_data(2024, "Regular Season")

        # The away row (BOS @ LAL) is dropped, leaving 4 home games
        assert len(result) == 4

        den_rows = result[result["TEAM_NAME"] == "Denver Nuggets"]
        assert den_rows["ALTITUDE"].all()
        assert sorted(den_rows["HOME_WIN"].tolist()) == [0, 1]  # one home win, one home loss

        uta_rows = result[result["TEAM_NAME"] == "Utah Jazz"]
        assert uta_rows["ALTITUDE"].all()
        assert uta_rows["HOME_WIN"].iloc[0] == 0  # home team (Jazz) lost

        bos_rows = result[result["TEAM_NAME"] == "Boston Celtics"]
        assert not bos_rows["ALTITUDE"].any()
        assert bos_rows["HOME_WIN"].iloc[0] == 1  # home team (Celtics) won


class TestFetchAltitudeDataFromRealCache:
    def test_returns_expected_columns_for_real_season(self, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", TEST_DATA_DIR)

        result = nba.fetch_altitude_data(1985, "Regular Season")

        assert result is not None
        assert list(result.columns) == ["TEAM_NAME", "HOME_WIN", "ALTITUDE"]
        assert len(result) > 0
        assert result["HOME_WIN"].isin([0, 1]).all()
        # Utah Jazz (TEAM_NAME stayed constant despite the UTH -> UTA
        # abbreviation change) should be tagged as an altitude team
        assert result.loc[result["TEAM_NAME"] == "Utah Jazz", "ALTITUDE"].all()


class TestComputeAltitudeStats:
    def test_aggregates_home_win_pct_per_team_and_other(self, monkeypatch):
        def fake_fetch(year, season_type):
            if year != 2024:
                return None
            return pd.DataFrame({
                "TEAM_NAME": ["Denver Nuggets", "Denver Nuggets", "Utah Jazz", "Boston Celtics", "Boston Celtics"],
                "HOME_WIN":  [1, 0, 1, 1, 0],
                "ALTITUDE":  [True, True, True, False, False],
            })

        monkeypatch.setattr(nba, "fetch_altitude_data", fake_fetch)
        seasons, stats = nba.compute_altitude_stats(2023, 2025, "Regular Season")

        assert seasons == ["23–24"]
        assert stats["Denver Nuggets"] == [50.0]
        assert stats["Utah Jazz"] == [100.0]
        assert stats["other"] == [50.0]

    def test_skips_years_with_no_data(self, monkeypatch):
        monkeypatch.setattr(nba, "fetch_altitude_data", lambda year, season_type: None)

        seasons, stats = nba.compute_altitude_stats(2023, 2025, "Regular Season")

        assert seasons == []
        for values in stats.values():
            assert values == []

    def test_skip_years_param_excludes_years(self, monkeypatch):
        calls = []

        def fake_fetch(year, season_type):
            calls.append(year)
            return None

        monkeypatch.setattr(nba, "fetch_altitude_data", fake_fetch)
        nba.compute_altitude_stats(2019, 2021, "Playoffs", skip_years={2020})

        assert calls == [2019, 2021]


class TestBucketStatsByEra:
    def test_buckets_seasons_into_eras_and_averages(self):
        # 83–84 -> 1984 and 93–94 -> 1994 both fall in the 1984–94 era
        seasons = ["83–84", "93–94"]
        stats = {
            "Denver Nuggets": [30.0, 50.0],
            "Utah Jazz":       [20.0, 40.0],
            "other":           [40.0, 40.0],
        }

        era_avgs, era_labels = nba.bucket_stats_by_era(seasons, stats)

        i = era_labels.index("1984–94")
        assert era_avgs["Denver Nuggets"][i] == 40.0
        assert era_avgs["Utah Jazz"][i] == 30.0
        assert era_avgs["other"][i] == 40.0

        # Eras with no matching seasons average to 0
        j = era_labels.index("2023–25")
        assert era_avgs["Denver Nuggets"][j] == 0
        assert era_avgs["Utah Jazz"][j] == 0
        assert era_avgs["other"][j] == 0

    def test_handles_nan_values_in_a_series(self):
        seasons = ["83–84", "93–94"]
        stats = {"x": [30.0, np.nan]}

        era_avgs, era_labels = nba.bucket_stats_by_era(seasons, stats)

        i = era_labels.index("1984–94")
        assert era_avgs["x"][i] == 30.0  # NaN excluded from the average


class TestFetchTimezoneData:
    def test_returns_none_when_cache_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        assert nba.fetch_timezone_data(2024, "Regular Season") is None

    def test_returns_none_for_empty_dataframe(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        pd.DataFrame(columns=["GAME_ID", "TEAM_NAME", "MATCHUP", "WL"]).to_csv(
            nba.cache_path(2024, "Regular Season"), index=False
        )
        assert nba.fetch_timezone_data(2024, "Regular Season") is None

    def test_computes_zones_crossed_and_drops_unknown_teams(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))

        # G1: Boston (Eastern, 0) hosts LA Lakers (Pacific, 3) -> 3 zones, home wins
        # G2: Boston (Eastern, 0) hosts Denver (Mountain, 2) -> 2 zones, away wins
        # G3: a team not in TEAM_TIMEZONES -> dropped entirely
        df = pd.DataFrame({
            "GAME_ID":   ["G1", "G1", "G2", "G2", "G3", "G3"],
            "TEAM_NAME": ["Boston Celtics", "Los Angeles Lakers",
                          "Boston Celtics", "Denver Nuggets",
                          "Boston Celtics", "Globetrotters"],
            "MATCHUP":   ["BOS vs. LAL", "LAL @ BOS",
                          "BOS vs. DEN", "DEN @ BOS",
                          "BOS vs. GLB", "GLB @ BOS"],
            "WL":        ["W", "L", "L", "W", "W", "L"],
        })
        df.to_csv(nba.cache_path(2024, "Regular Season"), index=False)

        result = nba.fetch_timezone_data(2024, "Regular Season")

        assert len(result) == 2
        result = result.sort_values("TZ_DIFF").reset_index(drop=True)
        assert result.loc[0, "TZ_DIFF"] == 2
        assert result.loc[0, "HOME_WIN"] == 0  # Boston lost to Denver
        assert result.loc[1, "TZ_DIFF"] == 3
        assert result.loc[1, "HOME_WIN"] == 1  # Boston beat the Lakers


class TestFetchTimezoneDataFromRealCache:
    def test_returns_expected_columns_for_real_season(self, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", TEST_DATA_DIR)

        result = nba.fetch_timezone_data(1985, "Regular Season")

        assert result is not None
        assert list(result.columns) == ["TZ_DIFF", "HOME_WIN"]
        assert len(result) > 0
        assert result["HOME_WIN"].isin([0, 1]).all()
        assert result["TZ_DIFF"].between(0, 3).all()


class TestComputeTimezoneStats:
    def test_aggregates_home_win_pct_by_zones_crossed(self, monkeypatch):
        def fake_fetch(year, season_type):
            if year != 2024:
                return None
            return pd.DataFrame({
                "TZ_DIFF":  [0, 0, 1, 2, 3, 3],
                "HOME_WIN": [0, 1, 0, 1, 0, 0],
            })

        monkeypatch.setattr(nba, "fetch_timezone_data", fake_fetch)
        seasons, stats = nba.compute_timezone_stats(2023, 2025, "Regular Season")

        assert seasons == ["23–24"]
        assert stats["0"] == [50.0]
        assert stats["1"] == [0.0]
        assert stats["2"] == [100.0]
        assert stats["3"] == [0.0]

    def test_skips_years_with_no_data(self, monkeypatch):
        monkeypatch.setattr(nba, "fetch_timezone_data", lambda year, season_type: None)

        seasons, stats = nba.compute_timezone_stats(2023, 2025, "Regular Season")

        assert seasons == []
        for values in stats.values():
            assert values == []

    def test_skip_years_param_excludes_years(self, monkeypatch):
        calls = []

        def fake_fetch(year, season_type):
            calls.append(year)
            return None

        monkeypatch.setattr(nba, "fetch_timezone_data", fake_fetch)
        nba.compute_timezone_stats(2019, 2021, "Playoffs", skip_years={2020})

        assert calls == [2019, 2021]


class TestFetchAllSeasons:
    def test_skips_playoffs_only_for_skip_years(self, monkeypatch):
        monkeypatch.setattr(nba, "START_YEAR", 2019)
        monkeypatch.setattr(nba, "END_YEAR", 2021)
        monkeypatch.setattr(nba, "SKIP_PLAYOFF_YEARS", {2020})
        monkeypatch.setattr(nba, "fetch_season_home_pct", lambda year, season_type: float(year))

        reg_seasons, reg_pcts, po_seasons, po_pcts = nba.fetch_all_seasons()

        assert reg_seasons == ["18–19", "19–20", "20–21"]
        assert reg_pcts == [2019.0, 2020.0, 2021.0]
        assert po_seasons == ["18–19", "20–21"]  # 2020 (bubble) excluded
        assert po_pcts == [2019.0, 2021.0]

    def test_no_data_seasons_are_skipped(self, monkeypatch):
        monkeypatch.setattr(nba, "START_YEAR", 2019)
        monkeypatch.setattr(nba, "END_YEAR", 2020)
        monkeypatch.setattr(nba, "SKIP_PLAYOFF_YEARS", set())
        monkeypatch.setattr(nba, "fetch_season_home_pct", lambda year, season_type: None)

        reg_seasons, reg_pcts, po_seasons, po_pcts = nba.fetch_all_seasons()

        assert reg_seasons == reg_pcts == po_seasons == po_pcts == []
