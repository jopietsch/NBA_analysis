# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Key files

- `FINDINGS.md` — narrative interpretation in 16 numbered `##` sections (§1–§15 analyses + §16 Summary); drives the PDF report prose and chart placement; edit by hand when understanding changes
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

Four Python files:

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
6. **`.gitignore`** — add the new PNG filename
7. **Run** — `MPLBACKEND=Agg python3 nba_home_court_advantage.py` to regenerate all PNGs and `RESULTS.md`
8. **Update FINDINGS.md** — replace placeholder prose with actual numbers and directions from `RESULTS.md`; then regenerate the PDF with `python3 generate_report.py`

## nba_api quirks

- `LeagueDashTeamShotLocations` uses `season=` (not `season_nullable=`) and `per_mode_detailed=` (not `per_mode_simple=`). Returns a MultiIndex DataFrame; `fetch_shot_zones()` flattens to flat column names before caching.
- `LeagueGameFinder` uses `season_nullable=` and `season_type_nullable=`.
- `BoxScoreSummaryV3` `data_sets[3]` contains officials (4 rows/game: crew chief + 2 refs + replay center). Game IDs from cached CSVs are integers and must be zero-padded to 10 digits: `f"{int(float(gid)):010d}"`.
