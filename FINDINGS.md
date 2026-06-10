# NBA Home Court Advantage — Findings

Narrative interpretation of the analysis. This file drives the PDF report —
update here and regenerate the PDF to keep them in sync. For regression tables
and coefficient values, see `RESULTS.md` (auto-generated each run).

---

## 1. The Decline

Home court advantage has been falling for 40 years in both the regular season
and the playoffs, with the playoff decline steeper than the regular-season one.
The gap between the two has nearly closed in recent seasons.

The 2020 bubble season (neutral-site playoffs) is excluded from playoff stats.
COVID seasons are flagged in the charts and regression as an anomaly.

---

## 2. Era and Format Period Analysis

The NBA has gone through six distinct rule-change eras since 1984, each affecting
pace, defense, and officiating. Home court advantage has declined in nearly every
successive era in both the regular season and the playoffs, with the steepest
drops in the most recent eras.

The playoff-format analysis divides the dataset into four periods defined by the
1985, 2003, and 2014 Finals scheduling changes. The 2014 shift from a 2-3-2 to a
2-2-1-1-1 series structure coincided with a sharp fall in playoff home win
percentage. Isolating format effects from the broader secular trend is difficult,
but the pattern is consistent across both framings.

---

## 3. Per-Era Trend Lines

Fitting a separate trend line within each era reveals that the decline is not a
smooth drift — there are periods of relative stability and periods of sharper
change. Playoff home court advantage has consistently exceeded the regular-season
figure but has converged dramatically in recent years.

---

## 4. What Explains the Decline?

A game-level logistic regression (outcome: home win) with era dummies, rest
differential, altitude, time-zone differential, and a COVID flag decomposes the
decline into measurable factors. Full tables are in `RESULTS.md`.

### Era dominates the model fit

The era dummies account for the majority of total model fit. The structural
multi-decade decline is not explained by rest, altitude, or travel — it spans
every rule-change era and those factors add only incremental explanatory power
on top of it.

### Rest, altitude, and time zone

**Rest** matters in both the regular season and the playoffs. The per-day effect
is larger in the playoffs than in the regular season — higher stakes amplify
fatigue. When the home team has more rest than the road team, the home win
probability rises; the reverse is also true.

**Altitude** at Denver and Utah carries a significant home edge in the regular
season but the effect disappears in the playoffs. Team quality is a confound:
when those franchises are strong enough to host playoff games, their opponents
are also strong, masking the altitude effect.

**Time zone differences** show no statistically significant effect in either
context. There are too few coast-to-coast playoff matchups across 42 seasons for
reliable inference, and the regular-season effect is also not significant.

### Pre/post-2014 level shift

Splitting the sample at the 2014 Finals format change confirms a real drop in the
overall home-win probability after 2014. Coefficients on rest, altitude, and time
zone are broadly stable across the split — those factors did not drive the
post-2014 decline.

---

## 5. Rest and Schedule Balance

Rest days are computed from game logs as days between consecutive games minus one
(0 = back-to-back, 1 = one rest day, etc.). When the home team has more rest than
the road team the advantage is larger; when the away team is more rested the
advantage shrinks significantly.

The effect is larger in the playoffs than in the regular season — higher stakes
amplify the impact of fatigue. Back-to-back rates for home and away teams have
shifted over time as the league has adjusted scheduling, but the rest differential
effect on winning has remained stable across eras.

---

## 6. Box-Score Differentials

Three box-score differentials (home minus away) show statistically significant
trends over time. For era-by-era averages and OLS trend values, see `RESULTS.md`.

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

Road teams used to take proportionally fewer 3-point attempts than home teams at
the same venue. As the 3-point revolution normalized high-volume shooting
league-wide, that difference has closed completely. Shot selection is no longer a
meaningful home court edge — road teams now arrive with the same offensive game
plan as the home team.

FG% (unweighted) is also narrowing. FT% and 3P% show no significant trend.

---

## 7. Shot Zone Analysis

Shot zone data is available from 1996–97 onward via NBA.com's
`LeagueDashTeamShotLocations` endpoint.

Paint access (restricted area + non-RA combined) shows the clearest pattern:
home teams have historically taken a higher share of shots from the paint —
the most efficient shots in basketball — and that gap is closing. This is
consistent with both the eFG% narrowing and the foul differential trend: road
teams are accessing the paint more freely than they used to.

Road teams consistently take a higher share of mid-range shots — the least
efficient shot type in modern basketball. This gap has been relatively stable,
suggesting that even as the paint advantage closes, road teams are still being
pushed away from the basket more often.

Corner 3 and above-break 3 show no systematic home/road difference throughout
the dataset. Shot quality at the arc is not a home court advantage.

---

## 9. Playoff Series Structure

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
(format changes in 1985, 2003, 2014) materially affect the aggregate playoff home
win %. The 2014 shift to 2-2-1-1-1 gave the lower seed more favorable hosting
in round 1 and Finals matchups, which mechanically compressed the overall playoff
home win % figure — an effect that overlaps with but cannot fully explain the
broader secular decline seen in the era analysis.

---

## 10. Win Margin Trends

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

This rules out one intuitive explanation for the win-rate decline — that games
at home are simply becoming more competitive and flipping the coin. Instead,
the pattern is more polarized: when the home team is good enough to win, they
win convincingly; but they drop more games outright.

### Playoffs show a different pattern

In the playoffs, the all-game margin shows no significant trend (+0.002 pts/yr,
not significant). But like the regular season, both win margins (+0.152 pts/yr,
p < 0.001) and loss margins (−0.076 pts/yr, p < 0.05) are growing in magnitude.
Playoff games are increasingly bimodal — blowouts in both directions are more
common than they were in the 1990s, yet the net margin is unchanged.

The regular-season mean margin (+2.80 pts) is lower than the playoff mean
(+4.36 pts), consistent with the higher overall home win percentage in the
playoffs across most of the dataset.

---

## 11. Competitive Balance and Parity

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

---

## 12. Travel Distance

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

---

## 8. Summary

Home court advantage has declined substantially in both the regular season and
the playoffs over the past 40 years, with the playoff decline steeper than the
regular season. The decline is structural — it spans every rule-change era and
the era effect accounts for the majority of variance explained by the regression
model. The mechanisms, in order of statistical strength, are listed in the table
below.

The core story: home court advantage has eroded because **referees call the game
more neutrally** than they did 40 years ago, **home teams no longer generate a
disproportionate paint-access or shooting edge**, and **the 3-point revolution
has equalized shot selection** between home and road teams. Rest remains a
meaningful factor — particularly in the playoffs — but cannot explain the secular
decline. Altitude at Denver and Utah confers a real regular-season edge but is
absent in the playoffs. Time-zone travel shows no statistically reliable effect.

For specific coefficient values, effect sizes, significance levels, and era
breakdowns, see `RESULTS.md`.
