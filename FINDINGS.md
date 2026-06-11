# NBA Home Court Advantage — Findings

Narrative interpretation of the analysis. This file drives the PDF report —
update here and regenerate the PDF to keep them in sync. For regression tables
and coefficient values, see `RESULTS.md` (auto-generated each run).

---

## 1. The Decline

Home court advantage has been falling for 40 years in both the regular season
and the playoffs, with the regular-season decline somewhat steeper than the
playoff one. The gap between the two widened through the mid-2000s and has
narrowed back to roughly its mid-1980s level in recent seasons.

The 2020 bubble season (neutral-site playoffs) is excluded from playoff stats.
COVID seasons are flagged in the charts and regression as an anomaly.

### The trend is statistically unambiguous

A trend line fit to per-season home win % on year confirms the decline is real and
precisely measured. The regular season falls at roughly **−0.25 pp per year**
(p < 0.001, R² = 0.73) — a total drop of more than 10 percentage points over
the 41-year dataset. The playoffs fall at **−0.20 pp per year** (p = 0.009),
though with more year-to-year volatility (R² = 0.16).

Within individual eras the season counts are mostly too small for reliable slope
estimates (only the 1984–94 and 2005–17 regular-season slopes reach p < 0.05),
but the overall trajectory is one of the strongest trends in the dataset. The
regularity of the decline — not a one-time step but a persistent drift — points
to systemic forces rather than a single rule change.

![Figure 1. Home win % per season, 1983–84 through 2024–25. Blue = regular season, green = playoffs. Dashed lines are overall trend fits. Background shading marks rule-change eras.](nba_home_court_advantage_season.png)

---

## 2. Era and Format Period Analysis

The NBA has gone through six distinct rule-change eras since 1984, each affecting
pace, defense, and officiating. Home court advantage has declined in nearly every
successive era in both the regular season and the playoffs, with the steepest
drops in the most recent eras.

The playoff-format analysis divides the dataset into four periods defined by the
1985, 2003, and 2014 Finals scheduling changes. The 2014 shift from a 2-3-2 to a
2-2-1-1-1 series structure coincided with a sharp fall in playoff home win
percentage — from 66.3% in 2003–13 to 59.8% in 2014–25, a −6.4 pp drop that is
highly significant in a direct comparison (p = 0.004). The earlier format changes
moved playoff home win % by less than 2 pp and neither is statistically
distinguishable from zero.

The drop cannot, however, be attributed to the format change itself: once the
secular year trend is controlled for, the format-period indicators add no
significant explanatory power (joint test p = 0.24; the 2014–25 indicator alone
p = 0.29). The post-2014 fall is consistent with the long-run decline passing
through that boundary, not with a distinct format effect.

![Figure 2. Average home win % by rule-change era. Blue = regular season, green = playoffs.](nba_home_court_advantage_era_bars.png)

![Figure 3. Average home win % by playoff format period (1985, 2003, 2014 format changes). Blue = regular season, green = playoffs.](nba_home_court_advantage_format_bars.png)

---

## 3. Per-Era Trend Lines

Fitting a separate trend line within each era reveals that the decline is not a
smooth drift — there are periods of relative stability and periods of sharper
change. Playoff home court advantage has consistently exceeded the regular-season
figure; the gap widened through the mid-2000s and has narrowed back toward its
1980s level in recent seasons.

![Figure 4. Regular-season home win % per season. A separate trend line is fit within each rule-change era. Background shading identifies each era.](nba_home_court_advantage_regular_era.png)

![Figure 5. Playoff home win % per season with a separate trend line per era. Vertical markers indicate playoff format changes (1985, 2003, 2014).](nba_home_court_advantage_playoffs_era.png)

### Rule-Change Eras (regular season and playoffs)

| Era | Seasons | Rule change |
|-----|---------|-------------|
| 1984–94 | 1983–84 through 1993–94 | Illegal defense rules (no zone defense) |
| 1995–01 | 1994–95 through 2000–01 | Hand-checking restrictions; zone still illegal |
| 2002–04 | 2001–02 through 2003–04 | Zone defense legalized, defensive 3-sec added |
| 2005–17 | 2004–05 through 2016–17 | Perimeter hand-checking banned (pace-and-space) |
| 2018–22 | 2017–18 through 2021–22 | Freedom-of-movement emphasis |
| 2023–25 | 2022–23 through 2024–25 | Transition take-foul rule added |

### Playoff Format Periods

| Period | Seasons | Format |
|--------|---------|--------|
| 1984 | 1983–84 | Best-of-5 R1, 2-2-1-1-1 Finals (alternating home court) |
| 1985–02 | 1984–85 through 2001–02 | Best-of-5 R1, 2-3-2 Finals (home court by record) |
| 2003–13 | 2002–03 through 2012–13 | Best-of-7 R1, 2-3-2 Finals |
| 2014–25 | 2013–14 through 2024–25 | Best-of-7 R1, 2-2-1-1-1 Finals |

---

## 4. Win Margin Trends

Point margin data (PLUS_MINUS) is unavailable in the NBA.com game logs before the
1995–96 season, so this analysis covers 1995–96 through 2024–25.

### The decline is not about wins getting closer

The overall home-team point margin in the regular season has declined
significantly (−0.055 pts per year, p < 0.001) — but the mechanism is
surprising. Home wins are actually getting **larger**, not smaller
(+0.041 pts/yr, p < 0.001). What is driving the decline is that home losses
are getting worse: the average home loss margin has grown by −0.083 pts/yr
(p < 0.001). Home teams are losing more games, and when they lose, they lose
by more.

### Polarization is genuine, not a composition artifact

The conditional-on-outcome pattern above could be a mechanical artifact: as
home win rate falls, marginal close games migrate from the win pool to the
loss pool, pushing both conditional means away from zero without any
individual game becoming more lopsided. Unconditional quantile regression on
the raw home margin directly tests this.

Regular-season quantile regression (1996–97 through 2024–25, N = 34,311 games)
finds that Q90 (big home wins) rises at **+0.045 pts/yr** (p = 0.005) while Q10
(big home losses) falls at **−0.154 pts/yr** (p < 0.001). The IQR spread widens
at **+0.199 pts/yr**. These slopes are statistically significant and diverge in
opposite directions — the distribution is genuinely widening, not merely
shifting. The "polarization" reading from the conditional-on-outcome analysis
reflects a real change in distribution shape, not a composition effect.

The median (Q50) declines at −0.056 pts/yr (p < 0.001), consistent with the
falling home win rate. The asymmetry — big home losses falling much faster
than the median while big home wins rise — is also consistent with the
conditional story: home teams are losing more games and, when they do, losing
by more, but still winning convincingly when they win.

### Playoffs show a different pattern

In the playoffs, the all-game margin shows no significant trend (+0.002 pts/yr,
not significant). Quantile regression confirms genuine polarization there too:
Q90 rises at +0.145 pts/yr (p = 0.010) and Q10 falls at −0.055 pts/yr (not
significant), with an IQR spread widening of +0.200 pts/yr. Playoff games are
increasingly bimodal — blowouts in both directions are more common than they
were in the 1990s, yet the net margin is unchanged.

The regular-season mean margin (+2.80 pts) is lower than the playoff mean
(+4.36 pts), consistent with the higher overall home win percentage in the
playoffs across most of the dataset.

![Figure 6. Home team point margin per season. Left: mean margin for all games (regular season and playoffs) with trend lines. Center: mean margin split by home wins vs. losses (regular season). Right: era-bucketed average margin, regular season vs. playoffs.](nba_home_court_margin.png)

---

## 5. Box-Score Differentials

Three box-score differentials (home minus away) show statistically significant
trends over time. For era-by-era averages and trend values, see `RESULTS.md`.

### Foul differential — referees are calling the game more neutrally

Home teams were called for substantially fewer fouls per game in the early era
than they are today, in both the regular season and the playoffs. This is the
single strongest mechanism. The trend is highly significant in both contexts.
Referees are calling the game more neutrally — this is likely the most important
driver of the overall decline.

### eFG% differential — the home shooting edge is shrinking

Home teams used to shoot meaningfully more efficiently than road teams (weighted
to give 3-pointers 1.5× the value of 2-pointers). That gap has narrowed
significantly in the regular season. This reflects both the foul trend (fewer
free throws for the home team) and a broader convergence in shot quality between
home and road teams.

### 3PA rate differential — shot selection has converged

Road teams used to take proportionally **more** 3-point attempts than home teams
at the same venue — consistent with being pushed away from the paint and toward
the perimeter. As the 3-point revolution normalized high-volume shooting
league-wide, that difference has not just closed but reversed slightly: home
teams now take a marginally higher share of their shots from three. Shot
selection is no longer a meaningful home court edge — road teams now arrive with
the same offensive game plan as the home team.

FG% (unweighted) is also narrowing. FT% and 3P% show no significant trend.

![Figure 7. Per-season home-minus-away box-score differentials, 1983–84 through 2024–25. Solid = regular season, dashed = playoffs. Dotted overlays are trend lines. Negative foul diff = home team called for fewer fouls.](nba_home_court_advantage_differentials.png)

---

## 6. Shot Zone Analysis

Shot zone data is available from 1996–97 onward via NBA.com's
`LeagueDashTeamShotLocations` endpoint.

Paint access (restricted area + non-RA combined) shows the clearest pattern:
home teams have historically taken a higher share of shots from the paint —
the most efficient shots in basketball — and that gap is closing. The trend line
confirms this is highly significant: **−0.037 pp/yr** (p < 0.001) in the regular
season. Road teams are accessing the paint more freely than they used to, which
is consistent with both the eFG% narrowing and the foul differential trend.

Road teams consistently take a higher share of mid-range shots — the least
efficient shot type in modern basketball. This gap is also narrowing
(**+0.024 pp/yr**, p < 0.001 in the regular season) as both home and road teams
have shifted toward the 3-point line and away from the mid-range, but road teams
have historically been pushed there more often and are now less disadvantaged.

Corner 3 and above-break 3 show no large or consistent home/road difference
throughout the dataset. Shot quality at the arc is not a meaningful home court
advantage. Above-break 3 shows a small but statistically significant positive
trend (+0.013 pp/yr, p < 0.05) in the regular season, though the effect is
minor compared to the paint and mid-range shifts.

![Figure 8. Home-minus-road shot zone % differentials, 1996–97 through 2024–25. Solid = regular season, dashed = playoffs. RA = restricted area (within ~4 ft of the basket).](nba_home_court_shot_zones.png)

---

## 7. Referee Patterns

Officials have historically called more fouls on visiting teams than on home
teams — a pattern consistent with crowd-driven influence on referee judgment.
This analysis asks whether that bias is distributed uniformly across referees or
concentrated in a subset, and whether individual referee tendencies have changed
as overall home court advantage has declined.

### Methodology

For each playoff game from 1983–84 through 2024–25 (excluding the 2020 bubble
season), officials were fetched from the NBA API (BoxScoreSummaryV3) and cached.
Each official's mean home foul differential (home fouls minus away fouls per
game) was computed across all playoff games they worked, restricted to officials
with at least 50 games. A negative value indicates the home team was called for
fewer fouls — the home-favoring direction. Era means were computed separately
for each official within each rule-change era to track whether individual biases
have shifted over time.

### Distribution of Referee Bias

Home-favoring foul bias is nearly universal: 41 of 42 officials with at least 50
playoff games show a negative career mean foul differential. The one exception —
Joe Forte (+0.451 fouls/game raw) — is the only qualifying official in the dataset
whose games tilted marginally toward the road team. The league-wide mean across
all qualifying officials is approximately −1.2 fouls per game, a substantial and
consistent tilt in the home team's favor.

The variation across individual referees is wide. The most home-favoring officials
averaged roughly 2.2–2.5 fewer fouls on the home team per game; the least
home-favoring still called fewer fouls on the home team but by only 0.1–0.6 fouls
per game. Nearly all referees show the same directional bias — they differ in
degree, not direction.

### Era Trends

The raw standard deviation of per-official era-mean foul bias declines from 2.08
in the 1995–01 era to 0.90 in 2023–25. However, a method-of-moments variance
decomposition — which subtracts sampling noise (each official's within-official
SE² / n) from the observed variance — reveals that this compression is partly a
small-sample artifact. For three of five eras (1995–01, 2018–22, and 2023–25) the
estimated true between-official SD is effectively zero: all of the observed spread
is consistent with sampling noise given the number of officials and games per
official in those eras. Only the 2005–17 era (the largest, with 42 officials and
long careers) shows clear evidence of genuine between-official variance (true
SD ≈ 0.62 fouls/game after noise correction).

The era means themselves are non-monotone (ranging from −0.781 in 2002–04 to
−1.239 in 1995–01, with the current era at −0.792), so there is no clear trend
in the average level of bias across eras. The apparent "fourfold compression" of
individual tendencies is real in the raw data but is partly sampling noise from
early eras where few officials had many games — the underlying true between-
official variance in the modern era (true SD ≈ 0.38 fouls/game career-level) is
lower than the raw spread implies but still above zero.

### Individual Referee Rankings

The top-ranked officials by home-favoring bias include Ron Garretson (−2.385 raw,
143 games), Joe Crawford (−2.288, 160 games), and Eddie Rush (−2.530, 100 games).
At the other end, Josh Tiven (−0.112 raw, 89 games) is among the most neutral;
his apparent near-zero career mean carries a p-value of 0.83 — correctly
identified as indistinguishable from zero with a realistic foul-diff SD of ~3
fouls/game. Empirical-Bayes shrinkage toward the league mean adjusts officials
with smaller samples: Tiven's shrunken estimate is −0.81 fouls/game (still well
below the top-10 threshold), reflecting that with 89 games the data can only
weakly distinguish his true level from the league average.

Of the 42 qualifying officials, **29 are individually significant at p < 0.05**
using per-game standard deviations (real t-tests replacing a previous zero-
variance implementation). All 29 also survive Benjamini–Hochberg correction
at FDR 5%, indicating the pattern is not a multiple-testing artifact. The 13
non-significant officials are those with smaller samples (51–96 games) or raw
means close to zero, not those with large negative means — confirming that the
directional signal is genuine even where the individual test lacks power.

![Figure 9. Referee home foul bias (playoffs). Left: top/bottom referees ranked by career mean home foul differential. Right: distribution of per-official era-mean foul bias by era (box plots), showing whether the spread of referee biases has narrowed over time.](nba_home_court_referee.png)

---

## 8. Rest and Schedule Balance

Rest days are computed from game logs as days between consecutive games minus one
(0 = back-to-back, 1 = one rest day, etc.). In the regular season the bucket
split is unambiguous: when the home team has more rest it wins 62.9% of the
time, versus 57.7% when the away team is more rested — a 5.2 pp swing around
the 60.3% baseline that a chi-square test confirms is highly significant
(p < 0.001).

In the playoffs, schedules are nearly always symmetric — about 92% of playoff
games are played on equal rest — so the unequal-rest buckets are small (139 and
98 games). Home teams with a rest edge win 75.5% of those games and the bucket
differences are significant (p = 0.003), though the small away-more-rest bucket
also sits above baseline, a reminder that playoff rest asymmetries arise only in
unusual series situations. The per-day regression estimate (≈ +2.3 pp per rest
day, §15) is the more reliable playoff measure, and it is larger than the
regular-season figure — higher stakes amplify the impact of fatigue.

Back-to-back rates for home and away teams have shifted substantially over time
as the league has adjusted scheduling, but the rest effect on winning has
remained stable across eras: a rest × era interaction test finds no evidence the
per-day effect has changed (p = 0.43 regular season, p = 0.75 playoffs).

![Figure 10. Regular-season rest analysis. Top: back-to-back rate per season for home and away teams. Bottom: home win % split by rest differential — home-more-rest vs equal vs away-more-rest.](nba_home_court_advantage_rest.png)

![Figure 11. Playoff rest analysis. First-round games are excluded because rest cannot be computed from a prior playoff game. Rest effects are larger in the playoffs.](nba_home_court_advantage_rest_playoffs.png)

---

## 9. Travel Distance

Away team travel distance (haversine miles from the visitor's home arena to the
game arena) is available for every game in the dataset — no new API calls required,
only the cached game logs and a coordinate lookup.

### Distance alone does not explain home court advantage

Across the four distance buckets (< 500, 500–1,000, 1,000–1,500, 1,500+ miles),
home win % shows no consistent ordering by travel burden — the buckets cluster
within ±1 percentage point of the baseline with no monotone relationship. The
bivariate logistic on continuous distance is statistically significant in the
regular season but the effect is negligible (less than 0.1 pp per 100 miles).
In the playoffs there is no significant effect at all.

This null result suggests that the coarse geographic proxy (time-zone differential)
already captures whatever travel effect exists, and that actual flight miles add no
additional predictive power. Visiting teams may also self-correct for distance by
arriving early, which erodes any mechanical disadvantage from long trips.

### Era trend is flat

There is no evidence that the travel-distance effect has grown or shrunk over the
four decades in the dataset. The era-bucketed averages show no systematic pattern.
Travel distance is not a driver of the long-run decline in home court advantage.

![Figure 12. Home win % by away team travel distance (regular season). Left: per-season home win % for each distance bucket with trend lines. Right: era-averaged home win % by distance bucket.](nba_home_court_travel.png)

---

## 10. Competitive Balance and Parity

Team-level win% disparity — measured as the per-season standard deviation of franchise
win percentages — quantifies how unequal the league is in any given year. A high
standard deviation means a few teams dominate while others lose consistently; a low
standard deviation means the field is compressed. The hypothesis was that salary-cap
and draft-lottery mechanisms have compressed team quality, leaving the home team with
less of a structural talent edge over any given road opponent.

### Parity does not explain home court advantage

The cross-season correlation between team win% disparity and home win % is near zero
and statistically non-significant. Despite decades of changes to the league's
competitive-balance mechanisms, the two series do not move together in any reliable
way. The era-bucketed pattern is mixed: win% disparity actually **peaked** in the
1995–01 era while home court advantage was already declining, then fell in 2002–04
while home win % ticked back up slightly before continuing its descent.

This rules out parity as a primary driver of the observed decline. The era coefficients
in the regression model are not explained by the compression of team talent alone.
Whatever the era effect captures — rule changes to pace and officiating, broader
cultural and travel shifts, improvements in sports science for road teams — it is not
reducible to a simple story about competitive balance.

![Figure 13. Competitive balance and home court advantage. Left: home win % (blue, left axis) and team win% std dev (red, right axis) over time — lower std dev = more equal league. Right: scatter of parity std dev vs. home win % per season, colored by era, with trend line.](nba_home_court_parity.png)

---

## 11. 3-Point Shooting and Home Court Advantage

The league-wide 3-point attempt rate — the share of all field-goal attempts that
are 3-pointers — has risen from below 10% in the mid-1980s to above 40% today.
This analysis asks whether that rise is mechanically connected to the decline in
home court advantage, or merely coincidental.

### The correlation is striking but not the whole story

At the season level, the correlation between league-wide 3PA rate and regular-season
home win % is strongly negative (Pearson r ≈ −0.90, p < 0.001). The two series
move nearly in lockstep over 40 years. In the playoffs the relationship is weaker
but still significant (r ≈ −0.47, p = 0.002), likely because playoff formats and
sample sizes add noise.

The era-bucketed table tells the same story: eras with higher 3PA rates have
lower home win percentages, with only one small inversion (1995–01 at 60.1%
vs. 2002–04 at 61.1%).

### 3PA rate predicts home win probability even within eras

The more important test is whether 3PA rate predicts home win probability at the
**game level**, controlling for era. If higher 3PA games have lower home win
probabilities even within the same rule-change era, the effect is not purely a
temporal trend — there is a real game-by-game mechanism.

In the regular season, the within-era effect survives: each 10 percentage-point
rise in a game's combined 3PA rate is associated with roughly **−2.3 pp lower home
win probability** (p < 0.001). In the playoffs, the within-era effect disappears
(p ≈ 0.10), suggesting that in the smaller playoff sample the signal is absorbed
by the era indicators.

### Why would more 3-point shooting reduce home advantage?

Three plausible mechanisms, consistent with the other analyses in this report:

- **Shot selection has equalized.** The 3PA rate differential and shot zone
  analyses show road teams no longer take a qualitatively worse shot diet than
  home teams. As both teams converge on the same high-3PA game plan, the home
  team loses a structural edge.
- **High-3PA games are higher-variance.** Three-point shooting has a wider
  per-possession outcome distribution than 2-point shooting. In higher-variance
  environments, the weaker team wins more often — which, from the home team's
  perspective, means an upset is easier for the visitor to pull off.
- **Crowd effects may matter less** when offense is driven by catch-and-shoot
  corner 3s executed by practiced routines, rather than by interior penetration
  that is sensitive to crowd pressure and referee calls.

These mechanisms are not mutually exclusive and likely all contribute. The foul
differential trend — referees calling the game more neutrally over time — is the
single strongest identified driver, and a neutral-foul environment both enables
more 3-point shooting and removes a key home advantage mechanism simultaneously.

![Figure 14. League-wide 3PA rate and home court advantage. Left: dual-axis time series showing 3PA rate (orange, right axis) and home win % (blue, left axis) moving in near-lockstep over 40 years. Center: regular-season scatter (one point per season, era-colored) with trend line. Right: same for playoffs.](nba_home_court_3pa.png)

---

## 12. Pace and Home Court Advantage

The NBA has undergone large swings in pace over the past 40 years. The
defensive-era 1990s produced some of the slowest games on record (~93-94
possessions per team per 48 min), while the 3-point revolution era has driven
pace back toward 1980s levels (~101-102). The hypothesis was that faster-paced
games would produce lower home court advantage by pushing outcomes closer to
expected value. The data do not support this.

### Season-level: no significant correlation

At the season level, the correlation between league-wide pace and regular-season
home win % is near zero and non-significant (Pearson r = +0.28, p = 0.072;
Spearman r = +0.15, p = 0.331). In the playoffs there is also no significant
relationship (r = -0.12, p = 0.474). The era table explains why: pace was
**high** in the 1984-94 era (~102 poss/48 min) when home court advantage was
also at its peak (65.0%), then **fell** during the defensive 1995-2004 era
(~93-94) while HCA also declined, then **rose again** in the modern era (~101)
while HCA continued its descent. The relationship is U-shaped across eras, not
monotone -- pace and HCA share no common trend.

### Game-level: the effect is positive, not negative

At the game level, faster-paced games have **higher** home win probability, not
lower. The bivariate logistic yields +2.37 pp per 10 extra possessions (p < 0.001
in the regular season), and the within-era logistic -- controlling for era --
actually strengthens the effect (+2.54 pp per 10 possessions, p < 0.001). In the
playoffs there is no significant game-level effect in either direction.

The most likely explanation is **game-state causality**: pace reflects what is
happening in a game as much as it determines it. When the home team is winning
and running off turnovers and makes, the game moves faster. Pace is partly an
*outcome* of home court advantage rather than a cause of it, which reverses the
apparent direction of the relationship.

### Pace does not explain the decline

Pace was approximately as high in 1984-94 as it is today, yet home court
advantage in those early seasons was ~10 pp higher. Whatever is driving the
long-run decline, it is not the number of possessions per game. The secular
decline runs through eras of both fast and slow play without pace tracking it.

![Figure 15. League-wide pace (possessions per 48 min) and home court advantage. Left: dual-axis time series showing pace (purple, right axis) and home win % (blue, left axis) over time, era-shaded. Center: regular-season scatter (one point per season, era-colored) with trend line. Right: same for playoffs.](nba_home_court_pace.png)

---

## 13. Playoff Series Structure

Playoff game IDs encode the game number within each series (last digit of GAME_ID),
allowing home win % to be tracked across G1–G7 pooled over all seasons.

### Higher-seed home games dominate; the alternating pattern is striking

The data reveals a sharp alternating structure. Higher-seed home games (G1, G2, G5)
see home win percentages of roughly 69–75%, while lower-seed home games (G3, G4, G6)
cluster tightly at 55–56% — barely above even. The G3/G4/G6 figure is only modestly
above 50% and reflects that the lower seed's home advantage is almost completely
offset by the quality gap between the opponents.

A chi-square test strongly rejects uniform home win % across game numbers
(χ²(6) = 80.40, p < 0.001). The variation is not random — it is structurally
determined by which team is at home, not by series pressure or fatigue effects.

### G7 is notably lower than G1/G2

Game 7 — the highest-stakes home game in sports — shows a win % of approximately
65%, meaningfully below G1 (69%) and G2 (72%). The small G7 sample (183 games)
limits inference, but the gap is consistent with the idea that opponent quality is
highest in games 7 (only the best road teams force a Game 7), partly offsetting the
home court advantage.

There is no significant linear trend across game numbers — the pattern is not a
simple "home advantage fades as the series gets deeper." The dominant structure is
the alternating host pattern, not a narrative about pressure or momentum.

### Implications for the overall decline

The strong G3/G4/G6 separation means that changes in which team hosts which games
(format changes in 1985, 2003, 2014) can mechanically affect the aggregate playoff
home win %. The 2014 shift to 2-2-1-1-1 gave the lower seed more favorable hosting
in round 1 and Finals matchups, which would compress the overall playoff home win %
figure. In practice, however, the trend-controlled test in §2 cannot statistically
separate any such format effect from the secular decline that runs through the
same years.

![Figure 16. Home win % by game number within playoff series. Left: pooled G1–G7 home win % with sample sizes and overall playoff baseline. Right: G1–G7 home win % split by era (six lines, era-colored).](nba_home_court_series_breakdown.png)

---

## 14. Franchise Home Court Advantage

Home court advantage is not equally distributed across franchises. Some arenas
have historically conferred a large and consistent home edge; others have
provided little beyond what team quality alone predicts. This analysis measures
per-franchise HCA as home win% minus road win% — a metric that controls for
overall team quality, since a dominant team like the 1990s Bulls wins at home
and on the road; what distinguishes a strong home court is the *gap* between
the two.

### Regular Season

Across 39 franchises with at least 50 home games in the dataset, the league
mean HCA is **+20.2 pp** (range: +9.6 to +35.4 pp). Every franchise shows a
positive HCA — no team in the dataset has historically been better on the road
than at home over a meaningful sample.

The altitude franchises dominate the top of the table. Denver ranks **#2 at
+28.5 pp** and Utah ranks **#3 at +26.8 pp** — both well above the league
mean and consistent with the altitude effect identified in §15. Portland (+23.2
pp) and Seattle (+25.6 pp) also rank near the top, suggesting that arenas in
the Pacific Northwest carry a structural advantage beyond just team quality.
Indiana, Atlanta, and Cleveland also appear in the top tier.

At the lower end sit franchises with shorter histories in the dataset or those
that have played in more neutral metropolitan markets. The Brooklyn Nets (+9.6
pp) and LA Clippers (+11.8 pp) show the smallest regular-season home advantages
among franchises with substantial samples — both play in large markets where
opposing fan sections are often well represented at road games. The Kansas City
Kings post the highest number (+35.4 pp) but with only 82 games (one season,
1983–84), so that figure is too small a sample to treat as reliable.

### Playoffs

The playoff table covers 32 franchises with at least 20 home playoff games.
The league mean HCA in the playoffs is **+27.1 pp** — notably higher than the
regular-season mean. This is not a contradiction of the lower overall playoff
home win%: here, each franchise's home record is compared to that same
franchise's *road* record in the playoffs, and in postseason play, the home
team is almost always a comparable or superior opponent than the road team
faces, amplifying the venue effect relative to the regular season.

Utah leads the playoff table at **+39.7 pp**, followed by Portland (+39.3 pp)
and Seattle (+37.7 pp). The Los Angeles Lakers (+31.7 pp) and Boston (+30.2
pp) — two of the most storied franchises — also rank highly, consistent with
their sustained success and strong home environments over decades.

The LA Clippers post the only **negative playoff HCA** in the dataset (−3.6
pp, 28 home games) — the one franchise where home court appears to have
provided no benefit, though the sample is too small to draw strong conclusions.

### Regular Season vs. Playoffs Consistency

The scatter of regular-season HCA versus playoff HCA shows a modest positive
relationship (Pearson r = +0.36, p = 0.045): franchises that protect home court
in the regular season tend to do so in the playoffs as well, though the
correlation is weak — by rank it is not significant (Spearman ρ = +0.26,
p = 0.15) — because playoff samples per franchise are small. The playoff HCAs
are uniformly larger (the mean playoff HCA exceeds the regular-season figure by
+7.2 pp across shared franchises) and more dispersed, reflecting both the
higher-stakes environment and the smaller sample sizes. Portland, Seattle, and Atlanta — already near the top
of the regular-season table — rank even higher in the playoffs, while others
like the New Jersey Nets show notably weaker playoff home advantages than
their regular-season figures might suggest.

![Figure 17. Franchise home court advantage. Left: horizontal bar chart of regular-season HCA by franchise, sorted from largest to smallest, across all seasons. Right: scatter of regular-season HCA vs. playoff HCA (one point per franchise with sufficient data); y=x diagonal shows where the two are equal.](nba_home_court_team_hca.png)

---

## 15. What Explains the Decline?

A game-level logistic regression (outcome: home win) with era indicators, rest
differential, altitude, time-zone differential, and a COVID flag decomposes the
decline into measurable factors. Full tables are in `RESULTS.md`.

### Era dominates the model fit

The era indicators account for roughly half of total model fit. The structural
multi-decade decline is not explained by rest, altitude, or travel — it spans
every rule-change era and those factors add only incremental explanatory power
on top of it.

The sequential decomposition (entering era first) assigns era 56% and
the remaining factors 44% combined. Because the sequential share depends on
entry order, we also computed Shapley R² shares, which average each block's
marginal contribution over all possible orderings. Era's Shapley share is
**50%** (vs. 56% sequential — sequential is inflated because era is entered
first and absorbs shared variance with rest and COVID). Altitude's Shapley share
is **26%**, rest **18%**, COVID **5%**, and time zone **2%**. The Shapley shares
are reported in the summary table below; the sequential table is retained in
`RESULTS.md` as a labeled cross-check.

### Rest, altitude, and time zone

**Rest** matters in both the regular season and the playoffs. The per-day effect
is larger in the playoffs than in the regular season — higher stakes amplify
fatigue. When the home team has more rest than the road team, the home win
probability rises; the reverse is also true.

**Altitude** at Denver and Utah carries a significant home edge in the regular
season but the effect disappears in the playoffs. Team quality is a confound:
when those franchises are strong enough to host playoff games, their opponents
are also strong, masking the altitude effect.

**Time zone differences** show no significant effect in the playoffs. In the
regular season, the effect is not significant in isolation (bivariate p = 0.085)
but becomes significant when controlling for era, rest, and altitude (p = 0.012,
−0.6 pp per time zone). The effect is real but small, and only emerges once the
larger era and altitude effects are accounted for. There are too few coast-to-coast
playoff matchups across 42 seasons for reliable playoff inference.

### Pre/post-2014 level shift

Splitting the sample at the 2014 Finals format change confirms a real drop in the
overall home-win probability after 2014. Coefficients on rest and time zone are
stable across the split; the altitude coefficient shrinks (+0.39 → +0.25
log-odds) but remains positive. None of these factors drove the post-2014
decline — the drop shows up in the intercept (−4.7 pp), not in the covariates.

---

## 16. Summary

Home court advantage has declined substantially in both the regular season and
the playoffs over the past 40 years, with the regular-season decline somewhat
steeper than the playoffs. The decline is structural — it spans every rule-change era and
the era effect accounts for the majority of variance explained by the regression
model. The mechanisms are summarized in the tables below, split by type of analysis.

*How to read these tables: "pp" means percentage points — a fall from 65% to
55% is a drop of 10 pp. The "Evidence" column translates each effect's p-value:
a small p-value (below 0.05) means the effect is very unlikely to be a chance
fluctuation; a large one means no reliable effect was found.*

**Regular season — what the prediction model credits** (share of the model's
explained variation):

Shares are Shapley R² — each block's average marginal McFadden R² over all possible entry orderings (32 logit fits, N = 47,215 games). The sequential share (era entered first) is shown in parentheses for reference.

| Factor | Share (Shapley) | Effect | Evidence |
|---|---|---|---|
| Era (structural decline) | 50% (seq: 56%) | Home advantage is 8.9 pp lower in 2023–25 than in 1984–94 | Very strong (p < 0.001) |
| Altitude (Denver / Utah) | 26% (seq: 25%) | +8.2 pp extra home advantage at altitude | Very strong (p < 0.001) |
| Rest differential | 18% (seq: 16%) | +1.5 pp per extra day of rest vs. the visitor | Very strong (p < 0.001) |
| COVID flag | 5% (seq: 1%) | Lower home win % in bubble and COVID seasons | Very strong (p < 0.001) |
| Time-zone differential | 2% (seq: 2%) | −0.6 pp per time zone the visitor crosses | Solid (p = 0.012) |

**Regular season — mechanisms behind the decline**:

| Factor | What changed | Evidence |
|---|---|---|
| Referee fouls (refs more neutral) | Home teams' foul advantage shrank from 1.2 fewer fouls/game in 1984–94 to 0.2 today | Very strong (p < 0.001) |
| Shot quality (shooting + paint access) | Home shooting-efficiency edge fell from +1.6 pp to +1.0 pp; home paint-access edge fell from +1.3 pp to +0.4 pp | Very strong (p < 0.001) |
| League-wide 3-point shooting | Seasons with more 3-point shooting have lower home win % (correlation −0.90); even within an era, higher-3PA games favor the visitor (−2.3 pp per 10 pp of 3PA rate) | Very strong (p < 0.001) |
| Travel distance | Longer trips barely hurt the visitor: −0.08 pp per 100 miles | Real but negligible (p = 0.024) |
| Competitive balance / parity | League parity does not track home advantage at all | None — likely chance (p = 0.68) |

**Playoffs — what the prediction model credits**:

| Factor | Effect | Evidence |
|---|---|---|
| Era (structural decline) | Every era since 1984–94 has lower home advantage | Very strong (p < 0.001) |
| Rest differential | +2.3 pp per extra day of rest — larger than in the regular season | Solid (p = 0.014) |
| Altitude (Denver / Utah) | No altitude edge in the playoffs (−1.8 pp) | None — likely chance (p = 0.59) |
| Time-zone / distance | No meaningful effect of either | None (p = 0.28 and p = 0.77) |

**Playoffs — mechanisms behind the decline**:

| Factor | What changed | Evidence |
|---|---|---|
| Referee fouls (refs more neutral) | Home teams' foul advantage shrank from 1.6 fewer fouls/game in 1984–94 to 0.7 today | Strong (p < 0.01) |
| League-wide 3-point shooting | Playoff seasons with more 3-point shooting have lower home win % (correlation −0.47) | Strong season-level (p = 0.002); weak within era (p = 0.097) |
| Shot quality (shooting + paint access) | Both edges trend downward, but the playoff sample is too small to be sure | Not significant |

The core story: the decline is primarily **structural** — controlling for which
rule-change era a game was played in accounts for the majority of explained
variance, meaning the forces driving the decline operate through long-run shifts
in how the game is played and officiated, not through any single identifiable
event. Within that structural decline, the strongest identified mechanisms are
that **referees call the game more neutrally** than they did 40 years ago,
**home teams no longer generate a disproportionate paint-access or shooting
edge**, and **the 3-point revolution has equalized shot selection** between home
and road teams. Rest remains a meaningful factor — particularly in the playoffs —
but cannot explain the secular decline. Altitude at Denver and Utah confers a
real regular-season edge but is absent in the playoffs. Time-zone differential
has a small but significant effect in the regular season once era and altitude
are controlled for, but no detectable effect in the playoffs.

For specific coefficient values, effect sizes, significance levels, and era
breakdowns, see `RESULTS.md`.
