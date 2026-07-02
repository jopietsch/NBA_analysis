#!/usr/bin/env python3
"""
Render a standalone Markdown document to a styled PDF.

Thin wrapper around nbakit.mdpdf — all logic lives there.

    python3 generate_doc_pdf.py stats_tutorial.md
    python3 generate_doc_pdf.py stats_tutorial.md [output.pdf]
    python3 generate_doc_pdf.py stats_tutorial.md --appendix <project>_results.md
    python3 generate_doc_pdf.py home_court_series.md --html-only
"""

import sys

import _bootstrap  # noqa: F401  — use this worktree's nbakit (see _bootstrap.py)
from nbakit.mdpdf import build

if __name__ == "__main__":
    args = sys.argv[1:]
    html_only = "--html-only" in args
    if html_only:
        args.remove("--html-only")
    appendix = None
    if "--appendix" in args:
        idx = args.index("--appendix")
        try:
            appendix = args[idx + 1]
        except IndexError:
            sys.exit("usage: --appendix requires a path (e.g. --appendix <project>_results.md)")
        del args[idx:idx + 2]
    if not args:
        sys.exit("usage: python3 generate_doc_pdf.py <markdown_file> "
                 "[output.pdf] [--appendix <project>_results.md] [--html-only]")
    build(args[0], args[1] if len(args) > 1 else None, appendix_path=appendix, html_only=html_only)
