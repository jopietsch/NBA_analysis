# Player Ranking Overview: Findings Outline

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

Internal outline. Cross-referenced to player_ranking_overview_results.md.
Technical shorthand fine here.

---

## Structure

### § 1. Introduction
- Hook: every NBA list ranks players in order, but ordinal rank hides how much bigger the gap is between #1 and #10 than between #10 and #20
- Thesis: the systems agree on who the stars are, disagree on how much the rest of the roster matters; combining them reveals what each uniquely sees

### § 2. The landscape: what we're measuring and what we can't
- Box-score recompute systems (PER, WS, BPM, VORP, Game Score) — what they measure, how they differ conceptually
- Impact metrics (RAPTOR, DARKO, EPM, LEBRON, ESPN RPM) — what "+/-" lineups-based systems try to capture that box stats miss
- Human rankings (MVP votes, All-NBA, media top-100) — reputation vs. production
- Blind spot: tracking-based and proprietary models

### § 3. Do the systems agree?
- Spearman correlation matrix → they agree on the top 10-15 stars, diverge on the 50th-100th percentile
- Key finding from results: [pull r-values from results.md]
- "Agreement heatmap" chart reference

### § 4. What each system uniquely sees
- Unique R² table: which systems add independent signal vs. which are near-redundant
- System outliers chart: players each system loves vs. consensus — likely a defender/playmaker split for box vs. impact models
- Key finding: [pull from results.md — likely BPM/RAPTOR see defenders better than PER does]

### § 5. The two uber ratings
- Consensus (z-score average): what the crowd of systems agrees on
- Wins-predictive: which combination of systems actually explains team wins
- Comparison: where do they differ? (likely: wins-predictive rewards efficiency less, raw counting less, and team-context adjustment more)
- Chart: scatter of the two

### § 6. The power of star players (distribution section)
- Key result: cumulative metrics (WS, VORP, RAPTOR WAR) are right-skewed; rate metrics (PER, BPM) are near-normal among qualified players
- Gini + top-5% share: stars hold outsized fraction of total value in cumulative systems
- The rank-value chart: what ordinal flattening looks like visually
- Plain-language explanation: why the #1 player is worth much more than being one spot above #2 implies

### § 7. Limitations and open questions
- Crosswalk coverage for each third-party source
- RAPM deferred
- Single season testbed: multi-season needed to assess stability
- Proprietary blind spot acknowledged

---

## Key numbers to pull from results.md (fill after pipeline runs)

- N qualified players
- Which systems are present
- Spearman r between PER and BPM, PER and RAPTOR, BPM and RAPTOR
- Top-5 consensus players
- Top-5 wins-predictive players (compare to consensus)
- Biggest consensus/wins-predictive divergences
- Gini for WS, VORP vs. PER, BPM
- Top-5% share for at least one cumulative and one rate metric
