# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the full analysis (fetches data, generates PNGs, runs regression)
MPLBACKEND=Agg python3 nba_home_court_advantage.py

# Run tests
python3 -m pytest

# Run a single test
python3 -m pytest test_nba_home_court_advantage.py::TestClassName::test_method_name

# Install dependencies
pip install -r requirements.txt
```

Use `MPLBACKEND=Agg` when running the script to suppress display windows and generate PNGs only.

## Architecture

The project is two Python modules plus one test file:

**`nba_home_court_advantage.py`** — data pipeline and visualization
- Fetches NBA game logs via `nba_api.stats.endpoints.LeagueGameFinder`, one CSV per season/type cached under `cache/`
- `fetch_all_seasons()` loads or fetches all seasons, returns parallel lists of (season labels, win %)
- `_load_game_log()` / `_merge_home_away_rows()` are shared helpers used by both this module and the regression module
- Altitude analysis (`fetch_altitude_data` / `compute_altitude_stats`) and timezone analysis (`fetch_timezone_data` / `compute_timezone_stats`) were built but their charts were removed; the underlying functions remain for the regression
- `main()` runs the full pipeline and ends with `import nba_home_court_regression; nba_home_court_regression.run()` — the import is inside `main()` to avoid a circular import (regression module imports this one at module level)

**`nba_home_court_regression.py`** — statistical analysis, called by `main()`
- `build_game_dataset()` loads all cached CSVs, computes rest days per team, merges home/away rows, and produces one game-level row with features: `home_win`, `era`, `format_period`, `rest_diff`, `altitude_home`, `tz_diff`, `covid`, `is_playoff`
- Three analyses printed to stdout:
  1. Sequential R² decomposition (regular season only) — era → +rest → +altitude → +tz → +covid
  2. Pre/post-2014 coefficient stability — do rest/altitude/tz effects change after the Finals format shift?
  3. Factor significance summary — bivariate logistic regressions for rest/altitude/tz in regular season vs. playoffs side-by-side
- Uses `statsmodels.formula.api.logit` with patsy formulas; McFadden R² as the fit metric
- Marginal effects reported as `coef × p̄ × (1−p̄) × 100` (percentage points at the mean)

**`test_nba_home_court_advantage.py`** — unit tests for the data/computation layer only; plotting functions are not tested. Tests use small synthetic DataFrames or read from the real `cache/` directory (skipped if cache is empty).

## Key domain constants (in `nba_home_court_advantage.py`)

- `ERA_DEFS` — 6 rule-change eras (1984–2025), used for era shading in charts and as categorical predictor in regression
- `PLAYOFF_FORMAT_PERIODS` — 4 periods defined by 1985/2003/2014 format changes
- `ALTITUDE_TEAMS` — `{"Denver Nuggets", "Utah Jazz"}` — the two high-elevation arenas
- `TEAM_TIMEZONES` — dict mapping franchise name → integer (0=Eastern … 3=Pacific)
- `SKIP_PLAYOFF_YEARS = {2020}` — bubble season excluded from playoff stats
- `COVID_SEASONS = {"19–20", "20–21"}` — flagged in charts and regression
