#!/usr/bin/env python3
"""
Generate a standalone PDF + HTML report from RESULTS.md.
Run after nba_home_court_advantage.py — RESULTS.md must exist.

    python3 generate_results_pdf.py
"""

import os
from nbakit.mdpdf import build

OUTPUT_DIR = "generated"

if __name__ == "__main__":
    build(
        "docs/RESULTS.md",
        output_path=os.path.join(OUTPUT_DIR, "nba_home_court_results.pdf"),
    )
