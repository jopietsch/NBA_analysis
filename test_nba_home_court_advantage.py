import os

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
