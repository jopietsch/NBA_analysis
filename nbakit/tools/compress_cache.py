"""
nbakit/tools/compress_cache.py — batch-compress the shared NBA cache.

Standalone script (not imported by the fetch pipeline; see CACHE_COMPRESSION_PLAN.md).
Walks the cache directory (nbakit.data.default_cache_dir() by default, or
--cache-dir) and, for every "*.csv" file that has no compressed sibling
("<name>.csv.zst" / "<name>.csv.gz"), compresses it and deletes the original:

    <name>.csv  --compress-->  <name>.csv.zst.tmp  --os.replace-->  <name>.csv.zst
                --verify (re-open, confirm it reads back)-->  delete <name>.csv

The compression is a raw byte-stream copy (zstandard / gzip), not a pandas
parse-then-rewrite, so the compressed file's bytes decompress to exactly the
original file, including the empty-marker convention (a 0/1-byte CSV that
raises pandas.errors.EmptyDataError on read, used to remember "this record
genuinely doesn't exist" instead of "not fetched yet"). Verification reads
the compressed file with pandas exactly as a real caller would; an
EmptyDataError there is treated as a valid, expected outcome for a marker.

Idempotent and resumable: a ".csv" with an existing compressed sibling is
skipped. An original ".csv" is only ever deleted after its compressed
sibling has been written (atomically, via a "*.tmp" + os.replace) AND
verified to read back; an interrupted run can leave a stray "*.tmp" file,
which the next run's compress step simply overwrites (os.replace clobbers
it), so nothing needs cleaning up by hand.

Usage:
    python3 nbakit/tools/compress_cache.py [--cache-dir DIR] [--codec {zst,gz}]
        [--dry-run] [--keep-original] [--verify-only] [--decompress]
"""

# Use this worktree's nbakit, not a global install (see nbakit/conftest.py).
import os as _os
import sys as _sys

_d = _os.path.dirname(_os.path.abspath(__file__))
while _os.path.dirname(_d) != _d and not _os.path.isdir(_os.path.join(_d, "nbakit", "nbakit")):
    _d = _os.path.dirname(_d)
_sys.path.insert(0, _os.path.join(_d, "nbakit"))

import argparse
import gzip
import multiprocessing
import os

import pandas as pd
import zstandard as zstd

_EXT = {"zst": ".zst", "gz": ".gz"}
_ZSTD_LEVEL = 10


# ── Raw byte-stream (de)compression ─────────────────────────────────────────────
# Compress/decompress the file's bytes directly, never through a pandas
# read_csv/to_csv round trip, so no formatting (float repr, quoting, NaN
# spelling) can drift and the empty-marker convention needs no special case.

def _compress_file(src_path: str, dst_path: str, codec: str) -> None:
    if codec == "zst":
        cctx = zstd.ZstdCompressor(level=_ZSTD_LEVEL)
        with open(src_path, "rb") as fin, open(dst_path, "wb") as fout:
            cctx.copy_stream(fin, fout)
    elif codec == "gz":
        with open(src_path, "rb") as fin, gzip.open(dst_path, "wb") as fout:
            fout.write(fin.read())
    else:
        raise ValueError(f"unknown codec {codec!r}")


def _decompress_file(src_path: str, dst_path: str, codec: str) -> None:
    if codec == "zst":
        dctx = zstd.ZstdDecompressor()
        with open(src_path, "rb") as fin, open(dst_path, "wb") as fout:
            dctx.copy_stream(fin, fout)
    elif codec == "gz":
        with gzip.open(src_path, "rb") as fin, open(dst_path, "wb") as fout:
            fout.write(fin.read())
    else:
        raise ValueError(f"unknown codec {codec!r}")


def _verify_readable(path: str) -> None:
    """Confirm `path` reads back like a real cache read would.

    A pd.errors.EmptyDataError is the expected shape of an empty-marker file
    and is NOT a failure; any other exception propagates to the caller.
    """
    try:
        pd.read_csv(path)
    except pd.errors.EmptyDataError:
        pass


def _compressed_sibling(path: str) -> str | None:
    """The existing compressed variant of a logical '<name>.csv' path, if any."""
    for ext in _EXT.values():
        if os.path.exists(path + ext):
            return path + ext
    return None


# ── Discovery ────────────────────────────────────────────────────────────────

def find_uncompressed_csvs(cache_dir: str) -> list[str]:
    """All '*.csv' files under cache_dir that have no compressed sibling."""
    out = []
    for root, _dirs, files in os.walk(cache_dir):
        for name in files:
            if not name.endswith(".csv"):
                continue
            full = os.path.join(root, name)
            if _compressed_sibling(full) is None:
                out.append(full)
    return out


def find_compressed_files(cache_dir: str, codec: str | None = None) -> list[str]:
    """All compressed cache files; restrict to one codec's extension if given."""
    exts = [_EXT[codec]] if codec else list(_EXT.values())
    out = []
    for root, _dirs, files in os.walk(cache_dir):
        for name in files:
            if any(name.endswith(ext) for ext in exts):
                out.append(os.path.join(root, name))
    return out


# ── Worker functions (module-level so multiprocessing can pickle them) ────────

def compress_one(item: tuple[str, str, bool]) -> dict:
    """Compress one '<name>.csv' to its compressed sibling; verify; delete original.

    item: (path, codec, keep_original). Never deletes `path` until the
    compressed sibling has been written atomically and verified.
    """
    path, codec, keep_original = item
    target = path + _EXT[codec]
    tmp = target + ".tmp"
    try:
        raw_bytes = os.path.getsize(path)
        _compress_file(path, tmp, codec)
        os.replace(tmp, target)          # atomic
        _verify_readable(target)
    except Exception as e:                # noqa: BLE001 - report, don't crash the pool
        for p in (tmp, target):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        return {"path": path, "ok": False, "error": str(e)}
    compressed_bytes = os.path.getsize(target)
    if not keep_original:
        os.remove(path)
    return {
        "path": path, "target": target, "ok": True,
        "raw_bytes": raw_bytes, "compressed_bytes": compressed_bytes,
    }


def decompress_one(item: tuple[str, bool]) -> dict:
    """Restore '<name>.csv' from a compressed sibling ('.zst' or '.gz').

    item: (target, keep_compressed). Rollback counterpart of compress_one.
    """
    target, keep_compressed = item
    codec = "zst" if target.endswith(".zst") else "gz" if target.endswith(".gz") else None
    if codec is None:
        return {"path": target, "ok": False, "error": "not a recognized compressed extension"}
    orig = target[: -len(_EXT[codec])]
    tmp = orig + ".tmp"
    try:
        _decompress_file(target, tmp, codec)
        os.replace(tmp, orig)
        _verify_readable(orig)
    except Exception as e:                # noqa: BLE001
        for p in (tmp, orig):
            if os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
        return {"path": target, "ok": False, "error": str(e)}
    if not keep_compressed:
        os.remove(target)
    return {"path": target, "ok": True, "restored": orig}


def _dry_run_one(item: tuple[str, str]) -> dict:
    """Project compressed size for one file without writing anything to disk."""
    path, codec = item
    raw_bytes = os.path.getsize(path)
    with open(path, "rb") as f:
        raw = f.read()
    compressed = (
        zstd.ZstdCompressor(level=_ZSTD_LEVEL).compress(raw)
        if codec == "zst" else gzip.compress(raw)
    )
    return {"path": path, "raw_bytes": raw_bytes, "compressed_bytes": len(compressed)}


# ── Orchestration ────────────────────────────────────────────────────────────
# Use the "fork" start method explicitly: this script's entry point inserts a
# path onto sys.path at runtime (see the header) so each worktree loads its
# own in-repo nbakit rather than a stale global editable install; "fork"
# inherits the parent's already-imported modules and sys.path directly,
# sidestepping any need for a freshly spawned interpreter to redo that dance.
def _pool(jobs: int | None):
    ctx = multiprocessing.get_context("fork")
    return ctx.Pool(jobs or os.cpu_count() or 1)


def run_compress(cache_dir: str, codec: str = "zst", *, keep_original: bool = False,
                  dry_run: bool = False, jobs: int | None = None) -> dict:
    files = find_uncompressed_csvs(cache_dir)
    if dry_run:
        with _pool(jobs) as pool:
            results = pool.map(_dry_run_one, [(p, codec) for p in files])
        raw_total = sum(r["raw_bytes"] for r in results)
        comp_total = sum(r["compressed_bytes"] for r in results)
        return {
            "mode": "dry-run", "codec": codec, "count": len(files),
            "raw_bytes": raw_total, "projected_compressed_bytes": comp_total,
            "results": results,
        }
    with _pool(jobs) as pool:
        results = pool.map(compress_one, [(p, codec, keep_original) for p in files])
    ok = [r for r in results if r["ok"]]
    errors = [r for r in results if not r["ok"]]
    return {
        "mode": "compress", "codec": codec, "count": len(files),
        "succeeded": len(ok), "errors": errors,
        "raw_bytes": sum(r["raw_bytes"] for r in ok),
        "compressed_bytes": sum(r["compressed_bytes"] for r in ok),
    }


def run_decompress(cache_dir: str, codec: str = "zst", *, keep_original: bool = False,
                    jobs: int | None = None) -> dict:
    """Rollback: restore '.csv' files from their compressed siblings."""
    files = find_compressed_files(cache_dir, codec=codec)
    with _pool(jobs) as pool:
        results = pool.map(decompress_one, [(p, keep_original) for p in files])
    ok = [r for r in results if r["ok"]]
    errors = [r for r in results if not r["ok"]]
    return {"mode": "decompress", "count": len(files), "succeeded": len(ok), "errors": errors}


def run_verify(cache_dir: str) -> dict:
    """Confirm every remaining '.csv' has a valid, readable compressed sibling."""
    mismatches = []
    checked = 0
    for root, _dirs, files in os.walk(cache_dir):
        for name in files:
            if not name.endswith(".csv"):
                continue
            checked += 1
            full = os.path.join(root, name)
            sib = _compressed_sibling(full)
            if sib is None:
                mismatches.append({"path": full, "issue": "no compressed sibling"})
                continue
            try:
                _verify_readable(sib)
            except Exception as e:          # noqa: BLE001
                mismatches.append({"path": full, "issue": f"sibling unreadable: {e}"})
    return {"mode": "verify", "checked": checked, "mismatches": mismatches}


# ── Reporting ────────────────────────────────────────────────────────────────

def _fmt_bytes(n: int) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if abs(n) < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def _print_summary(result: dict) -> None:
    mode = result["mode"]
    if mode == "dry-run":
        raw, comp = result["raw_bytes"], result["projected_compressed_bytes"]
        ratio = (raw / comp) if comp else float("inf")
        print(f"[dry-run] {result['count']} file(s) would be compressed ({result['codec']})")
        print(f"  raw:        {_fmt_bytes(raw)}")
        print(f"  projected:  {_fmt_bytes(comp)}")
        print(f"  ratio:      {ratio:.2f}x")
    elif mode == "compress":
        raw, comp = result["raw_bytes"], result["compressed_bytes"]
        ratio = (raw / comp) if comp else float("inf")
        print(f"[compress] {result['succeeded']}/{result['count']} file(s) compressed ({result['codec']})")
        print(f"  raw:        {_fmt_bytes(raw)}")
        print(f"  compressed: {_fmt_bytes(comp)}")
        print(f"  ratio:      {ratio:.2f}x")
        print(f"  errors:     {len(result['errors'])}")
        for e in result["errors"]:
            print(f"    {e['path']}: {e['error']}")
    elif mode == "decompress":
        print(f"[decompress] {result['succeeded']}/{result['count']} file(s) restored")
        print(f"  errors: {len(result['errors'])}")
        for e in result["errors"]:
            print(f"    {e['path']}: {e['error']}")
    elif mode == "verify":
        print(f"[verify] {result['checked']} '.csv' file(s) checked")
        print(f"  mismatches: {len(result['mismatches'])}")
        for m in result["mismatches"]:
            print(f"    {m['path']}: {m['issue']}")


# ── CLI ──────────────────────────────────────────────────────────────────────

def main(argv: list[str] | None = None) -> int:
    from nbakit.data import default_cache_dir

    p = argparse.ArgumentParser(description="Batch-compress the shared NBA cache.")
    p.add_argument("--cache-dir", default=None,
                   help="Cache directory (default: nbakit.data.default_cache_dir())")
    p.add_argument("--codec", choices=["zst", "gz"], default="zst")
    p.add_argument("--dry-run", action="store_true",
                   help="Report counts/bytes only; write nothing")
    p.add_argument("--keep-original", action="store_true",
                   help="Compress (or decompress) without deleting the source file")
    p.add_argument("--verify-only", action="store_true",
                   help="Check every '.csv' has a valid compressed sibling; report mismatches")
    p.add_argument("--decompress", action="store_true",
                   help="Rollback: restore '.csv' files from their compressed siblings")
    args = p.parse_args(argv)

    cache_dir = args.cache_dir or default_cache_dir()

    if args.verify_only:
        result = run_verify(cache_dir)
    elif args.decompress:
        result = run_decompress(cache_dir, codec=args.codec, keep_original=args.keep_original)
    else:
        result = run_compress(cache_dir, codec=args.codec, keep_original=args.keep_original,
                              dry_run=args.dry_run)

    _print_summary(result)
    has_errors = bool(result.get("errors") or result.get("mismatches"))
    return 1 if has_errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
