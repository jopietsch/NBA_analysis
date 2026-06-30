"""
player_rating_overview_data.py — assemble the unified per-season ratings table.

Calls nbakit engines (recompute) + third-party loaders + crosswalk to produce
one merged DataFrame with one row per (player_id, season_end_year) and one
column per rating system. Caches the merged table to cache/unified_ratings_{year}.csv.

Usage:
    from player_rating_overview_data import load_unified_ratings
    df = load_unified_ratings(2025)   # 2024-25 season
"""

import os
import time

import numpy as np
import pandas as pd
import requests

from nbakit.data import (
    default_cache_dir,
    fetch_player_season_totals,
    fetch_player_season_per100,
    fetch_team_season_totals,
    fetch_league_averages,
    fetch_game_logs,
    reconstruct_possessions,
    REGULAR_SEASON,
    PLAYOFFS,
    season_str,
)
from nbakit.ratings import (
    game_score,
    per as compute_per,
    shooting_rates,
    win_shares as compute_win_shares,
    bpm as compute_bpm,
    vorp as compute_vorp,
    rapm as compute_rapm_fit,
)
from nbakit.player_crosswalk import (
    build_crosswalk,
    apply_crosswalk,
    crosswalk_coverage_report,
)

CACHE_DIR = default_cache_dir()

# Minimum minutes to be included in the qualified-player pool for distribution
# and z-scoring. Players with fewer minutes are kept in the unified table but
# flagged as below threshold.
MIN_MINUTES_QUALIFIER = 500

# Rate metrics meaningful for a regular-season vs playoff comparison: each is
# per-minute or per-possession by construction, so it measures level of play
# rather than how many games a player accumulated. Cumulative Win Shares and
# VORP are excluded because their playoff totals mostly track how far a team
# advanced. Game Score is per-game (minutes-sensitive) and is excluded too.
PLAYOFF_DELTA_METRICS = ["PER", "WS48", "BPM", "OBPM", "DBPM"]

# Minimum playoff minutes to appear in the riser/faller table. Below this the
# postseason sample is too small to separate a real shift from noise; it also
# drops players who barely left the bench in a first-round sweep.
MIN_PLAYOFF_MINUTES = 150

# Three independent box-score formulations averaged into the composite playoff
# shift score. OBPM/DBPM are left out (they are the BPM split, so including all
# three would triple-count the BPM family); they are still reported as the
# offense/defense breakdown.
PLAYOFF_SHIFT_FORMULATIONS = ["PER", "WS48", "BPM"]


# ── Power-law fit ─────────────────────────────────────────────────────────────

# A system's value-vs-rank curve is called a power law here when the log-log fit
# explains at least this much of the variance. Below it, the drop-off is steeper
# or flatter than a straight power law (it bends on log-log axes).
POWERLAW_R2_THRESHOLD = 0.95


def powerlaw_fit(values, top_n: int = 50) -> dict | None:
    """Fit value(rank) = C * rank^(-alpha) to a system's top-N values.

    Sorts `values` descending, keeps the leading positive run within the top N
    (a power law is only defined on positive values), and runs an ordinary
    least-squares line on log(value) vs log(rank). Returns the exponent
    (`alpha`), the fit's R-squared, the number of ranks used, and the fitted
    log-intercept (`log_c`) so a plotter can draw the line. Returns None when
    there are too few positive points to fit.
    """
    v = np.sort(np.asarray(values, dtype=float))[::-1]
    v = v[:top_n]
    # Keep the leading run of strictly positive values (log is undefined at <=0).
    positive = np.where(v <= 0)[0]
    cutoff = positive[0] if len(positive) else len(v)
    v = v[:cutoff]
    if len(v) < 5:
        return None
    rank = np.arange(1, len(v) + 1)
    log_r = np.log(rank)
    log_v = np.log(v)
    slope, intercept = np.polyfit(log_r, log_v, 1)
    pred = slope * log_r + intercept
    ss_res = float(np.sum((log_v - pred) ** 2))
    ss_tot = float(np.sum((log_v - log_v.mean()) ** 2))
    r2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 0.0
    return {
        "alpha": float(-slope),
        "log_c": float(intercept),
        "r2": float(r2),
        "n_points": int(len(v)),
    }


# ── Cache path helpers ────────────────────────────────────────────────────────

def _cache(filename: str) -> str:
    os.makedirs(CACHE_DIR, exist_ok=True)
    return os.path.join(CACHE_DIR, filename)


# ── Recomputed ratings ────────────────────────────────────────────────────────

def _build_recomputed(end_year: int,
                      season_type: str = REGULAR_SEASON) -> pd.DataFrame:
    """Compute all box-score recompute ratings for one season.

    season_type is REGULAR_SEASON or PLAYOFFS. Each rating is normalized within
    its own season type (PER to a league average of 15, BPM to 0, WS/48 to
    ~0.100), using that season type's player totals, team totals, and league
    averages, so a playoff value is comparable to its regular-season twin.
    """
    print(f"  Fetching player totals {season_str(end_year)} ({season_type})...")
    player_df = fetch_player_season_totals(end_year, season_type)
    team_df = fetch_team_season_totals(end_year, season_type)
    league = fetch_league_averages(end_year, season_type)

    # Merge team totals onto player rows (for USG%, BPM team adjustments)
    team_cols = ["TEAM_ID", "FGA", "FTA", "TOV", "MIN", "GP", "PTS",
                 "OREB", "DREB", "AST", "STL", "BLK", "PF", "FGM"]
    win_cols = ["TEAM_ID", "W"]
    t_wins = team_df[[c for c in win_cols if c in team_df.columns]].rename(columns={"W": "TEAM_W"})
    t_small = team_df[[c for c in team_cols if c in team_df.columns]].rename(
        columns={c: f"TEAM_{c}" for c in team_cols if c != "TEAM_ID"}
    )
    p = player_df.merge(t_small, on="TEAM_ID", how="left").merge(t_wins, on="TEAM_ID", how="left")

    # Shooting rates
    p = shooting_rates(p)

    # Game Score
    p["GAME_SCORE"] = game_score(p)

    # PER
    p["PER"] = compute_per(p, team_df, league)

    # Win Shares
    ws = compute_win_shares(p, team_df, league)
    for col in ["OWS", "DWS", "WS", "WS48"]:
        p[col] = ws[col]

    # BPM / OBPM / DBPM
    bpm_df = compute_bpm(p, team_df, league)
    p["OBPM"] = bpm_df["OBPM"]
    p["DBPM"] = bpm_df["DBPM"]
    p["BPM"] = bpm_df["BPM"]

    # VORP
    team_games_map = team_df.set_index("TEAM_ID")["GP"].to_dict()
    p["TEAM_GP"] = p["TEAM_ID"].map(team_games_map).fillna(82)
    p["VORP"] = compute_vorp(p.assign(BPM=p["BPM"]),
                              games_in_season=int(p["TEAM_GP"].median()))

    # Qualified flag
    p["QUALIFIED"] = p["MIN"] >= MIN_MINUTES_QUALIFIER

    keep_cols = [
        "PLAYER_ID", "PLAYER_NAME", "TEAM_ID", "TEAM_ABBREVIATION",
        "GP", "MIN", "TEAM_W",
        "TS_PCT", "EFG_PCT", "USG_PCT",
        "GAME_SCORE", "PER",
        "OWS", "DWS", "WS", "WS48",
        "OBPM", "DBPM", "BPM", "VORP",
        "QUALIFIED",
    ]
    return p[[c for c in keep_cols if c in p.columns]].copy()


# ── Regular-season vs playoff deltas ──────────────────────────────────────────

def _playoff_delta_table(reg: pd.DataFrame, po: pd.DataFrame) -> pd.DataFrame:
    """Build the regular-vs-playoff delta table from two recomputed frames.

    Pure transform (no I/O): merges the regular-season and playoff recomputes on
    PLAYER_ID, keeps players with >= MIN_PLAYOFF_MINUTES playoff minutes, and
    adds <m>_reg, <m>_po, <m>_delta, <m>_delta_adj for each PLAYOFF_DELTA_METRICS
    metric plus the composite SHIFT_Z. Rows are sorted by SHIFT_Z (risers first).
    See load_playoff_deltas for the column meanings.
    """
    id_cols = ["PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION"]
    reg_small = reg[[c for c in id_cols if c in reg.columns]
                    + ["MIN"] + PLAYOFF_DELTA_METRICS].rename(
        columns={"MIN": "MIN_reg",
                 **{m: f"{m}_reg" for m in PLAYOFF_DELTA_METRICS}})
    po_small = po[["PLAYER_ID", "MIN"] + PLAYOFF_DELTA_METRICS].rename(
        columns={"MIN": "MIN_po",
                 **{m: f"{m}_po" for m in PLAYOFF_DELTA_METRICS}})

    df = reg_small.merge(po_small, on="PLAYER_ID", how="inner")
    df = df[df["MIN_po"] >= MIN_PLAYOFF_MINUTES].copy()

    for m in PLAYOFF_DELTA_METRICS:
        df[f"{m}_delta"] = df[f"{m}_po"] - df[f"{m}_reg"]
        pool_shift = df[f"{m}_delta"].mean()
        df[f"{m}_delta_adj"] = df[f"{m}_delta"] - pool_shift

    # Composite shift score: average the standardized adjusted deltas of three
    # different box formulations, so a player ranks as a riser only when the
    # formulations agree (robust to any single metric's scale).
    z_cols = []
    for m in PLAYOFF_SHIFT_FORMULATIONS:
        col = df[f"{m}_delta_adj"]
        std = col.std()
        df[f"_z_{m}"] = (col - col.mean()) / std if std > 0 else 0.0
        z_cols.append(f"_z_{m}")
    df["SHIFT_Z"] = df[z_cols].mean(axis=1)
    df = df.drop(columns=z_cols)

    return df.sort_values("SHIFT_Z", ascending=False).reset_index(drop=True)


def load_playoff_deltas(end_year: int, *,
                        force_rebuild: bool = False) -> pd.DataFrame:
    """Regular-season vs playoff rating deltas for one season.

    Recomputes the box-score rate metrics (PLAYOFF_DELTA_METRICS) for both
    season types, keeps players with at least MIN_PLAYOFF_MINUTES playoff
    minutes, and for each metric reports:
      <m>_reg, <m>_po    the regular-season and playoff value
      <m>_delta          playoff minus regular (positive = rose in the playoffs)
      <m>_delta_adj      that delta minus the average delta among the qualified
                         playoff pool, so a riser is measured against the other
                         rotation players who also advanced, not against the
                         whole league. (Each metric is already normalized within
                         its season type, so this only corrects for the qualified
                         pool being stronger than league average.)
      SHIFT_Z            composite riser/faller score: the average of the
                         standardized adjusted deltas of PER, WS/48, and BPM.

    Rows are sorted by SHIFT_Z (risers first).
    Cached at cache/playoff_deltas_{season}.csv. Returns an empty DataFrame when
    the season has no playoff data (e.g. a season still in progress).
    """
    path = _cache(f"playoff_deltas_{season_str(end_year)}.csv")
    if os.path.exists(path) and not force_rebuild:
        try:
            return pd.read_csv(path)
        except pd.errors.EmptyDataError:
            return pd.DataFrame()

    reg = _build_recomputed(end_year, REGULAR_SEASON)
    po = _build_recomputed(end_year, PLAYOFFS)

    if po.empty:
        pd.DataFrame().to_csv(path, index=False)
        return pd.DataFrame()

    df = _playoff_delta_table(reg, po)
    df.to_csv(path, index=False)
    print(f"Playoff deltas: {len(df)} players with >= {MIN_PLAYOFF_MINUTES} "
          f"playoff minutes → {path}")
    return df


# ── Team outcomes (for retrodiction) ──────────────────────────────────────────

def load_team_outcomes(end_year: int) -> pd.DataFrame:
    """Per-team regular-season outcomes used to grade the rating systems.

    Returns one row per team with:
      TEAM_ID
      point_diff   season point differential per game (PLUS_MINUS / games)
      win_pct      regular-season win percentage
    Point differential is the retrodiction target: a better rating, aggregated
    to the team, should better reconstruct who outscored their opponents.
    """
    team_df = fetch_team_season_totals(end_year, REGULAR_SEASON)
    gp = team_df["GP"].replace(0, np.nan)
    win_pct = (team_df["W_PCT"] if "W_PCT" in team_df.columns
               else team_df["W"] / gp)
    return pd.DataFrame({
        "TEAM_ID": team_df["TEAM_ID"],
        "point_diff": team_df["PLUS_MINUS"] / gp,
        "win_pct": win_pct,
    })


# ── Third-party loaders ───────────────────────────────────────────────────────

def _load_raptor(end_year: int) -> pd.DataFrame | None:
    """Load FiveThirtyEight RAPTOR from cached CSV or GitHub download.

    RAPTOR covers 2013-14 to 2022-23. Returns None for out-of-range years.
    Columns used: player_name, season, raptor_total, raptor_offense,
    raptor_defense, war_total (RAPTOR WAR).
    """
    if end_year < 2014 or end_year > 2023:
        return None
    path = _cache(f"raptor_{season_str(end_year)}.csv")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            return df if not df.empty else None
        except pd.errors.EmptyDataError:
            return None

    # Try to download from FiveThirtyEight GitHub
    # Modern RAPTOR (2014+): historical_RAPTOR_by_player.csv
    modern_url = (
        "https://raw.githubusercontent.com/fivethirtyeight/data/master/"
        "nba-raptor/modern_RAPTOR_by_player.csv"
    )
    try:
        print(f"  Downloading RAPTOR data from FiveThirtyEight GitHub...")
        r = requests.get(modern_url, timeout=30)
        if r.status_code == 200:
            all_raptor = pd.read_csv(pd.io.common.StringIO(r.text))
            # Save full file to cache, then filter
            all_path = _cache("raptor_modern_all.csv")
            all_raptor.to_csv(all_path, index=False)
            time.sleep(1)
            # Filter to requested season
            season_label = season_str(end_year)  # e.g., "2024-25"
            season_col = "season" if "season" in all_raptor.columns else None
            if season_col:
                # FTE uses e.g. "2022-23" format
                df = all_raptor[all_raptor[season_col] == season_label].copy()
                df.to_csv(path, index=False)
                return df if not df.empty else None
    except Exception as e:
        print(f"  WARN: Could not download RAPTOR: {e}")
    pd.DataFrame().to_csv(path, index=False)
    return None


def _load_raptor_from_cache_all(end_year: int) -> pd.DataFrame | None:
    """Load RAPTOR from the full cached download if available."""
    all_path = _cache("raptor_modern_all.csv")
    if not os.path.exists(all_path):
        return _load_raptor(end_year)
    try:
        all_raptor = pd.read_csv(all_path)
    except pd.errors.EmptyDataError:
        return None
    season_label = season_str(end_year)
    if "season" in all_raptor.columns:
        df = all_raptor[all_raptor["season"] == season_label].copy()
        return df if not df.empty else None
    return None


def _load_darko(end_year: int) -> pd.DataFrame | None:
    """Load DARKO DPM from a cached manual snapshot CSV.

    Place the downloaded CSV at cache/darko_{season}.csv with at minimum:
    player_name, season (or season_end_year), dpm (or DARKO_DPM).
    """
    path = _cache(f"darko_{season_str(end_year)}.csv")
    if not os.path.exists(path):
        print(f"  DARKO snapshot not found at {path} — skipping")
        return None
    try:
        df = pd.read_csv(path)
        return df if not df.empty else None
    except pd.errors.EmptyDataError:
        return None


def _load_epm(end_year: int) -> pd.DataFrame | None:
    """Load EPM from dunksandthrees.com API, caching result.

    Requires DUNKS_API_KEY env var. On cache hit, skips the network call.
    Season parameter: end_year (e.g. 2025 for 2024-25).
    """
    path = _cache(f"epm_{season_str(end_year)}.csv")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            return df if not df.empty else None
        except pd.errors.EmptyDataError:
            return None

    api_key = os.environ.get("DUNKS_API_KEY")
    if not api_key:
        print("  EPM: DUNKS_API_KEY not set — skipping (register at dunksandthrees.com)")
        return None

    url = "https://www.dunksandthrees.com/api/v1/season-epm"
    try:
        print(f"  Downloading EPM from dunksandthrees.com for {season_str(end_year)}...")
        r = requests.get(
            url,
            params={"season": end_year, "seasontype": 2},
            headers={"Authorization": api_key},
            timeout=30,
        )
        if r.status_code == 401:
            print("  EPM: DUNKS_API_KEY invalid or expired — skipping")
            return None
        r.raise_for_status()
        data = r.json()
    except Exception as e:
        print(f"  WARN: Could not download EPM: {e}")
        return None

    if not data:
        pd.DataFrame().to_csv(path, index=False)
        return None

    df = pd.DataFrame(data)
    rename = {"tot": "epm", "off": "epm_off", "def": "epm_def"}
    df = df.rename(columns={k: v for k, v in rename.items() if k in df.columns})
    keep = [c for c in ["player_name", "epm", "epm_off", "epm_def"] if c in df.columns]
    df = df[keep]
    df.to_csv(path, index=False)
    return df if not df.empty else None


def _load_lebron(end_year: int) -> pd.DataFrame | None:
    """Load LEBRON snapshot from cache/lebron_{season}.csv (manual snapshot)."""
    path = _cache(f"lebron_{season_str(end_year)}.csv")
    if not os.path.exists(path):
        print(f"  LEBRON snapshot not found at {path} — skipping")
        return None
    try:
        df = pd.read_csv(path)
        return df if not df.empty else None
    except pd.errors.EmptyDataError:
        return None


def _load_espn_rpm(end_year: int) -> pd.DataFrame | None:
    """Load ESPN RPM snapshot from cache/espn_rpm_{season}.csv (manual snapshot)."""
    path = _cache(f"espn_rpm_{season_str(end_year)}.csv")
    if not os.path.exists(path):
        print(f"  ESPN RPM snapshot not found at {path} — skipping")
        return None
    try:
        df = pd.read_csv(path)
        return df if not df.empty else None
    except pd.errors.EmptyDataError:
        return None


def _load_human_rankings(end_year: int) -> pd.DataFrame | None:
    """Load pre-assembled human-rankings table from cache/human_{season}.csv.

    This table is built separately (see fetch_human_rankings) and contains:
    player_name, season_end_year, mvp_share, all_nba_pts, all_star,
    nbarank (ESPN), ringer_rank.
    """
    path = _cache(f"human_{season_str(end_year)}.csv")
    if not os.path.exists(path):
        return None
    try:
        df = pd.read_csv(path)
        return df if not df.empty else None
    except pd.errors.EmptyDataError:
        return None


# ── BBR human-ranking fetchers ────────────────────────────────────────────────

def fetch_mvp_votes(end_year: int) -> pd.DataFrame | None:
    """Scrape MVP vote share from Basketball-Reference for one season.

    Returns DataFrame with: player_name, mvp_share (0–1 scale).
    """
    path = _cache(f"mvp_votes_{season_str(end_year)}.csv")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            return df if not df.empty else None
        except pd.errors.EmptyDataError:
            return None

    from nbakit.bbr import get_soup
    url = f"https://www.basketball-reference.com/awards/awards_{end_year}.html"
    soup = get_soup(url)
    if soup is None:
        pd.DataFrame().to_csv(path, index=False)
        return None

    table = soup.find("table", {"id": "mvp"})
    if table is None:
        pd.DataFrame().to_csv(path, index=False)
        return None

    rows = []
    for tr in table.find("tbody").find_all("tr"):
        classes = tr.get("class") or []
        if "thead" in classes:
            continue
        cells = {td.get("data-stat"): td.get_text(strip=True) for td in tr.find_all(["td", "th"])}
        name = cells.get("player", "")
        share_raw = cells.get("award_share", "") or "0"
        if name:
            try:
                share = float(share_raw)
            except ValueError:
                share = 0.0
            rows.append({"player_name": name, "mvp_share": share,
                         "season_end_year": end_year})

    df = pd.DataFrame(rows)
    df.to_csv(path, index=False)
    return df if not df.empty else None


def fetch_all_nba(end_year: int) -> pd.DataFrame | None:
    """Scrape All-NBA selections from BBR for one season.

    Returns DataFrame with: player_name, all_nba_pts (1st=5, 2nd=3, 3rd=1).
    """
    path = _cache(f"all_nba_{season_str(end_year)}.csv")
    if os.path.exists(path):
        try:
            df = pd.read_csv(path)
            return df if not df.empty else None
        except pd.errors.EmptyDataError:
            return None

    from nbakit.bbr import get_soup
    url = f"https://www.basketball-reference.com/awards/awards_{end_year}.html"
    soup = get_soup(url)
    if soup is None:
        pd.DataFrame().to_csv(path, index=False)
        return None

    # BBR uses a single 'leading_all_nba' table with an 'all_nba_team' column
    team_pts = {"1T": 5, "1": 5, "2T": 3, "2": 3, "3T": 1, "3": 1}
    rows: dict[str, int] = {}

    table = soup.find("table", {"id": "leading_all_nba"})
    if table is not None:
        for tr in table.find("tbody").find_all("tr"):
            cells = {td.get("data-stat"): td.get_text(strip=True)
                     for td in tr.find_all(["td", "th"])}
            name = cells.get("player", "")
            team_raw = cells.get("all_nba_team", "").strip()
            if name and team_raw:
                pts = team_pts.get(team_raw, 0)
                if pts > 0:
                    rows[name] = rows.get(name, 0) + pts

    df = pd.DataFrame([{"player_name": n, "all_nba_pts": p,
                         "season_end_year": end_year} for n, p in rows.items()])
    df.to_csv(path, index=False)
    return df if not df.empty else None


# ── Computed RAPM ─────────────────────────────────────────────────────────────

# Columns emitted by _season_possessions (renamed from off_player_i / def_player_i).
_POSS_COLS = (
    [f"off{i}" for i in range(1, 6)] +
    [f"def{i}" for i in range(1, 6)] +
    ["points"]
)


def _season_possessions(end_year: int,
                         season_type: str = REGULAR_SEASON) -> pd.DataFrame:
    """Build a possession table for one season from cached PBP files.

    Reads cached pbp_v3_{gid}.csv and boxscore_trad_{gid}.csv files, normalizes
    game IDs to zero-padded strings so the starter join fires, calls
    reconstruct_possessions, and renames off_player_i / def_player_i to off{i} /
    def{i}. Returns a DataFrame with columns off1..off5, def1..def5, points.
    Returns an empty DataFrame (same schema) when no PBP is cached.
    """
    empty = pd.DataFrame(columns=_POSS_COLS)

    # Reconstruction (read every game's PBP + reconcile lineups) is the expensive
    # step and is shared across the single-season and pooled paths, so cache the
    # finished possession table per season. Only the regular season is cached
    # (the only season type the RAPM paths use).
    poss_cache = _cache(f"possessions_{season_str(end_year)}.csv")
    if season_type == REGULAR_SEASON and os.path.exists(poss_cache):
        try:
            cached = pd.read_csv(poss_cache)
            return cached if not cached.empty else empty
        except pd.errors.EmptyDataError:
            return empty

    try:
        logs = fetch_game_logs(end_year, season_type)
    except Exception as e:
        print(f"  possessions {season_str(end_year)}: could not load game logs: {e} — skipping")
        return empty

    game_ids = sorted(logs["GAME_ID"].dropna().unique())
    if not game_ids:
        return empty

    pbp_dfs: list[pd.DataFrame] = []
    for gid in game_ids:
        gid_str = f"{int(float(gid)):010d}"
        path = os.path.join(CACHE_DIR, f"pbp_v3_{gid_str}.csv")
        if not os.path.exists(path):
            continue
        try:
            df = pd.read_csv(path)
        except pd.errors.EmptyDataError:
            continue
        if not df.empty:
            pbp_dfs.append(df)

    if not pbp_dfs:
        return empty

    pbp_all = pd.concat(pbp_dfs, ignore_index=True)

    # Box-score starters sharpen period-start lineups. Read only the cached
    # boxscore_trad_{game_id}.csv files (do not fetch here, so the pipeline never
    # blocks on a large download); fall back to action-based inference when none
    # are cached. fetch_pbp_players() populates these in the background.
    player_dfs: list[pd.DataFrame] = []
    for gid in game_ids:
        gid_str = f"{int(float(gid)):010d}"
        bpath = os.path.join(CACHE_DIR, f"boxscore_trad_{gid_str}.csv")
        if not os.path.exists(bpath):
            continue
        try:
            bdf = pd.read_csv(bpath)
        except pd.errors.EmptyDataError:
            continue
        if not bdf.empty:
            player_dfs.append(bdf)
    players_df = pd.concat(player_dfs, ignore_index=True) if player_dfs else None

    # Reading from CSV strips the zero-padded game IDs to ints, so pbp "gameId"
    # and box "game_id" both load as e.g. 22400001. reconstruct_possessions
    # matches players_df by str(gameId), which would never line up across the two
    # frames. Normalize both to the same zero-padded string so the starter join
    # actually fires (otherwise it silently falls back to lineup inference).
    if "gameId" in pbp_all.columns:
        pbp_all["gameId"] = pbp_all["gameId"].apply(lambda g: f"{int(float(g)):010d}")
    if players_df is not None:
        players_df = players_df.copy()
        players_df["game_id"] = players_df["game_id"].apply(lambda g: f"{int(float(g)):010d}")
        print(f"  possessions {season_str(end_year)}: using box-score starters for {len(player_dfs)} games")

    poss = reconstruct_possessions(pbp_all, players_df=players_df)
    if poss.empty:
        return empty

    rename_map = {f"off_player_{i}": f"off{i}" for i in range(1, 6)}
    rename_map.update({f"def_player_{i}": f"def{i}" for i in range(1, 6)})
    poss = poss.rename(columns=rename_map)
    if season_type == REGULAR_SEASON:
        poss.to_csv(poss_cache, index=False)
    return poss


def compute_rapm(end_year: int,
                 season_type: str = REGULAR_SEASON) -> pd.DataFrame:
    """Compute RAPM from cached PBP data for one season.

    Reads all cached pbp_v3_{game_id}.csv files for the season, reconstructs
    possessions, and fits a ridge-regression RAPM. Results are cached at
    cache/rapm_computed_{season}.csv.

    Returns a DataFrame with columns player_id, RAPM, O_RAPM, D_RAPM.
    Returns an empty DataFrame (with those columns) if no PBP is cached yet.
    """
    cache_path = _cache(f"rapm_computed_{season_str(end_year)}.csv")
    empty = pd.DataFrame(columns=["player_id", "RAPM", "O_RAPM", "D_RAPM"])

    poss = _season_possessions(end_year, season_type)
    if poss.empty:
        print(f"  RAPM: no possessions for {season_str(end_year)} — skipping")
        return empty

    try:
        result = compute_rapm_fit(poss)
    except Exception as e:
        print(f"  RAPM: fit failed for {season_str(end_year)}: {e}")
        return empty

    result = result.reset_index().rename(columns={"index": "player_id"})
    # rapm() returns index named player_id when indexed
    if "player_id" not in result.columns:
        result = result.reset_index()
        result.columns.values[0] = "player_id"

    result["player_id"] = result["player_id"].astype(int)
    result.to_csv(cache_path, index=False)
    print(f"  RAPM computed from {season_str(end_year)} → {cache_path}")
    return result[["player_id", "RAPM", "O_RAPM", "D_RAPM"]]


def pool_possessions(end_year: int, n_seasons: int = 3,
                     weights=None) -> pd.DataFrame:
    """Assemble a possession table spanning multiple seasons with recency weights.

    Builds possessions for the n_seasons most recent seasons ending at end_year
    (inclusive), attaches a per-row recency weight, and concatenates. Ready to
    feed the RAPM ridge regression with pooled lineup data.

    Returns an empty DataFrame (columns off1..off5, def1..def5, points, weight)
    when fewer than 2 seasons have cached PBP — RAPM needs at least 2 seasons.

    Default weights: linear recency with the most recent season highest.
      n_seasons=3: 1/3 (oldest) / 2/3 / 1.0 (current)
      n_seasons=2: 1/2 (older) / 1.0 (current)
    Each season's position in the window determines its weight regardless of
    which other seasons have data.

    weights: optional list that overrides the defaults. Must have the same length
      as the number of seasons that actually have cached PBP, ordered oldest first.
    """
    empty = pd.DataFrame(columns=_POSS_COLS + ["weight"])

    window = list(range(end_year - n_seasons + 1, end_year + 1))  # oldest → newest
    default_w = [(pos + 1) / n_seasons for pos in range(n_seasons)]

    present: list[tuple[pd.DataFrame, float]] = []
    for pos, yr in enumerate(window):
        poss = _season_possessions(yr)
        if not poss.empty:
            present.append((poss, default_w[pos]))

    if len(present) < 2:
        return empty

    if weights is not None:
        if len(weights) != len(present):
            raise ValueError(
                f"pool_possessions: weights has {len(weights)} entries but "
                f"{len(present)} seasons have cached PBP"
            )
        present = [(df, w) for (df, _), w in zip(present, weights)]

    parts = []
    for df, w in present:
        chunk = df.copy()
        chunk["weight"] = w
        parts.append(chunk)

    return pd.concat(parts, ignore_index=True)


def compute_rapm_my(end_year: int, prior_df: pd.DataFrame | None = None,
                    n_seasons: int = 3) -> pd.DataFrame:
    """Prior-informed, multi-year RAPM (RAPM_MY).

    Pools up to n_seasons of possessions (pool_possessions) and fits the ridge
    with a box-score prior: each player's offensive coefficient shrinks toward
    OBPM and the defensive coefficient toward DBPM, so the combined estimate
    shrinks toward BPM. Low-possession players collapse onto their box score;
    heavy-minute players move toward what the pooled lineup data shows.

    prior_df: DataFrame with player_id, OBPM, DBPM. When None it is built from
    the current season's recomputed box scores.

    Returns player_id, RAPM_MY, O_RAPM_MY, D_RAPM_MY. Empty when fewer than two
    seasons of PBP are cached. Cached at cache/rapm_computed_my_{season}.csv.
    """
    cache_path = _cache(f"rapm_computed_my_{season_str(end_year)}.csv")
    empty = pd.DataFrame(columns=["player_id", "RAPM_MY", "O_RAPM_MY", "D_RAPM_MY"])

    poss = pool_possessions(end_year, n_seasons=n_seasons)
    if poss.empty:
        print(f"  RAPM_MY: <2 seasons of PBP for {season_str(end_year)} — skipping")
        return empty

    if prior_df is None:
        base = _build_recomputed(end_year).rename(columns={"PLAYER_ID": "player_id"})
        prior_df = base[["player_id", "OBPM", "DBPM"]]

    prior = prior_df.dropna(subset=["player_id"]).copy()
    prior["player_id"] = prior["player_id"].astype(int)
    prior = (prior.set_index("player_id")[["OBPM", "DBPM"]]
                  .rename(columns={"OBPM": "off", "DBPM": "def"}))

    try:
        result = compute_rapm_fit(poss, prior=prior)
    except Exception as e:
        print(f"  RAPM_MY: fit failed for {season_str(end_year)}: {e}")
        return empty

    result = result.reset_index().rename(columns={"index": "player_id"})
    if "player_id" not in result.columns:
        result.columns.values[0] = "player_id"
    result["player_id"] = result["player_id"].astype(int)
    result = result.rename(columns={"RAPM": "RAPM_MY", "O_RAPM": "O_RAPM_MY",
                                    "D_RAPM": "D_RAPM_MY"})
    result.to_csv(cache_path, index=False)
    print(f"  RAPM_MY computed (pool {n_seasons}) for {season_str(end_year)} → {cache_path}")
    return result[["player_id", "RAPM_MY", "O_RAPM_MY", "D_RAPM_MY"]]


def _load_rapm_snapshot(end_year: int) -> pd.DataFrame | None:
    """Load a public RAPM snapshot CSV for cross-validation.

    Place the downloaded CSV at cache/rapm_snapshot_{season}.csv with at
    minimum: player_name, rapm (or RAPM_PUBLIC).

    Returns None (with a skip message) when the file is absent.
    """
    path = _cache(f"rapm_snapshot_{season_str(end_year)}.csv")
    if not os.path.exists(path):
        print(f"  RAPM snapshot not found at {path} — skipping")
        return None
    try:
        df = pd.read_csv(path)
        return df if not df.empty else None
    except pd.errors.EmptyDataError:
        return None


# ── Unified ratings table ─────────────────────────────────────────────────────

def load_unified_ratings(end_year: int, *,
                          force_rebuild: bool = False) -> pd.DataFrame:
    """Return the unified ratings table for one season.

    Cached at cache/unified_ratings_{season}.csv. Set force_rebuild=True to
    re-run even if the cache exists.
    """
    path = _cache(f"unified_ratings_{season_str(end_year)}.csv")
    if os.path.exists(path) and not force_rebuild:
        return pd.read_csv(path)

    print(f"Building unified ratings table for {season_str(end_year)}...")

    # 1. Recomputed box-score ratings
    base = _build_recomputed(end_year)
    base["season_end_year"] = end_year

    # 2. Build crosswalk from authoritative nba_api player list
    player_totals = fetch_player_season_totals(end_year, REGULAR_SEASON)
    xwalk = build_crosswalk(player_totals, end_year)

    # 3. Third-party sources — join via crosswalk
    external_sources: dict[str, tuple[pd.DataFrame | None, str, dict[str, str]]] = {
        "raptor": (
            _load_raptor_from_cache_all(end_year),
            "player_name",
            {
                "raptor_total": "RAPTOR",
                "raptor_offense": "RAPTOR_O",
                "raptor_defense": "RAPTOR_D",
                "war_total": "RAPTOR_WAR",
            },
        ),
        "darko": (
            _load_darko(end_year),
            "player_name",
            {"dpm": "DARKO_DPM"},
        ),
        "epm": (
            _load_epm(end_year),
            "player_name",
            {"epm": "EPM", "epm_off": "EPM_O", "epm_def": "EPM_D"},
        ),
        "lebron": (
            _load_lebron(end_year),
            "player_name",
            {"lebron": "LEBRON"},
        ),
        "espn_rpm": (
            _load_espn_rpm(end_year),
            "player_name",
            {"rpm": "ESPN_RPM", "orpm": "ESPN_ORPM", "drpm": "ESPN_DRPM"},
        ),
    }

    merged = base.rename(columns={"PLAYER_ID": "player_id"})

    for source_name, (ext_df, name_col, col_map) in external_sources.items():
        if ext_df is None or ext_df.empty:
            continue
        ext_df = ext_df.copy()

        # Standardize season column name
        if "season_end_year" not in ext_df.columns:
            ext_df["season_end_year"] = end_year

        ext_matched = apply_crosswalk(ext_df, xwalk,
                                       name_col=name_col,
                                       season_col="season_end_year")
        crosswalk_coverage_report(ext_matched, source_name)

        # Rename relevant columns
        rename = {k: v for k, v in col_map.items() if k in ext_matched.columns}
        ext_small = ext_matched[["player_id"] + list(rename.keys())].copy()
        ext_small = ext_small.rename(columns=rename)
        ext_small = ext_small.dropna(subset=["player_id"])
        ext_small["player_id"] = ext_small["player_id"].astype(int)

        merged = merged.merge(ext_small, on="player_id", how="left")

    # 3b. Computed RAPM — joins directly by player_id (PBP carries nba_api IDs).
    # Columns are always added (all-NaN when no PBP has been fetched yet).
    rapm_df = compute_rapm(end_year)
    if not rapm_df.empty:
        rapm_df = rapm_df.dropna(subset=["player_id"]).copy()
        rapm_df["player_id"] = rapm_df["player_id"].astype(int)
        merged = merged.merge(rapm_df[["player_id", "RAPM", "O_RAPM", "D_RAPM"]],
                              on="player_id", how="left")
    else:
        for col in ("RAPM", "O_RAPM", "D_RAPM"):
            merged[col] = np.nan

    # 3c. Prior-informed multi-year RAPM (RAPM_MY) — box-score prior (OBPM/DBPM)
    # plus pooled possessions. All-NaN when fewer than two seasons are cached.
    prior_src = (merged[["player_id", "OBPM", "DBPM"]]
                 if {"OBPM", "DBPM"}.issubset(merged.columns) else None)
    rapm_my_df = compute_rapm_my(end_year, prior_df=prior_src)
    if not rapm_my_df.empty:
        rapm_my_df = rapm_my_df.dropna(subset=["player_id"]).copy()
        rapm_my_df["player_id"] = rapm_my_df["player_id"].astype(int)
        merged = merged.merge(
            rapm_my_df[["player_id", "RAPM_MY", "O_RAPM_MY", "D_RAPM_MY"]],
            on="player_id", how="left")
    else:
        for col in ("RAPM_MY", "O_RAPM_MY", "D_RAPM_MY"):
            merged[col] = np.nan

    # 3c. Public RAPM snapshot for validation — uses crosswalk
    rapm_snap = _load_rapm_snapshot(end_year)
    if rapm_snap is not None and not rapm_snap.empty:
        rapm_snap = rapm_snap.copy()
        if "season_end_year" not in rapm_snap.columns:
            rapm_snap["season_end_year"] = end_year
        snap_col = "rapm" if "rapm" in rapm_snap.columns else (
            "RAPM_PUBLIC" if "RAPM_PUBLIC" in rapm_snap.columns else None)
        if snap_col and "player_name" in rapm_snap.columns:
            snap_matched = apply_crosswalk(rapm_snap, xwalk,
                                           name_col="player_name",
                                           season_col="season_end_year")
            crosswalk_coverage_report(snap_matched, "rapm_snapshot")
            snap_small = snap_matched[["player_id", snap_col]].copy()
            snap_small = snap_small.rename(columns={snap_col: "RAPM_PUBLIC"})
            snap_small = snap_small.dropna(subset=["player_id"])
            snap_small["player_id"] = snap_small["player_id"].astype(int)
            merged = merged.merge(snap_small, on="player_id", how="left")

    # 4. Human rankings
    mvp_df = fetch_mvp_votes(end_year)
    all_nba_df = fetch_all_nba(end_year)

    for hr_df, name_col, col_map in [
        (mvp_df, "player_name", {"mvp_share": "MVP_SHARE"}),
        (all_nba_df, "player_name", {"all_nba_pts": "ALL_NBA_PTS"}),
    ]:
        if hr_df is None or hr_df.empty:
            continue
        hr_df = hr_df.copy()
        if "season_end_year" not in hr_df.columns:
            hr_df["season_end_year"] = end_year
        hr_matched = apply_crosswalk(hr_df, xwalk, name_col=name_col,
                                      season_col="season_end_year")
        rename = {k: v for k, v in col_map.items() if k in hr_matched.columns}
        hr_small = hr_matched[["player_id"] + list(rename.keys())].dropna(subset=["player_id"]).copy()
        hr_small = hr_small.rename(columns=rename)
        hr_small["player_id"] = hr_small["player_id"].astype(int)
        merged = merged.merge(hr_small, on="player_id", how="left")

    # Fill missing values for columns that should be 0 when player wasn't on the list
    for col in ["MVP_SHARE", "ALL_NBA_PTS"]:
        if col in merged.columns:
            merged[col] = merged[col].fillna(0)

    merged.to_csv(path, index=False)
    print(f"Unified ratings table: {len(merged)} players → {path}")
    return merged


def pooled_qualified_values(start_year: int, end_year: int,
                            columns: list[str]) -> pd.DataFrame:
    """Stack qualified-player rows for the given columns across a season range.

    Reads each season's cached unified-ratings table, keeps qualified players,
    and concatenates the requested columns into one long frame (one row per
    player-season). Used for distribution-shape views that need more than a
    single season to settle, RAPM in particular, whose one-season histogram is
    too sparse to read. The returned frame carries QUALIFIED=True so the plots
    that filter on it treat every pooled row as already qualified. Seasons whose
    cache is missing are skipped.
    """
    frames = []
    for yr in range(start_year, end_year + 1):
        d = load_unified_ratings(yr)
        if "QUALIFIED" in d.columns:
            d = d[d["QUALIFIED"] == True]
        keep = [c for c in columns if c in d.columns]
        if keep:
            frames.append(d[keep])
    if not frames:
        return pd.DataFrame(columns=list(columns))
    out = pd.concat(frames, ignore_index=True)
    out["QUALIFIED"] = True
    return out
