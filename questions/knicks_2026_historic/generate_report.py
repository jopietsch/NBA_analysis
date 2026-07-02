#!/usr/bin/env python3
"""
Generate the 2026 Knicks historic-playoffs PDF report.
Run after knicks_2026_historic.py — all PNGs and knicks_2026_historic_results.md must exist.

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
    findings_path="docs/knicks_2026_historic_findings.md",
    results_path="docs/knicks_2026_historic_results.md",
    title="Did the 2026 Knicks Have a Historic Playoff Run?",
    subtitle="The 2025–26 New York Knicks in Context",
    data_line="Data: NBA.com via nba_api",
    footnote=(
        "Data: NBA.com via nba_api. The 2025–26 Knicks playoff run is ranked "
        "against historical playoff runs. See Appendix A for the companion "
        "documents, including the full analysis output (Regression Results)."
    ),
    output_path=os.path.join(OUTPUT_DIR, "knicks_2026_historic_report.pdf"),
    pipeline_cmd="MPLBACKEND=Agg python3 knicks_2026_historic.py",
    include_appendix=False,
)

if __name__ == "__main__":
    run_report(CONFIG, render_all)
