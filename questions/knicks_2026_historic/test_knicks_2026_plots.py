"""
Smoke tests for the plotting layer (knicks_2026_plots).

Each plot_* gets a no-raise test: feed it synthetic inputs and assert it runs
without error. No pixel/image comparison (brittle across font and library versions).
"""

import os
import pytest
import numpy as np
import pandas as pd

import knicks_2026_plots as plots
from knicks_2026_data import SUBJECT_YEAR


# ── Synthetic minimal data ────────────────────────────────────────────────────

KNICKS_ID = 1610612752
OPP1_ID   = 2
OPP2_ID   = 3


def _mini_champions() -> pd.DataFrame:
    years = list(range(2020, 2026)) + [SUBJECT_YEAR]
    rows = []
    for y in years:
        rows.append({
            "year": y, "champion_id": KNICKS_ID if y == SUBJECT_YEAR else 1,
            "wins": 16, "losses": 3, "win_rate": 0.842,
            "avg_margin": 14.9, "avg_opp_srs": 3.54,
            "adj_margin": 11.35, "clutch_rate": 0.316,
            "home_wr": 0.9, "away_wr": 0.9,
        })
    return pd.DataFrame(rows)


def _mini_gap() -> pd.DataFrame:
    return pd.DataFrame([
        {"year": y, "east_srs": -0.3, "west_srs": 0.3,
         "srs_gap": 0.6, "east_h2h_wr": 0.48}
        for y in range(2020, 2027)
    ])


def _mini_reg_srs() -> pd.Series:
    return pd.Series({KNICKS_ID: 5.0, OPP1_ID: -3.0, OPP2_ID: 2.0}, name="SRS")


def _mini_standings() -> pd.DataFrame:
    return pd.DataFrame([
        {"TeamID": KNICKS_ID, "TeamAbbreviation": "NYK",
         "TeamCity": "New York", "TeamName": "Knicks", "Conference": "East"},
        {"TeamID": OPP1_ID, "TeamAbbreviation": "BOS",
         "TeamCity": "Boston", "TeamName": "Celtics", "Conference": "East"},
        {"TeamID": OPP2_ID, "TeamAbbreviation": "GSW",
         "TeamCity": "Golden State", "TeamName": "Warriors", "Conference": "West"},
    ])


def _mini_po_2026() -> pd.DataFrame:
    """Two playoff games: Knicks beat OPP1 in G1, beat OPP2 in G2."""
    rows = []
    for gid, opp_id, date in [("G001", OPP1_ID, "2026-04-20"),
                               ("G002", OPP2_ID, "2026-05-01")]:
        rows.append({
            "GAME_ID": gid, "TEAM_ID": KNICKS_ID, "GAME_DATE": date,
            "WL": "W", "PTS": 120, "PLUS_MINUS": 15.0, "MATCHUP": "NYK @ BOS",
        })
        rows.append({
            "GAME_ID": gid, "TEAM_ID": opp_id, "GAME_DATE": date,
            "WL": "L", "PTS": 105, "PLUS_MINUS": -15.0, "MATCHUP": "BOS vs. NYK",
        })
    return pd.DataFrame(rows)


# ── Tests ─────────────────────────────────────────────────────────────────────

def test_module_imports():
    """The plots module imports cleanly (Agg backend, no display required)."""
    assert plots is not None


def test_plot_win_rate_ranking(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_win_rate_ranking(_mini_champions())
    assert os.path.isfile(path)


def test_plot_margin_ranking(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_margin_ranking(_mini_champions())
    assert os.path.isfile(path)


def test_plot_conference_gap(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_conference_gap(_mini_gap())
    assert os.path.isfile(path)


def test_plot_team_srs_2026(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_team_srs_2026(_mini_reg_srs(), _mini_standings())
    assert os.path.isfile(path)


def test_plot_opponent_srs_ranking(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_opponent_srs_ranking(_mini_champions())
    assert os.path.isfile(path)


def test_plot_adjusted_margin_ranking(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_adjusted_margin_ranking(_mini_champions())
    assert os.path.isfile(path)


def test_plot_game_margin_distribution(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_game_margin_distribution(_mini_po_2026())
    assert os.path.isfile(path)


def test_plot_opponent_srs_by_round(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_opponent_srs_by_round(
        _mini_po_2026(), _mini_reg_srs(), _mini_standings()
    )
    assert os.path.isfile(path)
