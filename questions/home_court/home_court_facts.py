"""Facts for home_court: the single source for every cited number.

The Fact/Facts model lives in ``nbakit.facts`` (shared across projects). This
module is the per-project shim: it re-exports that model and owns the singleton
the analysis writes into. (home_court_analysis.py pins _FACTS_PATH/_GUARDS_PATH
locally.)
"""
from nbakit.facts import Fact, Facts, load_displays, load_guards  # noqa: F401

# Module-level singleton the analysis writes into across all run_* functions.
FACTS = Facts()
