"""Render ``stats_tutorial.md`` from ``stats_tutorial.md.j2``.

Thin wrapper around ``nbakit.docs`` (the shared render engine). stats_tutorial
is a cross-project doc: it lives here at the questions/ level, not inside any
single project's docs/, because its worked examples draw on facts from both
home_court and player_rating_overview. Run after both projects' analysis
pipelines (which write their facts.json) and before building the PDF/HTML
(``generate_doc_pdf.py stats_tutorial.md``).

    python3 render_stats_tutorial.py             # render stats_tutorial.md.j2 → .md
    python3 render_stats_tutorial.py --annotate  # render to .annotated.md with fact names
    python3 render_stats_tutorial.py --watch     # re-render on change (Ctrl-C to stop)
"""
import _bootstrap  # noqa: F401  — use this worktree's nbakit (see _bootstrap.py)

import os
import sys

from nbakit.docs import render_all as _render_all
from nbakit.docs import watch as _watch

# ``docs_dir="."`` treats questions/ itself as the template dir, so render_all's
# glob for ``*.md.j2`` picks up stats_tutorial.md.j2 (the only one here).
DOCS_DIR = "."
FACTS_JSON = os.path.join("home_court", "docs", "home_court_facts.json")
# The tutorial's Part 9 cites player_rating_overview facts; merge that project's
# facts.json so those `<< f("...") >>` calls resolve (home_court facts win any
# name clash; the two namespaces are disjoint today).
EXTRA_FACTS = (os.path.join(
    "player_rating_overview", "docs", "player_rating_overview_facts.json"),)


def render_all(annotate: bool = False) -> list[str]:
    """Render stats_tutorial.md.j2 → stats_tutorial.md (or .annotated.md)."""
    return _render_all(FACTS_JSON, docs_dir=DOCS_DIR, annotate=annotate,
                       extra_facts=EXTRA_FACTS)


if __name__ == "__main__":
    argv = sys.argv[1:]
    if not argv:
        for path in render_all():
            print(f"rendered {path}")
    elif argv == ["--watch"]:
        _watch(FACTS_JSON, docs_dir=DOCS_DIR, extra_facts=EXTRA_FACTS)
    elif argv == ["--annotate"]:
        for path in render_all(annotate=True):
            print(f"rendered {path}")
    else:
        print("usage: render_stats_tutorial.py [--watch | --annotate]")
        sys.exit(2)
