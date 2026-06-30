# Player Rating Overview: Findings Outline

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

Internal outline.
Cross-referenced to player_rating_overview_results.md.
Technical shorthand fine here.
Reflects the current pipeline: 14 recomputed box-score systems plus a from-scratch RAPM (bare single-season + prior-informed multi-year RAPM_MY); other impact metrics and human rankings surveyed but not recomputed.

---

## Structure (matches the 12 sections in the findings)

### Intro (question-driven; before §1)
- Hook: the rating that best describes a finished season forecasts the next worst. PER ~64% describe vs ~25% forecast, averaged across 30 seasons.
- Three questions: (1) do the systems agree? (2) what does each uniquely capture? (3) how should they be combined?
- Settled up front: no single best system; agree at the top, diverge below; value is top-heavy (gap #1→#10 >> #10→#50).
- Testbed 2024-25; 14 box-score systems + RAPM/RAPM_MY recomputed; other impact + human rankings surveyed only. Two panels span 30 seasons back to 1996-97.

### § 1. The landscape of player rating
- Box-score (recomputed, present): Game Score, PER, Win Shares, WS/48, BPM, OBPM, DBPM, VORP.
- Impact metrics (surveyed): RAPTOR, EPM, LEBRON, DARKO, DRIP, ESPN RPM. RAPM backbone + box-score prior; noise/regularization.
- Human rankings (surveyed, not included): MVP votes, All-NBA, media top-100.
- Practitioner trust (external, cited in resources bibliography): HoopsHype survey of 29 execs, DARKO top at 8 votes; Dunks & Threes retrodiction order EPM > RPM > RAPTOR > BPM 2.0.

### § 2. Do the systems agree?
- Spearman matrix. Tight: PER-Game Score 0.831, BPM-VORP 0.972. Moderate: PER-WS 0.759, WS-WS/48 0.695. Loose: PER-BPM 0.489, Game Score-BPM 0.469.
- Player-level divergence even where overall correlation is high: WS favors efficient bigs (Domantas Sabonis, Nikola Jokić); PER favors high-usage scorers (Zion Williamson, Anthony Davis).
- RAPM sits apart: agrees with box scores at 0.22; bare 2024-25 puts reserve Isaiah Joe at #201 in consensus. Fixed RAPM_MY agrees with consensus 0.58 (up from 0.37), top Shai Gilgeous-Alexander/Giannis Antetokounmpo; RAPM_MY (combined only) feeds the consensus.
- Chart: rank-agreement heatmap.

### § 3. What the field has learned about evaluating these metrics
- Two community tests: retrodiction (1st-half → 2nd-half outcomes) and team-wins prediction; both reward a RAPM backbone + calibrated box-score prior. Academic caveat: complex metrics don't reliably beat simple ones as inputs to downstream salary/wins models.
- Direct describe test (held-out teams, 2024-25): PER best, ~72% of team point-diff, above the plus/minus metrics.
- Forecast test (prior-season ratings predict this season): order flips, PER ~15%, plus/minus best (BPM ~50%). Coverage ~89%.
- Multi-season panel (30 seasons / 29 handoffs back to 1996-97): PER describes ~64%, forecasts ~25%; best forecaster Game Score ~42%; BPM beats PER forecasting 20/29 handoffs.
- Impact-era panel (13 seasons from 2013-14, box scores vs RAPM): bare RAPM forecasts 9/10 (~17%, describe ~34% but mechanical), RAPM_MY 8/10 (~24%), both below box scores; top Game Score ~45%.
- Stability (year-over-year): Game Score retains 68% of its top 20, PER 64% (chance ~5%); steadiest Game Score 0.85, jumpiest BPM 0.70; 29 pairs. Stickiness cuts against forecasting (PER sticky but weak forecaster; BPM jumpy but better).
- Charts: retrodiction, next-season retrodiction, panel describe-vs-forecast, impact panel, rating stability.

### § 4. What each system uniquely sees
- Overlap R² (own kin held out; high = redundant): most redundant PER 0.893, Game Score 0.890; mid WS 0.683, VORP 0.586; least redundant BPM 0.526, DBPM 0.516. Caveat: BPM/VORP/RAPM are approximate recomputes, so low overlap may be noise, not signal.
- System-outliers chart: who each system rates above/below consensus.

### § 5. The two uber ratings
- Consensus (average normalized score). Top 5: Nikola Jokić 2.92, Shai Gilgeous-Alexander 2.72, Giannis Antetokounmpo 2.31, Tyrese Haliburton 1.65, James Harden 1.62.
- Wins-predictive (weighted by team-wins prediction). Top: Giannis Antetokounmpo 3.72, Shai Gilgeous-Alexander 3.45.
- Consensus vs. wins-predictive Spearman 0.925. Top riser Giannis Antetokounmpo +1.41; top faller Dillon Jones -1.23. Wins-predictive lifts stars on winning teams, discounts production on losing teams.

### § 6. Stars matter more than rank implies (distribution section)
- Rate metrics spread evenly: PER top-5% share 8.5%. Cumulative top-heavy: WS top-5% ~15%, VORP ~32%.
- Power-law steepness (alpha): PER 0.13 (shallow), Consensus 0.31, Wins-Pred 0.32, VORP 0.36 (steepest). Two groups: straight-line power laws vs. benders (plus/minus rate metrics).
- RAPM full distribution (13 seasons, 4678 player-seasons, 49% below 0) is a symmetric bell, not a power law; VORP leans right (the tail a power law needs).
- Gini kept only as a cross-check; it misleads on 0-centered metrics (Consensus Gini 0.756 > WS 0.363, an artifact, not real top-heaviness).
- Charts: all-systems distributions, distribution shape, power-law small multiples, power-law fits, gini, rank-value curves, ordinal-vs-value gap.

### § 7. Who lands in the top 20
- Top-20-by-system table across the 14 systems; rank-1-to-rank-20 gap as a concentration read.

### § 8. Who rose and fell in the playoffs
- Box-score rate metrics recomputed on playoff games only (impact metrics can't: a playoff run is too few games). 96 players ≥ 150 playoff minutes; change measured against that peer group (strips the leaguewide playoff dip).
- Risers: Gary Trent Jr., Kawhi Leonard, Paolo Banchero. Fallers: Michael Porter Jr., Austin Reaves, Miles McBride, incl. regular-season consensus #1 Nikola Jokić. One postseason, not proof.

### § 9. Summary
- Re-answers the three questions: agree at the top / each captures less uniquely than it looks (heavy overlap) / two combined ratings agreeing at 0.925.
- Through-line: value is top-heavy. Caveat: single-season cross-system comparison is a snapshot; the describe-vs-forecast and stability panels (30 seasons) are the firmer results.

### § 10. A note on the recomputed formulas
- PER cleanest (mean ~15, Jokić low 30s). WS/BPM/VORP are approximations; absolute values differ from BBR.
- VORP inflation for high-steal defenders: VORP rates Dyson Daniels further above consensus than any player (per-100 denominator uses player-possessions not team-possessions). Also Ellis, Wallace, Dunn.

### § 11. Limitations
- Single-season cross-system testbed; only the describe-vs-forecast and stability panels reach across 30 seasons.
- RAPM now computed from play-by-play (2024-25 back to 2013-14, 554 players in 2024-25): bare = noisy, no prior; RAPM_MY = 3 pooled seasons + BPM prior (consensus corr 0.58); neither beats box scores at forecasting. No tracking data, so can't match EPM/LEBRON.
- Tracking/team-internal blind spot (Second Spectrum, Synergy, franchise models).
- Playoff small-sample limit for RAPM-based metrics.

### § 12. What a Bayesian lens would add
- Uncertainty ranges: single-number metrics hide a ~2-3 pts/100 band; apparent 8th-vs-12th disputes often within it.
- Playoff vs. regular season: update the full-season prior with playoff lineup data; posterior barely shifts on 6 games, more on a Finals run.
- Better consensus weighting: estimate system weights from multi-season retrodiction.

---

## Key numbers (from results.md)

- Players: 569 total, 375 qualified (≥ 500 min). Systems present: 14.
- Correlations: PER-Game Score 0.831, PER-WS 0.759, WS-WS/48 0.695, PER-BPM 0.489, Game Score-BPM 0.469, BPM-VORP 0.972.
- RAPM: box-score corr 0.22 (bare), consensus corr 0.37 (bare) → 0.58 (RAPM_MY).
- Describe vs forecast (panel, 30 seasons): PER 64% / 25%; best forecaster Game Score 42%.
- Consensus top 5: Nikola Jokić 2.92, Shai Gilgeous-Alexander 2.72, Giannis Antetokounmpo 2.31, Tyrese Haliburton 1.65, James Harden 1.62.
- Consensus vs. wins-predictive Spearman: 0.925. Top riser Giannis Antetokounmpo +1.41; top faller Dillon Jones -1.23.
- Concentration: PER top-5% 8.5%; Gini cross-check Consensus 0.756 vs WS 0.363 (artifact).
- Overlap R² (own kin held out; high = redundant): PER 0.893, Game Score 0.890 most redundant; BPM 0.526, DBPM 0.516 least; WS 0.683, VORP 0.586 mid. Recompute-noise caveat on BPM/VORP/RAPM.
- Playoffs: 96 players ≥ 150 min; top riser Gary Trent Jr., top faller Michael Porter Jr..
