"""Shared statistical helpers for question analyses.

Promoted from the home_court and knicks projects so the same methods are written
once. Heavier methods (cointegration, change-point, Shapley, ...) can land here
as a second project reaches for them.
"""

import numpy as np


def shrink_to_mean(values, sampling_vars):
    """Empirical-Bayes shrinkage of estimates toward their grand mean.

    Method-of-moments: the true between-group variance is the observed variance
    of the estimates minus the average sampling variance. Each estimate is pulled
    toward the grand mean in proportion to its reliability,
    ``w = true_var / (true_var + sampling_var)`` — noisy (small-sample) estimates
    move most. Use for any "ranking of noisy means" (franchises, referees, ...).

    Parameters
    ----------
    values : 1-D array-like of point estimates.
    sampling_vars : 1-D array-like of each estimate's sampling variance.

    Returns
    -------
    (shrunken, info) : the array of shrunken estimates, and a dict with
    ``grand_mean``, ``obs_var``, ``mean_sampling_var``, ``true_var``, ``weights``.
    """
    values = np.asarray(values, dtype=float)
    sv = np.asarray(sampling_vars, dtype=float)
    grand_mean = float(values.mean())
    obs_var = float(np.var(values, ddof=1))
    mean_sv = float(sv.mean())
    true_var = max(0.0, obs_var - mean_sv)
    weights = (true_var / (true_var + sv)) if true_var > 0 else np.zeros_like(sv)
    shrunken = weights * values + (1.0 - weights) * grand_mean
    return shrunken, {
        "grand_mean": grand_mean,
        "obs_var": obs_var,
        "mean_sampling_var": mean_sv,
        "true_var": true_var,
        "weights": weights,
    }


def binom_sf_ge(k: int, n: int, p: float = 0.5) -> float:
    """One-tailed binomial p-value: ``P(X >= k)`` under ``Binomial(n, p)``."""
    from scipy.stats import binom
    return float(binom.sf(k - 1, n, p))


def t_interval(mean: float, std: float, n: int,
               confidence: float = 0.95) -> tuple[float, float]:
    """Two-sided Student-t confidence interval for a mean.

    ``std`` is the sample standard deviation (ddof=1). Returns ``(lower, upper)``,
    or ``(nan, nan)`` if ``n < 2``.
    """
    if n < 2:
        return float("nan"), float("nan")
    from scipy.stats import t as t_dist
    half = float(t_dist.ppf((1.0 + confidence) / 2.0, df=n - 1)) * std / np.sqrt(n)
    return mean - half, mean + half
