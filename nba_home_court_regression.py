"""
nba_home_court_regression.py — statistical analysis of home court advantage.

Game-level statistical analyses on all cached data — one run_* function per
FINDINGS.md section that needs numbers: decline trend, format periods,
sequential R² decomposition, coefficient stability, rest/altitude/time zone,
rest buckets, margins, box-score and shot-zone differentials, referees,
travel, parity, 3PA rate, pace, series structure, and franchise HCA.

Called from nba_home_court_advantage.main() after the plots.
"""

from __future__ import annotations

import contextlib
import io
import sys
import warnings
import numpy as np
import pandas as pd
import statsmodels.api as sm
import statsmodels.formula.api as smf
from nba_api.stats.library.parameters import SeasonType

import nba_home_court_data as nba


# ── Feature construction ──────────────────────────────────────────────────────

def _classify_year(year: int, defs: list) -> str:
    for label, y1, y2, *_ in defs:
        if y1 <= year <= y2:
            return label
    return "other"


def _era_for_year(year: int) -> str:
    return _classify_year(year, nba.ERA_DEFS)


def _format_period_for_year(year: int) -> str:
    return _classify_year(year, nba.PLAYOFF_FORMAT_PERIODS)


def build_game_dataset() -> pd.DataFrame:
    """
    Build a game-level DataFrame with regression features from all cached CSVs.
    One row per game. rest_diff/tz_diff are NaN where data is unavailable
    (first game of each team's season, or unknown franchise time zone).
    """
    print("  Building game-level dataset from cache...", end="", flush=True)
    chunks: list[pd.DataFrame] = []

    for year in range(nba.START_YEAR, nba.END_YEAR + 1):
        for season_type, is_playoff in [(SeasonType.regular, False), ("Playoffs", True)]:
            if is_playoff and year in nba.SKIP_PLAYOFF_YEARS:
                continue

            df = nba._load_game_log(year, season_type)
            if df is None:
                continue

            df = nba._add_rest_days(df)

            merged = nba._merge_home_away_rows(df)
            if merged is None:
                continue

            merged = merged.copy()
            merged["home_win"]      = (merged["WL_home"] == "W").astype(int)
            merged["year"]          = year
            merged["is_playoff"]    = int(is_playoff)
            merged["era"]           = _era_for_year(year)
            merged["format_period"] = _format_period_for_year(year)
            merged["covid"]         = int(nba.short_label(year) in nba.COVID_SEASONS)
            merged["rest_diff"]     = merged["REST_home"] - merged["REST_away"]
            merged["altitude_home"] = merged["TEAM_NAME_home"].isin(nba.ALTITUDE_TEAMS).astype(int)

            home_tz = merged["TEAM_NAME_home"].map(nba.TEAM_TIMEZONES)
            away_tz = merged["TEAM_NAME_away"].map(nba.TEAM_TIMEZONES)
            merged["tz_diff"] = (home_tz - away_tz).abs().astype("float64")
            merged.loc[home_tz.isna() | away_tz.isna(), "tz_diff"] = np.nan

            diffs = nba._compute_box_differentials(merged)
            merged[diffs.columns] = diffs
            merged["margin"] = merged["PLUS_MINUS_home"]

            if {"TOV_home", "TOV_away", "REB_home", "REB_away"}.issubset(merged.columns):
                merged["tov_diff"] = merged["TOV_home"] - merged["TOV_away"]
                merged["reb_diff"] = merged["REB_home"] - merged["REB_away"]
            else:
                merged["tov_diff"] = np.nan
                merged["reb_diff"] = np.nan

            total_fga  = merged["FGA_home"]  + merged["FGA_away"]
            total_fg3a = merged["FG3A_home"] + merged["FG3A_away"]
            merged["tpa_rate_avg"] = 100.0 * total_fg3a / total_fga.replace(0, np.nan)

            pace_cols = {"OREB_home", "OREB_away", "TOV_home", "TOV_away"}
            if pace_cols.issubset(merged.columns):
                home_poss = (merged["FGA_home"] - merged["OREB_home"]
                             + merged["TOV_home"] + 0.44 * merged["FTA_home"])
                away_poss = (merged["FGA_away"] - merged["OREB_away"]
                             + merged["TOV_away"] + 0.44 * merged["FTA_away"])
                merged["pace_avg"] = (home_poss + away_poss) / 2.0

                # Expected pace: leave-one-out per-team mean so realized pace
                # can't reflect game-outcome endogeneity.
                hp_arr = home_poss.values.astype(float)
                ap_arr = away_poss.values.astype(float)
                hteams = merged["TEAM_NAME_home"].values
                ateams = merged["TEAM_NAME_away"].values
                team_tot: dict[str, float] = {}
                team_cnt: dict[str, int] = {}
                for t, p in zip(np.concatenate([hteams, ateams]),
                                np.concatenate([hp_arr, ap_arr])):
                    team_tot[t] = team_tot.get(t, 0.0) + float(p)
                    team_cnt[t] = team_cnt.get(t, 0) + 1
                loo_h = np.array(
                    [(team_tot[t] - p) / (team_cnt[t] - 1)
                     if team_cnt[t] > 1 else np.nan
                     for t, p in zip(hteams, hp_arr)]
                )
                loo_a = np.array(
                    [(team_tot[t] - p) / (team_cnt[t] - 1)
                     if team_cnt[t] > 1 else np.nan
                     for t, p in zip(ateams, ap_arr)]
                )
                merged["expected_pace"] = (loo_h + loo_a) / 2.0
            else:
                merged["pace_avg"] = np.nan
                merged["expected_pace"] = np.nan

            if is_playoff:
                gid_str = merged["GAME_ID"].apply(lambda x: str(int(float(x))))
                merged["game_in_series"] = gid_str.str[-1].astype(int).astype(float)
            else:
                merged["game_in_series"] = np.nan

            home_c = merged["TEAM_NAME_home"].map(nba.ARENA_COORDS)
            away_c = merged["TEAM_NAME_away"].map(nba.ARENA_COORDS)
            merged["distance_miles"] = [
                nba._haversine(a[0], a[1], h[0], h[1])
                if isinstance(a, tuple) and isinstance(h, tuple) else np.nan
                for a, h in zip(away_c, home_c)
            ]

            chunks.append(merged[[
                "GAME_ID",
                "home_win", "year", "is_playoff", "era", "format_period", "covid",
                "rest_diff", "altitude_home", "tz_diff",
                "foul_diff", "fg_pct_diff", "efg_pct_diff", "tpa_rate_diff",
                "fg3_pct_diff", "ft_pct_diff", "tov_diff", "reb_diff",
                "margin", "game_in_series", "distance_miles", "tpa_rate_avg",
                "pace_avg", "expected_pace",
                "TEAM_NAME_home", "TEAM_NAME_away",
            ]])

    if not chunks:
        print(" no data.")
        return pd.DataFrame()

    result = pd.concat(chunks, ignore_index=True)
    n_complete = len(result.dropna(subset=["rest_diff", "tz_diff"]))
    print(f" {len(result):,} game rows ({n_complete:,} with complete features).")
    return result


def _add_quality_diff(df: pd.DataFrame) -> pd.DataFrame:
    """Add quality_diff = home RS win% - away RS win% (same season) to playoff rows.

    Playoff rest is earned by advancing quickly, which correlates with team strength,
    so quality_diff controls for that confound in playoff rest analyses.
    """
    rs = df[df["is_playoff"] == 0]
    home_records = (
        rs.groupby(["year", "TEAM_NAME_home"])["home_win"]
        .agg(wins="sum", games="count")
        .rename_axis(index={"TEAM_NAME_home": "team"})
    )
    away_records = (
        rs.groupby(["year", "TEAM_NAME_away"])["home_win"]
        .agg(losses="sum", games="count")
        .rename_axis(index={"TEAM_NAME_away": "team"})
    )
    away_records["wins"] = away_records["games"] - away_records["losses"]
    away_records = away_records.drop(columns="losses")

    all_records = pd.concat([home_records, away_records]).groupby(
        level=["year", "team"]
    ).sum()
    all_records["rs_winpct"] = all_records["wins"] / all_records["games"]
    winpct = all_records["rs_winpct"]  # MultiIndex: (year, team)

    po_mask = df["is_playoff"] == 1
    po = df[po_mask]
    df = df.copy()
    df.loc[po_mask, "quality_diff"] = (
        po.apply(
            lambda r: (
                winpct.get((r["year"], r["TEAM_NAME_home"]), np.nan)
                - winpct.get((r["year"], r["TEAM_NAME_away"]), np.nan)
            ),
            axis=1,
        ).values
    )
    df.loc[~po_mask, "quality_diff"] = np.nan
    return df


# ── Print helpers ─────────────────────────────────────────────────────────────

_W = 72


def _header(title: str) -> None:
    bar = "═" * _W
    print(f"\n{bar}\n{title}\n{bar}")


def _section(title: str) -> None:
    pad = max(0, _W - 5 - len(title))
    print(f"\n─── {title} {'─' * pad}")


def _stars(p: float) -> str:
    if p < 0.001: return "***"
    if p < 0.01:  return " **"
    if p < 0.05:  return "  *"
    return "   "


def _fmt_p(p: float) -> str:
    if np.isnan(p):
        return "n/a"
    return "<0.001" if p < 0.001 else f"{p:.3f}"


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
    league_mean = float(hcas.mean())

    samp_vars = np.array([
        1e4 * (
            (stats[t]["home_pct"] / 100.0) * (1.0 - stats[t]["home_pct"] / 100.0) / stats[t]["n_home"]
            + (stats[t]["road_pct"] / 100.0) * (1.0 - stats[t]["road_pct"] / 100.0) / stats[t]["n_road"]
        )
        for t in teams
    ])

    obs_var = float(np.var(hcas, ddof=1))
    mean_sv = float(samp_vars.mean())
    true_var = max(0.0, obs_var - mean_sv)

    shrunken: dict[str, float] = {}
    ci_hw: dict[str, float] = {}
    for i, t in enumerate(teams):
        sv_i = samp_vars[i]
        w = true_var / (true_var + sv_i) if true_var > 0 else 0.0
        shrunken[t] = w * stats[t]["hca"] + (1.0 - w) * league_mean
        ci_hw[t] = 1.96 * float(np.sqrt(sv_i))
    return shrunken, ci_hw


# ── Analysis 1: Overall decline ───────────────────────────────────────────────

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

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
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
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
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
        print()


# ── Analysis: Playoff format periods ──────────────────────────────────────────

def run_format_period_analysis(df: pd.DataFrame) -> None:
    """Playoff home win % by format period — pairwise tests between consecutive
    periods, plus a logistic model testing whether the format changes add a
    level shift beyond the secular year trend."""
    from scipy.stats import chi2
    from statsmodels.stats.proportion import proportions_ztest

    po = df[df["is_playoff"] == 1]
    if po.empty:
        return
    fmt_ref = nba.PLAYOFF_FORMAT_PERIODS[2][0]    # "2003–13"
    p_bar = po["home_win"].mean()

    _section("PLAYOFF FORMAT PERIODS — DID THE SCHEDULING CHANGES MATTER?")
    print("   Playoff home win % by format period (1985, 2003, 2014 changes).")
    print("   Pairwise tests compare consecutive periods; the trend-controlled model")
    print("   asks whether format adds a level shift beyond the secular year trend.\n")

    counts: dict[str, tuple[int, int]] = {}
    print(f"   {'Period':<10}  {'N games':>8}  {'Home win %':>11}")
    print(f"   {'─'*10}  {'─'*8}  {'─'*11}")
    for label, _, _, _ in nba.PLAYOFF_FORMAT_PERIODS:
        sub = po[po["format_period"] == label]
        if sub.empty:
            continue
        wins, n = int(sub["home_win"].sum()), len(sub)
        counts[label] = (wins, n)
        print(f"   {label:<10}  {n:>8,}  {100.0 * wins / n:>10.1f}%")

    print(f"\n   Consecutive periods — two-proportion z-tests:")
    avail = [lbl for lbl, *_ in nba.PLAYOFF_FORMAT_PERIODS if lbl in counts]
    for a, b in zip(avail, avail[1:]):
        (wa, na), (wb, nb) = counts[a], counts[b]
        z, p = proportions_ztest([wa, wb], [na, nb])
        diff = 100.0 * (wb / nb - wa / na)
        p_s = _fmt_p(p)
        print(f"   {a:>8} → {b:<8}  {diff:+5.1f} pp   "
              f"(z = {z:+.2f}, p = {p_s}  {_stars(p).strip()})")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m_year = smf.logit("home_win ~ year", data=po).fit(disp=0)
        m_fmt  = smf.logit(
            f"home_win ~ year + C(format_period, Treatment('{fmt_ref}'))",
            data=po,
        ).fit(disp=0)

    print(f"\n   Trend-controlled logistic: home_win ~ year + format_period")
    print(f"   (reference period = {fmt_ref})\n")
    print(f"   {'Predictor':<28}  {'log-odds':>8}  {'≈pp':>6}  {'p':>8}  {'':3}")
    print(f"   {'─'*28}  {'─'*8}  {'─'*6}  {'─'*8}  {'─'*3}")
    for name in m_fmt.params.index:
        if name == "Intercept":
            continue
        coef, pval = m_fmt.params[name], m_fmt.pvalues[name]
        label = (name
                 .replace(f"C(format_period, Treatment('{fmt_ref}'))[T.", "format: ")
                 .replace("]", "")
                 .replace("year", "year trend (per yr)"))
        pval_s = _fmt_p(pval)
        print(f"   {label:<28}  {coef:+8.3f}  {_pp(coef, p_bar):+6.1f}  "
              f"{pval_s:>8}  {_stars(pval)}")

    lr    = 2.0 * (m_fmt.llf - m_year.llf)
    dfree = int(m_fmt.df_model - m_year.df_model)
    p_lr  = chi2.sf(lr, dfree)
    p_lr_s = _fmt_p(p_lr)
    print(f"\n   LR test — format dummies jointly vs. year-only model: "
          f"χ²({dfree}) = {lr:.2f},  p = {p_lr_s}  {_stars(p_lr).strip()}")

    last_label = nba.PLAYOFF_FORMAT_PERIODS[-1][0]
    key = f"C(format_period, Treatment('{fmt_ref}'))[T.{last_label}]"
    c14 = m_fmt.params.get(key, np.nan)
    p14 = m_fmt.pvalues.get(key, np.nan)
    if not np.isnan(c14):
        if p14 < 0.05:
            print(f"\n   ► The {last_label} period sits {_pp(c14, p_bar):+.1f} pp from "
                  f"the {fmt_ref} level even after")
            print(f"     the year trend — the 2014 format change had a real level effect")
            print(f"     beyond the secular decline.")
        else:
            print(f"\n   ► After controlling for the year trend, the {last_label} dummy is "
                  f"not significant")
            print(f"     (p = {p14:.3f}) — the post-2014 drop is consistent with the secular")
            print(f"     decline passing through, not a distinct format-change effect.")


# ── Analysis: Rule-change era significance ────────────────────────────────────

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

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m_year = smf.logit("home_win ~ year", data=sub).fit(disp=0)
            m_era  = smf.logit(
                f"home_win ~ year + C(era, Treatment('{era_ref}'))",
                data=sub,
            ).fit(disp=0)

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


# ── Shapley R² helper ─────────────────────────────────────────────────────────

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
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for size in range(n + 1):
            for sub in combinations(names, size):
                key     = frozenset(sub)
                formula = ("home_win ~ 1" if not sub else
                           "home_win ~ " + " + ".join(block_terms[b] for b in sub))
                try:
                    cache[key] = _mcfadden(smf.logit(formula, data=reg).fit(disp=0))
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


# ── Analysis 2: Sequential decomposition (regular season) ─────────────────────

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
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for label, formula in steps:
            fitted.append((label, smf.logit(formula, data=reg).fit(
                disp=0, cov_type="cluster", cov_kwds={"groups": reg["year"].values},
            )))

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


# ── Analysis 2: Pre/post-2014 coefficient stability (regular season) ──────────

def run_stability_analysis(df: pd.DataFrame) -> None:
    _section("PRE/POST-2014 COEFFICIENT STABILITY  (regular season only)")
    print("   Do rest, altitude, and time zone effects change after the 2014 Finals format shift?")
    print("   Stable coefficients → those factors didn't drive the post-2014 change.\n")

    rs    = df[df["is_playoff"] == 0].dropna(subset=["rest_diff", "tz_diff"])
    pre   = rs[rs["year"] <  2014]
    post  = rs[rs["year"] >= 2014]
    formula = "home_win ~ rest_diff + altitude_home + tz_diff"

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m_pre  = smf.logit(formula, data=pre).fit(disp=0)
        m_post = smf.logit(formula, data=post).fit(disp=0)

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
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            m_int = smf.logit(
                "home_win ~ (rest_diff + altitude_home + tz_diff) * post2014",
                data=rs2,
            ).fit(disp=0)
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


# ── Analysis 4: Rest, altitude, time zone — do they matter? ──────────────────

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
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for raw, label in factors:
            m_re = smf.logit(f"home_win ~ {raw}", data=re).fit(disp=0)
            m_po = smf.logit(f"home_win ~ {raw}", data=po).fit(disp=0)
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
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                m_q = smf.logit(
                    "home_win ~ rest_diff + quality_diff", data=po_q
                ).fit(disp=0)
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


# ── Analysis: Rest-differential buckets and era stability ─────────────────────

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
        for label, cond in buckets:
            b = sub[cond(sub["rest_diff"])]
            if b.empty:
                continue
            wins, n = int(b["home_win"].sum()), len(b)
            pct = 100.0 * wins / n
            table.append([wins, n - wins])
            print(f"   {label:<16}  {n:>8,}  {pct:>10.1f}%  {pct - p_bar:>+12.1f} pp")

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
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                try:
                    m = smf.logit("home_win ~ rest_diff", data=era_rows).fit(disp=0)
                except Exception:
                    continue
            c, p = m.params["rest_diff"], m.pvalues["rest_diff"]
            pb = era_rows["home_win"].mean()
            p_s = _fmt_p(p)
            print(f"   {era_label:<12}  {len(era_rows):>7,}  {c:>+13.3f}  "
                  f"{_pp(c, pb):>+8.1f}  {p_s:>8}  {_stars(p)}")

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m_add = smf.logit("home_win ~ rest_diff + C(era)", data=sub).fit(disp=0)
                m_int = smf.logit("home_win ~ rest_diff * C(era)", data=sub).fit(disp=0)
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


# ── Analysis 4: Foul & shooting differentials by era ─────────────────────────

def run_differential_analysis(df: pd.DataFrame) -> None:
    col_keys   = ["foul_diff", "fg_pct_diff", "efg_pct_diff", "tpa_rate_diff",
                  "fg3_pct_diff", "ft_pct_diff"]
    col_labels = ["Foul diff", "FG% (pp)", "eFG% (pp)", "3PA rate (pp)",
                  "3P% (pp)", "FT% (pp)"]
    COL_W = 14

    _section("FOUL & SHOOTING DIFFERENTIALS BY ERA  (home minus away, per game)")
    print("   Negative foul diff = refs call fewer fouls on the home team.")
    print("   Trend = slope of trend line (change per season year); pp = percentage points.\n")

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
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = smf.ols(f"{key} ~ year", data=data).fit()
            coef = m.params["year"]
            pval = m.pvalues["year"]
            cell = f"{coef:>+{COL_W - 3}.3f}{_stars(pval)}"
            trend_row += cell
        print(trend_row)
        print()


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
    channels = [
        ("efg_pct_diff", "eFG% diff (pp)"),
        ("foul_diff",    "Foul diff"),
        ("tov_diff",     "TOV diff"),
        ("reb_diff",     "REB diff"),
    ]
    keys = [k for k, _ in channels]
    rhs = " + ".join(keys)
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

    for label, sub in [
        ("Regular season", df[df["is_playoff"] == 0]),
        ("Playoffs",       df[df["is_playoff"] == 1]),
    ]:
        d = sub.dropna(subset=keys + ["home_win", "year"])
        if len(d) < 100:
            print(f"   {label}: insufficient data.\n")
            continue

        hw = d["home_win"].mean() * 100
        level = hw - 50.0

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
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

        print(f"   {label}  (N = {len(d):,} games, home win % = {hw:.1f}, "
              f"level above coin flip = {level:+.1f} pp)")
        print(f"   Channel-model R² = {m_chan.rsquared:.3f} — share of game-outcome "
              f"variance the four channels carry.\n")

        print(f"   Level decomposition  (coef × mean diff):")
        print(f"   {'Channel':<16}  {'Mean diff':>10}  {'pp per unit':>12}  "
              f"{'Contribution':>13}  {'% of level':>10}")
        print(f"   {'─'*16}  {'─'*10}  {'─'*12}  {'─'*13}  {'─'*10}")
        for k, lbl in channels:
            b_pp = m_chan.params[k] * 100
            mu = d[k].mean()
            contrib = b_pp * mu
            stars = _stars(m_chan.pvalues[k]).strip()
            print(f"   {lbl:<16}  {mu:>+10.2f}  {b_pp:>+9.2f} {stars:<3}"
                  f"{contrib:>+10.1f} pp  {100*contrib/level:>9.0f}%")
        resid_level = m_chan.params["Intercept"] * 100 - 50.0
        print(f"   {'─'*16}  {'─'*10}  {'─'*12}  {'─'*13}  {'─'*10}")
        print(f"   {'Unexplained':<16}  {'':>10}  {'':>12}  {resid_level:>+10.1f} pp  "
              f"{100*resid_level/level:>9.0f}%")

        t_total = m_year.params["year"] * 100
        t_resid = m_full.params["year"] * 100
        p_total = m_year.pvalues["year"]

        print(f"\n   Trend decomposition  (pp of home win % per year):")
        print(f"   Total trend (home_win ~ year): {t_total:+.3f} pp/yr  "
              f"(p = {_fmt_p(p_total)}  {_stars(p_total).strip()})\n")
        print(f"   {'Channel':<16}  {'Trend in diff/yr':>16}  {'Contribution':>15}  "
              f"{'% of trend':>10}")
        print(f"   {'─'*16}  {'─'*16}  {'─'*15}  {'─'*10}")
        mediated = 0.0
        for k, lbl in channels:
            gamma = chan_trends[k].params["year"]
            stars = _stars(chan_trends[k].pvalues["year"]).strip()
            contrib = m_full.params[k] * 100 * gamma
            mediated += contrib
            print(f"   {lbl:<16}  {gamma:>+12.4f} {stars:<3}  {contrib:>+9.4f} pp/yr  "
                  f"{100*contrib/t_total:>9.0f}%")
        print(f"   {'─'*16}  {'─'*16}  {'─'*15}  {'─'*10}")
        print(f"   {'Sum, channels':<16}  {'':>16}  {mediated:>+9.4f} pp/yr  "
              f"{100*mediated/t_total:>9.0f}%")
        print(f"   {'Unmediated':<16}  {'':>16}  {t_resid:>+9.4f} pp/yr  "
              f"{100*t_resid/t_total:>9.0f}%")

        pct_level = 100 * (level - resid_level) / level
        pct_trend = 100 * mediated / t_total
        print(f"\n   ► {label}: channels carry {pct_level:.0f}% of the HCA level "
              f"and {pct_trend:.0f}% of its decline.")
        if label == "Playoffs":
            print("   ► Note: playoff differentials fold in the seed-quality gap (the")
            print("     home team is usually the better team) — see the seeding")
            print("     decomposition for that control.")
        print()

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
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
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


# ── Analysis 6: Shot zone differentials ──────────────────────────────────────

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
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = smf.ols("val ~ year", data=tdf).fit()
            c    = m.params["year"]
            pval = m.pvalues["year"]
            trend_row += f"{c:>+{COL_W - 3}.3f}{_stars(pval)}"
        print(trend_row)
        print()


# ── Analysis 7: Win margin trends ─────────────────────────────────────────────

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
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
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


# ── Analysis 4b: Unconditional quantile regression on margins ─────────────────

def run_quantile_margin_analysis(df: pd.DataFrame) -> None:
    """Unconditional quantile regression — tests whether 'polarization' in §1
    is genuine distribution widening or a composition artifact of the declining
    home win rate. (PLAN-STATS item 3.)

    All quantiles drifting down in parallel → pure level effect (wins appeared
    bigger / losses appeared worse only because marginal games changed sides).
    Lower quantiles declining while upper quantiles rise or hold → genuine
    variance widening (polarization confirmed).
    """
    _section("WIN MARGIN POLARIZATION — UNCONDITIONAL QUANTILE REGRESSION  (§1 check)")
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
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
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
            print(f"\n   IQR change rate (Q90 − Q10 slope diff): {spread_chg:+.3f} pts/yr")
            if spread_chg > 0.02:
                print(f"   ► Q90 rises / Q10 falls — genuine variance widening (polarization confirmed).")
                print(f"     The conditional-on-outcome divergence in §1 reflects a real change in")
                print(f"     distribution shape, not just a composition effect.")
            elif spread_chg < -0.02:
                print(f"   ► Q90 falls / Q10 rises — distribution compressing.")
            else:
                all_slopes = list(slopes.values())
                rng = max(all_slopes) - min(all_slopes)
                if rng < 0.05:
                    print(f"   ► All quantiles shift in parallel (spread change ≈ 0).")
                    print(f"     The §1 conditional divergence is a composition artifact:")
                    print(f"     as home win % declines, marginal games flip sides and push")
                    print(f"     the conditional-win and conditional-loss means apart without")
                    print(f"     any genuine change in the distribution's shape.")
                else:
                    print(f"   ► Mixed pattern; individual slopes above are the primary result.")
        print()


# ── Analysis 6: Competitive balance / parity ─────────────────────────────────

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
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
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


# ── Analysis 7: Playoff series structure ─────────────────────────────────────

def run_series_breakdown(df: pd.DataFrame) -> None:
    from scipy.stats import chi2_contingency

    po = df[df["is_playoff"] == 1].dropna(subset=["game_in_series"]).copy()
    po["game_in_series"] = po["game_in_series"].astype(int)
    po = po[po["game_in_series"].between(1, 7)]

    _section("PLAYOFF SERIES STRUCTURE — HOME WIN % BY GAME NUMBER")
    print("   Does home court advantage vary by game number within a series (G1–G7)?")
    print("   G1/G2 at higher seed, G3/G4 at lower seed, then alternates (2-2-1-1-1 format).\n")

    wins_by_game  : dict[int, int] = {}
    total_by_game : dict[int, int] = {}
    g1_pct: float | None = None

    print(f"   {'Game':>6}  {'N games':>8}  {'Home win %':>11}  {'vs. G1':>8}")
    print(f"   {'─'*6}  {'─'*8}  {'─'*11}  {'─'*8}")

    for gnum in range(1, 8):
        sub = po[po["game_in_series"] == gnum]
        if sub.empty:
            continue
        n    = len(sub)
        wins = int(sub["home_win"].sum())
        pct  = 100.0 * wins / n
        wins_by_game[gnum]  = wins
        total_by_game[gnum] = n
        if g1_pct is None:
            g1_pct = pct
        diff   = pct - g1_pct
        diff_s = f"{diff:+.1f} pp" if diff != 0 else "—"
        print(f"   {'G'+str(gnum):>6}  {n:>8,}  {pct:>10.1f}%  {diff_s:>8}")

    game_nums = sorted(wins_by_game)

    if len(game_nums) >= 2:
        table = [[wins_by_game[g], total_by_game[g] - wins_by_game[g]] for g in game_nums]
        chi2_stat, p_chi, dof, _ = chi2_contingency(table)
        p_chi_s = _fmt_p(p_chi)
        print(f"\n   Chi-square test (H0: home win % uniform across all game numbers):")
        print(f"   χ²({dof}) = {chi2_stat:.2f},  p = {p_chi_s}  {_stars(p_chi).strip()}")

    rows = pd.DataFrame({
        "game_num": game_nums,
        "home_pct": [100.0 * wins_by_game[g] / total_by_game[g] for g in game_nums],
        "n":        [float(total_by_game[g]) for g in game_nums],
    })
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = smf.ols("home_pct ~ game_num", data=rows, weights=rows["n"]).fit()
    coef = m.params["game_num"]
    pval = m.pvalues["game_num"]
    pval_s = _fmt_p(pval)
    print(f"\n   Weighted trend line across game numbers: {coef:+.2f} pp/game  "
          f"(p = {pval_s}  {_stars(pval).strip()})")
    print(f"   (Positive = home win % rises as the series goes deeper)")

    if 7 in total_by_game and g1_pct is not None:
        g7_pct  = 100.0 * wins_by_game[7] / total_by_game[7]
        g7_diff = g7_pct - g1_pct
        print(f"\n   ► G7 home win % = {g7_pct:.1f}%  (vs. G1 = {g1_pct:.1f}%, diff = {g7_diff:+.1f} pp)")
        print(f"     G7 n = {total_by_game[7]:,} games (series that went to 7)")


# ── Analysis: Playoff HCA — seeding quality decomposition ────────────────────

def run_playoff_quality_decomposition(df: pd.DataFrame) -> None:
    """Decompose the playoff HCA year trend into team-quality vs. true home-court.

    Compares year coefficients before and after controlling for quality_diff
    (home RS win% − away RS win%). If the year coefficient shrinks substantially,
    the decline is partly explained by seed-quality gaps compressing; if it
    barely moves, the decline is genuine HCA erosion.
    """
    po = df[(df["is_playoff"] == 1)].dropna(subset=["quality_diff"])
    if po.empty:
        _section("PLAYOFF HCA — SEEDING QUALITY DECOMPOSITION")
        print("   No playoff data with quality_diff available.\n")
        return

    p_bar = po["home_win"].mean()

    _section("PLAYOFF HCA — SEEDING QUALITY DECOMPOSITION")
    print("   Does the playoff HCA decline reflect true home-court weakening, or do")
    print("   better seeds simply fail to dominate lower seeds as they once did?")
    print("   quality_diff = home RS win% − away RS win% (same season).")
    print(f"   N = {len(po):,} playoff games with complete quality data.\n")

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m_year = smf.logit("home_win ~ year", data=po).fit(disp=0)
        m_qual = smf.logit("home_win ~ quality_diff", data=po).fit(disp=0)
        m_full = smf.logit("home_win ~ year + quality_diff", data=po).fit(disp=0)

    c_yr_base  = m_year.params["year"]
    c_yr_full  = m_full.params["year"]
    p_yr_base  = m_year.pvalues["year"]
    p_yr_full  = m_full.pvalues["year"]
    p_qual_biv = m_qual.pvalues["quality_diff"]
    p_qual_ful = m_full.pvalues["quality_diff"]

    pp_yr_base  = _pp(c_yr_base,  p_bar)
    pp_yr_full  = _pp(c_yr_full,  p_bar)
    pp_qual_biv = _pp(m_qual.params["quality_diff"], p_bar)
    pp_qual_ful = _pp(m_full.params["quality_diff"], p_bar)

    pct_retained = 100.0 * c_yr_full / c_yr_base if c_yr_base != 0 else np.nan

    print(f"   Model comparison — year trend before and after quality control:\n")
    print(f"   {'Model':<30}  {'year (pp/yr)':>13}  {'p':>8}  {'McF. R²':>8}")
    print(f"   {'─'*30}  {'─'*13}  {'─'*8}  {'─'*8}")
    print(f"   {'Year only':<30}  {pp_yr_base:>+13.3f}  {_fmt_p(p_yr_base):>8}  {_mcfadden(m_year):>8.4f}")
    print(f"   {'Quality only':<30}  {'—':>13}  {'—':>8}  {_mcfadden(m_qual):>8.4f}")
    print(f"   {'Year + quality_diff':<30}  {pp_yr_full:>+13.3f}  {_fmt_p(p_yr_full):>8}  {_mcfadden(m_full):>8.4f}")

    print(f"\n   quality_diff (bivariate):  {pp_qual_biv:>+.2f} pp per unit  "
          f"(p = {_fmt_p(p_qual_biv)}  {_stars(p_qual_biv).strip()})")
    print(f"   quality_diff (full model): {pp_qual_ful:>+.2f} pp per unit  "
          f"(p = {_fmt_p(p_qual_ful)}  {_stars(p_qual_ful).strip()})")
    print(f"   Year trend retained after quality control: {pct_retained:.0f}%")
    print(f"   Absorbed by quality_diff: {100.0 - pct_retained:.0f}%")

    # Has quality_diff itself trended over time?
    by_year = po.groupby("year")["quality_diff"].mean().reset_index()
    by_year.columns = ["year", "mean_qdiff"]
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m_qdrift = smf.ols("mean_qdiff ~ year", data=by_year).fit()
    c_qdrift = m_qdrift.params["year"]
    p_qdrift = m_qdrift.pvalues["year"]

    print(f"\n   Has the seed-quality gap itself trended over time?")
    print(f"   Trend in mean quality_diff per season: {c_qdrift:>+.5f} per yr  "
          f"(p = {_fmt_p(p_qdrift)}  {_stars(p_qdrift).strip()},  R² = {m_qdrift.rsquared:.4f})")

    print(f"\n   Era breakdown — mean quality_diff and playoff home win %:")
    print(f"   {'Era':<12}  {'N':>6}  {'Mean quality_diff':>18}  {'Home win %':>11}")
    print(f"   {'─'*12}  {'─'*6}  {'─'*18}  {'─'*11}")
    for era_label, y1, y2, _ in nba.ERA_DEFS:
        era_rows = po[(po["year"] >= y1) & (po["year"] <= y2)]
        if era_rows.empty:
            continue
        mq = era_rows["quality_diff"].mean()
        hw = era_rows["home_win"].mean() * 100
        print(f"   {era_label:<12}  {len(era_rows):>6,}  {mq:>+18.4f}  {hw:>10.1f}%")

    # G3/G4: lower seed at home, quality_diff < 0 → pure venue effect
    g34 = po[po["game_in_series"].isin([3.0, 4.0])].dropna(subset=["quality_diff"])
    g34_neg = g34[g34["quality_diff"] < 0]
    if not g34_neg.empty:
        hw_g34 = g34_neg["home_win"].mean() * 100
        print(f"\n   Lower-seed-at-home check (G3+G4 where quality_diff < 0):")
        print(f"   N = {len(g34_neg):,} games  Home win % = {hw_g34:.1f}%")
        print(f"   ► Even when the objectively weaker team is at home, they win {hw_g34:.0f}% — pure venue effect.")

    if np.isnan(pct_retained):
        pass
    elif 100.0 - pct_retained < 15:
        print(f"\n   ► Quality control barely moves the year coefficient ({pct_retained:.0f}% retained) —")
        print(f"     the playoff decline is primarily genuine home-court weakening, not seed compression.")
    elif 100.0 - pct_retained < 40:
        print(f"\n   ► Partial explanation: {100.0 - pct_retained:.0f}% of the trend absorbed by quality_diff —")
        print(f"     some decline reflects seed gaps compressing, but most is genuine HCA erosion.")
    else:
        print(f"\n   ► Substantial absorption: {100.0 - pct_retained:.0f}% of the trend absorbed by quality_diff —")
        print(f"     a major part of the playoff decline reflects seed-quality compression, not pure HCA.")


# ── Analysis 8: Travel distance ───────────────────────────────────────────────

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

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            try:
                m = smf.logit("home_win ~ distance_miles", data=sub).fit(
                    disp=0, cov_type="cluster", cov_kwds={"groups": sub["year"].values},
                )
                coef = m.params["distance_miles"]
                pval = m.pvalues["distance_miles"]
                pval_s = _fmt_p(pval)
                pp_per_100mi = _pp(coef, p_bar) * 100
                ci_lo, ci_hi = _ci_lo_hi(m, "distance_miles", p_bar)
                print(f"\n   Bivariate logistic: coef = {coef:+.5f} log-odds/mi  "
                      f"(≈{pp_per_100mi:+.2f} pp per 100 mi,  "
                      f"95% CI [{ci_lo*100:+.2f}, {ci_hi*100:+.2f}]),  "
                      f"p = {pval_s}  {_stars(pval).strip()}")
            except Exception:
                pass
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
        print(f"   Season-level Spearman ρ = {r_s:+.3f}  (p = {p_s_s}  {_stars(p_s).strip()})")

        header = (f"   {'Era':<10} {metric_header:>{COL_W}} {'Home win%':>{COL_W}} "
                  f"{'n seasons':>{COL_W}}")
        print(f"\n{header}")
        print(f"   {'-'*10} {'-'*COL_W} {'-'*COL_W} {'-'*COL_W}")
        for era_label, y1, y2, _ in nba.ERA_DEFS:
            era_years = [y for y in by_year["year"] if y1 <= y <= y2]
            era_rows = by_year[by_year["year"].isin(era_years)]
            if era_rows.empty:
                continue
            m_val = era_rows[agg_name].mean()
            m_pct = era_rows["home_pct"].mean()
            print(f"   {era_label:<10} {m_val:>{COL_W}.1f}{metric_sep}{m_pct:>{COL_W}.1f}% "
                  f"{len(era_rows):>{COL_W}}")

        p_bar = sub["home_win"].mean()
        try:
            m_biv = smf.logit(f"home_win ~ {col}", data=sub).fit(
                disp=0, cov_type="cluster", cov_kwds={"groups": sub["year"].values},
            )
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
        except Exception:
            pass

        try:
            m_era = smf.logit(f"home_win ~ {col} + C(era)", data=sub).fit(
                disp=0, cov_type="cluster", cov_kwds={"groups": sub["year"].values},
            )
            coef_e  = m_era.params[col]
            pval_e  = m_era.pvalues[col]
            pval_e_s = _fmt_p(pval_e)
            pp_era = _pp(coef_e, p_bar) * 10
            print(f"\n   Controlling for era (within-era game-level effect):")
            print(f"   coef = {coef_e:+.4f}  (≈ {pp_era:+.2f} pp {era_coef_desc})  "
                  f"p = {pval_e_s}  {_stars(pval_e).strip()}")
            if note_lines:
                for line in note_lines:
                    print(line)
        except Exception:
            pass

        if extra_block is not None:
            extra_block(df, is_po)

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
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m_biv_ep = smf.logit("home_win ~ expected_pace", data=sub_ep).fit(
                        disp=0, cov_type="cluster", cov_kwds={"groups": sub_ep["year"].values},
                    )
                c_ep = m_biv_ep.params["expected_pace"]
                p_ep = m_biv_ep.pvalues["expected_pace"]
                print(f"   Bivariate: coef = {c_ep:+.4f}  "
                      f"(≈ {_pp(c_ep, p_bar_ep) * 10:+.2f} pp per 10 poss)  "
                      f"p = {_fmt_p(p_ep)}  {_stars(p_ep).strip()}")
            except Exception:
                pass
            try:
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m_era_ep = smf.logit(
                        "home_win ~ expected_pace + C(era)", data=sub_ep
                    ).fit(
                        disp=0, cov_type="cluster", cov_kwds={"groups": sub_ep["year"].values},
                    )
                c_era_ep = m_era_ep.params["expected_pace"]
                p_era_ep = m_era_ep.pvalues["expected_pace"]
                pp_era_ep = _pp(c_era_ep, p_bar_ep) * 10
                print(f"   Within-era: coef = {c_era_ep:+.4f}  "
                      f"(≈ {pp_era_ep:+.2f} pp per 10 poss)  "
                      f"p = {_fmt_p(p_era_ep)}  {_stars(p_era_ep).strip()}")
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


# ── Analysis 13: Franchise home court advantage ───────────────────────────────

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
        print()


# ── Analysis: Franchise HCA consistency (regular season vs. playoffs) ─────────

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


# ── Analysis 14: Referee crew home foul bias ─────────────────────────────────

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


# ── Entry point ───────────────────────────────────────────────────────────────

_RESULTS_PATH = "RESULTS.md"


def run() -> None:
    buf = io.StringIO()

    with contextlib.redirect_stdout(buf):
        _header("NBA HOME COURT ADVANTAGE — REGRESSION ANALYSIS")
        print("Game-level logistic regression. Outcome: home_win (1/0) per game.")
        print("All data from cache/ — same source as the plots above.\n")

        df = build_game_dataset()
        if df.empty:
            print("No game data found in cache/. Run the main script first to populate it.")
            return
        df = _add_quality_diff(df)

        parity_seasons, parity_std = nba.compute_parity_stats(
            nba.START_YEAR, nba.END_YEAR, "Regular Season"
        )
        reg_by_year = df[df["is_playoff"] == 0].groupby("year")["home_win"].mean() * 100
        reg_pcts_by_season = {nba.short_label(y): float(pct) for y, pct in reg_by_year.items()}
        reg_seasons_sorted = sorted(reg_pcts_by_season)
        reg_pcts_sorted    = [reg_pcts_by_season[s] for s in reg_seasons_sorted]

        reg_zone_seasons, reg_zone_stats = nba.compute_shot_zone_stats(
            nba.START_YEAR, nba.END_YEAR, "Regular Season"
        )
        po_zone_seasons, po_zone_stats = nba.compute_shot_zone_stats(
            nba.START_YEAR, nba.END_YEAR, "Playoffs", skip_years=nba.SKIP_PLAYOFF_YEARS
        )

        # §1 The 40-Year Decline (magnitude, shape/timing, blowout polarization)
        run_decline_trend(df)
        run_margin_analysis(df)
        run_quantile_margin_analysis(df)

        # §2 What Creates Home Court Advantage
        run_differential_analysis(df)
        run_mediation_analysis(df)
        run_rest_bucket_analysis(df)
        run_factor_summary(df)

        # §3 What's Driving the Decline
        run_sequential_decomposition(df)
        run_stability_analysis(df)
        ref_df = nba.fetch_all_referee_data(
            nba.START_YEAR, nba.END_YEAR, "Playoffs",
            skip_years=nba.SKIP_PLAYOFF_YEARS,
        )
        if ref_df is not None:
            ref_bias_stats = nba.compute_referee_bias_stats(
                ref_df, nba.START_YEAR, nba.END_YEAR, "Playoffs",
                skip_years=nba.SKIP_PLAYOFF_YEARS, min_games=50,
            )
            if ref_bias_stats:
                run_referee_analysis(ref_bias_stats)
            else:
                print("   No officials met the minimum-games threshold.\n")
        else:
            print("   No cached referee data — run the analysis first to fetch it.\n")
        run_shot_zone_analysis(reg_zone_seasons, reg_zone_stats, po_zone_seasons, po_zone_stats)
        run_3pa_analysis(df)

        # §4 What Didn't Drive the Change (rule changes lead, then travel/pace/parity)
        run_era_analysis(df)
        run_travel_analysis(df)
        run_pace_analysis(df)
        run_parity_correlation(parity_seasons, parity_std, reg_seasons_sorted, reg_pcts_sorted)

        # §5 The Playoff Picture
        run_series_breakdown(df)
        run_playoff_quality_decomposition(df)
        run_format_period_analysis(df)
        reg_hca_stats = nba.compute_team_hca_stats(
            nba.START_YEAR, nba.END_YEAR, "Regular Season", min_games=50,
        )
        po_hca_stats = nba.compute_team_hca_stats(
            nba.START_YEAR, nba.END_YEAR, "Playoffs",
            skip_years=nba.SKIP_PLAYOFF_YEARS, min_games=20,
        )
        run_team_hca_analysis(reg_hca_stats, po_hca_stats)
        run_hca_consistency_analysis(reg_hca_stats, po_hca_stats)

        print("\n" + "═" * _W + "\n")

    with open(_RESULTS_PATH, "w") as f:
        f.write("# NBA Home Court Advantage — Regression Results\n\n")
        f.write("_Auto-generated by `nba_home_court_regression.py` — do not edit manually._  \n")
        f.write("_Re-run `MPLBACKEND=Agg python3 nba_home_court_advantage.py` to refresh._\n\n")
        f.write("```\n")
        f.write(buf.getvalue())
        f.write("```\n")
    sys.stdout.write(f"Saved → {_RESULTS_PATH}\n")
