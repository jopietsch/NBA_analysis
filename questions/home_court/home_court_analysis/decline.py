"""Section 1 (The 40-Year Decline): trend, structural break / CUSUM / Bayesian
changepoint, multilevel decline, HCA forecast, era comparison, interrupted
time series, and the rule-change placebo test."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf

from nbakit.textfmt import stars as _stars, p_value as _fmt_p
from nbakit.stats import shrink_to_mean

import home_court_data as nba
from home_court_facts import FACTS

from ._helpers import (
    suppress_noisy_fit_warnings, _warn_if_not_converged,
    _section, _pp, _ci_lo_hi,
)

def run_decline_trend(df: pd.DataFrame) -> None:
    """Trend line for home_win_pct ~ year at the season level — formally tests the decline."""
    _section("THE OVERALL DECLINE — IS IT STATISTICALLY REAL?")
    print("   Primary: binomial GLM (events/trials per season, weights by game count).")
    print("   Cross-check: OLS with Newey–West HAC SEs (maxlags=1).")
    print("   Per-era slopes use same methods on era subsets.\n")

    for ctx_label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po]
        agg = sub.groupby("year")["home_win"].agg(["sum", "count"]).reset_index()
        agg.columns = ["year", "wins", "games"]
        agg["year"] = agg["year"].astype(int)
        agg["pct"] = agg["wins"] / agg["games"] * 100
        if is_po:
            agg = agg[~agg["year"].isin(nba.SKIP_PLAYOFF_YEARS)]
        agg = agg.sort_values("year").reset_index(drop=True)
        if len(agg) < 3:
            continue

        yr_min, yr_max = int(agg["year"].min()), int(agg["year"].max())
        exog = sm.add_constant(agg["year"].values.astype(float))
        endog = agg[["wins", "games"]].copy()
        endog["losses"] = endog["games"] - endog["wins"]

        with suppress_noisy_fit_warnings():
            # Binomial GLM — primary
            glm = sm.GLM(
                endog[["wins", "losses"]].values,
                exog,
                family=sm.families.Binomial(),
            ).fit()
            # OLS with HAC SEs — cross-check
            ols_base = smf.ols("pct ~ year", data=agg).fit()
            ols_hac = ols_base.get_robustcov_results(cov_type="HAC", maxlags=1)

        # Binomial GLM reports slope in log-odds; convert to pp at the mean
        p_bar_frac = agg["pct"].mean() / 100.0
        glm_coef_lo = glm.params[1]
        glm_pp = glm_coef_lo * p_bar_frac * (1 - p_bar_frac) * 100.0
        glm_p = glm.pvalues[1]
        glm_total_lo = glm_coef_lo * (yr_max - yr_min)
        glm_total_pp = glm_total_lo * p_bar_frac * (1 - p_bar_frac) * 100.0
        glm_ci = glm.conf_int()         # numpy ndarray shape (n_params, 2)
        glm_ci_lo = glm_ci[1, 0] * p_bar_frac * (1 - p_bar_frac) * 100.0
        glm_ci_hi = glm_ci[1, 1] * p_bar_frac * (1 - p_bar_frac) * 100.0

        ols_coef = ols_base.params["year"]    # HAC doesn't change coefficients
        ols_p = ols_hac.pvalues[1]            # numpy array: 0=Intercept, 1=year
        ols_total = ols_coef * (yr_max - yr_min)
        ols_ci = ols_base.conf_int()
        ols_ci_lo = float(ols_ci.loc["year", 0])
        ols_ci_hi = float(ols_ci.loc["year", 1])

        print(f"   {ctx_label}  ({len(agg)} seasons, {yr_min}–{yr_max})")
        print(f"   Binomial GLM: {glm_pp:+.3f} pp/yr  95% CI [{glm_ci_lo:+.3f}, {glm_ci_hi:+.3f}]  "
              f"(p = {_fmt_p(glm_p)}  {_stars(glm_p).strip()},  total ≈ {glm_total_pp:+.1f} pp)")
        print(f"   OLS / HAC:    {ols_coef:+.3f} pp/yr  95% CI [{ols_ci_lo:+.3f}, {ols_ci_hi:+.3f}]  "
              f"(p = {_fmt_p(ols_p)}  {_stars(ols_p).strip()},  R² = {ols_base.rsquared:.3f},  total: {ols_total:+.1f} pp)\n")

        # ── Facts for the prose docs (findings/summary §1: the decline) ──
        # Exact figures feed the data model; the *_plain facts carry the
        # editorially-rounded wording used in the prose. The plain strings are
        # authored here, next to the exact values, so the wording can be
        # re-judged whenever the underlying number moves.
        ctx = "po" if is_po else "reg"
        fit_start = float(ols_base.predict(pd.DataFrame({"year": [yr_min]})).iloc[0])
        recent_avg = float(agg["pct"].tail(5).mean())
        FACTS.set(f"{ctx}.hw_first", fit_start, "{:.1f}%",
                  note=f"{ctx_label}: trend-fit home-win% at the start ({yr_min})")
        FACTS.set(f"{ctx}.hw_last", recent_avg, "{:.1f}%",
                  note=f"{ctx_label}: home-win% averaged over the last 5 seasons")
        FACTS.set(f"{ctx}.decline_total", glm_total_pp, "{:+.1f} pp",
                  note=f"{ctx_label}: modeled total decline (binomial GLM)")
        FACTS.set(f"{ctx}.hw_first_plain", "68%" if is_po else "65%",
                  note="prose rounding of hw_first")
        FACTS.set(f"{ctx}.hw_last_plain", "58%" if is_po else "55%",
                  note="prose rounding of hw_last")

        # Statistical detail for investigation.md (binomial GLM slope, CI, p).
        FACTS.set(f"{ctx}.slope", glm_pp, "{:+.2f}",
                  note=f"{ctx_label}: decline slope (binomial GLM, pp/yr)")
        FACTS.set(f"{ctx}.slope_mag", abs(glm_pp), "{:.2f}",
                  note=f"{ctx_label}: decline slope magnitude (pp/yr)")
        FACTS.set(f"{ctx}.slope_ci_lo", glm_ci_lo, "{:+.2f}",
                  note=f"{ctx_label}: decline slope 95% CI low")
        FACTS.set(f"{ctx}.slope_ci_hi", glm_ci_hi, "{:+.2f}",
                  note=f"{ctx_label}: decline slope 95% CI high")
        FACTS.set(f"{ctx}.slope_p", "< 0.001" if glm_p < 0.001 else f"= {glm_p:.3f}",
                  note=f"{ctx_label}: decline slope p-value (display)")
        FACTS.set(f"{ctx}.ols_r2", ols_base.rsquared, "{:.2f}",
                  note=f"{ctx_label}: OLS R² of season home-win% on year")

        if not is_po:
            FACTS.set("decline_both_plain", "10 percentage points",
                      note="both regular season and playoffs fell ~10 pp")
            FACTS.set("reg.slope_plain", "a quarter of a point",
                      note=f"prose phrasing of the reg-season slope ({glm_pp:+.3f} pp/yr)")
            FACTS.set("reg.slope_r2_plain", "three-quarters",
                      note=f"prose phrasing of reg R² ({ols_base.rsquared:.3f})")
            FACTS.set("reg.hw_mid90s",
                      float(agg[(agg["year"] >= 1995) & (agg["year"] <= 2001)]["pct"].mean()),
                      "{:.0f}%", note="Reg. season home-win %, 1995–2001 (the mid-90s level)")
        else:
            FACTS.set("po.slope_r2_plain", "a fifth",
                      note=f"prose phrasing of playoff R² ({ols_base.rsquared:.3f})")
            _plateau = agg[(agg["year"] >= 2005) & (agg["year"] <= 2017)]["pct"].mean()
            FACTS.set("po.hw_plateau", float(_plateau), "{:.0f}%",
                      note="Playoffs: home-win% plateau across 2005–2017")
            FACTS.set("po.hw_2018",
                      float(agg[(agg["year"] >= 2018) & (agg["year"] <= 2022)]["pct"].mean()),
                      "{:.0f}%", note="Playoffs: home-win %, 2018–2022")

        print(f"   {'Era':<12}  {'N':>4}  {'GLM pp/yr':>10}  {'GLM p':>8}  "
              f"{'OLS pp/yr':>10}  {'HAC p':>8}  {'':3}")
        print(f"   {'─'*12}  {'─'*4}  {'─'*10}  {'─'*8}  {'─'*10}  {'─'*8}  {'─'*3}")
        for era_label, y1, y2, _ in nba.ERA_DEFS:
            era_rows = agg[(agg["year"] >= y1) & (agg["year"] <= y2)]
            n = len(era_rows)
            if n < 3:
                print(f"   {era_label:<12}  {n:>4}  {'(too few)':>10}")
                continue
            era_exog = sm.add_constant(era_rows["year"].values.astype(float))
            era_endog = era_rows[["wins"]].copy()
            era_endog["losses"] = era_rows["games"] - era_rows["wins"]
            era_pbar = era_rows["pct"].mean() / 100.0
            with suppress_noisy_fit_warnings():
                era_glm = sm.GLM(
                    era_endog[["wins", "losses"]].values,
                    era_exog,
                    family=sm.families.Binomial(),
                ).fit()
                era_ols_base = smf.ols("pct ~ year", data=era_rows).fit()
                era_ols_hac = era_ols_base.get_robustcov_results(cov_type="HAC", maxlags=1)
            gc = era_glm.params[1] * era_pbar * (1 - era_pbar) * 100.0
            gp = era_glm.pvalues[1]
            oc = era_ols_base.params["year"]
            op = era_ols_hac.pvalues[1]
            print(f"   {era_label:<12}  {n:>4}  {gc:>+10.3f}  {_fmt_p(gp):>8}  "
                  f"{oc:>+10.3f}  {_fmt_p(op):>8}  {_stars(gp)}")
            if n <= 4:
                print(f"   {'':12}  {'':4}  ⚠ n={n}: too few seasons — treat as illustrative only")
        print()


def run_structural_break_test(df: pd.DataFrame, results: dict | None = None) -> None:
    """QLR (supremum Chow) test for structural breaks in the HCA time series.

    Finds the year with the strongest statistical evidence for a shift in level
    or slope. Runs a Chow F-test at every candidate year (outer 15% trimmed for
    minimum sub-sample reliability) and reports the supremum F statistic.
    Asymptotic critical values from Andrews (1993), k=2 parameters, π₀=0.15:
    10% → 7.12  |  5% → 8.85  |  1% → 12.37.
    The conditional p-values (from the F distribution) assume the break year is
    known in advance — they are conservative; the QLR critical values above are
    the correct simultaneous-inference benchmarks.
    """
    from numpy.linalg import lstsq as _lstsq
    from scipy.stats import f as _f_dist

    _section("STRUCTURAL BREAK TEST — WHERE DID THE DECLINE SHIFT?")
    print("   QLR supremum Chow F: Chow test at every candidate year, outer 15% trimmed.")
    print("   Conditional p-values assume the break year is known (single-test reference).")
    print("   Andrews (1993) QLR critical values, k=2, π₀=0.15:")
    print("   10% → 7.12  |  5% → 8.85  |  1% → 12.37\n")

    QLR_CV = {0.10: 7.12, 0.05: 8.85, 0.01: 12.37}

    for ctx_label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po]
        agg = sub.groupby("year")["home_win"].agg(["sum", "count"]).reset_index()
        agg.columns = ["year", "wins", "games"]
        agg["pct"] = agg["wins"] / agg["games"] * 100
        if is_po:
            agg = agg[~agg["year"].isin(nba.SKIP_PLAYOFF_YEARS)]
        agg = agg.sort_values("year").reset_index(drop=True)
        n = len(agg)
        if n < 10:
            continue

        y = agg["pct"].values.astype(float)
        x = agg["year"].values.astype(float)
        trim = max(3, int(np.ceil(0.15 * n)))

        X_full = np.column_stack([np.ones(n), x])
        b_full = _lstsq(X_full, y, rcond=None)[0]
        rss_full = float(np.sum((y - X_full @ b_full) ** 2))

        rows = []
        for k in range(trim, n - trim):
            y1, x1 = y[:k], x[:k]
            y2, x2 = y[k:], x[k:]
            X1 = np.column_stack([np.ones(len(y1)), x1])
            X2 = np.column_stack([np.ones(len(y2)), x2])
            b1 = _lstsq(X1, y1, rcond=None)[0]
            b2 = _lstsq(X2, y2, rcond=None)[0]
            rss12 = float(np.sum((y1 - X1 @ b1) ** 2) + np.sum((y2 - X2 @ b2) ** 2))
            K_p = 2
            chow_f = ((rss_full - rss12) / K_p) / (rss12 / (n - 2 * K_p))
            cond_p = float(_f_dist.sf(chow_f, K_p, n - 2 * K_p))
            rows.append({
                "year": int(agg.iloc[k]["year"]),
                "F": chow_f,
                "cond_p": cond_p,
                "sl_pre": b1[1],
                "sl_post": b2[1],
            })

        if not rows:
            continue
        rows.sort(key=lambda r: -r["F"])
        best = rows[0]

        if results is not None:
            key = "break_rs" if is_po == 0 else "break_po"
            results[key] = {
                "year": best["year"],
                "sl_pre": best["sl_pre"],
                "sl_post": best["sl_post"],
                "F": best["F"],
            }

        qlr_sig = (
            "p < 1%  ***" if best["F"] >= QLR_CV[0.01] else
            "p < 5%   **" if best["F"] >= QLR_CV[0.05] else
            "p < 10%   *" if best["F"] >= QLR_CV[0.10] else
            "n.s. at 10%"
        )

        print(f"   {ctx_label}  (N = {n} seasons, candidates: "
              f"{int(x[trim])}–{int(x[n - trim - 1])})")
        print(f"   Supremum Chow F = {best['F']:.2f}  at year {best['year']}  [{qlr_sig}]")
        print(f"   Subperiod slopes:  before {best['year']}: {best['sl_pre']:+.3f} pp/yr  |  "
              f"after {best['year']}: {best['sl_post']:+.3f} pp/yr")
        # Facts for stats_explainer.md §2 (structural break).
        _sbc = "po" if "Playoff" in ctx_label else "reg"
        FACTS.set(f"sb.{_sbc}_f", best["F"], "{:.2f}", note=f"{ctx_label}: QLR supremum Chow F")
        FACTS.set(f"sb.{_sbc}_break", int(best["year"]), "{:d}", note=f"{ctx_label}: data-implied break year")
        FACTS.set(f"sb.{_sbc}_slope_before", best["sl_pre"], "{:+.2f}", note=f"{ctx_label}: slope before the break (pp/yr)")
        FACTS.set(f"sb.{_sbc}_slope_after", best["sl_post"], "{:+.2f}", note=f"{ctx_label}: slope after the break (pp/yr)")

        print(f"\n   Top candidate break years:")
        print(f"   {'Year':>6}  {'Chow F':>8}  {'Cond. p':>10}  {'Slope before':>13}  {'Slope after':>12}")
        print(f"   {'─'*6}  {'─'*8}  {'─'*10}  {'─'*13}  {'─'*12}")
        for row in rows[:5]:
            print(f"   {row['year']:>6}  {row['F']:>8.2f}  {_fmt_p(row['cond_p']):>10}  "
                  f"{row['sl_pre']:>+13.3f}  {row['sl_post']:>+12.3f}")

        # Bootstrap 95% CI for break year (residual resampling from 2-segment model)
        K_p = 2
        k_break = next(
            (k for k in range(trim, n - trim) if int(agg.iloc[k]["year"]) == best["year"]),
            None,
        )
        if k_break is not None:
            B = 500
            X1_fit = np.column_stack([np.ones(k_break), x[:k_break]])
            X2_fit = np.column_stack([np.ones(n - k_break), x[k_break:]])
            b1_fit = _lstsq(X1_fit, y[:k_break], rcond=None)[0]
            b2_fit = _lstsq(X2_fit, y[k_break:], rcond=None)[0]
            fitted = np.concatenate([X1_fit @ b1_fit, X2_fit @ b2_fit])
            residuals = y - fitted
            rng_b = np.random.default_rng(42)
            boot_yrs: list[int] = []
            X_full = np.column_stack([np.ones(n), x])
            for _ in range(B):
                y_boot = fitted + rng_b.choice(residuals, size=n, replace=True)
                b_full = _lstsq(X_full, y_boot, rcond=None)[0]
                rss_f = float(np.sum((y_boot - X_full @ b_full) ** 2))
                best_f_b, best_yr_b = -np.inf, int(x[trim])
                for kb in range(trim, n - trim):
                    X1b = np.column_stack([np.ones(kb), x[:kb]])
                    X2b = np.column_stack([np.ones(n - kb), x[kb:]])
                    b1b = _lstsq(X1b, y_boot[:kb], rcond=None)[0]
                    b2b = _lstsq(X2b, y_boot[kb:], rcond=None)[0]
                    rss12b = (float(np.sum((y_boot[:kb] - X1b @ b1b) ** 2))
                              + float(np.sum((y_boot[kb:] - X2b @ b2b) ** 2)))
                    cf = ((rss_f - rss12b) / K_p) / (rss12b / (n - 2 * K_p))
                    if cf > best_f_b:
                        best_f_b, best_yr_b = cf, int(x[kb])
                boot_yrs.append(best_yr_b)
            boot_yrs.sort()
            ci_lo_b = boot_yrs[int(0.025 * B)]
            ci_hi_b = boot_yrs[int(0.975 * B)]
            print(f"\n   Bootstrap 95% CI for break year (B={B} residual resamples): "
                  f"[{ci_lo_b}, {ci_hi_b}]")
            if best["F"] >= QLR_CV[0.05]:
                print(f"   ► Break is robustly in {ci_lo_b}–{ci_hi_b}: supports 'late 1990s'")
                print(f"     framing; no single year can be pinpointed with precision.")
            else:
                print(f"   ► Break not significant; CI of [{ci_lo_b}, {ci_hi_b}] is wide")
                print(f"     and unreliable — no stable break location to report.")
        print()


def run_cusum_test(df: pd.DataFrame, results: dict | None = None) -> None:
    """CUSUM (Brown-Durbin-Evans) parameter-stability test — complements the QLR.

    Builds cumulative recursive residuals from the linear trend and tests whether
    they exceed the 5% critical band. The QLR asks 'where is the single strongest
    break?'; CUSUM asks 'does the trend ever show sustained instability anywhere?'
    Agreement between both tests increases confidence in the finding.
    """
    from statsmodels.regression.recursive_ls import RecursiveLS

    _section("CUSUM TEST — PARAMETER STABILITY  (complement to structural break test above)")
    print("   CUSUM (Brown-Durbin-Evans): cumulative recursive residuals from the linear")
    print("   trend. Exit from the 5% critical band = structural instability detected.")
    print("   QLR (§1b) finds the single strongest break; CUSUM tests global stability.")
    print("   Agreement → increased confidence; discrepancy → worth investigating.\n")

    for ctx_label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po]
        agg = sub.groupby("year")["home_win"].agg(["sum", "count"]).reset_index()
        agg.columns = ["year", "wins", "games"]
        agg["pct"] = agg["wins"] / agg["games"] * 100
        if is_po:
            agg = agg[~agg["year"].isin(nba.SKIP_PLAYOFF_YEARS)]
        agg = agg.sort_values("year").reset_index(drop=True)
        if len(agg) < 10:
            continue

        y = agg["pct"].values.astype(float)
        x = agg["year"].values.astype(float)
        X = np.column_stack([np.ones(len(y)), x])

        try:
            # Center years for numerical stability
            x_c = x - x.mean()
            X_c = np.column_stack([np.ones(len(y)), x_c])
            with suppress_noisy_fit_warnings():
                res = RecursiveLS(y, X_c).fit()
            cusum = res.cusum
            # _cusum_significance_bounds returns (lo_endpoints, hi_endpoints)
            # where each is a 2-element array (start, end) of the linear boundary.
            lo_pts, hi_pts = res._cusum_significance_bounds(alpha=0.05)
            steps = len(cusum)
            t_lin = np.linspace(0, 1, steps)
            lo_band = lo_pts[0] + (lo_pts[1] - lo_pts[0]) * t_lin
            hi_band = hi_pts[0] + (hi_pts[1] - hi_pts[0]) * t_lin
            cusum_years = agg["year"].values[len(y) - steps:]

            max_idx = int(np.argmax(np.abs(cusum)))
            max_val = float(cusum[max_idx])
            max_yr  = int(cusum_years[max_idx])
            bound_at_peak = float(hi_band[max_idx])
            exceeds = bool(np.any(cusum > hi_band) or np.any(cusum < lo_band))

            print(f"   {ctx_label}  (N = {len(agg)} seasons)")
            verdict = "YES — break detected" if exceeds else "no — stable within bounds"
            print(f"   Exceeds 5% critical band: {verdict}")
            print(f"   Peak |CUSUM| = {abs(max_val):.3f} at year {max_yr}  "
                  f"(5% bound at that point = ±{bound_at_peak:.3f})")
            if exceeds:
                exit_yr = None
                for i, (c, lo, hi) in enumerate(zip(cusum, lo_band, hi_band)):
                    if c > hi or c < lo:
                        exit_yr = int(cusum_years[i])
                        break
                if exit_yr is not None:
                    print(f"   First exits boundary at year: {exit_yr}")
                print(f"   ► CUSUM and QLR agree: structural instability confirmed.")
            else:
                pct = 100 * abs(max_val) / bound_at_peak if bound_at_peak > 0 else 0
                print(f"   Peak is {pct:.0f}% of the 5% boundary.")
                # Facts for stats_explainer.md §3 (CUSUM).
                _cc = "po" if is_po else "reg"
                FACTS.set(f"cusum.{_cc}_peak", abs(max_val), "{:.1f}", note=f"{ctx_label}: peak |CUSUM|")
                FACTS.set(f"cusum.{_cc}_peak_year", max_yr, "{:d}", note=f"{ctx_label}: year of peak CUSUM")
                FACTS.set(f"cusum.{_cc}_bound", bound_at_peak, "{:.1f}", note=f"{ctx_label}: 5% CUSUM bound at peak")
                FACTS.set(f"cusum.{_cc}_pct", pct, "{:.0f}", note=f"{ctx_label}: peak as % of 5% boundary")
                if is_po == 0:
                    br = (results or {}).get("break_rs", {})
                    break_yr = br.get("year", "late 1990s")
                    sl_pre = br.get("sl_pre")
                    sl_post = br.get("sl_post")
                    print(f"   ► CUSUM stays inside bounds even though the structural break test found a break:")
                    if sl_pre is not None and sl_post is not None:
                        print(f"     the slope change around {break_yr} is gradual ({sl_pre:+.2f} → {sl_post:+.2f} pp/yr),")
                    else:
                        print(f"     the slope change is gradual,")
                    print(f"     not a sharp level jump — CUSUM has lower power for slope-only breaks.")
            print()
        except Exception as e:
            print(f"   {ctx_label}: CUSUM failed ({e})\n")


def compute_bayesian_changepoint(df: pd.DataFrame) -> dict:
    """Piecewise WLS change-point computation (no printing).

    Compares k=0..3 using BIC-based marginal likelihoods under a uniform prior
    over model order and break locations.  Each segment must contain at least
    MIN_SEG seasons (enough to fit a line with ≥1 residual df).  This is more
    permissive than the 15% trim used by the QLR test (whose Andrews critical
    values are calibrated to that trim); here the BIC penalty itself disciplines
    against over-segmentation.

    Returns a results dict consumed by run_bayesian_changepoint() (prints) and
    plot_bayesian_changepoint() (chart).
    """
    from scipy.special import logsumexp

    MIN_SEG = 3   # minimum seasons per segment

    sub = df[df["is_playoff"] == 0]
    agg = (sub.groupby("year")["home_win"]
              .agg(["sum", "count"])
              .reset_index()
              .rename(columns={"sum": "wins", "count": "games"}))
    agg["pct"] = agg["wins"] / agg["games"] * 100
    agg = agg.sort_values("year").reset_index(drop=True)

    n = len(agg)
    y = agg["pct"].values.astype(float)
    x = agg["year"].values.astype(float)
    w = agg["games"].values.astype(float)
    w_norm = w / w.mean()   # normalize so BIC penalty uses n, not sum(w)

    def _wls(y_seg, x_seg, w_seg):
        """Weighted least squares: returns (beta[intercept, slope], weighted_RSS)."""
        ns = len(y_seg)
        if ns < 2:
            return np.array([np.nan, np.nan]), np.inf
        X = np.column_stack([np.ones(ns), x_seg])
        W = np.diag(w_seg)
        XtW = X.T @ W
        try:
            beta = np.linalg.solve(XtW @ X, XtW @ y_seg)
        except np.linalg.LinAlgError:
            return np.array([np.nan, np.nan]), np.inf
        resid = y_seg - X @ beta
        return beta, float((w_seg * resid ** 2).sum())

    def _bic(wrss, p_params):
        """BIC-comparable score (shared constant terms dropped)."""
        if wrss <= 0 or not np.isfinite(wrss):
            return np.inf
        return n * np.log(wrss / n) + p_params * np.log(n)

    # ── k=0 ──
    b0, wrss0 = _wls(y, x, w_norm)
    bic0 = _bic(wrss0, 2)
    fit0 = b0[0] + b0[1] * x

    # ── k=1 ──
    cands1 = list(range(MIN_SEG, n - MIN_SEG))
    bic1 = np.full(len(cands1), np.inf)
    fits1 = {}
    slopes1 = {}
    for i, tau in enumerate(cands1):
        ba, wra = _wls(y[:tau], x[:tau], w_norm[:tau])
        bb, wrb = _wls(y[tau:], x[tau:], w_norm[tau:])
        bic1[i] = _bic(wra + wrb, 4)
        fa = ba[0] + ba[1] * x[:tau]
        fb = bb[0] + bb[1] * x[tau:]
        fits1[tau] = np.concatenate([fa, fb])
        slopes1[tau] = (float(ba[1]), float(bb[1]))

    # ── k=2 ──
    cands2 = [(t1, t2)
              for t1 in range(MIN_SEG, n - 2 * MIN_SEG)
              for t2 in range(t1 + MIN_SEG, n - MIN_SEG)]
    bic2 = np.full(len(cands2), np.inf)
    fits2 = {}
    for i, (t1, t2) in enumerate(cands2):
        ba, wra = _wls(y[:t1],    x[:t1],    w_norm[:t1])
        bb, wrb = _wls(y[t1:t2],  x[t1:t2],  w_norm[t1:t2])
        bc, wrc = _wls(y[t2:],    x[t2:],    w_norm[t2:])
        bic2[i] = _bic(wra + wrb + wrc, 6)
        fits2[(t1, t2)] = np.concatenate([
            ba[0] + ba[1] * x[:t1],
            bb[0] + bb[1] * x[t1:t2],
            bc[0] + bc[1] * x[t2:],
        ])

    # ── k=3 ──
    cands3 = [(t1, t2, t3)
              for t1 in range(MIN_SEG, n - 3 * MIN_SEG)
              for t2 in range(t1 + MIN_SEG, n - 2 * MIN_SEG)
              for t3 in range(t2 + MIN_SEG, n - MIN_SEG)]
    bic3 = np.full(len(cands3), np.inf)
    fits3 = {}
    for i, (t1, t2, t3) in enumerate(cands3):
        ba, wra = _wls(y[:t1],    x[:t1],    w_norm[:t1])
        bb, wrb = _wls(y[t1:t2],  x[t1:t2],  w_norm[t1:t2])
        bc, wrc = _wls(y[t2:t3],  x[t2:t3],  w_norm[t2:t3])
        bd, wrd = _wls(y[t3:],    x[t3:],    w_norm[t3:])
        bic3[i] = _bic(wra + wrb + wrc + wrd, 8)
        fits3[(t1, t2, t3)] = np.concatenate([
            ba[0] + ba[1] * x[:t1],
            bb[0] + bb[1] * x[t1:t2],
            bc[0] + bc[1] * x[t2:t3],
            bd[0] + bd[1] * x[t3:],
        ])

    # ── Posterior model probabilities ──
    # log Z_k = logsumexp(-BIC/2 over configs) - log(n_configs)
    lz0 = -bic0 / 2
    lz1 = float(logsumexp(-bic1 / 2)) - np.log(len(cands1))
    lz2 = float(logsumexp(-bic2 / 2)) - np.log(len(cands2)) if cands2 else -np.inf
    lz3 = float(logsumexp(-bic3 / 2)) - np.log(len(cands3)) if cands3 else -np.inf
    lz = np.array([lz0, lz1, lz2, lz3])
    lz_shifted = lz - lz.max()
    k_probs = np.exp(lz_shifted) / np.exp(lz_shifted).sum()

    # ── k=1 posterior over break year ──
    lw1 = -bic1 / 2
    lw1 -= lw1.max()
    post1 = np.exp(lw1) / np.exp(lw1).sum()
    tau_post = {int(agg.iloc[tau]["year"]): float(post1[i]) for i, tau in enumerate(cands1)}

    # MAP and 95% HPD interval
    map_i1 = int(np.argmax(post1))
    map_tau = cands1[map_i1]
    map_year_k1 = int(agg.iloc[map_tau]["year"])
    sorted_desc = sorted(zip(post1, cands1), reverse=True)
    hpd_taus, cumprob = [], 0.0
    for prob, tau in sorted_desc:
        hpd_taus.append(int(agg.iloc[tau]["year"]))
        cumprob += prob
        if cumprob >= 0.95:
            break
    hpd_k1 = (min(hpd_taus), max(hpd_taus))

    # Statistical detail for investigation.md: the single-bend year and its range.
    FACTS.set("changepoint.map_year", map_year_k1, "{:d}",
              note="Bayesian change-point: most likely single-bend year")
    FACTS.set("changepoint.hpd_lo", hpd_k1[0], "{:d}", note="Change-point 95% HPD interval low")
    FACTS.set("changepoint.hpd_hi", hpd_k1[1], "{:d}", note="Change-point 95% HPD interval high")

    # Posterior-weighted pre/post slopes for k=1
    pre_sl  = np.array([slopes1[tau][0] for tau in cands1])
    post_sl = np.array([slopes1[tau][1] for tau in cands1])
    mean_pre  = float((post1 * pre_sl).sum())
    mean_post = float((post1 * post_sl).sum())
    std_pre   = float(np.sqrt((post1 * (pre_sl  - mean_pre) ** 2).sum()))
    std_post  = float(np.sqrt((post1 * (post_sl - mean_post) ** 2).sum()))

    # ── k=2 MAP ──
    best_k2_i = int(np.argmin(bic2)) if cands2 else None
    if best_k2_i is not None:
        best_k2 = cands2[best_k2_i]
        map_years_k2 = (int(agg.iloc[best_k2[0]]["year"]), int(agg.iloc[best_k2[1]]["year"]))
        fit2_map = fits2[best_k2]
        lw2 = -bic2 / 2
        lw2 -= lw2.max()
        post2 = np.exp(lw2) / np.exp(lw2).sum()
        marg1: dict[int, float] = {}
        marg2: dict[int, float] = {}
        for i, (t1, t2) in enumerate(cands2):
            yr1, yr2 = int(agg.iloc[t1]["year"]), int(agg.iloc[t2]["year"])
            marg1[yr1] = marg1.get(yr1, 0.0) + float(post2[i])
            marg2[yr2] = marg2.get(yr2, 0.0) + float(post2[i])
    else:
        map_years_k2, fit2_map, marg1, marg2 = None, None, {}, {}

    # ── k=3 MAP ──
    best_k3_i = int(np.argmin(bic3)) if cands3 else None
    if best_k3_i is not None:
        best_k3 = cands3[best_k3_i]
        map_years_k3 = tuple(int(agg.iloc[t]["year"]) for t in best_k3)
        fit3_map = fits3[best_k3]
    else:
        map_years_k3, fit3_map = None, None

    return {
        "years": x.astype(int).tolist(),
        "pct": y.tolist(),
        "n_games": w.tolist(),
        "k_probs": k_probs.tolist(),
        "lz": lz.tolist(),
        "k0_fit": fit0.tolist(),
        "k1_map_year": map_year_k1,
        "k1_hpd": hpd_k1,
        "k1_post": tau_post,
        "k1_map_fit": fits1[map_tau].tolist(),
        "k1_slopes": {
            "pre_mean": mean_pre, "post_mean": mean_post,
            "pre_std": std_pre,   "post_std": std_post,
        },
        "k2_map_years": map_years_k2,
        "k2_map_fit": fit2_map.tolist() if fit2_map is not None else None,
        "k2_marg1": marg1,
        "k2_marg2": marg2,
        "k3_map_years": map_years_k3,
        "k3_map_fit": fit3_map.tolist() if fit3_map is not None else None,
        "min_seg": MIN_SEG,
    }


def run_bayesian_changepoint(df: pd.DataFrame) -> dict:
    """Print Bayesian change-point results and return the results dict."""
    r = compute_bayesian_changepoint(df)
    k_probs = r["k_probs"]
    lz = r["lz"]
    tau_post = r["k1_post"]
    map_year_k1 = r["k1_map_year"]
    hpd_k1 = r["k1_hpd"]
    slopes = r["k1_slopes"]
    map_years_k2 = r.get("k2_map_years")
    map_years_k3 = r.get("k3_map_years")
    min_seg = r.get("min_seg", 3)
    x = r["years"]

    _section("BAYESIAN CHANGE-POINT MODEL — HOW MANY BREAKS, AND WHERE?")
    print("   Model comparison: k=0 (linear), k=1 (one break), k=2 (two breaks), k=3 (three breaks).")
    print("   BIC-based marginal likelihood. Uniform prior over k and break locations.")
    print(f"   Piecewise WLS (weights = game counts); minimum {min_seg} seasons per segment.")
    print("   Regular season only.\n")
    print(f"   N = {len(x)} seasons, {x[0]}–{x[-1]}")
    print(f"   Candidate break positions: min segment size = {min_seg} seasons\n")

    lz0, lz1, lz2, lz3 = lz[0], lz[1], lz[2], lz[3]
    bf1 = float(np.exp(lz1 - lz0))
    bf2 = float(np.exp(lz2 - lz0)) if np.isfinite(lz2) else 0.0
    bf3 = float(np.exp(lz3 - lz0)) if np.isfinite(lz3) else 0.0

    print(f"   ─ Posterior model probabilities ─")
    print(f"   (Uniform prior over k ∈ {{0,1,2,3}} and over all valid break locations)\n")
    print(f"   {'Model':<25}  {'BF vs k=0':>10}  {'Posterior P(k)':>14}")
    print(f"   {'─'*25}  {'─'*10}  {'─'*14}")
    for label, bf, kp in [
        ("k=0  (no break)",      1.0,  k_probs[0]),
        ("k=1  (one break)",     bf1,  k_probs[1]),
        ("k=2  (two breaks)",    bf2,  k_probs[2]),
        ("k=3  (three breaks)",  bf3,  k_probs[3]),
    ]:
        bf_s = f"{bf:>9.1f}" if bf < 1000 else f"{bf:>9.0f}"
        print(f"   {label:<25}  {bf_s}  {kp:>13.1%}")

    print(f"\n   ─ k=1 posterior over break year ─")
    print(f"   MAP break year:     {map_year_k1}")
    print(f"   95% HPD interval:   {hpd_k1[0]}–{hpd_k1[1]}")
    print(f"   Posterior-weighted slopes:")
    print(f"     Pre-break:  {slopes['pre_mean']:+.3f} pp/yr  (±{slopes['pre_std']:.3f} posterior SD)")
    print(f"     Post-break: {slopes['post_mean']:+.3f} pp/yr  (±{slopes['post_std']:.3f} posterior SD)")

    print(f"\n   Top break-year probabilities (k=1):")
    print(f"   {'Year':>6}  {'P(τ=year | k=1)':>16}")
    print(f"   {'─'*6}  {'─'*16}")
    for yr, prob in sorted(tau_post.items(), key=lambda kv: -kv[1])[:8]:
        bar = "█" * int(prob * 60)
        print(f"   {yr:>6}  {prob:>15.1%}  {bar}")

    if map_years_k2 is not None:
        print(f"\n   ─ k=2 MAP break years: {map_years_k2[0]} and {map_years_k2[1]} ─")

    if map_years_k3 is not None:
        print(f"\n   ─ k=3 MAP break years: {map_years_k3[0]}, {map_years_k3[1]}, and {map_years_k3[2]} ─")

    dominant_k = int(np.argmax(k_probs))
    if k_probs[dominant_k] > 0.5:
        print(f"\n   ► k={dominant_k} is the most probable model (P = {k_probs[dominant_k]:.1%}).")
    if bf1 > 10:
        print(f"   ► BF(k=1 vs k=0) = {bf1:.1f}: strong evidence for at least one structural break.")
    elif bf1 > 3:
        print(f"   ► BF(k=1 vs k=0) = {bf1:.1f}: moderate evidence for at least one structural break.")
    else:
        print(f"   ► BF(k=1 vs k=0) = {bf1:.1f}: weak evidence for a structural break.")
    if map_years_k2 is not None:
        print(f"   ► BF(k=2 vs k=1) = {(bf2/bf1):.1f}  BF(k=3 vs k=2) = {(bf3/bf2):.1f}" if bf2 > 0 else "")
    print()
    return r


def compute_multilevel_decline(df: pd.DataFrame) -> dict:
    """Is the HCA decline league-wide or concentrated in particular franchises?

    Builds a regular-season team-season panel of the HCA gap
    (home win% − road win%, which nets out each team's overall strength),
    fits each franchise's own year-slope by OLS, then separates the true
    between-team spread in those slopes from sampling noise — the same
    empirical-Bayes / variance-decomposition idiom this report uses for
    franchise HCA levels and referee bias. The pooled (cluster-robust) slope is
    the league-wide decline; the noise-adjusted between-team SD says how much
    franchises genuinely differ from it. Per-team slopes are EB-shrunken toward
    the league slope for display.

    Regular season only — per-franchise playoff samples (a handful of games per
    team-season) are far too small for a season-by-season panel.

    Returns a dict consumed by both run_multilevel_decline() and the plot.
    """
    MIN_G         = 15    # min home and road games per team-season (keeps lockouts)
    MIN_SEASONS   = 10    # franchises need a long enough panel for a slope estimate
    ACTIVE_CUTOFF = 2015  # drop franchises whose last season is before this year
    sub = df[df["is_playoff"] == 0]

    home = sub.groupby(["year", "TEAM_NAME_home"])["home_win"].agg(hw="sum", hn="count")
    away = sub.groupby(["year", "TEAM_NAME_away"])["home_win"].agg(rl="sum", an="count")
    home.index = home.index.rename(["year", "team"])
    away.index = away.index.rename(["year", "team"])
    panel = home.join(away, how="inner").reset_index()
    panel = panel[(panel["hn"] >= MIN_G) & (panel["an"] >= MIN_G)].copy()
    if panel.empty:
        return {"teams": []}

    panel["home_pct"] = 100.0 * panel["hw"] / panel["hn"]
    # home_win == 1 is a road loss for the away team, so road wins = an − rl.
    panel["road_pct"] = 100.0 * (panel["an"] - panel["rl"]) / panel["an"]
    panel["hca_gap"]  = panel["home_pct"] - panel["road_pct"]
    panel["year_c"]   = panel["year"] - panel["year"].mean()

    with suppress_noisy_fit_warnings():
        pooled = smf.ols("hca_gap ~ year_c", data=panel).fit(
            cov_type="cluster", cov_kwds={"groups": panel["team"]})
    league_slope = float(pooled.params["year_c"])
    league_se    = float(pooled.bse["year_c"])
    league_p     = float(pooled.pvalues["year_c"])

    rows: list[tuple[str, float, float, int]] = []  # (team, slope, slope_se, n)
    with suppress_noisy_fit_warnings():
        for t, g in panel.groupby("team"):
            if g["year"].nunique() < MIN_SEASONS:
                continue
            if int(g["year"].max()) < ACTIVE_CUTOFF:
                continue
            m = smf.ols("hca_gap ~ year_c", data=g).fit()
            rows.append((str(t), float(m.params["year_c"]),
                         float(m.bse["year_c"]), int(len(g))))
    if not rows:
        return {"teams": []}

    slopes = np.array([r[1] for r in rows])
    ses    = np.array([r[2] for r in rows])
    obs_var  = float(np.var(slopes, ddof=1))
    mean_se2 = float(np.mean(ses ** 2))
    true_var = max(0.0, obs_var - mean_se2)        # method-of-moments
    true_sd  = float(np.sqrt(true_var))
    noise_share = min(1.0, mean_se2 / obs_var) if obs_var > 0 else 1.0

    shrunk, _info = shrink_to_mean(slopes, ses ** 2)  # EB toward grand mean
    teams = sorted(
        [{"team": rows[i][0], "slope": float(slopes[i]), "se": float(ses[i]),
          "shrunk": float(shrunk[i]), "n": rows[i][3]}
         for i in range(len(rows))],
        key=lambda r: r["slope"],
    )

    return {
        "panel_rows": int(len(panel)),
        "n_teams": int(panel["team"].nunique()),
        "n_modeled": len(rows),
        "league_slope": league_slope, "league_se": league_se, "league_p": league_p,
        "obs_sd": float(np.sqrt(obs_var)), "true_sd": true_sd,
        "noise_share": noise_share,
        "teams": teams,  # dicts with raw slope + se + shrunken, sorted by raw slope
    }


def run_multilevel_decline(df: pd.DataFrame) -> None:
    """Print the verdict on whether the decline is league-wide or concentrated."""
    _section("IS THE DECLINE LEAGUE-WIDE? — PER-FRANCHISE HCA SLOPE DECOMPOSITION")
    print("   Regular-season team-season HCA gap = home win% − road win% (nets out")
    print("   each team's overall strength). Each franchise gets its own year-slope")
    print("   by OLS; the pooled cluster-robust slope is the league-wide decline.")
    print("   A method-of-moments split separates the true between-team spread in")
    print("   those slopes from sampling noise (same idiom as franchise HCA and")
    print("   referee bias). Near-zero true spread → the decline is league-wide.\n")

    d = compute_multilevel_decline(df)
    if not d.get("teams"):
        print("   Insufficient data.\n")
        return

    print(f"   Panel: {d['panel_rows']:,} team-seasons; per-team slopes fit for "
          f"{d['n_modeled']} franchises (≥10 seasons)\n")
    print(f"   League-wide slope (pooled, cluster-robust):  {d['league_slope']:+.3f} pp/yr  "
          f"(SE {d['league_se']:.3f}, p = {_fmt_p(d['league_p'])}  {_stars(d['league_p']).strip()})")
    print(f"   Observed SD of per-team slopes:              {d['obs_sd']:.3f} pp/yr")
    print(f"   Noise-adjusted true between-team SD:         {d['true_sd']:.3f} pp/yr")
    print(f"   Share of observed spread that is noise:      {d['noise_share'] * 100:.0f}%\n")

    teams  = d["teams"]
    n_pos  = sum(1 for r in teams if r["slope"] > 0)
    steep, shallow = teams[0], teams[-1]
    print(f"   Per-franchise raw slopes (extremes; both within noise of the league rate):")
    print(f"   Steepest decline:  {steep['slope']:+.3f} pp/yr  ({steep['team']})")
    print(f"   Shallowest/rising: {shallow['slope']:+.3f} pp/yr  ({shallow['team']})")
    print(f"   Franchises with a positive (rising) raw slope: {n_pos}/{len(teams)}")
    print(f"   After EB shrinkage every franchise collapses to ≈{d['league_slope']:+.2f} pp/yr.\n")

    FACTS.set("leaguewide.slope", d["league_slope"], "{:+.2f}", unit="pp/yr",
              note="Pooled cluster-robust per-franchise HCA-gap slope (league-wide decline)")
    FACTS.set("leaguewide.noise_share", d["noise_share"] * 100, "{:.0f}%",
              note="Share of per-franchise slope spread that is sampling noise")
    FACTS.set("leaguewide.n_modeled", d["n_modeled"], "{:d}",
              note="Franchises with a fitted per-team HCA slope (≥10 seasons)")
    FACTS.guard("leaguewide_all_decline", n_pos == 0,
                claim="every franchise with a long enough record shows a declining home-court edge",
                value=f"{n_pos}/{len(teams)} franchises have a rising raw slope")

    if d["true_sd"] > abs(d["league_slope"]) and d["noise_share"] < 0.5:
        print("   ► Franchises differ meaningfully in how fast their edge faded — the")
        print("     decline is concentrated, not a uniform league-wide drift.")
    else:
        print("   ► Once sampling noise is removed, franchises barely differ: most of the")
        print("     raw spread in team slopes is noise, and the shrunken slopes collapse")
        print("     onto one shared league rate. The decline is broadly league-wide, not")
        print("     driven by a handful of franchises losing their edge.")
    print("   ► Playoffs are excluded: per-franchise playoff samples are far too small")
    print("     for a season-by-season panel; the playoff decline is league-wide (§1, §5).\n")


def compute_hca_forecast(df: pd.DataFrame, horizon: int = 5) -> dict:
    """Forecast the season-level home win % forward with a structural
    time-series model, separately for regular season and playoffs.

    For each context the per-season home win % is the endog series; a local
    linear trend (an UnobservedComponents state-space model) lets the underlying
    level drift with its own slope, so the forecast extrapolates the current
    local slope rather than a single straight line through all 40 years. The fit
    is deterministic (`.fit(disp=False)`), so home_court_results.md stays
    reproducible. ``get_forecast`` yields the central path plus 80% and 95%
    prediction intervals — the fan that carries the honest uncertainty.

    Returns a dict keyed by "Regular season" / "Playoffs"; a context whose fit
    fails is skipped, so the result may be partial.
    """
    out: dict = {"horizon": horizon}

    for label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po]
        if is_po:
            sub = sub[~sub["year"].isin(nba.SKIP_PLAYOFF_YEARS)]
        g = sub.groupby("year")["home_win"]
        pct = (g.sum() / g.count() * 100.0).sort_index()
        if pct.shape[0] < 8:
            continue
        years = pct.index.to_numpy().astype(int)
        endog = pct.to_numpy().astype(float)

        try:
            with suppress_noisy_fit_warnings():
                res = sm.tsa.UnobservedComponents(
                    endog, level="local linear trend"
                ).fit(disp=False)
                level = np.asarray(res.level["smoothed"], dtype=float)
                slope = float(np.asarray(res.trend["smoothed"], dtype=float)[-1])
                fc = res.get_forecast(horizon)
                mean = np.asarray(fc.predicted_mean, dtype=float)
                ci95 = np.asarray(fc.conf_int(alpha=0.05), dtype=float)
                ci80 = np.asarray(fc.conf_int(alpha=0.20), dtype=float)
        except Exception:
            # A numerically unstable fit (singular state covariance) drops out
            # cleanly rather than crashing the whole pipeline.
            continue

        last_year = int(years[-1])
        fyears = np.arange(nba.END_YEAR + 1, nba.END_YEAR + 1 + horizon)
        out[label] = {
            "years": years.tolist(),
            "pcts": endog.tolist(),
            "level": level.tolist(),
            "slope": slope,
            "current_level": float(level[-1]),
            "early_level": float(level[0]),
            "last_year": last_year,
            "forecast_years": fyears.tolist(),
            "mean": mean.tolist(),
            "ci80_lo": ci80[:, 0].tolist(),
            "ci80_hi": ci80[:, 1].tolist(),
            "ci95_lo": ci95[:, 0].tolist(),
            "ci95_hi": ci95[:, 1].tolist(),
        }
    return out


def run_hca_forecast(df: pd.DataFrame) -> None:
    """Print the state-space forecast of home win % for the next few seasons,
    with prediction intervals, for the regular season and the playoffs."""
    _section("WHERE IS HOME COURT HEADING? — STATE-SPACE FORECAST")
    print("   A local-linear-trend state-space model on the season-level home")
    print("   win % lets the underlying level drift with its own slope, then")
    print("   extrapolates a few seasons forward with prediction intervals (the")
    print("   fan). Regular season and playoffs fit separately. This is a forward")
    print("   projection of the current slope, not a claim about future rule")
    print("   changes; the intervals widen with the horizon to show that.\n")

    data = compute_hca_forecast(df)

    for label in ("Regular season", "Playoffs"):
        d = data.get(label)
        if not d:
            print(f"   {label}: insufficient data to fit.\n")
            continue
        print(f"   {label}  ({d['years'][0]}–{d['last_year']}, "
              f"{len(d['years'])} seasons)")
        print(f"   Current smoothed level:  {d['current_level']:.1f}%   "
              f"(trend slope {d['slope']:+.1f} pp/yr)\n")
        print(f"   {'Season':>8}  {'Forecast':>9}  {'95% interval':>16}")
        print(f"   {'─'*8}  {'─'*9}  {'─'*16}")
        for i, yr in enumerate(d["forecast_years"]):
            print(f"   {yr:>8}  {d['mean'][i]:>8.1f}%  "
                  f"[{d['ci95_lo'][i]:>5.1f}, {d['ci95_hi'][i]:>5.1f}]")
        print()

        if label == "Regular season":
            FACTS.set("forecast.rs_current_level", d["current_level"], "{:.1f}%",
                      note="State-space: current smoothed RS home win % level")
            FACTS.set("forecast.rs_slope_pp", d["slope"], "{:.1f}", unit="pp",
                      note="State-space: current RS trend slope (pp/yr)")
            FACTS.set("forecast.rs_final_central", d["mean"][-1], "{:.1f}%",
                      note=f"State-space: central RS forecast for {d['forecast_years'][-1]}")
            FACTS.set("forecast.rs_final_lo95", d["ci95_lo"][-1], "{:.1f}%",
                      note=f"State-space: RS forecast 95% lower bound, {d['forecast_years'][-1]}")
            FACTS.set("forecast.rs_final_hi95", d["ci95_hi"][-1], "{:.1f}%",
                      note=f"State-space: RS forecast 95% upper bound, {d['forecast_years'][-1]}")
            FACTS.set("forecast.horizon_year", d["forecast_years"][-1], "{:.0f}",
                      note="State-space: final forecast (horizon) season")
        else:
            FACTS.set("forecast.po_current_level", d["current_level"], "{:.1f}%",
                      note="State-space: current smoothed PO home win % level")
            FACTS.set("forecast.po_slope_pp", d["slope"], "{:.1f}", unit="pp",
                      note="State-space: current PO trend slope (pp/yr)")
            FACTS.set("forecast.po_final_central", d["mean"][-1], "{:.1f}%",
                      note=f"State-space: central PO forecast for {d['forecast_years'][-1]}")
            FACTS.set("forecast.po_final_lo95", d["ci95_lo"][-1], "{:.1f}%",
                      note=f"State-space: PO forecast 95% lower bound, {d['forecast_years'][-1]}")
            FACTS.set("forecast.po_final_hi95", d["ci95_hi"][-1], "{:.1f}%",
                      note=f"State-space: PO forecast 95% upper bound, {d['forecast_years'][-1]}")

    # Guard: the central path keeps sliding in both contexts, and the entire 95%
    # range for the final regular-season forecast year stays below the mid-1980s
    # regular-season level. Verified against the live data before wording this.
    rs = data.get("Regular season")
    po = data.get("Playoffs")
    if rs and po:
        rs_declines = all(b < a for a, b in zip(rs["mean"], rs["mean"][1:]))
        po_declines = all(b < a for a, b in zip(po["mean"], po["mean"][1:]))
        rs_below_early = rs["ci95_hi"][-1] < rs["early_level"]
        FACTS.guard(
            "forecast_keeps_declining",
            bool(rs_declines and po_declines and rs_below_early),
            claim="the central forecast keeps sliding in both the regular season "
                  "and the playoffs, and the whole plausible range for the final "
                  "regular-season forecast year stays below the mid-1980s home win rate",
            value=(f"RS {rs['mean'][0]:.1f}→{rs['mean'][-1]:.1f}%, "
                   f"PO {po['mean'][0]:.1f}→{po['mean'][-1]:.1f}%, "
                   f"RS upper {rs['ci95_hi'][-1]:.1f}% < early {rs['early_level']:.1f}%"),
        )


def run_era_analysis(df: pd.DataFrame) -> None:
    """Test whether rule-change era breaks add a level shift beyond the year trend.

    Mirrors run_format_period_analysis() but for ERA_DEFS and runs in both
    regular season and playoffs.  The key question: does the decline happen in
    discrete steps at rule-change boundaries, or is it a smooth continuous drift?
    """
    from scipy.stats import chi2
    from statsmodels.stats.proportion import proportions_ztest

    era_ref = nba.ERA_DEFS[0][0]   # "1984–94"

    _section("RULE-CHANGE ERAS — DO THE ERA BREAKS MATTER BEYOND THE YEAR TREND?")
    print("   Home win % by rule-change era; pairwise tests between consecutive eras.")
    print("   Trend-controlled model: home_win ~ year + C(era).")
    print("   LR test: do era dummies jointly add explanatory power beyond the year trend?")
    print("   (If not, the decline is a smooth drift; if yes, specific rules caused jumps.)\n")

    for ctx_label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po]
        if is_po:
            sub = sub[~sub["year"].isin(nba.SKIP_PLAYOFF_YEARS)]
        if sub.empty:
            continue

        p_bar = sub["home_win"].mean()
        print(f"   {ctx_label}  (N = {len(sub):,} games)\n")

        counts: dict[str, tuple[int, int]] = {}
        print(f"   {'Era':<12}  {'N games':>8}  {'Home win %':>11}")
        print(f"   {'─'*12}  {'─'*8}  {'─'*11}")
        for era_label, y1, y2, _ in nba.ERA_DEFS:
            era_sub = sub[(sub["year"] >= y1) & (sub["year"] <= y2)]
            if era_sub.empty:
                continue
            wins_e, n_e = int(era_sub["home_win"].sum()), len(era_sub)
            counts[era_label] = (wins_e, n_e)
            print(f"   {era_label:<12}  {n_e:>8,}  {100.0 * wins_e / n_e:>10.1f}%")

        avail = [lbl for lbl, *_ in nba.ERA_DEFS if lbl in counts]
        print(f"\n   Consecutive eras — two-proportion z-tests:")
        for a, b in zip(avail, avail[1:]):
            (wa, na), (wb, nb) = counts[a], counts[b]
            z, p = proportions_ztest([wa, wb], [na, nb])
            diff = 100.0 * (wb / nb - wa / na)
            print(f"   {a:>8} → {b:<8}  {diff:+5.1f} pp   "
                  f"(z = {z:+.2f}, p = {_fmt_p(p)}  {_stars(p).strip()})")

        with suppress_noisy_fit_warnings():
            m_year = smf.logit("home_win ~ year", data=sub).fit(disp=0)
            _warn_if_not_converged(m_year, "run_era_analysis: m_year")
            m_era  = smf.logit(
                f"home_win ~ year + C(era, Treatment('{era_ref}'))",
                data=sub,
            ).fit(disp=0)
            _warn_if_not_converged(m_era, "run_era_analysis: m_era")

        print(f"\n   Trend-controlled logistic: home_win ~ year + C(era)")
        print(f"   (reference era = {era_ref})\n")
        print(f"   {'Predictor':<28}  {'log-odds':>8}  {'≈pp':>6}  {'p':>8}  {'':3}")
        print(f"   {'─'*28}  {'─'*8}  {'─'*6}  {'─'*8}  {'─'*3}")
        for name in m_era.params.index:
            if name == "Intercept":
                continue
            coef, pval = m_era.params[name], m_era.pvalues[name]
            label = (name
                     .replace(f"C(era, Treatment('{era_ref}'))[T.", "era: ")
                     .replace("]", "")
                     .replace("year", "year trend (per yr)"))
            print(f"   {label:<28}  {coef:+8.3f}  {_pp(coef, p_bar):+6.1f}  "
                  f"{_fmt_p(pval):>8}  {_stars(pval)}")
            # Fact for the prose (§1/§4/App C): the one-time 1994-95 drop is the
            # regular-season 1995–01 era level shift in this model.
            if is_po == 0 and "1995–01" in name:
                FACTS.set("era.drop_1995", abs(_pp(coef, p_bar)), "{:.1f}",
                          note="Rule-change era model: 1994-95 (hand-checking) reg-season level shift (pp)")
                FACTS.set("era.drop_1995_p", "< 0.001" if pval < 0.001 else f"= {pval:.3f}",
                          note="1994-95 era level-shift p-value (display)")
                _dlo, _dhi = _ci_lo_hi(m_era, name, p_bar)
                _dmag = sorted([abs(_dlo), abs(_dhi)])
                FACTS.set("era.drop_1995_ci_lo", _dmag[0], "{:.1f}",
                          note="1994-95 reg-season level-shift drop 95% CI low (pp, magnitude)")
                FACTS.set("era.drop_1995_ci_hi", _dmag[1], "{:.1f}",
                          note="1994-95 reg-season level-shift drop 95% CI high (pp, magnitude)")
                print(f"   → 1994-95 (1995–01) level shift: {_pp(coef, p_bar):+.1f} pp  "
                      f"95% CI [{_dlo:+.1f}, {_dhi:+.1f}] pp  "
                      f"(drop magnitude [{_dmag[0]:.1f}, {_dmag[1]:.1f}])")

        lr    = 2.0 * (m_era.llf - m_year.llf)
        dfree = int(m_era.df_model - m_year.df_model)
        p_lr  = chi2.sf(lr, dfree)
        print(f"\n   LR test — era dummies jointly vs. year-only model: "
              f"χ²({dfree}) = {lr:.2f},  p = {_fmt_p(p_lr)}  {_stars(p_lr).strip()}")

        if p_lr < 0.05:
            print(f"\n   ► Era dummies are jointly significant beyond the year trend —")
            print(f"     specific rule-change periods show a level shift above or below")
            print(f"     what the underlying trend alone would predict.")
        else:
            print(f"\n   ► Era dummies do not add significant explanatory power beyond")
            print(f"     the year trend (p = {_fmt_p(p_lr)}) — the decline is well-described")
            print(f"     as a continuous drift without discrete era-level jumps.")
        print()


def run_its_test(df: pd.DataFrame) -> None:
    """Interrupted Time Series (ITS) model at the 1994-95 boundary.

    Unified season-level WLS model:
        home_pct ~ year + post95 + time_since_break

    where post95 = 1 if year >= 1995 (level shift) and
    time_since_break = (year - 1994) * post95 (slope change).

    Tests both dimensions simultaneously: did HCA drop *immediately* at 1994-95
    (level shift) and/or did the *rate* of decline change (slope change)?
    """
    _section("ITS (INTERRUPTED TIME SERIES) — 1994-95 BOUNDARY")
    print("   Model: home_pct ~ year + post95 + time_since_break  (season-level WLS)")
    print("   post95      = 1 for seasons from 1994-95 onward (immediate level shift)")
    print("   time_since  = (year − 1994) × post95           (slope change post-break)")
    print("   Weights: game counts per season.\n")

    BREAK_YEAR = 1995  # first season in the 'post' window is the 1994-95 season

    for ctx_label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po]
        agg = sub.groupby("year")["home_win"].agg(["sum", "count"]).reset_index()
        agg.columns = ["year", "wins", "games"]
        agg["pct"] = agg["wins"] / agg["games"] * 100
        if is_po:
            agg = agg[~agg["year"].isin(nba.SKIP_PLAYOFF_YEARS)]
        agg = agg.sort_values("year").reset_index(drop=True)
        if len(agg) < 10:
            continue

        agg["post95"] = (agg["year"] >= BREAK_YEAR).astype(float)
        agg["time_since"] = (agg["year"] - (BREAK_YEAR - 1)) * agg["post95"]

        m = smf.wls("pct ~ year + post95 + time_since", data=agg, weights=agg["games"]).fit()

        b_yr     = m.params["year"]
        b_lev    = m.params["post95"]
        b_slp    = m.params["time_since"]
        p_yr     = m.pvalues["year"]
        p_lev    = m.pvalues["post95"]
        p_slp    = m.pvalues["time_since"]
        r2       = m.rsquared

        pre_slope_total = b_yr
        post_slope_total = b_yr + b_slp

        n = len(agg)
        print(f"   {ctx_label}  (N = {n} seasons)  R² = {r2:.3f}")
        print(f"   {'Parameter':<22}  {'Coef':>8}  {'p':>7}  {'Sig':>4}")
        print(f"   {'─'*22}  {'─'*8}  {'─'*7}  {'─'*4}")
        print(f"   {'Pre-break trend/yr':<22}  {b_yr:>+8.3f}  {_fmt_p(p_yr):>7}  {_stars(p_yr):>4}")
        print(f"   {'Level shift (1994-95)':<22}  {b_lev:>+8.3f}  {_fmt_p(p_lev):>7}  {_stars(p_lev):>4}")
        print(f"   {'Slope change/yr':<22}  {b_slp:>+8.3f}  {_fmt_p(p_slp):>7}  {_stars(p_slp):>4}")
        print()
        print(f"   Implied slopes: pre-break = {pre_slope_total:+.3f} pp/yr, "
              f"post-break = {post_slope_total:+.3f} pp/yr")
        # Facts for stats_explainer.md §15 (ITS at 1994-95).
        _ic = "po" if "Playoff" in ctx_label else "reg"
        FACTS.set(f"its.{_ic}_r2", r2, "{:.2f}", note=f"{_ic}: ITS R²")
        FACTS.set(f"its.{_ic}_pre_trend", b_yr, "{:+.2f}", note=f"{_ic}: ITS pre-break trend/yr")
        FACTS.set(f"its.{_ic}_pre_p", p_yr, "{:.3f}", note=f"{_ic}: ITS pre-break trend p")
        FACTS.set(f"its.{_ic}_level", b_lev, "{:+.2f}", note=f"{_ic}: ITS 1994-95 level shift")
        FACTS.set(f"its.{_ic}_level_p", p_lev, "{:.3f}", note=f"{_ic}: ITS level-shift p")
        FACTS.set(f"its.{_ic}_slope_chg", b_slp, "{:+.2f}", note=f"{_ic}: ITS slope change/yr")
        FACTS.set(f"its.{_ic}_slope_chg_p", p_slp, "{:.3f}", note=f"{_ic}: ITS slope-change p")
        FACTS.set(f"its.{_ic}_post_trend", post_slope_total, "{:+.2f}", note=f"{_ic}: ITS post-break trend/yr")

        if p_lev < 0.05 and p_slp >= 0.10:
            print(f"   ► Significant LEVEL shift only — HCA dropped sharply at 1994-95,")
            print(f"     no additional change in trajectory afterward.")
        elif p_slp < 0.05 and p_lev >= 0.10:
            print(f"   ► Significant SLOPE change only — HCA rate of decline slowed")
            print(f"     after 1994-95 without a discrete immediate jump.")
        elif p_lev < 0.05 and p_slp < 0.05:
            print(f"   ► Both level shift AND slope change significant — HCA dropped")
            print(f"     immediately AND rate of decline changed after 1994-95.")
        elif p_slp < 0.10 and p_lev >= 0.10:
            print(f"   ► Borderline slope change (p={p_slp:.3f}): rate of HCA decline appears")
            print(f"     to slow after 1994-95 ({pre_slope_total:+.2f} → {post_slope_total:+.2f} pp/yr),")
            print(f"     but no discrete immediate jump (level p={p_lev:.3f}). Consistent with")
            print(f"     the QLR break at 1999 — change accumulated gradually over seasons.")
        else:
            print(f"   ► Neither level nor slope significant at 1994-95.")
            print(f"     Overall HCA trend drove this context — 1994-95 not a sharp break.")
        print()


def run_placebo_tests(df: pd.DataFrame) -> None:
    """Falsification test: if 1994-95 caused the break, fake rule-change years
    should NOT produce significant step dummies.

    For every candidate year t in 1987–2010, tests a two-segment OLS model on
    season-level home win %:  pct ~ year + I(year >= t)
    The step dummy captures a discrete level shift at t beyond the year trend.
    If 1994-95 is the ONLY year (or by far the most significant) with a meaningful
    negative step, the causal attribution to that boundary is stronger.

    Season-level OLS is used (one row per season, weighted by game count) rather
    than game-level logistic, to avoid the game-count imbalance inflating z-stats.
    """
    _section("PLACEBO TESTS — IS 1994-95 UNIQUELY SIGNIFICANT?")
    print("   For each year t in 1987–2010: OLS on season home win%,")
    print("   model pct ~ year + step_t  (step_t = 1 if season >= t).")
    print("   A significant NEGATIVE step = discrete drop at that boundary.")
    print("   If 1994-95 uniquely stands out, it strengthens the causal claim.\n")

    for ctx_label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po]
        if is_po:
            sub = sub[~sub["year"].isin(nba.SKIP_PLAYOFF_YEARS)]
        agg = sub.groupby("year")["home_win"].agg(["sum", "count"]).reset_index()
        agg.columns = ["year", "wins", "games"]
        agg["pct"] = 100.0 * agg["wins"] / agg["games"]
        agg = agg.sort_values("year").reset_index(drop=True)
        if len(agg) < 10:
            continue

        print(f"   {ctx_label}  (N = {len(agg)} seasons)\n")
        print(f"   {'Year':>6}  {'Step coef (pp)':>15}  {'p-value':>10}  {'Sig':>4}")
        print(f"   {'─'*6}  {'─'*15}  {'─'*10}  {'─'*4}")

        sig_neg, sig_pos = [], []
        for t in range(1987, 2011):
            agg2 = agg.copy()
            agg2["step"] = (agg2["year"] >= t).astype(float)
            try:
                with suppress_noisy_fit_warnings():
                    m = smf.wls("pct ~ year + step", data=agg2,
                                weights=agg2["games"]).fit()
                coef = float(m.params.get("step", np.nan))
                pval = float(m.pvalues.get("step", np.nan))
                marker = "***" if pval < 0.001 else "** " if pval < 0.01 else "*  " if pval < 0.05 else "   "
                hi = " ← 1994-95" if t == 1995 else ""
                print(f"   {t:>6}  {coef:>+14.2f}  {_fmt_p(pval):>10}  {marker}{hi}")
                if t == 1995 and is_po == 0:
                    # Facts for stats_explainer.md §16 (placebo step at 1994-95).
                    FACTS.set("placebo.step_1995", coef, "{:+.2f}", note="Reg: placebo step coefficient at 1994-95")
                    FACTS.set("placebo.step_1995_p", pval, "{:.3f}", note="Reg: placebo step p at 1994-95")
                if pval < 0.05:
                    (sig_neg if coef < 0 else sig_pos).append(t)
            except Exception:
                print(f"   {t:>6}  {'—':>15}  {'—':>10}  {'—':>4}")

        if sig_neg:
            yr_range = f"{min(sig_neg)}–{max(sig_neg)}"
            print(f"\n   Significant negative steps (p<0.05): years {yr_range}")
            if 1995 in sig_neg:
                print(f"   ► 1994-95 (year=1995) IS in the significant window — consistent")
                print(f"     with a break in the decline period. Note: years before 1995 also")
                print(f"     appear significant because any boundary before the 1994-95 drop")
                print(f"     places the decline in the 'post' window; this is expected when")
                print(f"     a real break exists. The RULE-CHANGE ERAS test isolates 1994-95")
                print(f"     SPECIFICALLY after partialling out the year trend.")
        if sig_pos:
            print(f"   Significant positive steps (p<0.05): years {min(sig_pos)}–{max(sig_pos)}")
            print(f"   ► Positive dummies after ~{min(sig_pos)} reflect the slope moderation")
            print(f"     (§1b QLR): post-1999 HCA is 'too high' vs. the pre-1999 trend.")
        print()
