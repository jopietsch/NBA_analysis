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
- 95 facts, 7 guards (all holding). `results.md` is the auto-generated source (never
  hand-edited). `facts.json` + `guards.json` are committed.
- Worktree `nbakit` shim in place (`conftest.py` per project + entry-script shims), so
  each git worktree imports its own `nbakit` — this is what makes worktree-per-doc
  parallelism safe.

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

- **Phase 1 (serial):** register the statistical-detail facts (95% CIs, p-values, R²,
  coefficients, level pp) next to their existing prints in `analysis.py`. Shared file +
  shared `facts.json`, so this is one serial pass, committed before Phase 2. ~30-50
  facts, all already computed and printed to `results.md`.
- **Phase 2 (parallel):** template each doc independently. A doc only edits its own
  `*.md.j2` and renders + byte-identical-diffs against its own committed `.md` — no
  shared-file edits, so near-zero conflict. Run as one agent per doc, or one worktree
  per doc (the shim makes this safe). **Phase 2 cannot start until Phase 1 facts exist.**

## Intentionally left literal (claims policy)

Plain-language and ranges stay as prose: "more than 40%" (deliberate round of 43%),
"one and a half boards", "two-thirds", Lakers "under 1 point", bootstrap CI bounds
("a quarter to 38%"). One genuine non-chart holdout: "8 of those points" (the altitude
regression coefficient, from a separate model) — register if/when that model is wired.
