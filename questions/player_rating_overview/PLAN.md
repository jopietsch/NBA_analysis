# Plan: `player_rating_overview` — survey, recreate, compare, and combine NBA player rating systems

> Status: **draft plan for review.** No code written yet. Execution happens after sign-off.

## Context

A new project under `questions/` with a different shape than prior ones: instead of one
question about the game, it surveys *how players are rated*. Goals, in the user's words:

1. Collect every distinct way NBA players are rated/ranked, tagged by data availability:
   (a) methodology + data we can recompute, (b) results we can only capture, (c) proprietary
   we can't get.
2. Recompute the open ones in Python; cache the closed ones' published results.
3. Explore, understand, and **evaluate** each methodology: compare and contrast them.
4. Build one combined "uber" rating with the right weightings, via **two** lenses:
   a **consensus** rating (shared signal across systems) and a **wins-predictive** rating
   (weighted to predict team outcomes out-of-sample), then compare what each rewards.
5. Find the **best part of each** system: what unique insight it adds the others miss.
6. Explore each rating's **distribution** (hypothesis: power-law / heavy tail), and explain
   to sports readers the implication that the very best players have outsized impact that a
   plain ordinal ranking hides.

### Decisions locked with the user
- **Time scope:** start with the most recent completed season (2024-25) as the testbed, but
  architect so coverage extends as far back as each source allows. Future projects will reuse
  this data/analysis.
- **Uber rating:** build **both** the consensus and the wins-predictive rating, and compare.
- **Data sourcing:** cache locally with a documented, season-keyed acquisition path. Automatable
  sources get real `fetch_*` functions; truly closed sources get a documented manual drop into
  the same cache schema with provenance recorded. Updating years / adding next season is a
  parameterized operation, not a rewrite.
- **Reusability:** the recompute engines + data fetchers/loaders + the cross-system player
  crosswalk live in the **shared `nbakit` package** so later projects `import` them. The project
  itself holds the comparison/combination/power-law analysis and the prose.
- **Human rankings included** as a distinct category (reputation vs. model), for comparison.

## Rating-system inventory (initial; first task verifies/finalizes availability)

| System | Category | How we get it |
|---|---|---|
| Game Score (Hollinger) | Recompute (box) | formula on box totals |
| PER | Recompute (box + league pace/totals) | full Hollinger formula |
| True Shooting%, eFG%, Usage% | Recompute (components) | standard formulas |
| Win Shares (OWS/DWS/WS, WS/48) | Recompute (box + team + league) | Basketball-Reference methodology |
| Box Plus/Minus (BPM 2.0, OBPM/DBPM) | Recompute (box + team) | BBR-published regression coefficients |
| VORP | Recompute (from BPM + minutes) | derived |
| RAPM (regularized adjusted +/-) | **Stretch** recompute, else results | needs play-by-play stints + ridge; snapshot a public RAPM if not feasible |
| RAPTOR (FiveThirtyEight, defunct) | Results-only | archived CSVs on github (downloadable) |
| DARKO (DPM) | Results-only | public results front-end → cached CSV |
| EPM (dunksandthrees) | Results-only (partly paywalled) | snapshot top-N + available values |
| LEBRON (BBall-Index) | Results-only (partly paywalled) | methodology described; snapshot available values |
| ESPN RPM | Results-only | snapshot published values (if still published) |
| Team internal / Second Spectrum / tracking models | Proprietary — can't get | document as unavailable; acknowledge blind spot |
| MVP vote share, All-NBA, All-Star | Human/reputation | Basketball-Reference (fetchable) |
| ESPN #NBArank, The Ringer Top 100 | Human/reputation | snapshot published lists |

The first deliverable is an inventory doc that finalizes this table with exact source URLs,
coverage years, and availability tag per system.

## Architecture

Follows the repo's four-module pipeline (`*_data.py` → `*_plots.py` → `*_analysis.py` →
`*.py` orchestrator) plus `generate_report.py`, mirroring `home_court/` and `template/`.
Audience-tier docs and SVG-chart rules from `questions/CLAUDE.md` apply.

### New shared code in `nbakit` (reused by future projects)
- **`nbakit/ratings.py`** — recompute engines, each a pure function over season-totals +
  league/team context DataFrames: `game_score`, `per`, `shooting_rates`, `win_shares`,
  `bpm` (+ `obpm`/`dbpm`), `vorp`. Coefficients/constants documented inline with source.
- **Raw-input fetchers in `nbakit/data.py`** (extend the existing module that already has
  `fetch_player_game_logs`, `fetch_cached_csv`, `fetch_standings`): add
  `fetch_player_season_totals`, `fetch_team_season_advanced`, and league-average context
  needed by PER/WS/BPM. Reuse the existing `fetch_cached_csv` caching pattern and the nba_api
  quirks noted in `questions/CLAUDE.md` (zero-padded game IDs, `season_nullable` vs `season`).
- **Third-party result loaders** — `load_raptor`, `load_darko`, `load_epm`, `load_lebron`,
  `load_espn_rpm`, plus human-ranking loaders, all reading a documented cache schema; a small
  **source registry** records URL + acquisition method + snapshot date per source.
- **Player crosswalk** — `nbakit/player_crosswalk.py`: reconcile player identity across systems
  (nba_api `PERSON_ID` ↔ BBR slug ↔ free-text names in RAPTOR/DARKO/etc.) via a normalized-name
  + season + team match with a hand-maintained override table for collisions. **This is the
  single biggest hidden cost; called out so it gets budgeted.**

### Project code in `questions/player_rating_overview/`
- `player_rating_overview_data.py` — thin: assemble the unified per-season ratings table by
  calling nbakit engines + loaders + crosswalk; cache the merged table under `cache/`.
- `player_rating_overview_plots.py` — all `plot_*` (SVG; consistent color semantics).
- `player_rating_overview_analysis.py` — `run()` prints sections captured to
  `docs/player_rating_overview_results.md`.
- `player_rating_overview.py` — orchestrator.
- `generate_report.py` — copy/adapt from `home_court/`.
- `project_definition.md` — fill from the `template/`.

## Analysis components

1. **Unified ratings table** — one row per (player, season), one column per system, plus
   minutes/games for weighting. The backbone everything else reads.
2. **Compare & contrast** — rank agreement across systems (Spearman/Kendall matrix, reported
   plainly per tiering), an agreement heatmap, and a "who each system loves/hates vs. consensus"
   table (largest signed residuals). Honest about disagreement, not just averaged away.
3. **What each uniquely captures ("best part of each")** — regress each system on all the others;
   the residual variance = its unique signal. Identify which players that unique signal flags,
   and which systems are nearly redundant. Also: which single system best predicts team wins, and
   which is most stable (if multi-season pulled).
4. **Uber rating — two lenses:**
   - *Consensus:* z-score each system across qualified players, then average / take PCA first
     component. Measures agreement, not correctness.
   - *Wins-predictive:* aggregate player ratings to team level (minutes-weighted), fit a
     **out-of-sample** weighting (ridge / non-negative constrained) to predict team wins or SRS,
     then read back per-player weights. Compare the two weight vectors and where they disagree.
5. **Power-law / distribution exploration** — per metric: rank-size log-log plot, tail-heaviness
   (Gini, top-5% value share), and a fitted distribution. **Test the hypothesis honestly rather
   than assume it:** expect per-possession *rate* metrics (PER, BPM) to be near-normal across
   qualified players, but *cumulative value* metrics (Win Shares, VORP, RAPTOR WAR) to be heavily
   right-skewed because value = rate × minutes × availability and winning impact is convex.
   Report where the heavy tail is real and where it isn't (CLAUDE.md "don't overstate" rule).
6. **Reader explanation of the power-law implication** — a worked, plain-language section showing
   that ordinal rank flattens real gaps: the #1 player can be worth multiples of #10 even when
   they sit one line apart on a list. Use the convex value metrics to make it concrete.

## Documents (audience tiers per `questions/CLAUDE.md`)
- `docs/player_rating_overview_inventory.md` — the finalized system catalog + availability tags.
- `docs/player_rating_overview_findings.md` — main narrative (plain language; voice hook applies).
- `docs/player_rating_overview_summary.md` — one-page summary.
- `docs/player_rating_overview_investigation.md` — middle tier (p-values/CIs allowed) for the
  comparison/combination evidence.
- `docs/player_rating_overview_stats_explainer.md` — methods companion (real method names matched
  to the code: PER/WS/BPM formulas, ridge, PCA, power-law fitting).
- `docs/player_rating_overview_results.md` — auto-generated; never hand-edited.
- `docs/player_rating_overview_findings_outline.md` — internal outline.
- A dedicated power-law explainer section for sports readers (in findings, or its own doc).
- All new docs start with the Draft block (CLAUDE.md "Draft status").

## Build order (incremental; each phase verifiable)
1. **Inventory doc** → verify: every system tagged with source + coverage + availability.
2. **nbakit raw-input fetchers + cache** → verify: unit tests on synthetic frames; one live cached pull for 2024-25.
3. **nbakit recompute engines** → verify: recomputed PER/WS/BPM/VORP for 2024-25 match
   Basketball-Reference published values within rounding (spot-check ~10 known players).
4. **Crosswalk + third-party/human loaders + snapshots** → verify: merged table has high join
   coverage; unmatched players reported, not silently dropped.
5. **Unified table + plots + analysis** → verify: pipeline runs `MPLBACKEND=Agg python3
   player_rating_overview.py`, writes `_results.md`, all `plot_*` smoke-test green.
6. **Combination (both lenses) + power-law** → verify: numbers in results doc; out-of-sample
   wins fit reported with honest error.
7. **Prose docs + PDFs** → verify: `generate_report.py` builds; voice hook passes; numbers in
   prose match `_results.md`.

## Verification (end to end)
- `MPLBACKEND=Agg python3 player_rating_overview.py` regenerates charts + `_results.md`.
- `python3 -m pytest` (correctness tests for engines/crosswalk; no-raise smoke tests for plots;
  **no live API calls in tests** — synthetic frames + recorded fixtures).
- Recomputed metrics spot-checked against Basketball-Reference published values.
- `python3 generate_report.py` builds the PDF/HTML; standalone docs via `../generate_doc_pdf.py`.
- Crosswalk coverage report: % of each third-party list successfully joined; unmatched listed.

## Open items to confirm during build (not blockers)
- RAPM: attempt a stint-level ridge recompute, or snapshot a public RAPM? (decide at phase 4 by
  feasibility of play-by-play volume for one season).
- Qualified-player threshold (minutes/games) for distribution and z-scoring — pick a defensible
  cutoff and state it.

## Notes from exploration (reuse, don't reinvent)
- `nbakit/nbakit/data.py` already provides: `season_str`/`short_label` season helpers,
  `default_cache_dir` (shared monorepo `cache/`, `NBA_CACHE_DIR` override), `fetch_cached_csv`
  (generic cache-with-empty-miss-handling), `fetch_player_game_logs`, `fetch_standings`,
  `parse_min`, `compute_srs` (SRS for the wins-predictive target), `is_rate_limit_error`.
  New fetchers should follow these patterns rather than introduce a second caching style.
- `nbakit/nbakit/stats.py` has `shrink_to_mean`, `binom_sf_ge`, `t_interval` (useful for the
  honest-uncertainty reporting in the comparison section).
- `nbakit/nbakit/viz.py` has `output_path`, `save_chart`, `style_axes`, `new_fig`,
  `add_trend_line` — the chart scaffolding to reuse for the `plot_*` functions.
- `template/` and `home_court/` are the structural references for the four-module pipeline,
  `generate_report.py`, `project_definition.md`, and the docs/test layout.
