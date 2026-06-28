# CLAUDE.md

A Python system to fetch NBA data and analyze it to answer one question: **did the 2025–26 New York Knicks have a historic playoff run?** The answer is comparative — we rank the 2026 Knicks run against historical playoff runs on the dimensions that define a great postseason (seeding vs. result, margin, opponent strength, series shape). Output is a PDF report with charts and an analysis appendix.

The standard commands, module architecture, document workflow, test pattern, and the "adding a new analysis" order live in the parent `../CLAUDE.md` (loaded alongside this file). This file covers only what is specific to knicks_2026_historic.

## Project-specific notes

- The method is percentile/ranking against the historical champion set: every metric needs the 2026 Knicks value *and* the same value across the comparison set so it can be ranked.
- `knicks_2026_historic.py` captures `analysis.run()`'s stdout into `knicks_2026_historic_results.md` inside a ``` fence.
- The report is built with `include_appendix=False`: `knicks_2026_historic_results.md` is **not** inlined as an appendix; it is linked as a standalone companion doc from "Appendix A: Companion Documents" in the findings instead.
- `knicks_2026_historic_findings_outline.md` is a non-standard doc: keep it in sync with the findings (the `/sync-outline` command does this) and regenerate its PDF with `python3 ../generate_doc_pdf.py docs/knicks_2026_historic_findings_outline.md`.

## Key files

- `docs/knicks_2026_historic_findings.md` — narrative interpretation in numbered `## N. Title` sections; the single source of truth for report prose and chart placement. Edit by hand when understanding changes; the PDF picks up sections automatically. Image references use `../generated/images/<chart>.svg`.
- `docs/knicks_2026_historic_summary.md` — standalone one-page summary built around three core charts (adjusted margin ranking, round split, market vs actual) and the main question.
- `docs/knicks_2026_historic_stats_explainer.md` — hand-edited methods companion; regenerate its PDF with `python3 ../generate_doc_pdf.py docs/knicks_2026_historic_stats_explainer.md`.
- `docs/knicks_2026_historic_investigation.md` — companion document covering the full analysis in two parts. Part 1 makes the affirmative case the run was historic (each claim as claim/test/what the data showed/why it holds: raw dominance, opponent-adjusted dominance, overperformance and field elevation, the betting market, the forecast). Part 2 treats every objection to the run (weak East, soft bracket, fading opponents, padded margins, scoring-era inflation, opponent injury) in full: why each seemed plausible, what was tested, how much it explains away, then closes with the small-sample caveat that does survive. Part 2 mirrors the "What Does NOT Diminish the Run" section of the findings; update it when that section changes. Regenerate with `python3 ../generate_doc_pdf.py docs/knicks_2026_historic_investigation.md`.
- `docs/knicks_2026_historic_findings_outline.md` — condensed section-by-section outline of the findings, cross-referenced to `knicks_2026_historic_results.md`. Keep it in sync with the findings (the `/sync-outline` command does this); regenerate with `python3 ../generate_doc_pdf.py docs/knicks_2026_historic_findings_outline.md`.
- `docs/knicks_2026_historic_results.md` — auto-generated analysis output; **never edit manually**, always re-run the pipeline to refresh.

## Updating docs/knicks_2026_historic_findings.md

- When section order changes, update the order of `run_*` calls in `knicks_2026_analysis.py` to match, so `knicks_2026_historic_results.md` lines up.
- When the findings change, update `docs/knicks_2026_historic_findings_outline.md` to match (the `/sync-outline` command does this), then regenerate its PDF.
- When the "What Does NOT Diminish the Run" section changes, update `docs/knicks_2026_historic_investigation.md` to match.
