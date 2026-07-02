"""Tests for nbakit.stats — shared statistical / box-score helpers."""

import numpy as np
import pandas as pd

from nbakit.stats import possessions


def test_possessions_formula():
    df = pd.DataFrame([{"FGA": 80, "OREB": 10, "TOV": 12, "FTA": 25}])
    # 80 - 10 + 12 + 0.44*25 = 93.0
    assert possessions(df).iloc[0] == 93.0


def test_possessions_matches_inline_expression():
    rng = np.random.default_rng(0)
    df = pd.DataFrame({
        "FGA":  rng.integers(70, 100, 50),
        "OREB": rng.integers(5, 15, 50),
        "TOV":  rng.integers(8, 20, 50),
        "FTA":  rng.integers(10, 40, 50),
    })
    inline = df["FGA"] - df["OREB"] + df["TOV"] + 0.44 * df["FTA"]
    pd.testing.assert_series_equal(possessions(df), inline)


def test_possessions_suffix():
    merged = pd.DataFrame([{
        "FGA_home": 90, "OREB_home": 8, "TOV_home": 11, "FTA_home": 20,
        "FGA_away": 85, "OREB_away": 12, "TOV_away": 14, "FTA_away": 30,
    }])
    # home: 90 - 8 + 11 + 0.44*20 = 101.8
    assert possessions(merged, suffix="_home").iloc[0] == 101.8
    # away: 85 - 12 + 14 + 0.44*30 = 100.2
    assert possessions(merged, suffix="_away").iloc[0] == 100.2
