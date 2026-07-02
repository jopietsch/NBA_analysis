"""Fail if any qualitative prose claim no longer holds against the committed data.

Thin wrapper around ``nbakit.facts.assert_guards_hold``. Guards are recorded by
the analysis (``FACTS.guard``) next to the numbers they rest on and dumped to
``docs/PROJECT_guards.json`` by the pipeline, so a claim like "the home
advantage vanished" can't silently go stale: if the underlying condition flips,
the build turns red and names the phrase to rewrite.

The committed guards.json ships with one placeholder guard (registered in
PROJECT_analysis.py) so this assertion is exercised from day one; replace it
with real FACTS.guard() calls as qualitative claims are written.
"""
import os

from nbakit.facts import assert_guards_hold

GUARDS_PATH = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "docs", "PROJECT_guards.json"
)


def test_all_prose_claims_hold():
    assert_guards_hold(GUARDS_PATH)
