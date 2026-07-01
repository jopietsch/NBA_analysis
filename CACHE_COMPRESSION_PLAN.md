# Cache Compression Plan

**Status:** proposal, not executed. This document is the design; nothing here is applied yet.

## Goal

Compress the shared monorepo cache (`nba_analysis/cache/`, resolved via `nbakit.default_cache_dir()`) so it stores far fewer bytes, while every reader keeps working unchanged. Three requirements:

1. **Transparent reads** — code can read a cache entry whether it is stored compressed (`.csv.zst`) or uncompressed (`.csv`), with no call-site awareness.
2. **Compressed writes going forward** — every new cache file the fetch pipeline writes lands compressed.
3. **Batch migration** — one pass compresses all ~16k existing `.csv` files, then removes the originals.

## Why this is cheap to do

`pandas` infers compression from the file extension on **both** read and write. `pd.read_csv("x.csv.zst")` auto-decompresses; `df.to_csv("x.csv.zst")` auto-compresses. So the compression itself needs no manual (de)coding — only the *path resolution* (which extension exists / which to write) has to be centralized.

- **pandas 3.0.3** and **zstandard 0.25.0** are already installed, so `.csv.zst` works today with zero new dependencies.
- Measured ratios (zstd level 10) on real cache files:

  | File type | Raw | zstd-10 | Ratio |
  |---|---|---|---|
  | `pbp_v3_*.csv` (play-by-play, the bulk) | 70 KB | 9.9 KB | **7.1x** |
  | `*_players.csv` (per-game logs) | 3.8 MB | 497 KB | **7.7x** |
  | `player_totals_*.csv` (wide numeric) | 166 KB | 67 KB | 2.5x |

- Cache today: **1.5 GB** (1.1 GB of it is 16k play-by-play files). Post-compression estimate: **~300 MB** (~4-5x overall, dominated by PBP → ~155 MB). The pending 1996-onward RAPM build would add ~1.5 GB raw → ~200 MB compressed instead.

**Compression choice: zstd** (`.csv.zst`), level ~10. Faster and slightly smaller than gzip on our files, already installed, pandas-native. gzip (`.csv.gz`) is the conservative fallback if we ever want `zcat`-friendliness outside pandas; the design keeps the codec behind one config constant so switching is a one-line change.

## Current state (what the plan has to touch)

Cache I/O is spread across ~120 call sites — and **roughly 70 of them are in per-project code, not nbakit**, so this is not an nbakit-only change. The paths are built from `_cache()` / cache-dir helpers on one line and read/written on another (variables `path`, `all_path`, `poss_cache`, `rs_path`, `po_path`, `st_path`, `cache_file`), so a same-line grep undercounts; classify by tracing the variable.

| File | Cache I/O sites | Helper / notes |
|---|---|---|
| `nbakit/nbakit/data.py` | ~41 | `default_cache_dir()`, `cache_path()`; the fetch layer (game logs, player logs, PBP, boxscores, totals, league avgs) |
| `player_rating_overview_data.py` | ~40 | `_cache()`, `CACHE_DIR`, inline `pbp_v3_*`/`boxscore_trad_*` paths in the RAPM path |
| `knicks_2026_data.py` | ~17 | `rs_path`/`po_path`/`st_path`/`cache_file` |
| `knicks_2026_historic/fetch_data.py` | 3 | **bare `os.path.exists` gates** — the re-fetch hazard |
| `home_court_data.py` | ~10 | |
| `home_court/generate_report.py` | ~2 | classify first (may target `generated/`, not `cache/`) |

**Two edge cases the audit surfaced:**
- `player_rating_overview_data.py:519` `read_csv(pd.io.common.StringIO(r.text))` reads a **downloaded HTTP response, not a cache file** — the audit test (step 2) must whitelist `StringIO`/URL reads so it does not force this through the shim.
- `knicks_2026_historic/fetch_data.py` has bare `os.path.exists(po_path/rs_path/st_path)` cache-hit gates. These **must** move to `cache_exists`; if missed, they read a "miss" after the originals are deleted and silently re-fetch.

The dominant pattern at each site is the trio:

```python
if os.path.exists(path):          # (a) cache hit?
    return pd.read_csv(path)      # (b) read
...
df.to_csv(path, index=False)      # (c) write
```

plus an **empty-marker** convention: a genuinely-absent record is cached as `pd.DataFrame().to_csv(path)` and detected on read via `except pd.errors.EmptyDataError`. There are ~10+ of these markers in `nbakit/data.py` alone (e.g. a game the source has no PBP for). **The compression layer must preserve this exact semantics**, because it is what stops the pipeline re-fetching dead games forever.

`cache/` is already in `.gitignore`, so `.csv.zst` files are ignored too — no gitignore change needed.

## Design: one small cache-IO layer in `nbakit`

Add four helpers to `nbakit/nbakit/data.py` (or a new `nbakit/nbakit/cache_io.py` imported there). Every call site switches to these; the compressed/uncompressed logic lives **only** here.

```python
CACHE_CODEC = os.environ.get("NBA_CACHE_CODEC", "zst")   # "zst" | "gz" | "none"
_COMPRESSED_EXT = {"zst": ".zst", "gz": ".gz", "none": ""}

def cache_variants(path):
    """Given a logical '<name>.csv', return existing-variant paths, compressed first."""
    return [path + ".zst", path + ".gz", path]        # read preference order

def cache_exists(path):
    return any(os.path.exists(p) for p in cache_variants(path))

def cache_read_csv(path, **kw):
    """Read whichever variant exists (compressed preferred). pandas auto-decompresses."""
    for p in cache_variants(path):
        if os.path.exists(p):
            return pd.read_csv(p, **kw)          # EmptyDataError still propagates
    raise FileNotFoundError(path)

def cache_write_csv(df, path, **kw):
    """Write the canonical compressed variant; remove any stale sibling variants."""
    ext = _COMPRESSED_EXT[CACHE_CODEC]
    target = path + ext
    tmp = target + ".tmp"
    df.to_csv(tmp, index=kw.pop("index", False), **kw)   # pandas compresses by ext
    os.replace(tmp, target)                               # atomic
    # drop other variants so a later read never returns a stale copy
    for p in cache_variants(path):
        if p != target and os.path.exists(p):
            os.remove(p)

def cache_glob(pattern):
    """glob that matches '<pattern>' plus its .zst/.gz variants."""
    ...
```

Semantics that must hold:

- **Read** prefers `.csv.zst`, then `.csv.gz`, then `.csv`. So during migration (mixed state) everything is readable; after migration only `.zst` remains.
- **Write** always produces the canonical codec and atomically replaces (temp + `os.replace`), then deletes stale siblings so there is never both a `.csv` and a `.csv.zst` for the same logical name.
- **Empty markers**: `cache_write_csv(pd.DataFrame(), path)` writes a compressed empty CSV; `cache_read_csv` decompresses it and pandas raises `EmptyDataError` exactly as before. **Must be unit-tested** — this is the subtle one.
- **kwargs passthrough**: several sites pass `dtype=`, `usecols=`, etc.; the shim forwards `**kw`.
- **Callers keep using logical `.csv` paths.** `cache_path()` and `_cache()` are unchanged; only the read/write/exists calls swap to the shim. This keeps the diff mechanical and the path names stable.

## Batch migration script

A standalone `nbakit/tools/compress_cache.py` (not imported by the pipeline):

- Walk `default_cache_dir()`, find every `*.csv` that has no `.csv.zst` sibling.
- For each: compress to `<name>.csv.zst.tmp`, `os.replace` to `<name>.csv.zst`, **verify** (re-open and confirm it reads, or byte-count sanity), then delete the original `.csv`.
- **Idempotent / resumable**: skip files already migrated; safe to re-run after an interruption (temp files are ignored/overwritten, originals only deleted after a verified write).
- **Empty files** (0/1-byte markers): compress to a compressed-empty marker; preserve the EmptyDataError-on-read behavior.
- **Parallel**: CPU-bound, so a `multiprocessing.Pool(os.cpu_count())` over the file list. 16k files at ~7x is minutes, not hours. (This is where the *compute* parallelism lives — see the subagent note below.)
- **Flags**: `--dry-run` (report count, total raw vs projected compressed bytes, no writes), `--codec zst|gz`, `--keep-original` (compress but don't delete, for a cautious first pass), `--verify-only`.
- Leaves non-`.csv` files untouched (confirm the cache holds only CSVs first; facts JSON lives under `docs/`, not `cache/`).

## Sequencing (the one hazard that matters)

The failure mode: a **missed read site** that still calls raw `os.path.exists("x.csv")` will see a cache *miss* after migration deletes `x.csv`, and silently re-fetch from the API (hours of wasted calls, exactly the silent-data-loss class the repo already fights). Prevent it by ordering:

1. Land the shim + migrate **every** call site to it (reads still fall back to `.csv`, so nothing breaks while files are uncompressed).
2. Add an **audit test** that greps the codebase for raw `read_csv(`/`to_csv(`/`os.path.exists(` on cache paths and fails if any remain outside the shim. This is the completeness gate.
3. Only then run `compress_cache.py` (first `--dry-run`, then `--keep-original` for a smoke pass, then the real delete).
4. Run the full test suite + one real pipeline run per project against the compressed cache.

Because reads prefer compressed and fall back to uncompressed, steps 1-3 are safe in any partial state; the hard invariant is only that step 2 passes before step 3 deletes originals.

## Risks and mitigations

| Risk | Mitigation |
|---|---|
| A missed raw-`.csv` read site re-fetches after originals are deleted | Audit test (step 2) greps for raw cache I/O; migration keeps `--keep-original` until the suite is green |
| Empty-marker semantics break under compression | Dedicated unit test: write empty df compressed, assert `cache_read_csv` raises `EmptyDataError` and `cache_exists` is True |
| `read_csv` kwargs at call sites (dtype/usecols) dropped | Shim forwards `**kw`; grep call sites for non-default args during migration |
| Non-CSV files in cache | `compress_cache.py` only touches `*.csv`; a pre-check lists any other extensions |
| Concurrent pipeline run during migration | Migration is atomic per file (temp+replace) and idempotent; document "don't fetch while migrating," or gate on no running pipeline |
| Another project regresses (shared lib) | Run all three projects' test suites; the shim defaults preserve current behavior with `NBA_CACHE_CODEC=none` |

## Testing

- `nbakit/tests/test_cache_io.py` (new): roundtrip write→read for zst and gz; prefer-compressed when both exist; fallback to `.csv` when only it exists; empty-marker EmptyDataError; kwargs passthrough; `cache_exists`/`cache_glob` match all variants; atomic write leaves no `.tmp` on success.
- Audit test (new, in `nbakit/tests/` or repo-level): no raw `read_csv`/`to_csv`/`os.path.exists` on cache paths outside the shim.
- Each project's existing data tests must pass unchanged against a compressed fixture.
- `compress_cache.py --dry-run` on a temp copy: asserts projected sizes and that every `.csv` maps to exactly one `.csv.zst`.

## Execution with parallel subagents

The work splits into file-disjoint workstreams. The shim is the interlock and must land first (everyone imports its API); the call-site migrations are then independent per codebase area and run in parallel.

**Phase 1 — shim (blocking, do first):**
- **Workstream A — `opus`**: design + implement the cache-IO shim and `CACHE_CODEC` config in `nbakit/`, migrate the ~41 `nbakit/data.py` call sites, write `test_cache_io.py` + the audit test. Opus because the empty-marker semantics, atomicity, and read-preference logic are the correctness-critical core and define the API the others depend on.

**Phase 2 — call-site migration (parallel, after A merges; file-disjoint):**
- **Workstream B — `sonnet`**: migrate `questions/player_rating_overview/` (`player_rating_overview_data.py` + the inline RAPM `pbp_v3` paths) and its tests.
- **Workstream C — `sonnet`**: migrate `questions/knicks_2026_historic/` (`knicks_2026_data.py`, `fetch_data.py`) and tests.
- **Workstream D — `sonnet`**: migrate `questions/home_court/` (`home_court_data.py`, `generate_report.py`) and tests.
- **Workstream E — `sonnet`**: write `nbakit/tools/compress_cache.py` (dry-run/verify/parallel/idempotent). Independent file; can be built during Phase 2 but **run last**.

Each Phase-2 subagent gets the frozen shim API and a strict "only touch your directory" boundary, so they never edit the same file. They are launched together and run concurrently.

**Phase 3 — migrate + verify (serial, after all merge):**
- Run the audit test (completeness gate). Then `compress_cache.py --dry-run` → `--keep-original` → full suite → real delete → full suite + one pipeline run per project.

**Note on "parallel" for the batch itself:** the *code* is written by parallel subagents; the actual byte-compression of 16k files is done by `compress_cache.py`'s `multiprocessing.Pool` (CPU-bound, cores in parallel), not by subagents — sharding a pure-CPU compress across agents would be slower and harder to verify than one pooled script.

## Rollback

- Set `NBA_CACHE_CODEC=none` to make writes go back to plain `.csv` (reads still find existing `.zst`).
- To fully revert bytes: a `--decompress` mode on `compress_cache.py` restores `.csv` from `.csv.zst`.
- The shim change is backward compatible: with no compressed files present and codec `none`, behavior is byte-identical to today.

## Should more of this move to nbakit?

Considered and mostly declined, for this change. The per-project cache sites are almost all **domain-specific derived or third-party data** (player_rating: DARKO/EPM/LEBRON/RAPTOR/RAPM/unified; home_court: attendance/tracking; knicks: cross-era) — they belong to their projects, not the shared toolkit. The genuinely-shared base fetchers already live in nbakit and are imported. So:

- **The consolidation that matters for compression is already here**: the cache I/O *policy* (codec, path resolution, empty-marker handling) becomes one nbakit responsibility via the shim, instead of being re-implemented at ~120 sites. Every project calls the shim; none re-implements compression.
- **Moving the derived-cache computations into nbakit is rejected** — it would pollute the shared library with single-project logic and would not reduce the number of sites that must call the shim.
- **Two dedup wins, deferred to a separate pass** (do NOT bundle with this behavior-preserving change): (1) an optional nbakit `cached_fetch(path, fetch_fn, **kw)` helper wrapping the repeated exists→read→fetch→write dance, which would shrink every project's cache code and is a natural companion to the shim; (2) `knicks_2026_data.py`'s `{season}_standings` cache appears to duplicate nbakit's `fetch_standings` — reconcile it. Both are structural refactors with their own review/rollback surface; keeping them out of the compression PR keeps that PR mechanical.

## Out of scope / open decisions

- **Parquet instead of compressed CSV** for the numeric tables (season totals, ratings) would compress better and read faster, but changes the on-disk format and dtype round-tripping; deferred — this plan keeps CSV semantics and only adds compression.
- **Codec**: plan recommends zstd; confirm before Phase 1 (one-line change if gzip is preferred).
- Whether to compress tiny files (< a few KB) at all, or skip them by a size threshold (marginal savings, slightly simpler `ls`).

---

# Phase 4: directory sharding (Option A)

**Status:** proposal, not executed. Run **after** the RAPM historical build finishes (same "don't reorganize the cache while a fetch is writing to it" rule as the compression batch).

## Why

The cache is ~68k files and 98.8% of them are per-game (`pbp_v3_{gid}.csv.zst`, `boxscore_trad_{gid}.csv.zst`). Nothing is *broken* — APFS handles it and the hot paths read exact filenames (O(1), no directory scan) — but `ls` is unusable and any `glob` scans the whole directory. Sharding the per-game files into season subfolders fixes navigability and gives natural, immutable backup units, at low risk.

**Why A and not Parquet consolidation (Option B3):** at ~300 MB the Parquet wins (compression, columnar reads, types) are marginal, and B3's cost is real (new format, losing `zcat`/grep, compaction + a dual-representation hit check). A is right-sized. Crucially **A is a stepping-stone, not a dead end**: its `cache/pbp_v3/<season>/` layout is exactly the partition structure B3 would use, so upgrading later keeps the layout and only swaps the format. Revisit B3 only if the data grows a lot, real cross-season SQL queries become part of the workflow, or the type-coercion bugs start to bite.

## Layout

- Per-game files move into a type + season subdir: `cache/pbp_v3/<season>/<gid>.csv.zst`, `cache/boxscore_trad/<season>/<gid>.csv.zst` (~30 files/season/type).
- The ~800 per-season files (totals, standings, league averages, tracking, shot zones, referees, RAPM outputs, third-party snapshots) stay flat at the cache root — they are already few and readable.

## Mechanism (reuses the compression shim)

- **A path helper** in the shim maps a logical per-game filename to its sharded location: `pbp_v3_{gid}.csv` → `pbp_v3/<season>/{gid}.csv`. The handful of per-game path constructions (`fetch_pbp`, `fetch_pbp_players`, `_season_possessions` reads, the inline `pbp_v3_`/`boxscore_trad_` joins in `player_rating_overview_data.py`) route through it.
- **gid → season** is deterministic: the 10-digit game ID encodes the season (`002YYNNNNN`, `YY` = start-year last two digits, e.g. `0020500123` → `2005-06`). A small `season_of_game_id(gid)` helper does the parse. Writers already know the season from context; readers derive it from the gid.
- **Dual-representation reads (the critical requirement).** Exactly like the compression variant-fallback: a per-game read/exists must resolve **sharded path first, then flat**, so the cache works during the transition and after. The one-time reorg deletes the flat files only after the sharded copy is verified.

## One-time reorg script

`nbakit/tools/shard_cache.py`, mirroring `compress_cache.py`: walk flat per-game files, move each to its season subdir (atomic rename), idempotent/resumable, with `--dry-run`, `--verify-only`, and `--unshard` (rollback). Only touches `pbp_v3_*`/`boxscore_trad_*`; leaves per-season files flat.

## Rebuild-from-empty works unchanged

The cache is a derived artifact. On a fresh build the writers know each game's season, so they write straight into `pbp_v3/<season>/` — no reorg needed, no special cold-start handling. Resume-after-interruption and mixed flat/sharded states are covered by the dual-representation hit check above (the same discipline that makes "delete the cache and start over" safe today).

## Backup synergy

Once sharded, `backup_cache.sh --per-season` tars each season subdir separately. Completed seasons are immutable, so their archive is written once and never re-touched; only the in-progress season's tar changes. That is the incremental backup the flat layout can't do cleanly.

## Execution with subagents

Small enough to do in one or two workstreams: (A, opus) the shim path helper + `season_of_game_id` + `shard_cache.py` + tests; (B, sonnet) route the per-game call sites through the helper and confirm dual-path reads. Then the audit (no flat per-game path built outside the helper) → `shard_cache.py --dry-run` → real reorg → suite. Gated until the RAPM build is idle.
