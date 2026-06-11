# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Key files

- `FINDINGS.md` — narrative interpretation in 12 numbered `##` sections (plus Summary); drives the PDF report prose; edit by hand when understanding changes
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

The project is three Python modules plus one test file:

**`nba_home_court_data.py`** — all constants, data fetching, and computation (no matplotlib dependency)

*Data fetching (all results cached as CSVs under `cache/`):*
- `fetch_season_home_pct(end_year, season_type)` — game log → home win %; uses `LeagueGameFinder`
- `fetch_all_seasons()` — iterates all seasons, returns parallel (labels, pcts) lists for reg + playoffs
- `fetch_rest_data(end_year, season_type)` — per-game rest-day info; uses `_add_rest_days()`
- `fetch_altitude_data(end_year, season_type)` — per-game home win tagged with altitude flag
- `fetch_timezone_data(end_year, season_type)` — per-game home win tagged with TZ-diff
- `fetch_differential_data(end_year, season_type)` — per-game home-minus-away box-score differentials: foul, FG%, eFG%, 3PA rate, 3P%, FT%
- `fetch_shot_zones(end_year, season_type, location)` — team-level shot zone FGA totals from `LeagueDashTeamShotLocations` split by 'Home'/'Road'; columns flattened from API MultiIndex before caching
- `fetch_margin_data(end_year, season_type)` — per-home-game point margin from cached game log; renames `PLUS_MINUS` → `margin`; no new cache files (PLUS_MINUS absent before 1995–96)
- `fetch_series_data(end_year)` — playoffs only; derives `game_in_series` (GAME_ID last digit), `series_key` (GAME_ID[-3:-1]), `HOME_WIN`; returns home rows only
- `fetch_travel_data(end_year, season_type)` — merge home/away rows, map franchise names to `ARENA_COORDS`, compute haversine distance; drop unknown franchises; return `['distance_miles', 'HOME_WIN']`

*Shared low-level helpers:*
- `_load_game_log(end_year, season_type)` — load cached game log CSV (one row per team per game)
- `_merge_home_away_rows(df)` — join home/away rows on GAME_ID, producing one row per game
- `_add_rest_days(df)` — add REST column (days since prior game − 1); shared with regression module
- `_compute_box_differentials(merged)` — compute 6 home-minus-away box-score differentials (foul, FG%, eFG%, 3PA rate, 3P%, FT%) from a merged game DataFrame; shared between `fetch_differential_data()` and `build_game_dataset()`

*Aggregation helpers:*
- `_compute_period_averages(period_defs, ...)` — private; buckets reg/playoff win % into time periods; backing both public functions below
- `compute_era_averages(...)` — average win % within each ERA_DEFS period
- `compute_playoff_format_averages(...)` — average win % within each PLAYOFF_FORMAT_PERIODS period
- `compute_rest_stats(...)`, `compute_altitude_stats(...)`, `compute_timezone_stats(...)` — per-season stat series for each analysis
- `compute_differential_stats(...)` — per-season mean home-minus-away box-score differentials
- `compute_shot_zone_stats(...)` — per-season home-minus-road shot zone % differentials; calls `_zone_pcts()` internally
- `compute_margin_stats(...)` — per-season dict of home point margin statistics: `all_games_mean`, `home_wins_mean`, `home_losses_mean`, `std_dev`
- `compute_parity_stats(...)` — per-season std dev of team win%, a measure of competitive balance
- `compute_series_stats(...)` — pooled home win % per game number (G1–G7) across all playoff seasons; returns (game_nums, win_pcts, counts)
- `compute_series_stats_by_era(...)` — same split by era label; excludes game numbers with fewer than 5 games in an era
- `compute_travel_stats(...)` — per-season home win % grouped by `TRAVEL_BUCKETS` (0–500, 500–1000, 1000–1500, 1500+ miles)
- `compute_league_3pa_stats(...)` — per-season league-wide 3PA rate (% of all FGA) and home win %; used for the 3PA vs. HCA analysis
- `bucket_stats_by_era(seasons, stats)` — average any per-season stats dict within each ERA_DEFS period
- `_align_to_seasons(ref_seasons, target_seasons, target_stats, key)` — align a per-season stat series to a reference season list, filling gaps with NaN; used to overlay playoff data on the regular-season x-axis in plot functions

---

**`nba_home_court_plots.py`** — all visualization (imports `nba_home_court_data`, no data logic)

*Drawing helpers (private):*
- `_shade_eras(ax, seasons, label_y=46)` — draw era background shading + dividers; pass `label_y=None` to suppress text labels (used on non-win-% axes)
- `_annotate_bars(ax, bars, color)` — label bar heights with % values
- `_draw_season_overview(ax, reg_seasons, reg_pcts, po_seasons, po_pcts)` — draws the season-by-season reg+playoff combined panel (used by both the combined figure and individual PNG)
- `_draw_paired_bars(ax, reg_avg, po_avg, labels, title)` — draws a reg-season/playoff grouped bar chart panel; used for both the era and playoff-format-period views
- `_plot_season_era_panel(ax, seasons, pcts, color, title, format_markers=False)` — draws season-by-season line + per-era trend lines + era shading + COVID shading; used for the standalone playoff and regular-season panels

*Plotting functions:*
- `plot_results(...)` — saves the combined 5-panel `nba_home_court_advantage.png`, then saves each panel as an individual PNG: `_season`, `_playoffs_era`, `_regular_era`, `_era_bars`, `_format_bars`
- `plot_rest_analysis(...)` — 2-panel back-to-back rate and rest-split home win %
- `plot_category_road_win_analysis(...)` — generic 2-panel for altitude or timezone category comparisons
- `plot_differential_analysis(...)` — 2×3 figure: foul diff, FG%, eFG%, 3PA rate, 3P%, FT% differentials over time (reg + playoffs aligned)
- `plot_shot_zone_analysis(...)` — 2×2 figure: home-minus-road shot zone % differentials (paint, mid-range, corner 3, above-break 3)
- `plot_margin_analysis(...)` — 3-panel figure: all-game margin over time, win/loss margin split, era bar chart → `nba_home_court_margin.png`
- `plot_parity_analysis(...)` — 2-panel figure: dual-axis time series and era-colored scatter → `nba_home_court_parity.png`
- `plot_series_breakdown(...)` — 2-panel figure: bar chart by G1–G7 and era-colored lines → `nba_home_court_series_breakdown.png`
- `plot_category_road_win_analysis(...)` also used for travel → `nba_home_court_travel.png` (regular season; distance buckets as category keys)
- `plot_3pa_hca_analysis(...)` — 3-panel figure: dual-axis time series (3PA rate vs. home win %), regular-season scatter, playoff scatter → `nba_home_court_3pa.png`

---

**`nba_home_court_advantage.py`** — pipeline orchestration only; imports from the two modules above and calls them in sequence via `main()`. The regression module is imported inside `main()` to avoid any chance of circular import.

---

**`nba_home_court_regression.py`** — statistical analysis, called by `main()`

- `build_game_dataset()` — loads all cached CSVs, merges home/away rows, computes rest days via `nba._add_rest_days()`, and box-score differentials via `nba._compute_box_differentials()`; produces one game-level row per game with features:
  - `home_win`, `year`, `is_playoff`, `era`, `format_period`, `covid`
  - `rest_diff`, `altitude_home`, `tz_diff`
  - `foul_diff`, `fg_pct_diff`, `efg_pct_diff`, `tpa_rate_diff`, `fg3_pct_diff`, `ft_pct_diff`
  - `margin` — home team point differential (`PLUS_MINUS_home`); NaN before 1995–96
  - `distance_miles` — haversine miles from away team's arena to home arena; NaN for unknown franchises
  - `game_in_series` — last digit of GAME_ID for playoff rows; NaN for regular season
  - `tpa_rate_avg` — game-level combined 3PA rate: total FG3A / total FGA across both teams (%)

Eleven analyses printed to stdout:
1. **Overall decline** — trend line for `home_win_pct ~ year` at season level; overall slope and per-era slopes for regular season and playoffs
2. **Sequential R² decomposition** — era → +rest → +altitude → +tz → +covid
3. **Pre/post-2014 coefficient stability** — do rest/altitude/tz effects change after the Finals format shift?
4. **Factor significance summary** — bivariate logistic regressions for rest/altitude/tz in regular season vs. playoffs side-by-side
5. **Foul & shooting differentials by era** — trend line (change per season year) for each box-score differential, regular season and playoffs separately
6. **Shot zone differentials by era** — trend line for each shot zone differential (paint, mid-range, corner 3, above-break 3); data from 1996–97
7. **Win margin trends** — era-bucketed mean home point margin (all games, wins-only, losses-only) with trend lines
8. **Competitive balance / parity** — Pearson/Spearman correlation and trend line between team win% std dev and home win %; era-bucketed table
9. **Playoff series structure** — home win % by game number G1–G7; chi-square test for uniformity; weighted trend line across game numbers
10. **Travel distance** — home win % by distance bucket (0–500, 500–1000, 1000–1500, 1500+ miles); bivariate logistic with `distance_miles` as continuous predictor
11. **League-wide 3-point shooting** — season-level Pearson/Spearman r between 3PA rate and home win %; era-bucketed table; game-level logistic bivariate and era-controlled to test within-era mechanism

Uses `statsmodels.formula.api.logit` (binary outcome) and `smf.ols` (differentials). McFadden R² as logistic fit metric. Marginal effects reported as `coef × p̄ × (1−p̄) × 100` (percentage points at the mean). `scipy.stats` for Pearson/Spearman in parity and 3PA analyses. `scipy.stats.chi2_contingency` for series structure chi-square.

---

**`generate_report.py`** — assembles all PNGs and written analysis into a PDF report. Run after `nba_home_court_advantage.py`. Uses `reportlab` (platypus layout engine). Outputs `nba_home_court_advantage_report.pdf`. Narrative prose is read from `FINDINGS.md` via `_parse_findings()` (splits on `##` headings, keyed by exact heading text). Charts are injected at fixed positions within each section function. Appendix A renders `RESULTS.md` verbatim via `Preformatted`. Key helpers: `_section_header(title, s, sections)` returns the `[Paragraph, HR, prose]` preamble shared by all 13 section functions; `_md_to_flowables()` converts markdown body text to reportlab flowables (handles `### ` subheadings, `- ` bullet lists, `**bold**`, `` `code` ``); `_md_inline()` handles inline markup conversion.

---

**`test_nba_home_court_advantage.py`** — unit tests for the data/computation layer only; plotting functions are not tested. Tests use small synthetic DataFrames or read from the real `cache/` directory (skipped if cache is empty).

## Cache files

All fetched data is cached under `cache/` to avoid re-fetching:
- `{season}_{Regular_Season|Playoffs}.csv` — game logs from `LeagueGameFinder` (one row per team per game); all box-score columns present (FGM, FGA, FG3M, FG3A, FTM, FTA, FT_PCT, PF, etc.)
- `shot_zones_{season}_{type}_{Home|Road}.csv` — team shot zone FGA totals from `LeagueDashTeamShotLocations`; columns: TEAM_ID, TEAM_NAME, FGA_RA, FGA_NON_RA, FGA_MR, FGA_LC3, FGA_RC3, FGA_ATB3, FGA_BC

## Key domain constants (in `nba_home_court_data.py`)

- `ERA_DEFS` — 6 rule-change eras (1984–2025), used for era shading in charts and as categorical predictor in regression
- `PLAYOFF_FORMAT_PERIODS` — 4 periods defined by 1985/2003/2014 format changes
- `ALTITUDE_TEAMS` — `{"Denver Nuggets", "Utah Jazz"}` — the two high-elevation arenas
- `TEAM_TIMEZONES` — dict mapping franchise name → integer (0=Eastern … 3=Pacific)
- `ARENA_COORDS` — dict mapping franchise name → (lat, lon); covers all ~35 historical franchises; used with `_haversine()` to compute away team travel distance
- `TRAVEL_BUCKETS` — the four distance bin keys (0–500, 500–1000, 1000–1500, 1500+ miles); `TRAVEL_COLORS` and `TRAVEL_LABELS` are in `nba_home_court_plots.py`
- `SKIP_PLAYOFF_YEARS = {2020}` — bubble season excluded from playoff stats
- `COVID_SEASONS = {"19–20", "20–21"}` — flagged in charts and regression
- `SHOT_ZONE_GROUPS` — maps zone names to flat FGA column names in the shot-zone cache CSVs
- `_ZONE_COL_MAP` — maps `LeagueDashTeamShotLocations` MultiIndex column tuples to flat names

## nba_api quirks

- `LeagueDashTeamShotLocations` uses `season=` (not `season_nullable=`) and `per_mode_detailed=` (not `per_mode_simple=`). Returns a MultiIndex DataFrame; `fetch_shot_zones()` flattens to flat column names before caching.
- `LeagueGameFinder` uses `season_nullable=` and `season_type_nullable=`.
