"""Guard the dual-write: every numeric fact must be cited in results.md.

Thin wrapper: the matcher lives in ``nbakit.facts.assert_facts_in_results``.
Each numeric fact's value must appear in the committed results.md *near text
that shares context with the fact* (tokens from its name segments or ``note``),
so a drifted value can't pass on a coincidental match elsewhere in the file.
This module only pins the project's docs paths and its reviewed exception
lists.

On a brand-new project where facts.json is empty ({}), this test passes
trivially (no facts to check). Populate the exception lists after the first
full pipeline run, guided by the failure message.
"""
import os

from nbakit.facts import assert_facts_in_results

_DOCS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")

# Facts whose value legitimately never appears in results.md (derived or
# reformatted by design). Keep minimal; each entry is a deliberate,
# commented "not in results.md by design" statement.
ALLOW_ABSENT: set[str] = set()

# Documented fallback tier: the value is present, but only as a bare table
# cell / interval bound whose surrounding text shares no word with the fact's
# name or note. Value presence is still required; only the context requirement
# is waived. Keep minimal and reviewed.
ALLOW_NO_CONTEXT: set[str] = set()


def test_every_numeric_fact_appears_in_results():
    assert_facts_in_results(
        os.path.join(_DOCS, "PROJECT_facts.json"),
        os.path.join(_DOCS, "PROJECT_results.md"),
        allow_absent=ALLOW_ABSENT,
        allow_no_context=ALLOW_NO_CONTEXT,
    )
