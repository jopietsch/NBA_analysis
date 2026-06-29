"""
Unit tests for the data/computation layer.

Tests run against synthetic DataFrames — no live API calls.
"""

import numpy as np
import pandas as pd
import pytest

from nbakit.ratings import game_score, shooting_rates, per, win_shares, bpm, vorp
from nbakit.player_crosswalk import normalize_name, build_crosswalk, apply_crosswalk


# ── Synthetic data builders ───────────────────────────────────────────────────

def _mini_player(n: int = 5) -> pd.DataFrame:
    """Minimal synthetic player-totals DataFrame."""
    return pd.DataFrame({
        "PLAYER_ID": range(1, n + 1),
        "PLAYER_NAME": [f"Player {i}" for i in range(1, n + 1)],
        "TEAM_ID": [1, 1, 2, 2, 2],
        "TEAM_ABBREVIATION": ["AAA", "AAA", "BBB", "BBB", "BBB"],
        "GP": [80, 75, 82, 60, 40],
        "MIN": [3000.0, 2500.0, 3200.0, 1800.0, 900.0],
        "PTS": [1800.0, 1400.0, 2000.0, 900.0, 400.0],
        "FGM": [700.0, 550.0, 800.0, 350.0, 150.0],
        "FGA": [1500.0, 1200.0, 1600.0, 700.0, 350.0],
        "FG3M": [200.0, 150.0, 300.0, 100.0, 30.0],
        "FG3A": [600.0, 400.0, 800.0, 300.0, 80.0],
        "FTM": [200.0, 150.0, 100.0, 100.0, 70.0],
        "FTA": [250.0, 200.0, 140.0, 140.0, 90.0],
        "OREB": [100.0, 80.0, 200.0, 50.0, 20.0],
        "DREB": [300.0, 250.0, 500.0, 150.0, 60.0],
        "REB": [400.0, 330.0, 700.0, 200.0, 80.0],
        "AST": [500.0, 100.0, 200.0, 80.0, 30.0],
        "STL": [100.0, 80.0, 50.0, 40.0, 15.0],
        "BLK": [20.0, 15.0, 100.0, 30.0, 5.0],
        "TOV": [200.0, 150.0, 180.0, 80.0, 30.0],
        "PF": [150.0, 120.0, 180.0, 100.0, 50.0],
        # Team totals (merged columns for shooting_rates)
        "TEAM_FGA": [3100.0, 3100.0, 2650.0, 2650.0, 2650.0],
        "TEAM_FTA": [600.0, 600.0, 370.0, 370.0, 370.0],
        "TEAM_TOV": [680.0, 680.0, 490.0, 490.0, 490.0],
    })


def _mini_team() -> pd.DataFrame:
    return pd.DataFrame({
        "TEAM_ID": [1, 2],
        "TEAM_NAME": ["Alpha", "Beta"],
        "GP": [82, 82],
        "MIN": [19680.0, 19680.0],
        "PTS": [9000.0, 10000.0],
        "FGM": [3300.0, 3200.0],
        "FGA": [7000.0, 6800.0],
        "FG3M": [900.0, 1000.0],
        "FG3A": [2500.0, 2800.0],
        "FTM": [1100.0, 800.0],
        "FTA": [1400.0, 1100.0],
        "OREB": [800.0, 1000.0],
        "DREB": [2800.0, 3000.0],
        "REB": [3600.0, 4000.0],
        "AST": [2000.0, 2400.0],
        "STL": [600.0, 500.0],
        "BLK": [250.0, 400.0],
        "TOV": [1200.0, 1050.0],
        "PF": [1500.0, 1600.0],
    })


def _mini_league() -> dict:
    return {
        "lg_pts": 220000.0,
        "lg_ast": 55000.0,
        "lg_oreb": 24000.0,
        "lg_dreb": 72000.0,
        "lg_reb": 96000.0,
        "lg_stl": 15000.0,
        "lg_blk": 12000.0,
        "lg_tov": 30000.0,
        "lg_pf": 45000.0,
        "lg_fgm": 80000.0,
        "lg_fga": 175000.0,
        "lg_ftm": 30000.0,
        "lg_fta": 40000.0,
        "lg_fg3m": 25000.0,
        "lg_fg3a": 70000.0,
        "lg_min": 590400.0,
        "lg_pace": 100.0,
        "lg_orb_pct": 0.25,
    }


# ── shooting_rates ────────────────────────────────────────────────────────────

def test_shooting_rates_ts_pct():
    df = _mini_player()
    out = shooting_rates(df)
    assert "TS_PCT" in out.columns
    assert "EFG_PCT" in out.columns
    assert "USG_PCT" in out.columns
    # Player 0: PTS=1800, FGA=1500, FTA=250
    # TS% = 1800 / (2 * (1500 + 0.44*250)) = 1800 / (2 * 1610) = 0.5590
    expected_ts = 1800 / (2 * (1500 + 0.44 * 250))
    assert abs(out.iloc[0]["TS_PCT"] - expected_ts) < 0.001


def test_shooting_rates_efg_pct():
    df = _mini_player()
    out = shooting_rates(df)
    # Player 0: FGM=700, FG3M=200, FGA=1500
    expected_efg = (700 + 0.5 * 200) / 1500
    assert abs(out.iloc[0]["EFG_PCT"] - expected_efg) < 0.001


def test_shooting_rates_usg_pct():
    df = _mini_player()
    out = shooting_rates(df)
    # USG% present when team columns are available
    assert out["USG_PCT"].notna().sum() > 0


# ── game_score ────────────────────────────────────────────────────────────────

def test_game_score_basic():
    df = _mini_player()
    gs = game_score(df)
    assert len(gs) == len(df)
    assert gs.notna().all()
    # The best player (high PTS, AST) should have the highest game score
    assert gs.iloc[0] > gs.iloc[4]


def test_game_score_formula():
    # One-player synthetic: check formula directly
    df = pd.DataFrame([{
        "GP": 1, "MIN": 36,
        "PTS": 30, "FGM": 12, "FGA": 20,
        "FTA": 8, "FTM": 6,
        "OREB": 2, "DREB": 5,
        "STL": 2, "AST": 5, "BLK": 1, "PF": 3, "TOV": 3,
        # Team columns (not used by game_score)
        "TEAM_FGA": 80, "TEAM_FTA": 25, "TEAM_TOV": 15,
    }])
    gs = game_score(df)
    expected = (30 + 0.4*12 - 0.7*20 - 0.4*(8-6) + 0.7*2 + 0.3*5 + 2 + 0.7*5 + 0.7*1 - 0.4*3 - 3)
    assert abs(gs.iloc[0] - expected) < 0.01


# ── PER ───────────────────────────────────────────────────────────────────────

def test_per_league_average_is_15():
    """Minutes-weighted average PER across players should be ~15."""
    df = _mini_player()
    team_df = _mini_team()
    league = _mini_league()
    per_vals = per(df, team_df, league)
    assert per_vals.notna().sum() > 0
    # Minutes-weighted average
    mp = df["MIN"]
    valid = per_vals.dropna()
    mp_valid = mp.loc[valid.index]
    weighted_avg = (valid * mp_valid).sum() / mp_valid.sum()
    assert abs(weighted_avg - 15.0) < 2.0, f"Weighted average PER = {weighted_avg:.2f}, expected ~15"


def test_per_star_player_above_average():
    """A high-production player should have PER > 15."""
    df = _mini_player()
    team_df = _mini_team()
    league = _mini_league()
    per_vals = per(df, team_df, league)
    assert per_vals.iloc[0] > 15.0, f"Star player PER = {per_vals.iloc[0]:.2f}"


# ── Win Shares ────────────────────────────────────────────────────────────────

def test_win_shares_columns():
    df = _mini_player()
    team_df = _mini_team()
    league = _mini_league()
    ws_df = win_shares(df, team_df, league)
    for col in ["OWS", "DWS", "WS", "WS48"]:
        assert col in ws_df.columns, f"Missing column: {col}"


def test_win_shares_ws48_ratio():
    """WS/48 should equal WS / MIN * 48 for players with > 0 minutes."""
    df = _mini_player()
    ws_df = win_shares(df, _mini_team(), _mini_league())
    for _, row in ws_df.iterrows():
        if row["MIN"] > 0 and not np.isnan(row["WS48"]):
            expected = row["WS"] / row["MIN"] * 48
            assert abs(row["WS48"] - expected) < 0.001


# ── BPM ──────────────────────────────────────────────────────────────────────

def test_bpm_columns():
    df = _mini_player()
    bpm_df = bpm(df, _mini_team(), _mini_league())
    for col in ["OBPM", "DBPM", "BPM"]:
        assert col in bpm_df.columns


def test_bpm_equals_obpm_plus_dbpm():
    df = _mini_player()
    bpm_df = bpm(df, _mini_team(), _mini_league())
    valid = bpm_df["BPM"].notna()
    diff = (bpm_df.loc[valid, "BPM"] - bpm_df.loc[valid, "OBPM"] - bpm_df.loc[valid, "DBPM"]).abs()
    assert diff.max() < 0.001


def test_bpm_league_average_near_zero():
    """Minutes-weighted BPM average should be near 0 after normalization."""
    df = _mini_player()
    bpm_df = bpm(df, _mini_team(), _mini_league())
    valid = bpm_df["BPM"].dropna()
    mp_valid = df.loc[valid.index, "MIN"]
    weighted_avg = (valid * mp_valid).sum() / mp_valid.sum()
    assert abs(weighted_avg) < 0.5, f"BPM league avg = {weighted_avg:.3f}"


# ── VORP ────────────────────────────────────────────────────────────────────────

def test_vorp_positive_for_above_replacement():
    """A player with BPM > -2.0 should have positive VORP."""
    df = pd.DataFrame([{
        "PLAYER_ID": 1, "PLAYER_NAME": "Good Player",
        "TEAM_ID": 1, "BPM": 3.0, "MIN": 2000.0, "GP": 75,
    }])
    v = vorp(df)
    assert v.iloc[0] > 0


def test_vorp_zero_at_replacement_level():
    """A player at exactly replacement level (BPM = -2.0) has VORP = 0."""
    df = pd.DataFrame([{
        "PLAYER_ID": 1, "PLAYER_NAME": "Replacement",
        "TEAM_ID": 1, "BPM": -2.0, "MIN": 2000.0, "GP": 75,
    }])
    v = vorp(df)
    assert abs(v.iloc[0]) < 0.001


# ── Crosswalk ────────────────────────────────────────────────────────────────

def test_normalize_name_basic():
    assert normalize_name("LeBron James") == "lebron james"
    assert normalize_name("Kevin Durant Jr.") == "kevin durant"
    assert normalize_name("Nikola Jokić") == "nikola jokic"
    assert normalize_name("Marcus Morris Sr.") == "marcus morris"


def test_normalize_name_punctuation():
    assert normalize_name("P.J. Tucker") == "pj tucker"
    assert normalize_name("Mo Bamba") == "mo bamba"


def test_build_crosswalk_basic():
    player_totals = pd.DataFrame([
        {"PLAYER_ID": 1, "PLAYER_NAME": "LeBron James", "TEAM_ABBREVIATION": "LAL"},
        {"PLAYER_ID": 2, "PLAYER_NAME": "Nikola Jokić", "TEAM_ABBREVIATION": "DEN"},
    ])
    xwalk = build_crosswalk(player_totals, 2025)
    assert len(xwalk) == 2
    assert "norm_name" in xwalk.columns
    assert "lebron james" in xwalk["norm_name"].values
    assert "nikola jokic" in xwalk["norm_name"].values


def test_apply_crosswalk_matches_name_season():
    player_totals = pd.DataFrame([
        {"PLAYER_ID": 1, "PLAYER_NAME": "LeBron James", "TEAM_ABBREVIATION": "LAL"},
        {"PLAYER_ID": 2, "PLAYER_NAME": "Nikola Jokić", "TEAM_ABBREVIATION": "DEN"},
    ])
    xwalk = build_crosswalk(player_totals, 2025)

    external = pd.DataFrame([
        {"player_name": "LeBron James", "season_end_year": 2025, "raptor_total": 5.2},
        {"player_name": "Nikola Jokic", "season_end_year": 2025, "raptor_total": 7.1},
        {"player_name": "Unknown Player", "season_end_year": 2025, "raptor_total": 1.0},
    ])
    result = apply_crosswalk(external, xwalk, name_col="player_name",
                              season_col="season_end_year")
    assert result.iloc[0]["player_id"] == 1
    assert result.iloc[1]["player_id"] == 2
    assert pd.isna(result.iloc[2]["player_id"])
    assert result.iloc[2]["matched_on"] == "unmatched"


# ── Power-law fit ──────────────────────────────────────────────────────────────

def test_powerlaw_fit_perfect_power_law():
    from player_rating_overview_data import powerlaw_fit
    # value = 100 * rank^-0.5 is an exact power law: R^2 ~ 1, alpha ~ 0.5
    rank = np.arange(1, 51)
    vals = 100.0 * rank ** (-0.5)
    fit = powerlaw_fit(vals, top_n=50)
    assert fit is not None
    assert abs(fit["alpha"] - 0.5) < 1e-6
    assert fit["r2"] > 0.999
    assert fit["n_points"] == 50


def test_powerlaw_fit_drops_nonpositive_tail():
    from player_rating_overview_data import powerlaw_fit
    # Only the leading positive run is fit; values <= 0 truncate the series.
    vals = np.array([5.0, 4.0, 3.0, 2.0, 1.0, 0.0, -1.0, -2.0])
    fit = powerlaw_fit(vals, top_n=50)
    assert fit is not None
    assert fit["n_points"] == 5


def test_powerlaw_fit_too_few_points_returns_none():
    from player_rating_overview_data import powerlaw_fit
    assert powerlaw_fit(np.array([3.0, 2.0, -1.0]), top_n=50) is None


# ── Regular-season vs playoff deltas ──────────────────────────────────────────

def _recompute_frame(player_ids, mins, per, ws48, bpm, obpm, dbpm):
    return pd.DataFrame({
        "PLAYER_ID": player_ids,
        "PLAYER_NAME": [f"P{i}" for i in player_ids],
        "TEAM_ABBREVIATION": ["AAA"] * len(player_ids),
        "MIN": mins,
        "PER": per, "WS48": ws48, "BPM": bpm, "OBPM": obpm, "DBPM": dbpm,
    })


def test_playoff_delta_table_basic():
    from player_rating_overview_data import _playoff_delta_table, MIN_PLAYOFF_MINUTES
    ids = [1, 2, 3, 4]
    reg = _recompute_frame(ids, [2000, 2000, 2000, 2000],
                           per=[15, 12, 18, 14], ws48=[.10, .08, .12, .09],
                           bpm=[0, -2, 4, 1], obpm=[0, -1, 2, 0], dbpm=[0, -1, 2, 1])
    # Player 1 rises across the board; player 4 has too few playoff minutes.
    po = _recompute_frame(ids, [400, 400, 400, MIN_PLAYOFF_MINUTES - 1],
                          per=[20, 11, 18, 30], ws48=[.14, .07, .12, .30],
                          bpm=[6, -3, 4, 30], obpm=[3, -2, 2, 15], dbpm=[3, -1, 2, 15])
    out = _playoff_delta_table(reg, po)

    # Player 4 is filtered out by the minutes floor.
    assert set(out["PLAYER_ID"]) == {1, 2, 3}
    # Raw delta is playoff minus regular.
    row1 = out[out["PLAYER_ID"] == 1].iloc[0]
    assert row1["PER_delta"] == pytest.approx(5.0)
    assert row1["BPM_delta"] == pytest.approx(6.0)
    # Adjusted delta removes the pool mean, so it sums to ~0 across the pool.
    assert out["PER_delta_adj"].mean() == pytest.approx(0.0, abs=1e-9)
    # Composite is a z-score average, centered at ~0 across the pool.
    assert out["SHIFT_Z"].mean() == pytest.approx(0.0, abs=1e-9)
    # Rows sorted by SHIFT_Z, risers first; player 1 rose the most.
    assert out.iloc[0]["PLAYER_ID"] == 1
    assert out["SHIFT_Z"].is_monotonic_decreasing
