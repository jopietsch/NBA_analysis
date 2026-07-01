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

## Protecting new projects from this bug class

Two structural fixes, not just per-file patches, make this the default
instead of something each project has to remember:

1. **Any new per-record/per-season cache fetcher should build on
   `nbakit.data.fetch_cached_csv`** (or mirror its exception-vs-empty
   handling exactly) rather than hand-rolling a `try/except` around an API
   call. That helper had this exact bug until this pass (see below); now
   that it's fixed, every fetcher built on it — current and future — inherits
   the correct behavior for free. Bespoke per-project fetch loops
   (`fetch_pbp`, `fetch_referees`, `fetch_shot_zones`, `fetch_game_odds`) are
   where the bug keeps recurring precisely because each one reimplements the
   try/except by hand instead of sharing one audited implementation.
2. **The rule to hand-apply when a shared helper doesn't fit the shape of a
   new fetch:** an exception (network error, timeout, rate-limit, unexpected
   schema) must never be cached — return `None`/leave the file absent so a
   later run retries. Only a *successful* call that legitimately returns zero
   rows should be cached as a permanent empty marker. If code can't tell the
   two apart (e.g. `home_spread()` in `nbakit/nbakit/espn.py`, still pending
   above), that's itself a smell worth fixing: make the failure mode
   distinguishable, don't just guess.
3. **Add a same-shape test for every new fetch function**: monkeypatch the
   underlying API call to raise, assert no cache file was written and a
   second call retries. `questions/home_court/tests/test_home_court.py`'s
   `TestFetchShotZones` now has this test; copy its shape for new fetchers.
4. **Re-run this coverage audit (expected universe vs. cache state, and a
   parser-completeness spot check) whenever a new project's fetch pipeline
   is added**, not only after a bug is already suspected — this pass caught
   the `fetch_shot_zones` and `fetch_cached_csv` bugs by systematically
   diffing expected-vs-actual counts, not from a specific complaint.

## Fixed 2026-06-30 (home_court + knicks_2026_historic audit)

- **`fetch_shot_zones` cached an empty CSV on ANY exception**
  (`nbakit/nbakit/data.py:535-580`), the same H1/H2 shape already fixed for
  `fetch_pbp`/`fetch_pbp_players` but never applied here. Concrete stranded
  files were all one-sided (genuine source absence kills both Home and Road
  for a year; these killed exactly one): playoff shot-zones for **2003 Home,
  2006 Road, 2007 Home, 2009 Road, 2011 Home**. Because
  `compute_shot_zone_stats` skips a season when either side is `None`, all 5
  seasons dropped entirely from the playoff shot-zone series. Fixed the same
  way as `fetch_pbp`: an exception is no longer cached, only a genuine
  successful-but-empty result is. Deleted the 5 stale placeholders and
  refetched live: **all 5 recovered** (16 rows each), confirming they were
  transient failures, not real gaps.
- **`fetch_cached_csv` cached an empty CSV on ANY exception**
  (`nbakit/nbakit/data.py:364-394`). This is the shared generic helper new
  projects are meant to build fetch functions on (home_court's tracking
  rebounding/hustle/second-chance fetchers already route through it via
  `_fetch_tracking_cached`), so the bug was silently inherited by every
  caller. Fixed the same way as `fetch_pbp`/`fetch_shot_zones`: an exception
  is no longer cached. This is the highest-leverage fix in this pass since it
  protects every current and future project that uses the shared helper,
  not just one call site.
- **knicks_2026_historic: `fetch_game_odds` could freeze partial ESPN odds
  into cache with no coverage signal**
  (`questions/knicks_2026_historic/knicks_2026_data.py:920-966`). `home_spread()`
  returns `None` on any per-game failure (HTTP error, timeout, rate-limit, or
  an event-name-match miss) with no distinction from a genuinely missing
  line, and the frame was cached as-is. Fixed: if any game comes back with a
  null spread the file is not cached (so a later run retries all games) and a
  coverage warning is printed. Currently zero damage: the existing cached
  file has all 19 Knicks playoff games with valid spreads.

**Investigated, no fix needed — `OFFICIALS_KNOWN_EMPTY_YEARS={2003}`
(`questions/home_court/home_court_data.py:59`) is correct, not a masked bug.**
The initial hypothesis (both neighboring seasons complete, plus the
coincidental 2002-03 shot-zone gap above, looked like a stranded rate-limit
batch) turned out to be a false lead. Direct live verification against
`BoxScoreSummaryV3` for the 2002-03 playoffs shows every one of the 88 games
returns a normal 200 response with every other data set populated, but a
genuinely 0-row officials table, confirmed on a 6-game random sample plus the
first game of the season. This is real source absence in the NBA API for
that season, not a fetch bug. **Lesson for this audit process: circumstantial
evidence (two endpoints failing for the same season) is not proof; verify
empty results against a live call before concluding "bug" and changing
known-empty logic.**

## Pending (recorded for later; not yet fixed)

Ranked. Each is the same silent-loss shape.

- **L/M — partial pre-2002 referee caches, never completed, and they leak into
  the analysis** (`referee_1996-97_Playoffs.csv` 27/72 games,
  `1999-00` 6/75, `2000-01` 3/71). Non-empty partial CSVs read as cache hits,
  so `fetch_referees` never fills the gaps (the M2 shape). They also
  contradict `OFFICIALS_DATA_START_YEAR=2002` (officials data partially
  exists earlier) and get concatenated into `fetch_all_referee_data`, which
  runs from `START_YEAR=1984`. Impact is low in practice (the `min_games=50`
  filter screens most of it out), but worth cleaning for consistency.
- **L (latent, no current damage) — `fetch_attendance` schema-drift trap**
  (`questions/home_court/home_court_data.py:1196,1208-1210` +
  `nbakit.bbr.parse_schedule`). Transient failures are already handled
  correctly (returns `None`, doesn't cache). But a BBR table rename would make
  every page parse to `records=[]` and get cached as a permanent "genuine
  miss" — the same H5 shape flagged for the awards scrapers. All 27 attendance
  files are currently populated and correct.
- **L (latent, note only) — knicks_2026_historic: ESPN event match is a fixed
  substring** (`nbakit/nbakit/espn.py:64-69`, `"Knick" in event["name"]`),
  fragile to an ESPN label change the same way `fetch_all_nba`'s team-token
  dict is (L3 below). No current damage (19/19 games matched).
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
- **M2 / M3 — other permanent caches of transient failures.**
  `fetch_referees` (partial-season CSV written, gaps never retried),
  `parse_schedule`/`fetch_attendance` (BBR schedule schema drift → empty cached).
  `fetch_shot_zones` and generic `fetch_cached_csv` were in this list too;
  both fixed above.
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
- **home_court** (redone 2026-06-30, full pass including parser-completeness,
  not just presence/absence): game logs 86/86 (100%, 1984-2026 both season
  types), attendance 27/27, tracking reb+misc 52/52, regular-season shot zones
  60/60 — all populated with sane row counts. The empties split into two
  buckets. Genuine source absence (confirmed, not a bug): pre-1996-97 shot
  zones, pre-2002 officials **plus the 2002-03 playoffs specifically**
  (verified live, see "Fixed 2026-06-30" above), pre-2015-16 hustle
  box-outs, the 2019-20 bubble (`SKIP_PLAYOFF_YEARS={2020}`, correctly never
  requested, so absent not empty). **Recovered = 5 files**: the one-sided
  playoff shot-zone empties (2003H, 2006R, 2007H, 2009R, 2011H) were a real
  `fetch_shot_zones` bug, now fixed and refetched (all 5 came back with full
  16-team data). Plus 3 stale partial pre-2002 referee files (36 games, low
  practical impact, still pending) — see Pending above.
- **knicks_2026_historic** (redone 2026-06-30; the prior line only checked
  file presence, not parser/derivation correctness): **confirmed fully cached
  and complete.** Game logs, standings, and player logs are 43/43 for every
  pattern across 1984-2026, 0 empty placeholders, 0 absent. Every `build_*`
  derivation (champions, conference-gap, possession, adjusted-margin, and the
  Elo/Bradley-Terry/capped-SRS rating tables) returns exactly 43 rows, one per
  season, zero NaN in key columns. The two silent-drop shapes hunted for
  (unequal game-pair groups, unmapped conference/team lookups) drop nothing:
  0 non-paired games across all 86 season files, 0 unmapped teams. Franchise
  relocations (Seattle→OKC, Vancouver→Memphis, the Hornets/Pelicans swap) are
  a non-issue because every builder keys on integer `TEAM_ID`, never
  abbreviation. `fetch_game_logs`/`fetch_standings` have no
  empty-on-exception bug: a failed call propagates and leaves the file
  absent and retryable, which is why this project's cache is clean. Only
  finding: a latent odds-fetch fragility (now fixed, see above), which had
  caused zero damage to date.

Recoverable bug damage found and fixed this pass: **~83 PBP games** (mostly
2013-14, from the earlier RAPM-work fix) + **home_court: 5 playoff shot-zone
seasons recovered by delete+refetch**. knicks_2026_historic had no actual
damage, only a latent fragility that's now fixed. The 2002-03 playoff
referee gap (88 games) was investigated and confirmed as genuine source
absence, not recoverable.
