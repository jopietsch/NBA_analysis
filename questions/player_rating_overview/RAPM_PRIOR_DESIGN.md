# RAPM: box-score prior and reproducing the proprietary metrics

Design note for the computed RAPM. Internal analyst tier: technical shorthand is
fine. Most of the plan below is now shipped as `RAPM_MY` (prior-informed,
multi-year RAPM); this note records what was built, how it is wired, how close it
gets to EPM / LEBRON / RPM / DARKO / RAPTOR, and the two open items.

## Status: what shipped

The recommended path (bottom of this note) is built except for the public-snapshot
validation and the optional luck adjustment.

| Step | Status | Where |
|---|---|---|
| Multi-year pooling (2 to 3 seasons, recency-weighted) | Done | `pool_possessions()`, `compute_rapm_my()` in `..._data.py` |
| BPM box-score prior (prior-mean ridge) | Done | `rapm(prior=, prior_strength=)` in `nbakit/nbakit/ratings.py` |
| Validation vs public RAPM snapshot | Infra done, inactive: no snapshot CSV | `_load_rapm_snapshot()`, guard `rapm_val_reasonable` |
| Luck adjustment (shot-location expected-points proxy) | Not started (optional, partial) | — |

Two versions now exist in the unified table:

- **Bare single-season RAPM** with a zero-mean prior. The noisy baseline every
  serious metric improves on. Kept in the docs as the higher-variance cut.
- **`RAPM_MY`**: BPM box-score prior + pooled possessions (default 3 seasons,
  linear recency weights 1/3, 2/3, 1.0). This is the version to lead with.

The RAPM reconstruction fix earlier this session (recover valid possessions from a
game instead of discarding the whole game on any 5-on-5 reconcile failure) roughly
tripled usable games (~500 → ~1,230 per season) and lifted reliability across the
board: split-half ~0.10 → 0.32 (~0.48 Spearman-Brown full-data, ~0.60 at 5 pooled
seasons); bare single-season RAPM year-over-year 0.09 → 0.41; `RAPM_MY` year-over-
year 0.84, at least as stable as BPM (0.79). Only combined RAPM feeds the
consensus; the offense/defense splits stay out so a noisy single-season split
cannot swing the headline order.

## The prior is BPM

A box-score prior is a per-player impact-per-100 estimate built from box-score
stats, used as the center the ridge shrinks toward instead of zero. That is a
Statistical Plus/Minus (SPM) model, and our recomputed **BPM 2.0**
(`nbakit.ratings.bpm`, already on a points-per-100 scale) is one. It is the public
analog of what the proprietary metrics use internally:

- EPM: its own optimized SPM prior (plus tracking)
- LEBRON: PIPM coefficients as the prior
- RPM (Engelmann): an SPM prior
- BPM: the reproducible version of the same idea

BPM and bare RAPM agree at only ~0.23 (rank), so BPM-as-prior moves the noisy
low-possession players a lot (pulling reserve names down hard) while barely
touching a 2,500-minute star. That is the desired behavior.

Caveat: recomputed BPM absolute values are approximations (see the findings note
on the recomputed formulas). For a prior the scale is sanity-checked against the
BPM validation section each run rather than trusted blind.

## How the prior is wired

Prior-mean ridge minimizes

```
Sum (y - X beta)^2 + lambda * Sum (beta_i - prior_i)^2
```

No new solver. `rapm()` substitutes `gamma = beta - prior`:

1. Form the residual target `y' = y - X . prior`.
2. Run ridge on `y'` to get `gamma` (with a fixed strong penalty
   `RAPM_PRIOR_STRENGTH`, not the cross-validated one, so the shrink toward BPM is
   deliberate and stable).
3. Add back: `beta = gamma + prior`.

Column layout is `2*i` offensive / `2*i+1` defensive; players absent from the prior
fall back to a zero prior. Low-possession players (small, noisy `gamma`) collapse
onto their BPM; heavy-minute stars move far from it.

## Can we reproduce a proprietary metric?

The structure, yes; the exact metric, no. `RAPM_MY` captures what makes EPM / RPM /
LEBRON good (RAPM backbone + SPM prior + multi-year pooling). What it cannot
replicate is the proprietary inputs.

| Metric | What we match | The gap we cannot close |
|---|---|---|
| RPM (Engelmann) | Essentially all of it: RAPM + SPM prior + multi-year. Closest to reproducible. | His exact SPM coefficients; also defunct. |
| EPM | RAPM backbone + BPM-as-prior | Player-tracking inputs (Second Spectrum) and the per-stat stabilization weighting that is its actual edge |
| LEBRON | RAPM + prior structure | "Luck adjustment" needs shot-quality / expected-points data; PIPM prior uses tracking |
| DARKO | — | A different animal: a Kalman-filter daily now-cast, not a season RAPM. Needs per-game sequential modeling. |
| RAPTOR | on/off component | tracking-based offensive/defensive priors |

The wall for all of them is **player-tracking data** (speed, distance, shot
quality, matchup data), which is proprietary. A luck adjustment needs
expected-points-per-shot, which we only partially have via cached shot-location
data (not true shot quality).

## Recommended path

In order of leverage. Steps 1 and 2 shipped; 3 and 4 remain.

1. ~~**Multi-year pooling** (2 to 3 seasons, recency-weighted).~~ Done.
2. ~~**BPM box-score prior** via the prior-mean ridge substitution above.~~ Done.
3. **Validation** against a public RAPM snapshot. Infrastructure is in place: drop
   the downloaded CSV at `cache/rapm_snapshot_{season}.csv` (schema per
   `_load_rapm_snapshot`), rerun the pipeline, and the computed-vs-public section
   plus the `rapm_val_reasonable` guard (r > 0.70) activate. This is a manual
   data-acquisition step, not code; the snapshot source is external and partly
   paywalled.
4. Optional, partial: a **luck adjustment** using cached shot-location data as a
   rough expected-points proxy. Not full shot quality. Not started.

Outcome so far: the top tier sharpened to recognizable stars rather than
single-season role-player noise, while RAPM keeps the independent signal it adds
over the box scores. Call it RPM/EPM-like, not EPM or LEBRON itself, because the
tracking data and bespoke tuning are not ours to reproduce.
