# NBA Player Rating Systems: Methods

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

This document explains the statistical methods used in the player rating overview pipeline.
It is written for someone who knows statistics but may not have the formulas fresh.
Every method named here matches what the code in `player_rating_overview_analysis.py` and `nbakit/ratings.py` actually runs.

---

## Recomputed rating formulas

### Game Score

Game Score is a linear combination of per-game box-score statistics:

```
GmSc = PTS + 0.4*FGM − 0.7*FGA − 0.4*(FTA − FTM) + 0.7*OREB + 0.3*DREB + STL + 0.7*AST + 0.7*BLK − 0.4*PF − TOV
```

Coefficients are from Hollinger's original formulation.
This is a per-game average computed from season totals divided by games played.

### Player Efficiency Rating (PER)

PER is a per-minute efficiency rating normalized so that the minutes-weighted league average is always 15.
The unadjusted PER (uPER) is a weighted sum of per-minute box-score contributions.
The formula accounts for:
- Scoring efficiency: credit for made baskets, adjusted for the fraction assisted (assisted baskets are credited partly to the passer)
- Rebounding: offensive rebounds credited more than defensive rebounds because of their marginal value over team average
- Turnovers and missed shots: debited at the Value of a Possession (VOP) rate
- Free throws: credited for makes, debited for misses that were self-generated
- Steals, blocks, and assists: credited at approximately VOP rates

After computing uPER, it is adjusted for team pace (faster-paced teams have more opportunities, so per-minute uPER is lower) and then normalized by dividing by the minutes-weighted league uPER and multiplying by 15.

VOP (Value of a Possession) = `lg_pts / (lg_FGA - lg_OREB + lg_TOV + 0.44 * lg_FTA)`.

Reference: John Hollinger, "Pro Basketball Forecast." Basketball-Reference write-up: <https://www.basketball-reference.com/about/per.html>

### Win Shares

Win Shares allocates team wins to individual players using an offensive and defensive accounting framework.

**Offensive Win Shares (OWS):**
1. Compute the player's "points produced": a credit for directly scored points plus credits for assists at league-average efficiency, offensive rebounds, and marginal scoring.
2. Compute "scoring possessions" used.
3. Marginal offensive points = points produced minus VOP × possessions used.
4. Divide by the marginal points per win (PPW ≈ 0.32 × 2 × team points per game).

**Defensive Win Shares (DWS):** Built from a "stops" estimate (steals, blocked shots credited at the fraction that become turnovers, defensive rebounds above the floor).
The current implementation uses a simplified stops formula.
The full BBR methodology also accounts for defensive ratings and team defensive context with additional adjustments.

**WS/48:** WS / minutes × 48.
Rate stat.

Reference: Basketball-Reference methodology at <https://www.basketball-reference.com/about/ws.html>

### Box Plus/Minus (BPM)

BPM estimates a player's points per 100 possessions above a league-average player, built from box-score rate stats plus team context.
This project's BPM is recomputed in two stages and validated against the published Basketball-Reference values.

**Stage 1: a linear model fit to Basketball-Reference.** First we compute standard advanced rate stats for each player, minutes- and pace-aware, approximating the opponent with the league-average team: usage rate (USG%), assist rate (AST%), turnover rate (TOV%), offensive and defensive rebound rates (ORB%, DRB%), steal and block rates (STL%, BLK%), and a scoring-efficiency term built from true shooting (TS%).
Offensive BPM (OBPM) and Defensive BPM (DBPM) are each a weighted sum of those rates.
The weights are not Myers's published coefficients; they were fit by ordinary least squares (the straight-line fit that minimizes squared error) to reproduce Basketball-Reference's own published OBPM and DBPM for 2025-26.
That fit is the source of the weights.

**Stage 2: the team-margin anchor.** Within each team, OBPM is shifted by a single constant so its minutes-weighted average equals the team's offensive point margin per 100 possessions, and DBPM is shifted so its average equals the defensive margin.
A team's players, weighted by minutes, then sum to the team's point differential.
This is the defining property of BPM, and Basketball-Reference anchors the same way.
Because the anchor sets the scale, the intercepts from the Stage 1 fit are dropped.

**How well it matches.** On the 361 qualified players matched to Basketball-Reference, the recompute reproduces the published values closely.
Pearson correlation (how tightly two sets of numbers track a straight line, where 1.0 is identical) runs 0.946 for OBPM, 0.877 for DBPM, and 0.930 for combined BPM, with a mean absolute BPM gap of 0.80 points.
For Jalen Brunson the recompute gives 3.4, against Basketball-Reference's 3.1.
DBPM is the weakest of the three, and that is expected: box-score defense is genuinely hard to pin down, and Basketball-Reference's own DBPM is a limited signal.
The recompute also compresses the very top a little, so the best handful of players land slightly below their published BPM; the ordering and the correlation hold.

Reference: <https://www.basketball-reference.com/about/bpm2.html>

### VORP (Value Over Replacement Player)

VORP turns BPM from a per-100-possession rate into a season-long cumulative value:

```
VORP = (BPM − (−2.0)) × (MIN / (team_games × 48)) × (team_games / 82)
```

The replacement level is −2.0 BPM: a freely available roster filler is assumed to produce −2.0 per 100 possessions.
`MIN / (team_games × 48)` is the player's share of a roster slot's minutes (about 0.66 for a full-time star), and `team_games / 82` prorates a partial season.
VORP inherits BPM's validation; against Basketball-Reference it tracks at Pearson r = 0.961.

### Playoff-Weighted Value (PWV)

PWV asks a different question from the season-long metrics: who was most valuable once the games that decide titles are weighted up?
It is a minutes-weighted blend of each player's regular-season and playoff BPM, with playoff minutes counted more heavily:

```
PWV = (reg_BPM × reg_MIN + po_BPM × po_MIN × w) / (reg_MIN + po_MIN × w)
```

The playoff weight `w` is 2 in the primary version, so each playoff minute counts double a regular-season one.
The pool is the 103 players with at least 150 playoff minutes.
Because both inputs are BPM, PWV inherits BPM's validation and adds no estimation of its own.
At the primary weight the leaders are Nikola Jokić (10.2), Victor Wembanyama (8.8), and Shai Gilgeous-Alexander (8.6).
The weight matters most for players who raise their game in the playoffs: Jalen Brunson goes from +3.4 in the regular season to +4.6 in the playoffs, which lifts him from 15th in the pool at equal weight to 7th once playoff minutes are doubled.

---

## Cross-system comparison methods

### Spearman rank correlation

Spearman rank correlation measures the monotone association between two rankings.
For each pair of systems, players are assigned percentile ranks within each system, then the Pearson correlation of those ranks is computed.
Unlike Pearson correlation, Spearman does not assume linearity; it only requires that the two systems agree on ordering.

Values range from -1 (perfect disagreement) to +1 (perfect agreement).
A value of 0.7 or above among NBA players typically means the two systems identify largely the same group of players as above-average.

### Overlap variance (overlap R²)

For each system S, we regress S on all other present systems using ordinary least squares (OLS) and take the regression R².
That R² is the share of S the others can reconstruct: its overlap with the rest of the field, so a high value means the system is largely redundant and a low value means it carries independent signal.
Each system's own algebraic kin are held out of the predictor set: a metric and its offensive/defensive halves, or a rescaling of itself.
Without that, BPM (which is OBPM plus DBPM) would be reconstructed exactly from its own components and post a meaningless R² = 1.00; holding the kin out measures overlap against genuinely different systems instead.
The result splits the field: the simple box scores are the most redundant (PER and Game Score near R² = 0.89), while BPM and Defensive BPM carry the most of their own (near 0.52).
One reading caveat: an approximate recompute looks independent partly because its noise correlates with nothing, so a low overlap is not by itself proof of unique signal.

### Consensus rating (z-score average)

Each system's values are standardized: subtract the mean, divide by the standard deviation, among qualified players.
The consensus rating is the mean of these standardized scores across all systems with data for that player.
A player missing from a system (e.g., a player not in RAPTOR's era) gets that system excluded from their average.

The z-score average treats each system as equally reliable.
The limitation is that it can be dominated by systems that measure the same thing (e.g., if five box-score systems are included and two impact metrics, the consensus will weight box stats heavily).

### Wins-predictive rating (ridge regression)

To find the combination of systems that best predicts team wins:
1. Standardize each system's values per player (z-score, same as consensus).
2. Aggregate to team level: for each team, compute the minutes-weighted average of each system's player z-scores.
3. Regress actual team wins on these team-level ratings using ridge regression (L2 penalty, α = 5.0) to handle multicollinearity (the instability that arises when predictors are highly correlated with each other, which makes individual OLS coefficients swing wildly).
4. The regression coefficients define the importance weight for each system in predicting wins.
5. Apply the same weights per-player to construct the per-player wins-predictive rating.

**Ridge regression** is OLS with a penalty term that shrinks large coefficients toward zero.
With 30 data points (teams) and many correlated predictors (systems), OLS coefficients are unreliable.
Ridge stabilizes them at the cost of some bias.
The α = 5.0 penalty is not tuned by cross-validation for this application; the resulting weights should be taken as directional evidence, not precise estimates.

With only 30 teams per season, the wins-predictive weights are estimated on thin data.
A proper evaluation would require holding out seasons and testing whether the weights estimated on past seasons predict future-season team wins.
That analysis is deferred to a Phase 6 extension.

---

## Distribution analysis

How concentrated is value at the top of a system?
Two measures answer this, and they disagree for a reason worth understanding.
The power-law exponent is the one to trust across systems; the Gini coefficient is kept as a cross-check because it is distorted by metrics centered on zero.

### Power-law fit (log-log OLS)

A distribution follows a power law when value falls by a roughly constant percentage with each step down the ranks: value(rank) ≈ C · rank^(−α).
The exponent α is the steepness.
A larger α means value drops off faster, so the top is heavier relative to the rest.

The fit (`powerlaw_fit` in `player_rating_overview_data.py`) takes a system's top 50 qualified values, sorts them descending, and keeps the leading run of strictly positive values (the logarithm is undefined at zero or below, which is why the BPM-family metrics, full of negative values, contribute only their positive top).
It then runs an ordinary least-squares line of log(value) on log(rank).
The slope of that line is −α, and the fit's R² measures how straight the points are on log-log axes.
A system is labeled a power law when R² ≥ 0.95 (`POWERLAW_R2_THRESHOLD`): a straight line on log-log axes is the signature of a power law.
Curves that fall below the threshold "bend," meaning the top player sits below where a straight extrapolation would place them, so there is a natural ceiling rather than a runaway leader.

The 0.95 cutoff is a convention, not a hypothesis test.
Systems sitting right at the line (DBPM just clears it, BPM just misses) are effectively the same shape.
The reliable read is the grouping and the order of α across systems, not the label on any single borderline case.

α is the fair cross-system concentration measure because it does not depend on where zero sits: shifting every value by a constant leaves the slope on log-log axes unchanged once the curve is rescaled.
That property is exactly what the Gini coefficient lacks.

### Gini coefficient

The Gini coefficient measures inequality in a distribution.
For player ratings, a Gini of 0 means every player has the same rating (perfect equality); a Gini of 1 means one player has all the rating value and the rest have zero.
Computed as:

```
Gini = (2 * Σ(rank_i * value_i) / (n * Σ(value_i))) − (n+1)/n
```

where players are sorted ascending by value and rank_i runs from 1 to n.

Gini is reliable only for metrics that accumulate a quantity that cannot drop below zero (Win Shares, VORP).
The implementation here clips negative values to zero, so for metrics centered on zero (the BPM family, and the consensus and wins-predictive ratings) every below-average player is counted as a flat zero.
That inflates the score and makes the metric look more top-heavy than it is: the consensus rating posts a Gini near 0.76, above Win Shares near 0.36, an ordering the power-law exponents nearly erase (consensus 0.31 vs Win Shares 0.23), so the fair measure shows the two similarly concentrated rather than the wide gap Gini implies.
Gini is therefore reported only as a cross-check; the power-law exponent is the measure to trust when comparing systems.

### Top-5% share

The fraction of total positive rating value held by the top 5% of qualified players by that metric.
If the top 5% hold 30% of the total value, player value is moderately concentrated; if they hold 60%, the distribution is heavily right-skewed.

### Skewness

A standard measure of asymmetry.
Positive skewness means the right tail (high values) extends further than the left.
Values above 0.5 are conventionally "right-skewed"; above 1.0 is "heavily skewed." Rate metrics among qualified players typically show skewness near 0 (they are selected to be above a usage/minutes threshold, which truncates the left tail and creates a near-symmetric distribution).
Cumulative value metrics show positive skewness because high-value players are both highly efficient and play many minutes, and both conditions amplify total value.

---

## Bayesian foundations of impact metrics

### Prior, likelihood, and posterior

All RAPM-based metrics share a structure that is Bayesian in form.
Define the three components:

- **Prior:** the box-score estimate of a player's value per 100 possessions, built from statistics that stabilize quickly over a season (true shooting percentage, assist rate, usage, rebound rates, steals, blocks). This is what EPM calls the Statistical Plus/Minus (SPM) prior; what LEBRON inherits from PIPM coefficients; and what BPM 2.0 itself is when used as a prior inside another system.
- **Likelihood:** the on/off stint data. Each stint is a window of possessions during which a specific lineup was on the floor, producing an observed point differential. Across a full season these stints are the evidence that updates the prior.
- **Posterior:** the RAPM estimate that blends prior and likelihood, weighted by how much evidence exists. Heavy-minute players in stable lineups get posteriors that move substantially toward what the data shows. Bench players with few possessions get posteriors that remain close to the prior.

### Ridge regression as maximum a posteriori (MAP) estimation

Ridge regression is RAPM's estimator.
It minimizes:

```
Σ (observed_diff − X β)² + λ Σ βᵢ²
```

where X is the design matrix of stint-level player indicators (one column per player, one row per stint), β is the vector of player values, and λ is the regularization penalty.
This is identical to maximum a posteriori (MAP) estimation under a Bayesian model with two assumptions: (1) observed point differentials are Gaussian around the true lineup value, and (2) each player's true value βᵢ is drawn from a zero-mean Gaussian with variance σ²/λ.

The prior here is zero-mean: in the absence of data, every player is assumed to be average.
EPM improves on this by using a non-zero prior (the SPM estimate), making the prior informative rather than diffuse.
Larger λ means stronger shrinkage toward the prior; smaller λ means more trust in the data.
Calibrating λ well, so that bench players with few possessions are not estimated wildly from noise, is where most of the engineering work in these systems lives.

This report computes its own RAPM with exactly this estimator.
Each 2025-26 game's play-by-play is reconstructed into possessions; the design matrix gives every player two columns, one marked +1 on the possessions they played offense and one marked −1 on the possessions they played defense, the target is the offense's points per 100 possessions, and λ is chosen by five-fold cross-validation.
The prior is the zero-mean one above, with no SPM term.
That bare setup is the reason the single-season estimate is noisier than EPM or LEBRON.

The report also computes a stabilized version, RAPM+prior, that adds the two pieces the published metrics rely on.
First, a non-zero prior: instead of shrinking each coefficient toward zero, the ridge shrinks it toward the player's Box Plus/Minus (the offensive column toward OBPM, the defensive toward DBPM).
This is the prior-mean ridge, implemented by the substitution γ = β − prior, so the same RidgeCV solver fits the residual and the prior is added back.
BPM stands in for the optimized SPM priors that EPM and LEBRON use.
Second, multi-year pooling: three seasons of possessions are stacked with linear recency weights (most recent season weighted highest) and fit together, which is how RPM and EPM cut single-season noise.
RAPM+prior, combined only, is the version that feeds the consensus.
It does not match EPM or LEBRON, whose edge comes from player-tracking inputs this project does not have.

### Sequential updating: the Kalman filter

DARKO and DRIP weight recent games more heavily than early-season games.
The principled structure for this is a Kalman filter, the optimal Bayesian sequential estimator for linear-Gaussian systems.

At each time step (game played), the filter runs two steps:

1. **Predict:** project the current estimate forward using a process model that allows for some change in true talent since the last game. This is where the decay parameter lives: how fast the filter forgets old games.
2. **Update:** incorporate the new game's lineup data, weighting the new observation by the ratio of process noise (how much talent changes between games) to observation noise (how noisy a single game's lineup data is).

The filter maintains both a posterior mean (best current estimate of talent) and a posterior variance (uncertainty around that estimate).
The daily-updated ratings that DARKO and DRIP publish are these posterior means.
Because the filter is explicitly sequential, a hot streak or injury mid-season shifts the estimate in proportion to how informative the recent games are relative to the accumulated prior.

### What is missing: posterior uncertainty intervals

Every published metric reports a posterior mean without a posterior variance.
This gap matters in practice.

For a Bayesian ridge regression, the posterior variance over player values has a closed-form expression:

```
Var(β) = σ² (XᵀX + λI)⁻¹
```

where X is the stint design matrix, σ² is the residual variance of the regression, and λ is the regularization penalty.
Players who appear in many stints (large contribution to XᵀX) get narrower uncertainty intervals.
A bench player with 400 possessions might have an interval of ±3 points per 100; a starter with 3,000 possessions in stable lineups might be ±1.

Bootstrap resampling provides an alternative: draw the season's stints with replacement and re-run the ridge regression many times; the spread of estimates is the empirical uncertainty due to sampling variance.
This does not assume Gaussianity and is valid for non-linear extensions, but is much more expensive computationally.

Both methods would show that most apparent disagreements between systems about mid-tier player rankings fall within the single-system uncertainty bands.
The metrics agree more than the published rankings suggest, because the rankings do not show how wide the error bars are.

### Bayesian model averaging for the consensus

The consensus rating in this project uses equal-weighted z-scores.
A Bayesian alternative is Bayesian model averaging (BMA): treat each system as a model of the latent true player value, assign each model a weight proportional to its evidence (how well it explains the data), and compute the posterior over player value as the weighted average of the per-model posteriors.

Without published posterior variances from the third-party systems, a tractable proxy weights each system inversely by its disagreement with the others.
The overlap R² values computed in the cross-system comparison, how much of each system's variance the others can explain, approximate this agreement directly: high overlap means a system mostly tracks the field.
A system with high overlap is either very consistent with the others (high reliability) or measuring the same thing (redundant).
Distinguishing those two interpretations requires a retrodiction test: a system that is consistent with the others AND predicts game outcomes well is reliable; a system that is merely consistent but does not predict is just echoing shared biases.

---

## Data pipeline

All recomputed ratings are computed in `nbakit/ratings.py` from totals fetched via `nbakit/data.py` (nba_api endpoints: `LeagueDashPlayerStats`, `LeagueDashTeamStats`, `LeagueStandingsV3`).
Third-party results are loaded from cached CSVs and joined via the player crosswalk in `nbakit/player_crosswalk.py`.
The unified table is assembled in `player_rating_overview_data.py` and cached to `cache/unified_ratings_{season}.csv`.

The analysis module (`player_rating_overview_analysis.py`) runs all statistical computations from the unified table, printing results to stdout, which the orchestrator (`player_rating_overview.py`) captures into `docs/player_rating_overview_results.md`.
