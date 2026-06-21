Regenerate all PDFs and HTML for the current project's docs, in the correct cascade order.

This works for any project under `questions/` (home_court, knicks_2026_historic, ...). It runs the project's `generate_report.py` to build the main report from `<project>_findings.md`, then renders every other `docs/*.md` (RESULTS, summary, stats_explainer, outline, ...) to a standalone PDF + HTML. The findings file itself is skipped because the report already includes it.

Run from the project root (the directory that holds `generate_report.py`):

```bash
bash /Users/justin/code/nba_analysis/questions/regen_docs.sh
```

Report which files were saved and flag any errors. If the script reports "no generate_report.py", you are not in a project root — `cd` into the project first.
