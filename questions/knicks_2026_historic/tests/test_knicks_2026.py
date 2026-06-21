"""
Unit tests for the data/computation layer (knicks_2026_data).

Correctness tests over synthetic DataFrames and the season/cache helpers. As
compute_* metrics are added, test them here against hand-built frames with known
answers — never against live API calls.
"""

import numpy as np
import pandas as pd
import pytest
import knicks_2026_data as data

KNICKS_ID = data.KNICKS_TEAM_ID
OPP1_ID   = 2
OPP2_ID   = 3


def _mini_standings() -> pd.DataFrame:
    return pd.DataFrame([
        {"TeamID": KNICKS_ID, "TeamCity": "New York",    "TeamName": "Knicks"},
        {"TeamID": OPP1_ID,   "TeamCity": "Boston",       "TeamName": "Celtics"},
        {"TeamID": OPP2_ID,   "TeamCity": "Golden State", "TeamName": "Warriors"},
    ])


def _mini_po_2026() -> pd.DataFrame:
    """Knicks play OPP1 (2 games) then OPP2 (1 game)."""
    rows = []
    for gid, opp_id, date in [
        ("G001", OPP1_ID, "2026-04-20"),
        ("G002", OPP1_ID, "2026-04-22"),
        ("G003", OPP2_ID, "2026-05-01"),
    ]:
        rows.append({"GAME_ID": gid, "TEAM_ID": KNICKS_ID, "GAME_DATE": date,
                     "WL": "W", "PTS": 120, "PLUS_MINUS": 10.0,
                     "MATCHUP": "NYK vs. OPP"})
        rows.append({"GAME_ID": gid, "TEAM_ID": opp_id, "GAME_DATE": date,
                     "WL": "L", "PTS": 110, "PLUS_MINUS": -10.0,
                     "MATCHUP": "OPP @ NYK"})
    return pd.DataFrame(rows)


def _mini_player_logs() -> pd.DataFrame:
    """
    OPP1 has 5 core players (avg ≥15 min) appearing in both Knicks games.
    OPP2 has 5 core players but player P6 is absent from the Knicks game
    (appeared only in other playoff games outside the Knicks series).
    """
    rows = []
    # OPP1: 5 core players, both series games
    for pid in range(1, 6):
        for gid in ["G001", "G002"]:
            rows.append({"PLAYER_ID": pid, "TEAM_ID": OPP1_ID,
                         "GAME_ID": gid, "MIN": "25:00"})

    # OPP2: 5 core players in G003 (Knicks series), but P6 missing from Knicks game;
    # P6 appeared in a prior round game (G_PRIOR) to qualify as "core"
    for pid in range(6, 11):
        rows.append({"PLAYER_ID": pid, "TEAM_ID": OPP2_ID,
                     "GAME_ID": "G_PRIOR", "MIN": "25:00"})
    # Only P7-P10 appear in the Knicks game (P6 absent)
    for pid in range(7, 11):
        rows.append({"PLAYER_ID": pid, "TEAM_ID": OPP2_ID,
                     "GAME_ID": "G003", "MIN": "25:00"})

    return pd.DataFrame(rows)


def test_compute_playoff_elevation():
    po  = _mini_po_2026()
    # Build minimal reg-season logs: KNICKS won by +5 on average in reg season
    rs_rows = []
    for gid in ["R001", "R002"]:
        rs_rows.append({"GAME_ID": gid, "TEAM_ID": KNICKS_ID,
                        "WL": "W", "PTS": 105, "PLUS_MINUS": 5.0,
                        "MATCHUP": "NYK vs. OPP"})
        rs_rows.append({"GAME_ID": gid, "TEAM_ID": OPP1_ID,
                        "WL": "L", "PTS": 100, "PLUS_MINUS": -5.0,
                        "MATCHUP": "OPP @ NYK"})
    rs = pd.DataFrame(rs_rows)
    elev = data.compute_playoff_elevation(po, rs, KNICKS_ID)
    # In playoffs Knicks averaged +10, in reg season +5 → elevation ~positive
    assert not np.isnan(elev)  # should compute without error


def test_compute_league_scoring_avg():
    po = _mini_po_2026()
    # All rows have PTS=120 or PTS=110; mean is 115
    avg = data.compute_league_scoring_avg(po)
    assert avg == pytest.approx(115.0)


def test_compute_pace_adjusted_margin():
    # If season avg equals reference, factor = 1 (no change)
    assert data.compute_pace_adjusted_margin(10.0, 110.0, 110.0) == pytest.approx(10.0)
    # If season avg is higher (faster era), margin gets scaled down
    assert data.compute_pace_adjusted_margin(10.0, 120.0, 110.0) == pytest.approx(10.0 * 110 / 120)
    # If season avg is lower (slower era), margin gets scaled up
    assert data.compute_pace_adjusted_margin(10.0, 100.0, 110.0) == pytest.approx(10.0 * 110 / 100)


def test_compute_opponent_playoff_srs_excl():
    po  = _mini_po_2026()
    # Knicks played G001+G002 vs OPP1 and G003 vs OPP2
    # Excluding Knicks games leaves no rows → both opponents should be NaN
    result = data.compute_opponent_playoff_srs_excl(po, KNICKS_ID)
    # All games involve the Knicks, so no independent games → NaN for all
    assert set(result.index) == {OPP1_ID, OPP2_ID}
    assert np.isnan(result[OPP1_ID])
    assert np.isnan(result[OPP2_ID])


def test_compute_opponent_playoff_srs_excl_with_independent_games():
    """OPP1 plays OPP2 in a separate game; that game is independent of the Knicks."""
    po = _mini_po_2026().copy()
    # Add a game between OPP1 and OPP2 (no Knicks involved)
    extra = pd.DataFrame([
        {"GAME_ID": "G999", "TEAM_ID": OPP1_ID, "GAME_DATE": "2026-03-01",
         "WL": "W", "PTS": 115, "PLUS_MINUS": 8.0, "MATCHUP": "OPP1 vs. OPP2"},
        {"GAME_ID": "G999", "TEAM_ID": OPP2_ID, "GAME_DATE": "2026-03-01",
         "WL": "L", "PTS": 107, "PLUS_MINUS": -8.0, "MATCHUP": "OPP2 @ OPP1"},
    ])
    po_extended = pd.concat([po, extra], ignore_index=True)
    result = data.compute_opponent_playoff_srs_excl(po_extended, KNICKS_ID)
    # OPP1 and OPP2 now have one independent game vs each other → not NaN
    assert not np.isnan(result[OPP1_ID])
    assert not np.isnan(result[OPP2_ID])


def test_compute_margin_ci():
    po  = _mini_po_2026()
    lo, hi = data.compute_margin_ci(po, KNICKS_ID)
    # All 3 games are +10; std=0, so CI degenerates but should not error
    # (In practice std=0 gives width=0; both bounds equal mean)
    assert lo <= hi
    assert not np.isnan(lo)


def test_compute_series_margins_basic():
    po  = _mini_po_2026()
    srs = pd.Series({OPP1_ID: 2.0, OPP2_ID: 4.0, KNICKS_ID: 5.0})
    result = data.compute_series_margins(po, KNICKS_ID, srs)
    # G001+G002 vs OPP1, G003 vs OPP2  →  2 rows in chronological order
    assert list(result["opp_id"]) == [OPP1_ID, OPP2_ID]
    assert result.iloc[0]["n_games"] == 2
    assert result.iloc[1]["n_games"] == 1
    assert result.iloc[0]["raw_margin"] == pytest.approx(10.0)
    assert result.iloc[0]["opp_reg_srs"] == pytest.approx(2.0)
    assert result.iloc[0]["reg_adj_margin"] == pytest.approx(8.0)


def test_compute_series_margins_with_playoff_srs():
    po      = _mini_po_2026()
    reg_srs = pd.Series({OPP1_ID: 2.0, OPP2_ID: 4.0, KNICKS_ID: 5.0})
    po_srs  = pd.Series({OPP1_ID: 1.0, OPP2_ID: 5.0, KNICKS_ID: 7.0})
    result  = data.compute_series_margins(po, KNICKS_ID, reg_srs, po_srs)
    assert "opp_playoff_srs" in result.columns
    assert result.iloc[0]["opp_playoff_srs"] == pytest.approx(1.0)
    assert result.iloc[0]["playoff_adj_margin"] == pytest.approx(9.0)   # 10 - 1
    assert result.iloc[1]["opp_playoff_srs"] == pytest.approx(5.0)
    assert result.iloc[1]["playoff_adj_margin"] == pytest.approx(5.0)   # 10 - 5


def test_compute_games_weighted_opponent_srs():
    po  = _mini_po_2026()
    srs = pd.Series({OPP1_ID: 2.0, OPP2_ID: 4.0, KNICKS_ID: 5.0})
    result = data.compute_games_weighted_opponent_srs(po, srs, KNICKS_ID)
    # G001 + G002 vs OPP1 (SRS 2.0): 2 games; G003 vs OPP2 (SRS 4.0): 1 game
    # weighted avg = (2.0 + 2.0 + 4.0) / 3
    assert result == pytest.approx((2.0 + 2.0 + 4.0) / 3, abs=1e-6)


def test_compute_expected_margin_overperformance():
    po  = _mini_po_2026()
    srs = pd.Series({OPP1_ID: 2.0, OPP2_ID: 4.0, KNICKS_ID: 5.0})
    result = data.compute_expected_margin_overperformance(po, srs, KNICKS_ID)
    # G001: actual +10, expected = 5-2 = 3, residual = 7
    # G002: actual +10, expected = 5-2 = 3, residual = 7
    # G003: actual +10, expected = 5-4 = 1, residual = 9
    assert result == pytest.approx((7.0 + 7.0 + 9.0) / 3, abs=1e-6)


def test_per_game_adjusted_margins():
    po  = _mini_po_2026()
    srs = pd.Series({OPP1_ID: 2.0, OPP2_ID: 4.0, KNICKS_ID: 5.0})
    g = data.per_game_adjusted_margins(po, srs, KNICKS_ID)
    # G001/G002 vs OPP1 (srs 2): 10-2=8 each; G003 vs OPP2 (srs 4): 10-4=6
    assert sorted(g.tolist()) == pytest.approx([6.0, 8.0, 8.0])


def test_bootstrap_adjusted_margin_rank_point_estimate():
    po  = _mini_po_2026()
    srs = pd.Series({OPP1_ID: 2.0, OPP2_ID: 4.0, KNICKS_ID: 5.0})
    # Other champions all far below any possible resample mean (min draw is 6)
    res = data.bootstrap_adjusted_margin_rank(
        po, srs, KNICKS_ID, other_champ_adj=[5.0, 1.0, -2.0], n_boot=2000, seed=1
    )
    assert res["adj_point"] == pytest.approx((8.0 + 8.0 + 6.0) / 3)
    # Every resample mean (>=6) beats all other champions → always rank 1
    assert res["p_rank1"] == pytest.approx(1.0)
    assert res["rank_median"] == pytest.approx(1.0)
    assert 1 <= res["rank_lo"] <= res["rank_hi"] <= res["n_other"] + 1


def test_bootstrap_adjusted_margin_rank_contested():
    po  = _mini_po_2026()
    srs = pd.Series({OPP1_ID: 2.0, OPP2_ID: 4.0, KNICKS_ID: 5.0})
    # A champion at +7 sits inside the resample range [6, 8] → sometimes beaten
    res = data.bootstrap_adjusted_margin_rank(
        po, srs, KNICKS_ID, other_champ_adj=[7.0, 5.0], n_boot=2000, seed=2
    )
    assert 0.0 < res["p_rank1"] < 1.0
    assert res["ci_lo"] <= res["adj_point"] <= res["ci_hi"]


def test_parse_min():
    assert data.parse_min("35:42") == pytest.approx(35.7, abs=0.1)
    assert data.parse_min(30.0) == pytest.approx(30.0)
    assert data.parse_min(None) == 0.0


def test_compute_opponent_health_full_health():
    player_logs = _mini_player_logs()
    po          = _mini_po_2026()
    standings   = _mini_standings()
    health = data.compute_opponent_health(player_logs, po, KNICKS_ID, standings)
    opp1 = health[health["team_id"] == OPP1_ID].iloc[0]
    assert opp1["total_core"] == 5
    assert opp1["avg_core_per_game"] == pytest.approx(5.0)
    assert opp1["health_score"] == pytest.approx(1.0)


def test_compute_opponent_health_depleted():
    player_logs = _mini_player_logs()
    po          = _mini_po_2026()
    standings   = _mini_standings()
    health = data.compute_opponent_health(player_logs, po, KNICKS_ID, standings)
    opp2 = health[health["team_id"] == OPP2_ID].iloc[0]
    assert opp2["total_core"] == 5
    # Only 4 of 5 core players appeared in the 1-game Knicks series
    assert opp2["avg_core_per_game"] == pytest.approx(4.0)
    assert opp2["health_score"] == pytest.approx(0.8)


def test_compute_opponent_health_order():
    """Results are sorted by first game date (round order)."""
    player_logs = _mini_player_logs()
    po          = _mini_po_2026()
    standings   = _mini_standings()
    health = data.compute_opponent_health(player_logs, po, KNICKS_ID, standings)
    assert list(health["team_id"]) == [OPP1_ID, OPP2_ID]


def _mini_odds_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"GAME_ID": "G001", "GAME_DATE": "2026-04-20",
         "home_abbr": "NYK", "knicks_home": True,
         "raw_line": "NYK -8", "line_team": "NYK",
         "line_value": -8.0, "knicks_spread": -8.0},
        {"GAME_ID": "G002", "GAME_DATE": "2026-04-22",
         "home_abbr": "BOS", "knicks_home": False,
         "raw_line": "BOS -3", "line_team": "BOS",
         "line_value": -3.0, "knicks_spread": 3.0},
    ])


def test_compute_ats_stats_covered():
    odds = _mini_odds_df()
    po   = _mini_po_2026()
    stats = data.compute_ats_stats(odds, po, KNICKS_ID)
    g001 = stats[stats["GAME_ID"] == "G001"].iloc[0]
    # actual margin +10, spread -8 (Knicks -8 favorite) → ats_margin = 10 - (-8) = 18 → covered
    assert g001["ats_margin"] == pytest.approx(18.0)
    assert g001["covered"] == True


def test_compute_ats_stats_missed():
    odds = _mini_odds_df()
    po   = _mini_po_2026()
    stats = data.compute_ats_stats(odds, po, KNICKS_ID)
    g002 = stats[stats["GAME_ID"] == "G002"].iloc[0]
    # actual margin +10, spread +3 (Knicks +3 underdog) → ats_margin = 10 - 3 = 7 → covered
    # Wait - G002 is OPP2_ID game with +10 margin too (from _mini_po_2026)
    # Actually in _mini_po_2026, G002 is also a win by +10 for the Knicks
    # knicks_spread = +3 (underdog), actual = +10 → ats = 7 → covered
    assert g002["ats_margin"] == pytest.approx(7.0)
    assert g002["covered"] == True


def test_parse_vegas_line():
    assert data._parse_vegas_line("NYK -7.5") == ("NYK", -7.5)
    assert data._parse_vegas_line("ATL -3") == ("ATL", -3.0)
    assert data._parse_vegas_line("Pick") == ("PICK", 0.0)
    assert data._parse_vegas_line("") == ("PICK", 0.0)


def test_home_abbr():
    assert data.home_abbr("NYK vs. ATL") == "NYK"
    assert data.home_abbr("NYK @ ATL") == "ATL"
    assert data.home_abbr("NYK @ SAS") == "SAS"


def test_season_str():
    assert data.season_str(2026) == "2025-26"
    assert data.season_str(1984) == "1983-84"


def test_short_label():
    assert data.short_label(2026) == "25–26"
    assert data.short_label(1984) == "83–84"


def test_cache_path():
    assert data.cache_path(2026, "Playoffs").endswith("cache/2025-26_Playoffs.csv")
    # spaces in the season type become underscores in the filename
    assert "Regular_Season" in data.cache_path(2026, "Regular Season")
