"""PROJECT analysis module — statistical and comparative analysis.

Add run_* functions here; call them from run(). Use the box-drawing header
convention: print("─── SECTION TITLE " + "─" * 50). Register named facts with
FACTS.set() next to each print() that emits a cited number. At the end of run(),
call FACTS.dump(_FACTS_PATH) and FACTS.dump_guards(_GUARDS_PATH), then
write_reference() to refresh the docs/PROJECT_facts_reference.md lookup table.
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

    # Placeholder guard so tests/test_prose_claims.py is exercised from day one.
    # Replace with real FACTS.guard(name, condition, claim, value) calls placed
    # next to the numbers each qualitative prose claim rests on.
    FACTS.guard("example.placeholder", True,
                "placeholder — replace with the project's first real prose claim")

    FACTS.dump(_FACTS_PATH)
    FACTS.dump_guards(_GUARDS_PATH)
    from render_docs import write_reference
    print(f"Saved → {write_reference()}")
