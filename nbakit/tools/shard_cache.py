#!/usr/bin/env python3
"""One-time reorg: move flat per-game cache files into season subfolders.

    <cache>/pbp_v3_<gid>.csv.zst        ->  <cache>/pbp_v3/<season>/<gid>.csv.zst
    <cache>/boxscore_trad_<gid>.csv.zst ->  <cache>/boxscore_trad/<season>/<gid>.csv.zst

Only the per-game kinds are touched; per-season files (totals, standings, ...)
stay at the cache root. Moves are atomic renames (metadata-only on the same
filesystem, so fast), idempotent, and resumable. See CACHE_COMPRESSION_PLAN.md
Phase 4. Do NOT run while a fetch is writing to the cache.

Usage:
    python3 shard_cache.py [--cache-dir DIR] [--dry-run] [--verify-only] [--unshard]
"""
import argparse
import os
import re
import sys

# Use THIS checkout's nbakit (not a stale editable install pointing elsewhere).
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from nbakit.data import default_cache_dir, season_of_game_id  # noqa: E402

KINDS = ("pbp_v3", "boxscore_trad")
_FLAT = re.compile(r"^(" + "|".join(KINDS) + r")_(\d{10})\.csv(\.zst|\.gz)?$")


def _flat_files(cache_dir):
    """Yield (kind, gid, ext, path) for flat per-game files at the cache root."""
    for name in os.listdir(cache_dir):
        m = _FLAT.match(name)
        if m:
            yield m.group(1), m.group(2), m.group(3) or "", os.path.join(cache_dir, name)


def _sharded_files(cache_dir):
    """Yield (kind, gid, ext, path) for already-sharded per-game files."""
    for kind in KINDS:
        root = os.path.join(cache_dir, kind)
        if not os.path.isdir(root):
            continue
        for season in os.listdir(root):
            sdir = os.path.join(root, season)
            if not os.path.isdir(sdir):
                continue
            for name in os.listdir(sdir):
                m = re.match(r"^(\d{10})\.csv(\.zst|\.gz)?$", name)
                if m:
                    yield kind, m.group(1), m.group(2) or "", os.path.join(sdir, name)


def shard(cache_dir, *, dry_run=False):
    moved = removed_dup = 0
    for kind, gid, ext, src in list(_flat_files(cache_dir)):
        dest_dir = os.path.join(cache_dir, kind, season_of_game_id(gid))
        dest = os.path.join(dest_dir, f"{gid}.csv{ext}")
        if dry_run:
            moved += 1
            continue
        if os.path.exists(dest):
            os.remove(src)          # already sharded; drop the flat duplicate
            removed_dup += 1
            continue
        os.makedirs(dest_dir, exist_ok=True)
        os.replace(src, dest)       # atomic move
        moved += 1
    verb = "would move" if dry_run else "moved"
    print(f"[shard] {verb} {moved} file(s)"
          + ("" if dry_run else f"; removed {removed_dup} flat duplicate(s)"))
    return moved


def unshard(cache_dir, *, dry_run=False):
    moved = 0
    for kind, gid, ext, src in list(_sharded_files(cache_dir)):
        dest = os.path.join(cache_dir, f"{kind}_{gid}.csv{ext}")
        if dry_run:
            moved += 1
            continue
        if os.path.exists(dest):
            os.remove(src)
            continue
        os.replace(src, dest)
        moved += 1
    print(f"[unshard] {'would move' if dry_run else 'moved'} {moved} file(s) back to flat")
    return moved


def verify(cache_dir):
    flat = list(_flat_files(cache_dir))
    sharded = list(_sharded_files(cache_dir))
    print(f"[verify] {len(sharded)} sharded, {len(flat)} still flat")
    if flat:
        print("  still-flat examples:", [os.path.basename(p) for *_, p in flat[:5]])
    return len(flat) == 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--cache-dir", default=None)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--unshard", action="store_true")
    args = ap.parse_args(argv)
    cache_dir = args.cache_dir or default_cache_dir()
    if args.verify_only:
        ok = verify(cache_dir)
        return 0 if ok else 1
    if args.unshard:
        unshard(cache_dir, dry_run=args.dry_run)
    else:
        shard(cache_dir, dry_run=args.dry_run)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
