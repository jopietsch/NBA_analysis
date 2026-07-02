Audit the argument structure of one or more reader-facing docs: do the sections agree with the intro, does the summary cover the findings, and is the reasoning internally consistent? This is the structure-and-logic counterpart to `/check-consistency` (numbers vs. the results doc) and `/voice-review` (prose style).

This skill does NOT open `docs/*_results.md`. It works entirely within the prose documents. If you find a number that looks suspicious, note it for `/check-consistency` to verify — do not chase it here.

Scope: `$ARGUMENTS` is the doc path(s) to check. If empty, check the current project's `docs/<project>_findings.md` and `docs/<project>_summary.md`. Also runs on `*_investigation.md`, `*_stats_explainer.md`, and `stats_tutorial.md` when passed explicitly (see the stats-tier note in step 6). If the project has an article series (`docs/<project>_series.md` plus `docs/<project>_article_*.md`), pass all of them explicitly as a set: each article is a recut of a findings section, so treat the series hub like an intro/contract and each article like a body section when checking intro-vs-body and cross-reference consistency.

---

**Steps:**

1. Read each target doc in full. For a facts/template doc (a sibling `docs/<doc>.md.j2` exists, rendered into the `.md` by `generate_report.py` / `render_docs.py` filling each `<< f("name") >>` from `docs/*_facts.json`), read **both**: judge the argument against the real numbers the reader sees in the rendered `.md`, and open the `.md.j2` to see where an edit must land (literal text vs. a `<< f(...) >>` token). Coherence claims that hinge on a magnitude or direction ("X drove the decline", "barely moved") can only be checked against the rendered value, so you must see it.

2. **Extract the intro's headline claims.** The intro (everything before the first `##` section) is the contract: it tells the reader what the report will establish. List every headline claim — the answer to each stated question, every "X drove the decline," every "Y did not." These are the promises the body must keep.

3. **Check intro vs. body.** For each intro claim, find the section that develops it. Flag every mismatch:
   - Intro claims X; the relevant section's conclusion is not-X or weaker than X.
   - Intro claims four drivers; only three are substantiated in the body.
   - Intro says "ruled out"; the relevant section hedges or contradicts.
   - Intro uses causal language ("drove," "caused"); the relevant section only shows association. Or vice versa.

4. **Check body sections against each other.** Read each `##` section's opening claim and closing conclusion. Flag:
   - Two sections that reach contradictory conclusions about the same quantity or factor.
   - A "what didn't drive it" section that contradicts something a driver section claimed.
   - A later section that relies on a finding from an earlier section without acknowledging it, or contradicts it silently.

5. **Check the summary against the full document** (summary docs only). The summary must be independently coherent and agree with both the intro and the body:
   - Every headline claim in the summary must appear in the intro and be supported by the body.
   - Every major finding from the body must either appear in the summary or be explicitly drop-able for a one-pager (secondary detail, not a headline result). Flag genuine gaps — findings that belong in the summary but are missing.
   - If the summary states a direction, magnitude, or conclusion that differs from the body, flag it. These are the most damaging errors because readers of the summary never see the correction.

6. **Check the core questions and the document arc.** Most projects here are question-driven reports built on the arc in `questions/CLAUDE.md` ("Document arc for question-driven reports"): the intro states the project's questions in bold and front-loads their answers, the body develops one section per question in that order, and the summary re-answers the same set. Find the project's question set (the project's `CLAUDE.md` is the source of truth for how many there are; e.g. home court has four: (1) has it changed? (2) what makes it up? (3) what drove the change? (4) what did NOT contribute, even though people assume it did?). Verify each question is stated in the intro, developed in at least one body section, and reflected in the summary, all in a consistent order. Flag any question that goes unanswered, is answered differently in two places, or appears in the body but never in the intro/summary (a broken contract). If the doc clearly isn't question-driven, skip this check rather than forcing the structure.

   **For stats-tier docs** (`*_investigation.md`, `*_stats_explainer.md`, `stats_tutorial.md`), coherence also means **method consistency across sections**: a method named or described one way in one section must not be described incompatibly in another (e.g. a result called a "trend line / OLS" in one place and a "logistic regression" in another for the same analysis). Flag the conflict; whether either name matches the *code* is method-fidelity and belongs to `/check-consistency`, so note it but don't chase it here.

7. **Check cross-references.** Every `§N` pointer must resolve to a section that exists and says what the pointer claims. Section numbers must be sequential with no gaps or repeats.

8. For each flag: quote the conflicting phrases with line numbers, name the conflict (intro vs. §N, §N vs. §M, body vs. summary), and propose a specific rewrite or note.

9. Present the review grouped worst-first:
   - **Intro-vs-body contradictions** (most damaging — the report doesn't deliver what it promises)
   - **Body-vs-body contradictions** (internal inconsistency)
   - **Summary gaps or contradictions** (mislead readers who only read the short version)
   - **Broken cross-references**
   - Minor mismatches (hedge-level differences, framing inconsistencies)

   State explicitly what you verified as coherent, not just what's wrong.

10. Do NOT edit yet. Ask whether to apply. On confirmation, apply the edits, then run `/regen` (or `bash /Users/justin/code/nba_analysis/questions/regen_docs.sh`) from the project root, which renders every `.md.j2` before rebuilding PDFs/HTML. For a facts/template doc, edits go in the `.md.j2`, **not** the rendered `.md` (the render overwrites it); when you reword a sentence that contains a `<< f(...) >>` token, keep the token in place so the number still fills from the data model.
