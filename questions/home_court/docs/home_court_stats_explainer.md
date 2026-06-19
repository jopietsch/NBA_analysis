# Statistical Explainer — `nba_home_court_analysis.py`

A guide to every analysis that produces output in `RESULTS.md`: the data it uses,
the statistical approach, why that approach was chosen, what the results mean, and —
where a section has one — **why its figure takes the form it does** (a `Why this
chart` note). Sections appear in the same order as `RESULTS.md`. The figures
themselves are displayed and captioned in `home_court_findings.md`; here we only explain the
reasoning behind each chart choice. Unlike `home_court_findings.md`, this document uses
statistical terminology freely — it is the methods companion, not the narrative
report.

---

## 0. The Game-Level Dataset (`build_game_dataset`)

**The data.** Every analysis (except shot zones, franchise HCA, referees, and
parity, which use their own season-level inputs) runs on a single DataFrame with
one row per game: 52,399 games from 1983–84 through 2025–26, regular season and
playoffs, assembled from the cached game logs. Each row carries:

- `home_win` (1/0) — the outcome for all the logistic regressions
- `year`, `is_playoff`, `era` (rule-change era), `format_period` (playoff scheduling era), `covid` flag
- `rest_diff` — home team days of rest minus away team days of rest (NaN for each team's first game of a season)
- `altitude_home` — 1 if the home team is Denver or Utah
- `tz_diff` — absolute time-zone difference between the two franchises
- box-score differentials (home minus away): fouls, FG%, eFG%, 3PA rate, 3P%, FT%
- `tov_diff`, `reb_diff` — home-minus-away turnovers and total rebounds (the extra channels used by the mediation decomposition)
- `oreb_diff`, `dreb_diff`, `reb_share_edge`, `league_oreb_rate` — offensive/defensive rebound splits, the pace-free rebound-share edge, and the league offensive-rebound rate (the rebounding decomposition, Section 12)
- `margin` — home point differential
- `game_in_series` — for playoff games, the game number (parsed from the game ID)
- `distance_miles` — haversine distance from the away team's home arena to the game arena
- `tpa_rate_avg` — both teams' combined 3PA as a share of combined FGA
- `pace_avg` — estimated possessions per game (FGA − OREB + TOV + 0.44·FTA, averaged across both teams)
- `expected_pace` — leave-one-out pace: each team's average pace across all its *other* games that season, averaged for the two teams in this game. This matters for the pace analysis (Section 20): realized pace in a game is partly *caused* by the outcome (blowouts produce garbage-time possessions), so using each team's typical pace from other games removes that endogeneity.

For playoff rest and seeding analyses, `quality_diff` is added: home team
regular-season win% minus away team regular-season win% in the same season.
Playoff rest is earned by winning series quickly, so rest and team strength are
confounded; this column is the control.

---

## 1. The Overall Decline (`run_decline_trend`)

**The data.** Games aggregated to one row per season: wins, games, home win %.
43 regular seasons and 42 playoff seasons (lockout/COVID playoff gaps skipped).

**The approach.** Two regressions of home win rate on year, run separately for
regular season and playoffs, plus the same pair re-run within each rule-change era:

1. *Primary:* a **binomial GLM** with (wins, losses) per season as the outcome.
   This models the win count directly, so seasons with more games automatically
   get more weight and the variance is correct for proportion data. The slope
   comes out in log-odds per year and is converted to percentage points at the
   mean win rate for readability.
2. *Cross-check:* **OLS of the season percentage on year with Newey–West HAC
   standard errors** (one lag). Season win rates are autocorrelated — a high-HCA
   season tends to follow a high-HCA season — which makes naive OLS standard
   errors too small. HAC standard errors stay honest about that.

**Why two methods.** The GLM is the statistically right model for binomial data;
the OLS/HAC line is the familiar "fit a line through the points" everyone can
picture, with autocorrelation-robust inference. When both agree, the finding
doesn't depend on modeling choices.

**What the results mean.** They agree almost exactly: the regular season declines
about −0.25 pp/year (≈ −10 pp over 43 seasons, p < 0.001 in both, OLS R² = 0.74 —
year alone explains nearly three-quarters of season-to-season variation in HCA).
The playoffs decline at a similar rate (−0.22 pp/yr, total ≈ −9.5 pp) but with
much wider confidence intervals and a far lower R² (0.20), because each playoff
season is only ~80 games of data. The per-era table shows the decline was not
uniform: in the regular season the steepest significant declines were in
1984–94 (−0.52 pp/yr) and 2018–22 (−1.18 pp/yr); the 2023–26 slope (−0.77 pp/yr)
is gentler and rests on only 4 seasons and isn't significant (p = 0.223)
— with a flat-to-positive plateau between 1995 and 2004.
No individual playoff era reaches significance — single playoff eras are just
3–13 small seasons — so the playoff conclusion rests on the full 42-season trend.

**Why this chart.** The decline is a four-decade drift, so the headline figure is
the simplest thing that can carry it: one dot per season for the home win rate,
regular season and playoffs on the same axes, each with a fitted line. A line lets
a reader eyeball the slope *and* the scatter at once — the tight regular-season
cloud (R² = 0.74) against the noisy playoff one (R² = 0.20). The era shading and
the companion era-bar panel do what a single line can't: they expose that the drift
isn't perfectly smooth, which sets up the discrete-drop question Section 14 tests.

**A note on the per-era sub-regressions.** Two eras have only 3–4 seasons
(2002–04 has N=3 regular-season seasons; the 2002–04 and 2023–26 playoff groups
have N=3 and N=4 respectively). With so few data points, the slope estimates are
nearly unconstrained — a single unusual season can flip the sign. The output flags
these with a warning; treat the flagged slopes as illustrative rather than reliable.

---

## 2. Structural Break Test (`run_structural_break_test`)

**The question.** Section 1 shows the overall 40-year decline and Section 14 tests whether rule-change boundaries produced discrete steps. This section asks a different question: *where does the data itself see the strongest break*, with no prior assumption about which year matters?

**The data.** The same season-level home win % series: 43 regular-season seasons and 42 playoff seasons.

**The approach.** The **QLR (Quandt Likelihood-Ratio, or supremum Chow) test** — the standard econometric test for an unknown break point. For each candidate year *t* (the outer 15% trimmed to ensure both sub-samples have at least a handful of seasons), a **Chow F-test** asks: does fitting two separate regression lines (before *t* and after *t*) reduce the residual sum of squares enough to be noteworthy? The F-statistic at each candidate is

> F(t) = [(RSS_full − RSS_before(t) − RSS_after(t)) / k] / [(RSS_before(t) + RSS_after(t)) / (n − 2k)]

where k = 2 (intercept + slope). The **supremum** of F(t) over all candidate years is the QLR test statistic.

Because we take the max over ~33 candidates, the standard F-distribution p-value would overstate significance (we're doing multiple implicit tests). The correct reference is the asymptotic critical values from **Andrews (1993)**, which account for the maximization: 10% → 7.12, 5% → 8.85, 1% → 12.37 (k=2, outer 15% trimmed). The output also reports the *conditional* p-value (treating the break year as if it were known in advance) as a lower-bound reference.

**Why not just use the rule-change years.** Section 14 tests those. This test is the data-driven complement — it finds where the decline most abruptly changed pace, which may or may not align with a rule change. When the two methods converge, confidence increases; when they diverge, there's something to investigate.

**What the results mean.**
- **Regular season:** The strongest data-implied break falls at **1999 (supremum Chow F = 10.22)**, clearing the 5% Andrews threshold. Before 1999, the regular-season HCA was declining steeply (−0.65 pp/yr); after 1999 the decline slowed markedly (−0.26 pp/yr). The top-5 candidates all cluster in 1992–2003, bracketing the anti-hand-checking era (1995–01). The data-implied break is near but not identical to the rule-change boundary — 1999 falls at the *end* of the aggressive-enforcement window, not its start.
- **Playoffs:** The supremum is only 3.23 (at 2006), well below even the 10% threshold. The playoff decline shows no single data-implied break — consistent with Section 14's finding that playoff HCA is a smooth drift.

---

## 3. CUSUM Test — Parameter Stability (`run_cusum_test`)

**Why this section exists.** The structural break test (Section 2) finds the *single* year where the decline most sharply changes pace. This section asks the complementary question: is the trend *globally* stable, or does it wander outside what one straight line can absorb — anywhere, not just at one break?

**The data.** The same season-level home win % series — 43 regular-season and 42 playoff seasons.

**The approach.** The **CUSUM test (Brown–Durbin–Evans)** accumulates the recursive residuals from the linear year-trend and tracks the running sum against a 5% critical band that widens through the sample. If the cumulative sum exits the band, the parameters are unstable somewhere in that stretch. Where QLR (Section 2) pinpoints one break, CUSUM tests overall stability — agreement raises confidence, disagreement flags something to investigate.

**What the results mean.** Both contexts stay inside the band. The regular-season CUSUM peaks at **87% of the 5% boundary** (|CUSUM| = 14.0 at 2019 vs. a bound of ±16.1) — close, but never out; the playoffs are calmer (peak 32% of the boundary). The apparent tension with Section 2 — which *did* find a regular-season break near 1999 — is the point: that break is a **gradual slope change** (−0.65 → −0.25 pp/yr), not a discrete level jump, and CUSUM has low power against slope-only breaks. Read together, the two tests say the decline bent once, gently, in the late 1990s and has otherwise been a stable straight-line drift, with no hidden instability elsewhere.

---

## 4. Foul & Shooting Differentials by Era (`run_differential_analysis`)

**The data.** Per-game home-minus-away differentials in six box-score metrics —
personal fouls, FG%, eFG%, 3PA rate, 3P%, FT% — for all games in both contexts.

**The approach.** Era-bucketed means per metric, plus an **OLS trend on year**
per metric with significance stars. Negative foul diff = referees call fewer
fouls on the home team.

**Why.** These differentials are the *mechanisms* of HCA — the measurable things
home teams get on the court. The era means show levels; the year trends show
which mechanisms are eroding, which is the heart of research question 3.

**What the results mean.** Two mechanisms are clearly eroding and one is not:

- **Foul bias** collapsed: regular-season home foul advantage went from −1.23
  fouls/game (1984–94) to −0.25 (2023–26), trend +0.022/yr, p < 0.001 — an ~80%
  reduction. The playoffs show the same direction (−1.58 → −0.68, trend
  +0.020/yr, p < 0.01) but retain about 2.7× the residual bias (−0.68 vs. −0.25).
- **The shooting edge** is shrinking in the regular season: FG% diff trend
  −0.021 pp/yr and eFG% −0.015 pp/yr (both p < 0.001), from ~+1.6 pp to
  ~+0.7–1.0 pp. Playoff shooting trends point the same way but aren't
  significant — the playoff shooting edge has held up better.
- **3PA rate diff** trends positive (home teams historically took *fewer*
  threes than visitors; that gap is closing), consistent with league-wide
  shot-selection convergence. 3P% and FT% diffs show no significant trend —
  those were never large or changing.

Section 7 takes these differentials and quantifies how much of the HCA level and
its decline each one accounts for.

**Why this chart.** Six small-multiple panels, one per box-score metric, each a
home-minus-away line over time with a fitted trend and a zero reference line. Small
multiples on a shared layout let a reader scan in one sweep which mechanisms are
sliding toward zero (fouls, shooting) and which are flat (3P%, FT%); the era means
in the table give the levels, the lines give the trends. The zero line matters —
"toward zero" *is* the finding, so it has to be on the axis.

---

## 5. Referee Crew Home Foul Bias — Playoffs (`run_referee_analysis`)

**The data.** Per-official playoff records built from box-score officials data:
for each of the 47 officials with ≥50 playoff games, the mean and SD of
`foul_diff = PF_home − PF_away` across their games (negative = home-favoring),
plus the same stats within each era.

**The approach.** Four layers, each fixing a known statistical trap:

1. **Real one-sample t-tests** per official, using each official's per-game SD —
   testing whether their mean foul_diff differs from zero. (An earlier version
   used a degenerate zero-variance test that made every official "significant";
   this is the corrected test.)
2. **Benjamini–Hochberg FDR correction** across all 47 simultaneous tests — with
   47 officials, ~2 would clear p < 0.05 by luck alone; BH controls the expected
   false-discovery rate at 5%.
3. **Method-of-moments variance decomposition** of the career means: how much of
   the spread *between* officials is real vs. sampling noise.
4. **Empirical-Bayes shrinkage** of each official's mean toward the league mean
   before ranking, plus the same variance decomposition within each era to test
   whether the spread of officials has compressed over time.

**Why all the machinery.** Referee-bias rankings are the most misuse-prone output
in the project — a raw leaderboard of 47 noisy means will always produce
dramatic-looking "most biased ref" headlines. The t-tests establish whether
individual effects are real, BH keeps the count of significant officials honest,
and shrinkage keeps the ranking from rewarding small samples.

**What the results mean.** The bias is universal, not a few bad apples: 45 of 47
officials show home-favoring means, 29 of 47 are individually significant *and
all 29 survive BH correction* — that combination is the signature of a real,
widespread effect. The league mean is −1.10 fouls/game in favor of the home team.
Between-official differences are mostly noise (60% of observed spread; true
between-official SD ≈ 0.41 fouls/game), so even shrunken rankings should be read
loosely. The era decomposition shows compression over time: mean bias fell from
−2.24 (1995–01) to −0.75 (2023–26), and in the recent eras the true
between-official SD estimates hit zero — modern officials are both less
home-favoring and more uniform. (The headline numbers in `home_court_findings.md` quoting
"−1.6 → −0.7" come from Section 4's game-level playoff table; this section's
−1.10 league mean is an *across-officials* average and differs slightly by
construction.)

**Why this chart.** Two panels for two jobs. A horizontal ranked bar chart of the
top/bottom officials answers "who, and how big" — but on its own it is exactly the
leaderboard bait the section warns against, so it is paired with a per-era box plot.
The box plot shows the *distribution* of official biases narrowing and centering
over time, which is the real finding; a bar ranking cannot show a distribution
compressing, and a box plot is the standard tool for that.

---

## 6. Shot Zone Differentials by Era (`run_shot_zone_analysis`)

**The data.** Season-level (not game-level) home-minus-road differences in the
share of FGA taken from four zones — paint, mid-range, corner 3, above-break 3 —
from the NBA's shot-location tables, available only from 1996–97 (30 regular
seasons, 23 playoff seasons).

**The approach.** Same template as Section 4: era means per zone plus an OLS
trend on year. N is seasons, not games, so power is much lower.

**Why.** Section 4 shows home teams shoot *better*; this section shows they
historically also shot from *better places*. Zone shares isolate shot selection
from shot making.

**What the results mean.** The home paint advantage is evaporating in the
regular season: +1.28 pp of FGA share in 1995–01 down to +0.24 in 2023–26
(trend −0.041/yr, p < 0.001), with the mid-range deficit shrinking in mirror
image (+0.025/yr, p < 0.001). Visiting teams now generate paint shots nearly as
well as home teams — analytics-driven offense doesn't care where it's played.
The playoff trends point the same direction (paint −0.032/yr) but are not
significant on only 23 seasons of noisier data; the 2023–26 playoff paint edge
(+1.35) remains near its historical level, so the convergence is only firmly
established for the regular season.

**Why this chart.** Four panels, one per shot zone, each a home-minus-road share
line over time with a zero reference — the same small-multiple logic as Section 4.
The eye tracks the paint edge sliding toward zero and the mid-range deficit closing
in mirror image across the panels. Lines rather than bars because the claim is a
multi-decade convergence trend, not a level comparison.

---

## 7. Mediation — Box-Score Channels (`run_mediation_analysis`)

**The data.** All games with the four home-minus-away channel differentials:
eFG% (shooting), fouls (which carries the free-throw-attempt channel),
turnovers, and rebounds — 49,104 regular-season and 3,292 playoff games. FT%
diff is excluded as negligible (mean ≈ +0.3 pp).

**The approach.** A **linear-probability model (LPM)** — OLS of `home_win` on the
four differentials — with cluster-robust SEs by season, used to drive two exact
accounting identities:

1. **Level identity:** mean win % = intercept + Σ (coef × mean diff). This splits
   the home edge (the amount above a coin flip) into a contribution from each
   channel.
2. **Trend identity:** total pp/yr = unmediated pp/yr + Σ (coef × channel
   trend/yr). This splits the *decline* into per-channel contributions, using
   each channel differential's own year-trend (from the Section 4 template).

A third block — a **3PA-control diagnostic** — was added to settle whether the
turnover and rebounding contributions are independent or merely downstream of the
three-point revolution. For each channel it refits the differential's year-trend
twice, `channel ~ year` and `channel ~ year + tpa_rate_avg`, with season-clustered
SEs, and reports how much of the year-trend the game-level 3PA rate absorbs.
Game-to-game 3PA variation *within* a season gives the control real identifying
power (season means alone would be near-collinear with year). The test is
asymmetric: a trend that **survives** the control is strong evidence of an
independent driver; heavy absorption is only weakly informative because 3PA and
the calendar move together.

**Why an LPM, not a logit.** The whole point is the additive decomposition —
contributions that sum exactly to the level and to the trend. That additivity
holds only in a linear model; a logit's nonlinearity breaks the identity. The
usual LPM cost (fitted probabilities can leave [0,1]) is irrelevant for an
accounting exercise. The channels are *proximate* — how HCA expresses itself in
the box score — so the level/trend split is mediation in the accounting sense;
the 3PA-control diagnostic is what adds a causal-ordering question on top.

**What the results mean.** The four channels capture nearly all of HCA's level in
both contexts and nearly all of its regular-season decline:

- **Regular-season level:** channels carry 95% of the +10.1 pp home edge.
  Shooting (eFG%) is the largest single channel at 43% (+4.4 pp), then rebounds
  25% (+2.5 pp), fouls 14% (+1.4 pp), turnovers 13% (+1.3 pp); 5% unexplained.
- **Regular-season trend:** channels carry 96% of the −0.244 pp/yr decline,
  spread fairly evenly across rebounds (30%), turnovers (27%), shooting (21%),
  and fouls (18%); only 4% is unmediated.
- **Playoffs:** channels carry 93% of the level but only 67% of the decline —
  33% of the playoff decline runs outside the measured box-score channels.

The 3PA-control diagnostic then resolves the obvious follow-up — are rebounds and
turnovers real drivers or just downstream of the perimeter shift? The answers
differ by channel:

- **Shooting** is fully downstream: controlling for 3PA, the home eFG% trend
  doesn't just vanish, it flips sign (absorbed ≈ 210%). The fading home shooting
  edge *is* the three-point story.
- **Rebounding** is independent: only ≈8% of its year-trend is absorbed and it
  stays highly significant (p < 0.001). The home team's rebounding edge has slid
  for reasons the perimeter shift does not explain — a genuine fourth strand of
  the decline, now reflected in `home_court_findings.md` §3 and §7 (Summary). In the playoffs the
  rebounding fade is, if anything, sharper net of 3PA.
- **Fouls and turnovers** are roughly half-and-half (≈51% and ≈54% absorbed) but
  both survive — partly the perimeter story, partly their own.

So the earlier worry that the turnover/rebound shares were "just downstream" was
half right (turnovers, partly) and half wrong (rebounding is its own thing). One
remaining caution: the playoff numbers fold in the seed-quality gap — the home
team is usually the better team — which Section 26 isolates and controls.

**Why this chart.** Stacked horizontal bars, normalized to 100% — one stack for the
level, one for the decline, regular season vs. playoffs. The whole point of a
decomposition is *composition*: how the edge splits into parts that sum to a whole.
A stacked bar is the one chart form that shows shares adding to 100% at a glance; a
line or grouped bars would hide the very accounting identity the LPM exists to
deliver. The grey residual segment is deliberate too — it shows the unexplained
remainder rather than quietly dropping it.

---

## 8. Rest Differential — Buckets and Era Stability (`run_rest_bucket_analysis`)

**The data.** All games with computable rest for both teams (48,424 regular
season, 2,956 playoffs), bucketed into away-more-rested / equal / home-more-rested.

**The approach.** Bucket win rates with a **chi-square test** across buckets;
a **bivariate logistic regression** of `home_win ~ rest_diff` within each era;
and a **rest × era interaction LR test** (comparing `rest_diff + C(era)` against
`rest_diff * C(era)`).

**Why.** The buckets make the effect visible in plain percentages. The per-era
logits and the interaction test answer the change-over-time question that drives
the whole project: did the *rest effect itself* strengthen or weaken, which
could have contributed to the HCA decline?

**What the results mean.** Rest matters: regular-season home win % runs from
57.6% (away more rested) to 62.8% (home more rested), χ² p < 0.001, roughly
+1–3 pp per day of rest edge in every era. The playoff buckets are more extreme
(75.0% when home has more rest) but tiny (144 games) — and confounded, see
Section 9. The key result is the interaction test: p = 0.474 (RS) and 0.727
(playoffs) — **no evidence the rest effect changed across eras**. Rest is a
real component of any given night's HCA, but a stable one; it cannot explain
the 40-year decline.

---

## 9. Rest, Altitude, and Time Zone (`run_factor_summary`)

**The data.** Games with complete rest and time-zone features: 48,424 regular
season, 2,956 playoffs.

**The approach.** **Bivariate logistic regressions** — each factor alone against
`home_win` — in both contexts, with marginal effects in pp and 95% CIs. Then a
targeted follow-up: playoff rest re-estimated with `quality_diff` (the home–away
gap in regular-season win %) added as a control.

**Why bivariate.** This section answers "does each factor matter at all?" in
its simplest form; the multivariable versions live in Section 23. The playoff
quality control exists because playoff rest is endogenous: teams earn extra rest
by sweeping, and teams that sweep are better teams. Without the control, the
rest coefficient absorbs team quality.

**What the results mean.**

- **Rest:** significant in both contexts — +1.6 pp/day regular season,
  +2.4 pp/day playoffs (bivariate). But the playoff effect dies under the
  quality control: rest drops to +1.6 pp/day with p = 0.113, while quality_diff
  is overwhelming (+112 pp per unit, p < 0.001 — an extrapolated marginal effect
  over a full 0-to-1 win-% gap, so it exceeds the 100 pp a probability could
  literally move). Playoff "rest advantage" is mostly just being the better team.
- **Altitude:** Denver/Utah home games run +7.9 pp above baseline in the regular
  season (p < 0.001) but −1.6 pp, n.s., in the playoffs. The playoff null is
  partly confound (good Denver/Utah teams face good opponents) and partly small
  samples, but there is no detectable playoff altitude edge.
- **Time zones:** null in both contexts (−0.4 pp/zone RS, p = 0.086; +1.0
  playoffs, p = 0.330). Only 107 coast-to-coast playoff games exist in 43
  seasons, so the playoff test has little power — but the regular-season test
  has plenty and still finds nothing meaningful.

---

## 10. League-Wide 3-Point Shooting (`run_3pa_analysis`)

**The data.** Per-game combined 3PA rate (`tpa_rate_avg`: both teams' threes as
a share of both teams' FGA), in both contexts.

**The approach.** Five layers, run for regular season and playoffs:

1. **Season-level Pearson and Spearman correlations** between mean 3PA rate and
   home win %.
2. A **game-level bivariate logistic** of `home_win ~ tpa_rate_avg` with
   season-clustered SEs.
3. The same logistic **controlling for era** (`+ C(era)`) — the critical test.
4. A **partial correlation**: detrend both season-level series against year, then
   correlate the residuals. If the raw r collapses once the shared trend is gone,
   the correlation was mostly the trend; if a substantial piece survives, there is
   a genuine year-to-year link.
5. A **rolling 10-season Pearson r** to check whether the relationship is stable
   across the sample or only appears in one stretch (sign flips or wide swings
   would point to a spurious, trend-driven correlation).

**Why the era control is the crux.** 3PA rate and HCA both trended hard over 40
years, so a raw correlation between them is guaranteed and proves nothing
("ice cream sales and drownings"). The within-era model asks: *among games in
the same era*, do higher-3PA games show lower home win rates? If yes, the
relationship survives removal of the shared time trend and is much more likely
to be mechanistic (more threes → more variance → weaker edge for the slightly
better side, which at home is usually the home team).

**What the results mean.** The season-level correlation is enormous (r = −0.90
regular season) but, per the above, that alone is just the two trends. The
decisive result is that the within-era effect barely budges from the bivariate
one: −2.27 pp per 10 pp of 3PA rate (p < 0.001) vs. −2.64 unadjusted. The
3PA–HCA link is *not* merely the shared trend — it holds game-by-game within
eras. The playoffs show an even stronger coefficient (−3.12 pp per 10 pp within era)
at p = 0.027 on 3,292 games — directionally identical and now clearly
significant. This is the strongest mechanistic candidate the data offers for
the decline.

**Cointegration and detrending.** Two checks confirm that the raw r = −0.90 is
mostly, but not entirely, the shared trend. First, an **Engle-Granger
cointegration test**: both 3PA rate and home win % are I(1) (nonstationary
trending series, per ADF unit-root tests), but they are **not cointegrated**, so
they have no genuine long-run equilibrium relationship and a large part of the raw
correlation is just two series drifting in opposite directions for 43 years.
Second, the **partial correlation** quantifies how much: detrending both series
against year drops the season-level r from −0.902 to −0.526 (still p < 0.001), so
roughly 40% of the raw correlation is the shared trend and a real year-to-year
association remains. (The rolling 10-season r swings from −0.87 to −0.19 with no
sign flips — moderate instability consistent with a relationship that is partly
trend-driven.) The reconciliation is the within-era game-level effect: the raw r
overstates the link, the detrended residual and the within-era logit agree that a
genuine component survives, and the within-era result is the cleanest evidence of
it. This is why Section 10's critical test is "does it survive the era control,"
not "how strong is the raw r."

**Why this chart.** Three panels that walk the trap and its resolution. Panel 1 is a
dual-axis time series — 3PA rate rising as home win% falls — which *looks* like
proof but is exactly the shared-trend illusion. Panels 2 and 3 are season scatters
(regular season, playoffs) with the raw correlation annotated. Showing the seductive
dual-axis line right next to the scatter is deliberate: it puts the very correlation
the within-era model then has to defuse in front of the reader, so the payoff lands.

---

## 11. Granger Causality — Does 3PA Lead HCA? (`_run_granger_3pa`)

**The question.** The within-era test (Section 10) establishes that higher-3PA games tend to have lower home win rates within the same era. But correlation within eras still doesn't settle the direction: does the three-point revolution *cause* the decline, or do both respond to the same underlying forces (analytics culture, officiating philosophy, roster construction) without one driving the other?

**Granger causality** offers a limited time-series test: if 3PA rate in year *t* predicts home win % in year *t+1* better than past HCA values alone do, then 3PA "Granger-causes" HCA — it leads in the time series, at minimum. That is necessary (though not sufficient) for a causal story. If the reverse also holds (HCA predicting future 3PA), causality runs both ways or both are downstream of something else.

**The approach.** A **VAR-based Granger test** (`grangercausalitytests` from statsmodels) on the two-variable system [ΔHCA, Δ3PA], where Δ denotes first differences (used because both series are I(1); Granger tests assume stationarity). The test at lag *L* fits two VARs — one with HCA's own lags only, one adding L lags of 3PA — and compares the residual sums of squares with an F-test. Both directions are tested; with N = 42 first-differenced observations, max 2 lags is used to preserve degrees of freedom.

**What the results mean.** No Granger causality in either direction, at either lag (all F p-values > 0.2). Neither does 3PA rate in year *t* predict ΔHCA in year *t+1*, nor does HCA in year *t* predict Δ3PA in year *t+1*. The two series trend together but neither temporally leads the other.

This is informative even though it's a null result: it means the 3PA–HCA association is *contemporaneous* rather than leading/lagging. The within-era game-level link (Section 10) is the evidence that it's a real mechanical effect, not just a shared trend; the Granger null suggests that the annual adoption of threes and the annual change in HCA move together in the same season rather than one predicting the other a year ahead. Both may be downstream of the same broader strategic shift in how the game is played. The Granger test's practical limit here is power: with only 42 seasonal observations, lags of 1–2 years leave few degrees of freedom, so moderate causal effects could go undetected.

---

## 12. Rebounding Decomposition (`run_rebounding_decomposition`)

**Why this section exists.** Section 7 establishes that rebounding carries the
single largest share of the decline but cannot say *why* the home rebounding edge
faded. This section answers that, using only the cached box scores.

**The data.** The same game-level dataset, now carrying four rebounding columns
computed in `_compute_rebound_components`: `oreb_diff` and `dreb_diff`
(home-minus-away offensive/defensive rebounds), `reb_diff` (total), and
`reb_share_edge`.

**The rebound-share metric.** Raw rebound *counts* are a poor measure of skill:
they rise and fall with pace and with how many shots miss (more misses → more
boards to grab). The clean measure is the **share of available rebounds** a team
captures. A team's offensive-rebound share is

> OREB ÷ (own OREB + opponent DREB)

i.e. offensive boards grabbed divided by the team's own missed shots that were
reboundable. `reb_share_edge` is the home team's offensive-rebound share minus the
away team's, in percentage points. Because it is a *ratio* of boards won to boards
available, it is immune to the pace/shot-volume confound — a like-for-like measure
of who controls the glass.

**The approach.** An era table and an OLS year-trend (`stat ~ year`) for each of
the four columns, separately for regular season and playoffs — identical in form
to the differential analysis (Section 4). Then a season-level **Pearson
correlation** between the mean `reb_share_edge` and the league-wide
offensive-rebound rate (`league_oreb_rate` = both teams' OREB ÷ all rebounds),
testing whether the home edge tracks the league's strategic retreat from the
offensive glass.

**Reading the output.**
- The edge **died on the offensive glass**: regular-season `oreb_diff` falls from
  +0.61 to −0.05 (home teams no longer out-offensive-rebound visitors at all),
  while `dreb_diff` only softens (+1.64 → +0.59). All trends negative and highly
  significant (OREB −0.018, DREB −0.027, REB −0.044 per year, all p < 0.001).
- It is **not a pace artifact**: `reb_share_edge` still collapses ~10×, +2.14 pp →
  +0.21 pp (trend −0.052 pp/yr, p < 0.001).
- It is **league-driven**: the season-level correlation between the home share
  edge and the league offensive-rebound rate is **r = +0.82 (p < 0.001, N = 43)**;
  the league rate fell 33% → 26% over the same span. As teams abandoned offensive
  rebounding for transition defense, the effort-driven boards where a home edge
  could form disappeared. However, the **cointegration check** shows both series
  are I(1) (nonstationary) but **not cointegrated** — the r = +0.82 is likely
  spurious correlation from parallel trends rather than a genuine long-run
  relationship. The section-level 3PA-control from Section 7's mediation
  (rebounding survives with only ~8% absorbed) is the stronger evidence that the
  rebounding fade is a real, independent trend.
- The playoffs show the same shape (share edge +2.74 → +0.70 pp, trend −0.046
  pp/yr, p < 0.01), on a smaller sample.

**A note on the share identity.** Because available offensive rebounds for one
team are the same boards the other team can defensively rebound, the home team's
offensive-share edge equals its defensive-share edge exactly — there is one
"control of the glass" number, reported here as the offensive-rebound share edge.

**Player-tracking footnote.** A separate set of helpers
(`compute_tracking_rebound_stats` and `run_tracking_rebound_analysis`) pulls NBA
player-tracking and hustle data (offensive-rebound conversion, box-outs,
second-chance points) split Home/Road via `location_nullable`. It corroborates the
mechanism — no measurable home box-out edge today, offensive-rebound conversion
still shrinking — but only covers the tracking era (~2014 on), too short to carry
the 40-year story, so it is summarized in one sentence in `home_court_findings.md` §3 rather
than reported as its own section here. The code is retained but unwired from the
pipeline.

**Why this chart.** Four panels for the rebounding and turnover story. Panel 1 puts
home and away offensive-rebound rates on the left axis and defensive-rebound rates
on the right, with symmetric y-limits (left 17–37%, right 63–83%) so the
convergence reads at the same scale on both sides. The design makes the accounting
identity explicit: DREB rate = 100 − opponent OREB rate, so a single asymmetric
retreat from the offensive glass produces matching collapses on both sides
simultaneously — one panel rather than two. Panel 2 shows the raw OREB and DREB
differentials (home minus away per game), which are pace-sensitive but make the
absolute magnitudes visible; the DREB edge fell more in absolute terms because it
starts from a higher base. Panel 3 is a scatter of the total rebound differential
against each season's home win rate — the claim is an association, and a scatter
with a fitted line shows that more honestly than a time-series overlay. Panel 4
shows the turnover edge (away minus home turnovers per game), placed here because
the mediation analysis (Section 7) links both categories: they declined over the
same span, and pairing them lets the eye compare their shape and timing.

---

## 13. Player-Tracking Rebounding Mechanism (`run_tracking_rebound_analysis`)

**Why this section exists.** The rebounding decomposition (Section 12) shows the home edge died on the offensive glass, using box scores back to the 1980s. This section corroborates *how* that edge expresses itself up close, using the NBA's player-tracking and hustle data — a much shorter window, but one that can see box-outs and second chances the box score cannot.

**The data.** Home-minus-road differentials in three tracking metrics, split Home/Road via `location_nullable`: offensive-rebound conversion (share of one's own missed shots recovered), box-outs per game, and second-chance points per game. Coverage is the tracking era only — ~2013–14 on (13 seasons), ~2016 on for box-outs (11 seasons).

**The approach.** Identical in form to the box-score sections: a season-level mean and an OLS year-trend (`stat ~ year`) per metric, with significance stars. With at most 13 seasons, power is limited — this is a corroborating check, not a primary test.

**What the results mean.** The modern home edge is small and flat-to-declining on every metric. Offensive-rebound conversion is the only one with a significant trend (mean +0.71 pp, −0.086 pp/yr, p = 0.024) — still shrinking even within the tracking era. The box-out edge sits at essentially zero throughout (−0.000, p = 0.78) and the second-chance-points edge fades without reaching significance (+0.29, −0.016/yr, p = 0.30). The reading is that the offensive-glass advantage had **largely collapsed before high-resolution tracking even began**: by the time the cameras switched on, little edge was left to measure. The window is too short to carry the 40-year story — Section 12 does that — so this section only confirms the modern mechanism.

**Why this chart.** Three small-multiple panels, one per tracking metric, each a home-minus-road line over the tracking era with a zero reference. The shared layout mirrors the box-score differential charts (Sections 4 and 12) so the eye reads them the same way, and the flat-to-declining lines hugging zero are the visual point: the edge is already gone where the cameras can see it.

---

## 14. Rule-Change Eras (`run_era_analysis`)

**The data.** All games, split by the six rule-change eras (1984–94, 1995–01,
2002–04, 2005–17, 2018–22, 2023–26), run separately for regular season (49,107
games) and playoffs (3,292).

**The approach.** Raw win % per era, two-proportion z-tests between consecutive
eras, then `home_win ~ year + C(era)` with a **likelihood-ratio (LR) test**
against year-only.

**Why.** The question is whether the 40-year decline happened as a *smooth
drift* or in *discrete steps* at specific rule changes. The z-tests find the
candidate steps; the trend-controlled model asks whether any step is bigger than
the underlying drift would predict. Because almost none of them is, this analysis
lives in `home_court_findings.md` §4 ("What Didn't Drive the Change") — rule changes are the
most natural suspect, yet only one left a mark.

**What the results mean.** In the regular season, two boundaries show raw
significant drops: 1994→95 (−4.9 pp) and 2017→18 (−3.2 pp). After controlling
for the year trend, only the 1995–01 dummy survives (−2.6 pp, p = 0.010), and
the era dummies are jointly significant (LR p < 0.001). So the regular-season
decline is mostly smooth drift *plus one genuine discrete drop* at the 1994–95
hand-checking rules. In the playoffs, nothing survives: no z-test is significant
and the LR test is p = 0.815 — the playoff decline is pure drift, with no
rule-change fingerprints. (Small samples mean limited power, but there is simply
no signal there.) The same trend-vs-boundary logic recurs for the 2014 Finals
format change in Section 28.

**Why this chart.** This section has no separate figure: the era structure it tests
is already drawn as the shaded eras and the era-bar panel of the Section 1 decline
chart. The discrete-drop question is about reading those era levels *against* the
smooth trend — an inference the z-tests and LR test carry, not something a new
picture would add.

---

## 15. Interrupted Time Series — 1994-95 Boundary (`run_its_test`)

**Why this section exists.** The rule-change era analysis (Section 14) finds one genuine discrete drop, at 1994–95. This section examines that single boundary in isolation, separating an *immediate* level drop from a *change in the rate* of decline — the two ways a rule change could leave a mark.

**The data.** The season-level home win % series (43 regular-season, 42 playoff seasons), weighted by games per season.

**The approach.** An **interrupted-time-series (ITS) regression** by weighted least squares:

> home_pct ~ year + post95 + (year − 1994)·post95

where `post95` = 1 from 1994–95 on (an immediate **level shift**) and the interaction is the **change in slope** after the break. The level term asks "did HCA step down the instant the rules changed?"; the slope term asks "did the *rate* of decline change?"

**What the results mean.** The regular-season fit (R² = 0.78) shows a steep pre-break trend (−0.52 pp/yr, p = 0.004), no significant immediate level drop (−0.62 pp, p = 0.597), and a borderline slope change (+0.34 pp/yr, p = 0.060) that flattens the decline from −0.52 to −0.18 pp/yr afterward. So 1994–95 reads not as a cliff but as a **bend** — the decline slowed over the following seasons rather than dropping in a single step — exactly consistent with the QLR break landing at 1999 (Section 2) rather than 1995. In the playoffs nothing is significant (level p = 0.55, slope p = 0.39): the postseason has no detectable 1994–95 signature, matching the era analysis's finding of pure drift. (Section 14's era model, which *does* flag a significant 1994–95 drop after partialling the year trend, and this ITS are two cuts at the same boundary; together they say the effect is real but gradual, not a clean discrete step.)

---

## 16. Placebo Tests — Is 1994-95 Uniquely Significant? (`run_placebo_tests`)

**Why this section exists.** Section 14 singles out 1994–95 as the one rule boundary that left a mark. A placebo test guards against a tempting error: test *enough* candidate years and some will look significant by chance. This asks whether 1994–95 stands out, or is just one of many "significant" boundaries.

**The data.** The season-level home win % series.

**The approach.** For every candidate year *t* from 1987 to 2010, fit `pct ~ year + step_t`, where `step_t` = 1 for seasons from *t* on. A significant **negative** step coefficient means a discrete drop at that boundary. The 1994–95 boundary is one of 24 placebos; the question is whether it is special.

**What the results mean.** 1994–95 *is* in the significant-negative window (−2.00 pp, p = 0.043) — but so are the years 1990–1995 around it, and that is the subtle part. When a real break exists, **any** boundary placed a few years *before* the drop also tests significant, because it sweeps the decline into its "post" window. So the cluster of significant negatives in the early 1990s is the expected fingerprint of a genuine break in that period, not 24 independent findings. (The significant *positive* steps after ~2002 are the mirror image: post-1999 HCA sits "too high" relative to the steeper pre-1999 trend — the slope moderation QLR found in Section 2.) The placebo test therefore corroborates that *something* real happened in the early-to-mid 1990s but cannot isolate 1994–95 by itself; the trend-controlled era model (Section 14) is what pins the effect specifically to that boundary. In the playoffs no early-1990s boundary is significant at all (only a couple of positive steps in 2004–2006), reaffirming that the postseason decline carries no 1994–95 signature.

---

## 17. Channel Event Study — Which Changed First at 1994-95? (`run_channel_event_study`)

**Why this section exists.** Sections 14–16 establish that 1994–95 left a real mark on home court. This section asks *which mechanism* moved at that boundary — and in particular whether the fingerprint matches the leading suspect, the hand-checking crackdown. If hand-checking is the cause, the **foul** differential should jump immediately while the other channels respond little or only gradually.

**The data.** The four mediation channels (Section 7) as season-level home-minus-away differentials: fouls, eFG%, turnovers, rebounds.

**The approach.** The same interrupted-time-series model as Section 15, run **per channel**: `diff ~ year + post95 + (year − 1994)·post95`. The **level shift** (`post95`) is the immediate response at 1995; a mechanism that changed the instant the rules did should show a significant level term. (Sign note: foul_diff = PF_home − PF_away is negative when the home team is favored, so a *positive* level shift means the home foul edge **shrank** immediately.)

**What the results mean.** Only the foul channel shows a significant immediate response. In the regular season the foul-diff level shift is **+0.44, p = 0.007** — the home foul advantage contracted the moment the hand-checking rules took effect — while eFG% (p = 0.33), turnovers (p = 0.18), and rebounds (p = 0.85) show no significant jump. That is exactly the signature expected if the **hand-checking crackdown** was the operative change: it acts directly on fouls and defense, while the other box-score edges drifted on their own slower schedules. The playoffs show no significant channel shift (small samples, and no 1994–95 break to begin with). This is the closest the data comes to naming a *mechanism* for the one rule change that mattered.

---

## 18. Travel Distance (`run_travel_analysis`)

**The data.** All games with arena coordinates for both teams; distance is the
haversine (great-circle) miles from the away team's home arena to the game arena.

**The approach.** Win % by distance bucket (0–500, 500–1000, 1000–1500, 1500+
miles), plus a **bivariate logistic regression** of `home_win ~ distance_miles`
with **cluster-robust standard errors clustered on season** — games within a
season share league-wide conditions, so treating them as independent would
understate the standard errors.

**Why.** "The road team is tired from the flight" is one of the oldest HCA
folk theories, and distance is cleanly measurable. Buckets show the shape;
the logistic puts a per-mile number and CI on it.

**What the results mean.** Nearly nothing. The regular-season coefficient is
statistically significant (p = 0.010) but practically trivial: −0.07 pp per 100
miles, so a 2,500-mile cross-country trip costs the visitor under 2 pp — and the
buckets don't even decline monotonically (500–1000 miles has the *highest* home
win rate). With N = 49,107, significance is cheap; the effect size is the story.
In the playoffs the effect is null outright (p = 0.888). Travel does not explain
HCA's existence or its decline.

---

## 19. Back-to-Backs (`run_b2b_analysis`)

**The question.** One popular theory for the HCA decline is "load management": NBA schedules now include fewer back-to-back games (zero days of rest), so visiting teams are less often exhausted. Fewer tired visitors → a smaller scheduling edge for the home team → lower home win rates. This section tests whether that story holds up quantitatively.

**The data.** Regular-season games with a computable prior-game date for both teams (48,424 games; back-to-backs are rare enough in the playoffs to be ignored).

**The approach.** Two layers:

1. **Era-frequency table** of visitor and home B2B rates, alongside the era home win %, to see whether the schedule shift and the HCA decline move together.
2. **Shift-share decomposition** of the 1984–94 → 2023–26 home-win change (−9.29 pp) into two components: (a) the *frequency component* — how much of the change is explained by the shift in B2B scheduling, holding per-situation win rates fixed at their 1984–94 values; and (b) the *win-rate component* — how much is explained by the home edge within each rest situation eroding, holding scheduling fixed.

The shift-share identity is exact: frequency + win-rate + interaction = total change.

**Why.** A pure frequency story would show the frequency component absorbing most of the −9.29 pp, with win rates within each situation roughly stable. A frequency component near zero would rule the story out. The decomposition separates those two possibilities cleanly without a regression.

**What the results mean.** The schedule shift is real — visitor B2Bs fell from 35.0% of games in 1984–94 to 18.8% in 2023–26 — but its effect on the overall decline is trivial. When a visitor is on a B2B, the home team wins 64.7% vs. 59.1% when neither team is on one, a +5.6 pp lift. But that lift is modest and the frequency shift is partial, so the frequency component accounts for only **−0.71 pp** of the −9.29 pp total decline — about **8%**. The remaining 92% is the win-rate component: the home edge within every rest-situation category has simply eroded, independent of scheduling. Load management did not drive the decline.

**Why this chart.** This section adds no figure of its own. The era-level B2B frequency and home win % are captured in the era table, and the shift-share is an exact arithmetic decomposition — two numbers that sum to the total. A chart would add no information the table doesn't already carry.

---

## 20. Pace (`run_pace_analysis`)

**The data.** Per-game average possessions (`pace_avg`) and the leave-one-out
`expected_pace` described in Section 0.

**The approach.** The same three-layer template as Section 10 (season
correlations, game-level logit, within-era logit), plus a fourth layer: the
same logits re-run on **expected pace** instead of realized pace.

**Why expected pace matters.** Realized pace is contaminated by reverse
causality: blowouts inflate possession counts (garbage time, intentional
fouling, no late-game stalling), and home blowouts are disproportionately home
wins. So a positive realized-pace coefficient may mean "winning causes pace,"
not "pace causes winning." Expected pace — built only from each team's *other*
games — breaks that loop.

**What the results mean.** Pace is a clean rule-out, and a nice demonstration of
why the LOO version was needed. Season-level correlations are weak and
non-significant in both contexts (RS r = +0.24, p = 0.12; playoffs r = −0.14,
p = 0.37) — and note pace is *U-shaped* over time (fast 80s, slow 90s–00s, fast
again now) while HCA fell monotonically, so the two can't share a trend.
Realized pace shows a significant positive game-level effect (+2.3 pp per 10
possessions, p < 0.001), but switching to expected pace cuts it to +1.5 and
kills significance (p = 0.227; within-era p = 0.063) — confirming the realized
effect was substantially outcome-driven endogeneity. Playoffs: null everywhere.
Pace did not drive the decline.

**Why this chart.** The same three-panel layout as Section 10 (dual-axis time series
plus two season scatters), chosen for the same reason and to invite the side-by-side
comparison. It also makes the rule-out visible two ways: the dual-axis panel shows
pace is U-shaped while HCA fell monotonically — so the two can't even share a trend
— and the flat scatters show the weak season-level association, before the
leave-one-out test in the text delivers the verdict.

---

## 21. Competitive Balance / Parity (`run_parity_correlation`)

**The data.** Season-level: the standard deviation of all 30 teams' win
percentages (the parity measure — lower = more equal league) and the season's
regular-season home win %, 43 seasons.

**The approach.** Four layers:

1. **Pearson and Spearman correlations** between parity SD and home win %.
2. An **OLS slope** of home win % on parity SD, plus era-bucketed averages.
3. **First-differenced correlation**: Δparity vs. Δhome-win% year over year.
4. **Residual-on-year correlation**: each series detrended by its own linear
   year fit, then the residuals correlated.

**Why the detrending layers.** Same trap as Section 10: any two series that
both trend over 40 years will correlate spuriously. The raw correlation here
happens to be near zero anyway, but the detrended checks are the proper test of
the year-to-year relationship — first-differencing and residualizing are the
two standard ways to remove a common trend, and they have different noise
properties (differencing amplifies measurement noise), so both are run.

**Cointegration note.** In this case the formal test is reassuring for a
different reason: **parity (win% SD) is I(0) stationary** (ADF p = 0.023),
while home win % is I(1) — so the classical spurious-regression concern does
not directly apply. A stationary predictor correlated with a nonstationary
outcome is not a cointegration problem; the raw and detrended correlations
are interpretable without that specific worry. The near-zero raw correlation
(r = −0.09) is simply a genuine null.

**What the results mean.** The raw, trend-level answer is a rule-out: r = −0.092
(p = 0.56), R² = 0.009, and the era table actively contradicts the parity
hypothesis (the league's most *unequal* era, 1995–01, had falling HCA; the most
equal, 2002–04, saw HCA tick up). Parity cannot explain the 40-year decline.
The wrinkle: both detrended checks turn up a modest *negative* association
(first-differenced r = −0.330, p = 0.033; residual r = −0.345, p = 0.023) — in
years when the league gets more equal, HCA dips slightly that same year. That
runs in the direction the parity hypothesis predicts, but it is a small
year-to-year wobble on 42–43 data points, flagged in the output itself as
"interpret with caution." It coexists with, and does not overturn, the main
conclusion that parity didn't drive the structural decline.

**Why this chart.** Two panels. A dual-axis time series (home win% vs. parity) shows
the two series don't track; a season scatter with a near-flat fitted line shows the
same null at the cross-section. The dual-axis form is chosen precisely because it
*tempts* the shared-trend reading — the same setup as the 3PA and pace charts — so
the detrended correlations in the text have something concrete to rule out.

---

## 22. Arena Attendance (`run_attendance_analysis`)

**The data.** Per-game attendance scraped from Basketball-Reference, which —
unlike NBA.com — publishes the gate for every game. It is reliable only from
about 1999–2000 on, so this is a ~25-season series (27 seasons cached), not the
full 40. Two slices: (A) league average attendance per game per season vs. the
season's regular-season home win %; (B) every 2020–21 game's attendance paired
with its home_win, the one season when crowd size swung game to game.

**The approach.** Two questions, deliberately separated:

1. **Part A — does crowd *size* track HCA?** Same four-layer detrending battery
   as Section 21: Pearson and Spearman correlations, then a first-differenced
   and a residual-on-year correlation to strip the shared long-run trend.
2. **Part B — what is crowd *presence* worth?** A **logistic regression** of
   home_win on attendance (scaled per 1,000 fans) across the 2020–21 games,
   reported as a marginal effect in pp, alongside the raw empty-vs-present home
   win split.

**Why split size from presence.** They are different hypotheses and the data
answers them differently. Season-level attendance is nearly constant (every
arena runs near capacity), so it can rule a *size* effect in or out but can say
nothing about what a crowd is worth — there is no variation to exploit.

**Cointegration note.** League-average attendance is **I(0) stationary** (ADF
p = 0.005) — arenas have operated near-capacity for two decades with little
secular drift. Since one series is stationary, the classical spurious-regression
concern (two I(1) series falsely correlating) does not apply here. The detrended
checks are still run as a standard robustness step, but the raw correlation is
interpretable directly. The
2020–21 season supplied that missing variation by accident: COVID rules left
some buildings empty and others partly filled, a quasi-natural experiment that
isolates presence from everything else. Part B is closer to causal evidence
than anything else in the report; the trade-off is a single season and a
binary-ish exposure, so it is read cautiously.

**What the results mean.** Part A is a clean rule-out: the raw correlation is
weak and non-significant (Pearson r = +0.25, p = 0.21), and both detrended
checks are null (first-differenced r = +0.07, p = 0.72; residual-on-year
r = +0.33, p = 0.09). The lone significant number, Spearman ρ = −0.49
(p = 0.009), runs *against* the crowd-size story — attendance climbed to record
highs in the 2020s exactly as HCA bottomed out, so by rank the two move
opposite. Crowd size is not behind the decline. Part B is where the crowd shows
up: with the arena empty, home teams won just 51.0% (n = 573); with any fans
present, 58.5% (n = 591). The per-1,000-fans logistic slope is small and not
significant (+0.51 pp, p = 0.18), which is the point — the effect rides on the
*presence* of a crowd, not its exact size, and it vanished the moment arenas
refilled in 2021–22. A real ingredient of home court, but a switch, not the
four-decade dial.

**Why this chart.** The two panels mirror the two hypotheses the section
deliberately separates. Panel 1 (dual-axis time series) answers crowd *size* —
attendance flat near capacity while HCA falls. Panel 2 is a dose-response bar chart
of 2020–21 home win% by attendance bucket: a bar per dose is the natural way to show
the accidental experiment, with the empty-arena bar sitting at a coin flip and the
filled bars climbing above it. Two different questions, so two different chart
forms.

---

## 23. What Explains the Regular-Season Decline? (`run_sequential_decomposition`)

**The data.** Regular-season games with complete features (48,424).

**The approach.** Two decompositions of the same full model
(`home_win ~ era + rest_diff + altitude_home + tz_diff + covid`), fitted by
logistic regression with cluster-robust SEs (clusters = season):

1. **Sequential ΔR²:** five nested models, adding one block at a time (era
   first), recording how much **McFadden pseudo-R²** each block adds. McFadden
   R² = 1 − llf/llnull; its typical values are far smaller than linear R², so
   only relative shares are interpreted, never the absolute level.
2. **Shapley decomposition:** all 2⁵ = 32 subset models are fitted, and each
   block's contribution is its average marginal R² across every possible order
   of entry (weighted by the Shapley formula). This removes the arbitrary
   "era goes first" advantage that sequential decomposition gives.

**Why both.** Sequential decomposition is intuitive but order-dependent: whatever
enters first soaks up shared explanatory power. Shapley is the order-free
correction. Reporting them side by side shows how much the ordering mattered.

**What the results mean.** The full-model coefficients confirm everything is
simultaneously real: each era dummy is significantly negative and monotonically
deepening (down to −9.0 pp for 2023–26 vs. 1984–94), rest +1.5 pp/day, altitude
+7.8 pp, COVID seasons −2.3 pp, time zone −0.6 pp (significant but tiny). The
decomposition splits the model's explanatory power roughly 50/50: era (the
structural decline) gets a 53% Shapley share (58% sequential — modestly inflated
by going first), altitude 24%, rest 18%, with time zone and COVID under 5%
each. Reading it back: the situational factors (rest, altitude) explain which
*games* home teams win, but the era structure — the thing that changed over
40 years — is half the story, and none of the situational factors changed
(Sections 8, 24), so they can't be what drove the decline.

---

## 24. Pre/Post-2014 Coefficient Stability (`run_stability_analysis`)

**The data.** Regular-season games with complete features, split at 2014
(32,975 before, 15,449 after).

**The approach.** The logit `home_win ~ rest_diff + altitude_home + tz_diff`
fitted separately on each half, comparing coefficients; then a formal **pooled
interaction model** `(rest + altitude + tz) * post2014`, where each interaction
term tests whether that factor's effect changed and the `post2014` main effect
captures the level shift.

**Why.** The post-2014 window contains the steepest part of the recent decline.
If rest, altitude, or time-zone effects had weakened in that window, they would
be candidate explanations for it. Stable coefficients plus a falling intercept
means the decline operates *through some other channel*.

**What the results mean.** That is largely the pattern. The rest and time-zone
interactions are not significant (rest p = 0.142, tz p = 0.917); the altitude
interaction is (p = 0.026), with Denver/Utah's home edge roughly halving after
2014. But the headline is the post-2014 level shift, which is large and
unambiguous (−4.7 pp, p < 0.001) and dwarfs any factor-specific change. Home
teams kept their rest edge at full strength and most of their altitude edge; they
simply started winning less for reasons those factors don't capture — pointing to
the foul-bias and shot-selection channels in Sections 4 and 6. (Altitude's
−4.3 pp interaction is the one situational effect that has measurably weakened
with the added seasons, though it touches only two teams.)

---

## 25. Playoff Series Structure (`run_series_breakdown`)

**The data.** All playoff games with a parseable game number, G1 through G7
(509 down to 188 games as series lengths thin out).

**The approach.** Home win % per game number; a **chi-square contingency test**
of whether home win % is uniform across game numbers; and a **weighted OLS trend**
of home win % on game number (weights = games per game number).

**Why.** Two distinct hypotheses live here. The chi-square asks "does game
number matter at all?" The trend line asks the specific popular theory that
road teams adapt as a series progresses (which would show as a negative slope —
home win % falling in later games).

**What the results mean.** Game number matters enormously (χ²(6) = 84.5,
p < 0.001) but there is no monotonic trend (−1.07 pp/game, p = 0.55). The
pattern is entirely venue alternation: G1/G2/G5 at the higher seed run 69–75%
home win rates; G3/G4/G6 at the lower seed run 55–56%. G7, back at the higher
seed, is 63.8%. The "road teams figure it out by game 6" story has no support —
what looks like series dynamics is just which arena the game is in, plus the
fact that the higher seed is usually the better team.

**Why this chart.** Two panels. A bar chart of home win% by game number (G1–G7) with
sample-size labels makes the venue-alternation sawtooth obvious — bars, because game
number is a discrete category, not a continuous axis. The companion per-era line
panel shows the sawtooth is stable across eras, ruling out the "teams adapt over a
series" story visually before the trend test confirms no monotonic slope.

---

## 26. Playoff HCA — Seeding Quality Decomposition (`run_playoff_quality_decomposition`)

**The data.** All 3,292 playoff games with `quality_diff` = home team's
regular-season win % minus the away team's, same season.

**The approach.** Three pieces:

1. **Year-trend comparison across three logits** — year only, quality only,
   year + quality_diff — to see how much of the playoff decline is *absorbed*
   once the team-quality gap is in the model (reported as "% of the year
   coefficient retained").
2. **A trend test on mean `quality_diff` over seasons** — has the seed-quality
   gap itself narrowed over time, which could mimic a home-court decline?
3. **A lower-seed-at-home check** — home win % in G3/G4 games where the home
   team is objectively the weaker side (`quality_diff < 0`), which strips team
   quality out entirely and leaves only the venue.

**Why.** The playoff decline could be an artifact rather than real home-court
weakening: if top seeds no longer outclass their opponents as much, the playoff
home team (usually the better team) would win less *without home court itself
changing*. `quality_diff` is the control that separates "home court is genuinely
weakening" from "seeds are more evenly matched." This is the playoff counterpart
to Section 23's regular-season decomposition.

**What the results mean.** The decline is genuine home-court weakening, not seed
compression. Adding `quality_diff` barely moves the year coefficient
(−0.225 → −0.229 pp/yr; 102% retained, ≈ −2% absorbed), even though quality_diff
itself is a massive predictor of any single game (+112 pp per unit of win-% gap,
p < 0.001). The seed-quality gap *has* trended down slightly (−0.00026/yr,
p < 0.001), but that drift doesn't account for the home-win decline. The clincher
is the lower-seed-at-home check: when the objectively weaker team hosts G3/G4, it
still wins 51.5% — a pure venue effect with quality stripped out. This dovetails
with Section 7 (playoff channels carry only 67% of the decline) and Section 9
(playoff rest is confounded with quality, but the decline is not).

---

## 27. Team Quality Fixed Effects Robustness (`run_team_quality_robustness`)

**The question.** The sequential decomposition (Section 23) identifies how much the era structure explains, but it does not control for *which specific franchises* happen to be home or away. Could the era coefficients be confounded by systematic changes in home-team composition — for example, if the 1984–94 era had the league's dominant teams disproportionately hosting games, inflating the measured HCA?

**The approach.** Two logistic models, both with cluster-robust SEs on season:

1. **Baseline:** `home_win ~ era + rest_diff + altitude_home + tz_diff + covid` — the Section 23 full model.
2. **With team fixed effects:** the baseline plus `C(TEAM_NAME_home) + C(TEAM_NAME_away)` — one binary indicator per franchise in each role. With 30 current and historical franchises, this adds ~58 dummies to the logistic.

The comparison focuses on the era dummy coefficients. If they shift substantially, the era structure was absorbing roster/venue composition effects rather than a genuine change in home-court dynamics.

**Why team FE instead of quality scores.** Pre-game quality scores require per-team season win% computed separately per game (to avoid look-ahead), which adds complexity without adding much for a league-wide trend question. Team fixed effects remove any *time-averaged* franchise-level advantage — a cleaner and simpler check of the composition confound.

**What the results mean.** Era coefficients shift by at most **0.5 pp** across all five eras (max |Δ| = 0.5 pp). The team fixed effects explain additional variation (McFadden R² rises from 0.005 to 0.027) — individual franchises do have persistent home-win tendencies — but they are absorbed into the franchise intercepts, not into the era structure. The era decline is **not** an artifact of which teams happen to host games in which decades.

---

## 28. Playoff Format Periods (`run_format_period_analysis`)

**The data.** Playoff games only (3,292), grouped by the league's playoff
scheduling formats: 1984, 1985–02, 2003–13, and 2014–26 (the 2014 change moved
the Finals from 2-3-2 back to 2-2-1-1-1).

**The approach.** Three layers:

1. Raw home win % per format period.
2. **Two-proportion z-tests** between consecutive periods — the simplest test of
   whether the win rate actually moved at each boundary.
3. A **logistic regression** of `home_win ~ year + format_period`, plus a
   **likelihood-ratio (LR) test** comparing it against `home_win ~ year` alone.

**Why.** The raw comparison (step 2) shows a big, significant drop at the 2014
boundary (−6.8 pp, p = 0.002). But HCA was *also* declining smoothly throughout —
so any late-period dummy would look negative even if the format change did
nothing. Step 3 separates the two stories: if the format dummies still matter
after the year trend is in the model, the change had its own effect; if not, the
drop is just the trend passing through the boundary.

**What the results mean.** Once the year trend is controlled, no format dummy is
significant (all p ≈ 0.30) and the LR test for the dummies jointly is p = 0.197.
The post-2014 playoff drop is fully consistent with the secular decline; the
format change itself is exonerated.

**Why this chart.** The format periods are shown as paired regular-season/playoff
bars — discrete periods call for bars, not a line. The bars make the raw post-2014
drop look alarming on purpose; the section's whole point is that the drop is just
the secular trend passing through the boundary, which is why those bar levels are
read against the year-trend model in the text rather than taken at face value. This is the canonical example in this project
of why "raw difference between periods" and "effect of the boundary" are
different questions — the same logic the era analysis (Section 14) applies to
rule changes.

---

## 29. Franchise Home Court Advantage (`run_team_hca_analysis`)

**The data.** Per-franchise career totals across all 43 seasons: home win %,
road win %, and HCA = home% − road% (subtracting road win % controls for the
franchise just being good). 39 regular-season franchises (≥50 home games) and
32 playoff franchises (≥20).

**The approach.** Three pieces:

1. **Binomial confidence intervals** on each franchise's raw HCA.
2. A **method-of-moments variance decomposition**: the observed variance of HCA
   across franchises = true between-franchise variance + average sampling
   variance. Subtracting the (computable) sampling part estimates how much
   real spread exists.
3. **Empirical-Bayes shrinkage**: each franchise's estimate is pulled toward
   the league mean in proportion to how noisy it is —
   weight = true_var / (true_var + sampling_var). Noisy estimates (few games)
   get pulled hard; precise ones barely move.

**Why.** Raw franchise HCA tables are leaderboard bait: small-sample franchises
land at the extremes purely by luck (the Kansas City Kings' +35.4 raw HCA rests
on 82 home games). Shrinkage produces rankings you'd actually bet on, and the
variance decomposition says upfront whether *any* real franchise differences
exist before ranking them.

**What the results mean.** The two contexts give opposite answers. In the
regular season, true between-franchise spread is real: observed SD 4.9 pp, only
30% of it sampling noise, true SD ≈ 4.1 pp. Denver (+26.8 shrunken) and Utah
(+25.7) genuinely top the table — consistent with the altitude finding in
Section 9. In the playoffs, sampling noise accounts for 100% of the observed
spread: true between-franchise SD ≈ 0, and shrinkage collapses every franchise
to the league mean (+26.9 pp). Utah's raw +39.7 playoff HCA and the Clippers'
raw −3.6 are both indistinguishable from the same underlying value. No franchise
has demonstrably special playoff home court.

**Why this chart.** Two panels. A horizontal bar chart of franchise HCA, sorted and
carrying 95% confidence whiskers, shows both the ranking *and* how much of it is
noise — the whiskers are the visual antidote to leaderboard-reading. A reg-vs-playoff
scatter with a y=x line shows whether the same franchises lead in both contexts
(Section 30's question), and the points' error bars make the playoff cloud's
collapse to noise visible.

---

## 30. Franchise HCA Consistency (`run_hca_consistency_analysis`)

**The data.** The 32 franchises that appear in both tables from Section 29.

**The approach.** **Pearson and Spearman correlations** between regular-season
and playoff HCA across franchises, computed on raw values and (where defined)
on shrunken values — shrinkage reduces the attenuation bias that measurement
noise inflicts on correlations.

**Why.** If home court advantage is a stable property of an arena/fanbase, the
same franchises should top both lists. The two correlation flavors check
robustness: Pearson for the linear relationship, Spearman for rank agreement
(insensitive to outliers).

**What the results mean.** The raw Pearson correlation is positive and just
significant (r = +0.362, p = 0.042) but Spearman is not (p = 0.128) — weak
evidence that regular-season home-court strength carries into the playoffs.
The shrunken correlation is undefined because playoff true variance is zero
(Section 29), which is itself the deeper finding: there is no reliable
franchise-level playoff signal to correlate. One solid descriptive fact: playoff
HCA runs about +7.2 pp higher than regular-season HCA for the same franchises —
home court is worth more in the postseason on average, though the gap varies
widely by franchise (SD 7.4 pp, larger than the mean itself).

**Why this chart.** Like Section 14, this section adds no figure of its own: its
reg-vs-playoff question is exactly the scatter (with the y=x diagonal) in the
Section 29 franchise chart. The correlation reported here is what the spread of those
points around the diagonal amounts to numerically.

---

## 31. Win Margin Trends (`run_margin_analysis`)

**The data.** Home point differential per game, available from 1996–97 onward
(35,536 regular-season and 2,357 playoff games), split three ways: all games,
home wins only, home losses only.

**The approach.** Era-bucketed means for each of the three columns, plus a
simple **OLS trend of margin on year** per column, with significance stars.

**Why.** Win % is a coarse summary; margins show *how* games are changing. The
all-games column tracks the average home edge in points. The conditional columns
(wins-only, losses-only) test the "polarization" idea — are home wins getting
bigger even as home wins get rarer?

**What the results mean.** In the regular season the average home margin shrank
(−0.057 pts/yr, from ~+3.0 to ~+2.0 points) while home wins got *bigger*
(+0.048 pts/yr) and home losses got *worse* (−0.095 pts/yr) — all three trends
significant. The playoffs show the same conditional divergence (wins +0.149
pts/yr, losses −0.101) with a flat overall margin. But conditional-on-outcome
means have a built-in artifact: as the home win rate falls, games near zero
margin flip from narrow wins to narrow losses, which mechanically pushes both
conditional means apart. Section 32 exists to test whether the divergence is
real or just that artifact.

**Why this chart.** Win percentage is a coarse 1/0 summary, so the margin figure
plots the *size* of the home edge instead: mean margin per season (how big the
average edge is), a win-only vs. loss-only panel, and era bars. Lines are the right
form because the question is direction-over-time, and the two diverging win/loss
lines make the polarization claim visible to the eye before Section 32 tests it
formally.

---

## 32. Win Margin Polarization (`run_quantile_margin_analysis`)

**The data.** The same margin data as Section 31.

**The approach.** **Quantile regression** of margin on year at q = 0.10, 0.25,
0.50, 0.75, 0.90 — fitting a separate trend line through each part of the margin
distribution, *unconditional* on who won.

**Why.** This is the clean test of the artifact problem in Section 31. Quantiles
of the full distribution don't condition on the outcome, so they can't be fooled
by games switching sides. Two diagnostic patterns: if all five quantile slopes
are parallel, the distribution is just shifting down (a pure level effect, and
the Section 31 divergence is a composition artifact). If the bottom quantile
falls while the top rises, the distribution is genuinely widening —
polarization is real.

**What the results mean.** Polarization is real in both contexts. In the regular
season, Q10 falls at −0.167 pts/yr while Q90 rises at +0.050 (both significant);
the Q90−Q10 spread widens by +0.22 pts/yr. The playoffs widen even more
(+0.33 pts/yr), driven by the top of the distribution (Q75 and Q90
rising significantly; the bottom tail, Q10 −0.104, p = 0.062, is flat). In the
regular season both tails move — home blowout wins and home blowout losses are
both becoming more common; in the playoffs the widening is one-sided, driven by
the growing blowout wins alone. Either way it is a genuine change in the shape of
game outcomes, not a bookkeeping artifact.

**Why this chart.** This section adds no figure of its own. The polarization it
formalizes is already what the win-only/loss-only panel of the Section 31 margin
chart shows to the eye — two lines pulling apart. A separate quantile-fan chart
would just duplicate that picture; here the *unconditional* quantile slopes are
what make the claim airtight, and those live in the table, not a new plot.

---

## 33. Multiple Comparisons — BH FDR Correction (`run_multiple_comparisons_summary`)

**The problem.** The report runs roughly 14 primary hypothesis tests across sections. At α = 0.05, we expect 0.7 false discoveries by chance even if every null is true. Reporting each test against its own α = 0.05 threshold is defensible when tests are pre-specified and have independent scientific rationale, but it is worth checking whether any findings are fragile.

**The approach.** **Benjamini–Hochberg (BH) FDR correction** at q = 0.05. The procedure: (1) rank the 14 p-values from smallest to largest; (2) the BH threshold for rank i is (i/14) × 0.05; (3) find the largest rank where p ≤ threshold; (4) all tests at or below that rank "survive." BH controls the *false discovery rate* — the expected fraction of surviving tests that are false positives — at q = 5%. It is less conservative than Bonferroni (which controls FWER, the probability of any false positive) and is the standard choice when a small number of false positives is acceptable.

**The 14 tests** cover: the two overall HCA trends (RS and PO binomial GLMs); rest differential (RS and PO); altitude (RS); time zone (RS); 3PA within-era (RS and PO); pace LOO within-era (RS); travel distance (RS); parity first-differenced (RS); OREB rate vs. rebound share edge (RS); era dummies LR test beyond year trend (RS and PO).

**What the results mean.** 11 of 14 tests survive BH correction:
- **Survive:** both HCA trends, rest effect RS and PO, altitude RS, 3PA RS and PO, RS era dummies LR test (p = 0.002), travel RS, parity first-diff RS, OREB rate vs. rebound edge RS.
- **Do not survive:** time zone effect (p ≈ 0.05, marginal), pace LOO within-era (p ≈ 0.06), PO era dummies LR test (p ≈ 0.64).

The "ruled-out" findings remain correct descriptions of the data — the time zone and pace effects exist — but they are too small and marginal to be called reliable when multiple comparisons are accounted for. The core findings (structural decline, rest, altitude, three-point shooting) survive comfortably. Travel (p = 0.010) also survives, though the effect size is trivially small (Section 18).

---

## Recurring Methods — Quick Reference

- **Logistic regression / logit:** the workhorse for the binary `home_win`
  outcome. Coefficients are in log-odds; the code converts them to approximate
  percentage points via the marginal effect at the mean,
  `pp ≈ coef × p̄ × (1−p̄) × 100`.
- **Linear probability model (LPM):** OLS with a 0/1 outcome, used in the
  mediation decomposition (Section 7) because its coefficients are additive —
  the only way to make channel contributions sum exactly to the HCA level and
  trend. Logits can't deliver that identity.
- **Cluster-robust SEs (clusters = season):** used whenever game-level models
  pool many seasons; games within a season share league conditions, violating
  independence.
- **LR (likelihood-ratio) test:** compares nested logits; 2×(llf_big − llf_small)
  is χ² with df = added parameters. Used to test whether a *block* of dummies
  (eras, format periods, interactions) jointly earns its place.
- **McFadden pseudo-R²:** 1 − llf/llnull. Only relative comparisons are
  meaningful; values look tiny compared to linear R² even for strong effects.
- **Two-proportion z-test:** the simple raw comparison of win rates between two
  periods, used before trend-controlled models to show what the trend control
  changes.
- **Empirical-Bayes shrinkage + method-of-moments variance decomposition:**
  used for any "ranking of noisy means" (franchises, referees). Decomposition
  asks "is there any true spread?"; shrinkage weights each estimate by its
  reliability before ranking.
- **HAC (Newey–West) SEs:** autocorrelation-robust standard errors for
  season-level time-series OLS.
- **Benjamini–Hochberg (BH FDR):** false-discovery-rate control when running
  many simultaneous hypothesis tests. Used for the 47 referee t-tests (Section 5)
  and the 14 primary tests in the multiple-comparisons summary (Section 33).
  The threshold for test at rank i (sorted by ascending p-value) is (i/m)×q,
  where m is the total number of tests and q is the desired FDR level (0.05 here).
- **ADF unit-root test (Augmented Dickey-Fuller):** tests whether a time series
  has a unit root (I(1), nonstationary). H0: unit root; p < 0.05 means the
  series is stationary (I(0)). Used before any season-level correlation between
  two trending series to check for the spurious-regression risk.
- **Engle-Granger cointegration:** when two series are both I(1), this test asks
  whether they share a genuine long-run equilibrium relationship (cointegration)
  or merely happen to trend in the same direction. H0: no cointegration. If both
  series are I(1) but *not* cointegrated (as found for 3PA-HCA and OREB-HCA),
  their Pearson r is likely spurious and within-era controls are the reliable
  evidence.
- **Granger causality:** a time-series test of temporal ordering. "X Granger-causes
  Y" means lagged X improves forecasts of Y beyond what Y's own lags predict. Run
  on first differences when series are I(1). A null result means the two series
  move contemporaneously; they may still be mechanically linked within the same
  season (as 3PA and HCA appear to be, per Section 10's within-era game-level test).
- **QLR supremum Chow test:** the structural-break test for an unknown break year.
  A Chow F-test is run at each candidate year; the maximum (supremum) F is the
  QLR statistic. Because we maximize over many years, Andrews (1993) asymptotic
  critical values are used rather than a standard F-table (k=2 parameters, 15%
  trimming: 10% → 7.12, 5% → 8.85, 1% → 12.37).
