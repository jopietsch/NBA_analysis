# PLAN-STATS.md — Statistical Methodology Improvements

Implementation plan for the methodology issues identified in the June 2026
review. Ordered by risk to stated conclusions: P0 is a bug whose output is
already quoted in FINDINGS prose; P1 items could change conclusions; P2 items
are robustness upgrades where conclusions probably hold.

Scope note: this plan covers *changing the statistical approach* of existing
analyses, plus the one reporting improvement worth doing — confidence
intervals (item 12, absorbed from `STATISTICAL_METHODS.md`). The remaining
`STATISTICAL_METHODS.md` ideas (Bayes factors, TOST, full Bayesian rewrite)
are parked as optional; implementing this plan does **not** require them.
All items below need only `statsmodels`/`scipy`, already in
`requirements.txt`.

Workflow per item (per CLAUDE.md): change the `run_*` /`compute_*` function →
add unit tests for any data/computation-layer change → re-run
`MPLBACKEND=Agg python3 nba_home_court_advantage.py` → update the affected
FINDINGS.md section with the new numbers → `python3 generate_report.py`.
No new charts are planned, so no `.gitignore` changes.

---

## P0 — Bug fix (do first; FINDINGS currently states an unsupported claim)

### 1. §7 Referee per-official significance test is broken

**Problem.** `run_referee_analysis` computes each official's p-value as
`ttest_1samp([o["mean_foul_diff"]] * o["n_games"], 0)` — a constant vector
with zero variance. Every official therefore prints `p < 0.001 ***`
regardless of the data. FINDINGS §7 repeats the bogus result ("the career
biases are statistically significant for all qualifying officials"). With
realistic per-game noise (foul-diff SD is several fouls/game), near-zero
officials like Josh Tiven (−0.112 over 89 games) are almost certainly *not*
significant.

**Fix.**
- `nba_home_court_data.py`: extend `compute_referee_bias_stats` to also return
  each official's per-game foul-diff standard deviation (`sd_foul_diff`) and
  keep `n_games`. The per-game values are already in hand when the mean is
  computed.
- `nba_home_court_regression.py`: replace the fake test with a real one-sample
  t-test from summary stats: `t = mean / (sd / sqrt(n))`, p from
  `scipy.stats.t.sf(|t|, n−1) * 2` (or `ttest_1samp` on the actual per-game
  vector if returned).
- Report how many of the 42 officials remain individually significant, with a
  Benjamini–Hochberg correction across the 42 tests (cheap, and appropriate
  since we are testing 42 hypotheses).
- **Tests:** synthetic-DataFrame unit test in
  `test_nba_home_court_advantage.py` asserting `sd_foul_diff` is computed
  correctly and that a near-zero-mean official does not test significant.
- **FINDINGS §7:** rewrite the "statistically significant for all qualifying
  officials" sentence with the corrected counts. The directional claim
  (41/42 negative means) is unaffected — it never depended on the t-test.

---

## P1 — Different approach could change the conclusion

### 2. §7 Referee rankings and the variance-compression claim

**Problem.** (a) Career-mean rankings favor small-sample extremes — same
artifact as the Kansas City Kings row in §14. (b) The headline "SD across
officials fell 3.72 → 0.88" mixes true between-official variance with
sampling noise; officials with few games in an era have noisy era means,
which inflates early-era SDs mechanically.

**Fix.**
- Method-of-moments variance decomposition per era (transparent, no
  convergence issues): `true_var = var(observed era means) −
  mean(per-official sampling var)`, where sampling var = `sd²/n` per official
  within that era; floor at 0. Report the corrected between-official SD per
  era alongside the raw SD.
- Empirical-Bayes shrinkage for the rankings: shrink each career mean toward
  the league mean with weight `true_var / (true_var + sd²/n)`. Re-rank top/
  bottom 10 on shrunken means; keep raw means as a column.
- Optional cross-check: `statsmodels MixedLM` with official random intercepts
  on game-level foul diffs; only if the method-of-moments result is ambiguous.
- **FINDINGS §7:** the "fourfold compression" claim either survives with
  corrected numbers or gets restated as partly a sampling artifact — follow
  the data.

### 3. §4 Win-margin "polarization" — replace conditional-on-outcome trends

**Problem.** Trends in margin *conditional on win/loss* suffer from a
composition effect: as home win % declines, marginal close games migrate from
the win pool to the loss pool, shifting both conditional means without any
game becoming more lopsided. The "wins bigger, losses worse" finding may be
partly mechanical.

**Fix.**
- Quantile regression on the *unconditional* home margin:
  `smf.quantreg("margin ~ year", sub)` at q ∈ {0.10, 0.25, 0.50, 0.75, 0.90},
  regular season and playoffs. Report slope, p per quantile.
- Interpretation rules: lower quantiles trending down + upper quantiles
  trending up = genuine variance widening (polarization confirmed); all
  quantiles shifting down in parallel = pure level effect (polarization was a
  composition artifact).
- Keep the existing conditional table (it matches Figure 6) but add the
  quantile table and reframe FINDINGS §4 around it.

### 4. §15 Sequential R² decomposition is order-dependent

**Problem.** "Era accounts for 56% of model fit" depends on era being entered
first; era absorbs all variance it shares with rest (scheduling changed
across eras) and the COVID flag. The 56/25/16/2 split is presentation-order
arithmetic.

**Fix.**
- Shapley decomposition over the 5 predictor blocks (era, rest, altitude,
  tz, covid): fit all 2⁵ = 32 logits on the same N, compute each block's
  marginal ΔR² averaged over all orderings. Cache fitted log-likelihoods by
  frozenset of blocks — 32 fits on 47k rows is cheap.
- Print the Shapley shares next to the existing sequential table; label the
  sequential one "order-dependent (era entered first)".
- **FINDINGS §15/§16:** replace the 56/25/16/2 shares with Shapley shares in
  the summary table (the header already says "share of the model's explained
  variation", which describes Shapley better than sequential ΔR²).

---

## P2 — Robustness upgrades (conclusions probably hold)

### 5. §1 Season-level trend inference

Unweighted OLS on per-season percentages ignores (a) serial correlation and
(b) that a playoff season is ~80 games vs. ~1,230 regular-season games.
Replace with a binomial GLM (`sm.GLM(wins/games, Binomial(), var_weights=games)`
or events/trials form) with `year` as predictor; also report Newey–West
(HAC, maxlags=1) SEs for the existing OLS as a cross-check. Apply to overall
and per-era slopes in `run_decline_trend`. The playoff p = 0.009 is the
number most likely to move.

### 6. §12 Pace — expected pace instead of realized pace

The prose admits realized pace is partly an outcome of the game. Build
*expected* pace: per team-season leave-one-out mean possessions
(`(sum − own) / (n − 1)`), game-level expectation = mean of the two teams'
LOO values. Requires a small data-layer helper to compute per-team-game
possessions (the formula already exists inline in `build_game_dataset`).
Re-run the game-level logits with expected pace; if the positive
within-era effect disappears, FINDINGS §12's "game-state causality"
hypothesis is confirmed rather than asserted.

### 7. §8/§15 Playoff rest — control for team quality

Playoff rest is earned by winning the previous series quickly, so the
+2.3 pp/day estimate conflates rest with team strength. Data-layer helper:
same-season regular-season win % per team (from cached game logs); merge
`quality_diff = rs_win%_home − rs_win%_away` into playoff rows. Re-run the
playoff rest logit with `quality_diff` as a control and report both
coefficients. Update FINDINGS §8/§15/§16 if the rest effect attenuates
materially.

### 8. §15 Pre/post-2014 stability — formal test instead of eyeballing

The current table prints coefficient shifts ("altitude −0.144") with no
inference. Fit the pooled model
`home_win ~ (rest_diff + altitude_home + tz_diff) * post2014` and report each
interaction coefficient with its p-value — the same pattern already used for
rest × era in `run_rest_bucket_analysis`. FINDINGS §15 currently hedges
("the altitude coefficient shrinks"); this puts a p-value on it.

### 9. §14 Franchise HCA — shrinkage and uncertainty

Raw HCA differences let an 82-game franchise (Kansas City Kings, +35.4 pp)
top a table of 1,600-game franchises. Add: (a) a 95% CI per franchise from
binomial variances (`p_h(1−p_h)/n_h + p_r(1−p_r)/n_r`), printed as a column;
(b) empirical-Bayes shrinkage of HCA toward the league mean using the same
method-of-moments weights as item 2; re-rank on shrunken values. Re-run the
§14 regular-season-vs-playoff correlation on shrunken values — shrinkage
de-attenuates it, so the Pearson r = +0.36 likely strengthens. Update
FINDINGS §14 (the KC Kings caveat sentence can then cite the CI instead of
hand-waving).

### 10. §10 Parity — detrended correlation

Cross-season correlation of two (potentially) trending series risks spurious
(non-)association. Add a first-differenced check: correlate Δparity vs.
Δhome-win% year over year, and/or correlate residuals after regressing each
series on year. The null conclusion likely survives; this makes it solid.

### 11. Game-level regressions — cluster-robust SEs

All game-level logits treat games as independent; outcomes share
season-level shocks. Refit the headline models (sequential decomposition,
3PA, pace, travel) with `cov_type="cluster", cov_kwds={"groups": year}`.
Era-dummy p-values are the ones most at risk of being overstated. Apply as a
one-line change at each `fit(...)` call site; report clustered p-values in
place of the naive ones.

### 12. Confidence intervals throughout (absorbed from STATISTICAL_METHODS.md)

Add 95% CIs to the headline effect estimates: `conf_int()` at each `fit()`
call site, converted to the same units as the reported effect (pp via `_pp`
for logits, pp/yr for OLS trends), printed as `[lo, hi]` next to the point
estimate. Target the tables FINDINGS quotes directly: decline trend, full
model coefficients, bivariate factor summary, travel, 3PA, pace. This makes
"real but negligible" results self-evident (travel: −0.08 pp/100 mi with a CI
of roughly [−0.15, −0.01]) without changing any conclusion. Do §7's table
only after item 1 lands — CIs derived from the broken test would launder it.

---

## Sequencing

Model and effort recommendations per batch (which Claude model to run, what
effort setting, and why) are in `MODEL_USAGE.md`.

1. **Batch 1 (P0 + item 2):** referee fix + hierarchical re-check — same
   function, same FINDINGS section, ship together.
2. **Batch 2 (items 3, 4):** quantile margins + Shapley decomposition — both
   change §4/§15/§16 prose.
3. **Batch 3 (items 5–8, 12):** inference upgrades touching §1, §8, §12, §15,
   plus confidence intervals across the headline tables.
4. **Batch 4 (items 9–11):** §10, §14, and the cluster-SE sweep.

After each batch: full pipeline re-run, FINDINGS update for affected
sections, PDF regeneration, and a check that unchanged RESULTS sections are
byte-identical (re-run determinism check: `git diff RESULTS.md`).

Each batch is independently shippable; if any corrected result contradicts
current FINDINGS prose (most likely: item 1's "all officials significant",
item 2's compression claim, item 3's polarization story), the FINDINGS
rewrite is part of that batch, not deferred.
