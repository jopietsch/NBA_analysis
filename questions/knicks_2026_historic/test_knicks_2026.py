"""
Unit tests for the data/computation layer (knicks_2026_data).

Correctness tests over synthetic DataFrames and the season/cache helpers. As
compute_* metrics are added, test them here against hand-built frames with known
answers — never against live API calls.
"""

import knicks_2026_data as data


def test_season_str():
    assert data.season_str(2026) == "2025-26"
    assert data.season_str(1984) == "1983-84"


def test_short_label():
    assert data.short_label(2026) == "25–26"
    assert data.short_label(1984) == "83–84"


def test_cache_path():
    assert data.cache_path(2026, "Playoffs").endswith("cache/2025-26_Playoffs.csv")
    # spaces in the season type become underscores in the filename
    assert "Regular_Season" in data.cache_path(2026, "Regular Season")
