# Data-integrity audit: silent data loss in fetch/parse code

Repo-wide audit prompted by the RAPM reliability work (2026-06-30). The RAPM
signal was near-zero because the possession reconstruction silently discarded
~60% of games that had complete play-by-play. That is one instance of a recurring
shape: **a small per-record failure (a name that will not match, a game that hit a
rate-limit) is swallowed, and often frozen into an empty-CSV cache so it never
recovers, compounding into large aggregate loss.** This file records every
instance found so the non-urgent ones are not lost.

## Fixed on branch `worktree-rapm-reliability-fix`

- **Whole-game drop in `reconstruct_possessions`** (`nbakit/nbakit/data.py`). A
  single period that could not be reconciled to 5-on-5 discarded the entire game,
  throwing out ~60% of games with complete data. Fixed: keep the valid 5-on-5
  possessions (`_emit` already skips non-5-on-5 ones), self-heal by not carrying a
  drifted lineup into the next period. Result: ~470-500 → ~1225-1230 games/season.
- **M5 — arbitrary eviction in `_reconcile_player`.** When a missed sub forced a
  6th player, the lineup was patched by dropping the smallest-id player. Fixed:
  evict the player who has gone longest without a play (the likeliest unlogged
  sub-out), tracked via `last_seen`.

Combined reliability gain from the reconstruction + M5 fixes (bare RAPM, 1000+ min):
split-half **0.10 → 0.32** for a 3-season pool (~0.48 full-data reliability by
Spearman-Brown); 4 seasons ~0.53, 5 seasons ~0.60. RAPM went from noise to a
usable metric, and the "how many years for a stable RAPM" answer is ~4 pooled
seasons to clear the usable ~0.5 line.
- **Substitution IN-player resolution (H4)** and **surname collision (H3)**.
  Sub-in players were matched by raw-lowercased family name, missing on accents
  (`Pöltl`), disambiguation initials (`F. Wagner`/`M. Wagner`), and suffixes
  (`Nance Jr.`); and two players sharing a surname overwrote each other in the
  lookup. Fixed: `_norm_name` (accent/suffix/initial strip) + a family-name → list
  lookup with off-court disambiguation.
- **Cache bug (H1/H2)** in `fetch_pbp` and `fetch_pbp_players`
  (`nbakit/nbakit/data.py`). Both wrote an empty placeholder CSV on ANY exception
  (including rate-limits), which later runs read as "already fetched, no data" and
  skip forever. Fixed: cache an empty marker only on a *successful* call that
  returns no rows (genuine no-data); on a transient/rate-limit error leave the file
  absent so a later run retries.

## Pending (recorded for later; not yet fixed)

Ranked. Each is the same silent-loss shape.

- **H5 — BBR schema drift in `fetch_mvp_votes` / `fetch_all_nba`**
  (`questions/player_rating_overview/player_rating_overview_data.py`). Still read
  the old `data-stat="player"` key; `fetch_bbr_advanced` already had to move to
  `name_display` this session. If the awards tables rename similarly, every row
  parses to `name=""`, is skipped, and an empty scrape is cached permanently.
  Blast radius: MVP share + All-NBA points (a core evaluation target) silently
  vanish for every season. Fix: use `name_display` (fallback to `player`), and do
  not cache an empty scrape as a permanent miss.
- **M1 — human-rankings crosswalk has no coverage report**
  (same file, ~L1047-1067). Unmatched MVP/All-NBA names are `dropna`'d then
  `fillna(0)`, turning a name-spelling miss into a real vote-getter recorded as 0,
  with no log line. Fix: add a `crosswalk_coverage_report` and distinguish
  unmatched from genuine non-selection.
- **M2 / M3 / M6 — other permanent caches of transient failures.**
  `fetch_referees` (partial-season CSV written, gaps never retried),
  `parse_schedule`/`fetch_attendance` (BBR schedule schema drift → empty cached),
  `fetch_shot_zones` / generic `fetch_cached_csv` (empty-on-exception). Apply the
  same H1/H2 fix (don't cache transient misses).
- **M4 — `apply_crosswalk` drops both players on a normalized-name collision**
  (`nbakit/nbakit/player_crosswalk.py`). Suffix stripping makes "Gary Payton" and
  "Gary Payton II" collide when co-active; both set to None. `OVERRIDES` is empty.
- **L1-L3** — referee↔foul inner join drops unmatched game IDs (no count);
  `_infer_starters` pads best-effort and only warns; `fetch_all_nba` team-token map
  is a fixed dict fragile to a BBR label change.

## Per-project fetch-coverage numbers (audit result)

Counted expected game IDs (from cached season game logs) vs cached file state
(non-empty / empty-placeholder ≤2 bytes / absent). Headline: the cache bug's
actual damage was **small**; the reconstruction drop was the big loss.

- **player_rating_overview PBP: 15,586 / 15,669 non-empty (99.5%), 83 empty
  placeholders, 0 absent.** The 83 are recoverable by delete+refetch and are
  concentrated: **77 in 2013-14** (a stranded transient-failure batch; neighbors
  are 100%), 5 in 2024-25, 1 in 2014-15. Boxscore starters: 100%.
- **home_court:** referee/shot-zone/hustle "empties" are almost all *genuine
  source absence* (pre-2001-02 officials, pre-1996-97 shot zones, pre-2015-16
  hustle, 2019-20 bubble), NOT the bug. One to confirm: 2002-03 playoff referees
  (88 games, inside the officials era but flagged `OFFICIALS_KNOWN_EMPTY_YEARS`).
- **knicks_2026_historic:** fully cached, no gaps.

Recoverable bug damage across the repo = **~83 PBP games** (mostly 2013-14). The
cache-bug fix above stops it recurring; a targeted delete+refetch of those 83
placeholders would close it.
