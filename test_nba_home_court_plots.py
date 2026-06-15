"""
Smoke tests for the plotting layer (nba_home_court_plots.py).

These do NOT check pixels — image-comparison tests are brittle across font and
library versions. They feed each plot_* function minimal, well-formed synthetic
inputs and assert it runs to completion without raising. That catches the kind
of break a refactor causes (a renamed column/dict key the plot reads) in CI,
where the full pipeline can't run because cache/ is gitignored.

plot_attendance is intentionally omitted — that analysis is owned by another
agent and its signature is in flux.
"""

import matplotlib
matplotlib.use("Agg")  # no display; must precede any pyplot import

import matplotlib.pyplot as plt
import pytest

import nba_home_court_data as nba
import nba_home_court_plots as plots

SEASONS = [nba.short_label(y) for y in range(nba.START_YEAR, nba.END_YEAR + 1)]
N = len(SEASONS)
ERA_LABELS = [e[0] for e in nba.ERA_DEFS]
FORMAT_LABELS = [p[0] for p in nba.PLAYOFF_FORMAT_PERIODS]


def _series(n=N, base=2.0):
    """A deterministic per-season float series of length n."""
    return [base + 0.01 * i for i in range(n)]


@pytest.fixture(autouse=True)
def _isolate_output(tmp_path, monkeypatch):
    """Run each test in a temp dir so PNGs don't land in the repo, and close
    any figures left open."""
    monkeypatch.chdir(tmp_path)
    yield
    plt.close("all")


def test_plot_results():
    plots.plot_results(
        SEASONS, _series(base=58.0), SEASONS, _series(base=62.0),
        _series(6, 58.0), _series(6, 62.0), ERA_LABELS,
        _series(4, 58.0), _series(4, 62.0), FORMAT_LABELS,
    )


def test_plot_mediation():
    def _ctx():
        labels = ["Shooting", "Rebounding", "Fouls", "Turnovers"]
        return {
            "level": [{"chart_label": l, "pct": 20.0} for l in labels],
            "trend": [{"chart_label": l, "pct": 18.0} for l in labels],
            "level_unexplained": {"pct": 20.0},
            "trend_unmediated": {"pct": 28.0},
            "pct_level": 80.0,
            "pct_trend": 72.0,
        }
    plots.plot_mediation({"Regular season": _ctx(), "Playoffs": _ctx()})


def test_plot_differential_analysis():
    keys = ["foul_diff", "fg_pct_diff", "efg_pct_diff",
            "tpa_rate_diff", "fg3_pct_diff", "ft_pct_diff"]
    stats = {k: _series() for k in keys}
    plots.plot_differential_analysis(SEASONS, stats, SEASONS, dict(stats))


def test_plot_rebound_decomposition():
    keys = ["oreb_diff", "dreb_diff", "reb_diff",
            "reb_share_edge", "league_oreb_rate"]
    stats = {k: _series() for k in keys}
    stats["league_oreb_rate"] = _series(base=30.0)
    plots.plot_rebound_decomposition(SEASONS, stats, SEASONS, dict(stats))


def test_plot_margin_analysis():
    reg = {"all_games_mean": _series(base=3.0),
           "home_wins_mean": _series(base=11.0),
           "home_losses_mean": _series(base=-9.0)}
    po = {"all_games_mean": _series(base=2.5)}
    plots.plot_margin_analysis(SEASONS, reg, SEASONS, po)


def test_plot_parity_analysis():
    plots.plot_parity_analysis(SEASONS, _series(base=0.15), SEASONS, _series(base=58.0))


def test_plot_series_breakdown():
    game_nums = [1, 2, 3, 4, 5, 6, 7]
    pcts = [62.0, 64.0, 55.0, 57.0, 60.0, 58.0, 70.0]
    counts = [400, 400, 400, 380, 250, 180, 100]
    era_data = {lbl: {g: 55.0 + g for g in game_nums} for lbl in ERA_LABELS}
    plots.plot_series_breakdown(game_nums, pcts, counts, era_data, 60.0)


def test_plot_shot_zone_analysis():
    stats = {z: _series(base=1.0) for z in plots.SHOT_ZONE_LABELS}
    plots.plot_shot_zone_analysis(SEASONS, stats, SEASONS, dict(stats))


def test_plot_3pa_hca_analysis():
    plots.plot_3pa_hca_analysis(
        SEASONS, _series(base=0.25), _series(base=58.0),
        SEASONS, _series(base=0.27), _series(base=62.0),
    )


def test_plot_pace_hca_analysis():
    plots.plot_pace_hca_analysis(
        SEASONS, _series(base=95.0), _series(base=58.0),
        SEASONS, _series(base=92.0), _series(base=62.0),
    )


def _team_stats(teams, hca_base):
    return {
        t: {"hca": hca_base + i, "home_pct": 55.0 + i, "road_pct": 45.0 - i,
            "n_home": 1000, "n_road": 1000}
        for i, t in enumerate(teams)
    }


def test_plot_team_hca_analysis():
    teams = [f"Team {c}" for c in "ABCDEFGH"]
    plots.plot_team_hca_analysis(_team_stats(teams, 4.0), _team_stats(teams, 6.0))


def test_plot_referee_analysis():
    # sorted descending by mean_foul_diff (most positive first, most negative last)
    bias_stats = [
        {"name": f"Ref Number{i}", "mean_foul_diff": 1.0 - 0.2 * i,
         "era_means": {lbl: 0.5 - 0.1 * i for lbl in ERA_LABELS}}
        for i in range(10)
    ]
    plots.plot_referee_analysis(bias_stats)


def test_plot_referee_analysis_empty():
    plots.plot_referee_analysis([])  # must no-op, not raise
