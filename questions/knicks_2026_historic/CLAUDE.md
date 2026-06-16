# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

A Python system to fetch NBA data and analyze it to answer one question: **did the 2025–26 New York Knicks have a historic playoff run?** The answer is comparative — we rank the 2026 Knicks run against historical playoff runs on the dimensions that define a great postseason (seeding vs. result, margin, opponent strength, series shape). Output is a PDF report with charts and an analysis appendix.

This project is a sibling of `../nba_home_court` and deliberately mirrors its architecture, toolchain, and conventions. When something here is unspecified, that project is the reference.

## Commands

```bash
# Run the full analysis (fetches data, generates PNGs, writes RESULTS.md)
MPLBACKEND=Agg python3 knicks_2026_historic.py

# Generate the PDF report (run after the above — needs all PNGs + RESULTS.md)
python3 generate_report.py

# Regenerate a standalone markdown doc's PDF (e.g. FINDINGS_OUTLINE.md if added)
python3 generate_doc_pdf.py <FILE>.md

# Tests (coverage configured in pytest.ini)
python3 -m pytest

# A single test
python3 -m pytest test_knicks_2026.py::test_season_str

# Install dependencies
pip install -r requirements.txt
```

Always run the pipeline with `MPLBACKEND=Agg` to render PNGs without opening display windows.

## Architecture

Four pipeline modules plus two report generators, mirroring `nba_home_court`:

- **`knicks_2026_data.py`** — all constants, data fetching, and computation; no matplotlib dependency. `fetch_games()` pulls game logs via nba_api's `LeagueGameFinder` and caches them as CSVs under `cache/`. `compute_*` metrics turn raw frames into the numbers we rank.
- **`knicks_2026_plots.py`** — all visualization (`plot_*` functions saving `knicks_2026_*.png`); imports the data module, holds no data logic of its own.
- **`knicks_2026_analysis.py`** — statistical/comparative analysis; `run()` prints all sections to stdout. The method is percentile/ranking against the historical champion set.
- **`knicks_2026_historic.py`** — pipeline orchestration only: sequences data → plots → analysis, and captures `analysis.run()`'s stdout into `RESULTS.md` inside a ``` fence. The analysis module is imported inside `main()`.
- **`generate_report.py`** — assembles `FINDINGS.md` prose + PNGs into the PDF; iterates `##` sections in document order with no hardcoded list; TOC auto-generated; appendix renders `RESULTS.md` verbatim.
- **`generate_doc_pdf.py`** — general Markdown→PDF renderer for standalone docs (copied unchanged from the sibling; understands code fences, headings, lists, tables, images, and `--appendix`).

Tests: `test_knicks_2026.py` is correctness unit tests for the data/computation layer using synthetic DataFrames (never live API calls). `test_knicks_2026_plots.py` is no-raise smoke tests for plots — no pixel/image comparison (brittle across font and library versions).

All fetched data is cached as CSVs under `cache/` to avoid re-fetching.

## Key files

- `FINDINGS.md` — narrative interpretation in numbered `## N. Title` sections; the single source of truth for report prose and chart placement. Edit by hand when understanding changes; the PDF picks up sections automatically.
- `RESULTS.md` — auto-generated analysis output; **never edit manually**, always re-run the pipeline to refresh.

## Adding a new analysis

Follow this order (same as the sibling project):

1. **Data** (`knicks_2026_data.py`) — add `fetch_*` and `compute_*`; cache fetches under `cache/`. Every metric needs the 2026 Knicks value *and* the same value across the historical comparison set so it can be ranked.
2. **Plot** (`knicks_2026_plots.py`) — add a `plot_*`; wire its call into `main()` in `knicks_2026_historic.py`.
3. **Analysis** (`knicks_2026_analysis.py`) — add a `run_*`; call it from `run()`. Output goes to stdout and is captured into `RESULTS.md`. Use the box-drawing header convention the appendix parser expects: `print("─── SECTION TITLE " + "─" * 50)`.
4. **Tests** — correctness tests for new `compute_*` in `test_knicks_2026.py`; a no-raise smoke test for the new `plot_*` in `test_knicks_2026_plots.py`.
5. **FINDINGS.md** — add a `## N. Title` section with prose and `![caption](knicks_2026_*.png)` references.
6. **Run** — `MPLBACKEND=Agg python3 knicks_2026_historic.py` to regenerate PNGs and `RESULTS.md`, then `python3 generate_report.py`.

When section order in `FINDINGS.md` changes, change the order of `run_*` calls in `knicks_2026_analysis.py` to match, so `RESULTS.md` (and the appendix) line up.

## Editing FINDINGS.md

- Write like a sports-magazine editor for regular readers: replace statistical jargon with plain language, keep the voice concise, avoid redundancy (it confuses more than it reinforces).
- Every claim must be backed by `RESULTS.md` and the generated charts — verify the narrative matches the current data before regenerating.
- Don't put specific coefficients/percentages in prose that will go stale; describe direction and relative magnitude, and reference `RESULTS.md` for exact figures.
- After editing, regenerate the PDF: `python3 generate_report.py`.

## nba_api quirks

- `LeagueGameFinder` uses `season_nullable=` and `season_type_nullable=` (not the bare `season=`/`per_mode_*` other endpoints take). Pass `league_id_nullable="00"` to restrict to the NBA. It returns one row per team per game; `MATCHUP` is `'NYK vs. BOS'` for home, `'NYK @ BOS'` for away; `WL` is `'W'`/`'L'`.
- Game IDs from cached CSVs come back as integers and must be zero-padded to 10 digits for endpoints that take a game id: `f"{int(float(gid)):010d}"`.

## Working style

The sibling `nba_home_court/CLAUDE.md` spells these out at length and they apply here too: **think before coding** (state assumptions, surface tradeoffs, ask when unclear rather than guessing); **simplicity first** (minimum code that solves the problem, nothing speculative); **surgical changes** (touch only what the task requires, match existing style, don't refactor what isn't broken).
