# CLAUDE.md — questions/

Writing rules that apply to all prose in this project (FINDINGS, SUMMARY, STATS_EXPLAINER, and any other docs).

## No em-dashes

Never write em-dashes (`—`). Replace with the appropriate alternative:
- Introduced list or elaboration → colon (`:`)
- Parenthetical aside → commas or parentheses
- Two independent clauses joined mid-sentence → period (split into two sentences) or semicolon
- Coordinating conjunction mid-sentence → comma before the conjunction

If you find an em-dash in existing text, replace it using the same rules.

## No drama, no exaggeration: clarity only

Write like a careful analyst, not a sportswriter trying to hold attention. Avoid:
- Superlatives that aren't backed by the data ("most dramatic", "stunning", "remarkable")
- Emotional amplifiers ("sharply", "dramatically", "massive") unless the magnitude in the data actually warrants them; and then use the number instead
- Rhetorical buildup before a finding; just state the finding

Prefer: "The gap fell from 1.2 to 0.25 fouls per game." Over: "The whistle shifted dramatically, with the home advantage nearly vanishing."

## Don't overstate what the data supports

Only claim what the analysis can actually establish. Specifically:
- Correlation is not causation. If two series trend together, say they "move together" or "are associated," not that one "caused" or "drove" the other — unless a causal test was run and passed.
- "The data can't explain why" is an acceptable and honest sentence. Use it.
- Graphs show patterns; regressions establish direction and size; neither establishes mechanism unless the design supports it.
- Hypotheses offered as explanations must be labeled as such: "one plausible explanation is…" or "the data is consistent with…" not "this happened because…"
- Don't round up uncertainty. If a playoff result is consistent with the regular-season story but not independently established, say so.

## Write for regular readers

When editing or adding prose to any FINDINGS doc, write like a sports-magazine editor for regular readers. Replace statistical jargon with plain language. Keep the voice concise and clear. Avoid redundancy; repeated information usually confuses rather than reinforces.

## Verify narrative matches data

Before finalizing prose, make sure what is written actually matches the data from RESULTS.md and the generated charts. Don't put specific coefficients or percentages in prose that will go stale; describe direction and relative magnitude, and reference RESULTS.md for exact figures.

## Standard document workflow

Each project uses this naming convention:
- `docs/<project>_findings.md` — main narrative; drives the PDF report
- `docs/<project>_summary.md` — standalone one-page summary
- `docs/<project>_stats_explainer.md` — hand-edited methods companion to `RESULTS.md`
- `docs/RESULTS.md` — auto-generated analysis output; never edit manually, always re-run the pipeline to refresh

Standard commands (run from the project root):
- Main report PDF: `python3 generate_report.py`
- Any standalone doc PDF: `python3 generate_doc_pdf.py docs/<file>.md`

Cascade rules: when a file changes, update its dependents before closing the task:
- `RESULTS.md` changes: update `<project>_stats_explainer.md` so every number and conclusion still matches; regenerate its PDF
- `<project>_findings.md` changes: if headline figures changed, update `<project>_summary.md` to match; regenerate the main report PDF (and summary PDF if updated)
- Any standalone markdown doc changes: regenerate its PDF

## Standard commands

Run all commands from the project root.

```bash
# Run the full analysis pipeline (generates PNGs, runs analysis, writes docs/RESULTS.md)
MPLBACKEND=Agg python3 <project>.py

# Generate the main PDF + HTML report
python3 generate_report.py

# Regenerate any standalone doc PDF + HTML
python3 generate_doc_pdf.py docs/<project>_findings.md
python3 generate_doc_pdf.py docs/<project>_summary.md
python3 generate_doc_pdf.py docs/<project>_stats_explainer.md

# Run all tests
python3 -m pytest

# Install dependencies
pip install -r requirements.txt
```

Always use `MPLBACKEND=Agg` when running the analysis script to suppress display windows. All PNGs and PDFs land in `generated/` (gitignored). `docs/RESULTS.md` is the exception — it is committed. Image references in `docs/` use `../generated/<chart>.png`.

## Standard directory layout

```
<project>/
├── docs/          — prose files (FINDINGS, SUMMARY, STATS_EXPLAINER, RESULTS.md)
├── tests/         — test files; test fixture CSVs go in tests/data/
├── cache/         — fetched data CSVs (gitignored)
└── generated/     — all PNGs and PDFs (gitignored)
```

## Standard architecture

Each project follows a four-module pipeline plus two report generators:

- **`<project>_data.py`** — all constants, data fetching, and computation; no matplotlib dependency. All fetched data is cached as CSVs under `cache/`. This is the only module that calls external APIs.
- **`<project>_plots.py`** — all visualization; imports the data module and holds no data logic of its own. Each `plot_*` function saves a PNG to `generated/`.
- **`<project>_analysis.py`** — statistical/comparative analysis; `run()` prints all output to stdout, which is captured into `docs/RESULTS.md`. Use the box-drawing header convention: `print("─── SECTION TITLE " + "─" * 50)`.
- **`<project>.py`** (or `<project>_<name>.py`) — pipeline orchestration only; sequences data → plots → analysis; imports the analysis module inside `main()` to avoid circular imports.
- **`generate_report.py`** — assembles `docs/<project>_findings.md` prose and PNGs into the PDF; iterates `##` sections in document order with no hardcoded list; TOC auto-generated.
- **`generate_doc_pdf.py`** — general Markdown-to-PDF renderer for standalone docs (headings, lists, tables, code fences, images, `--appendix` flag).

Test pattern:
- `tests/test_<project>.py` — correctness unit tests for the data/computation layer using synthetic DataFrames; never make live API calls.
- `tests/test_<project>_plots.py` — no-raise smoke tests for each `plot_*`; no pixel or image comparison (brittle across font and library versions).

Adding a new analysis always follows this order: data → plot → analysis → tests → findings section → run pipeline → update findings prose from RESULTS.

## nba_api quirks

- `LeagueGameFinder` uses `season_nullable=` and `season_type_nullable=` (not the bare `season=` or `per_mode_*` that other endpoints take). Pass `league_id_nullable="00"` to restrict to the NBA. It returns one row per team per game; `MATCHUP` is `'TEAM vs. OPP'` for home and `'TEAM @ OPP'` for away; `WL` is `'W'` or `'L'`.
- Game IDs from cached CSVs come back as integers and must be zero-padded to 10 digits for any endpoint that takes a game ID: `f"{int(float(gid)):010d}"`.
- `LeagueDashTeamShotLocations` uses `season=` (not `season_nullable=`) and `per_mode_detailed=` (not `per_mode_simple=`). Returns a MultiIndex DataFrame; flatten to flat column names before caching.
- `BoxScoreSummaryV3` `data_sets[3]` contains officials: 4 rows per game (crew chief + 2 refs + replay center).

## Prerequisites

[Quarto](https://quarto.org) must be installed (`brew install --cask quarto`). PDF and HTML are generated via Quarto/Typst, no LaTeX required.

## Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them — don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it — don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.
