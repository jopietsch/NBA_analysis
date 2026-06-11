# Statistical Methods — Improvement Notes

Ideas for improving how statistical significance is *reported* in this project.

> **Status (2026-06-11):** numbers quoted below were re-verified against the
> current `RESULTS.md` and still hold. This file covers the reporting track
> only; *approach-level* fixes (the broken §7 referee t-test, order-dependent
> R² decomposition, conditional-margin composition effects, etc.) are tracked
> in `PLAN-STATS.md`. One interaction between the tracks matters: do not add
> CIs or Bayes factors to the §7 referee table until PLAN-STATS item 1 lands —
> those p-values come from a zero-variance test and are meaningless as-is.
>
> **Decision (2026-06-11):** confidence intervals (idea 1) are absorbed into
> `PLAN-STATS.md` as item 12 and will be implemented there. The remaining
> ideas below (Bayes factors, TOST, full Bayesian regression) are **parked**
> — optional polish, not pending work. The §16 summary-table rewrite already
> addresses the core large-N communication problem in prose, so nothing in
> this file blocks or is required by `PLAN-STATS.md`.

## The Core Problem with P-Values Here

With 47,000+ regular-season games, almost everything tests as "significant." The
travel distance result is the clearest example: p = 0.024 but the effect is −0.08 pp
per 100 miles — noise that cleared the significance threshold purely because of
sample size. P-values answer "is the effect nonzero?" not "does the effect matter?"

The `≈pp` marginal effects column already partially addresses this by showing
practical significance alongside statistical significance. That's the right instinct.

---

## Improvements Worth Considering

### 1. Confidence Intervals (easy, high value)

Show the range of plausible effect sizes rather than a binary yes/no. A CI of
[−0.15, −0.01] pp/100 miles makes the travel distance result immediately readable
as "tiny even in the best case." statsmodels already computes these — it's one
extra line of output per coefficient.

### 2. Bayes Factors (moderate effort, most honest for null results)

The Bayes Factor (BF) is the ratio of how much more likely the data are under H1
vs H0. The key advantage over p-values: **it can provide positive evidence for the
null hypothesis**, which p-values cannot.

Conventional interpretation:
- BF < 1/3 → evidence *for* the null
- BF 1/3–3 → inconclusive
- BF > 3 → moderate evidence for H1
- BF > 10 → strong evidence for H1

For the travel distance result (p = 0.024, N = 47k), the BF would likely be ~2–3
(weak/inconclusive) — more honest than calling it "significant." For era effects
(−8.9 pp, p < 0.001), BF would be enormous and the two methods would agree.

**The Lindley/Jeffreys-Lindley paradox:** p-values and Bayes Factors diverge as N
grows. p = 0.024 from 47k games is much weaker Bayesian evidence than p = 0.024
from 200 games. This project is squarely in the large-N regime where the divergence
matters.

The project now also has the *small*-N flip side: the franchise HCA consistency
correlation (Pearson r = +0.36, p = 0.045, N = 32 franchises) is borderline in
the opposite direction — at N = 32, p = 0.045 is weak evidence *for* an effect,
and a BF would likely land in the inconclusive 1–3 range.

**Implementation options:**
- `pingouin` library has `bayesfactor_ttest` — lightweight, no full Bayesian rewrite
- `pymc` or `bambi` for full Bayesian logistic regression with posterior distributions
  and credible intervals; adds real complexity but gives proper posteriors on all
  coefficients

### 3. Equivalence Testing / TOST (targeted use)

Two One-Sided Tests formally answer "is this effect smaller than a meaningful
threshold?" rather than "is this effect nonzero?" For results where the claim is
"travel distance is negligible," set a threshold of ±1 pp and test whether the CI
falls entirely within it. Turns a non-significant p-value into a positive claim about
the null.

The June 2026 additions made this more valuable: FINDINGS now affirmatively
claims several nulls that currently rest on failure-to-reject alone —
the rest × era stability claim (interaction p = 0.43 regular season / 0.75
playoffs, §8), the "format change is not separable from the secular trend"
conclusion (joint p = 0.24, §2), parity (p = 0.68, §10), and playoff altitude
(p = 0.59, §15). TOST would upgrade each from "no evidence of an effect" to
"evidence of no meaningful effect."

---

## Priority Order

1. **Confidence intervals** — **absorbed into `PLAN-STATS.md` item 12
   (Batch 3); implement there, not separately.**

Parked — optional, revisit only if the report's audience needs formally
licensed null claims or Bayesian evidence statements:

2. **Bayes Factors for the borderline / null results** — most useful for travel
   distance (p = 0.024, tiny effect), timezone (p = 0.085), and the franchise
   HCA consistency correlation (p = 0.045, N = 32). Would change the narrative
   from "not significant" to "positive evidence against an effect," but adds a
   `pingouin` dependency.

3. **Equivalence testing** — would upgrade the affirmative null claims now in
   FINDINGS §2, §8, §10, and §15 from "no evidence of an effect" to "evidence
   of no meaningful effect." Only worth it if those claims need to be formal.

4. **Full Bayesian regression** (`bambi`/`pymc`) — highest payoff for a rewrite,
   gives posterior distributions and credible intervals throughout, but significant
   added complexity for marginal narrative gain.

---

## Relevant Libraries

- `pingouin` — Bayes Factors for t-tests; easy drop-in
- `bambi` — high-level Bayesian regression built on PyMC; syntax similar to statsmodels
- `pymc` — full probabilistic programming; most flexible
- `scipy.stats` — already imported; has some equivalence-testing building blocks
