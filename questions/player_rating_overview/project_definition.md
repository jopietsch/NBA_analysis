# Project Definition: player_rating_overview

---

## The question

**In one sentence:** How do the major NBA player rating systems compare, what does each uniquely capture, and how can they be combined into a rating that best identifies who drives team success?

**Why it's worth answering:** Every published "top players" list uses a different methodology, and they disagree in ways that matter for evaluating players on losing teams, defensive specialists, and high-usage inefficient scorers. A reader who understands how the systems compare can read any rating critically; a combined rating built with the right weighting answers the practical question of who actually helps teams win.

---

## Hypothesis

**What you expect to find going in:** Box-score systems (PER, Win Shares) and impact metrics (RAPTOR, BPM, EPM) will agree strongly on the top 10-15 players but diverge on defensive specialists, role players, and players on bad teams. Combining them with a wins-predictive weighting will deemphasize counting stats and better identify players whose efficiency matters most. Cumulative metrics will show heavy right-tail distributions (star value is convex); rate metrics will be near-normal among qualified players.

**Why you expect that:** Box-score systems by design measure production, not impact. Impact metrics try to adjust for team context but are noisier. Human rankings overweight narrative and team success. The distribution prediction follows from the mathematical structure of cumulative value (rate × minutes) where both dimensions compound.

---

## Comparison set

**What is being compared against what:** Player ratings across all available systems in the 2024-25 regular season; secondary multi-season analysis where sources allow.

**Time range:** Primary testbed: 2024-25. Multi-season: back to 1983-84 for box-score systems; 2013-14 for impact metrics.

**Inclusion criteria:** Qualified players: 500+ regular-season minutes in 2024-25. All players retained in the unified table; qualifier filters apply to distribution/z-score analysis.

**Why this set and not another:** Most recent completed season as the testbed. The architecture parameterizes season so earlier and future seasons can be added without rewriting.

---

## Confirmation and refutation criteria

**The answer is clearly YES (systems diverge meaningfully) if:** Spearman rank correlations between box-score systems and impact metrics are below 0.70 across qualified players, and the "who each system loves" table shows clearly different player types.

**The answer is clearly NO (systems mostly agree) if:** All pairwise Spearman correlations exceed 0.85, the unique R² for each system is below 0.05, and the consensus and wins-predictive top-20 lists are identical.

**The answer is ambiguous if:** High correlations in the top 20 but meaningful divergence below that, making it unclear whether the differences are meaningful or noise.

---

## Alternative explanations to address

- **Teams confound box stats:** Players on good offensive teams get more easy shots and assisted baskets, inflating PER and Win Shares. The BPM team adjustment partially addresses this; we check whether the box/impact divergence tracks team quality.
- **Small sample impact noise:** Impact metrics are based on lineup data that is inherently noisy in one season. We report crosswalk coverage and note where impact metric divergence could reflect noise rather than real disagreement.
- **Minutes threshold selection:** Different qualification thresholds change which players are in the qualified pool and thus the distribution statistics. The 500-minute threshold is stated as a design choice; sensitivity to it is acknowledged.

---

## Data plan

**Primary source:** nba_api (player/team season totals), Basketball-Reference (human rankings via scrape), FiveThirtyEight GitHub (RAPTOR CSVs), and manual snapshots for EPM/LEBRON/ESPN RPM.

**Key tables/endpoints:** `LeagueDashPlayerStats` (Totals + Per100Possessions), `LeagueDashTeamStats`, `LeagueStandingsV3`, BBR award pages, FTE RAPTOR GitHub CSVs.

**Metrics to compute:** Game Score, PER, TS%, eFG%, USG%, Win Shares (OWS/DWS/WS/WS48), BPM (OBPM/DBPM), VORP. Third-party: RAPTOR, DARKO, EPM, LEBRON, ESPN RPM. Human: MVP vote share, All-NBA points, All-Star.

**Known gaps:** RAPM deferred. EPM/LEBRON/ESPN RPM partly paywalled or defunct. Tracking metrics proprietary. RAPTOR ended 2022-23.

---

## Done criteria

- [x] Inventory doc: all systems tagged with source, coverage, availability
- [ ] nbakit fetchers: `fetch_player_season_totals`, `fetch_team_season_totals`, `fetch_league_averages` pass unit tests with synthetic data
- [ ] nbakit ratings: recomputed PER/WS/BPM/VORP spot-check within rounding of BBR for 5+ known players in 2024-25
- [ ] Crosswalk: RAPTOR (where available) matches at >90%; unmatched players listed
- [ ] Pipeline runs: `MPLBACKEND=Agg python3 player_rating_overview.py` generates charts + results.md
- [ ] All 7 plot_ functions produce no-raise smoke tests green
- [ ] Cross-system correlation matrix in results.md
- [ ] Top-20 lists for consensus and wins-predictive in results.md
- [ ] Distribution stats (Gini, skewness, top-5% share) per system in results.md
- [ ] Findings prose matches results.md; no draft markers remain
- [ ] Summary doc written and reviewed
- [ ] generate_report.py builds PDF without errors

---

## Open questions

- RAPM: attempt from play-by-play stints (pbpstats), or use a public snapshot?
- Wins-predictive: α for ridge needs cross-validation across seasons before trusting weights; single-season α=5 is a placeholder.
- EPM and LEBRON: can full-season snapshots be obtained for 2024-25 without a subscription?
- ESPN RPM: still published? Last confirmed year?
