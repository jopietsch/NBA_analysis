# Prompt: Generate FINDINGS.md from Scratch

Use this prompt in a fresh Claude Code session when FINDINGS.md does not exist
or needs to be rebuilt from the analysis outputs alone.

---

## The Prompt

You are writing `FINDINGS.md` — the narrative report for an analysis of NBA home
court advantage. The analysis covers every NBA game from 1983–84 through 2024–25
(regular season and playoffs), roughly 51,000 games.

**Before writing anything, do these steps in order:**

1. Read `RESULTS.md` in full. This is the auto-generated regression output. Every
   claim you write must be traceable to a number in this file or visible in a chart.

2. Read each of the following PNG files as images, one at a time, and note what
   each chart shows before writing the section that references it:
   - `nba_home_court_advantage_season.png`
   - `nba_home_court_advantage_era_bars.png`
   - `nba_home_court_advantage_format_bars.png`
   - `nba_home_court_margin.png`
   - `nba_home_court_series_breakdown.png`
   - `nba_home_court_team_hca.png`
   - `nba_home_court_advantage_differentials.png`
   - `nba_home_court_shot_zones.png`
   - `nba_home_court_referee.png`
   - `nba_home_court_3pa.png`
   - `nba_home_court_pace.png`
   - `nba_home_court_parity.png`

3. Write `FINDINGS.md` following the structure and rules below.

---

## The Three Questions

Everything in FINDINGS.md is organized around three questions. Every section
must state clearly which question it is answering — either explicitly or by
framing its opening paragraph:

1. **Has home court advantage changed?** (Sections 1–4 — document the shape
   and size of the decline)
2. **What makes home court an advantage at all?** (Sections 5–6 — the factors
   that create the edge on any given night)
3. **What is driving the change — and what isn't?** (Sections 7–10 are the
   main causes; Sections 11–12 are things that don't explain it)

Section 13 is a Summary that synthesizes all three questions.

---

## File Format

FINDINGS.md must follow this exact format so that `generate_report.py` can
assemble it into a PDF without modification.

### Structure

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
## 13. Summary
[body]
```

### Rules

- Every section begins with `## N. Title` where N is the section number.
- Sub-headings within a section use `### Sub-heading`.
- Images are referenced as:
  `![Figure N. Caption text.](filename.png)`
  or with a size hint:
  `![Figure N. Caption text.](filename.png){width=0.5}`
- Paragraphs are separated by blank lines.
- Sections are separated by a `---` line.
- Do **not** include raw coefficient values, R² numbers, or p-values in the
  prose — those live in RESULTS.md. Use qualitative language instead:
  "significant," "dominant," "narrowing," "no effect," "worth about X percentage
  points," "one of the strongest findings."
- Exception: a single key number per section is acceptable when it is the
  clearest way to state the finding (e.g., "home teams won 65% in 1984 and
  55% today").

---

## Section-by-Section Guide

Write each section in the order below. For each one, the guide tells you:
- which PNG(s) to reference and their figure number
- which part of RESULTS.md to consult
- what question it answers
- what the key findings to convey are

Use the charts and RESULTS.md to fill in the actual numbers and directions.

---

### § 1. The Decline
**Question:** Has HCA changed?
**Chart:** Figure 1 — `nba_home_court_advantage_season.png`
**RESULTS.md:** look for the long-run logistic regression trend (slope per season,
R², HAC-robust test), the overall RS and playoff decline rates, and the pre/post
comparison.

Cover:
- The headline finding: home win % fell from ~65% in 1984 to ~55% today in the
  regular season; playoffs declined too but more slowly.
- How steady the decline is (the trend's explanatory power is remarkable for
  sports data).
- That it crosses every era and every rule change — this is a smooth drift,
  not a one-time shock (with one exception noted in §2).
- Place Figure 1 early in the section — it is the orientation chart for the
  whole report.
- Close by previewing the three-question structure so the reader knows what
  the rest of the report does.

---

### § 2. Era and Format Period Analysis
**Question:** Has HCA changed? (shape of the decline across rule-change eras)
**Charts:** Figure 2 — `nba_home_court_advantage_era_bars.png` (use `{width=0.5}`),
Figure 3 — `nba_home_court_advantage_format_bars.png` (use `{width=0.5}`)
**RESULTS.md:** look for era-dummy tests (which era transitions show a real step
beyond the trend), the 1994–95 hand-checking finding, and the 2014 format-change test.

Cover:
- A reference table of the six rule-change eras and four playoff format periods
  (use markdown tables — these are the definitions used throughout the rest of
  the report).
- Which rule changes produced a real one-time drop beyond the underlying trend,
  and which didn't. (RESULTS.md will show that almost all era transitions are
  noise; one is not.)
- The 2014 Finals format change: the playoff home win % did fall around that time,
  but whether the format itself caused it.
- That every era ends lower than the one before — no era reversed the decline.

---

### § 3. Win Margin Trends
**Question:** Has HCA changed? (what the decline looks like in points, not win%)
**Chart:** Figure 4 — `nba_home_court_margin.png`
**RESULTS.md:** look for unconditional quantile regression on margins (top and
bottom deciles), the mean all-game margin trend, and win/loss margin trends.

Cover:
- Frame this carefully: margins are not a cause of the decline, they describe
  what the decline looks like in points. Rule out the story that games are simply
  getting closer.
- The direction of home win margins vs. home loss margins (they move differently).
- What quantile regression reveals about the spread of outcomes.
- Close by explicitly stating this section does not explain the why — that comes
  later.

---

### § 4. Playoff Series Structure
**Question:** Has HCA changed? (how HCA operates within a series)
**Chart:** Figure 5 — `nba_home_court_series_breakdown.png`
**RESULTS.md:** look for the G1–G7 home win % breakdown and the higher-seed vs.
lower-seed hosting contrast.

Cover:
- How dramatically home win % differs by game number within a series (higher seed
  hosting vs. lower seed hosting).
- What Game 7 home win % looks like and why it differs from G1/G2.
- Connect back to §2: the 2014 format change shifted which games the higher seed
  hosts — but the underlying trend explains the post-2014 drop, not the format.

---

### § 5. Franchise Home Court Advantage
**Question:** What makes home court an advantage? (how much HCA varies by venue)
**Chart:** Figure 6 — `nba_home_court_team_hca.png`
**RESULTS.md:** look for the franchise HCA summary statistics (league mean, range,
top/bottom franchises).

Cover:
- Explicitly state this section answers question 2 (what makes HCA real), not
  question 3 (why it's falling). The franchise averages span 40 years of data, so
  they say nothing about the decline.
- The league-wide mean home-road gap (regular season and playoffs).
- Which franchises lead and why (altitude teams will stand out).
- The caveat on playoff franchise samples being too small for strong individual claims.
- Regular season vs. playoff HCA scatter: do teams that protect home court in the
  regular season do so in the playoffs too?

---

### § 6. The Usual Suspects: Rest, Travel, Altitude, and Time Zones
**Question:** What makes home court an advantage? (and why these factors don't
explain the decline)
**Chart:** none (these factors appear in RESULTS.md only)
**RESULTS.md:** look for the rest, altitude, travel, and time-zone coefficient
estimates; the game-level model with all factors; the pre/post-2014 stability test;
and the era effect size.

Cover:
- Each factor (rest, altitude, travel distance, time zones): state whether it's
  real and roughly how large.
- The key punchline: put all of them into a single model and the era effect (which
  decade the game was played in) accounts for as much of the outcome as all of
  them combined — meaning the factors that didn't change can't explain the trend.
- The pre/post-2014 test: the factor estimates are stable, but the baseline dropped.
- Close by previewing §7–10: the explanation lives inside the era effect.

---

### § 7. Box-Score Differentials
**Question:** What's driving the change?
**Chart:** Figure 7 — `nba_home_court_advantage_differentials.png`
**RESULTS.md:** look for the foul differential trend (early era vs. recent),
shooting efficiency differential trends, and the tpa_rate_diff finding.

Cover:
- Lead with the foul differential — it is the single most important finding.
  State the early-era foul gap and today's gap in plain terms.
- Shooting efficiency differential: is it closing?
- Shot selection differential (3PA rate): are road teams now shooting the same
  shot mix as home teams at the same venue?
- Free throw and raw FG% gaps: what trend do they show and what does it mean?
- Both regular season and playoffs for each metric.

---

### § 8. Shot Zone Analysis
**Question:** What's driving the change? (§7 in geographic detail)
**Chart:** Figure 8 — `nba_home_court_shot_zones.png`
**RESULTS.md:** look for paint, mid-range, corner-3, and above-break-3 differential
trends.

Cover:
- Open by explicitly linking back to §7: this is the same disappearing shot-quality
  edge, mapped onto the floor.
- Which zones show a narrowing home/road gap and which don't.
- What the paint and mid-range trends mean in plain English (is the visiting defense
  getting pushed away from the basket as much as it used to be?).
- Briefly note this section covers regular season; playoff zone trends point the
  same direction but are noisier.

---

### § 9. Referee Patterns
**Question:** What's driving the change? (who is responsible for the foul-call shift)
**Chart:** Figure 9 — `nba_home_court_referee.png`
**RESULTS.md:** look for the referee bias statistics: fraction of officials
home-favoring, mean career foul differential, number with statistically significant
bias, era-level distribution of biases.

Cover:
- Open by linking back to §7: this section identifies who was doing the tilting.
- The fraction of qualifying playoff officials who show a home-favoring career bias
  (the answer is "almost all of them").
- The range of individual biases.
- What the era distribution (box plot panel) shows: has the spread narrowed?
- The key interpretation: the profession moved together, not a handful of bad actors.
- Close by stating this is the decline's biggest single driver, seen one official
  at a time.

---

### § 10. 3-Point Shooting and Home Court Advantage
**Question:** What's driving the change?
**Chart:** Figure 10 — `nba_home_court_3pa.png`
**RESULTS.md:** look for the season-level correlation between 3PA rate and home
win %, the within-era game-level 3PA coefficient, and the playoff version.

Cover:
- The season-level correlation between rising 3PA rate and falling home win %
  (strong, with a specific r value from RESULTS.md).
- That this holds within eras too (not just a coincidence of shared timing).
- Three reasons why more 3-point shooting would erode home court:
  (1) shot selection has equalized — road teams used to take worse shots at the
  same venue;
  (2) more 3s means higher variance per possession, which favors the underdog;
  (3) interior contact is where crowd influence on refs is greatest — moving the
  game outside removes those moments.
- How the 3-point trend and the foul-call trend are probably reinforcing each other.

---

### § 11. Pace and Home Court Advantage
**Question:** What isn't driving the change?
**Chart:** Figure 11 — `nba_home_court_pace.png`
**RESULTS.md:** look for the season-level pace correlation, the game-level pace
coefficient, and the caveat about endogeneity.

Cover:
- Open by stating the popular theory and immediately note that the data does not
  support it as a cause of the decline.
- The season-level non-relationship (pace has been U-shaped while HCA steadily fell).
- The game-level finding and why it's not clean (the endogeneity problem: blowouts
  produce fast pace).
- The pre-game pace instrument result.
- The bottom line: whatever pace does at the game level, it can't explain a
  40-year trend that moved in only one direction.

---

### § 12. Competitive Balance and Parity
**Question:** What isn't driving the change?
**Chart:** Figure 12 — `nba_home_court_parity.png`
**RESULTS.md:** look for the raw correlation, the detrended year-to-year
association, and any notes on statistical limitations.

Cover:
- Open by acknowledging the intuition (a more equal league should reduce home
  advantage) then immediately note that the raw correlation is near zero.
- Why a simple correlation can mislead here (both series trend down, so they look
  related even if they're not).
- What the detrended test finds: is there a real year-to-year signal once the
  shared trend is removed?
- The verdict: parity may nudge HCA at the margins in any given year, but it is
  not the engine of the 40-year decline.

---

### § 13. Summary
**Question:** All three.
**Charts:** none
**RESULTS.md:** use the key numbers from across all sections.

Cover:
- Open with the headline fact: how many percentage points have been lost, over
  how many years, in both RS and playoffs.
- The reliability of the trend (use the trend's explanatory power).
- Note that the decline is in win rate, not margins — when home teams win they
  win bigger; the decline is in frequency.
- Three tables in this order:
  1. **"Why home court matters — factors real every night"**: rest, altitude,
     time zones, empty arenas (COVID). State the effect of each and note that
     none of them changed, so none explain the decline.
  2. **"Why it has fallen"**: refs more neutral, shot quality convergence,
     3-point shooting, and the one rule change that mattered (1994–95).
     Include the pre/post-2014 test result here too.
  3. **"Tested, not a driver"**: travel, pace, parity.
  4. **Playoff-specific tables**: same structure — playoff everyday edges
     (most evaporate in the postseason), playoff drivers, playoff ruled-out.
  5. **"Beyond the decline"**: structural facts about how HCA behaves
     (series structure, franchise variation, referee universality, format
     innocence).
- Close with a plain-English two-paragraph "short version" that a non-analyst
  could understand.

---

## Writing Style Rules

Follow these rules throughout. They matter as much as the accuracy of the numbers.

**Voice:** Write like an editor at a sports magazine — not an academic, not a stats
blog. Concise, direct, no hedging. The reader knows basketball but has no stats
background.

**No jargon:** Never use: "statistically significant," "OLS," "HAC-robust,"
"McFadden R²," "marginal effects," "logistic regression," "coefficient," "p-value,"
"standard error," "heteroskedasticity." Replace with: "the data confirms," "reliable
finding," "strong evidence," "the numbers rule this out," "no meaningful effect."

**No raw stats in prose:** Do not paste numbers directly from RESULTS.md into
sentences. Translate: "β = −0.0025, p < 0.001" → "the decline runs at roughly
−0.25 percentage points per year." A single key number per section is fine
when it is the most direct way to state the finding.

**Both regular season and playoffs:** Every section that covers a trend must
address both. They often differ — that difference is informative. Never write
only about one and ignore the other.

**No redundancy:** Say each thing once, in the most appropriate section.
Cross-reference with "(Section N)" rather than repeating.

**Backed by data:** Every claim must be visible in RESULTS.md or in one of the
charts. Do not speculate beyond what the data shows. If a finding is directional
but too noisy to confirm, say so plainly.

**Answer the question:** Every section must make clear — by the end of its first
paragraph — which of the three report questions it is addressing and what its
answer is. A reader skimming section headings should understand the whole story.

---

## After Writing

Once FINDINGS.md is drafted:

1. Re-read RESULTS.md and verify that every directional claim in the narrative
   matches the sign and rough magnitude of the corresponding result.
2. Check that both regular season and playoffs are addressed in every section
   that has data for both.
3. Regenerate the PDF: `python3 generate_report.py`
4. Skim the PDF to confirm all 13 section headings appear in the table of
   contents, all figures render, and the appendix contains the full regression
   tables.
