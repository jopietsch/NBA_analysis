"""Facts for knicks_2026_historic: the single source for every cited number.

The Fact/Facts model lives in ``nbakit.facts`` (shared across projects). This
module is the per-project shim: it re-exports that model and pins the paths the
pipeline dumps to. The analysis writes into ``FACTS`` next to each ``print()``,
then calls ``FACTS.dump(_FACTS_PATH)`` / ``FACTS.dump_guards(_GUARDS_PATH)``.
"""
from nbakit.facts import Fact, Facts, load_displays, load_guards  # noqa: F401

# Module-level singleton the analysis writes into across all run_* functions.
FACTS = Facts()

_FACTS_PATH = "docs/knicks_2026_historic_facts.json"
_GUARDS_PATH = "docs/knicks_2026_historic_guards.json"
