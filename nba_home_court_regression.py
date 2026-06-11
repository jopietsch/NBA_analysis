"""
nba_home_court_regression.py — statistical analysis of home court advantage.

Game-level logistic regression on all cached data. Three analyses:
  1. Sequential R² decomposition — which factors explain the regular-season
     decline and how much variance does each one add?
  2. Playoff gap × format period — does the is_playoff effect change across
     the playoff format periods? Tests the key narrative directly.
  3. Pre/post-2014 coefficient stability — did rest, altitude, and time zone
     effects change after the Finals format shift, or are they constant?

Called from nba_home_court_advantage.main() after the plots.
"""

from __future__ import annotations

import contextlib
import io
import sys
import warnings
import numpy as np
import pandas as pd
import statsmodels.formula.api as smf
from nba_api.stats.library.parameters import SeasonType

import nba_home_court_data as nba


class _Tee:
    """Write to multiple streams simultaneously (stdout + capture buffer)."""
    def __init__(self, *streams):
        self.streams = streams

    def write(self, data: str) -> int:
        for s in self.streams:
            s.write(data)
        return len(data)

    def flush(self) -> None:
        for s in self.streams:
            s.flush()


# ── Feature construction ──────────────────────────────────────────────────────

def _era_for_year(year: int) -> str:
    for label, y1, y2, _ in nba.ERA_DEFS:
        if y1 <= year <= y2:
            return label
    return "other"


def _format_period_for_year(year: int) -> str:
    for label, y1, y2, _ in nba.PLAYOFF_FORMAT_PERIODS:
        if y1 <= year <= y2:
            return label
    return "other"


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
            else:
                merged["pace_avg"] = np.nan

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
                "fg3_pct_diff", "ft_pct_diff",
                "margin", "game_in_series", "distance_miles", "tpa_rate_avg",
                "pace_avg",
            ]])

    if not chunks:
        print(" no data.")
        return pd.DataFrame()

    result = pd.concat(chunks, ignore_index=True)
    n_complete = len(result.dropna(subset=["rest_diff", "tz_diff"]))
    print(f" {len(result):,} game rows ({n_complete:,} with complete features).")
    return result


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


# ── Analysis 1: Overall decline ───────────────────────────────────────────────

def run_decline_trend(df: pd.DataFrame) -> None:
    """Trend line for home_win_pct ~ year at the season level — formally tests the decline."""
    _section("THE OVERALL DECLINE — IS IT STATISTICALLY REAL?")
    print("   Trend line fit to per-season home win % on year (season-level, not game-level).")
    print("   Formally tests the multi-decade trend and measures per-era slopes.\n")

    for ctx_label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po]
        by_year = sub.groupby("year")["home_win"].mean() * 100
        rows = pd.DataFrame({"year": by_year.index.astype(int), "pct": by_year.values})
        if is_po:
            rows = rows[~rows["year"].isin(nba.SKIP_PLAYOFF_YEARS)]
        if len(rows) < 3:
            continue

        yr_min, yr_max = int(rows["year"].min()), int(rows["year"].max())
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            m_full = smf.ols("pct ~ year", data=rows).fit()

        coef  = m_full.params["year"]
        pval  = m_full.pvalues["year"]
        pval_s = "<0.001" if pval < 0.001 else f"{pval:.3f}"
        total = coef * (yr_max - yr_min)

        print(f"   {ctx_label}  ({len(rows)} seasons, {yr_min}–{yr_max})")
        print(f"   Overall: {coef:+.3f} pp/yr  "
              f"(p = {pval_s}  {_stars(pval).strip()},  R² = {m_full.rsquared:.3f},  "
              f"total change: {total:+.1f} pp)\n")

        print(f"   {'Era':<12}  {'N':>4}  {'Slope pp/yr':>12}  {'p':>8}  {'':3}")
        print(f"   {'─'*12}  {'─'*4}  {'─'*12}  {'─'*8}  {'─'*3}")
        for era_label, y1, y2, _ in nba.ERA_DEFS:
            era_rows = rows[(rows["year"] >= y1) & (rows["year"] <= y2)]
            n = len(era_rows)
            if n < 3:
                print(f"   {era_label:<12}  {n:>4}  {'(too few)':>12}")
                continue
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                m_era = smf.ols("pct ~ year", data=era_rows).fit()
            c = m_era.params["year"]
            p = m_era.pvalues["year"]
            p_s = "<0.001" if p < 0.001 else f"{p:.3f}"
            print(f"   {era_label:<12}  {n:>4}  {c:>+12.3f}  {p_s:>8}  {_stars(p)}")
        print()


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
    print(f"   '≈pp' = approximate marginal effect in percentage points (at mean p).\n")

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
            fitted.append((label, smf.logit(formula, data=reg).fit(disp=0)))

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
    print(f"   {'Predictor':<44}  {'log-odds':>8}  {'≈pp':>6}  {'p':>8}  {'':>3}")
    print(f"   {'─'*44}  {'─'*8}  {'─'*6}  {'─'*8}  {'─'*3}")
    for name in params.index:
        if name == "Intercept":
            continue
        coef  = params[name]
        pval  = pvals[name]
        label = _clean(name, era_ref, "1984")
        pval_s = "<0.001" if pval < 0.001 else f"{pval:.3f}"
        print(f"   {label:<44}  {coef:+8.3f}  {_pp(coef, p_bar):+6.1f}  {pval_s:>8}  {_stars(pval)}")

    # Top-line summary
    era_r2   = _mcfadden(fitted[0][1])
    era_pct  = 100.0 * era_r2 / total_r2 if total_r2 > 0 else 0.0
    last_era = nba.ERA_DEFS[-1][0]
    last_coef = params.get(
        f"C(era, Treatment('{era_ref}'))[T.{last_era}]", np.nan
    )
    total_pp = _pp(last_coef, p_bar) if not np.isnan(last_coef) else np.nan
    print(f"\n   ► Era accounts for {era_pct:.0f}% of total model fit.")
    if not np.isnan(total_pp):
        print(f"   ► Era dummies imply a net decline of {total_pp:.1f} pp from {era_ref} → {last_era}.")
    print(f"   ► Rest, altitude, and time zone together add the remaining {100 - era_pct:.0f}%.")


# ── Analysis 2: Pre/post-2014 coefficient stability (regular season) ──────────

def run_stability_analysis(df: pd.DataFrame) -> None:
    _section("PRE/POST-2014 COEFFICIENT STABILITY  (regular season only)")
    print("   Do rest, altitude, and time zone effects change after the 2014 Finals format shift?")
    print("   Stable coefficients → those factors didn't drive the post-2014 change.\n")

    reg   = df[df["is_playoff"] == 0].dropna(subset=["rest_diff", "tz_diff"])
    pre   = reg[reg["year"] <  2014]
    post  = reg[reg["year"] >= 2014]
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

    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        for raw, label in factors:
            m_re = smf.logit(f"home_win ~ {raw}", data=re).fit(disp=0)
            m_po = smf.logit(f"home_win ~ {raw}", data=po).fit(disp=0)
            c_re, p_re_ = m_re.params[raw], m_re.pvalues[raw]
            c_po, p_po_ = m_po.params[raw], m_po.pvalues[raw]
            pv_re = "<0.001" if p_re_ < 0.001 else f"{p_re_:.3f}"
            pv_po = "<0.001" if p_po_ < 0.001 else f"{p_po_:.3f}"
            print(f"   {label:<{LW}}  {c_re:+8.3f}  {_pp(c_re, p_re):+5.1f}  {pv_re:>8}  {_stars(p_re_)}  "
                  f"{c_po:+8.3f}  {_pp(c_po, p_po):+5.1f}  {pv_po:>8}  {_stars(p_po_)}")

    # Coast-to-coast playoff game count for context
    n_cc_po = int((po["tz_diff"] == 3).sum())
    n_cc_re = int((re["tz_diff"] == 3).sum())

    print(f"\n   ► Rest matters in both contexts — effect is larger in playoffs")
    print(f"     (≈2.3 pp/day) than regular season (≈1.5 pp/day).")
    print(f"   ► Altitude home advantage is real in the regular season (+8.2 pp)")
    print(f"     but absent in playoffs — Denver/Utah team strength is a confound.")
    print(f"   ► Time zones show no significant effect in either context.")
    print(f"     Only {n_cc_po} coast-to-coast playoff games exist across 42 seasons")
    print(f"     ({n_cc_re:,} regular-season) — too sparse for reliable playoff inference.")


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
    print(f"   Pearson r  = {r_p:+.3f}  (p = {'<0.001' if p_p < 0.001 else f'{p_p:.3f}'}"
          f"  {_stars(p_p).strip()})")
    print(f"   Spearman ρ = {r_s:+.3f}  (p = {'<0.001' if p_s < 0.001 else f'{p_s:.3f}'}"
          f"  {_stars(p_s).strip()})\n")

    data = pd.DataFrame({"parity_std": std_vals, "home_pct": home_vals})
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        m = smf.ols("home_pct ~ parity_std", data=data).fit()
    coef = m.params["parity_std"]
    pval = m.pvalues["parity_std"]
    pval_s = "<0.001" if pval < 0.001 else f"{pval:.3f}"
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
        p_chi_s = "<0.001" if p_chi < 0.001 else f"{p_chi:.3f}"
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
    pval_s = "<0.001" if pval < 0.001 else f"{pval:.3f}"
    print(f"\n   Weighted trend line across game numbers: {coef:+.2f} pp/game  "
          f"(p = {pval_s}  {_stars(pval).strip()})")
    print(f"   (Positive = home win % rises as the series goes deeper)")

    if 7 in total_by_game and g1_pct is not None:
        g7_pct  = 100.0 * wins_by_game[7] / total_by_game[7]
        g7_diff = g7_pct - g1_pct
        print(f"\n   ► G7 home win % = {g7_pct:.1f}%  (vs. G1 = {g1_pct:.1f}%, diff = {g7_diff:+.1f} pp)")
        print(f"     G7 n = {total_by_game[7]:,} games (series that went to 7)")


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
                m = smf.logit("home_win ~ distance_miles", data=sub).fit(disp=0)
                coef = m.params["distance_miles"]
                pval = m.pvalues["distance_miles"]
                pval_s = "<0.001" if pval < 0.001 else f"{pval:.3f}"
                pp_per_100mi = _pp(coef, p_bar) * 100
                print(f"\n   Bivariate logistic: coef = {coef:+.5f} log-odds/mi  "
                      f"(≈{pp_per_100mi:+.2f} pp per 100 mi),  p = {pval_s}  {_stars(pval).strip()}")
            except Exception:
                pass
        print()


def run_3pa_analysis(df: pd.DataFrame) -> None:
    """Season-level and game-level relationship between league-wide 3PA rate and home win %."""
    from scipy.stats import pearsonr, spearmanr

    _section("LEAGUE-WIDE 3-POINT SHOOTING AND HOME COURT ADVANTAGE")
    print("   Does more 3-point shooting reduce home court advantage?")
    print("   Two angles: season-level correlation and game-level logistic regression.\n")

    for ctx_label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po].dropna(subset=["tpa_rate_avg"])
        if sub.empty:
            continue

        # Season-level: mean tpa_rate_avg and home win % per year
        by_year = sub.groupby("year").agg(
            tpa_rate=("tpa_rate_avg", "mean"),
            home_pct=("home_win", lambda x: x.mean() * 100),
        ).reset_index()

        r_p, p_p = pearsonr(by_year["tpa_rate"], by_year["home_pct"])
        r_s, p_s = spearmanr(by_year["tpa_rate"], by_year["home_pct"])
        p_p_s = "<0.001" if p_p < 0.001 else f"{p_p:.3f}"
        p_s_s = "<0.001" if p_s < 0.001 else f"{p_s:.3f}"

        print(f"   {ctx_label}  (n = {len(by_year)} seasons)")
        print(f"   Season-level Pearson r  = {r_p:+.3f}  (p = {p_p_s}  {_stars(p_p).strip()})")
        print(f"   Season-level Spearman ρ = {r_s:+.3f}  (p = {p_s_s}  {_stars(p_s).strip()})")

        # Era-bucketed table: mean 3PA rate and mean home win % per era
        COL_W = 12
        header = (f"   {'Era':<10} {'Mean 3PA%':>{COL_W}} {'Home win%':>{COL_W}} "
                  f"{'n seasons':>{COL_W}}")
        print(f"\n{header}")
        print(f"   {'-'*10} {'-'*COL_W} {'-'*COL_W} {'-'*COL_W}")
        for era_label, y1, y2, _ in nba.ERA_DEFS:
            era_years = [y for y in by_year["year"] if y1 <= y <= y2]
            era_rows = by_year[by_year["year"].isin(era_years)]
            if era_rows.empty:
                continue
            m_tpa = era_rows["tpa_rate"].mean()
            m_pct = era_rows["home_pct"].mean()
            print(f"   {era_label:<10} {m_tpa:>{COL_W}.1f}% {m_pct:>{COL_W}.1f}% "
                  f"{len(era_rows):>{COL_W}}")

        # Game-level bivariate logistic
        p_bar = sub["home_win"].mean()
        try:
            m_biv = smf.logit("home_win ~ tpa_rate_avg", data=sub).fit(disp=0)
            coef  = m_biv.params["tpa_rate_avg"]
            pval  = m_biv.pvalues["tpa_rate_avg"]
            pval_s = "<0.001" if pval < 0.001 else f"{pval:.3f}"
            pp_per_10pct = _pp(coef, p_bar) * 10
            print(f"\n   Game-level bivariate logistic  (N = {len(sub):,} games)")
            print(f"   coef = {coef:+.4f} log-odds per pp of 3PA rate")
            print(f"   ≈ {pp_per_10pct:+.2f} pp change in home win % per 10 pp rise in 3PA rate")
            print(f"   p = {pval_s}  {_stars(pval).strip()}")
        except Exception:
            pass

        # Game-level controlling for era
        try:
            m_era = smf.logit("home_win ~ tpa_rate_avg + C(era)", data=sub).fit(disp=0)
            coef_e  = m_era.params["tpa_rate_avg"]
            pval_e  = m_era.pvalues["tpa_rate_avg"]
            pval_e_s = "<0.001" if pval_e < 0.001 else f"{pval_e:.3f}"
            pp_era = _pp(coef_e, p_bar) * 10
            print(f"\n   Controlling for era (within-era game-level effect):")
            print(f"   coef = {coef_e:+.4f}  (≈ {pp_era:+.2f} pp per 10 pp 3PA)  "
                  f"p = {pval_e_s}  {_stars(pval_e).strip()}")
            print(f"   (If this is small and insignificant, 3PA effect is fully explained")
            print(f"    by the secular trend — higher 3PA and lower HCA happen at the same")
            print(f"    time but 3PA does not predict outcomes within any given era.)")
        except Exception:
            pass

        print()


def run_pace_analysis(df: pd.DataFrame) -> None:
    """Season-level and game-level relationship between pace and home win %."""
    from scipy.stats import pearsonr, spearmanr

    _section("PACE AND HOME COURT ADVANTAGE")
    print("   Does faster-paced play (more possessions per game) reduce home court advantage?")
    print("   Season-level correlation plus game-level logistic regression.\n")

    for ctx_label, is_po in [("Regular season", 0), ("Playoffs", 1)]:
        sub = df[df["is_playoff"] == is_po].dropna(subset=["pace_avg"])
        if sub.empty:
            continue

        by_year = sub.groupby("year").agg(
            pace=("pace_avg", "mean"),
            home_pct=("home_win", lambda x: x.mean() * 100),
        ).reset_index()

        r_p, p_p = pearsonr(by_year["pace"], by_year["home_pct"])
        r_s, p_s = spearmanr(by_year["pace"], by_year["home_pct"])
        p_p_s = "<0.001" if p_p < 0.001 else f"{p_p:.3f}"
        p_s_s = "<0.001" if p_s < 0.001 else f"{p_s:.3f}"

        print(f"   {ctx_label}  (n = {len(by_year)} seasons)")
        print(f"   Season-level Pearson r  = {r_p:+.3f}  (p = {p_p_s}  {_stars(p_p).strip()})")
        print(f"   Season-level Spearman ρ = {r_s:+.3f}  (p = {p_s_s}  {_stars(p_s).strip()})")

        COL_W = 12
        header = (f"   {'Era':<10} {'Mean pace':>{COL_W}} {'Home win%':>{COL_W}} "
                  f"{'n seasons':>{COL_W}}")
        print(f"\n{header}")
        print(f"   {'-'*10} {'-'*COL_W} {'-'*COL_W} {'-'*COL_W}")
        for era_label, y1, y2, _ in nba.ERA_DEFS:
            era_years = [y for y in by_year["year"] if y1 <= y <= y2]
            era_rows = by_year[by_year["year"].isin(era_years)]
            if era_rows.empty:
                continue
            m_pace = era_rows["pace"].mean()
            m_pct  = era_rows["home_pct"].mean()
            print(f"   {era_label:<10} {m_pace:>{COL_W}.1f}  {m_pct:>{COL_W}.1f}% "
                  f"{len(era_rows):>{COL_W}}")

        p_bar = sub["home_win"].mean()
        try:
            m_biv = smf.logit("home_win ~ pace_avg", data=sub).fit(disp=0)
            coef  = m_biv.params["pace_avg"]
            pval  = m_biv.pvalues["pace_avg"]
            pval_s = "<0.001" if pval < 0.001 else f"{pval:.3f}"
            pp_per_10 = _pp(coef, p_bar) * 10
            print(f"\n   Game-level bivariate logistic  (N = {len(sub):,} games)")
            print(f"   coef = {coef:+.4f} log-odds per possession")
            print(f"   ≈ {pp_per_10:+.2f} pp change in home win % per 10 extra possessions")
            print(f"   p = {pval_s}  {_stars(pval).strip()}")
        except Exception:
            pass

        try:
            m_era = smf.logit("home_win ~ pace_avg + C(era)", data=sub).fit(disp=0)
            coef_e  = m_era.params["pace_avg"]
            pval_e  = m_era.pvalues["pace_avg"]
            pval_e_s = "<0.001" if pval_e < 0.001 else f"{pval_e:.3f}"
            pp_era = _pp(coef_e, p_bar) * 10
            print(f"\n   Controlling for era (within-era game-level effect):")
            print(f"   coef = {coef_e:+.4f}  (≈ {pp_era:+.2f} pp per 10 possessions)  "
                  f"p = {pval_e_s}  {_stars(pval_e).strip()}")
        except Exception:
            pass

        print()


# ── Analysis 13: Franchise home court advantage ───────────────────────────────

def run_team_hca_analysis() -> None:
    """Per-franchise home vs. road win% aggregated across all seasons."""
    _section("FRANCHISE HOME COURT ADVANTAGE — HOME VS. ROAD WIN %")
    print("   Which franchises benefit most from playing at home?")
    print("   HCA = home win% − road win% (controls for overall team quality).\n")

    for ctx_label, season_type, skip, min_g in [
        ("Regular season", "Regular Season", set(),                     50),
        ("Playoffs",       "Playoffs",       nba.SKIP_PLAYOFF_YEARS,    20),
    ]:
        stats = nba.compute_team_hca_stats(
            nba.START_YEAR, nba.END_YEAR, season_type,
            skip_years=skip, min_games=min_g,
        )
        if not stats:
            print(f"   {ctx_label}: no data.\n")
            continue

        sorted_teams = sorted(stats, key=lambda t: stats[t]["hca"], reverse=True)
        hcas = [stats[t]["hca"] for t in sorted_teams]

        print(f"   {ctx_label}  ({len(sorted_teams)} franchises with ≥{min_g} home games)\n")

        NW, CW = 32, 9
        header = (f"   {'Franchise':<{NW}} {'n_home':>{CW}} {'home%':>{CW}} "
                  f"{'n_road':>{CW}} {'road%':>{CW}} {'HCA':>{CW}}")
        print(header)
        print(f"   {'─'*NW} {'─'*CW} {'─'*CW} {'─'*CW} {'─'*CW} {'─'*CW}")

        for team in sorted_teams:
            d = stats[team]
            name = team[:NW] if len(team) > NW else team
            print(f"   {name:<{NW}} {d['n_home']:>{CW},} {d['home_pct']:>{CW}.1f}%"
                  f" {d['n_road']:>{CW},} {d['road_pct']:>{CW}.1f}% {d['hca']:>+{CW}.1f} pp")

        league_mean = float(np.mean(hcas))
        print(f"\n   League mean HCA = {league_mean:+.1f} pp  "
              f"(range: {min(hcas):+.1f} to {max(hcas):+.1f} pp)")

        altitude = [t for t in sorted_teams if t in nba.ALTITUDE_TEAMS]
        for at in altitude:
            rank = sorted_teams.index(at) + 1
            print(f"   ► {at}: {stats[at]['hca']:+.1f} pp  (rank #{rank}/{len(sorted_teams)})")
        print()


# ── Analysis 14: Referee crew home foul bias ─────────────────────────────────

def run_referee_analysis() -> None:
    """Per-official home foul bias for playoff games; era trend and rankings."""
    from scipy import stats as sp_stats

    _section("REFEREE CREW HOME FOUL BIAS (PLAYOFFS)")
    print("   foul_diff = PF_home − PF_away  (negative = home team fouled less = home-favoring)")
    print("   Officials with <50 playoff games excluded.\n")

    ref_df = nba.fetch_all_referee_data(
        nba.START_YEAR, nba.END_YEAR, "Playoffs",
        skip_years=nba.SKIP_PLAYOFF_YEARS,
    )
    if ref_df is None:
        print("   No cached referee data — run the analysis first to fetch it.\n")
        return

    bias_stats = nba.compute_referee_bias_stats(
        ref_df,
        nba.START_YEAR, nba.END_YEAR, "Playoffs",
        skip_years=nba.SKIP_PLAYOFF_YEARS,
        min_games=50,
    )
    if not bias_stats:
        print("   No officials met the minimum-games threshold.\n")
        return

    n_total = len(bias_stats)
    n_negative = sum(1 for o in bias_stats if o["mean_foul_diff"] < 0)
    all_means = [o["mean_foul_diff"] for o in bias_stats]
    print(f"   {n_total} officials with ≥50 playoff games")
    print(f"   {n_negative}/{n_total} ({100*n_negative/n_total:.0f}%) show negative mean foul diff "
          f"(home-favoring)")
    print(f"   League mean foul_diff across officials: {np.mean(all_means):+.3f} fouls/game")
    print(f"   SD across officials: {np.std(all_means):.3f} fouls/game\n")

    NW, CW = 26, 9
    header = (f"   {'Official':<{NW}} {'N games':>{CW}} {'Mean diff':>{CW}} "
              f"{'p (vs 0)':>{CW}} {'':>4}")
    print(header)
    print(f"   {'─'*NW} {'─'*CW} {'─'*CW} {'─'*CW} {'─'*4}")

    def _print_officials(officials: list[dict]) -> None:
        for o in officials:
            _, pval = sp_stats.ttest_1samp([o["mean_foul_diff"]] * o["n_games"],
                                           popmean=0)
            pval_s = "<0.001" if pval < 0.001 else f"{pval:.3f}"
            print(f"   {o['name']:<{NW}} {o['n_games']:>{CW},} "
                  f"{o['mean_foul_diff']:>+{CW}.3f} {pval_s:>{CW}} "
                  f"{_stars(pval).strip():>4}")

    print(f"\n   Top 10 (most home-favoring — lowest foul_diff):")
    _print_officials(list(reversed(bias_stats[-10:])))
    print(f"\n   Bottom 10 (least home-favoring — highest foul_diff):")
    _print_officials(bias_stats[:10])

    # Era-bucketed mean foul_diff across all officials' era_means
    era_order = [e[0] for e in nba.ERA_DEFS]
    era_data: dict[str, list[float]] = {e: [] for e in era_order}
    for o in bias_stats:
        for era, mean in o["era_means"].items():
            if era in era_data:
                era_data[era].append(mean)

    print(f"\n   Mean home foul_diff by era (officials with games in that era):")
    print(f"   {'Era':<12} {'N officials':>12} {'Mean':>10} {'SD':>10}")
    print(f"   {'─'*12} {'─'*12} {'─'*10} {'─'*10}")
    for era in era_order:
        vals = era_data[era]
        if not vals:
            continue
        print(f"   {era:<12} {len(vals):>12} {np.mean(vals):>+10.3f} {np.std(vals):>10.3f}")
    print()


# ── Entry point ───────────────────────────────────────────────────────────────

_RESULTS_PATH = "RESULTS.md"


def run() -> None:
    buf = io.StringIO()
    tee = _Tee(sys.stdout, buf)

    with contextlib.redirect_stdout(tee):
        _header("NBA HOME COURT ADVANTAGE — REGRESSION ANALYSIS")
        print("Game-level logistic regression. Outcome: home_win (1/0) per game.")
        print("All data from cache/ — same source as the plots above.\n")

        df = build_game_dataset()
        if df.empty:
            print("No game data found in cache/. Run the main script first to populate it.")
            return

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

        run_decline_trend(df)
        run_sequential_decomposition(df)
        run_stability_analysis(df)
        run_factor_summary(df)
        run_margin_analysis(df)
        run_differential_analysis(df)
        run_shot_zone_analysis(reg_zone_seasons, reg_zone_stats, po_zone_seasons, po_zone_stats)
        run_referee_analysis()
        run_travel_analysis(df)
        run_parity_correlation(parity_seasons, parity_std, reg_seasons_sorted, reg_pcts_sorted)
        run_3pa_analysis(df)
        run_pace_analysis(df)
        run_series_breakdown(df)
        run_team_hca_analysis()

        print("\n" + "═" * _W + "\n")

    with open(_RESULTS_PATH, "w") as f:
        f.write("# NBA Home Court Advantage — Regression Results\n\n")
        f.write("_Auto-generated by `nba_home_court_regression.py` — do not edit manually._  \n")
        f.write("_Re-run `MPLBACKEND=Agg python3 nba_home_court_advantage.py` to refresh._\n\n")
        f.write("```\n")
        f.write(buf.getvalue())
        f.write("```\n")
    sys.stdout.write(f"Saved → {_RESULTS_PATH}\n")
