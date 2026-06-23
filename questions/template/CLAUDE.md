# CLAUDE.md

[One sentence: what question does this project answer?]

See `project_definition.md` for the full question design (hypothesis, comparison set,
confirmation criteria, objections, done criteria).

## Commands

```bash
# Run the full analysis pipeline
MPLBACKEND=Agg python3 PROJECT.py

# Generate the main PDF + HTML report
python3 generate_report.py

# Regenerate any standalone doc PDF + HTML
python3 ../generate_doc_pdf.py docs/PROJECT_findings.md
python3 ../generate_doc_pdf.py docs/PROJECT_summary.md
python3 ../generate_doc_pdf.py docs/PROJECT_stats_explainer.md

# Run all tests
python3 -m pytest

# Install dependencies
pip install -r ../requirements.txt
```

## Architecture

- **`PROJECT_data.py`** — all constants, data fetching, and computation; no matplotlib dependency. All fetched data cached as CSVs under `cache/`.
- **`PROJECT_plots.py`** — all visualization (`plot_*` functions saving SVGs to `generated/images/`); imports data module, holds no data logic.
- **`PROJECT_analysis.py`** — statistical/comparative analysis; `run()` prints all sections to stdout, captured into `docs/PROJECT_results.md`.
- **`PROJECT.py`** — pipeline orchestration only: sequences data → plots → analysis; imports analysis module inside `main()`.
- **`generate_report.py`** — assembles `docs/PROJECT_findings.md` prose + charts into the PDF; iterates `##` sections in document order.
- **`../generate_doc_pdf.py`** — shared Markdown→PDF renderer for standalone docs; lives at `questions/` level.

## Key files

- `project_definition.md` — question design: hypothesis, comparison set, confirmation/refutation criteria, done checklist. Fill out before coding; update if the question evolves.
- `docs/PROJECT_findings.md` — narrative interpretation in numbered `## N. Title` sections; drives the PDF report. Edit by hand when understanding changes.
- `docs/PROJECT_summary.md` — standalone one-page summary.
- `docs/PROJECT_stats_explainer.md` — hand-edited methods companion to `PROJECT_results.md`.
- `docs/PROJECT_results.md` — auto-generated analysis output; **never edit manually**, always re-run the pipeline to refresh.
- `docs/PROJECT_findings_outline.md` — condensed outline cross-referenced to `PROJECT_results.md`; keep in sync with findings (the `/sync-outline` command does this).

## Adding a new analysis

Follow this order:

1. **Data** (`PROJECT_data.py`) — add `fetch_*` and `compute_*`; cache fetches under `cache/`. Every metric needs the subject value *and* the same value across the historical comparison set.
2. **Plot** (`PROJECT_plots.py`) — add a `plot_*`; wire its call into `main()` in `PROJECT.py`.
3. **Analysis** (`PROJECT_analysis.py`) — add a `run_*`; call it from `run()`. Use the box-drawing header convention: `print("─── SECTION TITLE " + "─" * 50)`.
4. **Tests** — correctness tests for new `compute_*` in `tests/test_PROJECT.py`; no-raise smoke test for the new `plot_*` in `tests/test_PROJECT_plots.py`.
5. **docs/PROJECT_findings.md** — add a `## N. Title` section with prose and `![caption](../generated/images/PROJECT_*.svg)` references.
6. **Run** — `MPLBACKEND=Agg python3 PROJECT.py` to regenerate charts and `docs/PROJECT_results.md`, then `python3 generate_report.py`.
