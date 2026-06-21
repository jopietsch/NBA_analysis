# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A Python system to fetch NBA data and analyze it to answer one question: **did the 2025–26 New York Knicks have a historic playoff run?** The answer is comparative — we rank the 2026 Knicks run against historical playoff runs on the dimensions that define a great postseason (seeding vs. result, margin, opponent strength, series shape). Output is a PDF report with charts and an analysis appendix.

## Commands

```bash
# Run the full analysis pipeline
MPLBACKEND=Agg python3 knicks_2026_historic.py
```

## Architecture

Four pipeline modules plus two report generators, mirroring `home_court`:

- **`knicks_2026_data.py`** — all constants, data fetching, and computation; no matplotlib dependency. `fetch_games()` pulls game logs via nba_api's `LeagueGameFinder` and caches them as CSVs under `cache/`. `compute_*` metrics turn raw frames into the numbers we rank.
- **`knicks_2026_plots.py`** — all visualization (`plot_*` functions saving `knicks_2026_*.svg`); imports the data module, holds no data logic of its own.
- **`knicks_2026_analysis.py`** — statistical/comparative analysis; `run()` prints all sections to stdout. The method is percentile/ranking against the historical champion set.
- **`knicks_2026_historic.py`** — pipeline orchestration only: sequences data → plots → analysis, and captures `analysis.run()`'s stdout into `RESULTS.md` inside a ``` fence. The analysis module is imported inside `main()`.
- **`generate_report.py`** — assembles `docs/knicks_2026_historic_findings.md` prose + PNGs into the PDF; iterates `##` sections in document order with no hardcoded list; TOC auto-generated; appendix renders `docs/RESULTS.md` verbatim.
- **`generate_doc_pdf.py`** — general Markdown→PDF renderer for standalone docs (copied unchanged from the sibling; understands code fences, headings, lists, tables, images, and `--appendix`).

Tests: `tests/test_knicks_2026.py` is correctness unit tests for the data/computation layer using synthetic DataFrames (never live API calls). `tests/test_knicks_2026_plots.py` is no-raise smoke tests for plots — no pixel/image comparison (brittle across font and library versions).

All fetched data is cached as CSVs under `cache/` to avoid re-fetching.

## Key files

- `docs/knicks_2026_historic_findings.md` — narrative interpretation in numbered `## N. Title` sections; the single source of truth for report prose and chart placement. Edit by hand when understanding changes; the PDF picks up sections automatically. Image references use `../generated/images/<chart>.svg`.
- `docs/knicks_2026_historic_summary.md` — standalone one-page summary built around three core charts (adjusted margin ranking, round split, market vs actual) and the main question.
- `docs/knicks_2026_historic_stats_explainer.md` — hand-edited methods companion; regenerate its PDF with `python3 generate_doc_pdf.py docs/knicks_2026_historic_stats_explainer.md`.
- `docs/RESULTS.md` — auto-generated analysis output; **never edit manually**, always re-run the pipeline to refresh.

## Adding a new analysis

Follow this order (same as the sibling project):

1. **Data** (`knicks_2026_data.py`) — add `fetch_*` and `compute_*`; cache fetches under `cache/`. Every metric needs the 2026 Knicks value *and* the same value across the historical comparison set so it can be ranked.
2. **Plot** (`knicks_2026_plots.py`) — add a `plot_*`; wire its call into `main()` in `knicks_2026_historic.py`.
3. **Analysis** (`knicks_2026_analysis.py`) — add a `run_*`; call it from `run()`. Output goes to stdout and is captured into `RESULTS.md`. Use the box-drawing header convention the appendix parser expects: `print("─── SECTION TITLE " + "─" * 50)`.
4. **Tests** — correctness tests for new `compute_*` in `tests/test_knicks_2026.py`; a no-raise smoke test for the new `plot_*` in `tests/test_knicks_2026_plots.py`.
5. **docs/knicks_2026_historic_findings.md** — add a `## N. Title` section with prose and `![caption](../generated/images/knicks_2026_*.svg)` references.
6. **Run** — `MPLBACKEND=Agg python3 knicks_2026_historic.py` to regenerate PNGs and `docs/RESULTS.md`, then `python3 generate_report.py`.

## Updating docs/knicks_2026_historic_findings.md

- When section order changes, update the order of `run_*` calls in `knicks_2026_analysis.py` to match, so `RESULTS.md` (and the appendix) line up.

