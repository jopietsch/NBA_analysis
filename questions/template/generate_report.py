#!/usr/bin/env python3
"""
Generate the PROJECT PDF report.
Run after PROJECT.py — all charts and PROJECT_results.md must exist.

    python3 generate_report.py
"""

import os

from nbakit.report import ReportConfig, build_report
from render_docs import render_all

OUTPUT_DIR = "generated"

if __name__ == "__main__":
    render_all()
    build_report(ReportConfig(
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
    ))
