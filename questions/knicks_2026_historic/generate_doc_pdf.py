#!/usr/bin/env python3
"""
Render a standalone Markdown document to a styled PDF.

Thin wrapper around nbakit.mdpdf — all logic lives there.

    python3 generate_doc_pdf.py findings_outline.md
    python3 generate_doc_pdf.py findings_outline.md [output.pdf] [--appendix knicks_2026_historic_results.md]
"""

import sys
from nbakit.mdpdf import main

if __name__ == "__main__":
    main(sys.argv[1:])
