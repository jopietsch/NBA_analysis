"""
Smoke tests for the plotting layer (PROJECT_plots).

Each plot_* gets a no-raise test: feed it synthetic inputs and assert it runs
without error. No pixel/image comparison (brittle across font and library versions).
"""

import os
import pytest
import pandas as pd
import matplotlib
matplotlib.use("Agg")

import PROJECT_plots as plots


# ── Synthetic minimal data ────────────────────────────────────────────────────

def _mini_frame() -> pd.DataFrame:
    """TODO: return a minimal synthetic DataFrame matching what plot_* expects."""
    return pd.DataFrame([
        {"col_a": 1, "col_b": "value"},
    ])


# ── Smoke tests ───────────────────────────────────────────────────────────────

def test_plot_placeholder(tmp_path):
    """Replace with a real smoke test for each plot_* function."""
    pass
