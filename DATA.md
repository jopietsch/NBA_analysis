# Data: what it is, how we get it, and why it's stored this way

This document explains the data behind `nba_analysis`: where it comes from, how it's fetched and cached, and the design choices we've made. It's here so we remember the decisions, and so anyone who clones this repo can understand the data before relying on it.

## At a glance

- **Sources:** almost everything is public NBA data from `stats.nba.com` (via the `nba_api` package) and Basketball-Reference (scraped). A few third-party rating systems come from downloaded CSVs.
- **The cache is not in the repo.** All fetched data lives in `nba_analysis/cache/` (a single shared directory for every project), which is **gitignored**. A fresh clone starts with an empty cache and fills it on first run. Nothing here is primary data: the cache is a *derived artifact*, fully re-downloadable.
- **It's slow to build.** A full historical fetch (play-by-play back to 1996-97) is on the order of **~13 hours** of throttled API calls, which is why the cache is worth compressing and backing up.
- **On disk:** files are compressed (`.csv.zst`, ~7.8x). Reads transparently accept compressed or plain CSV.

## Where the data comes from

| Source | What we get from it | How |
|---|---|---|
| **nba_api** (`stats.nba.com`) | Game logs, player/team season totals, league averages, play-by-play, boxscores, standings, shot locations, player tracking, referees | Python `nba_api` endpoints |
| **Basketball-Reference** | Published advanced stats (OBPM/DBPM/BPM/VORP references), award voting (MVP, All-NBA, All-Star) | HTML scrape (`nbakit.bbr`) |
| **Third-party rating systems** | RAPTOR (FiveThirtyEight GitHub CSVs), DARKO / EPM / LEBRON (manual or snapshot CSVs, some paywalled/defunct) | Downloaded/snapshotted CSVs, joined via the player crosswalk |
| **ESPN / betting** | Reputation ranks, betting-market lines (used as cross-checks) | Snapshot / scrape |

## The main data types and how far back they go

"Fetchable" is what the source *can* serve; "we use" is what this project actually caches and computes against.

| Data type | Endpoint / source | Coverage |
|---|---|---|
| Game logs (one row per team per game) | `LeagueGameFinder` | 1983-84 → present |
| Player / team season totals | `LeagueDashPlayerStats` / `LeagueDashTeamStats` | 1996-97 → present (used); box era from 1983-84 |
| League averages | derived from team totals | 1996-97 → present |
| **Play-by-play** | `PlayByPlayV3` | **1996-97 → present** (the true floor: the league has no play-by-play before 1996-97) |
| Boxscores (lineups/starters) | `BoxScoreTraditionalV3` | 1996-97 → present |
| Standings | `LeagueStandingsV3` | 1983-84 → present |
| Player tracking (hustle, rebounding, misc) | tracking endpoints | 2013-14 → present (tracking era) |
| Referees | `BoxScoreSummaryV3` (officials data set) | as available |
| Awards / reputation | Basketball-Reference, ESPN, The Ringer | historical |
| Impact metrics (RAPTOR / DARKO / EPM / LEBRON) | third-party | RAPTOR 2013-14→2022-23; others vary, some defunct |

**Derived data we compute (not fetched):** RAPM and RAPM+prior (from reconstructed play-by-play possessions), and the recomputed box-score ratings (PER, Win Shares, BPM/VORP) live in the cache too but are produced by our own code from the fetched inputs.

## How the fetching works (and its quirks)

The data module is the only layer that calls external APIs; everything downstream reads the cache. A few `nba_api` quirks are worth knowing (they're also in `nbakit` and the project CLAUDE.md files):

- **Endpoint parameter names differ.** `LeagueGameFinder` uses `season_nullable=` / `season_type_nullable=`; most other endpoints use a bare `season=`. Easy to get wrong.
- **Game IDs must be zero-padded to 10 digits** for any endpoint that takes one (`f"{int(float(gid)):010d}"`). Reading them back from CSV loses the padding (they parse as ints), so we re-pad on use. (This is one reason typed storage like Parquet is tempting; see the design notes.)
- **Play-by-play uses V3, not V2.** `PlayByPlayV3` and `BoxScoreTraditionalV3` cover the whole 1996-2025 range; `PlayByPlayV2` errors in the current `nba_api` version.
- **Throttling.** `stats.nba.com` rate-limits, so fetches sleep between calls (~0.6-1.0 s; 0.6 s has been validated safe across thousands of calls). This is the main reason a full historical build takes hours.

## The cache

- **One shared cache for all projects:** `nba_analysis/cache/`, resolved by `nbakit.default_cache_dir()` and overridable with the `NBA_CACHE_DIR` env var. Every project reuses the same fetched data instead of keeping its own copy.
- **Gitignored.** The cache is build output, not source. It is safe to delete: rerunning the pipelines re-fetches everything (see "Rebuilding" below).
- **Compressed, with transparent reads.** Files are stored as `.csv.zst` (~7.8x smaller than raw CSV; 1.5 GB → ~300 MB). A thin cache-IO layer in `nbakit` (`cache_read_csv` / `cache_write_csv` / `cache_exists`) reads whichever exists (`.csv.zst` preferred, plain `.csv` as fallback) and writes compressed by default. Callers use logical `.csv` names and never think about compression. See `CACHE_COMPRESSION_PLAN.md`.
- **You can still inspect a file.** `zstdcat cache/<file>.csv.zst` (or a DuckDB query) reads any single file as text, so the "grep a CSV" workflow survives compression.

### How we record data we *couldn't* fetch

We distinguish two kinds of "missing," because they need opposite handling:

- **The origin genuinely has none** (e.g. play-by-play before 1996-97, or a game the source has no data for): we cache an **empty-marker file**, so we remember "permanently absent" and never re-request it.
- **The fetch failed** (throttle, HTTP error, timeout): we cache **nothing**, so the game stays uncached and the next run retries it. Caching a fake "absent" on a transient error is the bug we specifically avoid (it would silently drop data forever).

This is a deliberately simple, binary scheme. A richer future option is a **fetch-status manifest** (one row per game/endpoint recording `SUCCESS` / `ABSENT_AT_SOURCE` / `HTTP_ERROR`, with a timestamp and code), which would make coverage auditable and let a rebuild skip known-absent data. It's noted as a possible improvement, not yet built.

## Rebuilding from scratch

Because the cache is a derived artifact, **you can delete it and start over** — the pipelines will re-fetch and recompute everything. Two honest caveats:

- A full rebuild re-hits the API (~13 h for the play-by-play history), so it's not instant.
- The API can change or drop old data over time, so a rebuild is a fresh *snapshot*, not guaranteed byte-identical to what you deleted. Deleting also clears the "known-absent" markers, which get re-discovered by re-probing.

## Backing up

Because a rebuild costs ~13 h, keep a backup. Copying ~68k tiny files is slow everywhere, so bundle them: `./backup_cache.sh` writes a single timestamped `tar` of the whole cache (plain tar — the files are already compressed). Restore with `tar -xf`. See the script for a `--per-season` mode that becomes useful once the per-game files are sharded into season folders.

## Design decisions (why it's this way)

- **Compressed CSV, not Parquet (for now).** At ~300 MB the Parquet wins (better compression, columnar reads, typed schemas) are marginal, and CSV keeps the data greppable with ordinary tools. Parquet — and consolidating per-game files into per-season tables — is documented as a future option to revisit if the data grows a lot or real cross-season SQL queries become part of the workflow. See `CACHE_COMPRESSION_PLAN.md`.
- **Per-game files, sharded by season (planned).** Play-by-play and boxscores are cached one file per game so fetching is resumable and cache hits are per-game. Because that's ~67k files, the plan is to shard them into `pbp_v3/<season>/…` folders (Option A in the plan) for navigability and clean per-season backups — a low-risk step that also happens to be the layout a future Parquet move would use.
- **A single shared cache** across projects avoids re-downloading the same games for each analysis.
- **Recompute-and-validate** for box-score ratings: rather than trust one source, BPM/VORP are recomputed and checked against Basketball-Reference each run.

## Pointers

- `CACHE_COMPRESSION_PLAN.md` — the cache I/O layer: compression (shipped), directory sharding (Phase 4), and the Parquet option.
- `nbakit/` — the shared toolkit: all fetching, caching, and the rating computations.
- `questions/CLAUDE.md` and each `questions/<project>/CLAUDE.md` — project-level conventions and data notes.
