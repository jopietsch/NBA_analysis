# Detailed Outline — FINDINGS.md

## Introduction (Intro / TL;DR)
- **Three guiding questions:** (1) Has HCA really changed? (2) What makes home court an advantage? (3) What's driving the decline — and what isn't?
- **Headline answers:**
  - Change is real & steady: regular-season home win rate **~65% → 55%**; playoffs **~68% → 58%**.
  - HCA is built from: referee foul calls, shooting/shot-selection edge, plus smaller rest & altitude boosts.
  - Decline drivers: neutral whistle, converging shot selection, three-point revolution draining variance.
- **Ruled-out suspects:** rule changes, travel, time zones, pace, competitive balance, crowd size, 2014 playoff format.
- **Scope:** regular season vs. playoffs tracked separately (same direction, different timeline); ~51,000 games; tables in RESULTS.md.

---

## Section 1 — The 40-Year Decline
**Q1: Has it changed?**

- **Core stat:** Home win rate ~65 → ~55 per 100; ~quarter-point/year.
  - *RESULTS:* Reg season GLM **−0.245 pp/yr** [−0.282, −0.208], p<0.001, total ≈ **−10.0 pp**; OLS −0.251 pp/yr, R²=0.733.
  - *RESULTS:* Playoffs GLM **−0.209 pp/yr** [−0.348, −0.070], p=0.003, total ≈ **−8.6 pp**; peaked ~68% → 58% today (~9 pt drop, noisier).
- **Two waves of decline:**
  - First wave: sharp mid-1990s drop ~65% → 60% (steepest move). *RESULTS era slope 1984–94: −0.522 pp/yr, p<0.001.*
  - Flat for ~two decades.
  - Second wave: after 2017, below 56%. *RESULTS era slopes: 2018–22 −1.183 pp/yr (p=0.009), 2023–25 −1.802 pp/yr.*
  - Playoffs lagged: steady ~64% through 2017 across 3 eras, joined slide after 2018 → 61% → 58%.
- **Era table** (6 eras, 1984–94 through 2023–25, defined by major rule changes — used as calendar only; causation deferred to §4).
- **Counterintuitive finding — margins polarizing:** home wins bigger, home losses worse.
  - Not just composition effect — confirmed by unconditional quantile regression.
  - *RESULTS reg season:* Q10 **−0.154 pp/yr**, Q90 **+0.045 pp/yr**; IQR widening **+0.199 pts/yr**.
  - *RESULTS playoffs:* Q10 −0.055 (ns), Q90 +0.145 pt/yr; IQR widening **+0.200 pts/yr** — playoff spread driven mainly by big home wins growing (Home wins trend +0.152***/yr).
  - ~0.2 pts/yr widening in both contexts. Era of close games → era of blowouts.
**Figures:**

![Fig 1 — season trends](nba_home_court_advantage_season.png)

![Fig 2 — era bars](nba_home_court_advantage_era_bars.png)

![Fig 3 — margin trends](nba_home_court_margin.png)

---

## Section 2 — What Creates Home Court Advantage
**Q2: What makes up HCA?**

- **Referee foul calls** (most consistent component):
  - 1984–94 reg season: ~**1.2 fewer fouls** on home (RESULTS −1.23); playoffs ~**1.6 fewer** (RESULTS −1.58).
  - Playoff universality: **41 of 42** officials (≥50 playoff games) home-favoring; holds under all checks.
- **Shooting edge:** home shoot **>1 pp better FG%** (RESULTS 1984–94: +1.57 FG%, +1.56 eFG%); consistent across eras, both contexts.
- **Shot selection:** more attempts from close range, fewer mid-range → structural expected-scoring edge. *RESULTS shot zones 1995–01 reg: Paint +1.28, Mid-Range −1.24.*
- **Rebounding & ball control:** ~**1.5 extra rebounds** (RESULTS REB diff +1.56) and ~**0.3 fewer turnovers** (TOV diff −0.38); together rival shooting.
- **Box-score accounting (mediation):** four channels = **~95% of edge** (reg season); shooting biggest (**>40%**), then rebounding.
  - *RESULTS level decomp (reg):* eFG% **43%**, REB **25%**, Foul **14%**, TOV **13%**, unexplained 5%; channel R²=0.615.
  - *RESULTS playoffs level:* eFG% 33%, Foul 17%, TOV 22%, REB 22%, unexplained 6% (~94% total).
- **Rest & altitude:**
  - Rest: home better-rested wins **62.9%** (+2.7 pp); away better-rested **57.7%** (−2.5). *RESULTS χ²(2)=78.0, p<0.001; +1.5 pp/day reg, +2.3 pp/day playoffs; no era change (LR p=0.434).*
  - Altitude (DEN/UTA): **+8.2 pp** reg season (RESULTS [+6.4,+10.0], p<0.001); **absent in playoffs** (−1.8, p=0.591) — team-quality confound.
  - Playoff rest confounded: controlling for quality, rest shrinks to nothing (RESULTS rest +1.5 pp p=0.146; quality_diff dominant).
**Figure:**

![Fig 4 — box-score differentials](nba_home_court_advantage_differentials.png)

---

## Section 3 — What's Driving the Decline
**Q3: What drove the change?**

- **Referee foul bias narrowed sharply:**
  - Reg season **1.2 → 0.2 fouls/game** (≈**83% reduction**); playoffs **1.6 → 0.7**. *RESULTS reg trend +0.023***/yr; 2023–25 = −0.20.*
  - Generational shift: most home-favoring refs (Garretson, Crawford, Rush) worked 1990s–2000s; distribution compressed (Fig 5).
- **Shot zone advantage evaporated (reg season):**
  - Paint gap **~1.3 → 0.4 pp**. *RESULTS Paint trend −0.037***/yr reg.*
  - Playoffs: narrowed late 2010s then rebounded; downward drift NOT statistically established (playoff Paint trend −0.030, ns) → convergence is a reg-season phenomenon.
- **Three-point revolution:**
  - Tracks decline almost perfectly. 7% threes (1980s, 65% wins) → 40% (today, 55% wins).
  - **Explains the second wave (§1):** 3PA share leapt from ~¼ of shots to ~half right after 2017 — the years home court slid below 56%. *RESULTS 3PA%: 23.8% (2005–17) → 37.5% (2018–22) → 40.1% (2023–25).*
  - *RESULTS reg season-level Pearson r = −0.898, p<0.001.*
  - Within-era effect: ~**2 fewer home wins/100 per 10-pp rise** in 3PA. *RESULTS game-level −2.67 pp/10pp; within-era −2.31 pp, p<0.001.*
  - Playoffs: directional but weaker within-era signal (r=−0.468; within-era p=0.054) — team quality dominates.
- **Quieter fourth strand — rebounding (the glass):**
  - Home rebounding edge shrunk 40 yrs, NOT a 3-point byproduct.
  - *RESULTS 3PA control:* eFG% trend fully absorbed (**219%** absorbed → shooting fade IS the 3-pt story); REB only **11%** absorbed (survives); TOV **52%** absorbed (~half independent).
  - Playoffs: REB survives 3PA control (−66%/strengthens), comparable share of drop.
- **Adding it up (trend decomposition):**
  - Reg season: four channels = **~95% of decline**. *RESULTS:* REB **29%**, TOV **28%**, eFG% **21%**, Foul **18%**; unmediated 5%. → quiet pair (REB+TOV) carries >half.
  - Playoffs: channels = **only ~65%**; ~⅓ unexplained. *RESULTS:* REB 27%, Foul 18%, TOV 12%, eFG% 9%; unmediated 35%. Likely crowd-effect compression post-2018.
**Figures:**

![Fig 5 — referee bias](nba_home_court_referee.png)

![Fig 6 — shot zones](nba_home_court_shot_zones.png)

![Fig 7 — 3PA vs HCA](nba_home_court_3pa.png)

![Fig 8 — mediation shares](nba_home_court_mediation.png)

---

## Section 4 — What Didn't Drive the Change
**Q3 corollary: ruled-out factors**

- **Rule changes:** only **1994–95 hand-checking** crackdown left a mark (~**−2.6 pp** one-time drop; RESULTS era:1995–01 −0.108 log-odds, p=0.010; LR χ²(5)=20.70, p<0.001). All others passed through. Playoffs: not even hand-checking registers (LR p=0.879) — pure smooth drift.
- **Travel & time zones:**
  - Reg: ~**0.08 pp/100 mi** (RESULTS −0.08 pp/100mi, p=0.010), tiny & inconsistent direction; playoffs no effect (p=0.708).
  - Time zones flat both contexts (reg −0.4 pp p=0.085; playoffs +1.2 pp p=0.278).
- **Pace of play:** moves independently of HCA. *RESULTS reg season-level r=+0.280 (p=0.072, wrong direction); playoffs r=−0.115 (ns).*

![Fig 9 — pace vs HCA](nba_home_court_pace.png)

- **Competitive balance:** raw correlation near zero (RESULTS r=−0.066, p=0.676); era pattern inconsistent. Small wrinkle: detrended association emerges (first-diff r=−0.337 p=0.031; residual r=−0.355 p=0.021) but modest, can't explain magnitude.

![Fig 10 — parity vs HCA](nba_home_court_parity.png)

- **Crowd size:** arenas near capacity throughout (~17k→18k+), records set as HCA hit lows. *RESULTS r=+0.279 (p=0.167); detrended ns.* Playoffs ~guaranteed sellouts yet eroded too.

![Fig 11 — attendance & empty-arena](nba_home_court_attendance.png)
- **Empty-arena experiment (2020–21):** empty **51.0%** vs. fans present **58.5%** (RESULTS n=573 vs 591). Presence > count (dose-response +0.51 pp/1000 fans, p=0.184 ns). Vanished when arenas refilled → a switch, not a slow dial.
- **All together:** full model — era effect ≈ half of predictive power; situational factors ≈ other half. *RESULTS Shapley: Era 50%, Rest 17.6%, Altitude 25.7%, TZ 1.5%, COVID 4.8%.* Net era decline **−8.9 pp** (1984–94 → 2023–25) after all controls.
- **Pre/post-2014 test:** rest/altitude/TZ effects statistically unchanged across line; baseline home edge dropped **~4.6 pp** anyway (RESULTS intercept −0.193, post2014 −4.6 pp p<0.001; interaction terms ns). Situational factors held still while floor fell.

---

## Section 5 — The Playoff Picture

- **Home court > everything else:** strongest predictor of playoff outcome.
  - *RESULTS by game:* G1 **69.2%**, G2 **72.0%**, G3 **55.7%**, G4 **55.3%**, G5 **74.8%**, G6 **55.8%**, G7 **64.5%**. χ²(6)=80.40, p<0.001.
  - No evidence road teams adapt as series deepens; home-away split explains it entirely.

![Fig 12 — playoff win % by game number](nba_home_court_series_breakdown.png)
- **Decline is real weakening, not weaker seeds:**
  - *RESULTS:* year trend retained **101%** after quality control; quality absorbs −1%.
  - Lower-seed-at-home (G3+G4): still wins **51.8%** (n=797) — pure venue effect.
  - Seed-quality gap did trend slightly (−0.00028/yr, p<0.001) but doesn't explain HCA decline.
- **2014 format change didn't cause drop:** raw −6.4 pp from 2003–13 → 2014–25 (z=2.87, p=0.004), but trend-controlled dummy ns (p=0.290); LR χ²(3)=4.25, p=0.235. Format table (4 periods).

![Fig 13 — win % by format period](nba_home_court_advantage_format_bars.png)

---

## Section 6 — Other Findings

- **Referee differences real but overstated:** 41/42 home-favoring; spread ~1 foul/game between most-leaning (Garretson −1.736 shrunken, Crawford, Rush) and most even-handed (Foster, Zarba, McCutchen). **~63% of raw spread = sampling noise** (RESULTS true between-SD 0.376 vs observed 0.621). Measures tendencies, not game-fixing.
- **Denver & Utah best home court — altitude is why:** Nuggets **+27.3 pp**, Jazz **+25.9 pp** shrunken (league mean +20.2). ~70% of franchise variation is real (true SD ≈4.1 pp). Altitude piece ≈8 of those points.

![Fig 14 — franchise HCA](nba_home_court_team_hca.png)
- **Playoff franchise differences = illusion:** true between-franchise SD ≈ **0.0** (100% noise); all collapse to league mean +27.1 pp. Fortress reputation = being a good team that plays more home games.
- **Home court worth more in playoffs:** reg **~20 pp** vs. playoffs **~27 pp** → **+7 pp postseason premium** (RESULTS +7.2 pp, SD 7.5). Reg/playoff consistency positive but weak (raw r=+0.356, p=0.045).

---

## Section 7 — Summary
- Recap: HCA nearly halved over 40 yrs; reg **65% → 55.6%**, playoffs **~68% → 58%**.
- Three main drivers + quiet fourth: (1) fairer refs (largest single change), (2) converged shot selection, (3) three-point variance, (4) rebounding edge slipping independently.
- Ruled out: rule changes (except 1994–95), travel, time zones, pace, competitive balance, crowd size, format. Crowd noise = on/off switch (2020–21 51% vs 58.5%), not a slow fade.
- Playoffs follow reg season with ~decade lag; accelerated since 2018; genuine erosion (weaker host still winning less); no sign of bottoming out.
