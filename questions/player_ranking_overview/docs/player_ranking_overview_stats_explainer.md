# NBA Player Rating Systems: Methods

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

This document explains the statistical methods used in the player ranking overview pipeline. It is written for someone who knows statistics but may not have the formulas fresh. Every method named here matches what the code in `player_ranking_overview_analysis.py` and `nbakit/ratings.py` actually runs.

---

## Recomputed rating formulas

### Game Score

Game Score is a linear combination of per-game box-score statistics:

```
GmSc = PTS + 0.4*FGM − 0.7*FGA − 0.4*(FTA − FTM) + 0.7*OREB + 0.3*DREB + STL + 0.7*AST + 0.7*BLK − 0.4*PF − TOV
```

Coefficients are from Hollinger's original formulation. This is a per-game average computed from season totals divided by games played.

### Player Efficiency Rating (PER)

PER is a per-minute efficiency rating normalized so that the minutes-weighted league average is always 15. The unadjusted PER (uPER) is a weighted sum of per-minute box-score contributions. The formula accounts for:
- Scoring efficiency: credit for made baskets, adjusted for the fraction assisted (assisted baskets are credited partly to the passer)
- Rebounding: offensive rebounds credited more than defensive rebounds because of their marginal value over team average
- Turnovers and missed shots: debited at the Value of a Possession (VOP) rate
- Free throws: credited for makes, debited for misses that were self-generated
- Steals, blocks, and assists: credited at approximately VOP rates

After computing uPER, it is adjusted for team pace (faster-paced teams have more opportunities, so per-minute uPER is lower) and then normalized by dividing by the minutes-weighted league uPER and multiplying by 15.

VOP (Value of a Possession) = `lg_pts / (lg_FGA - lg_OREB + lg_TOV + 0.44 * lg_FTA)`.

Reference: John Hollinger, "Pro Basketball Forecast." Basketball-Reference write-up: https://www.basketball-reference.com/about/per.html

### Win Shares

Win Shares allocates team wins to individual players using an offensive and defensive accounting framework.

**Offensive Win Shares (OWS):**
1. Compute the player's "points produced" — a credit for directly scored points plus credits for assists at league-average efficiency, offensive rebounds, and marginal scoring.
2. Compute "scoring possessions" used.
3. Marginal offensive points = points produced minus VOP × possessions used.
4. Divide by the marginal points per win (PPW ≈ 0.32 × 2 × team points per game).

**Defensive Win Shares (DWS):**
Built from a "stops" estimate (steals, blocked shots credited at the fraction that become turnovers, defensive rebounds above the floor). The current implementation uses a simplified stops formula. The full BBR methodology also accounts for defensive ratings and team defensive context with additional adjustments.

**WS/48:** WS / minutes × 48. Rate stat.

Reference: Basketball-Reference methodology at https://www.basketball-reference.com/about/ws.html

### Box Plus/Minus (BPM 2.0)

BPM estimates a player's contribution per 100 possessions relative to an average player, derived from per-100-possession box rates plus team context.

**Offensive BPM (OBPM):**
```
OBPM = 0.7884*AST/10 − 0.8691*TOV% + 0.4234*(USG% − 20) + 0.7083*ORB%*10
       + 2.2192*(eFG% − 0.5)*10 + 0.5765*(FT_rate − 0.25)*10
       + role_coefficient
```

**Defensive BPM (DBPM):**
```
DBPM = 0.7837*DRB%*10 + 1.7432*STL%*100 + 0.9371*BLK%*100 + role_coefficient
```

Coefficients are published by Daniel Myers at Basketball-Reference. The role coefficient adjusts for the fact that low-usage players face lower average competition. After computing raw OBPM and DBPM, both are normalized so that the minutes-weighted league average BPM = 0.

Reference: https://www.basketball-reference.com/about/bpm2.html

### VORP (Value Over Replacement Player)

VORP converts BPM from a rate (per 100 possessions) to a cumulative value:

```
VORP = (BPM − (−2.0)) × (MIN / (team_games × 5 × 48)) × team_games
```

The replacement level is −2.0 BPM (a marginal roster player available from the waiver wire is assumed to perform at −2.0 per 100 possessions). Multiplying by the fraction of team possessions played gives the total value above replacement over the season.

---

## Cross-system comparison methods

### Spearman rank correlation

Spearman rank correlation measures the monotone association between two rankings. For each pair of systems, players are assigned percentile ranks within each system, then the Pearson correlation of those ranks is computed. Unlike Pearson correlation, Spearman does not assume linearity — it only requires that the two systems agree on ordering.

Values range from -1 (perfect disagreement) to +1 (perfect agreement). A value of 0.7 or above among NBA players typically means the two systems identify largely the same group of players as above-average.

### Unique variance (unique R²)

For each system S, we regress S on all other present systems using ordinary least squares (OLS). The model's R² measures how much of S can be explained by the others. The unique R² is defined here as the residual variance fraction: `1 − R²`. A system with unique R² of 0.40 means 40% of its variation cannot be reconstructed from the other systems — it is carrying independent signal.

### Consensus rating (z-score average)

Each system's values are standardized: subtract the mean, divide by the standard deviation, among qualified players. The consensus rating is the mean of these standardized scores across all systems with data for that player. A player missing from a system (e.g., a player not in RAPTOR's era) gets that system excluded from their average.

The z-score average treats each system as equally reliable. The limitation is that it can be dominated by systems that measure the same thing (e.g., if five box-score systems are included and two impact metrics, the consensus will weight box stats heavily).

### Wins-predictive rating (ridge regression)

To find the combination of systems that best predicts team wins:
1. Standardize each system's values per player (z-score, same as consensus).
2. Aggregate to team level: for each team, compute the minutes-weighted average of each system's player z-scores.
3. Regress actual team wins on these team-level ratings using ridge regression (L2 penalty, α = 5.0) to handle multicollinearity.
4. The regression coefficients define the importance weight for each system in predicting wins.
5. Apply the same weights per-player to construct the per-player wins-predictive rating.

**Ridge regression** is OLS with a penalty term that shrinks large coefficients toward zero. With 30 data points (teams) and many correlated predictors (systems), OLS coefficients are unreliable. Ridge stabilizes them at the cost of some bias. The α = 5.0 penalty is not tuned by cross-validation for this application; the resulting weights should be taken as directional evidence, not precise estimates.

With only 30 teams per season, the wins-predictive weights are estimated on thin data. A proper evaluation would require holding out seasons and testing whether the weights estimated on past seasons predict future-season team wins. That analysis is deferred to a Phase 6 extension.

---

## Distribution analysis

### Gini coefficient

The Gini coefficient measures inequality in a distribution. For player ratings, a Gini of 0 means every player has the same rating (perfect equality); a Gini of 1 means one player has all the rating value and the rest have zero. Computed as:

```
Gini = (2 * Σ(rank_i * value_i) / (n * Σ(value_i))) − (n+1)/n
```

where players are sorted ascending by value and rank_i runs from 1 to n.

### Top-5% share

The fraction of total positive rating value held by the top 5% of qualified players by that metric. If the top 5% hold 30% of the total value, player value is moderately concentrated; if they hold 60%, the distribution is heavily right-skewed.

### Skewness

A standard measure of asymmetry. Positive skewness means the right tail (high values) extends further than the left. Values above 0.5 are conventionally "right-skewed"; above 1.0 is "heavily skewed." Rate metrics among qualified players typically show skewness near 0 (they are selected to be above a usage/minutes threshold, which truncates the left tail and creates a near-symmetric distribution). Cumulative value metrics show positive skewness because high-value players are both highly efficient and play many minutes — both conditions amplify total value.

---

## Data pipeline

All recomputed ratings are computed in `nbakit/ratings.py` from totals fetched via `nbakit/data.py` (nba_api endpoints: `LeagueDashPlayerStats`, `LeagueDashTeamStats`, `LeagueStandingsV3`). Third-party results are loaded from cached CSVs and joined via the player crosswalk in `nbakit/player_crosswalk.py`. The unified table is assembled in `player_ranking_overview_data.py` and cached to `cache/unified_ratings_{season}.csv`.

The analysis module (`player_ranking_overview_analysis.py`) runs all statistical computations from the unified table, printing results to stdout, which the orchestrator (`player_ranking_overview.py`) captures into `docs/player_ranking_overview_results.md`.
