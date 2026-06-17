"""Tests for nbakit.teams — franchise reference data and haversine."""

import pytest

from nbakit.teams import ALTITUDE_TEAMS, TEAM_TIMEZONES, ARENA_COORDS, haversine


def test_haversine_boston_to_la():
    # TD Garden -> Crypto.com Arena is ~2600 miles
    dist = haversine(42.366, -71.062, 34.043, -118.267)
    assert 2500 < dist < 2700


def test_haversine_zero():
    assert haversine(0.0, 0.0, 0.0, 0.0) == pytest.approx(0.0, abs=1e-6)


def test_haversine_symmetric():
    d1 = haversine(42.366, -71.062, 34.043, -118.267)
    d2 = haversine(34.043, -118.267, 42.366, -71.062)
    assert d1 == pytest.approx(d2)


def test_altitude_teams_present():
    assert ALTITUDE_TEAMS["Denver Nuggets"] == 5280
    assert "Utah Jazz" in ALTITUDE_TEAMS


def test_reference_tables_share_team_names():
    # Every altitude team has a timezone and arena coordinate.
    for team in ALTITUDE_TEAMS:
        assert team in TEAM_TIMEZONES
        assert team in ARENA_COORDS
