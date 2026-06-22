Verify that every number in one or more reader-facing docs matches `docs/*_results.md`. This is the numbers-only counterpart to `/check-coherence` (argument structure) and `/voice-review` (prose style).

Scope: `$ARGUMENTS` is the doc path(s) to check. If empty, check the current project's `docs/<project>_findings.md` and `docs/<project>_summary.md`.

The source of truth is the project's results doc, `docs/*_results.md` (one per project, e.g. `home_court_results.md`; auto-generated; never edit by hand). Every figure in prose must trace back to it.

---

**Preparation — use the claim registry if it exists.**

Check whether `docs/home_court_findings_outline.md` (or the project equivalent) contains a "Key Numbers Registry" table. If it does, use it as the checklist: work through each row in order, verify the prose value against the results-doc value listed. After finishing the registry, do a free scan of the target docs for any numbers *not* in the registry.

If no registry exists, do the full free scan only (steps below).

---

**Steps:**

1. Read `docs/*_results.md` in full. Treat every number in it as correct.

2. Read each target doc in full.

3. For every number in the prose — percentage, count, ranking, margin, rate, coefficient — locate the matching row or cell in the results doc and compare. Flag every discrepancy, grouped worst-first:

   - **Wrong or stale number**: prose value does not match the results doc. Quote the prose value with its line number, quote the results-doc value and its section header.
   - **Same quantity, different values in two places**: the same metric cited with two different numbers in different sections without an explanation (e.g. two definitions, two eras). Either reconcile to one number or add a one-line note explaining the difference.
   - **Overclaim**: a statement stronger than the results doc supports — "largest in the dataset" when only a subset was measured, a causal direction when only a correlation was tested, a confidence not warranted by sample size. Quote the claim and explain what the results doc actually shows.
   - **Number present in prose but absent from the results doc**: flag it; it may be fabricated or sourced elsewhere.

4. For each flag: quote the prose phrase with its line number, state the conflict, propose a specific rewrite.

5. Present the review grouped worst-first. State explicitly what you verified as correct. Do NOT edit yet.

6. Ask whether to apply. On confirmation, apply the edits, then run `/regen` (or `bash /Users/justin/code/nba_analysis/questions/regen_docs.sh`) from the project root. Before regenerating, double-check each changed number against the results doc one more time.

**Note:** this skill does not change the results doc. If prose is correct and the results doc looks wrong, the fix is in the analysis code — re-run the pipeline.
