# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

This is for a python system to get data, and analyze to produce a report with graphs and statistics to understand NBA home court advantage and how and why it has changed over time.

Our main questions for all this analysis and the output is 1: has HCA changed over time? 2: what makes up HCA? 3: what contributes to it's change over time, and what does not, but people might thing that it does.

## Key files

- `FINDINGS.md` — narrative interpretation in 13 numbered `##` sections ordered by the three questions (§1–§4 the decline, §5–§6 what makes up HCA, §7–§10 what drove the change, §11–§12 ruled-out factors, §13 Summary); drives the PDF report prose and chart placement; edit by hand when understanding changes
- `RESULTS.md` — auto-generated regression tables; never edit manually, always re-run to refresh

## Commands

```bash
# Run the full analysis (fetches data, generates PNGs, runs regression)
MPLBACKEND=Agg python3 nba_home_court_advantage.py

# Generate the PDF report (run after the above)
python3 generate_report.py

# Run tests
python3 -m pytest

# Run a single test
python3 -m pytest test_nba_home_court_advantage.py::TestClassName::test_method_name

# Install dependencies
pip install -r requirements.txt
```

Use `MPLBACKEND=Agg` when running the script to suppress display windows and generate PNGs only.

## Architecture

Six files:

- **`nba_home_court_data.py`** — all constants, data fetching, and computation; no matplotlib dependency
- **`nba_home_court_plots.py`** — all visualization; imports data module, no data logic of its own
- **`nba_home_court_advantage.py`** — pipeline orchestration only; calls data, plots, and regression in sequence; regression module is imported inside `main()` to avoid circular imports
- **`nba_home_court_regression.py`** — statistical analysis; `run()` is called by `main()`; outputs go to stdout and are captured in `RESULTS.md`
- **`generate_report.py`** — assembles PNGs and `FINDINGS.md` prose into a PDF; iterates `##` sections in order with no hardcoded section list; TOC auto-generated; Appendix A renders `RESULTS.md` verbatim
- **`test_nba_home_court_advantage.py`** — unit tests for data/computation layer only; plotting functions are not tested

All fetched data is cached as CSVs under `cache/` to avoid re-fetching.

## Adding a new analysis

Every analysis follows the same steps, in this order:

1. **Data** (`nba_home_court_data.py`) — add `fetch_*` and `compute_*` functions; all fetched data cached under `cache/`
2. **Plot** (`nba_home_court_plots.py`) — add `plot_*` function; wire the call into `main()` in `nba_home_court_advantage.py`
3. **Regression** (`nba_home_court_regression.py`) — add `run_*` function; call it from `run()`; output goes to stdout and is captured in `RESULTS.md`
4. **Tests** (`test_nba_home_court_advantage.py`) — unit tests for the data/computation layer; use synthetic DataFrames
5. **FINDINGS.md** — add a new `## N. Title` section with placeholder prose and `![Figure N. caption](chart.png)` image references; the PDF picks it up automatically with no changes to `generate_report.py`
\6. **`.gitignore`** — add the new PNG filename
7. **Run** — `MPLBACKEND=Agg python3 nba_home_court_advantage.py` to regenerate all PNGs and `RESULTS.md`
8. **Update FINDINGS.md** — replace placeholder prose with actual numbers and directions from `RESULTS.md`; then regenerate the PDF with `python3 generate_report.py`

## updating FINDINGS.md
- when editing or adding to FINDINGS.md, act like an editor for a sports magazine and editor for their regular readors. Replace any statistical terms or language with something more readable. keep the overall voice concise and clear. We do not redundant information unless it's to strengthen a point. redudant information is usually confusing.
- make sure that the FINDINGS.md actually matches the data from RESULTS.md and from the graphs that are produced
- whenever the order of sections changes in FINDINGS.md, the order needs to also change in RESULTS.md so nba_home_court_regression.py must be updated to the new order
- do not overexplain statistical analysis. make sure everything you write is backed up by the data.
- throughout FINDINGS.md, make sure that both regular season and playoffs are mentinoned. We are trying to determine what changes for the regular season and what changed for the playoffs or post season.
- when FINDINGS.md is edited, regenerate the PDF report with `python 3 generate_report.py`

## nba_api quirks

- `LeagueDashTeamShotLocations` uses `season=` (not `season_nullable=`) and `per_mode_detailed=` (not `per_mode_simple=`). Returns a MultiIndex DataFrame; `fetch_shot_zones()` flattens to flat column names before caching.
- `LeagueGameFinder` uses `season_nullable=` and `season_type_nullable=`.
- `BoxScoreSummaryV3` `data_sets[3]` contains officials (4 rows/game: crew chief + 2 refs + replay center). Game IDs from cached CSVs are integers and must be zero-padded to 10 digits: `f"{int(float(gid)):010d}"`.

## Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
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
- If you notice unrelated dead code, mention it - don't delete it.

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
