---
name: pipeline
description: The analysis-project pipeline for questions/ projects — the four-module architecture (_data/_plots/_analysis/_facts.py plus the orchestrator and report generators), the shell commands to run the pipeline and build PDF/HTML reports, the directory layout and shared cache, the facts/guards test pattern, and nba_api endpoint quirks. Load this before scaffolding a new question, running or extending the pipeline, adding an analysis, editing a plot_* function, or fetching NBA data.
---

# Analysis pipeline

The mechanics for building and running a `questions/` analysis project. The document naming convention, facts-sourcing rule, and cascade rules live in `questions/CLAUDE.md` under "Standard document workflow"; this skill holds the code architecture, commands, layout, and data quirks.

## Standard commands

Run all commands from the project root.

```bash
# Run the full analysis pipeline (generates SVGs, runs analysis, writes docs/<project>_results.md
# and docs/<project>_facts.json + _guards.json)
MPLBACKEND=Agg python3 <project>.py

# Render .md.j2 templates → .md (run after the pipeline, before building PDFs)
python3 render_docs.py

# Generate the main PDF + HTML report (renders templates first)
python3 generate_report.py

# Regenerate any standalone doc PDF + HTML
python3 ../generate_doc_pdf.py docs/<project>_findings.md
python3 ../generate_doc_pdf.py docs/<project>_summary.md
python3 ../generate_doc_pdf.py docs/<project>_stats_explainer.md

# Write the facts reference table (dev helper while authoring templates)
python3 render_docs.py --reference

# Run all tests (includes guard tests: test_facts_match_results.py, test_prose_claims.py)
python3 -m pytest

# Install dependencies
pip install -r ../requirements.txt
```

Always use `MPLBACKEND=Agg` when running the analysis script to suppress display windows. Chart images land in `generated/images/` (gitignored); PDFs and HTML reports land in `generated/`. `docs/<project>_results.md` is the exception — it is committed. Image references in `docs/` use `../generated/images/<chart>.svg`.

## Standard directory layout

```
<project>/
├── docs/          — prose files (FINDINGS, SUMMARY, STATS_EXPLAINER, <project>_results.md)
├── tests/         — test files; test fixture CSVs go in tests/data/
└── generated/     — PDFs and HTML reports (gitignored)
    └── images/    — all chart SVGs/PNGs (gitignored)
```

Fetched data CSVs are **not** cached per project. They live in the shared
monorepo cache at the repo root (`nba_analysis/cache/`, gitignored), resolved via
`nbakit.default_cache_dir()` and overridable with the `NBA_CACHE_DIR` env var, so
every project reuses the same fetched data.

## Standard architecture

Each project follows a four-module pipeline plus two report generators plus the facts system:

- **`<project>_data.py`** — all constants, data fetching, and computation; no matplotlib dependency. All fetched data is cached as CSVs in the shared monorepo cache (`nba_analysis/cache/` at the repo root, resolved via `nbakit.default_cache_dir()`; override with `NBA_CACHE_DIR`), not in a per-project directory. This is the only module that calls external APIs.
- **`<project>_plots.py`** — all visualization; imports the data module and holds no data logic of its own. Each `plot_*` function saves an SVG to `generated/images/`.
- **`<project>_analysis.py`** — statistical/comparative analysis; `run()` prints all output to stdout, which is captured into `docs/<project>_results.md`. Use the box-drawing header convention: `print("─── SECTION TITLE " + "─" * 50)`. Register named facts with `FACTS.set()` next to each `print()` call that emits a cited number. Register qualitative claims with `FACTS.guard()`. At the end of `run()`, call `FACTS.dump(_FACTS_PATH)` and `FACTS.dump_guards(_GUARDS_PATH)`.
- **`<project>_facts.py`** — a thin shim over `nbakit.facts`: re-exports the shared `Fact`/`Facts`/`load_displays`/`load_guards` model, instantiates the project's `FACTS` singleton, and pins the `_FACTS_PATH`/`_GUARDS_PATH` constants. The `Fact`/`Facts` class itself lives in `nbakit/nbakit/facts.py` (one copy, shared across projects); `Fact.display` renders a number with `fmt`+`unit` or passes a plain-language string through unchanged.
- **`<project>.py`** (or `<project>_<name>.py`) — pipeline orchestration only; sequences data → plots → analysis; imports the analysis module inside `main()` to avoid circular imports.
- **`render_docs.py`** — a thin shim over `nbakit.docs`: pins the project's facts.json path and reference-table title, then delegates to the shared render engine. Renders `docs/*.md.j2` templates to `docs/*.md` using the facts JSON. Template delimiter: `<< f("fact.name") >>`. Run after the pipeline (which writes facts.json) and before building PDFs. `generate_report.py` calls `render_all()` automatically. Before rendering, `render_all` normalizes each template to one sentence per source line via `nbakit.sentence_split` (idempotent and render-neutral; see "One sentence per source line" in `questions/CLAUDE.md`). The render engine itself lives in `nbakit/nbakit/docs.py` (one copy, shared across projects).
- **`generate_report.py`** — calls `render_all()` first, then assembles `docs/<project>_findings.md` prose and charts into the PDF; iterates `##` sections in document order with no hardcoded list; TOC auto-generated.
- **`../generate_doc_pdf.py`** — shared Markdown-to-PDF renderer for standalone docs (headings, lists, tables, code fences, images, `--appendix` flag); lives at `questions/` level, not per-project.
- **`../render_stats_tutorial.py`** — the `render_docs.py` shim for `stats_tutorial.md.j2`, which lives at `questions/` level because it's a cross-project doc (cites both `home_court` and `player_rating_overview` facts). No single project's `render_docs.py`/`generate_report.py` renders it; run this script (then `../generate_doc_pdf.py`) directly when the template or either project's facts change.

Test pattern:
- `tests/test_<project>.py` — correctness unit tests for the data/computation layer using synthetic DataFrames; never make live API calls.
- `tests/test_<project>_plots.py` — no-raise smoke tests for each `plot_*`; no pixel or image comparison (brittle across font and library versions).
- The `Fact`/`Facts` class and the render engine are tested canonically in `nbakit/tests/test_facts.py` and `nbakit/tests/test_docs.py` (formatting, string passthrough, dump/load roundtrip, unknown-name `KeyError`; `--reference` table, annotate mode, `render_all` writes `.annotated.md` without clobbering `.md`). Projects no longer carry their own copies of these unit tests; they keep only the data-driven `test_facts_match_results.py` and `test_prose_claims.py` below.
- `tests/test_facts_match_results.py` — for each numeric fact, searches `results.md` for the value at several precisions; fails if a fact's value is absent from `results.md` (catches `FACTS.set()` drifting from its sibling `print()`). No-ops gracefully when facts.json is `{}`.
- `tests/test_prose_claims.py` — loads `*_guards.json`, asserts every guard is `"ok": true`. Skips when guards.json is `{}`.

Adding a new analysis always follows this order: data → plot → analysis (with FACTS.set/guard calls) → tests → `.md.j2` template updates → run pipeline → `python3 render_docs.py` → update findings prose from the results doc.

## nba_api quirks

- `LeagueGameFinder` uses `season_nullable=` and `season_type_nullable=` (not the bare `season=` or `per_mode_*` that other endpoints take). Pass `league_id_nullable="00"` to restrict to the NBA. It returns one row per team per game; `MATCHUP` is `'TEAM vs. OPP'` for home and `'TEAM @ OPP'` for away; `WL` is `'W'` or `'L'`.
- Game IDs from cached CSVs come back as integers and must be zero-padded to 10 digits for any endpoint that takes a game ID: `f"{int(float(gid)):010d}"`.
- `LeagueDashTeamShotLocations` uses `season=` (not `season_nullable=`) and `per_mode_detailed=` (not `per_mode_simple=`). Returns a MultiIndex DataFrame; flatten to flat column names before caching.
- `BoxScoreSummaryV3` `data_sets[3]` contains officials: 4 rows per game (crew chief + 2 refs + replay center).

## Prerequisites

[Quarto](https://quarto.org) must be installed (`brew install --cask quarto`). PDF and HTML are generated via Quarto/Typst, no LaTeX required.
