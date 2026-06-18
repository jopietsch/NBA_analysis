#!/usr/bin/env python3
"""
Render a standalone Markdown document to a styled PDF.

Thin wrapper around nbakit.mdpdf — all logic lives there.

    python3 generate_doc_pdf.py stats_tutorial.md
    python3 generate_doc_pdf.py home_court_stats_explainer.md [output.pdf]
    python3 generate_doc_pdf.py home_court_stats_explainer.md --appendix RESULTS.md
"""

import os
import sys
from nbakit.mdpdf import build

if __name__ == "__main__":
    args = sys.argv[1:]
    appendix = None
    if "--appendix" in args:
        idx = args.index("--appendix")
        try:
            appendix = args[idx + 1]
        except IndexError:
            sys.exit("usage: --appendix requires a path (e.g. --appendix docs/RESULTS.md)")
        del args[idx:idx + 2]
    if not args:
        sys.exit("usage: python3 generate_doc_pdf.py <markdown_file> "
                 "[output.pdf] [--appendix docs/RESULTS.md]")
    md_path = args[0]
    if len(args) > 1:
        out_path = args[1]
    else:
        stem = os.path.splitext(os.path.basename(md_path))[0]
        out_path = os.path.join("generated", stem + ".pdf")
    build(md_path, out_path, appendix_path=appendix)
