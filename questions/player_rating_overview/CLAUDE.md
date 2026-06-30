# CLAUDE.md

A Python system to fetch NBA player data and survey, compare, and combine the major player rating systems. See `project_definition.md` for the full question design (hypothesis, comparison set, confirmation criteria, alternatives, done criteria).

The standard commands, module architecture, document workflow, test pattern, and the "adding a new analysis" order live in the parent `../CLAUDE.md` (loaded alongside this file). This file covers only what is specific to player_rating_overview.

## The questions

The report is question-driven (see "Document arc for question-driven reports" in `../CLAUDE.md`). The one-sentence question, "how do the major NBA player rating systems compare, what does each uniquely capture, and how can they be combined into a rating that best identifies who drives team success?", breaks into three:

1. **Do the systems agree?** How strongly do box-score systems (PER, Win Shares) and impact metrics (RAPTOR, BPM, EPM) rank players the same way, and where do they diverge?
2. **What does each system uniquely capture?** What player types (defensive specialists, role players, players on bad teams, high-usage inefficient scorers) does each system see that the others miss?
3. **How should they be combined?** Can a wins-predictive weighting fold them into a single rating that best identifies who actually drives team success?

The findings intro should state these three in bold and front-load their answers; the body should develop one cluster of sections per question; the summary should re-answer all three. `/check-coherence` uses this set as the contract.

Primary testbed is the 2024-25 regular season, with multi-season analysis back to 1983-84 (box-score systems) and 2013-14 (impact metrics) where sources allow. Throughout the docs, be clear which claims rest on the single-season testbed versus the multi-season cache, and flag where impact-metric divergence could be one-season noise rather than real disagreement.

## Project-specific notes

- This project carries two **non-standard** docs beyond the standard set:
  - `docs/player_rating_overview_inventory.md.j2`: an inventory of every rating system tagged with source, coverage, and availability.
  - `docs/player_rating_resources.md.j2`: a curated reading list (note the filename is `player_rating_resources`, not `player_rating_overview_resources`).
- Recomputed `BPM`/`VORP` absolute values are approximate; spot-check against Basketball-Reference rather than treating them as exact.
- Third-party snapshots (DARKO, EPM, LEBRON, ESPN RPM) require manual CSVs and are partly paywalled or defunct; note coverage gaps in the docs where a system is missing or stale.
- See `FACTS_MIGRATION.md`, `PLAN.md`, and `RAPM_PRIOR_DESIGN.md` for in-progress design notes.

## Updating docs/player_rating_overview_findings.md

- When section order changes, update the order of the analysis calls in `player_rating_overview_analysis.py` to match, so `player_rating_overview_results.md` lines up.
- When the findings change, update `docs/player_rating_overview_findings_outline.md` to match (the `/sync-outline` command does this), then regenerate its PDF.
- Throughout the findings, keep the three questions answerable: state them in the intro, develop each in the body, re-answer them in the summary.
