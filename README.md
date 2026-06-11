# NBA Home Court Advantage

Fetches every NBA game from 1983-84 through 2024-25 via [nba_api](https://github.com/swar/nba_api),
analyzes how home court advantage has changed over time, and investigates the mechanisms behind its
40-year decline using logistic regression and box-score differentials.

## Usage

```bash
pip install -r requirements.txt

# Run the full analysis — generates all PNGs and prints regression output
MPLBACKEND=Agg python3 nba_home_court_advantage.py

# Generate the PDF report (run after the above)
python3 generate_report.py
```

Game logs and shot zone data are cached as CSVs under `cache/` so repeat runs don't re-fetch from
NBA.com. The first run takes several minutes (API calls per season with polite pauses); subsequent
runs use the cache and finish almost instantly.

Use `MPLBACKEND=Agg` to suppress display windows and generate PNGs only.

See `FINDINGS.md` for narrative interpretation and `RESULTS.md` for the full
regression tables (auto-generated each run, never edit manually).

## Output

### PNG charts

`nba_home_court_advantage.py` saves sixteen PNG charts.

**Overview (combined and individual panels):**

`nba_home_court_advantage.png` is a combined 5-panel figure. Each panel is also saved individually:

| File | Contents |
|------|----------|
| `nba_home_court_advantage_season.png` | Regular season vs playoffs home win % per season, overall trend lines, era shading, COVID highlighting |
| `nba_home_court_advantage_regular_era.png` | Regular-season home win % per season with a separate trend line per era |
| `nba_home_court_advantage_playoffs_era.png` | Same for playoffs, with playoff format-change markers (1985, 2003, 2014) |
| `nba_home_court_advantage_era_bars.png` | Home win % averaged within each rule-change era (reg season vs playoffs) |
| `nba_home_court_advantage_format_bars.png` | Home win % averaged within each playoff-format period |

Eras are defined by major NBA rule changes affecting pace/defense (see `ERA_DEFS` in `nba_home_court_data.py`). The 2020 bubble playoffs are excluded from playoff stats.

**Rest analysis:**

| File | Contents |
|------|----------|
| `nba_home_court_advantage_rest.png` | Regular-season back-to-back rates and home win % by rest differential |
| `nba_home_court_advantage_rest_playoffs.png` | Same for playoffs (first-round games excluded — no prior playoff game for rest calc) |

**Mechanism analysis:**

| File | Contents |
|------|----------|
| `nba_home_court_advantage_differentials.png` | 2×3 figure: per-season home-minus-away differentials for foul rate, FG%, eFG%, 3PA rate, 3P%, FT% |
| `nba_home_court_shot_zones.png` | 2×2 figure: per-season home-minus-road shot zone % differentials (paint, mid-range, corner 3, above-break 3); data from 1996-97 onward |
| `nba_home_court_margin.png` | 3-panel figure: home team point margin over time (all games, wins/losses split, era bar chart) |
| `nba_home_court_parity.png` | 2-panel figure: dual-axis time series of home win % and team win% std dev; era-colored scatter with trend line |
| `nba_home_court_series_breakdown.png` | 2-panel figure: home win % by game number G1–G7 (pooled) and per-era lines |
| `nba_home_court_travel.png` | 2-panel figure: home win % by away team travel distance bracket (per-season trend and era-averaged bars) |
| `nba_home_court_3pa.png` | 3-panel figure: league-wide 3PA rate vs. home win % (dual-axis time series, regular-season scatter, playoff scatter) |
| `nba_home_court_pace.png` | 3-panel figure: league-wide pace (possessions per 48 min) vs. home win % (dual-axis time series, regular-season scatter, playoff scatter) |

### Regression analysis (stdout)

Twelve analyses printed to stdout:

1. **Overall decline** — trend line for home win % on year at season level; overall and per-era slopes.
2. **Sequential R² decomposition** — how much era, rest, altitude, time zone, and COVID each add to explaining regular-season home win %.
3. **Pre/post-2014 coefficient stability** — whether rest/altitude/tz effects changed after the 2014 Finals format shift.
4. **Factor significance** — bivariate logistic regression for rest, altitude (DEN/UTA), and time zone in regular season vs playoffs.
5. **Foul & shooting differentials by era** — trend line per season year for each box-score differential, regular season and playoffs separately.
6. **Shot zone differentials by era** — trend line for each shot zone differential (paint, mid-range, corner 3, above-break 3); data from 1996–97.
7. **Win margin trends** — era-bucketed mean home point margin (all games, wins-only, losses-only) with trend lines; regular season and playoffs.
8. **Competitive balance / parity** — Pearson/Spearman correlation and trend line: does team win% disparity predict home court advantage?
9. **Playoff series structure** — home win % by game number G1–G7; chi-square test for uniformity; weighted trend line.
10. **Travel distance** — home win % by away team travel distance bucket (0–500, 500–1000, 1000–1500, 1500+ miles); bivariate logistic with continuous distance predictor.
11. **League-wide 3-point shooting** — season-level and game-level relationship between 3PA rate and home win %; within-era game-level test to separate trend from mechanism.
12. **Pace** — season-level and game-level relationship between possessions per 48 min and home win %; within-era test; result is a null/reversed finding (pace does not explain the decline).

### PDF report

`generate_report.py` assembles all charts and written analysis into a single PDF:

```bash
python3 generate_report.py
# → nba_home_court_advantage_report.pdf
```

The report contains fourteen sections plus an appendix. Narrative prose and chart placement are
driven entirely by `FINDINGS.md` — `generate_report.py` iterates its `##` sections in order with
no hardcoded section list. Edit `FINDINGS.md` to update prose or reorder charts; the PDF picks up
changes automatically. Appendix A renders `RESULTS.md` verbatim and is the authoritative source for
coefficient values and significance levels.

## Updating FINDINGS.md

`FINDINGS.md` is the single source of truth for narrative prose and chart
placement. It has thirteen numbered analysis sections (§1–§13) plus §14 Summary.
Charts are embedded as `![caption](filename.png)` image references within the
relevant section — the PDF picks them up automatically. Edit it when findings
change, then regenerate the PDF with `python3 generate_report.py`.

`RESULTS.md` is auto-generated each run — never edit manually.

Before updating `FINDINGS.md`, verify outputs are current and then revise the
narrative to match the latest data. Use this prompt with Claude Code:

```
Before updating FINDINGS.md, verify that the analysis outputs are current:

1. Check that RESULTS.md and all PNG files exist and were modified more recently
   than nba_home_court_advantage.py and nba_home_court_regression.py.
   Use: stat -f "%m %N" RESULTS.md *.png nba_home_court_advantage.py nba_home_court_regression.py
   If any output is older than the source files, stop and say so — the analysis
   must be re-run first: MPLBACKEND=Agg python3 nba_home_court_advantage.py

2. Read RESULTS.md in full to understand the current numbers, significance levels,
   and era-by-era breakdowns.

3. Read the current FINDINGS.md.

4. Update FINDINGS.md to reflect the current analysis. Rules:
   - FINDINGS.md has fourteen ## sections (§1–§13 analyses + §14 Summary).
     Do not rename or renumber sections without also updating any cross-references.
   - ### subheadings within a section are rendered as sub-headers in the PDF.
   - No specific coefficient values, R² values, or percentage points — those
     belong in RESULTS.md and go stale. Reference RESULTS.md for specifics.
   - Use qualitative language: "significant", "dominant", "narrowing", "no effect".
   - Describe the direction and relative magnitude of each effect.
   - If anything in the current RESULTS.md contradicts what FINDINGS.md says,
     update the narrative to match.

5. After editing FINDINGS.md, regenerate the PDF:
   python3 generate_report.py
```

## Tests

```bash
python3 -m pytest
```

Runs with coverage reporting (configured in `pytest.ini`). Tests cover the data-fetching/caching
logic, era-bucketing math, differential computations, and shot zone aggregation. Plotting functions
are not unit tested.
