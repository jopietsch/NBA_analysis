"""Tests for nbakit.bbr — schedule parsing (no live network)."""

import math

from bs4 import BeautifulSoup

from nbakit.bbr import parse_schedule


_HTML = """
<table id="schedule"><tbody>
  <tr>
    <th data-stat="date_game">Sat, Apr 20, 2024</th>
    <td data-stat="visitor_team_name">Boston Celtics</td>
    <td data-stat="visitor_pts">110</td>
    <td data-stat="home_team_name">New York Knicks</td>
    <td data-stat="home_pts">120</td>
    <td data-stat="attendance">19,812</td>
  </tr>
  <tr class="thead"><td>header</td></tr>
  <tr>
    <th data-stat="date_game">Sun, Apr 21, 2024</th>
    <td data-stat="visitor_team_name">Miami Heat</td>
    <td data-stat="visitor_pts"></td>
    <td data-stat="home_team_name">Chicago Bulls</td>
    <td data-stat="home_pts"></td>
    <td data-stat="attendance"></td>
  </tr>
</tbody></table>
"""


def test_parse_schedule_extracts_played_games():
    rows = parse_schedule(BeautifulSoup(_HTML, "lxml"))
    assert len(rows) == 1  # the unplayed game is skipped
    g = rows[0]
    assert g["home_team"] == "New York Knicks"
    assert g["home_pts"] == 120
    assert g["away_pts"] == 110
    assert g["attendance"] == 19812.0
    assert g["home_win"] == 1


def test_parse_schedule_no_table():
    assert parse_schedule(BeautifulSoup("<html></html>", "lxml")) == []


def test_parse_schedule_blank_attendance_is_nan():
    html = _HTML.replace("19,812", "")
    rows = parse_schedule(BeautifulSoup(html, "lxml"))
    assert math.isnan(rows[0]["attendance"])
