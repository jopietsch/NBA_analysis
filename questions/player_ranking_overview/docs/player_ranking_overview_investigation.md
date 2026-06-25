# NBA Player Rating Systems: Investigation

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

## How to read the numbers

This document shows the evidence behind the claims in the main findings doc. It uses p-values and confidence intervals to characterize how reliable the patterns are.

**p-value:** the probability of seeing a result at least this large if there were actually no real effect. A p-value below 0.05 is the conventional threshold for "this is unlikely to be noise." Below 0.01 is stronger; below 0.001 is very strong.

**Confidence interval (CI):** a range within which the true value likely falls. A 95% CI means that if you ran the same study many times, 95% of the CIs computed that way would contain the true value.

**Spearman rank correlation (r):** a measure of how consistently two rankings agree, from -1 (perfect disagreement) to +1 (perfect agreement). 0.7 or above is strong agreement; 0.4-0.7 is moderate; below 0.4 is weak.

---

## 1. Cross-system agreement

### Method

For each pair of rating systems with at least 20 players in common, Spearman rank correlations were computed among qualified players (500+ minutes). Because we are examining many pairs simultaneously, we report the full matrix rather than fishing for a single significant comparison.

### Results

Full correlation matrix: see `player_ranking_overview_results.md`.

Box-score systems (PER, WS, BPM) show high mutual correlations: PER and Win Shares typically correlate above r = 0.75 because they share inputs. PER and BPM share the same box-score inputs but process them through different formulas, so their correlation is usually 0.65-0.80.

The correlation between box-score systems and impact metrics depends on the season and which players qualify. Typically: BPM vs. RAPTOR r ≈ 0.55-0.70 (BPM uses similar inputs to RAPTOR's box prior); Win Shares vs. RAPTOR r ≈ 0.45-0.60 (Win Shares credits play differently).

Human rankings show the highest correlation with box systems among the top-25 players and meaningfully lower correlation in the broader qualified pool.

These figures are approximate before the pipeline runs; the results doc has the exact values for 2024-25.

### Interpretation

Correlations above 0.6 indicate the systems are measuring largely the same underlying quality signal but from different angles. Correlations below 0.5 indicate genuine methodological divergence — the systems disagree about who is contributing.

---

## 2. Unique signal analysis

### Method

For each system, we fit a linear model of that system's values on all other present systems. The fraction of variance the system explains beyond what the others capture is the unique R². This is an approximation of how redundant each system is: a high unique R² means the system adds independent information; a low unique R² means it is largely a function of the other systems.

One caveat: low unique R² does not mean a system is useless. It means it does not add information beyond what the others collectively carry. A highly reliable, well-validated system with low unique R² is still worth trusting; it is simply correlated with others.

### Results

Expected pattern: BPM and RAPTOR will show higher unique R² than PER and Win Shares, because the impact metrics incorporate on/off lineup data that box stats do not. VORP will have low unique R² because it is derived directly from BPM. Game Score will have low unique R² because it is a linear combination of box-score inputs that the other box systems also use.

Exact figures: `player_ranking_overview_results.md`.

---

## 3. Uber rating: wins-predictive weighting

### Method

Player ratings for each system were aggregated to the team level using a minutes-weighted average (each player's z-score weighted by their share of team minutes). These team-level ratings were then used as predictors of actual team wins in a ridge regression. Ridge regression adds a penalty on large coefficients, which prevents overfitting when the predictors are highly correlated (as they are here).

A non-negative constraint was not enforced in the current implementation; the ridge penalty alone handles the multicollinearity.

Because we have only 30 teams per season, the wins-predictive regression is estimated on small data. The coefficients should be interpreted as directional evidence of which systems track team performance, not as precise weights. Out-of-sample validation (held-out seasons) would be needed to trust the weights beyond 2024-25; that is planned as a Phase 6 extension.

### Results

The correlation between the consensus rating and the wins-predictive rating is in `player_ranking_overview_results.md`, along with the five players most divergently ranked by the two approaches.

---

## 4. Distribution analysis

### Method

For each system, we computed:
- **Gini coefficient:** measures inequality of value distribution among qualified players. 0 = perfectly equal; 1 = one player holds all value.
- **Top-5% share:** the fraction of total positive value held by the top 5% of qualified players.
- **Skewness:** a statistical measure of how much the distribution pulls to the right (positive values above the mean) or left.

We tested the hypothesis that cumulative metrics (Win Shares, VORP) are more right-skewed than rate metrics (PER, BPM) because value = rate × minutes, and the distribution of minutes × performance compounds the inequality.

### Results

The full distribution statistics are in `player_ranking_overview_results.md`. The hypothesis is expected to hold for WS and VORP vs. PER and BPM. The report states whether it held for each metric in the 2024-25 data.

![Rating value versus rank for cumulative and rate metrics: cumulative metrics fall steeply among the top players; rate metrics stay flatter.](../generated/images/rank_value_distributions.svg)

---

## 5. Crosswalk coverage

Third-party sources are joined to the nba_api player list by normalized name + season. The match rates for each source are reported in `player_ranking_overview_results.md`. Unmatched players are listed.

Match rates below 90% indicate a name-normalization issue in the source data (common with accented names and suffixes) or a player whose normalized name is shared by another player in the same season (an ambiguous collision). The crosswalk handles accents and suffixes automatically; collisions require a hand entry in the OVERRIDES table.
