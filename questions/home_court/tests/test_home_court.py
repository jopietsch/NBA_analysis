import os

import numpy as np
import pandas as pd
import pytest

import home_court_data as nba

TEST_DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


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

        # 13–14 -> 2014 falls in 2014–26
        i = format_labels.index("2014–26")
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
        j = era_labels.index("2023–26")
        assert era_avgs["Denver Nuggets"][j] == 0
        assert era_avgs["Utah Jazz"][j] == 0
        assert era_avgs["other"][j] == 0

    def test_handles_nan_values_in_a_series(self):
        seasons = ["83–84", "93–94"]
        stats = {"x": [30.0, np.nan]}

        era_avgs, era_labels = nba.bucket_stats_by_era(seasons, stats)

        i = era_labels.index("1984–94")
        assert era_avgs["x"][i] == 30.0  # NaN excluded from the average


class TestMergeHomeAwayRows:
    def test_returns_none_when_no_matching_game_ids(self):
        # Home row for G1, away row for G2 — merge produces an empty DataFrame
        df = pd.DataFrame({
            "GAME_ID": ["G1",         "G2"],
            "MATCHUP": ["BOS vs. MIA", "LAL @ PHX"],
            "WL":      ["W",           "L"],
        })
        assert nba._merge_home_away_rows(df) is None

    def test_returns_none_when_no_home_rows(self):
        df = pd.DataFrame({
            "GAME_ID": ["G1"], "MATCHUP": ["BOS @ MIA"], "WL": ["W"],
        })
        assert nba._merge_home_away_rows(df) is None

    def test_returns_none_when_no_away_rows(self):
        df = pd.DataFrame({
            "GAME_ID": ["G1"], "MATCHUP": ["BOS vs. MIA"], "WL": ["W"],
        })
        assert nba._merge_home_away_rows(df) is None

    def test_returns_none_for_empty_dataframe(self):
        df = pd.DataFrame(columns=["GAME_ID", "MATCHUP", "WL"])
        assert nba._merge_home_away_rows(df) is None

    def test_merges_home_and_away_on_game_id(self):
        df = pd.DataFrame({
            "GAME_ID": ["G1", "G1"],
            "MATCHUP": ["BOS vs. MIA", "MIA @ BOS"],
            "WL":      ["W",           "L"],
        })
        result = nba._merge_home_away_rows(df)
        assert result is not None
        assert len(result) == 1
        assert result.iloc[0]["WL_home"] == "W"
        assert result.iloc[0]["WL_away"] == "L"


class TestAddRestDays:
    def test_handles_empty_dataframe(self):
        df = pd.DataFrame(columns=["TEAM_ID", "GAME_DATE"])
        result = nba._add_rest_days(df)
        assert result.empty
        assert "REST" in result.columns

    def test_first_game_has_nan_rest(self):
        df = pd.DataFrame({
            "TEAM_ID":   [1],
            "GAME_DATE": ["2024-01-01"],
        })
        result = nba._add_rest_days(df)
        assert pd.isna(result.iloc[0]["REST"])

    def test_back_to_back_is_zero_rest(self):
        df = pd.DataFrame({
            "TEAM_ID":   [1, 1],
            "GAME_DATE": ["2024-01-01", "2024-01-02"],
        })
        result = nba._add_rest_days(df).sort_values("GAME_DATE").reset_index(drop=True)
        assert result.iloc[1]["REST"] == 0

    def test_one_day_gap_is_one_rest(self):
        df = pd.DataFrame({
            "TEAM_ID":   [1, 1],
            "GAME_DATE": ["2024-01-01", "2024-01-03"],
        })
        result = nba._add_rest_days(df).sort_values("GAME_DATE").reset_index(drop=True)
        assert result.iloc[1]["REST"] == 1

    def test_rest_computed_per_team(self):
        df = pd.DataFrame({
            "TEAM_ID":   [1, 2, 1],
            "GAME_DATE": ["2024-01-01", "2024-01-01", "2024-01-02"],
        })
        result = nba._add_rest_days(df).sort_values(["TEAM_ID", "GAME_DATE"]).reset_index(drop=True)
        # Team 1, second game: 1 day later = 0 rest (back-to-back)
        team1 = result[result["TEAM_ID"] == 1].reset_index(drop=True)
        assert team1.iloc[1]["REST"] == 0
        # Team 2 has only one game: NaN
        team2 = result[result["TEAM_ID"] == 2].reset_index(drop=True)
        assert pd.isna(team2.iloc[0]["REST"])


class TestFetchDifferentialData:
    def _write_game_log(self, tmp_path, df):
        df.to_csv(nba.cache_path(2024, "Regular Season"), index=False)

    def test_returns_none_when_cache_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        assert nba.fetch_differential_data(2024, "Regular Season") is None

    def test_returns_none_for_empty_dataframe(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        pd.DataFrame(columns=["GAME_ID", "MATCHUP", "WL"]).to_csv(
            nba.cache_path(2024, "Regular Season"), index=False
        )
        assert nba.fetch_differential_data(2024, "Regular Season") is None

    def test_returns_none_when_only_away_rows(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        df = pd.DataFrame({
            "GAME_ID": ["G1"], "MATCHUP": ["BOS @ MIA"],
            "PF": [20], "FGM": [35], "FGA": [80],
            "FG3M": [8], "FG3A": [20], "FTM": [10], "FTA": [15],
        })
        self._write_game_log(tmp_path, df)
        assert nba.fetch_differential_data(2024, "Regular Season") is None

    def test_computes_correct_differentials(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        # Home: FGM=40, FGA=80, FG3M=10, FG3A=20, FTM=15, FTA=20, PF=20
        # Away: FGM=35, FGA=80, FG3M=8,  FG3A=20, FTM=10, FTA=15, PF=22
        df = pd.DataFrame({
            "GAME_ID": ["G1",        "G1"],
            "MATCHUP": ["BOS vs. MIA", "MIA @ BOS"],
            "PF":      [20,           22],
            "FGM":     [40,           35],
            "FGA":     [80,           80],
            "FG3M":    [10,            8],
            "FG3A":    [20,           20],
            "FTM":     [15,           10],
            "FTA":     [20,           15],
            "WL":      ["W",         "L"],
        })
        self._write_game_log(tmp_path, df)

        result = nba.fetch_differential_data(2024, "Regular Season")
        assert result is not None
        assert len(result) == 1
        row = result.iloc[0]
        assert row["foul_diff"] == pytest.approx(-2.0)
        assert row["fg_pct_diff"] == pytest.approx(100 * (40/80 - 35/80))
        assert row["efg_pct_diff"] == pytest.approx(100 * (45/80 - 39/80))
        assert row["tpa_rate_diff"] == pytest.approx(0.0)
        assert row["fg3_pct_diff"] == pytest.approx(100 * (10/20 - 8/20))
        assert row["ft_pct_diff"] == pytest.approx(100 * (15/20 - 10/15))

    def test_zero_fg3a_becomes_nan_not_zero(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        df = pd.DataFrame({
            "GAME_ID": ["G1",           "G1"],
            "MATCHUP": ["BOS vs. MIA",  "MIA @ BOS"],
            "PF":      [20,             22],
            "FGM":     [40,             35],
            "FGA":     [80,             80],
            "FG3M":    [0,               0],
            "FG3A":    [0,               0],   # no 3s attempted by either team
            "FTM":     [15,             10],
            "FTA":     [20,             15],
            "WL":      ["W",            "L"],
        })
        self._write_game_log(tmp_path, df)

        result = nba.fetch_differential_data(2024, "Regular Season")
        assert result is not None
        assert pd.isna(result.iloc[0]["fg3_pct_diff"])


class TestComputeDifferentialStats:
    def test_aggregates_means_per_season(self, monkeypatch):
        def fake_fetch(year, season_type):
            if year != 2024:
                return None
            return pd.DataFrame({
                "foul_diff":    [-1.0, -2.0],
                "fta_diff":     [1.5,   2.5],
                "fg_pct_diff":  [1.0,   3.0],
                "efg_pct_diff": [1.5,   2.5],
                "tpa_rate_diff":[0.1,   0.3],
                "fg3_pct_diff": [0.5,   1.5],
                "ft_pct_diff":  [0.2,   0.4],
            })

        monkeypatch.setattr(nba, "fetch_differential_data", fake_fetch)
        seasons, stats = nba.compute_differential_stats(2023, 2025, "Regular Season")

        assert seasons == ["23–24"]
        assert stats["foul_diff"]    == [pytest.approx(-1.5)]
        assert stats["fg_pct_diff"]  == [pytest.approx(2.0)]
        assert stats["efg_pct_diff"] == [pytest.approx(2.0)]

    def test_skips_years_with_no_data(self, monkeypatch):
        monkeypatch.setattr(nba, "fetch_differential_data", lambda year, s: None)
        seasons, stats = nba.compute_differential_stats(2023, 2025, "Regular Season")
        assert seasons == []
        for v in stats.values():
            assert v == []

    def test_skip_years_param_excludes_years(self, monkeypatch):
        calls = []
        monkeypatch.setattr(nba, "fetch_differential_data",
                            lambda year, s: calls.append(year) or None)
        nba.compute_differential_stats(2019, 2021, "Playoffs", skip_years={2020})
        assert calls == [2019, 2021]


class TestFetchReboundData:
    def _write_game_log(self, tmp_path, df):
        df.to_csv(nba.cache_path(2024, "Regular Season"), index=False)

    def test_computes_correct_rebound_components(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        # Home: OREB=12, DREB=30, REB=42 ; Away: OREB=8, DREB=28, REB=36
        df = pd.DataFrame({
            "GAME_ID": ["G1",          "G1"],
            "MATCHUP": ["BOS vs. MIA", "MIA @ BOS"],
            "OREB":    [12,            8],
            "DREB":    [30,            28],
            "REB":     [42,            36],
            "WL":      ["W",           "L"],
        })
        self._write_game_log(tmp_path, df)

        result = nba.fetch_rebound_data(2024, "Regular Season")
        assert result is not None
        assert len(result) == 1
        row = result.iloc[0]
        assert row["oreb_diff"] == pytest.approx(4.0)
        assert row["dreb_diff"] == pytest.approx(2.0)
        assert row["reb_diff"]  == pytest.approx(6.0)
        # home share = 12/(12+28); away share = 8/(8+30); edge in pp
        assert row["reb_share_edge"] == pytest.approx(100 * (12/40 - 8/38))
        assert row["league_oreb_rate"] == pytest.approx(100 * 20 / 78)

    def test_zero_rebounds_becomes_nan_not_zero(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        df = pd.DataFrame({
            "GAME_ID": ["G1",          "G1"],
            "MATCHUP": ["BOS vs. MIA", "MIA @ BOS"],
            "OREB":    [0,             0],
            "DREB":    [0,             0],
            "REB":     [0,             0],
            "WL":      ["W",           "L"],
        })
        self._write_game_log(tmp_path, df)

        result = nba.fetch_rebound_data(2024, "Regular Season")
        assert result is not None
        assert pd.isna(result.iloc[0]["reb_share_edge"])
        assert pd.isna(result.iloc[0]["league_oreb_rate"])


class TestComputeReboundStats:
    def test_aggregates_means_per_season(self, monkeypatch):
        def fake_fetch(year, season_type):
            if year != 2024:
                return None
            return pd.DataFrame({
                "oreb_diff":        [0.4, 0.6],
                "dreb_diff":        [1.0, 2.0],
                "reb_diff":         [1.4, 2.6],
                "reb_share_edge":   [1.0, 3.0],
                "league_oreb_rate": [30.0, 26.0],
                "oreb_rate_home":   [28.0, 32.0],
                "oreb_rate_away":   [24.0, 26.0],
                "tov_diff":         [-0.3, -0.5],
            })

        monkeypatch.setattr(nba, "fetch_rebound_data", fake_fetch)
        seasons, stats = nba.compute_rebound_stats(2023, 2025, "Regular Season")

        assert seasons == ["23–24"]
        assert stats["oreb_diff"]      == [pytest.approx(0.5)]
        assert stats["reb_share_edge"] == [pytest.approx(2.0)]
        assert stats["league_oreb_rate"] == [pytest.approx(28.0)]


class TestComputeTrackingReboundStats:
    def test_home_minus_road_edge_per_team(self, monkeypatch):
        # Two teams; home OREB_CHANCE_PCT exceeds road by 0.02 and 0.04 → mean +0.03,
        # rescaled to pp = +3.0. Box-outs and 2nd-chance handled per source.
        def make(col, home_vals, road_vals):
            def fetch(end_year, location):
                if end_year != 2024:
                    return None
                vals = home_vals if location == "Home" else road_vals
                return pd.DataFrame({"TEAM_ID": [1, 2], col: vals})
            return fetch

        monkeypatch.setattr(nba, "fetch_tracking_rebounding",
                            make("OREB_CHANCE_PCT", [0.50, 0.48], [0.48, 0.44]))
        monkeypatch.setattr(nba, "fetch_hustle_rebounding",
                            make("BOX_OUTS", [10.0, 12.0], [9.0, 10.0]))
        monkeypatch.setattr(nba, "fetch_second_chance",
                            make("PTS_2ND_CHANCE", [13.0, 14.0], [12.0, 12.0]))

        seasons, stats = nba.compute_tracking_rebound_stats(2024, 2024)

        assert seasons == ["23–24"]
        assert stats["oreb_chance_pct_edge"] == [pytest.approx(3.0)]   # (0.02+0.04)/2 ×100
        assert stats["boxout_edge"]          == [pytest.approx(1.5)]   # (1.0+2.0)/2
        assert stats["second_chance_edge"]   == [pytest.approx(1.5)]   # (1.0+2.0)/2

    def test_missing_source_yields_nan(self, monkeypatch):
        monkeypatch.setattr(nba, "fetch_tracking_rebounding", lambda y, loc: None)
        monkeypatch.setattr(nba, "fetch_hustle_rebounding", lambda y, loc: None)
        monkeypatch.setattr(nba, "fetch_second_chance", lambda y, loc: None)

        seasons, stats = nba.compute_tracking_rebound_stats(2024, 2024)
        assert seasons == ["23–24"]
        for key in stats:
            assert pd.isna(stats[key][0])


class TestZonePcts:
    def _df(self):
        return pd.DataFrame({
            "TEAM_ID":    [1,    2],
            "TEAM_NAME":  ["A", "B"],
            "FGA_RA":     [100, 100],
            "FGA_NON_RA": [50,   50],
            "FGA_MR":     [80,   80],
            "FGA_LC3":    [30,   30],
            "FGA_RC3":    [20,   20],
            "FGA_ATB3":   [120, 120],
        })

    def test_sums_across_teams_and_returns_percentages(self):
        result = nba._zone_pcts(self._df())
        total = (100+50+80+30+20+120) * 2  # 800 total shots
        assert result["paint"]    == pytest.approx(100 * (100+50)*2 / total)
        assert result["midrange"] == pytest.approx(100 * 80*2 / total)
        assert result["corner3"]  == pytest.approx(100 * (30+20)*2 / total)
        assert result["above3"]   == pytest.approx(100 * 120*2 / total)
        assert sum(result.values()) == pytest.approx(100.0)

    def test_returns_all_nan_when_total_fga_is_zero(self):
        df = pd.DataFrame({"FGA_RA": [0], "FGA_NON_RA": [0],
                           "FGA_MR": [0], "FGA_LC3": [0],
                           "FGA_RC3": [0], "FGA_ATB3": [0]})
        result = nba._zone_pcts(df)
        assert all(np.isnan(v) for v in result.values())

    def test_ignores_missing_columns(self):
        df = pd.DataFrame({"FGA_RA": [100]})  # all other zone cols absent
        result = nba._zone_pcts(df)
        assert result["paint"] == pytest.approx(100.0)
        assert result["midrange"] == pytest.approx(0.0)


class TestComputeShotZoneStats:
    def _make_zone_df(self):
        return pd.DataFrame({
            "FGA_RA": [400], "FGA_NON_RA": [100],
            "FGA_MR": [200], "FGA_LC3": [50],
            "FGA_RC3": [50], "FGA_ATB3": [200],
        })

    def test_computes_home_minus_road_differential(self, monkeypatch):
        def fake_fetch(year, season_type, location):
            if year != 2024:
                return None
            # Home: more paint shots; Road: fewer paint shots
            if location == "Home":
                return pd.DataFrame({
                    "FGA_RA": [500], "FGA_NON_RA": [100],
                    "FGA_MR": [200], "FGA_LC3": [50],
                    "FGA_RC3": [50], "FGA_ATB3": [100],
                })
            return pd.DataFrame({
                "FGA_RA": [300], "FGA_NON_RA": [100],
                "FGA_MR": [200], "FGA_LC3": [50],
                "FGA_RC3": [50], "FGA_ATB3": [300],
            })

        monkeypatch.setattr(nba, "fetch_shot_zones", fake_fetch)
        seasons, stats = nba.compute_shot_zone_stats(2023, 2025, "Regular Season")

        assert seasons == ["23–24"]
        home_paint = 100 * 600 / 1000
        road_paint = 100 * 400 / 1000
        assert stats["paint"] == [pytest.approx(home_paint - road_paint)]

    def test_skips_year_when_either_side_is_none(self, monkeypatch):
        monkeypatch.setattr(nba, "fetch_shot_zones", lambda year, s, loc: None)
        seasons, stats = nba.compute_shot_zone_stats(2023, 2025, "Regular Season")
        assert seasons == []
        for v in stats.values():
            assert v == []

    def test_skips_year_when_zone_pcts_contain_nan(self, monkeypatch):
        # Both Home and Road return all-zero FGA → _zone_pcts returns NaN
        monkeypatch.setattr(nba, "fetch_shot_zones",
                            lambda year, s, loc: pd.DataFrame({
                                "FGA_RA": [0], "FGA_NON_RA": [0],
                                "FGA_MR": [0], "FGA_LC3": [0],
                                "FGA_RC3": [0], "FGA_ATB3": [0],
                            }))
        seasons, stats = nba.compute_shot_zone_stats(2023, 2025, "Regular Season")
        assert seasons == []

    def test_skip_years_param_excludes_years(self, monkeypatch):
        calls = []
        monkeypatch.setattr(nba, "fetch_shot_zones",
                            lambda year, s, loc: calls.append(year) or None)
        nba.compute_shot_zone_stats(2019, 2021, "Playoffs", skip_years={2020})
        assert 2020 not in calls


class TestFetchShotZones:
    def _path(self, tmp_path, end_year=2024, season_type="Regular Season", location="Home"):
        fname = f"shot_zones_{nba.season_str(end_year)}_{season_type.replace(' ', '_')}_{location}.csv"
        return tmp_path / fname

    def test_returns_none_for_truly_empty_file(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        self._path(tmp_path).write_text("")
        assert nba.fetch_shot_zones(2024, "Regular Season", "Home") is None

    def test_returns_none_for_empty_dataframe_csv(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        pd.DataFrame().to_csv(self._path(tmp_path), index=False)
        assert nba.fetch_shot_zones(2024, "Regular Season", "Home") is None

    def test_returns_none_and_does_not_cache_on_api_error(self, tmp_path, monkeypatch):
        # A transient/API error must NOT be cached: a stray rate-limit would
        # otherwise be frozen as "already fetched, no data" and skipped forever.
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        monkeypatch.setattr(nba.time, "sleep", lambda *_: None)

        from nba_api.stats.endpoints import leaguedashteamshotlocations

        class FailingEndpoint:
            def __init__(self, **kwargs):
                raise RuntimeError("boom")

        monkeypatch.setattr(leaguedashteamshotlocations, "LeagueDashTeamShotLocations", FailingEndpoint)

        result = nba.fetch_shot_zones(2024, "Regular Season", "Home")
        assert result is None
        assert not self._path(tmp_path).exists()  # not cached, so a later run retries

        # Second call retries the API rather than reading a stale sentinel
        result2 = nba.fetch_shot_zones(2024, "Regular Season", "Home")
        assert result2 is None

    def test_returns_none_and_caches_sentinel_on_empty_api_result(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        monkeypatch.setattr(nba.time, "sleep", lambda *_: None)

        from nba_api.stats.endpoints import leaguedashteamshotlocations

        class EmptyEndpoint:
            def __init__(self, **kwargs):
                pass
            def get_data_frames(self):
                return [pd.DataFrame()]

        monkeypatch.setattr(leaguedashteamshotlocations, "LeagueDashTeamShotLocations", EmptyEndpoint)

        result = nba.fetch_shot_zones(2024, "Regular Season", "Home")
        assert result is None
        assert self._path(tmp_path).exists()

    def test_fetches_from_api_flattens_multiindex_and_caches(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        monkeypatch.setattr(nba.time, "sleep", lambda *_: None)

        from nba_api.stats.endpoints import leaguedashteamshotlocations

        tuples = [
            ("", "TEAM_ID"), ("", "TEAM_NAME"),
            ("Restricted Area", "FGA"), ("In The Paint (Non-RA)", "FGA"),
            ("Mid-Range", "FGA"), ("Left Corner 3", "FGA"),
            ("Right Corner 3", "FGA"), ("Above the Break 3", "FGA"),
            ("Backcourt", "FGA"),
        ]
        multi_df = pd.DataFrame(
            [[1, "Boston Celtics", 1000, 300, 400, 200, 210, 500, 5]],
            columns=pd.MultiIndex.from_tuples(tuples),
        )

        class FakeEndpoint:
            def __init__(self, **kwargs):
                pass
            def get_data_frames(self):
                return [multi_df]

        monkeypatch.setattr(leaguedashteamshotlocations, "LeagueDashTeamShotLocations", FakeEndpoint)

        result = nba.fetch_shot_zones(2024, "Regular Season", "Home")
        assert result is not None
        assert "FGA_RA" in result.columns
        assert "FGA_ATB3" in result.columns
        assert result.iloc[0]["FGA_RA"] == 1000
        assert self._path(tmp_path).exists()  # cached with flat columns

        # Second call hits cache, not API
        result2 = nba.fetch_shot_zones(2024, "Regular Season", "Home")
        assert result2 is not None
        assert result2.iloc[0]["FGA_RA"] == 1000

    def test_loads_valid_cached_csv(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        df = pd.DataFrame({
            "TEAM_ID":   [1, 2],
            "TEAM_NAME": ["Boston Celtics", "Miami Heat"],
            "FGA_RA":    [1000, 900],
            "FGA_NON_RA": [300, 250],
            "FGA_MR":    [400, 350],
            "FGA_LC3":   [200, 180],
            "FGA_RC3":   [210, 190],
            "FGA_ATB3":  [500, 450],
            "FGA_BC":    [5, 3],
        })
        df.to_csv(self._path(tmp_path), index=False)

        result = nba.fetch_shot_zones(2024, "Regular Season", "Home")
        assert result is not None
        assert len(result) == 2
        assert list(result["TEAM_NAME"]) == ["Boston Celtics", "Miami Heat"]


class TestFetchMarginData:
    def test_returns_none_when_cache_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        assert nba.fetch_margin_data(2024, "Regular Season") is None

    def test_returns_none_for_empty_dataframe(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        pd.DataFrame(columns=["MATCHUP", "WL", "PLUS_MINUS"]).to_csv(
            nba.cache_path(2024, "Regular Season"), index=False
        )
        assert nba.fetch_margin_data(2024, "Regular Season") is None

    def test_extracts_home_rows_and_renames_column(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        df = pd.DataFrame({
            "MATCHUP":    ["BOS vs. MIA", "MIA @ BOS", "LAL vs. GSW", "GSW @ LAL"],
            "WL":         ["W",           "L",          "L",           "W"],
            "PLUS_MINUS": [12,            -12,          -5,             5],
        })
        df.to_csv(nba.cache_path(2024, "Regular Season"), index=False)

        result = nba.fetch_margin_data(2024, "Regular Season")

        assert result is not None
        assert len(result) == 2
        assert list(result.columns) == ["margin", "WL"]
        assert sorted(result["margin"].tolist()) == [-5, 12]

    def test_returns_none_when_no_home_games(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        df = pd.DataFrame({
            "MATCHUP": ["BOS @ MIA"], "WL": ["W"], "PLUS_MINUS": [10],
        })
        df.to_csv(nba.cache_path(2024, "Regular Season"), index=False)
        assert nba.fetch_margin_data(2024, "Regular Season") is None


class TestComputeMarginStats:
    def test_aggregates_means_per_season(self, monkeypatch):
        def fake_fetch(year, season_type):
            if year != 2024:
                return None
            return pd.DataFrame({
                "margin": [10.0, 8.0, -4.0, -6.0],
                "WL":     ["W",  "W",  "L",  "L"],
            })

        monkeypatch.setattr(nba, "fetch_margin_data", fake_fetch)
        seasons, stats = nba.compute_margin_stats(2023, 2025, "Regular Season")

        assert seasons == ["23–24"]
        assert stats["all_games_mean"]   == [pytest.approx(2.0)]
        assert stats["home_wins_mean"]   == [pytest.approx(9.0)]
        assert stats["home_losses_mean"] == [pytest.approx(-5.0)]
        assert stats["std_dev"][0] > 0

    def test_std_dev_is_positive(self, monkeypatch):
        monkeypatch.setattr(nba, "fetch_margin_data", lambda year, s: (
            pd.DataFrame({"margin": [5.0, -3.0, 10.0], "WL": ["W", "L", "W"]})
            if year == 2024 else None
        ))
        _, stats = nba.compute_margin_stats(2024, 2024, "Regular Season")
        assert stats["std_dev"][0] > 0

    def test_skips_years_with_no_data(self, monkeypatch):
        monkeypatch.setattr(nba, "fetch_margin_data", lambda year, s: None)
        seasons, stats = nba.compute_margin_stats(2023, 2025, "Regular Season")
        assert seasons == []
        for values in stats.values():
            assert values == []

    def test_skip_years_param_excludes_years(self, monkeypatch):
        calls = []
        monkeypatch.setattr(nba, "fetch_margin_data",
                            lambda year, s: calls.append(year) or None)
        nba.compute_margin_stats(2019, 2021, "Playoffs", skip_years={2020})
        assert calls == [2019, 2021]


class TestFetchSeriesData:
    def _write_playoffs_csv(self, tmp_path, df):
        df.to_csv(nba.cache_path(2024, "Playoffs"), index=False)

    def test_returns_none_when_cache_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        assert nba.fetch_series_data(2024) is None

    def test_derives_game_in_series_from_game_id(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        df = pd.DataFrame({
            "GAME_ID":  [42300101, 42300107],
            "MATCHUP":  ["BOS vs. MIA", "BOS vs. MIA"],
            "WL":       ["W", "L"],
        })
        self._write_playoffs_csv(tmp_path, df)

        result = nba.fetch_series_data(2024)

        assert result is not None
        assert sorted(result["game_in_series"].tolist()) == [1, 7]

    def test_filters_to_home_games_only(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        df = pd.DataFrame({
            "GAME_ID":  [42300101, 42300101, 42300102, 42300102],
            "MATCHUP":  ["BOS vs. MIA", "MIA @ BOS", "MIA vs. BOS", "BOS @ MIA"],
            "WL":       ["W", "L", "L", "W"],
        })
        self._write_playoffs_csv(tmp_path, df)

        result = nba.fetch_series_data(2024)

        assert result is not None
        assert len(result) == 2  # only the two "vs." (home) rows

    def test_returns_expected_columns(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        df = pd.DataFrame({
            "GAME_ID":  [42300101],
            "MATCHUP":  ["BOS vs. MIA"],
            "WL":       ["W"],
        })
        self._write_playoffs_csv(tmp_path, df)

        result = nba.fetch_series_data(2024)

        assert result is not None
        assert set(result.columns) == {"GAME_ID", "game_in_series", "series_key", "HOME_WIN"}
        assert result.iloc[0]["HOME_WIN"] == 1  # W → home win
        assert result.iloc[0]["series_key"] == "10"  # str[-3:-1] of "42300101"


class TestComputeSeriesStats:
    def test_aggregates_home_win_pct_by_game_number(self, monkeypatch):
        def fake_fetch(year):
            if year != 2024:
                return None
            return pd.DataFrame({
                "game_in_series": [1, 1, 2, 7],
                "HOME_WIN":       [1, 0, 1, 1],
                "series_key":     ["01", "01", "01", "01"],
                "GAME_ID":        [42300101, 42300101, 42300102, 42300107],
            })

        monkeypatch.setattr(nba, "fetch_series_data", fake_fetch)
        game_nums, win_pcts, counts = nba.compute_series_stats(2023, 2025)

        assert 1 in game_nums
        assert 2 in game_nums
        assert 7 in game_nums
        idx1 = game_nums.index(1)
        assert win_pcts[idx1] == pytest.approx(50.0)   # 1 win / 2 games
        assert counts[idx1] == 2
        idx7 = game_nums.index(7)
        assert win_pcts[idx7] == pytest.approx(100.0)  # 1 win / 1 game

    def test_skips_years_with_no_data(self, monkeypatch):
        monkeypatch.setattr(nba, "fetch_series_data", lambda year: None)
        game_nums, win_pcts, counts = nba.compute_series_stats(2023, 2025)
        assert game_nums == []
        assert win_pcts == []
        assert counts == []

    def test_skip_years_param_excludes_years(self, monkeypatch):
        calls = []
        monkeypatch.setattr(nba, "fetch_series_data",
                            lambda year: calls.append(year) or None)
        nba.compute_series_stats(2019, 2021, skip_years={2020})
        assert 2020 not in calls
        assert calls == [2019, 2021]


class TestComputeParityStats:
    def test_computes_season_win_pct_std_dev(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        # T1=3W/1L=75%, T2=2W/2L=50%, T3=1W/3L=25%, T4=0W/4L=0%
        df = pd.DataFrame({
            "TEAM_ID": [1, 1, 1, 1, 2, 2, 2, 2, 3, 3, 3, 3, 4, 4, 4, 4],
            "WL": ["W", "W", "W", "L",
                   "W", "W", "L", "L",
                   "W", "L", "L", "L",
                   "L", "L", "L", "L"],
            "MATCHUP": ["A vs. B"] * 16,
        })
        df.to_csv(nba.cache_path(2024, "Regular Season"), index=False)

        seasons, std_devs = nba.compute_parity_stats(2024, 2024, "Regular Season")

        assert seasons == ["23–24"]
        expected = np.std([0.75, 0.50, 0.25, 0.00], ddof=1)
        assert std_devs[0] == pytest.approx(expected, rel=1e-5)

    def test_returns_empty_when_cache_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        seasons, std_devs = nba.compute_parity_stats(2024, 2024, "Regular Season")
        assert seasons == []
        assert std_devs == []

    def test_skips_years_in_skip_years(self, monkeypatch):
        calls = []
        monkeypatch.setattr(nba, "_load_game_log",
                            lambda year, s: calls.append(year) or None)
        nba.compute_parity_stats(2019, 2021, "Playoffs", skip_years={2020})
        assert 2020 not in calls
        assert calls == [2019, 2021]


class TestHaversine:
    def test_boston_to_la_approximately_2600_miles(self):
        # TD Garden (Boston) → Crypto.com Arena (LA)
        dist = nba._haversine(42.366, -71.062, 34.043, -118.267)
        assert 2550 < dist < 2650

    def test_same_location_returns_zero(self):
        assert nba._haversine(0.0, 0.0, 0.0, 0.0) == pytest.approx(0.0, abs=1e-6)

    def test_is_symmetric(self):
        d1 = nba._haversine(42.366, -71.062, 34.043, -118.267)
        d2 = nba._haversine(34.043, -118.267, 42.366, -71.062)
        assert d1 == pytest.approx(d2, rel=1e-9)


class TestComputeLeaguePaceStats:
    def _write_csv(self, tmp_path, df):
        df.to_csv(nba.cache_path(2024, "Regular Season"), index=False)

    def test_computes_pace_per_season(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        # Two games (4 team-rows): poss = 80 - 5 + 15 + 0.44*20 = 98.8
        # pace = 98.8 * 240 / 240 = 98.8
        df = pd.DataFrame({
            "GAME_ID":  [1, 1, 2, 2],
            "MATCHUP":  ["A vs. B", "B @ A", "C vs. D", "D @ C"],
            "TEAM_NAME": ["Team A", "Team B", "Team C", "Team D"],
            "WL":       ["W", "L", "W", "L"],
            "FGA":      [80, 80, 80, 80],
            "OREB":     [5,  5,  5,  5],
            "TOV":      [15, 15, 15, 15],
            "FTA":      [20, 20, 20, 20],
            "MIN":      [240, 240, 240, 240],
        })
        self._write_csv(tmp_path, df)

        seasons, pace_vals, home_pcts = nba.compute_league_pace_stats(2024, 2024, "Regular Season")

        assert seasons == ["23–24"]
        expected_pace = (80 - 5 + 15 + 0.44 * 20) * 240 / 240
        assert pace_vals[0] == pytest.approx(expected_pace, rel=1e-5)
        assert home_pcts[0] == pytest.approx(100.0, rel=1e-5)

    def test_returns_empty_when_cache_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        seasons, pace_vals, home_pcts = nba.compute_league_pace_stats(2024, 2024, "Regular Season")
        assert seasons == []
        assert pace_vals == []
        assert home_pcts == []

    def test_skips_years_in_skip_years(self, monkeypatch):
        calls = []
        monkeypatch.setattr(nba, "_load_game_log",
                            lambda year, s: calls.append(year) or None)
        nba.compute_league_pace_stats(2019, 2021, "Regular Season", skip_years={2020})
        assert 2020 not in calls
        assert calls == [2019, 2021]

    def test_skips_seasons_with_missing_columns(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        # DataFrame without OREB/TOV columns
        df = pd.DataFrame({
            "GAME_ID":  [1, 1],
            "MATCHUP":  ["A vs. B", "B @ A"],
            "WL":       ["W", "L"],
            "FGA":      [80, 80],
            "FTA":      [20, 20],
            "MIN":      [240, 240],
        })
        self._write_csv(tmp_path, df)
        seasons, pace_vals, home_pcts = nba.compute_league_pace_stats(2024, 2024, "Regular Season")
        assert seasons == []


class TestComputeTeamHcaStats:
    def _make_game_log(self, tmp_path, year, rows):
        df = pd.DataFrame({
            "MATCHUP":   [r[0] for r in rows],
            "WL":        [r[1] for r in rows],
            "TEAM_NAME": [r[2] for r in rows],
        })
        df.to_csv(nba.cache_path(year, "Regular Season"), index=False)

    def test_computes_hca_correctly(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        # Boston: 42 home wins / 60 home games = 70%
        #          30 road wins / 60 road games = 50%  → HCA = +20 pp
        rows = (
            [("BOS vs. MIA", "W", "Boston Celtics")] * 42 +
            [("BOS vs. MIA", "L", "Boston Celtics")] * 18 +
            [("BOS @ LAL",   "W", "Boston Celtics")] * 30 +
            [("BOS @ LAL",   "L", "Boston Celtics")] * 30
        )
        self._make_game_log(tmp_path, 2024, rows)

        result = nba.compute_team_hca_stats(2024, 2024, "Regular Season", min_games=50)

        assert "Boston Celtics" in result
        bos = result["Boston Celtics"]
        assert abs(bos["home_pct"] - 70.0) < 0.01
        assert abs(bos["road_pct"] - 50.0) < 0.01
        assert abs(bos["hca"]     - 20.0) < 0.01
        assert bos["n_home"] == 60
        assert bos["n_road"] == 60

    def test_filters_teams_below_min_games(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        # Miami: only 5 home games — should be excluded with min_games=50
        rows = (
            [("BOS vs. MIA", "W", "Boston Celtics")] * 42 +
            [("BOS vs. MIA", "L", "Boston Celtics")] * 18 +
            [("BOS @ LAL",   "W", "Boston Celtics")] * 30 +
            [("BOS @ LAL",   "L", "Boston Celtics")] * 30 +
            [("MIA vs. BOS", "W", "Miami Heat")] * 3 +
            [("MIA vs. BOS", "L", "Miami Heat")] * 2
        )
        self._make_game_log(tmp_path, 2024, rows)

        result = nba.compute_team_hca_stats(2024, 2024, "Regular Season", min_games=50)

        assert "Boston Celtics" in result
        assert "Miami Heat" not in result

    def test_returns_empty_when_cache_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        result = nba.compute_team_hca_stats(2024, 2024, "Regular Season")
        assert result == {}

    def test_skip_years_excludes_seasons(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        rows = (
            [("BOS vs. MIA", "W", "Boston Celtics")] * 30 +
            [("BOS @ LAL",   "W", "Boston Celtics")] * 30
        )
        self._make_game_log(tmp_path, 2024, rows)

        result = nba.compute_team_hca_stats(2024, 2024, "Regular Season", skip_years={2024})
        assert result == {}


class TestComputeTeamSeasonHca:
    def _make_game_log(self, tmp_path, year, rows):
        df = pd.DataFrame({
            "MATCHUP":   [r[0] for r in rows],
            "WL":        [r[1] for r in rows],
            "TEAM_NAME": [r[2] for r in rows],
        })
        df.to_csv(nba.cache_path(year, "Regular Season"), index=False)

    def test_single_season_snapshot(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        # Boston: 6 home wins / 8 home = 75%; 4 road wins / 8 road = 50% → +25
        # Miami:  2 home wins / 8 home = 25%; 3 road wins / 8 road = 37.5% → -12.5
        rows = (
            [("BOS vs. MIA", "W", "Boston Celtics")] * 6 +
            [("BOS vs. MIA", "L", "Boston Celtics")] * 2 +
            [("BOS @ MIA",   "W", "Boston Celtics")] * 4 +
            [("BOS @ MIA",   "L", "Boston Celtics")] * 4 +
            [("MIA vs. BOS", "W", "Miami Heat")] * 2 +
            [("MIA vs. BOS", "L", "Miami Heat")] * 6 +
            [("MIA @ BOS",   "W", "Miami Heat")] * 3 +
            [("MIA @ BOS",   "L", "Miami Heat")] * 5
        )
        self._make_game_log(tmp_path, 2026, rows)

        result = nba.compute_team_season_hca(2026, "Regular Season")

        assert result["Boston Celtics"]["home_pct"] == pytest.approx(75.0)
        assert result["Boston Celtics"]["road_pct"] == pytest.approx(50.0)
        assert result["Boston Celtics"]["hca"]      == pytest.approx(25.0)
        # No min_games filter: Miami is kept even with a negative gap.
        assert result["Miami Heat"]["hca"] == pytest.approx(-12.5)

    def test_returns_empty_when_cache_missing(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        assert nba.compute_team_season_hca(2026, "Regular Season") == {}


class TestFetchRefereeData:
    def _make_game_log(self, path, game_ids):
        rows = []
        for gid in game_ids:
            rows.append({"GAME_ID": gid, "MATCHUP": "BOS vs. MIA", "WL": "W", "TEAM_NAME": "Boston Celtics"})
        pd.DataFrame(rows).to_csv(path, index=False)

    def test_reads_from_cache_when_present(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        cache_file = tmp_path / "referee_2023-24_Playoffs.csv"
        cached = pd.DataFrame({
            "GAME_ID": ["0042300401", "0042300401"],
            "personId": [1, 2],
            "name": ["Joe Smith", "Ann Jones"],
        })
        cached.to_csv(cache_file, index=False)
        result = nba.fetch_referee_data(2024, "Playoffs")
        assert result is not None
        assert len(result) == 2
        assert list(result["name"]) == ["Joe Smith", "Ann Jones"]

    def test_returns_none_when_no_game_log(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        result = nba.fetch_referee_data(2024, "Playoffs")
        assert result is None

    # The cache must tell genuine absence of officials data (cache an empty file,
    # never retry) apart from transient API failures (do not cache, retry).
    @staticmethod
    def _patch_box(monkeypatch, box_cls):
        import nba_api.stats.endpoints.boxscoresummaryv3 as bsv3
        monkeypatch.setattr(bsv3, "BoxScoreSummaryV3", box_cls)

    @staticmethod
    def _box_returning(df):
        class _DS:
            def get_data_frame(self):
                return df
        class Box:
            def __init__(self, **kwargs):
                self.data_sets = [None, None, None, _DS()]
        return Box

    def _prep(self, tmp_path, monkeypatch, year=2024):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        monkeypatch.setattr(nba, "_load_game_log",
                            lambda y, s: pd.DataFrame({"GAME_ID": ["0048300001", "0048300002"]}))
        monkeypatch.setattr(nba.time, "sleep", lambda *_: None)
        return tmp_path / f"referee_{nba.season_str(year)}_Playoffs.csv"

    def test_caches_empty_for_pre_data_season_with_no_officials(self, tmp_path, monkeypatch):
        # Pre-OFFICIALS_DATA_START_YEAR: API responds but officials are genuinely
        # absent. Safe to cache an empty marker and never retry.
        cache_file = self._prep(tmp_path, monkeypatch, year=1999)
        self._patch_box(monkeypatch, self._box_returning(pd.DataFrame(columns=["personId", "name"])))

        assert nba.fetch_referee_data(1999, "Playoffs") is None
        assert cache_file.exists()

    def test_suspect_empty_not_cached_for_modern_season(self, tmp_path, monkeypatch):
        # A season that *should* have officials (>= OFFICIALS_DATA_START_YEAR) but
        # returns all-empty with no error is the silent-rate-limit signature: must
        # NOT be cached, or a real season gets marked permanently empty.
        cache_file = self._prep(tmp_path, monkeypatch, year=2024)
        self._patch_box(monkeypatch, self._box_returning(pd.DataFrame(columns=["personId", "name"])))

        assert nba.fetch_referee_data(2024, "Playoffs") is None
        assert not cache_file.exists()  # left absent so the next run retries

    def test_does_not_cache_when_all_calls_raise(self, tmp_path, monkeypatch):
        # Rate limit / outage: every call raises. Must not poison the cache.
        cache_file = self._prep(tmp_path, monkeypatch)

        class FailingBox:
            def __init__(self, **kwargs):
                raise RuntimeError("rate limited")
        self._patch_box(monkeypatch, FailingBox)

        assert nba.fetch_referee_data(2024, "Playoffs") is None
        # Transient failure -> no file, so the next run retries.
        assert not cache_file.exists()

    def test_caches_records_when_officials_present(self, tmp_path, monkeypatch):
        cache_file = self._prep(tmp_path, monkeypatch)
        officials = pd.DataFrame({"personId": [1, 2, 3], "name": ["A", "B", "C"]})
        self._patch_box(monkeypatch, self._box_returning(officials))

        result = nba.fetch_referee_data(2024, "Playoffs")
        assert result is not None
        assert len(result) == 6  # 3 officials x 2 games
        assert cache_file.exists()

    def test_is_rate_limit_error_classification(self):
        import requests
        from nbakit.data import is_rate_limit_error
        assert is_rate_limit_error(requests.exceptions.ReadTimeout("slow"))
        assert is_rate_limit_error(requests.exceptions.ConnectionError("dropped"))
        assert is_rate_limit_error(RuntimeError("HTTP 429 Too Many Requests"))
        assert not is_rate_limit_error(ValueError("missing key 'personId'"))


class TestComputeRefereeBiasStats:
    def _setup(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        # Two games: game 1 (home wins, more home fouls), game 2 (visitor fouls more)
        game_log = pd.DataFrame({
            "GAME_ID":  [1, 1, 2, 2],
            "MATCHUP":  ["BOS vs. MIA", "MIA @ BOS", "LAL vs. GSW", "GSW @ LAL"],
            "WL":       ["W", "L", "L", "W"],
            "TEAM_NAME": ["Boston Celtics", "Miami Heat", "Los Angeles Lakers", "Golden State Warriors"],
            "PF":       [22, 18, 18, 24],
            "FGM":      [40, 38, 38, 42],
            "FGA":      [85, 82, 82, 88],
            "FG3M":     [12, 10, 10, 14],
            "FG3A":     [30, 28, 28, 32],
            "FTM":      [18, 16, 16, 20],
            "FTA":      [22, 20, 20, 24],
        })
        game_log.to_csv(nba.cache_path(2024, "Playoffs"), index=False)

        # GAME_IDs must normalize to the same 10-digit string as the game log entries
        # game log has int GAME_ID 1 → "0000000001"; 2 → "0000000002"
        ref_df = pd.DataFrame({
            "GAME_ID":  ["0000000001", "0000000001", "0000000002", "0000000002"],
            "personId": [10, 11, 10, 12],
            "name":     ["Alice Ref", "Bob Ref", "Alice Ref", "Carol Ref"],
            "year":     [2024, 2024, 2024, 2024],
        })
        return ref_df

    def test_computes_per_official_mean_foul_diff(self, tmp_path, monkeypatch):
        ref_df = self._setup(tmp_path, monkeypatch)
        # game 1: foul_diff = 22-18 = +4; game 2: foul_diff = 18-24 = -6
        # Alice worked both games: mean = (4 + -6) / 2 = -1.0
        result = nba.compute_referee_bias_stats(
            ref_df, 2024, 2024, "Playoffs", min_games=1
        )
        alice = next(o for o in result if o["name"] == "Alice Ref")
        assert abs(alice["mean_foul_diff"] - (-1.0)) < 0.01
        assert alice["n_games"] == 2

    def test_excludes_officials_below_min_games(self, tmp_path, monkeypatch):
        ref_df = self._setup(tmp_path, monkeypatch)
        # With min_games=2, only Alice (2 games) qualifies; Bob and Carol have 1 each
        result = nba.compute_referee_bias_stats(
            ref_df, 2024, 2024, "Playoffs", min_games=2
        )
        names = [o["name"] for o in result]
        assert "Alice Ref" in names
        assert "Bob Ref" not in names
        assert "Carol Ref" not in names


class TestShapleyShares:
    """PLAN-STATS item 4: Shapley R² decomposition properties."""

    def _make_reg_df(self, n=200, seed=42):
        """Minimal synthetic game-level DataFrame for testing Shapley fits."""
        import home_court_analysis as reg_mod
        rng = np.random.default_rng(seed)
        year = rng.integers(1984, 2025, size=n)
        era = np.where(year <= 1994, "1984–94",
              np.where(year <= 2001, "1995–01",
              np.where(year <= 2004, "2002–04",
              np.where(year <= 2017, "2005–17",
              np.where(year <= 2022, "2018–22", "2023–26")))))
        rest_diff     = rng.integers(-2, 3, size=n).astype(float)
        altitude_home = rng.integers(0, 2, size=n).astype(float)
        tz_diff       = rng.integers(0, 4, size=n).astype(float)
        covid         = (year >= 2020) & (year <= 2021)
        home_win      = rng.integers(0, 2, size=n)
        return pd.DataFrame({
            "home_win":      home_win,
            "year":          year,
            "era":           era,
            "rest_diff":     rest_diff,
            "altitude_home": altitude_home,
            "tz_diff":       tz_diff,
            "covid":         covid.astype(int),
        })

    def test_shares_sum_to_100(self):
        import home_court_analysis as reg_mod
        df = self._make_reg_df()
        shares = reg_mod._compute_shapley_shares(df, "1984–94")
        total = sum(shares.values())
        assert abs(total - 100.0) < 0.5  # allow small floating-point discrepancy

    def test_all_shares_finite(self):
        import home_court_analysis as reg_mod
        df = self._make_reg_df()
        shares = reg_mod._compute_shapley_shares(df, "1984–94")
        assert all(np.isfinite(v) for v in shares.values())

    def test_returns_all_five_blocks(self):
        import home_court_analysis as reg_mod
        df = self._make_reg_df()
        shares = reg_mod._compute_shapley_shares(df, "1984–94")
        assert set(shares.keys()) == {"era", "rest", "altitude", "tz", "covid"}


class TestComputeRefereeBiasStatsSd:
    """PLAN-STATS item 1: sd_foul_diff must be computed from actual per-game values."""

    def _setup(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        # Game 1: foul_diff = PF_home - PF_away = 22 - 18 = +4
        # Game 2: foul_diff = 18 - 24 = -6
        game_log = pd.DataFrame({
            "GAME_ID":   [1, 1, 2, 2],
            "MATCHUP":   ["BOS vs. MIA", "MIA @ BOS", "LAL vs. GSW", "GSW @ LAL"],
            "WL":        ["W", "L", "L", "W"],
            "TEAM_NAME": ["Boston Celtics", "Miami Heat", "Los Angeles Lakers", "Golden State Warriors"],
            "PF":        [22, 18, 18, 24],
            "FGM":       [40, 38, 38, 42],
            "FGA":       [85, 82, 82, 88],
            "FG3M":      [12, 10, 10, 14],
            "FG3A":      [30, 28, 28, 32],
            "FTM":       [18, 16, 16, 20],
            "FTA":       [22, 20, 20, 24],
        })
        game_log.to_csv(nba.cache_path(2024, "Playoffs"), index=False)

        ref_df = pd.DataFrame({
            "GAME_ID":  ["0000000001", "0000000001", "0000000002", "0000000002"],
            "personId": [10, 11, 10, 12],
            "name":     ["Alice Ref", "Bob Ref", "Alice Ref", "Carol Ref"],
            "year":     [2024, 2024, 2024, 2024],
        })
        return ref_df

    def test_sd_foul_diff_is_per_game_std(self, tmp_path, monkeypatch):
        ref_df = self._setup(tmp_path, monkeypatch)
        result = nba.compute_referee_bias_stats(ref_df, 2024, 2024, "Playoffs", min_games=1)
        alice = next(o for o in result if o["name"] == "Alice Ref")
        # Alice: per-game foul_diffs = [+4, -6]; std(ddof=1) = sqrt(50) ≈ 7.071
        expected_sd = float(np.std([4.0, -6.0], ddof=1))
        assert abs(alice["sd_foul_diff"] - expected_sd) < 0.01

    def test_single_game_official_sd_is_zero(self, tmp_path, monkeypatch):
        ref_df = self._setup(tmp_path, monkeypatch)
        result = nba.compute_referee_bias_stats(ref_df, 2024, 2024, "Playoffs", min_games=1)
        bob = next(o for o in result if o["name"] == "Bob Ref")
        # Bob worked only 1 game — sd is 0 (not NaN) so t-test code won't divide by zero
        assert bob["sd_foul_diff"] == pytest.approx(0.0)

    def test_era_sd_and_era_n_are_populated(self, tmp_path, monkeypatch):
        ref_df = self._setup(tmp_path, monkeypatch)
        result = nba.compute_referee_bias_stats(ref_df, 2024, 2024, "Playoffs", min_games=1)
        alice = next(o for o in result if o["name"] == "Alice Ref")
        assert "era_sd" in alice
        assert "era_n" in alice
        # 2024 falls in the 2023–26 era; Alice has 2 games there → n=2 and sd is present
        era = "2023–26"
        assert alice["era_n"].get(era, 0) == 2
        assert era in alice["era_sd"]


class TestRealTtestSignificance:
    """PLAN-STATS item 1: verify the real t-test is used and gives sensible results."""

    def test_near_zero_mean_official_not_significant(self):
        # Josh Tiven-like case: mean=-0.112, realistic SD=3.0, n=89
        # Old broken test: ttest_1samp([-0.112]*89, 0) → p<0.001 (zero variance, WRONG)
        # Correct test: t = mean / (sd / sqrt(n)) = -0.112 / (3/sqrt(89)) ≈ -0.352 → p≈0.73
        from scipy import stats as sp_stats
        mean, sd, n = -0.112, 3.0, 89
        t = mean / (sd / np.sqrt(n))
        p = float(sp_stats.t.sf(abs(t), n - 1) * 2)
        assert p > 0.05

    def test_large_bias_official_is_significant(self):
        # Mean=-0.6, SD=3.0, n=200 → t≈-2.83 → p≈0.005
        from scipy import stats as sp_stats
        mean, sd, n = -0.6, 3.0, 200
        t = mean / (sd / np.sqrt(n))
        p = float(sp_stats.t.sf(abs(t), n - 1) * 2)
        assert p < 0.05


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


def _write_attendance_cache(cache_dir, end_year, rows):
    """Write a synthetic per-game attendance cache file for one season."""
    path = os.path.join(cache_dir, f"attendance_{nba.season_str(end_year)}.csv")
    pd.DataFrame(rows, columns=[
        "game_date", "away_team", "home_team",
        "away_pts", "home_pts", "attendance", "home_win",
    ]).to_csv(path, index=False)


class TestComputeAttendanceSeasonStats:
    def test_averages_only_reported_crowds_and_drops_empty_seasons(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        # 2024: crowds 10,000 / 20,000 / a 0 (unreported) -> mean of the two >0 = 15,000
        _write_attendance_cache(str(tmp_path), 2024, [
            ["d1", "A", "B", 90, 100, 10000, 1],
            ["d2", "C", "D", 88, 99, 20000, 1],
            ["d3", "E", "F", 95, 80, 0, 1],   # 0 excluded from the mean
        ])
        # 2025: all zero attendance -> no reported crowd -> season skipped
        _write_attendance_cache(str(tmp_path), 2025, [
            ["d1", "A", "B", 90, 100, 0, 1],
        ])

        seasons, avg = nba.compute_attendance_season_stats(2024, 2025)

        assert seasons == ["23–24"]
        assert avg == [15000.0]

    def test_missing_season_is_skipped(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        _write_attendance_cache(str(tmp_path), 2024, [
            ["d1", "A", "B", 90, 100, 12000, 1],
        ])
        # 2023 has no cache file and no network is hit because we never request it
        seasons, avg = nba.compute_attendance_season_stats(2024, 2024)
        assert seasons == ["23–24"]
        assert avg == [12000.0]


class TestComputeAttendanceCovidDoseResponse:
    def test_keeps_zeros_drops_nan_and_returns_two_columns(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        _write_attendance_cache(str(tmp_path), 2021, [
            ["d1", "A", "B", 90, 100, 0, 1],       # empty arena kept
            ["d2", "C", "D", 99, 88, 3000, 0],     # crowd kept
            ["d3", "E", "F", 80, 95, "", 1],       # NaN attendance dropped
        ])
        out = nba.compute_attendance_covid_doseresponse(2021)

        assert list(out.columns) == ["attendance", "home_win"]
        assert len(out) == 2  # NaN row dropped, zero row kept
        assert set(out["attendance"]) == {0.0, 3000.0}

    def test_returns_empty_frame_when_no_cache(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        # cache the miss so fetch_attendance never reaches the network
        pd.DataFrame().to_csv(
            os.path.join(str(tmp_path), f"attendance_{nba.season_str(2021)}.csv"), index=False
        )
        out = nba.compute_attendance_covid_doseresponse(2021)
        assert out.empty
        assert list(out.columns) == ["attendance", "home_win"]


class TestFetchAttendanceCaching:
    def test_empty_cache_file_returns_none_without_network(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        # a cached miss (empty file) must short-circuit before any BBR request
        def _boom(*_a, **_k):
            raise AssertionError("network must not be hit when cache exists")
        monkeypatch.setattr(nba, "_bbr_get", _boom)
        pd.DataFrame().to_csv(
            os.path.join(str(tmp_path), f"attendance_{nba.season_str(2024)}.csv"), index=False
        )
        assert nba.fetch_attendance(2024) is None

    def test_transient_failure_is_not_cached(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        monkeypatch.setattr(nba, "_bbr_get", lambda url: None)  # 429/network failure
        assert nba.fetch_attendance(2024) is None
        # a transient failure must NOT write a miss file, so the season retries
        assert not os.path.exists(
            os.path.join(str(tmp_path), f"attendance_{nba.season_str(2024)}.csv")
        )

    def test_genuine_miss_is_cached(self, tmp_path, monkeypatch):
        monkeypatch.setattr(nba, "CACHE_DIR", str(tmp_path))
        from bs4 import BeautifulSoup
        # index loads (200) but has no month-filter links -> genuine empty season
        monkeypatch.setattr(nba, "_bbr_get",
                            lambda url: BeautifulSoup("<html></html>", "lxml"))
        assert nba.fetch_attendance(2024) is None
        assert os.path.exists(
            os.path.join(str(tmp_path), f"attendance_{nba.season_str(2024)}.csv")
        )


class TestComputeLeague3paStats:
    def test_rate_and_home_pct_per_season(self, monkeypatch):
        # 2010: FG3A 40 of FGA 200 -> 20% 3PA rate; merged 3/4 home wins -> 75%
        def fake_load(year, season_type):
            if year == 2010:
                return pd.DataFrame({"FGA": [100, 100], "FG3A": [25, 15]})
            return None
        monkeypatch.setattr(nba, "_load_game_log", fake_load)
        monkeypatch.setattr(nba, "_merge_home_away_rows",
                            lambda df: pd.DataFrame({"WL_home": ["W", "L", "W", "W"]}))

        seasons, rates, pcts = nba.compute_league_3pa_stats(2009, 2011, "Regular Season")
        assert seasons == [nba.short_label(2010)]   # 2009/2011 load None -> skipped
        assert rates == pytest.approx([20.0])
        assert pcts == pytest.approx([75.0])

    def test_zero_fga_season_skipped(self, monkeypatch):
        monkeypatch.setattr(nba, "_load_game_log",
                            lambda y, st: pd.DataFrame({"FGA": [0, 0], "FG3A": [0, 0]}))
        monkeypatch.setattr(nba, "_merge_home_away_rows",
                            lambda df: pd.DataFrame({"WL_home": ["W"]}))
        seasons, rates, pcts = nba.compute_league_3pa_stats(2010, 2010, "Regular Season")
        assert seasons == [] and rates == [] and pcts == []


class TestComputeSeriesStatsByEra:
    def test_buckets_by_era_with_min_game_threshold(self, monkeypatch):
        # game 1: 6 games (4 home wins -> 66.7%); game 2: 3 games (< 5 -> dropped)
        def fake_fetch(year):
            if year == 2010:
                return pd.DataFrame({
                    "game_in_series": [1] * 6 + [2] * 3,
                    "HOME_WIN":       [1, 1, 1, 1, 0, 0] + [1, 1, 1],
                })
            return None
        monkeypatch.setattr(nba, "fetch_series_data", fake_fetch)

        result = nba.compute_series_stats_by_era(2009, 2011)
        era = next(lbl for lbl, y1, y2, _ in nba.ERA_DEFS if y1 <= 2010 <= y2)
        assert result[era][1] == pytest.approx(100 * 4 / 6)
        assert 2 not in result[era]                 # below 5-game threshold
        # eras with no underlying data are omitted entirely
        assert set(result) == {era}

    def test_skip_years_excluded(self, monkeypatch):
        monkeypatch.setattr(nba, "fetch_series_data",
                            lambda y: pd.DataFrame({"game_in_series": [1] * 6,
                                                    "HOME_WIN": [1] * 6}))
        result = nba.compute_series_stats_by_era(2010, 2010, skip_years={2010})
        assert result == {}


class TestSimulateSeriesHomeWinProb:
    def test_fair_coin_is_a_coin_flip(self):
        # p=0.5 single game -> ~0.5 series win for either side, regardless of pattern
        assert nba.simulate_series_home_win_prob(0.5, n_sims=50_000) == pytest.approx(0.5, abs=0.01)

    def test_monotonic_in_per_game_edge(self):
        probs = [nba.simulate_series_home_win_prob(p, n_sims=40_000)
                 for p in (0.55, 0.60, 0.65, 0.70)]
        assert probs == sorted(probs)

    def test_compresses_the_per_game_edge(self):
        # a 60% single-game edge yields a series edge strictly between 50% and 60%
        s = nba.simulate_series_home_win_prob(0.60, n_sims=80_000)
        assert 0.50 < s < 0.60

    def test_certain_winner_sweeps(self):
        assert nba.simulate_series_home_win_prob(1.0, n_sims=1_000) == pytest.approx(1.0)

    def test_seed_is_reproducible(self):
        a = nba.simulate_series_home_win_prob(0.62, n_sims=20_000, seed=7)
        b = nba.simulate_series_home_win_prob(0.62, n_sims=20_000, seed=7)
        assert a == b

    def test_rejects_out_of_range_probability(self):
        with pytest.raises(ValueError):
            nba.simulate_series_home_win_prob(1.5)


class TestComputeSeriesSimulation:
    def test_assembles_per_era_and_curve(self, monkeypatch):
        # one regular-season home win % and one playoff home win % per era,
        # via a fake game log: 3 home rows, home WL controls the win %.
        def fake_log(year, season_type):
            wl = ["W", "W", "L"] if season_type == "Playoffs" else ["W", "L", "L"]
            return pd.DataFrame({
                "MATCHUP": ["AAA vs. BBB"] * 3,
                "WL": wl,
            })
        monkeypatch.setattr(nba, "_load_game_log", fake_log)

        data = nba.compute_series_simulation(
            nba.START_YEAR, nba.END_YEAR, n_sims=20_000,
        )
        eras = [e[0] for e in nba.ERA_DEFS]
        assert data["era_labels"] == eras
        # playoffs 2/3 home wins -> 66.7%, regular season 1/3 -> 33.3%
        assert data["po_pgame"][0] == pytest.approx(100 * 2 / 3, abs=0.1)
        assert data["reg_pgame"][0] == pytest.approx(100 * 1 / 3, abs=0.1)
        # a >50% per-game edge compresses toward 50 at the series level
        assert 50 < data["po_series"][0] < data["po_pgame"][0]
        # a <50% per-game "edge" leaves the host below the coin flip
        assert data["reg_series"][0] < 50
        # transfer curve spans the 50–70% input grid
        assert data["curve_pgame"][0] == pytest.approx(50.0)
        assert data["curve_pgame"][-1] == pytest.approx(70.0)
        assert len(data["curve_series"]) == len(data["curve_pgame"])
