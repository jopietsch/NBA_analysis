"""Shared text formatting for analysis RESULTS output.

Promoted from the home_court project so every question renders its RESULTS the
same way (the box-drawing section header convention in questions/CLAUDE.md).
The helpers return strings; callers decide where to print them.
"""

import math

SECTION_WIDTH = 72


def section(title: str, width: int = SECTION_WIDTH) -> str:
    """Main section header, with a leading blank line:  ``─── TITLE ──────────``."""
    pad = max(0, width - 5 - len(title))
    return f"\n─── {title} {'─' * pad}"


def subsection(title: str) -> str:
    """Lighter sub-header:  ``── title ──``."""
    return f"\n── {title} ──"


def stars(p: float) -> str:
    """Significance stars, padded to width 3: ``'***'``, ``' **'``, ``'  *'``, ``'   '``."""
    if math.isnan(p):
        return "   "
    if p < 0.001:
        return "***"
    if p < 0.01:
        return " **"
    if p < 0.05:
        return "  *"
    return "   "


def p_value(p: float) -> str:
    """Format a p-value: ``'<0.001'``, ``'0.034'``, or ``'n/a'``."""
    if math.isnan(p):
        return "n/a"
    return "<0.001" if p < 0.001 else f"{p:.3f}"
