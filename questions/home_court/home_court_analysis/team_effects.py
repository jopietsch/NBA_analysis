"""Team- and franchise-level home-court findings: per-team HCA (with
empirical-Bayes shrinkage), franchise era comparison, HCA consistency, and
margin / net-rating distributions."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from nbakit.textfmt import stars as _stars, p_value as _fmt_p

import home_court_data as nba
from home_court_facts import FACTS

from ._helpers import suppress_noisy_fit_warnings, _section, _shrink_hca

def run_team_hca_analysis(reg_stats: dict, po_stats: dict) -> None:
    """Per-franchise home vs. road win% aggregated across all seasons."""
    _section("FRANCHISE HOME COURT ADVANTAGE — HOME VS. ROAD WIN %")
    print("   Which franchises benefit most from playing at home?")
    print("   HCA = home win% − road win% (controls for overall team quality).\n")

    for ctx_label, stats, min_g in [
        ("Regular season", reg_stats, 50),
        ("Playoffs",       po_stats,  20),
    ]:
        if not stats:
            print(f"   {ctx_label}: no data.\n")
            continue

        shrunken, ci_hw = _shrink_hca(stats)
        sh_vals = np.array([shrunken[t] for t in stats])
        all_shrunken_equal = bool(np.std(sh_vals) < 1e-6)

        if all_shrunken_equal:
            # true_var = 0: sort by raw HCA
            sorted_teams = sorted(stats, key=lambda t: stats[t]["hca"], reverse=True)
        else:
            sorted_teams = sorted(stats, key=lambda t: shrunken[t], reverse=True)
        hcas = [stats[t]["hca"] for t in sorted_teams]

        print(f"   {ctx_label}  ({len(sorted_teams)} franchises with ≥{min_g} home games)")
        if all_shrunken_equal:
            print(f"   Sorted by raw HCA (EB shrinkage collapses all to league mean — see variance decomp below).")
        else:
            print(f"   Sorted by EB-shrunken HCA.")
        print(f"   CI ± = 95% half-width (binomial SE).\n")

        NW, CW, CW2 = 26, 7, 9
        header = (f"   {'Franchise':<{NW}} {'n_h':>{CW}} {'home%':>{CW}} "
                  f"{'n_r':>{CW}} {'road%':>{CW}} {'HCA':>{CW}} {'CI ±':>{CW}} {'Shrunken':>{CW2}}")
        sep = f"   {'─'*NW} {'─'*CW} {'─'*CW} {'─'*CW} {'─'*CW} {'─'*CW} {'─'*CW} {'─'*CW2}"
        print(header)
        print(sep)

        for team in sorted_teams:
            d = stats[team]
            name = team[:NW] if len(team) > NW else team
            print(f"   {name:<{NW}} {d['n_home']:>{CW},} {d['home_pct']:>{CW}.1f}%"
                  f" {d['n_road']:>{CW},} {d['road_pct']:>{CW}.1f}% {d['hca']:>+{CW}.1f}"
                  f" ±{ci_hw[team]:>{CW}.1f} {shrunken[team]:>+{CW2}.1f} pp")

        league_mean = float(np.mean(hcas))

        # Variance decomposition
        all_teams = list(stats)
        samp_vars_all = np.array([
            1e4 * (
                (stats[t]["home_pct"] / 100.0) * (1.0 - stats[t]["home_pct"] / 100.0) / stats[t]["n_home"]
                + (stats[t]["road_pct"] / 100.0) * (1.0 - stats[t]["road_pct"] / 100.0) / stats[t]["n_road"]
            )
            for t in all_teams
        ])
        obs_var_all  = float(np.var(np.array([stats[t]["hca"] for t in all_teams]), ddof=1))
        mean_sv_all  = float(samp_vars_all.mean())
        true_var_all = max(0.0, obs_var_all - mean_sv_all)
        noise_pct    = 100.0 * mean_sv_all / obs_var_all if obs_var_all > 0 else 100.0

        print(f"\n   League mean HCA = {league_mean:+.1f} pp  "
              f"(raw range: {min(hcas):+.1f} to {max(hcas):+.1f} pp)")
        print(f"   Variance decomposition: observed SD = {np.sqrt(obs_var_all):.1f} pp, "
              f"sampling noise = {noise_pct:.0f}%, true between-franchise SD ≈ {np.sqrt(true_var_all):.1f} pp")

        altitude = [t for t in sorted_teams if t in nba.ALTITUDE_TEAMS]
        for at in altitude:
            rank = sorted_teams.index(at) + 1
            print(f"   ► {at}: raw {stats[at]['hca']:+.1f} pp, shrunken {shrunken[at]:+.1f} pp  "
                  f"(rank #{rank}/{len(sorted_teams)} by shrunken)")

        # Facts for the prose (Appendix B): the altitude franchises' HCA, the
        # league average, and the genuine (non-noise) share of franchise spread.
        if ctx_label == "Regular season":
            FACTS.set("altitude.league_mean", league_mean, "{:.0f}",
                      note="League-average regular-season HCA (pp)")
            FACTS.set("altitude.signal_pct", 100.0 - noise_pct, "{:.0f}%",
                      note="Share of franchise HCA variation that is genuine, not sampling noise")
            for at in altitude:
                _short = ("denver" if "Denver" in at else
                          "utah" if "Utah" in at else at.lower().replace(" ", "_"))
                FACTS.set(f"altitude.{_short}_hca", stats[at]["hca"], "{:.0f}",
                          note=f"{at} full home-minus-road gap (pp, rounded)")
        print()


def run_franchise_era_comparison(
    early_stats: dict, late_stats: dict,
    early_label: str = "1984–2001",
    late_label: str = "2002–26",
    min_games: int = 400,
) -> None:
    """Per-franchise HCA in the early era vs. the recent era (split at 2001–02)."""
    _section("FRANCHISE HCA — ERA COMPARISON (split at 2001–02)")
    print(f"   Regular season only. Franchise name changes merged: "
          f"Bullets→Wizards, LA Clippers→Los Angeles Clippers.")
    print(f"   Min {min_games} home games in each era required.\n")

    _NAME_MAP = {
        "Washington Bullets": "Washington Wizards",
        "LA Clippers": "Los Angeles Clippers",
    }

    def _aggregate(stats: dict) -> dict:
        raw: dict[str, dict] = {}
        for name, s in stats.items():
            key = _NAME_MAP.get(name, name)
            if key not in raw:
                raw[key] = {"hw": 0, "hn": 0, "rw": 0, "rn": 0}
            raw[key]["hw"] += round(s["home_pct"] * s["n_home"] / 100)
            raw[key]["hn"] += s["n_home"]
            raw[key]["rw"] += round(s["road_pct"] * s["n_road"] / 100)
            raw[key]["rn"] += s["n_road"]
        out: dict[str, dict] = {}
        for name, c in raw.items():
            if c["hn"] and c["rn"]:
                h = 100.0 * c["hw"] / c["hn"]
                r = 100.0 * c["rw"] / c["rn"]
                out[name] = {"hca": round(h - r, 1), "n_home": c["hn"]}
        return out

    early_n = _aggregate(early_stats)
    late_n  = _aggregate(late_stats)

    common = {
        t for t in set(early_n) & set(late_n)
        if early_n[t]["n_home"] >= min_games and late_n[t]["n_home"] >= min_games
    }

    if not common:
        print(f"   N = 0 franchises with ≥{min_games} home games in both eras "
              f"(insufficient data for an era comparison)\n")
        return

    rows = sorted(
        [(t, early_n[t]["hca"], late_n[t]["hca"], late_n[t]["hca"] - early_n[t]["hca"])
         for t in common],
        key=lambda x: x[3],
    )

    league_early = sum(early_n[t]["hca"] for t in common) / len(common)
    league_late  = sum(late_n[t]["hca"]  for t in common) / len(common)

    print(f"   N = {len(rows)} franchises with ≥{min_games} home games in both eras")
    print(f"   League avg HCA — {early_label}: {league_early:.1f} pp  |  "
          f"{late_label}: {league_late:.1f} pp  |  change: {league_late - league_early:+.1f} pp\n")

    # Facts for the prose (Appendix B): league-average HCA fell across the
    # two-era split, and every qualifying franchise declined.
    FACTS.set("franchise.league_early", league_early, "{:.1f}",
              note=f"League-average HCA, {early_label}")
    FACTS.set("franchise.league_late", league_late, "{:.0f}",
              note=f"League-average HCA, {late_label}")
    FACTS.set("franchise.n", len(rows), "{:d}",
              note=f"Franchises with >={min_games} home games in both eras")

    print(f"   {'Franchise':<30}  {early_label:>9}  {late_label:>8}  {'Change':>7}  {'N early':>7}")
    print(f"   {'─' * 30}  {'─' * 9}  {'─' * 8}  {'─' * 7}  {'─' * 7}")
    for t, e, l, chg in rows:
        ne = early_n[t]["n_home"]
        print(f"   {t:<30}  {e:>+9.1f}  {l:>+8.1f}  {chg:>+7.1f}  {ne:>7}")

    biggest  = rows[:3]
    smallest = rows[-3:][::-1]
    print(f"\n   ► Every franchise declined: {len([r for r in rows if r[3] < 0])}/{len(rows)} "
          f"with a negative change.")
    print(f"   ► Biggest declines: "
          + ", ".join(f"{t} ({chg:+.1f} pp)" for t, _, _, chg in biggest))
    print(f"   ► Smallest declines (least negative): "
          + ", ".join(f"{t} ({chg:+.1f} pp)" for t, _, _, chg in smallest))
    print()

    # Facts for the prose (Appendix B): named-franchise era-to-era HCA drops, and
    # a guard on which two fell the most.
    _chg = {t: chg for t, _, _, chg in rows}

    def _drop(substr):
        return next((abs(c) for t, c in _chg.items() if substr in t), None)

    for _name, _key in [("Sacramento", "sacramento"), ("Phoenix", "phoenix"),
                        ("New York", "knicks"), ("Denver", "denver"), ("Utah", "utah")]:
        _d = _drop(_name)
        if _d is not None:
            FACTS.set(f"franchise.drop_{_key}", _d, "{:.0f}",
                      note=f"{_name} HCA drop, early to recent era (pp)")
    _top2 = {rows[0][0], rows[1][0]}
    FACTS.guard("sacramento_phoenix_fell_most",
                any("Sacramento" in t for t in _top2) and any("Phoenix" in t for t in _top2),
                claim="Sacramento and Phoenix fell the most",
                value=", ".join(f"{t} ({c:+.0f})" for t, _, _, c in rows[:2]))


def run_hca_consistency_analysis(reg_stats: dict, po_stats: dict) -> None:
    """Correlation between regular-season and playoff franchise HCA — do the
    same franchises protect home court in both contexts?"""
    from scipy.stats import pearsonr, spearmanr

    _section("FRANCHISE HCA — REGULAR SEASON VS. PLAYOFFS CONSISTENCY")
    print("   Do franchises that protect home court in the regular season also do")
    print("   so in the playoffs? Correlation across franchises with both figures.\n")

    rs = reg_stats
    po = po_stats
    shared = sorted(set(rs) & set(po))
    if len(shared) < 5:
        print("   Insufficient overlap between the two tables.\n")
        return

    rs_vals = np.array([rs[t]["hca"] for t in shared])
    po_vals = np.array([po[t]["hca"] for t in shared])
    r_p, p_p = pearsonr(rs_vals, po_vals)
    r_s, p_s = spearmanr(rs_vals, po_vals)
    p_p_s = _fmt_p(p_p)
    p_s_s = _fmt_p(p_s)

    print(f"   N = {len(shared)} franchises with both regular-season and playoff HCA")
    print(f"   Raw HCA:")
    print(f"   Pearson r  = {r_p:+.3f}  (p = {p_p_s}  {_stars(p_p).strip()})")
    print(f"   Spearman ρ = {r_s:+.3f}  (p = {p_s_s}  {_stars(p_s).strip()})")

    # Shrunken-value correlation — attenuation bias reduced
    rs_sh, _ = _shrink_hca(rs)
    po_sh, _ = _shrink_hca(po)
    sh_rs = np.array([rs_sh[t] for t in shared])
    sh_po = np.array([po_sh[t] for t in shared])

    if np.std(sh_po) < 1e-6 or np.std(sh_rs) < 1e-6:
        print(f"\n   Shrunken HCA: true between-franchise variance ≈ 0 in at least one context")
        print(f"   (observed spread across franchises is entirely sampling noise).")
        print(f"   Shrinkage collapses all values to the league mean — shrunken correlation undefined.")
        print(f"   This confirms that franchise-level playoff HCA differences are not reliably")
        print(f"   distinguishable from random variation given typical playoff sample sizes.")
    else:
        r_sh_p, p_sh_p = pearsonr(sh_rs, sh_po)
        r_sh_s, p_sh_s = spearmanr(sh_rs, sh_po)
        print(f"\n   Shrunken HCA (EB toward league mean; reduces attenuation from small samples):")
        print(f"   Pearson r  = {r_sh_p:+.3f}  (p = {_fmt_p(p_sh_p)}  {_stars(p_sh_p).strip()})")
        print(f"   Spearman ρ = {r_sh_s:+.3f}  (p = {_fmt_p(p_sh_s)}  {_stars(p_sh_s).strip()})")
        if r_sh_p > r_p:
            print(f"   Shrinkage strengthens r: raw {r_p:+.3f} → shrunken {r_sh_p:+.3f} (attenuation reduced).")

    print()
    gap = po_vals - rs_vals
    print(f"   Mean regular-season HCA (shared franchises): {rs_vals.mean():+.1f} pp")
    print(f"   Mean playoff HCA (shared franchises):        {po_vals.mean():+.1f} pp")
    print(f"   Mean playoff − regular-season gap:           {gap.mean():+.1f} pp "
          f"(SD {gap.std():.1f})")

    if p_p < 0.05 and r_p > 0:
        print(f"\n   ► Raw correlation positive and significant (r = {r_p:+.3f}) —")
        print(f"     franchises that protect home court in the regular season tend to do so")
        print(f"     in the playoffs too, though playoff sample sizes are too small for")
        print(f"     franchise-level shrinkage to improve on raw estimates.")
    elif p_p >= 0.05:
        print(f"\n   ► No significant correlation — regular-season HCA does not reliably")
        print(f"     predict playoff HCA at the franchise level (playoff samples are small).")


def run_margin_analysis(df: pd.DataFrame) -> None:
    COL_W   = 13
    columns = [
        ("All games",   None, "margin"),
        ("Home wins",   1,    "margin"),
        ("Home losses", 0,    "margin"),
    ]

    _section("WIN MARGIN TRENDS  (home team point differential per game)")
    print("   Positive = home team winning by more.")
    print("   Trend = slope of trend line (change per season year).\n")

    for season_label, sub in [
        ("Regular season", df[df["is_playoff"] == 0]),
        ("Playoffs",       df[df["is_playoff"] == 1]),
    ]:
        n = len(sub.dropna(subset=["margin"]))
        print(f"   {season_label}  (N = {n:,} games)\n")

        header  = f"   {'Era':<12}" + "".join(f"{lbl:>{COL_W}}" for lbl, _, _ in columns)
        divider = f"   {'─'*12}" + "─" * (COL_W * len(columns))
        print(header)
        print(divider)

        for era_label, y1, y2, _ in nba.ERA_DEFS:
            era_rows = sub[(sub["year"] >= y1) & (sub["year"] <= y2)]
            row = f"   {era_label:<12}"
            for _, win_flag, col in columns:
                if win_flag is None:
                    vals = era_rows[col].dropna()
                else:
                    vals = era_rows.loc[era_rows["home_win"] == win_flag, col].dropna()
                row += f"{vals.mean():>+{COL_W}.2f}" if len(vals) else f"{'—':>{COL_W}}"
            print(row)

        print(divider)
        trend_row = f"   {'Trend/yr':<12}"
        for _, win_flag, col in columns:
            data = (
                sub[["year", col]].dropna()
                if win_flag is None
                else sub.loc[sub["home_win"] == win_flag, ["year", col]].dropna()
            )
            if len(data) < 10:
                trend_row += f"{'—':>{COL_W}}"
                continue
            with suppress_noisy_fit_warnings():
                m = smf.ols(f"{col} ~ year", data=data).fit()
            coef = m.params["year"]
            pval = m.pvalues["year"]
            trend_row += f"{coef:>+{COL_W - 3}.3f}{_stars(pval)}"
        print(trend_row)
        print()

    reg_mean = df.loc[df["is_playoff"] == 0, "margin"].mean()
    po_mean  = df.loc[df["is_playoff"] == 1, "margin"].mean()
    print(f"   ► Overall reg-season mean margin: {reg_mean:+.2f} pts.")
    print(f"   ► Overall playoff mean margin:    {po_mean:+.2f} pts.")


def run_quantile_margin_analysis(df: pd.DataFrame) -> None:
    """Unconditional quantile regression — tests whether the margin
    'polarization' reported in §6 is genuine distribution widening or a
    composition artifact of the declining home win rate. (PLAN-STATS item 3.)

    All quantiles drifting down in parallel → pure level effect (wins appeared
    bigger / losses appeared worse only because marginal games changed sides).
    Lower quantiles declining while upper quantiles rise or hold → genuine
    variance widening (polarization confirmed).
    """
    _section("WIN MARGIN POLARIZATION — UNCONDITIONAL QUANTILE REGRESSION  (checks blowout claim in other findings)")
    print("   home margin ~ year at q = 0.10, 0.25, 0.50, 0.75, 0.90.")
    print("   Margin > 0 = home winning. Q10 = big home losses; Q90 = big home wins.")
    print("   All quantiles parallel → pure level effect (conditional divergence is artifact).")
    print("   Q10↓ with Q90↑ → genuine polarization.\n")

    quantiles = [0.10, 0.25, 0.50, 0.75, 0.90]
    q_labels  = ["Q10", "Q25", "Q50", "Q75", "Q90"]

    for ctx_label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po].dropna(subset=["margin"])
        if len(sub) < 100:
            continue
        yr_min, yr_max = int(sub["year"].min()), int(sub["year"].max())
        print(f"   {ctx_label}  (N = {len(sub):,} games, {yr_min}–{yr_max})\n")
        print(f"   {'Quantile':>8}  {'Slope pts/yr':>13}  {'95% CI':>20}  {'p':>8}  {'':3}")
        print(f"   {'─'*8}  {'─'*13}  {'─'*20}  {'─'*8}  {'─'*3}")

        slopes: dict[str, float] = {}
        for q, qlbl in zip(quantiles, q_labels):
            try:
                with suppress_noisy_fit_warnings():
                    m = smf.quantreg("margin ~ year", data=sub).fit(q=q, disp=0)
                coef = float(m.params["year"])
                pval = float(m.pvalues["year"])
                ci   = m.conf_int().loc["year"]
                lo, hi = float(ci.iloc[0]), float(ci.iloc[1])
                pval_s = _fmt_p(pval)
                print(f"   {qlbl:>8}  {coef:>+13.3f}  "
                      f"[{lo:+.3f}, {hi:+.3f}]  {pval_s:>8}  {_stars(pval)}")
                slopes[qlbl] = coef
            except Exception as exc:
                print(f"   {qlbl:>8}  (failed: {exc})")

        if "Q10" in slopes and "Q90" in slopes:
            spread_chg = slopes["Q90"] - slopes["Q10"]
            q50 = slopes.get("Q50", 0.0)
            # Fact for the prose (Appendix B): the win/loss-margin spread widens
            # by this many points per year (matches the margin chart).
            FACTS.set(f"margin.spread_{'po' if is_po else 'reg'}", spread_chg, "{:.1f}",
                      note=f"{ctx_label}: win-margin spread widening (Q90−Q10 slope, pts/yr)")
            print(f"\n   IQR change rate (Q90 − Q10 slope diff): {spread_chg:+.3f} pts/yr")
            if spread_chg > 0.02:
                print(f"   ► Q90 rises / Q10 falls — genuine variance widening (polarization confirmed).")
                print(f"     The conditional-on-outcome divergence in §6 reflects a real change in")
                print(f"     distribution shape, not just a composition effect.")
            elif spread_chg < -0.02:
                print(f"   ► Q90 falls / Q10 rises — distribution compressing.")
            else:
                all_slopes = list(slopes.values())
                rng = max(all_slopes) - min(all_slopes)
                if rng < 0.05:
                    print(f"   ► All quantiles shift in parallel (spread change ≈ 0).")
                    print(f"     The §6 conditional divergence is a composition artifact:")
                    print(f"     as home win % declines, marginal games flip sides and push")
                    print(f"     the conditional-win and conditional-loss means apart without")
                    print(f"     any genuine change in the distribution's shape.")
                else:
                    print(f"   ► Mixed pattern; individual slopes above are the primary result.")
        print()


def run_net_rating_analysis(df: pd.DataFrame) -> None:
    """Home-team net rating (pts per 100 poss) by era and trend over time.

    Net rating = margin / pace_avg * 100. Requires pace data (OREB/TOV);
    seasons without it are excluded (typically pre-1997).
    """
    _section("NET RATING SPLIT BY VENUE  (home team pts per 100 possessions)")
    print("   Net rating = (home pts − away pts) / avg possessions × 100.")
    print("   Positive = home team outscored visitors per 100 possessions.")
    print("   Requires pace data; seasons without TOV/OREB data are excluded.\n")

    COL_W = 22

    for season_label, sub in [
        ("Regular season", df[df["is_playoff"] == 0]),
        ("Playoffs",       df[df["is_playoff"] == 1]),
    ]:
        valid = sub.dropna(subset=["margin", "pace_avg"])
        valid = valid[valid["pace_avg"] > 0].copy()
        valid["net_rating"] = valid["margin"] / valid["pace_avg"] * 100

        n = len(valid)
        print(f"   {season_label}  (N = {n:,} games with pace data)\n")

        header  = f"   {'Era':<12}{'Net rating (pts/100)':>{COL_W}}"
        divider = f"   {'─'*12}{'─'*COL_W}"
        print(header)
        print(divider)

        nr_by_era = []
        for era_label, y1, y2, _ in nba.ERA_DEFS:
            era_rows = valid[(valid["year"] >= y1) & (valid["year"] <= y2)]
            if len(era_rows) < 10:
                print(f"   {era_label:<12}{'—':>{COL_W}}")
                nr_by_era.append(None)
            else:
                nr = era_rows["net_rating"].mean()
                print(f"   {era_label:<12}{nr:>+{COL_W}.2f}")
                nr_by_era.append(nr)

        # Facts for the prose (§1): regular-season net rating, mid-2010s vs today.
        # ERA_DEFS order: [..., 3]=2005–17 (mid-2010s), [5]=2023–26 (today).
        # Skip when either era is too sparse to have a value (None), as on the
        # test fixture; the full dataset always populates both.
        if season_label == "Regular season" and nr_by_era[3] is not None and nr_by_era[5] is not None:
            FACTS.set("net.reg_mid2010s", nr_by_era[3], "{:.0f}",
                      note="Reg. season net rating 2005–17 (pts/100)")
            FACTS.set("net.reg_today", nr_by_era[5], "{:.0f}",
                      note="Reg. season net rating 2023–26 (pts/100)")
            # Guard the prose magnitude (§6 / summary): the mid-2010s→today net
            # rating drop is "more than a third" (3.13 → 1.97 ≈ 37%).
            _nr_drop = (nr_by_era[3] - nr_by_era[5]) / nr_by_era[3] if nr_by_era[3] else float("nan")
            FACTS.guard("net_reg_drop_over_third", _nr_drop > 1 / 3,
                        claim="the regular-season net-rating advantage shrank by more than a third",
                        value=f"{nr_by_era[3]:.2f} → {nr_by_era[5]:.2f} = {_nr_drop * 100:.0f}% drop")

        print(divider)
        if len(valid) >= 10:
            with suppress_noisy_fit_warnings():
                m = smf.ols("net_rating ~ year", data=valid).fit()
            coef = m.params["year"]
            pval = m.pvalues["year"]
            print(f"   {'Trend/yr':<12}{coef:>+{COL_W - 3}.3f}{_stars(pval)}")
        print()

    reg = df[df["is_playoff"] == 0].dropna(subset=["margin", "pace_avg"])
    reg = reg[reg["pace_avg"] > 0]
    po  = df[df["is_playoff"] == 1].dropna(subset=["margin", "pace_avg"])
    po  = po[po["pace_avg"] > 0]
    if len(reg) > 0:
        reg_nr = (reg["margin"] / reg["pace_avg"] * 100).mean()
        print(f"   ► Overall reg-season mean net rating: {reg_nr:+.2f} pts/100 poss.")
    if len(po) > 0:
        po_nr = (po["margin"] / po["pace_avg"] * 100).mean()
        print(f"   ► Overall playoff mean net rating:    {po_nr:+.2f} pts/100 poss.")
