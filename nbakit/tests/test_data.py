"""Tests for nbakit.data — season helpers, SRS, champion identification."""

import os
import pandas as pd
import pytest

from nbakit.data import (
    fill_plus_minus,
    add_rest_days,
    cache_path,
    compute_srs,
    default_cache_dir,
    home_abbr,
    identify_champion,
    is_home,
    merge_home_away_rows,
    season_range_label,
    season_str,
    short_label,
)


# ── Season helpers ─────────────────────────────────────────────────────────────

def test_season_str():
    assert season_str(2026) == "2025-26"
    assert season_str(1984) == "1983-84"
    assert season_str(2000) == "1999-00"


def test_short_label():
    assert short_label(2026) == "25–26"
    assert short_label(1984) == "83–84"


def test_season_range_label():
    assert season_range_label(1984, 2026) == "1983–84 through 2025–26"
    assert season_range_label(2000, 2010) == "1999–00 through 2009–10"


def test_cache_path_uses_shared_dir():
    path = cache_path(2026, "Playoffs")
    assert path.endswith("2025-26_Playoffs.csv")
    assert "cache" in path


def test_cache_path_spaces_become_underscores():
    assert "Regular_Season" in cache_path(2026, "Regular Season")


def test_cache_path_custom_dir(tmp_path):
    p = cache_path(2026, "Playoffs", cache_dir=str(tmp_path))
    assert str(tmp_path) in p


def test_default_cache_dir_env_var(tmp_path, monkeypatch):
    monkeypatch.setenv("NBA_CACHE_DIR", str(tmp_path))
    assert default_cache_dir() == str(tmp_path)


# ── fill_plus_minus ───────────────────────────────────────────────────────────

def test_fill_plus_minus_from_pts():
    df = pd.DataFrame([
        {"GAME_ID": "G1", "TEAM_ID": 1, "PTS": 110, "PLUS_MINUS": float("nan")},
        {"GAME_ID": "G1", "TEAM_ID": 2, "PTS": 100, "PLUS_MINUS": float("nan")},
    ])
    filled = fill_plus_minus(df)
    assert filled.loc[filled["TEAM_ID"] == 1, "PLUS_MINUS"].iloc[0] == 10.0
    assert filled.loc[filled["TEAM_ID"] == 2, "PLUS_MINUS"].iloc[0] == -10.0


def test_fill_plus_minus_leaves_existing_values():
    df = pd.DataFrame([
        {"GAME_ID": "G1", "TEAM_ID": 1, "PTS": 110, "PLUS_MINUS": 99.0},
        {"GAME_ID": "G1", "TEAM_ID": 2, "PTS": 100, "PLUS_MINUS": -99.0},
    ])
    filled = fill_plus_minus(df)
    assert filled.loc[filled["TEAM_ID"] == 1, "PLUS_MINUS"].iloc[0] == 99.0


# ── compute_srs ────────────────────────────────────────────────────────────────

def _make_game_logs():
    """Three-team round-robin: T1 beats T2 by 10, T3 beats T1 by 5, T2 beats T3 by 3."""
    return pd.DataFrame([
        {"GAME_ID": "G1", "TEAM_ID": 1, "PLUS_MINUS": 10.0},
        {"GAME_ID": "G1", "TEAM_ID": 2, "PLUS_MINUS": -10.0},
        {"GAME_ID": "G2", "TEAM_ID": 1, "PLUS_MINUS": -5.0},
        {"GAME_ID": "G2", "TEAM_ID": 3, "PLUS_MINUS": 5.0},
        {"GAME_ID": "G3", "TEAM_ID": 2, "PLUS_MINUS": 3.0},
        {"GAME_ID": "G3", "TEAM_ID": 3, "PLUS_MINUS": -3.0},
    ])


def test_compute_srs_returns_series():
    srs = compute_srs(_make_game_logs())
    assert isinstance(srs, pd.Series)
    assert set(srs.index) == {1, 2, 3}


def test_compute_srs_sums_to_zero():
    srs = compute_srs(_make_game_logs())
    assert abs(srs.sum()) < 1e-9


def test_compute_srs_ordering():
    # T1 beat T2 badly; T3 beat T1; T2 beat T3 narrowly
    # Expected ranking: T1 > T3 > T2
    srs = compute_srs(_make_game_logs())
    assert srs[1] > srs[3] > srs[2]


def test_compute_srs_known_values():
    srs = compute_srs(_make_game_logs())
    # Derived analytically: T1=5/3, T2=-7/3, T3=2/3
    assert abs(srs[1] - 5 / 3) < 1e-6
    assert abs(srs[2] - (-7 / 3)) < 1e-6
    assert abs(srs[3] - 2 / 3) < 1e-6


# ── identify_champion ─────────────────────────────────────────────────────────

def _make_playoff_logs():
    """T1 wins 16, T2 wins 12, T3 wins 8."""
    rows = []
    for team, wins in [(1, 16), (2, 12), (3, 8)]:
        for i in range(wins):
            rows.append({"TEAM_ID": team, "WL": "W", "GAME_ID": f"T{team}W{i}"})
        rows.append({"TEAM_ID": team, "WL": "L", "GAME_ID": f"T{team}L0"})
    return pd.DataFrame(rows)


def test_identify_champion_returns_most_wins():
    assert identify_champion(_make_playoff_logs()) == 1


def test_identify_champion_type():
    assert isinstance(identify_champion(_make_playoff_logs()), int)


# ── MATCHUP parsing ───────────────────────────────────────────────────────────

def test_is_home():
    assert is_home("NYK vs. BOS") is True
    assert is_home("NYK @ BOS") is False


def test_home_abbr():
    assert home_abbr("NYK vs. BOS") == "NYK"
    assert home_abbr("NYK @ BOS") == "BOS"


def test_merge_home_away_rows():
    df = pd.DataFrame([
        {"GAME_ID": "1", "MATCHUP": "NYK vs. BOS", "PTS": 100},
        {"GAME_ID": "1", "MATCHUP": "BOS @ NYK", "PTS": 95},
    ])
    merged = merge_home_away_rows(df)
    assert len(merged) == 1
    assert merged.iloc[0]["PTS_home"] == 100
    assert merged.iloc[0]["PTS_away"] == 95


def test_merge_home_away_rows_none_when_one_sided():
    df = pd.DataFrame([{"GAME_ID": "1", "MATCHUP": "NYK vs. BOS", "PTS": 100}])
    assert merge_home_away_rows(df) is None


# ── add_rest_days ─────────────────────────────────────────────────────────────

def test_add_rest_days():
    df = pd.DataFrame([
        {"TEAM_ID": 1, "GAME_DATE": "2024-01-01"},
        {"TEAM_ID": 1, "GAME_DATE": "2024-01-02"},  # back-to-back -> 0
        {"TEAM_ID": 1, "GAME_DATE": "2024-01-05"},  # 2 days rest
    ])
    out = add_rest_days(df).sort_values("GAME_DATE").reset_index(drop=True)
    assert pd.isna(out.loc[0, "REST"])
    assert out.loc[1, "REST"] == 0
    assert out.loc[2, "REST"] == 2
