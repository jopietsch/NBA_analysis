"""Game-level feature construction: build_game_dataset() and era/format-period
classification shared by every analysis module in this package."""

from __future__ import annotations

import numpy as np
import pandas as pd
from nba_api.stats.library.parameters import SeasonType

from nbakit.stats import possessions as _possessions
from nbakit.data import normalize_game_id

import home_court_data as nba

def _classify_year(year: int, defs: list) -> str:
    for label, y1, y2, *_ in defs:
        if y1 <= year <= y2:
            return label
    return "other"


def _era_for_year(year: int) -> str:
    return _classify_year(year, nba.ERA_DEFS)


def _format_period_for_year(year: int) -> str:
    return _classify_year(year, nba.PLAYOFF_FORMAT_PERIODS)


def build_game_dataset() -> pd.DataFrame:
    """
    Build a game-level DataFrame with regression features from all cached CSVs.
    One row per game. rest_diff/tz_diff are NaN where data is unavailable
    (first game of each team's season, or unknown franchise time zone).
    """
    print("  Building game-level dataset from cache...", end="", flush=True)
    chunks: list[pd.DataFrame] = []

    for year in range(nba.START_YEAR, nba.END_YEAR + 1):
        for season_type, is_playoff in [(SeasonType.regular, False), ("Playoffs", True)]:
            if is_playoff and year in nba.SKIP_PLAYOFF_YEARS:
                continue

            df = nba._load_game_log(year, season_type)
            if df is None:
                continue

            df = nba._add_rest_days(df)

            merged = nba._merge_home_away_rows(df)
            if merged is None:
                continue

            merged = merged.copy()
            merged["home_win"]      = (merged["WL_home"] == "W").astype(int)
            merged["year"]          = year
            merged["is_playoff"]    = int(is_playoff)
            merged["era"]           = _era_for_year(year)
            merged["format_period"] = _format_period_for_year(year)
            merged["covid"]         = int(nba.short_label(year) in nba.COVID_SEASONS)
            merged["rest_diff"]     = merged["REST_home"] - merged["REST_away"]
            merged["away_b2b"]      = (merged["REST_away"] == 0).astype("float64")
            merged["home_b2b"]      = (merged["REST_home"] == 0).astype("float64")
            merged.loc[merged["REST_away"].isna(), "away_b2b"] = np.nan
            merged.loc[merged["REST_home"].isna(), "home_b2b"] = np.nan
            merged["altitude_home"] = merged["TEAM_NAME_home"].isin(nba.ALTITUDE_TEAMS).astype(int)

            home_tz = merged["TEAM_NAME_home"].map(nba.TEAM_TIMEZONES)
            away_tz = merged["TEAM_NAME_away"].map(nba.TEAM_TIMEZONES)
            merged["tz_diff"] = (home_tz - away_tz).abs().astype("float64")
            merged.loc[home_tz.isna() | away_tz.isna(), "tz_diff"] = np.nan

            diffs = nba._compute_box_differentials(merged)
            merged[diffs.columns] = diffs
            merged["margin"] = merged["PLUS_MINUS_home"]

            if {"TOV_home", "TOV_away", "REB_home", "REB_away"}.issubset(merged.columns):
                merged["tov_diff"] = merged["TOV_home"] - merged["TOV_away"]
                merged["reb_diff"] = merged["REB_home"] - merged["REB_away"]
            else:
                merged["tov_diff"] = np.nan
                merged["reb_diff"] = np.nan

            if {"OREB_home", "OREB_away", "DREB_home", "DREB_away"}.issubset(merged.columns):
                reb = nba._compute_rebound_components(merged)
                merged[reb.columns] = reb
            else:
                for col in ("oreb_diff", "dreb_diff", "reb_share_edge", "league_oreb_rate"):
                    merged[col] = np.nan

            total_fga  = merged["FGA_home"]  + merged["FGA_away"]
            total_fg3a = merged["FG3A_home"] + merged["FG3A_away"]
            merged["tpa_rate_avg"] = 100.0 * total_fg3a / total_fga.replace(0, np.nan)

            pace_cols = {"OREB_home", "OREB_away", "TOV_home", "TOV_away"}
            if pace_cols.issubset(merged.columns):
                home_poss = _possessions(merged, suffix="_home")
                away_poss = _possessions(merged, suffix="_away")
                merged["pace_avg"] = (home_poss + away_poss) / 2.0

                # Expected pace: leave-one-out per-team mean so realized pace
                # can't reflect game-outcome endogeneity.
                hp_arr = home_poss.values.astype(float)
                ap_arr = away_poss.values.astype(float)
                hteams = merged["TEAM_NAME_home"].values
                ateams = merged["TEAM_NAME_away"].values
                team_tot: dict[str, float] = {}
                team_cnt: dict[str, int] = {}
                for t, p in zip(np.concatenate([hteams, ateams]),
                                np.concatenate([hp_arr, ap_arr])):
                    team_tot[t] = team_tot.get(t, 0.0) + float(p)
                    team_cnt[t] = team_cnt.get(t, 0) + 1
                loo_h = np.array(
                    [(team_tot[t] - p) / (team_cnt[t] - 1)
                     if team_cnt[t] > 1 else np.nan
                     for t, p in zip(hteams, hp_arr)]
                )
                loo_a = np.array(
                    [(team_tot[t] - p) / (team_cnt[t] - 1)
                     if team_cnt[t] > 1 else np.nan
                     for t, p in zip(ateams, ap_arr)]
                )
                merged["expected_pace"] = (loo_h + loo_a) / 2.0
            else:
                merged["pace_avg"] = np.nan
                merged["expected_pace"] = np.nan

            if is_playoff:
                # Only the trailing digit (game-in-series) is read, so the
                # zero-padded canonical form is interchangeable here.
                gid_str = merged["GAME_ID"].apply(normalize_game_id)
                merged["game_in_series"] = gid_str.str[-1].astype(int).astype(float)
            else:
                merged["game_in_series"] = np.nan

            home_c = merged["TEAM_NAME_home"].map(nba.ARENA_COORDS)
            away_c = merged["TEAM_NAME_away"].map(nba.ARENA_COORDS)
            merged["distance_miles"] = [
                nba._haversine(a[0], a[1], h[0], h[1])
                if isinstance(a, tuple) and isinstance(h, tuple) else np.nan
                for a, h in zip(away_c, home_c)
            ]

            chunks.append(merged[[
                "GAME_ID",
                "home_win", "year", "is_playoff", "era", "format_period", "covid",
                "rest_diff", "away_b2b", "home_b2b", "altitude_home", "tz_diff",
                "foul_diff", "fta_diff", "fg_pct_diff", "efg_pct_diff", "tpa_rate_diff",
                "fg3_pct_diff", "ft_pct_diff", "tov_diff", "reb_diff",
                "oreb_diff", "dreb_diff", "reb_share_edge", "league_oreb_rate",
                "margin", "game_in_series", "distance_miles", "tpa_rate_avg",
                "pace_avg", "expected_pace",
                "TEAM_NAME_home", "TEAM_NAME_away",
            ]])

    if not chunks:
        print(" no data.")
        return pd.DataFrame()

    result = pd.concat(chunks, ignore_index=True)
    n_complete = len(result.dropna(subset=["rest_diff", "tz_diff"]))
    print(f" {len(result):,} game rows ({n_complete:,} with complete features).")
    return result


def _add_quality_diff(df: pd.DataFrame) -> pd.DataFrame:
    """Add quality_diff = home RS win% - away RS win% (same season) to playoff rows.

    Playoff rest is earned by advancing quickly, which correlates with team strength,
    so quality_diff controls for that confound in playoff rest analyses.
    """
    rs = df[df["is_playoff"] == 0]
    home_records = (
        rs.groupby(["year", "TEAM_NAME_home"])["home_win"]
        .agg(wins="sum", games="count")
        .rename_axis(index={"TEAM_NAME_home": "team"})
    )
    away_records = (
        rs.groupby(["year", "TEAM_NAME_away"])["home_win"]
        .agg(losses="sum", games="count")
        .rename_axis(index={"TEAM_NAME_away": "team"})
    )
    away_records["wins"] = away_records["games"] - away_records["losses"]
    away_records = away_records.drop(columns="losses")

    all_records = pd.concat([home_records, away_records]).groupby(
        level=["year", "team"]
    ).sum()
    all_records["rs_winpct"] = all_records["wins"] / all_records["games"]
    winpct = all_records["rs_winpct"]  # MultiIndex: (year, team)

    po_mask = df["is_playoff"] == 1
    po = df[po_mask]
    df = df.copy()
    df.loc[po_mask, "quality_diff"] = (
        po.apply(
            lambda r: (
                winpct.get((r["year"], r["TEAM_NAME_home"]), np.nan)
                - winpct.get((r["year"], r["TEAM_NAME_away"]), np.nan)
            ),
            axis=1,
        ).values
    )
    df.loc[~po_mask, "quality_diff"] = np.nan
    return df
