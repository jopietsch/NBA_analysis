"""Render ``docs/*.md.j2`` templates to ``docs/*.md`` from the facts data model.

Thin wrapper around ``nbakit.docs`` (the shared render engine). All logic lives
there; this module pins the project's facts.json path and reference-table title.
Run after the analysis pipeline (which writes facts.json) and before
``generate_report.py``.

    python3 render_docs.py             # render docs/*.md.j2 → docs/*.md
    python3 render_docs.py --reference # write the facts reference table
    python3 render_docs.py --annotate  # render to *.annotated.md with fact names
    python3 render_docs.py --watch     # re-render on change (Ctrl-C to stop)
"""
import sys

from nbakit.docs import render_all as _render_all
from nbakit.docs import main as _main

FACTS_JSON = "docs/PROJECT_facts.json"
REFERENCE_MD = "docs/PROJECT_facts_reference.md"
REFERENCE_TITLE = "PROJECT facts reference"


def render_all(facts_path: str = FACTS_JSON, annotate: bool = False) -> list[str]:
    """Render every ``docs/*.md.j2`` template (used by generate_report.py)."""
    return _render_all(facts_path, annotate=annotate)


if __name__ == "__main__":
    _main(sys.argv[1:], facts_json=FACTS_JSON, reference_md=REFERENCE_MD,
          reference_title=REFERENCE_TITLE)
