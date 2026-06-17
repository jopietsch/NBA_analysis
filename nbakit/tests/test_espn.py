"""Tests for nbakit.espn — Vegas-line parsing (no live network)."""

from nbakit.espn import parse_vegas_line


def test_parse_vegas_line_favored():
    assert parse_vegas_line("NYK -7.5") == ("NYK", -7.5)
    assert parse_vegas_line("ATL -3") == ("ATL", -3.0)


def test_parse_vegas_line_pick():
    assert parse_vegas_line("Pick") == ("PICK", 0.0)
    assert parse_vegas_line("") == ("PICK", 0.0)
    assert parse_vegas_line("N/A") == ("PICK", 0.0)


def test_parse_vegas_line_unparseable():
    assert parse_vegas_line("garbage text ???") == (None, None)
