# NBA Home Court Advantage

Fetches every NBA game from 1983-84 through 2024-25 via [nba_api](https://github.com/swar/nba_api),
analyzes how home court advantage has changed over time, and investigates the mechanisms behind its
40-year decline using logistic regression and box-score differentials.

## Usage

```bash
pip install -r requirements.txt
MPLBACKEND=Agg python3 nba_home_court_advantage.py
```

Game logs and shot zone data are cached as CSVs under `cache/` so repeat runs don't re-fetch from
NBA.com. The first run takes several minutes (API calls per season with polite pauses); subsequent
runs use the cache and finish almost instantly.

Use `MPLBACKEND=Agg` to suppress display windows and generate PNGs only.

## Output

The script generates five PNG charts and prints a regression analysis to stdout.

### `nba_home_court_advantage.png` — Overview

5-panel figure showing the full history of home court advantage:

1. **Regular season vs playoffs** — home win % per season, with overall trend lines, era shading, and COVID-season highlighting.
2. **Playoffs only** — home win % per season with a separate trend line per era, plus markers for playoff format/scheduling changes (1985, 2003, 2014).
3. **Regular season only** — same as above for regular season data.
4. **Era averages** — grouped bar chart comparing regular season vs playoff home win % across each rule-change era.
5. **Playoff format period averages** — grouped bar chart across the four playoff-format periods (1984; 1985-2002; 2003-2013; 2014-2025).

Eras are defined by major NBA rule changes affecting pace/defense (see `ERA_DEFS` in `nba_home_court_advantage.py`). The 2020 bubble playoffs are excluded from playoff stats.

### `nba_home_court_advantage_rest.png` / `..._rest_playoffs.png` — Rest Analysis

2-panel chart exploring whether schedule-driven rest disparities explain the decline, for regular season and playoffs separately:

1. **Back-to-back rate** — % of games where the home/away team plays on no rest, per season.
2. **Home win % by rest differential** — home win % split by whether the home team, away team, or neither had more rest.

### `nba_home_court_advantage_differentials.png` — Box-Score Differentials

2×3 figure showing per-season home-minus-away differentials for six box-score stats (regular season and playoffs on the same axes):

- **Foul differential** — home teams called for fewer fouls; this gap has sharply narrowed.
- **FG% differential** — home team shooting edge, slightly narrowing.
- **eFG% differential** — same but weighting 3-pointers at 1.5×; the home edge is declining.
- **3PA rate differential** — home vs away share of shots taken from 3; converging as the 3-point revolution normalized shot selection league-wide.
- **3P% differential** — home vs away 3-point accuracy; no clear trend.
- **FT% differential** — home vs away free throw accuracy; no clear trend.

### `nba_home_court_shot_zones.png` — Shot Zone Analysis

2×2 figure showing per-season home-minus-road shot zone % differentials (share of FGA by zone). Data from `LeagueDashTeamShotLocations`; available from ~1996-97 onward.

- **Paint (RA + Non-RA)** — home teams have historically taken a higher share of shots from the paint; that gap is closing.
- **Mid-range** — road teams consistently take a higher mid-range share (~1–1.5 pp); relatively stable.
- **Corner 3** — no systematic home/road difference.
- **Above-break 3** — small differences, converging toward zero.

### Regression Analysis (stdout)

Four analyses printed to stdout after the charts:

1. **Sequential R² decomposition** — how much era, rest, altitude, time zone, and COVID each add to explaining regular-season home win %.
2. **Pre/post-2014 coefficient stability** — whether rest/altitude/tz effects changed after the 2014 Finals format shift.
3. **Factor significance** — bivariate logistic regression for rest, altitude (DEN/UTA), and time zone in regular season vs playoffs.
4. **Foul & shooting differentials by era** — OLS trend per season year for each box-score differential, regular season and playoffs separately.

See `FINDINGS.md` for a summary of the key results.

## Tests

```bash
python3 -m pytest
```

Runs with coverage reporting (configured in `pytest.ini`). Tests cover the data-fetching/caching logic and era-bucketing math; plotting functions are not unit tested.
