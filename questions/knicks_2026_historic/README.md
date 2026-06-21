# Did the 2026 Knicks Have a Historic Playoff Run?

Fetches NBA playoff game logs via [nba_api](https://github.com/swar/nba_api) and
ranks the 2025–26 New York Knicks playoff run against historical playoff runs to
answer one question: **how historic was it?**

Built on the same toolchain and conventions as the sibling `home_court`
project (Python data pipeline → matplotlib charts → statistical analysis →
reportlab PDF).

> **Status:** scaffolded. The data/cache plumbing and report pipeline are in
> place; the specific "historic" metrics and the findings narrative are still to
> be designed. See `CLAUDE.md` → "Adding a new analysis".

## Usage

```bash
pip install -r requirements.txt

# Run the full analysis — fetches data, generates PNGs, writes RESULTS.md
MPLBACKEND=Agg python3 knicks_2026_historic.py

# Generate the PDF report (run after the above)
python3 generate_report.py
```

Game logs are cached as CSVs under `cache/`. The first run hits the NBA.com API
(with polite pauses); subsequent runs use the cache.

See `knicks_2026_historic_findings.md` for narrative interpretation and `RESULTS.md` for the
auto-generated analysis output (never edit by hand).

## Tests

```bash
python3 -m pytest
```

Coverage is configured in `pytest.ini`. Tests cover the data/computation layer;
plotting functions get no-raise smoke tests only.
