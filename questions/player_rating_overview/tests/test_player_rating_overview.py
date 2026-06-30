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


def test_pooled_qualified_values_stacks_and_filters(monkeypatch):
    import player_rating_overview_data as data

    def fake_load(year):
        return pd.DataFrame({
            "RAPM": [year - 2000.0, -1.0, 99.0],
            "VORP": [1.0, 2.0, 3.0],
            "QUALIFIED": [True, True, False],  # third row dropped
        })

    monkeypatch.setattr(data, "load_unified_ratings", fake_load)
    out = data.pooled_qualified_values(2014, 2016, ["RAPM", "VORP"])
    # 3 seasons * 2 qualified rows each = 6 rows; unqualified row excluded.
    assert len(out) == 6
    assert (out["QUALIFIED"] == True).all()
    assert 99.0 not in out["RAPM"].values
    assert list(out.columns).count("RAPM") == 1


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


# ── Retrodiction ──────────────────────────────────────────────────────────────

def _retro_inputs(n_teams=14, noise=0.0, seed=0):
    """Synthetic players where team skill drives both the rating and the outcome."""
    rng = np.random.default_rng(seed)
    rows, outcomes = [], []
    for t in range(n_teams):
        skill = t - n_teams / 2          # team skill, centered
        for p in range(3):               # three players per team
            rows.append({
                "PLAYER_ID": t * 10 + p,
                "TEAM_ID": t,
                "MIN": 1500,
                "GOOD": skill + rng.normal(0, noise),   # tracks skill
                "NOISE": rng.normal(0, 1),              # unrelated to skill
            })
        outcomes.append({"TEAM_ID": t, "point_diff": 2.0 * skill})
    return pd.DataFrame(rows), pd.DataFrame(outcomes)


def test_retrodiction_good_system_scores_high():
    from player_rating_overview_analysis import retrodiction_scores
    df, outcomes = _retro_inputs(noise=0.0)
    scores = retrodiction_scores(df, outcomes, ["GOOD", "NOISE"])
    # A rating that tracks team skill rebuilds the outcome almost perfectly.
    assert scores["GOOD"]["r2"] > 0.99
    assert scores["GOOD"]["cv_r2"] > 0.99
    assert scores["GOOD"]["n"] == 14


def test_retrodiction_noise_system_scores_low():
    from player_rating_overview_analysis import retrodiction_scores
    df, outcomes = _retro_inputs(noise=0.0)
    scores = retrodiction_scores(df, outcomes, ["GOOD", "NOISE"])
    # An unrelated rating cannot rebuild the outcome; CV R² is far below GOOD's.
    assert scores["NOISE"]["cv_r2"] < scores["GOOD"]["cv_r2"]
    assert scores["NOISE"]["cv_r2"] < 0.5


def test_retrodiction_skips_short_panels():
    from player_rating_overview_analysis import retrodiction_scores
    df, outcomes = _retro_inputs(n_teams=6)   # fewer than the 10-team minimum
    scores = retrodiction_scores(df, outcomes, ["GOOD"])
    assert scores == {}


def _nextseason_inputs(n_teams=14, n_rookies=2, seed=1):
    """Prior-season ratings + current rosters where prior skill drives the outcome."""
    rng = np.random.default_rng(seed)
    prior_rows, curr_rows, outcomes = [], [], []
    pid = 0
    for t in range(n_teams):
        skill = t - n_teams / 2
        for _ in range(3):
            pid += 1
            prior_rows.append({"player_id": pid, "GOOD": skill, "NOISE": rng.normal()})
            curr_rows.append({"player_id": pid, "TEAM_ID": t, "MIN": 1500})
        outcomes.append({"TEAM_ID": t, "point_diff": 2.0 * skill})
    # Rookies appear only in the current season (no prior rating).
    for r in range(n_rookies):
        pid += 1
        curr_rows.append({"player_id": pid, "TEAM_ID": r, "MIN": 1500})
    return pd.DataFrame(prior_rows), pd.DataFrame(curr_rows), pd.DataFrame(outcomes)


def test_next_season_retrodiction_predicts_from_prior():
    from player_rating_overview_analysis import next_season_retrodiction
    prior, curr, outcomes = _nextseason_inputs(n_rookies=0)
    scores = next_season_retrodiction(prior, curr, outcomes, ["GOOD", "NOISE"])
    # Prior skill perfectly sets the current outcome, so GOOD forecasts it.
    assert scores["GOOD"]["r2"] > 0.99
    assert scores["NOISE"]["r2"] < scores["GOOD"]["r2"]
    assert scores["GOOD"]["coverage"] == pytest.approx(1.0)


def test_next_season_retrodiction_coverage_below_one_with_rookies():
    from player_rating_overview_analysis import next_season_retrodiction
    prior, curr, outcomes = _nextseason_inputs(n_rookies=4)
    scores = next_season_retrodiction(prior, curr, outcomes, ["GOOD"])
    # Rookies have no prior rating, so coverage drops below 1.
    assert 0.0 < scores["GOOD"]["coverage"] < 1.0


def _panel_season(skill_to_outcome=2.0, seed=0):
    """One synthetic season with stable player_ids so seasons chain.

    Player ids and team skill are the same every season, so a prior season's
    rating maps onto the next season's roster (the forecast test needs the same
    players across years). GOOD tracks team skill; NOISE is unrelated.
    """
    rng = np.random.default_rng(seed)
    rows, outs = [], []
    for t in range(14):
        skill = t - 7
        for p in range(3):
            rows.append({"player_id": t * 10 + p, "TEAM_ID": t, "MIN": 1500,
                         "GOOD": skill + rng.normal(0, 0.01), "NOISE": rng.normal()})
        outs.append({"TEAM_ID": t, "point_diff": skill_to_outcome * skill})
    return pd.DataFrame(rows), pd.DataFrame(outs)


def test_panel_retrodiction_pools_describe_and_forecast(monkeypatch):
    import player_rating_overview_analysis as A
    seasons = {y: _panel_season(seed=y) for y in (2021, 2022, 2023)}
    monkeypatch.setattr(A, "load_unified_ratings", lambda y, **k: seasons[y][0])
    monkeypatch.setattr(A, "load_team_outcomes", lambda y: seasons[y][1])

    panel = A.panel_retrodiction(2021, 2023, ["GOOD", "NOISE"])

    # Three describe seasons, two forecast pairs.
    assert panel["seasons"] == [2021, 2022, 2023]
    assert panel["pairs"] == [(2021, 2022), (2022, 2023)]
    assert len(panel["describe"]["GOOD"]) == 3
    assert len(panel["forecast"]["GOOD"]) == 2
    # A rating that tracks team skill both describes and forecasts well; an
    # unrelated rating forecasts worse.
    assert np.mean(panel["describe"]["GOOD"]) > 0.9
    assert np.mean(panel["forecast"]["GOOD"]) > 0.9
    assert np.mean(panel["forecast"]["GOOD"]) > np.mean(panel["forecast"]["NOISE"])


def _stability_season(seed, stable_skill):
    """One season: STABLE equals a fixed per-player skill, NOISE is random."""
    rng = np.random.default_rng(seed)
    return pd.DataFrame([
        {"player_id": pid, "MIN": 1500, "QUALIFIED": True,
         "STABLE": float(stable_skill[pid]), "NOISE": rng.normal()}
        for pid in range(20)
    ])


def test_rating_stability_persistent_vs_noise(monkeypatch):
    import player_rating_overview_analysis as A
    skill = np.arange(20, dtype=float)  # identical every season
    seasons = {y: _stability_season(y, skill) for y in (2021, 2022, 2023)}
    monkeypatch.setattr(A, "load_unified_ratings", lambda y, **k: seasons[y])

    st = A.rating_stability(2021, 2023, ["STABLE", "NOISE"], top_n=5)

    assert st["pairs"] == [(2021, 2022), (2022, 2023)]
    # A rating fixed to player skill repeats exactly; a random one does not.
    assert np.mean(st["corr"]["STABLE"]) > 0.99
    assert np.mean(st["corr"]["STABLE"]) > np.mean(st["corr"]["NOISE"])
    # The same five players stay in the top five every year for STABLE.
    assert np.mean(st["retention"]["STABLE"]) == pytest.approx(1.0)
    assert np.mean(st["retention"]["STABLE"]) > np.mean(st["retention"]["NOISE"])


# ── compute_rapm column rename / orchestration ────────────────────────────────

def _mini_possessions(n: int = 200, rng=None) -> pd.DataFrame:
    """Synthetic possession table as emitted by reconstruct_possessions.

    Uses off_player_1..5 / def_player_1..5 column names (pre-rename),
    which is what compute_rapm receives before bridging to rapm().
    """
    if rng is None:
        rng = np.random.default_rng(0)
    # Two lineups (10 distinct players total per "team pair")
    off_ids = [[101, 102, 103, 104, 105]] * (n // 2) + [[106, 107, 108, 109, 110]] * (n // 2)
    def_ids = [[106, 107, 108, 109, 110]] * (n // 2) + [[101, 102, 103, 104, 105]] * (n // 2)
    records = []
    for off, dfd in zip(off_ids, def_ids):
        records.append({
            "game_id": "0000000001",
            "period": 1,
            "off_team_id": 1,
            "off_player_1": off[0], "off_player_2": off[1], "off_player_3": off[2],
            "off_player_4": off[3], "off_player_5": off[4],
            "def_player_1": dfd[0], "def_player_2": dfd[1], "def_player_3": dfd[2],
            "def_player_4": dfd[3], "def_player_5": dfd[4],
            "points": int(rng.choice([0, 2, 3], p=[0.6, 0.3, 0.1])),
            "possession": 1,
        })
    return pd.DataFrame(records)


def test_compute_rapm_column_rename_and_output(monkeypatch, tmp_path):
    """compute_rapm renames off_player_1..5/def_player_1..5→off1..5/def1..5
    before calling rapm(), and returns RAPM/O_RAPM/D_RAPM indexed by player_id.
    Uses a synthetic possession table; no network calls.
    """
    import player_rating_overview_data as D
    from nbakit.data import REGULAR_SEASON

    poss = _mini_possessions()

    # Monkeypatch: supply fake game logs, fake cached PBP, and redirect cache.
    fake_logs = pd.DataFrame({"GAME_ID": ["0000000001"]})
    monkeypatch.setattr(D, "fetch_game_logs", lambda *a, **k: fake_logs)
    monkeypatch.setattr(D, "CACHE_DIR", str(tmp_path))

    # Write the synthetic PBP as a stub (won't actually be read since we also
    # patch reconstruct_possessions — but the file must exist for the glob).
    pbp_stub_path = tmp_path / "pbp_v3_0000000001.csv"
    poss.to_csv(pbp_stub_path, index=False)  # file presence triggers pickup

    # Patch reconstruct_possessions to return our synthetic possession table.
    monkeypatch.setattr(D, "reconstruct_possessions", lambda pbp, **k: poss)

    result = D.compute_rapm(2025, REGULAR_SEASON)

    assert not result.empty, "compute_rapm returned empty on a non-empty possession table"
    for col in ["player_id", "RAPM", "O_RAPM", "D_RAPM"]:
        assert col in result.columns, f"Missing column: {col}"

    # All 10 synthetic players should appear.
    expected_pids = {101, 102, 103, 104, 105, 106, 107, 108, 109, 110}
    assert expected_pids == set(result["player_id"].tolist())

    # RAPM = O_RAPM + D_RAPM (sign convention)
    diff = (result["RAPM"] - result["O_RAPM"] - result["D_RAPM"]).abs()
    assert diff.max() < 0.01, "RAPM != O_RAPM + D_RAPM"


def test_compute_rapm_no_pbp_returns_empty(monkeypatch, tmp_path):
    """compute_rapm returns an empty DataFrame (correct columns) when no PBP cached."""
    import player_rating_overview_data as D

    fake_logs = pd.DataFrame({"GAME_ID": ["0022400001", "0022400002"]})
    monkeypatch.setattr(D, "fetch_game_logs", lambda *a, **k: fake_logs)
    monkeypatch.setattr(D, "CACHE_DIR", str(tmp_path))  # empty dir, no pbp files

    result = D.compute_rapm(2025)

    assert result.empty
    for col in ["player_id", "RAPM", "O_RAPM", "D_RAPM"]:
        assert col in result.columns


# ── pool_possessions ──────────────────────────────────────────────────────────

def _mini_possessions_poolable(n: int = 10, seed: int = 0) -> pd.DataFrame:
    """Synthetic possession table with renamed columns (off1..5/def1..5/points).

    This is the format _season_possessions emits — already renamed, ready to
    pool.
    """
    rng = np.random.default_rng(seed)
    off_ids = [101, 102, 103, 104, 105]
    def_ids = [106, 107, 108, 109, 110]
    records = []
    for _ in range(n):
        rec = {f"off{i + 1}": off_ids[i] for i in range(5)}
        rec.update({f"def{i + 1}": def_ids[i] for i in range(5)})
        rec["points"] = int(rng.choice([0, 2, 3], p=[0.6, 0.3, 0.1]))
        records.append(rec)
    return pd.DataFrame(records)


def test_pool_possessions_three_seasons_schema_and_weights(monkeypatch):
    """pool_possessions concatenates 3 seasons, attaches correct weights, right schema."""
    import player_rating_overview_data as D

    frames = {
        2023: _mini_possessions_poolable(10, seed=0),
        2024: _mini_possessions_poolable(10, seed=1),
        2025: _mini_possessions_poolable(10, seed=2),
    }
    monkeypatch.setattr(D, "_season_possessions", lambda yr, *a, **k: frames.get(yr, pd.DataFrame(columns=D._POSS_COLS)))

    result = D.pool_possessions(2025, n_seasons=3)

    # Schema: off1..off5, def1..def5, points, weight
    expected_cols = [f"off{i}" for i in range(1, 6)] + [f"def{i}" for i in range(1, 6)] + ["points", "weight"]
    for col in expected_cols:
        assert col in result.columns, f"Missing column: {col}"

    # 3 seasons x 10 rows each = 30 rows
    assert len(result) == 30

    # Weights: 2023 -> 1/3, 2024 -> 2/3, 2025 -> 1.0
    unique_weights = sorted(result["weight"].unique())
    assert len(unique_weights) == 3
    assert unique_weights[0] == pytest.approx(1 / 3)
    assert unique_weights[1] == pytest.approx(2 / 3)
    assert unique_weights[2] == pytest.approx(1.0)

    # Each season contributes exactly 10 rows at its weight
    assert np.isclose(result["weight"], 1 / 3).sum() == 10
    assert np.isclose(result["weight"], 2 / 3).sum() == 10
    assert np.isclose(result["weight"], 1.0).sum() == 10


def test_pool_possessions_two_seasons_weights(monkeypatch):
    """pool_possessions with n_seasons=2 uses weights 0.5 / 1.0."""
    import player_rating_overview_data as D

    frames = {
        2024: _mini_possessions_poolable(8, seed=3),
        2025: _mini_possessions_poolable(8, seed=4),
    }
    monkeypatch.setattr(D, "_season_possessions", lambda yr, *a, **k: frames.get(yr, pd.DataFrame(columns=D._POSS_COLS)))

    result = D.pool_possessions(2025, n_seasons=2)

    assert len(result) == 16
    unique_weights = sorted(result["weight"].unique())
    assert unique_weights[0] == pytest.approx(0.5)
    assert unique_weights[1] == pytest.approx(1.0)


def test_pool_possessions_fewer_than_two_seasons_returns_empty(monkeypatch):
    """pool_possessions returns empty DataFrame when fewer than 2 seasons have PBP."""
    import player_rating_overview_data as D

    # Only 2025 has data; 2023 and 2024 return empty
    frames = {2025: _mini_possessions_poolable(10, seed=5)}
    monkeypatch.setattr(D, "_season_possessions", lambda yr, *a, **k: frames.get(yr, pd.DataFrame(columns=D._POSS_COLS)))

    result = D.pool_possessions(2025, n_seasons=3)

    assert result.empty
    for col in [f"off{i}" for i in range(1, 6)] + [f"def{i}" for i in range(1, 6)] + ["points", "weight"]:
        assert col in result.columns


def test_pool_possessions_explicit_weights(monkeypatch):
    """pool_possessions accepts explicit weights that override the defaults."""
    import player_rating_overview_data as D

    frames = {
        2024: _mini_possessions_poolable(5, seed=6),
        2025: _mini_possessions_poolable(5, seed=7),
    }
    monkeypatch.setattr(D, "_season_possessions", lambda yr, *a, **k: frames.get(yr, pd.DataFrame(columns=D._POSS_COLS)))

    result = D.pool_possessions(2025, n_seasons=2, weights=[0.3, 0.9])

    assert len(result) == 10
    unique_weights = sorted(result["weight"].unique())
    assert unique_weights[0] == pytest.approx(0.3)
    assert unique_weights[1] == pytest.approx(0.9)


def test_pool_possessions_wrong_weights_length_raises(monkeypatch):
    """pool_possessions raises ValueError when explicit weights length mismatches."""
    import player_rating_overview_data as D

    frames = {
        2024: _mini_possessions_poolable(5, seed=8),
        2025: _mini_possessions_poolable(5, seed=9),
    }
    monkeypatch.setattr(D, "_season_possessions", lambda yr, *a, **k: frames.get(yr, pd.DataFrame(columns=D._POSS_COLS)))

    with pytest.raises(ValueError, match="weights"):
        D.pool_possessions(2025, n_seasons=2, weights=[0.5])
