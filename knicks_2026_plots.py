"""
knicks_2026_plots.py — visualization for the 2026 Knicks playoff analysis.

Imports the data module; holds no data logic of its own. Each plot_* function
takes already-computed frames/values, draws one figure, and saves a
``knicks_2026_*.png``. main() in knicks_2026_historic.py wires the calls.

Run the pipeline with MPLBACKEND=Agg to render PNGs without opening windows.

TBD — add plot_* functions as the analysis takes shape (see CLAUDE.md "Adding a
new analysis"). Each gets a no-raise smoke test in test_knicks_2026_plots.py.
"""

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt   # noqa: E402

import knicks_2026_data as data   # noqa: E402,F401
