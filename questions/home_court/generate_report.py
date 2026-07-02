#!/usr/bin/env python3
"""
Generate the NBA home court advantage PDF report.
Run after home_court.py — all PNGs and home_court_results.md must exist.

    python3 generate_report.py

Declarative shim: the machinery lives in ``nbakit.report`` (``run_report``
renders the docs templates, then builds the PDF/HTML); this module only
supplies the project's ``ReportConfig``.
"""
import _bootstrap  # noqa: F401  — use this worktree's nbakit (see questions/_bootstrap.py)

import os

import home_court_data as nba
from nbakit.report import ReportConfig, count_regular_season_games, run_report
from render_docs import render_all

OUTPUT_DIR = "generated"

CONFIG = ReportConfig(
    findings_path="docs/home_court_findings.md",
    title="NBA Home Court Advantage",
    subtitle="A 40-Year Decline",
    data_line=(
        f"Data: NBA.com  ·  {nba.season_range_label()}"
        f"  ·  {count_regular_season_games(nba.cache_path, nba.START_YEAR, nba.END_YEAR):,} games"
    ),
    footnote=(
        f"Data: NBA.com. Analysis covers {nba.season_range_label()}. "
        "Shot zone data available from 1996–97. "
        "Logistic regression uses McFadden R²; marginal effects at the mean. "
        "See Appendix A for companion documents."
    ),
    include_appendix=False,
    output_path=os.path.join(OUTPUT_DIR, "home_court_report.pdf"),
    pipeline_cmd="MPLBACKEND=Agg python3 home_court.py",
)

if __name__ == "__main__":
    run_report(CONFIG, render_all)
