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
- [x] `fetch_series_data(end_year)` — load cached playoffs CSV, derive `game_in_series = GAME_ID.str[-1].astype(int)`, `series_key = GAME_ID.str[-3:-1]`, `HOME_WIN = (WL == 'W').astype(int)`; filter to home rows only
- [x] `compute_series_stats(start_year, end_year, skip_years)` — per-game-number home win % averaged across seasons; return (game_numbers, home_win_pcts, game_counts)
- [x] `compute_series_stats_by_era(start_year, end_year, skip_years)` — same split by era label
- No new cache files

### `build_game_dataset` change (`nba_home_court_regression.py`)
- [x] Add `game_in_series` column — last digit of GAME_ID for playoff rows; `NaN` for regular season rows

### Tests (`test_nba_home_court_advantage.py`)
- [x] `TestFetchSeriesData::test_derives_game_in_series_from_game_id` — synthetic df with known GAME_IDs (`42300101` = G1, `42300137` = G7); assert last digit parsed correctly
- [x] `TestFetchSeriesData::test_filters_to_home_games_only`
- [x] `TestFetchSeriesData::test_returns_expected_columns`
- [x] `TestFetchSeriesData::test_returns_none_when_cache_missing`
- [x] `TestComputeSeriesStats::test_aggregates_home_win_pct_by_game_number`
- [x] `TestComputeSeriesStats::test_skip_years_param_excludes_years`
- [x] `TestComputeSeriesStats::test_skips_years_with_no_data`

### Statistical Analysis (`nba_home_court_regression.py`)
- [x] `run_series_breakdown(df)` — table: game # | N games | home win % | vs. G1 difference; chi-square test for uniformity across G1–G7; OLS linear trend across game numbers

### Plot (`nba_home_court_advantage.py`)
- [x] `plot_series_breakdown(game_nums, home_win_pcts, game_counts, era_data)` → `nba_home_court_series_breakdown.png`
  - Panel 1: bar chart of home win % by game number (G1–G7) with sample size annotations; horizontal reference line at overall playoff home win %
  - Panel 2: G1–G7 home win % per era (6 lines, era-colored using ERA_COLORS)

### PDF Integration
- [x] Add `## 9. Playoff Series Structure` section to `FINDINGS.md`
- [x] Add `_section_series_breakdown(s, sections)` function to `generate_report.py`
- [x] Add `story += _section_series_breakdown(s, sections)` call in `build_report()` (place after era-lines section)

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

## Analysis F: Referee Crew Assignments

**Status: Ready to implement (playoffs-only first; expand to regular season if findings are interesting)**

**Data acquisition complexity: HIGH**
- Playoffs only: 3,207 unique game IDs across 41 seasons ≈ 50–60 minutes to fetch
- Full dataset: ~51k calls (defer until playoffs-only results justify it)

### API decisions (verified 2026-06-11)

- **Use `BoxScoreSummaryV3`**, not V2. V2 has known data availability issues for games on or after
  4/10/2025 and nba_api now warns to migrate. V3 has the same `game_id` parameter and same timeout.
- **Officials are in `data_sets[3]`** — confirmed on game `0042400401` (2024–25 playoffs):
  4 rows with columns `gameId, personId, name, nameI, firstName, familyName, jerseyNum`.
  The 4 officials = crew chief + 2 referees + replay center official.
- **Game IDs**: cached playoff CSVs have integer GAME_ID values (e.g. `42400407`). Must
  zero-pad to 10 digits when calling the API: `f"{game_id:010d}"`.
- **Cache file per season**: `cache/referee_{season}_{type}.csv` with columns
  `GAME_ID, personId, name` (one row per official per game, 4 rows/game).
  Flat format is simpler than pivoting to OFFICIAL_1/2/3 — join on GAME_ID at analysis time.

### Analysis design

Primary question: **does referee crew composition predict home foul differential, and has
crew-level home bias changed over time?**

- **Home foul bias per official**: join referee rows to the game-level dataset on GAME_ID;
  compute each official's per-game home foul differential (using `foul_diff` column already
  in `build_game_dataset()`); average across all games they worked.
- **Era trend**: group bias by era label — test whether crew-level bias has declined in sync
  with the foul differential trend (§6 of FINDINGS.md).
- **Top/bottom officials**: rank officials by mean home foul bias; flag outliers.
- **Regression**: game-level logistic — does presence of a high-bias crew predict `home_win`
  above and beyond era + rest + altitude + tz?

### Data Layer (`nba_home_court_data.py`)
- [x] `fetch_referee_data(end_year, season_type)` — for each unique GAME_ID in the cached
      game log, call `BoxScoreSummaryV3(game_id=f"{gid:010d}", timeout=60)`, extract
      `data_sets[3]`, keep `GAME_ID, personId, name`; cache result as
      `cache/referee_{season}_{type}.csv`; skip if cache file already exists; sleep
      `SLEEP_SEC` between calls
- [x] `fetch_all_referee_data(start_year, end_year, season_type, skip_years)` — iterate
      seasons, call `fetch_referee_data`, return concatenated DataFrame
- [x] `compute_referee_bias_stats(ref_df, start_year, end_year, season_type, skip_years,
      min_games)` — builds foul_diff from game logs internally; per-official mean,
      n_games, era_means; returns list of dicts sorted by mean_foul_diff

### Tests (`test_nba_home_court_advantage.py`)
- [x] `TestFetchRefereeData::test_reads_from_cache_when_present`
- [x] `TestFetchRefereeData::test_returns_none_when_no_game_log`
- [x] `TestComputeRefereeBiasStats::test_computes_per_official_mean_foul_diff`
- [x] `TestComputeRefereeBiasStats::test_excludes_officials_below_min_games`

### Statistical Analysis (`nba_home_court_regression.py`)
- [x] `run_referee_analysis()` — fetches ref_df internally; per-official mean home foul
      bias table (top 10 / bottom 10); era-bucketed distribution; distribution stats

### Plot (`nba_home_court_plots.py`)
- [x] `plot_referee_analysis(bias_stats)` → `nba_home_court_referee.png`
  - Panel 1: top/bottom 15 officials ranked by career mean home foul diff
  - Panel 2: box plots of per-official era-mean foul diff by era

### PDF / docs
- [x] Add `## 16. Referee Patterns` section with placeholder prose + `![caption](nba_home_court_referee.png)` to `FINDINGS.md`
- [x] Add `nba_home_court_referee.png` to `.gitignore`
- [x] Update `README.md` (PNG table, regression list, counts) and `CLAUDE.md` (function lists, analysis count)
- [ ] Run `MPLBACKEND=Agg python3 nba_home_court_advantage.py` to regenerate PNGs and `RESULTS.md`
- [ ] Update `FINDINGS.md` §16 with actual numbers from `RESULTS.md`; regenerate PDF

---

## PDF Integration (how it works now)

`generate_report.py` no longer has `_section_*` functions or a pipeline list.
`build_report()` iterates `FINDINGS.md` `##` sections in order — each section's
prose and `![caption](path)` image references render automatically. TOC is also
auto-generated from section headings.

**To add a new analysis to the PDF:** add a `## N. Title` section to `FINDINGS.md`
with prose and one or more `![Figure N. caption text](chart_filename.png)` lines.
That's it — no changes to `generate_report.py` needed.

Current FINDINGS.md section order (§1–§15):
```
§1  The Decline
§2  Era and Format Period Analysis
§3  Per-Era Trend Lines
§4  What Explains the Decline?
§5  Rest and Schedule Balance
§6  Box-Score Differentials
§7  Shot Zone Analysis
§8  Playoff Series Structure
§9  Win Margin Trends
§10 Competitive Balance and Parity
§11 Travel Distance
§12 3-Point Shooting and Home Court Advantage
§13 Pace and Home Court Advantage
§14 Franchise Home Court Advantage
§15 Summary          ← renumber to §16 once F is added
```

- [ ] Update Summary rank table in FINDINGS.md once F findings are in
- [ ] Renumber `## 15. Summary` to `## 16. Summary` once F is added

---

## Progress Tracker

| Analysis | Data | Tests | Regression | Plot | FINDINGS.md | PDF |
|----------|------|-------|------------|------|-------------|-----|
| B: Margin | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| C: Parity | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| A: Series | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| E: Travel | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| G: Pace   | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| H: TeamHCA| ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| F: Refs   | ✅ | ✅ | ✅ | ✅ | ✅ | ⬜ |
