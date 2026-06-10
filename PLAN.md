# NBA Home Court Advantage — New Analyses Implementation Plan

Tracks implementation of six new analyses exploring why home court advantage has
been declining, especially in the playoffs. See FINDINGS.md for current narrative
and RESULTS.md for current regression tables.

## Implementation Order

Start with B → C → A → E (all derive from cached data, no new API calls).
Defer D and F — require per-game BoxScoreSummaryV2 calls (820–51k API calls).

---

## Analysis B: Win Margin / Point Differential Trends

**Hypothesis:** Home teams may be winning by less even when they win — margin
compression would show the decline is not just about win/loss flips.

**Key insight:** `PLUS_MINUS` already in cached game logs. Home rows (MATCHUP
contains `vs.`) have PLUS_MINUS = home_pts − away_pts. No merge or new data needed.

### Data Layer (`nba_home_court_advantage.py`)
- [x] `fetch_margin_data(end_year, season_type)` — load game log, filter to home rows, return `margin` (renamed PLUS_MINUS) + `WL`
- [x] `compute_margin_stats(start_year, end_year, season_type, skip_years)` — per-season dict with keys `all_games_mean`, `home_wins_mean`, `home_losses_mean`, `std_dev`
- No new cache files

### Tests (`test_nba_home_court_advantage.py`)
- [x] `TestFetchMarginData::test_returns_none_when_cache_missing`
- [x] `TestFetchMarginData::test_extracts_home_rows_and_renames_column` — synthetic CSV; assert only home rows returned and column renamed to `margin`
- [x] `TestFetchMarginData::test_returns_none_for_empty_dataframe`
- [x] `TestFetchMarginData::test_returns_none_when_no_home_games`
- [x] `TestComputeMarginStats::test_aggregates_means_per_season`
- [x] `TestComputeMarginStats::test_std_dev_is_positive`
- [x] `TestComputeMarginStats::test_skips_years_with_no_data`
- [x] `TestComputeMarginStats::test_skip_years_param_excludes_years`

### Statistical Analysis (`nba_home_court_regression.py`)
- [x] `run_margin_analysis(df)` — OLS `margin ~ year` (all games and wins-only); era-bucketed mean margin table for regular season and playoffs
- [x] Add `margin` column to `build_game_dataset()` (use `PLUS_MINUS_home` from merged df)

### Plot (`nba_home_court_advantage.py`)
- [x] `plot_margin_analysis(reg_seasons, reg_stats, po_seasons, po_stats)` → `nba_home_court_margin.png`
  - Panel 1: mean all-game margin per season (reg + playoffs) with trend lines
  - Panel 2: mean win-only vs loss-only margin per season (regular season)
  - Panel 3: era-bucketed bar chart (reg vs playoff mean margin)

### PDF Integration
- [x] Add `## 9. Win Margin Trends` section to `FINDINGS.md` (placeholder; update after running)
- [x] Add `_section_margin(s, sections)` function to `generate_report.py`
- [x] Add `story += _section_margin(s, sections)` call in `build_report()`

---

## Analysis C: Competitive Balance / Talent Parity

**Hypothesis:** If the salary cap + draft lottery have compressed team quality,
the home team's structural advantage over any given road team is smaller — this
would explain the era coefficients independent of rule changes.

**Key insight:** No new data needed. Per-team win% is computable from existing
game logs via groupby.

### Data Layer (`nba_home_court_advantage.py`)
- [x] `compute_parity_stats(start_year, end_year, season_type, skip_years)` — per-season std dev of team win%; no new fetch function or cache files

### Tests (`test_nba_home_court_advantage.py`)
- [x] `TestComputeParityStats::test_computes_season_win_pct_std_dev`
- [x] `TestComputeParityStats::test_returns_empty_when_cache_missing`
- [x] `TestComputeParityStats::test_skips_years_in_skip_years`

### Statistical Analysis (`nba_home_court_regression.py`)
- [x] `run_parity_correlation(parity_seasons, parity_vals, reg_seasons, reg_pcts)` — Pearson/Spearman correlation; OLS `home_win_pct ~ parity_std_dev`; era-bucketed table
- [x] Call `nba.compute_parity_stats(...)` at top of `run()` and pass results in

### Plot (`nba_home_court_advantage.py`)
- [x] `plot_parity_analysis(parity_seasons, parity_vals, reg_seasons, reg_pcts)` → `nba_home_court_parity.png`
  - Panel 1: dual-axis time series — home win % (left y) and win% std dev (right y) over seasons
  - Panel 2: scatter of parity std dev vs. home win %, one point per season, era-colored with OLS fit

### PDF Integration
- [x] Add `## 11. Competitive Balance and Parity` section to `FINDINGS.md`
- [x] Add `_section_parity(s, sections)` function to `generate_report.py`
- [x] Add `story += _section_parity(s, sections)` call in `build_report()`

---

## Analysis A: Playoff Game-Within-Series Breakdown

**Hypothesis:** Home court advantage may manifest differently by game number
(G1 vs. G7). Has the ability to protect home games eroded across eras?

**Key insight:** GAME_ID encodes game-within-series as its last digit
(`42300137` = game 7). 100% derivable from existing cached game logs.

### Data Layer (`nba_home_court_advantage.py`)
- [ ] `fetch_series_data(end_year)` — load cached playoffs CSV, derive `game_in_series = GAME_ID.str[-1].astype(int)`, `series_key = GAME_ID.str[-3:-1]`, `HOME_WIN = (WL == 'W').astype(int)`; filter to home rows only
- [ ] `compute_series_stats(start_year, end_year, skip_years)` — per-game-number home win % averaged across seasons; return (game_numbers, home_win_pcts, game_counts)
- [ ] `compute_series_stats_by_era(start_year, end_year, skip_years)` — same split by era label
- No new cache files

### `build_game_dataset` change (`nba_home_court_regression.py`)
- [ ] Add `game_in_series` column — last digit of GAME_ID for playoff rows; `NaN` for regular season rows

### Tests (`test_nba_home_court_advantage.py`)
- [ ] `TestFetchSeriesData::test_derives_game_in_series_from_game_id` — synthetic df with known GAME_IDs (`42300101` = G1, `42300137` = G7); assert last digit parsed correctly
- [ ] `TestFetchSeriesData::test_filters_to_home_games_only`
- [ ] `TestFetchSeriesData::test_returns_expected_columns`
- [ ] `TestFetchSeriesData::test_returns_none_when_cache_missing`
- [ ] `TestComputeSeriesStats::test_aggregates_home_win_pct_by_game_number`
- [ ] `TestComputeSeriesStats::test_skip_years_param_excludes_years`
- [ ] `TestComputeSeriesStats::test_skips_years_with_no_data`

### Statistical Analysis (`nba_home_court_regression.py`)
- [ ] `run_series_breakdown(df)` — table: game # | N games | home win % | vs. G1 difference; chi-square test for uniformity across G1–G7; OLS linear trend across game numbers

### Plot (`nba_home_court_advantage.py`)
- [ ] `plot_series_breakdown(game_nums, home_win_pcts, game_counts, era_data)` → `nba_home_court_series_breakdown.png`
  - Panel 1: bar chart of home win % by game number (G1–G7) with sample size annotations; horizontal reference line at overall playoff home win %
  - Panel 2: G1–G7 home win % per era (6 lines, era-colored using ERA_COLORS)

### PDF Integration
- [ ] Add `## 9. Playoff Series Structure` section to `FINDINGS.md`
- [ ] Add `_section_series_breakdown(s, sections)` function to `generate_report.py`
- [ ] Add `story += _section_series_breakdown(s, sections)` call in `build_report()` (place after era-lines section)

---

## Analysis E: Travel Distance

**Hypothesis:** Timezone bucket is a coarse proxy for travel fatigue. Actual
flight miles — and road trip length — may explain variance the timezone variable misses.

**Data acquisition:** No new API calls. Arena coordinates hardcoded as a constant
(~35 franchise entries matching exact TEAM_NAME strings in cache CSVs, accounting
for franchise relocations).

### Data Layer (`nba_home_court_advantage.py`)
- [ ] `ARENA_COORDS: dict[str, tuple[float, float]]` constant near `TEAM_TIMEZONES` — map franchise name → (lat, lon)
- [ ] `_haversine(lat1, lon1, lat2, lon2) -> float` private helper
- [ ] `fetch_travel_data(end_year, season_type)` — merge home/away rows, map team names to coords via ARENA_COORDS, compute haversine distance; drop rows with unknown franchises; return df with `distance_miles`, `HOME_WIN`
- [ ] `compute_travel_stats(start_year, end_year, season_type, skip_years)` — bucket distances: `0–500`, `500–1000`, `1000–1500`, `1500+` miles; return per-bucket per-season home win %
- No new cache files

### Tests (`test_nba_home_court_advantage.py`)
- [ ] `TestHaversine::test_boston_to_la_approximately_2600_miles` — assert within ±50 miles of known value
- [ ] `TestHaversine::test_same_location_returns_zero`
- [ ] `TestHaversine::test_is_symmetric`
- [ ] `TestFetchTravelData::test_computes_distance_from_arena_coords` — synthetic CSV with Boston home vs. LA Lakers; assert distance > 2500 and HOME_WIN correct
- [ ] `TestFetchTravelData::test_drops_unknown_franchises`
- [ ] `TestFetchTravelData::test_returns_none_when_cache_missing`
- [ ] `TestComputeTravelStats::test_aggregates_home_win_pct_by_distance_bucket`
- [ ] `TestComputeTravelStats::test_skips_years_with_no_data`
- [ ] `TestComputeTravelStats::test_skip_years_param_excludes_years`

### Statistical Analysis (`nba_home_court_regression.py`)
- [ ] Add distance bucket coefficients to logistic model (parallel to timezone analysis)
- [ ] `run_travel_analysis(df)` — bivariate logistic per bucket; table of bucket | N | home win % | log-odds | p

### Plot (`nba_home_court_advantage.py`)
- [ ] Reuse `plot_category_road_win_analysis` with distance buckets as category keys → `nba_home_court_travel.png`

### PDF Integration
- [ ] Add `## 12. Travel Distance` section to `FINDINGS.md`
- [ ] Add `_section_travel(s, sections)` function to `generate_report.py`
- [ ] Add `story += _section_travel(s, sections)` call in `build_report()`

---

## Analysis D: Attendance Data (Deferred)

**Data acquisition complexity: HIGH**
Requires `BoxScoreSummaryV2.GameInfo` — one API call per game.
- Full game-level: ~51k calls ≈ 14 hours
- Season-level sampling (20 games/season × 41 seasons): ~820 calls ≈ 15 minutes

**Approach when implemented:**
- `fetch_attendance_summary(end_year)` — sample 20 games/season from `BoxScoreSummaryV2`, average attendance; cache as `attendance_{season}.csv`
- Start with playoffs only (~3k calls) to validate trend before extending to full regular season
- Plot: dual-axis time series of attendance vs. home win %

### Status: Deferred — implement after D's BoxScoreSummaryV2 pattern is established
- [ ] `fetch_attendance_summary(end_year)`
- [ ] `compute_attendance_stats(...)`
- [ ] Tests for above
- [ ] `run_attendance_analysis(df)`
- [ ] `plot_attendance_analysis(...)`
- [ ] `## 13. Attendance` in FINDINGS.md
- [ ] `_section_attendance(s, sections)` in generate_report.py

---

## Analysis F: Referee Crew Assignments (Deferred)

**Data acquisition complexity: VERY HIGH**
Requires `BoxScoreSummaryV2.Officials` — same per-game fetch as D.
- Playoffs only: ~3k calls ≈ 50 minutes
- Full dataset: ~51k calls

**Approach when implemented:**
- Reuse BoxScoreSummaryV2 infrastructure from Analysis D
- Cache as `referee_{season}_{type}.csv` with columns `GAME_ID, OFFICIAL_1, OFFICIAL_2, OFFICIAL_3`
- Analysis: per-crew home foul bias index over time; does crew-level variation explain the foul differential trend?
- This directly tests the "referees call the game more neutrally" finding (Section 6 of FINDINGS.md)

### Status: Deferred — implement after Analysis D establishes BoxScoreSummaryV2 pattern
- [ ] `fetch_all_referee_data(start_year, end_year, season_type)`
- [ ] `compute_referee_bias_stats(...)`
- [ ] Tests for above
- [ ] `run_referee_analysis(df)`
- [ ] `plot_referee_analysis(...)`
- [ ] `## 14. Referee Patterns` in FINDINGS.md
- [ ] `_section_referees(s, sections)` in generate_report.py

---

## Final PDF Wiring (do after all analyses are complete)

Current `build_report()` call order in `generate_report.py`:

```
_section_overview        §1
_section_era_bars        §2
_section_era_lines       §3
_section_regression      §4  (was §4, stays §4)
_section_rest            §5
_section_differentials   §6
_section_shot_zones      §7
_section_summary         §8
_appendix_results
```

Target order after all analyses:

```
_section_overview          §1
_section_era_bars          §2
_section_era_lines         §3
_section_series_breakdown  §9  ← new (Analysis A)
_section_regression        §4
_section_rest              §5
_section_differentials     §6
_section_shot_zones        §7
_section_margin            §10 ← new (Analysis B)
_section_parity            §11 ← new (Analysis C)
_section_travel            §12 ← new (Analysis E)
_section_attendance        §13 ← new (Analysis D, when ready)
_section_referees          §14 ← new (Analysis F, when ready)
_section_summary           §8  (renumber to §15 in FINDINGS.md)
_appendix_results
```

- [ ] Renumber `## 8. Summary` to `## 15. Summary` in FINDINGS.md once all sections added
- [ ] TOC updates automatically from FINDINGS.md `##` headings — no extra work needed
- [ ] Update rank table in Summary section once all findings are in

---

## Progress Tracker

| Analysis | Data | Tests | Regression | Plot | FINDINGS.md | PDF |
|----------|------|-------|------------|------|-------------|-----|
| B: Margin | ✅ | ✅ | ✅ | ✅ | ✅* | ✅ |
| C: Parity | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A: Series | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| E: Travel | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| D: Attend | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
| F: Refs   | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ |
