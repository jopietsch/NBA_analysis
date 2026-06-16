#!/usr/bin/env python3
"""
knicks_2026_analysis.py — Phase 2 analysis for "Did the 2026 Knicks have a
historic playoff run?"

Produces RESULTS.md with all numerical findings.  Run this first, then:
  - knicks_2026_plots.py  (Phase 3 charts)
  - generate_report.py    (Phase 4 PDF)

All computation is in Python.  No network calls — uses cached CSVs in
nba_analysis/cache/.
"""

import io
import os
import sys

import numpy as np
import pandas as pd

from knicks_2026_data import (
    KNICKS_TEAM_ID,
    SUBJECT_YEAR,
    START_YEAR,
    END_YEAR,
    PLAYOFFS,
    REGULAR_SEASON,
    season_str,
    short_label,
    season_range_label,
    fetch_game_logs,
    fetch_standings,
    compute_srs,
    identify_champion,
    compute_playoff_record,
    compute_playoff_margin,
    compute_clutch_rate,
    compute_home_away_split,
    compute_opponent_srs,
    compute_avg_opponent_srs,
    compute_adjusted_margin,
    compute_conference_avg_srs,
    compute_srs_gap,
    compute_inter_conference_h2h,
    build_champions_table,
    build_conference_gap_table,
)

OUTPUT_DIR   = os.path.join(os.path.dirname(__file__), "generated")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "RESULTS.md")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _pct_rank(series: pd.Series, value: float, ascending: bool = True) -> float:
    """Percentile rank of `value` within `series` (0–100)."""
    clean = series.dropna()
    if ascending:
        return float((clean <= value).mean() * 100)
    else:
        return float((clean >= value).mean() * 100)


def _hdr(title: str) -> str:
    width = 72
    return f"\n{'═' * width}\n{title}\n{'─' * width}"


def _subhdr(title: str) -> str:
    return f"\n── {title} ──"


# ── Section 1: Raw claim ─────────────────────────────────────────────────────

def run_raw_claim(po_2026: pd.DataFrame,
                  champions: pd.DataFrame,
                  out: io.StringIO) -> None:
    wins, losses, wr = compute_playoff_record(po_2026, KNICKS_TEAM_ID)
    margin = compute_playoff_margin(po_2026, KNICKS_TEAM_ID)

    print(_hdr("§1  THE RAW CLAIM"), file=out)
    print(f"2025-26 Knicks playoff record: {wins}-{losses}  (win rate {wr:.3f})", file=out)
    print(f"Average margin of victory:     {margin:+.1f} pts/game", file=out)

    wr_series  = champions["win_rate"]
    mgn_series = champions["avg_margin"]
    wr_pct     = _pct_rank(wr_series,  wr,     ascending=True)
    mgn_pct    = _pct_rank(mgn_series, margin, ascending=True)
    n          = len(champions)

    print(f"\nAmong {n} champion seasons ({season_range_label(START_YEAR, END_YEAR)}):", file=out)
    print(f"  Win-rate percentile:   {wr_pct:5.1f}th  "
          f"({wr:.3f} vs. mean {wr_series.mean():.3f}, best {wr_series.max():.3f})", file=out)
    print(f"  Margin percentile:     {mgn_pct:5.1f}th  "
          f"({margin:+.1f} vs. mean {mgn_series.mean():+.1f}, best {mgn_series.max():+.1f})", file=out)

    best  = champions.loc[champions["win_rate"].idxmax()]
    worst = champions.loc[champions["win_rate"].idxmin()]
    print(f"\n  Best win rate:  {short_label(int(best.year))}  {best.win_rate:.3f}", file=out)
    print(f"  Worst win rate: {short_label(int(worst.year))}  {worst.win_rate:.3f}", file=out)


# ── Section 2: East weakness 2025-26 ────────────────────────────────────────

def run_east_weakness(reg_2026: pd.DataFrame,
                      po_2026: pd.DataFrame,
                      standings_2026: pd.DataFrame,
                      out: io.StringIO) -> None:
    srs_2026  = compute_srs(reg_2026)
    conf_avgs = compute_conference_avg_srs(srs_2026, standings_2026)
    gap       = compute_srs_gap(conf_avgs)
    h2h       = compute_inter_conference_h2h(reg_2026, standings_2026)

    print(_hdr("§2  WAS THE EAST WEAK IN 2025-26?"), file=out)
    print(f"Average regular-season SRS by conference:", file=out)
    print(f"  East: {conf_avgs['East']:+.2f}  |  West: {conf_avgs['West']:+.2f}", file=out)
    print(f"  SRS gap (West − East): {gap:+.2f} pts/game", file=out)
    print(f"  East inter-conference win rate: {h2h:.3f}", file=out)

    opp_srs  = compute_opponent_srs(po_2026, srs_2026, KNICKS_TEAM_ID)
    avg_opp  = float(opp_srs.mean()) if len(opp_srs) > 0 else float("nan")
    name_map = standings_2026.set_index("TeamID").apply(
        lambda r: f"{r['TeamCity']} {r['TeamName']}", axis=1
    ).to_dict()
    print(f"\n2025-26 Knicks playoff opponents (SRS from regular season):", file=out)
    for opp_id, srs_val in opp_srs.sort_values(ascending=False).items():
        name = name_map.get(int(opp_id), f"Team {int(opp_id)}")
        print(f"  {name:<30} SRS {srs_val:+.2f}", file=out)
    print(f"  Average opponent SRS: {avg_opp:+.2f}", file=out)


# ── Section 3: Historical East/West gap ─────────────────────────────────────

def run_gap_history(gap_table: pd.DataFrame, out: io.StringIO) -> None:
    print(_hdr("§3  HOW WEAK IS THE EAST HISTORICALLY?"), file=out)

    subject_gap = gap_table.loc[gap_table["year"] == SUBJECT_YEAR, "srs_gap"]
    if subject_gap.empty:
        print("  No gap data for 2025-26.", file=out)
        return

    gap_2026 = float(subject_gap.iloc[0])
    gap_pct  = _pct_rank(gap_table["srs_gap"], gap_2026, ascending=True)

    print(f"2025-26 SRS gap (West − East): {gap_2026:+.2f} pts/game", file=out)
    print(f"Percentile among all {len(gap_table)} seasons "
          f"(100th = most West-dominant): {gap_pct:.1f}th", file=out)

    top3 = gap_table.nlargest(3, "srs_gap")[["year", "srs_gap"]]
    print(f"\nTop 3 most West-dominant seasons:", file=out)
    for _, row in top3.iterrows():
        marker = "  ← 2025-26" if int(row.year) == SUBJECT_YEAR else ""
        print(f"  {short_label(int(row.year))}: {row.srs_gap:+.2f}{marker}", file=out)

    bottom3 = gap_table.nsmallest(3, "srs_gap")[["year", "srs_gap"]]
    print(f"\nTop 3 most East-dominant seasons:", file=out)
    for _, row in bottom3.iterrows():
        print(f"  {short_label(int(row.year))}: {row.srs_gap:+.2f}", file=out)

    h2h_2026 = float(gap_table.loc[gap_table["year"] == SUBJECT_YEAR, "east_h2h_wr"].iloc[0])
    h2h_pct  = _pct_rank(gap_table["east_h2h_wr"], h2h_2026, ascending=False)
    print(f"\n2025-26 East inter-conference win rate: {h2h_2026:.3f}", file=out)
    print(f"Percentile (100th = worst for East): {h2h_pct:.1f}th", file=out)


# ── Section 4: Opponent quality ──────────────────────────────────────────────

def run_opponent_quality(po_2026: pd.DataFrame,
                         reg_2026: pd.DataFrame,
                         champions: pd.DataFrame,
                         out: io.StringIO) -> None:
    srs_2026 = compute_srs(reg_2026)
    avg_opp  = compute_avg_opponent_srs(po_2026, srs_2026, KNICKS_TEAM_ID)

    print(_hdr("§4  WHO DID THE KNICKS BEAT?"), file=out)
    print(f"Average opponent regular-season SRS: {avg_opp:+.2f} pts/game", file=out)

    opp_series = champions["avg_opp_srs"].dropna()
    opp_pct    = _pct_rank(opp_series, avg_opp, ascending=True)
    print(f"Percentile among champions: {opp_pct:.1f}th  "
          f"(mean {opp_series.mean():+.2f}, easiest {opp_series.min():+.2f}, "
          f"hardest {opp_series.max():+.2f})", file=out)

    easiest = champions.nsmallest(5, "avg_opp_srs")[["year", "avg_opp_srs"]]
    print(f"\nChampions who faced weakest opponents (avg opp SRS):", file=out)
    for _, row in easiest.iterrows():
        marker = "  ← 2025-26 Knicks" if int(row.year) == SUBJECT_YEAR else ""
        print(f"  {short_label(int(row.year))}: {row.avg_opp_srs:+.2f}{marker}", file=out)


# ── Section 5: Opponent-adjusted dominance ──────────────────────────────────

def run_adjusted_dominance(po_2026: pd.DataFrame,
                           reg_2026: pd.DataFrame,
                           champions: pd.DataFrame,
                           out: io.StringIO) -> None:
    srs_2026   = compute_srs(reg_2026)
    avg_opp    = compute_avg_opponent_srs(po_2026, srs_2026, KNICKS_TEAM_ID)
    raw_margin = compute_playoff_margin(po_2026, KNICKS_TEAM_ID)
    adj        = compute_adjusted_margin(raw_margin, avg_opp)

    print(_hdr("§5  OPPONENT-ADJUSTED DOMINANCE"), file=out)
    print(f"Adjusted margin = raw margin − avg opponent SRS", file=out)
    print(f"  Raw margin:     {raw_margin:+.2f}", file=out)
    print(f"  Avg opp SRS:    {avg_opp:+.2f}", file=out)
    print(f"  Adj margin:     {adj:+.2f}", file=out)

    adj_series = champions["adj_margin"].dropna()
    adj_pct    = _pct_rank(adj_series, adj, ascending=True)
    print(f"\nAmong {len(adj_series)} champion seasons:", file=out)
    print(f"  Adj-margin percentile: {adj_pct:.1f}th  "
          f"(mean {adj_series.mean():+.2f}, best {adj_series.max():+.2f})", file=out)

    top5 = champions.nlargest(5, "adj_margin")[["year", "avg_margin", "avg_opp_srs", "adj_margin"]]
    print(f"\nTop 5 adjusted-margin champions:", file=out)
    for _, row in top5.iterrows():
        marker = "  ← 2025-26 Knicks" if int(row.year) == SUBJECT_YEAR else ""
        print(f"  {short_label(int(row.year))}: raw {row.avg_margin:+.2f}  opp {row.avg_opp_srs:+.2f}"
              f"  adj {row.adj_margin:+.2f}{marker}", file=out)


# ── Section 6: Other deflators ───────────────────────────────────────────────

def run_deflators(po_2026: pd.DataFrame, champions: pd.DataFrame,
                  out: io.StringIO) -> None:
    clutch   = compute_clutch_rate(po_2026, KNICKS_TEAM_ID)
    home_wr, away_wr = compute_home_away_split(po_2026, KNICKS_TEAM_ID)

    print(_hdr("§6  OTHER DEFLATORS"), file=out)

    print(_subhdr("Clutch / close games"), file=out)
    print(f"  Fraction of Knicks 2026 playoff games decided by ≤5 pts: {clutch:.3f}", file=out)
    c_pct = _pct_rank(champions["clutch_rate"].dropna(), clutch, ascending=True)
    print(f"  Percentile (100th = most clutch): {c_pct:.1f}th  "
          f"(mean {champions['clutch_rate'].mean():.3f})", file=out)

    print(_subhdr("Home/away splits"), file=out)
    knicks = po_2026[po_2026["TEAM_ID"] == KNICKS_TEAM_ID]
    home_g = knicks["MATCHUP"].str.contains(r" vs\.", na=False).sum()
    away_g = knicks["MATCHUP"].str.contains(r" @ ", na=False).sum()
    print(f"  Home games: {home_g}  win rate: {home_wr:.3f}", file=out)
    print(f"  Away games: {away_g}  win rate: {away_wr:.3f}", file=out)
    if not np.isnan(home_wr):
        h_pct = _pct_rank(champions["home_wr"].dropna(), home_wr, ascending=True)
        a_pct = _pct_rank(champions["away_wr"].dropna(), away_wr, ascending=True)
        print(f"  Home win-rate percentile (vs champions): {h_pct:.1f}th", file=out)
        print(f"  Away win-rate percentile (vs champions): {a_pct:.1f}th", file=out)

    total  = len(knicks)
    wins   = (knicks["WL"] == "W").sum()
    losses = (knicks["WL"] == "L").sum()
    print(_subhdr("Record summary"), file=out)
    print(f"  Total: {wins}W {losses}L across {total} games", file=out)

    # Round-by-round breakdown: identify series by opponent TEAM_ID
    standings_2026 = fetch_standings(SUBJECT_YEAR)
    name_map = standings_2026.set_index("TeamID").apply(
        lambda r: f"{r['TeamCity']} {r['TeamName']}", axis=1
    ).to_dict()
    game_teams = (
        po_2026.groupby("GAME_ID")["TEAM_ID"]
        .apply(lambda s: [x for x in s.tolist() if x != KNICKS_TEAM_ID])
        .reset_index()
    )
    knicks_w_opp = po_2026[po_2026["TEAM_ID"] == KNICKS_TEAM_ID].merge(
        game_teams.rename(columns={"TEAM_ID": "OPP_LIST"}), on="GAME_ID"
    ).copy()
    knicks_w_opp["OPP_ID"] = knicks_w_opp["OPP_LIST"].apply(
        lambda x: int(x[0]) if x else None
    )
    knicks_w_opp = knicks_w_opp.sort_values("GAME_DATE")

    print(_subhdr("Round-by-round breakdown"), file=out)
    for opp_id, grp in knicks_w_opp.groupby("OPP_ID", sort=False):
        grp = grp.sort_values("GAME_DATE")
        series_wins   = (grp["WL"] == "W").sum()
        series_losses = (grp["WL"] == "L").sum()
        avg_mgn = grp["PLUS_MINUS"].mean()
        opp_name = name_map.get(int(opp_id), f"Team {int(opp_id)}")
        print(f"  vs. {opp_name:<28} {series_wins}-{series_losses}  avg margin {avg_mgn:+.1f}", file=out)


# ── Section 7: Verdict ───────────────────────────────────────────────────────

def run_verdict(po_2026: pd.DataFrame, reg_2026: pd.DataFrame,
                champions: pd.DataFrame, gap_table: pd.DataFrame,
                out: io.StringIO) -> None:
    wins, losses, wr = compute_playoff_record(po_2026, KNICKS_TEAM_ID)
    margin  = compute_playoff_margin(po_2026, KNICKS_TEAM_ID)
    srs     = compute_srs(reg_2026)
    avg_opp = compute_avg_opponent_srs(po_2026, srs, KNICKS_TEAM_ID)
    adj     = compute_adjusted_margin(margin, avg_opp)

    wr_pct  = _pct_rank(champions["win_rate"],          wr,     ascending=True)
    mgn_pct = _pct_rank(champions["avg_margin"],        margin, ascending=True)
    adj_pct = _pct_rank(champions["adj_margin"].dropna(), adj,  ascending=True)
    opp_pct = _pct_rank(champions["avg_opp_srs"].dropna(), avg_opp, ascending=True)

    subject = gap_table.loc[gap_table["year"] == SUBJECT_YEAR]
    gap_2026 = float(subject["srs_gap"].iloc[0]) if not subject.empty else float("nan")
    gap_pct  = _pct_rank(gap_table["srs_gap"], gap_2026, ascending=True) if not np.isnan(gap_2026) else float("nan")

    print(_hdr("§7  VERDICT"), file=out)
    print(f"The 2025-26 Knicks went {wins}-{losses} in the playoffs.", file=out)
    print(f"\nKEY METRICS vs. all {len(champions)} champions ({season_range_label(START_YEAR, END_YEAR)}):", file=out)
    print(f"  Win rate {wr:.3f}:               {wr_pct:.0f}th percentile", file=out)
    print(f"  Avg margin {margin:+.1f} pts/game:    {mgn_pct:.0f}th percentile", file=out)
    print(f"  Avg opp SRS {avg_opp:+.2f}:           {opp_pct:.0f}th percentile (lower = easier schedule)", file=out)
    print(f"  Adj margin {adj:+.1f} pts/game:    {adj_pct:.0f}th percentile", file=out)
    if not np.isnan(gap_2026):
        print(f"  East/West SRS gap {gap_2026:+.2f}:         {gap_pct:.0f}th percentile (West dominance)", file=out)

    # Verdict logic
    print(f"\nSUMMARY:", file=out)
    if wr_pct >= 85:
        dom = "elite"
    elif wr_pct >= 70:
        dom = "strong"
    else:
        dom = "moderate"

    if adj_pct >= 70:
        adj_verdict = "holds up well after adjusting for schedule"
    elif adj_pct >= 50:
        adj_verdict = "is somewhat deflated by opponent adjustment"
    else:
        adj_verdict = "is significantly deflated by a weak schedule"

    east_context = ""
    if not np.isnan(gap_2026) and gap_pct >= 80:
        east_context = " The East was historically weak this year, providing meaningful context."

    print(f"  The 2025-26 Knicks had a {dom} playoff run by win rate, which "
          f"{adj_verdict}.{east_context}", file=out)


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Loading 2025-26 data from cache...")
    po_2026        = fetch_game_logs(SUBJECT_YEAR, PLAYOFFS)
    reg_2026       = fetch_game_logs(SUBJECT_YEAR, REGULAR_SEASON)
    standings_2026 = fetch_standings(SUBJECT_YEAR)

    print("Building champion stats table (all seasons)...")
    champions = build_champions_table(START_YEAR, END_YEAR)

    print("Building conference gap table (all seasons)...")
    gap_table = build_conference_gap_table(START_YEAR, END_YEAR)

    print(f"Ready: {len(champions)} champion seasons, {len(gap_table)} gap seasons\n")

    out = io.StringIO()
    run_raw_claim(po_2026, champions, out)
    run_east_weakness(reg_2026, po_2026, standings_2026, out)
    run_gap_history(gap_table, out)
    run_opponent_quality(po_2026, reg_2026, champions, out)
    run_adjusted_dominance(po_2026, reg_2026, champions, out)
    run_deflators(po_2026, champions, out)
    run_verdict(po_2026, reg_2026, champions, gap_table, out)

    body = out.getvalue()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        f.write("# RESULTS\n\n")
        f.write("Auto-generated by `knicks_2026_analysis.py`. "
                "Do not edit by hand — re-run the script.\n\n")
        f.write("```\n")
        f.write(body)
        f.write("\n```\n")

    print(f"Saved → RESULTS.md")
    print(body)


if __name__ == "__main__":
    main()
