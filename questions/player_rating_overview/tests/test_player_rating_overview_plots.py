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


def test_plot_distribution_shape(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    df = _mini_ratings(n=60, tmp_path=tmp_path)
    df["RAPM"] = np.random.default_rng(7).normal(0, 3, len(df))
    path = plots.plot_distribution_shape(df)
    assert os.path.exists(path)


def test_plot_distribution_shape_missing_rate_system(tmp_path):
    # No RAPM column: the rate panel falls back to a "no data" message, no raise.
    plots.OUTPUT_DIR = str(tmp_path)
    df = _mini_ratings(n=30, tmp_path=tmp_path)
    path = plots.plot_distribution_shape(df)
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


def _mini_comp():
    rng = np.random.default_rng(7)
    n = 40
    a = rng.normal(0, 1, n)
    movers = pd.DataFrame({
        "player_id": range(1, n + 1),
        "PLAYER_NAME": [f"Player {i}" for i in range(1, n + 1)],
        "a": a,
        "b": a + rng.normal(0, 0.5, n),
    })
    movers["delta"] = movers["b"] - movers["a"]
    return {"label_a": "2024-25", "label_b": "2025-26",
            "movers": movers.sort_values("delta").reset_index(drop=True)}


def test_plot_season_comparison(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    path = plots.plot_season_comparison(_mini_comp(), top_n=6)
    assert os.path.exists(path)


def test_plot_season_comparison_empty(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    path = plots.plot_season_comparison({})
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


def test_plot_next_season_retrodiction(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    # Both sides carry ONLY cv_r2: the forecast bars must read the leave-one-
    # team-out CV number, same as the describe bars (apples-to-apples). Omitting
    # the in-sample "r2" key pins this — code that reads r2 raises a KeyError.
    same = {"PER": {"cv_r2": 0.72}, "BPM": {"cv_r2": 0.62}, "WS": {"cv_r2": 0.46}}
    nxt = {"BPM": {"cv_r2": 0.50}, "PER": {"cv_r2": 0.15}, "WS": {"cv_r2": 0.40}}
    path = plots.plot_next_season_retrodiction(same, nxt)
    assert os.path.exists(path)


def test_plot_next_season_retrodiction_empty(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    path = plots.plot_next_season_retrodiction({}, {})
    assert os.path.exists(path)


def test_plot_panel_describe_vs_forecast(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    panel = {
        "describe": {"PER": [0.70, 0.74, 0.69], "BPM": [0.60, 0.63, 0.61],
                     "WS": [0.50, 0.47, 0.52]},
        "forecast": {"PER": [0.16, 0.14, 0.18], "BPM": [0.49, 0.52, 0.50],
                     "WS": [0.40, 0.38, 0.41]},
        "seasons": [2021, 2022, 2023, 2024],
        "pairs": [(2021, 2022), (2022, 2023), (2023, 2024)],
    }
    path = plots.plot_panel_describe_vs_forecast(panel)
    assert os.path.exists(path)


def test_plot_panel_describe_vs_forecast_empty(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    path = plots.plot_panel_describe_vs_forecast(
        {"describe": {}, "forecast": {}, "seasons": [], "pairs": []})
    assert os.path.exists(path)


def test_plot_rating_stability(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    stab = {
        "corr": {"Game Score": [0.85, 0.83, 0.86], "PER": [0.80, 0.78, 0.82],
                 "BPM": [0.70, 0.68, 0.72]},
        "retention": {"Game Score": [0.68, 0.70, 0.66], "PER": [0.64, 0.62, 0.66],
                      "BPM": [0.50, 0.48, 0.52]},
        "pairs": [(2021, 2022), (2022, 2023), (2023, 2024)],
    }
    path = plots.plot_rating_stability(stab, top_n=20, chance=0.05)
    assert os.path.exists(path)


def test_plot_rating_stability_empty(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    path = plots.plot_rating_stability({"corr": {}, "retention": {}, "pairs": []})
    assert os.path.exists(path)


def _mini_pwv_deltas(n: int = 24) -> pd.DataFrame:
    rng = np.random.default_rng(11)
    return pd.DataFrame({
        "PLAYER_ID": range(1, n + 1),
        "PLAYER_NAME": [f"Player {i}" for i in range(1, n + 1)],
        "BPM_reg": rng.normal(0, 3, n),
        "BPM_po": rng.normal(0, 3, n),
        "MIN_reg": rng.uniform(800, 2800, n),
        "MIN_po": rng.uniform(150, 800, n),
    })


def test_plot_playoff_weighted_value(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    path = plots.plot_playoff_weighted_value(_mini_pwv_deltas(), top_n=8)
    assert os.path.exists(path)


def test_plot_playoff_weighted_value_empty(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    path = plots.plot_playoff_weighted_value(pd.DataFrame())
    assert os.path.exists(path)


def _mini_rapm_reliability() -> dict:
    return {
        "by_bin": [
            {"lo": 0, "hi": 500, "n": 80, "r": 0.08},
            {"lo": 500, "hi": 1000, "n": 60, "r": 0.11},
            {"lo": 1000, "hi": 1500, "n": 50, "r": 0.09},
            {"lo": 1500, "hi": 2000, "n": 40, "r": 0.12},
            {"lo": 2000, "hi": 3500, "n": 30, "r": 0.10},
        ],
        "splithalf": 0.10,
        "min_minutes": 1000,
        "n_splithalf": 120,
        "yoy": {"RAPM": 0.10, "RAPM_MY": 0.75, "BPM": 0.79},
    }


def test_plot_rapm_reliability(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    path = plots.plot_rapm_reliability(_mini_rapm_reliability())
    assert os.path.exists(path)


def test_plot_rapm_reliability_empty(tmp_path):
    plots.OUTPUT_DIR = str(tmp_path)
    path = plots.plot_rapm_reliability({})
    assert os.path.exists(path)
