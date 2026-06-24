Review one or more reader-facing docs for voice and plain-language problems. This is the deep on-demand pass that complements the `voice_check.py` hook: the hook only flags hard jargon on save, while this also catches drama, em-dashes, overstated causation, and generated-sounding prose.

Scope: `$ARGUMENTS` is the doc path(s) to review. If empty, review the current project's `docs/<project>_findings.md` and `docs/<project>_summary.md` (the standard doc names from `questions/CLAUDE.md`).

Pick the standard by filename (see the audience-tier table in `questions/CLAUDE.md`). Each tier flips what counts as a problem, so route first, then apply only that tier's checks:
- `*_findings.md` / `*_summary.md` — general reader: strip statistical jargon to plain language (translation table).
- `*_investigation.md` — **middle tier**: strip the same jargon as findings, with ONE exception — p-values, significance stars, and confidence intervals are allowed and expected here. Do NOT flag them as jargon. DO flag: (a) a p-value or CI used before the "How to read the numbers" box defines it; (b) a p-value reported with no CI beside it (this tier pairs them); (c) explainer-tier method-speak that slipped down a tier ("coefficient", "OLS", "logistic", "heteroskedastic", estimator names) — name what was tested and what it showed instead.
- `*_stats_explainer.md` / `stats_tutorial.md` — stats-literate but rusty: do NOT strip the real terms. Instead check, in order: (a) **term-before-definition** — every method/term (binomial GLM, cluster-robust SE, QLR, bootstrap, CI) is defined or reminded on first use, and never used earlier than that; (b) **method named correctly** — the term matches the actual procedure (don't call an LPM a logit, don't call HAC "clustering"); (c) **jargon load right for "rusty"** — not dumbed down to sports-reader level, but not piling on unreminded jargon either. (Whether the named method matches what the *code* ran is method-fidelity — that belongs to `/check-consistency`, not here; note it but don't chase it.)
- the results doc — never hand-edit; stat language is correct there. Decline to "fix" it.

Steps:
1. Read `questions/CLAUDE.md` — the sections "Audience tiers", the plain-language translation table, "No em-dashes", "No drama, no exaggeration", and "Write like a person". That is the rubric; do not invent rules.
2. Read each target doc in full.
3. Flag every issue, grouped worst-first by category. The first category is tier-dependent (use the routing above); the rest apply to every tier:
   - **Tier-fit** — for findings/summary/investigation: **statistical jargon** a general reader would stumble on; give the replacement from the translation table (but on investigation, p-values/stars/CIs are not jargon — see routing). For explainer/tutorial: **term-before-definition** and **method-named-wrong**, per the routing, not jargon-stripping. Ignore stat terms inside link/image URLs, chart filenames, and the companion-doc tables (a link to "Regression Results" is not prose jargon).
   - **Em-dashes** (banned everywhere).
   - **Drama / exaggeration** not backed by the data: superlatives, emotional amplifiers, rhetorical buildup. Overstated causation where only association was shown.
   - **Generated-sounding prose**: filler openers ("It is worth noting"), filler transitions ("moreover"), summarizing closers that restate the prior sentence, monotone rhythm, vague abstractions where a concrete number belongs.
   - Leave real NBA stats as-is (eFG%, net rating, pace, Four Factors, OREB%); do not flag these.
4. For each flag, quote the phrase with its line number, say briefly why it's a problem, and propose a specific rewrite.
5. Present the review grouped by severity. Do NOT edit yet.
6. Ask whether to apply. On confirmation, apply the edits, then regenerate the affected output following the project's "Standard document workflow" and cascade rules in `questions/CLAUDE.md`: findings → `python3 generate_report.py`; any other standalone doc → `python3 generate_doc_pdf.py docs/<file>.md`. If the findings changed, also follow any project-specific cascade in the project's own `CLAUDE.md` (e.g. updating a findings outline and regenerating its PDF).
