#!/usr/bin/env python3
"""
Generate the NBA home court advantage PDF report.
Run after home_court.py — all PNGs and home_court_results.md must exist.

    python3 generate_report.py
"""

import os

import home_court_data as nba
from nbakit.report import ReportConfig, build_report

OUTPUT_DIR = "generated"


def _count_regular_season_games() -> int:
    """Count total regular-season games from cached CSVs (each game = 2 rows)."""
    import pandas as pd
    total = 0
    for year in range(nba.START_YEAR, nba.END_YEAR + 1):
        path = nba.cache_path(year, "Regular Season")
        if os.path.exists(path):
            total += len(pd.read_csv(path, usecols=[0]))
    return total // 2


if __name__ == "__main__":
    build_report(ReportConfig(
        findings_path="docs/home_court_findings.md",
        title="NBA Home Court Advantage",
        subtitle="A 40-Year Decline",
        data_line=(
            f"Data: NBA.com  ·  {nba.season_range_label()}"
            f"  ·  {_count_regular_season_games():,} games"
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
    ))
