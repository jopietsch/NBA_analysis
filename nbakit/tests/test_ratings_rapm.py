"""Tests for nbakit.ratings.rapm — RAPM recovery from synthetic possessions."""

import numpy as np
import pandas as pd
import pytest
from scipy.stats import spearmanr

from nbakit.ratings import rapm


# ── Helpers ────────────────────────────────────────────────────────────────────

def _simulate_possessions(
    n_players: int = 30,
    n_possessions: int = 6000,
    seed: int = 42,
) -> tuple[pd.DataFrame, np.ndarray, np.ndarray]:
    """Return (possessions_df, true_o_rapm, true_d_rapm) for recovery tests.

    True ratings are drawn from Normal(0, 3) (offensive) and Normal(0, 2)
    (defensive) in units of points per 100 possessions above average.

    Points on each possession:
        pts = (100 + sum(o_true[off]) - sum(d_true[def])) / 100 + noise
    where noise ~ Normal(0, 0.10) mimics within-possession variance.

    The design matches what rapm() expects: each possession has exactly 5
    offensive and 5 defensive player IDs drawn without replacement.
    """
    rng = np.random.default_rng(seed)
    player_ids = list(range(n_players))

    o_true = rng.normal(0.0, 3.0, size=n_players)
    d_true = rng.normal(0.0, 2.0, size=n_players)

    off_lists, def_lists, points = [], [], []
    for _ in range(n_possessions):
        chosen = rng.choice(player_ids, size=10, replace=False)
        off5 = chosen[:5].tolist()
        def5 = chosen[5:].tolist()

        # True expected pts per possession; noise models shot variance
        true_pts_per_100 = 100.0 + o_true[off5].sum() - d_true[def5].sum()
        noise = rng.normal(0.0, 10.0)  # ±10 pts/100 possession-level noise
        pts = (true_pts_per_100 + noise) / 100.0

        off_lists.append(off5)
        def_lists.append(def5)
        points.append(pts)

    df = pd.DataFrame({
        "off_player_ids": off_lists,
        "def_player_ids": def_lists,
        "points": points,
    })
    return df, o_true, d_true


# ── Recovery tests ─────────────────────────────────────────────────────────────

def test_rapm_output_shape_and_columns():
    """rapm() returns one row per player and the three expected columns."""
    df, _, _ = _simulate_possessions(n_players=20, n_possessions=1000)
    result = rapm(df, cv=3)

    assert isinstance(result, pd.DataFrame)
    assert list(result.columns) == ["RAPM", "O_RAPM", "D_RAPM"]
    assert result.index.name == "player_id"
    # All 20 players present
    assert set(result.index) == set(range(20))


def test_rapm_rapm_equals_o_plus_d():
    """RAPM = O_RAPM + D_RAPM for every player."""
    df, _, _ = _simulate_possessions(n_players=20, n_possessions=1000)
    result = rapm(df, cv=3)
    np.testing.assert_allclose(
        result["RAPM"].values,
        (result["O_RAPM"] + result["D_RAPM"]).values,
        atol=1e-10,
    )


def test_rapm_recovers_true_offensive_ratings():
    """O_RAPM rank order matches true offensive ratings with Spearman > 0.90."""
    df, o_true, _ = _simulate_possessions()
    result = rapm(df)
    result = result.sort_index()  # player_id 0..29

    rho, _ = spearmanr(result["O_RAPM"].values, o_true)
    assert rho > 0.90, f"O_RAPM Spearman = {rho:.3f}, expected > 0.90"


def test_rapm_recovers_true_defensive_ratings():
    """D_RAPM rank order matches true defensive ratings with Spearman > 0.90."""
    df, _, d_true = _simulate_possessions()
    result = rapm(df)
    result = result.sort_index()

    rho, _ = spearmanr(result["D_RAPM"].values, d_true)
    assert rho > 0.90, f"D_RAPM Spearman = {rho:.3f}, expected > 0.90"


def test_rapm_recovers_true_total_ratings():
    """Combined RAPM rank order matches true total ratings with Spearman > 0.90."""
    df, o_true, d_true = _simulate_possessions()
    result = rapm(df)
    result = result.sort_index()

    true_total = o_true + d_true
    rho, _ = spearmanr(result["RAPM"].values, true_total)
    assert rho > 0.90, f"RAPM Spearman = {rho:.3f}, expected > 0.90"


def test_rapm_recovers_scale_not_just_rank():
    """O_RAPM magnitude must track the true point-per-100 scale, not collapse.

    Guards the scale bug: an over-wide alpha grid drives cross-validation to a
    huge penalty that shrinks every rating toward zero, so rank order survives
    (the other tests pass) while the absolute scale is destroyed. With ample
    clean data the recovered spread should sit close to the true spread.
    """
    df, o_true, _ = _simulate_possessions(n_players=60, n_possessions=30000)
    result = rapm(df).sort_index()
    ratio = result["O_RAPM"].std() / o_true.std()
    assert 0.7 < ratio < 1.3, (
        f"O_RAPM scale ratio = {ratio:.3f}; expected near 1.0 "
        "(scale collapsed: check the alpha grid upper bound)"
    )


def test_rapm_scale_survives_weak_signal():
    """Even with a noisy, sparse panel the scale must not collapse to ~zero.

    The bounded alpha grid caps shrinkage so degenerate data yields a
    regularized (smaller) but still interpretable spread, never the near-zero
    output an unbounded grid produced on the real partial-season data.
    """
    df, o_true, _ = _simulate_possessions(n_players=150, n_possessions=6000, seed=3)
    result = rapm(df).sort_index()
    ratio = result["O_RAPM"].std() / o_true.std()
    assert ratio > 0.3, f"O_RAPM scale ratio = {ratio:.3f}; collapsed under weak signal"


# ── Format B: flat off1..off5 / def1..def5 columns ────────────────────────────

def test_rapm_flat_column_format():
    """rapm() accepts off1..off5 / def1..def5 flat columns."""
    df_list, o_true, _ = _simulate_possessions(n_players=20, n_possessions=1000)

    rows = []
    for _, row in df_list.iterrows():
        flat = {f"off{i+1}": row["off_player_ids"][i] for i in range(5)}
        flat.update({f"def{i+1}": row["def_player_ids"][i] for i in range(5)})
        flat["points"] = row["points"]
        rows.append(flat)
    df_flat = pd.DataFrame(rows)

    result = rapm(df_flat, cv=3)
    assert list(result.columns) == ["RAPM", "O_RAPM", "D_RAPM"]
    assert len(result) == 20


# ── Edge cases ─────────────────────────────────────────────────────────────────

def test_rapm_with_weight_column():
    """rapm() accepts an optional weight column without crashing."""
    df, _, _ = _simulate_possessions(n_players=20, n_possessions=500)
    df["weight"] = 1.0
    result = rapm(df, cv=3)
    assert len(result) == 20


def test_rapm_invalid_columns_raises():
    """rapm() raises ValueError when neither accepted column format is present."""
    df = pd.DataFrame({"x": [1, 2], "points": [1.0, 0.0]})
    with pytest.raises(ValueError, match="off_player_ids"):
        rapm(df)


# ── Prior-mean ridge tests ─────────────────────────────────────────────────────

def test_rapm_prior_zero_matches_no_prior():
    """A zero prior produces the same result as calling with no prior at all.

    This is the regression guard: the prior code path must not change output
    when prior_vector is all zeros.
    """
    df, _, _ = _simulate_possessions(n_players=20, n_possessions=1000, seed=11)

    result_baseline = rapm(df, cv=3)

    player_ids = list(result_baseline.index)
    zero_prior = pd.DataFrame(
        {"off": np.zeros(len(player_ids)), "def": np.zeros(len(player_ids))},
        index=pd.Index(player_ids, name="player_id"),
    )
    result_zero_prior = rapm(df, cv=3, prior=zero_prior)

    pd.testing.assert_frame_equal(result_baseline, result_zero_prior, atol=1e-10)


def test_rapm_prior_sparse_player_shrinks_to_prior():
    """A player with very few possessions ends up near his box-score prior.

    The sparse player (player_id == sparse_id) appears in only 2 possessions.
    With alpha=500 and 2 data points, regularization overwhelms the data and
    the estimate stays close to the prior (off=+5, def=+3). A data-rich player
    (player_id == 0, ~4000 appearances) given a deliberately wrong prior
    (off=-10) still recovers closer to his true rating than to -10.
    """
    rng = np.random.default_rng(7)
    n_reg = 20
    n_poss = 8000
    sparse_id = n_reg
    regular_ids = list(range(n_reg))

    o_true = rng.normal(0.0, 3.0, size=n_reg + 1)
    d_true = rng.normal(0.0, 2.0, size=n_reg + 1)

    off_lists, def_lists, pts_list = [], [], []

    # Many possessions for the 20 regular players
    for _ in range(n_poss):
        chosen = rng.choice(regular_ids, size=10, replace=False)
        off5 = chosen[:5].tolist()
        def5 = chosen[5:].tolist()
        true_pts = 100.0 + o_true[off5].sum() - d_true[def5].sum()
        pts = (true_pts + rng.normal(0.0, 10.0)) / 100.0
        off_lists.append(off5)
        def_lists.append(def5)
        pts_list.append(pts)

    # Only 2 possessions for the sparse player (on offense each time)
    for _ in range(2):
        chosen = rng.choice(regular_ids, size=9, replace=False)
        off5 = [sparse_id] + chosen[:4].tolist()
        def5 = chosen[4:9].tolist()
        true_pts = 100.0 + o_true[off5].sum() - d_true[def5].sum()
        pts = (true_pts + rng.normal(0.0, 10.0)) / 100.0
        off_lists.append(off5)
        def_lists.append(def5)
        pts_list.append(pts)

    df = pd.DataFrame({
        "off_player_ids": off_lists,
        "def_player_ids": def_lists,
        "points": pts_list,
    })

    # Sparse player prior: off=+5, def=+3 (distinctive signal to detect)
    # Rich player (id=0) prior: deliberately wrong at -10 for both
    prior = pd.DataFrame(
        {"off": [5.0, -10.0], "def": [3.0, -10.0]},
        index=pd.Index([sparse_id, 0], name="player_id"),
    )

    # Fixed alpha=500 so test is deterministic and shrinkage strength is known
    result = rapm(df, alphas=[500.0], cv=2, prior=prior)

    sparse_o = result.loc[sparse_id, "O_RAPM"]
    sparse_d = result.loc[sparse_id, "D_RAPM"]
    rich_o = result.loc[0, "O_RAPM"]
    true_o_rich = o_true[0]

    # Sparse player: 2 possessions vs. alpha=500 -> prior dominates
    assert abs(sparse_o - 5.0) < 1.5, (
        f"Sparse O_RAPM = {sparse_o:.3f}, expected near prior=5.0"
    )
    assert abs(sparse_d - 3.0) < 1.5, (
        f"Sparse D_RAPM = {sparse_d:.3f}, expected near prior=3.0"
    )

    # Rich player: ~4000 appearances vs. alpha=500 -> data dominates wrong prior
    assert abs(rich_o - true_o_rich) < abs(rich_o - (-10.0)), (
        f"Rich player O_RAPM = {rich_o:.3f}, true = {true_o_rich:.3f}, "
        f"wrong prior = -10. Data should dominate the prior."
    )


def test_rapm_prior_strength_pins_to_prior():
    """A large prior_strength collapses every rating onto its box-score prior.

    prior_strength adds pseudo-observations pulling each coefficient toward the
    prior; a very large strength overwhelms the possession data so the output
    equals the prior regardless of what the lineups did. This is the mechanism
    that makes moderate-minute players (which a single CV ridge penalty
    under-shrinks) collapse onto their box score.
    """
    df, _, _ = _simulate_possessions(n_players=20, n_possessions=4000, seed=5)
    rng = np.random.default_rng(1)
    prior = pd.DataFrame(
        {"off": rng.normal(0.0, 4.0, 20), "def": rng.normal(0.0, 3.0, 20)},
        index=pd.Index(range(20), name="player_id"),
    )
    result = rapm(df, alphas=[100.0], cv=2, prior=prior,
                  prior_strength=1e7).sort_index()
    np.testing.assert_allclose(result["O_RAPM"].values, prior["off"].values, atol=0.2)
    np.testing.assert_allclose(result["D_RAPM"].values, prior["def"].values, atol=0.2)


def test_rapm_prior_strength_zero_is_backward_compatible():
    """prior_strength=0 (default) keeps the original prior-mean-shift behavior."""
    df, _, _ = _simulate_possessions(n_players=20, n_possessions=1500, seed=9)
    prior = pd.DataFrame(
        {"off": np.linspace(-3, 3, 20), "def": np.linspace(-2, 2, 20)},
        index=pd.Index(range(20), name="player_id"),
    )
    a = rapm(df, alphas=[300.0], cv=2, prior=prior)
    b = rapm(df, alphas=[300.0], cv=2, prior=prior, prior_strength=0.0)
    pd.testing.assert_frame_equal(a, b, atol=1e-10)
