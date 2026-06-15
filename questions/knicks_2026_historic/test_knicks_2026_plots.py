"""
Smoke tests for the plotting layer (knicks_2026_plots).

Plots are not correctness-tested (no pixel/image comparison — brittle across
font and library versions). Each plot_* gets a no-raise test here: feed it
synthetic inputs and assert it runs. Add one per plot as plots are added.
"""

import knicks_2026_plots  # noqa: F401  — import must not raise


def test_module_imports():
    """The plots module imports cleanly (Agg backend, no display required)."""
    assert knicks_2026_plots is not None
