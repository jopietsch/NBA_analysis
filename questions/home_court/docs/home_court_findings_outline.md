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
  - Change is real & one-directional: regular-season home win rate **~65% → 55%**; playoffs **~68% → 58%**. Shape = a slow gradual erosion + **two sharper one-time drops** layered on top.
  - HCA is built from: referee foul calls, shooting/shot-selection advantage, plus smaller rest & altitude boosts.
  - Decline drivers: neutral whistle, converging shot selection, rise in three-point shooting eroding home court through the shooting channel — and the biggest driver of all (the one nobody was watching): the collapse of the home advantage on the boards (above all the offensive glass), which carries more of the decline than the headline causes combined.
- **Ruled-out suspects:** rule changes, travel, time zones, pace, crowd size, playoff format changes (best-of-seven shifts and Finals reschedules, incl. 2014). Competitive balance is a partial exception: it can't explain the long-run decline (parity is mean-reverting; HCA has declined steadily for 40 years), but year-to-year parity fluctuations show a weak association with HCA fluctuations in the same year.
- **Scope:** regular season vs. playoffs tracked separately (same direction, different timeline); ~52,000 games; tables in RESULTS.md.

---

## Section 1 — The 40-Year Decline
**Q1: Has it changed?**

- **Core stat:** Home win rate ~65 → ~55 per 100; ~quarter-point/year.
  - *RESULTS:* Reg season GLM **−0.244 pp/yr** [−0.280, −0.209], p<0.001, total ≈ **−10.3 pp**; OLS −0.250 pp/yr, R²=0.745.
  - *RESULTS:* Playoffs GLM **−0.225 pp/yr** [−0.359, −0.091], p<0.001, total ≈ **−9.5 pp**; OLS −0.216 pp/yr, R²=0.195; peaked ~68% → 58% today (~9 to 10 pt drop, noisier).
- **Two speeds — gradual drift vs. sharp drops** (key framing for the whole report):
  - **Gradual:** a continuous ~quarter-point/year erosion underneath everything, from the §3 box-score categories grinding down.
  - **Sharp — two drops** layered on top, each a moment when one force accelerated the same trend. "Drops" = stretches of steepened slope, not one-season level jumps. Change-point tests (§3) resolve only the first (slope change in the late 1990s, no level jump; CUSUM still reads 40 yrs as smooth drift); the post-2017 steepening sits at the end of the sample where the break tests have little power and shows up as a step down in era win rates, not a dated break:
    - First drop: sharp mid-to-late 1990s fall ~65% → 60% (steepest move). Cause = **1994–95 rule shock** (§4); deep-dive detail (break-point test, confounds) deferred to §4. *RESULTS era slope 1984–94: −0.522 pp/yr, p<0.001.*
    - Flat for ~two decades.
    - Second drop: after 2017, below 56%. Coincides with the **three-point surge** hitting full stride — but the surge is the most visible *marker* of a broader move to the perimeter, not the whole cause (mechanics in §3). *RESULTS era slopes: 2018–22 −1.183 pp/yr (p=0.009), 2023–26 −0.773 pp/yr (p=0.223).*
  - The drops are not extra causes — they're the same box-score categories' story told at faster speed. Handled in different sections because the events differ: discrete rule shock (§4) vs. gradual stylistic shift inside the categories (§3).
  - Playoffs lagged: steady ~64% through 2017 across 3 eras, joined slide after 2018 → 61% → 58%.
- **Era table** (6 eras, 1984–94 through 2023–26, defined by major rule changes — used as calendar only; causation deferred to §4).
- **Where the trend is headed:** 3PA share approaching ceiling (~40%); league OREB rate approaching floor (~26%, down from 33%). If both forces are near their asymptotes, pace of decline should slow. Floor from empty-arena data: home teams won 51% with no crowd/bias/prep edge, probably the long-run lower bound. Information diffusion as mechanism is not basketball-specific: other sports investing heavily in analytics are likely on the same trajectory (prediction, not tested here).
**Figures:**

![Fig 1 — season trends](../generated/nba_home_court_advantage_season.png)

---

## Section 2 — What Creates Home Court Advantage
**Q2: What makes up HCA?**

- **Referee foul calls** (most consistent component):
  - 1984–94 reg season: ~**1.2 fewer fouls** on home (RESULTS −1.23); playoffs ~**1.6 fewer** (RESULTS −1.58).
  - Playoff universality: **45 of 47** officials (≥50 playoff games) home-favoring; holds under all checks.
- **Shooting advantage:** home shoot **>1 pp better FG%** (RESULTS 1984–94: +1.57 FG%, +1.56 eFG%); consistent across eras, both contexts.
- **Shot selection:** more attempts from close range, fewer mid-range → structural expected-scoring advantage. *RESULTS shot zones 1995–01 reg: Paint +1.28, Mid-Range −1.24.*
- **Rebounding & ball control:** ~**1.5 extra rebounds** (RESULTS REB diff +1.52) and ~**0.4 fewer turnovers** (TOV diff −0.38); together rival shooting.
- **Box-score accounting (mediation):** four categories = **~95% of advantage** (reg season); shooting biggest (**>40%**), then rebounding.
  - *RESULTS level decomp (reg):* eFG% **43%**, REB **25%**, Foul **14%**, TOV **13%**, unexplained 5%; category R²=0.615.
  - *RESULTS playoffs level:* eFG% 33%, Foul 17%, TOV 22%, REB 21%, unexplained 7% (~93% total).
  - **Coefficient stability across eras:** re-fitting the LPM within each of the six eras confirms the channel weights are nearly constant (eFG% +3.28 to +3.61 pp, Fouls −1.63 to −2.20 pp, TOV −3.19 to −3.57 pp, REB +1.57 to +1.70 pp). The pooled decomposition is not an artifact of blending very different periods. *RESULTS: coefficient stability table in MEDIATION section.*
- **Rest & altitude (Fig 4):**
  - Rest: home better-rested wins **62.8%** (+2.7 pp); away better-rested **57.6%** (−2.6). *RESULTS χ²(2)=79.22, p<0.001; +1.6 pp/day reg, +2.4 pp/day playoffs; no era change (LR p=0.474).*
  - Altitude (DEN/UTA): **+7.9 pp** reg season (RESULTS [+6.1,+9.7], p<0.001); **absent in playoffs** (−1.6, p=0.633) — team-quality confound.
  - Playoff rest confounded: controlling for quality, rest shrinks to nothing (RESULTS rest +1.6 pp p=0.113; quality_diff dominant).
**Figures:**

![Fig 3 — box-score differentials](../generated/nba_home_court_advantage_differentials.png)

![Fig 4 — rest & altitude (home win % by rest situation; altitude teams vs league)](../generated/nba_home_court_rest_altitude.png)

---

## Section 3 — What's Driving the Decline
**Q3: What drove the change?**

- **Shot selection changed in two ways (together ~21% of decline, both feeding the shooting line):**
  - **First: shot zone convergence (reg season).** Paint gap **~1.3 → 0.2 pp**. *RESULTS Paint trend −0.041***/yr reg.* Playoffs: narrowed late 2010s then rebounded; NOT statistically established (playoff Paint trend −0.030, ns) → reg-season story.
  - **Second: the three-point revolution.**
  - Tracks decline over four decades in lockstep. 7% threes (1980s, 65% wins) → 40% (today, 55% wins).
  - **Marks (not fully causes) the second drop (§1):** 3PA share rose from ~¼ of shots to nearly 40% right after 2017 — the years home court slid below 56%. Timing coincidence is strong; the measured causal bite runs through the shooting channel (~1/5 of decline), with the broader perimeter shift also absorbing ~half of the foul and turnover channels (rebounding, the largest channel, stays independent of it). *RESULTS 3PA%: 23.8% (2005–17) → 37.5% (2018–22) → 40.5% (2023–26).*
  - *RESULTS reg season-level Pearson r = −0.902, p<0.001.* **BUT: both series I(1) and NOT cointegrated; detrended partial r = −0.526 (raw r collapses ~40% once shared drift is removed); Granger test shows 3PA rate does NOT temporally lead HCA in either direction. Season-level correlation is largely a parallel-trend artifact — within-era game-level test is the reliable evidence.**
  - Within-era effect: ~**2 fewer home wins/100 per 10-pp rise** in 3PA. *RESULTS game-level −2.64 pp/10pp; within-era −2.27 pp, p<0.001.* This survives as the substantive finding.
  - **No temporal lead (Granger):** the annual rise in threes doesn't lead the HCA decline by a year, nor vice versa; both shift within the same season. *RESULTS: 3PA→HCA lag-1 F=1.49 p=0.23; lag-2 F=1.37 p=0.27; reverse also ns.* Consistent with both being downstream of the same strategic shift. (Note: folded into the 3PA narrative in FINDINGS, not a separate paragraph.)
  - Playoffs: directional but weaker within-era signal (r=−0.499; within-era p=0.027) — team quality dominates.
- **Rebounding (the glass), biggest driver, now explained:**
  - Home rebounding advantage shrunk 40 yrs, NOT a 3-point byproduct.
  - *RESULTS 3PA control (Fig 10):* eFG% **210%** absorbed → shooting decline not only disappears but reverses under 3PA control; net of 3PA, home shooting edge was actually improving; REB only **8%** absorbed (survives, p<0.001); TOV **54%** absorbed (~half independent); Foul 51%. Playoffs noisy — only REB survives.
  - **Died on the OFFENSIVE glass.** *RESULTS rebounding decomp (reg):* OREB diff +0.61 → **−0.05** (goes negative); DREB diff +1.64 → +0.59 (only softens); REB diff +2.24 → +0.54. Trends/yr all negative, all p<0.001 (OREB −0.018, DREB −0.027, REB −0.044).
  - **Direction of convergence:** home OREB rate fell **34% → 26%** (−8 pp); away OREB rate fell **31% → 26%** (−5 pp). The gap closed because home teams retreated faster, not because away teams improved. (Chart left panel now shows home vs. away OREB rates directly.)
  - **Pace-free share advantage** (home share of available boards − away) still collapses ~10×: **+2.14pp → +0.21pp** (trend −0.052/yr, p<0.001). → not a pace/volume artifact.
  - **Cause = league-wide retreat from O-rebounding:** league OREB rate 33% → 26%; home share advantage declined alongside. **Cointegration check: both series I(1) and NOT cointegrated — the r=+0.82 is likely spurious (parallel long-run trends).** The reliable evidence for the rebounding fade's independence is the 3PA control (only 8% absorbed), not the season-level correlation.
  - Playoffs: share advantage **+2.74pp → +0.70pp** (trend −0.046/yr, p<0.01). 3PA-control absorption is unstable in playoffs (−42%, noisy small-N) → can't confirm independence the way RS does; read as consistent with RS, not proven.
  - **Player-tracking (last decade) fits:** no measurable home box-out advantage today (mean −0.00/gm, p=0.78); OREB-conversion advantage still shrinking (+0.71 pp mean, −0.086/yr, **p=0.024**); 2nd-chance-points advantage no significant trend (+0.29 mean, ns, p=0.304). *RESULTS: PLAYER-TRACKING REBOUNDING MECHANISM.* Full treatment moved to §6; brief mention kept here to close the rebounding argument.
- **Referee foul bias narrowed:**
  - Reg season **1.2 → ~0.25 fouls/game** (≈**80% reduction**); playoffs **1.6 → 0.7**. *RESULTS reg trend +0.022***/yr; 2023–26 = −0.25.*
  - Generational shift: most home-favoring refs (Garretson, Crawford, Rush) worked 1990s–2000s; distribution compressed (Fig 6).
- **Adding it up (trend decomposition):**
  - Reg season: four categories = **~96% of decline**; all four trends p<0.001. *RESULTS:* REB **30%**, TOV **27%**, eFG% **21%**, Foul **18%**; unmediated 4%. → overlooked pair (REB+TOV) carries >half.
  - Playoffs: overall trend 4× less precisely measured than RS (CI [−0.359, −0.091] vs [−0.280, −0.209]); categories = **only ~67%**; ~⅓ unexplained. *RESULTS:* REB 28%, Foul 18%, eFG% 12%, TOV 10%; unmediated 33%. Only Foul & REB trends significant (p<0.05); eFG% & TOV trends not distinguishable from noise → split is suggestive/consistent-with-RS, not independently established. Strongest playoff evidence is the venue/seeding control (§5), not the box score. Unexplained third has no box-score column to point at.
- **3PA reaches ~half the decline, but not the whole:** within-season link is genuine (−2.27 pp/10pp, p<0.001). It registers most directly as the shooting channel (~21% of decline; eFG% 210% absorbed under the 3PA control, i.e. fully + reverses), and also absorbs ~half of the foul (51%) and turnover (54%) channels — so the perimeter shift touches close to half the decline overall. Rebounding (the largest single channel, 30%) is the part it does NOT explain (only 8% absorbed). (Point now made within the 3PA narrative in FINDINGS, not as a separate closing paragraph.)
- **Shape of the decline: continuous drift, not shocks.** The structural-break test marks a slope change ~1999 (decline ran steeper through the late 1990s, eased after) but no level jump; CUSUM finds no structural instability across 40 seasons. Granger: 3PA does not temporally lead HCA; both co-move, pulled by the same underlying force.
- **Bayesian change-point model:** strongly favors ≥1 slope change over a straight line (BF=18.0 for k=1 vs k=0). One-vs-two breaks is close: k=2 P=66.3% vs k=1 P=31.9%, only a ~2:1 BF, too thin to call. Break years are not datable: even the best single break has a bootstrap range ~1993–2002, so nominal MAPs (k=1: 1999, 95% HPD 1992–2003; k=2: 1992 & 2003) mark a broad late-1990s–early-2000s window, not specific seasons; the k=2 locations carry no reported uncertainty interval. Posterior-weighted k=1 slopes **−0.584 → −0.255 pp/yr**. Consistent with QLR (best single break ~1999) and CUSUM (no level instability); each test asks a different question. *RESULTS: BAYESIAN CHANGE-POINT MODEL.*
- Data most consistent with information diffusion: as analytical strategies spread uniformly across all 30 teams, strategies converged toward the same optima regardless of venue, and the home familiarity advantage compressed alongside them.
**Figures:**

![Fig 5 — mediation shares (leads the section as the roadmap)](../generated/nba_home_court_mediation.png)

![Fig 6 — shot zones](../generated/nba_home_court_shot_zones.png)

![Fig 7 — 3PA vs HCA](../generated/nba_home_court_3pa.png)

![Fig 8 — rebounding decomposition (home vs away OREB rates converging; share advantage vs league OREB rate)](../generated/nba_home_court_rebounding.png)

![Fig 9 — referee era distribution](../generated/nba_home_court_referee_era.png)

![Fig 10 — 3PA-control channel test (which fades survive holding 3-point volume constant)](../generated/nba_home_court_3pa_control.png)

![Fig X — Bayesian change-point model (k=0/1/2 fitted lines; posterior distribution over break year for k=1)](../generated/nba_home_court_bayesian_changepoint.png)

---

## Section 4 — What Didn't Drive the Change
**Q3 corollary: ruled-out factors**

- **Rule changes:** only the **1994–95 season** left a mark (~**−2.6 pp** discrete step; RESULTS era:1995–01 −0.108 log-odds, p=0.010; LR χ²(5)=20.68, p<0.001). Two changes that season — hand-check crackdown (more consistent with channel data) + shortened 3-pt line (1994–97) — confounded at season level; channel event study shows foul diff responded immediately and significantly (level p=0.007) while shooting did not (p=0.327), pointing toward hand-checking. The step was immediate but the multi-year adjustment continued through the late 1990s. **Break-point test:** formal QLR supremum-Chow test locates the *slope* shift in the **late 1990s** (sup F=10.22, p<5% by Andrews 1993 critical values), slope going from −0.65 pp/yr before to −0.26 pp/yr after — read as the 1994–95 adjustment settling in, though the ~4-yr lag makes the link an inference. Playoffs show no significant break (sup F=3.23, n.s.) — steady drift. All other boundaries passed through; playoffs neither change registers (LR p=0.815).
- **Travel & time zones:**
  - Reg: ~**0.07 pp/100 mi** (RESULTS −0.07 pp/100mi, p=0.010), tiny & inconsistent direction; playoffs no effect (p=0.888).
  - Time zones flat both contexts (reg −0.4 pp p=0.086; playoffs +1.0 pp p=0.330).
- **Back-to-backs / load management (Fig 12):** visitor B2B rate fell **35.0% → 18.8%** (1984–94 → 2023–26), confirming the blog's premise. But shift-share of the −9.29 pp RS decline: frequency component only **−0.71 pp (~8%)**; win-rate component −8.59 pp (~92%). Per-situation home win%: visitor-B2B-only 64.7% vs neither 59.1% (narrow gap). RS only (B2Bs rare in playoffs). Scheduling nudged HCA, didn't drive it.
- **Pace of play:** moves independently of HCA. *RESULTS reg season-level r=+0.241 (p=0.120, wrong direction); playoffs r=−0.142 (ns).*

![Fig 11 — back-to-back / load management (visitor B2B rate by era; shift-share of decline)](../generated/nba_home_court_back_to_back.png)

![Fig 12 — pace vs HCA](../generated/nba_home_court_pace.png)

- **Home vs. away 3PA differential:** home and away teams attempt threes at nearly identical rates; the trend moves the wrong direction — home teams now take *more* threes than visitors (+0.44 pp in 2023–26 vs. −0.35 pp in 1984–94, trend +0.018***/yr). Not the mechanism behind the decline. *RESULTS 3PA rate diff trend +0.018***/yr.*
- **Competitive balance:** can't explain the long-run decline. Parity is mean-reverting (I(0) stationary) while HCA has declined steadily for 40 years — structurally, they can't be linked as cause and effect. Raw correlation near zero (RESULTS r=−0.092, p=0.556); era pattern inconsistent. Small wrinkle: detrended association emerges (first-diff r=−0.330 p=0.033; residual r=−0.345 p=0.023) but modest, small sample — means year-to-year parity fluctuations weakly track HCA fluctuations, not that parity drives the decline.

![Fig 13 — parity vs HCA](../generated/nba_home_court_parity.png)

- **Crowd size:** arenas near capacity throughout (~17k→18k+), records set as HCA hit lows. *RESULTS r=+0.248 (p=0.212); detrended ns.* Playoffs ~guaranteed sellouts yet eroded too.

![Fig 14 — attendance & empty-arena](../generated/nba_home_court_attendance.png)
- **Empty-arena experiment (2020–21):** empty **51.0%** vs. fans present **58.5%** (RESULTS n=573 vs 591). Presence > count (dose-response +0.51 pp/1000 fans, p=0.184 ns). Vanished when arenas refilled → a switch, not a slow dial.
- **All together:** full model — era effect ≈ half of predictive power; situational factors ≈ other half. *RESULTS Shapley: Era 53%, Rest 17.9%, Altitude 23.7%, TZ 1.4%, COVID 4.5%.* Net era decline **−9.0 pp** (1984–94 → 2023–26) after all controls.
- **Pre/post-2014 test:** rest/altitude/TZ effects statistically unchanged across line; baseline home advantage dropped **~4.7 pp** anyway (RESULTS post2014 level shift −0.196, −4.7 pp p<0.001; rest & TZ interactions ns, altitude weakened p=0.026). Situational factors held still while the baseline dropped.

---

## Section 5 — The Playoff Picture

- **Home court > everything else:** strongest predictor of playoff outcome.
  - *RESULTS by game:* G1 **69.4%**, G2 **71.9%**, G3 **55.0%**, G4 **55.3%**, G5 **74.5%**, G6 **55.5%**, G7 **63.8%**. χ²(6)=84.54, p<0.001.
  - No evidence road teams adapt as series deepens; home-away split explains it entirely.

![Fig 15 — playoff win % by game number](../generated/nba_home_court_series_breakdown.png)

![Fig 16 — playoff seeding decomposition (decline survives quality control; weaker host still wins)](../generated/nba_home_court_playoff_quality.png)
- **Decline is real weakening, not weaker seeds (Fig 16):**
  - *RESULTS:* year trend retained **102%** after quality control; quality absorbs −2%.
  - Lower-seed-at-home (G3+G4): still wins **51.5%** (n=827) — pure venue effect.
  - Seed-quality gap did trend slightly (−0.00026/yr, p<0.001) but doesn't explain HCA decline.
- **2014 format change didn't cause drop:** raw −6.8 pp from 2003–13 → 2014–26 (z=3.10, p=0.002), but trend-controlled dummy ns (p=0.298); LR χ²(3)=4.68, p=0.197. Format table (4 periods).

![Fig 17 — win % by format period](../generated/nba_home_court_advantage_format_bars.png)

---

## Section 6 — Other Findings

- **Referee differences real but overstated:** 45/47 home-favoring; spread ~1 foul/game between most-leaning (Garretson −1.734 shrunken, Crawford, Rush) and most even-handed (Brothers, Tiven, Forte). **~60% of raw spread = sampling noise** (RESULTS true between-SD 0.407 vs observed 0.645). Measures tendencies, not game-fixing.
- **Denver & Utah best home court — altitude the likely reason:** Nuggets **+26.8 pp**, Jazz **+25.7 pp** shrunken (league mean +20.0). ~70% of franchise variation is real (true SD ≈4.1 pp). Altitude piece ≈8 of those points. (n=2 high-altitude teams — elevation can't be fully separated from other franchise-specific factors.)

- **Referee differences real but detailed (Fig 18):** top/bottom 15 officials ranked by career mean shrunken home foul differential — Garretson, Crawford, Rush most home-favoring; Brothers, Tiven, Forte most even-handed.

![Fig 18 — referee rankings](../generated/nba_home_court_referee_rankings.png)

![Fig 19 — franchise HCA](../generated/nba_home_court_team_hca.png)
- **Playoff franchise differences = illusion:** true between-franchise SD ≈ **0.0** (100% noise); all collapse to league mean +26.9 pp. Apparent postseason home-court strength reflects being a good team that plays more home games.
- **Home court worth more in playoffs:** reg **~20 pp** vs. playoffs **~27 pp** → **+7 pp postseason premium** (RESULTS +7.2 pp, SD 7.4). Reg/playoff consistency positive but weak (raw r=+0.362, p=0.042).
- **Player-tracking caught the final chapter of the rebounding fade (Fig 20):** OREB-conversion advantage fell from ~1.5 pp (mid-2010s) to below zero (2025–26); box-out advantage essentially zero throughout. Cameras confirmed a fade already nearly complete before 2013–14. *RESULTS: OREB conversion p=0.024*, box-out p=0.775.*

![Fig 20 — player-tracking rebounding](../generated/nba_home_court_rebounding_tracking.png)
- **Margins polarizing — blowouts getting bigger:** home wins bigger, home losses worse, even as home teams win less.
  - Not just a composition effect — confirmed by unconditional quantile regression.
  - *RESULTS reg season:* Q10 **−0.167 pts/yr**, Q90 **+0.050 pts/yr**; IQR widening **+0.217 pts/yr**.
  - *RESULTS playoffs:* Q10 −0.104 (ns), Q90 +0.222 pt/yr; IQR widening **+0.326 pts/yr** — playoff spread driven mainly by big home wins growing (Home wins trend +0.149***/yr).
  - ~0.2–0.3 pts/yr widening in both contexts. Era of close games → era of blowouts.
- **Team strategy implications:** Rebounding is the most tractable remaining home-court lever (30% of decline; only 8% absorbed by 3PA control; tracking data shows conversion edge still declining). Turnover channel has independent component (~46% not 3PA-driven); pressure defense at home targets it. Crowd presence = switch (even a few thousand restores full effect; size above that adds little). Away teams: 3PA has already largely equalized the shooting channel. Offensive glass is where road disadvantage persists and no current trend is closing it. Rest: away team entering better-rested = ~3 pp drop in home win rate, available from scheduling.

![Fig 21 — margin trends](../generated/nba_home_court_margin.png)

---

## Section 7 — Summary
- Recap: HCA nearly halved over 40 yrs; reg **65% → ~55%**, playoffs **~68% → 58%**.
- Shape: slow four-decade erosion + two sharper drops (slope steepening, not level jumps) — 1994–95 rule jolt (most likely hand-checking, confounded with the shortened 3-pt line; multi-year adjustment through late 1990s, outside the categories) and post-2017 perimeter shift (inside the categories — three-point surge on the shooting line, parallel offensive-glass retreat on the rebounding line). Bayesian model: ≥1 break strongly favored (BF=18 vs no break); one-vs-two breaks close (k=2 P=66% vs k=1 P=32%, ~2:1) and break years not datable to better than a ~decade. QLR and CUSUM consistent.
- Three main drivers + the biggest driver of all (**together ~96% of RS decline**): (1) fairer refs — 1.2 → ~0.25 fouls/game RS, 1.6 → 0.7 playoffs; 45/47 officials home-favoring (largest single change), (2) shot selection changed in two ways: away teams closed the paint gap (1.3 → 0.2 pp) AND the league-wide 3PA rise compressed home court through the shooting line (within-era game-level effect is real; season-level r=−0.902 is co-trending; no Granger temporal lead), (3) rebounding advantage slipping independently (3PA control shows independence; season-level r=0.82 with OREB rate is parallel-trend correlation, not cointegration).
- Ruled out: rule changes (except 1994–95), travel, time zones, pace, crowd size, format. Competitive balance can't explain the long-run decline (parity is mean-reverting, HCA is a 40-year trend), though year-to-year parity fluctuations show a weak association; treated as exploratory. Fewer back-to-backs explain only ~8% of the RS decline. Crowd presence = on/off switch (2020–21 51% vs 58.5%; isolates presence, not noise itself), not a slow fade.
- Playoffs follow reg season with **nearly a two-decade delay**; trend direction not in doubt but 4× less precisely measured than RS (CI [−0.359, −0.091]); accelerated since 2018; genuine erosion (weaker host still winning less). Game-by-game structure stark: G1 69%, G2 72%, G5 74.5%, G7 64%.
- Franchise notes: Denver & Utah strongest reg-season home courts (~27 & ~26 pts above own road rate), altitude the likely reason (n=2, confounded with franchise) — washes out in playoffs (franchise spread indistinguishable from zero). Home court worth **~7 pts more in playoffs** than reg season.
- Blowouts getting bigger as HCA falls (IQR widening ~0.2–0.3 pts/yr in both contexts).

---

## Appendix B — Independent Corroboration (Sparkle Technologies Blog)
- Blog: Sparkle Technologies, same question, independent pipeline. Main agreements: overall decline, foul story, travel/pace irrelevance, altitude (Denver +27 pp, Utah +26 pp — within 0.1 pp of ours).
- **Key disagreement — cause:** blog crowns three-point revolution the primary driver (raw r=−0.88 season-level). We find ~40% of that correlation is parallel-trend artifact (detrended partial r=−0.53; Granger test: no temporal lead). 3PA effect is real within seasons (−2.27 pp/10pp). It registers most directly as the shooting channel (~21% of the decline), and counting its share of the foul and turnover channels (~half of each) reaches close to half the decline overall — still short of the whole story. Rebounding (30%, the largest channel and independent of the 3PA shift) is the piece the blog never measures.
- **Mid-1990s drop:** blog attributes to shortened 3-pt line (1994–97); we attribute to hand-checking crackdown. Events overlap at season level. Channel event study gives leverage: foul diff immediate and significant at 1994-95 (p=0.007); shooting channel not significant (p=0.327). Hand-checking is the more consistent explanation; the two cannot be fully separated.
- **Empty-arena numbers:** blog's "empty arena" figure (54.4%) = 2020–21 season average blending zero-fan and partial-crowd games. Our split: empty 51.0% vs. any fans 58.5%. No disagreement on conclusion (presence = switch); blog averaged over the distinction.
- **Back-to-backs:** blog claimed 15–20% of decline; we tested directly — frequency premise confirmed (35.0% → 18.8%); magnitude is ~8%, not 15–20% (shift-share: frequency component −0.71 pp; within-situation component −8.59 pp).
- **What the blog missed:** rebounding channel (absent entirely from blog's box-score account), turnover-edge erosion, shot-zone convergence, formal playoff seeding control (G3–G4 weaker-host still 51.5%), ruling-out tests for format/balance/crowd.
