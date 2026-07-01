"""Tests for the nbakit.data cache-IO shim (transparent compression).

Uses pytest tmp_path throughout; never touches the real cache. The module
constant ``data.CACHE_CODEC`` is monkeypatched to exercise each codec.
"""

import glob
import os

import pandas as pd
import pytest

from nbakit import data


def _df():
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


@pytest.mark.parametrize("codec,ext", [("zst", ".zst"), ("gz", ".gz"), ("none", "")])
def test_write_read_roundtrip(tmp_path, monkeypatch, codec, ext):
    monkeypatch.setattr(data, "CACHE_CODEC", codec)
    path = str(tmp_path / "t.csv")
    written = data.cache_write_csv(_df(), path)
    assert written == path + ext
    assert os.path.exists(written)
    got = data.cache_read_csv(path)
    pd.testing.assert_frame_equal(got, _df())
    assert data.cache_exists(path)


def test_read_prefers_compressed(tmp_path, monkeypatch):
    # Both a plain .csv and a .csv.zst exist with DIFFERENT contents; the
    # compressed variant must win.
    monkeypatch.setattr(data, "CACHE_CODEC", "zst")
    path = str(tmp_path / "t.csv")
    pd.DataFrame({"v": [999]}).to_csv(path, index=False)         # stale plain csv
    pd.DataFrame({"v": [1]}).to_csv(path + ".zst", index=False)  # compressed
    got = data.cache_read_csv(path)
    assert got["v"].tolist() == [1]


def test_read_fallback_to_plain_csv(tmp_path):
    # Only the plain .csv exists (mid-migration state): read still works.
    path = str(tmp_path / "t.csv")
    _df().to_csv(path, index=False)
    assert not os.path.exists(path + ".zst")
    got = data.cache_read_csv(path)
    pd.testing.assert_frame_equal(got, _df())
    assert data.cache_exists(path)


def test_read_missing_raises_filenotfound(tmp_path):
    with pytest.raises(FileNotFoundError):
        data.cache_read_csv(str(tmp_path / "nope.csv"))


@pytest.mark.parametrize("codec", ["zst", "gz", "none"])
def test_empty_marker_roundtrips_to_emptydataerror(tmp_path, monkeypatch, codec):
    monkeypatch.setattr(data, "CACHE_CODEC", codec)
    path = str(tmp_path / "empty.csv")
    data.cache_write_csv(pd.DataFrame(), path)
    assert data.cache_exists(path)
    with pytest.raises(pd.errors.EmptyDataError):
        data.cache_read_csv(path)


def test_kwargs_passthrough(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "CACHE_CODEC", "zst")
    path = str(tmp_path / "t.csv")
    data.cache_write_csv(_df(), path)
    got = data.cache_read_csv(path, usecols=["a"])
    assert list(got.columns) == ["a"]


def test_write_index_kwarg(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "CACHE_CODEC", "zst")
    path = str(tmp_path / "t.csv")
    df = _df()
    data.cache_write_csv(df, path, index=True)
    got = data.cache_read_csv(path)
    # Writing with index=True produces an unnamed first column on read.
    assert "Unnamed: 0" in got.columns or got.columns[0] == "Unnamed: 0"


def test_write_leaves_no_tmp_and_removes_stale_sibling(tmp_path, monkeypatch):
    monkeypatch.setattr(data, "CACHE_CODEC", "zst")
    path = str(tmp_path / "t.csv")
    # Pre-existing stale plain .csv sibling.
    pd.DataFrame({"v": [999]}).to_csv(path, index=False)
    assert os.path.exists(path)
    data.cache_write_csv(_df(), path)
    # Stale sibling removed, canonical compressed variant present, no .tmp left.
    assert not os.path.exists(path)                # plain csv removed
    assert os.path.exists(path + ".zst")
    assert glob.glob(str(tmp_path / "*.tmp")) == []


def test_cache_glob_matches_all_variants(tmp_path):
    base = str(tmp_path / "pbp_v3_000.csv")
    pd.DataFrame({"v": [1]}).to_csv(base, index=False)
    pd.DataFrame({"v": [1]}).to_csv(str(tmp_path / "pbp_v3_001.csv.zst"),
                                    index=False)
    pd.DataFrame({"v": [1]}).to_csv(str(tmp_path / "pbp_v3_002.csv.gz"),
                                    index=False)
    matches = data.cache_glob(str(tmp_path / "pbp_v3_*.csv"))
    names = sorted(os.path.basename(m) for m in matches)
    assert names == ["pbp_v3_000.csv", "pbp_v3_001.csv.zst", "pbp_v3_002.csv.gz"]


def test_cache_glob_dedups(tmp_path):
    # A pattern that would match the same file under two sub-patterns is deduped.
    p = str(tmp_path / "x.csv")
    pd.DataFrame({"v": [1]}).to_csv(p, index=False)
    matches = data.cache_glob(str(tmp_path / "x.csv"))
    assert matches.count(p) == 1


def test_cache_variants_order(tmp_path):
    path = str(tmp_path / "t.csv")
    assert data.cache_variants(path) == [path + ".zst", path + ".gz", path]
