# MODEL_USAGE.md — Model and Effort Choices for Implementing PLAN-STATS.md

Notes from the June 2026 discussion on which Claude model and effort setting
to use when implementing `PLAN-STATS.md`. The short version: the plan was
written to be over-specified precisely so a cheaper model or lower effort can
execute most of it — concentrate the expensive capability on the items where
errors are silent and on every FINDINGS rewrite.

These notes reference each analysis by name rather than by section number,
because `home_court_FINDINGS.md` and `home_court_results.md` get reordered as the report evolves and
fixed numbers go stale.

## Pricing context (as of June 2026)

| Model | Input $/MTok | Output $/MTok | Notes |
|---|---|---|---|
| Claude Fable 5 (`claude-fable-5`) | $10 | $50 | New tokenizer counts ~30% more tokens for the same content, so the effective gap vs. Sonnet is roughly 4× |
| Claude Opus 4.8 (`claude-opus-4-8`) | $5 | $25 | Middle ground |
| Claude Sonnet 4.6 (`claude-sonnet-4-6`) | $3 | $15 | Best speed/cost balance |

Fable also works in longer, more deliberate turns — cost and wall-clock both
favor smaller models for mechanical work.

## The deciding principle

The failure mode in this codebase is not code that crashes — it is code that
runs and prints plausible-looking wrong numbers. The referee foul-bias t-test
bug ran cleanly for months, produced significance stars in every row, and
propagated into published FINDINGS prose. Model capability matters exactly where
that silent-failure shape exists, and on the prose steps where claims must be
calibrated to evidence. It matters much less where the plan already specifies
the formula, the file, and the acceptance criteria.

## Model assignment by batch

| PLAN-STATS batch | Risk shape | Model |
|---|---|---|
| Batch 1 (referee t-test fix, variance decomposition / shrinkage) | Conclusion genuinely in play; silent-failure math (shrinkage weights, variance floors) | Fable 5, or Opus 4.8 to economize |
| Batch 2 (quantile regression, Shapley decomposition) | Interpretation drives the margin-polarization and combined situational-vs-era rewrites; combinatorial bookkeeping | Fable 5, or Opus 4.8 |
| Batch 3 (inference upgrades + confidence intervals) | Tightly specified; conclusions probably hold | Sonnet 4.6 is fine |
| Batch 4 (perimeter / situational analyses + cluster-SE sweep) | Mostly one-line changes copying existing patterns | Sonnet 4.6 is fine |

Watch the leave-one-out expected-pace item inside Batch 3 — it has the silent
leakage-risk shape even though the batch is otherwise mechanical.

**Alternative pattern:** implement everything on Sonnet, then have Fable (or
Opus) review the diffs and the FINDINGS edits. Review costs a fraction of
implementation and catches exactly the silent-wrong-number class of error.

**Consistency rule:** whichever model implements, keep it consistent within a
batch — the end-of-batch FINDINGS rewrite needs the context of what the
numbers came out to be. Don't switch models mid-batch.

## Effort settings (when staying on Fable 5)

Effort (`/model` in Claude Code) is arguably the better lever than model
switching: it tunes depth and cost per batch while keeping one model's
context, which sidesteps the mid-batch-switch problem entirely.

| Work | Effort | Why |
|---|---|---|
| Batches 3–4 implementation | `medium` | The plan did the thinking; lower effort means fewer, more consolidated tool calls. High effort on routine work risks over-exploration and unrequested tidying at Fable prices. |
| Batches 1–2 | `high` | The benefit is verification behavior: rechecking shrinkage weights by hand, sanity-checking that the Shapley fits sum correctly, noticing when a quantile slope contradicts the prose it's about to support. |
| Every end-of-batch FINDINGS rewrite | `high` | Translating new numbers into prose claims is judgment work — it's where all the overclaiming was found. Bump up even if the batch ran at `medium`. |
| `xhigh` / `max` | Skip by default | They earn their cost on open-ended, underspecified problems; PLAN-STATS is deliberately the opposite. Exception: a Batch 1 result that collapses the existing narrative (e.g. negative true variance in most eras) and needs a from-scratch rethink rather than plan execution. |

Two practical notes:

- Higher effort up front sometimes *reduces* total cost on multi-step work by
  cutting turn count and rework. If a `medium` run starts thrashing, switch to
  `high` and redo cleanly rather than letting it iterate.
- Fable at lower effort still performs very well — often exceeding the
  highest-effort performance of previous-generation models — so `medium` on
  the mechanical batches is not a quality concession.
