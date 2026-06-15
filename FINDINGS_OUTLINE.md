# Detailed Outline — FINDINGS.md

## Introduction (Intro / TL;DR)
- **Three guiding questions:** (1) Has HCA really changed? (2) What makes home court an advantage? (3) What's driving the decline — and what isn't?
- **Headline answers:**
  - Change is real & one-directional: regular-season home win rate **~65% → 55%**; playoffs **~68% → 58%**. Shape = a slow gradual erosion + **two sharper one-time drops** layered on top.
  - HCA is built from: referee foul calls, shooting/shot-selection edge, plus smaller rest & altitude boosts.
  - Decline drivers: neutral whistle, converging shot selection, three-point revolution draining variance.
- **Ruled-out suspects:** rule changes, travel, time zones, pace, competitive balance, crowd size, 2014 playoff format.
- **Scope:** regular season vs. playoffs tracked separately (same direction, different timeline); ~52,000 games; tables in RESULTS.md.

---

## Section 1 — The 40-Year Decline
**Q1: Has it changed?**

- **Core stat:** Home win rate ~65 → ~55 per 100; ~quarter-point/year.
  - *RESULTS:* Reg season GLM **−0.244 pp/yr** [−0.280, −0.209], p<0.001, total ≈ **−10.3 pp**; OLS −0.250 pp/yr, R²=0.745.
  - *RESULTS:* Playoffs GLM **−0.225 pp/yr** [−0.359, −0.091], p<0.001, total ≈ **−9.5 pp**; OLS −0.216 pp/yr, R²=0.195; peaked ~68% → 58% today (~9 pt drop, noisier).
- **Two speeds — gradual drift vs. sharp drops** (key framing for the whole report):
  - **Gradual:** a continuous ~quarter-point/year erosion underneath everything, from the §3 box-score categories grinding down.
  - **Sharp — two drops** layered on top, each a moment one force shoved the same trend harder:
    - First drop: sharp mid-1990s fall ~65% → 60% (steepest move). Cause = **1994–95 rule shock** (§4) — most likely the hand-check crackdown, but confounded with the simultaneous shortened 3-pt line (1994–97); season-level data can't separate them. Discrete event, handled in §4. *RESULTS era slope 1984–94: −0.522 pp/yr, p<0.001.*
    - Flat for ~two decades.
    - Second drop: after 2017, below 56%. Cause = **three-point surge** (§3) hitting full stride — registers *inside* the box-score categories (on the shooting line). *RESULTS era slopes: 2018–22 −1.183 pp/yr (p=0.009), 2023–26 −0.773 pp/yr (p=0.223).*
  - The drops are not extra causes — they're the same box-score categories' story told at faster speed. Asymmetry (first-drop cause outside the categories in §4, second-drop cause inside them in §3) is why each is explained in a different section.
  - Playoffs lagged: steady ~64% through 2017 across 3 eras, joined slide after 2018 → 61% → 58%.
- **Era table** (6 eras, 1984–94 through 2023–26, defined by major rule changes — used as calendar only; causation deferred to §4).
**Figures:**

![Fig 1 — season trends](nba_home_court_advantage_season.png)

![Fig 2 — era bars](nba_home_court_advantage_era_bars.png)

---

## Section 2 — What Creates Home Court Advantage
**Q2: What makes up HCA?**

- **Referee foul calls** (most consistent component):
  - 1984–94 reg season: ~**1.2 fewer fouls** on home (RESULTS −1.23); playoffs ~**1.6 fewer** (RESULTS −1.58).
  - Playoff universality: **45 of 47** officials (≥50 playoff games) home-favoring; holds under all checks.
- **Shooting edge:** home shoot **>1 pp better FG%** (RESULTS 1984–94: +1.57 FG%, +1.56 eFG%); consistent across eras, both contexts.
- **Shot selection:** more attempts from close range, fewer mid-range → structural expected-scoring edge. *RESULTS shot zones 1995–01 reg: Paint +1.28, Mid-Range −1.24.*
- **Rebounding & ball control:** ~**1.5 extra rebounds** (RESULTS REB diff +1.52) and ~**0.3 fewer turnovers** (TOV diff −0.38); together rival shooting.
- **Box-score accounting (mediation):** four categories = **~95% of edge** (reg season); shooting biggest (**>40%**), then rebounding.
  - *RESULTS level decomp (reg):* eFG% **43%**, REB **25%**, Foul **14%**, TOV **13%**, unexplained 5%; category R²=0.615.
  - *RESULTS playoffs level:* eFG% 33%, Foul 17%, TOV 22%, REB 21%, unexplained 7% (~93% total).
- **Rest & altitude:**
  - Rest: home better-rested wins **62.8%** (+2.7 pp); away better-rested **57.6%** (−2.6). *RESULTS χ²(2)=79.22, p<0.001; +1.6 pp/day reg, +2.4 pp/day playoffs; no era change (LR p=0.474).*
  - Altitude (DEN/UTA): **+7.9 pp** reg season (RESULTS [+6.1,+9.7], p<0.001); **absent in playoffs** (−1.6, p=0.633) — team-quality confound.
  - Playoff rest confounded: controlling for quality, rest shrinks to nothing (RESULTS rest +1.6 pp p=0.113; quality_diff dominant).
**Figure:**

![Fig 3 — box-score differentials](nba_home_court_advantage_differentials.png)

---

## Section 3 — What's Driving the Decline
**Q3: What drove the change?**

- **Referee foul bias narrowed sharply:**
  - Reg season **1.2 → ~0.25 fouls/game** (≈**80% reduction**); playoffs **1.6 → 0.7**. *RESULTS reg trend +0.022***/yr; 2023–26 = −0.25.*
  - Generational shift: most home-favoring refs (Garretson, Crawford, Rush) worked 1990s–2000s; distribution compressed (Fig 5).
- **Shot zone advantage evaporated (reg season):**
  - Paint gap **~1.3 → 0.2 pp**. *RESULTS Paint trend −0.041***/yr reg.*
  - Playoffs: narrowed late 2010s then rebounded; downward drift NOT statistically established (playoff Paint trend −0.030, ns) → convergence is a reg-season phenomenon.
- **Three-point revolution:**
  - Tracks decline almost perfectly. 7% threes (1980s, 65% wins) → 40% (today, 55% wins).
  - **Explains the second drop (§1):** 3PA share leapt from ~¼ of shots to ~half right after 2017 — the years home court slid below 56%. *RESULTS 3PA%: 23.8% (2005–17) → 37.5% (2018–22) → 40.5% (2023–26).*
  - *RESULTS reg season-level Pearson r = −0.902, p<0.001.*
  - Within-era effect: ~**2 fewer home wins/100 per 10-pp rise** in 3PA. *RESULTS game-level −2.64 pp/10pp; within-era −2.27 pp, p<0.001.*
  - Playoffs: directional but weaker within-era signal (r=−0.499; within-era p=0.027) — team quality dominates.
- **Quieter fourth strand — rebounding (the glass), now explained:**
  - Home rebounding edge shrunk 40 yrs, NOT a 3-point byproduct.
  - *RESULTS 3PA control:* eFG% trend fully absorbed (**210%** absorbed → shooting fade IS the 3-pt story); REB only **8%** absorbed (survives); TOV **54%** absorbed (~half independent).
  - **Died on the OFFENSIVE glass.** *RESULTS rebounding decomp (reg):* OREB diff +0.61 → **−0.05** (goes negative); DREB diff +1.64 → +0.59 (only softens); REB diff +2.24 → +0.54. Trends/yr all negative, all p<0.001 (OREB −0.018, DREB −0.027, REB −0.044).
  - **Pace-free share edge** (home share of available boards − away) still collapses ~10×: **+2.14pp → +0.21pp** (trend −0.052/yr, p<0.001). → not a pace/volume artifact.
  - **Cause = league-wide retreat from O-rebounding:** league OREB rate 33% → 26%; share edge vs league OREB rate **r = +0.82, p<0.001 (N=43)**. Effort-driven O-boards coached out (transition defense).
  - Playoffs: share edge **+2.74pp → +0.70pp** (trend −0.046/yr, p<0.01); REB survives 3PA control (−42%/strengthens).
  - **Player-tracking (last decade) fits:** no measurable home box-out edge today; OREB-conversion edge still shrinking. (One sentence in §3; not a RESULTS section — short tracking-era window corroborates the mechanism only. Code/fetchers retained but unwired.)
- **Adding it up (trend decomposition):**
  - Reg season: four categories = **~96% of decline**. *RESULTS:* REB **30%**, TOV **27%**, eFG% **21%**, Foul **18%**; unmediated 4%. → quiet pair (REB+TOV) carries >half.
  - Playoffs: categories = **only ~67%**; ~⅓ unexplained. *RESULTS:* REB 28%, Foul 18%, eFG% 12%, TOV 10%; unmediated 33%. Likely crowd-effect compression post-2018.
- **Why the 3-point revolution is NOT the main driver:** near-perfect raw 3PA↔HCA correlation is partly shared 40-yr trend; within-season effect is real but modest and lands almost entirely on the shooting line. Shooting = only ~21% of decline; REB+TOV (the bigger half) barely move under the 3PA control. Threes drove one channel (shooting), not the whole decline. Playoffs: within-game 3-pt signal fainter, ⅓ of decline off the box score entirely.
**Figures:**

![Fig 4 — referee bias](nba_home_court_referee.png)

![Fig 5 — shot zones](nba_home_court_shot_zones.png)

![Fig 6 — 3PA vs HCA](nba_home_court_3pa.png)

![Fig 7 — rebounding decomposition (OREB/DREB, share edge, league OREB corr)](nba_home_court_rebounding.png)

![Fig 8 — mediation shares](nba_home_court_mediation.png)

---

## Section 4 — What Didn't Drive the Change
**Q3 corollary: ruled-out factors**

- **Rule changes:** only the **1994–95 season** left a mark (~**−2.6 pp** one-time drop; RESULTS era:1995–01 −0.108 log-odds, p=0.010; LR χ²(5)=20.68, p<0.001). Two changes that season — hand-check crackdown (likelier culprit) + shortened 3-pt line (1994–97) — confounded, can't separate at season level. All other boundaries passed through. Playoffs: neither change registers (LR p=0.815) — pure smooth drift.
- **Travel & time zones:**
  - Reg: ~**0.07 pp/100 mi** (RESULTS −0.07 pp/100mi, p=0.010), tiny & inconsistent direction; playoffs no effect (p=0.888).
  - Time zones flat both contexts (reg −0.4 pp p=0.086; playoffs +1.0 pp p=0.330).
- **Back-to-backs / load management:** visitor B2B rate fell **35.0% → 18.8%** (1984–94 → 2023–26), confirming the blog's premise. But shift-share of the −9.29 pp RS decline: frequency component only **−0.71 pp (~8%)**; win-rate component −8.59 pp (~92%). Per-situation home win%: visitor-B2B-only 64.7% vs neither 59.1% (narrow gap). RS only (B2Bs rare in playoffs). Scheduling nudged HCA, didn't drive it.
- **Pace of play:** moves independently of HCA. *RESULTS reg season-level r=+0.241 (p=0.120, wrong direction); playoffs r=−0.142 (ns).*

![Fig 9 — pace vs HCA](nba_home_court_pace.png)

- **Competitive balance:** raw correlation near zero (RESULTS r=−0.092, p=0.556); era pattern inconsistent. Small wrinkle: detrended association emerges (first-diff r=−0.330 p=0.033; residual r=−0.345 p=0.023) but modest, can't explain magnitude.

![Fig 10 — parity vs HCA](nba_home_court_parity.png)

- **Crowd size:** arenas near capacity throughout (~17k→18k+), records set as HCA hit lows. *RESULTS r=+0.248 (p=0.212); detrended ns.* Playoffs ~guaranteed sellouts yet eroded too.

![Fig 11 — attendance & empty-arena](nba_home_court_attendance.png)
- **Empty-arena experiment (2020–21):** empty **51.0%** vs. fans present **58.5%** (RESULTS n=573 vs 591). Presence > count (dose-response +0.51 pp/1000 fans, p=0.184 ns). Vanished when arenas refilled → a switch, not a slow dial.
- **All together:** full model — era effect ≈ half of predictive power; situational factors ≈ other half. *RESULTS Shapley: Era 53%, Rest 17.9%, Altitude 23.7%, TZ 1.4%, COVID 4.5%.* Net era decline **−9.0 pp** (1984–94 → 2023–26) after all controls.
- **Pre/post-2014 test:** rest/altitude/TZ effects statistically unchanged across line; baseline home edge dropped **~4.7 pp** anyway (RESULTS post2014 level shift −0.196, −4.7 pp p<0.001; rest & TZ interactions ns, altitude weakened p=0.026). Situational factors held still while floor fell.

---

## Section 5 — The Playoff Picture

- **Home court > everything else:** strongest predictor of playoff outcome.
  - *RESULTS by game:* G1 **69.4%**, G2 **71.9%**, G3 **55.0%**, G4 **55.3%**, G5 **74.5%**, G6 **55.5%**, G7 **63.8%**. χ²(6)=84.54, p<0.001.
  - No evidence road teams adapt as series deepens; home-away split explains it entirely.

![Fig 12 — playoff win % by game number](nba_home_court_series_breakdown.png)
- **Decline is real weakening, not weaker seeds:**
  - *RESULTS:* year trend retained **102%** after quality control; quality absorbs −2%.
  - Lower-seed-at-home (G3+G4): still wins **51.5%** (n=827) — pure venue effect.
  - Seed-quality gap did trend slightly (−0.00026/yr, p<0.001) but doesn't explain HCA decline.
- **2014 format change didn't cause drop:** raw −6.8 pp from 2003–13 → 2014–26 (z=3.10, p=0.002), but trend-controlled dummy ns (p=0.298); LR χ²(3)=4.68, p=0.197. Format table (4 periods).

![Fig 13 — win % by format period](nba_home_court_advantage_format_bars.png)

---

## Section 6 — Other Findings

- **Referee differences real but overstated:** 45/47 home-favoring; spread ~1 foul/game between most-leaning (Garretson −1.734 shrunken, Crawford, Rush) and most even-handed (Brothers, Tiven, Forte). **~60% of raw spread = sampling noise** (RESULTS true between-SD 0.407 vs observed 0.645). Measures tendencies, not game-fixing.
- **Denver & Utah best home court — altitude is why:** Nuggets **+26.8 pp**, Jazz **+25.7 pp** shrunken (league mean +20.0). ~70% of franchise variation is real (true SD ≈4.1 pp). Altitude piece ≈8 of those points.

![Fig 14 — franchise HCA](nba_home_court_team_hca.png)
- **Playoff franchise differences = illusion:** true between-franchise SD ≈ **0.0** (100% noise); all collapse to league mean +26.9 pp. Fortress reputation = being a good team that plays more home games.
- **Home court worth more in playoffs:** reg **~20 pp** vs. playoffs **~27 pp** → **+7 pp postseason premium** (RESULTS +7.2 pp, SD 7.4). Reg/playoff consistency positive but weak (raw r=+0.362, p=0.042).
- **Margins polarizing — blowouts getting bigger:** home wins bigger, home losses worse, even as home teams win less.
  - Not just a composition effect — confirmed by unconditional quantile regression.
  - *RESULTS reg season:* Q10 **−0.167 pts/yr**, Q90 **+0.050 pts/yr**; IQR widening **+0.217 pts/yr**.
  - *RESULTS playoffs:* Q10 −0.104 (ns), Q90 +0.222 pt/yr; IQR widening **+0.326 pts/yr** — playoff spread driven mainly by big home wins growing (Home wins trend +0.149***/yr).
  - ~0.2–0.3 pts/yr widening in both contexts. Era of close games → era of blowouts.

![Fig 15 — margin trends](nba_home_court_margin.png)

---

## Section 7 — Summary
- Recap: HCA nearly halved over 40 yrs; reg **65% → 55.6%**, playoffs **~68% → 58%**.
- Shape: slow four-decade erosion + two sharper drops — 1994–95 rule jolt (most likely hand-checking, confounded with the shortened 3-pt line; discrete, outside the categories) and post-2017 three-point surge (inside the categories, shooting line).
- Three main drivers + quiet fourth: (1) fairer refs (largest single change), (2) converged shot selection, (3) three-point variance, (4) rebounding edge slipping independently — specifically the OFFENSIVE-glass edge dying (OREB diff → negative) in lockstep with the league-wide retreat from O-rebounding (r=0.82).
- Ruled out: rule changes (except 1994–95), travel, time zones, pace, competitive balance, crowd size, format. Fewer back-to-backs explain only ~8% of the RS decline. Crowd noise = on/off switch (2020–21 51% vs 58.5%), not a slow fade.
- Playoffs follow reg season with ~decade lag; accelerated since 2018; genuine erosion (weaker host still winning less); no sign of bottoming out.
