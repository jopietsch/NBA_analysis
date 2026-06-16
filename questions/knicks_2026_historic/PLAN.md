# Plan — Did the 2025–26 Knicks Have a Historic Playoff Run?

**Status: DONE** — All phases complete. PDF report and RESULTS.md generated, 24 tests pass.

Derived from `project_definition.md`. This is the working plan to get the project
off the ground: what we'll measure, with what data, in what order, and how we'll
check that the conclusions hold up.

## The question, sharpened

The naive claim: **the 2025–26 Knicks went 16–3 in the playoffs, so their run was
historic.** A 16–3 record is a championship run (16 wins = title) with only three
losses — on its face one of the best title runs ever.

Our job is to stress-test that claim. The headline alternative explanation:

> **The Eastern Conference was weak in 2025–26, so a 16–3 record overstates how
> dominant the Knicks actually were.** They may have beaten soft opponents for
> three rounds and only met a genuinely elite team (if at all) in the Finals.

We also test secondary deflators: easy path/bracket luck, blowouts vs. nail-biters,
era/pace inflation of margins, opponent injuries, and home-court/rest edges. The
deliverable is an honest verdict: **how historic, after adjusting for who they
actually beat.**

### Stated assumptions (verify against data before relying on them)

- **16–3 means the Knicks won the 2026 title.** The pipeline must confirm this from
  game logs, not take it on faith.
- **Use the full 1984–2026 span (max data).** The catch: playoff format changed, so
  *raw win totals* aren't comparable across eras — champions needed 15 wins in
  1984–2002 (best-of-5 first round) but 16 wins from 2003 on (best-of-7 throughout).
  So the **primary comparison metrics are format-robust rates** — playoff **win rate**
  and **average margin** — usable across all 42 seasons. Raw records (like "16–3") are
  reported with an era caveat, not used as the cross-era ranking key. `START_YEAR` is
  already 1984 in the data module.
- **Conference membership is taken from season standings**, not assumed static
  (teams have switched divisions/conferences over the decades).

## Phase 0 — Foundation: extract `nbakit`, then build on it

Do this **before** the analysis. `knicks_2026` was forked from `nba_home_court` and
already duplicates its two PDF generators verbatim plus the data plumbing. Rather
than let a second project harden the copy-paste, extract the question-agnostic
infrastructure into a shared library so improvements (and bug fixes) propagate to
every question instead of being re-copied by hand.

### Layout (monorepo: shared library + thin per-question packages)

```
nba_analysis/
  nbakit/                    # shared library — pip install -e
    pyproject.toml
    nbakit/
      data.py    # season helpers, cache, LeagueGameFinder wrapper, SRS,
                 #   conference mapping (LeagueStandings), champion-ID
      report.py  # FINDINGS.md → PDF (cover/title/output parametrized)
      mdpdf.py   # general markdown → PDF (was generate_doc_pdf.py)
      pipeline.py# run()→RESULTS.md capture boilerplate
    tests/
  questions/
    home_court/              # nba_home_court, migrated onto nbakit
    knicks_2026_historic/    # this project, built on nbakit
```

Stays **per-question** (don't generalize these — forced abstraction would hurt):
`compute_*` metrics, `plot_*`, `analysis.run_*`, `FINDINGS.md`, and the project's
`START_YEAR`/`END_YEAR`/`SUBJECT_YEAR` constants + a thin report config (title,
subtitle, output path).

### Steps

1. Create `nbakit/` with `mdpdf.py` + `report.py` (the verbatim-copied generators,
   cover/title/output parametrized). Point **both** projects at it — kills the worst
   duplication immediately.
2. Move season/cache/`LeagueGameFinder` helpers into `nbakit/data.py`; write **SRS,
   conference mapping, and champion-ID once there** (this project needs all three).
3. Migrate `nba_home_court` onto `nbakit` (verify its report + tests still pass) and
   wire `knicks_2026` onto it. Leave `compute_*`/plots/analysis/FINDINGS per-question.
4. Root `CLAUDE.md` documents `nbakit`; each question keeps its own `CLAUDE.md`.

**Guardrail:** extract on second use, not speculatively (our "Simplicity First" rule).
The generators and data helpers already qualify; analysis-specific code does not.

### Conventions baked into `nbakit` (carried from `nba_home_court`)

- **Output to `generated/`.** Already the `nba_home_court` convention (commit
  `7f7cb61`). Every `plot_*` saves to `generated/<name>.png`; the report's prerequisite
  check scans `FINDINGS.md` for those paths. `.gitignore` ignores `generated/` (done).
- **Date-robustness — single source of truth (commit `d742700`).** All displayed date
  ranges and counts derive from `START_YEAR`/`END_YEAR` (and `SUBJECT_YEAR` here); no
  hardcoded year strings anywhere in code-generated text. Concretely, carry into
  `nbakit`:
  - `season_range_label(start, end)` → e.g. `"1983–84 through 2025–26"`.
  - Report cover/footer take the range label **and a cache-derived game count**
    (the `_count_regular_season_games()` pattern) — never literal `"…2025–26 · 52,399 games"`.
  - Plot subtitles and any era/format buckets use `season_range_label()` /
    `str(END_YEAR)[-2:]`, not literal years.
  - For this project specifically: "2025–26", "the 2026 Knicks", and chart labels are
    derived from `SUBJECT_YEAR`/`END_YEAR`, so a future re-run for a different
    team/year changes one constant. (FINDINGS.md narrative prose is the one place
    literal years are unavoidable — keep them minimal.)
- **Centralized cache (shared across all questions).** Raw nba_api pulls are keyed by
  `(season, season_type)` and are question-agnostic — `nba_home_court` and this project
  fetch the *same* league-wide game logs. So all raw data goes in **one shared cache at
  the monorepo root** (`nba_analysis/cache/`), owned by `nbakit.data` and overridable
  via a `NBA_CACHE_DIR` env var. The second project reuses the first's downloads
  instead of re-fetching, and there's a single place to see exactly what's been pulled
  (so we don't accidentally fetch more than necessary). The shared cache is gitignored
  at the root. (Project-local `cache/` ignores become moot but stay harmless.)
- All math in Python, none in Claude.

---

## Phase 1 — Data acquisition (nba_api, via `nbakit`)

Question-specific fetches go in `knicks_2026_data.py` (importing `nbakit.data`
primitives); shared fetch/cache/SRS/conference/champion logic lives in `nbakit`.
All raw data cached in the **shared root cache** (`nba_analysis/cache/`, see Phase 0).

| Data | nba_api source | Use |
|------|----------------|-----|
| Playoff game logs, every season | `LeagueGameFinder` (`season_type_nullable="Playoffs"`) | Identify each champion; champion run records, margins, opponents |
| Regular-season game logs, every season | `LeagueGameFinder` (`"Regular Season"`) | SRS, net margin, **inter-conference head-to-head** |
| Team → conference, per season | `LeagueStandings` | Tag each team East/West; conference strength |
| Team advanced stats, per season | `LeagueDashTeamStats` (advanced) | Net rating cross-check on SRS |

Derived-not-fetched (computed in Python, no endpoint) — these are general NBA
primitives, so they live in **`nbakit.data`**, not the question module:

- **SRS (Simple Rating System)** per team per season — average scoring margin
  adjusted for strength of schedule, solved as a least-squares linear system from
  regular-season game logs (`numpy.linalg.lstsq`). Backbone opponent-quality and
  team-quality metric; self-contained and historically consistent.
- **Conference mapping** per season — `team_conference(season)` from `LeagueStandings`.
- **Champion identification** per season — the team with the title-clinching final
  playoff win (max playoff wins in that season's bracket).

`nbakit.data` exposes: `compute_srs(reg_season_games)`, `team_conference(season)`,
`identify_champion(playoff_games)`. Question-specific `compute_*` (opponent-adjusted
margin, the East/West gap series, percentile ranks) stay in `knicks_2026_data.py`.

---

## Phase 2 — Metrics & analysis (`knicks_2026_analysis.py`, `compute_*` in data)

Each metric is computed for the **2026 Knicks** *and* across the **historical
champion comparison set**, so the Knicks can be ranked / percentile-scored. Output
sections print to stdout → captured into `RESULTS.md` (box-drawing headers per
`CLAUDE.md`). Proposed sections, in narrative order:

1. **The raw claim.** 2026 Knicks playoff W–L, win rate, and average scoring margin;
   percentile vs. all champions 1984–2026 on the format-robust rates (win rate,
   margin), with the raw "16–3" reported under its era caveat. Establishes the "on
   its face, historic" baseline.
2. **Was the East weak in 2025–26?** Inter-conference head-to-head win pct (the
   gold-standard measure), plus mean SRS gap East vs. West, with a significance test
   on the conference SRS difference. Quantify the gap.
3. **How weak, in historical context?** Rank the 2025–26 East–West gap against every
   season since 1984. Is this a normal year or an outlier-weak East?
4. **Who did the Knicks actually beat?** SRS / net rating / regular-season win total
   of each Knicks playoff opponent, by round. Compare the *average opponent SRS the
   Knicks faced* to the average opponent faced by historical champions. Did their
   bracket dodge the league's best (especially Western) teams?
5. **Opponent-adjusted dominance (the money metric).** Adjust the Knicks' per-game
   playoff margin for opponent SRS, then re-rank champions on this adjusted basis.
   This is where "16–3" gets converted into "how good against whom."
6. **Other deflators / robustness:**
   - **Blowout vs. clutch:** distribution of game margins (did they win big or squeak
     by?); record in close games (≤5 pts).
   - **Era/pace:** normalize margins by league pace/scoring environment of each season
     so 2026 margins are comparable to slower eras.
   - **Path luck:** opponent SRS by round — did upsets elsewhere hand them an easy draw?
   - **Home court / rest:** seeding and rest-day edges, if material.
7. **Verdict.** Synthesize: where the Knicks land before vs. after the East/opponent
   adjustment. A defensible, quantified answer to "how historic."

---

## Phase 3 — Run the pipeline → `RESULTS.md` + `generated/*.png`

`plot_*` functions in `knicks_2026_plots.py`, wired into `main()`. Candidate charts
(one per key claim; finalize as the numbers come in):

1. Champions ranked by playoff win rate — Knicks highlighted.
2. Champions ranked by average playoff margin — Knicks highlighted.
3. East vs. West inter-conference win pct by season, 2025–26 flagged.
4. 2025–26 team SRS, colored by conference (visualizes the East/West gap).
5. Average opponent SRS faced by each champion — Knicks highlighted.
6. **Opponent-adjusted playoff dominance** ranking — Knicks highlighted (the headline).
7. Knicks per-game margin distribution (blowouts vs. close games).
8. Knicks opponent SRS by round (path strength).

Run: `MPLBACKEND=Agg python3 knicks_2026_historic.py` then `python3 generate_report.py`.

---

## Phase 4 — Write `FINDINGS.md`

Narrative referencing the numbers in `RESULTS.md` and the `generated/*` charts.
Voice and rules per `CLAUDE.md` ("Editing FINDINGS.md"): sports-magazine register,
no unexplained jargon, no stale hard-coded coefficients, every claim backed by data.

Provisional section order (mirrors the analysis arc, conclusions front-loaded):

1. **Intro + headline verdict** — state the answer up front (so readers don't bail),
   then the "but here's the catch" hook.
2. The raw case for "historic" (16–3, margins).
3. The weak-East counter-argument (conference gap, in historical context).
4. Who they actually beat (opponent quality).
5. The adjusted verdict (opponent-adjusted ranking).
6. Other explanations weighed (blowouts/clutch, era, path, rest).
7. Summary.

---

## Phase 5 — Review battery (run after a complete draft)

Run these as explicit review passes (from `project_definition.md`):

1. **Support check** — for each `FINDINGS.md` section, confirm it's backed by a
   specific `RESULTS.md` number or `generated/*` chart. Flag anything unsupported.
2. **Coherence & order** — does each section earn its place and advance the argument?
   Are sections ordered to build the case? Are the main conclusions in the intro?
3. **Readability** — flag statistics terms a general reader won't appreciate; replace
   or briefly gloss them.
4. **Adversarial fact-check** — review as a serious-publication editor whose
   reputation is on the line: every fact must match `RESULTS.md`/charts, every
   conclusion must be justified by the data. No overclaiming.

Each pass produces a punch-list; fix, regenerate the PDF, re-check.

---

## Phase 6 — Beyond nba_api (supplementary data)

Once nba_api is exhausted, ask what *else* would sharpen the answer, then fetch it in
Python (likely Basketball-Reference scraping, as the sibling `nba_home_court` does for
attendance). Candidates:

- **Opponent injuries / player availability** during the Knicks' series — the biggest
  un-measured luck factor (did they beat depleted teams?).
- **Betting-market data** (series prices / win probabilities) as a market view of how
  dominant the run "should" have looked.
- **Advanced playoff efficiency** (playoff net rating, clutch splits) if not fully
  covered by nba_api.

For each: add `fetch_*`/`compute_*`, a `plot_*`, an analysis section, update
`FINDINGS.md`, and re-run the **Phase 5** review battery.

---

## Definition of done

- `nbakit` exists; both `nba_home_court` and `knicks_2026` build on it; their reports
  and tests still pass after migration.
- Raw nba_api data lives in the single shared root cache; no project re-fetches what
  another already pulled.
- Date-robust: changing `END_YEAR`/`SUBJECT_YEAR` updates every code-generated label,
  range, and count — no hardcoded years outside `FINDINGS.md` prose.
- `RESULTS.md` regenerates from `knicks_2026_historic.py`; all charts in `generated/`.
- `FINDINGS.md` gives a clear, front-loaded, data-backed verdict on how historic the
  run was *after* adjusting for conference/opponent strength.
- Every `FINDINGS.md` claim survives the Phase 5 adversarial review.
- All computation is in Python; Claude does none of the math.
```
