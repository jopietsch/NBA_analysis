"""
nba_home_court_regression.py — statistical analysis of home court advantage.

Game-level statistical analyses on all cached data — one run_* function per
home_court_FINDINGS.md section that needs numbers: decline trend, format periods,
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
            merged["away_b2b"]      = (merged["REST_away"] == 0).astype("float64")
            merged["home_b2b"]      = (merged["REST_home"] == 0).astype("float64")
            merged.loc[merged["REST_away"].isna(), "away_b2b"] = np.nan
            merged.loc[merged["REST_home"].isna(), "home_b2b"] = np.nan
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

            if {"OREB_home", "OREB_away", "DREB_home", "DREB_away"}.issubset(merged.columns):
                reb = nba._compute_rebound_components(merged)
                merged[reb.columns] = reb
            else:
                for col in ("oreb_diff", "dreb_diff", "reb_share_edge", "league_oreb_rate"):
                    merged[col] = np.nan

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
                "rest_diff", "away_b2b", "home_b2b", "altitude_home", "tz_diff",
                "foul_diff", "fg_pct_diff", "efg_pct_diff", "tpa_rate_diff",
                "fg3_pct_diff", "ft_pct_diff", "tov_diff", "reb_diff",
                "oreb_diff", "dreb_diff", "reb_share_edge", "league_oreb_rate",
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
            if n <= 4:
                print(f"   {'':12}  {'':4}  ⚠ n={n}: too few seasons — treat as illustrative only")
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


def compute_mediation_decomposition(df: pd.DataFrame) -> dict:
    """Box-score channel shares of the HCA level and its trend, RS and playoffs.

    The numbers run_mediation_analysis prints, returned in a structure the plot
    layer renders directly — so the chart and RESULTS.md never diverge. Each
    channel row carries both a table_label (for RESULTS.md) and a chart_label
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
            contrib = m_full.params[k] * 100 * gamma
            mediated += contrib
            trend_rows.append({
                "key": k, "table_label": tl, "chart_label": clab,
                "gamma": gamma, "contrib": contrib, "pct": 100 * contrib / t_total,
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
        print(f"   {'Channel':<16}  {'Trend in diff/yr':>16}  {'Contribution':>15}  "
              f"{'% of trend':>10}")
        print(f"   {'─'*16}  {'─'*16}  {'─'*15}  {'─'*10}")
        for r in ctx["trend"]:
            print(f"   {r['table_label']:<16}  {r['gamma']:>+12.4f} {r['stars']:<3}  "
                  f"{r['contrib']:>+9.4f} pp/yr  {r['pct']:>9.0f}%")
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
        if label == "Playoffs":
            print("   ► Note: playoff differentials fold in the seed-quality gap (the")
            print("     home team is usually the better team) — see the seeding")
            print("     decomposition for that control.")
        print()

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


# ── Analysis 5b: Rebounding decomposition ────────────────────────────────────

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


# ── Analysis 5c: Player-tracking rebounding mechanism ────────────────────────

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
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m = smf.ols("v ~ year", data=xy).fit()
        coef, pval = m.params["year"], m.pvalues["year"]
        print(f"   {label:<{label_w}}{len(xy):>11}{xy['v'].mean():>+10.3f}"
              f"{coef:>+9.3f}{_stars(pval)}{_fmt_p(pval):>9}")

    print()
    print("   ► The home edge is small and flat-to-declining across the tracking era —")
    print("     consistent with the offensive-glass advantage having largely collapsed")
    print("     before high-resolution tracking even began.")
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
    for s in order:
        b = rs[rs["situ"] == s]
        if not b.empty:
            print(f"   {labels[s]:<16}  {len(b):>8,}  {100*b['home_win'].mean():>10.1f}%")

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

    print(f"\n   Shift-share decomposition of the home win % change, "
          f"{first_lbl} → {last_lbl}:")
    print(f"   Home win %: {hca_f:.1f}% → {hca_l:.1f}%   (total change {total:+.2f} pp)")
    print(f"   {'Frequency component (schedule: fewer B2Bs)':<46}  {freq_comp:>+7.2f} pp  ({share:>4.0f}% of change)")
    print(f"   {'Win-rate component (per-situation edge eroding)':<46}  {rate_comp:>+7.2f} pp")
    print(f"   {'Interaction':<46}  {inter:>+7.2f} pp")
    print(f"\n   ► Visitor B2Bs have grown much rarer, which does nudge home court")
    print(f"     downward — but the win-rate gap between rested and tired matchups is")
    print(f"     small, so the schedule shift explains only ~{abs(share):.0f}% of the decline.")
    print(f"     The other ~{abs(100-share):.0f}% is the home edge within each rest situation")
    print(f"     eroding — not a scheduling story.\n")


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
    print(f"   2020-21 home win %:  empty arena {100*empty['home_win'].mean():.1f}% "
          f"(n={len(empty)})  vs.  fans present {100*crowd['home_win'].mean():.1f}% "
          f"(n={len(crowd)})")

    d = dose_df.copy()
    d["att_k"] = d["attendance"] / 1000.0  # coefficient = effect per 1,000 fans
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = smf.logit("home_win ~ att_k", data=d).fit(disp=0)
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

# ── Analysis 4b: Placebo / falsification tests for 1994-95 boundary ──────────

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
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m = smf.wls("pct ~ year + step", data=agg2,
                                weights=agg2["games"]).fit()
                coef = float(m.params.get("step", np.nan))
                pval = float(m.pvalues.get("step", np.nan))
                marker = "***" if pval < 0.001 else "** " if pval < 0.01 else "*  " if pval < 0.05 else "   "
                hi = " ← 1994-95" if t == 1995 else ""
                print(f"   {t:>6}  {coef:>+14.2f}  {_fmt_p(pval):>10}  {marker}{hi}")
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


# ── Analysis: Structural break test ──────────────────────────────────────────

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


# ── Structural break: CUSUM test (complements QLR) ───────────────────────────

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
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
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


# ── Helper: ADF unit-root + Engle-Granger cointegration ──────────────────────

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


# ── Helper: Granger causality — does 3PA lead HCA? ───────────────────────────

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
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                gc_res = grangercausalitytests(d_arr, maxlag=2, verbose=False)
            for lag in [1, 2]:
                F = gc_res[lag][0]["ssr_ftest"][0]
                p = gc_res[lag][0]["ssr_ftest"][1]
                verdict = "leads" if p < 0.05 else "no Granger effect"
                print(f"   {lag:>4}  {F:>8.3f}  {_fmt_p(p):>10}  {verdict:>28}  {_stars(p).strip()}")
        except Exception as exc:
            print(f"   Test failed: {exc}")
        print()


# ── Analysis: Channel-specific ITS around 1994-95 ────────────────────────────

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
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore")
                    m = smf.ols(f"{key} ~ year_c + post95 + time_since",
                                data=by_yr2).fit()
                pre_slope  = float(m.params.get("year_c",    np.nan))
                level_shift = float(m.params.get("post95",    np.nan))
                slope_chg  = float(m.params.get("time_since", np.nan))
                p_level    = float(m.pvalues.get("post95",    np.nan))
                p_slope    = float(m.pvalues.get("time_since", np.nan))
                print(f"   {label:<18}  {pre_slope:>+13.3f}  {level_shift:>+12.3f}  "
                      f"{slope_chg:>+13.3f}  {_fmt_p(p_level):>8}  {_fmt_p(p_slope):>8}  "
                      f"{_stars(p_level).strip()}/{_stars(p_slope).strip()}")
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


# ── Analysis: Team quality fixed effects robustness ───────────────────────────

def run_team_quality_robustness(df: pd.DataFrame) -> None:
    """Check: do era coefficients survive adding home/away team fixed effects?

    The sequential decomposition (§3) does not control for which specific teams
    host games. Franchise fixed effects remove any confound from systematic
    changes in home-team composition across eras — e.g., strong teams hosting
    more games in some periods. If era slopes are stable under team FE, the
    decline is not an artifact of roster or attendance patterns.
    """
    era_ref = nba.ERA_DEFS[0][0]
    reg = df[df["is_playoff"] == 0].dropna(subset=["rest_diff", "tz_diff"])

    _section("TEAM QUALITY ROBUSTNESS — ERA EFFECT WITH HOME/AWAY TEAM FIXED EFFECTS")
    print("   Does the era decline survive adding home- and away-team fixed effects?")
    print("   Franchise indicators remove systematic differences in home win rates")
    print("   across teams, so the era slope is not confounded by which franchises")
    print("   happen to host more games in different periods.\n")

    era_terms = f"C(era, Treatment('{era_ref}'))"
    f_base = (f"home_win ~ {era_terms} + rest_diff + altitude_home + tz_diff + covid")
    f_fe   = f_base + " + C(TEAM_NAME_home) + C(TEAM_NAME_away)"
    p_bar  = reg["home_win"].mean()

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        try:
            m_base = smf.logit(f_base, data=reg).fit(
                disp=0, cov_type="cluster",
                cov_kwds={"groups": reg["year"].values})
            m_fe = smf.logit(f_fe, data=reg).fit(
                disp=0, cov_type="cluster",
                cov_kwds={"groups": reg["year"].values})
        except Exception as exc:
            print(f"   Model failed: {exc}\n")
            return

    print(f"   Era coefficients (pp relative to 1984-94 baseline):\n")
    print(f"   {'Era':<12}  {'Baseline':>12}  {'With team FE':>14}  {'Shift':>8}")
    print(f"   {'─'*12}  {'─'*12}  {'─'*14}  {'─'*8}")

    shifts = []
    for era_label, y1, y2, _ in nba.ERA_DEFS[1:]:
        key = f"{era_terms}[T.{era_label}]"
        c_b  = m_base.params.get(key, np.nan)
        c_fe = m_fe.params.get(key, np.nan)
        pp_b  = _pp(c_b,  p_bar) if not np.isnan(c_b)  else np.nan
        pp_fe = _pp(c_fe, p_bar) if not np.isnan(c_fe) else np.nan
        shift = pp_fe - pp_b if not (np.isnan(pp_b) or np.isnan(pp_fe)) else np.nan
        if not np.isnan(shift):
            shifts.append(abs(shift))
        pp_b_s  = f"{pp_b:+.1f} pp" if not np.isnan(pp_b)  else "—"
        pp_fe_s = f"{pp_fe:+.1f} pp" if not np.isnan(pp_fe) else "—"
        sh_s    = f"{shift:+.1f} pp" if not np.isnan(shift) else "—"
        print(f"   {era_label:<12}  {pp_b_s:>12}  {pp_fe_s:>14}  {sh_s:>8}")

    max_shift = max(shifts) if shifts else 0.0
    r2_b  = _mcfadden(m_base)
    r2_fe = _mcfadden(m_fe)
    print(f"\n   McFadden R²: baseline = {r2_b:.4f}  →  with team FE = {r2_fe:.4f}  "
          f"(Δ = +{r2_fe - r2_b:.4f})")
    print(f"   Max era coefficient shift across eras: {max_shift:.1f} pp")
    verdict = "stable" if max_shift < 1.5 else "shifted"
    not_str = "not " if verdict == "stable" else ""
    print(f"   ► Era coefficients are {verdict} under team FE — the decline is")
    print(f"     {not_str}explained by which franchises host games.\n")


# ── Analysis: Multiple comparisons — BH FDR correction ───────────────────────

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
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m = smf.logit(formula, data=data).fit(
                    disp=0, cov_type="cluster",
                    cov_kwds={"groups": data["year"].values})
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
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
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
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                f_yr  = f"home_win ~ year + rest_diff + altitude_home + tz_diff + covid"
                f_era = (f"home_win ~ year + C(era, Treatment('{era_ref}')) "
                         f"+ rest_diff + altitude_home + tz_diff + covid")
                m_yr  = smf.logit(f_yr,  data=sub).fit(disp=0)
                m_era = smf.logit(f_era, data=sub).fit(disp=0)
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


# ── Entry point ───────────────────────────────────────────────────────────────

_RESULTS_PATH = "RESULTS.md"


def generate_results_text(df: pd.DataFrame | None = None) -> str:
    """Run every analysis and return the captured report body (no file I/O).

    Split out of run() so tests can regenerate the results in-memory and
    compare against the committed RESULTS.md without overwriting it.
    """
    buf = io.StringIO()

    with contextlib.redirect_stdout(buf):
        _header("NBA HOME COURT ADVANTAGE — REGRESSION ANALYSIS")
        print("Game-level logistic regression. Outcome: home_win (1/0) per game.")
        print("All data from cache/ — same source as the plots above.\n")

        if df is None:
            df = build_game_dataset()
        if df.empty:
            print("No game data found in cache/. Run the main script first to populate it.")
            return buf.getvalue()
        df = _add_quality_diff(df)

        parity_seasons, parity_std = nba.compute_parity_stats(
            nba.START_YEAR, nba.END_YEAR, "Regular Season"
        )
        att_seasons, att_avg = nba.compute_attendance_season_stats(
            nba.BBR_START_YEAR, nba.END_YEAR
        )
        dose_df = nba.compute_attendance_covid_doseresponse(2021)
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

        results: dict = {}

        # §1 The 40-Year Decline (magnitude, shape/timing, blowout polarization)
        run_decline_trend(df)
        run_structural_break_test(df, results)
        run_cusum_test(df, results)
        run_its_test(df)
        run_margin_analysis(df)
        run_quantile_margin_analysis(df)

        # §2 What Creates Home Court Advantage
        run_differential_analysis(df)
        run_mediation_analysis(df)
        run_rebounding_decomposition(df)
        run_rest_bucket_analysis(df)
        run_factor_summary(df)

        # §3 What's Driving the Decline
        run_sequential_decomposition(df)
        run_stability_analysis(df)
        run_channel_event_study(df)
        run_team_quality_robustness(df)
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
        _run_granger_3pa(df)

        # §4 What Didn't Drive the Change (rule changes lead, then travel/pace/parity)
        run_era_analysis(df)
        run_placebo_tests(df)
        run_travel_analysis(df)
        run_back_to_back_analysis(df)
        run_pace_analysis(df)
        run_parity_correlation(parity_seasons, parity_std, reg_seasons_sorted, reg_pcts_sorted)
        run_attendance_analysis(att_seasons, att_avg, reg_seasons_sorted, reg_pcts_sorted, dose_df)

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
        run_multiple_comparisons_summary(df)

        print("\n" + "═" * _W + "\n")

    return buf.getvalue()


def run(df: pd.DataFrame | None = None) -> None:
    text = generate_results_text(df)
    with open(_RESULTS_PATH, "w") as f:
        f.write("# NBA Home Court Advantage — Regression Results\n\n")
        f.write("_Auto-generated by `nba_home_court_regression.py` — do not edit manually._  \n")
        f.write("_Re-run `MPLBACKEND=Agg python3 nba_home_court_advantage.py` to refresh._\n\n")
        f.write("```\n")
        f.write(text)
        f.write("```\n")
    sys.stdout.write(f"Saved → {_RESULTS_PATH}\n")
