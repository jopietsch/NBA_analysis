# Statistical Explainer — `knicks_2026_analysis.py`

A guide to every analysis that produces output in `RESULTS.md`: the data it uses,
the statistical approach, why that approach was chosen, what the results mean, and —
where a section has one — **why its figure takes the form it does**. Sections appear
in the same order as `RESULTS.md`. The figures themselves are embedded in `knicks_2026_historic_FINDINGS.md`;
here we only explain the reasoning behind each choice. Unlike `knicks_2026_historic_FINDINGS.md`, this
document uses statistical terminology freely — it is the methods companion, not the
narrative report.

---

## 0. The Comparison Dataset (`build_champions_table`, `build_conference_gap_table`)

**The data.** Every comparison (Sections 1, 4, 5, 6) runs against one of two
tables built by looping over all 43 NBA seasons from 1983–84 through 2025–26:

Note that the 2025-26 Knicks won the title (`identify_champion` returns the
Knicks for 2026), so they are themselves one of the 43 rows. Every percentile in
the report ranks the Knicks against a set that *includes their own season* — the
count and the denominator both contain them. This is why a "100th percentile /
1st of 43" reads as "no other champion did better," not "better than 43 other
teams."

`build_champions_table` produces one row per season with:

- `year` — the season's end year (e.g. 2026 for 2025–26)
- `champion_id` — the team with the most playoff wins (`identify_champion`, which
  counts wins from the playoff game-log cache; ties broken by the team with the
  highest win count in the regular season)
- `wins`, `losses`, `win_rate` — the champion's playoff record
- `avg_margin` — mean per-game point differential, with PLUS_MINUS filled from
  PTS for pre-1997 seasons (see §Pre-1997 note below)
- `avg_opp_srs` — games-weighted average regular-season SRS of playoff opponents
  (each game counts once; a 5-game Finals opponent has 5× the weight of a
  4-game sweep opponent, matching the per-game basis of `avg_margin`)
- `adj_margin` — `avg_margin − avg_opp_srs`
- `champion_reg_srs` — the champion's own regular-season SRS
- `overperformance` — `avg_margin − champion_reg_srs + avg_opp_srs`; equivalently,
  mean per-game residual (actual − expected) where expected = champion_SRS − opp_SRS
- `clutch_rate` — fraction of games decided by ≤5 points
- `home_wr`, `away_wr` — home and away win rates

`build_conference_gap_table` produces one row per season with:

- `east_srs`, `west_srs` — mean regular-season SRS across all teams in each
  conference
- `srs_gap` — `west_srs − east_srs` (positive = West stronger)
- `east_h2h_wr` — East win rate in games played cross-conference

**Why loop from cache, not from the API.** All CSVs were pre-fetched once by
`fetch_data.py` and stored in `nba_analysis/cache/`. The loop reads from disk
only. This makes the analysis fully reproducible offline and fast enough to
re-run in under a minute.

**Pre-1997 PLUS_MINUS.** The NBA.com API (`LeagueGameFinder`) returns null
PLUS_MINUS for seasons before 1997. The helper `_fill_plus_minus` (in
`nbakit/data.py`) fills these from `PTS`: for each `GAME_ID`, the two rows are
swapped to give each team the opponent's score, and `PLUS_MINUS = PTS − OPP_PTS`
is computed exactly. This is algebraically exact for game margins. Without this
fix, 13 of 43 seasons would have NaN margins and could not appear in the
percentile comparisons.

---

## 1. The Raw Claim (`run_raw_claim`)

**The data.** The Knicks' 2025–26 playoff game log (from cache) and the
`champions` table spanning 43 seasons.

**The approach.** Two metrics — win rate and average margin — are computed for
the Knicks and each is fed to `_pct_rank`:

```
_pct_rank(series, value, ascending=True)
    → (series ≤ value).mean() × 100
```

This is the **empirical percentile rank**: the fraction of 43 champions whose
value is at or below the Knicks' value, expressed as a percentage. The
`ascending=True` convention means higher values are better (a value at the 95th
percentile is better than 95% of champions).

No distributional assumptions are made — only counting. With 43 data points, the
finest percentile resolution is 1/43 ≈ 2.3 pp; exact ties are counted as "≤",
so achieving the best historical value yields 100th percentile.

**What the results mean.** Win rate 0.842 sits at the 88th percentile (better
than 38 of 43 champions; best ever is the 2016–17 Warriors at 0.941). Average
margin +14.9 pts/game is the 100th percentile — the highest ever recorded in the
dataset. The margin claim is the strongest of the two raw numbers.

**Why these two charts.** Both are horizontal bar charts of all 43 champions
ranked from lowest to highest on the metric, with the Knicks bar highlighted in
blue. A ranked bar chart answers two questions simultaneously: "where does this
team rank?" (bar position) and "how unusual is the gap from the next-best?"
(spacing). Horizontal orientation keeps the 43 season labels readable. Vertical
wouldn't — 43 narrow columns of year labels would overlap. The Knicks bar is
labeled with the value; the chart is the main visual for the report's §2 "The
Raw Numbers."

---

## 2. Conference Context — 2025-26 (`run_east_weakness`)

**The data.** 2025–26 regular-season game logs and standings (one row per team
with `TeamID`, `Conference`, `TeamCity`, `TeamName`).

**The approach.** Three computations using that season's data only:

1. `compute_srs(reg_2026)` — returns a `pd.Series` indexed by TEAM_ID with each
   team's regular-season SRS (see §SRS in the Recurring Methods section).
2. `compute_conference_avg_srs(srs, standings)` — maps each TEAM_ID to its
   conference and takes the unweighted mean of SRS within East and West.
3. `compute_inter_conference_h2h(reg_logs, standings)` — iterates every game in
   the regular-season log, identifies games between an East and a West team (using
   the standings `Conference` column), and counts East wins divided by total
   cross-conference games. Each game contributes one East-win or one West-win.

Additionally, `compute_opponent_srs(po_2026, srs_2026, KNICKS_TEAM_ID)` is used
here to show the Knicks' specific opponents and their SRS values. It finds every
unique opponent TEAM_ID by inspecting the two-row-per-GAME_ID structure of the
playoff logs: for each game, all team IDs except `KNICKS_TEAM_ID` are collected,
then each opponent's SRS is looked up from the regular-season series.

**What the results mean.** The East SRS average was −0.20 pts/game vs. West
+0.20 (gap +0.39). The inter-conference win rate was 0.487 — very close to parity.
The Knicks' opponents had SRS values from −0.27 (76ers) to +8.28 (Spurs).

**Why this chart (team SRS bar).** The team SRS bar chart — all 30 teams on one
axis, East bars in green, West in blue — is the direct visualization of the
conference-averages computation. The eye instantly compares the two conference
clouds. An alternative (two box plots, one per conference) would show distributions
better but would obscure where specific opponents (the Spurs, Cavaliers) sit.
Because the Knicks' opponents are all identified by name in the text, the
full-team bar chart gives context for where each one sits relative to all 30 teams.

---

## 3. Historical Conference Gap (`run_gap_history`)

**The data.** The `gap_table` (43 seasons × 5 columns).

**The approach.** Two layers of analysis:

1. `_pct_rank` against the 43-season `srs_gap` series (100th = most West-dominant).
2. Z-score and 95% confidence interval:
   - Z = (gap_2026 − mean_gap) / std_gap; tells how many standard deviations from
     the historical average this season's gap is.
   - 95% CI on the mean gap (t-distribution with df = n-1): shows the range of
     plausible "true average" West-East gaps given 43 observations.

The `scipy.stats.t.ppf(0.975, df=42)` critical value is used for the CI half-width:
`ci_half = t * std / sqrt(n)`.

Three "most West-dominant" and three "most East-dominant" seasons are also
reported as concrete anchors.

**What the results mean.** Z = −0.21: the 2025–26 gap (+0.39) is only 0.21
standard deviations below the historical mean gap (+0.78). This is well within
normal variation (|z| < 1), formally confirming the percentile-based conclusion.
The historical mean of the gap is +0.78 — the West has typically been stronger
than the East — but 2025–26 was slightly below that average (more East-competitive
than normal), though not significantly so. The "easy conference" narrative is
ruled out not just by ranking (37th percentile) but by formal significance testing.

**Why this chart (conference gap line).** The conference gap is a time series —
43 data points, one per season — so a line is the natural form. It shows the gap
oscillating over time rather than trending, which is the important visual point.
A bar chart could work (one bar per season, positive = West dominant) but would
look cluttered with 43 bars. The shading above/below zero makes East vs. West
dominance immediately readable. The 2025–26 dot and annotation show exactly
where the subject season falls on that multi-decade chart.

---

## 4. Opponent Quality (`run_opponent_quality`)

**The data.** 2025–26 playoff logs, 2025–26 regular-season SRS, and the
`champions` table.

**The approach.** `compute_avg_opponent_srs(po_2026, srs_2026, KNICKS_TEAM_ID)`
finds all unique opponents (by GAME_ID inspection, as in §2) and averages their
regular-season SRS values. That single number (+3.54) is then ranked via
`_pct_rank` against `champions["avg_opp_srs"]` — the same metric for all 43
champions.

**Why regular-season SRS for opponents, not playoff SRS.** Playoff SRS could be
computed, but it would be circular: a team's playoff SRS reflects partly who they
faced, which again includes the Knicks. Regular-season SRS measures each
opponent's strength on an independent baseline (all 82 games before the playoffs
began), making it a cleaner gauge of how hard the Knicks' draw was.

**Why games-weighted, not unique-opponent average.** `avg_opp_srs` is computed
as a per-game average across all playoff games (each game contributes one opponent
SRS data point), not as a simple average of four unique opponents.  This matches
the basis of `avg_margin`, which is also a per-game average.  When the same
formula `adj_margin = avg_margin − avg_opp_srs` is applied, both sides are
expressed on the same per-game scale, making the subtraction internally consistent:
"how dominant per game after accounting for per-game opponent quality?"  A unique-
opponent average could give equal weight to a 4-game first-round opponent and a
7-game Finals opponent, which would misstate the actual per-game opponent quality
experienced.

**What the results mean.** Games-weighted average opponent SRS +3.67 sits at the
49th percentile among 43 champions — right at the historical median. The schedule
was not unusually easy or hard. Champions who faced the weakest opponents
(2022–23 Nuggets +0.62, 1986–87 Lakers +1.32) faced average SRS values more than
2 pts/game below the Knicks'.

**Why two charts here.** The opponent-SRS ranking bar (all 43 champions) and the
opponent-by-round bar (four Knicks opponents) answer different questions. The
ranking says "relative to history, was the schedule hard?" The round-by-round bar
says "which specific opponents were strong and which were weak?" — it shows that
the Spurs (+8.28) in the Finals were elite while the 76ers (−0.27) in the second
round were below average. A reader needs both to understand the Knicks' path.

---

## 5. Opponent-Adjusted Dominance (`run_adjusted_dominance`)

**The data.** 2025–26 playoff logs, regular-season SRS, and the `champions` table.

**The approach.** A two-step analysis: adjusted margin (opponent quality) plus
overperformance (playoff elevation relative to own regular-season baseline).

*Adjusted margin:*
```
adj_margin = raw_margin − avg_opp_srs
```
where `avg_opp_srs` is games-weighted (see §4).  This is a direct additive
correction asking: "how dominant would this team look if they had faced average-SRS
opponents?"  The assumption — one SRS point of opponent quality = one margin point
— is natural because the SRS system is defined in point-differential space.

*Overperformance (playoff elevation):*
```
overperformance = mean(actual_margin_per_game − expected_margin_per_game)
                = raw_margin − champion_SRS + games_weighted_opp_srs
                = adj_margin − champion_SRS
```
where expected_margin_per_game = champion_SRS − opp_SRS_for_that_game.  This
measures how much better a champion performed than a team of their regular-season
quality was expected to perform against those opponents.  Positive = elevated in
playoffs; negative = underperformed.

Both values are ranked via `_pct_rank` against the `champions` table.

**Why this specific adjustment.** The SRS system is built around the identity
that a team with SRS +X is expected to outscore a 0-SRS opponent by X points per
game. Subtracting the games-weighted average opponent SRS "returns" the champion
to a neutral-schedule baseline. The overperformance metric additionally subtracts
the champion's own regular-season SRS, capturing "playoff elevation" — the amount
by which the champion exceeded what their regular-season quality predicted.

**Limitations.** The adjustment assumes opponents' regular-season SRS accurately
reflects playoff-mode strength; it doesn't account for injuries, resting veterans,
or playoff-specific preparation. A more elaborate model could regress playoff
margin on opponent SRS across all champions, but with 43 data points and one
adjustment variable, the direct subtraction and its ranking are the right level
of complexity.

**What the results mean.** Adjusted margin +11.2 is the 100th percentile of 43
champions — the highest ever even after correcting for schedule difficulty. The
comparison with 2016–17 Golden State (+10.2) and 1986–87 Los Angeles Lakers
(+9.5) provides the natural peer group for "all-time dominant playoff runs."
The overperformance metric (+12.5 pts/game, 97.7th percentile) is notably
different from adjusted margin: the 2016–17 Warriors, who had a much higher
regular-season SRS (~+10), rank lower on overperformance because they
*expected* to dominate. The Knicks elevated more relative to their regular-season
baseline. The 2000–01 Lakers rank 1st (+14.5) on overperformance — they had a
strong but not historically dominant regular season and then absolutely dominated
the playoffs.

**Why this is the headline chart.** The adjusted margin ranking is the single
number that answers the central question — "historically dominant?" — most fully.
Win rate alone doesn't account for the quality of opponents; raw margin doesn't
either. Adjusted margin does both. The bar chart annotates the Knicks' position
explicitly with the value (+11.4) and the legend says "#1 of 43." It is the chart
that tells the whole story in one panel.

---

## 6. Other Deflators (`run_deflators`)


**The data.** 2025–26 Knicks playoff game logs and the `champions` table.

**The approach.** Three "deflator" checks that could reduce the historicity claim,
each ranked against champions:

**Clutch rate.** `compute_clutch_rate(po_2026, KNICKS_TEAM_ID)` takes the mean of
`(|PLUS_MINUS| ≤ 5)` across the Knicks' 19 games. This is the fraction of games
decided by 5 points or fewer. A low clutch rate (lots of blowouts) inflates the
raw margin number; a high rate means the dominance was built on close wins.
`_pct_rank` with `ascending=True` is used here: a team that wins many close games
("clutch" in the common sense) scores higher than one that blows teams out.

**Home/away split.** `compute_home_away_split` uses the `MATCHUP` string to split
home games (`"vs."` in matchup) from road games (`"@"` in matchup). Win rates
are computed separately. These are ranked against `champions["home_wr"]` and
`champions["away_wr"]` via `_pct_rank`. The away win rate is the more meaningful
deflator check: a champion who only wins at home is more fragile than one who
dominates on the road.

**Round-by-round breakdown.** Rather than a statistical test, this is a
descriptive accounting: for each unique opponent (grouped from the playoff log by
`OPP_ID`, which is derived by finding the non-Knicks TEAM_ID in each GAME_ID),
the series wins, losses, and mean `PLUS_MINUS` are printed in chronological order.
This shows *where* the margins came from — the sweeps inflated the headline number
while the Finals were contested.

**What the results mean.** Clutch rate 31.6% is the 84th percentile — the Knicks
played *more* close games than most champions, not fewer. The blowout narrative
(the margins were "just garbage time") is unsupported: they also won tight games
at an above-average rate. Away win rate 90.0% is the 98th percentile — only one
other champion in 43 years won road games at a higher clip. Home win rate 77.8%
is the 23rd percentile, so the Knicks were an unusual champion: dominant on the
road, relatively ordinary at home.

**Why this chart (game margins).** The 19-game bar chart — one bar per game in
chronological order, blue for wins, red for losses, with the average overlaid —
shows both the blowouts (tall blue bars in rounds 2 and 3) and the close games
(annotated small-margin games near the zero line). A histogram of margins would
show the distribution but would hide the chronological narrative (that the
margins were tightest in the Finals). The bar-per-game form preserves the "film"
of the run.

---

## 7. Playoff SRS and Elevation (`run_playoff_srs`)

**The data.** 2025–26 playoff and regular-season game logs; the `champions` table
(which now includes `champion_po_srs` and `playoff_elevation`).

**The approach.** `compute_playoff_srs` applies `compute_srs` to the playoff game
log only.  The SRS algorithm (see Recurring Methods) solves the same
`(I − A) @ srs = mean_margin_vector` system from the playoff bracket graph.
Because the bracket is sparser than the regular season (not every team plays
every other team), the solution is a least-squares approximation — the same
`numpy.linalg.lstsq` call handles this naturally.

*Elevation* = playoff_SRS − regular_season_SRS.  A positive value means the
champion performed at a higher level in the playoffs than their 82-game baseline
predicted.  Both playoff and regular-season SRS are expressed in points per game
in the same season's scoring environment, so the difference is directly
interpretable.

`playoff_elevation` is added as a column in `build_champions_table` for each of
the 43 champion seasons.

**What the results mean.**
- Knicks regular-season SRS: +6.05 — a strong team, but not historically dominant.
- Knicks playoff SRS: +17.53 — among the highest playoff SRS values ever.
- Elevation: +11.48, 97.7th percentile (2nd all-time, behind 2000–01 Lakers +12.58).
- The 2016–17 Warriors — the most dominant regular-season team (+11.35 SRS) —
  had a lower elevation (+8.83) because their regular-season baseline was so high.
- The mean elevation across 43 champions is +4.43, confirming that playoff
  performance typically outpaces regular-season baselines (home-court advantage,
  higher effort, bracket-specific preparation).

**Why this metric.** Playoff SRS elevation directly answers whether a team
"showed up" in the playoffs or merely coasted on regular-season talent. It
complements the overperformance metric (Gap 1) and is independently derived —
if both metrics agree, the conclusion is robust. They do agree: the Knicks are
2nd all-time on both, and the 2000–01 Lakers rank 1st on both.

---

## 8. Era/Pace Adjustment (`run_pace_era`)

**The data.** The `champions` table (which now includes `league_scoring` — the
average pts per team per game in each season's regular season) and the 2025–26
regular-season game logs.

**The approach.** Two-step normalization applied to both raw margin and
opponent-adjusted margin:

```
pace_adj_margin     = raw_margin  × (ref_scoring / season_scoring)
pace_adj_adj_margin = adj_margin  × (ref_scoring / season_scoring)
```

where `ref_scoring` is the historical mean of `league_scoring` across all 43
seasons and `season_scoring` is that season's average.  A season with higher
scoring than the historical mean (like 2025–26) gets a discount; a low-scoring
era gets a boost.  The scale factor is applied to both raw and adjusted margins.

**Why this normalization.** Point margins are not dimensionless — a +10 margin in
a 115-pt era is fewer standard deviations above zero than a +10 in a 92-pt era.
Dividing by the scoring average (or equivalently multiplying by the ratio to the
reference) converts margins to "units of average team output," making comparisons
across 42 seasons more apples-to-apples.  Note that the opponent-adjusted margin
(`adj_margin`) already partially controls for era because both the champion's raw
margin and opponents' SRS are expressed in the same season's point-differential
units. But the inflation is not fully cancelled: `adj_margin = raw − opp_SRS`, and
if both raw and opp_SRS are inflated proportionally, adj_margin is inflated too.

**What the results mean.**
- 2025–26 is the highest-scoring era since 1984 (115.6 pts/team/game; historical
  mean 103.5). Scale factor: 0.896 — a ~10% discount.
- Pace-adjusted raw margin: +13.3 pts/game (95th pct, 3rd all-time) — the raw
  "best ever" claim doesn't survive era adjustment. The 2000–01 Lakers (+13.9)
  and 2016–17 Warriors (+13.4) both rank above on this metric.
- Pace+opp-adjusted margin: +10.1 pts/game (100th pct) — still first, but by
  a razor's edge over the 2016–17 Warriors (+10.0). These two runs are
  statistically indistinguishable on the most complete metric.

---

## 9. The Verdict (`run_verdict`)

**The data.** All of the above; this section re-computes the key metrics from
scratch to produce a single summary table and a text verdict.

**The approach.** All metrics (win rate, margin, opp SRS, adjusted margin,
pace-adjusted margin, opp+pace-adjusted margin, overperformance, SRS gap) are
pulled, their percentile ranks computed, and a branching verdict string is
assembled using thresholds:

```python
if wr_pct >= 85:   dom = "elite"
elif wr_pct >= 70: dom = "strong"
else:              dom = "moderate"

if adj_pct >= 70:  adj_verdict = "holds up well after adjusting for schedule"
elif adj_pct >= 50: adj_verdict = "is somewhat deflated by opponent adjustment"
else:              adj_verdict = "is significantly deflated by a weak schedule"
```

The east_context clause fires only if `gap_pct >= 80` — i.e. only if the East
was genuinely historically weak (top-quintile West dominance) is the caveat
included. Since 2025–26 is at the 37th percentile (West dominance was below
average), no caveat fires.

**What the results mean.** Win rate 88th percentile → "elite." Adjusted margin
100th percentile → "holds up well." East weakness at 37th percentile → no caveat.
The verdict is: the run was elite, and the schedule was at the historical median,
so the dominance is real.

**Why no new chart.** The verdict section's job is to synthesize the previous
sections, not introduce new data. The metrics already have their charts in
Sections 1–7; a summary radar or scorecard would duplicate them. The paragraph
verdict is the right form for a synthesis.

---

## 10. Betting-Market Significance (`run_betting_market`)

**The data.** Game-level ATS data from the ESPN core API, merged with actual
margins from the playoff game log.

**The approach.** The 16-3 ATS record is tested against a null hypothesis of
50% coverage (the efficient market expectation: if spreads are fair, any team
covers ~50% of games). A one-tailed binomial test computes P(X ≥ 16 | n=19, p=0.5):

```python
from scipy.stats import binom
p_value = binom.sf(15, 19, 0.5)   # P(X >= 16) = 1 - CDF(15)
```

The z-score is computed as `(k − np) / sqrt(np(1−p))` = `(16 − 9.5) / sqrt(4.75)`.

**Why a one-tailed test.** We are testing whether the Knicks covered *more* than
expected, not whether they differed from 50% in either direction. The question
("was this ATS performance unusual?") is directional.

**What the results mean.** Z = +2.98, p = 0.0022.  A team covering 16 of 19
games under a fair-coin null has only a 0.22% probability. This is not random
variation — the East-opponent performance (14-0 ATS in rounds 1-3) drove the
signal, while the Finals (2-5 ATS) was exactly what the efficient market predicted.

**An important caveat.** This p-value applies to one team in one playoff run. We
identified this run because it was interesting (the champion); if we instead asked
"of all playoff champions, how often do we see ATS records this extreme?", the
reference distribution would be different and we'd need historical ATS data for
all 43 champions. The p-value is best interpreted as "the ATS outperformance
against East opponents was systematic, not luck" — not as an unbiased statistical
claim across all possible playoff runs.

---

## Recurring Methods — Quick Reference

**`_pct_rank(series, value, ascending=True)`**
The single statistical primitive used throughout. Definition:
`(series.dropna() ≤ value).mean() × 100` when `ascending=True`;
`(series.dropna() ≥ value).mean() × 100` when `ascending=False`.
This is the empirical CDF evaluated at `value`. With 43 seasons, resolution is
~2.3 pp. A value equal to the best historical value yields 100th percentile
(since it is ≤ itself and every other value). No smoothing, no interpolation.

**SRS (Simple Rating System) — `compute_srs` in `nbakit.data`**
SRS solves a system of linear equations that makes each team's rating equal its
average point margin per game plus an adjustment for opponent strength. The system
is:

```
(I − A) @ srs = mean_margin_vector
```

where `A[i, j]` = fraction of team `i`'s games against team `j` (the
normalized schedule matrix), and `mean_margin_vector[i]` is team `i`'s average
per-game margin across all regular-season games. The constraint `sum(srs) = 0` is
imposed so the solution is unique and ratings are relative rather than absolute.
This is solved via `numpy.linalg.lstsq` on the augmented system (adding a row
for the constraint). An SRS of +5 means "this team outperforms a 0-SRS schedule
by 5 points per game"; a +8.28 SRS for San Antonio (the Finals opponent) places
them among the elite regular-season teams in 2025–26.

**`identify_champion`**
Counts wins per team in the playoff game log and returns the team with the most.
This is unambiguous: the actual Finals winner has more wins than every other team
by construction (they won the championship). For seasons where the data is
complete and consistent, this is always the same as the documented champion.

**`_fill_plus_minus`**
For pre-1997 seasons where `PLUS_MINUS` is NaN, the helper uses the two-row
structure of the game log (one row per team per game) to compute margins from
`PTS`. For each `GAME_ID`, the `PTS` column is reversed within the group (using
`transform(lambda s: s.iloc[::-1].values)`) to give each row the opponent's
points, and `PLUS_MINUS = PTS − OPP_PTS` is filled where null. This is
algebraically exact under the assumption that the box-score `PTS` totals match
the official game score (they do).

**Percentile vs. rank.** The report uses "Nth percentile" rather than "Kth of 43"
because percentile is more intuitive at this sample size and because it is
comparable across sections with slightly different sample sizes (some metrics
have fewer than 43 valid values due to NaN, e.g. in pre-1997 margins before the
fill).

**Why no regression.** The analysis is fundamentally descriptive: it ranks a
single team against a historical distribution. Regression would add complexity
(what is the outcome variable? what are the controls?) without answering the
simpler and more direct question of "where does this run rank?" The adjusted margin
is the closest thing to a model — it makes a specific functional-form assumption
(opponent adjustment = direct subtraction) — but it is explicitly stated and
motivated by the SRS identity rather than fit from data.
