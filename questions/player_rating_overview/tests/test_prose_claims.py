"""Fail if any qualitative prose claim no longer holds against the committed data.

Guards are recorded by the analysis (FACTS.guard) next to the numbers they rest
on and dumped to docs/player_rating_overview_guards.json by the pipeline. This
test reads that file so a claim like "the two ratings agree very closely" can't
silently go stale: if the underlying condition flips, the build turns red and
names the phrase to rewrite.
"""
import os

from player_rating_overview_facts import load_guards

GUARDS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "docs", "player_rating_overview_guards.json"
)


def test_all_prose_claims_hold():
    guards = load_guards(GUARDS_PATH)
    assert guards, "no guards recorded — run the pipeline to generate guards.json"
    failed = {n: g for n, g in guards.items() if not g["ok"]}
    assert not failed, "prose claims no longer hold:\n" + "\n".join(
        f'  {n}: "{g["claim"]}"  (now: {g["value"]})' for n, g in failed.items()
    )
