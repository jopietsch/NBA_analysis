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

All of the major impact metrics share the same technical backbone: Regularized Adjusted Plus/Minus (RAPM), a ridge regression that estimates each player's per-100-possession contribution to scoring margin after stripping out the effects of teammates and opponents. Raw RAPM is noisy with one season of data, so every system adds a "prior" — a box-score estimate of what a player should be worth — to pull uncertain estimates toward something stable. The systems mostly differ in how that prior is built and what data feeds it.

**RAPTOR** (FiveThirtyEight, 2013-14 through 2022-23) combined on/off lineup data with player-tracking data (speed, distance, shot quality). FiveThirtyEight shut down its sports coverage in April 2023, so RAPTOR has no 2024-25 values. Historical data is downloadable from their GitHub.

**EPM** (dunksandthrees) uses a RAPM calculation with a Bayesian prior built from a highly optimized Statistical Plus/Minus model that incorporates player-tracking data. EPM is the only public metric that directly optimizes the weighting of each underlying stat by how quickly it stabilizes, which is one reason it tends to perform well in retrodiction tests.

**LEBRON** (BBall-Index) also uses a luck-adjusted RAPM with a box-score prior. "Luck adjustment" means the on/off data removes variance attributable to shot-making volatility rather than player skill. The prior coefficients come from PIPM (Player Impact Plus/Minus), an earlier metric by Jacob Goldstein that is no longer updated.

**DARKO DPM** is best thought of as a projection system rather than a season average. Like baseball projection systems (PECOTA, Steamer), DARKO weights recent games more heavily and updates daily, so it answers "what is this player's current true talent?" more than "how did this player perform this season?" That distinction matters when comparing across systems.

**DRIP** (Daily Updated Rating of Individual Performance, Opta Analyst) is similar to DARKO in structure: it now-casts current player talent by weighting recent performance more heavily, rather than averaging over the full season.

**ESPN RPM** used RAPM with a box-score prior from Jeremias Engelmann, who also created the foundational RAPM dataset that most other systems calibrate against. ESPN stopped publishing RPM publicly around 2023.

The core limitation across all these systems is sample size: a player's on/off data in one season is much noisier than their box-score totals. Regularization pulls noisy estimates toward a prior, which means the prior's assumptions matter a great deal, especially for players with limited minutes.

**Which metrics do practitioners trust?** A HoopsHype survey of 29 NBA front-office executives (2021) found DARKO DPM was the most preferred catch-all metric (8 respondents), followed by EPM and LEBRON. A retrodiction study by Dunks & Threes, comparing how well each metric predicts future game outcomes, put EPM first, followed by RPM, RAPTOR, and BPM 2.0 in that order. EPM and RPM were the only two metrics using RAPM directly with a Bayesian prior at the time of that study, which appears to be the structural feature that drives their edge over box-score-only approaches.

### Human rankings

MVP vote share, All-NBA selections, and media top-100 lists measure something neither box nor impact models capture directly: reputation and narrative. A player with a great story can receive more MVP votes than their on-court numbers warrant; a player on a losing team can be underrated.

Including human rankings as a category lets us compare model-based and reputation-based consensus, and see where they disagree.

## 3. Do the systems agree?

![Agreement between each pair of systems: darker squares mean stronger rank correlation.](../generated/images/rank_agreement_heatmap.svg){#fig-agreement}

The box-score systems largely agree with each other at the top. PER and Game Score move closely together (0.83 on a 0-to-1 scale, among qualified 2024-25 players); PER also moves with BPM, though less tightly (0.49), and Game Score with BPM (0.47). Win Shares and WS/48 are nearly interchangeable (0.97), but both diverge sharply from PER and Game Score: PER and Win Shares overlap almost not at all (0.01).

That near-zero overlap stands out: PER and Win Shares rank players almost independently of each other, despite both claiming to measure overall contribution. Win Shares rewards defensive-minded players on good teams (Ivica Zubac, Walker Kessler) who generate stops without the counting-stat production that PER credits. PER rewards volume scorers at high efficiency.

MVP votes and All-NBA points agree closely with each other (0.89), less so with the box-score systems. Game Score and MVP share move in the same direction, but loosely (0.28 out of a possible 1.0): voters weight narrative, team success, and season arc, not just nightly production.

The exact correlation figures are in `docs/player_ranking_overview_results.md`.

## 4. What the field has learned about evaluating these metrics

Not all player rating systems are equally trusted, and the analytics community has developed two main ways to test whether a metric is actually measuring what it claims to measure.

**Retrodiction** uses the first half of a season's games to predict game outcomes in the second half. A metric that genuinely captures player impact should let you predict which team wins when you know each team's lineup. This is the test used in the Dunks & Threes comparison study, which found EPM and RPM at the top, followed by RAPTOR and BPM 2.0. The structural feature that separated the top metrics from the rest: both used RAPM with a box-score prior, while lower-ranked metrics either skipped the prior or used only box-score data without the RAPM step.

**Team wins prediction** aggregates player ratings to the team level and asks how well the total predicts actual wins. This is what the HoopsHype executive survey used to rank metrics by RMSE, and it is also the logic behind the wins-predictive rating built in this report.

Both tests reward the same thing: a RAPM backbone stabilized by a well-calibrated box-score prior. That combination handles the two main failure modes — pure box-score metrics miss what a player does off the ball, and pure RAPM is too noisy with one season of data.

One important result from the academic literature runs against the intuition that more sophisticated is better: peer-reviewed research has found that complex metrics do not reliably outperform simpler ones when used as variables in salary or wins regressions. That is not a flaw in the metrics themselves. They are built to estimate player impact per possession, not to serve as inputs in every downstream analysis. The lesson is that a metric's predictive accuracy in a retrodiction test is not the same as its usefulness for a specific application, and the right tool depends on the question being asked.

## 5. What each system uniquely sees

Not all systems add independent information. The analysis of what each system adds beyond what the others already capture (see results) shows which systems see something genuinely different, and which are mostly duplicating one another.

The "system outliers" chart shows the players each system rates most above and below the consensus. This is where methodological differences become visible: a system that captures defensive value heavily will love rim protectors; a system that penalizes inefficient volume scoring will discount high-usage players with middling true shooting.

![Players each system rates most above or below the consensus.](../generated/images/system_outliers.svg){#fig-outliers}

## 6. The two uber ratings

Two combined ratings are built from the systems present in the data.

Each system uses a different scale — PER is centered around 15, BPM around 0, Win Shares in the single digits — so you cannot average them directly. A z-score converts each system to the same scale by asking: how many typical-player gaps above or below average is this player? A z-score of 0 means exactly average; +2 means two standard deviations above average (well into star territory); −1 means a step below average. Once every system is on this common scale, they can be combined.

**Consensus rating:** the average z-score across all systems. This measures what the crowd of methodologies agrees on, not what is best-supported by any one theory. The 2024-25 consensus top five: Shai Gilgeous-Alexander, Giannis Antetokounmpo, Jayson Tatum, Nikola Jokić, Donovan Mitchell.

**Wins-predictive rating:** a combination of those scores weighted by how well each system (aggregated to team level) predicts actual team wins. The two ratings correlate at Spearman r = 0.98: they agree on who the very best players are. But the wins-predictive rating pushes SGA, Giannis, and Tatum even higher relative to the consensus, because their teams won the most games. Conversely, players on losing teams (Brandon Ingram, Vasilije Micic) rate lower on the wins-predictive scale than on the consensus — their numbers look good in context but their teams still lost.

![Consensus versus wins-predictive rating: each dot is a player; distance from the diagonal marks where the two approaches disagree.](../generated/images/uber_rating_comparison.svg){#fig-uber}

Aggregating across systems is not unique to this report. HoopsHype publishes periodic "Analytics MVP" posts that combine EPM, LEBRON, DARKO, RAPTOR, and BPM into a single ranking, typically using a simple equal-weighted average. ESPN's #NBArank is a different kind of aggregate: journalists vote rather than models, making it closer to the human-reputation category than to a model combination. Some metrics do the aggregation internally: LEBRON, for example, blends a box-score prior with luck-adjusted on/off data as part of its own formula rather than publishing both separately and combining them downstream. What distinguishes the wins-predictive rating here is that the system weights are estimated from data (how well each system actually predicted team wins) rather than assigned by hand. The practical difference is small — the two ratings correlate at 0.98 — but the weights tell you which systems carried the most predictive signal for 2024-25, which is worth knowing.

## 7. Stars matter more than rank implies

![Rating systems normalized to the same scale: value falls steeply in the top tier for every methodology, but at very different rates.](../generated/images/all_systems_distributions.svg){#fig-all-dist}

PER spreads relatively evenly among qualified 2024-25 players: the top 5% account for only 8.5% of total value. The gap between the 50th and 95th percentile player in PER is smaller than it looks on a ranked list.

Win Shares and VORP are a different story. The top 5% of players hold 32% of total positive Win Shares; VORP piles up almost as steeply. Both concentrate at the top because they multiply rate by minutes, and the best players lead in both.

![Gini coefficients by system: Win Shares and VORP concentrate value at the top far more than rate metrics like PER or Game Score.](../generated/images/gini_by_system.svg){#fig-gini}

The Gini coefficient measures how unequally a metric's value is distributed across players, on a scale from 0 (everyone rated the same) to 1 (one player holds all the value). A high Gini means the metric is top-heavy: the gap between the best player and an average one is large relative to the spread across the rest of the league. A low Gini means the metric treats most qualified players as roughly comparable, with only a small premium at the top. For this report the Gini chart makes a specific point: a metric's Gini tells you how much it will disagree with ordinal rank. Rate metrics like PER and Game Score have low Ginis, so ranks 10 through 50 are bunched close together in value. Cumulative metrics like Win Shares and VORP have high Ginis, so the top handful of players are far ahead of everyone else in actual value — a gap that a ranked list, by construction, cannot show.

![Each line shows a system's value as a percentage of its rank-1 player. Win Shares and VORP fall steeply; PER and BPM stay much flatter.](../generated/images/rank_value_distributions.svg){#fig-distributions}

![The gap between rank 1 and rank 10 is far larger than rank 10 to rank 50 in value-based systems.](../generated/images/ordinal_vs_value_gap.svg){#fig-gap}

The visual gap between rank 1 and rank 10 looks like 10 spots on a list. The numerical gap is often several times larger than the gap between rank 10 and rank 50.

The data is consistent with the explanation that elite talent is worth more than rank implies: having the best player on the roster matters more to team success than being one spot ahead of the second-best, because team results depend on the ceiling in ways that raw averages don't capture.

## 8. Who lands in the top 20

The table below shows the top 20 players under each system and their raw score. The gap between rank 1 and rank 20 is the most direct read on how concentrated value is: a large gap means the top player is in a different tier from the rest; a small gap means the list is relatively flat.

![Top 20 players and their raw scores under each of the ten rating systems. Blue row is rank 1, red row is rank 20.](../generated/images/top20_by_system.svg){#fig-top20}

## 9. A note on the recomputed formulas

The box-score recompute engines (PER, Win Shares, BPM, VORP) implement the published methodologies from Hollinger and Basketball-Reference, but they are approximations. The most precisely recomputed metric is PER: the league-average normalization produces values in the expected range (mean ~15, Nikola Jokić in the high 20s). The Win Shares and BPM formulas use simplified versions of the defensive credit and team-context adjustments, and the resulting absolute values differ from Basketball-Reference's published figures. The relative rankings within each system are directionally correct.

A Phase 3 planned improvement is to spot-check the recomputed values against BBR for 5-10 known players, and to tighten the BPM per-100-possession rate computation (currently using player-possession-based denominators rather than the team-possession-based denominators BBR uses). For comparison purposes (which system ranks whom higher or lower), the current implementation is sufficient. For absolute values, treat the recomputed BPM/VORP as approximations.

One consequence is visible in the data: Dyson Daniels ranks 2nd in VORP in this dataset, just behind Shai Gilgeous-Alexander. On Basketball-Reference's published figures, Daniels ranks well outside the top 10. The difference traces to steals: Daniels led the league in steals in 2024-25, and the DBPM formula credits steals heavily. Our approximation amplifies that credit further because it uses player-possession denominators rather than team-possession denominators, inflating per-100 steal rates. His PER of 16.4 and Win Shares near zero tell a more representative story of a strong defensive specialist whose overall value does not place him among the top two players in the league.

## 10. Limitations

The 2024-25 testbed is a single season. Stability analysis (do the same players rate highly across multiple seasons?) requires multi-season data and is a natural extension.

The crosswalk matching rate for each third-party source is reported in `docs/player_ranking_overview_results.md`. Players who could not be matched are listed there; they are excluded from the cross-system comparison but retained in the unified table.

RAPM (regularized adjusted plus/minus) is the technical backbone of every serious modern impact metric — EPM, LEBRON, DARKO, RAPTOR, and RPM all build on it — but it is not recomputed here. Computing RAPM requires play-by-play data broken into stints (which lineup was on the floor for each possession), then a simultaneous ridge regression over all players. That data volume and the regression setup push beyond what this project tackles in its current form. The practical consequence: the only impact signal in our system comes through BPM, which estimates what RAPM would say using box-score inputs. BPM is a reasonable proxy but known to miss things that only appear in the lineup data, particularly for players whose impact on team defense does not show up in personal stats. A public RAPM snapshot can be dropped into the cache schema when one is available.

The tracking-based and team-internal systems (Second Spectrum, franchise models, Synergy) are documented in the inventory but not accessible. The blind spot is acknowledged.

## Appendix A: Companion Documents

- [Full analysis output](player_ranking_overview_results.md)
- [System inventory and acquisition paths](player_ranking_overview_inventory.md)
- [Methods and statistics](player_ranking_overview_stats_explainer.md)
