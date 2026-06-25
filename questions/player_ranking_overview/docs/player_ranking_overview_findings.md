# NBA Player Rating Systems: Survey, Comparison, and Combination

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

## 1. Introduction

Every "top players" list puts names in order. But ordinal rank is a compression: the gap between the best player in the league and the tenth-best is not the same as the gap between the tenth and the twentieth. The numbers beneath the ranks tell a different story than the ranks themselves.

This report surveys how NBA players get rated, compares what each system actually measures, and builds two combined ratings designed to answer two different questions: what do all the systems agree on, and which combination of them best explains which teams win?

The testbed is the 2024-25 season. The architecture extends to earlier seasons as data allows.

## 2. The landscape of player rating

### Box-score systems

The oldest and most available systems work entirely from the standard box score: points, rebounds, assists, steals, blocks, turnovers, and shot attempts. They can be computed for any season back to the 1980s.

**Player Efficiency Rating (PER)** was John Hollinger's attempt to fold everything into one per-minute number normalized so the league average is always 15. A 20 PER is well above average; 30 or above is an all-time great season.

**Win Shares (WS)** takes a different angle. Rather than measuring efficiency per minute, it allocates the team's actual wins back to individual players based on their offensive production and a defensive credit. The cumulative version (total Win Shares) grows with playing time; WS/48 normalizes it back to a per-minute rate.

**Box Plus/Minus (BPM)** tries to estimate what a player's presence adds per 100 possessions compared to an average player, derived from box-score rates and adjusted for team quality. It splits into Offensive BPM and Defensive BPM. VORP extends it into a cumulative value by multiplying by playing time and comparing to a replacement-level player rather than an average one.

**Game Score** (also Hollinger) is a simpler per-game summary that weights each box-score category by its approximate value. It is not normalized.

### Impact metrics

Box-score systems share a blind spot: they do not directly measure whether a player made their team better or worse. A prolific scorer who forces bad shots and plays poor defense can rate well on PER and WS. Lineup-based "impact" metrics try to fix this by measuring how the team's scoring margin changes when a player is on the floor versus off it, with various forms of regularization to handle the noise.

**RAPTOR** (FiveThirtyEight, 2013-14 through 2022-23) combined on/off lineup data with player tracking data. FiveThirtyEight shut down its sports coverage in April 2023, so RAPTOR has no 2024-25 values.

**DARKO DPM**, **EPM** (dunksandthrees), **LEBRON** (BBall-Index), and **ESPN RPM** are the main active impact metrics. Each uses some variant of regularized adjusted plus/minus, sometimes blended with box-score priors.

The core limitation is sample size: a player's on/off data in one season is much noisier than their box-score totals. These systems use regularization to pull noisy estimates toward a prior, but that makes them sensitive to how the prior is set.

### Human rankings

MVP vote share, All-NBA selections, and media top-100 lists measure something neither box nor impact models capture directly: reputation and narrative. A player with a great story can receive more MVP votes than their on-court numbers warrant; a player on a losing team can be underrated.

Including human rankings as a category lets us compare model-based and reputation-based consensus, and see where they disagree.

## 3. Do the systems agree?

![Agreement between each pair of systems: darker squares mean stronger rank correlation.](../generated/images/rank_agreement_heatmap.svg){#fig-agreement}

The box-score systems largely agree with each other at the top. PER and Game Score move closely together (0.83 on a 0-to-1 scale, among qualified 2024-25 players); PER also moves with BPM, though less tightly (0.49), and Game Score with BPM (0.47). Win Shares and WS/48 are nearly interchangeable (0.97), but both diverge sharply from PER and Game Score: PER and Win Shares overlap almost not at all (0.01).

That near-zero overlap stands out: PER and Win Shares rank players almost independently of each other, despite both claiming to measure overall contribution. Win Shares rewards defensive-minded players on good teams (Ivica Zubac, Walker Kessler) who generate stops without the counting-stat production that PER credits. PER rewards volume scorers at high efficiency.

MVP votes and All-NBA points agree closely with each other (0.89), less so with the box-score systems. Game Score and MVP share move in the same direction, but loosely (0.28 out of a possible 1.0): voters weight narrative, team success, and season arc, not just nightly production.

The exact correlation figures are in `docs/player_ranking_overview_results.md`.

## 4. What each system uniquely sees

Not all systems add independent information. The analysis of what each system adds beyond what the others already capture (see results) shows which systems see something genuinely different, and which are mostly duplicating one another.

The "system outliers" chart shows the players each system rates most above and below the consensus. This is where methodological differences become visible: a system that captures defensive value heavily will love rim protectors; a system that penalizes inefficient volume scoring will discount high-usage players with middling true shooting.

![Players each system rates most above or below the consensus.](../generated/images/system_outliers.svg){#fig-outliers}

## 5. The two uber ratings

Two combined ratings are built from the systems present in the data:

**Consensus rating:** the average z-score across all systems. This measures what the crowd of methodologies agrees on, not what is best-supported by any one theory. The 2024-25 consensus top five: Shai Gilgeous-Alexander, Giannis Antetokounmpo, Jayson Tatum, Nikola Jokić, Donovan Mitchell.

**Wins-predictive rating:** a combination of system z-scores weighted by how well each system (aggregated to team level) predicts actual team wins. The two ratings correlate at Spearman r = 0.98: they agree on who the very best players are. But the wins-predictive rating pushes SGA, Giannis, and Tatum even higher relative to the consensus, because their teams won the most games. Conversely, players on losing teams (Brandon Ingram, Vasilije Micic) rate lower on the wins-predictive scale than on the consensus — their numbers look good in context but their teams still lost.

![Consensus versus wins-predictive rating: each dot is a player; distance from the diagonal marks where the two approaches disagree.](../generated/images/uber_rating_comparison.svg){#fig-uber}

## 6. Stars matter more than rank implies

![All ten systems normalized to the same scale: value falls steeply in the top tier for every methodology, but at very different rates.](../generated/images/all_systems_distributions.svg){#fig-all-dist}

PER spreads relatively evenly among qualified 2024-25 players: the top 5% account for only 8.5% of total value. The gap between the 50th and 95th percentile player in PER is smaller than it looks on a ranked list.

Win Shares and VORP are a different story. The top 5% of players hold 32% of total positive Win Shares; VORP piles up almost as steeply. Both concentrate at the top because they multiply rate by minutes, and the best players lead in both.

![Gini coefficients by system: Win Shares and VORP concentrate value at the top far more than rate metrics like PER or Game Score.](../generated/images/gini_by_system.svg){#fig-gini}

![Rating value versus rank for cumulative and rate metrics: cumulative metrics (Win Shares, VORP) fall steeply among the top players; rate metrics stay flatter across the distribution.](../generated/images/rank_value_distributions.svg){#fig-distributions}

![The gap between rank 1 and rank 10 is far larger than rank 10 to rank 50 in value-based systems.](../generated/images/ordinal_vs_value_gap.svg){#fig-gap}

The visual gap between rank 1 and rank 10 looks like 10 spots on a list. The numerical gap is often several times larger than the gap between rank 10 and rank 50.

The data is consistent with the explanation that elite talent is worth more than rank implies: having the best player on the roster matters more to team success than being one spot ahead of the second-best, because team results depend on the ceiling in ways that raw averages don't capture.

## 7. Who lands in the top 20

The table below shows the top 20 players under each system and their raw score. The gap between rank 1 and rank 20 is the most direct read on how concentrated value is: a large gap means the top player is in a different tier from the rest; a small gap means the list is relatively flat.

![Top 20 players and their raw scores under each of the ten rating systems. Blue row is rank 1, red row is rank 20.](../generated/images/top20_by_system.svg){#fig-top20}

## 8. A note on the recomputed formulas

The box-score recompute engines (PER, Win Shares, BPM, VORP) implement the published methodologies from Hollinger and Basketball-Reference, but they are approximations. The most precisely recomputed metric is PER: the league-average normalization produces values in the expected range (mean ~15, Nikola Jokić in the high 20s). The Win Shares and BPM formulas use simplified versions of the defensive credit and team-context adjustments, and the resulting absolute values differ from Basketball-Reference's published figures. The relative rankings within each system are directionally correct.

A Phase 3 planned improvement is to spot-check the recomputed values against BBR for 5-10 known players, and to tighten the BPM per-100-possession rate computation (currently using player-possession-based denominators rather than the team-possession-based denominators BBR uses). For comparison purposes (which system ranks whom higher or lower), the current implementation is sufficient. For absolute values, treat the recomputed BPM/VORP as approximations.

## 9. Limitations

The 2024-25 testbed is a single season. Stability analysis (do the same players rate highly across multiple seasons?) requires multi-season data and is a natural extension.

The crosswalk matching rate for each third-party source is reported in `docs/player_ranking_overview_results.md`. Players who could not be matched are listed there; they are excluded from the cross-system comparison but retained in the unified table.

RAPM (regularized adjusted plus/minus from play-by-play stints) is not recomputed here. It requires play-by-play data at a volume that pushes beyond what this project tackles; a public RAPM snapshot can be dropped into the cache schema when available.

The tracking-based and team-internal systems (Second Spectrum, franchise models, Synergy) are documented in the inventory but not accessible. The blind spot is acknowledged.

## Appendix A: Companion Documents

- [Full analysis output](player_ranking_overview_results.md)
- [System inventory and acquisition paths](player_ranking_overview_inventory.md)
- [Methods and statistics](player_ranking_overview_stats_explainer.md)
