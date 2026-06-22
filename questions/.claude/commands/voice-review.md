Review one or more reader-facing docs for voice and plain-language problems. This is the deep on-demand pass that complements the `voice_check.py` hook: the hook only flags hard jargon on save, while this also catches drama, em-dashes, overstated causation, and generated-sounding prose.

Scope: `$ARGUMENTS` is the doc path(s) to review. If empty, review the current project's `docs/<project>_findings.md` and `docs/<project>_summary.md` (the standard doc names from `questions/CLAUDE.md`).

Pick the standard by filename (see the audience-tier table in `questions/CLAUDE.md`):
- `*_findings.md` / `*_summary.md` — general reader: strip statistical jargon to plain language.
- `*_stats_explainer.md` / `stats_tutorial.md` — stats-literate but rusty: do NOT strip the real terms; instead check they are used correctly and defined/refreshed on first use.
- the results doc — never hand-edit; stat language is correct there. Decline to "fix" it.

Steps:
1. Read `questions/CLAUDE.md` — the sections "Audience tiers", the plain-language translation table, "No em-dashes", "No drama, no exaggeration", and "Write like a person". That is the rubric; do not invent rules.
2. Read each target doc in full.
3. Flag every issue, grouped worst-first by category:
   - **Statistical jargon** a general reader would stumble on; give the replacement from the translation table. Ignore stat terms inside link/image URLs, chart filenames, and the companion-doc tables (a link to "Regression Results" is not prose jargon).
   - **Em-dashes** (banned everywhere).
   - **Drama / exaggeration** not backed by the data: superlatives, emotional amplifiers, rhetorical buildup. Overstated causation where only association was shown.
   - **Generated-sounding prose**: filler openers ("It is worth noting"), filler transitions ("moreover"), summarizing closers that restate the prior sentence, monotone rhythm, vague abstractions where a concrete number belongs.
   - Leave real NBA stats as-is (eFG%, net rating, pace, Four Factors, OREB%); do not flag these.
4. For each flag, quote the phrase with its line number, say briefly why it's a problem, and propose a specific rewrite.
5. Present the review grouped by severity. Do NOT edit yet.
6. Ask whether to apply. On confirmation, apply the edits, then regenerate the affected output following the project's "Standard document workflow" and cascade rules in `questions/CLAUDE.md`: findings → `python3 generate_report.py`; any other standalone doc → `python3 generate_doc_pdf.py docs/<file>.md`. If the findings changed, also follow any project-specific cascade in the project's own `CLAUDE.md` (e.g. updating a findings outline and regenerating its PDF).
