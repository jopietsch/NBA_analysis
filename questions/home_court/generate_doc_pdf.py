#!/usr/bin/env python3
"""
Render a standalone Markdown document to a styled PDF.

Thin wrapper around nbakit.mdpdf — all logic lives there.

    python3 generate_doc_pdf.py STATS_TUTORIAL.md
    python3 generate_doc_pdf.py STATS_EXPLAINER.md [output.pdf]
    python3 generate_doc_pdf.py STATS_EXPLAINER.md --appendix RESULTS.md
"""

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
            sys.exit("usage: --appendix requires a path (e.g. --appendix RESULTS.md)")
        del args[idx:idx + 2]
    if not args:
        sys.exit("usage: python3 generate_doc_pdf.py <markdown_file> "
                 "[output.pdf] [--appendix RESULTS.md]")
    build(args[0], args[1] if len(args) > 1 else None, appendix_path=appendix)
