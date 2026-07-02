#!/usr/bin/env python3
"""
Generate the PROJECT PDF report.
Run after PROJECT.py — all charts and PROJECT_results.md must exist.

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
    findings_path="docs/PROJECT_findings.md",
    results_path="docs/PROJECT_results.md",
    title="TODO: Report title",
    subtitle="TODO: Report subtitle",
    data_line="Data: NBA.com via nba_api",
    footnote=(
        "Data: NBA.com via nba_api. "
        "See Appendix A for companion documents."
    ),
    output_path=os.path.join(OUTPUT_DIR, "PROJECT_report.pdf"),
    pipeline_cmd="MPLBACKEND=Agg python3 PROJECT.py",
    include_appendix=False,
)

if __name__ == "__main__":
    run_report(CONFIG, render_all)
