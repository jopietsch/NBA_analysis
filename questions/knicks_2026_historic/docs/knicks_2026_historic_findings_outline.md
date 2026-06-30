# Knicks 2026 Historic Run — Findings Outline

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

Internal analyst reference.
Cross-referenced to `knicks_2026_historic_results.md`.
Update when findings prose or RESULTS change.

---

## §1. The Verdict (Up Front)

- **Record:** 16-3, win rate 0.842, 88th pct among 43 champions (1983-84 through 2025-26).
- **Raw margin:** +14.9 pts/game, 100th pct (best in dataset).
- **Adj margin (reg-SRS):** +11.2 pts/game, 100th pct (best in dataset). Opp SRS weighted by games played per series.
- **Pace caveat:** 2025-26 is highest-scoring era (115.6 pts/team/game); but possessions only ~4% above average — efficiency, not pace. Per-100-poss margin stays #1.
- **East strength:** West-East SRS gap +0.39 pts/game = 37th pct of West dominance (below historical mean +0.78). East was not weak.
- **Health:** All four opponents essentially fully healthy (avg 98%). No injury asterisk.
- **Spurs:** Final-round opponent elevated from reg-SRS +8.28 to playoff SRS +14.48 — the biggest improvement of any Knicks opponent.
- knicks_2026_historic_results.md refs: §1 THE RAW CLAIM, §10 VERDICT

## §2. The Raw Numbers

- 16-3 record; win rate 0.842 vs. champion mean 0.752; best (2016-17 Warriors) 0.941.
- +14.9 pts/game margin, 100th pct; mean among champions +7.0 pts/game.
- 95% CI on margin (19 games): [+7.4, +22.4]. Even lower bound ranks 63rd pct.
- Round breakdown: Hawks 4-2 (+17.5), 76ers 4-0 (+22.2), Cavaliers 4-0 (+19.2), Spurs 4-1 (+2.4).
- Finals: 4 of 5 games decided by 4 pts or fewer.
- knicks_2026_historic_results.md refs: §1 THE RAW CLAIM

## §3. Was the East Weak?

- West-East SRS gap +0.39 pts/game = 37th pct. Historical mean +0.78, std 1.81. Well within normal variation (z = -0.21).
- East inter-conference win rate 0.487 (near parity). 37th pct (100th = worst for East).
- Top 3 most West-dominant: 2013-14 (+4.08), 2003-04 (+3.73), 2000-01 (+3.11). 2025-26 well below those.
- Knicks games-weighted opp SRS +3.67 = 49th pct among champions (mean +3.68). Schedule at historical median.
- knicks_2026_historic_results.md refs: §2 WAS THE EAST WEAK, §3 HOW WEAK IS THE EAST HISTORICALLY, §4 WHO DID THE KNICKS BEAT

## §4. Opponent-Adjusted Dominance

- Adj margin +11.23 pts/game (raw +14.89 minus games-wtd opp SRS +3.67) = 100th pct.
- Top 5: 2025-26 +11.23, 2016-17 Warriors +10.23, 1986-87 Lakers +9.52, 1990-91 Bulls +9.20, 1985-86 Celtics +7.72.
- Playoff overperformance vs. reg-SRS prediction: +12.52 pts/game, 97.7th pct (2nd all-time behind 2000-01 Lakers +14.49).
- Playoff SRS +17.53 vs. reg-season SRS +6.05 = elevation +11.48, 97.7th pct (2nd all-time, behind 2000-01 +12.58).
- knicks_2026_historic_results.md refs: §5 OPPONENT-ADJUSTED DOMINANCE

## §5. Was the East Weak in the Playoffs?

- Each opponent's playoff SRS computed excluding Knicks series (independent read). Hawks excluded (no other playoff games).
- 76ers: reg SRS -0.27, playoff SRS -1.43 (gap -1.16); Cavaliers: reg +3.77, playoff +2.32 (gap -1.45). Both slight dips but based on few games.
- Spurs: reg SRS +8.28, playoff SRS +14.48 (gap +6.20) — based on full West bracket, most independent. Biggest improvement of any Knicks opponent.
- Full-run playoff-SRS-adjusted margin: +9.05 pts/game, 100th pct. Effectively tied with 1986-87 Lakers +8.99.
- knicks_2026_historic_results.md refs: §6 ROUND-BY-ROUND (playoff SRS table)

## §6. Both Finalists Were the Biggest Risers

- Knicks: reg SRS +6.05 → playoff SRS +17.53, elevation +11.48 — largest of any 2026 playoff team.
- Spurs: reg SRS +8.28 → playoff SRS +15.13, elevation +6.85 — second largest.
- OKC led regular season (+11.04) but barely changed (+0.38 elevation).
- Finals paired the two biggest risers in the field, not the two best regular-season teams.
- Note: Spurs playoff SRS here (+15.13) includes the Knicks series; the §5 independent measure (+14.48) excludes it.
- knicks_2026_historic_results.md refs: §6 ROUND-BY-ROUND (field elevation table)

## §7. Other Context

- Clutch (decided by <=5 pts): 31.6% of games, 83.7th pct (mean 0.256).
- Home: 9 games, 77.8% win rate, 23rd pct vs. champions (below average at home).
- Away: 10 games, 90.0% win rate, 97.7th pct (better than all but one champion).
- The road dominance is the unusual piece; the home number is ordinary.
- knicks_2026_historic_results.md refs: §7 OTHER DEFLATORS

## §8. What the Betting Market Said

- 16-3 ATS; avg beat spread by +16.9 pts/game across 19 games.
- ATS vs. East rounds: 14-0 (R1 6/6 +21.5, R2 4/4 +26.2, CF 4/4 +22.0).
- Finals ATS: 2-5, avg margin essentially on the spread (+2.4 actual vs. +2.5 spread).
- Note: ATS margin is not independent of raw margin — it's the same scoreline minus a near-zero spread. Also series correlation reduces effective sample from 19 to ~7.
- knicks_2026_historic_results.md refs: §12 BETTING-MARKET EXPECTATIONS

## §9. Opponent Health (No Injury Asterisk)

- Availability: Hawks 100%, 76ers 96%, Cavaliers 97%, Spurs 100%.
- Avg 98%; most depleted was 76ers at 96%. Spurs fully intact.
- Definition: rotation players averaging >=15 min/game across all their 2025-26 playoff appearances.
- knicks_2026_historic_results.md refs: §11 OPPONENT PLAYER AVAILABILITY

## §10. How Solid Is the #1 Ranking?

- Bootstrap (20,000 re-draws): #1 in 59.6% of re-runs; top 3 in 69.9%; top 5 in 82.4%. 90% interval on adj margin: [+5.08, +17.71].
- Empirical-Bayes shrinkage: 19 games pin down only 41% of estimate; shrunken margin +6.50 pts/game (95% CI [+1.53, +11.48]), still beats 83% of champions.
- Adding opponent-SRS uncertainty barely moves result: #1 chance stays ~59.4%. Game variance dominates.
- Hierarchical (partial-pooling) test — every champion treated as uncertain: Knicks posterior mean +4.70 pts/game (90% CI [+1.80, +7.60]). P(true #1) = 9%. P(top 3) = 22.8%. Median rank 9.
- Streakiness (huge sweeps + tight Finals) makes the run weaker evidence than a steady one — hence the hard pull from +11.2 to ~+4.7 in the hierarchical model.
- Honest bottom line: clearly elite, very likely top-handful all-time, but data cannot crown them the single best. Chance of being true #1 runs from ~60% (holding history fixed) to ~9% (fairest test).
- knicks_2026_historic_results.md refs: §13 ROBUSTNESS, §14 HIERARCHICAL

## §11. A Second Opinion: Other Rating Systems

- Bradley-Terry (wins-only, no margins): Knicks adj margin +11.37, rank #1 of 43. Correlation with SRS-adjusted: +0.990. Blowouts are not an artifact — dominance is real.
- Capped-margin SRS (clip each game at ±15, robust to blowouts): adj margin +11.93, rank #1 of 43, corr with SRS +0.996. Schedule strength isn't a blowout artifact either.
- Elo (recency-weighted): opp rating +5.53 (tougher than SRS's +3.67 — opponents played well down the stretch). Elo-adjusted margin +9.36, rank #3 of 43 (behind 2016-17 Warriors and 1990-91 Bulls).
- All four systems put Knicks in top three (#1 on three; #3 only on Elo). What shifts them off #1 is crediting opponents' recent form (Elo), not stripping out margins (BT) or capping blowouts.
- knicks_2026_historic_results.md refs: §15 ELO CROSS-CHECK, §16 WINS-ONLY (BRADLEY-TERRY) CROSS-CHECK, §21 CAPPED-MARGIN (ROBUST) SRS CROSS-CHECK

## §12. How Unlikely Was a 16-3 Run?

- Forward model (reg-season SRS only): Knicks given only 14.7% title probability (Spurs out-rated them in regular season).
- Expected losses in title run: 6.5 (actual: 3). P(championship run losing <=3 games): 6.7%. P(title AND <=3 losses): 1.0%.
- Path-only caveat: model follows only the Knicks' realized bracket, not the full field. Strongest reg-season team was Oklahoma City Thunder (+11.04 SRS), ahead of the Spurs (+8.28); OKC exited before the Finals so only the Spurs are scored.
- Echoes the margin overperformance in §4: the Knicks played far above their regular-season level.
- knicks_2026_historic_results.md refs: §18 SERIES-LEVEL WIN-PROBABILITY MODEL

## §13. What Does NOT Diminish the Run

- Synthesis section (prose only, no new RESULTS analysis): scorecard of the six deflationary objections, each with a verdict and a pointer to the section that tests it.
- East weak → no (§3, gap +0.39); bracket soft → no (§3–§4, opp SRS +3.67, 49th pct); early-round teams fading → a little at the edges (§5, 76ers/Cavs ~1.2–1.5 below on few games, Spurs +6.2); margins padded → no (§11, wins-only #1); scoring-era inflation → mostly no (§14, per-possession still #1); opponent injured → no (§9, 98% health).
- The one genuine caveat is not on the list: 19-game small sample → single best only ~9% under the fairest test (§10–§11).
- Full per-objection treatment lives in the companion doc `knicks_2026_historic_investigation.md`.
- knicks_2026_historic_results.md refs: none new (points to §3, §4, §5, §9, §11, §13, §14 of RESULTS via the cited findings sections).

## §14. Comparing Across Eras: How Much of #1 Survives?

- The cross-era goal made first-class: "most dominant ever" depends on the yardstick. Lays the techniques side by side.
- Level adjustments leave the Knicks #1: scoring-share drops the raw margin to 3rd but the opp-adjusted margin stays #1; per-100 possessions (pace only) also #1 (2025-26 pace just ~4% above average, the scoring is efficiency).
- Dispersion adjustment is the one that changes it: SRS spread grew from 3.1 (1984) to 5.90 (2026); graded on the era's spread (z = adj_margin / season SRS SD), Knicks are +1.90 SD, rank #5 of 43; 16–17 Warriors lead (z +2.48).
- Ladder of ranks: raw 1st, opp-adj 1st, + scoring-share 1st, + per-100 1st, + spread-standardized 5th, Elo (recency) 3rd. Absolute measures → #1; relative measures (spread, recency) → top-five.
- knicks_2026_historic_results.md refs: §22 SPREAD-STANDARDIZED DOMINANCE (Z-SCORE); §9 ERA/PACE, §17 POSSESSIONS

## §15. Limitations

- 19 games: wide CI. Comparison set only 43 champions.
- Pre-1997: PLUS_MINUS null; derived from PTS (algebraically exact for game margins).
- Era comparisons rest on §14 choices; spread-standardized z mixes playoff margin with regular-season spread, so the exact rank (~#5) is not settled though the direction is robust.
- Playoff-SRS adjustment for §5 (opponent independent form) excludes Hawks (no independent data). Hawks series reads as raw only.

## §16. Methodology

- Python (pandas, numpy). Data via nba_api (LeagueGameFinder, LeagueStandingsV3).
- SRS: least-squares system (I − A) @ srs = mean_margin, constrained to sum = 0.
- Full details in knicks_2026_historic_results.md (linked as a companion doc, not inlined) and knicks_2026_analysis.py.

## Appendix A: Companion Documents

- Findings now end with "Appendix A: Companion Documents" linking the standalone Regression Results (RESULTS), The Investigation, the one-page Summary, the Stats Explainer, and this Outline.
- The report is built with `include_appendix=False`: RESULTS is no longer inlined as a report appendix; it is a linked companion doc.

## Appendix B: Every Champion, Opponent-and-Pace-Adjusted

- Full ranked table of all 43 champions by opp+pace-adjusted margin (rank, season, champion, Raw/Opp-adj/Opp+Pace). Knicks +10.05 #1, 2016-17 Warriors a hair behind (effective tie).
- Reading the shape: scores are bell-shaped, not a power law. Mean +3.29, 65% within 1 SD; Knicks sit +2.0 SD above the mean (the expected spot for the best of 43 draws). Statistical echo of §10: real #1, but the leading edge of an ordinary spread.
- knicks_2026_historic_results.md refs: §20 APPENDIX: FULL OPP+PACE-ADJUSTED CHAMPION RANKING

## Appendix C: The Full-Field Title Odds

- Forward bracket sim of all 16 playoff teams (generalizes §12's realized-path model): seeds into the fixed bracket, plays every round from reg-season SRS. Favorite = Oklahoma City Thunder at 54.5%, more than triple any rival.
- Knicks only 3.5% as the East 3-seed, far below the realized-path 14.7% (§12); gap is the bracket draw (East 1/2 seeds upset before NY met them), not play. Neither knows they would elevate.
- knicks_2026_historic_results.md refs: §19 FULL-FIELD TITLE ODDS (FORWARD BRACKET SIM)

---

## Key Numbers Registry

Cross-reference table: each row maps a prose claim to its authoritative value in `knicks_2026_historic_results.md`.
`update_registry_lines.py` (PostToolUse hook) auto-updates the first line number in "Findings location" whenever `knicks_2026_historic_findings.md` is edited.

| ID  | Findings location | Prose claim | knicks_2026_historic_results.md section | Authoritative value |
|-----|------------------|-------------|-------------------|---------------------|
| K01 | §1 L15  | 16-3, 88th pct win rate | §1 THE RAW CLAIM | win rate 0.842; 88.4th pct; mean 0.752 |
| K02 | §1 L16  | +14.9 pts/game raw margin, highest ever | §1 THE RAW CLAIM | +14.89 pts/game, 100th pct |
| K03 | §1 L18 | CI [+7.4, +22.4] | §1 THE RAW CLAIM | 95% CI [+7.4, +22.4] (t-interval, 19 games) |
| K04 | §1 L24 | adj margin +11.2 pts/game, first all-time | §5 OPPONENT-ADJUSTED | adj margin +11.23, 100th pct |
| K05 | §3 L84 | West-East SRS gap +0.39, 37th pct | §3 HOW WEAK IS THE EAST | gap +0.39, 37.2th pct; mean +0.78 |
| K06 | §1 L29 | 63% of seasons West more dominant | §3 HOW WEAK IS THE EAST | 37.2th pct West dominance → 62.8% more dominant |
| K07 | §1 L38 | Spurs SRS +8.28 reg → +15.13 playoff | §6 ROUND-BY-ROUND (field elevation table) | Spurs reg +8.28, playoff SRS +15.13 (incl. Knicks series), elev +6.85 |
| K08 | §1 L44 | avg opponent availability 98% | §11 OPPONENT PLAYER AVAILABILITY | avg health 98% |
| K09 | §2 L56 | win rate 0.842 vs. mean 0.752 | §1 THE RAW CLAIM | mean 0.752; best 0.941 |
| K10 | §2 L71 | 4 of 5 Finals games decided by 4 pts or fewer | §7 OTHER DEFLATORS | not directly; 31.6% games <=5 pts |
| K11 | §3 L89 | most West-dominant: 2013-14 +4.08 | §3 HOW WEAK IS THE EAST | top 3: 13-14 +4.08, 03-04 +3.73, 00-01 +3.11 |
| K12 | §3 L94 | opp SRS +3.67, 49th pct | §4 WHO DID THE KNICKS BEAT | games-wtd opp SRS +3.67, 48.8th pct |
| K13 | §4 L120 | Warriors adj +10.2 (2nd) | §5 OPPONENT-ADJUSTED (top 5) | 16-17: adj +10.23 |
| K14 | §4 L130 | overperformance +12.5 pts/game, 2nd all-time | §5 OPPONENT-ADJUSTED (overperf) | +12.52 pts/game, 97.7th pct |
| K15 | §4 L132 | elevation +11.48, 2nd all-time | §8 PLAYOFF SRS AND ELEVATION | elev +11.48, 97.7th pct; best 2000-01 +12.58 |
| K16 | §5 L172 | playoff-SRS-adj margin +9.1 pts/game, best | §6 ROUND-BY-ROUND (full-run po-SRS adj) | +9.05 pts/game, 100th pct; 86-87 +8.99 |
| K17 | §5 L166 | Spurs reg +8.28, playoff +14.5, +6.2 jump | §6 ROUND-BY-ROUND (opp SRS table) | Spurs PO SRS +14.48, gap +6.20 |
| K18 | §6 L186 | Knicks elevation +11.48, largest in 2026 field | §6 ROUND-BY-ROUND (field elevation) | Knicks +11.48, Spurs +6.85, Blazers +3.01 |
| K19 | §6 L191 | Spurs climbed to playoff SRS +15.13, rise +6.85 | §6 ROUND-BY-ROUND (field elevation) | Spurs reg +8.28, PO +15.13, elev +6.85 |
| K20 | §6 L205 | OKC led regular season (+11.04), barely changed (+0.38) | §6 ROUND-BY-ROUND (field elevation) | OKC reg +11.04, PO +11.42, elev +0.38 |
| K21 | §7 L220 | 31.6% games decided by <=5 pts, 83.7th pct | §7 OTHER DEFLATORS | 0.316; 83.7th pct; mean 0.256 |
| K22 | §7 L224 | home win rate 77.8%, 23rd pct | §7 OTHER DEFLATORS | home 9G, 0.778, 23.3th pct |
| K23 | §7 L226 | away win rate 90.0%, 98th pct | §7 OTHER DEFLATORS | away 10G, 0.900, 97.7th pct |
| K24 | §8 L239 | beat spread by avg +16.9 pts/game | §12 BETTING-MARKET | avg ATS margin +16.9; ATS record 16-3 |
| K25 | §8 L248 | 14-0 ATS vs. East opponents | §12 BETTING-MARKET (round-by-round ATS) | R1 6/6, R2 4/4, CF 4/4 = 14-0 |
| K26 | §8 L249 | Finals dead-on: 2-5 ATS | §12 BETTING-MARKET (round-by-round ATS) | Finals 2/5; avg margin +2.4 vs. spread +2.5 |
| K27 | §9 L290 | avg opponent health 98% | §11 OPPONENT PLAYER AVAILABILITY | avg 98%; Spurs 100% |
| K28 | §9 L292 | close Finals margin +2.4 reflects real competition | §11 OPPONENT PLAYER AVAILABILITY | Spurs 100% health confirmed |
| K29 | §10 L306 | #1 in 60% of bootstrap re-runs | §13 ROBUSTNESS (bootstrap rank) | P(rank #1) = 59.6% |
| K30 | §10 L306 | top 3 in 70% | §13 ROBUSTNESS | P(top 3) = 69.9% |
| K31 | §10 L307 | top 5 in 82% | §13 ROBUSTNESS | P(top 5) = 82.4% |
| K32 | §10 L309 | adj margin range [+5.1, +17.7] | §13 ROBUSTNESS | 90% interval [+5.08, +17.71] |
| K33 | §10 L316 | shrunken margin +6.5/game | §13 ROBUSTNESS (EB shrinkage) | posterior +6.50; 95% CI [+1.53, +11.48] |
| K34 | §10 L316 | shrinkage range [+1.5, +11.5] | §13 ROBUSTNESS | 95% credible interval [+1.53, +11.48] |
| K35 | §10 L337 | hierarchical: Knicks true #1 only ~9% | §14 HIERARCHICAL | P(true #1) = 9.0%; posterior mean +4.70 |
| K36 | §10 L345 | hierarchical pulls from +11.2 down to ~+4.7 | §14 HIERARCHICAL | Knicks posterior +4.70; 90% CI [+1.80, +7.60] |
| K37 | §11 L371 | wins-only (BT): Knicks #1 of 43 | §16 WINS-ONLY (BRADLEY-TERRY) | BT adj +11.37, rank #1; corr with SRS +0.990 |
| K38 | §11 L381 | Elo-adjusted margin +9.4/game, 3rd | §15 ELO CROSS-CHECK | Elo adj +9.36, rank #3; opp rating +5.53 |
| K39 | §12 L406 | model gave Knicks only 15% title probability | §18 SERIES-LEVEL WIN-PROBABILITY | P(title) = 14.7% |
| K40 | §12 L408 | only 7% of model championship runs that clean | §18 SERIES-LEVEL WIN-PROBABILITY | P(title run <=3 losses) = 6.7% |
| K41 | §12 L409 | barely 1% produced title AND <=3 losses | §18 SERIES-LEVEL WIN-PROBABILITY | P(title AND <=3 losses) = 1.0% |
| K42 | §1 L21  | possessions only ~4% above average | §17 POSSESSIONS-BASED PACE | 2025-26 pace 101.8 vs. mean 98.0 = +3.8/game (~4%) |
| K43 | §12 | field's strongest reg-season team was Oklahoma City Thunder (+11.04 SRS) | §18 SERIES-LEVEL WIN-PROBABILITY (field note) | strongest field SRS +11.04 vs. Spurs +8.28 |
| K44 | App.B | champion scores bell-shaped, mean +3.29, Knicks +2.0 SD out | §20 APPENDIX RANKING (shape) | mean +3.29, SD 3.38, 65% within 1 SD |
| K45 | App.C | full-field favorite Oklahoma City Thunder 54.5%, Knicks 3.5% | §19 FULL-FIELD TITLE ODDS | favorite 54.5%, Knicks 3.5% (seed 3), Spurs 14.2% |
| K46 | §11 | capped-margin SRS: Knicks adj +11.93, #1 of 43 | §21 CAPPED-MARGIN (ROBUST) SRS | cap ±15, adj +11.93, rank #1, corr SRS +0.996 |
| K47 | §14 | spread-standardized: Knicks +1.90 SD, #5 of 43 | §22 SPREAD-STANDARDIZED DOMINANCE | z +1.90, rank #5; leader 16–17 z +2.48; SD 1984 3.1 → 2026 5.90 |
| K48 | §14 | era-adjustment ladder: opp-adj #1, scoring-share #1, spread #5 | §22 SPREAD-STANDARDIZED + §9 + §17 | ladder ranks oppadj 1, scoring-share 1, z 5 |
