# NBA Home Court Advantage — Findings

Narrative interpretation of the analysis. For the actual regression tables and
coefficient values, see `RESULTS.md` (auto-generated each run).

---

## The Decline

Home court advantage has been falling for 40 years in both the regular season
and the playoffs, with the playoff decline steeper than the regular-season one.
The gap between the two has nearly closed in recent seasons.

The 2020 bubble season (neutral-site playoffs) is excluded from playoff stats.
COVID seasons are flagged in the charts and regression as an anomaly.

---

## What Explains It

A game-level logistic regression (outcome: home win) with era dummies, rest
differential, altitude, time-zone differential, and a COVID flag shows that:

**Era (structural decline) dominates.** The era dummies account for the majority
of total model fit. The decline is not explained by rest, altitude, or travel —
it is a structural trend that has unfolded across every rule-change era.

**Rest matters in both contexts, more so in the playoffs.** When the home team
has more rest than the road team, home win probability rises. The per-day effect
is larger in the playoffs than in the regular season — higher stakes amplify
fatigue. Rest explains a meaningful share of model fit on top of the era effect.

**Altitude is real in the regular season, absent in the playoffs.** Denver and
Utah carry a significant home edge in the regular season. In the playoffs the
effect disappears — team quality is a confound when those franchises are strong
enough to host playoff games.

**Time zone differences are not significant in either context.** There are too
few coast-to-coast playoff matchups across 42 seasons for reliable inference,
and the regular-season effect is also not significant.

**The post-2014 level shift is confirmed.** Splitting the sample at the 2014
Finals format change shows the overall home-win probability dropped significantly
after 2014. Coefficients on rest, altitude, and time zone are broadly stable
across the split — those factors did not drive the post-2014 decline.

---

## Mechanisms: Why Is Home Court Advantage Shrinking?

Three box-score differentials (home minus away) show statistically significant
trends over time:

**Foul differential — referees are calling the game more neutrally.**
Home teams were called for substantially fewer fouls per game in the early era
than they are today, in both the regular season and the playoffs. This is the
single strongest mechanism. The trend is highly significant in both contexts.

**eFG% differential — the home shooting edge is shrinking.**
Home teams used to shoot meaningfully more efficiently than road teams. That
gap has narrowed significantly in the regular season. This reflects both the
foul trend (fewer free throws for the home team) and convergence in shot quality.

**3PA rate differential — shot selection has converged.**
Road teams used to take proportionally fewer 3-point attempts than home teams.
As the 3-point revolution normalized high-volume shooting league-wide, that
difference has closed. Shot selection is no longer a meaningful home court edge.

FG% (unweighted) is also narrowing. FT% and 3P% show no significant trend.

---

## Shot Zone Analysis

Paint access (restricted area + non-RA combined) shows the clearest pattern:
home teams have historically taken a higher share of shots from the paint —
the most efficient shots in basketball — and that gap is closing. This is
consistent with both the eFG% narrowing and the foul differential trend.

Road teams consistently take a higher share of mid-range shots, but that gap
is relatively stable. Corner 3 and above-break 3 show no systematic home/road
difference throughout the dataset.

Shot zone data is only available from ~1996-97 onward.

---

## Summary

The core story: home court advantage has eroded because **referees call the game
more neutrally** than they did 40 years ago, **home teams no longer generate a
disproportionate paint-access or shooting edge**, and **the 3-point revolution
has equalized shot selection** between home and road teams. Rest matters but
cannot explain the secular decline. Altitude is real in the regular season.
Time-zone travel is not a significant factor.

For specific coefficient values, effect sizes, significance levels, and era
breakdowns, see `RESULTS.md`.
