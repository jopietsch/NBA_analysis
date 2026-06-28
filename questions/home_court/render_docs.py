"""Render ``docs/*.md.j2`` templates to ``docs/*.md`` from the facts data model.

Thin wrapper around ``nbakit.docs`` (the shared render engine). All logic lives
there; this module pins home_court's facts.json path, reference-table title, and
the shared ``../stats_tutorial.md.j2`` (which lives one level up in questions/
but draws on the same facts). Run after the analysis pipeline (which writes
facts.json) and before ``generate_report.py``.

    python3 render_docs.py             # render docs/*.md.j2 → docs/*.md
    python3 render_docs.py --reference # write the facts reference table
    python3 render_docs.py --annotate  # render to *.annotated.md with fact names
    python3 render_docs.py --watch     # re-render on change (Ctrl-C to stop)
"""
import os
import sys

# Use this worktree's nbakit, not a global install (see conftest.py).
_d = os.path.dirname(os.path.abspath(__file__))
while os.path.dirname(_d) != _d and not os.path.isdir(os.path.join(_d, "nbakit", "nbakit")):
    _d = os.path.dirname(_d)
sys.path.insert(0, os.path.join(_d, "nbakit"))

from nbakit.docs import render_all as _render_all
from nbakit.docs import write_reference as _write_reference
from nbakit.docs import main as _main

FACTS_JSON = "docs/home_court_facts.json"
REFERENCE_MD = "docs/home_court_facts_reference.md"
REFERENCE_TITLE = "Home-court facts reference"
# The stats tutorial lives one level above the project (questions/) but draws on
# the same facts, so it isn't in docs/. Render it too.
EXTRA_TEMPLATES = (os.path.join("..", "stats_tutorial.md.j2"),)


def render_all(facts_path: str = FACTS_JSON, annotate: bool = False) -> list[str]:
    """Render every ``docs/*.md.j2`` template plus the stats tutorial."""
    return _render_all(facts_path, annotate=annotate, extra_templates=EXTRA_TEMPLATES)


def write_reference(facts_path: str = FACTS_JSON, out_path: str = REFERENCE_MD,
                    title: str = REFERENCE_TITLE) -> str:
    """Write the facts reference table (delegates to nbakit with pinned paths)."""
    return _write_reference(facts_path, out_path, title)


if __name__ == "__main__":
    _main(sys.argv[1:], facts_json=FACTS_JSON, reference_md=REFERENCE_MD,
          reference_title=REFERENCE_TITLE, extra_templates=EXTRA_TEMPLATES)
