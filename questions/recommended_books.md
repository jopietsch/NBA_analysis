# Recommended Books — Statistics for NBA Analysis

A reading path keyed to the methods in `STATS_TUTORIAL.md`. The tutorial sections
are noted so you can read selectively.

---

## Foundations + OLS (STATS_TUTORIAL Parts 0–1)

**"Statistics" by Freedman, Pisani & Purves**
The best conceptual foundations book: probability, confidence intervals, and
regression without hiding behind formulas. Dense but worth it. Covers the ideas
behind §§0–1 (probability, OLS, z-tests, chi-square, correlation).

---

## Regression through GLMs (STATS_TUTORIAL Parts 2–4)

**"Regression and Other Stories" by Gelman, Hill & Vehtari**
Covers OLS, logistic regression, GLMs, R², mediation, and interactions in one
coherent book. Close to a direct map to §§2–4. Free draft PDF available from
the authors.

Covers: logistic regression (§2.1), log-odds → pp translation (§2.2), binomial
GLM (§2.3), LPM (§2.4), McFadden R² (§2.5), LR test (§4.1), mediation (§4.3),
interaction terms (§7.4).

---

## Causal Inference and Robust SEs (STATS_TUTORIAL Parts 3, 7)

**"Mostly Harmless Econometrics" by Angrist & Pischke**
The authoritative source on cluster-robust SEs, HAC/Newey-West, natural
experiments, and controlling for confounders. Covers exactly the "getting
inference right" layer.

Covers: cluster-robust SEs (§3.2), HAC (§3.3), confounders and controls (§7.1),
spurious correlation / detrending (§7.2), natural experiments (§7.5).

**"The Effect" by Nick Huntington-Klein** *(gentler alternative to Angrist & Pischke)*
More readable introduction to the same causal-inference ideas. Free online at
theeffectbook.net. Good entry point before tackling Mostly Harmless.

---

## Empirical Bayes (STATS_TUTORIAL Part 6)

**"Introduction to Empirical Bayes" by David Robinson**
A short free ebook. Directly covers the shrinkage estimator in §6 with worked
examples — the closest match to the franchise/referee ranking methods used here.

Covers: variance decomposition (§6.1), empirical-Bayes shrinkage (§6.2).

---

## Quantile Regression (STATS_TUTORIAL Part 5)

**"Quantile Regression" by Roger Koenker**
The authoritative text — dense but comprehensive. For practical use, the
`statsmodels` docs and the Wikipedia article on quantile regression are faster
entry points before reaching for the full book.

Covers: quantile regression and polarization (§5.1).

---

## Suggested Reading Order

1. **Gelman, Hill & Vehtari** — builds the core toolkit (regression through GLMs)
2. **Angrist & Pischke** *or* **Huntington-Klein** — adds the causal / inference layer
3. **Robinson's EB ebook** — short, fills Part 6 exactly
4. **Freedman, Pisani & Purves** — add this if foundations feel shaky after step 1

Quantile regression (Koenker) is only worth pursuing if Part 5 of the analysis
becomes a focus; the `statsmodels` docs are sufficient for reading the results.
