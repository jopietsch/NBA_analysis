"""
Box-score math tests for nbakit.ratings.

Pure computations over synthetic DataFrames — no live API calls. These cover the
recompute engines (shooting_rates, game_score, per, win_shares, bpm, vorp) so
nbakit is self-verifying on its own formulas, independent of any consuming
project.
"""

import numpy as np
import pandas as pd

from nbakit.ratings import game_score, shooting_rates, per, win_shares, bpm, vorp


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
        # Team totals (merged columns for shooting_rates). FGA/FTA/TOV match
        # _mini_team()'s season totals per team (7000/1400/1200 for team 1,
        # 6800/1100/1050 for team 2) and MIN is realistic game-minutes
        # (82 games x 48 minutes), so USG% comes out at a sane ~0.20-0.30
        # rather than reading off an internally-inconsistent team total.
        "TEAM_FGA": [7000.0, 7000.0, 6800.0, 6800.0, 6800.0],
        "TEAM_FTA": [1400.0, 1400.0, 1100.0, 1100.0, 1100.0],
        "TEAM_TOV": [1200.0, 1200.0, 1050.0, 1050.0, 1050.0],
        "TEAM_MIN": [3936.0, 3936.0, 3936.0, 3936.0, 3936.0],
    })


def _mini_team(plus_minus=None) -> pd.DataFrame:
    """Synthetic team-totals DataFrame. MIN is game-minutes (82 games x 48).

    plus_minus, if given, is a 2-element list of season PLUS_MINUS totals for
    teams 1 and 2; it adds a PLUS_MINUS column used by the BPM team-margin
    anchor test. Omitted by default so existing BPM tests (which rely on the
    zero-margin default when PLUS_MINUS is absent) are unaffected.
    """
    d = {
        "TEAM_ID": [1, 2],
        "TEAM_NAME": ["Alpha", "Beta"],
        "GP": [82, 82],
        "MIN": [3936.0, 3936.0],
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
    }
    if plus_minus is not None:
        d["PLUS_MINUS"] = plus_minus
    return pd.DataFrame(d)


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


def test_shooting_rates_usg_pct_sane_range():
    """USG% is a fraction (~0.15-0.45), not the old ~1.0/missing-minutes-term bug."""
    df = _mini_player()
    out = shooting_rates(df)
    # Player 0 is the highest-volume player in the fixture.
    assert 0.15 < out.iloc[0]["USG_PCT"] < 0.45
    assert out["USG_PCT"].between(0.15, 0.45).all()


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


def test_defensive_win_shares_nonzero_and_varies():
    """DWS must be a live number: non-zero and different across players.

    Regression guard for the placeholder bug where team_def_rating was
    hardcoded to 100, forcing player_drtg == team_def_rating so DWS == 0 for
    everyone (Win Shares silently became offense-only).
    """
    df = _mini_player()
    ws_df = win_shares(df, _mini_team(), _mini_league())
    dws = ws_df["DWS"]
    assert dws.notna().all()
    # Not all zero.
    assert (dws.abs() > 1e-6).any(), "DWS collapsed to zero for every player"
    # Genuinely varies across players (not a single constant).
    assert dws.nunique() > 1, f"DWS is constant across players: {dws.tolist()}"


def test_defensive_win_shares_rewards_defense():
    """A high-STL/BLK/DREB player beats a low one on the same team.

    Two otherwise-identical teammates (same minutes, same offense) differ only
    in defensive counting stats; the stronger defender must earn more DWS. This
    is exactly what the old hardcoded-DRtg placeholder could never express.
    """
    team = _mini_team()
    league = _mini_league()
    base = dict(
        PLAYER_NAME="X", TEAM_ID=1, TEAM_ABBREVIATION="AAA", GP=82, MIN=2400.0,
        PTS=1200.0, FGM=450.0, FGA=1000.0, FG3M=100.0, FG3A=300.0,
        FTM=200.0, FTA=250.0, OREB=80.0, DREB=200.0, REB=280.0, AST=200.0,
        TOV=150.0, PF=150.0,
    )
    strong = {**base, "PLAYER_ID": 1, "STL": 160.0, "BLK": 120.0, "DREB": 500.0}
    weak = {**base, "PLAYER_ID": 2, "STL": 20.0, "BLK": 5.0, "DREB": 120.0}
    df = pd.DataFrame([strong, weak])
    ws_df = win_shares(df, team, league)
    strong_dws = ws_df.loc[ws_df["PLAYER_ID"] == 1, "DWS"].iloc[0]
    weak_dws = ws_df.loc[ws_df["PLAYER_ID"] == 2, "DWS"].iloc[0]
    assert strong_dws > weak_dws, (
        f"strong defender DWS={strong_dws:.3f} !> weak defender DWS={weak_dws:.3f}"
    )


def test_defensive_win_shares_uses_team_plus_minus():
    """A better team defense (larger positive PLUS_MINUS) lifts a player's DWS.

    Confirms the team defensive-rating anchor is actually wired in: holding a
    player's box line fixed, a stingier team defense should not lower his DWS.
    """
    df = _mini_player()
    league = _mini_league()
    good_def = win_shares(df, _mini_team(plus_minus=[600.0, -600.0]), league)
    bad_def = win_shares(df, _mini_team(plus_minus=[-600.0, 600.0]), league)
    # Team 1 players: the +600 (good defense) run must give >= DWS than -600.
    team1 = df["TEAM_ID"] == 1
    assert (good_def.loc[team1, "DWS"] >= bad_def.loc[team1, "DWS"]).all()
    # And the two PLUS_MINUS scenarios must actually move DWS.
    assert not np.allclose(good_def["DWS"], bad_def["DWS"])


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


def test_bpm_team_margin_anchor():
    """Each team's minutes-weighted BPM x 5 should equal its point margin per 100.

    This is BPM's defining property: a team's players sum to the team's point
    differential. team1 is given a +300 season PLUS_MINUS, team2 a -300.
    """
    df = _mini_player()
    team_df = _mini_team(plus_minus=[300.0, -300.0])
    bpm_df = bpm(df, team_df, _mini_league())

    team_idx = team_df.set_index("TEAM_ID")
    for tid, grp in bpm_df.groupby("TEAM_ID"):
        w = grp["MIN"]
        weighted_bpm = (grp["BPM"] * w).sum() / w.sum()
        trow = team_idx.loc[tid]
        team_poss = trow["FGA"] + 0.44 * trow["FTA"] - trow["OREB"] + trow["TOV"]
        margin_per100 = trow["PLUS_MINUS"] / team_poss * 100
        assert abs(weighted_bpm * 5 - margin_per100) < 0.5, (
            f"team {tid}: weighted BPM*5 = {weighted_bpm * 5:.3f}, "
            f"margin/100 = {margin_per100:.3f}"
        )


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


def test_vorp_realistic_scale_for_full_season_star():
    """A full-season star (BPM 8.0, 2800 minutes) lands in single digits.

    Locks in the fix for the ~20x inflation bug: VORP leaders should land
    around 6-9, not ~20x that.
    """
    df = pd.DataFrame([{
        "PLAYER_ID": 1, "PLAYER_NAME": "Star", "TEAM_ID": 1,
        "BPM": 8.0, "MIN": 2800.0, "GP": 82,
    }])
    v = vorp(df, games_in_season=82)
    assert 3 < v.iloc[0] < 10, f"VORP = {v.iloc[0]:.2f}"
