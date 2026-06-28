"""Facts for player_ranking_overview: the single source for every cited number.

The Fact/Facts model lives in ``nbakit.facts`` (shared across projects). This
module is the per-project shim: it re-exports that model and pins the paths the
pipeline dumps to. The analysis writes into ``FACTS`` next to each ``print()``,
then calls ``FACTS.dump(_FACTS_PATH)`` / ``FACTS.dump_guards(_GUARDS_PATH)``.

PENDING-REGEN CAVEAT: These facts are registered against the current 8-system
run (GAME_SCORE, PER, WS, WS48, BPM, OBPM, DBPM, VORP). When the third-party
systems (DARKO, EPM, LEBRON, RAPTOR, ESPN_RPM) are added, facts.json must be
regenerated and every .md.j2 template citing correlation pairs or top-20 lists
must be re-reviewed: the 28 correlation pairs will expand to ~45, and the top-20
consensus/wins-predictive lists will reorder.
"""
from nbakit.facts import Fact, Facts, load_displays, load_guards  # noqa: F401

# Module-level singleton the analysis writes into across all run_* functions.
FACTS = Facts()

_FACTS_PATH = "docs/player_ranking_overview_facts.json"
_GUARDS_PATH = "docs/player_ranking_overview_guards.json"
