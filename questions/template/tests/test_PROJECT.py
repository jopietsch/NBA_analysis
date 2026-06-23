"""
Unit tests for the data/computation layer (PROJECT_data).

Correctness tests over synthetic DataFrames. As compute_* functions are added,
test them here against hand-built frames with known answers — never against live
API calls.
"""

import pandas as pd
import pytest
import PROJECT_data as data


# ── Synthetic minimal data ────────────────────────────────────────────────────

def _mini_frame() -> pd.DataFrame:
    """TODO: return a minimal synthetic DataFrame matching the real schema."""
    return pd.DataFrame([
        {"col_a": 1, "col_b": "value"},
    ])


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_placeholder():
    """Replace with real tests as compute_* functions are added."""
    df = _mini_frame()
    assert len(df) == 1
