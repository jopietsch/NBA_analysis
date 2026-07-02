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
#
# The old substring matcher "passed" all three of these via coincidental
# substrings elsewhere in the file (e.g. "70" inside "70.7%") — they were
# never actually printed by the pipeline.
ALLOW_ABSENT: set[str] = {
    # 70%: share of franchise HCA variance that is signal, computed for the
    # prose; results.md prints the underlying variance components only.
    "altitude.signal_pct",
    # 31%: away OREB conversion rate in the earliest tracked season, cited in
    # prose; results.md prints the league OREB-rate trajectory instead.
    "reb.oreb_away_early",
    # 55.3%: home-win% averaged over the last 5 seasons, a prose aggregate;
    # results.md prints per-season values only.
    "reg.hw_last",
}

# Documented fallback tier: the value is present, but only as a bare table
# cell / interval bound whose surrounding text shares no word with the fact's
# name or note. Value presence is still required; only the context requirement
# is waived. Keep minimal and reviewed.
ALLOW_NO_CONTEXT: set[str] = {
    # 2031: the final row of the state-space forecast fan tables; the
    # "Season  Forecast" header sits 6 lines above, outside the context window.
    "forecast.horizon_year",
    # Bare bounds inside the "Channels carry ... (95% CI [91, 97]%)" summary
    # lines; the line says "Channels", never "four factors".
    "share.fourfactors.adv_ci_lo",
    "share.fourfactors_po.adv_ci_lo",
}


def test_every_numeric_fact_appears_in_results():
    assert_facts_in_results(
        os.path.join(_DOCS, "home_court_facts.json"),
        os.path.join(_DOCS, "home_court_results.md"),
        allow_absent=ALLOW_ABSENT,
        allow_no_context=ALLOW_NO_CONTEXT,
    )
