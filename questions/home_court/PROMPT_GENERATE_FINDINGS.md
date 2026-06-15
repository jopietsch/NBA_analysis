# Prompt: Generate FINDINGS.md from Scratch

Use this prompt in a fresh Claude Code session when FINDINGS.md does not exist
or needs to be rebuilt from the analysis outputs alone.

---

## The Prompt

You are writing `FINDINGS.md` — the narrative report for a statistical analysis
of NBA home court advantage covering every game from 1983–84 through 2024–25
(roughly 51,000 games, regular season and playoffs).

Your two data sources are:
- **`RESULTS.md`** — auto-generated regression output. The authoritative source
  for all numbers, directions, and effect sizes.
- **The PNG charts** — listed by `![...](.png)` references inside FINDINGS.md
  once it exists; discover the current set by looking at what PNGs exist in the
  working directory.

---

## Before Writing Anything

Read everything first. Do not write a single sentence until you have absorbed
both data sources in full.

1. Read `RESULTS.md` completely.
2. Read each PNG as an image and note what it shows: the direction of each trend,
   which time periods stand out, whether regular season and playoffs move together
   or diverge, and what a reader would take away at a glance.
3. Identify the three or four most important findings across all charts and tables.
   These become the spine of the report. Everything else supports them.

Only once you have that full picture should you begin drafting.

---

## Organizing Principle

The report answers three questions, in order:

1. **Has home court advantage changed?** Establish the phenomenon before
   explaining it. Show the shape, size, and consistency of the trend. A reader
   should be convinced the decline is real before they hear why.

2. **What makes home court an advantage at all?** Separate the factors that
   create a home edge on any given night from the factors that explain the
   long-run trend. These are different questions. Conflating them is the most
   common mistake in sports analysis.

3. **What is driving the change — and what isn't?** Lead with what the data
   most strongly implicates. End with what it rules out. A finding that clears
   a popular explanation is just as valuable as one that confirms it.

Every section in FINDINGS.md should make clear — by the end of its first
paragraph — which of these three questions it is answering and what the answer
is. A reader skimming section headings should understand the full story.

---

## Translating Data into Prose

Never paste statistics directly into prose. Every number from RESULTS.md needs
to be translated into plain English before it belongs in a sentence.

**The test:** if a reader who knows basketball but has never taken a statistics
class would be confused by a sentence, rewrite it.

- "β = −0.0025, p < 0.001, HAC-robust" → "the decline runs at roughly a quarter
  of a percentage point per year, and the data leaves no room to doubt it"
- "McFadden R² = 0.043" → "the trend explains a remarkable share of game
  outcomes for a sport with this much randomness"
- "era dummy: coef = −0.031, SE = 0.014" → "about three percentage points
  vanished at that era transition beyond what the underlying trend would predict"

One key number per section is acceptable when it is the most direct way to
state the finding. Avoid prose that reads like a results table.

Never use: "statistically significant," "OLS," "HAC-robust," "McFadden R²,"
"marginal effects," "logistic regression," "coefficient," "p-value," "standard
error," "heteroskedasticity." Replace with: "the data confirms," "reliable
finding," "strong evidence," "the numbers rule this out," "no meaningful effect."

---

## Both Regular Season and Playoffs

Every section that covers a trend must address both. They often differ, and
that difference is informative. If the regular season declined steadily but
the playoffs declined more slowly, say so and note why that might be. Never
write only about one and ignore the other.

---

## Narrative Arc

Structure the report so that each section builds on what came before:

- **Establish the phenomenon first.** Don't open with explanations. Show the
  reader what needs explaining. Give them the orientation chart early.
- **Show how it behaves before explaining why.** Era breakdowns, margin trends,
  and series structure are descriptive — they tell you the shape of the decline.
  Save the causal sections for after.
- **Lead with the strongest findings.** If referees and 3-point shooting are
  the main drivers, they get full sections with charts. Don't bury the lede in
  a table.
- **Rule-outs belong at the end.** Pace, parity, travel — test them, then
  dismiss them. Ending with what the data clears gives the reader confidence
  that the positive findings survived scrutiny.
- **Summarize last.** The final section synthesizes all three questions. It
  should be readable on its own — someone who skips the body should still
  understand the key findings.

---

## Voice

Write like an editor at a sports magazine. Direct, concise, no hedging. The
reader knows basketball but has no stats background.

- Say what the data shows, not what it "suggests" or "may indicate."
- Short paragraphs. Active sentences. One idea per paragraph.
- When a finding is uncertain or too noisy to confirm, say so plainly — but
  don't hedge findings that are solid.
- No redundancy: say each thing once, in the most appropriate section.
  Cross-reference with "(see Section N)" rather than repeating.

---

## File Format

FINDINGS.md must follow this exact structure so that `generate_report.py` can
assemble it into a PDF without modification:

```
# NBA Home Court Advantage — Findings

[2–3 sentence preamble pointing to RESULTS.md for numbers]

---

## 1. Section Title
[body]
---

## 2. Section Title
[body]
---
...
```

- Every section begins with `## N. Title` where N is the section number.
- Sub-headings within a section use `### Sub-heading`.
- Images are referenced as (charts live in the `generated/` directory):
  `![Figure N. Caption text.](generated/filename.png)`
  or with a size hint: `![Figure N. Caption text.](generated/filename.png){width=0.5}`
- Paragraphs are separated by blank lines.
- Sections are separated by a `---` line.

---

## After Writing

1. Re-read `RESULTS.md` and verify that every directional claim in the
   narrative matches the sign and rough magnitude of the corresponding result.
2. Check that both regular season and playoffs are addressed in every section
   that has data for both.
3. Check that the three questions are each answered clearly — not implied,
   answered.
4. Regenerate the PDF: `python3 generate_report.py`
5. Skim the PDF to confirm all section headings appear in the TOC, all figures
   render, and the appendix contains the full regression tables.
