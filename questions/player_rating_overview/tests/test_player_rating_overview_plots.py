"""
Smoke tests for the plotting layer.

Each plot_* gets a no-raise test with synthetic data. No pixel/image comparison.
"""

import os
import numpy as np
import pandas as pd
import pytest
import matplotlib
matplotlib.use("Agg")

import player_rating_overview_plots as plots


# ── Synthetic data ────────────────────────────────────────────────────────────

def _mini_ratings(n: int = 30, tmp_path=None) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    df = pd.DataFrame({
        "PLAYER_ID": range(1, n + 1),
        "PLAYER_NAME": [f"Player {i}" for i in range(1, n + 1)],
        "TEAM_ID": rng.integers(1, 4, size=n),
        "MIN": rng.uniform(500, 3000, size=n),
        "GP": rng.integers(20, 82, size=n),
        "QUALIFIED": True,
        "PER": rng.normal(15, 5, n),
        "WS": rng.exponential(3, n),
        "WS48": rng.normal(0.1, 0.06, n),
        "BPM": rng.normal(0, 3, n),
        "OBPM": rng.normal(0, 2, n),
        "DBPM": rng.normal(0, 2, n),
        "VORP": rng.exponential(1.5, n),
        "GAME_SCORE": rng.normal(12, 4, n),
        "CONSENSUS": rng.normal(0, 1, n),
        "WINS_PRED": rng.normal(0, 1, n),
    })
    # Patch OUTPUT_DIR to tmp_path if provided
    if tmp_path:
        plots.OUTPUT_DIR = str(tmp_path)
    return df


# ── Smoke tests ───────────────────────────────────────────────────────────────

def test_plot_rank_agreement_heatmap(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    df = _mini_ratings(n=30, tmp_path=tmp_path)
    systems = ["PER", "WS", "BPM", "VORP", "GAME_SCORE"]
    path = plots.plot_rank_agreement_heatmap(df, systems)
    assert os.path.exists(path)


def test_plot_system_outliers(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    df = _mini_ratings(n=30, tmp_path=tmp_path)
    systems = ["PER", "WS", "BPM", "VORP"]
    path = plots.plot_system_outliers(df, systems)
    assert os.path.exists(path)


def test_plot_rank_value_distributions(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    df = _mini_ratings(n=30, tmp_path=tmp_path)
    systems = ["PER", "BPM", "WS", "VORP"]
    path = plots.plot_rank_value_distributions(df, systems)
    assert os.path.exists(path)


def test_plot_powerlaw_fits(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    df = _mini_ratings(n=30, tmp_path=tmp_path)
    systems = ["PER", "WS", "VORP", "GAME_SCORE"]
    path = plots.plot_powerlaw_fits(df, systems)
    assert os.path.exists(path)


def test_plot_powerlaw_small_multiples(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    df = _mini_ratings(n=30, tmp_path=tmp_path)
    systems = ["PER", "WS", "VORP", "GAME_SCORE", "BPM"]
    path = plots.plot_powerlaw_small_multiples(df, systems)
    assert os.path.exists(path)


def test_plot_ordinal_vs_value_gap(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    df = _mini_ratings(n=30, tmp_path=tmp_path)
    path = plots.plot_ordinal_vs_value_gap(df, metric="VORP")
    assert os.path.exists(path)


def test_plot_uber_rating_comparison(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    df = _mini_ratings(n=30, tmp_path=tmp_path)
    path = plots.plot_uber_rating_comparison(df)
    assert os.path.exists(path)


def test_plot_gini_by_system(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    gini_scores = {"PER": 0.22, "WS": 0.45, "BPM": 0.18, "VORP": 0.51}
    path = plots.plot_gini_by_system(gini_scores)
    assert os.path.exists(path)


def test_plot_unique_signal(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    unique_r2 = {"PER": 0.12, "WS": 0.08, "BPM": 0.31, "VORP": 0.05}
    path = plots.plot_unique_signal(unique_r2)
    assert os.path.exists(path)


def _mini_deltas(n: int = 24) -> pd.DataFrame:
    rng = np.random.default_rng(7)
    df = pd.DataFrame({
        "PLAYER_NAME": [f"Player {i}" for i in range(1, n + 1)],
        "TEAM_ABBREVIATION": rng.choice(["AAA", "BBB", "CCC"], size=n),
        "PER_delta_adj": rng.normal(0, 3, n),
        "SHIFT_Z": rng.normal(0, 1, n),
    })
    return df


def test_plot_playoff_shift(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    path = plots.plot_playoff_shift(_mini_deltas(), top_n=5)
    assert os.path.exists(path)


def test_plot_playoff_shift_empty(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    path = plots.plot_playoff_shift(pd.DataFrame())
    assert os.path.exists(path)


def test_plot_retrodiction(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    retro = {
        "PER": {"r2": 0.76, "cv_r2": 0.72, "n": 30},
        "BPM": {"r2": 0.67, "cv_r2": 0.62, "n": 30},
        "WS": {"r2": 0.53, "cv_r2": 0.46, "n": 30},
    }
    path = plots.plot_retrodiction(retro, outcome_calibrated={"BPM", "WS"})
    assert os.path.exists(path)


def test_plot_retrodiction_empty(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    path = plots.plot_retrodiction({}, outcome_calibrated=set())
    assert os.path.exists(path)
