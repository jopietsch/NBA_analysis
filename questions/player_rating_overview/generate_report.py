#!/usr/bin/env python3
"""
Generate the player_rating_overview PDF report.
Run after player_rating_overview.py — all charts and _results.md must exist.

    python3 generate_report.py

Declarative shim: the machinery lives in ``nbakit.report`` (``run_report``
renders the docs templates, then builds the PDF/HTML); this module only
supplies the project's ``ReportConfig``.
"""
import _bootstrap  # noqa: F401  — use this worktree's nbakit (see questions/_bootstrap.py)

import os

from nbakit.report import ReportConfig, run_report
from render_docs import render_all

OUTPUT_DIR = "generated"

CONFIG = ReportConfig(
    findings_path="docs/player_rating_overview_findings.md",
    results_path="docs/player_rating_overview_results.md",
    title="NBA Player Rating Systems: Survey, Comparison, and Combination",
    subtitle="2024–25 season testbed",
    data_line="Data: NBA.com via nba_api; Basketball-Reference; FiveThirtyEight (RAPTOR)",
    footnote=(
        "Data: NBA.com via nba_api, Basketball-Reference, FiveThirtyEight (RAPTOR). "
        "See Appendix A for companion documents."
    ),
    output_path=os.path.join(OUTPUT_DIR, "player_rating_overview_report.pdf"),
    pipeline_cmd="MPLBACKEND=Agg python3 player_rating_overview.py",
    include_appendix=False,
)

if __name__ == "__main__":
    run_report(CONFIG, render_all)
