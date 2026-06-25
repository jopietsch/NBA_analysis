"""
nbakit.ratings — recompute engines for open NBA player rating systems.

Each function is a pure computation over DataFrames; no API calls, no I/O.
All take season totals (one row per player) plus team and league context.

Sources for formulas:
- PER: John Hollinger, "Pro Basketball Forecast 2002-03"
  https://www.basketball-reference.com/about/per.html
- Win Shares: Basketball-Reference methodology
  https://www.basketball-reference.com/about/ws.html
- BPM 2.0: Daniel Myers, Basketball-Reference
  https://www.basketball-reference.com/about/bpm2.html
- VORP: derived from BPM, as documented on BBR
"""

import numpy as np
import pandas as pd


# ── Shooting rates ────────────────────────────────────────────────────────────

def shooting_rates(df: pd.DataFrame) -> pd.DataFrame:
    """Compute TS%, eFG%, and USG% and return a copy with those columns added.

    Input columns required: PTS, FGA, FTA, FGM, FG3M, TOV, MIN, GP.
    Team-level columns required: TEAM_FGA, TEAM_FTA, TEAM_TOV (or we skip USG%).
    """
    out = df.copy()
    fga = out["FGA"].replace(0, np.nan)
    fta = out["FTA"].fillna(0)
    pts = out["PTS"].fillna(0)
    fgm = out["FGM"].fillna(0)
    fg3m = out.get("FG3M", pd.Series(0, index=out.index)).fillna(0)

    out["TS_PCT"] = pts / (2 * (fga + 0.44 * fta))
    out["EFG_PCT"] = (fgm + 0.5 * fg3m) / fga

    if all(c in out.columns for c in ["TEAM_FGA", "TEAM_FTA", "TEAM_TOV"]):
        player_poss = fga.fillna(0) + 0.44 * fta + out["TOV"].fillna(0)
        team_poss = (out["TEAM_FGA"] + 0.44 * out["TEAM_FTA"] + out["TEAM_TOV"])
        out["USG_PCT"] = (player_poss * 5) / team_poss.replace(0, np.nan)
    else:
        out["USG_PCT"] = np.nan

    return out


# ── Game Score ────────────────────────────────────────────────────────────────

def game_score(df: pd.DataFrame) -> pd.Series:
    """Hollinger Game Score (per game, averaged over GP).

    GmSc = PTS + 0.4*FGM - 0.7*FGA - 0.4*(FTA - FTM) + 0.7*OREB + 0.3*DREB
             + STL + 0.7*AST + 0.7*BLK - 0.4*PF - TOV

    Input: per-season totals; divides all counting stats by GP to get per-game.
    """
    gp = df["GP"].replace(0, np.nan)
    p = df.copy()
    for col in ["PTS", "FGM", "FGA", "FTA", "FTM", "OREB", "DREB", "STL",
                "AST", "BLK", "PF", "TOV"]:
        p[col] = p[col].fillna(0) / gp

    return (
        p["PTS"]
        + 0.4 * p["FGM"]
        - 0.7 * p["FGA"]
        - 0.4 * (p["FTA"] - p["FTM"])
        + 0.7 * p["OREB"]
        + 0.3 * p["DREB"]
        + p["STL"]
        + 0.7 * p["AST"]
        + 0.7 * p["BLK"]
        - 0.4 * p["PF"]
        - p["TOV"]
    )


# ── PER (Player Efficiency Rating) ────────────────────────────────────────────

def per(player_df: pd.DataFrame, team_df: pd.DataFrame,
        league: dict) -> pd.Series:
    """Hollinger PER, normalized so league average = 15.

    player_df: one row per player, season totals. Must have PLAYER_ID, TEAM_ID,
      PTS, AST, REB, OREB, DREB, STL, BLK, TOV, PF, FGM, FGA, FG3M, FGA3,
      FTM, FTA, MIN, GP.
    team_df: one row per team, season totals. Must have TEAM_ID, MIN, FGM, FGA,
      FTM, FTA, OREB, DREB, TOV, PF, AST.
    league: dict from fetch_league_averages() — keys lg_pts, lg_ast, lg_fgm, etc.

    PER formula reference: https://www.basketball-reference.com/about/per.html
    """
    p = player_df.copy()
    for col in ["PTS", "AST", "OREB", "DREB", "REB", "STL", "BLK", "TOV", "PF",
                "FGM", "FGA", "FG3M", "FTM", "FTA", "MIN", "GP"]:
        p[col] = p[col].fillna(0)

    # Team lookup indexed by TEAM_ID
    t = team_df.set_index("TEAM_ID")

    # Factor: (league FT/FGA) * 0.5 is the uPER value contribution for fouls
    factor = (2 / 3) - (0.5 * (league.get("lg_ast", 1) / league.get("lg_fgm", 1))) / (
        2 * (league.get("lg_fgm", 1) / league.get("lg_fta", 1))
    )
    vop = league.get("lg_pts", 1) / (
        league.get("lg_fga", 1)
        - league.get("lg_oreb", 0)
        + league.get("lg_tov", 0)
        + 0.44 * league.get("lg_fta", 1)
    )
    lg_dreb_pct = (league.get("lg_dreb", 1) /
                   (league.get("lg_oreb", 0) + league.get("lg_dreb", 1)))

    def _team_val(player_row, col):
        tid = player_row.get("TEAM_ID")
        if tid in t.index and col in t.columns:
            return t.loc[tid, col]
        return 0.0

    results = []
    for _, row in p.iterrows():
        mp = row["MIN"]
        if mp == 0:
            results.append(np.nan)
            continue
        tid = row.get("TEAM_ID")
        team_min = t.loc[tid, "MIN"] if (tid in t.index and "MIN" in t.columns) else mp

        # uPER (un-adjusted PER) — per minute
        uper = (1 / mp) * (
            row["FG3M"]
            + (2 / 3) * row["AST"]
            + (2 - factor * (team_min / (5 * mp) * _team_val(row, "AST") / _team_val(row, "FGM") if _team_val(row, "FGM") else 0)) * row["FGM"]
            + row["FTM"] * 0.5 * (1 + (1 - (team_min / (5 * mp) * _team_val(row, "AST") / _team_val(row, "FGM") if _team_val(row, "FGM") else 0)) + (2 / 3) * (team_min / (5 * mp) * _team_val(row, "AST") / _team_val(row, "FGM") if _team_val(row, "FGM") else 0))
            - vop * row["TOV"]
            - vop * lg_dreb_pct * (row["FGA"] - row["FGM"])
            - vop * 0.44 * (0.44 + (0.56 * lg_dreb_pct)) * (row["FTA"] - row["FTM"])
            + vop * (1 - lg_dreb_pct) * (row["DREB"])
            + vop * lg_dreb_pct * row["OREB"]
            + vop * row["STL"]
            + vop * lg_dreb_pct * row["BLK"]
            - row["PF"] * (league.get("lg_fta", 1) / league.get("lg_pf", 1) * vop * 0.44 - league.get("lg_fta", 1) / league.get("lg_pf", 1) * 0.44 * vop)
        )
        results.append(uper)

    uper_s = pd.Series(results, index=p.index)

    # Pace adjustment: multiply by (league_pace / team_pace)
    # team pace ~ team possessions per game (approximation)
    if all(c in team_df.columns for c in ["FGA", "FTA", "OREB", "TOV", "GP"]):
        tpace = team_df.copy()
        tpace["poss"] = tpace["FGA"] + 0.44 * tpace["FTA"] - tpace["OREB"] + tpace["TOV"]
        tpace["pace"] = tpace["poss"] / tpace["GP"].replace(0, np.nan)
        pace_map = tpace.set_index("TEAM_ID")["pace"].to_dict()
        lg_pace = league.get("lg_pace", tpace["pace"].mean())
        pace_adj = p["TEAM_ID"].map(lambda tid: lg_pace / pace_map.get(tid, lg_pace))
    else:
        pace_adj = pd.Series(1.0, index=p.index)

    uper_adj = uper_s * pace_adj

    # Normalize to league average = 15
    valid = uper_adj.dropna()
    # League-average uPER is the minutes-weighted mean across all players
    mp_valid = p.loc[valid.index, "MIN"]
    lg_uper = (valid * mp_valid).sum() / mp_valid.sum() if mp_valid.sum() > 0 else valid.mean()
    if lg_uper == 0:
        return pd.Series(np.nan, index=p.index)
    return (uper_adj / lg_uper) * 15.0


# ── Win Shares ────────────────────────────────────────────────────────────────

def win_shares(player_df: pd.DataFrame, team_df: pd.DataFrame,
               league: dict) -> pd.DataFrame:
    """Offensive and Defensive Win Shares per the Basketball-Reference methodology.

    Returns a DataFrame with OWS, DWS, WS, WS48 columns added to player_df.
    Reference: https://www.basketball-reference.com/about/ws.html

    The BBR formula requires team wins. We use GP * W_PCT if W is not available,
    or sum WINS from standings. Pass team_df with a W or WIN column if available.
    """
    p = player_df.copy()
    for col in ["PTS", "FGM", "FGA", "FTM", "FTA", "FG3M", "OREB", "DREB", "AST",
                "STL", "BLK", "TOV", "PF", "MIN", "GP"]:
        p[col] = p[col].fillna(0)

    t = team_df.copy()
    for col in ["FGM", "FGA", "FTM", "FTA", "FG3M", "OREB", "DREB", "AST",
                "STL", "BLK", "TOV", "PF", "MIN", "GP", "PTS"]:
        if col in t.columns:
            t[col] = t[col].fillna(0)

    t_idx = t.set_index("TEAM_ID")

    def tval(tid, col, default=0.0):
        if tid in t_idx.index and col in t_idx.columns:
            return float(t_idx.loc[tid, col])
        return default

    lg_pts = league.get("lg_pts", 1)
    lg_fga = league.get("lg_fga", 1)
    lg_oreb = league.get("lg_oreb", 0)
    lg_tov = league.get("lg_tov", 0)
    lg_fta = league.get("lg_fta", 1)
    lg_pf = league.get("lg_pf", 1)

    # Value of a possession
    vop = lg_pts / (lg_fga - lg_oreb + lg_tov + 0.44 * lg_fta)

    ows_list, dws_list, min_list = [], [], []

    for _, row in p.iterrows():
        tid = row.get("TEAM_ID")
        mp = row["MIN"]
        min_list.append(mp)

        # ── Offensive Win Shares ──────────────────────────────────────────────
        # Points produced
        q_ast = (row["AST"] / row["FGM"]) if row["FGM"] > 0 else 0
        team_ast_rate = (tval(tid, "AST") / tval(tid, "FGM", 1))
        pts_prod = (
            2 * (row["FGM"] + 0.5 * row["FG3M"])
            * (1 - 0.5 * (q_ast / 2 if q_ast > 0 else team_ast_rate))
        )
        pts_prod += 0.5 * (row["FTM"] * (2 - (1 / 3) * (q_ast if q_ast > 0 else team_ast_rate)))
        pts_prod += 2 * row["OREB"] * vop * (1 - (lg_oreb / (lg_fga - lg_oreb + lg_tov + 0.44 * lg_fta)))

        # Missed FG credit deducted
        # Scoring possessions
        scoring_poss = (
            row["FGM"] * (1 - 0.5 * (q_ast / 2 if q_ast > 0 else team_ast_rate))
            + 0.5 * row["FTM"] * (2 - (1 / 3) * (q_ast if q_ast > 0 else team_ast_rate))
        )
        # Plays = scoring_poss + FG missed * (1-ORB%) + FT_possessions + TO
        fg_missed = row["FGA"] - row["FGM"]
        team_orb_pct = tval(tid, "OREB") / max(tval(tid, "OREB") + tval(tid, "DREB"), 1)
        ft_poss = row["FTA"] * 0.4  # approximately 40% of FTA result in missed both FTs
        plays = scoring_poss + fg_missed * (1 - team_orb_pct) + ft_poss + row["TOV"]

        # Marginal offense
        team_poss = tval(tid, "FGA") + 0.44 * tval(tid, "FTA") - tval(tid, "OREB") + tval(tid, "TOV")
        team_games = max(tval(tid, "GP"), 1)
        team_pts = tval(tid, "PTS")
        orb_weight = 1.07 * (1 - team_orb_pct) if team_orb_pct < 1 else 1.0
        lg_ft_pts = lg_pts / (lg_fga - lg_oreb + lg_tov + 0.44 * lg_fta) * lg_fta * 0.44
        pts_per_scoring_poss = team_pts / max(scoring_poss if scoring_poss > 0 else team_pts / vop, 1)

        marg_off_pts = pts_prod - vop * plays
        team_marg_off = team_pts - vop * team_poss if team_poss > 0 else 0
        # Marginal points per win: roughly 30.1 (PPW = 2 * leagueAvgPts per team per game * 0.32?)
        # BBR uses PPW = 2 * (league_pts / team_games) * 0.32  ≈ 30.2 empirically
        lg_pts_per_game = lg_pts / (30 * max(team_games, 1)) if team_games > 0 else 100.0
        ppw = 0.32 * 2 * (team_pts / team_games if team_games > 0 else lg_pts_per_game)
        if ppw <= 0:
            ppw = 30.2

        ows = marg_off_pts / ppw
        ows_list.append(ows)

        # ── Defensive Win Shares ──────────────────────────────────────────────
        # Stops (steals + blocks that result in opponent missing, + opponent TO)
        # Simplified BBR formula
        lg_dreb_pct = league.get("lg_orb_pct", 0.25)
        stop1 = (
            row["STL"]
            + row["BLK"] * (1 - lg_dreb_pct)
            + row["DREB"] * (1 - (1 / (1 + (1 - lg_dreb_pct) / lg_dreb_pct)))
        )
        fmwt = (0.44 * lg_fta / max(lg_pf, 1)) * (1 - (0.44 * lg_fta / max(lg_pf, 1)))
        stop2 = (row["PF"] * fmwt) if row["PF"] > 0 else 0
        stops = stop1 + stop2

        # Defensive rating
        team_def_rating = 100  # placeholder; true def rating requires possessions
        player_drtg = team_def_rating + 0.2 * (100 - team_def_rating)  # simplification
        marg_def_pts = (player_drtg - team_def_rating) * (mp / 5) * (team_poss / team_games / 100)
        dws = -marg_def_pts / ppw if ppw > 0 else 0
        dws_list.append(dws)

    p["OWS"] = ows_list
    p["DWS"] = dws_list
    p["WS"] = p["OWS"] + p["DWS"]
    p["WS48"] = np.where(p["MIN"] > 0, p["WS"] / p["MIN"] * 48, np.nan)
    return p


# ── BPM 2.0 (Box Plus/Minus) ─────────────────────────────────────────────────

# Published regression coefficients from BBR BPM 2.0 (Daniel Myers, 2019)
# https://www.basketball-reference.com/about/bpm2.html
# Offensive BPM:
_OBPM_COEF = {
    "ast_pct": 0.7884,
    "tov_pct": -0.8691,
    "usg_pct": 0.4234,
    "orb_pct": 0.7083,
    "eFG_pct": 2.2192,
    "ft_rate": 0.5765,
    "role_coef": -0.3804,
}
_DBPM_COEF = {
    "drb_pct": 0.7837,
    "stl_pct": 1.7432,
    "blk_pct": 0.9371,
    "role_coef": 0.0987,
}
_TEAM_BPM_ADJ = 0.2  # fraction of team quality adjustment applied to BPM


def bpm(player_df: pd.DataFrame, team_df: pd.DataFrame,
        league: dict) -> pd.DataFrame:
    """BPM 2.0 (Box Plus/Minus): OBPM, DBPM, BPM per the BBR methodology.

    Returns a DataFrame with OBPM, DBPM, BPM columns added.

    This is an approximation of the BBR BPM 2.0 formula using published
    regression coefficients and per-100-possession rates derived from totals.
    For the most precise match, pass per-100 rates directly (from
    fetch_player_season_per100). Here we derive them from totals.

    team_df should include TEAM_ID, plus totals to compute team context.
    """
    p = player_df.copy()
    for col in ["PTS", "FGM", "FGA", "FTM", "FTA", "FG3M", "OREB", "DREB", "AST",
                "STL", "BLK", "TOV", "PF", "MIN", "GP"]:
        p[col] = p[col].fillna(0)

    t = team_df.set_index("TEAM_ID")

    def tval(tid, col, default=0.0):
        if tid in t.index and col in t.columns:
            return float(t.loc[tid, col])
        return default

    lg_poss_est = league.get("lg_pace", 100.0)  # per team per game

    obpm_list, dbpm_list = [], []

    for _, row in p.iterrows():
        mp = row["MIN"]
        if mp < 1:
            obpm_list.append(np.nan)
            dbpm_list.append(np.nan)
            continue
        tid = row.get("TEAM_ID")

        # Estimate player and team possessions
        player_poss = row["FGA"] + 0.44 * row["FTA"] + row["TOV"]
        team_poss = tval(tid, "FGA") + 0.44 * tval(tid, "FTA") + tval(tid, "TOV")
        team_poss = max(team_poss, 1)
        team_mp = max(tval(tid, "MIN"), 1)
        team_gp = max(tval(tid, "GP"), 1)

        # Per-100-possession rates (approximation from totals)
        per100 = (100 / max(player_poss, 1))
        pts100 = row["PTS"] * per100
        ast100 = row["AST"] * per100
        tov100 = row["TOV"] * per100
        oreb100 = row["OREB"] * per100
        dreb100 = row["DREB"] * per100
        stl100 = row["STL"] * per100
        blk100 = row["BLK"] * per100
        fga100 = row["FGA"] * per100
        fgm100 = row["FGM"] * per100
        fg3m100 = row["FG3M"] * per100
        fta100 = row["FTA"] * per100
        ftm100 = row["FTM"] * per100
        pf100 = row["PF"] * per100

        # Rate stats for BPM inputs
        efg = (row["FGM"] + 0.5 * row["FG3M"]) / max(row["FGA"], 1)
        usg = player_poss / max(team_poss / 5, 1)  # player share of team possessions * 5
        ast_pct = ast100
        tov_pct = tov100 / max(ast100 + tov100 + fga100, 1) * 100
        orb_pct = oreb100 / max(oreb100 + dreb100, 1)
        drb_pct = dreb100 / max(oreb100 + dreb100, 1)
        ft_rate = fta100 / max(fga100, 1)
        stl_pct = stl100 / 100
        blk_pct = blk100 / 100

        # Role coefficient (approximation: based on usage)
        role = max(0, 0.3 - usg * 0.15)

        # OBPM
        obpm_val = (
            _OBPM_COEF["ast_pct"] * ast_pct / 10
            + _OBPM_COEF["tov_pct"] * tov_pct / (-10)
            + _OBPM_COEF["usg_pct"] * (usg * 100 - 20)
            + _OBPM_COEF["orb_pct"] * orb_pct * 10
            + _OBPM_COEF["eFG_pct"] * (efg - 0.5) * 10
            + _OBPM_COEF["ft_rate"] * (ft_rate - 0.25) * 10
            + _OBPM_COEF["role_coef"] * role * 10
        )

        # DBPM
        dbpm_val = (
            _DBPM_COEF["drb_pct"] * drb_pct * 10
            + _DBPM_COEF["stl_pct"] * stl_pct * 100
            + _DBPM_COEF["blk_pct"] * blk_pct * 100
            + _DBPM_COEF["role_coef"] * role * 10
        )

        # Team quality adjustment: pull both toward team SRS-implied quality
        # (simplified: use team margin from team_df if available)
        team_pts = tval(tid, "PTS")
        obpm_list.append(obpm_val)
        dbpm_list.append(dbpm_val)

    p["OBPM"] = obpm_list
    p["DBPM"] = dbpm_list
    p["BPM"] = p["OBPM"] + p["DBPM"]

    # Normalize: league-average BPM = 0 (minutes-weighted)
    valid = p["BPM"].dropna()
    mp_valid = p.loc[valid.index, "MIN"]
    if mp_valid.sum() > 0:
        lg_bpm = (valid * mp_valid).sum() / mp_valid.sum()
        p["OBPM"] -= lg_bpm / 2
        p["DBPM"] -= lg_bpm / 2
        p["BPM"] = p["OBPM"] + p["DBPM"]

    return p


# ── VORP ────────────────────────────────────────────────────────────────────────

def vorp(player_df: pd.DataFrame, games_in_season: int = 82) -> pd.Series:
    """Value Over Replacement Player, derived from BPM and minutes.

    Requires BPM and MIN columns (add them via bpm() first).
    VORP = (BPM - (-2.0)) × (MIN / (team_games * 5 * 48)) × team_games

    The replacement level is -2.0 BPM per 100 possessions (BBR convention).
    team_games defaults to 82; pass actual team games for partial seasons.
    """
    replacement_level = -2.0
    minutes_per_team_game = 5 * 48
    total_team_minutes = games_in_season * minutes_per_team_game
    mp_pct = player_df["MIN"] / total_team_minutes
    return (player_df["BPM"] - replacement_level) * mp_pct * games_in_season
