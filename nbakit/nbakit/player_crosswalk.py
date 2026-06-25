"""
nbakit.player_crosswalk — reconcile player identity across rating systems.

Different sources use different identifiers: nba_api uses PERSON_ID (integer),
Basketball-Reference uses slug strings (e.g., "jamesle01"), RAPTOR and DARKO
use free-text player names. This module provides a unified crosswalk so that
ratings from multiple systems can be joined into one row per (player, season).

Strategy:
1. Primary key: (normalized_name, season_end_year, team_abbr) where normalized_name
   is lowercase, no punctuation, no suffixes (Jr., Sr., III).
2. Secondary key: normalized_name + season_end_year alone (for players who changed
   teams mid-season or whose team abbreviation differs across sources).
3. Hand-maintained override table (OVERRIDES) for collision pairs and
   known bad normalizations (e.g., two players sharing a name in the same season).

Usage:
    from nbakit.player_crosswalk import build_crosswalk, apply_crosswalk

    # Build from nba_api player totals (always the authoritative id source)
    xwalk = build_crosswalk(player_totals_df)

    # Join an external df that has 'player_name', 'season', optional 'team'
    merged = apply_crosswalk(external_df, xwalk,
                             name_col='player_name', season_col='season')
"""

import re
import unicodedata

import pandas as pd


# ── Name normalization ────────────────────────────────────────────────────────

_SUFFIX_RE = re.compile(r"\b(jr\.?|sr\.?|ii|iii|iv)\b", re.IGNORECASE)
_PUNCT_RE = re.compile(r"[^a-z0-9 ]")


def normalize_name(name: str) -> str:
    """Lowercase, strip accents, remove suffixes (Jr/Sr/II/III/IV) and punctuation."""
    if not isinstance(name, str):
        return ""
    # Strip accents: é → e, ö → o, etc.
    nfkd = unicodedata.normalize("NFKD", name)
    ascii_name = nfkd.encode("ascii", "ignore").decode("ascii")
    lower = ascii_name.lower().strip()
    no_suffix = _SUFFIX_RE.sub("", lower).strip()
    no_punct = _PUNCT_RE.sub("", no_suffix)
    return re.sub(r"\s+", " ", no_punct).strip()


# ── Hand-maintained collision overrides ──────────────────────────────────────
# Format: {(normalized_name, season_end_year): preferred_player_id (nba_api PERSON_ID)}
# Add entries here when two active players share a normalized name in the same season.
OVERRIDES: dict[tuple[str, int], int] = {
    # Example (not real):
    # ("marcus morris", 2020): 1627763,  # Marcus Morris Sr.
}


# ── Crosswalk build ───────────────────────────────────────────────────────────

def build_crosswalk(player_totals: pd.DataFrame,
                    season_end_year: int) -> pd.DataFrame:
    """Build a crosswalk from nba_api player-totals for one season.

    Returns a DataFrame with columns:
      player_id, player_name, norm_name, team_abbr, season_end_year

    player_totals must have: PLAYER_ID, PLAYER_NAME, TEAM_ABBREVIATION.
    Players who appear multiple times (traded mid-season) get one row per
    team stint; the crosswalk uses all team_abbr values for matching.
    """
    p = player_totals[["PLAYER_ID", "PLAYER_NAME", "TEAM_ABBREVIATION"]].copy()
    p.columns = ["player_id", "player_name", "team_abbr"]
    p["season_end_year"] = season_end_year
    p["norm_name"] = p["player_name"].map(normalize_name)
    return p.drop_duplicates(subset=["player_id", "team_abbr"]).reset_index(drop=True)


def apply_crosswalk(external_df: pd.DataFrame,
                    crosswalk: pd.DataFrame,
                    *,
                    name_col: str = "player_name",
                    season_col: str = "season_end_year",
                    team_col: str | None = None) -> pd.DataFrame:
    """Join external_df to the crosswalk to resolve player_id.

    Matching order:
      1. (norm_name, season_end_year, team_abbr) — exact three-way match
      2. (norm_name, season_end_year) — name + season only (picks the row
         with the most minutes if duplicates exist in the crosswalk)
      3. Override table for known collision pairs

    Returns external_df with 'player_id' and 'matched_on' columns added.
    Unmatched rows get player_id=NaN and matched_on='unmatched'.
    """
    ext = external_df.copy()
    ext["_norm"] = ext[name_col].map(normalize_name)
    ext["_season"] = ext[season_col]

    # Build lookup dictionaries from crosswalk
    xw = crosswalk.copy()
    xw["_norm"] = xw["norm_name"]

    three_way: dict[tuple, int] = {}
    two_way: dict[tuple, int] = {}
    ambiguous_two_way: set[tuple] = set()

    for _, row in xw.iterrows():
        k3 = (row["_norm"], int(row["season_end_year"]), str(row["team_abbr"]).upper())
        three_way[k3] = int(row["player_id"])

        k2 = (row["_norm"], int(row["season_end_year"]))
        if k2 in two_way and two_way[k2] != int(row["player_id"]):
            ambiguous_two_way.add(k2)
        else:
            two_way[k2] = int(row["player_id"])

    ids, methods = [], []
    for _, row in ext.iterrows():
        norm = row["_norm"]
        season = int(row["_season"]) if not pd.isna(row["_season"]) else 0

        # Override check
        override_key = (norm, season)
        if override_key in OVERRIDES:
            ids.append(OVERRIDES[override_key])
            methods.append("override")
            continue

        # Three-way match (name + season + team)
        if team_col and team_col in ext.columns and not pd.isna(row.get(team_col, None)):
            team = str(row[team_col]).upper()
            k3 = (norm, season, team)
            if k3 in three_way:
                ids.append(three_way[k3])
                methods.append("name+season+team")
                continue

        # Two-way match (name + season)
        k2 = (norm, season)
        if k2 in two_way and k2 not in ambiguous_two_way:
            ids.append(two_way[k2])
            methods.append("name+season")
            continue
        if k2 in ambiguous_two_way:
            ids.append(None)
            methods.append("ambiguous")
            continue

        ids.append(None)
        methods.append("unmatched")

    ext["player_id"] = ids
    ext["matched_on"] = methods
    ext = ext.drop(columns=["_norm", "_season"])
    return ext


def crosswalk_coverage_report(merged_df: pd.DataFrame,
                               source_name: str) -> None:
    """Print a coverage summary for one external source after apply_crosswalk."""
    total = len(merged_df)
    matched = merged_df["matched_on"].isin(["name+season+team", "name+season", "override"]).sum()
    ambiguous = (merged_df["matched_on"] == "ambiguous").sum()
    unmatched = (merged_df["matched_on"] == "unmatched").sum()
    print(f"  {source_name}: {matched}/{total} matched ({100*matched/max(total,1):.1f}%), "
          f"{ambiguous} ambiguous, {unmatched} unmatched")
    if unmatched > 0:
        print("  Unmatched players:")
        for _, row in merged_df[merged_df["matched_on"] == "unmatched"].iterrows():
            name_col = [c for c in merged_df.columns if "name" in c.lower()]
            name = row[name_col[0]] if name_col else "(unknown)"
            print(f"    - {name}")
