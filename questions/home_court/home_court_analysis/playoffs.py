"""The Playoff Picture: series breakdown and era split, series-length
simulation, playoff quality decomposition, team-quality robustness, and
playoff-format-period analysis."""

from __future__ import annotations

import numpy as np
import pandas as pd
import statsmodels.formula.api as smf

from nbakit.textfmt import stars as _stars, p_value as _fmt_p

import home_court_data as nba
from home_court_facts import FACTS

from ._helpers import (
    suppress_noisy_fit_warnings, _warn_if_not_converged,
    _section, _pp, _mcfadden,
)
from ._features import _add_quality_diff

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
    with suppress_noisy_fit_warnings():
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


def run_series_era_split(df: pd.DataFrame) -> None:
    """Home win % by era, split into higher-seed home games and lower-seed home games.

    In 2-2-1-1-1: G1, G2, G5, G7 are at the higher seed; G3, G4, G6 at the lower seed.
    Note: 1985-2013 Finals used 2-3-2 (G3,G4,G5 at lower seed; G6,G7 at higher seed),
    but the Finals is ~1/15 of playoff games so the effect on pooled numbers is small.
    """
    _section("PLAYOFF HOME WIN % BY ERA — HIGHER SEED vs LOWER SEED AT HOME")
    print("   In 2-2-1-1-1 format: G1,G2,G5,G7 = higher seed at home; G3,G4,G6 = lower seed at home.")
    print("   (Pre-2014 Finals used 2-3-2; Finals ≈ 1/15 of games — minor effect on pooled figures.)\n")

    po = df[(df["is_playoff"] == 1)].dropna(subset=["game_in_series", "era"]).copy()
    po["game_in_series"] = po["game_in_series"].astype(int)
    po = po[po["game_in_series"].between(1, 7)]

    higher_seed_games = {1, 2, 5, 7}
    lower_seed_games  = {3, 4, 6}

    po["home_type"] = po["game_in_series"].apply(
        lambda g: "higher_seed" if g in higher_seed_games else "lower_seed"
    )

    print(f"   {'Era':<12}  {'Higher seed at home (G1,2,5,7)':>32}  {'Lower seed at home (G3,4,6)':>28}  {'Gap':>6}")
    print(f"   {'─'*12}  {'─'*32}  {'─'*28}  {'─'*6}")

    seed_rows: dict[str, tuple[float, float]] = {}
    for era_label, y1, y2, _ in nba.ERA_DEFS:
        era_sub = po[po["era"] == era_label]
        h = era_sub[era_sub["home_type"] == "higher_seed"]
        l = era_sub[era_sub["home_type"] == "lower_seed"]
        if h.empty or l.empty:
            continue
        h_pct = 100.0 * h["home_win"].sum() / len(h)
        l_pct = 100.0 * l["home_win"].sum() / len(l)
        seed_rows[era_label] = (h_pct, l_pct)
        gap   = h_pct - l_pct
        print(f"   {era_label:<12}  {h_pct:>6.1f}%  ({len(h):>4} games){'':<14}  "
              f"{l_pct:>6.1f}%  ({len(l):>4} games){'':<5}  {gap:>+5.1f} pp")

    # Facts for the prose: the weaker team (lower seed) at home used to win
    # ~65–66%, nearly matching the stronger team; today it is far lower. The
    # early ranges are authored here next to the per-era figures above.
    _last = nba.ERA_DEFS[-1][0]
    if _last in seed_rows:
        FACTS.set("seed.stronger_today", seed_rows[_last][0], "{:.0f}%",
                  note=f"{_last}: higher-seed (stronger team) home win %")
        FACTS.set("seed.weaker_today", seed_rows[_last][1], "{:.0f}%",
                  note=f"{_last}: lower-seed (weaker team) home win %")
    FACTS.set("seed.weaker_early_plain", "65–66%",
              note="1984–94 / 1995–01 lower-seed home win % (range)")
    FACTS.set("seed.stronger_early_plain", "70–75%",
              note="higher-seed home win % across the earlier eras (range)")
    for _i, _ky in [(0, "1984"), (1, "1995")]:
        _lbl = nba.ERA_DEFS[_i][0]
        if _lbl in seed_rows:
            FACTS.set(f"seed.weaker_{_ky}", seed_rows[_lbl][1], "{:.0f}%",
                      note=f"{_lbl}: lower-seed (weaker team) home win %")
    _early = [(e[0], seed_rows[e[0]]) for e in nba.ERA_DEFS[:2] if e[0] in seed_rows]
    FACTS.guard("weaker_matched_stronger",
                any(l >= h for _, (h, l) in _early),
                claim="the weaker team at home matched or exceeded the stronger team's home win rate",
                value="; ".join(f"{lbl}: weaker {l:.0f}% vs stronger {h:.0f}%" for lbl, (h, l) in _early))

    # Overall
    h_all = po[po["home_type"] == "higher_seed"]
    l_all = po[po["home_type"] == "lower_seed"]
    h_pct_all = 100.0 * h_all["home_win"].sum() / len(h_all)
    l_pct_all = 100.0 * l_all["home_win"].sum() / len(l_all)
    print(f"   {'─'*12}  {'─'*32}  {'─'*28}  {'─'*6}")
    print(f"   {'All eras':<12}  {h_pct_all:>6.1f}%  ({len(h_all):>4} games){'':<14}  "
          f"{l_pct_all:>6.1f}%  ({len(l_all):>4} games){'':<5}  {h_pct_all-l_pct_all:>+5.1f} pp")

    print(f"\n   ► In the early eras (1984–94, 1995–01) the lower-seeded team won ~65–66% at home,")
    print(f"     nearly matching the higher seed's own home win rate. Home court was a genuine")
    print(f"     equalizer. From 2002 onward the lower-seed home win rate collapsed to ~47–52%,")
    print(f"     while the higher seed's remained at 65–75%. What faded is the boost home court")
    print(f"     gave to the team that needed it most.")


def run_series_simulation(data: dict) -> None:
    """How much of the per-game home edge survives a best-of-7.

    Monte Carlo (data layer): for each era, take the observed single-game home
    win % and simulate 2-2-1-1-1 series between two otherwise-equal teams. The
    best-of-7 compresses both the level of home court and its decline.
    """
    _section("PLAYOFF SERIES SIMULATION — DOES THE PER-GAME EDGE SURVIVE A BEST-OF-7?")
    print(f"   Monte Carlo: {data['n_sims']:,} simulated 2-2-1-1-1 series between two")
    print("   otherwise-equal teams, home-court team hosting games 1,2,5,6,7. Input is")
    print("   the observed single-game home win % per era.\n")

    eras = data["era_labels"]
    print(f"   {'Era':<10}{'RS /game':>10}{'RS series':>11}{'PO /game':>11}{'PO series':>11}")
    print(f"   {'─'*10}{'─'*10}{'─'*11}{'─'*11}{'─'*11}")
    for i, era in enumerate(eras):
        def _f(key):
            v = data[key][i]
            return f"{v:.1f}%" if v is not None else "—"
        print(f"   {era:<10}{_f('reg_pgame'):>10}{_f('reg_series'):>11}"
              f"{_f('po_pgame'):>11}{_f('po_series'):>11}")

    def _span(pg_key, s_key):
        pg = [v for v in data[pg_key] if v is not None]
        s  = [v for v in data[s_key]  if v is not None]
        if len(pg) < 2:
            return None
        return pg[0] - pg[-1], s[0] - s[-1], s[-1]

    print()
    rs = _span("reg_pgame", "reg_series")
    if rs is not None:
        dpg, ds, last = rs
        # Fact for the prose (§1): a home-court team that took the series ~55% of
        # the time in the earliest era is now barely better than a coin flip.
        FACTS.set("series.rs_early", data["reg_series"][0], "{:.0f}%",
                  note="Regular-season-input series home win %, earliest era")
        FACTS.set("series.rs_now", last, "{:.0f}%",
                  note="Regular-season-input series home win %, latest era")
        FACTS.guard("series_coin_flip", 50.0 <= last <= 53.5,
                    claim="barely better than a coin flip", value=f"{last:.1f}%")
        print(f"   ► Regular season: per-game home edge fell {dpg:.1f} pp across eras,")
        print(f"     but the series edge fell only {ds:.1f} pp (now {last:.1f}%).")
    po = _span("po_pgame", "po_series")
    if po is not None:
        dpg, ds, last = po
        # Fact for the prose (§5): the playoff-input series advantage today, a
        # touch above the regular-season series figure (series.rs_now).
        FACTS.set("series.po_now", last, "{:.0f}%",
                  note="Playoff-input series home win %, latest era")
        if rs is not None:
            FACTS.guard("playoff_series_above_regular", last >= rs[2],
                        claim="the playoff series advantage sits at or above the regular-season series advantage",
                        value=f"playoff {last:.1f}% vs regular {rs[2]:.1f}%")
        print(f"   ► Playoffs: per-game edge fell {dpg:.1f} pp, series edge fell {ds:.1f} pp"
              f" (now {last:.1f}%).")
    print()
    print("   Caveats: the playoff per-game % conflates home court with seeding (better")
    print("   teams host more), so the regular-season row is the cleaner pure-venue")
    print("   input. The sim assumes games are independent given the per-game edge, so")
    print("   it illustrates the format's leverage rather than forecasting a series.")
    print()


def compute_playoff_quality_plotdata(df: pd.DataFrame) -> dict:
    """Chart-ready playoff seeding decomposition: the HCA year-trend before and
    after controlling for the seed-quality gap, plus home win % by who hosts.
    Same numbers run_playoff_quality_decomposition prints. Backs the claim that
    the playoff decline is genuine home-court erosion (quality control barely
    moves the trend) and that even the weaker team wins when it hosts.
    """
    if "quality_diff" not in df.columns:
        df = _add_quality_diff(df)
    po = df[df["is_playoff"] == 1].dropna(subset=["quality_diff", "game_in_series"]).copy()
    p_bar = po["home_win"].mean()
    with suppress_noisy_fit_warnings():
        m_year = smf.logit("home_win ~ year", data=po).fit(disp=0)
        _warn_if_not_converged(m_year, "compute_playoff_quality_plotdata: m_year")
        m_full = smf.logit("home_win ~ year + quality_diff", data=po).fit(disp=0)
        _warn_if_not_converged(m_full, "compute_playoff_quality_plotdata: m_full")
    c_raw = m_year.params["year"]
    retained = 100.0 * m_full.params["year"] / c_raw if c_raw else float("nan")

    def _hw(games, neg=False):
        s = po[po["game_in_series"].isin(games)]
        if neg:
            s = s[s["quality_diff"] < 0]
        return (100.0 * s["home_win"].mean(), len(s))

    return {
        "pp_raw": _pp(c_raw, p_bar),
        "pp_adj": _pp(m_full.params["year"], p_bar),
        "retained": retained,
        "seed_bars": [
            ("Higher seed\nhosts (G1–2)", *_hw([1.0, 2.0])),
            ("Lower seed\nhosts (G3–4)",  *_hw([3.0, 4.0])),
            ("Weaker team\nhosts (G3–4)", *_hw([3.0, 4.0], neg=True)),
        ],
    }


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

    with suppress_noisy_fit_warnings():
        m_year = smf.logit("home_win ~ year", data=po).fit(disp=0)
        _warn_if_not_converged(m_year, "run_playoff_quality_decomposition: m_year")
        m_qual = smf.logit("home_win ~ quality_diff", data=po).fit(disp=0)
        _warn_if_not_converged(m_qual, "run_playoff_quality_decomposition: m_qual")
        m_full = smf.logit("home_win ~ year + quality_diff", data=po).fit(disp=0)
        _warn_if_not_converged(m_full, "run_playoff_quality_decomposition: m_full")

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
    with suppress_noisy_fit_warnings():
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
        FACTS.set("pq.weaker_hosts", hw_g34, "{:.1f}%",
                  note="Playoff home win % when the objectively weaker team hosts (G3/G4)")
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

    with suppress_noisy_fit_warnings():
        try:
            m_base = smf.logit(f_base, data=reg).fit(
                disp=0, cov_type="cluster",
                cov_kwds={"groups": reg["year"].values})
            _warn_if_not_converged(m_base, "run_team_quality_robustness: m_base")
            m_fe = smf.logit(f_fe, data=reg).fit(
                disp=0, cov_type="cluster",
                cov_kwds={"groups": reg["year"].values})
            _warn_if_not_converged(m_fe, "run_team_quality_robustness: m_fe")
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
    FACTS.set("teamfe.max_shift", max_shift, "{:.1f}", unit="pp",
              note="Largest era-coefficient change after adding home/away team fixed effects")
    verdict = "stable" if max_shift < 1.5 else "shifted"
    not_str = "not " if verdict == "stable" else ""
    print(f"   ► Era coefficients are {verdict} under team FE — the decline is")
    print(f"     {not_str}explained by which franchises host games.\n")


def run_format_period_analysis(df: pd.DataFrame) -> None:
    """Playoff home win % by format period — pairwise tests between consecutive
    periods, plus a logistic model testing whether the format changes add a
    level shift beyond the secular year trend."""
    from scipy.stats import chi2
    from statsmodels.stats.proportion import proportions_ztest

    po = df[df["is_playoff"] == 1]
    if po.empty:
        return
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

    # Fact for the prose (§5): the raw playoff home-win drop across the 2014
    # format change (2003-13 period vs 2014-26 period).
    if {"2003–13", "2014–26"} <= counts.keys():
        (w3, n3), (w4, n4) = counts["2003–13"], counts["2014–26"]
        FACTS.set("format.drop_2014", 100.0 * (w3 / n3 - w4 / n4), "{:.0f}",
                  note="Playoff home win % drop, 2003–13 to 2014–26 format period (pp)")

    print(f"\n   Consecutive periods — two-proportion z-tests:")
    avail = [lbl for lbl, *_ in nba.PLAYOFF_FORMAT_PERIODS if lbl in counts]
    default_ref = nba.PLAYOFF_FORMAT_PERIODS[2][0]   # "2003–13"
    fmt_ref = default_ref if default_ref in counts else (avail[0] if avail else default_ref)
    for a, b in zip(avail, avail[1:]):
        (wa, na), (wb, nb) = counts[a], counts[b]
        z, p = proportions_ztest([wa, wb], [na, nb])
        diff = 100.0 * (wb / nb - wa / na)
        p_s = _fmt_p(p)
        print(f"   {a:>8} → {b:<8}  {diff:+5.1f} pp   "
              f"(z = {z:+.2f}, p = {p_s}  {_stars(p).strip()})")

    with suppress_noisy_fit_warnings():
        m_year = smf.logit("home_win ~ year", data=po).fit(disp=0)
        _warn_if_not_converged(m_year, "run_format_period_analysis: m_year")
        m_fmt  = smf.logit(
            f"home_win ~ year + C(format_period, Treatment('{fmt_ref}'))",
            data=po,
        ).fit(disp=0)
        _warn_if_not_converged(m_fmt, "run_format_period_analysis: m_fmt")

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
