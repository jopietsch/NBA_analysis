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
