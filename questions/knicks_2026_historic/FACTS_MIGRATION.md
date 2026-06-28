# Facts / template migration — status

Internal dev note (not a report doc; not picked up by `generate_report.py`).

## The model

The analysis registers every cited number as a named **fact**
(`knicks_2026_facts.py`, `FACTS.set`) and every qualitative/directional claim as a
**guard** (`FACTS.guard`). Registration lives next to the `print(...)` that emits the
same value inside each `run_*(out)` function in `knicks_2026_analysis.py`; the dumps
(`FACTS.dump` / `FACTS.dump_guards`) run at the end of `main()`. The pipeline writes
`docs/knicks_2026_historic_facts.json` and `docs/knicks_2026_historic_guards.json`
(both committed).

Reader-facing docs are Jinja templates (`docs/*.md.j2`) using `<< f("name") >>`
delimiters (so Quarto's `{{`/`{%`/`{#` pass through). `render_docs.py` fills them to
`docs/*.md`; `render_all()` is called at the top of `generate_report.py` so the report
build always re-renders first. Single source: a number is computed once, formatted
once, and renders identically in every doc.

## Status — DONE

All five reader-facing docs render from facts; `results.md` stays the untemplated
auto-generated source.

- **232 facts, 13 guards** (all holding).
- Templated, render byte-identical to the pre-migration committed docs:
  `findings.md` (99 facts), `summary.md` (34), `investigation.md` (53),
  `stats_explainer.md` (~103 references), `findings_outline.md` (42).
- One intended correction during the migration: `stats_explainer.md` §5 cited the
  headline adjusted-margin chart annotation as `+11.4`; the chart annotates
  `adj_margin` = `+11.2` (the `+11.4` is the Bradley–Terry-adjusted value, correctly
  used in §16). Now single-sourced from `adj.margin`.
- `f("name", "{:.2f}")` precision overrides used where denser docs reuse a fact's raw
  value at higher precision; `|tm` converts ASCII hyphen to typographic minus.

## ALLOW_ABSENT

Empty. Every numeric fact appears verbatim in `results.md`.

## Intentionally-literal numbers (not facts)

Left literal by policy (editorial roundings, derived combinations not separately
registered, structural constants). Covered by `/check-consistency` (literal check),
not the cross-check guard test:

- Editorial roundings: `~4%` pace, "about a third", "six or seven games", win rates
  written in sport convention (`.842`, `.941`).
- Derived combinations cited once: per-round W-L records (`4-2`, `4-0`, …); per-opponent
  SRS dips (`gap -1.16`, `+6.2` Spurs rise); `+8.99` (1986–87 Lakers, #2 by playoff
  adj-margin — no `adj_po.top2.margin` fact); `+3.54` unique-opponent avg SRS;
  competitor pace-adjusted values.
- Structural / definitional: season labels (`2025–26`, `1986–87`), `82 games`,
  `20,000 re-draws`, section numbers, formula constants.

A handful of these (e.g. `adj_po.top2.margin`, `opp.srs_unique`) could be backfilled to
the pipeline to reduce literals; deferred as low-value single-use numbers.

## Tests

`tests/test_knicks_2026_facts.py` (Fact/Facts class behavior),
`tests/test_render_docs.py` (render smoke), `tests/test_facts_match_results.py`
(every numeric fact present in `results.md`), `tests/test_prose_claims.py` (every guard
`ok: true`). Full `pytest`: 77 passing.
