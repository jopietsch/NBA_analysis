"""
nba_home_court_data.py — data pipeline for NBA home court advantage analysis.

Fetches game logs from NBA.com via nba_api, caches them as CSVs, and provides
fetch_* and compute_* functions consumed by nba_home_court_plots and
nba_home_court_regression.

Data source: NBA.com via the nba_api package
  - LeagueGameFinder: pulls every game result for a given season
  - Covers 1983-84 through 2024-25
"""

import os
import time
import pandas as pd
import numpy as np

from nba_api.stats.endpoints import leaguegamefinder
from nba_api.stats.library.parameters import SeasonType


# ── Config ────────────────────────────────────────────────────────────────────
START_YEAR = 1984   # season ending in this year = 1983-84
END_YEAR   = 2025   # season ending in this year = 2024-25
SLEEP_SEC  = 1.0    # polite pause between API calls

# 2020 bubble playoffs: all games at neutral site — exclude from playoff stats
SKIP_PLAYOFF_YEARS = {2020}

# Seasons with limited/no fans (COVID) — highlighted in the chart
COVID_SEASONS = {"19–20", "20–21"}

# Raw game logs are cached here as CSVs to avoid re-fetching from NBA.com
CACHE_DIR = "cache"


def season_str(end_year: int) -> str:
    """2024 -> '2023-24'  (NBA API format)"""
    return f"{end_year - 1}-{str(end_year)[-2:]}"


def short_label(end_year: int) -> str:
    """2024 -> '23–24'  (chart axis label)"""
    return f"{str(end_year - 1)[-2:]}–{str(end_year)[-2:]}"


def cache_path(end_year: int, season_type: str) -> str:
    season = season_str(end_year)
    return os.path.join(CACHE_DIR, f"{season}_{season_type.replace(' ', '_')}.csv")


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
    ("2023–25", 2023, 2025, "Transition take-foul rule added"),
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
    ("2014–25",  2014, 2025, "Best-of-7 R1, 2-2-1-1-1 Finals"),
]


def label_to_year(lbl: str) -> int:
    suffix = int(lbl.split("–")[1])
    return (2000 + suffix) if suffix < 50 else (1900 + suffix)


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
    reg_avg, po_avg = [], []
    for _, y1, y2, _ in period_defs:
        rv = [p for s, p in zip(reg_seasons, reg_pcts) if y1 <= label_to_year(s) <= y2]
        pv = [p for s, p in zip(po_seasons,  po_pcts)  if y1 <= label_to_year(s) <= y2]
        reg_avg.append(round(np.mean(rv), 1) if rv else 0)
        po_avg.append( round(np.mean(pv), 1) if pv else 0)
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


def _merge_home_away_rows(df: pd.DataFrame) -> pd.DataFrame | None:
    """
    Collapse a per-team-per-game log into one row per game by joining each
    game's home and away rows on GAME_ID (columns get '_home'/'_away'
    suffixes). Returns None if either side has no rows.
    """
    home = df[df["MATCHUP"].str.contains(" vs. ", regex=False, na=False)]
    away = df[df["MATCHUP"].str.contains(" @ ", regex=False, na=False)]
    if home.empty or away.empty:
        return None

    merged = home.merge(away, on="GAME_ID", suffixes=("_home", "_away"))
    if merged.empty:
        return None
    return merged


def _add_rest_days(df: pd.DataFrame) -> pd.DataFrame:
    """Add a REST column: days since each team's previous game minus 1 (0 = back-to-back)."""
    df = df.copy()
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"])
    df = df.sort_values(["TEAM_ID", "GAME_DATE"])
    df["PREV_DATE"] = df.groupby("TEAM_ID")["GAME_DATE"].shift(1)
    df["REST"] = (df["GAME_DATE"] - df["PREV_DATE"]).dt.days - 1
    return df


def bucket_stats_by_era(seasons: list[str], stats: dict) -> tuple[dict, list[str]]:
    """
    Average each per-season stat series within each rule-change era
    (ERA_DEFS). Works for any stats dict of the form {category: [per-season
    values]} — used by both the altitude and time-zone analyses.
    """
    era_avgs: dict[str, list[float]] = {key: [] for key in stats}
    for _, y1, y2, _ in ERA_DEFS:
        idx = [i for i, s in enumerate(seasons) if y1 <= label_to_year(s) <= y2]
        for key, values in stats.items():
            vals = [values[i] for i in idx if not np.isnan(values[i])]
            era_avgs[key].append(round(np.mean(vals), 1) if vals else 0)

    era_labels_short = [e[0] for e in ERA_DEFS]
    return era_avgs, era_labels_short


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


# ── Rest-day analysis ─────────────────────────────────────────────────────────
def fetch_rest_data(end_year: int, season_type: str) -> pd.DataFrame | None:
    """
    Compute per-game rest-day info for one season/type from the cached game
    log (one row per team per game). REST = days between a team's
    consecutive games minus 1 (0 = back-to-back). Games where either team's
    rest is unknown (their first game in this cached log) are dropped.

    Note: for playoffs, "first game" means the team's first playoff game of
    that year, since the cache only contains playoff games — so first-round
    games are dropped (no prior playoff game to compute rest from).
    """
    df = _load_game_log(end_year, season_type)
    if df is None:
        return None

    df = _add_rest_days(df)

    merged = _merge_home_away_rows(df)
    if merged is None:
        return None

    merged = merged.dropna(subset=["REST_home", "REST_away"])
    if merged.empty:
        return None

    merged["REST_DIFF"] = merged["REST_home"] - merged["REST_away"]
    merged["HOME_WIN"] = (merged["WL_home"] == "W").astype(int)
    return merged[["REST_home", "REST_away", "REST_DIFF", "HOME_WIN"]]


def compute_rest_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], dict]:
    """Per-season back-to-back rates and home win % by rest differential."""
    seasons: list[str] = []
    stats: dict[str, list[float]] = {
        "b2b_home_pct": [], "b2b_away_pct": [],
        "win_home_more_rest": [], "win_equal_rest": [], "win_away_more_rest": [],
    }

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        g = fetch_rest_data(year, season_type)
        if g is None or g.empty:
            continue

        seasons.append(short_label(year))
        stats["b2b_home_pct"].append(100 * (g["REST_home"] == 0).mean())
        stats["b2b_away_pct"].append(100 * (g["REST_away"] == 0).mean())

        more  = g[g["REST_DIFF"] > 0]
        equal = g[g["REST_DIFF"] == 0]
        less  = g[g["REST_DIFF"] < 0]
        stats["win_home_more_rest"].append(100 * more["HOME_WIN"].mean()  if len(more)  else np.nan)
        stats["win_equal_rest"].append(    100 * equal["HOME_WIN"].mean() if len(equal) else np.nan)
        stats["win_away_more_rest"].append(100 * less["HOME_WIN"].mean()  if len(less)  else np.nan)

    return seasons, stats


# ── Altitude analysis ─────────────────────────────────────────────────────────
# Home arenas at significant elevation, used to test whether visiting teams
# are specifically disadvantaged at altitude (vs. just facing good teams).
# Matched on TEAM_NAME since the Jazz's abbreviation changed (UTH -> UTA)
# partway through the dataset, but TEAM_NAME has stayed constant.
# Source: https://en.wikipedia.org/wiki/List_of_NBA_arenas
ALTITUDE_TEAMS = {
    "Denver Nuggets": 5280,
    "Utah Jazz": 4226,
}


def fetch_altitude_data(end_year: int, season_type: str) -> pd.DataFrame | None:
    """
    Per-home-game result from the cached game log, tagged with whether the
    home team plays at elevation (Denver, Utah). HOME_WIN = 1 if the home
    team won that game.
    """
    df = _load_game_log(end_year, season_type)
    if df is None:
        return None

    home = df[df["MATCHUP"].str.contains(" vs. ", regex=False, na=False)].copy()
    if home.empty:
        return None

    home["HOME_WIN"] = (home["WL"] == "W").astype(int)
    home["ALTITUDE"] = home["TEAM_NAME"].isin(ALTITUDE_TEAMS)
    return home[["TEAM_NAME", "HOME_WIN", "ALTITUDE"]]


def compute_altitude_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], dict]:
    """Per-season home win % at each altitude city vs elsewhere."""
    seasons: list[str] = []
    stats: dict[str, list[float]] = {name: [] for name in ALTITUDE_TEAMS}
    stats["other"] = []

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        g = fetch_altitude_data(year, season_type)
        if g is None or g.empty:
            continue

        seasons.append(short_label(year))
        other = g[~g["ALTITUDE"]]
        stats["other"].append(100 * other["HOME_WIN"].mean() if len(other) else np.nan)
        for name in ALTITUDE_TEAMS:
            team_g = g[g["TEAM_NAME"] == name]
            stats[name].append(100 * team_g["HOME_WIN"].mean() if len(team_g) else np.nan)

    return seasons, stats


# ── Time-zone analysis ────────────────────────────────────────────────────────
# Time zone for each franchise that has appeared in the dataset, numbered
# 0 (Eastern) through 3 (Pacific). Used to measure how many time zones a
# visiting team crossed to play a given game. DST is ignored, and Arizona
# (no DST) is grouped with Mountain — both approximations are fine for a
# zones-crossed count.
# Source: https://en.wikipedia.org/wiki/Time_in_the_United_States
TEAM_TIMEZONES = {
    # Eastern
    "Atlanta Hawks": 0, "Boston Celtics": 0, "Brooklyn Nets": 0,
    "Charlotte Bobcats": 0, "Charlotte Hornets": 0, "Cleveland Cavaliers": 0,
    "Detroit Pistons": 0, "Indiana Pacers": 0, "Miami Heat": 0,
    "New Jersey Nets": 0, "New York Knicks": 0, "Orlando Magic": 0,
    "Philadelphia 76ers": 0, "Toronto Raptors": 0, "Washington Bullets": 0,
    "Washington Wizards": 0,
    # Central
    "Chicago Bulls": 1, "Dallas Mavericks": 1, "Houston Rockets": 1,
    "Kansas City Kings": 1, "Memphis Grizzlies": 1, "Milwaukee Bucks": 1,
    "Minnesota Timberwolves": 1, "New Orleans Hornets": 1,
    "New Orleans Pelicans": 1, "New Orleans/Oklahoma City Hornets": 1,
    "Oklahoma City Thunder": 1, "San Antonio Spurs": 1,
    # Mountain (incl. Arizona, which doesn't observe DST)
    "Denver Nuggets": 2, "Phoenix Suns": 2, "Utah Jazz": 2,
    # Pacific
    "Golden State Warriors": 3, "LA Clippers": 3, "Los Angeles Clippers": 3,
    "Los Angeles Lakers": 3, "Portland Trail Blazers": 3,
    "Sacramento Kings": 3, "San Diego Clippers": 3, "Seattle SuperSonics": 3,
    "Vancouver Grizzlies": 3,
}

TZ_CATEGORIES = ["0", "1", "2", "3"]


def fetch_timezone_data(end_year: int, season_type: str) -> pd.DataFrame | None:
    """
    Per-game result from the cached game log, tagged with how many time
    zones the visiting team crossed. AWAY_WIN = 1 if the visiting team won.
    Games involving a team not in TEAM_TIMEZONES are dropped.
    """
    df = _load_game_log(end_year, season_type)
    if df is None:
        return None

    merged = _merge_home_away_rows(df)
    if merged is None:
        return None

    home_tz = merged["TEAM_NAME_home"].map(TEAM_TIMEZONES)
    away_tz = merged["TEAM_NAME_away"].map(TEAM_TIMEZONES)
    merged = merged[home_tz.notna() & away_tz.notna()].copy()
    if merged.empty:
        return None

    home_tz = merged["TEAM_NAME_home"].map(TEAM_TIMEZONES)
    away_tz = merged["TEAM_NAME_away"].map(TEAM_TIMEZONES)
    merged["TZ_DIFF"] = (home_tz - away_tz).abs().astype(int)
    merged["HOME_WIN"] = (merged["WL_home"] == "W").astype(int)
    return merged[["TZ_DIFF", "HOME_WIN"]]


def compute_timezone_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], dict]:
    """Per-season home win % grouped by time zones the visiting team crossed."""
    seasons: list[str] = []
    stats: dict[str, list[float]] = {cat: [] for cat in TZ_CATEGORIES}

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        g = fetch_timezone_data(year, season_type)
        if g is None or g.empty:
            continue

        seasons.append(short_label(year))
        for cat in TZ_CATEGORIES:
            sub = g[g["TZ_DIFF"] == int(cat)]
            stats[cat].append(100 * sub["HOME_WIN"].mean() if len(sub) else np.nan)

    return seasons, stats


# ── Travel distance analysis ──────────────────────────────────────────────────
# Haversine distance from the away team's home arena to the game arena,
# used to test whether longer road trips reduce the visiting team's odds.
# Coordinates are approximate arena lat/lon; small errors (< 20 mi) don't
# affect the broad distance-bucket analysis. Franchise names must match
# TEAM_NAME strings in the cached CSVs.
ARENA_COORDS: dict[str, tuple[float, float]] = {
    # Eastern
    "Atlanta Hawks":           (33.757,  -84.396),
    "Boston Celtics":          (42.366,  -71.062),
    "Brooklyn Nets":           (40.683,  -73.975),
    "Charlotte Bobcats":       (35.225,  -80.839),
    "Charlotte Hornets":       (35.225,  -80.839),
    "Cleveland Cavaliers":     (41.497,  -81.688),
    "Detroit Pistons":         (42.697,  -83.245),   # Palace of Auburn Hills (most of dataset)
    "Indiana Pacers":          (39.764,  -86.156),
    "Miami Heat":              (25.781,  -80.188),
    "New Jersey Nets":         (40.814,  -74.067),   # Meadowlands (East Rutherford, NJ)
    "New York Knicks":         (40.750,  -73.994),
    "Orlando Magic":           (28.539,  -81.384),
    "Philadelphia 76ers":      (39.901,  -75.172),
    "Toronto Raptors":         (43.643,  -79.379),
    "Washington Bullets":      (38.898,  -77.021),
    "Washington Wizards":      (38.898,  -77.021),
    # Central
    "Chicago Bulls":           (41.881,  -87.674),
    "Dallas Mavericks":        (32.791,  -96.810),
    "Houston Rockets":         (29.751,  -95.362),
    "Kansas City Kings":       (39.076,  -94.578),
    "Memphis Grizzlies":       (35.138,  -90.051),
    "Milwaukee Bucks":         (43.044,  -87.917),
    "Minnesota Timberwolves":  (44.979,  -93.276),
    "New Orleans Hornets":     (29.949,  -90.082),
    "New Orleans Pelicans":    (29.949,  -90.082),
    "New Orleans/Oklahoma City Hornets": (29.949,  -90.082),  # NOLA home base
    "Oklahoma City Thunder":   (35.463,  -97.515),
    "San Antonio Spurs":       (29.427,  -98.438),
    # Mountain
    "Denver Nuggets":          (39.749, -104.983),
    "Phoenix Suns":            (33.446, -112.071),
    "Utah Jazz":               (40.768, -111.901),
    # Pacific
    "Golden State Warriors":   (37.750, -122.201),   # Oakland (majority of dataset)
    "LA Clippers":             (34.043, -118.267),
    "Los Angeles Clippers":    (34.043, -118.267),
    "Los Angeles Lakers":      (34.043, -118.267),
    "Portland Trail Blazers":  (45.532, -122.667),
    "Sacramento Kings":        (38.580, -121.500),
    "San Diego Clippers":      (32.710, -117.157),
    "Seattle SuperSonics":     (47.622, -122.354),
    "Vancouver Grizzlies":     (49.278, -123.109),
}

TRAVEL_BUCKETS = ["0–500", "500–1000", "1000–1500", "1500+"]


def _haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance in miles between two lat/lon points."""
    R = 3958.8  # Earth radius in miles
    phi1, phi2 = np.radians(lat1), np.radians(lat2)
    dphi    = np.radians(lat2 - lat1)
    dlambda = np.radians(lon2 - lon1)
    a = np.sin(dphi / 2) ** 2 + np.cos(phi1) * np.cos(phi2) * np.sin(dlambda / 2) ** 2
    return float(2 * R * np.arcsin(np.sqrt(a)))


def _bucket_distance(miles: float) -> str:
    """Return the TRAVEL_BUCKETS key for a given distance in miles."""
    if miles < 500:
        return "0–500"
    if miles < 1000:
        return "500–1000"
    if miles < 1500:
        return "1000–1500"
    return "1500+"


def fetch_travel_data(end_year: int, season_type: str) -> pd.DataFrame | None:
    """
    Per-game home win result tagged with haversine distance (miles) from the
    away team's home arena to the home arena. Rows with unknown franchise
    names are dropped. Returns columns ['distance_miles', 'HOME_WIN'].
    """
    df = _load_game_log(end_year, season_type)
    if df is None:
        return None
    merged = _merge_home_away_rows(df)
    if merged is None:
        return None

    home_coords = merged["TEAM_NAME_home"].map(ARENA_COORDS)
    away_coords = merged["TEAM_NAME_away"].map(ARENA_COORDS)
    mask = home_coords.notna() & away_coords.notna()
    merged = merged[mask].copy()
    if merged.empty:
        return None

    home_c = merged["TEAM_NAME_home"].map(ARENA_COORDS)
    away_c = merged["TEAM_NAME_away"].map(ARENA_COORDS)
    merged["distance_miles"] = [
        _haversine(a[0], a[1], h[0], h[1])
        for a, h in zip(away_c, home_c)
    ]
    merged["HOME_WIN"] = (merged["WL_home"] == "W").astype(int)
    return merged[["distance_miles", "HOME_WIN"]]


def compute_travel_stats(
    start_year: int, end_year: int, season_type: str, skip_years: set[int] = frozenset(),
) -> tuple[list[str], dict]:
    """Per-season home win % grouped by away team travel distance (bucketed)."""
    seasons: list[str] = []
    stats: dict[str, list[float]] = {b: [] for b in TRAVEL_BUCKETS}

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        g = fetch_travel_data(year, season_type)
        if g is None or g.empty:
            continue

        seasons.append(short_label(year))
        g = g.copy()
        g["bucket"] = g["distance_miles"].apply(_bucket_distance)
        for bucket in TRAVEL_BUCKETS:
            sub = g[g["bucket"] == bucket]
            stats[bucket].append(100 * sub["HOME_WIN"].mean() if len(sub) else np.nan)

    return seasons, stats


# ── Box-score differential analysis ──────────────────────────────────────────

def _compute_box_differentials(merged: pd.DataFrame) -> pd.DataFrame:
    """Home-minus-away box-score differentials for fouls and shooting."""
    fg3a_home = merged["FG3A_home"].replace(0, np.nan)
    fg3a_away = merged["FG3A_away"].replace(0, np.nan)
    fta_home  = merged["FTA_home"].replace(0, np.nan)
    fta_away  = merged["FTA_away"].replace(0, np.nan)
    return pd.DataFrame({
        "foul_diff":     merged["PF_home"] - merged["PF_away"],
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
    """Per-season mean home-minus-away differentials for fouls and shooting %."""
    seasons: list[str] = []
    stats: dict[str, list[float]] = {
        "foul_diff": [], "fg_pct_diff": [], "efg_pct_diff": [], "tpa_rate_diff": [],
        "fg3_pct_diff": [], "ft_pct_diff": [],
    }

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        g = fetch_differential_data(year, season_type)
        if g is None or g.empty:
            continue

        seasons.append(short_label(year))
        for key in stats:
            stats[key].append(g[key].mean(skipna=True))

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

    for year in range(start_year, end_year + 1):
        if year in skip_years:
            continue
        g = fetch_margin_data(year, season_type)
        if g is None or g.empty:
            continue

        seasons.append(short_label(year))
        stats["all_games_mean"].append(g["margin"].mean())
        wins   = g[g["WL"] == "W"]
        losses = g[g["WL"] == "L"]
        stats["home_wins_mean"].append(  wins["margin"].mean()   if len(wins)   else np.nan)
        stats["home_losses_mean"].append(losses["margin"].mean() if len(losses) else np.nan)
        stats["std_dev"].append(g["margin"].std())

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
# Mapping from the API's MultiIndex (zone, stat) column tuples to flat CSV names.
_ZONE_COL_MAP: dict[tuple[str, str], str] = {
    ("Restricted Area",       "FGA"): "FGA_RA",
    ("In The Paint (Non-RA)", "FGA"): "FGA_NON_RA",
    ("Mid-Range",             "FGA"): "FGA_MR",
    ("Left Corner 3",         "FGA"): "FGA_LC3",
    ("Right Corner 3",        "FGA"): "FGA_RC3",
    ("Above the Break 3",     "FGA"): "FGA_ATB3",
    ("Backcourt",             "FGA"): "FGA_BC",
}

SHOT_ZONE_GROUPS: dict[str, list[str]] = {
    "paint":    ["FGA_RA", "FGA_NON_RA"],
    "midrange": ["FGA_MR"],
    "corner3":  ["FGA_LC3", "FGA_RC3"],
    "above3":   ["FGA_ATB3"],
    # FGA_BC excluded — backcourt heaves are noise
}


def fetch_shot_zones(end_year: int, season_type: str, location: str) -> pd.DataFrame | None:
    """
    Fetch team-level shot zone FGA totals from LeagueDashTeamShotLocations,
    split by location ('Home' or 'Road'). Cached as shot_zones_*.csv.
    """
    path = os.path.join(
        CACHE_DIR,
        f"shot_zones_{season_str(end_year)}_{season_type.replace(' ', '_')}_{location}.csv",
    )
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            return None
        return df if not df.empty else None

    os.makedirs(CACHE_DIR, exist_ok=True)

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
        pd.DataFrame().to_csv(path, index=False)  # cache the miss so we don't retry
        return None

    # The API returns a MultiIndex DataFrame: columns are (zone_name, stat) tuples.
    # Flatten to simple names before caching so the CSV round-trips cleanly.
    id_map = {("", "TEAM_ID"): "TEAM_ID", ("", "TEAM_NAME"): "TEAM_NAME"}
    col_map = {**id_map, **_ZONE_COL_MAP}
    present = [c for c in col_map if c in df.columns]
    df = df[present].copy()
    df.columns = [col_map[c] for c in present]

    os.makedirs(CACHE_DIR, exist_ok=True)
    df.to_csv(path, index=False)
    time.sleep(SLEEP_SEC)
    return df


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
