"""Situational and structural mechanisms behind home-court advantage: box-score
differentials, FTA distribution, officiating (referees, shot zones), rest
buckets, rebounding (+ player tracking), 3PA rate (+ Granger causality),
pace, travel, back-to-back games, attendance, and parity."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from nbakit.textfmt import stars as _stars, p_value as _fmt_p

import home_court_data as nba
from home_court_facts import FACTS

from ._helpers import (
    suppress_noisy_fit_warnings, _warn_if_not_converged,
    _section, _pp, _ci_lo_hi, _run_cointegration, _run_league_metric_analysis,
)

def run_differential_analysis(df: pd.DataFrame) -> None:
    col_keys   = ["foul_diff", "fta_diff", "fg_pct_diff", "efg_pct_diff", "tpa_rate_diff",
                  "fg3_pct_diff", "ft_pct_diff"]
    col_labels = ["Foul diff", "FTA diff", "FG% (pp)", "eFG% (pp)", "3PA rate (pp)",
                  "3P% (pp)", "FT% (pp)"]
    COL_W = 14

    _section("FOUL & SHOOTING DIFFERENTIALS BY ERA  (home minus away, per game)")
    print("   Negative foul diff = refs call fewer fouls on the home team.")
    print("   Positive fta_diff = home team attempted more free throws.")
    print("   Trend = slope of trend line (change per season year); pp = percentage points.\n")

    # Facts for the prose (§2/§3): the home foul and free-throw-attempt gaps,
    # earliest era vs most recent, regular season and playoffs.
    _e0, _eN = nba.ERA_DEFS[0], nba.ERA_DEFS[-1]

    def _era_mean(_s, col, era):
        return float(_s[(_s["year"] >= era[1]) & (_s["year"] <= era[2])][col].mean())

    for _ctx, _sub in [("reg", df[df["is_playoff"] == 0]), ("po", df[df["is_playoff"] == 1])]:
        _foul_e = abs(_era_mean(_sub, "foul_diff", _e0))   # fouls the home team avoids
        _foul_t = abs(_era_mean(_sub, "foul_diff", _eN))
        FACTS.set(f"ref.{_ctx}_foul_early", _foul_e, "{:.1f}", note=f"{_ctx}: home foul gap, earliest era")
        FACTS.set(f"ref.{_ctx}_foul_today", _foul_t, "{:.1f}", note=f"{_ctx}: home foul gap, recent era")
        FACTS.set(f"ref.{_ctx}_foul_reduction", 100 * (1 - _foul_t / _foul_e), "{:.0f}%",
                  note=f"{_ctx}: home foul gap reduction")
        FACTS.set(f"ref.{_ctx}_fta_early", _era_mean(_sub, "fta_diff", _e0), "{:.1f}",
                  note=f"{_ctx}: home FTA gap, earliest era")
        FACTS.set(f"ref.{_ctx}_fta_today", _era_mean(_sub, "fta_diff", _eN), "{:.1f}",
                  note=f"{_ctx}: home FTA gap, recent era")
        # Signed, 2-decimal era values cited in stats_explainer.md §4.
        FACTS.set(f"diff.{_ctx}_foul_early", _era_mean(_sub, "foul_diff", _e0), "{:+.2f}",
                  note=f"{_ctx}: foul diff, earliest era")
        FACTS.set(f"diff.{_ctx}_foul_late", _era_mean(_sub, "foul_diff", _eN), "{:+.2f}",
                  note=f"{_ctx}: foul diff, recent era")
        FACTS.set(f"diff.{_ctx}_fta_early", _era_mean(_sub, "fta_diff", _e0), "{:+.2f}",
                  note=f"{_ctx}: FTA diff, earliest era")
        FACTS.set(f"diff.{_ctx}_fta_late", _era_mean(_sub, "fta_diff", _eN), "{:+.2f}",
                  note=f"{_ctx}: FTA diff, recent era")
    # The summary cites the regular-season FTA gap with coarser rounding; keep those names.
    FACTS.set("ref.fta_early", _era_mean(df[df["is_playoff"] == 0], "fta_diff", _e0), "{:.0f}",
              note="Reg. FTA gap, earliest era (rounded to whole)")
    FACTS.set("ref.fta_today", _era_mean(df[df["is_playoff"] == 0], "fta_diff", _eN), "{:.1f}",
              note="Reg. FTA gap, recent era")
    FACTS.set("ref.reg_foul_today_plain", "a quarter of a foul",
              note="prose phrasing of the reg-season foul gap today (~0.25)")

    for season_label, sub in [
        ("Regular season", df[df["is_playoff"] == 0]),
        ("Playoffs",       df[df["is_playoff"] == 1]),
    ]:
        print(f"   {season_label}  (N = {len(sub):,} games)\n")

        header = f"   {'Era':<12}" + "".join(f"{lbl:>{COL_W}}" for lbl in col_labels)
        divider = f"   {'─'*12}" + "─" * (COL_W * len(col_keys))
        print(header)
        print(divider)

        for era_label, y1, y2, _ in nba.ERA_DEFS:
            era_rows = sub[(sub["year"] >= y1) & (sub["year"] <= y2)]
            row = f"   {era_label:<12}"
            for key in col_keys:
                vals = era_rows[key].dropna()
                row += f"{vals.mean():>+{COL_W}.2f}" if len(vals) else f"{'—':>{COL_W}}"
            print(row)

        print(divider)
        trend_row = f"   {'Trend/yr':<12}"
        for key in col_keys:
            data = sub[["year", key]].dropna()
            if len(data) < 10:
                trend_row += f"{'—':>{COL_W}}"
                continue
            with suppress_noisy_fit_warnings():
                m = smf.ols(f"{key} ~ year", data=data).fit()
            coef = m.params["year"]
            pval = m.pvalues["year"]
            cell = f"{coef:>+{COL_W - 3}.3f}{_stars(pval)}"
            trend_row += cell
            # Year-trend facts cited in stats_explainer.md §4.
            _short = {"fta_diff": "fta", "fg_pct_diff": "fg", "efg_pct_diff": "efg"}
            if key in _short:
                _tc = "reg" if season_label.startswith("Regular") else "po"
                FACTS.set(f"diff.{_tc}_{_short[key]}_trend", coef, "{:+.3f}",
                          note=f"{_tc}: {key} year trend (pp/yr)")
        print(trend_row)
        print()


def run_fta_distribution_analysis(df: pd.DataFrame) -> None:
    """
    Companion to run_differential_analysis: how the small average foul/FTA
    edge compares to the game-to-game swing around it, and whether that
    swing narrowed as fast as the average edge did. Feeds Appendix B of
    FINDINGS ("how can 2 extra free throws matter").
    """
    _section("FOUL & FTA DIFFERENTIAL — PER-GAME SPREAD VS. THE AVERAGE EDGE")
    print("   P10/P90 = 10th/90th percentile of the per-game home-minus-away gap.")
    print("   width = P90 - P10, the typical night-to-night swing around the average.")
    print("   home-favored = share of games where the gap ran the home team's way.\n")

    _e0, _eN = nba.ERA_DEFS[0], nba.ERA_DEFS[-1]

    def _stats(col, era_rows, favor_home):
        vals = era_rows[col].dropna()
        p10, p90 = (float(v) for v in np.percentile(vals, [10, 90]))
        return {
            "mean":  float(vals.mean()),
            "p10":   p10, "p90": p90, "width": p90 - p10,
            "favor": 100 * float(favor_home(vals).mean()),
        }

    for _ctx, _sub in [("reg", df[df["is_playoff"] == 0]), ("po", df[df["is_playoff"] == 1])]:
        label = "Regular season" if _ctx == "reg" else "Playoffs"
        print(f"   {label}")

        eras = {}
        for era_tag, era in [("early", _e0), ("late", _eN)]:
            era_rows = _sub[(_sub["year"] >= era[1]) & (_sub["year"] <= era[2])]
            eras[era_tag] = {
                "fta":  _stats("fta_diff",  era_rows, lambda v: v > 0),
                "foul": _stats("foul_diff", era_rows, lambda v: v < 0),
            }
            fta, foul = eras[era_tag]["fta"], eras[era_tag]["foul"]
            print(f"      {era_tag:<6}  FTA  mean={fta['mean']:+.2f}  P10={fta['p10']:+.0f}  "
                  f"P90={fta['p90']:+.0f}  width={fta['width']:.0f}  home-favored={fta['favor']:.0f}%")
            print(f"      {'':6}  Foul mean={foul['mean']:+.2f}  P10={foul['p10']:+.0f}  "
                  f"P90={foul['p90']:+.0f}  width={foul['width']:.0f}  home-favored={foul['favor']:.0f}%")

            # dist.*_mean_* duplicates diff.{ctx}_{fta,foul}_{early,late} from
            # run_differential_analysis above; kept under this namespace too
            # since Appendix B's tables read every cell from "dist.*".
            for stat_key, stat in (("fta", fta), ("foul", foul)):
                FACTS.set(f"dist.{_ctx}_{stat_key}_mean_{era_tag}", stat["mean"], "{:+.2f}",
                          note=f"{_ctx} {stat_key}_diff: mean, {era_tag} era")
                FACTS.set(f"dist.{_ctx}_{stat_key}_p10_{era_tag}", stat["p10"], "{:+.0f}",
                          note=f"{_ctx} {stat_key}_diff: P10, {era_tag} era")
                FACTS.set(f"dist.{_ctx}_{stat_key}_p90_{era_tag}", stat["p90"], "{:+.0f}",
                          note=f"{_ctx} {stat_key}_diff: P90, {era_tag} era")
                FACTS.set(f"dist.{_ctx}_{stat_key}_width_{era_tag}", stat["width"], "{:.0f}",
                          note=f"{_ctx} {stat_key}_diff: P90-P10 spread, {era_tag} era")
                FACTS.set(f"dist.{_ctx}_{stat_key}_favor_{era_tag}", stat["favor"], "{:.0f}%",
                          note=f"{_ctx} {stat_key}_diff: % games favoring home, {era_tag} era")
        print()

        for stat_key in ("fta", "foul"):
            early, late = eras["early"][stat_key], eras["late"][stat_key]
            mean_drop  = 100 * (1 - abs(late["mean"]) / abs(early["mean"]))
            width_drop = 100 * (1 - late["width"] / early["width"])
            FACTS.set(f"dist.{_ctx}_{stat_key}_mean_drop_pct", mean_drop, "{:.0f}%",
                      note=f"{_ctx} {stat_key}_diff: % decline in average edge, early->late era")
            FACTS.set(f"dist.{_ctx}_{stat_key}_width_drop_pct", width_drop, "{:.0f}%",
                      note=f"{_ctx} {stat_key}_diff: % narrowing in game-to-game spread, early->late era")
            print(f"      {stat_key}: average edge fell {mean_drop:.0f}%, "
                  f"game-to-game spread narrowed only {width_drop:.0f}%")
        print()


def run_referee_analysis(bias_stats: list) -> None:
    """Per-official home foul bias for playoff games; era trend and rankings.

    PLAN-STATS items 1 & 2: uses real per-game SDs for t-tests (not the
    zero-variance trick that made every official appear significant), adds
    Benjamini–Hochberg correction across all 42 tests, method-of-moments
    variance decomposition, and empirical-Bayes shrinkage for the rankings.
    """
    from scipy import stats as sp_stats
    from statsmodels.stats.multitest import multipletests

    _section("REFEREE CREW HOME FOUL BIAS (PLAYOFFS)")
    print("   foul_diff = PF_home − PF_away  (negative = home team fouled less = home-favoring)")
    print("   Officials with <50 playoff games excluded.")
    print("   t-tests use per-game SDs (real test). BH = Benjamini-Hochberg FDR 5% correction.\n")

    n_total   = len(bias_stats)
    n_negative = sum(1 for o in bias_stats if o["mean_foul_diff"] < 0)
    all_means  = [o["mean_foul_diff"] for o in bias_stats]
    league_mean = float(np.mean(all_means))

    # ── Real one-sample t-tests using per-game SDs ──────────────────────────
    raw_pvals: list[float] = []
    for o in bias_stats:
        n  = o["n_games"]
        sd = o.get("sd_foul_diff", 0.0)
        if sd > 0 and n > 1:
            t = o["mean_foul_diff"] / (sd / np.sqrt(n))
            p = float(sp_stats.t.sf(abs(t), n - 1) * 2)
        else:
            p = np.nan
        raw_pvals.append(p)

    # BH correction across all officials simultaneously
    valid_idx = [i for i, p in enumerate(raw_pvals) if not np.isnan(p)]
    bh_pvals: list[float] = [np.nan] * n_total
    if valid_idx:
        _, padj, _, _ = multipletests([raw_pvals[i] for i in valid_idx], method="fdr_bh")
        for k, i in enumerate(valid_idx):
            bh_pvals[i] = float(padj[k])

    n_sig_raw = sum(1 for p in raw_pvals if not np.isnan(p) and p < 0.05)
    n_sig_bh  = sum(1 for p in bh_pvals  if not np.isnan(p) and p < 0.05)

    print(f"   {n_total} officials with ≥50 playoff games")
    print(f"   {n_negative}/{n_total} ({100*n_negative/n_total:.0f}%) show negative mean foul diff (home-favoring)")
    # Facts for the prose (§2/§6/Appendix B): N of M playoff officials call fewer
    # fouls on the home team.
    FACTS.set("ref.n_biased", n_negative, "{:d}",
              note="Playoff officials (≥50 games) with a home-favoring foul gap")
    FACTS.set("ref.n_total", n_total, "{:d}", note="Playoff officials with ≥50 games on record")
    FACTS.set("ref.n_significant", n_sig_bh, "{:d}",
              note="Playoff officials individually clear after Benjamini-Hochberg correction")
    print(f"   Individually significant (p<0.05, real t-test):    {n_sig_raw}/{n_total}")
    print(f"   Survive Benjamini-Hochberg correction (FDR 5%):    {n_sig_bh}/{n_total}")
    print(f"   League mean foul_diff across officials: {league_mean:+.3f} fouls/game")

    # ── Method-of-moments variance decomposition — career level ─────────────
    obs_var = float(np.var(all_means, ddof=1))
    samp_vars = [
        o["sd_foul_diff"] ** 2 / o["n_games"]
        for o in bias_stats
        if o.get("sd_foul_diff", 0.0) > 0 and o["n_games"] > 1
    ]
    mean_samp_var = float(np.mean(samp_vars)) if samp_vars else 0.0
    true_var = max(0.0, obs_var - mean_samp_var)
    true_sd  = float(np.sqrt(true_var))

    print(f"\n   Variance decomposition (career level, method of moments):")
    print(f"   Observed SD across officials: {np.sqrt(obs_var):.3f} fouls/game")
    print(f"   Mean within-official SE:      {np.sqrt(mean_samp_var):.3f} fouls/game")
    print(f"   Estimated true between-SD:    {true_sd:.3f} fouls/game")
    if true_var == 0:
        print(f"   ► Career-mean spread is entirely sampling noise (true between-official SD ≈ 0).")
    else:
        noise_pct = 100.0 * mean_samp_var / obs_var if obs_var > 0 else 0.0
        print(f"   ► Sampling noise explains {noise_pct:.0f}% of observed spread.")

    # ── Empirical-Bayes shrinkage ────────────────────────────────────────────
    shrunken: list[float] = []
    for o in bias_stats:
        sd_i = o.get("sd_foul_diff", 0.0)
        if true_var > 0 and sd_i > 0 and o["n_games"] > 1:
            samp_var_i = sd_i ** 2 / o["n_games"]
            w = true_var / (true_var + samp_var_i)
            shrunken.append(w * o["mean_foul_diff"] + (1.0 - w) * league_mean)
        else:
            shrunken.append(league_mean)

    # Sort by shrunken mean ascending = most home-favoring (most negative) first
    ranked = sorted(
        zip(bias_stats, raw_pvals, bh_pvals, shrunken),
        key=lambda x: x[3],
    )

    # Facts for the prose (Appendix A): last playoff season each of the three
    # most home-favoring officials worked (named in the findings text).
    by_name = {o["name"]: o for o in bias_stats}
    print(f"\n   Last playoff season worked, most home-favoring officials:")
    for slug, official_name in [
        ("garretson", "Ron Garretson"), ("crawford", "Joe Crawford"), ("rush", "Eddie Rush"),
    ]:
        o = by_name.get(official_name)
        if o is not None:
            last_season = nba.season_str(o["last_year"])
            print(f"   {official_name:<20} last worked {last_season}")
            FACTS.set(f"ref.{slug}_last_season", last_season,
                      note=f"Last playoff season officiated by {official_name}")

    NW, CW = 26, 9

    header = (f"   {'Official':<{NW}} {'N games':>{CW}} {'Raw diff':>{CW}} "
              f"{'Shrunken':>{CW}} {'p':>{CW}} {'BH-p':>{CW}}")
    sep    = f"   {'─'*NW} {'─'*CW} {'─'*CW} {'─'*CW} {'─'*CW} {'─'*CW}"

    def _print_block(block):
        print(header)
        print(sep)
        for o, rp, bp, s in block:
            print(f"   {o['name']:<{NW}} {o['n_games']:>{CW},} "
                  f"{o['mean_foul_diff']:>+{CW}.3f} {s:>+{CW}.3f} "
                  f"{_fmt_p(rp):>{CW}} {_fmt_p(bp):>{CW}}")

    print(f"\n   Top 10 most home-favoring (by shrunken mean foul_diff):")
    _print_block(ranked[:10])
    print(f"\n   Bottom 10 least home-favoring (by shrunken mean foul_diff):")
    _print_block(ranked[-10:])

    # ── Era variance decomposition ───────────────────────────────────────────
    era_order = [e[0] for e in nba.ERA_DEFS]
    era_entries: dict[str, list[tuple[float, float, int]]] = {e: [] for e in era_order}
    for o in bias_stats:
        for era in era_order:
            m  = o["era_means"].get(era)
            sd = o.get("era_sd", {}).get(era)
            n  = o.get("era_n", {}).get(era, 0)
            if m is not None and sd is not None and n > 1:
                era_entries[era].append((float(m), float(sd), int(n)))

    print(f"\n   Era variance decomposition — does official spread compress over time?")
    print(f"   {'Era':<12} {'N off':>7} {'Mean':>8} {'Raw SD':>9} {'True SD':>9} {'Noise %':>9}")
    print(f"   {'─'*12} {'─'*7} {'─'*8} {'─'*9} {'─'*9} {'─'*9}")
    for era in era_order:
        entries = era_entries[era]
        if len(entries) < 3:
            continue
        vals   = [e[0] for e in entries]
        obs_v  = float(np.var(vals, ddof=1))
        sv     = float(np.mean([e[1] ** 2 / e[2] for e in entries]))
        true_v = max(0.0, obs_v - sv)
        noise  = 100.0 * min(1.0, sv / obs_v) if obs_v > 0 else 100.0
        print(f"   {era:<12} {len(vals):>7} {np.mean(vals):>+8.3f} "
              f"{np.sqrt(obs_v):>9.3f} {np.sqrt(true_v):>9.3f} {noise:>8.0f}%")
    print()


def run_shot_zone_analysis(
    reg_seasons: list, reg_stats: dict,
    po_seasons:  list, po_stats:  dict,
) -> None:
    """Trend line for each shot zone differential — parallel to run_differential_analysis."""
    zone_labels = {
        "paint":    "Paint (RA+Non-RA)",
        "midrange": "Mid-Range",
        "corner3":  "Corner 3",
        "above3":   "Above Break 3",
    }
    COL_W = 18

    _section("SHOT ZONE DIFFERENTIALS BY ERA  (home minus road % of FGA)")
    print("   Positive = home team takes a higher share of FGA from that zone.")
    print("   Trend = slope of trend line (change per season year). Data from 1996–97 onward.\n")

    # Facts for the prose (§3): the home paint-attempt-share gap, then vs now.
    _zyears = [nba.label_to_year(s) for s in reg_seasons]

    def _paint_era(era):
        idx = [i for i, y in enumerate(_zyears) if era[1] <= y <= era[2]]
        vals = [reg_stats["paint"][i] for i in idx if not np.isnan(reg_stats["paint"][i])]
        return float(np.mean(vals)) if vals else float("nan")

    if reg_seasons:
        _first_era = next((e for e in nba.ERA_DEFS if not np.isnan(_paint_era(e))), nba.ERA_DEFS[0])
        FACTS.set("zone.paint_early", _paint_era(_first_era), "{:.1f}",
                  note="Reg. paint FGA-share gap (home minus away), earliest era with data")
        FACTS.set("zone.paint_today", _paint_era(nba.ERA_DEFS[-1]), "{:.1f}",
                  note="Reg. paint FGA-share gap (home minus away), recent era")

    for season_label, seasons, stats in [
        ("Regular season", reg_seasons, reg_stats),
        ("Playoffs",       po_seasons,  po_stats),
    ]:
        if not seasons:
            continue

        years = [nba.label_to_year(s) for s in seasons]
        col_keys = list(zone_labels.keys())
        col_display = list(zone_labels.values())

        print(f"   {season_label}  (N = {len(seasons)} seasons)\n")
        header  = f"   {'Era':<12}" + "".join(f"{lbl:>{COL_W}}" for lbl in col_display)
        divider = f"   {'─'*12}" + "─" * (COL_W * len(col_keys))
        print(header)
        print(divider)

        for era_label, y1, y2, _ in nba.ERA_DEFS:
            era_idx = [i for i, y in enumerate(years) if y1 <= y <= y2]
            if not era_idx:
                continue
            row = f"   {era_label:<12}"
            for key in col_keys:
                vals = [stats[key][i] for i in era_idx if not np.isnan(stats[key][i])]
                row += f"{np.mean(vals):>+{COL_W}.2f}" if vals else f"{'—':>{COL_W}}"
            print(row)

        print(divider)
        trend_row = f"   {'Trend/yr':<12}"
        for key in col_keys:
            pairs = [(y, v) for y, v in zip(years, stats[key]) if not np.isnan(v)]
            if len(pairs) < 3:
                trend_row += f"{'—':>{COL_W}}"
                continue
            tdf = pd.DataFrame(pairs, columns=["year", "val"])
            with suppress_noisy_fit_warnings():
                m = smf.ols("val ~ year", data=tdf).fit()
            c    = m.params["year"]
            pval = m.pvalues["year"]
            trend_row += f"{c:>+{COL_W - 3}.3f}{_stars(pval)}"
        print(trend_row)
        print()


def compute_rest_altitude_plotdata(df: pd.DataFrame) -> dict:
    """Chart-ready home win % by rest situation and for the altitude teams.

    Returns {"rest": {ctx: {...}}, "altitude": {ctx: {...}}} for ctx in
    ("reg", "po"). Rest buckets mirror run_rest_bucket_analysis; altitude
    compares each high-elevation team's home win % to the league baseline.
    The chart rendered from this is the visual companion to those two
    RESULTS sections — same numbers, no new data.
    """
    rest_buckets = [
        ("Away more rested", lambda s: s < 0),
        ("Equal rest",       lambda s: s == 0),
        ("Home more rested", lambda s: s > 0),
    ]
    out: dict = {"rest": {}, "altitude": {}}
    for ctx, is_po in [("reg", 0), ("po", 1)]:
        sub = df[df["is_playoff"] == is_po]

        r = sub.dropna(subset=["rest_diff"])
        out["rest"][ctx] = {
            "baseline": 100.0 * r["home_win"].mean() if len(r) else float("nan"),
            "buckets": {
                label: (100.0 * b["home_win"].mean(), len(b))
                for label, cond in rest_buckets
                if len(b := r[cond(r["rest_diff"])])
            },
        }

        alt = {"League": (100.0 * sub["home_win"].mean(), len(sub))}
        for team in nba.ALTITUDE_TEAMS:
            t = sub[sub["TEAM_NAME_home"] == team]
            if len(t):
                alt[team] = (100.0 * t["home_win"].mean(), len(t))
        out["altitude"][ctx] = alt
    return out


def run_rest_bucket_analysis(df: pd.DataFrame) -> None:
    """Home win % by rest-differential bucket, plus a rest × era interaction
    test — has the rest effect changed across eras?"""
    from scipy.stats import chi2, chi2_contingency

    _section("REST DIFFERENTIAL — WIN % BY BUCKET AND ERA STABILITY")
    print("   Buckets: away team more rested (rest_diff < 0), equal rest, and home")
    print("   team more rested (rest_diff > 0). Games without a prior game to")
    print("   compute rest from are excluded.\n")

    buckets = [
        ("Away more rest", lambda s: s < 0),
        ("Equal rest",     lambda s: s == 0),
        ("Home more rest", lambda s: s > 0),
    ]

    for ctx_label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po].dropna(subset=["rest_diff"])
        if sub.empty:
            continue
        p_bar = sub["home_win"].mean() * 100
        print(f"   {ctx_label}  (N = {len(sub):,}, baseline home win % = {p_bar:.1f}%)\n")
        print(f"   {'Bucket':<16}  {'N games':>8}  {'Home win %':>11}  {'vs. baseline':>13}")
        print(f"   {'─'*16}  {'─'*8}  {'─'*11}  {'─'*13}")

        table = []
        pct_by_bucket = {}
        for label, cond in buckets:
            b = sub[cond(sub["rest_diff"])]
            if b.empty:
                continue
            wins, n = int(b["home_win"].sum()), len(b)
            pct = 100.0 * wins / n
            pct_by_bucket[label] = pct
            table.append([wins, n - wins])
            print(f"   {label:<16}  {n:>8,}  {pct:>10.1f}%  {pct - p_bar:>+12.1f} pp")

        # Facts for the prose (§4): home win % when each side is better-rested.
        if is_po == 0 and {"Home more rest", "Away more rest"} <= pct_by_bucket.keys():
            FACTS.set("rest.home_rested", pct_by_bucket["Home more rest"], "{:.0f}%",
                      note="Reg. home win % when the home team is better-rested")
            FACTS.set("rest.visitor_rested", pct_by_bucket["Away more rest"], "{:.0f}%",
                      note="Reg. home win % when the visitor is better-rested")
            FACTS.set("rest.away_vs_baseline", abs(pct_by_bucket["Away more rest"] - p_bar), "{:.1f}",
                      note="Reg. home win % drop when the visitor is better-rested, vs baseline")

        if len(table) >= 2:
            stat, p_chi, dof, _ = chi2_contingency(table)
            p_s = _fmt_p(p_chi)
            print(f"\n   Chi-square (H0: home win % equal across buckets): "
                  f"χ²({dof}) = {stat:.2f},  p = {p_s}  {_stars(p_chi).strip()}")

        print(f"\n   Rest effect by era (bivariate logistic within each era):")
        print(f"   {'Era':<12}  {'N':>7}  {'log-odds/day':>13}  {'≈pp/day':>8}  {'p':>8}  {'':3}")
        print(f"   {'─'*12}  {'─'*7}  {'─'*13}  {'─'*8}  {'─'*8}  {'─'*3}")
        for era_label, y1, y2, _ in nba.ERA_DEFS:
            era_rows = sub[(sub["year"] >= y1) & (sub["year"] <= y2)]
            if len(era_rows) < 50 or era_rows["rest_diff"].nunique() < 2:
                continue
            with suppress_noisy_fit_warnings():
                try:
                    m = smf.logit("home_win ~ rest_diff", data=era_rows).fit(disp=0)
                    _warn_if_not_converged(m, "run_rest_bucket_analysis: m")
                except Exception:
                    continue
            c, p = m.params["rest_diff"], m.pvalues["rest_diff"]
            pb = era_rows["home_win"].mean()
            p_s = _fmt_p(p)
            print(f"   {era_label:<12}  {len(era_rows):>7,}  {c:>+13.3f}  "
                  f"{_pp(c, pb):>+8.1f}  {p_s:>8}  {_stars(p)}")

        try:
            with suppress_noisy_fit_warnings():
                m_add = smf.logit("home_win ~ rest_diff + C(era)", data=sub).fit(disp=0)
                _warn_if_not_converged(m_add, "run_rest_bucket_analysis: m_add")
                m_int = smf.logit("home_win ~ rest_diff * C(era)", data=sub).fit(disp=0)
                _warn_if_not_converged(m_int, "run_rest_bucket_analysis: m_int")
            lr    = 2.0 * (m_int.llf - m_add.llf)
            dfree = int(m_int.df_model - m_add.df_model)
            p_lr  = chi2.sf(lr, dfree)
            p_lr_s = _fmt_p(p_lr)
            verdict = ("the rest effect has NOT been stable across eras"
                       if p_lr < 0.05
                       else "no evidence the rest effect changed across eras")
            print(f"\n   Rest × era interaction (LR test): χ²({dfree}) = {lr:.2f},  "
                  f"p = {p_lr_s}  {_stars(p_lr).strip()}")
            print(f"   ► {verdict}.")
        except Exception:
            pass
        print()


def run_rebounding_decomposition(df: pd.DataFrame) -> None:
    """Split the home rebounding edge into offensive vs defensive boards and a
    pace-free rebound share, then test whether it tracks the league-wide retreat
    from offensive rebounding.

    The mediation accounting credits rebounding with the largest single share of
    the HCA decline but cannot say why. Raw rebound counts conflate skill with
    shot volume and pace, so this re-expresses the edge as the home team's share
    of available offensive boards (OREB / (OREB + opponent DREB)) and correlates
    it, season by season, with the league's overall offensive-rebound rate.
    """
    col_keys   = ["oreb_diff", "dreb_diff", "reb_diff", "reb_share_edge"]
    col_labels = ["OREB diff", "DREB diff", "REB diff", "Share edge (pp)"]
    COL_W = 16

    _section("REBOUNDING DECOMPOSITION — WHY THE HOME EDGE FADED  (home minus away)")
    print("   OREB/DREB diff = home minus away offensive/defensive rebounds per game.")
    print("   Share edge = home share of available offensive boards minus away share")
    print("   (percentage points) — a pace- and volume-free measure of the edge.")
    print("   Trend = slope of trend line (change per season year).\n")

    # Facts for the prose (§3): the home offensive- and defensive-rebound gaps,
    # earliest era vs most recent (regular season).
    _reg_reb = df[df["is_playoff"] == 0]
    _e0, _eN = nba.ERA_DEFS[0], nba.ERA_DEFS[-1]

    def _reb_mean(col, era):
        return float(_reg_reb[(_reg_reb["year"] >= era[1]) & (_reg_reb["year"] <= era[2])][col].mean())

    FACTS.set("reb.dreb_early", _reb_mean("dreb_diff", _e0), "{:+.1f}",
              note="Reg. DREB diff (home minus away), earliest era")
    FACTS.set("reb.dreb_today", _reb_mean("dreb_diff", _eN), "{:+.1f}",
              note="Reg. DREB diff (home minus away), recent era")
    FACTS.set("reb.oreb_early", _reb_mean("oreb_diff", _e0), "{:+.1f}",
              note="Reg. OREB diff (home minus away), earliest era")

    # Facts for the prose (§3): home vs away offensive-rebound conversion rates,
    # the converging lines in the rebounding chart (same compute as the plot).
    _rseasons, _rstats = nba.compute_rebound_stats(nba.START_YEAR, nba.END_YEAR, "Regular Season")
    _h = [v for v in _rstats["oreb_rate_home"] if v == v]
    _a = [v for v in _rstats["oreb_rate_away"] if v == v]
    if _h and _a:
        FACTS.set("reb.oreb_home_early", _h[0], "{:.0f}%", note="Home OREB conversion rate, first season")
        FACTS.set("reb.oreb_away_early", _a[0], "{:.0f}%", note="Away OREB conversion rate, first season")
        FACTS.set("reb.oreb_home_drop", _h[0] - _h[-1], "{:.0f}", note="Home OREB rate drop, first to last season (pp)")
        FACTS.set("reb.oreb_away_drop", _a[0] - _a[-1], "{:.0f}", note="Away OREB rate drop, first to last season (pp)")

    # Statistical detail for investigation.md: the pace-free share-edge trend + p,
    # and the early/recent share-edge level, regular season and playoffs.
    for _rc, _rsub in [("reg", df[df["is_playoff"] == 0]), ("po", df[df["is_playoff"] == 1])]:
        _se = _rsub[["year", "reb_share_edge"]].dropna()
        if len(_se) >= 10:
            with suppress_noisy_fit_warnings():
                _sm = smf.ols("reb_share_edge ~ year", data=_se).fit()
            FACTS.set(f"{_rc}.reb_share_trend", _sm.params["year"], "{:+.3f}",
                      note=f"{_rc}: pace-free rebound share-edge trend per year")
            FACTS.set(f"{_rc}.reb_share_trend_mag", abs(_sm.params["year"]), "{:.3f}",
                      note=f"{_rc}: rebound share-edge trend magnitude per year")
            _slo, _shi = _ci_lo_hi(_sm, "year")
            FACTS.set(f"{_rc}.reb_share_trend_ci_lo", _slo, "{:+.3f}",
                      note=f"{_rc}: rebound share-edge trend 95% CI low (per year)")
            FACTS.set(f"{_rc}.reb_share_trend_ci_hi", _shi, "{:+.3f}",
                      note=f"{_rc}: rebound share-edge trend 95% CI high (per year)")
            _sp = _sm.pvalues["year"]
            FACTS.set(f"{_rc}.reb_share_p", "< 0.001" if _sp < 0.001 else f"= {_sp:.3f}",
                      note=f"{_rc}: rebound share-edge trend p-value (display)")
            print(f"   {_rc}: reb-share-edge trend/yr = {_sm.params['year']:+.3f}  "
                  f"95% CI [{_slo:+.3f}, {_shi:+.3f}]  (p = {_fmt_p(_sp)})")
        _e0r, _eNr = nba.ERA_DEFS[0], nba.ERA_DEFS[-1]
        _em = lambda era: float(_rsub[(_rsub["year"] >= era[1]) & (_rsub["year"] <= era[2])]["reb_share_edge"].mean())
        FACTS.set(f"{_rc}.reb_share_early", _em(_e0r), "{:+.2f}",
                  note=f"{_rc}: rebound share-edge, earliest era")
        FACTS.set(f"{_rc}.reb_share_today", _em(_eNr), "{:+.2f}",
                  note=f"{_rc}: rebound share-edge, recent era")

    for season_label, sub in [
        ("Regular season", df[df["is_playoff"] == 0]),
        ("Playoffs",       df[df["is_playoff"] == 1]),
    ]:
        print(f"   {season_label}  (N = {len(sub):,} games)\n")

        header = f"   {'Era':<12}" + "".join(f"{lbl:>{COL_W}}" for lbl in col_labels)
        divider = f"   {'─'*12}" + "─" * (COL_W * len(col_keys))
        print(header)
        print(divider)

        for era_label, y1, y2, _ in nba.ERA_DEFS:
            era_rows = sub[(sub["year"] >= y1) & (sub["year"] <= y2)]
            row = f"   {era_label:<12}"
            for key in col_keys:
                vals = era_rows[key].dropna()
                row += f"{vals.mean():>+{COL_W}.2f}" if len(vals) else f"{'—':>{COL_W}}"
            print(row)

        print(divider)
        trend_row = f"   {'Trend/yr':<12}"
        for key in col_keys:
            data = sub[["year", key]].dropna()
            if len(data) < 10:
                trend_row += f"{'—':>{COL_W}}"
                continue
            with suppress_noisy_fit_warnings():
                m = smf.ols(f"{key} ~ year", data=data).fit()
            cell = f"{m.params['year']:>+{COL_W - 3}.3f}{_stars(m.pvalues['year'])}"
            trend_row += cell
        print(trend_row)
        print()

    # ── Does the home edge track the league's retreat from offensive rebounding? ─
    from scipy.stats import pearsonr
    rs = df[df["is_playoff"] == 0]
    season = (rs.groupby("year")[["reb_share_edge", "league_oreb_rate"]]
                .mean().dropna())
    if len(season) >= 3:
        r, p = pearsonr(season["league_oreb_rate"], season["reb_share_edge"])
        FACTS.set("reb.league_oreb_corr", r, "{:+.2f}",
                  note="Reg: season-level correlation of rebound share-edge with the league OREB rate")
        first, last = season.iloc[0], season.iloc[-1]
        print("   Does the home edge track the league's retreat from the offensive glass?")
        print(f"   Season-level Pearson r (share edge vs league OREB rate) = "
              f"{r:+.3f}  (p = {_fmt_p(p)}  {_stars(p).strip()},  N = {len(season)} seasons)")
        print(f"   League OREB rate: {first['league_oreb_rate']:.1f}% → {last['league_oreb_rate']:.1f}%   "
              f"|   Home share edge: {first['reb_share_edge']:+.2f}pp → {last['reb_share_edge']:+.2f}pp")
        print("   ► The home rebounding edge fades in lockstep with the league-wide")
        print("     decline in offensive rebounding — the effort-driven offensive boards")
        print("     where a home edge could form have largely disappeared.")
        print()
        print("   ─ Cointegration check: is the OREB-HCA correlation genuine or spurious? ─")
        _run_cointegration(
            season["league_oreb_rate"].values,
            season["reb_share_edge"].values,
            "League OREB rate",
            "Home rebound share edge",
        )


def run_tracking_rebound_analysis(seasons: list, stats: dict) -> None:
    """Trend of each home-minus-road player-tracking rebounding edge over the
    tracking era — the mechanism behind the box-score rebounding fade.

    Covers only ~2014 on (box-outs ~2016 on), far shorter than the 40-year
    series, so these corroborate the modern mechanism rather than the full
    decline. Each edge = mean across teams of (home − road) per season.
    """
    _section("PLAYER-TRACKING REBOUNDING MECHANISM  (home minus road, tracking era)")
    print("   Confirms how the home rebounding edge expresses itself in the tracking")
    print("   data: offensive-rebound conversion, box-outs, and second-chance points.")
    print("   Window is short (~2014 on; box-outs ~2016 on) — corroborates the modern")
    print("   mechanism, not the 40-year decline.\n")

    rows = [
        ("oreb_chance_pct_edge", "OREB conversion edge (pp)"),
        ("boxout_edge",          "Box-out edge (per game)"),
        ("second_chance_edge",   "2nd-chance pts edge (per game)"),
    ]
    label_w = 30
    print(f"   {'Metric':<{label_w}}{'N seasons':>11}{'Mean':>10}{'Trend/yr':>12}{'p':>9}")
    print(f"   {'─'*label_w}{'─'*11}{'─'*10}{'─'*12}{'─'*9}")

    years = [nba.label_to_year(s) for s in seasons]
    for key, label in rows:
        y = np.array(stats.get(key, []), dtype=float)
        xy = pd.DataFrame({"year": years, "v": y}).dropna()
        if len(xy) < 3:
            print(f"   {label:<{label_w}}{len(xy):>11}{'—':>10}{'—':>12}{'—':>9}")
            continue
        with suppress_noisy_fit_warnings():
            m = smf.ols("v ~ year", data=xy).fit()
        coef, pval = m.params["year"], m.pvalues["year"]
        print(f"   {label:<{label_w}}{len(xy):>11}{xy['v'].mean():>+10.3f}"
              f"{coef:>+9.3f}{_stars(pval)}{_fmt_p(pval):>9}")

    # Guard for the prose (§3/Appendix B): the tracking offensive-rebound
    # conversion edge started above a point in the mid-2010s and is under 0.2 today.
    _oce = [v for v in stats.get("oreb_chance_pct_edge", []) if v == v]
    if len(_oce) >= 2:
        FACTS.guard("tracking_oreb_shrank", _oce[0] >= 1.0 and _oce[-1] < 0.3,
                    claim="the tracking offensive-rebound edge fell from ~1.2-1.3 in the mid-2010s to under 0.2 today",
                    value=f"{_oce[0]:.1f} -> {_oce[-1]:.1f}")
        FACTS.set("track.oreb_conv_edge", float(np.mean(_oce)), "{:+.2f}", unit="pp",
                  note="Mean home offensive-rebound conversion edge, tracking era")

    print()
    print("   ► The home edge is small and flat-to-declining across the tracking era —")
    print("     consistent with the offensive-glass advantage having largely collapsed")
    print("     before high-resolution tracking even began.")
    print()


def run_3pa_analysis(df: pd.DataFrame) -> None:
    """Season-level and game-level relationship between league-wide 3PA rate and home win %."""
    _section("LEAGUE-WIDE 3-POINT SHOOTING AND HOME COURT ADVANTAGE")
    print("   Does more 3-point shooting reduce home court advantage?")
    print("   Two angles: season-level correlation and game-level logistic regression.\n")
    _run_league_metric_analysis(
        df,
        col="tpa_rate_avg",
        agg_name="tpa_rate",
        metric_header="Mean 3PA%",
        metric_sep="% ",
        coef_desc="per pp of 3PA rate",
        scale_desc="10 pp rise in 3PA rate",
        era_coef_desc="per 10 pp 3PA",
        note_lines=[
            "   (If this is small and insignificant, 3PA effect is fully explained",
            "    by the secular trend — higher 3PA and lower HCA happen at the same",
            "    time but 3PA does not predict outcomes within any given era.)",
        ],
    )

    # ── Cointegration: is the 3PA-HCA season-level correlation genuine? ─────────
    reg = df[df["is_playoff"] == 0].dropna(subset=["tpa_rate_avg"])
    by_year = (
        reg.groupby("year")
           .agg(tpa_rate=("tpa_rate_avg", "mean"),
                home_pct=("home_win", lambda x: x.mean() * 100))
           .reset_index()
           .sort_values("year")
    )
    print("   ─ Cointegration check: is the 3PA-HCA correlation genuine or spurious? ─")
    _run_cointegration(
        by_year["tpa_rate"].values,
        by_year["home_pct"].values,
        "3PA rate (regular season)",
        "Home win %",
    )

    # ── Test 6: Partial correlation — detrend both series, check residual r ──────
    from numpy.linalg import lstsq as _lstsq
    print("   ─ Partial correlation: detrend both series, then correlate residuals ─")
    print("   Remove the year trend from both 3PA rate and home win %;")
    print("   if the residual r collapses, the raw r = -0.90 is a trend artifact.\n")
    yrs = by_year["year"].values.astype(float)
    x_c = yrs - yrs.mean()
    for _raw_col in ["tpa_rate", "home_pct"]:
        y_raw = by_year[_raw_col].values.astype(float)
        b = _lstsq(np.column_stack([np.ones(len(yrs)), x_c]), y_raw, rcond=None)[0]
        by_year[f"{_raw_col}_resid"] = y_raw - (b[0] + b[1] * x_c)

    r_raw   = float(np.corrcoef(by_year["tpa_rate"], by_year["home_pct"])[0, 1])
    r_resid = float(np.corrcoef(by_year["tpa_rate_resid"], by_year["home_pct_resid"])[0, 1])
    n_r     = len(by_year)
    t_stat  = r_resid * np.sqrt((n_r - 2) / (1 - r_resid**2)) if abs(r_resid) < 1 else np.inf
    from scipy import stats as _stats
    p_resid = float(2 * _stats.t.sf(abs(t_stat), df=n_r - 2))

    print(f"   Raw Pearson r (season level):        r = {r_raw:+.3f}")
    print(f"   Partial r (year-detrended residuals): r = {r_resid:+.3f}  p = {_fmt_p(p_resid)}  {_stars(p_resid)}")
    shrinkage = (abs(r_raw) - abs(r_resid)) / abs(r_raw) * 100 if r_raw != 0 else 0
    # Fact for the prose (§3/App C): how much of the 3PA-HCA correlation is just
    # the shared long-run drift (lost when the year trend is removed).
    FACTS.set("tpa.raw_corr", r_raw, "{:.2f}",
              note="Reg. raw season-level 3PA-vs-HCA Pearson correlation")
    FACTS.set("tpa.raw_corr_mag", abs(r_raw), "{:.3f}",
              note="Reg. raw 3PA-vs-HCA Pearson correlation magnitude")
    FACTS.set("tpa.partial_r_mag", abs(r_resid), "{:.3f}",
              note="Reg. year-detrended 3PA-vs-HCA partial correlation magnitude")
    FACTS.set("tpa.detrend_loss", shrinkage, "{:.0f}%",
              note="Reg. 3PA-HCA correlation strength lost after removing the shared year trend")
    if abs(r_resid) < 0.20:
        print(f"   ► Residual r collapsed to ~0 (raw: {r_raw:+.3f} → partial: {r_resid:+.3f}) —")
        print(f"     the raw correlation is entirely driven by the shared secular trend.\n")
    elif p_resid >= 0.05:
        print(f"   ► Residual r non-significant (raw: {r_raw:+.3f} → partial: {r_resid:+.3f},")
        print(f"     {shrinkage:.0f}% of raw r explained by shared trend). 3PA does not")
        print(f"     predict HCA within eras after removing the year trend.\n")
    elif shrinkage >= 30:
        print(f"   ► Residual r shrinks but remains significant (raw: {r_raw:+.3f} → partial:")
        print(f"     {r_resid:+.3f}; {shrinkage:.0f}% of raw r explained by shared trend).")
        print(f"     The 3PA-HCA relationship has a genuine component, but the shared")
        print(f"     40-year secular trend accounts for a large fraction of the raw r.\n")
    else:
        print(f"   ► Residual r remains similar (raw: {r_raw:+.3f} → partial: {r_resid:+.3f}) —")
        print(f"     the 3PA-HCA link is robust and not mainly trend-driven.\n")

    # ── Test 7: Rolling correlation — stability check ─────────────────────────────
    print("   ─ Rolling 10-season Pearson r: stability of the 3PA-HCA relationship ─")
    print("   Stable r → genuine relationship; large swings or sign flips → spurious.\n")
    window = 10
    rolling_r: list[tuple[int, float]] = []
    byyear = by_year.sort_values("year").reset_index(drop=True)
    for i in range(window - 1, len(byyear)):
        sub = byyear.iloc[i - window + 1 : i + 1]
        if len(sub) == window:
            r_w = float(np.corrcoef(sub["tpa_rate"], sub["home_pct"])[0, 1])
            rolling_r.append((int(sub["year"].iloc[-1]), r_w))

    if rolling_r:
        rs = [r for _, r in rolling_r]
        r_min = min(rs); r_max = max(rs)
        sign_flips = sum(
            1 for i in range(1, len(rs)) if rs[i] * rs[i - 1] < 0
        )
        peak_yr = rolling_r[rs.index(r_min)][0]  # year of most negative r
        print(f"   {window}-season rolling r range: [{r_min:+.3f}, {r_max:+.3f}]  "
              f"sign flips: {sign_flips}")
        print(f"   Most negative r = {r_min:+.3f} centered on season ending {peak_yr}")
        if sign_flips > 0:
            print(f"   ► Rolling r changes sign {sign_flips}x — correlation is UNSTABLE.")
            print(f"     This is the hallmark of a spurious trend-driven relationship.")
        elif r_max < -0.40 and r_min < -0.40:
            print(f"   ► Rolling r consistently negative — correlation appears stable;")
            print(f"     the 3PA-HCA link holds across sub-periods.")
        else:
            print(f"   ► Rolling r varies widely ({r_min:+.2f} to {r_max:+.2f}) — moderate")
            print(f"     instability suggests the relationship is partly trend-driven.")
    print()


def _run_granger_3pa(df: pd.DataFrame) -> None:
    """Granger causality: does lagged 3PA rate predict future HCA beyond HCA lags?

    If 3PA in year t-1 improves forecasts of home win % in year t, that is
    consistent with the three-point revolution *driving* the decline (not just
    co-trending with it). Tests run on first differences when both series are
    I(1), to satisfy the stationarity requirement of the Granger VAR test.
    N=43 seasons limits power; max 2 lags is used to preserve degrees of freedom.
    """
    from statsmodels.tsa.stattools import adfuller, grangercausalitytests

    _section("GRANGER CAUSALITY — DOES 3PA RATE LEAD HOME COURT ADVANTAGE?")
    print("   Granger causality: does 3PA rate in year t-1 improve forecasts of HCA in")
    print("   year t, beyond what past HCA values predict on their own?")
    print("   H0: 3PA lags add no predictive power for HCA (F-test via VAR).")
    print("   Both series differenced when I(1) to satisfy stationarity. Max 2 lags.\n")

    reg = df[df["is_playoff"] == 0].dropna(subset=["tpa_rate_avg"])
    by_year = (
        reg.groupby("year")
           .agg(tpa_rate=("tpa_rate_avg", "mean"),
                home_pct=("home_win", lambda x: x.mean() * 100))
           .reset_index()
           .sort_values("year")
    )
    if len(by_year) < 15:
        print("   Insufficient data (need ≥ 15 seasons).\n")
        return

    tpa = by_year["tpa_rate"].values
    hca = by_year["home_pct"].values

    adf_tpa = adfuller(tpa, maxlag=1, autolag=None)
    adf_hca = adfuller(hca, maxlag=1, autolag=None)
    i1_tpa = adf_tpa[1] >= 0.05
    i1_hca = adf_hca[1] >= 0.05

    if i1_tpa and i1_hca:
        data_arr = np.column_stack([np.diff(hca), np.diff(tpa)])
        diff_note = "first-differenced (both I(1))"
    else:
        data_arr = np.column_stack([hca, tpa])
        diff_note = "levels"

    print(f"   Testing in {diff_note}  (N = {len(data_arr)} observations)\n")
    # Fact for stats_explainer.md §11 (Granger).
    FACTS.set("granger.n", len(data_arr), "{:d}", note="Granger test: differenced observations")

    lead_ps: list[float] = []
    for direction, d_arr, y_lbl, x_lbl in [
        ("3PA rate → HCA (does 3PA lead the decline?)",
         data_arr,
         "Δ Home win %", "Δ 3PA rate"),
        ("HCA → 3PA rate (reverse: does HCA drive 3PA adoption?)",
         data_arr[:, ::-1],
         "Δ 3PA rate", "Δ Home win %"),
    ]:
        print(f"   {direction}")
        print(f"   {'Lag':>4}  {'F-stat':>8}  {'p-value':>10}  {'Verdict':>28}")
        print(f"   {'─'*4}  {'─'*8}  {'─'*10}  {'─'*28}")
        try:
            with suppress_noisy_fit_warnings():
                gc_res = grangercausalitytests(d_arr, maxlag=2, verbose=False)
            for lag in [1, 2]:
                F = gc_res[lag][0]["ssr_ftest"][0]
                p = gc_res[lag][0]["ssr_ftest"][1]
                verdict = "leads" if p < 0.05 else "no Granger effect"
                if x_lbl == "Δ 3PA rate":
                    lead_ps.append(float(p))
                print(f"   {lag:>4}  {F:>8.3f}  {_fmt_p(p):>10}  {verdict:>28}  {_stars(p).strip()}")
        except Exception as exc:
            print(f"   Test failed: {exc}")
        print()

    if lead_ps:
        FACTS.guard("granger_no_lead", all(p >= 0.05 for p in lead_ps),
                    claim="a season's three-point rate does not predict the next season's home court beyond home court's own past",
                    value="3PA→HCA Granger p = " + ", ".join(f"{p:.2f}" for p in lead_ps))


def run_pace_analysis(df: pd.DataFrame) -> None:
    """Season-level and game-level relationship between pace and home win %."""
    _section("PACE AND HOME COURT ADVANTAGE")
    print("   Does faster-paced play (more possessions per game) reduce home court advantage?")
    print("   Season-level correlation plus game-level logistic regression.\n")

    def _expected_pace_block(df: pd.DataFrame, is_po: int) -> None:
        sub_ep = df[df["is_playoff"] == is_po].dropna(subset=["expected_pace"])
        if not sub_ep.empty:
            p_bar_ep = sub_ep["home_win"].mean()
            print(f"\n   Expected pace (LOO)  (N = {len(sub_ep):,} games)")
            try:
                with suppress_noisy_fit_warnings():
                    m_biv_ep = smf.logit("home_win ~ expected_pace", data=sub_ep).fit(
                        disp=0, cov_type="cluster", cov_kwds={"groups": sub_ep["year"].values},
                    )
                    _warn_if_not_converged(m_biv_ep, "_expected_pace_block: m_biv_ep")
                c_ep = m_biv_ep.params["expected_pace"]
                p_ep = m_biv_ep.pvalues["expected_pace"]
                print(f"   Bivariate: coef = {c_ep:+.4f}  "
                      f"(≈ {_pp(c_ep, p_bar_ep) * 10:+.2f} pp per 10 poss)  "
                      f"p = {_fmt_p(p_ep)}  {_stars(p_ep).strip()}")
                if is_po == 0:  # facts for stats_explainer.md §20 (expected pace)
                    FACTS.set("pace.expected_biv", _pp(c_ep, p_bar_ep) * 10, "{:+.1f}",
                              note="Reg: expected-pace bivariate HCA effect per 10 poss")
                    FACTS.set("pace.expected_p", p_ep, "{:.3f}", note="Reg: expected-pace bivariate p")
            except Exception:
                pass
            try:
                with suppress_noisy_fit_warnings():
                    m_era_ep = smf.logit(
                        "home_win ~ expected_pace + C(era)", data=sub_ep
                    ).fit(
                        disp=0, cov_type="cluster", cov_kwds={"groups": sub_ep["year"].values},
                    )
                    _warn_if_not_converged(m_era_ep, "_expected_pace_block: m_era_ep")
                c_era_ep = m_era_ep.params["expected_pace"]
                p_era_ep = m_era_ep.pvalues["expected_pace"]
                pp_era_ep = _pp(c_era_ep, p_bar_ep) * 10
                print(f"   Within-era: coef = {c_era_ep:+.4f}  "
                      f"(≈ {pp_era_ep:+.2f} pp per 10 poss)  "
                      f"p = {_fmt_p(p_era_ep)}  {_stars(p_era_ep).strip()}")
                if is_po == 0:
                    FACTS.set("pace.expected_era_p",
                              "< 0.001" if p_era_ep < 0.001 else f"= {p_era_ep:.3f}",
                              note="Reg: within-era expected-pace bivariate p (display)")
            except Exception:
                pass

    _run_league_metric_analysis(
        df,
        col="pace_avg",
        agg_name="pace",
        metric_header="Mean pace",
        metric_sep="  ",
        coef_desc="per possession",
        scale_desc="10 extra possessions",
        era_coef_desc="per 10 possessions",
        extra_block=_expected_pace_block,
    )


def run_travel_analysis(df: pd.DataFrame) -> None:
    """Bivariate table: does haversine travel distance predict home win?"""
    full = df.dropna(subset=["distance_miles"])
    if full.empty:
        _section("TRAVEL DISTANCE — AWAY TEAM FLIGHT MILES")
        print("   No distance data available in this dataset.")
        return

    _section("TRAVEL DISTANCE — HOME WIN % BY AWAY TEAM FLIGHT MILES")
    print("   Distance = haversine miles from away team's home arena to game arena.")
    print("   Does longer travel reduce the visiting team's winning odds?\n")

    buckets = [("0–500", 0, 500), ("500–1000", 500, 1000),
               ("1000–1500", 1000, 1500), ("1500+", 1500, np.inf)]

    for context_label, sub in [("Regular season", full[full["is_playoff"] == 0]),
                                ("Playoffs",       full[full["is_playoff"] == 1])]:
        if sub.empty:
            continue
        p_bar = sub["home_win"].mean()
        print(f"   {context_label}  (N = {len(sub):,}, baseline home win % = {p_bar*100:.1f}%)\n")
        print(f"   {'Bucket':>12}  {'N':>8}  {'Home win %':>11}  {'vs. baseline':>13}")
        print(f"   {'─'*12}  {'─'*8}  {'─'*11}  {'─'*13}")

        for label, lo, hi in buckets:
            bsub = sub[(sub["distance_miles"] >= lo) & (sub["distance_miles"] < hi)]
            if bsub.empty:
                continue
            bpct = 100.0 * bsub["home_win"].mean()
            diff = bpct - p_bar * 100
            print(f"   {label:>12}  {len(bsub):>8,}  {bpct:>10.1f}%  {diff:>+12.1f} pp")

        with suppress_noisy_fit_warnings():
            try:
                m = smf.logit("home_win ~ distance_miles", data=sub).fit(
                    disp=0, cov_type="cluster", cov_kwds={"groups": sub["year"].values},
                )
                _warn_if_not_converged(m, "run_travel_analysis: m")
                coef = m.params["distance_miles"]
                pval = m.pvalues["distance_miles"]
                pval_s = _fmt_p(pval)
                pp_per_100mi = _pp(coef, p_bar) * 100
                ci_lo, ci_hi = _ci_lo_hi(m, "distance_miles", p_bar)
                print(f"\n   Bivariate logistic: coef = {coef:+.5f} log-odds/mi  "
                      f"(≈{pp_per_100mi:+.2f} pp per 100 mi,  "
                      f"95% CI [{ci_lo*100:+.2f}, {ci_hi*100:+.2f}]),  "
                      f"p = {pval_s}  {_stars(pval).strip()}")
                _tvc = "po" if context_label == "Playoffs" else "reg"
                if context_label == "Regular season":
                    # Fact for the prose (§4): travel's negligible regular-season effect.
                    FACTS.set("travel.per_100mi", abs(pp_per_100mi), "{:.2f}",
                              note="Reg. home win % effect per 100 miles of visitor travel (pp)")
                # Statistical detail for investigation.md: the travel-effect 95% CI.
                FACTS.set(f"travel.{_tvc}_ci_lo", ci_lo * 100, "{:+.2f}",
                          note=f"{context_label}: travel effect 95% CI low (pp/100mi)")
                FACTS.set(f"travel.{_tvc}_ci_hi", ci_hi * 100, "{:+.2f}",
                          note=f"{context_label}: travel effect 95% CI high (pp/100mi)")
            except Exception:
                pass
        print()


def compute_back_to_back_plotdata(df: pd.DataFrame) -> dict:
    """Chart-ready 'load management' decomposition: visitor back-to-back rate by
    era, and the shift-share split of the regular-season home win % decline into
    a schedule (frequency) component and a within-situation (win-rate) component.
    Same numbers run_back_to_back_analysis prints.
    """
    rs = df[df["is_playoff"] == 0].dropna(subset=["away_b2b", "home_b2b"]).copy()
    order = ["neither_b2b", "vis_b2b_only", "home_b2b_only", "both_b2b"]

    def _situ(r):
        if r["away_b2b"] and r["home_b2b"]:
            return "both_b2b"
        if r["away_b2b"]:
            return "vis_b2b_only"
        if r["home_b2b"]:
            return "home_b2b_only"
        return "neither_b2b"

    rs["situ"] = rs.apply(_situ, axis=1)

    eras, vis_b2b = [], []
    for era_label, y1, y2, _ in nba.ERA_DEFS:
        e = rs[(rs["year"] >= y1) & (rs["year"] <= y2)]
        if e.empty:
            continue
        eras.append(era_label)
        vis_b2b.append(100.0 * e["away_b2b"].mean())

    def _cells(sub):
        c = sub.groupby("situ")["home_win"].agg(["count", "mean"]).reindex(order).fillna(0)
        c["freq"] = c["count"] / c["count"].sum()
        return c

    _, fy1, fy2, _ = nba.ERA_DEFS[0]
    _, ly1, ly2, _ = nba.ERA_DEFS[-1]
    cf = _cells(rs[(rs["year"] >= fy1) & (rs["year"] <= fy2)])
    cl = _cells(rs[(rs["year"] >= ly1) & (rs["year"] <= ly2)])
    total = (float((cl["freq"] * cl["mean"]).sum()) - float((cf["freq"] * cf["mean"]).sum())) * 100
    freq_comp = float(((cl["freq"] - cf["freq"]) * cf["mean"]).sum()) * 100
    rate_comp = float((cf["freq"] * (cl["mean"] - cf["mean"])).sum()) * 100
    return {
        "eras": eras, "vis_b2b": vis_b2b,
        "total": total, "freq_comp": freq_comp, "rate_comp": rate_comp,
        "freq_share": 100.0 * freq_comp / total if total else float("nan"),
        "rate_share": 100.0 * rate_comp / total if total else float("nan"),
    }


def run_back_to_back_analysis(df: pd.DataFrame) -> None:
    """Did the league-wide drop in back-to-backs drive the HCA decline?
    Tests the 'load management' story: visitor B2Bs have fallen, but how much
    of the decline does that schedule shift explain? Shift-share decomposition
    splits the change into a frequency part (fewer tired teams) and a win-rate
    part (the per-situation home edge eroding)."""
    _section("BACK-TO-BACKS — DID FEWER TIRED VISITORS DRIVE THE DECLINE?")
    print("   A back-to-back (B2B) is a game on zero days' rest. The 'load")
    print("   management' story: visitor B2Bs have grown rarer, so home teams")
    print("   face fewer tired opponents. Regular season only (B2Bs are rare")
    print("   in the playoffs). Games without a known prior game are excluded.\n")

    rs = df[df["is_playoff"] == 0].dropna(subset=["away_b2b", "home_b2b"]).copy()
    if rs.empty:
        print("   No usable rest data.\n")
        return

    def situ(row):
        if row["away_b2b"] and row["home_b2b"]:
            return "both_b2b"
        if row["away_b2b"]:
            return "vis_b2b_only"
        if row["home_b2b"]:
            return "home_b2b_only"
        return "neither_b2b"

    rs["situ"] = rs.apply(situ, axis=1)

    # ── Frequency of each rest situation, by era ───────────────────────────────
    print("   Visitor and home B2B frequency by era:")
    print(f"   {'Era':<12}  {'N':>7}  {'Visitor B2B':>11}  {'Home B2B':>9}  {'Home win %':>11}")
    print(f"   {'─'*12}  {'─'*7}  {'─'*11}  {'─'*9}  {'─'*11}")
    for era_label, y1, y2, _ in nba.ERA_DEFS:
        e = rs[(rs["year"] >= y1) & (rs["year"] <= y2)]
        if e.empty:
            continue
        print(f"   {era_label:<12}  {len(e):>7,}  {100*e['away_b2b'].mean():>10.1f}%  "
              f"{100*e['home_b2b'].mean():>8.1f}%  {100*e['home_win'].mean():>10.1f}%")

    # ── Home win % by rest situation (pooled) ──────────────────────────────────
    print(f"\n   Home win % by rest situation (all seasons pooled):")
    print(f"   {'Situation':<16}  {'N games':>8}  {'Home win %':>11}")
    print(f"   {'─'*16}  {'─'*8}  {'─'*11}")
    labels = {"neither_b2b": "Neither on B2B", "vis_b2b_only": "Visitor B2B only",
              "home_b2b_only": "Home B2B only", "both_b2b": "Both on B2B"}
    order = ["neither_b2b", "vis_b2b_only", "home_b2b_only", "both_b2b"]
    _situ_pct = {}
    for s in order:
        b = rs[rs["situ"] == s]
        if not b.empty:
            _situ_pct[s] = 100 * b["home_win"].mean()
            print(f"   {labels[s]:<16}  {len(b):>8,}  {100*b['home_win'].mean():>10.1f}%")
    # Statistical detail for investigation.md: tired-visitor vs baseline home win %.
    if "neither_b2b" in _situ_pct:
        FACTS.set("b2b.baseline", _situ_pct["neither_b2b"], "{:.0f}%",
                  note="Home win % with neither team on a back-to-back")
    if "vis_b2b_only" in _situ_pct:
        FACTS.set("b2b.tired_visitor", _situ_pct["vis_b2b_only"], "{:.0f}%",
                  note="Home win % with only the visitor on a back-to-back")

    # ── Shift-share: first era vs last era ─────────────────────────────────────
    first_lbl, fy1, fy2, _ = nba.ERA_DEFS[0]
    last_lbl,  ly1, ly2, _ = nba.ERA_DEFS[-1]

    def cells(sub):
        c = sub.groupby("situ")["home_win"].agg(["count", "mean"]).reindex(order).fillna(0)
        c["freq"] = c["count"] / c["count"].sum()
        return c

    cf = cells(rs[(rs["year"] >= fy1) & (rs["year"] <= fy2)])
    cl = cells(rs[(rs["year"] >= ly1) & (rs["year"] <= ly2)])
    hca_f = float((cf["freq"] * cf["mean"]).sum()) * 100
    hca_l = float((cl["freq"] * cl["mean"]).sum()) * 100
    total = hca_l - hca_f
    freq_comp = float(((cl["freq"] - cf["freq"]) * cf["mean"]).sum()) * 100
    rate_comp = float((cf["freq"] * (cl["mean"] - cf["mean"])).sum()) * 100
    inter = total - freq_comp - rate_comp
    share = 100 * freq_comp / total if total else float("nan")
    # Facts for the prose (§4/§6/App C): visitor back-to-backs grew rarer, but
    # that schedule change explains only a small share of the decline.
    FACTS.set("b2b.freq_share", abs(share), "{:.0f}%",
              note="Fewer visitor back-to-backs: share of the regular-season decline")
    FACTS.set("b2b.freq_pp", abs(freq_comp), "{:.1f}",
              note="Fewer visitor back-to-backs: absolute pp of the decline they explain")
    _e0b, _eNb = nba.ERA_DEFS[0], nba.ERA_DEFS[-1]
    FACTS.set("b2b.freq_early",
              100 * rs[(rs["year"] >= _e0b[1]) & (rs["year"] <= _e0b[2])]["away_b2b"].mean(),
              "{:.0f}%", note="Visitor back-to-back frequency, earliest era")
    FACTS.set("b2b.freq_late_plain", "under 20%",
              note=f"Visitor B2B frequency today (~{100 * rs[(rs['year'] >= _eNb[1]) & (rs['year'] <= _eNb[2])]['away_b2b'].mean():.0f}%)")

    print(f"\n   Shift-share decomposition of the home win % change, "
          f"{first_lbl} → {last_lbl}:")
    print(f"   Home win %: {hca_f:.1f}% → {hca_l:.1f}%   (total change {total:+.2f} pp)")
    print(f"   {'Frequency component (schedule: fewer B2Bs)':<46}  {freq_comp:>+7.2f} pp  ({share:>4.0f}% of change)")
    print(f"   {'Win-rate component (per-situation edge fading)':<46}  {rate_comp:>+7.2f} pp")
    print(f"   {'Interaction':<46}  {inter:>+7.2f} pp")
    print(f"\n   ► Visitor B2Bs have grown much rarer, which does nudge home court")
    print(f"     downward — but the win-rate gap between rested and tired matchups is")
    print(f"     small, so the schedule shift explains only ~{abs(share):.0f}% of the decline.")
    print(f"     The other ~{abs(100-share):.0f}% is the home edge within each rest situation")
    print(f"     fading — not a scheduling story.\n")


def run_attendance_analysis(
    att_seasons: list[str], att_avg: list[float],
    reg_seasons: list[str], reg_pcts: list[float],
    dose_df: pd.DataFrame,
) -> None:
    """Two questions: does crowd *size* track HCA across seasons (ruled-out
    factor), and what is one fan worth (2020-21 dose-response)?"""
    from scipy import stats as scipy_stats

    _section("ARENA ATTENDANCE AND HOME COURT ADVANTAGE")
    print("   Source: Basketball-Reference per-game attendance (~2000 onward).")
    print("   Part A: does league attendance track home win % across seasons?")
    print("   Part B: 2020-21 dose-response — crowd size varied by local rule.\n")

    # ── Part A: season-level crowd size vs. home win % ─────────────────────────
    att_map = dict(zip(att_seasons, att_avg))
    shared = [s for s in reg_seasons if s in att_map]
    if len(shared) < 5:
        print("   Insufficient attendance data for season-trend correlation.\n")
    else:
        att_vals  = np.array([att_map[s] for s in shared], dtype=float)
        home_vals = np.array([reg_pcts[reg_seasons.index(s)] for s in shared])

        r_p, p_p = scipy_stats.pearsonr(att_vals, home_vals)
        r_s, p_s = scipy_stats.spearmanr(att_vals, home_vals)
        print(f"   N = {len(shared)} seasons "
              f"(avg crowd {int(att_vals.min()):,}–{int(att_vals.max()):,}/game)")
        print(f"   Pearson r  = {r_p:+.3f}  (p = {_fmt_p(p_p)}  {_stars(p_p).strip()})")
        print(f"   Spearman ρ = {r_s:+.3f}  (p = {_fmt_p(p_s)}  {_stars(p_s).strip()})\n")

        # Detrended checks — both series can share a long-run drift.
        years = np.array([nba.label_to_year(s) for s in shared])
        order = np.argsort(years)
        y, a, h = years[order], att_vals[order], home_vals[order]
        d_a, d_h = np.diff(a), np.diff(h)
        r_fd, p_fd = scipy_stats.pearsonr(d_a, d_h)
        from scipy.stats import linregress
        sl_a, ic_a, *_ = linregress(y, a)
        sl_h, ic_h, *_ = linregress(y, h)
        r_rd, p_rd = scipy_stats.pearsonr(a - (sl_a * y + ic_a), h - (sl_h * y + ic_h))
        print(f"   Detrended (remove shared drift):")
        print(f"   First-differenced  r = {r_fd:+.3f}  (p = {_fmt_p(p_fd)}  {_stars(p_fd).strip()})"
              f"  N = {len(d_a)} year-pairs")
        print(f"   Residual-on-year   r = {r_rd:+.3f}  (p = {_fmt_p(p_rd)}  {_stars(p_rd).strip()})"
              f"  N = {len(shared)} seasons")

        print()
        print("   ─ Cointegration check: is the attendance-HCA correlation genuine? ─")
        _run_cointegration(att_vals, home_vals, "League avg attendance", "Home win %")

        if (abs(r_p) < 0.15 or p_p >= 0.05) and p_fd >= 0.05 and p_rd >= 0.05:
            print(f"\n   ► Crowd *size* does not track home court advantage. Attendance has")
            print(f"     held near arena capacity for 25 years while HCA fell — the level is")
            print(f"     flat where the advantage is not. Crowd size is not behind the decline.")
        elif r_p > 0:
            print(f"\n   ► Positive association, but see Part B: it is the *presence* of a crowd,")
            print(f"     not its size, that moves the needle — and size has barely changed.")
        else:
            print(f"\n   ► Negative association — counter to the crowd-size hypothesis.")

    # ── Part B: 2020-21 empty-arena dose-response ──────────────────────────────
    print()
    if dose_df.empty or dose_df["home_win"].nunique() < 2:
        print("   No usable 2020-21 attendance data for the dose-response.\n")
        return

    empty = dose_df[dose_df["attendance"] == 0]
    crowd = dose_df[dose_df["attendance"] > 0]
    p_bar = float(dose_df["home_win"].mean())
    # Facts for the prose (§2.1/§3): empty 2020-21 arenas dropped home teams to
    # ~51%; any crowd at all restored ~58%.
    FACTS.set("crowd.empty", 100 * float(empty["home_win"].mean()), "{:.0f}%",
              note="2020-21 home win % with empty arenas")
    FACTS.set("crowd.fans", 100 * float(crowd["home_win"].mean()), "{:.0f}%",
              note="2020-21 home win % with fans present")
    FACTS.set("crowd.fans_plain", "58%", note="prose rounding of crowd.fans (58.5%)")
    # Appendix C compares against the blog using one-decimal precision.
    FACTS.set("crowd.empty_precise", 100 * float(empty["home_win"].mean()), "{:.1f}%",
              note="2020-21 empty-arena home win % (one decimal)")
    FACTS.set("crowd.fans_precise", 100 * float(crowd["home_win"].mean()), "{:.1f}%",
              note="2020-21 fans-present home win % (one decimal)")
    FACTS.set("crowd.fans_median", float(crowd["attendance"].median()), "{:,.0f}",
              note="2020-21 median attendance among fans-present games")
    print(f"   2020-21 home win %:  empty arena {100*empty['home_win'].mean():.1f}% "
          f"(n={len(empty)})  vs.  fans present {100*crowd['home_win'].mean():.1f}% "
          f"(n={len(crowd)}, median attendance {crowd['attendance'].median():.0f})")

    d = dose_df.copy()
    d["att_k"] = d["attendance"] / 1000.0  # coefficient = effect per 1,000 fans
    with suppress_noisy_fit_warnings():
        m = smf.logit("home_win ~ att_k", data=d).fit(disp=0)
        _warn_if_not_converged(m, "run_attendance_analysis: m")
    coef, pval = m.params["att_k"], m.pvalues["att_k"]
    pp = _pp(coef, p_bar)
    lo, hi = _ci_lo_hi(m, "att_k", p_bar)
    print(f"   Logit home_win ~ attendance (per 1,000 fans):")
    print(f"   Effect: {pp:+.2f} pp per 1,000 fans  [95% CI {lo:+.2f}, {hi:+.2f}]"
          f"  (p = {_fmt_p(pval)}  {_stars(pval).strip()})")

    if pval < 0.05 and coef > 0:
        print(f"\n   ► A direct measure of the crowd. With arenas empty, home court nearly")
        print(f"     vanished ({100*empty['home_win'].mean():.0f}%); letting fans back in")
        print(f"     restored it. The crowd is a real ingredient — but a 2020-21 swing that")
        print(f"     reversed when fans returned, not part of the four-decade slide.")
    else:
        print(f"\n   ► No significant within-season attendance effect detected.")


def run_parity_correlation(
    parity_seasons: list[str], parity_std: list[float],
    reg_seasons: list[str], reg_pcts: list[float],
) -> None:
    from scipy import stats as scipy_stats

    _section("COMPETITIVE BALANCE AND HOME COURT ADVANTAGE")
    print("   Hypothesis: more parity (lower team win% std dev) → lower home court advantage.")
    print("   Parity = std dev of all-team win percentages for the season.\n")

    parity_map = dict(zip(parity_seasons, parity_std))
    shared = [s for s in reg_seasons if s in parity_map]
    if len(shared) < 5:
        print("   Insufficient data for correlation analysis.")
        return

    std_vals  = np.array([parity_map[s] for s in shared])
    home_vals = np.array([reg_pcts[reg_seasons.index(s)] for s in shared])

    r_p, p_p = scipy_stats.pearsonr(std_vals, home_vals)
    r_s, p_s = scipy_stats.spearmanr(std_vals, home_vals)

    print(f"   N = {len(shared)} seasons")
    print(f"   Pearson r  = {r_p:+.3f}  (p = {_fmt_p(p_p)}"
          f"  {_stars(p_p).strip()})")
    print(f"   Spearman ρ = {r_s:+.3f}  (p = {_fmt_p(p_s)}"
          f"  {_stars(p_s).strip()})\n")

    data = pd.DataFrame({"parity_std": std_vals, "home_pct": home_vals})
    with suppress_noisy_fit_warnings():
        m = smf.ols("home_pct ~ parity_std", data=data).fit()
    coef = m.params["parity_std"]
    pval = m.pvalues["parity_std"]
    pval_s = _fmt_p(pval)
    print(f"   Trend line: home_win_pct ~ parity_std_dev")
    print(f"   Slope: {coef:+.3f} pp per unit std dev  (p = {pval_s}  {_stars(pval).strip()})")
    print(f"   R² = {m.rsquared:.4f}\n")

    print(f"   Era-bucketed averages (disparity ↓ = more parity, home win % ↓ = less advantage):\n")
    print(f"   {'Era':<12}  {'Win% std dev':>14}  {'Home win %':>12}")
    print(f"   {'─'*12}  {'─'*14}  {'─'*12}")
    for era_label, y1, y2, _ in nba.ERA_DEFS:
        era_seasons = [s for s in shared if y1 <= nba.label_to_year(s) <= y2]
        if not era_seasons:
            print(f"   {era_label:<12}  {'—':>14}  {'—':>12}")
            continue
        era_std  = float(np.mean([parity_map[s] for s in era_seasons]))
        era_home = float(np.mean([reg_pcts[reg_seasons.index(s)] for s in era_seasons]))
        print(f"   {era_label:<12}  {era_std:>14.4f}  {era_home:>11.1f}%")

    if abs(r_p) < 0.15 or pval >= 0.05:
        print(f"\n   ► Near-zero, non-significant correlation — parity (team win% disparity)")
        print(f"     does not independently predict home court advantage across seasons.")
        print(f"     The era-bucketed pattern is mixed: disparity peaked in 1995–01 while")
        print(f"     home win % was already declining, and fell in 2002–04 while home win %")
        print(f"     ticked back up. The two series do not move in lockstep.")
    elif r_p > 0:
        print(f"\n   ► Positive r: higher disparity ↔ higher home advantage — weaker road")
        print(f"     teams lose more away from home when the talent gap is larger.")
        print(f"   ► But both series share a downward trend; era is a dominant confound.")
    else:
        print(f"\n   ► Negative r: more disparity ↔ lower home advantage — counter to the")
        print(f"     parity hypothesis. Effect is significant but era is a dominant confound.")

    # ── Cointegration check: are parity and HCA genuinely linked? ─────────────
    print()
    print("   ─ Cointegration check: is the parity-HCA correlation genuine or spurious? ─")
    _run_cointegration(std_vals, home_vals, "League parity (win% std dev)", "Home win %")

    # ── Detrended checks — remove spurious cross-trend correlation ─────────────
    years_arr = np.array([nba.label_to_year(s) for s in shared])
    sort_idx = np.argsort(years_arr)
    years_sorted = years_arr[sort_idx]
    std_sorted   = std_vals[sort_idx]
    home_sorted  = home_vals[sort_idx]

    # First-differenced: year-to-year changes
    d_std  = np.diff(std_sorted)
    d_home = np.diff(home_sorted)
    r_fd, p_fd = scipy_stats.pearsonr(d_std, d_home)
    print(f"\n   Detrended checks (both series share a downward trend — remove it first):")
    print(f"   First-differenced (Δparity vs. Δhome-win%):")
    print(f"   Pearson r = {r_fd:+.3f}  (p = {_fmt_p(p_fd)}  {_stars(p_fd).strip()})  "
          f"N = {len(d_std)} year-pairs")

    # Residual-on-year: detrend each series independently then correlate
    from scipy.stats import linregress
    sl_s, ic_s, *_ = linregress(years_sorted, std_sorted)
    sl_h, ic_h, *_ = linregress(years_sorted, home_sorted)
    res_std  = std_sorted  - (sl_s * years_sorted + ic_s)
    res_home = home_sorted - (sl_h * years_sorted + ic_h)
    r_rd, p_rd = scipy_stats.pearsonr(res_std, res_home)
    print(f"   Residual-on-year (detrended parity vs. detrended home-win%):")
    print(f"   Pearson r = {r_rd:+.3f}  (p = {_fmt_p(p_rd)}  {_stars(p_rd).strip()})  "
          f"N = {len(shared)} seasons")

    if p_fd >= 0.05 and p_rd >= 0.05:
        print(f"\n   ► Both detrended tests are non-significant — the raw correlation is")
        print(f"     driven by the shared downward trend, not a causal link.")
        print(f"     Year-to-year changes in parity do not predict year-to-year changes")
        print(f"     in home court advantage.")
    elif p_fd < 0.05 or p_rd < 0.05:
        print(f"\n   ► At least one detrended test is significant — some association")
        print(f"     remains after removing the common trend. Interpret with caution")
        print(f"     (N is small and first-differences amplify measurement noise).")
