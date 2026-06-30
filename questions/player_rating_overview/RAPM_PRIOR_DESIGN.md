# RAPM: box-score prior and reproducing the proprietary metrics

Design note on the next iteration of the computed RAPM. Internal analyst tier:
technical shorthand is fine. Captures the discussion of what a box-score prior
would be, how to wire it in, and how close we can get to EPM / LEBRON / RPM /
DARKO / RAPTOR.

## Where we are now

RAPM is computed from play-by-play for 2013-14 through 2025-26 (ridge with a
cross-validated penalty, possessions reconstructed with box-score starters). The
current version is **bare single-season RAPM with a zero-mean prior**: in the
absence of lineup data every player is assumed average. That is the noisy version
every serious metric improves on. The tell is the 2024-25 top: Isaiah Joe (a
reserve) at #1 and a cluster of role-player bigs ahead of the stars. One season
of lineup data cannot separate a player's impact from the quality of the lineups
they happened to share the floor with.

Only the combined RAPM feeds the consensus; the offense/defense splits are kept
out so a noisy single-season split cannot swing the headline order.

## The prior is already in the codebase: BPM

A box-score prior is a per-player estimate of impact per 100 possessions built
from box-score stats, used as the center the ridge shrinks toward instead of
zero. That is exactly what a Statistical Plus/Minus (SPM) model is, and our
recomputed **BPM 2.0** (`nbakit.ratings.bpm`, already in the unified table,
already on a points-per-100 scale) is one. It is the documented public analog of
what the proprietary metrics use internally:

- EPM: its own optimized SPM prior (plus tracking)
- LEBRON: PIPM coefficients as the prior
- RPM (Engelmann): an SPM prior
- BPM: the reproducible version of the same idea

BPM and our raw RAPM agree at only ~0.23 (rank), so using BPM as the prior would
move the noisy low-possession players a lot (pulling Isaiah Joe down hard) while
barely touching a 2,500-minute star. That is the desired behavior.

Caveat: our recomputed BPM absolute values are approximations (see the findings
note on the recomputed formulas). For a prior, the scale should be sanity-checked
or lightly calibrated against published BPM before trusting the absolute output.

## How to wire a prior into the existing ridge

Prior-mean ridge minimizes

```
Sum (y - X beta)^2 + lambda * Sum (beta_i - prior_i)^2
```

No new solver is needed. Substitute `gamma = beta - prior`:

1. Form each player's prior contribution and the residual target
   `y' = y - X . prior`.
2. Run the existing zero-mean `RidgeCV` on `y'` to get `gamma`.
3. Add back: `beta = gamma + prior`.

Low-possession players (small, noisy `gamma`) collapse onto their BPM; heavy-
minute players move far from it. This is roughly 20 lines on top of `rapm()`
(add a `prior=` argument; map each player's BPM onto the design-matrix columns).

## The bigger lever: multi-year pooling

The prior is the second most important fix. The first is **pooling 2 to 3
seasons of possessions** into one regression, often with recency weighting, which
is what RPM / EPM / RAPTOR all do. We now have 13 seasons of play-by-play cached,
so this is immediately doable and would cut the single-season noise more than the
prior alone. Prior plus multi-year pooling together is what makes these metrics
stable.

## Can we reproduce a proprietary metric?

The structure, yes; the exact metric, no. We can build a credible prior-informed,
multi-year, regularized RAPM that captures what makes EPM / RPM / LEBRON good.
What we cannot replicate is the proprietary inputs.

| Metric | What we can match | The gap we cannot close |
|---|---|---|
| RPM (Engelmann) | Essentially all of it: RAPM + SPM prior + multi-year. Closest to reproducible. | His exact SPM coefficients; also defunct. |
| EPM | RAPM backbone + BPM-as-prior | Player-tracking inputs (Second Spectrum) and the per-stat stabilization weighting that is its actual edge |
| LEBRON | RAPM + prior structure | "Luck adjustment" needs shot-quality / expected-points data; PIPM prior uses tracking |
| DARKO | — | A different animal: a Kalman-filter daily now-cast, not a season RAPM. Needs per-game sequential modeling. |
| RAPTOR | on/off component | tracking-based offensive/defensive priors |

The wall for all of them is **player-tracking data** (speed, distance, shot
quality, matchup data), which is proprietary. A luck adjustment needs
expected-points-per-shot, which we only partially have via the cached
shot-location data (not true shot quality).

## Recommended path

Build an honest "RPM/EPM-like" metric, in order of leverage:

1. **Multi-year pooling** (2 to 3 seasons of possessions, recency-weighted). Data
   is already cached.
2. **BPM box-score prior** via the prior-mean ridge substitution above.
3. **Validation** against a public RAPM snapshot dropped at
   `cache/rapm_snapshot_{season}.csv` (activates the existing computed-vs-public
   guard, `rapm_val_reasonable`, r > 0.70).
4. Optional, partial: a **luck adjustment** using cached shot-location data as a
   rough expected-points proxy. Not full shot quality.

Expected outcome: the top tier sharpens to recognizable stars rather than
single-season role-player noise, while RAPM keeps the independent signal it adds
over the box scores. We can call it RPM/EPM-like, not EPM or LEBRON itself,
because the tracking data and bespoke tuning are not ours to reproduce.
