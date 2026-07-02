"""Guard the dual-write: every numeric fact must be cited in results.md.

Thin wrapper: the matcher lives in ``nbakit.facts.assert_facts_in_results``.
Each numeric fact's value must appear in the committed results.md *near text
that shares context with the fact* (tokens from its name segments or ``note``),
so a drifted value can't pass on a coincidental match elsewhere in the file.
This module only pins the project's docs paths and its reviewed exception
lists.
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
ALLOW_NO_CONTEXT: set[str] = {
    # +7.60: bare upper bound in "90% credible interval: [+1.80, +7.60]"; the
    # §14 HIERARCHICAL section header sits 11 lines above, outside the window.
    "hier.ci.hi",
}


def test_every_numeric_fact_appears_in_results():
    assert_facts_in_results(
        os.path.join(_DOCS, "knicks_2026_historic_facts.json"),
        os.path.join(_DOCS, "knicks_2026_historic_results.md"),
        allow_absent=ALLOW_ABSENT,
        allow_no_context=ALLOW_NO_CONTEXT,
    )
