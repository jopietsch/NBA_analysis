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

Game logs and shot zone data are cached as CSVs under `cache/`. The first run takes several minutes
(API calls per season with polite pauses); subsequent runs use the cache and finish almost instantly.

See `FINDINGS.md` for narrative interpretation and `RESULTS.md` for the full regression tables
(auto-generated each run, never edit manually).

## Output

Running the analysis produces eighteen PNG charts and prints fourteen regression analyses to stdout.
Running `generate_report.py` assembles everything into `nba_home_court_advantage_report.pdf` — sixteen
sections plus an appendix with the full regression tables.

## Updating FINDINGS.md

`FINDINGS.md` is the single source of truth for narrative prose and chart placement. Edit it when
findings change, then regenerate the PDF with `python3 generate_report.py`.

Before updating, verify outputs are current and then revise the narrative to match the latest data.
Use this prompt with Claude Code:

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
   - FINDINGS.md has thirteen ## sections (§1–§12 analyses + §13 summary).
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
