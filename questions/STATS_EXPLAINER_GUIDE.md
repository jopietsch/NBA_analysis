# Stats Explainer: shared best practices

How to write a `*_stats_explainer.md.j2` so every project's methods companion covers the most statistics in the clearest, most consistent way. This is the contract `*_stats_explainer` docs are held to; the audience-tier rules in `CLAUDE.md` (the "knows statistics, but rusty" row) still apply on top of it.

## Who this doc is for, and its one cardinal rule

The reader **once took the stats course and is rusty**. Name methods with their real terms (binomial GLM, cluster-robust SE, ridge/MAP, QLR, bootstrap, confidence interval) and **refresh each on first use** — do not dumb down to the findings-tier plain language, and do not pile on jargon a rusty reader can't reconstruct without the reminder.

**Cardinal rule: the named method must match what the pipeline actually ran.** Verify every method name against `<project>_analysis.py` / `nbakit/` and `<project>_results.md` before writing it. Describing an estimator the code does not use is the worst failure this doc can make.

## The seven requirements (all projects, both layouts)

1. **Orientation note up top** — one short "How to read this" block stating: the audience (rusty stats reader), that this is the *methods companion* (findings = plain narrative; investigation = evidence with p-values; this = *how the numbers were computed*), that sections follow `_results.md` order (or naming the order used), and that every named method matches the code.
2. **A Dataset section, early** — how the analysis dataset(s) are built: source, date range, one-row-per-*what*, and the key columns with *why each exists*. If several analyses share one frame, describe it once here and have sections point back.
3. **Complete coverage** — every statistical method that produces a number in `_results.md` is explained exactly once. Nothing in `_results.md` is left unexplained; check the two against each other.
4. **No phantom methods** — never describe a technique the code doesn't run (the cardinal rule). If the code fits an OLS trend line with cluster-robust SEs, say exactly that, not "a regression."
5. **Define once, reference after (DRY)** — a method used in more than one place is defined a single time in the **Methods Toolbox** (below); later uses link/refer to it rather than re-explaining. This is the single biggest quality lever: it stops a 30-section doc re-teaching "cluster-robust SE" ten times.
6. **Numbers come from facts** — every cited figure is a `<< f("section.metric") >>` call, never hand-typed, so it can't go stale (matches the project-wide facts rule).
7. **A Limitations close** — what the methods can and cannot establish: correlation vs. causation, what the design identifies, sample-size caveats. State it plainly; naming the limit is part of the doc's job.

## The per-item template

Whether an item is a pipeline step (Layout A) or a metric/technique (Layout B), explain it with the same four beats, in this order:

- **The data** — which inputs / subset this uses (or "the game-level frame from the Dataset section").
- **The method** — the real name + what it estimates; if recurring, one clause + a pointer to the Toolbox entry.
- **Why this method** — why it fits the question, or the alternative it beats (e.g. "LPM not logit here, because its coefficients are additive and must sum to the total").
- **What the result means** — how to read the output (coefficient sign/size, CI, p-value, test statistic) with the headline number via `<< f() >>`. Add a **Why this chart** beat when the section owns a figure: why the chart takes that form (not what it shows — that's the findings doc).

## The Methods Toolbox (the DRY core)

A dedicated section (home_court and knicks call it **"Recurring Methods: Quick Reference"** — keep that name) that defines every recurring method **once**. Each entry is compact and follows the same shape:

> **Name (real term):** one-line refresh of what it is · how to read its output (what the number/CI/stat means) · the key assumption or when it can mislead.

Example (from home_court, the model to match):

> **Cluster-robust SEs (clusters = season):** used whenever game-level models pool many seasons; games within a season share league conditions, violating independence. Widens SEs relative to naive OLS; does not change the point estimate.

Put every method that appears in two or more sections here. A method used in exactly one place can be defined inline in that section instead.

## Two layouts — pick by project type

The requirements above are fixed; the arrangement is not. Choose the layout that fits, and say which at the top.

**Layout A — pipeline walkthrough** (for analysis-driven projects: `home_court`, `knicks_2026_historic`). One `##` section per `run_*` analysis, in `_results.md` order, each naming its function `(`run_xxx`)` and following the per-item template, then a Methods Toolbox at the end. Best when the project *is* a sequence of tests and traceability to each `_results.md` block matters most.

**Layout B — topical methods catalog** (for methods-survey projects: `player_rating_overview`, where the metrics themselves are the subject). Group by technique family (e.g. "Recomputed rating formulas", "Cross-system comparison", "Distribution analysis", "Bayesian foundations"), each entry following the per-item template. Still carries all seven requirements: the orientation note, a Data section near the front (not buried at the end), completeness against `_results.md`, and Limitations. Note the DRY requirement is met *by the grouping itself* here — each technique is defined once in its family section — so a separate "Recurring Methods" toolbox is optional in Layout B, used only for a method that genuinely spans families.

Both layouts share the same front matter, per-item template, Toolbox, facts discipline, and Limitations close — only the spine (pipeline order vs. technique grouping) differs.

## Ordering within a doc

- Orientation note → Dataset/Data → the body (walkthrough or catalog) → Methods Toolbox → Limitations.
- Within the body, simplest methods before advanced/robustness ones, so the refresh builds.
- A term must not appear before it is defined; if the Toolbox is at the end, the first substantive use should point forward to it ("see the Toolbox").

## Checklist before marking a stats explainer done

- [ ] Orientation note names the audience, the sibling-doc relationship, and the section order.
- [ ] Dataset/Data section is present and near the front.
- [ ] Every method in `_results.md` is explained exactly once (completeness).
- [ ] No method is described that the code does not run (no phantoms).
- [ ] Recurring methods live once in the Methods Toolbox; sections reference, don't repeat.
- [ ] Every cited number is a `<< f() >>` call.
- [ ] Each item follows the data / method / why / meaning (/ why-chart) template.
- [ ] Limitations section states what the methods can't establish.
- [ ] Layout (A or B) is declared and consistent.
