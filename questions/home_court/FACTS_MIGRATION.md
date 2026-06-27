# Facts / template migration — status & plan

Internal dev note (not a report doc; not picked up by `generate_report.py`).

## The model

The analysis registers every cited number as a named **fact** (`home_court_facts.py`,
`FACTS.set`) and every qualitative claim as a **guard** (`FACTS.guard`). The pipeline
dumps `docs/home_court_facts.json` (the data model) and `docs/home_court_guards.json`.
Reader-facing docs are Jinja templates (`docs/*.md.j2`) using `<< f("name") >>`
delimiters (so Quarto brace attributes pass through); `render_docs.py` fills them to
`docs/*.md`. `run()` re-checks guards on every pipeline run and warns which claim broke.

Single source: a number is computed once, formatted once, and appears identically in
every doc. Chart-sourced numbers register from the same `compute_*` the plot uses, so
chart and prose can't diverge.

## Status (done)

- `findings.md` + `summary.md`: fully converted, render byte-identical, committed.
- **Phase 1 complete:** registered investigation.md's statistical detail end to end
  (decline slope/CI/p/R², mediation level + four-factor CIs + per-channel decline CIs,
  channel trends, 3PA bivariate/within-era effects + CIs, the 1994-95 fingerprint
  (era p + event-study jumps), travel CIs, back-to-back detail, referee BH count,
  rebounding 3PA-absorption + p + league-OREB corr, altitude effect, change-point year +
  HPD). Every value spot-checked against the doc. **190 facts, 7 guards (all holding).**
- `f("name", "{:.2f}")` precision override added so denser docs reuse a fact's raw value
  at higher precision without duplicates.
- `results.md` is the auto-generated source (never hand-edited). `facts.json` +
  `guards.json` are committed.
- Worktree `nbakit` shim in place (`conftest.py` per project + entry-script shims), so
  each git worktree imports its own `nbakit` — this is what makes worktree-per-doc
  parallelism safe.

## Phase 2 status (parallel, in progress)

Ran four parallel worktree subagents. Results:
- **investigation.md: DONE** (committed). 111 substitutions; byte-identical except two
  intended reconciliations (po.slope 0.22->0.23, a playoff p `<0.01`->`=0.004`). It is now
  the best **stats-tier** worked example to copy.
- **stats_tutorial.md: DONE** (committed) + wired into `render_all()` (it lives in the
  parent dir but renders from these facts). Byte-identical.
- **Review tooling: DONE** (committed) — `render_docs.py --watch | --reference | --annotate`.
- **stats_explainer.md: DONE where shared facts exist** (75 substitutions). A retry
  subagent (committing incrementally) + a manual finish templated every number that maps
  to an existing fact. The remaining numbers are **method-specific statistics** cited only
  here (structural-break F, CUSUM, ITS coefficients, Granger, pace, parity, win-margin,
  net-rating eras, shrunken franchise HCA, multiple-comparisons) — never registered as
  facts. Those stay literal and are covered by the updated `/check-consistency` (literal
  check) + the cross-check test. Fully single-sourcing them would mean ~150 single-use
  facts across ~20 functions — deferred as low-value.
- **All five reader-facing docs now render byte-identical from facts.** 208 facts, 7
  guards, 250 tests pass. Review tooling, the dual-write cross-check test
  (`tests/test_facts_match_results.py`), and the updated `/check-consistency` skill are in.
- `results.md`-from-facts (#3) was **declined** — render + cross-check already cover the
  high-stakes cases; the ~80-edit retrofit wasn't worth it for the small-int edge.

Lessons for the explainer redo: (1) the byte-identical render gate does NOT catch
*under*-templating (a literal number trivially matches itself) — drive completeness with a
literal-token grep and `--annotate`. (2) Commit incrementally so a stall doesn't lose work.

## Known Phase-2 reconciliations (facts now correct; docs to update on templating)

- `po.slope` renders -0.23 (the -0.225 GLM value); investigation.md currently says 0.22.
- p-value display: some facts render `= 0.004` where the doc wrote `< 0.01`; pick one
  convention when templating.
- altitude `27/26` already corrected to `28/27` and detrend `40% -> 42%` in findings
  (the system catching stale figures); investigation may have parallel figures to refresh.

## Tooling to build (DON'T FORGET) — do before/with Phase 1

These keep template-editing and review comfortable; they also help review what's
already converted:

1. **`render_docs.py --watch`** — re-render on save (edit template -> see real numbers
   instantly).
2. **Generated `facts_reference.md`** — every fact as `name -> value -> note`, the
   lookup while writing.
3. **Annotate render mode** — render each number with its fact name inline
   (`-0.24 [reg.slope]`) for review: verify the *right* fact is wired, not just that a
   number appears. This is the answer to "how do I review a template-driven stats doc."

## Remaining docs (Phase 2 candidates)

| Doc | ~Numbers | Notes |
|---|---|---|
| `investigation.md` | ~140 | Highest value. Reuses many facts; needs CIs + p-values (Phase 1). Do first as the stats-tier pattern proof. |
| `stats_explainer.md` | ~390 | Large; method values must match `results.md`. |
| `stats_tutorial.md` (parent dir) | ~560 | Worked arithmetic; template inputs/outputs, leave illustrative steps. |
| `findings_outline.md` | ~660 | Internal, 660-number cross-reference. **Decide: template vs auto-generate from facts.json** (generating may retire it as a hand-maintained doc). |
| `question_summaries.md` | ~19 | Small; do for free. |

## Phasing

- **Phase 1 (serial): DONE.** Registered the statistical-detail facts (95% CIs,
  p-values, R², coefficients, level pp) next to their existing prints in `analysis.py`,
  driven by investigation.md (the densest stats doc). Committed.
- **Phase 2 (parallel): READY.** Template each doc independently. A doc only edits its
  own `*.md.j2` and renders + byte-identical-diffs against its own committed `.md` — no
  shared-file edits, so near-zero conflict. Run as one agent per doc, or one worktree
  per doc (the shim makes this safe). Start with `investigation.md` (its facts are all
  registered); explainer/tutorial reuse most of them and add a few of their own.

## Intentionally left literal (claims policy)

Plain-language and ranges stay as prose: "more than 40%" (deliberate round of 43%),
"one and a half boards", "two-thirds", Lakers "under 1 point", bootstrap CI bounds
("a quarter to 38%"). One genuine non-chart holdout: "8 of those points" (the altitude
regression coefficient, from a separate model) — register if/when that model is wired.
