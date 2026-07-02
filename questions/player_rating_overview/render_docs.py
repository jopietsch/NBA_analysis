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
import _bootstrap  # noqa: F401  — use this worktree's nbakit (see questions/_bootstrap.py)

import sys

from nbakit.docs import project_shim

render_all, write_reference, _main = project_shim(
    facts_json="docs/player_rating_overview_facts.json",
    reference_md="docs/player_rating_overview_facts_reference.md",
    reference_title="Player rating overview facts reference",
)

if __name__ == "__main__":
    _main(sys.argv[1:])
