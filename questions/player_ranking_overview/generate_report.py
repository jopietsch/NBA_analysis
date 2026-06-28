#!/usr/bin/env python3
"""
Generate the player_ranking_overview PDF report.
Run after player_ranking_overview.py — all charts and _results.md must exist.

    python3 generate_report.py
"""

import os

from nbakit.report import ReportConfig, build_report
from render_docs import render_all

OUTPUT_DIR = "generated"

if __name__ == "__main__":
    render_all()
    build_report(ReportConfig(
        findings_path="docs/player_ranking_overview_findings.md",
        results_path="docs/player_ranking_overview_results.md",
        title="NBA Player Rating Systems: Survey, Comparison, and Combination",
        subtitle="2024–25 season testbed",
        data_line="Data: NBA.com via nba_api; Basketball-Reference; FiveThirtyEight (RAPTOR)",
        footnote=(
            "Data: NBA.com via nba_api, Basketball-Reference, FiveThirtyEight (RAPTOR). "
            "See Appendix A for companion documents."
        ),
        output_path=os.path.join(OUTPUT_DIR, "player_ranking_overview_report.pdf"),
        pipeline_cmd="MPLBACKEND=Agg python3 player_ranking_overview.py",
        include_appendix=False,
    ))
