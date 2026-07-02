"""Shared print/stat helpers and model-fit warning handling used across the
home_court_analysis package: section banners, marginal-effect and CI helpers,
empirical-Bayes shrinkage, and the cointegration/league-metric helpers shared
by more than one themed module."""

from __future__ import annotations

import contextlib
import sys
import warnings

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from statsmodels.tools import sm_exceptions

from nbakit.textfmt import section as _section_str, stars as _stars, p_value as _fmt_p
from nbakit.stats import shrink_to_mean

import home_court_data as nba
from home_court_facts import FACTS

_NOISY_FIT_WARNINGS: tuple[type[Warning], ...] = (
    FutureWarning,
    RuntimeWarning,
    sm_exceptions.ValueWarning,
    sm_exceptions.IterationLimitWarning,
)


_W = 72


@contextlib.contextmanager
def suppress_noisy_fit_warnings():
    """Ignore only known-noisy statsmodels warning categories around a fit.

    Deliberately does NOT suppress ConvergenceWarning or
    PerfectSeparationWarning — see module note above.
    """
    with warnings.catch_warnings():
        for category in _NOISY_FIT_WARNINGS:
            warnings.simplefilter("ignore", category=category)
        yield


def _warn_if_not_converged(res, label: str) -> None:
    """Print a visible, unmissable notice if an MLE fit (smf.logit) failed to
    converge. Does not raise — the pipeline must still complete and produce
    its other numbers — but a non-converged fit must never ship silently.
    """
    if not getattr(res, "mle_retvals", {}).get("converged", True):
        print(f"    *** WARNING: fit did NOT converge — {label} ***",
              file=sys.stderr, flush=True)


def _header(title: str) -> None:
    bar = "═" * _W
    print(f"\n{bar}\n{title}\n{bar}")


def _section(title: str) -> None:
    print(_section_str(title, _W))


def _mcfadden(model) -> float:
    return 1.0 - model.llf / model.llnull


def _pp(coef: float, p_bar: float) -> float:
    """Marginal effect at the mean in percentage points."""
    return coef * p_bar * (1.0 - p_bar) * 100.0


def _clean(name: str, era_ref: str, fmt_ref: str) -> str:
    """Convert patsy's auto-generated parameter names to readable labels."""
    return (
        name
        .replace(f"C(era, Treatment('{era_ref}'))[T.", "era: ")
        .replace(f"C(format_period, Treatment('{fmt_ref}'))[T.", "")
        .replace("]:is_playoff", " × playoff")
        .replace("]", "")
        .replace("altitude_home", "altitude home (DEN/UTA)")
        .replace("rest_diff", "rest diff (per day)")
        .replace("tz_diff", "time zone diff (per zone)")
        .replace("covid", "COVID seasons")
        .replace("is_playoff", "playoff (vs. regular season)")
    )


def _ci_lo_hi(model, param: str, p_bar: float | None = None) -> tuple[float, float]:
    """Return 95% CI for a model parameter, optionally converted to pp via p_bar."""
    ci = model.conf_int()
    lo, hi = float(ci.loc[param, 0]), float(ci.loc[param, 1])
    if p_bar is not None:
        lo = lo * p_bar * (1 - p_bar) * 100.0
        hi = hi * p_bar * (1 - p_bar) * 100.0
    return lo, hi


def _shrink_hca(stats: dict) -> tuple[dict[str, float], dict[str, float]]:
    """Empirical-Bayes shrinkage of franchise HCA toward the league mean.

    Returns (shrunken, ci_hw):
    - shrunken[team]: EB-shrunken HCA in pp
    - ci_hw[team]: 95% CI half-width in pp (binomial variance formula)
    """
    teams = list(stats)
    hcas = np.array([stats[t]["hca"] for t in teams], dtype=float)
    samp_vars = np.array([
        1e4 * (
            (stats[t]["home_pct"] / 100.0) * (1.0 - stats[t]["home_pct"] / 100.0) / stats[t]["n_home"]
            + (stats[t]["road_pct"] / 100.0) * (1.0 - stats[t]["road_pct"] / 100.0) / stats[t]["n_road"]
        )
        for t in teams
    ])

    shrunk, _info = shrink_to_mean(hcas, samp_vars)
    shrunken = {t: float(shrunk[i]) for i, t in enumerate(teams)}
    ci_hw = {t: 1.96 * float(np.sqrt(samp_vars[i])) for i, t in enumerate(teams)}
    return shrunken, ci_hw


def _run_cointegration(x: np.ndarray, y: np.ndarray,
                        x_label: str, y_label: str) -> None:
    """ADF unit-root tests on x and y, then Engle-Granger cointegration.

    Determines whether the season-level Pearson r between two trending series
    reflects a genuine long-run relationship (cointegration) or spurious
    correlation driven by shared trend. H0 of ADF: unit root (I(1)); fail to
    reject (p ≥ 0.05) means the series is nonstationary. H0 of Engle-Granger
    cointegration test: no long-run relationship.
    """
    from statsmodels.tsa.stattools import adfuller, coint
    from scipy.stats import pearsonr

    r_raw, _ = pearsonr(x, y)

    def _adf(series):
        res = adfuller(series, maxlag=1, autolag=None)
        return float(res[0]), float(res[1])

    stat_x, p_x = _adf(x)
    stat_y, p_y = _adf(y)
    i1_x = p_x >= 0.05
    i1_y = p_y >= 0.05

    lx = "I(1) nonstationary" if i1_x else "I(0) stationary"
    ly = "I(1) nonstationary" if i1_y else "I(0) stationary"

    print(f"   ADF unit-root tests  (H0: unit root; p ≥ 0.05 → I(1) / nonstationary):")
    print(f"   {x_label:<34}  ADF = {stat_x:+.3f}  p = {_fmt_p(p_x)}  → {lx}")
    print(f"   {y_label:<34}  ADF = {stat_y:+.3f}  p = {_fmt_p(p_y)}  → {ly}")

    if i1_x and i1_y:
        ct, cp, _ = coint(x, y)
        print(f"\n   Engle-Granger cointegration  (H0: no long-run relationship):")
        print(f"   t = {ct:+.3f}  p = {_fmt_p(cp)}  {_stars(cp).strip()}")
        if cp < 0.05:
            print(f"   ► Both I(1) and cointegrated — r = {r_raw:+.3f} reflects a genuine")
            print(f"     long-run relationship, not just parallel trends.")
        else:
            print(f"   ► Both I(1) but NOT cointegrated — r = {r_raw:+.3f} is likely")
            print(f"     spurious; within-era game-level controls are the reliable evidence.")
    else:
        print(f"   ► At least one series is I(0) stationary; cointegration does not apply.")
        print(f"     Standard correlation is interpretable without spurious-trend concern.")
    print()


def _run_league_metric_analysis(
    df: pd.DataFrame,
    col: str,
    agg_name: str,
    metric_header: str,
    metric_sep: str,
    coef_desc: str,
    scale_desc: str,
    era_coef_desc: str,
    note_lines: list[str] | None = None,
    extra_block=None,
) -> None:
    """Shared season-level correlation + era table + cluster logistic loop used by
    run_3pa_analysis and run_pace_analysis.  metric_sep is appended to the formatted
    metric value in the era table row (e.g. '% ' for 3PA, '  ' for pace)."""
    from scipy.stats import pearsonr, spearmanr

    COL_W = 12

    for ctx_label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po].dropna(subset=[col])
        if sub.empty:
            continue

        by_year = sub.groupby("year").agg(
            **{agg_name: (col, "mean"),
               "home_pct": ("home_win", lambda x: x.mean() * 100)},
        ).reset_index()

        r_p, p_p = pearsonr(by_year[agg_name], by_year["home_pct"])
        r_s, p_s = spearmanr(by_year[agg_name], by_year["home_pct"])
        p_p_s = _fmt_p(p_p)
        p_s_s = _fmt_p(p_s)

        print(f"   {ctx_label}  (n = {len(by_year)} seasons)")
        print(f"   Season-level Pearson r  = {r_p:+.3f}  (p = {p_p_s}  {_stars(p_p).strip()})")
        if metric_header == "Mean pace":
            _pc = "po" if "Playoff" in ctx_label else "reg"
            FACTS.set(f"pace.{_pc}_r", r_p, "{:+.2f}", note=f"{_pc}: season-level pace-HCA Pearson r")
            FACTS.set(f"pace.{_pc}_r_p", p_p, "{:.2f}", note=f"{_pc}: pace-HCA Pearson p")
        print(f"   Season-level Spearman ρ = {r_s:+.3f}  (p = {p_s_s}  {_stars(p_s).strip()})")

        header = (f"   {'Era':<10} {metric_header:>{COL_W}} {'Home win%':>{COL_W}} "
                  f"{'n seasons':>{COL_W}}")
        print(f"\n{header}")
        print(f"   {'-'*10} {'-'*COL_W} {'-'*COL_W} {'-'*COL_W}")
        first_m_val = last_m_val = None
        for era_label, y1, y2, _ in nba.ERA_DEFS:
            era_years = [y for y in by_year["year"] if y1 <= y <= y2]
            era_rows = by_year[by_year["year"].isin(era_years)]
            if era_rows.empty:
                continue
            m_val = era_rows[agg_name].mean()
            m_pct = era_rows["home_pct"].mean()
            if first_m_val is None:
                first_m_val = m_val
            last_m_val = m_val
            print(f"   {era_label:<10} {m_val:>{COL_W}.1f}{metric_sep}{m_pct:>{COL_W}.1f}% "
                  f"{len(era_rows):>{COL_W}}")

        # Facts for the prose (§2.1/§3): three-point attempts went from ~7% of
        # shots in the 1980s to ~40% today.
        if ctx_label == "Regular season" and "3PA" in metric_header and last_m_val is not None:
            FACTS.set("tpa.early_share", first_m_val, "{:.0f}%",
                      note="Regular-season 3PA share of FGA, earliest era")
            FACTS.set("tpa.recent_share", last_m_val, "{:.0f}%",
                      note="Regular-season 3PA share of FGA, most recent era")

        p_bar = sub["home_win"].mean()
        try:
            m_biv = smf.logit(f"home_win ~ {col}", data=sub).fit(
                disp=0, cov_type="cluster", cov_kwds={"groups": sub["year"].values},
            )
            _warn_if_not_converged(m_biv, "_run_league_metric_analysis: m_biv")
            coef  = m_biv.params[col]
            pval  = m_biv.pvalues[col]
            pval_s = _fmt_p(pval)
            pp_per_10 = _pp(coef, p_bar) * 10
            ci_lo, ci_hi = _ci_lo_hi(m_biv, col, p_bar)
            print(f"\n   Game-level bivariate logistic  (N = {len(sub):,} games)")
            print(f"   coef = {coef:+.4f} log-odds {coef_desc}")
            print(f"   ≈ {pp_per_10:+.2f} pp per {scale_desc}  "
                  f"95% CI [{ci_lo*10:+.2f}, {ci_hi*10:+.2f}]")
            print(f"   p = {pval_s}  {_stars(pval).strip()}")
            if metric_header == "Mean pace" and ctx_label == "Regular season":
                FACTS.set("pace.bivariate", pp_per_10, "{:+.1f}",
                          note="Reg: pace bivariate HCA effect per 10 poss")
                FACTS.set("pace.realized_p",
                          "< 0.001" if pval < 0.001 else f"= {pval:.3f}",
                          note="Reg: realized-pace bivariate p-value (display)")
            if "3PA" in metric_header:
                _tctx = "po" if ctx_label == "Playoffs" else "reg"
                FACTS.set(f"tpa.effect_{_tctx}", pp_per_10, "{:+.2f}",
                          note=f"{ctx_label}: bivariate HCA effect per 10pp of 3PA rate")
                FACTS.set(f"tpa.effect_{_tctx}_mag", abs(pp_per_10), "{:.2f}",
                          note=f"{ctx_label}: bivariate 3PA effect magnitude per 10pp")
                FACTS.set(f"tpa.effect_{_tctx}_ci_lo", ci_lo * 10, "{:+.2f}",
                          note=f"{ctx_label}: 3PA effect 95% CI low")
                FACTS.set(f"tpa.effect_{_tctx}_ci_hi", ci_hi * 10, "{:+.2f}",
                          note=f"{ctx_label}: 3PA effect 95% CI high")
        except Exception:
            pass

        try:
            m_era = smf.logit(f"home_win ~ {col} + C(era)", data=sub).fit(
                disp=0, cov_type="cluster", cov_kwds={"groups": sub["year"].values},
            )
            _warn_if_not_converged(m_era, "_run_league_metric_analysis: m_era")
            coef_e  = m_era.params[col]
            pval_e  = m_era.pvalues[col]
            pval_e_s = _fmt_p(pval_e)
            pp_era = _pp(coef_e, p_bar) * 10
            _wlo_e, _whi_e = _ci_lo_hi(m_era, col, p_bar)
            print(f"\n   Controlling for era (within-era game-level effect):")
            print(f"   coef = {coef_e:+.4f}  (≈ {pp_era:+.2f} pp {era_coef_desc})  "
                  f"95% CI [{_wlo_e*10:+.2f}, {_whi_e*10:+.2f}]  "
                  f"p = {pval_e_s}  {_stars(pval_e).strip()}")
            if "3PA" in metric_header:
                _tctx = "po" if ctx_label == "Playoffs" else "reg"
                FACTS.set(f"tpa.within_{_tctx}", pp_era, "{:+.2f}",
                          note=f"{ctx_label}: within-era HCA effect per 10pp of 3PA rate")
                FACTS.set(f"tpa.within_{_tctx}_mag", abs(pp_era), "{:.2f}",
                          note=f"{ctx_label}: within-era 3PA effect magnitude per 10pp")
                FACTS.set(f"tpa.within_{_tctx}_p",
                          "< 0.001" if pval_e < 0.001 else f"= {pval_e:.3f}",
                          note=f"{ctx_label}: within-era 3PA effect p-value (display)")
                _wlo, _whi = _ci_lo_hi(m_era, col, p_bar)
                FACTS.set(f"tpa.within_{_tctx}_ci_lo", _wlo * 10, "{:+.2f}",
                          note=f"{ctx_label}: within-era 3PA effect 95% CI low (per 10pp)")
                FACTS.set(f"tpa.within_{_tctx}_ci_hi", _whi * 10, "{:+.2f}",
                          note=f"{ctx_label}: within-era 3PA effect 95% CI high (per 10pp)")
            if note_lines:
                for line in note_lines:
                    print(line)
        except Exception:
            pass

        if extra_block is not None:
            extra_block(df, is_po)

        print()
