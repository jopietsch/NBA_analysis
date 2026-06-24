Verify that every number in one or more reader-facing docs matches `docs/*_results.md`. This is the numbers-only counterpart to `/check-coherence` (argument structure) and `/voice-review` (prose style).

Scope: `$ARGUMENTS` is the doc path(s) to check. If empty, check the current project's `docs/<project>_findings.md` and `docs/<project>_summary.md`. It also runs on the stats-tier docs when passed explicitly: `*_investigation.md`, `*_stats_explainer.md`, and `stats_tutorial.md` (which lives at `questions/`, not under `docs/`).

The source of truth is the project's results doc, `docs/*_results.md` (one per project, e.g. `home_court_results.md`; auto-generated; never edit by hand). Every figure in prose must trace back to it.

**The depth of the check is tier-dependent** (route by filename, see the audience-tier table in `questions/CLAUDE.md`):
- `*_findings.md` / `*_summary.md` — point estimates only; these docs mostly avoid p-values and CIs.
- `*_investigation.md` — point estimates **plus CI bounds plus p-values / significance stars**. This tier reports the full evidence, so a CI cited as `[+11, +28]%` or a `p = 0.007` must match the results row exactly, and a claim's direction (negative/positive, "significant"/"not") must match.
- `*_stats_explainer.md` — everything above, **plus method fidelity**: the named estimator or test ("binomial GLM", "cluster-robust SE by season", "QLR / supremum Chow", "linear-probability model") must match what the pipeline actually runs. Source of truth for method fidelity is the analysis code (`*_analysis.py`), cross-checked against the results-doc section headers, not the results numbers alone. A described method the code never runs is the most serious flag in this tier.
- `stats_tutorial.md` — everything above, **plus recompute**: each worked example shows intermediate arithmetic (e.g. an SE from `sqrt[p·q·(1/n₁ + 1/n₂)]`). Recompute every step, confirm it is internally correct, and confirm it lands on the matching `*_results.md` value. A worked example that is self-consistent but ends on a number absent from the results doc is still a flag.

---

**Preparation — use the claim registry if it exists.**

Check whether `docs/home_court_findings_outline.md` (or the project equivalent) contains a "Key Numbers Registry" table. If it does, use it as the checklist: work through each row in order, verify the prose value against the results-doc value listed. After finishing the registry, do a free scan of the target docs for any numbers *not* in the registry.

If no registry exists, do the full free scan only (steps below).

---

**Steps:**

1. Read `docs/*_results.md` in full. Treat every number in it as correct. If any target is `*_stats_explainer.md` or `stats_tutorial.md`, also read `*_analysis.py` (the analysis code is the source of truth for *which method* was run, which the results doc only shows the output of).

2. Read each target doc in full.

3. For every number in the prose — percentage, count, ranking, margin, rate, coefficient — locate the matching row or cell in the results doc and compare. Flag every discrepancy, grouped worst-first:

   - **Wrong or stale number**: prose value does not match the results doc. Quote the prose value with its line number, quote the results-doc value and its section header.
   - **Same quantity, different values in two places**: the same metric cited with two different numbers in different sections without an explanation (e.g. two definitions, two eras). Either reconcile to one number or add a one-line note explaining the difference.
   - **Overclaim**: a statement stronger than the results doc supports — "largest in the dataset" when only a subset was measured, a causal direction when only a correlation was tested, a confidence not warranted by sample size. Quote the claim and explain what the results doc actually shows.
   - **Number present in prose but absent from the results doc**: flag it; it may be fabricated or sourced elsewhere.
   - **CI / p-value mismatch** (investigation, explainer, tutorial): a confidence-interval bound or a p-value / significance star that doesn't match the results row, or a "significant" / "not significant" / direction claim that the row contradicts. A p-value cited with no CI beside it in `*_investigation.md` is a tier-fit flag, not a number flag — note it for `/voice-review`.
   - **Method-fidelity mismatch** (explainer, tutorial): the named estimator or test does not match what `*_analysis.py` runs for that section. Quote the method phrase, name what the code actually does. This is the most serious flag in these tiers.
   - **Worked-example recompute error** (tutorial only): an intermediate arithmetic step is wrong, or a self-consistent worked example lands on a value not in the results doc. Show the recomputed value and the step that breaks.

4. For each flag: quote the prose phrase with its line number, state the conflict, propose a specific rewrite.

5. Present the review grouped worst-first. State explicitly what you verified as correct. Do NOT edit yet.

6. Ask whether to apply. On confirmation, apply the edits, then run `/regen` (or `bash /Users/justin/code/nba_analysis/questions/regen_docs.sh`) from the project root. Before regenerating, double-check each changed number against the results doc one more time.

**Note:** this skill does not change the results doc. If prose is correct and the results doc looks wrong, the fix is in the analysis code — re-run the pipeline.
