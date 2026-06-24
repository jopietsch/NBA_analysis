Run all three reader-facing doc reviews at once: numbers (`/check-consistency`), argument structure (`/check-coherence`), and prose style (`/voice-review`). Each review's find-and-flag phase runs in its own parallel subagent and returns only a findings list; you merge the three lists, gate the edits once, apply once, and regenerate once.

Use this when you want to review a doc on all three axes together (the common case). To run just one axis, use the standalone `/check-consistency`, `/check-coherence`, or `/voice-review` instead.

Scope: `$ARGUMENTS` is the doc path(s) to review. If empty, review the current project's `docs/<project>_findings.md` and `docs/<project>_summary.md`. The stats-tier docs (`*_investigation.md`, `*_stats_explainer.md`, `stats_tutorial.md`) are reviewed when passed explicitly; each skill routes on filename and applies the right tier's checks, so no extra flags are needed here.

This command does NOT restate each review's rules. Each subagent reads the relevant skill file and follows it, so the three reviews can never drift from their standalone versions. Because the skills are tier-aware, this command needs no per-tier logic of its own — the only thing that changes by tier is the model you assign the consistency agent (next step).

---

**Steps:**

1. **Resolve the target docs.** Use `$ARGUMENTS` if given, else the project's findings + summary. Confirm the paths exist before fanning out.

2. **Fan out — spawn three subagents in parallel** (all three `Agent` calls in a single response). Each is read-only: it finds and flags, it does NOT edit any file. Each gets a model matched to its cognitive load (set the `Agent` `model` parameter). Give each one the resolved doc paths and the matching instruction:

   - **Coherence agent** (`general-purpose`, `model: opus`): "Read `questions/.claude/commands/check-coherence.md` and execute its flag phase against these docs: <paths>. Run every step up to and including presenting the findings, but STOP before applying — do not edit any file, do not run regen. Return only your findings list, grouped worst-first exactly as the skill specifies." Opus because this is whole-document reasoning (intro-vs-body contradictions, silent body-vs-body conflicts), the hardest of the three.
   - **Consistency agent** (`general-purpose`, `model: sonnet`): same wording, pointed at `check-consistency.md`. Sonnet because it is mechanical number-matching against the results doc, checklist-driven when a Key Numbers Registry exists. **Bump to `model: opus` when any target is `*_stats_explainer.md` or `stats_tutorial.md`**: those tiers add method-fidelity (the named estimator must match `*_analysis.py`) and, for the tutorial, recomputing worked arithmetic — reasoning work, not number-matching. If a pass ever looks doubtful, re-run just this one on `model: opus`.
   - **Voice agent** (`general-purpose`, `model: sonnet`): same wording, pointed at `voice-review.md`. Sonnet because it is mostly pattern-matching against the translation table; bump to `opus` only if you want sharper calls on the subjective drama / generated-prose checks.

   Each subagent returns just its findings list. Only the consistency agent should open `*_results.md`; the other two work from prose alone, per their skill files.

3. **Merge the three lists.** Group first by document, then by line/region within the doc, so flags that touch the same sentence sit together (a voice rewrite and a consistency fix on one line should be reconciled into a single proposed edit, not applied twice). Within each region, order by severity worst-first. Label every flag with its source review (consistency / coherence / voice) so the reasoning is traceable.

4. **Present the merged review.** State explicitly what each review verified as clean, not only what's wrong. Do NOT edit yet.

5. **Gate once.** Ask whether to apply. If the user wants only a subset, apply only those.

6. **Apply once, in the main thread.** Make all confirmed edits. Reconcile overlapping flags into one coherent edit per region rather than stacking changes. Before saving any changed number, re-check it against `*_results.md` one more time (per the consistency skill's caution).

7. **Regenerate once.** Run `/regen` (or `bash /Users/justin/code/nba_analysis/questions/regen_docs.sh`) a single time from the project root, after all edits land — not once per review. Report which files were saved and flag any errors. If the findings doc changed, follow any project-specific cascade in the project's own `CLAUDE.md` (e.g. updating a findings outline and regenerating its PDF).

**Note:** none of this changes `*_results.md`. If prose is correct and the results doc looks wrong, the fix is in the analysis code — re-run the pipeline.
