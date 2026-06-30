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


def _mini_reg_logs() -> pd.DataFrame:
    rows = []
    for gid in ["R001", "R002"]:
        rows.append({"GAME_ID": gid, "TEAM_ID": KNICKS_ID,
                     "WL": "W", "PTS": 110, "PLUS_MINUS": 8.0,
                     "MATCHUP": "NYK vs. BOS"})
        rows.append({"GAME_ID": gid, "TEAM_ID": OPP1_ID,
                     "WL": "L", "PTS": 102, "PLUS_MINUS": -8.0,
                     "MATCHUP": "BOS @ NYK"})
        rows.append({"GAME_ID": gid + "b", "TEAM_ID": OPP2_ID,
                     "WL": "W", "PTS": 108, "PLUS_MINUS": 3.0,
                     "MATCHUP": "GSW vs. BOS"})
        rows.append({"GAME_ID": gid + "b", "TEAM_ID": OPP1_ID,
                     "WL": "L", "PTS": 105, "PLUS_MINUS": -3.0,
                     "MATCHUP": "BOS @ GSW"})
    return pd.DataFrame(rows)


def test_plot_playoff_field_elevation(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_playoff_field_elevation(
        _mini_po_2026(), _mini_reg_logs(), _mini_standings()
    )
    assert os.path.exists(path)


def test_plot_title_run_rarity(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_title_run_rarity(
        _mini_po_2026(), _mini_reg_logs(), _mini_standings()
    )
    assert os.path.exists(path)


def _mini_alt_table(adj_subject: float) -> pd.DataFrame:
    years = list(range(2020, 2026)) + [SUBJECT_YEAR]
    rows = []
    for i, y in enumerate(years):
        adj = adj_subject if y == SUBJECT_YEAR else 3.0 + i * 0.5
        rows.append({"year": y, "champion_id": 1, "avg_margin": 12.0,
                     "avg_opp_rating": 3.0, "adj_margin": adj})
    return pd.DataFrame(rows)


def test_plot_rating_systems(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_rating_systems(
        _mini_champions(), _mini_alt_table(11.0), _mini_alt_table(9.4),
        _mini_alt_table(11.9)
    )
    assert os.path.exists(path)


def test_plot_bootstrap_margin(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_bootstrap_margin(
        _mini_po_2026(), _mini_reg_srs(), _mini_champions()
    )
    assert os.path.isfile(path)


def _mini_posterior_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"year": SUBJECT_YEAR, "adj_mean": 11.2, "post_mean": 4.7, "post_sd": 1.8},
        {"year": 1991, "adj_mean": 9.2, "post_mean": 5.3, "post_sd": 1.6},
        {"year": 2017, "adj_mean": 10.2, "post_mean": 5.1, "post_sd": 1.7},
        {"year": 2001, "adj_mean": 7.3, "post_mean": 4.7, "post_sd": 1.5},
    ]).sort_values("post_mean", ascending=False).reset_index(drop=True)


def test_plot_hierarchical_posterior(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_hierarchical_posterior(_mini_posterior_df(), p_rank1=0.09)
    assert os.path.isfile(path)


def test_plot_hierarchical_posterior_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    assert plots.plot_hierarchical_posterior(pd.DataFrame(), p_rank1=0.1) == ""


def _mini_series_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"opp_id": OPP1_ID, "n_games": 4, "raw_margin": 20.0,
         "opp_reg_srs": 2.0, "reg_adj_margin": 18.0,
         "opp_playoff_srs": 1.0, "playoff_adj_margin": 19.0},
        {"opp_id": OPP2_ID, "n_games": 5, "raw_margin": 3.0,
         "opp_reg_srs": 8.0, "reg_adj_margin": -5.0,
         "opp_playoff_srs": 9.0, "playoff_adj_margin": -6.0},
    ])


def test_plot_round_split(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_round_split(_mini_series_df())
    assert os.path.isfile(path)


def test_plot_round_split_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    result = plots.plot_round_split(pd.DataFrame())
    assert result == ""


def _mini_health_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"team_id": OPP1_ID, "team_name": "Boston Celtics",
         "games_in_series": 4, "total_core": 8,
         "avg_core_per_game": 8.0, "missing_core_avg": 0.0,
         "health_score": 1.0, "first_game_date": "2026-04-20"},
        {"team_id": OPP2_ID, "team_name": "Golden State Warriors",
         "games_in_series": 5, "total_core": 8,
         "avg_core_per_game": 6.5, "missing_core_avg": 1.5,
         "health_score": 0.81, "first_game_date": "2026-05-01"},
    ])


def test_plot_opponent_health(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_opponent_health(_mini_health_df())
    assert os.path.isfile(path)


def test_plot_opponent_health_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    result = plots.plot_opponent_health(pd.DataFrame())
    assert result == ""


def _mini_ats_df() -> pd.DataFrame:
    return pd.DataFrame([
        {"GAME_ID": "G001", "GAME_DATE": "2026-04-20", "WL": "W",
         "actual_margin": 15.0, "knicks_spread": -8.0, "ats_margin": 23.0,
         "covered": True, "OPP_ID": OPP1_ID},
        {"GAME_ID": "G002", "GAME_DATE": "2026-05-01", "WL": "W",
         "actual_margin": 10.0, "knicks_spread": 3.0, "ats_margin": 7.0,
         "covered": True, "OPP_ID": OPP2_ID},
    ])


def test_plot_market_vs_actual(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    path = plots.plot_market_vs_actual(_mini_ats_df())
    assert os.path.isfile(path)


def test_plot_market_vs_actual_empty(tmp_path, monkeypatch):
    monkeypatch.setattr(plots, "OUTPUT_DIR", str(tmp_path))
    result = plots.plot_market_vs_actual(pd.DataFrame())
    assert result == ""
