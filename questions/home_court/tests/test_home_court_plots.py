"""
Smoke tests for the plotting layer (home_court_plots.py).

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

import home_court_data as nba
import home_court_plots as plots

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
    decomp = {"Regular season": _ctx(), "Playoffs": _ctx()}
    plots.plot_mediation(decomp)  # no bootstrap (back-compat path)
    boot = {
        c: {"pct_level_ci": (74.0, 86.0), "pct_trend_ci": (60.0, 84.0)}
        for c in ("Regular season", "Playoffs")
    }
    plots.plot_mediation(decomp, boot)


def test_plot_differential_analysis():
    keys = ["fta_diff", "fg_pct_diff", "efg_pct_diff",
            "tpa_rate_diff", "fg3_pct_diff", "ft_pct_diff"]
    stats = {k: _series() for k in keys}
    plots.plot_differential_analysis(SEASONS, stats, SEASONS, dict(stats))


def test_plot_rebound_decomposition():
    keys = ["oreb_diff", "dreb_diff", "reb_diff",
            "reb_share_edge", "league_oreb_rate",
            "oreb_rate_home", "oreb_rate_away"]
    stats = {k: _series() for k in keys}
    stats["oreb_diff"]      = _series(base=0.4)
    stats["dreb_diff"]      = _series(base=1.2)
    stats["reb_diff"]       = _series(base=1.6)
    stats["oreb_rate_home"] = _series(base=28.0)
    stats["oreb_rate_away"] = _series(base=26.0)
    win_pcts = [59.0 + i * 0.3 for i in range(len(SEASONS))]
    plots.plot_rebound_decomposition(SEASONS, stats, SEASONS, dict(stats),
                                     win_seasons=SEASONS, win_pcts=win_pcts)


def test_plot_back_to_back():
    data = {"eras": ERA_LABELS, "vis_b2b": [35.0, 34.6, 34.0, 32.7, 21.0, 18.8],
            "total": -9.29, "freq_comp": -0.71, "rate_comp": -8.59,
            "freq_share": 7.6, "rate_share": 92.5}
    plots.plot_back_to_back(data)


def test_plot_playoff_quality():
    data = {"pp_raw": -0.225, "pp_adj": -0.229, "retained": 102.0,
            "seed_bars": [("Higher seed\nhosts (G1–2)", 70.6, 1021),
                          ("Lower seed\nhosts (G3–4)", 55.1, 1010),
                          ("Weaker team\nhosts (G3–4)", 51.5, 827)]}
    plots.plot_playoff_quality(data)


def test_plot_channel_3pa_control():
    def _ctx(n):
        # (label, surviving%, p_ctrl, win_raw, win_ctrl) — one row crosses zero
        chans = [("Shooting", -110.0, 0.03, -0.52, 0.57),
                 ("Turnovers", 46.0, 0.04, -0.65, -0.30),
                 ("Fouls", 49.0, 0.01, -0.44, -0.21),
                 ("Rebounding", 92.0, 0.001, -0.74, -0.68)]
        return {"n": n, "channels": [
            {"chart_label": c, "g_raw": -0.02, "g_ctrl": -0.01,
             "surviving": s, "absorbed": 100 - s, "win_raw": wr, "win_ctrl": wc,
             "p_raw": 0.001, "p_ctrl": p}
            for c, s, p, wr, wc in chans]}
    plots.plot_channel_3pa_control({"Regular season": _ctx(49000), "Playoffs": _ctx(3300)})


def test_plot_team_decline_slopes():
    rng = [(-0.55 + 0.03 * i, 0.18) for i in range(12)]
    data = {
        "league_slope": -0.49, "league_se": 0.026, "league_p": 0.0,
        "obs_sd": 0.32, "true_sd": 0.0, "noise_share": 1.0,
        "n_modeled": 12, "n_teams": 12, "panel_rows": 1200,
        "teams": [
            {"team": f"Team {c}", "slope": s, "se": se, "shrunk": -0.49, "n": 30}
            for c, (s, se) in zip("ABCDEFGHIJKL", rng)
        ],
    }
    plots.plot_team_decline_slopes(data)


def test_plot_team_decline_slopes_empty():
    plots.plot_team_decline_slopes({"teams": []})  # must no-op, not raise


def test_plot_oos_forecast():
    def _ctx(off):
        rows = [(2014 + i, 58.0 - 0.3 * i + off, 58.2 - 0.3 * i + off,
                 58.1 - 0.2 * i + off) for i in range(12)]
        return {
            "is_playoff": 0, "cut_year": 2014,
            "train_years": (1984, 2013), "test_years": (2014, 2025),
            "rows": rows,
            "actual_full": [(1984 + i, 64.0 - 0.2 * i + off) for i in range(42)],
            "rmse_channel": 0.9, "rmse_trend": 1.4, "rmse_naive": 5.5,
            "train_mean": 61.0,
        }
    plots.plot_oos_forecast({"reg": _ctx(0.0), "po": _ctx(4.0)})


def test_plot_oos_forecast_empty():
    plots.plot_oos_forecast({"reg": {}, "po": {}})  # must no-op, not raise


def test_plot_rest_altitude():
    def _ctx(base):
        return {
            "rest": {
                "baseline": base,
                "buckets": {
                    "Away more rested": (base - 2.0, 5000),
                    "Equal rest":       (base, 12000),
                    "Home more rested": (base + 3.0, 8000),
                },
            },
            "altitude": {
                "League":         (base, 25000),
                "Denver Nuggets": (base + 5.0, 1700),
                "Utah Jazz":      (base + 9.0, 1700),
            },
        }
    data = {"rest": {"reg": _ctx(60.0)["rest"], "po": _ctx(64.0)["rest"]},
            "altitude": {"reg": _ctx(60.0)["altitude"], "po": _ctx(64.0)["altitude"]}}
    plots.plot_rest_altitude(data)


def test_plot_tracking_rebounding():
    track_seasons = [nba.short_label(y) for y in range(2014, nba.END_YEAR + 1)]
    n = len(track_seasons)
    stats = {
        "oreb_chance_pct_edge": [0.7 - 0.02 * i for i in range(n)],
        "boxout_edge":          [0.0 for _ in range(n)],
        "second_chance_edge":   [0.3 - 0.01 * i for i in range(n)],
    }
    plots.plot_tracking_rebounding(track_seasons, stats)


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


def test_plot_series_simulation():
    n = len(ERA_LABELS)
    data = {
        "era_labels": ERA_LABELS,
        "reg_pgame":  [65.0 - i for i in range(n)],
        "po_pgame":   [67.0 - i for i in range(n)],
        "reg_series": [55.0 - 0.5 * i for i in range(n)],
        "po_series":  [56.0 - 0.5 * i for i in range(n)],
        "curve_pgame":  [50.0 + i for i in range(21)],
        "curve_series": [50.0 + 0.4 * i for i in range(21)],
        "pattern": [1, 1, 0, 0, 1, 0, 1],
        "n_sims": 1000,
    }
    plots.plot_series_simulation(data)


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


def test_plot_team_season_hca():
    teams = [f"Team {c}" for c in "ABCDEFGH"]
    stats = _team_stats(teams, 4.0)
    stats["Team A"] = {"hca": -3.0, "home_pct": 42.0, "road_pct": 45.0,
                       "n_home": 41, "n_road": 41}  # one team below road, red segment
    plots.plot_team_season_hca(stats, nba.END_YEAR)


def _referee_bias_stats(n=10):
    return [
        {"name": f"Ref Number{i}", "mean_foul_diff": 1.0 - 0.2 * i,
         "era_means": {lbl: 0.5 - 0.1 * i for lbl in ERA_LABELS}}
        for i in range(n)
    ]


def test_plot_referee_era_distribution():
    plots.plot_referee_era_distribution(_referee_bias_stats())


def test_plot_referee_era_distribution_empty():
    plots.plot_referee_era_distribution([])  # must no-op, not raise


def test_plot_referee_rankings():
    plots.plot_referee_rankings(_referee_bias_stats())


def test_plot_referee_rankings_empty():
    plots.plot_referee_rankings([])  # must no-op, not raise
