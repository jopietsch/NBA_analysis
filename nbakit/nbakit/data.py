"""
nbakit.data — shared NBA data primitives.

Season helpers, a CSV cache for nba_api game logs, SRS computation,
conference mapping, and champion identification. Question-specific data modules
import these and add their own compute_* functions on top.

Cache directory: reads NBA_CACHE_DIR env var; defaults to the nba_analysis/cache/
directory at the monorepo root so all questions share downloaded data.
Override: export NBA_CACHE_DIR=/path/to/cache
"""

import os
import time

import numpy as np
import pandas as pd

SLEEP_SEC      = 1.0
PLAYOFFS       = "Playoffs"
REGULAR_SEASON = "Regular Season"


# ── Cache ──────────────────────────────────────────────────────────────────────

def default_cache_dir() -> str:
    """Absolute path to the shared monorepo cache (nba_analysis/cache/)."""
    env = os.environ.get("NBA_CACHE_DIR")
    if env:
        return env
    # nbakit/nbakit/data.py → ../../ = nba_analysis/
    return os.path.normpath(
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "cache")
    )


# ── Season helpers ─────────────────────────────────────────────────────────────

def season_str(end_year: int) -> str:
    """2026 → '2025-26' (nba_api season format)."""
    return f"{end_year - 1}-{str(end_year)[-2:]}"


def short_label(end_year: int) -> str:
    """2026 → '25–26' (chart axis label)."""
    return f"{str(end_year - 1)[-2:]}–{str(end_year)[-2:]}"


def season_range_label(start_year: int, end_year: int) -> str:
    """(1984, 2026) → '1983–84 through 2025–26'."""
    s = f"{start_year - 1}–{str(start_year)[-2:]}"
    e = f"{end_year - 1}–{str(end_year)[-2:]}"
    return f"{s} through {e}"


def label_to_year(lbl: str) -> int:
    """Short season label ('83–84') → ending year (1984)."""
    suffix = int(lbl.split("–")[1])
    return (2000 + suffix) if suffix < 50 else (1900 + suffix)


# ── Period bucketing ────────────────────────────────────────────────────────────
# Periods are lists of tuples whose first three positions are
# (label, start_year, end_year); any further positions (e.g. a description) are
# ignored. Used to average per-season series within rule-change eras, playoff-
# format spans, etc.

def bucket_series_by_period(seasons: list[str], values: list[float],
                            periods: list, *, drop_nan: bool = False,
                            round_to: int = 1) -> list[float]:
    """Average `values` within each period; one number per period (0 if empty)."""
    out: list[float] = []
    for period in periods:
        y1, y2 = period[1], period[2]
        vals = [
            v for s, v in zip(seasons, values)
            if y1 <= label_to_year(s) <= y2 and not (drop_nan and np.isnan(v))
        ]
        out.append(round(float(np.mean(vals)), round_to) if vals else 0)
    return out


def bucket_stats_by_period(seasons: list[str], stats: dict, periods: list,
                           *, drop_nan: bool = True,
                           round_to: int = 1) -> tuple[dict, list[str]]:
    """Average each series in `stats` ({key: per-season values}) within each period.

    Returns (averages_by_key, period_labels).
    """
    avgs = {
        key: bucket_series_by_period(seasons, values, periods,
                                     drop_nan=drop_nan, round_to=round_to)
        for key, values in stats.items()
    }
    return avgs, [p[0] for p in periods]


def cache_path(end_year: int, season_type: str,
               cache_dir: str | None = None) -> str:
    d = cache_dir or default_cache_dir()
    fname = f"{season_str(end_year)}_{season_type.replace(' ', '_')}.csv"
    return os.path.join(d, fname)


# ── MATCHUP parsing ─────────────────────────────────────────────────────────────

def is_home(matchup: str) -> bool:
    """True if this nba_api MATCHUP row is the home team.

    'NYK vs. BOS' → True (NYK home);  'NYK @ BOS' → False (NYK away).
    """
    return " vs. " in str(matchup)


def home_abbr(matchup: str) -> str:
    """Home-team abbreviation from an nba_api MATCHUP string.

    'NYK vs. BOS' → 'NYK';  'NYK @ BOS' → 'BOS'.
    """
    s = str(matchup)
    if " vs. " in s:
        return s.split(" vs. ")[0].strip()
    return s.split(" @ ")[1].strip()


def merge_home_away_rows(df: pd.DataFrame) -> pd.DataFrame | None:
    """Collapse a per-team-per-game log into one row per game.

    Joins each game's home and away rows on GAME_ID; columns get '_home' /
    '_away' suffixes. Returns None if either side is empty.
    """
    home = df[df["MATCHUP"].str.contains(" vs. ", regex=False, na=False)]
    away = df[df["MATCHUP"].str.contains(" @ ", regex=False, na=False)]
    if home.empty or away.empty:
        return None
    merged = home.merge(away, on="GAME_ID", suffixes=("_home", "_away"))
    if merged.empty:
        return None
    return merged


def add_rest_days(df: pd.DataFrame) -> pd.DataFrame:
    """Add a REST column: days since each team's previous game minus 1.

    0 = back-to-back. Requires GAME_DATE and TEAM_ID columns.
    """
    df = df.copy()
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df = df.sort_values(["TEAM_ID", "GAME_DATE"])
    df["PREV_DATE"] = df.groupby("TEAM_ID")["GAME_DATE"].shift(1)
    df["REST"] = (df["GAME_DATE"] - df["PREV_DATE"]).dt.days - 1
    return df


# ── Fetchers ───────────────────────────────────────────────────────────────────

def fetch_game_logs(end_year: int, season_type: str = PLAYOFFS,
                    cache_dir: str | None = None) -> pd.DataFrame:
    """Fetch game logs for one season/type; cache as CSV.

    Returns one row per team per game (nba_api LeagueGameFinder format).
    MATCHUP is 'NYK vs. BOS' (home) or 'NYK @ BOS' (away); WL is 'W'/'L'.

    LeagueGameFinder quirk: uses season_nullable= and season_type_nullable=,
    not the bare season= other endpoints take.
    """
    path = cache_path(end_year, season_type, cache_dir)
    if os.path.exists(path):
        return pd.read_csv(path)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    from nba_api.stats.endpoints import leaguegamefinder
    df = leaguegamefinder.LeagueGameFinder(
        season_nullable=season_str(end_year),
        season_type_nullable=season_type,
        league_id_nullable="00",
    ).get_data_frames()[0]
    df.to_csv(path, index=False)
    time.sleep(SLEEP_SEC)
    return df


def fetch_player_game_logs(end_year: int, season_type: str = PLAYOFFS,
                           cache_dir: str | None = None) -> pd.DataFrame:
    """Fetch player-level game logs for one season/type; cache as CSV.

    Returns one row per player per game (LeagueGameFinder player mode).
    MIN column is a string 'MM:SS'; use parse_min() to convert to float.
    """
    d = cache_dir or default_cache_dir()
    slug = season_type.replace(" ", "_")
    path = os.path.join(d, f"{season_str(end_year)}_{slug}_players.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    os.makedirs(d, exist_ok=True)
    from nba_api.stats.endpoints import leaguegamefinder
    df = leaguegamefinder.LeagueGameFinder(
        player_or_team_abbreviation="P",
        season_nullable=season_str(end_year),
        season_type_nullable=season_type,
        league_id_nullable="00",
    ).get_data_frames()[0]
    df.to_csv(path, index=False)
    time.sleep(SLEEP_SEC)
    return df


def parse_min(val) -> float:
    """Parse nba_api MIN column: 'MM:SS' string or numeric → float minutes."""
    if pd.isna(val):
        return 0.0
    s = str(val)
    if ":" in s:
        parts = s.split(":", 1)
        try:
            return float(parts[0]) + float(parts[1]) / 60
        except ValueError:
            return 0.0
    try:
        return float(val)
    except (ValueError, TypeError):
        return 0.0


def fetch_standings(end_year: int,
                    cache_dir: str | None = None) -> pd.DataFrame:
    """Fetch team standings for one season; cache as CSV.

    Relevant columns: TeamID, Conference, WINS, LOSSES, DiffPointsPG.
    Uses LeagueStandingsV3 (season= format, not season_nullable=).
    """
    d = cache_dir or default_cache_dir()
    path = os.path.join(d, f"{season_str(end_year)}_standings.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    os.makedirs(d, exist_ok=True)
    from nba_api.stats.endpoints import leaguestandingsv3
    df = leaguestandingsv3.LeagueStandingsV3(
        league_id_nullable="00",
        season=season_str(end_year),
        season_type="Regular Season",
    ).get_data_frames()[0]
    df.to_csv(path, index=False)
    time.sleep(SLEEP_SEC)
    return df


# ── SRS ────────────────────────────────────────────────────────────────────────

def fill_plus_minus(game_logs: pd.DataFrame) -> pd.DataFrame:
    """Return game_logs with PLUS_MINUS filled from PTS where null.

    Pre-1997 NBA data from nba_api has PLUS_MINUS=NaN; we derive it from
    PTS by pairing the two rows for each GAME_ID.
    """
    df = game_logs.copy()
    if "PLUS_MINUS" not in df.columns or df["PLUS_MINUS"].notna().all():
        return df
    null_mask = df["PLUS_MINUS"].isna()
    if not null_mask.any() or "PTS" not in df.columns:
        return df
    pts_by_game = df[["GAME_ID", "TEAM_ID", "PTS"]].copy()
    pts_by_game["OPP_PTS"] = (
        pts_by_game.groupby("GAME_ID")["PTS"]
        .transform(lambda s: s.iloc[::-1].values)
    )
    computed = (pts_by_game["PTS"] - pts_by_game["OPP_PTS"]).reindex(df.index)
    df.loc[null_mask, "PLUS_MINUS"] = computed[null_mask]
    return df


def compute_srs(game_logs: pd.DataFrame) -> pd.Series:
    """Compute Simple Rating System from regular-season game logs.

    SRS = average point differential adjusted for strength of schedule.
    Solved as a least-squares linear system (I − A) @ srs = mean_margin,
    constrained to sum(srs) = 0 (league average = 0).

    For pre-1997 seasons where nba_api returns PLUS_MINUS=NaN, the margin
    is derived from PTS (both team rows per GAME_ID are required).

    Returns pd.Series indexed by TEAM_ID, values in points per game.
    """
    game_logs = fill_plus_minus(game_logs)
    df = game_logs[["GAME_ID", "TEAM_ID", "PLUS_MINUS"]].dropna().copy()
    df["TEAM_ID"] = df["TEAM_ID"].astype(int)

    # Build opponent map from GAME_ID grouping (each game appears exactly twice)
    opp: dict[tuple, int] = {}
    for gid, grp in df.groupby("GAME_ID"):
        ids = grp["TEAM_ID"].tolist()
        if len(ids) == 2:
            opp[(gid, ids[0])] = ids[1]
            opp[(gid, ids[1])] = ids[0]

    df["OPP_ID"] = [opp.get((r.GAME_ID, r.TEAM_ID)) for r in df.itertuples()]
    df = df.dropna(subset=["OPP_ID"])
    df["OPP_ID"] = df["OPP_ID"].astype(int)

    teams = sorted(df["TEAM_ID"].unique())
    n = len(teams)
    idx = {t: i for i, t in enumerate(teams)}

    # Schedule matrix A[i,j] = fraction of team i's games played vs team j
    A = np.zeros((n, n))
    m = np.zeros(n)
    for tid, grp in df.groupby("TEAM_ID"):
        i = idx[tid]
        m[i] = grp["PLUS_MINUS"].mean()
        for opp_id, cnt in grp["OPP_ID"].value_counts().items():
            if opp_id in idx:
                A[i, idx[opp_id]] = cnt / len(grp)

    # Solve (I − A) @ srs = m  s.t.  sum(srs) = 0
    aug_A = np.vstack([np.eye(n) - A, np.ones((1, n))])
    aug_b = np.append(m, 0.0)
    srs_vals, _, _, _ = np.linalg.lstsq(aug_A, aug_b, rcond=None)

    return pd.Series(srs_vals, index=pd.Index(teams, name="TEAM_ID"), name="SRS")


# ── Champion identification ────────────────────────────────────────────────────

def identify_champion(playoff_logs: pd.DataFrame) -> int:
    """Return TEAM_ID of the season champion (team with most playoff wins).

    Works across formats: pre-2003 champions won 15 games; post-2003 won 16.
    Only the champion reaches 15 or 16 wins, so argmax is unambiguous.
    """
    wins = playoff_logs[playoff_logs["WL"] == "W"]["TEAM_ID"].value_counts()
    return int(wins.idxmax())


# ── Conference / game pairing ────────────────────────────────────────────────────

def team_conference_map(standings: pd.DataFrame) -> dict:
    """{TeamID: Conference} from a LeagueStandingsV3 standings frame."""
    return standings.set_index("TeamID")["Conference"].to_dict()


def iter_game_pairs(df: pd.DataFrame):
    """Yield (row_a, row_b) for each GAME_ID with exactly two team rows.

    Game logs carry one row per team per game; this pairs the two rows so
    callers can compare the two sides (winner/loser, conference matchup, etc.).
    """
    for _, grp in df.groupby("GAME_ID"):
        if len(grp) == 2:
            yield grp.iloc[0], grp.iloc[1]


# ── Generic endpoint caching ─────────────────────────────────────────────────────

def is_rate_limit_error(exc: Exception) -> bool:
    """True if an exception looks like API throttling (timeout, 429, or a
    dropped connection) rather than a genuine, permanent data error."""
    import requests
    if isinstance(exc, (requests.exceptions.Timeout,
                        requests.exceptions.ConnectionError)):
        return True
    msg = str(exc).lower()
    return "429" in msg or "rate limit" in msg or "timed out" in msg


def fetch_cached_csv(path: str, build_df, keep_cols: list[str], *,
                     id_col: str = "TEAM_ID",
                     sleep_sec: float = 1.0) -> pd.DataFrame | None:
    """Cache one DataFrame build to CSV, keeping id_col + keep_cols.

    On a cache hit, returns the cached frame (None if it was an empty miss).
    On a miss, calls build_df(); any exception or an empty/id-less result is
    cached as an empty CSV so unavailable pulls aren't retried.
    """
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            return None
        return df if not df.empty else None

    os.makedirs(os.path.dirname(path), exist_ok=True)
    try:
        df = build_df()
    except Exception as e:
        print(f"    ERROR fetching {os.path.basename(path)}: {e}")
        pd.DataFrame().to_csv(path, index=False)
        return None

    if df.empty or id_col not in df.columns:
        pd.DataFrame().to_csv(path, index=False)
        return None

    present = [id_col] + [c for c in keep_cols if c in df.columns and c != id_col]
    df = df[present].copy()
    df.to_csv(path, index=False)
    time.sleep(sleep_sec)
    return df


# ── Player / team season-stat fetchers (for ratings recompute) ─────────────────

def fetch_player_season_totals(end_year: int,
                               season_type: str = REGULAR_SEASON,
                               cache_dir: str | None = None) -> pd.DataFrame:
    """Season totals for all players via LeagueDashPlayerStats (Totals mode).

    One row per player. Key columns: PLAYER_ID, PLAYER_NAME, TEAM_ID, TEAM_ABBREVIATION,
    GP, MIN, PTS, REB, AST, STL, BLK, TOV, FGM, FGA, FG3M, FG3A, FTM, FTA,
    OREB, DREB, PF, PLUS_MINUS.
    """
    d = cache_dir or default_cache_dir()
    slug = season_type.replace(" ", "_")
    path = os.path.join(d, f"player_totals_{season_str(end_year)}_{slug}.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    os.makedirs(d, exist_ok=True)
    from nba_api.stats.endpoints import leaguedashplayerstats
    df = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season_str(end_year),
        season_type_all_star=season_type,
        per_mode_detailed="Totals",
        measure_type_detailed_defense="Base",
        league_id_nullable="00",
        timeout=60,
    ).get_data_frames()[0]
    df.to_csv(path, index=False)
    time.sleep(SLEEP_SEC)
    return df


def fetch_player_season_per100(end_year: int,
                                season_type: str = REGULAR_SEASON,
                                cache_dir: str | None = None) -> pd.DataFrame:
    """Per-100-possession rates for all players (for BPM inputs).

    Same endpoint as totals but per_mode_detailed='Per100Possessions'.
    """
    d = cache_dir or default_cache_dir()
    slug = season_type.replace(" ", "_")
    path = os.path.join(d, f"player_per100_{season_str(end_year)}_{slug}.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    os.makedirs(d, exist_ok=True)
    from nba_api.stats.endpoints import leaguedashplayerstats
    df = leaguedashplayerstats.LeagueDashPlayerStats(
        season=season_str(end_year),
        season_type_all_star=season_type,
        per_mode_detailed="Per100Possessions",
        measure_type_detailed_defense="Base",
        league_id_nullable="00",
        timeout=60,
    ).get_data_frames()[0]
    df.to_csv(path, index=False)
    time.sleep(SLEEP_SEC)
    return df


def fetch_team_season_totals(end_year: int,
                              season_type: str = REGULAR_SEASON,
                              cache_dir: str | None = None) -> pd.DataFrame:
    """Season totals for all teams via LeagueDashTeamStats (Totals mode).

    One row per team. Key columns: TEAM_ID, TEAM_NAME, GP, W, L, MIN,
    PTS, REB, AST, STL, BLK, TOV, FGM, FGA, FG3M, FG3A, FTM, FTA, OREB, DREB, PF.
    """
    d = cache_dir or default_cache_dir()
    slug = season_type.replace(" ", "_")
    path = os.path.join(d, f"team_totals_{season_str(end_year)}_{slug}.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    os.makedirs(d, exist_ok=True)
    from nba_api.stats.endpoints import leaguedashteamstats
    df = leaguedashteamstats.LeagueDashTeamStats(
        season=season_str(end_year),
        season_type_all_star=season_type,
        per_mode_detailed="Totals",
        measure_type_detailed_defense="Base",
        league_id_nullable="00",
        timeout=60,
    ).get_data_frames()[0]
    df.to_csv(path, index=False)
    time.sleep(SLEEP_SEC)
    return df


def fetch_league_averages(end_year: int,
                           season_type: str = REGULAR_SEASON,
                           cache_dir: str | None = None) -> dict:
    """League-average context needed by PER and Win Shares formulas.

    Derived from the team-totals frame so no extra API call is needed.
    Returns a dict with keys: lg_pts, lg_ast, lg_oreb, lg_dreb, lg_reb,
    lg_stl, lg_blk, lg_tov, lg_pf, lg_fgm, lg_fga, lg_ftm, lg_fta,
    lg_fg3m, lg_fg3a, lg_min, lg_pace, lg_orb_pct.
    """
    import numpy as np
    d = cache_dir or default_cache_dir()
    slug = season_type.replace(" ", "_")
    path = os.path.join(d, f"league_avg_{season_str(end_year)}_{slug}.csv")
    if os.path.exists(path):
        row = pd.read_csv(path).iloc[0].to_dict()
        return row
    team_df = fetch_team_season_totals(end_year, season_type, cache_dir)
    lg: dict = {}
    for col in ["PTS", "AST", "OREB", "DREB", "REB", "STL", "BLK", "TOV", "PF",
                "FGM", "FGA", "FTM", "FTA", "FG3M", "FG3A", "MIN"]:
        lg[f"lg_{col.lower()}"] = float(team_df[col].sum()) if col in team_df.columns else 0.0
    # Pace: total possessions per 48 minutes per team, simplified as pts-based estimate
    # Use FGA + 0.44*FTA - OREB + TOV as possession estimate per team
    n_teams = len(team_df)
    if all(c in team_df.columns for c in ["FGA", "FTA", "OREB", "TOV", "GP"]):
        team_poss = team_df["FGA"] + 0.44 * team_df["FTA"] - team_df["OREB"] + team_df["TOV"]
        lg["lg_pace"] = float((team_poss / team_df["GP"]).mean()) if n_teams > 0 else 100.0
    else:
        lg["lg_pace"] = 100.0
    lg["lg_orb_pct"] = (lg["lg_oreb"] / (lg["lg_oreb"] + lg.get("lg_dreb", 1))) if lg.get("lg_dreb", 0) > 0 else 0.25
    pd.DataFrame([lg]).to_csv(path, index=False)
    return lg


# ── Shot-zone and referee fetchers (generic nba_api endpoint wrappers) ──────────

# LeagueDashTeamShotLocations returns a MultiIndex (zone, stat); flatten the FGA
# column of each zone to a flat name so the cached CSV round-trips cleanly.
SHOT_ZONE_FGA_COLS = {
    ("Restricted Area",       "FGA"): "FGA_RA",
    ("In The Paint (Non-RA)", "FGA"): "FGA_NON_RA",
    ("Mid-Range",             "FGA"): "FGA_MR",
    ("Left Corner 3",         "FGA"): "FGA_LC3",
    ("Right Corner 3",        "FGA"): "FGA_RC3",
    ("Above the Break 3",     "FGA"): "FGA_ATB3",
    ("Backcourt",             "FGA"): "FGA_BC",
}


def fetch_shot_zones(end_year: int, season_type: str, location: str, *,
                     cache_dir: str | None = None,
                     sleep: float = SLEEP_SEC) -> "pd.DataFrame | None":
    """Team-level shot-zone FGA totals from LeagueDashTeamShotLocations, split by
    location ('Home' or 'Road'). Cached as shot_zones_*.csv. Returns None on an
    empty/error result (the miss is cached so it is not retried)."""
    cache_dir = cache_dir or default_cache_dir()
    path = os.path.join(
        cache_dir,
        f"shot_zones_{season_str(end_year)}_{season_type.replace(' ', '_')}_{location}.csv",
    )
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            return None
        return df if not df.empty else None

    os.makedirs(cache_dir, exist_ok=True)
    try:
        from nba_api.stats.endpoints import leaguedashteamshotlocations
        result = leaguedashteamshotlocations.LeagueDashTeamShotLocations(
            season=season_str(end_year),
            season_type_all_star=season_type,
            location_nullable=location,
            per_mode_detailed="Totals",
            timeout=60,
        )
        df = result.get_data_frames()[0]
    except Exception as e:
        print(f"    ERROR fetching shot zones {season_str(end_year)} {season_type} {location}: {e}")
        pd.DataFrame().to_csv(path, index=False)  # cache the miss so we don't retry
        return None

    if df.empty:
        pd.DataFrame().to_csv(path, index=False)
        return None

    id_map = {("", "TEAM_ID"): "TEAM_ID", ("", "TEAM_NAME"): "TEAM_NAME"}
    col_map = {**id_map, **SHOT_ZONE_FGA_COLS}
    present = [c for c in col_map if c in df.columns]
    df = df[present].copy()
    df.columns = [col_map[c] for c in present]
    df.to_csv(path, index=False)
    time.sleep(sleep)
    return df


def fetch_referees(end_year: int, season_type: str, *,
                   game_ids=None, cache_dir: str | None = None,
                   sleep: float = SLEEP_SEC, officials_start_year: int = 2002,
                   known_empty_years=frozenset({2003})) -> "pd.DataFrame | None":
    """Officials for every game via BoxScoreSummaryV3 (data_sets[3]). Cached as
    referee_*.csv with [GAME_ID, personId, name]. On a cache hit returns the
    cached frame; otherwise needs ``game_ids`` (returns None without them). The
    empty-result handling distinguishes genuine absence (cache the miss) from a
    likely silent rate-limit, which is not cached so it retries next run."""
    cache_dir = cache_dir or default_cache_dir()
    cache_file = os.path.join(
        cache_dir, f"referee_{season_str(end_year)}_{season_type.replace(' ', '_')}.csv")
    if os.path.exists(cache_file):
        try:
            df = pd.read_csv(cache_file)
        except pd.errors.EmptyDataError:
            return None
        return df if not df.empty else None
    if not game_ids:
        return None

    from nba_api.stats.endpoints import boxscoresummaryv3
    records: list[dict] = []
    failed = rate_limited = 0
    game_ids = sorted(game_ids)
    print(f"  Fetching referee data: {season_str(end_year)} {season_type} "
          f"({len(game_ids)} games)...", flush=True)
    for i, gid in enumerate(game_ids, 1):
        gid_str = f"{int(float(gid)):010d}"
        try:
            b = boxscoresummaryv3.BoxScoreSummaryV3(game_id=gid_str, timeout=60)
            for _, row in b.data_sets[3].get_data_frame().iterrows():
                records.append({"GAME_ID": gid_str, "personId": int(row["personId"]),
                                "name": str(row["name"])})
        except Exception as e:
            failed += 1
            if is_rate_limit_error(e):
                rate_limited += 1
            if failed <= 3:
                print(f"    WARN {gid_str}: {e!r}")
        time.sleep(sleep)
        if i % 100 == 0:
            print(f"    ...{i}/{len(game_ids)}", flush=True)

    if failed:
        tag = f" — {rate_limited} look rate-limited" if rate_limited else ""
        print(f"    {failed} games failed (API errors){tag}")
    if rate_limited:
        print(f"    RATE LIMITED: {rate_limited} call(s) throttled this season.")

    os.makedirs(cache_dir, exist_ok=True)
    if not records:
        if failed:
            # No records *and* API errors: transient failure, not genuine absence.
            # Do not cache an empty file, or later runs would never retry.
            print("    No records and API errors occurred — not caching; will retry next run.")
            return None
        if end_year >= officials_start_year and end_year not in known_empty_years:
            # Every call returned empty with no error: the hallmark of a silent
            # rate-limit (empty 200 body) for a season that should carry data.
            print(f"    SUSPECT empty: {season_str(end_year)} should have officials "
                  f"data (>= {officials_start_year}) but returned none — likely a "
                  f"silent rate-limit. Not caching; will retry next run.")
            return None
        pd.DataFrame().to_csv(cache_file, index=False)  # genuine, permanent absence
        return None

    df = pd.DataFrame(records)
    df.to_csv(cache_file, index=False)
    return df


# ── Play-by-play (PlayByPlayV3) ────────────────────────────────────────────────

def fetch_pbp_players(end_year: int, season_type: str = REGULAR_SEASON, *,
                      cache_dir: str | None = None,
                      sleep: float = SLEEP_SEC) -> pd.DataFrame:
    """Player roster per game from BoxScoreTraditionalV3. One CSV per game.

    Returns a DataFrame with columns:
        game_id (str, zero-padded 10 digits), team_id (int),
        personId (int), familyName (str), is_starter (bool).

    is_starter=True for the 5 players whose ``position`` field is non-empty
    (starters have 'G', 'F', or 'C'; bench/DNP rows do not).
    Caches each game as ``boxscore_trad_{game_id}.csv``.
    """
    d = cache_dir or default_cache_dir()
    logs = fetch_game_logs(end_year, season_type, d)
    game_ids = sorted(logs["GAME_ID"].dropna().unique())

    all_records: list[dict] = []
    for gid in game_ids:
        gid_str = f"{int(float(gid)):010d}"
        path = os.path.join(d, f"boxscore_trad_{gid_str}.csv")
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
            except pd.errors.EmptyDataError:
                continue
            if not df.empty:
                all_records.extend(df.to_dict("records"))
            continue
        os.makedirs(d, exist_ok=True)
        try:
            from nba_api.stats.endpoints import boxscoretraditionalv3
            bs = boxscoretraditionalv3.BoxScoreTraditionalV3(
                game_id=gid_str, timeout=60)
            ps = bs.player_stats.get_data_frame()
        except Exception as e:
            print(f"    WARN boxscore {gid_str}: {e!r}")
            pd.DataFrame().to_csv(path, index=False)
            time.sleep(sleep)
            continue
        if ps.empty:
            pd.DataFrame().to_csv(path, index=False)
            time.sleep(sleep)
            continue
        rows = []
        for _, r in ps.iterrows():
            rows.append({
                "game_id": gid_str,
                "team_id": int(r["teamId"]),
                "personId": int(r["personId"]),
                "familyName": str(r.get("familyName", "")),
                "is_starter": bool(str(r.get("position", "")).strip()),
            })
        pd.DataFrame(rows).to_csv(path, index=False)
        all_records.extend(rows)
        time.sleep(sleep)
    return pd.DataFrame(all_records) if all_records else pd.DataFrame(
        columns=["game_id", "team_id", "personId", "familyName", "is_starter"])


def fetch_pbp(end_year: int, season_type: str = REGULAR_SEASON, *,
              cache_dir: str | None = None,
              sleep: float = SLEEP_SEC) -> pd.DataFrame:
    """Fetch PlayByPlayV3 events for a full season, one CSV per game.

    PlayByPlayV2 is deprecated for 2024-25+; this always uses V3.
    Game IDs come from fetch_game_logs (reuses the shared season cache).
    Each game is cached as ``pbp_v3_{game_id}.csv`` so a partial run
    resumes without re-fetching completed games.

    Returns a concatenated DataFrame with V3 columns:
        gameId, actionNumber, clock, period, teamId, personId, playerName,
        scoreHome, scoreAway, pointsTotal, description, actionType, subType,
        shotValue, actionId, ...
    """
    d = cache_dir or default_cache_dir()
    logs = fetch_game_logs(end_year, season_type, d)
    game_ids = sorted(logs["GAME_ID"].dropna().unique())

    all_dfs: list[pd.DataFrame] = []
    n = len(game_ids)
    print(f"  Fetching PBP: {season_str(end_year)} {season_type} ({n} games)...",
          flush=True)
    failed = rate_limited = 0
    for i, gid in enumerate(game_ids, 1):
        gid_str = f"{int(float(gid)):010d}"
        path = os.path.join(d, f"pbp_v3_{gid_str}.csv")
        if os.path.exists(path):
            try:
                df = pd.read_csv(path)
            except pd.errors.EmptyDataError:
                continue
            if not df.empty:
                all_dfs.append(df)
            continue
        os.makedirs(d, exist_ok=True)
        try:
            from nba_api.stats.endpoints import playbyplayv3
            pbp = playbyplayv3.PlayByPlayV3(
                game_id=gid_str, timeout=60).play_by_play.get_data_frame()
        except Exception as e:
            failed += 1
            if is_rate_limit_error(e):
                rate_limited += 1
                time.sleep(sleep * 5)
            if failed <= 3:
                print(f"    WARN {gid_str}: {e!r}")
            pd.DataFrame().to_csv(path, index=False)
            time.sleep(sleep)
            continue
        if pbp.empty:
            pd.DataFrame().to_csv(path, index=False)
            time.sleep(sleep)
            continue
        pbp.to_csv(path, index=False)
        all_dfs.append(pbp)
        time.sleep(sleep)
        if i % 100 == 0:
            print(f"    ...{i}/{n}", flush=True)

    if failed:
        tag = f" ({rate_limited} rate-limited)" if rate_limited else ""
        print(f"    {failed} games failed{tag}")
    return pd.concat(all_dfs, ignore_index=True) if all_dfs else pd.DataFrame()


# ── Lineup/possession reconstruction ──────────────────────────────────────────

def _parse_sub_in_name(description: str) -> str:
    """'SUB: Rupert FOR Thybulle' → 'rupert' (lower-case family name)."""
    desc = str(description)
    if desc.startswith("SUB: ") and " FOR " in desc:
        return desc[5:desc.index(" FOR ")].strip().lower()
    return ""


def _is_last_ft(subtype: str) -> bool:
    """True if this FT is the final attempt in a sequence ('X of X')."""
    s = str(subtype)
    parts = s.split(" of ")
    if len(parts) == 2:
        try:
            return int(parts[-2][-1]) == int(parts[-1])
        except (ValueError, IndexError):
            return False
    return False


def _build_name_lookup(game_pbp: pd.DataFrame,
                       game_players: pd.DataFrame | None) -> dict[tuple, int]:
    """Return {(team_id, family_name_lower): personId} for one game.

    Merges two sources:
    1. Non-substitution PBP events (player took an action → ID is in the row).
    2. players_df rows for the game (box-score roster, more complete).
    """
    lookup: dict[tuple, int] = {}
    # Source 1: observed events
    obs = game_pbp[(game_pbp["personId"].fillna(0).astype(float) > 0) &
                   (game_pbp["actionType"] != "Substitution")]
    for _, r in obs.iterrows():
        tid = int(float(r["teamId"])) if float(str(r["teamId"]).replace("nan", "0") or 0) > 0 else 0
        pid = int(float(r["personId"]))
        name = str(r.get("playerName", "")).strip().lower()
        if tid and pid and name:
            # playerName in V3 is family name only
            lookup[(tid, name)] = pid
    # Source 2: box-score roster (covers players who took no stat actions)
    if game_players is not None and not game_players.empty:
        for _, r in game_players.iterrows():
            tid = int(r["team_id"])
            pid = int(r["personId"])
            fname = str(r["familyName"]).strip().lower()
            if tid and pid and fname:
                lookup[(tid, fname)] = pid
    return lookup


def _infer_starters(period_events: pd.DataFrame,
                    team_ids: list[int]) -> dict[int, set]:
    """Infer period-start lineup for each team from first player appearances.

    For each team, collect the player IDs seen before the first substitution
    for that team. If < 5 are found, fill with any subsequently seen player
    until we have 5 (best-effort; warns if we can't reach 5).
    """
    starters: dict[int, set] = {t: set() for t in team_ids}
    first_sub_seen: dict[int, bool] = {t: False for t in team_ids}
    all_seen: dict[int, set] = {t: set() for t in team_ids}

    for _, row in period_events.iterrows():
        tid = int(float(row.get("teamId", 0) or 0))
        pid = int(float(row.get("personId", 0) or 0))
        action = str(row.get("actionType", ""))
        if tid not in team_ids or pid <= 0:
            continue
        all_seen[tid].add(pid)
        if action == "Substitution":
            first_sub_seen[tid] = True
            # The OUT player was definitely on court before this sub
            starters[tid].add(pid)
        elif not first_sub_seen[tid]:
            starters[tid].add(pid)

    # Fill to 5 using players seen anywhere in the period
    for t in team_ids:
        if len(starters[t]) < 5:
            for pid in all_seen[t]:
                if len(starters[t]) >= 5:
                    break
                starters[t].add(pid)
        if len(starters[t]) < 5:
            import warnings
            warnings.warn(
                f"Could not infer 5 starters for team {t}; "
                f"found {len(starters[t])}. Pass players_df for accuracy.")
    return starters


def reconstruct_possessions(pbp_df: pd.DataFrame,
                            players_df: pd.DataFrame | None = None
                            ) -> pd.DataFrame:
    """Reconstruct on-court lineups and possession outcomes. Pure function.

    Parameters
    ----------
    pbp_df:
        PlayByPlayV3 events, as returned by fetch_pbp. Must contain columns:
        gameId, period, teamId, personId, playerName, actionType, subType,
        description, shotValue, scoreHome, scoreAway.
    players_df:
        Optional roster from fetch_pbp_players. Columns:
        game_id, team_id, personId, familyName, is_starter.
        Improves substitution-in-player resolution and starter accuracy.
        If None, starters are inferred from first observed actions per period.

    Returns
    -------
    DataFrame with one row per possession:
        game_id, period, off_team_id,
        off_player_1 … off_player_5,
        def_player_1 … def_player_5,
        points, possession (always 1).

    Games where any period cannot be reconciled to 5-on-5 are dropped with
    a warning rather than emitting corrupt lineup data.
    """
    import warnings

    _OFF = [f"off_player_{i}" for i in range(1, 6)]
    _DEF = [f"def_player_{i}" for i in range(1, 6)]
    cols = ["game_id", "period", "off_team_id"] + _OFF + _DEF + ["points", "possession"]
    records: list[dict] = []

    if pbp_df.empty or "gameId" not in pbp_df.columns:
        return pd.DataFrame(columns=cols)

    for game_id, game_pbp in pbp_df.groupby("gameId"):
        game_id_str = str(game_id)
        game_pbp = game_pbp.sort_values("actionNumber").reset_index(drop=True)

        # Build name→ID lookup for this game
        gp = None
        if players_df is not None and not players_df.empty:
            gp = players_df[players_df["game_id"] == game_id_str]
            if gp.empty:
                gp = None
        name_lookup = _build_name_lookup(game_pbp, gp)

        # Identify the two teams
        team_ids = [int(float(t)) for t in game_pbp["teamId"].dropna().unique()
                    if float(str(t).replace("nan", "0") or 0) > 0]
        team_ids = sorted(set(team_ids))
        if len(team_ids) < 2:
            warnings.warn(f"Game {game_id_str}: found {len(team_ids)} teams, skipping.")
            continue

        # Starters for period 1 from players_df (is_starter=True)
        p1_starters: dict[int, set] = {}
        if gp is not None:
            for tid in team_ids:
                s = set(int(r["personId"]) for _, r in gp[
                    (gp["team_id"] == tid) & (gp["is_starter"] == True)
                ].iterrows())
                if len(s) == 5:
                    p1_starters[tid] = s

        game_ok = True
        # Lineups carry across periods; initialised at each period start
        carry_lineups: dict[int, set] = {}

        for period, period_pbp in game_pbp.groupby("period"):
            period_pbp = period_pbp.reset_index(drop=True)

            # Determine starting lineups for this period
            if period == 1 and all(t in p1_starters for t in team_ids):
                lineups: dict[int, set] = {t: set(p1_starters[t]) for t in team_ids}
            elif carry_lineups and all(t in carry_lineups for t in team_ids):
                lineups = {t: set(carry_lineups[t]) for t in team_ids}
            else:
                # Fall back to inference
                lineups = _infer_starters(period_pbp, team_ids)

            # Validate and clamp to 5
            for t in team_ids:
                if len(lineups[t]) != 5:
                    if len(lineups[t]) > 5:
                        lineups[t] = set(list(lineups[t])[:5])
                    # < 5: continue and let observation-reconciliation fill it

            ball_team: int | None = None
            other_team_of = {team_ids[0]: team_ids[1], team_ids[1]: team_ids[0]}
            poss_pts = 0
            period_records: list[dict] = []
            period_ok = True

            def _emit(b_team: int) -> None:
                nonlocal poss_pts
                if b_team not in lineups or other_team_of.get(b_team) not in lineups:
                    return
                off_l = sorted(lineups[b_team])
                def_l = sorted(lineups[other_team_of[b_team]])
                if len(off_l) != 5 or len(def_l) != 5:
                    return  # incomplete lineup; skip possession
                row = {"game_id": game_id_str, "period": int(period),
                       "off_team_id": b_team, "points": poss_pts, "possession": 1}
                for j, pid in enumerate(off_l, 1):
                    row[f"off_player_{j}"] = pid
                for j, pid in enumerate(def_l, 1):
                    row[f"def_player_{j}"] = pid
                period_records.append(row)
                poss_pts = 0

            def _reconcile_player(tid: int, pid: int) -> None:
                """Add pid to lineup if missing; drop least-recently-added if full."""
                if pid in lineups[tid]:
                    return
                if len(lineups[tid]) < 5:
                    lineups[tid].add(pid)
                else:
                    # Drop the player with the smallest ID (arbitrary but stable)
                    victim = min(lineups[tid] - {pid})
                    lineups[tid].discard(victim)
                    lineups[tid].add(pid)

            for _, ev in period_pbp.iterrows():
                action = str(ev.get("actionType", ""))
                subtype = str(ev.get("subType", ""))
                tid_raw = ev.get("teamId", 0)
                pid_raw = ev.get("personId", 0)
                try:
                    tid = int(float(tid_raw)) if float(str(tid_raw).replace("nan","0") or 0) > 0 else 0
                    pid = int(float(pid_raw)) if float(str(pid_raw).replace("nan","0") or 0) > 0 else 0
                except (ValueError, TypeError):
                    tid = pid = 0

                if action == "period":
                    if subtype == "end":
                        if ball_team is not None:
                            _emit(ball_team)
                            ball_team = None
                    continue

                if action == "Jump Ball" and period == 1:
                    # "Jump Ball X vs. Y: Tip to Z" — find Z's team
                    desc = str(ev.get("description", ""))
                    if "Tip to " in desc:
                        tip_name = desc.split("Tip to ")[-1].strip().lower()
                        for lt in team_ids:
                            if (lt, tip_name) in name_lookup:
                                ball_team = lt
                                break
                        if ball_team is None and tid in team_ids:
                            # fallback: team in the jump ball row
                            ball_team = tid
                    continue

                if action == "Substitution":
                    # OUT: personId; IN: parse from description
                    if tid in team_ids and pid > 0:
                        lineups[tid].discard(pid)
                    in_name = _parse_sub_in_name(str(ev.get("description", "")))
                    in_pid = name_lookup.get((tid, in_name), 0) if tid in team_ids else 0
                    if tid in team_ids and in_pid > 0:
                        lineups[tid].add(in_pid)
                    continue

                # V3 team rebounds/turnovers: teamId=0, personId=TEAM_ID.
                # Resolve the acting team from whichever field is non-zero.
                acting_team = tid if tid in team_ids else (
                    pid if pid in team_ids else 0)

                # For player events: reconcile and infer ball_team.
                if tid in team_ids and pid > 0:
                    _reconcile_player(tid, pid)
                    if ball_team is None and action in (
                            "Made Shot", "Missed Shot", "Turnover", "Free Throw"):
                        ball_team = tid

                if action == "Made Shot":
                    if ball_team is None:
                        ball_team = tid
                    try:
                        sv = int(float(ev.get("shotValue", 2) or 2))
                    except (ValueError, TypeError):
                        sv = 2
                    poss_pts += sv
                    _emit(ball_team)
                    ball_team = other_team_of.get(ball_team)

                elif action == "Free Throw":
                    # Skip technical FTs (possession doesn't belong to FT shooter
                    # in the standard sense; the game resumes for the original
                    # possessing team). Technical FTs don't end a possession.
                    is_tech = "Technical" in subtype
                    made = "MISS" not in str(ev.get("description", ""))
                    if not is_tech and made:
                        poss_pts += 1
                    if not is_tech and _is_last_ft(subtype) and ball_team is not None:
                        if made:
                            _emit(ball_team)
                            ball_team = other_team_of.get(ball_team)
                        # Missed last FT: rebound will close the possession

                elif action == "Rebound":
                    # Use acting_team (handles teamId=0, personId=TEAM_ID team rebds)
                    reb_team = acting_team
                    if reb_team and ball_team is not None:
                        if reb_team != ball_team:
                            # Defensive rebound: possession ends
                            _emit(ball_team)
                            ball_team = reb_team
                        # Offensive rebound: same possession continues

                elif action == "Turnover":
                    # acting_team = the team that turned it over
                    to_team = acting_team if acting_team else tid
                    if ball_team is None and to_team:
                        ball_team = to_team
                    if ball_team is not None:
                        _emit(ball_team)
                        ball_team = other_team_of.get(ball_team)

            # Check lineup integrity for this period
            for t in team_ids:
                if len(lineups[t]) != 5:
                    period_ok = False
                    break

            if not period_ok:
                warnings.warn(
                    f"Game {game_id_str} period {period}: lineup not reconciled "
                    f"to 5-on-5 — dropping game.")
                game_ok = False
                break

            carry_lineups = {t: set(lineups[t]) for t in team_ids}
            records.extend(period_records)

        if not game_ok:
            # Remove any records emitted for this game before the bad period
            records = [r for r in records if r["game_id"] != game_id_str]

    return pd.DataFrame(records, columns=cols) if records else pd.DataFrame(columns=cols)
