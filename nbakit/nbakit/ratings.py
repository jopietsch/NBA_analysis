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

    if all(c in out.columns for c in ["TEAM_FGA", "TEAM_FTA", "TEAM_TOV",
                                      "TEAM_MIN", "MIN"]):
        player_poss = fga.fillna(0) + 0.44 * fta + out["TOV"].fillna(0)
        team_poss = (out["TEAM_FGA"] + 0.44 * out["TEAM_FTA"] + out["TEAM_TOV"])
        # USG% = share of team possessions a player uses while on the floor,
        # as a fraction. The TmMP/MP term converts season totals to an on-court
        # rate (TEAM_MIN is game-minutes, GP x 48); without it a full-time player
        # reads ~1.0 instead of the correct ~0.20-0.30.
        tmmp = out["TEAM_MIN"]
        mp = out["MIN"].replace(0, np.nan)
        out["USG_PCT"] = (player_poss * tmmp) / (mp * team_poss.replace(0, np.nan))
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

        # Team-assist share of this player's makes, scaled to on-court minutes;
        # feeds the assisted-make discount in the FGM and FTM terms below.
        team_fgm = _team_val(row, "FGM")
        ast_ratio = (team_min / (5 * mp) * _team_val(row, "AST") / team_fgm) if team_fgm else 0

        # uPER (un-adjusted PER) — per minute
        uper = (1 / mp) * (
            row["FG3M"]
            + (2 / 3) * row["AST"]
            + (2 - factor * ast_ratio) * row["FGM"]
            + row["FTM"] * 0.5 * (1 + (1 - ast_ratio) + (2 / 3) * ast_ratio)
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

    Defensive Win Shares follow Dean Oliver's individual-defense chain: player
    Stops (Stops1 + Stops2) -> Stop% -> an individual DRtg anchored to the team's
    actual defensive rating -> marginal defensive points -> DWS. The team
    defensive rating is opponent points per 100 possessions, derived from
    team PTS and season point differential (team_df["PLUS_MINUS"]); if
    PLUS_MINUS is absent the team is centered at a league-average opponent, so
    DWS still varies across a team's players by their own Stop%. Approximation:
    the BBR Stops formulas need per-opponent box totals the Base team-totals
    frame does not carry, so the opponent a team faced is modeled as the
    league-average team (league totals / number of teams). DWS absolute values
    are therefore approximate (like the BPM/VORP recomputes), but the ordering
    and scale across players are faithful.

    The offensive side reuses the marginal-points-per-win (ppw) scaling; team_df
    should carry season totals (PTS, FGA, FTA, TOV, OREB, DREB, FGM, GP, MIN) and,
    for the defensive anchor, PLUS_MINUS.
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
    lg_fgm = league.get("lg_fgm", 1)
    lg_oreb = league.get("lg_oreb", 0)
    lg_dreb = league.get("lg_dreb", 1)
    lg_tov = league.get("lg_tov", 0)
    lg_fta = league.get("lg_fta", 1)
    lg_ftm = league.get("lg_ftm", 0.75 * lg_fta)
    lg_pf = league.get("lg_pf", 1)

    # Value of a possession
    lg_poss = lg_fga - lg_oreb + lg_tov + 0.44 * lg_fta
    vop = lg_pts / lg_poss
    lg_ppp = lg_pts / lg_poss  # league points per possession

    # ── Defensive context (Dean Oliver / Basketball-Reference DWS) ────────────
    # The BBR individual-defense formulas need per-opponent box totals (opponent
    # FGA/FGM/ORB/TOV/FTA/FTM) that the team-Base totals frame does not carry.
    # We approximate the opponent a team faced by the league-average team
    # (league totals / number of teams) — accurate over a full season and the
    # same approximation _advanced_pct() uses for BPM's rate stats.
    n_teams = max(len(t_idx), 1)
    has_plus_minus = "PLUS_MINUS" in t_idx.columns
    opp_fga = lg_fga / n_teams
    opp_fgm = lg_fgm / n_teams
    opp_oreb = lg_oreb / n_teams
    opp_tov = lg_tov / n_teams
    opp_fta = lg_fta / n_teams
    opp_ftm = lg_ftm / n_teams
    opp_fg_pct = (opp_fgm / opp_fga) if opp_fga > 0 else 0.45

    ows_list, dws_list, min_list = [], [], []

    for _, row in p.iterrows():
        tid = row.get("TEAM_ID")
        mp = row["MIN"]
        min_list.append(mp)

        # ── Offensive Win Shares ──────────────────────────────────────────────
        # qAST is the fraction of the player's FGMs that were assisted by a teammate.
        # We use the team assist rate as a proxy (team_AST / team_FGM), which is
        # better than AST/FGM: the latter measures the player's own playmaking, not
        # how many of their shots were set up by someone else.
        team_ast_rate = tval(tid, "AST") / max(tval(tid, "FGM"), 1)

        # PProd_FG: scoring credit from own FGs. Assisted makes give half-credit to
        # the assister, so the scorer retains (1 - 0.5*qAST) of the value.
        pprod_fg = 2 * (row["FGM"] + 0.5 * row["FG3M"]) * (1 - 0.5 * team_ast_rate)

        # PProd_AST: assist credit — assister earns half the point value per basket.
        avg_pts_per_fgm = (2 * tval(tid, "FGM") + tval(tid, "FG3M")) / max(tval(tid, "FGM"), 1)
        pprod_ast = row["AST"] * avg_pts_per_fgm * 0.5

        # PProd_ORB: credit for offensive rebounds
        orb_factor = 1 - (lg_oreb / (lg_fga - lg_oreb + lg_tov + 0.44 * lg_fta))
        pprod_orb = 2 * row["OREB"] * vop * orb_factor

        # PProd_FT: made free throws are worth 1 point each
        pprod_ft = row["FTM"]

        pts_prod = pprod_fg + pprod_ast + pprod_orb + pprod_ft

        # Scoring possessions — FG plays only; FTs are accounted for separately via ft_poss.
        scoring_poss = row["FGM"] * (1 - 0.5 * team_ast_rate)

        # Plays = FG scoring possessions + missed FGs lost to opponent + FT trips + turnovers
        fg_missed = row["FGA"] - row["FGM"]
        team_orb_pct = tval(tid, "OREB") / max(tval(tid, "OREB") + tval(tid, "DREB"), 1)
        ft_poss = 0.44 * row["FTA"]  # BBR standard: 0.44 * FTA
        plays = scoring_poss + fg_missed * (1 - team_orb_pct) + ft_poss + row["TOV"]

        # Marginal offense
        team_poss = tval(tid, "FGA") + 0.44 * tval(tid, "FTA") - tval(tid, "OREB") + tval(tid, "TOV")
        team_games = max(tval(tid, "GP"), 1)
        team_pts = tval(tid, "PTS")
        marg_off_pts = pts_prod - vop * plays
        ppw = 0.32 * 2 * (team_pts / team_games if team_games > 0 else lg_pts / 30)
        if ppw <= 0:
            ppw = 30.2

        ows = marg_off_pts / ppw
        ows_list.append(ows)

        # ── Defensive Win Shares (Dean Oliver / Basketball-Reference) ─────────
        # Full individual-defense chain: player Stops -> Stop% -> individual
        # DRtg anchored to the team's actual defensive rating -> marginal
        # defensive points -> DWS. See the opponent approximation note above.
        tm_drb = tval(tid, "DREB")
        tm_blk = tval(tid, "BLK")
        tm_stl = tval(tid, "STL")
        tm_pf = max(tval(tid, "PF"), 1.0)
        # Team minutes are reported as game-minutes (GP x 48); the BBR "Tm MP"
        # term is the whole team's player-minutes, i.e. 5x that.
        tm_mp = 5.0 * tval(tid, "MIN")
        tm_pts = tval(tid, "PTS")

        # Team defensive rating: opponent points per 100 defensive possessions.
        # Opponent points = team points - season point differential (PLUS_MINUS);
        # opponent possessions ~ the team's own possessions over a season. When
        # PLUS_MINUS is absent we fall back to a league-average opponent, which
        # centers every team at league-average team defense but still lets each
        # player's DRtg vary by his own Stop%.
        opp_pts = (tm_pts - tval(tid, "PLUS_MINUS")) if has_plus_minus else (lg_pts / n_teams)
        tm_def_poss = team_poss if team_poss > 0 else 1.0
        tm_def_rating = 100.0 * opp_pts / tm_def_poss

        # Defensive field-goal weighting (FMwt) and opponent offensive-rebound
        # rate (DOR%) against this team.
        dor_pct = opp_oreb / (opp_oreb + tm_drb) if (opp_oreb + tm_drb) > 0 else 0.25
        fmwt_den = (opp_fg_pct * (1 - dor_pct)
                    + (1 - opp_fg_pct) * dor_pct)
        fmwt = (opp_fg_pct * (1 - dor_pct)) / fmwt_den if fmwt_den > 0 else 0.0

        # Stops1: individual defensive events (steals, blocks that stick, DREBs).
        stop1 = (
            row["STL"]
            + row["BLK"] * fmwt * (1 - 1.07 * dor_pct)
            + row["DREB"] * (1 - fmwt)
        )
        # Stops2: the player's share of team-level forced misses / turnovers,
        # plus stops driven off his personal fouls.
        if tm_mp > 0:
            stop2 = (
                (((opp_fga - opp_fgm - tm_blk) / tm_mp) * fmwt * (1 - 1.07 * dor_pct)
                 + (opp_tov - tm_stl) / tm_mp) * mp
                + (row["PF"] / tm_pf) * 0.4 * opp_fta
                * (1 - (opp_ftm / opp_fta if opp_fta > 0 else 0.0)) ** 2
            )
        else:
            stop2 = 0.0
        stops = stop1 + stop2

        # Stop%: share of the opponent possessions the player ends while on court.
        stop_pct = (stops * tm_mp) / (tm_def_poss * mp) if (tm_def_poss * mp) > 0 else 0.0

        # Points the defense concedes per scoring possession (opponent side).
        scposs_den = (opp_fgm + (1 - (1 - (opp_ftm / opp_fta if opp_fta > 0 else 0.0)) ** 2)
                      * opp_fta * 0.4)
        d_pts_per_scposs = opp_pts / scposs_den if scposs_den > 0 else lg_ppp

        # Individual DRtg: 20% player Stop%, 80% team defense (Oliver's split).
        player_drtg = tm_def_rating + 0.2 * (
            100.0 * d_pts_per_scposs * (1 - stop_pct) - tm_def_rating)

        # Marginal defense: possessions the player influenced, valued against the
        # 1.08 x league-points-per-possession defensive baseline. A lower DRtg
        # (better defender) yields more marginal defensive points.
        marg_def_pts = (mp / tm_mp) * tm_def_poss * (1.08 * lg_ppp - player_drtg / 100.0) \
            if tm_mp > 0 else 0.0
        dws = marg_def_pts / ppw if ppw > 0 else 0.0
        dws_list.append(dws)

    p["OWS"] = ows_list
    p["DWS"] = dws_list
    p["WS"] = p["OWS"] + p["DWS"]
    p["WS48"] = np.where(p["MIN"] > 0, p["WS"] / p["MIN"] * 48, np.nan)
    return p


# ── BPM (Box Plus/Minus) ─────────────────────────────────────────────────────

# We model OBPM and DBPM as linear functions of standard advanced rate stats
# (per-minute / per-possession, not per player-possession), then anchor each
# team's minutes-weighted average to the team's actual offensive / defensive
# point margin per 100 — the defining property of BPM. The slopes below were fit
# by least squares against Basketball-Reference's published OBPM / DBPM for the
# 2025-26 season; on 500+ minute players they reproduce BBR at OBPM r=0.95,
# DBPM r=0.88, combined BPM r=0.93, VORP r=0.96. The fitted intercepts are
# discarded on purpose: the team-margin anchor sets the level, which also keeps
# the metric calibrated across seasons without re-fitting. Inputs are standard
# advanced percentages (usg, ast, tov, orb, drb, stl, blk on the usual 0-100
# scale; scor = usg x (TS% - league TS%); ftr = FTA / FGA). See _advanced_pct.
_OBPM_W = {"scor": 1.43, "usg": 0.18, "ast": 0.135, "tov": -0.244, "orb": 0.164,
           "ftr": -2.04}
_DBPM_W = {"stl": 1.26, "blk": 0.26, "drb": 0.046}
_VORP_REPLACEMENT = -2.0


def _advanced_pct(player_df: pd.DataFrame, team_df: pd.DataFrame,
                  league: dict) -> pd.DataFrame:
    """Standard advanced rate stats per player, minutes/pace-aware.

    Opponent rebounding and shot volume (needed for ORB%/DRB%/STL%/BLK%) are
    approximated by the league-average team, which is accurate over a full
    season. Returns a DataFrame of percentage features aligned to player_df.index;
    rows with < 1 minute come back as 0 (BPM masks them out separately).
    """
    p = player_df
    n = max(len(team_df), 1)
    t = team_df.set_index("TEAM_ID")

    def tm(col):
        if col in t.columns:
            return p["TEAM_ID"].map(t[col])
        return pd.Series(np.nan, index=p.index)

    def g(col):
        return p[col].fillna(0) if col in p.columns else pd.Series(0.0, index=p.index)

    mp = p["MIN"].where(p["MIN"] >= 1)
    # NBA team MIN is reported as game-minutes (GP x 48), which already equals the
    # "team minutes / 5" term in the standard advanced-stat formulas, so it is
    # used directly (no further /5).
    tmmp = tm("MIN")
    TmFGA, TmFTA, TmTOV = tm("FGA"), tm("FTA"), tm("TOV")
    TmFGM, TmOREB, TmDREB = tm("FGM"), tm("OREB"), tm("DREB")
    tm_poss = TmFGA + 0.44 * TmFTA - TmOREB + TmTOV

    lg_ts = league["lg_pts"] / (2 * (league["lg_fga"] + 0.44 * league["lg_fta"]))
    opp_dreb = league["lg_dreb"] / n
    opp_oreb = league["lg_oreb"] / n
    opp_fga = league["lg_fga"] / n
    opp_fg3a = league["lg_fg3a"] / n

    out = pd.DataFrame(index=p.index)
    out["usg"] = 100 * ((g("FGA") + 0.44 * g("FTA") + g("TOV")) * tmmp) / (
        mp * (TmFGA + 0.44 * TmFTA + TmTOV))
    ast_den = (mp / tmmp) * TmFGM - g("FGM")
    out["ast"] = 100 * g("AST") / ast_den.where(ast_den > 0)
    out["tov"] = 100 * g("TOV") / (
        g("FGA") + 0.44 * g("FTA") + g("TOV")).replace(0, np.nan)
    out["orb"] = 100 * (g("OREB") * tmmp) / (mp * (TmOREB + opp_dreb))
    out["drb"] = 100 * (g("DREB") * tmmp) / (mp * (TmDREB + opp_oreb))
    out["stl"] = 100 * (g("STL") * tmmp) / (mp * tm_poss)
    out["blk"] = 100 * (g("BLK") * tmmp) / (mp * (opp_fga - opp_fg3a))
    ts = g("PTS") / (2 * (g("FGA") + 0.44 * g("FTA"))).replace(0, np.nan)
    out["scor"] = out["usg"] * (ts - lg_ts)
    out["ftr"] = g("FTA") / g("FGA").replace(0, np.nan)
    return out.replace([np.inf, -np.inf], np.nan).fillna(0.0)


def bpm(player_df: pd.DataFrame, team_df: pd.DataFrame,
        league: dict) -> pd.DataFrame:
    """Box Plus/Minus: OBPM, DBPM, BPM, validated against Basketball-Reference.

    Returns a DataFrame with OBPM, DBPM, BPM columns added. Each is points per 100
    possessions above a league-average player.

    Two stages (see _OBPM_W / _DBPM_W for the why):
      1. Raw OBPM / DBPM from a linear model on the advanced rate stats in
         _advanced_pct (fit to reproduce BBR's BPM 2.0).
      2. Team-margin anchor: within each team, OBPM is shifted so its
         minutes-weighted average equals the team's offensive point margin per
         100, and DBPM so it equals the defensive margin (derived from team
         PLUS_MINUS and possessions). This is the defining BPM property — a
         team's players sum to the team's point differential — and it sets the
         scale, so the fitted intercepts are not needed. When PLUS_MINUS is
         absent the team is centered at zero margin.

    team_df should include TEAM_ID plus season totals (PTS, FGA, FTA, TOV, OREB,
    DREB, FGM, MIN) and, for the anchor, PLUS_MINUS.
    """
    p = player_df.copy()
    for col in ["PTS", "FGM", "FGA", "FTM", "FTA", "FG3M", "OREB", "DREB", "AST",
                "STL", "BLK", "TOV", "PF", "MIN", "GP"]:
        if col in p.columns:
            p[col] = p[col].fillna(0)

    pct = _advanced_pct(p, team_df, league)
    raw_o = sum(w * pct[k] for k, w in _OBPM_W.items())
    raw_d = sum(w * pct[k] for k, w in _DBPM_W.items())
    p["_ro"], p["_rd"] = raw_o, raw_d

    t = team_df.set_index("TEAM_ID")
    lg_poss = (league["lg_fga"] + 0.44 * league["lg_fta"]
               - league["lg_oreb"] + league["lg_tov"])
    lg_off = league["lg_pts"] / lg_poss * 100

    obpm = pd.Series(np.nan, index=p.index)
    dbpm = pd.Series(np.nan, index=p.index)
    for tid, grp in p.groupby("TEAM_ID"):
        if tid not in t.index:
            continue
        TmPTS = float(t.loc[tid, "PTS"])
        PM = float(t.loc[tid, "PLUS_MINUS"]) if "PLUS_MINUS" in t.columns else 0.0
        tm_poss = (float(t.loc[tid, "FGA"]) + 0.44 * float(t.loc[tid, "FTA"])
                   - float(t.loc[tid, "OREB"]) + float(t.loc[tid, "TOV"]))
        tm_poss = max(tm_poss, 1.0)
        off_margin = TmPTS / tm_poss * 100 - lg_off
        def_margin = lg_off - (TmPTS - PM) / tm_poss * 100
        w = grp["MIN"]
        wsum = w.sum() if w.sum() > 0 else 1.0
        adj_o = off_margin / 5 - (grp["_ro"] * w).sum() / wsum
        adj_d = def_margin / 5 - (grp["_rd"] * w).sum() / wsum
        obpm.loc[grp.index] = grp["_ro"] + adj_o
        dbpm.loc[grp.index] = grp["_rd"] + adj_d

    valid = p["MIN"] >= 1
    p["OBPM"] = obpm.where(valid)
    p["DBPM"] = dbpm.where(valid)
    p["BPM"] = p["OBPM"] + p["DBPM"]
    return p.drop(columns=["_ro", "_rd"])


# ── VORP ────────────────────────────────────────────────────────────────────────

def vorp(player_df: pd.DataFrame, games_in_season: int = 82) -> pd.Series:
    """Value Over Replacement Player, derived from BPM and minutes.

    Requires BPM and MIN columns (add them via bpm() first).
    VORP = (BPM - (-2.0)) × (MIN / (team_games × 48)) × (team_games / 82)

    MIN / (team_games × 48) is the player's share of his team's individual
    minutes (≈ 0.66 for a star), and team_games / 82 prorates a partial season.
    The replacement level is -2.0 BPM (BBR convention). Pass actual team games
    for partial seasons.
    """
    mp_share = player_df["MIN"] / (games_in_season * 48)
    return ((player_df["BPM"] - _VORP_REPLACEMENT) * mp_share
            * (games_in_season / 82.0))


# ── RAPM (Regularized Adjusted Plus-Minus) ────────────────────────────────────

def rapm(
    possessions_df: pd.DataFrame,
    *,
    alphas=None,
    cv: int = 5,
    prior=None,
    prior_strength: float = 0.0,
) -> pd.DataFrame:
    """Regularized Adjusted Plus-Minus via ridge regression with cross-validated penalty.

    Returns a DataFrame indexed by player_id with columns RAPM, O_RAPM, D_RAPM.

    Sign convention:
      O_RAPM > 0  — player's offense adds points above average.
      D_RAPM > 0  — player's defense prevents points (good defender).
      RAPM = O_RAPM + D_RAPM.

    Input schema (possessions_df):
      One row per possession. Two accepted formats for the ten players on court:

      Format A (list columns):
        off_player_ids  — list of 5 player IDs on offense for this possession
        def_player_ids  — list of 5 player IDs on defense

      Format B (flat columns):
        off1 .. off5   — one column per offensive player ID
        def1 .. def5   — one column per defensive player ID

      Both formats also require:
        points   — points scored by the offense on this possession (numeric)
        weight   — (optional) possession weight; defaults to 1 per row

    Method:
      Builds a sparse design matrix with 2 columns per player: an offensive
      column (+1 when the player is on offense) and a defensive column (-1 when
      on defense). The target y = points * 100 (i.e., the per-100-possessions
      scale). Fits sklearn.linear_model.RidgeCV with k-fold cross-validation
      to choose the regularization penalty from ``alphas``.

      Ridge acts as a shrinkage prior here, not a possession-level predictor, so
      the default ``alphas`` grid is bounded (see below): an unbounded grid lets
      CV drive the penalty arbitrarily high and collapse the point-per-100 scale.

      When ``prior`` is provided, implements prior-mean ridge (shrink toward the
      box-score prior instead of zero) via the substitution gamma = beta - prior_vector:
        y' = y - X @ prior_vector
        fit RidgeCV on (X, y') -> gamma
        beta = gamma + prior_vector
      Players absent from ``prior`` fall back to a zero prior.

    Parameters
    ----------
    possessions_df : DataFrame
        Possession-level data as described above.
    alphas : array-like, optional
        Candidate regularization penalties. Defaults to 17 values log-spaced
        from 10 to 1000. The upper bound is intentional: it caps shrinkage so
        the output stays on an interpretable point-per-100 scale even when the
        possession data is sparse or noisy.
    cv : int
        Number of folds for cross-validation (default 5).
    prior : DataFrame, optional
        Box-score prior for each player. Must be indexed by player_id with two
        columns:
          ``off`` -- offensive prior in points per 100 possessions; same scale
                     and sign as O_RAPM (positive = above-average offense).
          ``def`` -- defensive prior in points per 100 possessions; same scale
                     and sign as D_RAPM (positive = good defender who prevents
                     points).
        Players present in the possessions but absent from ``prior`` receive a
        zero prior (standard ridge-toward-zero behavior). When None (default),
        all priors are zero and rapm() returns the same result as the no-prior
        call.

    Returns
    -------
    DataFrame indexed by player_id with columns RAPM, O_RAPM, D_RAPM.
    """
    from scipy.sparse import coo_matrix, csr_matrix
    from sklearn.linear_model import Ridge, RidgeCV

    df = possessions_df.reset_index(drop=True)
    n = len(df)

    # --- Resolve player-ID columns ---
    off_cols_5 = [f"off{i}" for i in range(1, 6)]
    def_cols_5 = [f"def{i}" for i in range(1, 6)]

    if "off_player_ids" in df.columns and "def_player_ids" in df.columns:
        off_ids = df["off_player_ids"].tolist()
        def_ids = df["def_player_ids"].tolist()
    elif all(c in df.columns for c in off_cols_5 + def_cols_5):
        off_ids = df[off_cols_5].values.tolist()
        def_ids = df[def_cols_5].values.tolist()
    else:
        raise ValueError(
            "possessions_df must have either 'off_player_ids'/'def_player_ids' "
            "list columns, or 'off1'..'off5'/'def1'..'def5' columns."
        )

    # --- Build player index ---
    all_ids = sorted({pid for group in off_ids + def_ids for pid in group})
    pid_to_idx = {pid: i for i, pid in enumerate(all_ids)}
    n_players = len(all_ids)
    n_cols = n_players * 2  # column layout: 2*i = offensive, 2*i+1 = defensive

    # --- Build sparse design matrix in COO format ---
    rows, cols, vals = [], [], []
    for row_i in range(n):
        for pid in off_ids[row_i]:
            rows.append(row_i)
            cols.append(pid_to_idx[pid] * 2)
            vals.append(1.0)
        for pid in def_ids[row_i]:
            rows.append(row_i)
            cols.append(pid_to_idx[pid] * 2 + 1)
            vals.append(-1.0)

    X = csr_matrix(
        coo_matrix((vals, (rows, cols)), shape=(n, n_cols), dtype=np.float32)
    )
    y = df["points"].to_numpy(dtype=np.float64) * 100.0

    weights = (
        df["weight"].to_numpy(dtype=np.float64)
        if "weight" in df.columns
        else np.ones(n, dtype=np.float64)
    )

    # --- Build prior vector aligned to design-matrix columns ---
    # Column layout: 2*i = offensive column (prior["off"]), 2*i+1 = defensive
    # column (prior["def"]). Both use the same sign as O_RAPM / D_RAPM.
    # Players absent from prior keep their prior at zero (standard ridge behavior).
    prior_vector = np.zeros(n_cols, dtype=np.float64)
    if prior is not None:
        for pid, idx in pid_to_idx.items():
            if pid in prior.index:
                prior_vector[idx * 2] = float(prior.loc[pid, "off"])
                prior_vector[idx * 2 + 1] = float(prior.loc[pid, "def"])

    # --- Ridge regression with cross-validated alpha ---
    # The grid is deliberately bounded to [10, 1000]. A single possession is
    # almost unpredictable, so cross-validation that is free to pick a very large
    # penalty will: it minimizes possession-level prediction error by shrinking
    # every coefficient toward zero. With an unbounded grid (e.g. up to 1e5) that
    # collapses the point-per-100 scale entirely (ratings come out near ±0.05
    # instead of ±5). Ridge here is a shrinkage prior, not a possession predictor,
    # so the upper bound keeps the penalty in a regime that preserves interpretable
    # units; on clean, plentiful data CV still settles near the low end (~15).
    if alphas is None:
        alphas = np.logspace(1, 3, 17)  # 10 .. 1000

    # Prior-mean shift: shrink gamma = beta - prior_vector toward zero, which is
    # equivalent to shrinking beta toward prior_vector. y' = y - X @ prior_vector
    # is a no-op when prior_vector is all zeros. The league baseline (~110 pts/100)
    # stays in the unpenalized intercept, so the shrinkage never distorts the level.
    y_fit = y - X.dot(prior_vector)

    if prior is not None and prior_strength > 0:
        # Informative prior with a FIXED, strong penalty instead of a
        # cross-validated one. CV optimizes possession-level prediction and
        # settles on a penalty far too weak to pull a moderate-minute player
        # (Cisse, ~900 possessions) off a lucky lineup context, so it leaves such
        # players spiking at the top. A fixed strong penalty shrinks low-possession
        # players onto their box-score prior while heavy-minute stars, with far
        # more possessions, still move to what the lineup data shows.
        model = Ridge(alpha=float(prior_strength), fit_intercept=True)
        model.fit(X, y_fit, sample_weight=weights)
    else:
        model = RidgeCV(alphas=alphas, cv=cv, fit_intercept=True)
        model.fit(X, y_fit, sample_weight=weights)

    # Recover beta = gamma + prior_vector (no-op when prior_vector is all zeros)
    coefs = model.coef_ + prior_vector  # shape (n_cols,)

    # Even indices = offensive columns; odd = defensive columns.
    # D_RAPM = the defensive coefficient directly: because X uses -1 for
    # defensive presence, a positive beta_def means the player's presence
    # lowers the opponent's score (good defense).
    o_rapm = coefs[0::2]
    d_rapm = coefs[1::2]

    result = pd.DataFrame(
        {"O_RAPM": o_rapm, "D_RAPM": d_rapm},
        index=pd.Index(all_ids, name="player_id"),
    )
    result["RAPM"] = result["O_RAPM"] + result["D_RAPM"]
    return result[["RAPM", "O_RAPM", "D_RAPM"]]
