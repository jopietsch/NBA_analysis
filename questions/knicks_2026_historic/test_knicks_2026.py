"""
Unit tests for the data/computation layer (knicks_2026_data).

Correctness tests over synthetic DataFrames and the season/cache helpers. As
compute_* metrics are added, test them here against hand-built frames with known
answers — never against live API calls.
"""

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
