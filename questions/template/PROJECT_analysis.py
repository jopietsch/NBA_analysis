"""PROJECT analysis module — statistical and comparative analysis.

Add run_* functions here; call them from run(). Use the box-drawing header
convention: print("─── SECTION TITLE " + "─" * 50). Register named facts with
FACTS.set() next to each print() that emits a cited number. At the end of run(),
call FACTS.dump(_FACTS_PATH) and FACTS.dump_guards(_GUARDS_PATH).
"""
import sys

from PROJECT_facts import FACTS, _FACTS_PATH, _GUARDS_PATH


def run(out=None) -> None:
    """Run all analysis sections; output goes to ``out`` (default: stdout)."""
    if out is None:
        out = sys.stdout

    # TODO: add run_* calls here, e.g.:
    # run_summary(out)
    # run_trends(out)

    FACTS.dump(_FACTS_PATH)
    FACTS.dump_guards(_GUARDS_PATH)
