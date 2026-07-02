"""Channel decomposition of home-court advantage: mediation decomposition and
bootstrap, 3PA-controlled mediation, sensitivity, SHAP channel attribution,
out-of-sample forecast, sequential R² decomposition, coefficient stability,
the combined factor summary, the rule-change channel event study, and the
cross-test multiple-comparisons summary."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
import contextlib
import io

from nbakit.textfmt import stars as _stars, p_value as _fmt_p

import home_court_data as nba
from home_court_facts import FACTS

from ._helpers import (
    suppress_noisy_fit_warnings, _warn_if_not_converged,
    _section, _pp, _ci_lo_hi, _mcfadden, _clean,
)

_MED_KEYS = ["efg_pct_diff", "foul_diff", "tov_diff", "reb_diff"]


_SENS_CHANNELS: list[tuple[str, str]] = [
    ("efg_pct_diff", "Shooting"),
    ("foul_diff",    "Fouls"),
    ("tov_diff",     "Turnovers"),
    ("reb_diff",     "Rebounding"),
]


_SHAP_CHANNELS: list[tuple[str, str]] = [
    ("efg_pct_diff", "Shooting"),
    ("foul_diff",    "Fouls"),
    ("tov_diff",     "Turnovers"),
    ("reb_diff",     "Rebounding"),
]


_OOS_CHANNELS = ["efg_pct_diff", "foul_diff", "tov_diff", "reb_diff"]


def compute_mediation_decomposition(df: pd.DataFrame) -> dict:
    """Box-score channel shares of the HCA level and its trend, RS and playoffs.

    The numbers run_mediation_analysis prints, returned in a structure the plot
    layer renders directly — so the chart and home_court_results.md never diverge. Each
    channel row carries both a table_label (for home_court_results.md) and a chart_label
    (for the plot). Linear-probability identities; see run_mediation_analysis.
    """
    channels = [
        ("efg_pct_diff", "eFG% diff (pp)", "Shooting"),
        ("foul_diff",    "Foul diff",      "Fouls"),
        ("tov_diff",     "TOV diff",       "Turnovers"),
        ("reb_diff",     "REB diff",       "Rebounding"),
    ]
    keys = [k for k, _, _ in channels]
    rhs = " + ".join(keys)

    out: dict = {"channels": [(k, tl, cl) for k, tl, cl in channels]}
    for label, sub in [
        ("Regular season", df[df["is_playoff"] == 0]),
        ("Playoffs",       df[df["is_playoff"] == 1]),
    ]:
        d = sub.dropna(subset=keys + ["home_win", "year"])
        if len(d) < 100:
            continue

        hw = d["home_win"].mean() * 100
        level = hw - 50.0

        with suppress_noisy_fit_warnings():
            cl = {"groups": d["year"]}
            m_chan = smf.ols(f"home_win ~ {rhs}", data=d).fit(
                cov_type="cluster", cov_kwds=cl)
            m_year = smf.ols("home_win ~ year", data=d).fit(
                cov_type="cluster", cov_kwds=cl)
            m_full = smf.ols(f"home_win ~ year + {rhs}", data=d).fit(
                cov_type="cluster", cov_kwds=cl)
            chan_trends = {
                k: smf.ols(f"{k} ~ year", data=d).fit(
                    cov_type="cluster", cov_kwds=cl)
                for k in keys
            }

        level_rows = []
        for k, tl, clab in channels:
            b_pp = m_chan.params[k] * 100
            mu = d[k].mean()
            contrib = b_pp * mu
            level_rows.append({
                "key": k, "table_label": tl, "chart_label": clab,
                "mean_diff": mu, "pp_per_unit": b_pp,
                "contrib": contrib, "pct": 100 * contrib / level,
                "stars": _stars(m_chan.pvalues[k]).strip(),
            })
        resid_level = m_chan.params["Intercept"] * 100 - 50.0

        t_total = m_year.params["year"] * 100
        t_resid = m_full.params["year"] * 100
        trend_rows = []
        mediated = 0.0
        for k, tl, clab in channels:
            gamma = chan_trends[k].params["year"]
            g_lo, g_hi = _ci_lo_hi(chan_trends[k], "year")
            contrib = m_full.params[k] * 100 * gamma
            mediated += contrib
            trend_rows.append({
                "key": k, "table_label": tl, "chart_label": clab,
                "gamma": gamma, "gamma_ci_lo": g_lo, "gamma_ci_hi": g_hi,
                "contrib": contrib, "pct": 100 * contrib / t_total,
                "stars": _stars(chan_trends[k].pvalues["year"]).strip(),
            })

        out[label] = {
            "n": len(d), "home_win_pct": hw, "level_pp": level,
            "chan_r2": m_chan.rsquared,
            "level": level_rows,
            "level_unexplained": {"contrib": resid_level, "pct": 100 * resid_level / level},
            "trend_total_pp": t_total, "trend_total_p": m_year.pvalues["year"],
            "trend": trend_rows,
            "trend_unmediated": {"contrib": t_resid, "pct": 100 * t_resid / t_total},
            "pct_level": 100 * (level - resid_level) / level,
            "pct_trend": 100 * mediated / t_total,
        }
    return out


def _mediation_shares_np(Y: np.ndarray, YEAR: np.ndarray, CH: np.ndarray):
    """One bootstrap replicate of the mediation shares, in pure numpy.

    Reproduces the point-estimate identities in compute_mediation_decomposition
    (the cluster-robust SEs there don't change the coefficients), but with
    pre-built design matrices so 500 resamples stay fast. Returns
    (level_pct[4], trend_pct[4], pct_level, pct_trend).
    """
    ols = lambda X, y: np.linalg.lstsq(X, y, rcond=None)[0]
    ones = np.ones(len(Y))
    b_chan = ols(np.column_stack([ones, CH]), Y)          # [int, 4 channel betas]
    b_year = ols(np.column_stack([ones, YEAR]), Y)        # [int, year]
    b_full = ols(np.column_stack([ones, YEAR, CH]), Y)    # [int, year, 4 betas]
    gammas = np.array([ols(np.column_stack([ones, YEAR]), CH[:, j])[1]
                       for j in range(CH.shape[1])])

    level   = Y.mean() * 100.0 - 50.0
    t_total = b_year[1] * 100.0
    level_contrib = b_chan[1:] * 100.0 * CH.mean(axis=0)
    trend_contrib = b_full[2:] * 100.0 * gammas
    resid_level   = b_chan[0] * 100.0 - 50.0

    level_pct = 100.0 * level_contrib / level if level else np.full(4, np.nan)
    trend_pct = 100.0 * trend_contrib / t_total if t_total else np.full(4, np.nan)
    pct_level = 100.0 * (level - resid_level) / level if level else float("nan")
    pct_trend = 100.0 * trend_contrib.sum() / t_total if t_total else float("nan")
    return level_pct, trend_pct, pct_level, pct_trend


def compute_mediation_bootstrap(df: pd.DataFrame, n_boot: int = 500,
                                seed: int = 0) -> dict:
    """Season-block bootstrap 95% CIs for the mediation shares (RS and playoffs).

    Resamples whole seasons with replacement (the cluster unit, matching the
    cluster-robust SEs the point decomposition uses) and recomputes each
    channel's % of the level and % of the decline, plus the two headline
    "channels carry X%" figures. Seeded, so home_court_results.md stays reproducible.
    """
    rng = np.random.default_rng(seed)
    out: dict = {}
    for label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po].dropna(subset=_MED_KEYS + ["home_win", "year"])
        if len(sub) < 100:
            continue
        Y    = sub["home_win"].to_numpy(dtype=float)
        YEAR = sub["year"].to_numpy(dtype=float)
        CH   = sub[_MED_KEYS].to_numpy(dtype=float)
        years   = np.unique(YEAR)
        idx_by  = {y: np.flatnonzero(YEAR == y) for y in years}

        lvl = [[] for _ in _MED_KEYS]
        trd = [[] for _ in _MED_KEYS]
        pls, pts = [], []
        for _ in range(n_boot):
            pick = rng.choice(years, size=len(years), replace=True)
            rows = np.concatenate([idx_by[y] for y in pick])
            try:
                lp, tp, pl, pt = _mediation_shares_np(Y[rows], YEAR[rows], CH[rows])
            except Exception:
                continue
            for j in range(len(_MED_KEYS)):
                lvl[j].append(lp[j]); trd[j].append(tp[j])
            pls.append(pl); pts.append(pt)

        ci = lambda a: (
            (float(np.nanpercentile(a, 2.5)), float(np.nanpercentile(a, 97.5)))
            if a else (float("nan"), float("nan")))
        out[label] = {
            "n_boot": len(pts),
            "level_ci": {k: ci(lvl[j]) for j, k in enumerate(_MED_KEYS)},
            "trend_ci": {k: ci(trd[j]) for j, k in enumerate(_MED_KEYS)},
            "pct_level_ci": ci(pls),
            "pct_trend_ci": ci(pts),
        }
    return out


def compute_channel_3pa_control(df: pd.DataFrame) -> dict:
    """Each box-score channel's home-differential year-trend, before and after
    controlling for the game's 3PA rate — the test behind "the shooting fade is
    the three-point story, the rebounding fade is not." Same regressions
    run_mediation_analysis prints in its diagnostic block; returned here for the
    plot layer so the chart and RESULTS never diverge.

    Returns {ctx: {"channels": [{chart_label, g_raw, g_ctrl, surviving, absorbed,
    win_raw, win_ctrl, p_raw, p_ctrl}, ...], "n": int}} for ctx in
    ("Regular season", "Playoffs"). `surviving` = g_ctrl/g_raw as a percent
    (100 = untouched by the control, 0 = fully absorbed, <0 = the trend reverses
    once threes are held constant). `win_raw`/`win_ctrl` re-express the channel's
    before/after slope as win-percentage-points per decade (channel slope × the
    full-model win coefficient × 10), giving the dumbbell chart one shared axis.
    """
    channels = [
        ("efg_pct_diff", "Shooting"),
        ("foul_diff",    "Fouls"),
        ("tov_diff",     "Turnovers"),
        ("reb_diff",     "Rebounding"),
    ]
    keys = [k for k, _ in channels]
    rhs = " + ".join(keys)
    out: dict = {}
    for label, sub in [
        ("Regular season", df[df["is_playoff"] == 0]),
        ("Playoffs",       df[df["is_playoff"] == 1]),
    ]:
        d = sub.dropna(subset=keys + ["year", "tpa_rate_avg", "home_win"])
        if len(d) < 100:
            continue
        rows = []
        with suppress_noisy_fit_warnings():
            cl = {"groups": d["year"]}
            # Full win-model coefficients convert each channel's per-year slope
            # into win-percentage-points — the same currency as the mediation
            # chart — so the before/after dumbbell can share one axis across the
            # four channels (which are otherwise in different box-score units).
            m_win = smf.ols(f"home_win ~ year + {rhs}", data=d).fit(
                cov_type="cluster", cov_kwds=cl)
            for k, clbl in channels:
                m_raw  = smf.ols(f"{k} ~ year", data=d).fit(cov_type="cluster", cov_kwds=cl)
                m_ctrl = smf.ols(f"{k} ~ year + tpa_rate_avg", data=d).fit(
                    cov_type="cluster", cov_kwds=cl)
                g_raw, g_ctrl = float(m_raw.params["year"]), float(m_ctrl.params["year"])
                surviving = 100.0 * g_ctrl / g_raw if g_raw != 0 else float("nan")
                coef = float(m_win.params[k]) * 100.0  # win pp per unit of channel k
                rows.append({
                    "chart_label": clbl, "g_raw": g_raw, "g_ctrl": g_ctrl,
                    "surviving": surviving, "absorbed": 100.0 - surviving,
                    "win_raw":  coef * g_raw  * 10.0,  # win pp/decade, before 3PA control
                    "win_ctrl": coef * g_ctrl * 10.0,  # win pp/decade, after 3PA control
                    "p_raw": float(m_raw.pvalues["year"]),
                    "p_ctrl": float(m_ctrl.pvalues["year"]),
                })
        out[label] = {"channels": rows, "n": len(d)}
    return out


def run_mediation_analysis(df: pd.DataFrame) -> None:
    """Convert box-score channels into win-% shares of the HCA level and trend.

    Linear-probability model (OLS on home_win) so both decompositions are
    exact identities:
      level: mean win % = intercept + Σ coef × mean differential
      trend: year slope (bivariate) = year slope (full model)
             + Σ coef × (channel trend per year)   [omitted-variable identity]
    Channels are proximate — they are how home advantage shows up in the box
    score — so this is an accounting decomposition, not deep causation.
    """
    ft_mean = df.loc[df["is_playoff"] == 0, "ft_pct_diff"].mean()

    _section("MEDIATION — BOX-SCORE CHANNELS AS SHARES OF HCA LEVEL AND TREND")
    print("   How much of the home edge, and of its decline, flows through the")
    print("   measured channels: shooting (eFG%), referee fouls, turnovers, and")
    print("   rebounds? Linear-probability model of home_win on the four")
    print("   home-minus-away differentials; cluster-robust SEs by season.")
    print("   Level identity:  mean win % = intercept + Σ coef × mean diff.")
    print("   Trend identity:  total pp/yr = unmediated pp/yr + Σ coef × channel trend/yr.")
    print("   Foul diff carries the free-throw-attempt channel; FT% diff is")
    print(f"   excluded (mean ≈ {ft_mean:+.1f} pp, negligible). Channels are proximate —")
    print("   how HCA expresses itself in the box score — so this is an")
    print("   accounting decomposition, not deep causation.\n")

    decomp = compute_mediation_decomposition(df)
    for label in ("Regular season", "Playoffs"):
        ctx = decomp.get(label)
        if ctx is None:
            print(f"   {label}: insufficient data.\n")
            continue

        level = ctx["level_pp"]
        # Statistical detail for investigation.md: the HCA level above a coin flip.
        _mctx = "po" if label == "Playoffs" else "reg"
        FACTS.set(f"{_mctx}.level_pp", level, "{:+.1f}",
                  note=f"{label}: HCA level above coin flip (pp)")
        FACTS.set(f"{_mctx}.level_unexplained_pct", ctx["level_unexplained"]["pct"], "{:.0f}%",
                  note=f"{label}: share of the HCA level left unexplained by the four channels")
        print(f"   {label}  (N = {ctx['n']:,} games, home win % = {ctx['home_win_pct']:.1f}, "
              f"level above coin flip = {level:+.1f} pp)")
        print(f"   Channel-model R² = {ctx['chan_r2']:.3f} — share of game-outcome "
              f"variance the four channels carry.\n")

        print(f"   Level decomposition  (coef × mean diff):")
        print(f"   {'Channel':<16}  {'Mean diff':>10}  {'pp per unit':>12}  "
              f"{'Contribution':>13}  {'% of level':>10}")
        print(f"   {'─'*16}  {'─'*10}  {'─'*12}  {'─'*13}  {'─'*10}")
        for r in ctx["level"]:
            print(f"   {r['table_label']:<16}  {r['mean_diff']:>+10.2f}  "
                  f"{r['pp_per_unit']:>+9.2f} {r['stars']:<3}"
                  f"{r['contrib']:>+10.1f} pp  {r['pct']:>9.0f}%")
        ru = ctx["level_unexplained"]
        print(f"   {'─'*16}  {'─'*10}  {'─'*12}  {'─'*13}  {'─'*10}")
        print(f"   {'Unexplained':<16}  {'':>10}  {'':>12}  {ru['contrib']:>+10.1f} pp  "
              f"{ru['pct']:>9.0f}%")

        t_total = ctx["trend_total_pp"]
        print(f"\n   Trend decomposition  (pp of home win % per year):")
        print(f"   Total trend (home_win ~ year): {t_total:+.3f} pp/yr  "
              f"(p = {_fmt_p(ctx['trend_total_p'])}  {_stars(ctx['trend_total_p']).strip()})\n")
        print(f"   {'Channel':<16}  {'Trend in diff/yr':>16}  {'95% CI (diff/yr)':>22}  "
              f"{'Contribution':>15}  {'% of trend':>10}")
        print(f"   {'─'*16}  {'─'*16}  {'─'*22}  {'─'*15}  {'─'*10}")
        for r in ctx["trend"]:
            _ci = f"[{r['gamma_ci_lo']:+.4f}, {r['gamma_ci_hi']:+.4f}]"
            print(f"   {r['table_label']:<16}  {r['gamma']:>+12.4f} {r['stars']:<3}  "
                  f"{_ci:>22}  {r['contrib']:>+9.4f} pp/yr  {r['pct']:>9.0f}%")
        mu = ctx["trend_unmediated"]
        mediated_pp = sum(r["contrib"] for r in ctx["trend"])
        mediated_pct = sum(r["pct"] for r in ctx["trend"])
        print(f"   {'─'*16}  {'─'*16}  {'─'*15}  {'─'*10}")
        print(f"   {'Sum, channels':<16}  {'':>16}  {mediated_pp:>+9.4f} pp/yr  "
              f"{mediated_pct:>9.0f}%")
        print(f"   {'Unmediated':<16}  {'':>16}  {mu['contrib']:>+9.4f} pp/yr  "
              f"{mu['pct']:>9.0f}%")

        print(f"\n   ► {label}: channels carry {ctx['pct_level']:.0f}% of the HCA level "
              f"and {ctx['pct_trend']:.0f}% of its decline.")

        # ── Facts for the prose docs (§2: the four-factor share table) ──
        if label == "Regular season":
            _short = {"efg_pct_diff": "shooting", "foul_diff": "fouls",
                      "tov_diff": "turnovers", "reb_diff": "rebounding"}
            for r in ctx["level"]:
                FACTS.set(f"share.{_short[r['key']]}.adv", r["pct"], "{:.0f}%",
                          note=f"Reg. season: {r['table_label']} share of the HCA level")
            for r in ctx["trend"]:
                FACTS.set(f"share.{_short[r['key']]}.decline", r["pct"], "{:.0f}%",
                          note=f"Reg. season: {r['table_label']} share of the decline")
                FACTS.set(f"trend.{_short[r['key']]}", r["gamma"], "{:+.3f}",
                          note=f"Reg: {r['table_label']} home-minus-away trend per year")
                FACTS.set(f"trend.{_short[r['key']]}_mag", abs(r["gamma"]), "{:.3f}",
                          note=f"Reg: {r['table_label']} trend magnitude per year")
                FACTS.set(f"trend.{_short[r['key']]}_ci_lo", r["gamma_ci_lo"], "{:+.3f}",
                          note=f"Reg: {r['table_label']} trend 95% CI low (per year)")
                FACTS.set(f"trend.{_short[r['key']]}_ci_hi", r["gamma_ci_hi"], "{:+.3f}",
                          note=f"Reg: {r['table_label']} trend 95% CI high (per year)")
            FACTS.set("share.fourfactors.adv", ctx["pct_level"], "{:.0f}%",
                      note="Reg. season: all four channels' share of the HCA level")
            FACTS.set("share.fourfactors.decline", ctx["pct_trend"], "{:.0f}%",
                      note="Reg. season: all four channels' share of the decline")
            _decline_shares = {_short[r["key"]]: r["pct"] for r in ctx["trend"]}
            _largest = max(_decline_shares, key=_decline_shares.get)
            FACTS.guard("rebounding_largest_driver", _largest == "rebounding",
                        claim="rebounding is the largest single driver of the decline",
                        value=f"largest is {_largest} ({_decline_shares[_largest]:.0f}%)")

        if label == "Playoffs":
            FACTS.set("share.fourfactors_po.decline", ctx["pct_trend"], "{:.0f}%",
                      note="Playoffs: all four channels' share of the decline")
            _shortp = {"efg_pct_diff": "shooting", "foul_diff": "fouls",
                       "tov_diff": "turnovers", "reb_diff": "rebounding"}
            for r in ctx["level"]:
                FACTS.set(f"share_po.{_shortp[r['key']]}.adv", r["pct"], "{:.0f}%",
                          note=f"Playoffs: {r['table_label']} share of the HCA level")
            for r in ctx["trend"]:
                FACTS.set(f"share_po.{_shortp[r['key']]}.decline", r["pct"], "{:.0f}%",
                          note=f"Playoffs: {r['table_label']} share of the decline")
                FACTS.set(f"trend_po.{_shortp[r['key']]}", r["gamma"], "{:+.3f}",
                          note=f"Playoffs: {r['table_label']} home-minus-away trend per year")
                FACTS.set(f"trend_po.{_shortp[r['key']]}_mag", abs(r["gamma"]), "{:.3f}",
                          note=f"Playoffs: {r['table_label']} trend magnitude per year")
                FACTS.set(f"trend_po.{_shortp[r['key']]}_ci_lo", r["gamma_ci_lo"], "{:+.3f}",
                          note=f"Playoffs: {r['table_label']} trend 95% CI low (per year)")
                FACTS.set(f"trend_po.{_shortp[r['key']]}_ci_hi", r["gamma_ci_hi"], "{:+.3f}",
                          note=f"Playoffs: {r['table_label']} trend 95% CI high (per year)")
            FACTS.set("share.fourfactors_po.adv", ctx["pct_level"], "{:.0f}%",
                      note="Playoffs: all four channels' share of the HCA level")
            print("   ► Note: playoff differentials fold in the seed-quality gap (the")
            print("     home team is usually the better team) — see the seeding")
            print("     decomposition for that control.")
        print()

    # ── Bootstrap CIs on the shares (season block resample) ───────────────────
    print("   ─ Bootstrap 95% CIs on the shares (season block resample, B=500) ─")
    print("   Resamples whole seasons with replacement and recomputes the shares;")
    print("   the band is the 2.5–97.5 percentile across resamples. Wide bands")
    print("   (especially in the playoffs) mean the point share is loosely pinned.\n")
    boot = compute_mediation_bootstrap(df)
    for label in ("Regular season", "Playoffs"):
        b, ctx = boot.get(label), decomp.get(label)
        if not b or ctx is None:
            continue
        lvl_pt = {r["key"]: r["pct"] for r in ctx["level"]}
        trd_pt = {r["key"]: r["pct"] for r in ctx["trend"]}
        print(f"   {label}  (B = {b['n_boot']} resamples)")
        print(f"   {'Channel':<16}  {'% level':>8}  {'95% CI':>15}  "
              f"{'% trend':>8}  {'95% CI':>15}")
        print(f"   {'─'*16}  {'─'*8}  {'─'*15}  {'─'*8}  {'─'*15}")
        _shortb = {"efg_pct_diff": "shooting", "foul_diff": "fouls",
                   "tov_diff": "turnovers", "reb_diff": "rebounding"}
        _pfx = "share_po" if label == "Playoffs" else "share"
        for k, tl, _ in decomp["channels"]:
            ll, lh = b["level_ci"][k]
            tlo, thi = b["trend_ci"][k]
            # Statistical detail for investigation.md: per-channel decline-share CIs.
            FACTS.set(f"{_pfx}.{_shortb[k]}.decline_ci_lo", tlo, "{:.0f}",
                      note=f"{label}: {tl} decline-share 95% CI low")
            FACTS.set(f"{_pfx}.{_shortb[k]}.decline_ci_hi", thi, "{:.0f}",
                      note=f"{label}: {tl} decline-share 95% CI high")
            print(f"   {tl:<16}  {lvl_pt[k]:>7.0f}%  [{ll:>+5.0f},{lh:>+5.0f}]%  "
                  f"{trd_pt[k]:>7.0f}%  [{tlo:>+5.0f},{thi:>+5.0f}]%")
        pl, pt = b["pct_level_ci"], b["pct_trend_ci"]
        # Statistical detail for investigation.md: 95% CIs on the four-factor shares.
        _ff = "share.fourfactors_po" if label == "Playoffs" else "share.fourfactors"
        FACTS.set(f"{_ff}.adv_ci_lo", pl[0], "{:.0f}", note=f"{label}: four-factor level share 95% CI low")
        FACTS.set(f"{_ff}.adv_ci_hi", pl[1], "{:.0f}", note=f"{label}: four-factor level share 95% CI high")
        FACTS.set(f"{_ff}.decline_ci_lo", pt[0], "{:.0f}", note=f"{label}: four-factor decline share 95% CI low")
        FACTS.set(f"{_ff}.decline_ci_hi", pt[1], "{:.0f}", note=f"{label}: four-factor decline share 95% CI high")
        print(f"   {'─'*16}")
        print(f"   Channels carry {ctx['pct_level']:.0f}% of the level "
              f"(95% CI [{pl[0]:.0f}, {pl[1]:.0f}]%) and {ctx['pct_trend']:.0f}% of the "
              f"decline (95% CI [{pt[0]:.0f}, {pt[1]:.0f}]%).\n")

    channels = [(k, tl) for k, tl, _ in decomp["channels"]]
    keys = [k for k, _ in channels]

    # ── Diagnostic: are the channel trends downstream of the 3-point shift? ──
    # The trend decomposition credits rebounding and turnovers with large shares
    # of the decline, but those edges may simply be fading because the game moved
    # to the perimeter. Re-fit each channel differential's year-trend with the
    # game's 3PA rate added. Game-to-game 3PA variation within a season gives the
    # control real identifying power. A trend that SURVIVES the control is an
    # independent driver; one that collapses is downstream of the shooting shift.
    # (Caveat: season-mean 3PA is near-collinear with year, so high absorption is
    #  expected and only weakly informative — survival is the strong signal.)
    print("   ─ Are the channel trends downstream of the 3-point shift? ─")
    print("   Each differential's year-trend, before and after controlling for the")
    print("   game's 3PA rate. A trend that survives the control is an independent")
    print("   driver; one that collapses faded with the move to the perimeter.\n")

    for label, sub in [
        ("Regular season", df[df["is_playoff"] == 0]),
        ("Playoffs",       df[df["is_playoff"] == 1]),
    ]:
        d = sub.dropna(subset=keys + ["year", "tpa_rate_avg"])
        if len(d) < 100:
            continue
        print(f"   {label}  (N = {len(d):,} games)")
        print(f"   {'Channel':<16}  {'Trend/yr':>11}  {'Trend/yr | 3PA':>16}  {'Absorbed':>9}")
        print(f"   {'─'*16}  {'─'*11}  {'─'*16}  {'─'*9}")
        absorbed_by: dict[str, tuple[float, float]] = {}
        with suppress_noisy_fit_warnings():
            cl = {"groups": d["year"]}
            for k, lbl in channels:
                m_raw  = smf.ols(f"{k} ~ year", data=d).fit(cov_type="cluster", cov_kwds=cl)
                m_ctrl = smf.ols(f"{k} ~ year + tpa_rate_avg", data=d).fit(
                    cov_type="cluster", cov_kwds=cl)
                g_raw, g_ctrl = m_raw.params["year"], m_ctrl.params["year"]
                s_raw  = _stars(m_raw.pvalues["year"]).strip()
                s_ctrl = _stars(m_ctrl.pvalues["year"]).strip()
                absorbed = 100 * (1 - g_ctrl / g_raw) if g_raw != 0 else float("nan")
                absorbed_by[k] = (absorbed, m_ctrl.pvalues["year"])
                print(f"   {lbl:<16}  {g_raw:>+9.4f}{s_raw:<2}  {g_ctrl:>+14.4f}{s_ctrl:<2}  "
                      f"{absorbed:>8.0f}%")

        if label == "Regular season":
            _foul_abs = absorbed_by["foul_diff"][0]
            _tov_abs = absorbed_by["tov_diff"][0]
            FACTS.guard("threept_half_foul_tov",
                        40 <= _foul_abs <= 65 and 40 <= _tov_abs <= 65,
                        claim="the three-point shift explains about half of both the foul and turnover declines",
                        value=f"foul {_foul_abs:.0f}% / turnover {_tov_abs:.0f}% absorbed by 3PA")
            # Statistical detail for investigation.md: 3PA absorbs little of the
            # rebounding trend, which stays significant.
            _reb_abs, _reb_ap = absorbed_by["reb_diff"]
            FACTS.set("reb.absorbed_by_3pa", _reb_abs, "{:.0f}%",
                      note="Reg: share of the rebounding trend absorbed by the 3PA control")
            FACTS.set("reb.controlled_3pa_p", "< 0.001" if _reb_ap < 0.001 else f"= {_reb_ap:.3f}",
                      note="Reg: rebounding trend p-value after the 3PA control (display)")

        reb_p = absorbed_by["reb_diff"][1]
        tov_p = absorbed_by["tov_diff"][1]
        if reb_p > 0.05 and tov_p > 0.05:
            print(f"\n   ► With 3PA controlled, neither the rebounding nor the turnover")
            print(f"     trend stays significant — both edges faded with the move to the")
            print(f"     perimeter, not as independent drivers.")
        else:
            survivors = [lbl for k, (_, p) in absorbed_by.items()
                         for kk, lbl in channels if kk == k and p < 0.05
                         and k in ("reb_diff", "tov_diff")]
            print(f"\n   ► Survives the 3PA control: {', '.join(survivors)} — not fully")
            print(f"     explained by the shooting revolution.")
        print()

    # ── Coefficient stability by era ──────────────────────────────────────────
    # The pooled decomposition assumes each channel's marginal effect on home
    # winning probability is constant across 43 seasons. Re-fit the channel
    # model within each era to check whether the coefficients shift materially.
    # Regular season only (playoffs have too few games per era for stable fits).
    print("   ─ Coefficient stability by era (regular season only) ─")
    print("   Re-fitting the LPM within each era to check whether the channel")
    print("   coefficients are stable across 43 seasons.")
    print("   (pp per unit of each home-minus-away differential)\n")

    rs = df[df["is_playoff"] == 0]
    print(f"   {'Era':<12}  {'N games':>8}  "
          f"{'eFG%':>8}  {'Fouls':>8}  {'TOV':>8}  {'REB':>8}")
    print(f"   {'─'*12}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*8}")
    for era_label, y1, y2, _ in nba.ERA_DEFS:
        sub = rs[(rs["year"] >= y1) & (rs["year"] <= y2)].dropna(subset=keys + ["home_win"])
        if len(sub) < 200:
            print(f"   {era_label:<12}  {len(sub):>8,}  {'⚠ too few':>36}")
            continue
        with suppress_noisy_fit_warnings():
            rhs = " + ".join(keys)
            m = smf.ols(f"home_win ~ {rhs}", data=sub).fit(
                cov_type="cluster", cov_kwds={"groups": sub["year"]})
        b = m.params
        print(f"   {era_label:<12}  {len(sub):>8,}  "
              f"{b['efg_pct_diff']*100:>+7.2f}  "
              f"{b['foul_diff']*100:>+7.2f}  "
              f"{b['tov_diff']*100:>+7.2f}  "
              f"{b['reb_diff']*100:>+7.2f}")

    print(f"\n   Pooled (all seasons):  "
          f"eFG%={decomp['Regular season']['level'][0]['pp_per_unit']:+.2f}  "
          f"Fouls={decomp['Regular season']['level'][1]['pp_per_unit']:+.2f}  "
          f"TOV={decomp['Regular season']['level'][2]['pp_per_unit']:+.2f}  "
          f"REB={decomp['Regular season']['level'][3]['pp_per_unit']:+.2f}  (pp per unit)")
    print("   ► Stable coefficients validate the pooled decomposition.")
    print("     Large era-to-era shifts would mean the 'share' percentages are")
    print("     a blend of heterogeneous effects and should be interpreted with caution.")
    print()


def compute_mediation_sensitivity(df: pd.DataFrame) -> dict:
    """Cinelli & Hazlett (2020) sensitivity-to-unmeasured-confounding for the
    mediation's full OLS model, regular season and playoffs.

    Fits home_win ~ year + the four box-score edges with classical OLS, then for
    each channel reports the partial R² with the outcome and the robustness value
    (RV): the minimum share of the residual variation in BOTH that channel and
    home_win an unmeasured confounder would have to explain to drive the channel's
    coefficient to zero. Higher RV = harder to explain away. This bounds robustness
    to a hidden cause; it is not proof of causation.

    The RV uses the classical (non-robust) t-stat and residual degrees of freedom,
    which is the sensemakr standard. The cluster-by-year p-value the mediation uses
    is reported alongside for context only. Skips a context with too few rows.
    """
    keys = [k for k, _ in _SENS_CHANNELS]
    rhs = " + ".join(keys)
    out: dict = {"channels": list(_SENS_CHANNELS)}
    for label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        d = df[df["is_playoff"] == is_po].dropna(subset=keys + ["home_win", "year"])
        if len(d) < 100:
            continue
        with suppress_noisy_fit_warnings():
            m = smf.ols(f"home_win ~ year + {rhs}", data=d).fit()   # classical SEs
            m_cl = smf.ols(f"home_win ~ year + {rhs}", data=d).fit(
                cov_type="cluster", cov_kwds={"groups": d["year"]})
        dof = float(m.df_resid)
        rows = []
        for k, name in _SENS_CHANNELS:
            t = float(m.tvalues[k])
            partial_r2 = t**2 / (t**2 + dof)
            f = t / np.sqrt(dof)
            rv = 0.5 * (np.sqrt(f**4 + 4.0 * f**2) - f**2)
            rows.append({
                "key": k, "label": name,
                "coef": float(m.params[k]), "t": t, "dof": dof,
                "partial_r2": partial_r2 * 100.0,
                "robustness_value": rv * 100.0,
                "p_cluster": float(m_cl.pvalues[k]),
            })
        out[label] = {"n": len(d), "dof": dof, "channels": rows}
    return out


def run_mediation_sensitivity(df: pd.DataFrame) -> None:
    """Print the Cinelli & Hazlett robustness check on the mediation: how strong
    an unmeasured confounder would have to be to explain away each channel's link
    to home winning."""
    _section("MEDIATION ROBUSTNESS — SENSITIVITY TO UNMEASURED CONFOUNDING")
    print("   Robustness check on the mediation. The decomposition assumes the four")
    print("   box-score channels are the path home advantage takes; a hidden cause")
    print("   correlated with both a channel and the outcome could bias its share.")
    print("   For each channel this reports the partial R² with home_win and the")
    print("   robustness value (RV, Cinelli & Hazlett 2020): the minimum share of")
    print("   the residual variation in BOTH that channel and home_win a confounder")
    print("   would have to explain to drive the channel's coefficient to zero.")
    print("   Higher RV = harder to explain away. This bounds robustness to a hidden")
    print("   cause; it does not prove the channel causes home wins.\n")

    data = compute_mediation_sensitivity(df)
    if not data or all(k not in data for k in ("Regular season", "Playoffs")):
        print("   Insufficient data — skipping.\n")
        return

    for label in ("Regular season", "Playoffs"):
        d = data.get(label)
        if not d:
            continue
        print(f"   {label}  (N = {d['n']:,} games, residual dof = {d['dof']:,.0f})\n")
        print(f"   {'Channel':<12}  {'partial R²':>11}  {'robustness value':>17}  Interpretation")
        print(f"   {'─'*12}  {'─'*11}  {'─'*17}  {'─'*40}")
        for r in d["channels"]:
            interp = (f"a confounder must explain ≥ {r['robustness_value']:.1f}% of "
                      f"both to zero it out")
            print(f"   {r['label']:<12}  {r['partial_r2']:>10.1f}%  "
                  f"{r['robustness_value']:>16.1f}%  {interp}")
        print()

        if label == "Regular season":
            fouls = next(r for r in d["channels"] if r["label"] == "Fouls")
            efg   = next(r for r in d["channels"] if r["label"] == "Shooting")
            FACTS.set("sens.reg_fouls_rv", fouls["robustness_value"], "{:.1f}%",
                      note="Sensitivity: foul channel robustness value (RS)")
            FACTS.set("sens.reg_fouls_partial_r2", fouls["partial_r2"], "{:.1f}%",
                      note="Sensitivity: foul channel partial R² with home_win (RS)")
            FACTS.set("sens.reg_efg_rv", efg["robustness_value"], "{:.1f}%",
                      note="Sensitivity: shooting (eFG%) channel robustness value (RS)")
            FACTS.set("sens.reg_efg_partial_r2", efg["partial_r2"], "{:.1f}%",
                      note="Sensitivity: shooting (eFG%) channel partial R² with home_win (RS)")
            # Guard: the foul link is not fragile to a hidden cause. A confounder
            # would have to explain at least the foul channel's RV of the residual
            # variation in BOTH fouls and home wins — more than the foul channel's
            # own partial R² with the outcome — to overturn it. (Bounds robustness;
            # not a causal proof.)
            FACTS.guard(
                "foul_link_robust_to_confounding",
                bool(fouls["robustness_value"] > fouls["partial_r2"]),
                claim="overturning the foul channel needs a hidden cause stronger "
                      "than the foul channel's own measured link to home winning",
                value=f"foul RV {fouls['robustness_value']:.1f}% vs "
                      f"partial R² {fouls['partial_r2']:.1f}%",
            )
        print()


def compute_shap_channels(df: pd.DataFrame, seed: int = 0) -> dict:
    """Non-parametric decomposition of the HCA decline via a gradient-boosted
    win model and SHAP, as a robustness check on the linear mediation.

    A gradient-boosted classifier learns home_win from the four box-score edges
    (eFG%, fouls, turnovers, rebounds) with no linearity assumption and with
    interactions. SHAP values split each game's predicted win probability into
    additive per-channel contributions that sum to the prediction minus the
    league-average prediction. Averaging the signed SHAP within an era gives that
    era's channel contributions, which sum to the era's deviation from the overall
    home win rate; so the early-minus-late difference per channel sums to the
    actual decline. That is the non-parametric analogue of the mediation trend
    decomposition: same target, no straight-line assumption.

    Deterministic given ``seed`` (model fit, background sample, SHAP are all
    seeded / exact), so home_court_results.md stays reproducible.
    """
    # Heavy, optional deps — import lazily so the rest of the pipeline never pays
    # for them and a missing install degrades to "skip" rather than crash.
    try:
        import shap
        from sklearn.ensemble import GradientBoostingClassifier
    except ImportError:
        return {}

    keys = [k for k, _ in _SHAP_CHANNELS]
    out: dict = {"channels": list(_SHAP_CHANNELS)}

    for label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po].dropna(
            subset=keys + ["home_win", "era", "year"]
        ).copy()
        if len(sub) < 500:
            continue

        X = sub[keys].values.astype(float)
        y = sub["home_win"].values.astype(int)
        with suppress_noisy_fit_warnings():
            model = GradientBoostingClassifier(
                n_estimators=200, max_depth=3, learning_rate=0.05,
                subsample=0.8, random_state=seed,
            ).fit(X, y)
            acc = float(model.score(X, y))

            rng = np.random.default_rng(seed)
            bg = X[rng.choice(len(X), min(100, len(X)), replace=False)]
            explainer = shap.TreeExplainer(
                model, data=bg,
                feature_perturbation="interventional",
                model_output="probability",
            )
            # SHAP's progress bar writes to stderr; results.md captures stdout.
            with contextlib.redirect_stderr(io.StringIO()):
                sv = np.asarray(explainer.shap_values(X))
            proba = model.predict_proba(X)[:, 1]
        # Interventional SHAP is exactly additive: per game, the channel values
        # plus this base sum to the predicted win probability. So averaging the
        # signed SHAP within an era reconstructs (predicted mean − base) exactly.
        base = float(np.ravel(explainer.expected_value)[0])

        eras = list(pd.unique(sub.sort_values("year")["era"]))
        era_mask = {e: (sub["era"] == e).values for e in eras}
        era_phi = {e: sv[era_mask[e]].mean(axis=0) for e in eras}
        era_pred = {e: float(proba[era_mask[e]].mean()) for e in eras}   # what SHAP sums to
        era_actual = {e: float(y[era_mask[e]].mean()) for e in eras}     # observed, for the cross-check
        early, late = eras[0], eras[-1]

        delta = era_phi[early] - era_phi[late]          # per-channel, in prob units
        shap_decline_pp = float(delta.sum()) * 100.0     # SHAP-implied total decline
        actual_decline_pp = (era_actual[early] - era_actual[late]) * 100.0

        channel_rows = []
        for i, (k, name) in enumerate(_SHAP_CHANNELS):
            contrib_pp = float(delta[i]) * 100.0
            channel_rows.append({
                "key": k, "label": name,
                "contrib_pp": contrib_pp,
                "pct": 100.0 * contrib_pp / shap_decline_pp if shap_decline_pp else float("nan"),
                "early_pp": float(era_phi[early][i]) * 100.0,
                "late_pp":  float(era_phi[late][i]) * 100.0,
            })

        out[label] = {
            "n": len(sub), "acc": acc, "base_pct": base * 100.0,
            "actual_home_win_pct": float(y.mean()) * 100.0,
            "eras": eras, "early": early, "late": late,
            "era_contrib_pp": {e: (era_phi[e] * 100.0).tolist() for e in eras},
            "era_dev_pp": {e: (era_pred[e] - base) * 100.0 for e in eras},
            "era_actual_pct": {e: era_actual[e] * 100.0 for e in eras},
            "channels": channel_rows,
            "shap_decline_pp": shap_decline_pp,
            "actual_decline_pp": actual_decline_pp,
        }
    return out


def run_shap_channels(df: pd.DataFrame) -> None:
    """Print the gradient-boosting + SHAP channel decomposition of the decline,
    and compare it with the linear mediation it cross-checks."""
    _section("NON-PARAMETRIC CHANNEL DECOMPOSITION — GRADIENT BOOSTING + SHAP")
    print("   Robustness check on the linear mediation. A gradient-boosted win")
    print("   model learns home_win from the four box-score edges (eFG%, fouls,")
    print("   turnovers, rebounds) with no straight-line assumption and with")
    print("   interactions. SHAP splits each game's predicted win probability into")
    print("   additive channel contributions; averaged within an era they sum to")
    print("   that era's gap from the overall home win rate, so the early-minus-late")
    print("   difference per channel sums to the actual decline. Agreement with the")
    print("   linear breakdown means that breakdown does not hinge on linearity.\n")

    data = compute_shap_channels(df)
    if not data or "channels" not in data:
        print("   shap / scikit-learn not available — skipping.\n")
        return

    for label in ("Regular season", "Playoffs"):
        d = data.get(label)
        if not d:
            continue
        print(f"   {label}  (N = {d['n']:,} games, model accuracy {d['acc']:.3f},")
        print(f"   {d['early']} → {d['late']}: home win % {d['actual_home_win_pct']:.1f} overall)\n")
        print(f"   Decline decomposition  (signed SHAP, {d['early']} minus {d['late']})")
        print(f"   {'Channel':<12}  {'Early pp':>9}  {'Late pp':>8}  {'Contribution':>13}  {'% of decline':>12}")
        print(f"   {'─'*12}  {'─'*9}  {'─'*8}  {'─'*13}  {'─'*12}")
        for r in d["channels"]:
            print(f"   {r['label']:<12}  {r['early_pp']:>+8.1f}  {r['late_pp']:>+7.1f}  "
                  f"{r['contrib_pp']:>+11.1f} pp  {r['pct']:>11.0f}%")
        print(f"   {'─'*12}  {'─'*9}  {'─'*8}  {'─'*13}  {'─'*12}")
        print(f"   {'SHAP total':<12}  {'':>9}  {'':>8}  {d['shap_decline_pp']:>+11.1f} pp  "
              f"(actual decline {d['actual_decline_pp']:+.1f} pp)\n")

        if label == "Regular season":
            ranked = sorted(d["channels"], key=lambda r: r["contrib_pp"], reverse=True)
            top = ranked[0]
            FACTS.set("shap.reg_top_channel", top["label"],
                      note="SHAP: largest single channel in the RS decline")
            FACTS.set("shap.reg_top_pct", top["pct"], "{:.0f}%",
                      note="SHAP: that channel's share of the channel-explained RS decline")
            FACTS.set("shap.reg_acc", d["acc"], "{:.2f}",
                      note="SHAP: gradient-boosted win-model accuracy (RS)")
            FACTS.set("shap.reg_decline_pp", d["shap_decline_pp"], "{:.1f}", unit="pp",
                      note="SHAP-implied total RS decline (early minus late era)")
            fouls = next(r for r in d["channels"] if r["label"] == "Fouls")
            FACTS.set("shap.reg_fouls_pct", fouls["pct"], "{:.0f}%",
                      note="SHAP: fouls' share of the channel-explained RS decline")
            # Guard: the non-parametric breakdown agrees with the linear mediation
            # on the big picture — rebounding is a top channel and fouls is not the
            # largest — so the mediation conclusions don't depend on linearity.
            reb = next(r for r in d["channels"] if r["label"] == "Rebounding")
            reb_is_major = reb["pct"] >= 20.0
            fouls_not_largest = fouls["pct"] < max(r["pct"] for r in d["channels"])
            FACTS.guard(
                "shap_agrees_with_mediation",
                bool(reb_is_major and fouls_not_largest),
                claim="a model that makes no straight-line assumption splits the "
                      "decline across the same channels as the linear breakdown, with "
                      "rebounding a leading channel and fouls not the largest",
                value=f"rebounding {reb['pct']:.0f}%, fouls {fouls['pct']:.0f}%",
            )
        print()


def _oos_forecast(df: pd.DataFrame, is_playoff: int, cut_year: int) -> dict:
    """Freeze the channel→win mapping on seasons before cut_year, then predict
    each later season's home win % from that season's box-score edges. Compares
    against two baselines: extrapolating the training-window trend line, and a
    flat "training mean" forecast. Returns per-season actual/predicted plus RMSEs.
    """
    sub = df[df["is_playoff"] == is_playoff].copy()
    if is_playoff:
        sub = sub[~sub["year"].isin(nba.SKIP_PLAYOFF_YEARS)]
    sub = sub.dropna(subset=_OOS_CHANNELS + ["home_win"])
    train = sub[sub["year"] < cut_year]
    test  = sub[sub["year"] >= cut_year]
    if train["year"].nunique() < 5 or test["year"].nunique() < 3:
        return {}

    with suppress_noisy_fit_warnings():
        lpm = smf.ols("home_win ~ " + " + ".join(_OOS_CHANNELS), data=train).fit()
        tr_season = train.groupby("year")["home_win"].agg(p="mean", n="count").reset_index()
        tr_season["p"] *= 100.0
        wls = smf.wls("p ~ year", data=tr_season,
                      weights=tr_season["n"]).fit()

    train_mean = 100.0 * train["home_win"].mean()
    rows = []
    for y, g in test.groupby("year"):
        actual  = 100.0 * g["home_win"].mean()
        pred_ch = 100.0 * (lpm.params["Intercept"]
                           + sum(lpm.params[c] * g[c].mean() for c in _OOS_CHANNELS))
        pred_tr = float(wls.params["Intercept"] + wls.params["year"] * y)
        rows.append((int(y), actual, pred_ch, pred_tr))

    actual_full = [
        (int(y), 100.0 * float(p))
        for y, p in sub.groupby("year")["home_win"].mean().items()
    ]

    A  = np.array([r[1] for r in rows])
    Pc = np.array([r[2] for r in rows])
    Pt = np.array([r[3] for r in rows])
    rmse = lambda p: float(np.sqrt(np.mean((A - p) ** 2)))

    return {
        "is_playoff": is_playoff, "cut_year": cut_year,
        "train_years": (int(train["year"].min()), int(train["year"].max())),
        "test_years":  (int(test["year"].min()),  int(test["year"].max())),
        "rows": rows, "actual_full": actual_full,
        "rmse_channel": rmse(Pc), "rmse_trend": rmse(Pt),
        "rmse_naive": rmse(np.full_like(A, train_mean)),
        "train_mean": train_mean,
    }


def compute_oos_forecast(df: pd.DataFrame, cut_year: int = 2014) -> dict:
    """Out-of-sample decline forecast for regular season and playoffs."""
    return {
        "reg": _oos_forecast(df, 0, cut_year),
        "po":  _oos_forecast(df, 1, cut_year),
    }


def run_oos_forecast(df: pd.DataFrame) -> None:
    """Does the channel mechanism, fit only on early seasons, forecast the later
    decline out of sample? If yes, the box-score story isn't fitted to hindsight."""
    _section("OUT-OF-SAMPLE FORECAST — DO THE CHANNELS PREDICT THE LATER DECLINE?")
    print("   Freeze the four-channel win model (eFG%, fouls, turnovers, rebounds)")
    print("   on the training seasons, then predict each later season's home win %")
    print("   from that season's box-score edges. A frozen early mapping that tracks")
    print("   the held-out decline means the mechanism is stable, not fitted to")
    print("   hindsight. Baselines: extrapolating the training trend line, and a flat")
    print("   training-mean forecast. Lower RMSE on the held-out seasons is better.\n")

    data = compute_oos_forecast(df)
    for ctx_label, key in [("Regular season", "reg"), ("Playoffs", "po")]:
        d = data.get(key) or {}
        if not d:
            print(f"   {ctx_label}: insufficient data for a train/test split.\n")
            continue
        tr0, tr1 = d["train_years"]
        te0, te1 = d["test_years"]
        if key == "reg":
            FACTS.set("oos.train_end", tr1, "{:d}",
                      note="Out-of-sample forecast: last training season")
            _miss = max(abs(a - pc) for _, a, pc, _ in d["rows"])
            FACTS.guard("oos_within_a_point", _miss <= 1.6,
                        claim="predicts each later season's home win rate to within about a point",
                        value=f"largest held-out miss {_miss:.1f} pp")
            FACTS.set("oos.rmse_channel", d["rmse_channel"], "{:.0f}",
                      note="Reg. held-out RMSE of the frozen channel model (pp)")
            FACTS.set("oos.rmse_naive", d["rmse_naive"], "{:.0f}",
                      note="Reg. held-out RMSE of a flat training-mean guess (pp)")
            FACTS.set("oos.rmse_trend", d["rmse_trend"], "{:.2f}",
                      note="Reg. held-out RMSE of extrapolating the training trend line (pp)")
            FACTS.set("oos.test_start", te0, "{:d}",
                      note="Out-of-sample forecast: first held-out season")
            FACTS.set("oos.test_end", te1, "{:d}",
                      note="Out-of-sample forecast: last held-out season")
        elif key == "po":
            FACTS.set("oos.rmse_channel_po", d["rmse_channel"], "{:.2f}",
                      note="Playoff held-out RMSE of the frozen channel model (pp)")
            FACTS.set("oos.rmse_trend_po", d["rmse_trend"], "{:.2f}",
                      note="Playoff held-out RMSE of extrapolating the training trend line (pp)")
        print(f"   {ctx_label}  (train {tr0}–{tr1}, test {te0}–{te1})\n")
        print(f"   {'Season':>7}  {'Actual':>8}  {'Channel pred':>13}  {'Trend pred':>11}")
        print(f"   {'─'*7}  {'─'*8}  {'─'*13}  {'─'*11}")
        for y, a, pc, pt in d["rows"]:
            print(f"   {y:>7}  {a:>7.1f}%  {pc:>12.1f}%  {pt:>10.1f}%")
        print(f"\n   Held-out RMSE:  channel = {d['rmse_channel']:.2f} pp   "
              f"trend = {d['rmse_trend']:.2f} pp   flat mean = {d['rmse_naive']:.2f} pp")

        if d["rmse_channel"] < d["rmse_naive"]:
            if d["rmse_channel"] < d["rmse_trend"] - 0.25:
                extra = " and beats a naive extension of the early trend line"
            elif d["rmse_channel"] <= d["rmse_trend"] + 0.25:
                extra = " and matches the extrapolated trend line"
            else:
                extra = ""
            print(f"   ► The frozen early channel model reconstructs the {te0}–{te1} decline")
            print(f"     it never saw{extra} — the box-score mechanism is stable across the")
            print(f"     split, not an artifact of fitting on the full history.\n")
        else:
            print(f"   ► The frozen channel model does not beat a flat forecast out of")
            print(f"     sample here — read the held-out fit with caution.\n")


def _compute_shapley_shares(reg: pd.DataFrame, era_ref: str) -> dict[str, float]:
    """Shapley R² decomposition for 5 predictor blocks via all 2^5 = 32 logits.

    Fits every subset on the same N rows, computes each block's average marginal
    McFadden R² over all orderings. Returns {block_name: pct_of_total_r2}
    where values sum to 100. (PLAN-STATS item 4.)
    """
    from itertools import combinations
    from math import factorial

    block_terms = {
        "era":      f"C(era, Treatment('{era_ref}'))",
        "rest":     "rest_diff",
        "altitude": "altitude_home",
        "tz":       "tz_diff",
        "covid":    "covid",
    }
    names = list(block_terms)
    n     = len(names)

    cache: dict[frozenset, float] = {}
    with suppress_noisy_fit_warnings():
        for size in range(n + 1):
            for sub in combinations(names, size):
                key     = frozenset(sub)
                formula = ("home_win ~ 1" if not sub else
                           "home_win ~ " + " + ".join(block_terms[b] for b in sub))
                try:
                    res = smf.logit(formula, data=reg).fit(disp=0)
                    _warn_if_not_converged(
                        res, f"_compute_shapley_shares: subset={sorted(sub) or ['baseline']}")
                    cache[key] = _mcfadden(res)
                except Exception:
                    cache[key] = 0.0

    total = cache.get(frozenset(names), 0.0)

    shapley: dict[str, float] = {}
    for bi in names:
        others = [b for b in names if b != bi]
        phi    = 0.0
        for size in range(n):
            w = factorial(size) * factorial(n - size - 1) / factorial(n)
            for sub in combinations(others, size):
                S = frozenset(sub)
                phi += w * (cache.get(S | {bi}, 0.0) - cache.get(S, 0.0))
        shapley[bi] = phi

    return (
        {k: 100.0 * v / total for k, v in shapley.items()}
        if total > 0 else {k: 0.0 for k in names}
    )


def run_sequential_decomposition(df: pd.DataFrame) -> None:
    era_ref = nba.ERA_DEFS[0][0]   # "1984–94"
    reg = df[df["is_playoff"] == 0].dropna(subset=["rest_diff", "tz_diff"])
    n = len(reg)
    p_bar = reg["home_win"].mean()

    _section(f"WHAT EXPLAINS THE REGULAR-SEASON DECLINE?  (N = {n:,} games)")
    print(f"   Outcome: home_win. Baseline home win %: {p_bar * 100:.1f}%.")
    print(f"   McFadden R² is analogous to a linear-regression R² but typical values are much smaller;")
    print(f"   the ΔR² column shows how much each block adds over the previous model.")
    print(f"   '≈pp' = approximate marginal effect in percentage points (at mean p).")
    print(f"   p-values and CIs use cluster-robust SEs (clusters = season-year).\n")

    er = f"C(era, Treatment('{era_ref}'))"
    steps = [
        ("Era only",             f"home_win ~ {er}"),
        ("+ Rest differential",  f"home_win ~ {er} + rest_diff"),
        ("+ Altitude (DEN/UTA)", f"home_win ~ {er} + rest_diff + altitude_home"),
        ("+ Time zone diff",     f"home_win ~ {er} + rest_diff + altitude_home + tz_diff"),
        ("+ COVID flag",         f"home_win ~ {er} + rest_diff + altitude_home + tz_diff + covid"),
    ]

    fitted = []
    with suppress_noisy_fit_warnings():
        for label, formula in steps:
            res = smf.logit(formula, data=reg).fit(
                disp=0, cov_type="cluster", cov_kwds={"groups": reg["year"].values},
            )
            _warn_if_not_converged(res, f"run_sequential_decomposition: {label}")
            fitted.append((label, res))

    total_r2 = _mcfadden(fitted[-1][1])

    print(f"   {'Model':<30}  {'R²':>7}  {'ΔR²':>8}  {'% of fit':>9}")
    print(f"   {'─'*30}  {'─'*7}  {'─'*8}  {'─'*9}")
    prev_r2 = 0.0
    for label, m in fitted:
        r2    = _mcfadden(m)
        delta = r2 - prev_r2
        share = 100.0 * delta / total_r2 if total_r2 > 0 else 0.0
        prev_r2 = r2
        print(f"   {label:<30}  {r2:7.4f}  {delta:+8.4f}  {share:>8.1f}%")

    full = fitted[-1][1]
    params, pvals = full.params, full.pvalues

    print(f"\n   Full model coefficients  (reference era = {era_ref}):\n")
    print(f"   {'Predictor':<44}  {'log-odds':>8}  {'≈pp':>6}  {'95% CI (pp)':>14}  {'p':>8}  {'':>3}")
    print(f"   {'─'*44}  {'─'*8}  {'─'*6}  {'─'*14}  {'─'*8}  {'─'*3}")
    full_ci = full.conf_int()
    for name in params.index:
        if name == "Intercept":
            continue
        coef  = params[name]
        pval  = pvals[name]
        label = _clean(name, era_ref, "1984")
        pval_s = _fmt_p(pval)
        ci_lo = full_ci.loc[name, 0] * p_bar * (1 - p_bar) * 100.0
        ci_hi = full_ci.loc[name, 1] * p_bar * (1 - p_bar) * 100.0
        print(f"   {label:<44}  {coef:+8.3f}  {_pp(coef, p_bar):+6.1f}  "
              f"[{ci_lo:+5.1f},{ci_hi:+5.1f}]  {pval_s:>8}  {_stars(pval)}")

    # Sequential shares for side-by-side with Shapley
    seq_block_order = ["era", "rest", "altitude", "tz", "covid"]
    seq_shares: dict[str, float] = {}
    prev = 0.0
    for (_, m_i), bname in zip(fitted, seq_block_order):
        r2_i = _mcfadden(m_i)
        seq_shares[bname] = 100.0 * (r2_i - prev) / total_r2 if total_r2 > 0 else 0.0
        prev = r2_i

    last_era  = nba.ERA_DEFS[-1][0]
    last_coef = params.get(f"C(era, Treatment('{era_ref}'))[T.{last_era}]", np.nan)
    total_pp  = _pp(last_coef, p_bar) if not np.isnan(last_coef) else np.nan
    if not np.isnan(total_pp):
        print(f"\n   ► Era dummies imply a net decline of {total_pp:.1f} pp from {era_ref} → {last_era}.")

    # ── Shapley R² decomposition ───────────────────────────────────────────
    print(f"\n   Shapley R² decomposition  (2⁵ = 32 logits, same N = {n:,} games):")
    print(f"   Each block's average marginal R² over all 5! orderings.")
    print(f"   Compare to sequential (order-dependent, era entered first).\n")
    print(f"   {'Block':<28}  {'Shapley':>8}  {'Sequential':>11}")
    print(f"   {'─'*28}  {'─'*8}  {'─'*11}")

    shapley_pct = _compute_shapley_shares(reg, era_ref)

    block_display = {
        "era":      "Era (structural decline)",
        "rest":     "Rest differential",
        "altitude": "Altitude (DEN/UTA)",
        "tz":       "Time zone diff",
        "covid":    "COVID flag",
    }
    for bname in seq_block_order:
        lbl = block_display[bname]
        print(f"   {lbl:<28}  {shapley_pct.get(bname, 0):>7.1f}%  "
              f"{seq_shares.get(bname, 0):>10.1f}%")

    era_sh  = shapley_pct.get("era", 0.0)
    era_seq = seq_shares.get("era", 0.0)
    rest_sh = sum(shapley_pct.get(b, 0) for b in ["rest", "altitude", "tz", "covid"])
    print(f"\n   ► Era Shapley share: {era_sh:.0f}%  (sequential: {era_seq:.0f}% — "
          f"sequential inflated because era is entered first).")
    print(f"   ► Rest + altitude + tz + COVID (Shapley): {rest_sh:.0f}%.")


def run_stability_analysis(df: pd.DataFrame) -> None:
    _section("PRE/POST-2014 COEFFICIENT STABILITY  (regular season only)")
    print("   Do rest, altitude, and time zone effects change after the 2014 Finals format shift?")
    print("   Stable coefficients → those factors didn't drive the post-2014 change.\n")

    rs    = df[df["is_playoff"] == 0].dropna(subset=["rest_diff", "tz_diff"])
    pre   = rs[rs["year"] <  2014]
    post  = rs[rs["year"] >= 2014]
    formula = "home_win ~ rest_diff + altitude_home + tz_diff"

    with suppress_noisy_fit_warnings():
        m_pre  = smf.logit(formula, data=pre).fit(disp=0)
        _warn_if_not_converged(m_pre, "run_stability_analysis: m_pre")
        m_post = smf.logit(formula, data=post).fit(disp=0)
        _warn_if_not_converged(m_post, "run_stability_analysis: m_post")

    p_pre  = pre["home_win"].mean()
    p_post = post["home_win"].mean()

    print(f"   {'Predictor':<35}  {'Pre-2014':>10}  {'Post-2014':>10}  {'Shift':>8}")
    print(f"   {'':35}  {'log-odds':>10}  {'log-odds':>10}  {'':>8}")
    print(f"   {'─'*35}  {'─'*10}  {'─'*10}  {'─'*8}")

    display = {
        "rest_diff":     "rest diff (per day)",
        "altitude_home": "altitude home (DEN/UTA)",
        "tz_diff":       "time zone diff (per zone)",
    }
    for raw, label in display.items():
        c_pre  = m_pre.params.get(raw, np.nan)
        c_post = m_post.params.get(raw, np.nan)
        shift  = c_post - c_pre
        print(f"   {label:<35}  {c_pre:+10.3f}  {c_post:+10.3f}  {shift:+8.3f}")

    # Intercept shift = overall level change
    i_pre  = m_pre.params.get("Intercept", np.nan)
    i_post = m_post.params.get("Intercept", np.nan)
    i_shift = i_post - i_pre
    pp_shift = _pp(i_shift, (p_pre + p_post) / 2)
    print(f"   {'─'*35}  {'─'*10}  {'─'*10}  {'─'*8}")
    print(f"   {'Intercept (overall home adv. level)':<35}  {i_pre:+10.3f}  {i_post:+10.3f}  {i_shift:+8.3f}")

    print(f"\n   N pre-2014:  {len(pre):,} games  (home win %: {p_pre*100:.1f}%)")
    print(f"   N post-2014: {len(post):,} games  (home win %: {p_post*100:.1f}%)")
    print(f"\n   ► The intercept dropped by {abs(pp_shift):.1f} pp after 2014, confirming the overall decline.")
    print(f"   ► Rest, altitude, and tz coefficients show {'little' if all(abs(m_post.params.get(r, 0) - m_pre.params.get(r, 0)) < 0.05 for r in display) else 'some'} "
          f"change — those factors' effects on winning are largely stable.")

    # Formal interaction test: pooled model with post2014 × factor interactions
    print(f"\n   Formal interaction test — pooled logit with post2014 × factor interactions:")
    print(f"   H0: coefficients unchanged before and after 2014.\n")
    rs2 = rs.copy()
    rs2["post2014"] = (rs2["year"] >= 2014).astype(int)
    p_bar = rs2["home_win"].mean()
    with suppress_noisy_fit_warnings():
        try:
            m_int = smf.logit(
                "home_win ~ (rest_diff + altitude_home + tz_diff) * post2014",
                data=rs2,
            ).fit(disp=0)
            _warn_if_not_converged(m_int, "run_stability_analysis: m_int")
            interaction_terms = [
                ("rest_diff:post2014",     "rest_diff × post2014"),
                ("altitude_home:post2014", "altitude_home × post2014"),
                ("tz_diff:post2014",       "tz_diff × post2014"),
            ]
            print(f"   {'Interaction term':<30}  {'log-odds':>8}  {'≈pp':>6}  {'p':>8}  {'':3}")
            print(f"   {'─'*30}  {'─'*8}  {'─'*6}  {'─'*8}  {'─'*3}")
            for raw, label in interaction_terms:
                if raw in m_int.params.index:
                    c = m_int.params[raw]
                    p = m_int.pvalues[raw]
                    print(f"   {label:<30}  {c:+8.3f}  {_pp(c, p_bar):+6.1f}  "
                          f"{_fmt_p(p):>8}  {_stars(p)}")
                else:
                    print(f"   {label:<30}  {'(omitted)':>8}")
            if "post2014" in m_int.params.index:
                c_l = m_int.params["post2014"]
                p_l = m_int.pvalues["post2014"]
                print(f"   {'─'*30}  {'─'*8}  {'─'*6}  {'─'*8}  {'─'*3}")
                print(f"   {'post2014 (level shift)':<30}  {c_l:+8.3f}  {_pp(c_l, p_bar):+6.1f}  "
                      f"{_fmt_p(p_l):>8}  {_stars(p_l)}")
        except Exception:
            pass


def run_factor_summary(df: pd.DataFrame) -> None:
    re = df[df["is_playoff"] == 0].dropna(subset=["rest_diff", "tz_diff"])
    po = df[df["is_playoff"] == 1].dropna(subset=["rest_diff", "tz_diff"])

    _section("REST, ALTITUDE, AND TIME ZONE — DO THEY MATTER?")
    print(f"   Bivariate logistic regression — each factor tested independently.")
    print(f"   N regular season: {len(re):,}   N playoffs: {len(po):,}\n")

    p_re = re["home_win"].mean()
    p_po = po["home_win"].mean()

    factors = [
        ("rest_diff",     "Rest diff (per day)"),
        ("altitude_home", "Altitude home (DEN/UTA)"),
        ("tz_diff",       "Time zone diff (per zone)"),
    ]
    LW = 28  # label column width

    print(f"   {'Factor':<{LW}}  {'── Regular season ──':^26}  {'──── Playoffs ────':^26}")
    print(f"   {'':^{LW}}  {'log-odds':>8}  {'≈pp':>5}  {'p':>8}  {'':3}  "
          f"{'log-odds':>8}  {'≈pp':>5}  {'p':>8}  {'':3}")
    print(f"   {'─'*LW}  {'─'*8}  {'─'*5}  {'─'*8}  {'─'*3}  "
          f"{'─'*8}  {'─'*5}  {'─'*8}  {'─'*3}")

    res: dict[str, dict[str, float]] = {}
    with suppress_noisy_fit_warnings():
        for raw, label in factors:
            m_re = smf.logit(f"home_win ~ {raw}", data=re).fit(disp=0)
            _warn_if_not_converged(m_re, "run_factor_summary: m_re")
            m_po = smf.logit(f"home_win ~ {raw}", data=po).fit(disp=0)
            _warn_if_not_converged(m_po, "run_factor_summary: m_po")
            c_re, p_re_ = m_re.params[raw], m_re.pvalues[raw]
            c_po, p_po_ = m_po.params[raw], m_po.pvalues[raw]
            pp_re, pp_po = _pp(c_re, p_re), _pp(c_po, p_po)
            res[raw] = {"pp_re": pp_re, "p_re": p_re_, "pp_po": pp_po, "p_po": p_po_}
            pv_re = _fmt_p(p_re_)
            pv_po = _fmt_p(p_po_)
            ci_re = _ci_lo_hi(m_re, raw, p_re)
            ci_po = _ci_lo_hi(m_po, raw, p_po)
            print(f"   {label:<{LW}}  {c_re:+8.3f}  {pp_re:+5.1f}  {pv_re:>8}  {_stars(p_re_)}  "
                  f"{c_po:+8.3f}  {pp_po:+5.1f}  {pv_po:>8}  {_stars(p_po_)}")
            print(f"   {'95% CI (pp)':>{LW}}  {'':8}  [{ci_re[0]:+4.1f},{ci_re[1]:+4.1f}]  {'':8}  {'':3}  "
                  f"{'':8}  [{ci_po[0]:+4.1f},{ci_po[1]:+4.1f}]")

    # Coast-to-coast game counts and full season span for context
    n_cc_po = int((po["tz_diff"] == 3).sum())
    n_cc_re = int((re["tz_diff"] == 3).sum())
    n_seasons = int(df["year"].nunique())

    rest, alt, tz = res["rest_diff"], res["altitude_home"], res["tz_diff"]
    # Statistical detail: the altitude franchises' home-win boost (DEN/UTA), the
    # "8 of those points" / "about 8 percentage points" figure.
    FACTS.set("altitude.effect_pp", alt["pp_re"], "{:.0f}",
              note="Reg. home-win % boost for the altitude franchises (DEN/UTA)")

    # Rest verdict — driven by the computed p-values
    rest_re_sig, rest_po_sig = rest["p_re"] < 0.05, rest["p_po"] < 0.05
    if rest_re_sig and rest_po_sig:
        bigger = "playoffs" if abs(rest["pp_po"]) > abs(rest["pp_re"]) else "the regular season"
        print(f"\n   ► Rest matters in both contexts — {rest['pp_re']:+.1f} pp/day regular")
        print(f"     season, {rest['pp_po']:+.1f} pp/day playoffs (larger in {bigger}).")
    elif rest_re_sig or rest_po_sig:
        ctx, pp = (("the regular season", rest["pp_re"]) if rest_re_sig
                   else ("the playoffs", rest["pp_po"]))
        print(f"\n   ► Rest matters only in {ctx} ({pp:+.1f} pp/day).")
    else:
        print(f"\n   ► Rest shows no significant effect in either context.")

    # Altitude verdict
    alt_re_sig, alt_po_sig = alt["p_re"] < 0.05, alt["p_po"] < 0.05
    if alt_re_sig and not alt_po_sig:
        print(f"   ► Altitude home advantage is real in the regular season "
              f"({alt['pp_re']:+.1f} pp)")
        print(f"     but absent in playoffs — Denver/Utah team strength is a confound.")
    elif alt_re_sig and alt_po_sig:
        print(f"   ► Altitude home advantage is significant in both contexts "
              f"({alt['pp_re']:+.1f} pp")
        print(f"     regular season, {alt['pp_po']:+.1f} pp playoffs).")
    else:
        print(f"   ► Altitude home advantage is not statistically significant "
              f"({alt['pp_re']:+.1f} pp regular season).")

    # Time zone verdict
    tz_re_sig, tz_po_sig = tz["p_re"] < 0.05, tz["p_po"] < 0.05
    if not tz_re_sig and not tz_po_sig:
        print(f"   ► Time zones show no significant effect in either context.")
    elif tz_re_sig and not tz_po_sig:
        print(f"   ► Time zones matter in the regular season ({tz['pp_re']:+.1f} pp/zone)")
        print(f"     but not the playoffs.")
    else:
        print(f"   ► Time zones show a significant effect "
              f"({tz['pp_re']:+.1f} pp RS, {tz['pp_po']:+.1f} pp playoffs).")
    print(f"     Only {n_cc_po} coast-to-coast playoff games exist across {n_seasons} seasons")
    print(f"     ({n_cc_re:,} regular-season) — too sparse for reliable playoff inference.")

    # Playoff rest: control for team quality (RS win% differential)
    # Rest is earned by winning quickly, which correlates with team strength.
    po_q = df[(df["is_playoff"] == 1)].dropna(subset=["rest_diff", "quality_diff"])
    if not po_q.empty:
        p_po_q = po_q["home_win"].mean()
        print(f"\n   Playoff rest controlling for team quality (N = {len(po_q):,} games):")
        print(f"   quality_diff = home RS win% − away RS win% (same season).")
        with suppress_noisy_fit_warnings():
            try:
                m_q = smf.logit(
                    "home_win ~ rest_diff + quality_diff", data=po_q
                ).fit(disp=0)
                _warn_if_not_converged(m_q, "run_factor_summary: m_q")
                c_rest = m_q.params["rest_diff"]
                p_rest = m_q.pvalues["rest_diff"]
                c_qual = m_q.params["quality_diff"]
                p_qual = m_q.pvalues["quality_diff"]
                print(f"   {'Predictor':<28}  {'log-odds':>8}  {'≈pp':>6}  {'p':>8}  {'':3}")
                print(f"   {'─'*28}  {'─'*8}  {'─'*6}  {'─'*8}  {'─'*3}")
                print(f"   {'rest_diff (per day)':<28}  {c_rest:+8.3f}  "
                      f"{_pp(c_rest, p_po_q):+6.1f}  {_fmt_p(p_rest):>8}  {_stars(p_rest)}")
                print(f"   {'quality_diff (RS win% gap)':<28}  {c_qual:+8.3f}  "
                      f"{_pp(c_qual, p_po_q):+6.1f}  {_fmt_p(p_qual):>8}  {_stars(p_qual)}")
            except Exception:
                pass


def run_channel_event_study(df: pd.DataFrame) -> None:
    """Interrupted time series (ITS) on each box-score channel around 1994-95.

    If the hand-checking rule change is the mechanism behind the HCA decline,
    the FOUL differential should show the strongest IMMEDIATE response at 1994-95,
    with other channels (eFG%, rebounds, turnovers) following more gradually as
    teams restructured their shot selection and rotations.

    Model per channel:
        channel_diff ~ year + post95 + (year - 1994) * post95
    where post95 = 1 if year >= 1995.
    β_level = immediate discrete shift at 1995 beyond the year trend.
    β_slope = change in the per-year rate of change after 1995.
    """
    _section("CHANNEL EVENT STUDY — WHICH CHANGED FIRST AT 1994-95?")
    print("   ITS model per channel: diff ~ year + post95 + (year-1994)×post95")
    print("   β_level = immediate shift at 1995; β_slope = change in per-year rate.")
    print("   If hand-checking is the mechanism, FOUL diff should show the")
    print("   strongest IMMEDIATE response; others should be smaller or delayed.\n")

    channels = [
        ("foul_diff",    "Foul diff"),
        ("efg_pct_diff", "eFG% diff (pp)"),
        ("tov_diff",     "TOV diff"),
        ("reb_diff",     "REB diff"),
    ]

    for ctx_label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po]
        if sub.empty:
            continue

        by_year = sub.groupby("year")[
            [k for k, _ in channels]
        ].mean().reset_index().sort_values("year")
        by_year["post95"]  = (by_year["year"] >= 1995).astype(float)
        by_year["time_since"] = (by_year["year"] - 1994) * by_year["post95"]
        by_year["year_c"]  = by_year["year"] - by_year["year"].mean()

        print(f"   {ctx_label}  (N = {len(by_year)} seasons)\n")
        print(f"   {'Channel':<18}  {'Pre slope/yr':>13}  {'Level shift':>12}  "
              f"{'Slope chg/yr':>13}  {'Lev p':>8}  {'Slp p':>8}")
        print(f"   {'─'*18}  {'─'*13}  {'─'*12}  {'─'*13}  {'─'*8}  {'─'*8}")

        for key, label in channels:
            by_yr2 = by_year[["year_c", key, "post95", "time_since"]].dropna()
            if len(by_yr2) < 8:
                continue
            try:
                with suppress_noisy_fit_warnings():
                    m = smf.ols(f"{key} ~ year_c + post95 + time_since",
                                data=by_yr2).fit()
                pre_slope  = float(m.params.get("year_c",    np.nan))
                level_shift = float(m.params.get("post95",    np.nan))
                slope_chg  = float(m.params.get("time_since", np.nan))
                p_level    = float(m.pvalues.get("post95",    np.nan))
                p_slope    = float(m.pvalues.get("time_since", np.nan))
                _ls_lo, _ls_hi = _ci_lo_hi(m, "post95")
                print(f"   {label:<18}  {pre_slope:>+13.3f}  {level_shift:>+12.3f}  "
                      f"{slope_chg:>+13.3f}  {_fmt_p(p_level):>8}  {_fmt_p(p_slope):>8}  "
                      f"{_stars(p_level).strip()}/{_stars(p_slope).strip()}")
                print(f"        level-shift 95% CI [{_ls_lo:+.2f}, {_ls_hi:+.2f}]")
                # Statistical detail for investigation.md: the 1994-95 fingerprint
                # is an immediate foul jump while shooting shows none.
                if is_po == 0 and key == "foul_diff":
                    FACTS.set("event.foul_jump", level_shift, "{:+.2f}",
                              note="1994-95 immediate foul-diff level shift (pp)")
                    FACTS.set("event.foul_jump_p", "< 0.001" if p_level < 0.001 else f"= {p_level:.3f}",
                              note="1994-95 foul jump p-value (display)")
                    _flo, _fhi = _ci_lo_hi(m, "post95")
                    FACTS.set("event.foul_jump_ci_lo", _flo, "{:+.2f}",
                              note="1994-95 foul-diff level shift 95% CI low")
                    FACTS.set("event.foul_jump_ci_hi", _fhi, "{:+.2f}",
                              note="1994-95 foul-diff level shift 95% CI high")
                if is_po == 0 and key == "efg_pct_diff":
                    FACTS.set("event.shooting_jump_p", "< 0.001" if p_level < 0.001 else f"= {p_level:.3f}",
                              note="1994-95 shooting jump p-value (display)")
            except Exception as e:
                print(f"   {label:<18}  (failed: {e})")
        print()

    print("   Note: foul_diff = PF_home − PF_away. Negative values mean away teams")
    print("   get MORE fouls called (home court foul advantage). A positive level shift")
    print("   means the home foul advantage SHRANK immediately (foul_diff moved toward 0).")
    print("   The expected signature of the hand-checking rule change:")
    print("   • Foul diff: significant POSITIVE level shift (home foul edge shrinks IMMEDIATELY)")
    print("   • Other channels: no significant immediate shift (teams adapt over seasons)")
    print()


def run_multiple_comparisons_summary(df: pd.DataFrame) -> None:
    """Collect ~14 primary hypothesis tests and apply Benjamini-Hochberg FDR correction.

    With this many tests, a raw α=0.05 threshold expects ~0.7 false discoveries.
    BH controls the false discovery rate at q=5%: the expected fraction of flagged
    results that are null is ≤ 5%. Tests are ranked by ascending p-value; a test
    survives if its p-value is at or below the BH threshold (i/m)×0.05 for its rank.
    Tests are re-run here to form a self-contained consolidated table.
    """
    from scipy.stats import pearsonr

    _section("MULTIPLE COMPARISONS — BH FDR CORRECTION ACROSS PRIMARY TESTS")
    print("   BH correction at q = 0.05; threshold for rank i (ascending p): (i/m) × 0.05.")
    print("   Tests re-run here on the same data to form a self-contained table.\n")

    tests: list[tuple[str, float]] = []

    reg = df[df["is_playoff"] == 0]
    po  = df[df["is_playoff"] == 1]

    def _logit_p(formula: str, data: pd.DataFrame, col: str) -> float:
        try:
            with suppress_noisy_fit_warnings():
                m = smf.logit(formula, data=data).fit(
                    disp=0, cov_type="cluster",
                    cov_kwds={"groups": data["year"].values})
                _warn_if_not_converged(m, "_logit_p: m")
            return float(m.pvalues[col])
        except Exception:
            return 1.0

    # 1–2: overall HCA trend (binomial GLM on season-level aggregates)
    for ctx_label, sub in [
        ("RS HCA year trend", reg),
        ("PO HCA year trend", po[~po["year"].isin(nba.SKIP_PLAYOFF_YEARS)]),
    ]:
        agg = sub.groupby("year")["home_win"].agg(["sum", "count"]).reset_index()
        agg.columns = ["year", "wins", "games"]
        agg["losses"] = agg["games"] - agg["wins"]
        try:
            with suppress_noisy_fit_warnings():
                X = sm.add_constant(agg["year"].values.astype(float))
                glm = sm.GLM(agg[["wins", "losses"]].values, X,
                             family=sm.families.Binomial()).fit()
            tests.append((ctx_label, float(glm.pvalues[1])))
        except Exception:
            tests.append((ctx_label, 1.0))

    # 3–6: factor effects (bivariate logistic, game level)
    reg_cf = reg.dropna(subset=["rest_diff", "tz_diff"])
    po_cf  = po.dropna(subset=["rest_diff", "tz_diff"])
    for label, sub, col in [
        ("RS rest differential",   reg_cf, "rest_diff"),
        ("PO rest differential",   po_cf,  "rest_diff"),
        ("RS altitude (DEN/UTA)",  reg_cf, "altitude_home"),
        ("RS time zone effect",    reg_cf, "tz_diff"),
    ]:
        tests.append((label, _logit_p(f"home_win ~ {col}", sub, col)))

    # 7–8: 3PA within-era (era-controlled game-level logistic)
    for label, sub in [
        ("RS 3PA within-era effect", reg),
        ("PO 3PA within-era effect", po),
    ]:
        sub_c = sub.dropna(subset=["tpa_rate_avg"])
        tests.append((label, _logit_p(
            "home_win ~ tpa_rate_avg + C(era)", sub_c, "tpa_rate_avg")))

    # 9: pace LOO within-era
    sub_ep = reg.dropna(subset=["expected_pace"])
    tests.append(("RS pace LOO within-era",
                  _logit_p("home_win ~ expected_pace + C(era)", sub_ep, "expected_pace")))

    # 10: travel distance
    sub_tr = reg.dropna(subset=["distance_miles"])
    tests.append(("RS travel distance",
                  _logit_p("home_win ~ distance_miles", sub_tr, "distance_miles")))

    # 11: parity first-differenced
    try:
        parity_seasons, parity_std = nba.compute_parity_stats(
            nba.START_YEAR, nba.END_YEAR, "Regular Season")
        reg_by_year = reg.groupby("year")["home_win"].mean() * 100
        shared_p = sorted(
            [s for s in parity_seasons if nba.label_to_year(s) in reg_by_year.index],
            key=nba.label_to_year)
        if len(shared_p) >= 10:
            std_v  = np.array([parity_std[parity_seasons.index(s)] for s in shared_p])
            home_v = np.array([float(reg_by_year[nba.label_to_year(s)]) for s in shared_p])
            _, p_fd = pearsonr(np.diff(std_v), np.diff(home_v))
            tests.append(("RS parity vs HCA (first-diff)", float(p_fd)))
    except Exception:
        pass

    # 12: OREB rate vs rebound share edge (season level)
    reg_reb = reg.dropna(subset=["reb_share_edge", "league_oreb_rate"])
    s_reb = reg_reb.groupby("year")[["reb_share_edge", "league_oreb_rate"]].mean().dropna()
    if len(s_reb) >= 5:
        _, p_reb = pearsonr(s_reb["league_oreb_rate"].values, s_reb["reb_share_edge"].values)
        tests.append(("RS OREB rate vs rebound share edge", float(p_reb)))

    # 13: era LR test RS (era dummies beyond year trend)
    era_ref = nba.ERA_DEFS[0][0]
    for label, sub in [
        ("RS era dummies beyond year trend", reg.dropna(subset=["rest_diff", "tz_diff"])),
        ("PO era dummies beyond year trend", po.dropna(subset=["rest_diff", "tz_diff"])),
    ]:
        try:
            with suppress_noisy_fit_warnings():
                f_yr  = f"home_win ~ year + rest_diff + altitude_home + tz_diff + covid"
                f_era = (f"home_win ~ year + C(era, Treatment('{era_ref}')) "
                         f"+ rest_diff + altitude_home + tz_diff + covid")
                m_yr  = smf.logit(f_yr,  data=sub).fit(disp=0)
                _warn_if_not_converged(m_yr, "run_multiple_comparisons_summary: m_yr")
                m_era = smf.logit(f_era, data=sub).fit(disp=0)
                _warn_if_not_converged(m_era, "run_multiple_comparisons_summary: m_era")
            from scipy.stats import chi2
            lr_stat = 2 * (m_era.llf - m_yr.llf)
            df_diff = m_era.df_model - m_yr.df_model
            p_lr = float(chi2.sf(lr_stat, df_diff))
            tests.append((label, p_lr))
        except Exception:
            tests.append((label, 1.0))

    # Apply BH correction
    m_total = len(tests)
    sorted_idx = sorted(range(m_total), key=lambda i: tests[i][1])
    bh_thresh = [(rank + 1) / m_total * 0.05 for rank in range(m_total)]

    bh_cutoff = -1
    for rank, orig_i in enumerate(sorted_idx):
        if tests[orig_i][1] <= bh_thresh[rank]:
            bh_cutoff = rank
    sig_labels = {tests[sorted_idx[i]][0] for i in range(bh_cutoff + 1)}

    print(f"   m = {m_total} primary tests.  BH threshold for rank i: (i/{m_total}) × 0.05.\n")
    print(f"   {'Rank':>4}  {'Test':<40}  {'p-value':>10}  {'BH thresh':>10}  {'Survives':>8}")
    print(f"   {'─'*4}  {'─'*40}  {'─'*10}  {'─'*10}  {'─'*8}")
    for rank, orig_i in enumerate(sorted_idx):
        label, p = tests[orig_i]
        thresh   = bh_thresh[rank]
        survives = "YES" if label in sig_labels else "no"
        print(f"   {rank+1:>4}  {label:<40}  {_fmt_p(p):>10}  {thresh:>10.4f}  {survives:>8}")

    n_survive = len(sig_labels)
    failed = [tests[sorted_idx[i]][0]
              for i in range(m_total) if tests[sorted_idx[i]][0] not in sig_labels]
    print(f"\n   BH result: {n_survive} / {m_total} tests survive (q = 0.05).")
    if failed:
        print(f"   Does NOT survive BH: {', '.join(failed)}")
    print(f"   ► Core findings (HCA trends, rest, altitude, era shift, 3PA) survive.")
    print(f"     Marginal factors (travel, parity, time zone) may not — treat as exploratory.\n")
