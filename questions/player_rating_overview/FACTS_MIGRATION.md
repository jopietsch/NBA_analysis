# Facts / template migration — status

Internal dev note (not a report doc; not picked up by `generate_report.py`).

## The model

The analysis registers every cited number as a named **fact**
(`player_rating_overview_facts.py`, `FACTS.set`) and every qualitative claim as a
**guard** (`FACTS.guard`), both inside `run()` in
`player_rating_overview_analysis.py`, next to the `print(...)` that emits the same
value. `FACTS.dump` / `FACTS.dump_guards` run at the end of `run()`, writing
`docs/player_rating_overview_facts.json` and `docs/player_rating_overview_guards.json`
(both committed).

Reader-facing docs are Jinja templates (`docs/*.md.j2`) using `<< f("name") >>`
delimiters; `render_docs.py` fills them to `docs/*.md`, and `render_all()` is called at
the top of `generate_report.py`.

## Status — DONE

All seven reader-facing docs render from facts; `results.md` stays the untemplated
auto-generated source.

- **236 facts, 6 guards** (all holding).
- Templated, render byte-identical to the pre-migration committed docs:
  `findings.md` (21 facts), `findings_outline.md` (54), and five docs that carry no
  pipeline-derived numbers and so contain zero `f()` calls but still render through the
  one path: `summary.md`, `investigation.md`, `stats_explainer.md`, `inventory.md`,
  `player_rating_resources.md`.
- The plan flagged "4 wrong findings numbers" vs `results.md`; on the current run these
  were a precision artifact, not errors: `corr.WS_WS48` (0.6954) and `corr.PER_WS`
  (0.7593) both display as `0.70` / `0.76` at the 2-decimal precision the prose uses, so
  the render is byte-identical. They are now single-sourced from facts. The consensus
  top-5 list and the top-5% share roundings (WS ~15%, VORP ~32%) already matched the
  data.

## The list-fact pattern (Option A)

Ranked lists (consensus top, wins-predictive top, who-each-system-loves/discounts) use
**per-item scalar facts**, not list-valued Facts, so the scalar cross-check and
`--annotate` work unchanged:

- `consensus.top.{1..5}.name` / `.z`, `wins_pred.top.{1..5}.name` / `.z` (top 5 only —
  the ranks the prose actually cites).
- `loves.{SYS}.{1..3}.{name,diff}` and `discounts.{SYS}.{1..3}.{name,diff}` (8 systems).

## ALLOW_ABSENT

- `cov.n_systems` (= 8): a single digit filtered by the candidate-string search; the
  forms `8.0` / `+8` don't appear verbatim in the `Rating systems present: 8` line.

## Intentionally-literal numbers (not facts)

Definitional formula constants (Game Score / PER / BPM 2.0 / VORP coefficients, ridge
α, Gini and skewness thresholds, Spearman ±1 range), external-citation figures
(`29 execs`, `8 votes`, survey years), method constraints (`>= 500 min`, `30 teams`),
illustrative hypotheticals, and `121 steals` / section-9 player names with no matching
fact. Covered by `/check-consistency`, not the cross-check guard test.

## Pending regeneration (third-party systems)

The current run has **8 of the planned 10** systems (DARKO, EPM, LEBRON, RAPTOR,
ESPN_RPM await manual CSVs). When they land, `facts.json` must be regenerated **and**
every `.md.j2` citing a correlation pair or a consensus / wins-predictive top list must
be re-reviewed: the 28 Spearman pairs expand to ~45 and the top-20 lists reorder. The
guard tests (`test_facts_match_results.py`, `test_prose_claims.py`) flag direction /
value drift automatically; stale magnitude words need a human `/review-all` pass.

## Tests

`tests/test_player_rating_overview_facts.py`, `tests/test_render_docs.py`,
`tests/test_facts_match_results.py`, `tests/test_prose_claims.py`. Full `pytest`: 36
passing.
