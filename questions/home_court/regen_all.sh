#!/usr/bin/env bash
set -e
cd "$(dirname "$0")"
python3 generate_report.py
python3 generate_doc_pdf.py docs/RESULTS.md
python3 generate_doc_pdf.py docs/home_court_findings_outline.md
python3 generate_doc_pdf.py docs/home_court_summary.md
python3 generate_doc_pdf.py docs/home_court_investigation.md
python3 generate_doc_pdf.py docs/home_court_stats_explainer.md
