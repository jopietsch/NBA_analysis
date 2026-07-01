"""Tests for nbakit/tools/compress_cache.py — the batch cache-compression tool.

Everything runs against a pytest tmp_path fixture; NEVER the real cache
(nbakit.data.default_cache_dir()). A live fetch job may be writing to the real
cache while these tests run, so touching it here would be actively harmful.
"""

import gzip
import os

import pandas as pd
import pytest

from tools import compress_cache as cc


def _df():
    return pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})


def _seed(tmp_path):
    """A representative mixed cache dir: normal csv, empty-marker csv,
    pre-existing .csv.zst (already migrated, no plain sibling), and a
    non-csv file that must never be touched.
    """
    normal = tmp_path / "normal.csv"
    _df().to_csv(normal, index=False)

    empty = tmp_path / "empty_marker.csv"
    pd.DataFrame().to_csv(empty, index=False)

    # Already migrated: only the compressed variant exists, no plain .csv.
    migrated_zst = tmp_path / "migrated.csv.zst"
    tmp_plain = tmp_path / "_migrated_seed.csv"
    _df().to_csv(tmp_plain, index=False)
    cc._compress_file(str(tmp_plain), str(migrated_zst), "zst")
    os.remove(tmp_plain)

    other = tmp_path / "notes.txt"
    other.write_text("not a csv, leave me alone")

    return normal, empty, migrated_zst, other


def test_find_uncompressed_csvs(tmp_path):
    normal, empty, migrated_zst, other = _seed(tmp_path)
    found = cc.find_uncompressed_csvs(str(tmp_path))
    assert sorted(found) == sorted([str(normal), str(empty)])


def test_compress_run_migrates_and_verifies(tmp_path):
    normal, empty, migrated_zst, other = _seed(tmp_path)

    result = cc.run_compress(str(tmp_path), codec="zst")

    assert result["mode"] == "compress"
    assert result["count"] == 2          # normal.csv + empty_marker.csv
    assert result["succeeded"] == 2
    assert result["errors"] == []

    # Originals removed.
    assert not normal.exists()
    assert not empty.exists()

    # Compressed siblings present and readable.
    normal_zst = tmp_path / "normal.csv.zst"
    empty_zst = tmp_path / "empty_marker.csv.zst"
    assert normal_zst.exists()
    assert empty_zst.exists()
    got = pd.read_csv(normal_zst)
    pd.testing.assert_frame_equal(got, _df())

    # Empty marker still raises EmptyDataError on read, exactly like the
    # uncompressed convention it replaces.
    with pytest.raises(pd.errors.EmptyDataError):
        pd.read_csv(empty_zst)

    # Pre-existing migrated file and non-csv file are untouched.
    assert migrated_zst.exists()
    assert other.exists()
    assert other.read_text() == "not a csv, leave me alone"

    # No stray temp files left behind.
    assert not any(f.endswith(".tmp") for f in os.listdir(tmp_path))


def test_second_run_is_a_no_op(tmp_path):
    _seed(tmp_path)
    first = cc.run_compress(str(tmp_path), codec="zst")
    assert first["count"] == 2

    snapshot_before = sorted(os.listdir(tmp_path))
    mtimes_before = {
        f: os.path.getmtime(tmp_path / f) for f in snapshot_before
    }

    second = cc.run_compress(str(tmp_path), codec="zst")
    assert second["count"] == 0
    assert second["succeeded"] == 0

    snapshot_after = sorted(os.listdir(tmp_path))
    assert snapshot_after == snapshot_before
    for f in snapshot_after:
        assert os.path.getmtime(tmp_path / f) == mtimes_before[f]


def test_keep_original_flag(tmp_path):
    normal, empty, migrated_zst, other = _seed(tmp_path)
    result = cc.run_compress(str(tmp_path), codec="zst", keep_original=True)
    assert result["succeeded"] == 2
    # Originals kept this time.
    assert normal.exists()
    assert empty.exists()
    assert (tmp_path / "normal.csv.zst").exists()
    assert (tmp_path / "empty_marker.csv.zst").exists()


def test_dry_run_writes_nothing(tmp_path):
    normal, empty, migrated_zst, other = _seed(tmp_path)
    before = sorted(os.listdir(tmp_path))

    result = cc.run_compress(str(tmp_path), codec="zst", dry_run=True)

    assert result["mode"] == "dry-run"
    assert result["count"] == 2
    assert result["raw_bytes"] > 0
    assert result["projected_compressed_bytes"] > 0

    after = sorted(os.listdir(tmp_path))
    assert after == before               # nothing written, nothing removed
    assert normal.exists() and empty.exists()
    assert not any(f.endswith(".zst.tmp") or f.endswith(".gz.tmp") for f in after)
    assert not (tmp_path / "normal.csv.zst").exists()


def test_verify_only_reports_mismatches(tmp_path):
    normal, empty, migrated_zst, other = _seed(tmp_path)
    # normal.csv / empty_marker.csv have no compressed sibling yet -> mismatches.
    result = cc.run_verify(str(tmp_path))
    assert result["checked"] == 2        # only real .csv files are checked
    paths_with_issues = {m["path"] for m in result["mismatches"]}
    assert str(normal) in paths_with_issues
    assert str(empty) in paths_with_issues

    # After compressing, verify-only should report no mismatches.
    cc.run_compress(str(tmp_path), codec="zst", keep_original=True)
    result2 = cc.run_verify(str(tmp_path))
    assert result2["mismatches"] == []


def test_decompress_restores_csv(tmp_path):
    normal, empty, migrated_zst, other = _seed(tmp_path)
    cc.run_compress(str(tmp_path), codec="zst")
    assert not normal.exists()
    assert (tmp_path / "normal.csv.zst").exists()

    result = cc.run_decompress(str(tmp_path), codec="zst")
    assert result["mode"] == "decompress"
    assert result["succeeded"] == result["count"]
    assert result["errors"] == []

    # .csv restored and byte-identical in content to the original data.
    assert normal.exists()
    got = pd.read_csv(normal)
    pd.testing.assert_frame_equal(got, _df())

    # Empty marker restored and still raises EmptyDataError.
    assert empty.exists()
    with pytest.raises(pd.errors.EmptyDataError):
        pd.read_csv(empty)

    # Compressed files removed after rollback (default: not kept).
    assert not (tmp_path / "normal.csv.zst").exists()
    assert not (tmp_path / "empty_marker.csv.zst").exists()
    # The file that was already-compressed before our compress step ran is
    # also a .zst, so --decompress restores it too; that's expected since
    # decompress targets every compressed file found.
    assert not migrated_zst.exists()
    assert (tmp_path / "migrated.csv").exists()


def test_decompress_keep_original_keeps_compressed_copy(tmp_path):
    normal, empty, migrated_zst, other = _seed(tmp_path)
    cc.run_compress(str(tmp_path), codec="zst")
    result = cc.run_decompress(str(tmp_path), codec="zst", keep_original=True)
    assert result["succeeded"] == result["count"]
    assert normal.exists()
    assert (tmp_path / "normal.csv.zst").exists()


def test_gzip_codec_roundtrip(tmp_path):
    path = tmp_path / "gzcase.csv"
    _df().to_csv(path, index=False)
    result = cc.run_compress(str(tmp_path), codec="gz")
    assert result["succeeded"] == 1
    assert not path.exists()
    gz_path = tmp_path / "gzcase.csv.gz"
    assert gz_path.exists()
    with gzip.open(gz_path, "rt") as f:
        assert "a,b" in f.readline()
    got = pd.read_csv(gz_path)
    pd.testing.assert_frame_equal(got, _df())


def test_non_csv_and_other_codec_never_touched(tmp_path):
    (tmp_path / "keep.csv.zst").write_bytes(b"not-touched-by-tool")
    (tmp_path / "notes.md").write_text("hello")
    found = cc.find_uncompressed_csvs(str(tmp_path))
    assert found == []
    result = cc.run_compress(str(tmp_path), codec="zst")
    assert result["count"] == 0
    assert (tmp_path / "keep.csv.zst").read_bytes() == b"not-touched-by-tool"
    assert (tmp_path / "notes.md").read_text() == "hello"
