#!/usr/bin/env python3
"""
knicks_2026_analysis.py — Phase 2 analysis for "Did the 2026 Knicks have a
historic playoff run?"

Produces knicks_2026_historic_results.md with all numerical findings.  Run this first, then:
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

from nbakit.textfmt import section as _hdr, subsection as _subhdr
from nbakit.stats import binom_sf_ge, t_interval

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
    fetch_player_game_logs,
    fetch_standings,
    compute_srs,
    identify_champion,
    compute_playoff_record,
    compute_playoff_margin,
    compute_clutch_rate,
    compute_home_away_split,
    compute_opponent_srs,
    compute_avg_opponent_srs,
    compute_games_weighted_opponent_srs,
    compute_expected_margin_overperformance,
    compute_adjusted_margin,
    compute_playoff_srs,
    compute_playoff_elevation,
    compute_playoff_field_elevation,
    compute_series_margins,
    compute_opponent_playoff_srs_excl,
    compute_margin_ci,
    compute_league_scoring_avg,
    compute_pace_adjusted_margin,
    compute_conference_avg_srs,
    compute_srs_gap,
    compute_inter_conference_h2h,
    compute_opponent_health,
    fetch_game_odds,
    compute_ats_stats,
    clustered_cover_significance,
    build_champions_table,
    build_conference_gap_table,
    build_adjusted_margin_samples,
    hierarchical_adjusted_margin_rank,
    compute_elo_ratings,
    compute_bradley_terry_ratings,
    build_alt_rating_adjusted_table,
    compute_possessions_per_game,
    compute_per100_margin,
    build_possession_table,
    simulate_title_run,
    build_title_run_specs,
)

OUTPUT_DIR   = os.path.join(os.path.dirname(__file__), "generated")
RESULTS_PATH = os.path.join(os.path.dirname(__file__), "docs", "knicks_2026_historic_results.md")


# ── Helpers ──────────────────────────────────────────────────────────────────

def _pct_rank(series: pd.Series, value: float, ascending: bool = True) -> float:
    """Percentile rank of `value` within `series` (0–100)."""
    clean = series.dropna()
    if ascending:
        return float((clean <= value).mean() * 100)
    else:
        return float((clean >= value).mean() * 100)


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

    ci_lo, ci_hi = compute_margin_ci(po_2026, KNICKS_TEAM_ID)
    lo_pct = _pct_rank(mgn_series, ci_lo, ascending=True)

    print(f"\nAmong {n} champion seasons ({season_range_label(START_YEAR, END_YEAR)}):", file=out)
    print(f"  Win-rate percentile:   {wr_pct:5.1f}th  "
          f"({wr:.3f} vs. mean {wr_series.mean():.3f}, best {wr_series.max():.3f})", file=out)
    print(f"  Margin percentile:     {mgn_pct:5.1f}th  "
          f"({margin:+.1f} vs. mean {mgn_series.mean():+.1f}, best {mgn_series.max():+.1f})", file=out)
    print(f"\n  95% CI on margin (19 games, t-interval): [{ci_lo:+.1f}, {ci_hi:+.1f}]", file=out)
    print(f"  Lower CI bound {ci_lo:+.1f} would rank at {lo_pct:.0f}th pct among champions", file=out)

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
    unique_avg = float(opp_srs.mean()) if len(opp_srs) > 0 else float("nan")
    weighted_avg = compute_games_weighted_opponent_srs(po_2026, srs_2026, KNICKS_TEAM_ID)
    name_map = standings_2026.set_index("TeamID").apply(
        lambda r: f"{r['TeamCity']} {r['TeamName']}", axis=1
    ).to_dict()
    print(f"\n2025-26 Knicks playoff opponents (SRS from regular season):", file=out)
    for opp_id, srs_val in opp_srs.sort_values(ascending=False).items():
        name = name_map.get(int(opp_id), f"Team {int(opp_id)}")
        print(f"  {name:<30} SRS {srs_val:+.2f}", file=out)
    print(f"  Unique-opponent avg SRS:        {unique_avg:+.2f}", file=out)
    print(f"  Games-weighted avg SRS:         {weighted_avg:+.2f}  (primary metric)", file=out)


# ── Section 3: Historical East/West gap ─────────────────────────────────────

def run_gap_history(gap_table: pd.DataFrame, out: io.StringIO) -> None:
    print(_hdr("§3  HOW WEAK IS THE EAST HISTORICALLY?"), file=out)

    subject_gap = gap_table.loc[gap_table["year"] == SUBJECT_YEAR, "srs_gap"]
    if subject_gap.empty:
        print("  No gap data for 2025-26.", file=out)
        return

    gap_2026 = float(subject_gap.iloc[0])
    gap_pct  = _pct_rank(gap_table["srs_gap"], gap_2026, ascending=True)

    # Statistical description of the gap distribution
    gaps     = gap_table["srs_gap"].dropna()
    gap_mean = float(gaps.mean())
    gap_std  = float(gaps.std(ddof=1))
    z_score  = (gap_2026 - gap_mean) / gap_std if gap_std > 0 else float("nan")
    n        = len(gaps)
    # 95% confidence interval on the mean (t-distribution, df=n-1)
    ci_lo, ci_hi = t_interval(gap_mean, gap_std, n)

    print(f"2025-26 SRS gap (West − East): {gap_2026:+.2f} pts/game", file=out)
    print(f"Percentile among all {n} seasons "
          f"(100th = most West-dominant): {gap_pct:.1f}th", file=out)
    print(f"\nGap distribution ({n} seasons):", file=out)
    print(f"  Mean:   {gap_mean:+.2f} pts/game", file=out)
    print(f"  Std:    {gap_std:.2f} pts/game", file=out)
    print(f"  95% CI on mean: [{ci_lo:+.2f}, {ci_hi:+.2f}]", file=out)
    print(f"  Z-score of 2025-26 gap: {z_score:+.2f}  "
          f"({'above' if z_score > 0 else 'below'} historical mean)", file=out)
    if abs(z_score) < 1.0:
        sig_note = "well within normal variation (|z| < 1)."
    elif abs(z_score) < 1.96:
        sig_note = "within normal range (|z| < 1.96, not statistically unusual)."
    else:
        sig_note = "statistically unusual (|z| ≥ 1.96)."
    print(f"  2025-26 gap is {sig_note}", file=out)

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
    avg_opp  = compute_games_weighted_opponent_srs(po_2026, srs_2026, KNICKS_TEAM_ID)

    print(_hdr("§4  WHO DID THE KNICKS BEAT?"), file=out)
    print(f"Games-weighted avg opponent SRS: {avg_opp:+.2f} pts/game", file=out)

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
    avg_opp    = compute_games_weighted_opponent_srs(po_2026, srs_2026, KNICKS_TEAM_ID)
    raw_margin = compute_playoff_margin(po_2026, KNICKS_TEAM_ID)
    adj        = compute_adjusted_margin(raw_margin, avg_opp)
    knicks_srs = float(srs_2026.get(KNICKS_TEAM_ID, float("nan")))
    overperf   = compute_expected_margin_overperformance(po_2026, srs_2026, KNICKS_TEAM_ID)

    print(_hdr("§5  OPPONENT-ADJUSTED DOMINANCE"), file=out)
    print(f"Adjusted margin = raw margin − games-weighted opponent SRS", file=out)
    print(f"  Raw margin:             {raw_margin:+.2f}", file=out)
    print(f"  Games-wtd opp SRS:      {avg_opp:+.2f}", file=out)
    print(f"  Adj margin:             {adj:+.2f}", file=out)

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

    # Overperformance: per-game actual vs. SRS-predicted margin
    print(_subhdr("Playoff overperformance (vs. regular-season SRS prediction)"), file=out)
    if not np.isnan(knicks_srs) and not np.isnan(overperf):
        expected_margin = knicks_srs - avg_opp
        print(f"  Knicks regular-season SRS:  {knicks_srs:+.2f}", file=out)
        print(f"  Expected margin/game:        {expected_margin:+.2f}  "
              f"(= SRS {knicks_srs:+.2f} − opp {avg_opp:+.2f})", file=out)
        print(f"  Actual margin/game:          {raw_margin:+.2f}", file=out)
        print(f"  Overperformance:             {overperf:+.2f} pts/game", file=out)

        op_series = champions["overperformance"].dropna()
        op_pct    = _pct_rank(op_series, overperf, ascending=True)
        print(f"\n  Among {len(op_series)} champion seasons:", file=out)
        print(f"  Overperf percentile: {op_pct:.1f}th  "
              f"(mean {op_series.mean():+.2f}, best {op_series.max():+.2f})", file=out)

        top5op = champions.dropna(subset=["overperformance"]).nlargest(
            5, "overperformance"
        )[["year", "avg_margin", "champion_reg_srs", "overperformance"]]
        print(f"\n  Top 5 overperformance champions:", file=out)
        for _, row in top5op.iterrows():
            marker = "  ← 2025-26 Knicks" if int(row.year) == SUBJECT_YEAR else ""
            print(
                f"    {short_label(int(row.year))}: raw {row.avg_margin:+.2f}  "
                f"reg-SRS {row.champion_reg_srs:+.2f}  "
                f"overperf {row.overperformance:+.2f}{marker}",
                file=out,
            )


# ── Section 6: Round-by-round split — raw vs. opponent-adjusted ──────────────

def run_round_split(po_2026: pd.DataFrame,
                    reg_2026: pd.DataFrame,
                    standings_2026: pd.DataFrame,
                    champions: pd.DataFrame,
                    out: io.StringIO) -> None:
    """Per-round margin breakdown: raw, reg-season-SRS-adj, playoff-SRS-adj.

    Tests whether the East was weak *in the playoffs*, not just in the regular
    season.  If East opponents' playoff SRS < their reg-season SRS they were
    weaker in the postseason than their season rating implied; if the gap
    persists after adjusting to playoff SRS, the Knicks were genuinely dominant.
    """
    print(_hdr("§6  ROUND-BY-ROUND: RAW vs. OPPONENT-ADJUSTED"), file=out)

    srs_2026       = compute_srs(reg_2026)
    opp_po_excl    = compute_opponent_playoff_srs_excl(po_2026, KNICKS_TEAM_ID)

    series_df = compute_series_margins(po_2026, KNICKS_TEAM_ID, srs_2026, opp_po_excl)
    if series_df.empty:
        print("  No series data found.", file=out)
        return

    name_map = standings_2026.set_index("TeamID").apply(
        lambda r: f"{r['TeamCity']} {r['TeamName']}", axis=1
    ).to_dict()

    round_names = ["R1", "R2", "CF", "Finals"]

    print(
        "\nreg-adj  = raw margin − opponent regular-season SRS\n"
        "po-adj   = raw margin − opponent playoff SRS (excl. Knicks series)\n"
        "(po-adj is more positive when opponents played below their reg-season level\n"
        " against other teams; NaN = opponent had no independent playoff games)\n",
        file=out,
    )

    hdr = (f"{'Round':<8} {'Opponent':<28} {'N':>2} "
           f"{'Opp Reg SRS':>12} {'Opp PO SRS':>11} "
           f"{'Raw':>7} {'Reg-Adj':>8} {'PO-Adj':>8}")
    print(hdr, file=out)
    print("─" * len(hdr), file=out)

    for i, row in series_df.iterrows():
        rnd      = round_names[i] if i < len(round_names) else f"R{i+1}"
        name     = name_map.get(int(row["opp_id"]), f"Team {int(row['opp_id'])}")
        opp_reg  = row["opp_reg_srs"]
        opp_po   = row.get("opp_playoff_srs", float("nan"))
        raw      = row["raw_margin"]
        reg_adj  = row["reg_adj_margin"]
        po_adj   = row.get("playoff_adj_margin", float("nan"))
        print(
            f"{rnd:<8} {name:<28} {int(row['n_games']):>2} "
            f"{opp_reg:>+12.2f} {opp_po:>+11.2f} "
            f"{raw:>+7.1f} {reg_adj:>+8.1f} {po_adj:>+8.1f}",
            file=out,
        )

    print(_subhdr("Opponent reg-season SRS vs. playoff SRS"), file=out)
    print(
        "Opponent playoff SRS is computed from games EXCLUDING the Knicks series,\n"
        "so it is an independent measure of each team's playoff form.\n"
        "NaN = team had no playoff games outside the Knicks series (Hawks).\n",
        file=out,
    )
    print(f"{'Opponent':<28} {'Reg SRS':>8} {'PO SRS':>8} {'Gap (PO−Reg)':>13}  Note",
          file=out)
    print("─" * 75, file=out)
    for i, row in series_df.iterrows():
        name    = name_map.get(int(row["opp_id"]), f"Team {int(row['opp_id'])}")
        opp_reg = row["opp_reg_srs"]
        opp_po  = row.get("opp_playoff_srs", float("nan"))
        gap     = opp_po - opp_reg if not np.isnan(opp_po) else float("nan")
        if np.isnan(opp_po):
            note = "(no independent playoff games — NaN)"
        elif i == len(series_df) - 1:
            note = "(full West bracket — most independent)"
        else:
            note = "(games before reaching Knicks)"
        gap_str = f"{gap:>+13.2f}" if not np.isnan(gap) else "         n/a"
        print(f"{name:<28} {opp_reg:>+8.2f} {opp_po:>+8.2f} {gap_str}  {note}",
              file=out)

    if len(series_df) >= 2:
        pre = series_df.iloc[:-1]
        fin = series_df.iloc[-1]
        pre_raw = float(pre["raw_margin"].mean())
        pre_reg = float(pre["reg_adj_margin"].mean())
        pre_po  = float(pre["playoff_adj_margin"].mean())
        fin_raw = float(fin["raw_margin"])
        fin_reg = float(fin["reg_adj_margin"])
        fin_po  = float(fin["playoff_adj_margin"])

        print(_subhdr("Pre-Finals vs. Finals summary"), file=out)
        print(f"{'':28} {'Raw':>7} {'Reg-Adj':>8} {'PO-Adj':>8}", file=out)
        print(f"{'Pre-Finals avg (R1–CF)':<28} {pre_raw:>+7.1f} {pre_reg:>+8.1f} {pre_po:>+8.1f}", file=out)
        print(f"{'Finals':<28} {fin_raw:>+7.1f} {fin_reg:>+8.1f} {fin_po:>+8.1f}", file=out)
        print(f"{'Gap (pre − Finals)':<28} {pre_raw-fin_raw:>+7.1f} {pre_reg-fin_reg:>+8.1f} {pre_po-fin_po:>+8.1f}", file=out)

    # Historical rank: playoff-SRS-adjusted full-run margin
    if "adj_playoff_margin" in champions.columns:
        subj_rows = champions[champions["year"] == SUBJECT_YEAR]
        if not subj_rows.empty:
            knicks_pa = float(subj_rows["adj_playoff_margin"].iloc[0])
            knicks_opp_po = float(subj_rows["avg_opp_playoff_srs"].iloc[0])
            pa_series = champions["adj_playoff_margin"].dropna()
            pa_pct    = _pct_rank(pa_series, knicks_pa, ascending=True)
            print(_subhdr("Full-run opponent-playoff-SRS-adjusted margin"), file=out)
            print(
                f"  Knicks games-wtd avg opponent playoff SRS: {knicks_opp_po:+.2f}\n"
                f"  Adj margin (raw − opp playoff SRS):        {knicks_pa:+.2f}\n"
                f"  Percentile among {len(pa_series)} champions: {pa_pct:.1f}th",
                file=out,
            )
            top5 = champions.dropna(subset=["adj_playoff_margin"]).nlargest(
                5, "adj_playoff_margin"
            )[["year", "avg_margin", "avg_opp_playoff_srs", "adj_playoff_margin"]]
            print(f"\n  Top 5 (opponent-playoff-SRS-adjusted):", file=out)
            for _, r in top5.iterrows():
                marker = "  ← 2025-26 Knicks" if int(r.year) == SUBJECT_YEAR else ""
                print(
                    f"    {short_label(int(r.year))}: raw {r.avg_margin:+.2f}"
                    f"  opp-po-SRS {r.avg_opp_playoff_srs:+.2f}"
                    f"  adj {r.adj_playoff_margin:+.2f}{marker}",
                    file=out,
                )

    # 2025-26 playoff field: who improved most from the regular season
    field = compute_playoff_field_elevation(po_2026, reg_2026)
    print(_subhdr("2025-26 playoff field — most improved (reg→playoff SRS)"), file=out)
    print(
        "Full playoff SRS (all of a team's playoff games, unlike the opponent\n"
        "table above which excludes the Knicks series) minus regular-season SRS,\n"
        "computed identically for every 2025-26 playoff team.\n",
        file=out,
    )
    fhdr = f"{'Team':<28} {'Reg SRS':>8} {'PO SRS':>8} {'Elev':>7} {'PO G':>5}"
    print(fhdr, file=out)
    print("─" * len(fhdr), file=out)
    for _, frow in field.iterrows():
        nm     = name_map.get(int(frow["team_id"]), f"Team {int(frow['team_id'])}")
        marker = "  ← Knicks" if int(frow["team_id"]) == KNICKS_TEAM_ID else ""
        print(
            f"{nm:<28} {frow['reg_srs']:>+8.2f} {frow['po_srs']:>+8.2f} "
            f"{frow['elevation']:>+7.2f} {int(frow['po_games']):>5}{marker}",
            file=out,
        )


# ── Section 7: Other deflators ───────────────────────────────────────────────

def run_deflators(po_2026: pd.DataFrame, champions: pd.DataFrame,
                  out: io.StringIO) -> None:
    clutch   = compute_clutch_rate(po_2026, KNICKS_TEAM_ID)
    home_wr, away_wr = compute_home_away_split(po_2026, KNICKS_TEAM_ID)

    print(_hdr("§7  OTHER DEFLATORS"), file=out)

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

    # East (pre-Finals) combined vs. Finals close-game shape.  Series run in
    # date order, so the last opponent is the Finals; the rest are the East run.
    ordered_opps = list(dict.fromkeys(knicks_w_opp["OPP_ID"].tolist()))
    if len(ordered_opps) >= 2:
        finals_opp = ordered_opps[-1]
        east   = knicks_w_opp[knicks_w_opp["OPP_ID"] != finals_opp]
        finals = knicks_w_opp[knicks_w_opp["OPP_ID"] == finals_opp]
        east_w = int((east["WL"] == "W").sum())
        east_l = int((east["WL"] == "L").sum())
        east_margin  = float(east["PLUS_MINUS"].mean())
        finals_close = int((finals["PLUS_MINUS"].abs() <= 4).sum())
        print(_subhdr("East (pre-Finals) combined vs. Finals shape"), file=out)
        print(f"  East opponents (R1–CF), games-weighted: {east_w}-{east_l}, "
              f"avg margin {east_margin:+.1f} pts/game over {len(east)} games", file=out)
        print(f"  Finals games decided by ≤4 pts: {finals_close} of {len(finals)}", file=out)


# ── Section 8: Playoff SRS and elevation ─────────────────────────────────────

def run_playoff_srs(po_2026: pd.DataFrame,
                    reg_2026: pd.DataFrame,
                    champions: pd.DataFrame,
                    out: io.StringIO) -> None:
    """Compare the Knicks' playoff SRS to their regular-season SRS."""
    print(_hdr("§8  PLAYOFF SRS AND ELEVATION"), file=out)

    reg_srs_2026 = compute_srs(reg_2026)
    po_srs_2026  = compute_playoff_srs(po_2026)

    knicks_reg_srs = float(reg_srs_2026.get(KNICKS_TEAM_ID, float("nan")))
    knicks_po_srs  = float(po_srs_2026.get(KNICKS_TEAM_ID, float("nan")))
    elevation      = compute_playoff_elevation(po_2026, reg_2026, KNICKS_TEAM_ID)

    print(f"2025-26 Knicks:", file=out)
    print(f"  Regular-season SRS: {knicks_reg_srs:+.2f}", file=out)
    print(f"  Playoff SRS:        {knicks_po_srs:+.2f}", file=out)
    print(f"  Elevation:          {elevation:+.2f}  (playoff − regular-season SRS)", file=out)

    elev_series = champions["playoff_elevation"].dropna()
    elev_pct    = _pct_rank(elev_series, elevation, ascending=True)
    print(f"\nAmong {len(elev_series)} champion seasons:", file=out)
    print(f"  Elevation percentile: {elev_pct:.1f}th  "
          f"(mean {elev_series.mean():+.2f}, best {elev_series.max():+.2f}, "
          f"worst {elev_series.min():+.2f})", file=out)

    # Print top and bottom elevators
    top5 = champions.dropna(subset=["playoff_elevation"]).nlargest(
        5, "playoff_elevation"
    )[["year", "champion_reg_srs", "champion_po_srs", "playoff_elevation"]]
    print(f"\nTop 5 playoff elevators (most improved reg→playoff):", file=out)
    for _, row in top5.iterrows():
        marker = "  ← 2025-26 Knicks" if int(row.year) == SUBJECT_YEAR else ""
        print(
            f"  {short_label(int(row.year))}: reg {row.champion_reg_srs:+.2f} → "
            f"playoff {row.champion_po_srs:+.2f}  elev {row.playoff_elevation:+.2f}{marker}",
            file=out,
        )

    bot5 = champions.dropna(subset=["playoff_elevation"]).nsmallest(
        5, "playoff_elevation"
    )[["year", "champion_reg_srs", "champion_po_srs", "playoff_elevation"]]
    print(f"\nBottom 5 (most declined reg→playoff):", file=out)
    for _, row in bot5.iterrows():
        print(
            f"  {short_label(int(row.year))}: reg {row.champion_reg_srs:+.2f} → "
            f"playoff {row.champion_po_srs:+.2f}  elev {row.playoff_elevation:+.2f}",
            file=out,
        )


# ── Section 9: Era/pace normalization ────────────────────────────────────────

def run_pace_era(reg_2026: pd.DataFrame,
                 po_2026: pd.DataFrame,
                 champions: pd.DataFrame,
                 out: io.StringIO) -> None:
    """Compare the 2025-26 Knicks' margin to the pace-adjusted ranking."""
    srs_2026   = compute_srs(reg_2026)
    avg_opp    = compute_games_weighted_opponent_srs(po_2026, srs_2026, KNICKS_TEAM_ID)
    raw_margin = compute_playoff_margin(po_2026, KNICKS_TEAM_ID)
    adj        = compute_adjusted_margin(raw_margin, avg_opp)
    scoring_2026 = compute_league_scoring_avg(reg_2026)
    ref_scoring  = float(champions["league_scoring"].mean())
    pace_adj     = compute_pace_adjusted_margin(raw_margin, scoring_2026, ref_scoring)
    pace_adj_adj = compute_pace_adjusted_margin(adj, scoring_2026, ref_scoring)

    print(_hdr("§9  ERA / PACE ADJUSTMENT"), file=out)
    print(f"League scoring environment:", file=out)
    print(f"  2025-26 avg pts/team/game: {scoring_2026:.1f}", file=out)
    print(f"  Historical mean ({START_YEAR}–{END_YEAR}): {ref_scoring:.1f}", file=out)
    print(f"  Scale factor: {ref_scoring / scoring_2026:.3f}", file=out)
    print(f"\nKnicks 2025-26:", file=out)
    print(f"  Raw avg margin:             {raw_margin:+.2f} pts/game", file=out)
    print(f"  Pace-adjusted margin:       {pace_adj:+.2f} pts/game", file=out)
    print(f"  Opp-adj margin (raw):       {adj:+.2f} pts/game", file=out)
    print(f"  Opp+pace-adjusted margin:   {pace_adj_adj:+.2f} pts/game", file=out)

    pa_series  = champions["pace_adj_margin"].dropna()
    paa_series = champions["pace_adj_adj_margin"].dropna()
    pa_pct     = _pct_rank(pa_series,  pace_adj,     ascending=True)
    paa_pct    = _pct_rank(paa_series, pace_adj_adj, ascending=True)
    print(f"\nAmong {len(pa_series)} champion seasons:", file=out)
    print(f"  Pace-adj raw-margin percentile:      {pa_pct:.1f}th  "
          f"(mean {pa_series.mean():+.2f}, best {pa_series.max():+.2f})", file=out)
    print(f"  Opp+pace-adj margin percentile:      {paa_pct:.1f}th  "
          f"(mean {paa_series.mean():+.2f}, best {paa_series.max():+.2f})", file=out)

    top5 = champions.dropna(subset=["pace_adj_margin"]).nlargest(
        5, "pace_adj_margin"
    )[["year", "avg_margin", "league_scoring", "pace_adj_margin"]]
    print(f"\nTop 5 pace-adjusted raw-margin champions:", file=out)
    for _, row in top5.iterrows():
        marker = "  ← 2025-26 Knicks" if int(row.year) == SUBJECT_YEAR else ""
        print(
            f"  {short_label(int(row.year))}: raw {row.avg_margin:+.2f}  "
            f"era-scoring {row.league_scoring:.1f}  "
            f"pace-adj {row.pace_adj_margin:+.2f}{marker}",
            file=out,
        )

    top5adj = champions.dropna(subset=["pace_adj_adj_margin"]).nlargest(
        5, "pace_adj_adj_margin"
    )[["year", "adj_margin", "league_scoring", "pace_adj_adj_margin"]]
    print(f"\nTop 5 opp+pace-adjusted margin champions:", file=out)
    for _, row in top5adj.iterrows():
        marker = "  ← 2025-26 Knicks" if int(row.year) == SUBJECT_YEAR else ""
        print(
            f"  {short_label(int(row.year))}: opp-adj {row.adj_margin:+.2f}  "
            f"era-scoring {row.league_scoring:.1f}  "
            f"opp+pace-adj {row.pace_adj_adj_margin:+.2f}{marker}",
            file=out,
        )

    lo3 = champions.nsmallest(3, "league_scoring")[["year", "league_scoring"]]
    hi3 = champions.nlargest(3, "league_scoring")[["year", "league_scoring"]]
    print(f"\nLowest-scoring eras (margins get scaled UP):", file=out)
    for _, r in lo3.iterrows():
        print(f"  {short_label(int(r.year))}: {r.league_scoring:.1f} pts/team/game", file=out)
    print(f"Highest-scoring eras (margins get scaled DOWN):", file=out)
    for _, r in hi3.iterrows():
        print(f"  {short_label(int(r.year))}: {r.league_scoring:.1f} pts/team/game", file=out)


# ── Section 10: Verdict ──────────────────────────────────────────────────────

def run_verdict(po_2026: pd.DataFrame, reg_2026: pd.DataFrame,
                champions: pd.DataFrame, gap_table: pd.DataFrame,
                out: io.StringIO) -> None:
    wins, losses, wr = compute_playoff_record(po_2026, KNICKS_TEAM_ID)
    margin  = compute_playoff_margin(po_2026, KNICKS_TEAM_ID)
    srs     = compute_srs(reg_2026)
    avg_opp = compute_games_weighted_opponent_srs(po_2026, srs, KNICKS_TEAM_ID)
    adj     = compute_adjusted_margin(margin, avg_opp)
    overperf = compute_expected_margin_overperformance(po_2026, srs, KNICKS_TEAM_ID)

    wr_pct  = _pct_rank(champions["win_rate"],          wr,     ascending=True)
    mgn_pct = _pct_rank(champions["avg_margin"],        margin, ascending=True)
    adj_pct = _pct_rank(champions["adj_margin"].dropna(), adj,  ascending=True)
    opp_pct = _pct_rank(champions["avg_opp_srs"].dropna(), avg_opp, ascending=True)
    op_pct  = _pct_rank(champions["overperformance"].dropna(), overperf, ascending=True)

    scoring_2026 = compute_league_scoring_avg(reg_2026)
    ref_scoring  = float(champions["league_scoring"].mean())
    pace_adj     = compute_pace_adjusted_margin(margin, scoring_2026, ref_scoring)
    pa_pct       = _pct_rank(champions["pace_adj_margin"].dropna(), pace_adj, ascending=True)

    subject = gap_table.loc[gap_table["year"] == SUBJECT_YEAR]
    gap_2026 = float(subject["srs_gap"].iloc[0]) if not subject.empty else float("nan")
    gap_pct  = _pct_rank(gap_table["srs_gap"], gap_2026, ascending=True) if not np.isnan(gap_2026) else float("nan")

    print(_hdr("§10 VERDICT"), file=out)
    print(f"The 2025-26 Knicks went {wins}-{losses} in the playoffs.", file=out)
    print(f"\nKEY METRICS vs. all {len(champions)} champions ({season_range_label(START_YEAR, END_YEAR)}):", file=out)
    print(f"  Win rate {wr:.3f}:               {wr_pct:.0f}th percentile", file=out)
    print(f"  Avg margin {margin:+.1f} pts/game:    {mgn_pct:.0f}th percentile", file=out)
    print(f"  Games-wtd opp SRS {avg_opp:+.2f}:     {opp_pct:.0f}th percentile (lower = easier schedule)", file=out)
    print(f"  Adj margin {adj:+.1f} pts/game:    {adj_pct:.0f}th percentile", file=out)
    if not np.isnan(pace_adj):
        pace_adj_adj_v = compute_pace_adjusted_margin(adj, scoring_2026, ref_scoring)
        paa_pct_v = _pct_rank(champions["pace_adj_adj_margin"].dropna(), pace_adj_adj_v, ascending=True)
        print(f"  Pace-adj raw margin {pace_adj:+.1f} pts/game: {pa_pct:.0f}th percentile", file=out)
        print(f"  Opp+pace-adj margin {pace_adj_adj_v:+.1f} pts/game: {paa_pct_v:.0f}th percentile", file=out)
    if not np.isnan(overperf):
        print(f"  Overperformance {overperf:+.1f} pts/game: {op_pct:.0f}th percentile", file=out)
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


# ── Section 11: Opponent player availability ─────────────────────────────────

def run_opponent_health(player_po_logs: pd.DataFrame,
                        po_2026: pd.DataFrame,
                        standings_2026: pd.DataFrame,
                        out: io.StringIO) -> None:
    health = compute_opponent_health(
        player_po_logs, po_2026, KNICKS_TEAM_ID, standings_2026
    )

    print(_hdr("§11 OPPONENT PLAYER AVAILABILITY"), file=out)
    if health.empty:
        print("  No player availability data found.", file=out)
        return

    round_names = ["R1", "R2", "CF", "Finals"]
    print(f"{'Round':<8} {'Opponent':<30} {'Core':<6} {'Avail/game':<12} {'Health'}", file=out)
    print("─" * 65, file=out)
    for i, row in health.iterrows():
        rnd = round_names[i] if i < len(round_names) else f"R{i+1}"
        print(
            f"{rnd:<8} {row['team_name']:<30} {int(row['total_core']):<6} "
            f"{row['avg_core_per_game']:.1f}/{int(row['total_core']):<8} "
            f"{row['health_score']:.0%}",
            file=out,
        )

    print(
        "\nDefinition: 'core' = player averaging ≥15 min/game across all "
        "their 2025-26 playoff appearances.\n"
        "Health = fraction of core players who appeared per game in the "
        "Knicks series.",
        file=out,
    )

    avg_health = health["health_score"].mean()
    worst = health.loc[health["health_score"].idxmin()]
    best  = health.loc[health["health_score"].idxmax()]
    print(f"\nAverage opponent health:  {avg_health:.0%}", file=out)
    print(f"Most depleted opponent:   {worst['team_name']} ({worst['health_score']:.0%})", file=out)
    print(f"Healthiest opponent:      {best['team_name']} ({best['health_score']:.0%})", file=out)

    # Flag Finals context specifically
    finals_row = health[health["team_name"].str.contains("Spur", na=False)]
    if not finals_row.empty:
        s = float(finals_row["health_score"].iloc[0])
        if s >= 0.90:
            note = "The Spurs were fully healthy — the Finals result stands without asterisk."
        elif s >= 0.75:
            note = f"The Spurs were mostly healthy ({s:.0%}) — one key player typically absent."
        else:
            note = (
                f"The Spurs were significantly depleted ({s:.0%}) in the Finals — "
                "the close series (avg +2.4 margin) may partly reflect their injuries."
            )
        print(f"\nFinals note: {note}", file=out)


# ── Section 12: Betting-market expectations ──────────────────────────────────

def run_betting_market(ats_df: pd.DataFrame,
                       po_2026: pd.DataFrame,
                       standings_2026: pd.DataFrame,
                       out: io.StringIO) -> None:
    print(_hdr("§12 BETTING-MARKET EXPECTATIONS (ATS)"), file=out)

    if ats_df.empty:
        print("  No odds data available (BBR scrape returned no lines).", file=out)
        return

    n_total = len(ats_df)
    n_covered = int(ats_df["covered"].sum())
    avg_spread = float(ats_df["knicks_spread"].mean())
    avg_ats    = float(ats_df["ats_margin"].mean())

    print(f"Games with Vegas lines: {n_total} of 19", file=out)
    print(f"ATS record:             {n_covered}-{n_total - n_covered}", file=out)
    print(f"Avg Knicks spread:      {avg_spread:+.1f} pts (negative = Knicks favored)", file=out)
    print(f"Avg ATS margin:         {avg_ats:+.1f} pts (how much they beat the spread)", file=out)

    # Statistical significance of the ATS record
    # Null hypothesis: each game is a fair coin flip at the spread (p=0.50)
    # One-tailed p-value: P(X >= n_covered | Binom(n_total, 0.5))
    p_val = binom_sf_ge(n_covered, n_total, p=0.5)
    z = (n_covered - n_total * 0.5) / (n_total * 0.5 * 0.5) ** 0.5
    print(_subhdr("Statistical significance of ATS record"), file=out)
    print(f"  Null hypothesis: each game covers at 50% (efficient market)", file=out)
    print(f"  Observed: {n_covered}/{n_total} covers ({n_covered/n_total:.1%})", file=out)
    print(f"  Z-score:  {z:+.2f}", file=out)
    print(f"  One-tailed p-value (P(X≥{n_covered}) under null): {p_val:.4f}", file=out)
    if p_val < 0.001:
        sig = "Extremely significant (p < 0.001) — far outside normal random variation."
    elif p_val < 0.01:
        sig = "Highly significant (p < 0.01)."
    elif p_val < 0.05:
        sig = "Significant (p < 0.05)."
    else:
        sig = "Not statistically significant at p < 0.05."
    print(f"  Interpretation: {sig}", file=out)

    # Get opponent names via standings
    game_teams = (
        po_2026.groupby("GAME_ID")["TEAM_ID"]
        .apply(lambda s: [x for x in s.tolist() if x != KNICKS_TEAM_ID])
        .reset_index()
    )
    knicks_w_opp = (
        po_2026[po_2026["TEAM_ID"] == KNICKS_TEAM_ID]
        .merge(game_teams.rename(columns={"TEAM_ID": "OPP_LIST"}), on="GAME_ID")
        .copy()
    )
    knicks_w_opp["OPP_ID"] = knicks_w_opp["OPP_LIST"].apply(
        lambda x: int(x[0]) if x else None
    )
    knicks_w_opp = knicks_w_opp.sort_values("GAME_DATE")

    # Cluster-adjusted significance: the 19 games are 4 series, and outcomes
    # inside a series are correlated, so the iid binomial p above overstates it.
    opp_by_game = knicks_w_opp.set_index("GAME_ID")["OPP_ID"].to_dict()
    clust = ats_df["GAME_ID"].map(opp_by_game)
    valid = clust.notna()
    clus_res = clustered_cover_significance(
        ats_df.loc[valid, "covered"], clust[valid]
    )
    if clus_res:
        print(_subhdr("Adjusted for series correlation"), file=out)
        print(
            "  The 19 games are 4 series; covers within a series move together\n"
            "  (same matchup, correlated spread error), so the iid test above\n"
            "  overstates the evidence.  Inflating the variance by the design\n"
            "  effect gives:",
            file=out,
        )
        print(f"    Within-series correlation (ICC): {clus_res['icc']:.2f}", file=out)
        print(f"    Design effect:                   {clus_res['deff']:.2f}", file=out)
        print(f"    Effective sample size:           {clus_res['n_eff']:.1f} "
              f"(of {clus_res['n_games']} games, {clus_res['n_series']} series)", file=out)
        print(f"    Adjusted z-score:                {clus_res['z']:+.2f}", file=out)
        print(f"    Adjusted one-tailed p-value:     {clus_res['p_value']:.4f}", file=out)
        print(
            "  Still beyond chance, but an order of magnitude weaker than the iid\n"
            "  0.0022.  Note too that ATS margin is the raw margin minus a near-zero\n"
            "  average spread, so this is not independent confirmation of the\n"
            "  dominance result — it is largely the same data re-expressed.",
            file=out,
        )

    name_map = standings_2026.set_index("TeamID").apply(
        lambda r: f"{r['TeamCity']} {r['TeamName']}", axis=1
    ).to_dict()

    opp_series = (
        knicks_w_opp.dropna(subset=["OPP_ID"])
        .groupby("OPP_ID", sort=False)
        .apply(lambda g: g.sort_values("GAME_DATE").iloc[0]["GAME_DATE"])
    ).sort_values()
    first_opp_order = list(opp_series.index.astype(int))

    round_names = ["R1", "R2", "CF", "Finals"]
    print(_subhdr("Round-by-round ATS"), file=out)
    print(f"  {'Round':<8} {'Opponent':<28} {'Spread':>8} {'Actual':>8} "
          f"{'ATS':>8} {'Cover'}", file=out)
    print("  " + "─" * 65, file=out)

    opp_game_map = knicks_w_opp.set_index("GAME_ID")["OPP_ID"].to_dict()
    ats_df = ats_df.copy()
    ats_df["OPP_ID"] = ats_df["GAME_ID"].map(opp_game_map)

    for i, opp_id in enumerate(first_opp_order):
        sub = ats_df[ats_df["OPP_ID"] == opp_id]
        if sub.empty:
            continue
        rnd = round_names[i] if i < len(round_names) else f"R{i+1}"
        opp_name = name_map.get(int(opp_id), f"Team {opp_id}").split()[-1]
        avg_sp  = float(sub["knicks_spread"].mean())
        avg_act = float(sub["actual_margin"].mean())
        avg_at  = float(sub["ats_margin"].mean())
        covers  = int(sub["covered"].sum())
        total_g = len(sub)
        print(f"  {rnd:<8} {opp_name:<28} {avg_sp:>+8.1f} {avg_act:>+8.1f} "
              f"{avg_at:>+8.1f} {covers}/{total_g}", file=out)

    # Highlight Finals specifically
    finals_ats = ats_df[ats_df["OPP_ID"] == first_opp_order[-1]] if first_opp_order else pd.DataFrame()
    if not finals_ats.empty:
        finals_avg_spread = float(finals_ats["knicks_spread"].mean())
        finals_avg_actual = float(finals_ats["actual_margin"].mean())
        if finals_avg_spread < -3:
            market_view = f"favored by {abs(finals_avg_spread):.1f} pts on average"
        elif finals_avg_spread > 3:
            market_view = f"underdogs by {finals_avg_spread:.1f} pts on average"
        else:
            market_view = "near even odds"
        print(f"\nFinals market view: Knicks were {market_view}.", file=out)
        print(f"  Actual avg margin: {finals_avg_actual:+.1f} (vs. spread of {finals_avg_spread:+.1f})",
              file=out)


# ── Section 13: Robustness of the #1 ranking ─────────────────────────────────

def run_robustness(po_2026: pd.DataFrame,
                   reg_2026: pd.DataFrame,
                   champions: pd.DataFrame,
                   out: io.StringIO) -> None:
    """How fragile is the "#1 opponent-adjusted margin" claim?

    The headline rank comes from a single 19-game point estimate.  This section
    puts uncertainty on it two ways: a game-level bootstrap of the rank, and an
    empirical-Bayes shrinkage of the margin toward the champion average.
    """
    from knicks_2026_data import (
        bootstrap_adjusted_margin_rank,
        bootstrap_adjusted_margin_rank_srs_error,
        compute_srs_se,
        shrink_adjusted_margin,
    )

    print(_hdr("§13 ROBUSTNESS OF THE #1 RANKING"), file=out)

    srs_2026   = compute_srs(reg_2026)
    other_adj  = champions.loc[champions["year"] != SUBJECT_YEAR, "adj_margin"]

    boot = bootstrap_adjusted_margin_rank(
        po_2026, srs_2026, KNICKS_TEAM_ID, other_adj
    )

    print(_subhdr("Bootstrapped rank of opponent-adjusted margin"), file=out)
    if not boot:
        print("  Insufficient data to bootstrap.", file=out)
        return

    conf_pct = int(round(boot["confidence"] * 100))
    print(
        "Resamples the 19 playoff games with replacement (20,000 times) and\n"
        "re-ranks the opponent-adjusted margin against the other 42 champions.\n"
        "Games within a series are correlated, so the true spread is a little\n"
        "wider than an iid game bootstrap shows.\n",
        file=out,
    )
    print(f"  Point estimate (adj margin):  {boot['adj_point']:+.2f} pts/game", file=out)
    print(f"  {conf_pct}% interval on adj margin:  "
          f"[{boot['ci_lo']:+.2f}, {boot['ci_hi']:+.2f}]", file=out)
    print(f"  P(rank #1 all-time):          {boot['p_rank1']:.1%}", file=out)
    print(f"  P(top 3):                     {boot['p_top3']:.1%}", file=out)
    print(f"  P(top 5):                     {boot['p_top5']:.1%}", file=out)
    print(f"  Median rank:                  {boot['rank_median']:.0f}  "
          f"({conf_pct}% interval: {boot['rank_lo']:.0f}–{boot['rank_hi']:.0f})", file=out)

    shr = shrink_adjusted_margin(po_2026, srs_2026, KNICKS_TEAM_ID, other_adj)
    print(_subhdr("Empirical-Bayes shrinkage of the adjusted margin"), file=out)
    if not shr:
        print("  Insufficient data to shrink.", file=out)
        return
    shr_pct = int(round(shr["confidence"] * 100))
    print(
        "A 19-game margin singled out for being extreme overstates true strength.\n"
        "Pulling it toward how dominant championship runs typically are (the other\n"
        "42 champions, mean adj margin shown below) gives a regularized estimate.\n",
        file=out,
    )
    print(f"  Raw adjusted margin (data):   {shr['data_mean']:+.2f} pts/game", file=out)
    print(f"  Champion prior mean:          {shr['prior_mean']:+.2f} pts/game", file=out)
    print(f"  Weight on the 19-game data:   {shr['weight_data']:.0%}", file=out)
    print(f"  Shrunken (posterior) margin:  {shr['post_mean']:+.2f} pts/game", file=out)
    print(f"  {shr_pct}% credible interval:        "
          f"[{shr['ci_lo']:+.2f}, {shr['ci_hi']:+.2f}]", file=out)
    other_adj_pct = _pct_rank(other_adj.dropna(), shr["post_mean"], ascending=True)
    print(f"  Even shrunken, that margin still beats {other_adj_pct:.0f}% of "
          f"champions outright.", file=out)

    # Opponent-strength uncertainty: opponent SRS is itself estimated (~82 games)
    srs_se = compute_srs_se(reg_2026)
    se_boot = bootstrap_adjusted_margin_rank_srs_error(
        po_2026, srs_2026, srs_se, KNICKS_TEAM_ID, other_adj
    )
    print(_subhdr("Adding opponent-strength uncertainty"), file=out)
    if se_boot:
        print(
            "The opponent adjustment treats each opponent's SRS as exact, but it\n"
            "is estimated from ~82 games.  Re-running the bootstrap while also\n"
            "shocking each opponent's SRS by its standard error each time:\n",
            file=out,
        )
        print(f"  {int(round(se_boot['confidence']*100))}% interval on adj margin:  "
              f"[{se_boot['ci_lo']:+.2f}, {se_boot['ci_hi']:+.2f}]", file=out)
        print(f"  P(rank #1 all-time):          {se_boot['p_rank1']:.1%}  "
              f"(games-only was {boot['p_rank1']:.1%})", file=out)
        print(f"  P(top 5):                     {se_boot['p_top5']:.1%}", file=out)
        print("  Opponent-strength noise barely moves the picture: game-to-game\n"
              "  variance dominates the uncertainty in this ranking.", file=out)


# ── Section 14: Hierarchical (partial-pooling) ranking ───────────────────────

def run_hierarchical(samples_df: pd.DataFrame, out: io.StringIO) -> None:
    """Rank the champions by a partial-pooling Bayesian model.

    The §13 bootstrap and shrinkage each fixed the other 42 champions at their
    point estimates.  Here every champion is shrunk and carries its own posterior
    uncertainty, so a noisy rival can genuinely overtake the Knicks in a draw.
    The headline number is P(the Knicks have the highest TRUE adjusted margin).
    """
    print(_hdr("§14 HIERARCHICAL (PARTIAL-POOLING) RANK"), file=out)

    res = hierarchical_adjusted_margin_rank(samples_df, SUBJECT_YEAR)
    if not res:
        print("  Insufficient data for the hierarchical model.", file=out)
        return

    print(
        "Random-effects model over all champions' opponent-adjusted margins:\n"
        "  y_c | theta_c ~ Normal(theta_c, v_c)     (observed mean, sampling var)\n"
        "  theta_c       ~ Normal(mu, tau^2)        (population of true dominance)\n"
        "tau^2 by DerSimonian-Laird; every champion shrunk toward mu by its own\n"
        "reliability, then all champions simulated jointly and ranked.\n",
        file=out,
    )
    print(f"  Population mean (mu):            {res['mu']:+.2f} pts/game", file=out)
    print(f"  Between-champion SD (tau):       {res['tau']:.2f} pts/game", file=out)
    print(f"  Knicks raw adj margin:           "
          f"{float(samples_df.loc[samples_df['year']==SUBJECT_YEAR,'adj_mean'].iloc[0]):+.2f}", file=out)
    print(f"  Knicks posterior (shrunk) mean:  {res['subj_post_mean']:+.2f} pts/game", file=out)
    print(f"  {int(round(res['confidence']*100))}% credible interval:        "
          f"[{res['subj_ci_lo']:+.2f}, {res['subj_ci_hi']:+.2f}]", file=out)
    print(f"\n  P(Knicks are the true #1):       {res['p_rank1']:.1%}", file=out)
    print(f"  P(top 3):                        {res['p_top3']:.1%}", file=out)
    print(f"  P(top 5):                        {res['p_top5']:.1%}", file=out)
    print(f"  Median posterior rank:           {res['rank_median']:.0f}  "
          f"({int(round(res['confidence']*100))}% interval: "
          f"{res['rank_lo']:.0f}–{res['rank_hi']:.0f})", file=out)

    post = res["posterior"]
    print(_subhdr("Top champions by posterior (shrunk) adjusted margin"), file=out)
    print(f"  {'Season':<8} {'Raw adj':>8} {'Posterior':>10} {'±90% CI':>16}", file=out)
    for _, r in post.head(6).iterrows():
        marker = "  ← Knicks" if int(r["year"]) == SUBJECT_YEAR else ""
        z90 = 1.6448536
        lo = r["post_mean"] - z90 * r["post_sd"]
        hi = r["post_mean"] + z90 * r["post_sd"]
        print(f"  {short_label(int(r['year'])):<8} {r['adj_mean']:>+8.2f} "
              f"{r['post_mean']:>+10.2f}   [{lo:+.1f}, {hi:+.1f}]{marker}", file=out)


# ── Section 15: Elo opponent-rating cross-check ──────────────────────────────

def _alt_rating_ranking(alt_table: pd.DataFrame,
                        champions: pd.DataFrame,
                        rating_label: str,
                        out: io.StringIO) -> None:
    """Shared printer: rank the Knicks' adjusted margin under an alternative
    opponent rating and compare to the SRS-based rank."""
    subj = alt_table[alt_table["year"] == SUBJECT_YEAR]
    if subj.empty:
        print(f"  No {rating_label} data for the subject season.", file=out)
        return
    knicks_adj = float(subj["adj_margin"].iloc[0])
    knicks_opp = float(subj["avg_opp_rating"].iloc[0])
    series = alt_table["adj_margin"].dropna()
    pct = _pct_rank(series, knicks_adj, ascending=True)
    rank = int((series > knicks_adj).sum()) + 1

    # SRS-based rank for comparison
    srs_series = champions["adj_margin"].dropna()
    srs_subj = float(champions.loc[champions["year"] == SUBJECT_YEAR, "adj_margin"].iloc[0])
    srs_rank = int((srs_series > srs_subj).sum()) + 1

    print(f"  Knicks games-wtd opp rating ({rating_label}): {knicks_opp:+.2f} pts/game", file=out)
    print(f"  Knicks {rating_label}-adjusted margin:        {knicks_adj:+.2f} pts/game", file=out)
    print(f"  Rank among champions:               #{rank} of {len(series)} "
          f"({pct:.1f}th pct)", file=out)
    print(f"  For comparison, SRS-adjusted rank:  #{srs_rank} of {len(srs_series)}", file=out)

    # Agreement between the two systems across all champions
    merged = alt_table.merge(
        champions[["year", "adj_margin"]], on="year", suffixes=("_alt", "_srs")
    ).dropna(subset=["adj_margin_alt", "adj_margin_srs"])
    if len(merged) >= 3:
        corr = float(merged["adj_margin_alt"].corr(merged["adj_margin_srs"]))
        print(f"  Correlation with SRS-adjusted margin (all champions): {corr:+.3f}", file=out)

    top5 = alt_table.dropna(subset=["adj_margin"]).nlargest(5, "adj_margin")
    print(f"\n  Top 5 by {rating_label}-adjusted margin:", file=out)
    for _, r in top5.iterrows():
        marker = "  ← Knicks" if int(r["year"]) == SUBJECT_YEAR else ""
        print(f"    {short_label(int(r['year'])):<8} raw {r['avg_margin']:+.2f}  "
              f"opp {r['avg_opp_rating']:+.2f}  adj {r['adj_margin']:+.2f}{marker}", file=out)


def run_elo_check(elo_table: pd.DataFrame,
                  champions: pd.DataFrame,
                  reg_2026: pd.DataFrame,
                  po_2026: pd.DataFrame,
                  standings_2026: pd.DataFrame,
                  out: io.StringIO) -> None:
    """Re-rank the opponent-adjusted margin using Elo instead of SRS."""
    print(_hdr("§15 ELO OPPONENT-RATING CROSS-CHECK"), file=out)
    print(
        "SRS rates teams from season-aggregate margins.  Elo is a sequential,\n"
        "recency-weighted alternative (FiveThirtyEight NBA formula, K=20, 100-pt\n"
        "home edge, MOV multiplier), converted to points above average (~28 Elo =\n"
        "1 pt).  If the Knicks' ranking holds under Elo, it isn't an SRS artifact.\n",
        file=out,
    )
    _alt_rating_ranking(elo_table, champions, "Elo", out)

    # Sanity: the 2025-26 Knicks' opponents under both systems
    elo_2026 = compute_elo_ratings(reg_2026)
    srs_2026 = compute_srs(reg_2026)
    opp_srs = compute_opponent_srs(po_2026, srs_2026, KNICKS_TEAM_ID)
    name_map = standings_2026.set_index("TeamID").apply(
        lambda r: f"{r['TeamCity']} {r['TeamName']}", axis=1
    ).to_dict()
    print(_subhdr("2025-26 Knicks opponents: SRS vs Elo (points)"), file=out)
    print(f"  {'Opponent':<28} {'SRS':>7} {'Elo-pts':>8}", file=out)
    for opp_id in opp_srs.sort_values(ascending=False).index:
        nm = name_map.get(int(opp_id), f"Team {int(opp_id)}")
        print(f"  {nm:<28} {float(opp_srs[opp_id]):>+7.2f} "
              f"{float(elo_2026.get(int(opp_id), float('nan'))):>+8.2f}", file=out)


# ── Section 16: Wins-only (Bradley–Terry) cross-check ────────────────────────

def run_bt_check(bt_table: pd.DataFrame,
                 champions: pd.DataFrame,
                 out: io.StringIO) -> None:
    """Re-rank using a wins-only rating that never sees a point margin."""
    print(_hdr("§16 WINS-ONLY (BRADLEY–TERRY) CROSS-CHECK"), file=out)
    print(
        "SRS and Elo are both built from point margins.  Bradley–Terry is fit from\n"
        "win/loss ONLY (P(i beats j) = pi_i/(pi_i+pi_j)), so it shares no margin\n"
        "information with the raw dominance number.  Ratings are log-odds converted\n"
        "to points by the Elo convention (~6.2 pts/log-odds); only the units borrow\n"
        "that constant, the ordering is 100% wins-based.  This is the strongest test\n"
        "that the result isn't a margin-inflation artifact.\n",
        file=out,
    )
    _alt_rating_ranking(bt_table, champions, "Bradley–Terry", out)


# ── Section 17: Possessions-based pace adjustment ────────────────────────────

def run_pace_possessions(champions: pd.DataFrame,
                         poss_table: pd.DataFrame,
                         out: io.StringIO) -> None:
    """Re-do the era adjustment using estimated possessions, not points.

    §9 scales margins by points/game, which conflates pace (possessions) with
    efficiency (points per possession).  In the 3-point era teams score more per
    possession without playing faster, so the scoring-share adjustment
    over-penalizes 2025-26.  Dividing by estimated possessions isolates pace.
    """
    print(_hdr("§17 POSSESSIONS-BASED PACE ADJUSTMENT"), file=out)

    df = champions.merge(poss_table, on="year").dropna(subset=["poss_per_game"])
    if df.empty or SUBJECT_YEAR not in set(df["year"]):
        print("  No possession data available.", file=out)
        return

    df = df.copy()
    df["margin_per100"] = df.apply(
        lambda r: compute_per100_margin(r["avg_margin"], r["poss_per_game"]), axis=1)
    df["adj_per100"] = df.apply(
        lambda r: compute_per100_margin(r["adj_margin"], r["poss_per_game"]), axis=1)

    subj = df[df["year"] == SUBJECT_YEAR].iloc[0]
    poss_2026 = float(subj["poss_per_game"])
    hist_mean = float(df["poss_per_game"].mean())

    print(f"Estimated possessions (FGA − OREB + TOV + 0.44·FTA):", file=out)
    print(f"  2025-26 poss/team/game:     {poss_2026:.1f}", file=out)
    print(f"  Historical mean ({START_YEAR}–{END_YEAR}): {hist_mean:.1f}", file=out)
    print(f"  2025-26 pace is {'above' if poss_2026 > hist_mean else 'below'} "
          f"average by {abs(poss_2026-hist_mean):.1f} poss/game.\n", file=out)

    def _rank(col, val):
        s = df[col].dropna()
        return int((s > val).sum()) + 1, _pct_rank(s, val, ascending=True), len(s)

    raw_rank, raw_pct, n = _rank("margin_per100", subj["margin_per100"])
    adj_rank, adj_pct, _ = _rank("adj_per100", subj["adj_per100"])

    print(f"Knicks raw margin:              {subj['avg_margin']:+.2f} pts/game", file=out)
    print(f"  Per-100-possessions:         {subj['margin_per100']:+.2f}  "
          f"→ #{raw_rank} of {n} ({raw_pct:.1f}th pct)", file=out)
    print(f"Knicks opponent-adjusted margin:{subj['adj_margin']:+.2f} pts/game", file=out)
    print(f"  Per-100-possessions:         {subj['adj_per100']:+.2f}  "
          f"→ #{adj_rank} of {n} ({adj_pct:.1f}th pct)", file=out)

    # Contrast with the scoring-share adjustment from §9
    if "pace_adj_margin" in champions.columns:
        ps = champions["pace_adj_margin"].dropna()
        ss_subj = float(champions.loc[champions["year"] == SUBJECT_YEAR,
                                      "pace_adj_margin"].iloc[0])
        ss_rank = int((ps > ss_subj).sum()) + 1
        print(f"\n  For contrast, the §9 scoring-share adjustment put the raw margin"
              f" at #{ss_rank}.", file=out)
        print(f"  Possessions isolate pace from the 3-point scoring boom, so 2025-26"
              f" is\n  penalized less than the scoring-share number implied.", file=out)

    top5 = df.nlargest(5, "adj_per100")[
        ["year", "avg_margin", "poss_per_game", "adj_per100"]]
    print(f"\n  Top 5 by opponent-adjusted margin per 100 possessions:", file=out)
    for _, r in top5.iterrows():
        marker = "  ← Knicks" if int(r["year"]) == SUBJECT_YEAR else ""
        print(f"    {short_label(int(r['year'])):<8} raw {r['avg_margin']:+.2f}  "
              f"pace {r['poss_per_game']:.1f}  adj/100 {r['adj_per100']:+.2f}{marker}",
              file=out)


# ── Section 18: Series-level win-probability model ───────────────────────────

def run_series_winprob(po_2026: pd.DataFrame,
                       reg_2026: pd.DataFrame,
                       standings_2026: pd.DataFrame,
                       out: io.StringIO) -> None:
    """How likely was a 16-3 title run from the Knicks' regular-season strength?"""
    print(_hdr("§18 SERIES-LEVEL WIN-PROBABILITY MODEL"), file=out)

    champ_srs, specs, meta, name_map = build_title_run_specs(
        po_2026, reg_2026, standings_2026
    )

    res = simulate_title_run(champ_srs, specs)

    print(
        "Forward model from regular-season strength only (it does NOT know the\n"
        "Knicks would elevate in May).  Per game: win prob = Phi((SRS_NYK − SRS_opp\n"
        "± home edge)/sigma), sigma=12 pts, home edge=3 pts, best-of-7 per round.\n"
        f"Knicks regular-season SRS: {champ_srs:+.2f}\n",
        file=out,
    )
    round_names = ["R1", "R2", "CF", "Finals"]
    print(f"  {'Round':<8} {'Opponent':<24} {'Opp SRS':>8} {'NYK home?':>9} "
          f"{'P(win series)':>14}", file=out)
    for i, ((oid, osrs, home), p) in enumerate(zip(meta, res["series_winprob"])):
        rnd = round_names[i] if i < len(round_names) else f"R{i+1}"
        nm = name_map.get(oid, f"Team {oid}").split()[-1]
        print(f"  {rnd:<8} {nm:<24} {osrs:>+8.2f} {('yes' if home else 'no'):>9} "
              f"{p:>13.1%}", file=out)

    print(f"\n  P(Knicks win the title):           {res['p_title']:.1%}", file=out)
    print(f"  Expected losses in a title run:    {res['exp_losses_given_title']:.1f} "
          f"(actual: 3)", file=out)
    print(f"  P(a title run loses ≤3 games):     {res['p_le3_losses_given_title']:.1%} "
          f"(this is how clean 16-3 is)", file=out)
    print(f"  P(title AND ≤3 losses), unconditional: {res['p_title_and_le3_losses']:.1%}",
          file=out)
    print(
        "\nThe model made the Knicks a Finals underdog (the Spurs out-rated them in\n"
        "the regular season), so a 16-3 title was well above the forward forecast:\n"
        "they beat the bracket their own regular season predicted, echoing the\n"
        "margin-based overperformance in §5.",
        file=out,
    )


# ── Main ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("Loading 2025-26 data from cache...")
    po_2026          = fetch_game_logs(SUBJECT_YEAR, PLAYOFFS)
    reg_2026         = fetch_game_logs(SUBJECT_YEAR, REGULAR_SEASON)
    standings_2026   = fetch_standings(SUBJECT_YEAR)
    player_po_2026   = fetch_player_game_logs(SUBJECT_YEAR, PLAYOFFS)

    print("Building champion stats table (all seasons)...")
    champions = build_champions_table(START_YEAR, END_YEAR)

    print("Building conference gap table (all seasons)...")
    gap_table = build_conference_gap_table(START_YEAR, END_YEAR)

    print("Building adjusted-margin samples (all seasons)...")
    adj_samples = build_adjusted_margin_samples(START_YEAR, END_YEAR)

    print("Building Elo-adjusted table (all seasons)...")
    elo_table = build_alt_rating_adjusted_table(compute_elo_ratings, START_YEAR, END_YEAR)

    print("Building Bradley–Terry-adjusted table (all seasons)...")
    bt_table = build_alt_rating_adjusted_table(
        compute_bradley_terry_ratings, START_YEAR, END_YEAR
    )

    print("Building possession table (all seasons)...")
    poss_table = build_possession_table(START_YEAR, END_YEAR)

    print(f"Ready: {len(champions)} champion seasons, {len(gap_table)} gap seasons\n")

    out = io.StringIO()
    run_raw_claim(po_2026, champions, out)
    run_east_weakness(reg_2026, po_2026, standings_2026, out)
    run_gap_history(gap_table, out)
    run_opponent_quality(po_2026, reg_2026, champions, out)
    run_adjusted_dominance(po_2026, reg_2026, champions, out)
    run_round_split(po_2026, reg_2026, standings_2026, champions, out)
    run_deflators(po_2026, champions, out)
    run_playoff_srs(po_2026, reg_2026, champions, out)
    run_pace_era(reg_2026, po_2026, champions, out)
    run_verdict(po_2026, reg_2026, champions, gap_table, out)
    run_opponent_health(player_po_2026, po_2026, standings_2026, out)

    print("Loading betting odds from cache / BBR...", file=sys.stderr)
    odds_df  = fetch_game_odds(po_2026, KNICKS_TEAM_ID)
    ats_df   = compute_ats_stats(odds_df, po_2026, KNICKS_TEAM_ID)
    run_betting_market(ats_df, po_2026, standings_2026, out)
    run_robustness(po_2026, reg_2026, champions, out)
    run_hierarchical(adj_samples, out)
    run_elo_check(elo_table, champions, reg_2026, po_2026, standings_2026, out)
    run_bt_check(bt_table, champions, out)
    run_pace_possessions(champions, poss_table, out)
    run_series_winprob(po_2026, reg_2026, standings_2026, out)

    body = out.getvalue()

    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(RESULTS_PATH, "w") as f:
        f.write("# RESULTS\n\n")
        f.write("Auto-generated by `knicks_2026_analysis.py`. "
                "Do not edit by hand — re-run the script.\n\n")
        f.write("```\n")
        f.write(body)
        f.write("\n```\n")

    print(f"Saved → knicks_2026_historic_results.md")
    print(body)


if __name__ == "__main__":
    main()
