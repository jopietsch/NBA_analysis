# NBA Home Court Advantage

Fetches every NBA game from 1983-84 through 2024-25 via [nba_api](https://github.com/swar/nba_api),
computes the home team's win percentage per season (regular season and playoffs),
and renders a chart exploring how home court advantage has changed over time.

## Usage

```bash
pip install -r requirements.txt
python3 nba_home_court_advantage.py
```

Game logs are cached as CSVs under `cache/` so repeat runs don't re-fetch from
NBA.com. The first run takes 2-4 minutes (one API call per season/type, with a
polite 1s pause between calls); subsequent runs use the cache and finish almost
instantly.

The script saves `nba_home_court_advantage.png` and displays the figure.

## Output

The figure has four panels:

1. **Regular season vs playoffs** — home win % per season, with an overall
   trend line for each, era shading, and COVID-season highlighting.
2. **Playoffs only** — home win % per season with a separate trend line fit
   per era.
3. **Regular season only** — same as above, but for regular season data.
4. **Era averages** — grouped bar chart comparing regular season vs playoff
   home win % across each rule-change era.

Eras are defined by major NBA rule changes affecting pace/defense (see
`ERA_DEFS` in `nba_home_court_advantage.py` for sources). The 2020 bubble
playoffs (all neutral-site games) are excluded from playoff stats, and the
2019-20 / 2020-21 seasons are flagged as COVID-impacted (limited/no fans).

## Tests

```bash
python3 -m pytest
```

Runs with coverage reporting (configured in `pytest.ini`). Tests cover the
data-fetching/caching logic and era-bucketing math; the plotting code in
`plot_results()` is not unit tested.
