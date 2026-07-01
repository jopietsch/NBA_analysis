"""Tests for per-game cache sharding: the nbakit.data game_cache_* helpers and
the tools/shard_cache.py reorg. All against pytest tmp_path, never the real cache.
"""
import os
import sys

import pandas as pd
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from nbakit.data import (  # noqa: E402
    season_of_game_id, game_cache_path, game_cache_exists,
    game_cache_read_csv, game_cache_write_csv, cache_write_csv,
)
from tools import shard_cache  # noqa: E402

GID = "0020500123"   # 2005-06
GID2 = "0029600007"  # 1996-97


def test_season_of_game_id():
    assert season_of_game_id("0020500123") == "2005-06"
    assert season_of_game_id("0029600001") == "1996-97"
    assert season_of_game_id("0021200999") == "2012-13"
    assert season_of_game_id("0020000001") == "2000-01"
    assert season_of_game_id(20500123) == "2005-06"          # int input
    assert season_of_game_id("0040500101") == "2005-06"      # playoff prefix (4)


def test_game_cache_write_read_sharded(tmp_path):
    d = str(tmp_path)
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    written = game_cache_write_csv(df, d, "pbp_v3", GID)
    assert written.endswith(os.path.join("pbp_v3", "2005-06", "0020500123.csv.zst"))
    assert os.path.exists(written)
    assert game_cache_exists(d, "pbp_v3", GID)
    pd.testing.assert_frame_equal(game_cache_read_csv(d, "pbp_v3", GID), df)


def test_game_cache_flat_fallback(tmp_path):
    d = str(tmp_path)
    df = pd.DataFrame({"x": [9]})
    # write a LEGACY flat file directly, no sharded version
    cache_write_csv(df, game_cache_path(d, "boxscore_trad", GID2, sharded=False))
    assert not os.path.exists(game_cache_path(d, "boxscore_trad", GID2) + ".zst")
    assert game_cache_exists(d, "boxscore_trad", GID2)        # found via flat
    pd.testing.assert_frame_equal(game_cache_read_csv(d, "boxscore_trad", GID2), df)


def test_game_cache_empty_marker_roundtrips(tmp_path):
    d = str(tmp_path)
    game_cache_write_csv(pd.DataFrame(), d, "pbp_v3", GID)
    assert game_cache_exists(d, "pbp_v3", GID)
    with pytest.raises(pd.errors.EmptyDataError):
        game_cache_read_csv(d, "pbp_v3", GID)


def _seed_flat(d):
    for gid in (GID, GID2):
        cache_write_csv(pd.DataFrame({"g": [gid]}),
                        game_cache_path(d, "pbp_v3", gid, sharded=False))
        cache_write_csv(pd.DataFrame({"g": [gid]}),
                        game_cache_path(d, "boxscore_trad", gid, sharded=False))
    # a per-season file that must NOT move, and a non-matching file
    cache_write_csv(pd.DataFrame({"s": [1]}), os.path.join(d, "2005-06_standings.csv"))
    open(os.path.join(d, "notes.txt"), "w").write("keep me")


def test_shard_moves_only_per_game_files(tmp_path):
    d = str(tmp_path)
    _seed_flat(d)
    moved = shard_cache.shard(d)
    assert moved == 4
    # sharded destinations exist, flat originals gone
    assert os.path.exists(os.path.join(d, "pbp_v3", "2005-06", "0020500123.csv.zst"))
    assert os.path.exists(os.path.join(d, "boxscore_trad", "1996-97", "0029600007.csv.zst"))
    assert not os.path.exists(os.path.join(d, "pbp_v3_0020500123.csv.zst"))
    # per-season + non-matching untouched
    assert os.path.exists(os.path.join(d, "2005-06_standings.csv.zst"))
    assert os.path.exists(os.path.join(d, "notes.txt"))
    # reads still work through the helper after the move
    assert game_cache_exists(d, "pbp_v3", GID)
    # idempotent second run
    assert shard_cache.shard(d) == 0
    assert shard_cache.verify(d) is True


def test_shard_dry_run_moves_nothing(tmp_path):
    d = str(tmp_path)
    _seed_flat(d)
    assert shard_cache.shard(d, dry_run=True) == 4
    assert os.path.exists(os.path.join(d, "pbp_v3_0020500123.csv.zst"))  # still flat


def test_unshard_reverses(tmp_path):
    d = str(tmp_path)
    _seed_flat(d)
    shard_cache.shard(d)
    assert shard_cache.unshard(d) == 4
    assert os.path.exists(os.path.join(d, "pbp_v3_0020500123.csv.zst"))
    assert not os.path.exists(os.path.join(d, "pbp_v3", "2005-06", "0020500123.csv.zst"))
