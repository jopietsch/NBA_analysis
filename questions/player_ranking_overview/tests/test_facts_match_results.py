"""Guard the dual-write: every numeric fact's value must appear in results.md.

``docs/player_ranking_overview_facts.json`` and ``docs/player_ranking_overview_results.md``
are both produced by ``player_ranking_overview_analysis.py``, but via separate code paths
(``FACTS.set`` vs ``print``). They share the computed variable today, so they
can't drift — but a future edit could change a print without its fact (or vice
versa). This test asserts each numeric fact's value is present in the committed
``results.md`` (tried at several precisions), catching that drift.

String facts (plain-language phrasings) are skipped. Facts whose value
legitimately does not appear verbatim in results.md are listed in
``ALLOW_ABSENT``, which should stay small and reviewed.
"""
import json
import os

_DOCS = os.path.join(os.path.dirname(os.path.dirname(__file__)), "docs")
_FACTS = os.path.join(_DOCS, "player_ranking_overview_facts.json")
_RESULTS = os.path.join(_DOCS, "player_ranking_overview_results.md")

# Curated after a first run: facts whose value is derived/reformatted and so does
# not appear verbatim in results.md. Keep minimal; each entry is a deliberate
# "not in results.md by design" statement.
#
# cov.n_systems = 8 (integer 8): the single digit "8" is filtered by _candidates
# because len("8") == 1 and "8".isdigit(); "8.0" and "8.00" don't appear verbatim
# in results.md's "Rating systems present: 8" line.
ALLOW_ABSENT: set[str] = {
    "cov.n_systems",
}


def _candidates(value: float) -> set[str]:
    """String forms of a numeric value to search for in results.md."""
    forms: set[str] = set()
    for p in range(0, 5):
        forms.add(f"{value:.{p}f}")
        forms.add(f"{abs(value):.{p}f}")
        forms.add(f"{value:+.{p}f}")
    # Drop forms that are too short to be a meaningful match (a bare "0"/"8"
    # appears everywhere); require at least one digit and not a lone integer 0-9.
    return {s for s in forms if not (s.lstrip("+-").isdigit() and len(s.lstrip("+-")) <= 1)}


def test_every_numeric_fact_appears_in_results():
    with open(_FACTS) as fh:
        facts = json.load(fh)
    with open(_RESULTS) as fh:
        results = fh.read()

    missing = []
    for name, rec in facts.items():
        value = rec["value"]
        if not isinstance(value, (int, float)) or name in ALLOW_ABSENT:
            continue
        if not any(c in results for c in _candidates(value)):
            missing.append((name, rec["display"]))

    assert not missing, (
        "Numeric facts whose value is not found in results.md (dual-write drift, "
        "or add to ALLOW_ABSENT if derived by design):\n"
        + "\n".join(f"  {n} = {d}" for n, d in missing)
    )
