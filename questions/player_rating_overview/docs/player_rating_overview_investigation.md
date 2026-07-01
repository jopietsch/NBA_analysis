# NBA Player Rating Systems: Investigation

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

## How to read the numbers

This document shows the evidence behind the claims in the main findings doc.
Most of that evidence is rank correlations and explained-variance scores, with reliability shown by cross-validation and by how steady a number stays from season to season.

**Spearman rank correlation (r):** how consistently two rankings agree, from -1 (perfect disagreement) to +1 (perfect agreement).
0.7 or above is strong agreement; 0.4-0.7 is moderate; below 0.4 is weak.

**R² and cross-validated R² (CV R²):** R² is the share of one thing's variation that another set of numbers can reconstruct, from 0 (none) to 1 (all).
Plain R² is measured on the same data it was fit to, so it flatters the fit.
CV R² refits with one team held out at a time and scores only the held-out team, so it is the honest out-of-sample read and always the lower, more trustworthy number.

**Season-to-season range [low, high]:** where a result is averaged over many seasons, the bracket gives the lowest and highest single-season value.
A tight range means the pattern is steady and not a one-year fluke; a wide range means it swings.
This range stands in for a formal confidence interval, which the thin single-season samples here (30 teams) do not support.

**p-value:** the probability of seeing a result at least this large if there were no real effect; below 0.05 is the usual "unlikely to be noise" threshold.
One p-value appears in this document, where two ratings are compared head to head; everywhere else the cross-validation and the season range carry the reliability.

---

## 1. Cross-system agreement

### Method

For each pair of rating systems, Spearman rank correlations were computed among qualified players (500+ minutes), all 378 of whom carry every recomputed system.
Because we are examining many pairs at once, we read the full matrix rather than fishing for a single comparison that clears a threshold.

### Results

The full correlation matrix is in `player_rating_overview_results.md`; the patterns below are its spine.

The box-score systems form a tight cluster.
Game Score and PER rank players almost identically (r = 0.862), PER and Win Shares closely (r = 0.768), Game Score and Win Shares nearly as much (r = 0.674).
The recomputed BPM sits inside this cluster too: it agrees with PER at r = 0.901 and with Game Score at r = 0.739, on par with how tightly the box scores agree among themselves, even though BPM weighs team point margin and defense that those scoring-led metrics leave out.
VORP tracks BPM almost perfectly (r = 0.964), which is no surprise since VORP is BPM scaled by minutes.

The box scores and the single-season RAPM agree only loosely.
PER vs bare RAPM is r = 0.302, Win Shares vs RAPM 0.367, BPM vs RAPM 0.355, and its average rank agreement across the box-score systems is 0.33.
Its top-rated player, Chet Holmgren, sits at No. 22 in the consensus: one season of lineup data still moves the leaderboard around, which is the price of reading the game through possessions rather than the box score.
Against the consensus itself bare RAPM lands at 0.42.

RAPM+prior, the multi-year version shrunk toward a box-score prior, agrees far more.
BPM vs RAPM+prior is r = 0.892, PER vs RAPM+prior 0.811, its mean box-score agreement 0.75, and it tracks the consensus at 0.91.
Its top five are now the players the box scores also rate highest: Shai Gilgeous-Alexander, Giannis Antetokounmpo, Nikola Jokić, Victor Wembanyama, and Luka Dončić.
The multi-year pooling and the box-score prior, not any single season's raw lineup data, are what pull the order into line.

Offense and defense move independently.
O-RAPM and D-RAPM correlate at -0.068, essentially unrelated, and the box-score halves barely relate either: OBPM vs DBPM is 0.089, and Game Score, a scoring-led measure, is nearly unrelated to DBPM (r = 0.102).

### Interpretation

The systems agree most where they share inputs and least where they don't.
The box scores cluster because they read the same box totals; they part from RAPM because RAPM reads lineup results the box scores never see.
A correlation at 0.7 or above means two systems are largely measuring the same quality from different angles; below 0.4 means they genuinely disagree about who is contributing.
Bare single-season RAPM is the noisier read, so its loose agreement with the box scores is partly one-season variance rather than a real difference of opinion; the multi-year, prior-informed RAPM+prior is the version to compare against the field, and it agrees with the field far more.

### How we built and checked BPM

This project's earlier BPM was broken: low-minute players topped the list, usage rates came back near 1.0, and VORP ran into the hundreds.
It has been rebuilt and checked player-by-player against Basketball-Reference's published values.

The rebuild runs in two steps.
First, a trend line: OBPM and DBPM are each a weighted sum of standard box-score rate stats (usage, assists, turnovers, rebounds, steals, blocks, shooting efficiency), with the weights fit to reproduce Basketball-Reference's own OBPM and DBPM.
Second, a team anchor: within each team the OBPM and DBPM are shifted so the players, weighted by minutes, sum to the team's actual point differential.
The anchor is what BPM is built to do, and it sets the scale.

The check matches every qualified player to Basketball-Reference for 2025-26.
Across the 361 matched players the recompute moves almost one-for-one with the published numbers: the correlation is 0.946 for OBPM, 0.877 for DBPM, 0.930 for combined BPM, and 0.961 for the cumulative VORP.
The typical player sits 0.80 points off the published BPM; Jalen Brunson, for one, comes out at 3.4 here against 3.1 at Basketball-Reference.
DBPM is the weakest match, which is honest rather than alarming: box-score defense is hard to capture, and Basketball-Reference's own DBPM carries the same limit.
The recompute also compresses the very top a little, so the league's best land just under their published BPM; the ordering and the strong agreement are what the rest of this report leans on.

### How the RAPM fix landed

RAPM used to belong in a "known broken" box; it no longer does, and the repair is worth spelling out.
The problem was never the model but the data feeding it: a reconstruction bug threw out any game whose substitutions failed to reconcile back to five-on-five, and it was silently discarding about 60% of the games that had complete play-by-play.
Recovering those games (and repairing the substitution-name matching that caused most of the misfires) roughly tripled the usable possessions, and the RAPM ratings went from noise to a real signal.

How we know: split-half reliability, the clean test for whether a rating measures anything real.
Split the possessions in half at random, fit RAPM on each half, and correlate the two sets of player ratings; if the lineup signal is real the halves agree, if it is noise they do not.
That number rose from about 0.10 before the fix to 0.32 after it (a full-data reliability near 0.48 once you correct for using only half the data each time).
Bare single-season RAPM's year-over-year stability climbed the same way, from about 0.09 to 0.41.
And RAPM+prior, the multi-year version anchored to the box-score prior, is now at least as steady from season to season as BPM: 0.84 against BPM's 0.79, which means it is adding a genuine lineup contribution on top of the box score rather than echoing it.
The full method and the split-half evidence are laid out in the RAPM methods companion (`player_rating_overview_rapm_methods.md`).

Two honest caveats remain.
Bare single-season RAPM is still the noisier of the two cuts, so RAPM+prior is the version to trust and to compare against the field.
And reliability keeps rising as more seasons are pooled (roughly 0.48 at three pooled seasons and 0.60 at five, on the full-data scale), so RAPM sharpens further the more play-by-play it is given.

---

## 2. Overlap: how much each system repeats the others

### Method

For each system, we measured how much of its rating can be rebuilt from all the other systems together, fitting a trend line on the rest.
The share that can be reconstructed is the overlap: a high overlap means the system mostly repeats what the others already say; a low overlap means it carries something of its own.
Each system's own algebraic kin are held out of the comparison, so BPM is never "explained" by its own offensive and defensive halves, which would otherwise force its overlap to a meaningless 1.00.

One caveat: high overlap does not make a system useless.
A reliable, well-validated system that moves in lockstep with the others is still worth trusting; it just is not adding a separate piece of information.

### Results

The systems split sharply.
The all-in-one box scores are the most redundant: PER sits at 0.947 overlap and BPM at 0.937, each almost fully reconstructable from the rest.
The metrics that carry the most of their own sit at the other end: WS/48 (0.596), bare RAPM at 0.684 and its offensive half, and Win Shares (0.668).
Defensive BPM, which once looked the most independent here, has slid toward the middle (0.770) now that the fixed RAPM accounts for much of the defensive impact it alone used to catch; RAPM+prior, anchored to the box score, sits high with the redundant group (0.939; see the caveat below).

That ordering matches intuition: a measure that only reshuffles box-score totals largely echoes the others, while one that reaches for defense or on-court impact picks up something they miss.
One caveat blunts the conclusion.
This project's BPM and VORP are validated against Basketball-Reference (see "How we built and checked BPM" above), so their overlap reads as real.
The RAPM family used to carry an asterisk here: it was an approximate, near-noise recompute, so its low overlap meant little (noise lines up with nothing, so it cannot be reconstructed from anything).
That asterisk is gone.
The possession-reconstruction fix (Section 1, and the RAPM methods companion) took RAPM from noise to a validated signal, confirmed by split-half reliability, so its overlap now reflects real agreement rather than recompute slack.
Bare RAPM carries the most of its own (0.684), while RAPM+prior, leaning on the box-score prior, tracks the field closely (0.939).

---

## 3. Uber rating: wins-predictive weighting

### Method

Player ratings for each system were aggregated to the team level using a minutes-weighted average (each player's z-score weighted by their share of team minutes).
These team-level ratings were then used to predict actual team wins, with a penalty on large weights that keeps any one system from dominating when the systems overlap as heavily as they do here.

No system was forced to a positive weight; the penalty alone handles the overlap between the closely related systems.

Because we have only 30 teams per season, the wins-predictive fit is estimated on thin data.
The weights should be read as directional evidence of which systems track team performance, not as precise estimates.
Out-of-sample validation (held-out seasons) would be needed to trust the weights beyond 2025-26; that is planned as a Phase 6 extension.

### Results

The consensus rating and the wins-predictive rating rank players almost the same way: their rankings correlate at 0.963 (the one place a direct significance test applies, p < 0.001).
Reweighting the systems to chase team wins barely moves the order from simply averaging them.
Where they part is instructive: the wins-predictive rating lifts Victor Wembanyama (+1.27 versus consensus), Kawhi Leonard (+0.90), and Shai Gilgeous-Alexander (+0.90), the stars its team-margin weighting rewards most, and marks down low-minute role players like Jericho Sims and Bub Carrington.

A sharper test than fitting wins is rebuilding them.
Each system's player ratings, minutes-weighted to the team level, are fit to team point differential and scored out of sample by holding one team out at a time (CV R²).
Some ratings are themselves built from team or lineup point differential, so their rebuild score is partly mechanical: BPM, anchored to sum to team margin, tops out at 1.000, and VORP (0.939) and the multi-year RAPM+prior (0.924) lean on that same anchor.
The honest read is the outcome-blind systems that never saw who won: among those, PER leads, rebuilding 73% of the team point-differential spread out of sample (CV R² = 0.727).
RAPM+prior's high rebuild is no longer the recompute artifact it once looked like: the possession-reconstruction fix (Section 1) makes it a validated signal resting on the anchored box-score prior plus real lineup data.

Describing a season and forecasting the next are different jobs, and they reward different systems.
Carrying each rating onto the next season's rosters and predicting that season's team margin, PER falls the furthest, from 0.73 describing to 0.37 forecasting, while Game Score barely moves (0.47 to 0.40) and ends up the best forecaster among the outcome-blind box scores.
Pooled across 29 season-pairs back to 1996-97 the same flip holds: PER averages 0.64 describing but 0.25 forecasting, and BPM forecasts better than PER in 29 of 29 pairs.
Over the 13 seasons with play-by-play, the fix flips this row too: the multi-year RAPM+prior is now the strongest forecaster in the impact-era panel, rebuilding 62% of next season's team margin on average against bare RAPM's 38%, so once the lineup data is pooled and anchored it predicts the next season better than the box scores do.
The lesson for the combined rating: the metric that best describes the season just played is not automatically the one that best predicts the next.

---

## 4. Distribution analysis

### Method

For each system, we measured how concentrated value is at the top, with these views:
- **Top-of-the-ranks drop-off:** how fast a system's value falls from the best player down the ranks. A steeper drop-off means the top is heavier relative to the rest. This is the measure to compare across systems, because it does not depend on where a system places its zero point.
- **Gini coefficient:** the standard inequality measure, where 0 means every player is equal and 1 means one player holds all the value. We keep it only as a cross-check: it is distorted for systems centered on zero (the BPM family, the consensus), where it counts every below-average player as a flat zero and so reads as more top-heavy than the system really is.
- **Top-5% share:** the fraction of total positive value held by the top 5% of qualified players.
- **Skewness:** how far the distribution leans toward the high-value side.

We tested the hypothesis that cumulative metrics (Win Shares, VORP) are more top-heavy than rate metrics (PER, BPM), because value = rate × minutes, so minutes and performance compound.

### Results

The full distribution statistics are in `player_rating_overview_results.md`.
The drop-off measure and the Gini coefficient can disagree sharply: the consensus rating and Win Shares have drop-offs far closer (0.37 vs 0.23) than their Gini scores (0.75 vs 0.36), which look far apart because Gini penalizes the consensus rating's zero-centered scale.
When the two conflict, the drop-off is the one to trust.

The cumulative-versus-rate hypothesis holds where it can be read cleanly.
Win Shares and VORP are right-skewed (skew 1.16 and 2.07), with the top 5% of players holding 14% and 24% of all value; the rate metric PER is far flatter (skew 0.83, top 5% holding just 9%).
Value built as rate times minutes piles up at the top, because the best players are both efficient and heavily used.
BPM, the other rate metric, looks deceptively top-heavy here (top 5% at 34%) for the same zero-centering reason that inflates its Gini: a scale artifact, not real concentration.

![Rating value versus rank for cumulative and rate metrics: cumulative metrics fall steeply among the top players; rate metrics stay flatter.](../generated/images/rank_value_distributions.svg){#fig-distributions}

---

## 5. Crosswalk coverage

The 14 systems analyzed here are all recomputed in-house or built from play-by-play, so they share the nba_api player list and need no name matching.
The crosswalk matters only for the third-party snapshots (RAPTOR, EPM, LEBRON, DARKO), which are joined to the nba_api player list by normalized name plus season.
None of those are loaded yet, so no match rates appear in `player_rating_overview_results.md`; they will once a snapshot is cached.

When they are, a match rate below 90% will flag a name-normalization issue (common with accented names and suffixes) or a player whose normalized name is shared by another player in the same season (an ambiguous collision).
The crosswalk handles accents and suffixes automatically; collisions require a hand entry in the OVERRIDES table.

---

## 6. Season-over-season change

### Method

To gauge how much the single-season comparison depends on the season chosen, we built the consensus for both 2024-25 and 2025-26 over each season's qualified players and matched the 290 players who qualified in both.
We then measured the year-over-year consensus rank correlation, the change in each player's standardized consensus standing, and the mean inter-system agreement in each season.

### Results

The consensus order is moderately stable: it agrees from 2024-25 to 2025-26 at Spearman r = 0.75.
Nikola Jokić and Shai Gilgeous-Alexander rank first and second in both seasons, and 4 of the top 5 carry over, so the stability is strongest at the very top.
The largest single-year moves are Kawhi Leonard up (+1.37 in standardized standing) and Ivica Zubac down (-1.50); swings this size are indistinguishable from health, role, and roster changes on one season of data, which is why the cross-system orderings are read as a snapshot.

The mean rank agreement among the box-score systems barely moved, 0.70 in 2024-25 and 0.73 in 2025-26.
The systems disagree by about the same amount each year, so the divergences this document maps are a standing property of the metrics, not a one-season artifact.
