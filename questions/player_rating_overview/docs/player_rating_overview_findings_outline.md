# Player Rating Overview: Findings Outline

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

Internal outline. Cross-referenced to player_rating_overview_results.md.
Technical shorthand fine here. Reflects the current 11-box-score-system pipeline
(human rankings removed; impact metrics surveyed but not recomputed).

---

## Structure (matches the 11 sections in the findings)

### § 1. Introduction
- Hook: ordinal rank compresses; the gap between #1 and #10 is not the gap between #10 and #20.
- Thesis: two combined ratings answer two questions, what the systems agree on vs. which combination best predicts team wins.
- Testbed: 2024-25; 11 box-score systems recomputed; impact metrics and human rankings surveyed but not included.

### § 2. The landscape of player rating
- Box-score (recomputed, present): Game Score, PER, Win Shares, WS/48, BPM, OBPM, DBPM, VORP.
- Impact metrics (surveyed, not recomputed): RAPTOR, EPM, LEBRON, DARKO, DRIP, ESPN RPM. RAPM backbone + box-score prior; noise/regularization.
- Human rankings (surveyed, not included): MVP votes, All-NBA, media top-100.
- Practitioner trust (external, cited in resources bibliography): HoopsHype survey of 29 execs, DARKO top at 8 votes; Dunks & Threes retrodiction order EPM > RPM > RAPTOR > BPM 2.0.

### § 3. Do the systems agree?
- Spearman matrix. Tight: PER-Game Score 0.831, BPM-VORP 0.972. Moderate: PER-WS 0.759, WS-WS/48 0.695. Loose: PER-BPM 0.489, Game Score-BPM 0.469.
- Player-level divergence even where overall correlation is high: WS favors efficient bigs (Sabonis +2.66, Zubac +2.31 vs. consensus); PER favors high-usage scorers (Zion +1.90, Porziņģis +1.56).
- Chart: rank-agreement heatmap.

### § 4. What the field has learned about evaluating metrics
- Two tests: retrodiction (first half predicts second half) and team-wins prediction.
- Both reward RAPM backbone + calibrated box-score prior.
- Academic caveat: complex metrics do not reliably beat simple ones as inputs to downstream salary/wins models.

### § 5. What each system uniquely sees
- Unique R²: BPM/OBPM/DBPM 1.000; PER 0.893; Game Score 0.888; VORP 0.872; WS 0.867; WS/48 0.838.
- System-outliers chart: who each system rates above/below consensus (e.g. DBPM discounts the offensive stars: Jokić -3.32, Giannis -3.31, SGA -3.11).

### § 6. The two uber ratings
- Consensus (average normalized score). Top 5: Jokić 2.78, SGA 2.55, Giannis 2.25, Harden 1.62, Young 1.61.
- Wins-predictive (weighted by team-wins prediction). Top 5: Jokić 3.71, SGA 3.69, Giannis 3.22, Harden 2.42, Daniels 2.27.
- Consensus vs. wins-predictive Spearman 0.938. Risers: SGA +1.45, Giannis +1.25, Gafford +1.15, Wembanyama +0.99, Caruso +0.97. Fallers: Micic -1.17, AJ Johnson -1.16, Cody Williams -0.98.
- Illustration: Jokić tops both; SGA close second and the largest riser into wins-predictive.

### § 7. Stars matter more than rank implies (distribution section)
- Rate metrics spread evenly: PER top-5% share 8.5% (Gini 0.159). Cumulative metrics top-heavy: WS top-5% 14.8% (Gini 0.363), VORP 31.9% (Gini 0.749); BPM also high (32.2%, Gini 0.767).
- Charts: all-systems distributions, Gini by system, rank-value curves, ordinal-vs-value gap.
- Point: cumulative metrics' high Gini is how much they disagree with ordinal rank.

### § 8. Who lands in the top 20
- Top-20-by-system table across the 11 systems; rank-1-to-rank-20 gap as a concentration read.

### § 9. A note on the recomputed formulas
- PER cleanest (mean ~15, Jokić high 20s). WS/BPM/VORP are approximations; absolute values differ from BBR.
- VORP inflation for high-steal defenders: VORP rates Daniels further above consensus than any player (+3.09); per-100 denominator uses player-possessions not team-possessions. Also Ellis, Wallace, Dunn.

### § 10. Limitations
- Single-season testbed; multi-season needed for stability.
- RAPM not recomputed; only impact signal is BPM as a box-score proxy.
- Proprietary/tracking blind spot (Second Spectrum, Synergy, franchise models).
- Playoff small-sample limit for RAPM-based metrics.

### § 11. What a Bayesian lens would add
- Uncertainty ranges: single-number metrics hide a ~2-3 pts/100 band; apparent 8th-vs-12th disputes often within it.
- Playoff vs. regular season: update the full-season prior with playoff lineup data; posterior barely shifts on 6 games, more on a Finals run.
- Better consensus weighting: estimate system weights from multi-season retrodiction.

---

## Key numbers (from results.md)

- Players: 569 total, 375 qualified (>= 500 min). Systems present: 11.
- Correlations: PER-Game Score 0.831, PER-WS 0.759, WS-WS/48 0.695, PER-BPM 0.489, Game Score-BPM 0.469, BPM-VORP 0.972.
- Consensus top 5: Jokić 2.78, SGA 2.55, Giannis 2.25, Harden 1.62, Young 1.61.
- Wins-predictive top 5: Jokić 3.71, SGA 3.69, Giannis 3.22, Harden 2.42, Daniels 2.27.
- Consensus vs. wins-predictive Spearman: 0.938. Top riser SGA +1.45; top faller Micic -1.17.
- Concentration (top-5% share / Gini): PER 8.5% / 0.159, WS 14.8% / 0.363, VORP 31.9% / 0.749, BPM 32.2% / 0.767.
- Unique R²: BPM/OBPM/DBPM 1.000; PER 0.893; Game Score 0.888; VORP 0.872; WS 0.867; WS/48 0.838.
