# Detailed Outline — home_court_findings.md

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

## Introduction (Intro / TL;DR)
- **Three guiding questions:** (1) Has HCA really changed? (2) What makes home court an advantage? (3) What's driving the decline — and what isn't?
- **Headline answers:**
  - Change is real & one-directional: regular-season home win rate **~65% → 55%**; playoffs **~68% → 58%**. Shape = a slow gradual fade + steeper stretches in the mid-1990s and post-2017, with a brief visible uptick around 2002-04 in between.
  - HCA is built from four box-score categories (shooting, rebounding, foul calls, turnover margin) that capture **~95%** of it, shooting the largest; plus smaller rest & altitude boosts for specific matchups.
  - Decline drivers (four categories, ~96% of RS decline): fairer officiating, the shift to three-point shooting, the fading home rebounding edge, and the closing turnover gap. Rebounding is the largest single channel and is independent of the three-point shift.
- **Why it matters:** In the 1980s and 1990s, a weaker team playing at home in the playoffs won 65% and 66% of those games, nearly the same rate as the stronger team hosting. Today that number is 49%. Home court used to compensate for being outmatched; it no longer does. The decline also reveals three real changes in the game: officiating grew more even, the three-point move flattened the home shooting edge, and teams abandoned the offensive glass. It corrects the crowd assumption: arenas are fuller than ever (attendance records in the same years HCA bottomed).
- **Ruled-out suspects:** rule changes, travel, time zones, pace, crowd size, playoff format changes (best-of-seven shifts and Finals reschedules, incl. 2014), fewer back-to-backs (~8% of decline). Competitive balance is a partial exception: it can't explain the long-run decline (parity is mean-reverting; HCA has declined steadily for 40 years), but year-to-year parity fluctuations show a weak association with HCA fluctuations in the same year.
- **Scope:** regular season vs. playoffs tracked separately (same direction, different timeline); ~52,000 games; tables in home_court_results.md.

---

## Section 1 — The 40-Year Decline
**Q1: Has it changed?**

- **Core stat:** Home win rate ~65 → ~55 per 100; ~quarter-point/year.
  - *RESULTS:* Reg season GLM **−0.244 pp/yr** [−0.280, −0.209], p<0.001, total ≈ **−10.3 pp**; OLS −0.250 pp/yr, R²=0.745.
  - *RESULTS:* Playoffs GLM **−0.225 pp/yr** [−0.359, −0.091], p<0.001, total ≈ **−9.5 pp**; OLS −0.216 pp/yr, R²=0.195; peaked ~68% → 58% today (~9 to 10 pt drop, noisier).
- **Mostly one slow fade; two brief accelerations within it (not extra drops on top):**
  - Slow fade (~quarter-point/year) accounts for nearly the whole drop; changepoint test reads it as smooth, not a staircase.
  - First (firmer) acceleration: mid-to-late 1990s, ~65% → 60%, traces to 1994–95 hand-checking crackdown. *RESULTS era slope 1984–94: −0.522 pp/yr, p<0.001.*
  - Brief uptick ~2002–04: visible but only 3 seasons, not significant (p=0.23).
  - Second acceleration: after 2017, below 56% — the three-point shift on the calendar; defers to §3 mechanism, not a separate event.
  - Playoffs lagged: steady ~64% through 2017, then joined slide → 61% → 58%.
- **Still near-universal today (@fig-team-season-hca):** most recent regular season, all but one team won more at home than on the road. Single-season dumbbell (home% blue, road% grey, gap bar; red = the lone team that won more on the road). Noisy snapshot of how widespread HCA still is, not a franchise ranking.
- **Decline is league-wide, not team-concentrated (@fig-team-decline-slopes):** per-franchise year-slopes of the home-minus-road win gap, fit separately by OLS then split into true spread vs sampling noise (EB / variance-decomposition idiom). *RESULTS: pooled league slope −0.49 pp/yr (p<0.001); observed SD of team slopes 0.213, noise-adjusted true between-team SD ≈ 0.00 (100% of spread is noise); 0/31 franchises with a positive raw slope.* Every franchise faded at one shared league rate; no team stands apart as the cause. Regular season only (per-team playoff samples too small); playoff decline is itself league-wide.
- **Era table** moved to §4 (where rule changes are analyzed); in §1 the eras serve as the calendar the rest of the report runs on.
- **Where the trend is headed:** 3PA share approaching ceiling (~40%); league OREB rate approaching floor (~26%, down from 33%). If both forces are near their asymptotes, pace of decline should slow. Floor from empty-arena data: home teams won 51% with no crowd/bias/prep edge, probably the long-run lower bound. Information diffusion as mechanism is not basketball-specific: other sports investing heavily in analytics are likely on the same trajectory (prediction, not tested here).
**Figures:**

![Season trends](../generated/images/home_court_advantage_season.svg){#fig-advantage-season}

![Current-season team home vs road win%](../generated/images/home_court_team_season_hca.svg){#fig-team-season-hca}

![Per-franchise HCA decline slopes vs the league rate](../generated/images/home_court_team_decline_slopes.svg){#fig-team-decline-slopes}

---

## Section 2 — What Creates Home Court Advantage
**Q2: What makes up HCA?**

- **Referee foul calls and free throws** (most consistent component; Dean Oliver's "FT rate" factor):
  - 1984–94 reg season: ~**1.2 fewer fouls** on home (RESULTS −1.23) → **~2 more FTA/game** (RESULTS +1.97); playoffs ~**1.6 fewer fouls** (RESULTS −1.58) → **~2.4 more FTA/game** (RESULTS +2.35).
  - Playoff universality: **45 of 47** officials (≥50 playoff games) home-favoring; holds under all checks.
- **Shooting advantage:** home shoot **>1 pp better FG%** (RESULTS 1984–94: +1.57 FG%, +1.56 eFG%); consistent across eras, both contexts.
- **Shot selection:** more attempts from close range, fewer mid-range → structural expected-scoring advantage. *RESULTS shot zones 1995–01 reg: Paint +1.28, Mid-Range −1.24.*
- **Rebounding & ball control:** ~**1.5 extra rebounds** (RESULTS REB diff +1.52) and ~**0.4 fewer turnovers** (TOV diff −0.38); together rival shooting.
- **Box-score accounting (mediation):** Dean Oliver's Four Factors (eFG%, FT rate, TOV%, OREB%) are a *complete* set (every possession ends in a shot, turnover, FT trip, or rebound), so the payoff isn't discovering which categories matter but quantifying each one's share = **~95% of advantage** (reg season); shooting (eFG%) biggest (**>40%**), then rebounding.
  - *RESULTS level decomp (reg):* eFG% **43%**, REB **25%**, Foul **14%**, TOV **13%**, unexplained 5%; category R²=0.615.
  - *RESULTS playoffs level:* eFG% 33%, Foul 17%, TOV 22%, REB 21%, unexplained 7% (~93% total).
  - **Coefficient stability across eras:** re-fitting the LPM within each of the six eras confirms the channel weights are nearly constant (eFG% +3.28 to +3.61 pp, Fouls −1.63 to −2.20 pp, TOV −3.19 to −3.57 pp, REB +1.57 to +1.70 pp). The pooled decomposition is not an artifact of blending very different periods. *RESULTS: coefficient stability table in MEDIATION section.*
- **Rest & altitude (@fig-rest-altitude):**
  - Rest: home better-rested wins **62.8%** (+2.7 pp); away better-rested **57.6%** (−2.6). *RESULTS χ²(2)=79.22, p<0.001; +1.6 pp/day reg, +2.4 pp/day playoffs; no era change (LR p=0.474).*
  - Altitude (DEN/UTA): **+7.9 pp** reg season (RESULTS [+6.1,+9.7], p<0.001); **absent in playoffs** (−1.6, p=0.633) — team-quality confound.
  - Playoff rest confounded: controlling for quality, rest shrinks to nothing (RESULTS rest +1.6 pp p=0.113; quality_diff dominant).
**Figures:**

![Box-score differentials](../generated/images/home_court_advantage_differentials.svg){#fig-advantage-differentials}

![Rest & altitude (home win % by rest situation; altitude teams vs league)](../generated/images/home_court_rest_altitude.svg){#fig-rest-altitude}

---

## Section 3 — What's Driving the Decline
**Q3: What drove the change?**

- **Framing (intro, two-questions bridge + table):** keeps two questions apart: *where* the decline shows up on the stat sheet (box-score accounting, clean answers) vs. *what changed in the real world* to cause it (the more interesting question; data settles only part). Honesty-as-feature: some causes proven, some proposed. Bridge **table** maps each category → share → real-world cause → proven/proposed: REB 30% (cause = teams stopped crashing the O-glass; **proposed**, data can't say why), TOV 27% (half 3PA proven, half better visiting-team prep proposed → **mixed**), eFG% 21% (3PA shift; **proven**), Foul 18% (half 3PA + half fairer/more uniform officiating; **proven**). 3PT revolution runs through 3 of 4 rows (~half the decline) but its own channel (shooting) is only ~21%; REB is the largest channel and the one row 3PA never touches. The two proposed causes may share one root (analytics reaching all 30 teams).
- **Shot selection changed in two ways (together ~21% of decline, both feeding the shooting line):**
  - **First: shot zone convergence (reg season).** Paint gap **~1.3 → 0.2 pp**. *RESULTS Paint trend −0.041***/yr reg.* Playoffs: narrowed late 2010s then rebounded; NOT statistically established (playoff Paint trend −0.030, ns) → reg-season story.
  - **Second: the three-point revolution.**
  - Tracks decline over four decades in lockstep. 7% threes (1980s, 65% wins) → 40% (today, 55% wins).
  - **Marks (not fully causes) the second drop (§1):** 3PA share rose from ~¼ of shots to nearly 40% right after 2017 — the years home court slid below 56%. Timing coincidence is strong; the measured causal bite runs through the shooting channel (~1/5 of decline), with the broader perimeter shift also absorbing ~half of the foul and turnover channels (rebounding, the largest channel, stays independent of it). *RESULTS 3PA%: 23.8% (2005–17) → 37.5% (2018–22) → 40.5% (2023–26).*
  - *RESULTS reg season-level Pearson r = −0.902, p<0.001.* **BUT: both series I(1) and NOT cointegrated; detrended partial r = −0.526 (raw r collapses ~40% once shared drift is removed); Granger test shows 3PA rate does NOT temporally lead HCA in either direction. Season-level correlation is largely a parallel-trend artifact — within-era game-level test is the reliable evidence.**
  - Within-era effect: ~**2 fewer home wins/100 per 10-pp rise** in 3PA. *RESULTS game-level −2.64 pp/10pp; within-era −2.27 pp, p<0.001.* This survives as the substantive finding.
  - **No temporal lead (Granger):** the annual rise in threes doesn't lead the HCA decline by a year, nor vice versa; both shift within the same season. *RESULTS: 3PA→HCA lag-1 F=1.49 p=0.23; lag-2 F=1.37 p=0.27; reverse also ns.* Consistent with both being downstream of the same strategic shift. (Note: folded into the 3PA narrative in FINDINGS, not a separate paragraph.)
  - Playoffs: directional but weaker within-era signal (r=−0.499; within-era p=0.027) — team quality dominates.
- **Rebounding (the glass), largest independent channel, now explained:**
  - Home rebounding advantage shrunk 40 yrs, NOT a 3-point byproduct.
  - *RESULTS 3PA control (@fig-3pa-control):* eFG% **210%** absorbed → shooting decline fully accounted for by the 3PA shift (point estimate flips sign, but that below-zero portion rests on conditioning on a mediator, so read it as "fully absorbed," not a real reversal); REB only **8%** absorbed (survives, p<0.001); TOV **54%** absorbed (~half independent); Foul 51%. Playoffs noisy — only REB survives.
  - **Died on the OFFENSIVE glass.** *RESULTS rebounding decomp (reg):* OREB diff +0.61 → **−0.05** (goes negative); DREB diff +1.64 → +0.59 (only softens); REB diff +2.24 → +0.54. Trends/yr all negative, all p<0.001 (OREB −0.018, DREB −0.027, REB −0.044).
  - **Direction of convergence:** home OREB rate fell **34% → 26%** (−8 pp); away OREB rate fell **31% → 26%** (−5 pp). The gap closed because home teams retreated faster, not because away teams improved. (Chart left panel now shows home vs. away OREB rates directly.)
  - **Pace-free share advantage** (home share of available boards − away) still collapses ~10×: **+2.14pp → +0.21pp** (trend −0.052/yr, p<0.001). → not a pace/volume artifact.
  - **Cause = league-wide retreat from O-rebounding:** league OREB rate 33% → 26%; home share advantage declined alongside. **Cointegration check: both series I(1) and NOT cointegrated — the r=+0.82 is likely spurious (parallel long-run trends).** The reliable evidence for the rebounding fade's independence is the 3PA control (only 8% absorbed), not the season-level correlation.
  - Playoffs: share advantage **+2.74pp → +0.70pp** (trend −0.046/yr, p<0.01). 3PA-control absorption is unstable in playoffs (−42%, noisy small-N) → can't confirm independence the way RS does; read as consistent with RS, not proven.
  - **Player-tracking (last decade) fits:** no measurable home box-out advantage today (mean −0.00/gm, p=0.78); OREB-conversion advantage still shrinking (+0.71 pp mean, −0.086/yr, **p=0.024**); 2nd-chance-points advantage no significant trend (+0.29 mean, ns, p=0.304). *RESULTS: PLAYER-TRACKING REBOUNDING MECHANISM.* Full treatment moved to §6; brief mention kept here to close the rebounding argument.
- **Referee foul bias narrowed:**
  - Reg season **1.2 → ~0.25 fouls/game** (≈**80% reduction**); free throw edge **+1.97 → +0.46 FTA/game**. Playoffs **1.6 → 0.7 fouls**; **+2.35 → +1.09 FTA/game**. *RESULTS reg trend +0.022***/yr; 2023–26 = −0.25 fouls, +0.46 FTA.*
  - Generational shift: most home-favoring refs (Garretson, Crawford, Rush) worked 1990s–2000s; distribution compressed (@fig-referee-era).
- **Adding it up (trend decomposition):**
  - Reg season: four categories = **~96% of decline**; all four trends p<0.001. *RESULTS:* REB **30%**, TOV **27%**, eFG% **21%**, Foul **18%**; unmediated 4%. → overlooked pair (REB+TOV) carries >half.
  - Playoffs: overall trend 4× less precisely measured than RS (CI [−0.359, −0.091] vs [−0.280, −0.209]); categories = **only ~67%**; ~⅓ unexplained. *RESULTS:* REB 28%, Foul 18%, eFG% 12%, TOV 10%; unmediated 33%. Only Foul & REB trends significant (p<0.05); eFG% & TOV trends not distinguishable from noise → split is suggestive/consistent-with-RS, not independently established. Strongest playoff evidence is the venue/seeding control (§5), not the box score. Unexplained third has no box-score column to point at.
  - **Bootstrap 95% CIs (season block resample, B=500):** RS shares tightly pinned — REB decline share [25, 38]%, channels carry the decline 96% [87, 107]% and the level 95% [91, 97]%. Playoff shares loose — channels carry the decline 67% [38, 107]%, level 93% [86, 102]%; the wide band is the statistical reason the playoff split is read as consistent-with-RS, not established on its own. Headline CIs annotated on @fig-mediation-level / @fig-mediation-decline. *RESULTS: MEDIATION → Bootstrap 95% CIs on the shares.*
- **3PA reaches ~half the decline, but not the whole:** within-season link is genuine (−2.27 pp/10pp, p<0.001). It registers most directly as the shooting channel (~21% of decline; eFG% 210% absorbed under the 3PA control, i.e. fully accounted for), and also absorbs ~half of the foul (51%) and turnover (54%) channels — so the perimeter shift touches close to half the decline overall. Rebounding (the largest single channel, 30%) is the part it does NOT explain (only 8% absorbed). (Point now made within the 3PA narrative in FINDINGS, not as a separate closing paragraph.)
- Data most consistent with information diffusion: as analytical strategies spread uniformly across all 30 teams, strategies converged toward the same optima regardless of venue, and the home familiarity advantage compressed alongside them.
**Figures:**

![Mediation shares (leads the section as the roadmap)](../generated/images/home_court_mediation.svg){#fig-mediation}

![Shot zones](../generated/images/home_court_shot_zones.svg){#fig-shot-zones}

![3PA vs HCA](../generated/images/home_court_3pa.svg){#fig-3pa}

![Rebounding decomposition (home vs away OREB rates converging; share advantage vs league OREB rate)](../generated/images/home_court_rebounding.svg){#fig-rebounding}

![Referee era distribution](../generated/images/home_court_referee_era.svg){#fig-referee-era}

![3PA-control channel test, a before/after dumbbell in win-% per decade: each category's contribution to the decline before (open dot) and after (filled dot) games are compared at the same number of threes; a dot pulled to zero (or past it) means the move to threes explains that category's whole decline, a dot that stays out declined on its own. RS shooting crosses past zero (move to threes explains all of it), rebounding barely moves (its decline is its own), fouls/turnovers ~half; playoffs greyed except rebounding.](../generated/images/home_court_3pa_control.svg){#fig-3pa-control}

---

## Section 4 — What Didn't Drive the Change
**Q4: What did NOT contribute to the decline (though people often assume it did)?**

- **Rule changes:** only the **1994–95 season** left a mark (~**−2.6 pp** discrete step; RESULTS era:1995–01 −0.108 log-odds, p=0.010; LR χ²(5)=20.68, p<0.001). Two changes that season — hand-check crackdown (more consistent with channel data) + shortened 3-pt line (1994–97) — confounded at season level; channel event study shows foul diff responded immediately and significantly (level p=0.007) while shooting did not (p=0.327), pointing toward hand-checking. The step was immediate but the multi-year adjustment continued through the late 1990s. **Break-point test:** formal QLR supremum-Chow test locates the *slope* shift in the **late 1990s** (sup F=10.22, p<5% by Andrews 1993 critical values), slope going from −0.65 pp/yr before to −0.26 pp/yr after — read as the 1994–95 adjustment settling in, though the ~4-yr lag makes the link an inference. Playoffs show no significant break (sup F=3.23, n.s.) — steady drift. All other boundaries passed through; playoffs neither change registers (LR p=0.815).
- **Shape of the decline: continuous drift, not shocks (@fig-bayesian-changepoint).** Smooth drift, not a staircase of sudden drops at the rule boundaries. The structural-break test marks a slope change ~1999 (decline ran steeper through the late 1990s, eased after) but no level jump; CUSUM finds no structural instability across 40 seasons. Granger: 3PA does not temporally lead HCA; both co-move, pulled by the same underlying force. (Figure and prose discussion now live in the Investigation Part 2 "Rule Changes and the Era Labels," not the findings §4 narrative; kept here as the analyst cross-reference to results. Supports the rule-boundary verdict; the post-2017 steepening rests on the §3 3PA evidence, not this coarse test.)
- **Bayesian change-point model:** strongly favors ≥1 slope change over a straight line (BF=14.2 for k=1 vs k=0). Evidence splits between two and three breaks: k=2 P=40.5%, k=3 P=38.8% (essentially tied, BF(k=3 vs k=2)=1.0), k=1 P=19.3%. Best-fit break years: k=1: 1999 (HPD 1992–2003); k=2: 1992 & 2020; k=3: 1988, 1998, & 2020. All models agree on a late-1980s–mid-1990s break; the 2020 break in both k=2 and k=3 reflects COVID disruption + accelerating modern decline. Break years are not precisely datable: the best single break has a bootstrap range ~1993–2002. Posterior-weighted k=1 slopes **−0.577 → −0.255 pp/yr**. Consistent with QLR (best single break ~1999) and CUSUM (no level instability); each test asks a different question. *RESULTS: BAYESIAN CHANGE-POINT MODEL.*

![Bayesian change-point model (k=0/1/2/3 fitted lines; posterior distribution over break year for k=1)](../generated/images/home_court_bayesian_changepoint.svg){#fig-bayesian-changepoint}

- **Travel & time zones:**
  - Reg: ~**0.07 pp/100 mi** (RESULTS −0.07 pp/100mi, p=0.010), tiny & inconsistent direction; playoffs no effect (p=0.888).
  - Time zones flat both contexts (reg −0.4 pp p=0.086; playoffs +1.0 pp p=0.330).
- **Back-to-backs / load management (@fig-back-to-back):** visitor B2B rate fell **35.0% → 18.8%** (1984–94 → 2023–26), confirming the blog's premise. But shift-share of the −9.29 pp RS decline: frequency component only **−0.71 pp (~8%)**; win-rate component −8.59 pp (~92%). Per-situation home win%: visitor-B2B-only 64.7% vs neither 59.1% (narrow gap). RS only (B2Bs rare in playoffs). Scheduling nudged HCA, didn't drive it.
- **Pace of play:** moves independently of HCA. *RESULTS reg season-level r=+0.241 (p=0.120, wrong direction); playoffs r=−0.142 (ns).*

![Back-to-back / load management (visitor B2B rate by era; shift-share of decline)](../generated/images/home_court_back_to_back.svg){#fig-back-to-back}

![Pace vs HCA](../generated/images/home_court_pace.svg){#fig-pace}

- **Home vs. away 3PA differential:** home and away teams attempt threes at nearly identical rates; the trend moves the wrong direction — home teams now take *more* threes than visitors (+0.44 pp in 2023–26 vs. −0.35 pp in 1984–94, trend +0.018***/yr). Not the mechanism behind the decline. *RESULTS 3PA rate diff trend +0.018***/yr.*
- **Competitive balance:** can't explain the long-run decline. Parity is mean-reverting (I(0) stationary) while HCA has declined steadily for 40 years — structurally, they can't be linked as cause and effect. Raw correlation near zero (RESULTS r=−0.092, p=0.556); era pattern inconsistent. Small wrinkle: detrended association emerges (first-diff r=−0.330 p=0.033; residual r=−0.345 p=0.023) but modest, small sample — means year-to-year parity fluctuations weakly track HCA fluctuations, not that parity drives the decline.

![Parity vs HCA](../generated/images/home_court_parity.svg){#fig-parity}

- **Crowd size:** arenas near capacity throughout (~17k→18k+), records set as HCA hit lows. *RESULTS r=+0.248 (p=0.212); detrended ns.* Playoffs ~guaranteed sellouts yet faded too.

![Attendance & empty-arena](../generated/images/home_court_attendance.svg){#fig-attendance}

- **Empty-arena experiment (2020–21):** empty **51.0%** vs. fans present **58.5%** (RESULTS n=573 vs 591). Presence > count (dose-response +0.51 pp/1000 fans, p=0.184 ns). Vanished when arenas refilled → a switch, not a slow dial.
- **All together:** full model — era effect ≈ half of predictive power; situational factors ≈ other half. *RESULTS Shapley: Era 53%, Rest 17.9%, Altitude 23.7%, TZ 1.4%, COVID 4.5%.* Net era decline **−9.0 pp** (1984–94 → 2023–26) after all controls.
- **Pre/post-2014 test:** rest/altitude/TZ effects statistically unchanged across line; baseline home advantage dropped **~4.7 pp** anyway (RESULTS post2014 level shift −0.196, −4.7 pp p<0.001; rest & TZ interactions ns, altitude weakened p=0.026). Situational factors held still while the baseline dropped.

---

## Section 5 — The Playoff Picture

- **Averaged across the four decades, which arena a playoff game is in has mattered more to the outcome than the quality gap between the two teams (among measured factors).** All-era-average claim, not present-tense: the venue edge that once overwhelmed quality has nearly flattened (see seed split below, §5 L178). (Removed prior overclaims "more than anything else" and the unqualified present-tense "more reliably than quality.")
  - *RESULTS by game:* G1 **69.4%**, G2 **71.9%**, G3 **55.0%**, G4 **55.3%**, G5 **74.5%**, G6 **55.5%**, G7 **63.8%**. χ²(6)=84.54, p<0.001.
  - No evidence road teams adapt as series deepens; home-away split explains it entirely.

![Playoff win % by game number](../generated/images/home_court_series_breakdown.svg){#fig-series-breakdown}

![Playoff seeding decomposition (decline survives quality control; weaker host still wins)](../generated/images/home_court_playoff_quality.svg){#fig-playoff-quality}

- **Lower-seed home win rate collapsed by decade (run_series_era_split):** 1984–94: lower seed at home **65.4%** vs higher seed **71.0%** (gap 5.6 pp); 1995–01: **65.8%** vs **60.1%** (gap −5.7 pp — lower seed won MORE at home this era); 2005–17: **51.5%** vs **75.2%** (gap 23.7 pp); 2018–22: **47.4%** vs **71.7%** (gap 24.4 pp). In the early eras the lower seed won nearly as often at home as the higher seed did. By the modern era the gap widened to 22+ pp. FINDINGS frames this as: quality barely mattered once you were in your own building (1980s–90s); it does now.
- **Decline is real weakening, not weaker seeds (@fig-playoff-quality):**
  - *RESULTS:* year trend retained **102%** after quality control; quality absorbs −2%.
  - Lower-seed-at-home (G3+G4): still wins **51.5%** (n=827) — pure venue effect.
  - Seed-quality gap did trend slightly (−0.00026/yr, p<0.001) but doesn't explain HCA decline.
- **2014 format change didn't cause drop:** raw −6.8 pp from 2003–13 → 2014–26 (z=3.10, p=0.002), but trend-controlled dummy ns (p=0.298); LR χ²(3)=4.68, p=0.197. Format table (4 periods).

![Win % by format period](../generated/images/home_court_advantage_format_bars.svg){#fig-advantage-format-bars}

- **Best-of-7 absorbs most of home court, and most of its decline (@fig-series-simulation):** Monte Carlo, 200,000 simulated 2-2-1-1-1 series between two equal teams, home-court team hosts G1,2,5,6,7. Per-game home win % → series win % for the home-court team.
  - *RESULTS series simulation table:* RS 1984–94 **64.9%/game → 54.9% series**; 2023–26 **55.6% → 51.9%**. PO 1984–94 **67.9% → 56.0%**; 2023–26 **57.6% → 52.5%**.
  - Format compresses level and decline: RS per-game edge fell **9.3 pp** across eras but series edge fell only **3.0 pp** (now 51.9%, barely a coin flip); PO per-game −10.3 pp → series −3.4 pp (now 52.5%).
  - Caveats: PO per-game conflates home court with seeding (RS row is cleaner pure-venue input); sim assumes game independence → illustrates format leverage, not a forecast.

![Series simulation: per-game edge → much smaller series edge, drifting toward 50% over eras](../generated/images/home_court_series_simulation.svg){#fig-series-simulation}

---

## Section 6 — Other Findings

- **Referee differences real but overstated:** 45/47 home-favoring; spread ~1 foul/game between most-leaning (Garretson −1.734 shrunken, Crawford, Rush) and most even-handed (Brothers, Tiven, Forte). **~60% of raw spread = sampling noise** (RESULTS true between-SD 0.407 vs observed 0.645). Measures tendencies, not game-fixing.
- **Denver & Utah best home court — altitude the likely reason:** Nuggets **+26.8 pp**, Jazz **+25.7 pp** shrunken (league mean +20.0). ~70% of franchise variation is real (true SD ≈4.1 pp). Altitude piece ≈8 of those points. (n=2 high-altitude teams — elevation can't be fully separated from other franchise-specific factors.)

- **Referee differences real but detailed (@fig-referee-rankings):** top/bottom 15 officials ranked by career mean shrunken home foul differential — Garretson, Crawford, Rush most home-favoring; Brothers, Tiven, Forte most even-handed.

![Referee rankings](../generated/images/home_court_referee_rankings.svg){#fig-referee-rankings}

![Franchise HCA](../generated/images/home_court_team_hca.svg){#fig-team-hca}

- **Playoff franchise differences = illusion:** true between-franchise SD ≈ **0.0** (100% noise); all collapse to league mean +26.9 pp. Apparent postseason home-court strength reflects being a good team that plays more home games.
- **Home court worth more in playoffs:** reg **~20 pp** vs. playoffs **~27 pp** → **+7 pp postseason premium** (RESULTS +7.2 pp, SD 7.4). Reg/playoff consistency positive but weak (raw r=+0.362, p=0.042).
- **Player-tracking caught the final chapter of the rebounding fade (@fig-rebounding-tracking):** OREB-conversion advantage fell from ~1.2 pp (mid-2010s) to under 0.2 today; box-out advantage essentially zero throughout. Cameras confirmed a fade already nearly complete before 2013–14. *RESULTS: OREB conversion p=0.024*, box-out p=0.775.*

![Player-tracking rebounding](../generated/images/home_court_rebounding_tracking.svg){#fig-rebounding-tracking}

- **Margins polarizing — blowouts getting bigger:** home wins bigger, home losses worse, even as home teams win less.
  - Not just a composition effect — confirmed by unconditional quantile regression.
  - *RESULTS reg season:* Q10 **−0.167 pts/yr**, Q90 **+0.050 pts/yr**; IQR widening **+0.217 pts/yr**.
  - *RESULTS playoffs:* Q10 −0.104 (ns), Q90 +0.222 pt/yr; IQR widening **+0.326 pts/yr** — playoff spread driven mainly by big home wins growing (Home wins trend +0.149***/yr).
  - ~0.2–0.3 pts/yr widening in both contexts. Era of close games → era of blowouts.
- **Team strategy implications:** Rebounding is the most tractable remaining home-court lever (30% of decline; only 8% absorbed by 3PA control; tracking data shows conversion edge still declining). Turnover channel has independent component (~46% not 3PA-driven); pressure defense at home targets it. Crowd presence = switch (even a few thousand restores full effect; size above that adds little). Away teams: 3PA has already largely equalized the shooting channel. Offensive glass is where road disadvantage persists and no current trend is closing it. Rest: away team entering better-rested = ~3 pp drop in home win rate, available from scheduling.

![Margin trends](../generated/images/home_court_margin.svg){#fig-margin}

---

## Section 7 — Summary
- Recap: HCA nearly halved over 40 yrs; reg **65% → ~55%**, playoffs **~68% → 58%**. In net rating terms: reg-season gap **~3.2 → ~2.0 pts/100 poss** (trend −0.067***/yr); playoffs **~4.3–4.9 → ~3.9 pts/100 poss** (trend −0.036, ns). *RESULTS: NET RATING SPLIT BY VENUE.*
- Shape: slow four-decade fade + steeper stretches in the mid-1990s and post-2017, with a brief visible uptick around 2002-04. 1994–95 rule jolt (most likely hand-checking, confounded with shortened 3-pt line; multi-year adjustment). Post-2017 perimeter shift (three-point surge on the shooting line, parallel offensive-glass retreat on rebounding line); Bayesian model places break near 2020, not 2017 (COVID + acceleration). Bayesian model: ≥1 break strongly favored (BF=14.2 vs no break); k=2 (40%) and k=3 (39%) essentially tied (BF=1.0); break years not datable to better than ~decade. QLR and CUSUM consistent.
- **Q2 now answered in summary (added):** eFG% largest contributor to the level advantage (>40%, 43%); REB second at 25%; four categories carry ~95% of RS level advantage. Summary explicitly states: the same four categories that make up HCA are the ones that narrowed over 40 years.
- **Four drivers; rebounding is the largest** (framing added to counter the 3PA narrative) — **together ~96% of RS decline**; all Dean Oliver's Four Factors: (1) fairer refs — fouls 1.2 → ~0.25/game RS, FTA edge +1.97 → +0.46/game; 1.6 → 0.7 fouls playoffs, FTA +2.35 → +1.09/game; 45/47 officials home-favoring, (2) shot selection changed two ways: paint gap 1.3 → 0.2 pp AND league-wide 3PA rise through the shooting line (within-era −2.27 pp/10pp real; season-level r=−0.902 is co-trending; no Granger lead), (3) rebounding advantage slipped independently — largest channel at 30%; 3PA control only 8% absorbed; home OREB rate 34% → 26% (−8 pp), away 31% → 26% (−5 pp); home teams retreated faster, (4) **TOV now own bold paragraph (extracted from rebounding block):** TOV gap ~27% of RS decline; 0.4 fewer turnovers → ~0.0; ~half from 3PA perimeter shift (fewer drives = fewer live turnovers), half independent; same pattern in playoffs but too noisy to read independently; cause not established.
- Ruled out: rule changes (except 1994–95), travel, time zones, pace, crowd size, format. Competitive balance can't explain the long-run decline (parity is mean-reverting, HCA is a 40-year trend), though year-to-year parity fluctuations show a weak association; treated as exploratory. Fewer back-to-backs explain only ~8% of the RS decline. Crowd presence = on/off switch (2020–21 51% vs 58.5%; isolates presence, not noise itself), not a slow fade.
- Playoffs follow reg season with **nearly a two-decade delay**; trend direction not in doubt but 4× less precisely measured than RS (CI [−0.359, −0.091]); accelerated since 2018; genuine weakening (weaker host still winning less). Game-by-game structure stark: G1 69%, G2 72%, G5 74.5%, G7 64%. Lower-seed home win rate: **65%/66%** in 1980s–90s (nearly matching the higher seed) → **49%** in 2023–26; higher seed held near 70–77% from mid-2000s onward. Home court used to compensate for quality; it no longer does.
- Franchise notes: Denver & Utah strongest reg-season home courts (~27 & ~26 pts above own road rate), altitude the likely reason (n=2, confounded with franchise) — washes out in playoffs (franchise spread indistinguishable from zero). Home court worth **~7 pts more in playoffs** than reg season.
- Blowouts getting bigger as HCA falls (IQR widening ~0.2–0.3 pts/yr in both contexts).

---

## Appendix A — The Box-Score Model Predicts a Decline It Never Saw
- **Out-of-sample forecast (@fig-oos-forecast):** four-factor win model trained only on games through 2013, coefficients frozen, then used to predict each 2014–2026 season's home win% from that season's box-score edges. *RESULTS: held-out RMSE — RS channel 0.95 pp vs trend-extrapolation 1.45 vs flat-mean 5.48; PO channel 3.87 vs trend 7.30 vs flat 8.11.* The frozen model tracks the held-out decline (RS catches the 2021 dip the trend line misses; PO reconstructs the modern decline that a flat early-trend extension misses entirely). The box-score mechanism predicts the decline it was not built on, so it isn't fitted to hindsight. Moved out of §3 into a lead appendix: it's a credibility check on the method, not a step in the causal argument; §3 keeps a one-line pointer here.

![Out-of-sample forecast: pre-2014-trained channel model vs actual vs trend extrapolation, RS and PO](../generated/images/home_court_oos_forecast.svg){#fig-oos-forecast}

---

## Appendix C — Independent Corroboration (Sparkle Technologies Blog)
- Blog: Sparkle Technologies, same question, independent pipeline. Main agreements: overall decline, foul story, travel/pace irrelevance, altitude (Denver +27 pp, Utah +26 pp — within 0.1 pp of mine).
- **Key disagreement — cause:** blog crowns three-point revolution the primary driver (raw r=−0.88 season-level). I find ~40% of that correlation is parallel-trend artifact (detrended partial r=−0.53; Granger test: no temporal lead). 3PA effect is real within seasons (−2.27 pp/10pp). It registers most directly as the shooting channel (~21% of the decline), and counting its share of the foul and turnover channels (~half of each) reaches close to half the decline overall — still short of the whole story. Rebounding (30%, the largest channel and independent of the 3PA shift) is the piece the blog never measures. Category-vs-cause framing: 3PA is the most far-reaching cause (touches three of four channels) but no single channel it drives is as large as rebounding, which has its own separate cause.
- **Mid-1990s drop:** blog attributes to shortened 3-pt line (1994–97); I attribute to hand-checking crackdown. Events overlap at season level. Channel event study gives leverage: foul diff immediate and significant at 1994-95 (p=0.007); shooting channel not significant (p=0.327). Hand-checking is the more consistent explanation; the two cannot be fully separated.
- **Empty-arena numbers:** blog's "empty arena" figure (54.4%) = 2020–21 season average blending zero-fan and partial-crowd games. My split: empty 51.0% vs. any fans 58.5%. No disagreement on conclusion (presence = switch); blog averaged over the distinction.
- **Back-to-backs:** blog claimed 15–20% of decline; I tested directly — frequency premise confirmed (35.0% → 18.8%); magnitude is ~8%, not 15–20% (shift-share: frequency component −0.71 pp; within-situation component −8.59 pp).
- **What the blog missed:** rebounding channel (absent entirely from blog's box-score account), fading turnover edge, shot-zone convergence, formal playoff seeding control (G3–G4 weaker-host still 51.5%), ruling-out tests for format/balance/crowd.

---

## Key Numbers Registry

Checklist for `/check-consistency`. Each row is one prose claim with the home_court_results.md value it must match. Covers all headline numbers — those in the intro, summary, and section leads, plus numbers that appear in more than one place. Update this table whenever findings prose or the analysis pipeline changes.

**How to use:** work through each row in ID order, locate the prose claim in the findings (use the line number), compare against the home_court_results.md section named, and verify the value matches. After finishing, do a free scan for any numbers in the prose not listed here.

| ID | Findings location | Prose claim | home_court_results.md section | Authoritative value |
|---|---|---|---|---|
| N01 | intro L13; §6 L204 | RS win rate fell from ~65% to ~55% | OVERALL DECLINE, RS era table | 65.0% (1984–94) → 55.6% (2023–26) |
| N02 | intro L13; §6 L204 | PO win rate fell from ~68% to ~58% | OVERALL DECLINE, PO era table | 67.9% (1984–94) → 57.6% (2023–26) |
| N03 | intro L17; §5 L173; §6 L216 | PO lower seed won 65% and 66% at home in 1980s/90s | SEEDING ERA SPLIT, lower-seed column | 65.4% (1984–94), 65.8% (1995–01) |
| N04 | intro L17; §6 L216 | PO lower seed today wins ~49% at home | SEEDING ERA SPLIT, lower-seed column | 49.0% (2023–26) |
| N05 | intro L17; §6 L216 | PO higher seed fell from ~71% to ~65% | SEEDING ERA SPLIT, higher-seed column | 71.0% (1984–94) → 64.7% (2023–26) |
| N06 | §1 L28; §6 L206 | RS decline ~quarter-point per year | OVERALL DECLINE, RS Binomial GLM | −0.244 pp/yr |
| N07 | §1 L28 | RS fell from ~65% to ~60% in mid-1990s | RULE-CHANGE ERAS, RS era table | 65.0% (1984–94) → 59.9% (1995–01) |
| N08 | §1 L28; §3 L86 | 3PA share rose from ~quarter to ~40% | FOUL & SHOOTING ERAS, RS 3PA rate column | 23.8% (2005–17) → 40.5% (2023–26) |
| N09 | §1 L28 | RS rate pushed below 56% (2nd steepening) | RULE-CHANGE ERAS, RS era table | 55.6% (2023–26) |
| N10 | §1 L28 | PO held near 64% through 2017, then 61%, then 58% | RULE-CHANGE ERAS, PO era table | 64.3% (2005–17) → 60.7% (2018–22) → 57.6% (2023–26) |
| N11 | §2 L42; §3 L116 | 1980s RS foul diff ~1.2 fewer fouls/game | FOUL & SHOOTING ERAS, RS 1984–94 foul diff | −1.23 |
| N12 | §2 L42; §3 L116; §6 L208 | 1980s RS FTA diff ~2 more/game | FOUL & SHOOTING ERAS, RS 1984–94 FTA diff | +1.97 |
| N13 | §2 L42; §3 L116; §6 L208 | 1980s PO foul diff ~1.6 fewer fouls/game | FOUL & SHOOTING ERAS, PO 1984–94 foul diff | −1.58 |
| N14 | §2 L42; §3 L116; §6 L208 | 1980s PO FTA diff ~2.4 more/game | FOUL & SHOOTING ERAS, PO 1984–94 FTA diff | +2.35 |
| N15 | §2 L44; §C L270 | 45 of 47 playoff officials home-favoring | REFEREE CREW | 45/47 (96%) |
| N16 | §2 L52 | Four Factors carry ~95% of RS level | MEDIATION, RS level — bootstrap summary | 95% (95% CI [91, 97]%) |
| N17 | §2 L52 | eFG% largest piece, >40% of RS level | MEDIATION, RS level decomp | 43% |
| N18 | §2 L52 | REB is second-largest, 25% of RS level | MEDIATION, RS level decomp | 25% |
| N19 | §3 L73; §6 L206 | Four Factors carry ~96% of RS decline | MEDIATION, RS trend — bootstrap summary | 96% (95% CI [87, 107]%) |
| N20 | §3 L66; §6 L210 | REB 30% of RS decline | MEDIATION, RS trend decomp | 30% |
| N21 | §3 L67; §6 L210 | TOV 27% of RS decline | MEDIATION, RS trend decomp | 27% |
| N22 | §3 L68; §6 L210 | eFG% 21% of RS decline | MEDIATION, RS trend decomp | 21% |
| N23 | §3 L69; §6 L208 | Foul 18% of RS decline | MEDIATION, RS trend decomp | 18% |
| N24 | §3 L73; §6 L208 | PO channels ~67% of decline | MEDIATION, PO trend — bootstrap summary | 67% (95% CI [38, 107]%) |
| N25 | §3 L81; §6 L210 | Paint shot gap fell from 1.3 pp to 0.2 pp (RS) | SHOT ZONE DIFFERENTIALS, RS Paint column | +1.28 (1995–01) → +0.24 (2023–26) |
| N26 | §3 L85 | 7% threes in 1980s, home teams won 65% | LEAGUE-WIDE 3-POINT, RS era table | 6.8% / 65.0% (1984–94) |
| N27 | §3 L87 | ~40% of 40-yr 3PA-HCA correlation is trend artifact | LEAGUE-WIDE 3-POINT, partial correlation | raw r=−0.902 → partial r=−0.526; 42% shrinkage |
| N28 | §3 L89 | 2–3 fewer home wins/100 per 10-pp 3PA rise | LEAGUE-WIDE 3-POINT, game-level logistic | −2.64 pp/10pp (bivariate); −2.27 pp within-era |
| N29 | §3 L97; §6 L212 | DREB diff fell from +1.64 to +0.59 | REBOUNDING DECOMP, RS DREB diff column | +1.64 (1984–94) → +0.59 (2023–26) |
| N30 | §3 L97; §6 L212 | OREB diff fell from +0.61 to slightly below zero | REBOUNDING DECOMP, RS OREB diff column | +0.61 (1984–94) → −0.05 (2023–26) |
| N31 | §3 L101; §6 L212 | Home OREB rate 34% → 26%, fell 8 pp | REBOUNDING DECOMP, RS — league rate + share edge | derived: league 32.9% + share edge +2.74pp → home ≈34.3%; final ≈25.75% |
| N32 | §3 L101; §6 L212 | Away OREB rate 31% → 26%, fell 5 pp | REBOUNDING DECOMP, RS — league rate + share edge | derived: away ≈31.5% → ≈26.1% |
| N33 | §3 L115; §6 L208 | RS foul diff 1.2 → 0.25 fouls (80% reduction) | FOUL & SHOOTING ERAS, RS foul diff column | −1.23 (1984–94) → −0.25 (2023–26); 80% = (1.23−0.25)/1.23 |
| N34 | §3 L115; §6 L208 | RS FTA edge +2 → under 0.5/game | FOUL & SHOOTING ERAS, RS FTA diff column | +1.97 (1984–94) → +0.46 (2023–26) |
| N35 | §3 L115; §6 L208 | PO foul gap 1.6 → 0.7 fouls | FOUL & SHOOTING ERAS, PO foul diff column | −1.58 (1984–94) → −0.68 (2023–26) |
| N36 | §3 L115; §6 L208 | PO FTA edge 2.4 → 1.1/game | FOUL & SHOOTING ERAS, PO FTA diff column | +2.35 (1984–94) → +1.09 (2023–26) |
| N37 | §4 L152 | 1994–95 discrete step ~−2.6 pp | RULE-CHANGE ERAS, RS trend-controlled era:1995–01 | ≈pp = −2.6 (log-odds −0.108, p=0.010) |
| N38 | §4 L154 | Travel ~0.07 pp per 100 miles (RS) | REST, ALTITUDE, AND TIME ZONE | −0.07 pp/100 mi (bivariate logistic) |
| N39 | §4 L154 | B2B frequency 35% → under 20% | BACK-TO-BACKS, visitor B2B by era | 35.0% (1984–94) → 18.8% (2023–26) |
| N40 | §4 L154 | Schedule shift explains ~8% of RS decline | BACK-TO-BACKS, shift-share | frequency component −0.71 pp ≈ 8% of −9.29 pp total |
| N41 | §4 L154 | Rest: home better-rested 63%, visitor better-rested 58% | REST DIFFERENTIAL, RS bucket table | home-more-rest: 62.8%; away-more-rest: 57.6% |
| N42 | §4 L156 | Empty arena 51%, any crowd 58.5% | ARENA ATTENDANCE, 2020-21 | empty 51.0% (n=573); fans present 58.5% (n=591) |
| N43 | §5 L170; §6 L216 | G1 69%, G2 72% | PLAYOFF SERIES STRUCTURE, game table | G1=69.4%, G2=71.9% |
| N44 | §5 L170; §6 L216 | G5 74.5% | PLAYOFF SERIES STRUCTURE, game table | G5=74.5% |
| N45 | §5 L170; §6 L216 | G7 64% | PLAYOFF SERIES STRUCTURE, game table | G7=63.8% |
| N46 | §5 L172; §6 L216 | Lower seed won 65% and 66% in 1980s/90s | SEEDING ERA SPLIT, lower-seed column | 65.4% (1984–94), 65.8% (1995–01) — same as N03 |
| N47 | §5 L172; §6 L216 | Lower seed today: ~49% at home | SEEDING ERA SPLIT, lower-seed column | 49.0% (2023–26) — same as N04 |
| N48 | §5 L172; §6 L219 | Higher seed held 70–75% through 2022 | SEEDING ERA SPLIT, higher-seed column | 74.2% (2002–04), 75.2% (2005–17), 71.7% (2018–22) |
| N49 | §5 L172 | Higher seed fell to ~65% recently | SEEDING ERA SPLIT, higher-seed column | 64.7% (2023–26) |
| N50 | §5 L172 | Gap: 3–5 pp → 20+ pp peak → 15 pp today | SEEDING ERA SPLIT, Gap column | 5.6 pp (1984–94) → 24.4 pp peak (2018–22) → 15.7 pp (2023–26) |
| N51 | §5 L176 | Weaker host (G3–4) wins 51.5% | SEEDING QUALITY DECOMP, lower-seed check | 51.5% (N=827) |
| N52 | §5 L193 | RS: 65%/game → 55% series (1980s) | SERIES SIMULATION, RS 1984–94 row | 64.9%/game → 54.9% series |
| N53 | §5 L193 | RS: ~56%/game → under 52% series (today) | SERIES SIMULATION, RS 2023–26 row | 55.6%/game → 51.9% series |
| N54 | §5 L193 | PO series edge ~52.5% today | SERIES SIMULATION, PO 2023–26 row | 52.5% series |
| N55 | §5 L193 | RS per-game fell ~9 pp, series fell ~3 pp | SERIES SIMULATION, RS summary note | per-game −9.3 pp; series −3.0 pp |
| N56 | §6 L203 | RS net rating ~3 pts → ~2 pts per 100 poss | NET RATING SPLIT BY VENUE, RS era table | 3.22 (1995–01) → 1.97 (2023–26) |
| N57 | §6 L203 | PO net rating ~4.3–4.9 → just under 4 pts | NET RATING SPLIT BY VENUE, PO era table | 4.31 (1995–01), 4.89 peak (2002–04) → 3.93 (2023–26) |
| N58 | §6 L213 | OREB rate fell from 33% to 26% | REBOUNDING DECOMP, RS — share edge note | 32.9% → 25.9% |
| N59 | §C L277 | Denver +27 pp, Utah +26 pp HCA (raw) | FRANCHISE HCA, RS table top rows | +27.9 pp (Denver raw), +26.6 pp (Utah raw) |
| N60 | §C L277 | League average HCA ~20 pp | FRANCHISE HCA, RS summary line | +20.0 pp |
| N61 | §C L277 | ~70% of franchise variation is real | FRANCHISE HCA, RS variance decomp | noise=30%, true SD=4.1/observed SD=4.9 → (4.1/4.9)²≈70% |
| N62 | §C L277 | Altitude adds ~8 pp for Denver/Utah | REST, ALTITUDE, AND TIME ZONE | +7.9 pp [+6.1, +9.7] |
