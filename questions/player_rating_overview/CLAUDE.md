# CLAUDE.md

A Python system to fetch NBA player data and survey, compare, and combine the major player rating systems. See `project_definition.md` for the full question design (hypothesis, comparison set, confirmation criteria, alternatives, done criteria).

The standard commands, module architecture, document workflow, test pattern, and the "adding a new analysis" order live in the parent `../CLAUDE.md` (loaded alongside this file). This file covers only what is specific to player_rating_overview.

## The questions

The report is question-driven (see "Document arc for question-driven reports" in `../CLAUDE.md`). The one-sentence question, "how do the major NBA player rating systems compare, what does each uniquely capture, and how can they be combined into a rating that best identifies who drives team success?", breaks into three:

1. **Do the systems agree?** How strongly do box-score systems (PER, Win Shares) and impact metrics (RAPTOR, BPM, EPM) rank players the same way, and where do they diverge?
2. **What does each system uniquely capture?** What player types (defensive specialists, role players, players on bad teams, high-usage inefficient scorers) does each system see that the others miss?
3. **How should they be combined?** Can a wins-predictive weighting fold them into a single rating that best identifies who actually drives team success?

The findings intro should state these three in bold and front-load their answers; the body should develop one cluster of sections per question; the summary should re-answer all three. `/check-coherence` uses this set as the contract.

Primary testbed is the 2025-26 regular season, with multi-season analysis back to 1983-84 (box-score systems) and 2013-14 (impact metrics) where sources allow. Throughout the docs, be clear which claims rest on the single-season testbed versus the multi-season cache, and flag where impact-metric divergence could be one-season noise rather than real disagreement.

## Project-specific notes

- This project carries two **non-standard** docs beyond the standard set:
  - `docs/player_rating_overview_inventory.md.j2`: an inventory of every rating system tagged with source, coverage, and availability.
  - `docs/player_rating_resources.md.j2`: a curated reading list (note the filename is `player_rating_resources`, not `player_rating_overview_resources`).
- `BPM`/`VORP` are recomputed (linear fit to reproduce Basketball-Reference's OBPM/DBPM on standard advanced percentages, plus a team-margin anchor) and validated against BBR each run by the "BPM VALIDATION vs BASKETBALL-REFERENCE" analysis section (2025-26: r≈0.93 BPM, 0.96 VORP). The fit weights live in `nbakit/nbakit/ratings.py` (`_OBPM_W`/`_DBPM_W`); `fetch_bbr_advanced` in the data module supplies the reference. DBPM agreement is the weakest (box defense is hard).
- The `RAPM` family was crippled by a reconstruction bug in `nbakit/nbakit/data.py::reconstruct_possessions`: any period that failed to reconcile to 5-on-5 silently dropped the *whole* game, discarding ~60% of games that had complete play-by-play. Fixed this session by recovering the valid possessions from a game rather than discarding it, matching substitution names robustly in `_norm_name`, and evicting the least-recently-active player when a lineup needs a forced repair. Result: usable games rose from ~500 to ~1,230 per season, and reliability climbed across the board: split-half reliability ~0.10 → 0.32 (~0.48 Spearman-Brown full-data; ~0.60 at 5 pooled seasons); bare single-season RAPM year-over-year 0.09 → 0.41; and `RAPM_MY` (RAPM+prior) year-over-year 0.84, at least as stable as BPM (0.79). The box-score prior is folded in as a fixed strong ridge penalty (see `nbakit/nbakit/ratings.py::rapm`, `RAPM_PRIOR_STRENGTH`). Bare single-season RAPM remains the noisier of the two versions, so still lead with `RAPM_MY` in the docs and flag bare RAPM as the higher-variance cut. See the repo-wide `questions/DATA_INTEGRITY_AUDIT.md` for the related cache-bug fix and the remaining silent-data-loss backlog.
- Third-party snapshots (DARKO, EPM, LEBRON, ESPN RPM) require manual CSVs and are partly paywalled or defunct; note coverage gaps in the docs where a system is missing or stale.
- See `FACTS_MIGRATION.md` and `RAPM_PRIOR_DESIGN.md` for in-progress design notes.

## Updating docs/player_rating_overview_findings.md

- When section order changes, update the order of the analysis calls in `player_rating_overview_analysis.py` to match, so `player_rating_overview_results.md` lines up.
- When the findings change, update `docs/player_rating_overview_findings_outline.md` to match (the `/sync-outline` command does this), then regenerate its PDF.
- Throughout the findings, keep the three questions answerable: state them in the intro, develop each in the body, re-answer them in the summary.

## When a metric is fixed or added (the standing cascade)

Fixing a rating (the RAPM follow-on) or adding a new one moves numbers across every doc. The examples section (`## 4`, archetype reps) and the BPM validation / Playoff-Weighted Value sections are built to keep up with minimal hand-work, but only if you run the cascade:

1. **Rerun the pipeline.** `MPLBACKEND=Agg python3 player_rating_overview.py` (regenerates `_results.md`, `_facts.json`, `_guards.json`, images), then `python3 render_docs.py`. Every templated number refreshes automatically.
2. **Run pytest.** `test_facts_match_results.py` catches facts that drifted from their `print()`; `test_prose_claims.py` fails loudly if any guard's premise flipped (e.g. an example archetype's defining claim, or `blind_rating_rebuilds_team_diff`). A failing guard names the exact sentence to revisit.
3. **Re-run `/review-all`** on the changed reader-facing docs. The guards catch direction; only a human voice pass catches a magnitude word that stayed directionally true but went stale.

The four non-pinned example archetypes are **rule-selected in `_analysis.py`** (`example.*.name` facts: agreed elite = best worst-rank; defense star = top-BPM-tier max DBPM; split scorer = high-USG, PER rank >> BPM rank; riser = top playoff shift) and re-point automatically when the data moves. Brunson is the one pinned example. So a metric change usually needs new prose only where a sentence interprets *why* a number is what it is, not for the names or figures themselves.

Watch for downstream flips when a metric's distribution changes: the BPM rewrite (team-margin anchor) made BPM mechanically top the team-point-differential retrodiction (`retro.mechanical.*`; the genuine champion is the top outcome-blind rating in `retro.top.*`) and moved OBPM/DBPM/VORP into the power-law group in `## 6`. These are correct consequences, not bugs, but they require prose updates that the guards flag.
