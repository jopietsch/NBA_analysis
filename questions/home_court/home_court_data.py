"""
home_court_data.py — data pipeline for NBA home court advantage analysis.

Fetches game logs from NBA.com via nba_api, caches them as CSVs, and provides
fetch_* and compute_* functions consumed by home_court_plots and
home_court_analysis.

Data sources:
  - NBA.com via the nba_api package (LeagueGameFinder etc.): every game result,
    1983-84 through 2025-26
  - Basketball-Reference (scraped): per-game attendance, ~1999-2000 onward
    (NBA.com does not expose attendance)
"""

import os
import sys
import time
import pandas as pd
import numpy as np

from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.library.parameters import SeasonType

import nbakit.data as _nbakit
from nbakit.teams import ALTITUDE_TEAMS, TEAM_TIMEZONES, ARENA_COORDS, haversine
from nbakit import bbr as _bbr


# ── Config ────────────────────────────────────────────────────────────────────
START_YEAR = 1984   # season ending in this year = 1983-84
END_YEAR   = 2026   # season ending in this year = 2025-26
SLEEP_SEC  = 1.0    # polite pause between API calls

# Basketball-Reference attendance scrape (NBA.com does not expose attendance).
# Per-game attendance is only reliably populated from ~1999-2000 onward, so the
# attendance series is ~25 seasons, not the full 40.
BBR_START_YEAR  = 2000   # first season with reliable per-game attendance
BBR_SLEEP_SEC   = 6.0    # ~10 req/min — BBR 429s near its 20/min ceiling, so stay well under
BBR_BACKOFF_SEC = 45.0   # base wait after a 429 before retrying (grows per attempt)
BBR_MAX_RETRIES = 3      # retries on a 429 before giving up (season retries next run)
BBR_BASE       = "https://www.basketball-reference.com"
BBR_HEADERS    = {  # BBR blocks the default python-requests UA
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
    )
}

# BoxScoreSummaryV3 carries no officials before the 2001-02 playoffs (verified:
# every game pre-2002 returns an empty officials set). A 0-record result for a
# season at or after this year is therefore suspect — the signature of a silent
# rate-limit (an empty 200 body), not genuine absence — and must not be cached.
OFFICIALS_DATA_START_YEAR = 2002

# Exception to the rule above: a handful of in-range seasons genuinely have no
# officials in the endpoint (verified empty across many retries, not flaky). These
# are treated as real absence — cached as an empty marker — so they don't retry
# forever and leak fetch output into captured reports. {2003} = the 2002-03 gap.
OFFICIALS_KNOWN_EMPTY_YEARS = {2003}

# 2020 bubble playoffs: all games at neutral site — exclude from playoff stats
SKIP_PLAYOFF_YEARS = {2020}

# Seasons with limited/no fans (COVID) — highlighted in the chart
COVID_SEASONS = {"19–20", "20–21"}

# Shared monorepo cache — override with NBA_CACHE_DIR env var
CACHE_DIR = _nbakit.default_cache_dir()

# Season helpers — delegated to nbakit so improvements propagate to all questions
season_str = _nbakit.season_str
short_label = _nbakit.short_label


def season_range_label() -> str:
    """'1983–84 through 2025–26' — derived from START_YEAR/END_YEAR."""
    return _nbakit.season_range_label(START_YEAR, END_YEAR)


def cache_path(end_year: int, season_type: str) -> str:
    """Path to cached CSV; uses CACHE_DIR (patchable in tests via monkeypatch)."""
    return _nbakit.cache_path(end_year, season_type, cache_dir=CACHE_DIR)


def fetch_season_home_pct(end_year: int, season_type: str) -> float | None:
    """
    Pull every game log for one season/type, keep only home games,
    and return the fraction won.

    nba_api returns one row per team per game.  For a home game the
    MATCHUP field looks like  'BOS vs. MIA'  (vs. = home)
    and for away games        'BOS @ MIA'    (@ = away).
    WL is 'W' or 'L'.

    Game logs are cached as CSVs under CACHE_DIR so repeat runs don't
    re-fetch from NBA.com.
    """
    season = season_str(end_year)
    path = cache_path(end_year, season_type)

    if os.path.exists(path):
        df = pd.read_csv(path)
    else:
        try:
            finder = leaguegamefinder.LeagueGameFinder(
                season_nullable=season,
                season_type_nullable=season_type,
                timeout=60,
            )
            df = finder.get_data_frames()[0]
        except Exception as e:
            print(f"    ERROR fetching {season} {season_type}: {e}")
            return None

        os.makedirs(CACHE_DIR, exist_ok=True)
        df.to_csv(path, index=False)
        time.sleep(SLEEP_SEC)  # polite pause, only needed after a real API call

    if df.empty:
        return None

    # Home games have 'vs.' in MATCHUP
    home = df[df["MATCHUP"].str.contains(" vs. ", regex=False, na=False)].copy()
    if home.empty:
        return None

    wins  = (home["WL"] == "W").sum()
    total = len(home)
    return round(100 * wins / total, 1)


# ── Era definitions ───────────────────────────────────────────────────────────
# Eras are bounded by major NBA rule changes affecting pace/defense. Sources:
#   - Hand-checking restrictions (1994-95): https://theballzone.com/when-was-hand-checking-banned-in-the-nba/
#   - Illegal defense eliminated / zone legalized / defensive 3-sec (2001-02):
#       https://en.wikipedia.org/wiki/Defensive_three-second_violation
#   - Perimeter hand-checking ban (2004-05):
#       https://www.basketballnetwork.net/old-school/how-removing-the-hand-check-rule-changed-the-nba-forever
#   - Freedom-of-movement emphasis (2017-18) / transition take-foul rule (2022-23):
#       https://videorulebook.nba.com/rule/transition-take-fouls/
ERA_DEFS = [
    ("1984–94", 1984, 1994, "Illegal defense rules (no zone defense)"),
    ("1995–01", 1995, 2001, "Hand-checking restrictions; zone still illegal"),
    ("2002–04", 2002, 2004, "Zone defense legalized, defensive 3-sec added"),
    ("2005–17", 2005, 2017, "Perimeter hand-checking banned (pace-and-space)"),
    ("2018–22", 2018, 2022, "Freedom-of-movement emphasis"),
    (f"2023–{str(END_YEAR)[-2:]}", 2023, END_YEAR, "Transition take-foul rule added"),
]

# Playoff series-format / scheduling changes (separate from the defensive-rule
# eras above — these only affect the playoff data). Marked as vertical lines
# on the playoffs panel rather than background shading to avoid clutter.
# Sources:
#   - 1985: Finals move to 2-3-2 format; home-court advantage based on
#       regular-season record instead of alternating by conference:
#       https://en.wikipedia.org/wiki/2%E2%80%933%E2%80%932_format
#   - 2003: First round expanded from best-of-5 to best-of-7:
#       https://en.wikipedia.org/wiki/NBA_playoffs
#   - 2014: Finals revert to 2-2-1-1-1 (same format as all other rounds):
#       https://en.wikipedia.org/wiki/2%E2%80%933%E2%80%932_format
PLAYOFF_FORMAT_CHANGES = [
    (1985, "'85: Finals → 2-3-2,\nhome court by record"),
    (2003, "'03: Round 1 →\nbest-of-7"),
    (2014, "'14: Finals →\n2-2-1-1-1"),
]

# Playoff format "periods" — the spans of seasons between the format changes
# above, used to bucket playoff home win % by which format was in effect.
PLAYOFF_FORMAT_PERIODS = [
    ("1984",     1984, 1984, "Best-of-5 R1, 2-2-1-1-1 Finals (alternating home court)"),
    ("1985–02",  1985, 2002, "Best-of-5 R1, 2-3-2 Finals (home court by record)"),
    ("2003–13",  2003, 2013, "Best-of-7 R1, 2-3-2 Finals"),
    (f"2014–{str(END_YEAR)[-2:]}", 2014, END_YEAR, "Best-of-7 R1, 2-2-1-1-1 Finals"),
]


# Short season label ('83–84') → ending year. Lives in nbakit.data now.
label_to_year = _nbakit.label_to_year


def fetch_all_seasons() -> tuple[list[str], list[float], list[str], list[float]]:
    """Fetch home win % for every season/type in [START_YEAR, END_YEAR]."""
    print("Fetching NBA data via nba_api (NBA.com)...")
    print(f"Seasons: {season_str(START_YEAR)} → {season_str(END_YEAR)}")
    print("(~2 API calls per season, should take 2–4 minutes)\n")

    reg_seasons:  list[str]   = []
    reg_pcts:     list[float] = []
    po_seasons:   list[str]   = []
    po_pcts:      list[float] = []

    for year in range(START_YEAR, END_YEAR + 1):
        label = short_label(year)

        # Regular season
        pct = fetch_season_home_pct(year, SeasonType.regular)
        if pct is not None:
            reg_seasons.append(label)
            reg_pcts.append(pct)

        # Playoffs
        if year not in SKIP_PLAYOFF_YEARS:
            pct_po = fetch_season_home_pct(year, "Playoffs")
            if pct_po is not None:
                po_seasons.append(label)
                po_pcts.append(pct_po)

    print(f"\nRegular season: {len(reg_seasons)} seasons fetched")
    print(f"Playoffs:       {len(po_seasons)} seasons fetched")

    return reg_seasons, reg_pcts, po_seasons, po_pcts


def _compute_period_averages(
    period_defs: list,
    reg_seasons: list[str], reg_pcts: list[float],
    po_seasons: list[str], po_pcts: list[float],
) -> tuple[list[float], list[float], list[str]]:
    reg_avg = _nbakit.bucket_series_by_period(reg_seasons, reg_pcts, period_defs)
    po_avg  = _nbakit.bucket_series_by_period(po_seasons,  po_pcts,  period_defs)
    return reg_avg, po_avg, [p[0] for p in period_defs]


def compute_era_averages(
    reg_seasons: list[str], reg_pcts: list[float],
    po_seasons: list[str], po_pcts: list[float],
) -> tuple[list[float], list[float], list[str]]:
    """Average regular-season and playoff home win % within each era."""
    return _compute_period_averages(ERA_DEFS, reg_seasons, reg_pcts, po_seasons, po_pcts)


def compute_playoff_format_averages(
    reg_seasons: list[str], reg_pcts: list[float],
    po_seasons: list[str], po_pcts: list[float],
) -> tuple[list[float], list[float], list[str]]:
    """Average regular-season and playoff home win % within each playoff-format period."""
    return _compute_period_averages(PLAYOFF_FORMAT_PERIODS, reg_seasons, reg_pcts, po_seasons, po_pcts)


# ── Shared helpers for per-game analyses ─────────────────────────────────────
def _load_game_log(end_year: int, season_type: str) -> pd.DataFrame | None:
    """Load one season/type's cached game log (one row per team per game)."""
    path = cache_path(end_year, season_type)
    if not os.path.exists(path):
        return None

    df = pd.read_csv(path)
    if df.empty:
        return None
    return df


# Collapse a per-team-per-game log into one row per game (home/away joined on
# GAME_ID with '_home'/'_away' suffixes). Lives in nbakit.data now.
_merge_home_away_rows = _nbakit.merge_home_away_rows


# Add a REST column (days since each team's previous game minus 1; 0 = back-to-
# back). Lives in nbakit.data now.
_add_rest_days = _nbakit.add_rest_days


def bucket_stats_by_era(seasons: list[str], stats: dict) -> tuple[dict, list[str]]:
    """
    Average each per-season stat series within each rule-change era
    (ERA_DEFS). Works for any stats dict of the form {category: [per-season
    values]} — used by the margin analysis.
    """
    return _nbakit.bucket_stats_by_period(seasons, stats, ERA_DEFS)


def _align_to_seasons(
    ref_seasons: list[str], target_seasons: list[str],
    target_stats: dict, key: str,
) -> np.ndarray:
    """Align a per-season stat series to a reference season list, filling gaps with NaN."""
    lookup = {s: i for i, s in enumerate(target_seasons)}
    return np.array(
        [target_stats[key][lookup[s]] if s in lookup else np.nan for s in ref_seasons],
        dtype=float,
    )


def _iter_season_frames(start_year, end_year, season_type, skip_years, fetch):
    """Yield (year, frame) for each season that has cached data."""
    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        g = fetch(year, season_type)
        if g is None or g.empty:
            continue
        yield year, g


# Team geo reference data — ALTITUDE_TEAMS, TEAM_TIMEZONES, ARENA_COORDS, and
# haversine() — now live in nbakit.teams (imported at the top of this module).
# Used by the altitude, time-zone, and travel-distance analyses.
_haversine = haversine


# ── Box-score differential analysis ──────────────────────────────────────────

def _compute_box_differentials(merged: pd.DataFrame) -> pd.DataFrame:
    """Home-minus-away box-score differentials for fouls, free throws, and shooting."""
    fg3a_home = merged["FG3A_home"].replace(0, np.nan)
    fg3a_away = merged["FG3A_away"].replace(0, np.nan)
    fta_home  = merged["FTA_home"].replace(0, np.nan)
    fta_away  = merged["FTA_away"].replace(0, np.nan)
    return pd.DataFrame({
        "foul_diff":     merged["PF_home"] - merged["PF_away"],
        "fta_diff":      merged["FTA_home"] - merged["FTA_away"],
        "fg_pct_diff":   100 * (merged["FGM_home"] / merged["FGA_home"]
                                - merged["FGM_away"] / merged["FGA_away"]),
        "efg_pct_diff":  100 * ((merged["FGM_home"] + 0.5 * merged["FG3M_home"]) / merged["FGA_home"]
                                - (merged["FGM_away"] + 0.5 * merged["FG3M_away"]) / merged["FGA_away"]),
        "tpa_rate_diff": 100 * (merged["FG3A_home"] / merged["FGA_home"]
                                - merged["FG3A_away"] / merged["FGA_away"]),
        "fg3_pct_diff":  100 * (merged["FG3M_home"] / fg3a_home
                                - merged["FG3M_away"] / fg3a_away),
        "ft_pct_diff":   100 * (merged["FTM_home"]  / fta_home
                                - merged["FTM_away"]  / fta_away),
    })


def fetch_differential_data(end_year: int, season_type: str) -> pd.DataFrame | None:
    """
    Per-game home-minus-away differentials for fouls and shooting efficiency
    (shooting % in percentage points). Computed from raw M/A columns so games
    with zero attempts (e.g., 0 FG3A) become NaN rather than zero.
    """
    df = _load_game_log(end_year, season_type)
    if df is None:
        return None
    merged = _merge_home_away_rows(df)
    if merged is None:
        return None
    return _compute_box_differentials(merged)


def compute_differential_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], dict]:
    """Per-season mean home-minus-away differentials for fouls, free throws, and shooting %."""
    seasons: list[str] = []
    stats: dict[str, list[float]] = {
        "foul_diff": [], "fta_diff": [], "fg_pct_diff": [], "efg_pct_diff": [],
        "tpa_rate_diff": [], "fg3_pct_diff": [], "ft_pct_diff": [],
    }

    for year, g in _iter_season_frames(start_year, end_year, season_type, skip_years, fetch_differential_data):
        seasons.append(short_label(year))
        for key in stats:
            stats[key].append(g[key].mean(skipna=True))

    return seasons, stats


# ── Rebounding decomposition ──────────────────────────────────────────────────

def _compute_rebound_components(merged: pd.DataFrame) -> pd.DataFrame:
    """Home-minus-away rebounding components, plus rebound-share and league context.

    reb_share_edge is the home team's share of available offensive rebounds minus
    the away team's share (percentage points). Measuring rebounding as a share of
    available boards removes the pace/shot-volume confound that inflates raw counts.
    league_oreb_rate is the game's league-wide offensive-rebound rate (both teams) —
    the context that the home edge's decline tracks.
    """
    oreb_h, oreb_a = merged["OREB_home"], merged["OREB_away"]
    dreb_h, dreb_a = merged["DREB_home"], merged["DREB_away"]
    home_oreb_chance = (oreb_h + dreb_a).replace(0, np.nan)
    away_oreb_chance = (oreb_a + dreb_h).replace(0, np.nan)
    total_reb = (oreb_h + oreb_a + dreb_h + dreb_a).replace(0, np.nan)
    tov_h = merged["TOV_home"] if "TOV_home" in merged.columns else pd.Series(np.nan, index=merged.index)
    tov_a = merged["TOV_away"] if "TOV_away" in merged.columns else pd.Series(np.nan, index=merged.index)
    return pd.DataFrame({
        "oreb_diff":        oreb_h - oreb_a,
        "dreb_diff":        dreb_h - dreb_a,
        "reb_diff":         merged["REB_home"] - merged["REB_away"],
        "reb_share_edge":   100 * (oreb_h / home_oreb_chance - oreb_a / away_oreb_chance),
        "league_oreb_rate": 100 * (oreb_h + oreb_a) / total_reb,
        "oreb_rate_home":   100 * oreb_h / home_oreb_chance,
        "oreb_rate_away":   100 * oreb_a / away_oreb_chance,
        "tov_diff":         tov_h - tov_a,
    })


def fetch_rebound_data(end_year: int, season_type: str) -> pd.DataFrame | None:
    """Per-game home-minus-away rebounding components (see _compute_rebound_components)."""
    df = _load_game_log(end_year, season_type)
    if df is None:
        return None
    merged = _merge_home_away_rows(df)
    if merged is None:
        return None
    return _compute_rebound_components(merged)


def compute_rebound_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], dict]:
    """Per-season mean home-minus-away rebounding components."""
    seasons: list[str] = []
    stats: dict[str, list[float]] = {
        "oreb_diff": [], "dreb_diff": [], "reb_diff": [],
        "reb_share_edge": [], "league_oreb_rate": [],
        "oreb_rate_home": [], "oreb_rate_away": [],
        "tov_diff": [],
    }

    for year, g in _iter_season_frames(start_year, end_year, season_type, skip_years, fetch_rebound_data):
        seasons.append(short_label(year))
        for key in stats:
            stats[key].append(g[key].mean(skipna=True))

    return seasons, stats


# ── Player-tracking rebounding (mechanism, tracking era only) ─────────────────
# Tests *why* the home rebounding edge faded, using NBA player-tracking and
# hustle endpoints split Home vs Road (location_nullable). These cover only the
# tracking era (~2014 on; box-outs ~2016 on) — far shorter than the 40-year
# box-score series — so they corroborate the modern mechanism, not the full
# decline. Each metric's home edge = mean across teams of (home − road), so no
# per-game merge is needed.

TRACKING_START_YEAR = 2014  # 2013-14, first player-tracking season


def _fetch_tracking_cached(path: str, build_df, keep_cols: list[str]) -> pd.DataFrame | None:
    """Shared cache/error wrapper for one season/location tracking pull.

    Caches the miss (empty CSV) so unavailable seasons aren't re-fetched.
    """
    return _nbakit.fetch_cached_csv(path, build_df, keep_cols, sleep_sec=SLEEP_SEC)


def fetch_tracking_rebounding(end_year: int, location: str) -> pd.DataFrame | None:
    """Team rebound-tracking (LeagueDashPtStats, Rebounding), Home/Road split."""
    path = os.path.join(CACHE_DIR, f"tracking_reb_{season_str(end_year)}_{location}.csv")

    def build():
        from nba_api.stats.endpoints import leaguedashptstats
        return leaguedashptstats.LeagueDashPtStats(
            season=season_str(end_year), season_type_all_star="Regular Season",
            pt_measure_type="Rebounding", player_or_team="Team",
            per_mode_simple="PerGame", location_nullable=location, timeout=60,
        ).get_data_frames()[0]

    return _fetch_tracking_cached(path, build, ["OREB_CHANCE_PCT", "REB_CONTEST", "AVG_REB_DIST"])


def fetch_hustle_rebounding(end_year: int, location: str) -> pd.DataFrame | None:
    """Team hustle stats (LeagueHustleStatsTeam): box-outs etc., Home/Road split."""
    path = os.path.join(CACHE_DIR, f"tracking_hustle_{season_str(end_year)}_{location}.csv")

    def build():
        from nba_api.stats.endpoints import leaguehustlestatsteam
        return leaguehustlestatsteam.LeagueHustleStatsTeam(
            season=season_str(end_year), season_type_all_star="Regular Season",
            per_mode_time="PerGame", location_nullable=location, timeout=60,
        ).get_data_frames()[0]

    return _fetch_tracking_cached(path, build, ["BOX_OUTS", "OFF_BOXOUTS"])


def fetch_second_chance(end_year: int, location: str) -> pd.DataFrame | None:
    """Team Misc stats (LeagueDashTeamStats, Misc): second-chance points, Home/Road split."""
    path = os.path.join(CACHE_DIR, f"tracking_misc_{season_str(end_year)}_{location}.csv")

    def build():
        from nba_api.stats.endpoints import leaguedashteamstats
        return leaguedashteamstats.LeagueDashTeamStats(
            season=season_str(end_year), season_type_all_star="Regular Season",
            measure_type_detailed_defense="Misc", per_mode_detailed="PerGame",
            location_nullable=location, timeout=60,
        ).get_data_frames()[0]

    return _fetch_tracking_cached(path, build, ["PTS_2ND_CHANCE"])


def compute_tracking_rebound_stats(
    start_year: int = TRACKING_START_YEAR, end_year: int = END_YEAR,
) -> tuple[list[str], dict]:
    """Per-season home-minus-road tracking rebounding edges (regular season).

    Each edge is the mean across teams of (home metric − road metric). Seasons
    before a metric exists yield NaN. OREB_CHANCE_PCT is rescaled to percentage
    points; box-outs and second-chance points stay per game.
    """
    # (key, fetch_fn, source_column, scale)
    specs = [
        ("oreb_chance_pct_edge", fetch_tracking_rebounding, "OREB_CHANCE_PCT", 100.0),
        ("boxout_edge",          fetch_hustle_rebounding,   "BOX_OUTS",        1.0),
        ("second_chance_edge",   fetch_second_chance,       "PTS_2ND_CHANCE",  1.0),
    ]
    seasons: list[str] = []
    stats: dict[str, list[float]] = {key: [] for key, _, _, _ in specs}

    for year in range(start_year, end_year + 1):
        seasons.append(short_label(year))
        for key, fetch, col, scale in specs:
            home = fetch(year, "Home")
            road = fetch(year, "Road")
            if (home is None or road is None
                    or col not in home.columns or col not in road.columns):
                stats[key].append(np.nan)
                continue
            m = home[["TEAM_ID", col]].merge(
                road[["TEAM_ID", col]], on="TEAM_ID", suffixes=("_h", "_r"))
            stats[key].append(scale * (m[f"{col}_h"] - m[f"{col}_r"]).mean()
                              if len(m) else np.nan)

    return seasons, stats


def compute_league_3pa_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], list[float], list[float]]:
    """
    Per-season league-wide 3PA rate (% of all FGA) and home win %.
    Returns (seasons, tpa_rates, home_win_pcts).
    """
    seasons: list[str] = []
    tpa_rates: list[float] = []
    home_win_pcts: list[float] = []

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        df = _load_game_log(year, season_type)
        if df is None:
            continue
        total_fga = df["FGA"].sum()
        if total_fga == 0:
            continue
        tpa_rate = 100.0 * df["FG3A"].sum() / total_fga
        merged = _merge_home_away_rows(df)
        if merged is None:
            continue
        hw_pct = 100.0 * (merged["WL_home"] == "W").mean()
        seasons.append(short_label(year))
        tpa_rates.append(tpa_rate)
        home_win_pcts.append(hw_pct)

    return seasons, tpa_rates, home_win_pcts


def compute_league_pace_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], list[float], list[float]]:
    """
    Per-season league-wide pace (possessions per 48 min, per team) and home win %.
    Pace = (FGA − OREB + TOV + 0.44×FTA) / MIN × 240.
    Returns (seasons, pace_vals, home_win_pcts).
    """
    seasons: list[str] = []
    pace_vals: list[float] = []
    home_win_pcts: list[float] = []

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        df = _load_game_log(year, season_type)
        if df is None or df.empty:
            continue
        if not {"FGA", "OREB", "TOV", "FTA", "MIN"}.issubset(df.columns):
            continue
        df = df.copy()
        poss = df["FGA"] - df["OREB"] + df["TOV"] + 0.44 * df["FTA"]
        pace = poss * 240.0 / df["MIN"].replace(0, np.nan)
        avg_pace = float(pace.dropna().mean())
        if np.isnan(avg_pace):
            continue
        merged = _merge_home_away_rows(df)
        if merged is None:
            continue
        hw_pct = 100.0 * (merged["WL_home"] == "W").mean()
        seasons.append(short_label(year))
        pace_vals.append(avg_pace)
        home_win_pcts.append(float(hw_pct))

    return seasons, pace_vals, home_win_pcts


# ── Team home court advantage analysis ───────────────────────────────────────

def compute_team_hca_stats(
    start_year: int, end_year: int, season_type: str,
    skip_years: set[int] = frozenset(), min_games: int = 50,
) -> dict[str, dict]:
    """
    All-time per-franchise home and road win% aggregated across seasons.
    Returns dict: TEAM_NAME -> {home_pct, road_pct, hca, n_home, n_road}.
    Franchises with fewer than min_games home games are excluded.
    """
    home_wins:  dict[str, int] = {}
    home_total: dict[str, int] = {}
    road_wins:  dict[str, int] = {}
    road_total: dict[str, int] = {}

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        df = _load_game_log(year, season_type)
        if df is None:
            continue

        is_home = df["MATCHUP"].str.contains(" vs. ", regex=False, na=False)
        is_road = df["MATCHUP"].str.contains(" @ ", regex=False, na=False)

        for subset, w_dict, t_dict in [
            (df[is_home], home_wins, home_total),
            (df[is_road], road_wins, road_total),
        ]:
            for team, grp in subset.groupby("TEAM_NAME", sort=False):
                t_dict[team] = t_dict.get(team, 0) + len(grp)
                w_dict[team] = w_dict.get(team, 0) + int((grp["WL"] == "W").sum())

    result: dict[str, dict] = {}
    for team in sorted(set(home_total) | set(road_total)):
        n_h = home_total.get(team, 0)
        n_r = road_total.get(team, 0)
        if n_h < min_games or n_r < min_games:
            continue
        h_pct = 100.0 * home_wins.get(team, 0) / n_h
        r_pct = 100.0 * road_wins.get(team, 0) / n_r
        result[team] = {
            "home_pct": round(h_pct, 1),
            "road_pct": round(r_pct, 1),
            "hca":      round(h_pct - r_pct, 1),
            "n_home":   n_h,
            "n_road":   n_r,
        }
    return result


def fetch_margin_data(end_year: int, season_type: str) -> pd.DataFrame | None:
    """
    Per-home-game point margin from the cached game log.
    PLUS_MINUS for a home row equals home_pts − away_pts exactly.
    Returns a DataFrame with columns ['margin', 'WL']; None if no data.
    """
    df = _load_game_log(end_year, season_type)
    if df is None:
        return None
    home = df[df["MATCHUP"].str.contains(" vs. ", regex=False, na=False)].copy()
    if home.empty:
        return None
    return home[["PLUS_MINUS", "WL"]].rename(columns={"PLUS_MINUS": "margin"})


def compute_margin_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], dict]:
    """Per-season home team point-differential statistics."""
    seasons: list[str] = []
    stats: dict[str, list[float]] = {
        "all_games_mean": [], "home_wins_mean": [], "home_losses_mean": [], "std_dev": [],
    }

    for year, g in _iter_season_frames(start_year, end_year, season_type, skip_years, fetch_margin_data):
        seasons.append(short_label(year))
        stats["all_games_mean"].append(g["margin"].mean())
        wins   = g[g["WL"] == "W"]
        losses = g[g["WL"] == "L"]
        stats["home_wins_mean"].append(  wins["margin"].mean()   if len(wins)   else np.nan)
        stats["home_losses_mean"].append(losses["margin"].mean() if len(losses) else np.nan)
        stats["std_dev"].append(g["margin"].std())

    return seasons, stats


def fetch_net_rating_data(end_year: int, season_type: str) -> pd.DataFrame | None:
    """Per-game home-team net rating (points per 100 possessions).

    Requires TOV and OREB columns (available from ~1997 onward). Returns None
    for seasons where pace cannot be computed.
    """
    df = _load_game_log(end_year, season_type)
    if df is None:
        return None
    merged = _merge_home_away_rows(df)
    if merged is None:
        return None
    pace_cols = {"FGA_home", "FGA_away", "OREB_home", "OREB_away",
                 "TOV_home", "TOV_away", "FTA_home", "FTA_away", "PLUS_MINUS_home"}
    if not pace_cols.issubset(merged.columns):
        return None
    home_poss = (merged["FGA_home"] - merged["OREB_home"]
                 + merged["TOV_home"] + 0.44 * merged["FTA_home"])
    away_poss = (merged["FGA_away"] - merged["OREB_away"]
                 + merged["TOV_away"] + 0.44 * merged["FTA_away"])
    pace_avg = (home_poss + away_poss) / 2
    net_rating = merged["PLUS_MINUS_home"] / pace_avg.replace(0, np.nan) * 100
    result = pd.DataFrame({"net_rating": net_rating})
    return result.dropna()


def compute_net_rating_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], dict]:
    """Per-season mean home-team net rating (points per 100 possessions)."""
    seasons: list[str] = []
    stats: dict[str, list[float]] = {"net_rating_mean": []}

    for year, g in _iter_season_frames(start_year, end_year, season_type, skip_years, fetch_net_rating_data):
        seasons.append(short_label(year))
        stats["net_rating_mean"].append(g["net_rating"].mean())

    return seasons, stats


def compute_parity_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], list[float]]:
    """Per-season std dev of team win%, a measure of competitive balance (lower = more parity)."""
    seasons: list[str] = []
    std_devs: list[float] = []

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        df = _load_game_log(year, season_type)
        if df is None or df.empty:
            continue

        team_wins = df.groupby("TEAM_ID")["WL"].apply(lambda x: (x == "W").mean())
        if len(team_wins) < 2:
            continue

        seasons.append(short_label(year))
        std_devs.append(float(team_wins.std()))

    return seasons, std_devs


# ── Playoff series structure analysis ─────────────────────────────────────────

def fetch_series_data(end_year: int) -> pd.DataFrame | None:
    """
    Load cached playoffs game log and derive game-within-series number from
    GAME_ID (last digit), series key (second-to-last two digits), and
    HOME_WIN from WL. Returns home-rows-only with columns
    ['GAME_ID', 'game_in_series', 'series_key', 'HOME_WIN'].
    """
    df = _load_game_log(end_year, "Playoffs")
    if df is None:
        return None

    home = df[df["MATCHUP"].str.contains(" vs. ", regex=False, na=False)].copy()
    if home.empty:
        return None

    # GAME_ID may be int64 in cache; str(int(float(x))) handles int, float, str
    game_id = home["GAME_ID"].apply(lambda x: str(int(float(x))))
    home = home.copy()
    home["game_in_series"] = game_id.str[-1].astype(int)
    home["series_key"]     = game_id.str[-3:-1]
    home["HOME_WIN"]       = (home["WL"] == "W").astype(int)

    return home[["GAME_ID", "game_in_series", "series_key", "HOME_WIN"]]


def compute_series_stats(
    start_year: int, end_year: int, skip_years: set[int] = frozenset(),
) -> tuple[list[int], list[float], list[int]]:
    """
    Home win % and game count per game-within-series number (1–7), pooled
    across all seasons. Returns (game_numbers, home_win_pcts, game_counts).
    """
    wins  = {g: 0 for g in range(1, 8)}
    total = {g: 0 for g in range(1, 8)}

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        g = fetch_series_data(year)
        if g is None or g.empty:
            continue
        for gnum, win in zip(g["game_in_series"], g["HOME_WIN"]):
            if 1 <= gnum <= 7:
                wins[gnum]  += int(win)
                total[gnum] += 1

    game_nums = [g for g in range(1, 8) if total[g] > 0]
    win_pcts  = [100.0 * wins[g] / total[g] for g in game_nums]
    counts    = [total[g] for g in game_nums]
    return game_nums, win_pcts, counts


def compute_series_stats_by_era(
    start_year: int, end_year: int, skip_years: set[int] = frozenset(),
) -> dict[str, dict[int, float]]:
    """
    Home win % per game-within-series number split by era.
    Returns {era_label: {game_num: home_win_pct}}.
    Game numbers with fewer than 5 games in an era are excluded.
    """
    era_wins  = {e[0]: {g: 0 for g in range(1, 8)} for e in ERA_DEFS}
    era_total = {e[0]: {g: 0 for g in range(1, 8)} for e in ERA_DEFS}

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        era_label = next(
            (lbl for lbl, y1, y2, _ in ERA_DEFS if y1 <= year <= y2), None
        )
        if era_label is None:
            continue

        g = fetch_series_data(year)
        if g is None or g.empty:
            continue

        for gnum, win in zip(g["game_in_series"], g["HOME_WIN"]):
            if 1 <= gnum <= 7:
                era_wins[era_label][gnum]  += int(win)
                era_total[era_label][gnum] += 1

    result: dict[str, dict[int, float]] = {}
    for era_label in era_wins:
        pcts = {
            g: 100.0 * era_wins[era_label][g] / era_total[era_label][g]
            for g in range(1, 8)
            if era_total[era_label][g] >= 5
        }
        if pcts:
            result[era_label] = pcts
    return result


# ── Shot-zone analysis ────────────────────────────────────────────────────────
# LeagueDashTeamShotLocations column names for each shot zone's FGA.
# RA = Restricted Area, PITP = Paint In The Paint (non-RA), MR = Mid-Range,
# LC3/RC3 = Left/Right Corner 3, ATB3 = Above the Break 3, BC = Back Court.
SHOT_ZONE_GROUPS: dict[str, list[str]] = {
    "paint":    ["FGA_RA", "FGA_NON_RA"],
    "midrange": ["FGA_MR"],
    "corner3":  ["FGA_LC3", "FGA_RC3"],
    "above3":   ["FGA_ATB3"],
    # FGA_BC excluded — backcourt heaves are noise
}


def fetch_shot_zones(end_year: int, season_type: str, location: str) -> pd.DataFrame | None:
    """Team-level shot-zone FGA totals, split by location. See nbakit.data.fetch_shot_zones."""
    return _nbakit.fetch_shot_zones(end_year, season_type, location,
                                    cache_dir=CACHE_DIR, sleep=SLEEP_SEC)


def _zone_pcts(df: pd.DataFrame) -> dict[str, float]:
    """League-wide shot zone percentages (share of total FGA) from a team-level DataFrame."""
    totals = {
        zone: sum(df[col].sum() for col in cols if col in df.columns)
        for zone, cols in SHOT_ZONE_GROUPS.items()
    }
    total_fga = sum(totals.values())
    if total_fga == 0:
        return {k: np.nan for k in SHOT_ZONE_GROUPS}
    return {k: 100.0 * v / total_fga for k, v in totals.items()}


def compute_shot_zone_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], dict]:
    """
    Per-season home-minus-road shot zone % differentials.
    Each value is the pp difference in that zone's share of total FGA (home − road).
    """
    seasons: list[str] = []
    stats: dict[str, list[float]] = {zone: [] for zone in SHOT_ZONE_GROUPS}

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        home_df = fetch_shot_zones(year, season_type, "Home")
        road_df = fetch_shot_zones(year, season_type, "Road")
        if home_df is None or road_df is None:
            continue

        home_pcts = _zone_pcts(home_df)
        road_pcts = _zone_pcts(road_df)
        if any(np.isnan(v) for v in {**home_pcts, **road_pcts}.values()):
            continue

        seasons.append(short_label(year))
        for zone in SHOT_ZONE_GROUPS:
            stats[zone].append(home_pcts[zone] - road_pcts[zone])

    return seasons, stats


# ── Referee crew analysis ─────────────────────────────────────────────────────

def fetch_referee_data(end_year: int, season_type: str) -> pd.DataFrame | None:
    """Officials for every game in the cached game log. See nbakit.data.fetch_referees."""
    game_log = _load_game_log(end_year, season_type)
    game_ids = sorted(game_log["GAME_ID"].unique()) if game_log is not None else None
    return _nbakit.fetch_referees(
        end_year, season_type, game_ids=game_ids, cache_dir=CACHE_DIR, sleep=SLEEP_SEC,
        officials_start_year=OFFICIALS_DATA_START_YEAR,
        known_empty_years=OFFICIALS_KNOWN_EMPTY_YEARS)


def fetch_all_referee_data(
    start_year: int,
    end_year: int,
    season_type: str,
    skip_years: set[int] = frozenset(),
) -> pd.DataFrame | None:
    """
    Fetch referee data for all seasons and return a concatenated DataFrame with
    columns [GAME_ID, personId, name, year], or None if nothing is cached.
    """
    chunks: list[pd.DataFrame] = []
    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        df = fetch_referee_data(year, season_type)
        if df is None or df.empty:
            continue
        df = df.copy()
        df["year"] = year
        chunks.append(df)
    if not chunks:
        return None
    return pd.concat(chunks, ignore_index=True)


def compute_referee_bias_stats(
    ref_df: pd.DataFrame,
    start_year: int,
    end_year: int,
    season_type: str,
    skip_years: set[int] = frozenset(),
    min_games: int = 50,
) -> list[dict]:
    """
    Per-official home foul bias aggregated across all games they worked.
    Loads game logs internally to compute foul_diff (PF_home − PF_away) so this
    function does not depend on the regression game dataset.

    Returns a list of dicts sorted by mean_foul_diff descending, each with:
      {personId, name, n_games, mean_foul_diff, era_means: {era_label: mean}}
    Officials with fewer than min_games games are excluded.
    """
    def _norm(gid) -> str:
        return f"{int(float(gid)):010d}"

    foul_chunks: list[pd.DataFrame] = []
    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        df = _load_game_log(year, season_type)
        if df is None:
            continue
        merged = _merge_home_away_rows(df)
        if merged is None:
            continue
        era_label = next(
            (lbl for lbl, y1, y2, _ in ERA_DEFS if y1 <= year <= y2), "other"
        )
        diffs = _compute_box_differentials(merged)
        foul_chunks.append(pd.DataFrame({
            "GAME_ID":    merged["GAME_ID"].apply(_norm),
            "foul_diff":  diffs["foul_diff"].values,
            "era":        era_label,
        }))

    if not foul_chunks:
        return []

    foul_data = pd.concat(foul_chunks, ignore_index=True)

    ref = ref_df.copy()
    ref["GAME_ID"] = ref["GAME_ID"].apply(_norm)
    joined = ref.merge(foul_data, on="GAME_ID", how="inner")

    result: list[dict] = []
    for (pid, name), grp in joined.groupby(["personId", "name"]):
        if len(grp) < min_games:
            continue
        era_means = grp.groupby("era")["foul_diff"].mean().to_dict()
        # era_sd / era_n: needed for method-of-moments variance decomposition.
        # std(ddof=1) is NaN when n==1; filter those out so callers get clean dicts.
        era_sd_raw = grp.groupby("era")["foul_diff"].std(ddof=1).to_dict()
        era_n_raw  = grp.groupby("era")["foul_diff"].count().to_dict()
        era_sd = {k: float(v) for k, v in era_sd_raw.items() if not (isinstance(v, float) and np.isnan(v))}
        era_n  = {k: int(v)   for k, v in era_n_raw.items()}
        result.append({
            "personId":       int(pid),
            "name":           str(name),
            "n_games":        len(grp),
            "mean_foul_diff": float(grp["foul_diff"].mean()),
            "sd_foul_diff":   float(grp["foul_diff"].std(ddof=1)) if len(grp) > 1 else 0.0,
            "era_means":      era_means,
            "era_sd":         era_sd,
            "era_n":          era_n,
        })

    result.sort(key=lambda x: x["mean_foul_diff"], reverse=True)
    return result


# ── Attendance (Basketball-Reference) ─────────────────────────────────────────
# NBA.com does not expose attendance, so we scrape Basketball-Reference's monthly
# schedule pages. Per-game attendance is reliable from ~1999-2000 onward. Each
# season is cached as cache/attendance_{season}.csv so the scrape runs only once.

# GET a BBR page (polite pause + 429 backoff) and parse a monthly schedule
# table. The mechanics live in nbakit.bbr; we pass this project's rate-limit
# tuning. fetch progress/errors go to stderr so run()'s stdout->RESULTS.md
# capture stays clean.
def _bbr_get(url: str):
    return _bbr.get_soup(url, headers=BBR_HEADERS, sleep_sec=BBR_SLEEP_SEC,
                         backoff_sec=BBR_BACKOFF_SEC, max_retries=BBR_MAX_RETRIES)


_parse_bbr_schedule = _bbr.parse_schedule


def fetch_attendance(end_year: int) -> pd.DataFrame | None:
    """
    Per-game attendance for one season, scraped from Basketball-Reference.
    Crawls the season index for its month links, parses each monthly schedule
    page, and caches the result as cache/attendance_{season}.csv (an empty file
    is written on a miss so we never re-fetch).
    """
    path = os.path.join(CACHE_DIR, f"attendance_{season_str(end_year)}.csv")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            return None
        return df if not df.empty else None

    os.makedirs(CACHE_DIR, exist_ok=True)

    # A transient failure (rate-limit/network) must NOT be cached as a miss, or
    # the season is permanently skipped. Only a page that loads but genuinely
    # has no data is cached empty so we don't retry it.
    index = _bbr_get(f"{BBR_BASE}/leagues/NBA_{end_year}_games.html")
    if index is None:
        return None  # transient — retry on the next run

    filt = index.find("div", class_="filter")
    month_hrefs = [a.get("href") for a in filt.find_all("a")] if filt else []
    if not month_hrefs:
        pd.DataFrame().to_csv(path, index=False)  # genuine miss
        return None

    print(f"  Fetching attendance: {season_str(end_year)} "
          f"({len(month_hrefs)} month pages)...", file=sys.stderr, flush=True)
    records: list[dict] = []
    for href in month_hrefs:
        soup = _bbr_get(f"{BBR_BASE}{href}")
        if soup is None:
            return None  # transient mid-season — abort without caching a partial season
        records.extend(_parse_bbr_schedule(soup))

    if not records:
        pd.DataFrame().to_csv(path, index=False)  # genuine miss
        return None

    df = pd.DataFrame(records)
    df.to_csv(path, index=False)
    return df


def compute_attendance_season_stats(
    start_year: int = BBR_START_YEAR, end_year: int = END_YEAR,
) -> tuple[list[str], list[float]]:
    """
    League average attendance per game, per season (short labels).
    Averages only games with a reported crowd (>0); a 0 means an empty or
    unreported arena, so it is excluded from the mean but kept in the raw cache
    for the dose-response below.
    """
    seasons: list[str] = []
    avg_attendance: list[float] = []
    for year in range(start_year, end_year + 1):
        df = fetch_attendance(year)
        if df is None or df.empty:
            continue
        played = df.loc[df["attendance"] > 0, "attendance"]
        if played.empty:
            continue
        seasons.append(short_label(year))
        avg_attendance.append(round(float(played.mean()), 0))
    return seasons, avg_attendance


def compute_attendance_covid_doseresponse(end_year: int = 2021) -> pd.DataFrame:
    """
    Per-game attendance vs. home_win for the COVID season (default 2020-21),
    when crowd size varied game-to-game by local restriction — a natural
    dose-response test of what the crowd is worth. Zero-attendance games are
    kept; rows with unreported (NaN) attendance are dropped.
    """
    df = fetch_attendance(end_year)
    if df is None or df.empty:
        return pd.DataFrame(columns=["attendance", "home_win"])
    out = df.loc[df["attendance"].notna(), ["attendance", "home_win"]].copy()
    out["attendance"] = out["attendance"].astype(float)
    out["home_win"] = out["home_win"].astype(int)
    return out.reset_index(drop=True)
