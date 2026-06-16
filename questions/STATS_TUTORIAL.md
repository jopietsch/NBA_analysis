# Statistics Tutorial — Reading the NBA Analyses

A teaching companion to the `RESULTS.md` files in this project. The goal: if
you've taken one or two statistics courses but wouldn't call yourself an expert,
this should let you understand *every* number in the results files — what it is,
why we used it, and how to read it without being fooled.

It covers two analyses:

- **Home court advantage** (`home_court/`) — why HCA fell over 40 years, what
  drives it, and what's a red herring. Heavy inference: logistic regression, trend
  tests, mediation decompositions, quantile regression.
- **2025-26 Knicks historically** (`knicks_2026_historic/`) — was the playoff run
  all-time dominant? Lighter methods: percentile ranking, SRS, schedule-adjusted
  margin.

It's organized **by method, not by section**, because the same handful of tools
show up over and over. Learn logistic regression once and you've unlocked ten
sections of the home-court results. Where it helps, each method is illustrated
with *actual numbers from this project* — many worked examples reproduce a row of
`RESULTS.md` exactly so you can check the arithmetic yourself.

Companion docs:
- `home_court/STATS_EXPLAINER.md` — goes section-by-section through the home-court
  `RESULTS.md` using full statistical vocabulary; explains *why each section's
  figure takes the form it does*. Read that *after* this once the vocabulary is
  familiar.
- `knicks_2026_historic/STATS_EXPLAINER.md` — same role for the Knicks analysis.
- `home_court/FINDINGS.md` / `knicks_2026_historic/FINDINGS.md` — plain-English
  narratives with no jargon.

---

## How to use this tutorial

Each method follows the same template:

> **The question it answers** → **The intuition** → **The mechanics (lightly)** →
> **A worked example from our data** → **How to read it in `RESULTS.md`** →
> **The trap it avoids**

You do not have to read in order, but Part 0 (Foundations) underlies everything
else, so start there.

**Contents**

- **Part 0 — Foundations:** probability vs. odds vs. log-odds; percentage points;
  p-values, confidence intervals, and significance stars; statistical vs.
  practical significance.
- **Part 1 — Describing and comparing groups:** fitting a trend line (OLS);
  two-proportion z-test; chi-square test; Pearson vs. Spearman correlation.
- **Part 2 — Modeling a yes/no outcome:** logistic regression; turning log-odds
  into percentage points; binomial GLM; the linear probability model; McFadden
  pseudo-R².
- **Part 3 — Getting the uncertainty right:** why naive standard errors lie;
  cluster-robust SEs; HAC/Newey-West SEs; multiple comparisons and
  Benjamini-Hochberg.
- **Part 4 — Comparing models and splitting up credit:** the likelihood-ratio
  test; sequential delta-R² vs. Shapley; the mediation accounting identities.
- **Part 5 — Looking beyond the average:** quantile regression and polarization.
- **Part 6 — Ranking noisy things fairly:** variance decomposition and
  empirical-Bayes shrinkage.
- **Part 7 — Avoiding the classic traps:** confounders and controls; spurious
  correlation from shared trends (and how detrending fixes it); reverse
  causality and the leave-one-out trick; interaction terms.
- **Part 8 — Ranking a single team historically:** empirical percentile rank;
  SRS (Simple Rating System); schedule-adjusted margin.

---

# Part 0 — Foundations

## 0.1 Probability, odds, and log-odds

Almost every model in this project predicts one thing: **did the home team win?**
That's a yes/no (1/0) outcome. Three different ways of expressing "how likely"
show up in the results, and you need all three.

- **Probability** is the everyday one: the home team wins **60.1%** of regular-season
  games, so *p* = 0.601.
- **Odds** = *p* / (1 - *p*). At *p* = 0.601 the odds are 0.601 / 0.399 = **1.51**
  -- "about 1.5 to 1 in favor." Odds run from 0 to infinity, with 1.0 meaning a
  coin flip.
- **Log-odds** (also called the **logit**) = the natural log of the odds:
  ln(1.51) = **+0.410**. Log-odds run from -inf to +inf, with **0 meaning a coin
  flip**, positive favoring the home team, negative favoring the road team.

Why bother with the awkward log-odds scale? Because it's symmetric and unbounded,
which makes it the natural scale for regression. A model can add and subtract
log-odds freely without ever producing an impossible probability like 1.2 or
-0.3. The cost is that log-odds aren't intuitive -- which is why we always
translate them back to percentage points (see §2.2).

```
 probability    0% ......... 50% ......... 100%
 odds            0 ......... 1.0 ......... inf
 log-odds       -inf ........ 0 .......... +inf   <- the modeling scale
```

When `RESULTS.md` says a coefficient is "+0.065 log-odds per day" of rest and
then "~+1.6 pp," it computed the log-odds first and translated to percentage
points for you. §2.2 shows exactly how.

## 0.2 Percentage points (pp) vs. percent

A small but constant source of confusion. If the home win rate falls from 65% to
55%, that is a drop of **10 percentage points (pp)**, *not* 10%. (As a *percent*
of 65 it's about a 15% relative drop.) This project always speaks in **percentage
points** to avoid the ambiguity. "-0.244 pp/yr" means the home win rate loses
about a quarter of a percentage point each year. Over 43 seasons that's
~-10 pp -- from ~65% down to ~55%.

## 0.3 p-values, confidence intervals, and those `*` `**` `***` stars

Every result carries a measure of "could this just be luck?"

- A **p-value** answers: *if there were truly no effect, how often would random
  chance alone produce a result at least this extreme?* Small p = "chance is an
  unlikely explanation." The conventional thresholds, shown as stars in the
  tables:

  | stars | p-value | rough meaning |
  |-------|---------|---------------|
  | `*`   | < 0.05  | unlikely to be pure chance |
  | `**`  | < 0.01  | quite unlikely |
  | `***` | < 0.001 | extremely unlikely |
  | (none)| >= 0.05 | can't rule out chance |

- A **confidence interval (CI)** is usually more informative than the p-value. A
  "95% CI" is a range that would contain the true value 95% of the time if we
  repeated the study. When `RESULTS.md` reports the regular-season decline as
  **-0.244 pp/yr, 95% CI [-0.280, -0.209]**, it's saying: the true slope is
  almost certainly somewhere in that narrow band, and the *whole band is
  negative*, so the decline is real. **A 95% CI that excludes 0 is equivalent to
  p < 0.05** -- but the CI also tells you the *size* and *precision* of the
  effect, which a lone p-value hides.

Read CIs first. "Significant" with a CI of [+0.5, +20] is a barely-detected,
wildly-uncertain effect; "significant" with [+8.0, +8.4] is a precisely-pinned
one. Same star count, very different findings.

## 0.4 Statistical significance vs. practical importance

With 49,107 games, this project can detect effects far too small to matter. The
travel-distance result (§ Travel in `RESULTS.md`) is the textbook case:
**p = 0.010** (a `*`), but the effect is **-0.07 pp per 100 miles** -- a brutal
2,500-mile cross-country trip costs the visitor under 2 pp, and the win-rate
buckets don't even fall in order. The lesson appears repeatedly here: **with huge
samples, significance is cheap; always check the effect size.** Conversely, a big
effect with a fat CI (most single-era playoff numbers) may be real but
unproven -- the sample is just too small.

---

# Part 1 — Describing and comparing groups

## 1.1 Fitting a trend line (Ordinary Least Squares, "OLS")

**The question:** is something drifting up or down over time, and how fast?

**The intuition.** OLS draws the single straight line that comes closest to all
the points, where "closest" means it minimizes the sum of the *squared* vertical
distances from points to line. (Squaring punishes big misses and makes the math
clean.) The line's **slope** is the headline: how much the *y* value changes for
each one-unit step in *x*.

**A worked example.** Take one dot per season -- the home win % -- and fit a line
against the year. That's the regular-season decline: a slope of **-0.250 pp per
year** (the OLS line in `RESULTS.md`'s decline section). The
`nba_home_court_advantage_season.png` figure is literally this line drawn through
the season dots.

![Season-level home win % with fitted decline](home_court/generated/nba_home_court_advantage_season.png)

**R² -- how tight is the fit?** Alongside the slope you'll see **R² = 0.745**.
R² ("R-squared") is the share of the up-and-down variation in the points that the
line explains, from 0 (line tells you nothing) to 1 (points sit exactly on the
line). 0.74 means *year alone* accounts for nearly three-quarters of why some
seasons have higher HCA than others -- a strong, clean trend. Contrast the
playoffs: same kind of line, but **R² = 0.20**, because each playoff season is
only ~80 games, so the dots scatter much more around the trend.

**How to read it in `RESULTS.md`:** look for "Trend/yr" rows and "slope" /
"pp/yr" language. The stars next to a slope test the hypothesis "the true slope
is zero (flat)."

**The trap it avoids -- and one it can fall into.** A trend line summarizes
direction honestly, but plain OLS assumes the points are independent. Season win
rates are *not* independent (a high-HCA season tends to follow a high-HCA season),
which makes naive OLS error bars too optimistic. The fix is **HAC standard
errors** -- see §3.3.

## 1.2 The two-proportion z-test

**The question:** two groups each have a yes/no rate (here, a home win %). Is the
gap between them more than chance?

**The intuition.** Each observed rate is a little fuzzy because it's based on a
finite number of games. The z-test asks whether the gap between the two rates is
large *relative to that fuzziness*. Big gap + lots of games = confident the
difference is real.

**The mechanics (lightly).** Pool the two groups to estimate a common rate
p_pool, compute the standard error of the difference, and form

```
        p1 - p2
z = ──────────────────────────── ,     p-value from the normal curve
    sqrt[ p_pool*(1-p_pool)*(1/n1 + 1/n2) ]
```

**A worked example -- reproducing a `RESULTS.md` row.** The era analysis compares
the first two regular-season eras: 1984-94 at **64.9%** (n = 11,275) vs. 1995-01
at **59.9%** (n = 7,777).

- Pooled rate: p_pool = (0.649*11275 + 0.599*7777) / 19052 = **0.629**
- SE = sqrt[0.629*0.371*(1/11275 + 1/7777)] = **0.0071**
- z = (0.649 - 0.599) / 0.0071 = **+7.0**

`RESULTS.md` reports **z = +6.95, p < 0.001 ****** for that boundary (the tiny
difference is rounding the displayed percentages). A z of ~7 is enormous -- this
-4.9 pp drop at the 1994-95 hand-checking rule change is rock solid.

**How to read it in `RESULTS.md`:** the "Consecutive eras -- two-proportion
z-tests" and "format period" blocks. Each line is one boundary.

**The trap it avoids... and the bigger trap it *doesn't*.** The z-test cleanly
tells you two rates differ. It does **not** tell you the rule change *caused* the
drop -- because HCA was sliding the whole time anyway, *any* later period looks
lower. Separating "these two periods differ" from "the boundary itself did
something" needs the LR test in §4.1. This distinction is the spine of the whole
project; keep it in mind.

## 1.3 The chi-square test

**The question:** across several categories, are the yes/no rates all the same,
or do they differ somewhere?

**The intuition.** The z-test compares *two* groups; chi-square generalizes to
*many* at once. It compares the counts you actually observed to the counts you'd
*expect* if every category had the identical rate. The bigger the total mismatch,
the bigger the chi-square statistic, the smaller the p-value.

**The mechanics (lightly).** chi-sq = sum (observed - expected)^2 / expected,
summed over every cell of the table. It's tested against the chi-square
distribution with "degrees of freedom" = (number of categories - 1) for a simple
rate comparison.

**A worked example.** The rest-bucket analysis splits regular-season games into
three buckets -- away more rested (57.6% home wins), equal rest (59.3%), home more
rested (62.8%) -- and asks "are these three really different?" Result:
**chi-sq(2) = 79.2, p < 0.001.** The "(2)" is the degrees of freedom (3 buckets
- 1). A chi-sq of 78 on 2 df is far out in the tail: rest clearly shifts the
home win rate.

The playoff series-structure section uses the same test across the seven game
numbers G1-G7: **chi-sq(6) = 84.5, p < 0.001** -- home win % is emphatically
*not* uniform across game numbers (it swings from 55% to 75% depending on which
arena hosts).

**The trap it avoids.** Running a separate z-test for every pair of categories
inflates your chance of a false positive (see §3.4). Chi-square asks the single
honest question "is there *any* difference among these groups?" in one test.

**Its limit:** chi-square tells you a difference exists *somewhere*; it doesn't
tell you *where* or *which direction*. That's why `RESULTS.md` pairs it with the
bucket table (to see the pattern) and, for series games, notes the pattern is
venue alternation rather than a trend.

## 1.4 Correlation: Pearson vs. Spearman

**The question:** do two measured quantities move together?

**The intuition.** A **correlation coefficient** runs from -1 to +1. +1 = perfect
lockstep, -1 = perfect opposition, 0 = no linear relationship. It's a unitless
summary of "as one goes up, does the other?"

**The two flavors, and why both are reported:**

- **Pearson r** measures *linear* association -- how close the dots sit to a
  straight line. Sensitive to outliers and assumes the relationship is roughly
  straight.
- **Spearman rho** does the same thing on the *ranks* of the data instead of the
  raw values. It catches any *monotonic* relationship (consistently up-together,
  even if curved) and shrugs off outliers. When Pearson and Spearman agree, the
  relationship is robust; when they diverge, an outlier or a curve is doing the
  work.

**A worked example.** Season 3-point rate vs. season home win %:
**Pearson r = -0.902, Spearman rho = -0.890** (both p < 0.001). Nearly identical
and both near -0.9 -- a very strong, very robust "more threes, less home
advantage" pattern at the season level. Compare the franchise-consistency
section, where raw **Pearson = +0.362 (p = 0.042)** but **Spearman = +0.275
(p = 0.128)** -- they *disagree*, so the relationship is fragile and shouldn't be
leaned on.

**The trap it avoids -- but also sets.** Reporting both guards against being
fooled by an outlier or a curve. But correlation has its own famous trap:
**two things that both drift over time will correlate even if unrelated** (ice
cream sales and drownings both rise in summer). That r = -0.90 for threes is
*mostly that trap* until we control for it -- which is exactly what §7.2
(detrending) and the within-era logit in §2.1 are for. Correlation alone is
never the end of the story in this project.

---

# Part 2 — Modeling a yes/no outcome

## 2.1 Logistic regression (the workhorse)

**The question:** how does the chance of the home team winning depend on one or
more factors (rest, altitude, era, ...)?

**Why not just fit a straight line to win/loss?** A straight line through 0/1
outcomes will happily predict a 130% or a -20% win probability for extreme
inputs, which is nonsense. **Logistic regression** fixes this by modeling the
**log-odds** (§0.1) as a straight line, then bending it back into a valid 0-1
probability with the S-shaped logistic curve. Predictions can never escape [0, 1].

```
 P(home win)
   1 |                         ........
     |                  ......
 0.5 |            ......              <- steepest near 50/50
     |     ......
   0 |......
     -------------------------------------------------
        favors road  <--  log-odds  -->  favors home
```

![The logistic curve: log-odds map to probability](generated/tutorial_logistic_curve.png)

The green arrows make the key quirk visible: **the same +1 step in log-odds is
worth ~23 pp near a 50/50 game but only ~5 pp out in the tail.** That's why
coefficients get translated to percentage points *at the average win rate*
(§2.2) -- the pp value of a log-odds effect depends on where on the curve you are.

**Reading a coefficient.** Each coefficient is *the change in log-odds* for a
one-unit change in that factor, holding the others fixed. Sign is what you read
first: **positive = helps the home team, negative = hurts.** The raw size is on
the log-odds scale, so the code also gives you the percentage-point translation
(§2.2).

**"Bivariate" vs. "controlling for...".** A *bivariate* logistic uses one
predictor alone ("does rest matter at all?"). Adding more predictors lets you ask
"does this factor matter *holding the others constant?*" The single most important
move in the whole project is **"controlling for era":** running
`home_win ~ 3PA_rate` alone gives -2.64 pp per 10 pp of threes, but adding
`+ C(era)` -- comparing only games *within the same era* -- barely changes it
(-2.27 pp). That tells you the 3PA effect isn't just the shared time trend; it
holds game-to-game even inside a fixed era. (More on this logic in §7.2.)

**`C(era)` and "dummy variables."** A category like era can't go into a regression
as a number. Instead each era becomes its own 0/1 ("dummy") column, measured
against a left-out **reference** era (here 1984-94). So "era: 2023-26 = -0.375
log-odds (~-9.0 pp)" means: relative to 1984-94, the 2023-26 era sits 9.0 pp
lower, after the other factors are accounted for.

**How to read it in `RESULTS.md`:** any block with "log-odds" and "~pp" columns.
Read sign -> significance (stars/CI) -> the pp translation for size.

## 2.2 Turning log-odds into percentage points

This one formula demystifies half the tables. A log-odds coefficient is converted
to an approximate effect in percentage points using the slope of the logistic
curve at the average win rate p_avg:

```
pp  ~  coef * p_avg * (1 - p_avg) * 100
```

The p_avg*(1-p_avg) factor is the curve's steepness -- effects translate to the
most percentage points near a 50/50 race and get squeezed near 0% or 100%.

**Worked example (reproduces a row exactly).** Regular-season p_avg = 0.601, so
p_avg*(1-p_avg) = 0.240. The rest coefficient is **+0.065 log-odds per day**:

```
0.065 * 0.240 * 100  ~  +1.6 pp per day
```

-- exactly the "~+1.6 pp" you see next to it. Now you can sanity-check any
log-odds-to-pp conversion in the file yourself.

## 2.3 The binomial GLM

**The question:** same as the trend line -- is the season-by-season decline real
-- but done with the *statistically correct* model for proportions.

**The intuition.** Instead of treating each season's win *percentage* as a plain
number and drawing an OLS line through it, the binomial GLM models the underlying
**(wins out of games)** counts directly. Two automatic benefits: (1) seasons with
more games get more weight (a 1,230-game season should count more than a
shortened one), and (2) the math knows that a proportion's variability depends on
the proportion itself (a rate near 50% is noisier than one near 95%). "GLM" =
*generalized* linear model; the binomial version is logistic regression's
season-aggregated cousin.

**Why it's run alongside OLS.** The decline section reports *both* the binomial
GLM (**-0.244 pp/yr**) and the OLS/HAC line (**-0.250 pp/yr**). They land in
essentially the same place. That agreement is the point: **when the rigorous model
and the familiar straight line agree, the finding doesn't hinge on a modeling
choice.** This "two methods, same answer" pattern is a credibility move you'll see
throughout.

## 2.4 The linear probability model (LPM)

**The question:** when you need contributions that *add up exactly*, how do you
model a 0/1 outcome?

**The intuition.** The LPM is the "wrong" model done deliberately: plain OLS with
the 0/1 win as the *y*. Its known flaw -- it can predict probabilities outside
[0, 1] -- genuinely doesn't matter when you don't care about individual
predictions. What you gain is **additivity**: the coefficients combine by simple
addition, so you can split the home edge into channel-by-channel pieces that sum
to the exact total. A logistic model's S-curve is nonlinear and *cannot* give you
that clean sum. (See §4.3, the mediation decomposition, for the payoff.)

**How to read it in `RESULTS.md`:** the mediation section. When you see
contributions that total to "100% of the level" and "95% of the trend," an LPM
made that exact bookkeeping possible.

## 2.5 McFadden's pseudo-R²

**The question:** how much does a logistic model explain -- the logit's answer to
"R²"?

**The catch you must internalize.** Ordinary R² (§1.1) doesn't exist for logistic
regression, so we use **McFadden's pseudo-R² = 1 - (model log-likelihood / empty
model log-likelihood)**. Critically, **its numbers are nowhere near linear R²**.
A McFadden R² of **0.05** can represent a strong, important model. In
`RESULTS.md` you'll see values like **0.0028** or **0.0675** -- those are not
"the model explains 0.3% of anything" in the everyday sense.

**The rule:** *never* read a McFadden value as an absolute percentage. Only read
it in **relative** terms -- "block A adds twice the delta-R² of block B," or
"quality control left 101% of the year trend intact." The sequential decomposition
(§4.2) uses exactly these relative comparisons and never quotes the raw level as
if it were ordinary R².

---

# Part 3 — Getting the uncertainty right

The point estimates (slopes, win rates) are often the easy part. Half of careful
statistics is computing *honest error bars*. Three situations in this project
break the textbook assumptions, and each has a fix.

## 3.1 Why naive standard errors lie

Standard error formulas assume every observation is an **independent** draw. When
observations are secretly related, the formula thinks you have more independent
information than you really do, so it reports error bars that are too narrow and
p-values that are too small -- you get false confidence. The next two methods
patch the two ways independence breaks here.

## 3.2 Cluster-robust standard errors (clustering on season)

**The problem.** In a game-level model pooling 47,000 games across 43 seasons,
games *within the same season* share that season's league-wide conditions (the
rules, the ball, the officiating climate). They're not 47,000 independent facts;
they're more like 42 seasons' worth of correlated games. Treat them as fully
independent and your error bars shrink too far.

**The fix.** **Cluster-robust standard errors** group the games into clusters --
here, one cluster per season-year -- and compute uncertainty *between* clusters
rather than pretending every game is its own island. The point estimate doesn't
change; the error bars get appropriately wider and the p-values more honest.

**How to read it in `RESULTS.md`:** wherever a game-level model says
"cluster-robust SEs by season" (the mediation, decomposition, travel, 3PA, and
pace sections). You don't do anything differently -- just know the CIs already
account for the fact that seasons, not games, are the truly independent unit.

## 3.3 HAC (Newey-West) standard errors

**The problem (time-series version).** Season-level series are **autocorrelated**:
a high-HCA season tends to be followed by another high-HCA season. Consecutive
points carry overlapping information, so -- again -- naive OLS error bars are too
tight.

**The fix.** **HAC** ("heteroskedasticity- and autocorrelation-consistent"), a.k.a.
**Newey-West**, standard errors widen the error bars to account for that
year-to-year carryover. The "maxlags = 1" you see means it corrects for
correlation between a season and the one immediately adjacent.

**How to read it in `RESULTS.md`:** the decline section's "OLS / HAC" line. The
slope is the same line you'd draw by eye; the *inference* (its CI and p-value)
has been made robust to the fact that seasons aren't independent. It's the
time-series sibling of clustering (§3.2): both stop you from over-trusting
correlated data.

## 3.4 Multiple comparisons and Benjamini-Hochberg

**The problem.** Run *one* test at p < 0.05 and there's a 5% false-alarm rate.
Run *47* tests -- one per playoff referee -- and you'd expect about **two** to
clear p < 0.05 **by pure luck**, even if no referee were biased at all. Naively
counting "significant" referees over-counts.

**The fix.** The **Benjamini-Hochberg (BH)** procedure controls the **false
discovery rate** -- it adjusts the threshold so that, among the tests you *call*
significant, only ~5% are expected to be false alarms. It's less brutal than the
old Bonferroni "divide by the number of tests" rule, which keeps useful power
when you have real effects.

**Why it's the punchline of the referee section, not a footnote.** A raw
leaderboard of 47 noisy referee means *will* manufacture a "most biased ref"
headline. BH is what lets `RESULTS.md` say something trustworthy:
**29 of 47 officials are individually significant, and all 29 survive BH
correction.** That "survives correction" is the signature of a *real, widespread*
effect rather than a few lucky draws -- exactly the universal (not a-few-bad-apples)
home-foul bias the analysis concludes.

---

# Part 4 — Comparing models and splitting up credit

## 4.1 The likelihood-ratio (LR) test

**The question:** does adding a *block* of variables (all the era dummies, all the
format-period dummies) genuinely improve the model, or are they just decoration?

**The intuition.** Fit two **nested** models: a small one (`home_win ~ year`) and
a bigger one that adds the block (`home_win ~ year + C(era)`). The bigger model
will *always* fit the data at least slightly better -- more knobs always help a
little. The LR test asks whether it fits **enough** better to justify the extra
knobs, or just the amount you'd expect from random wiggle room.

**The mechanics (lightly).** The statistic is 2*(log-likelihood difference),
compared against a chi-square distribution with df = number of variables added. A
small p-value = "the block earns its place."

**The worked example that defines the project.** This is the formal version of the
§1.2 caution. The era section asks: beyond the smooth year-by-year drift, did
specific rule-change eras cause *extra* jumps?

- **Regular season:** LR test **chi-sq(5) = 20.68, p < 0.001** -> the era dummies
  *do* add real explanatory power. There's a genuine discrete drop (at 1994-95)
  on top of the smooth slide.
- **Playoffs:** LR test **chi-sq(5) = 2.24, p = 0.815** -> the era dummies add
  nothing. The playoff decline is a *pure smooth drift* with no rule-change
  fingerprints.

Same logic exonerates the 2014 playoff format change: the raw z-test showed a
scary **-6.8 pp** drop at 2014, but once the year trend is in the model the LR
test for the format dummies is **p = 0.197** -- the "drop" is just the steady
decline passing through that year, not the schedule change doing anything.

**The trap it avoids.** It separates "this period is lower" (a raw difference,
which the ever-present downward trend guarantees) from "this boundary *itself*
moved the needle." If you remember one idea from this tutorial, make it this one
-- it recurs in the era, format, and (implicitly) the decomposition sections.

## 4.2 Splitting up R²: sequential vs. Shapley

**The question:** five factors jointly explain the regular-season decline. How
much credit does *each* deserve?

**The naive way (sequential), and its flaw.** Add factors one at a time and record
how much each *new* one bumps the (pseudo-)R². The problem: **whoever goes first
hogs the shared credit.** Era and altitude both partly track the same teams; if
era is entered first, it absorbs the overlap and looks bigger than it should.

In `RESULTS.md`, era entered first gets a **57.9%** sequential share.

**The fair way (Shapley).** Borrowed from game theory, the **Shapley value** asks:
average each factor's contribution **over every possible order** of entry (all
2^5 = 32 subset models). No factor gets the artificial first-mover bonus; shared
credit is split evenly. Era's honest **Shapley share drops to 52.6%** -- still
half the story, but the inflation from going first is removed.

**How to read it in `RESULTS.md`:** the decomposition section lists both columns
side by side precisely so you can see how much the ordering mattered (here, era
was modestly inflated; altitude and rest barely moved). When they're close,
ordering didn't matter and you can trust either; when they diverge, trust Shapley.

**The takeaway it supports.** Era (the structural decline) ~53%, situational
factors (rest, altitude, time zone, COVID) ~47%. And since none of those
situational factors *changed* over time (§7 and the stability tests), they explain
*which games* are won, not *why HCA fell* -- half the explanatory power belongs
to the era structure itself.

## 4.3 Mediation: the level and trend accounting identities

**The question:** the home edge shows up in the box score as better shooting,
fewer fouls called, fewer turnovers, more rebounds. How much of the home edge --
and of its *decline* -- flows through each of those four channels?

**Why it needs the LPM (§2.4).** Because the answer is an **exact decomposition**:
the channel contributions must sum to the totals. Only a *linear* model
(additivity) makes that possible. Two identities do the work:

**Level identity** -- split the home edge (the 10.1 pp *above* a coin flip) into
channels:

```
mean win %  =  intercept  +  sum( coef * mean channel difference )
```

Each channel's contribution = how much the home team is ahead on that channel
(`mean diff`) times how much a unit of it is worth (`coef`). For the regular
season:

| channel | contribution | share of the +10.1 pp edge |
|---|---|---|
| shooting (eFG%) | +4.4 pp | 43% |
| rebounds | +2.5 pp | 25% |
| fouls (carries free throws) | +1.4 pp | 14% |
| turnovers | +1.3 pp | 13% |
| unexplained | +0.5 pp | 5% |

The four measurable channels reconstruct **95%** of the home edge.

**Trend identity** -- split the *decline* the same way, using each channel's own
year-trend:

```
total pp/yr  =  unmediated pp/yr  +  sum( coef * channel's trend per year )
```

**Worked check (reproduces a row).** Shooting is worth **+3.42 pp** per pp of
eFG% edge, and that eFG% edge is shrinking at **-0.0151 pp/yr**. Multiply:
3.42 * (-0.0151) ~ **-0.0516 pp/yr** -- exactly the shooting channel's reported
contribution to the decline. Sum all four channels and you recover **96%** of the
regular-season -0.244 pp/yr slide; only 4% is "unmediated."

**The honesty label you must respect.** `RESULTS.md` calls these channels
**proximate** and the level/trend split an **accounting decomposition, not
causation**. A 27% "share" tells you *where* the change shows up in the box score,
not *why* it happened -- and on its own it can't tell you whether two channels are
independent stories or both downstream of one deeper cause. A decomposition just
hands each channel its slice; you need a further test to probe what's behind it.

**Going one step further -- the 3PA-control diagnostic.** The obvious worry: maybe
the rebounding and turnover slices are really just the three-point revolution
wearing different hats. The section now tests this head-on. For each channel it
refits the channel's *year-trend* twice -- `channel ~ year` and
`channel ~ year + 3PA rate` -- and reports how much of the trend the 3PA control
**absorbs**. (It uses game-to-game 3PA variation *within* a season, which gives
the control real bite; season averages alone would be nearly interchangeable with
the calendar.)

The logic is **asymmetric**, and it's worth understanding why. A trend that
*survives* the control is **strong** evidence of an independent driver -- it slid
for reasons threes don't explain. Heavy absorption is only **weak** evidence of
downstream-ness, because 3PA and the calendar march together (the §7.2
shared-trend trap), so the control can soak up a trend without genuinely
explaining it. Trust a survival; treat an absorption gently.

The four channels split three ways:

| channel | 3PA absorbs | verdict |
|---|---|---|
| shooting (eFG%) | ~210% (flips sign) | **fully downstream** -- the fading home shooting edge *is* the three-point story |
| rebounding | ~8%, still p < 0.001 | **independent** -- a genuine fourth strand of the decline |
| fouls / turnovers | ~51% / ~54% | **mixed** -- partly the perimeter shift, partly their own |

So the earlier "it's probably all downstream" hunch was half right (turnovers,
partly) and half wrong: **rebounding stands on its own**, and `FINDINGS.md` now
treats it as a separate driver. This is the template for going *past* a
decomposition -- when a share is ambiguous, add the suspected common cause as a
control and see what survives.

**Regular season vs. playoffs.** Channels carry 96% of the regular-season decline
but only **67%** of the playoff decline -- 33% of the playoff story runs outside
the box score (and folds in seed quality, which §7.1 isolates). The rebounding
fade, if anything, is sharper in the playoffs once 3PA is controlled.

---

# Part 5 — Looking beyond the average

## 5.1 Quantile regression and "polarization"

**The question:** is the *whole distribution* of game margins changing the same
way, or are its tails moving differently from its middle?

**Why averages aren't enough.** A trend line on the *average* margin (§1.1) tells
you the center is sliding, but it's blind to the *shape*. Two very different
worlds can share the same falling average: one where every game just gets a bit
closer, and one where blowouts in *both* directions get more common while the
average barely moves. You need to watch different parts of the distribution
separately.

**The intuition.** **Quantile regression** fits a separate trend line through a
chosen *percentile* of the outcome rather than the mean. The **Q10** line tracks
the 10th percentile (the home team's *worst* nights -- big losses); **Q90** tracks
the 90th (its *best* nights -- big wins); **Q50** is the median. Each gets its
own slope over the years.

**The two diagnostic patterns:**

```
  If all the quantile lines slide down in parallel:    the distribution just
                                                        shifted -- a pure "level"
                                                        change, nothing about
                                                        shape changed.

  If the bottom (Q10) falls while the top (Q90) rises:  the distribution is
                                                        spreading apart --
                                                        genuine polarization.
```

![Pure level shift vs. genuine polarization](generated/tutorial_quantile_diagnostic.png)

The left panel is the hypothetical "boring" outcome -- every quantile sliding down
in parallel at the median's rate. The right panel is the *actual* regular-season
data: the Q90 line tilts *up* while Q10 dives *down*, so the lines fan apart.
That fanning is polarization; parallel lines would have meant nothing about shape
changed.

**The worked example.** Regular-season margins:

| quantile | slope (pts/yr) | meaning |
|---|---|---|
| Q10 | **-0.167*** | the worst home losses are getting worse |
| Q50 | -0.053*** | median drifting down |
| Q90 | **+0.050 ** | the biggest home wins are getting bigger |

The top rises *as* the bottom falls. The spread between them (Q90 - Q10) widens
by **+0.22 pts/yr** -- confirmed **polarization**: home blowout wins *and* home
blowout losses are both becoming more common. The `nba_home_court_margin.png`
figure shows this fanning-apart visually.

**The trap it avoids -- this is the whole reason the section exists.** The simpler
margin analysis (§ Win Margin in `RESULTS.md`) split games into "home wins" and
"home losses" and found both groups' margins growing apart. But that split has a
**built-in artifact**: as the home win rate falls, games that used to be narrow
home *wins* flip into narrow home *losses*, which mechanically pushes the two
conditional averages apart *even if nothing about the distribution truly changed*.
Quantile regression looks at the *unconditional* distribution -- it never
conditions on who won -- so it **can't be fooled by games switching sides**. It
confirms the polarization is real, not bookkeeping.

---

# Part 6 — Ranking noisy things fairly

Two methods that always travel together, used anywhere `RESULTS.md` ranks a list
of noisy averages -- the 39 franchises and the 47 referees.

## 6.1 Variance decomposition (method of moments)

**The question, asked *before* you rank anything:** is there even any *real*
spread among these groups, or is the leaderboard entirely luck?

**The intuition.** The spread you *observe* across franchises is a mix of two
things:

```
observed variance  =  true between-group variance  +  average sampling noise
```

Sampling noise is the wobble you'd see even if every group were truly identical,
just because each is measured on a finite number of games -- and crucially, you
can *compute* it from the sample sizes. Subtract it from the observed spread and
what's left is an estimate of the **true** spread.

**Two worked examples that reach opposite conclusions:**

- **Regular-season franchises:** observed SD = 4.9 pp; sampling noise accounts for
  only **30%**; estimated true SD ~**4.1 pp**. (Check: 4.9^2 = 24.0,
  4.1^2 = 16.8, so noise = 7.2 = 30% of 24.0.) Real differences exist -- Denver
  and Utah genuinely have stronger home court (the altitude finding).
- **Playoff franchises:** observed SD = 8.0 pp, but sampling noise accounts for
  **100%** of it; true SD ~**0**. The entire playoff leaderboard spread is luck.
  No franchise has a *demonstrably* special playoff home court -- the samples
  (20-220 games) are just too small.

**The lesson:** always ask "is there real spread?" *before* ranking. If the answer
is "no" (playoffs), any ranking is noise dressed up as signal.

## 6.2 Empirical-Bayes shrinkage

**The question:** given that small-sample groups land at the extremes by luck,
how do you produce a leaderboard you'd actually bet on?

**The intuition.** **Pull each group's estimate toward the league average, by an
amount that depends on how noisy it is.** A franchise measured on 1,700 games
barely moves; one measured on 82 games gets yanked hard toward the middle, because
its extreme value is probably mostly luck. The pull weight is

```
weight = true variance / (true variance + that group's sampling variance)
```

-- reliable (low-noise) estimates keep most of their distinctiveness; noisy ones
mostly collapse to the average.

**A worked example that reproduces the table exactly.** Using the regular-season
true variance ~4.1^2 = 16.8 and the league mean +20.0 pp:

- **Kansas City Kings:** raw **+35.4** on just 82 games (sampling SE ~7.2 pp ->
  sampling var ~51.7). Weight = 16.8 / (16.8 + 51.7) = **0.245**, so shrunken
  = 20.0 + 0.245 * (35.4 - 20.0) = **+23.8 pp** -- pulled down 11.6 points,
  because that gaudy raw number rests on almost no data. Matches `RESULTS.md`.
- **Denver Nuggets:** raw **+27.9** on 1,730 games (sampling SE ~1.6 -> var ~2.7).
  Weight = 16.8 / (16.8 + 2.7) = **0.86**, so shrunken = 20.0 + 0.86 *
  (27.9 - 20.0) = **+26.8 pp** -- barely moves, and stays #1. Matches `RESULTS.md`.

That's the whole idea: shrinkage demotes lucky small samples (Kansas City) while
leaving well-measured ones (Denver) essentially untouched.

![Shrinkage pulls noisy estimates toward the league mean](generated/tutorial_shrinkage.png)

Read the figure as "length of the red arrow = how much we distrust the raw
number." Kansas City's huge error bar (only 82 games) earns an 11.6 pp pull;
Denver's tight bar (1,730 games) barely moves. The project's own
`nba_home_court_team_hca.png` shows the same raw-vs-shrunken comparison for all 39
franchises.

**And when there's no true spread (playoffs)?** Shrinkage collapses *every*
franchise to the league mean (+26.9 pp) -- which is the honest answer when the
variance decomposition already told you the true spread is zero. Utah's raw +39.7
and the Clippers' raw -3.6 are both just +26.9 once you account for their tiny
samples.

---

# Part 7 — Avoiding the classic traps

The previous parts were tools. This part is judgment -- the four ways an analysis
of observational sports data fools you, and the move that defuses each. These are
where the project earns its conclusions.

## 7.1 Confounders and controls

**The trap.** A factor looks important but is really a stand-in for something
else. **Playoff rest** is the case study: teams earn extra rest by *sweeping* a
series, and teams that sweep are *better* teams. So "well-rested home team wins"
might really be "better team wins" wearing a rest costume.

**The fix -- add a control.** Re-run the model with a measure of the confounder
included, and see if the suspect effect survives. Here the control is
**`quality_diff`** = the home team's regular-season win % minus the away team's.

**The result.** Bivariate, playoff rest looks worth **+2.4 pp/day**
(significant). Add `quality_diff` and rest collapses to **+1.6 pp/day,
p = 0.113** -- no longer significant -- while `quality_diff` is overwhelming
(+112 pp per unit, p < 0.001). Verdict: most playoff "rest advantage" was just
*being the better team*.

**The same move clears the playoff decline of a different suspicion.** Maybe the
playoff HCA fell only because top seeds stopped dominating? Add `quality_diff`
and the year trend barely flinches (-0.225 -> -0.229 pp/yr; **102% retained**).
The clincher is a control by *design*: when the objectively weaker team hosts
G3/G4, it *still* wins **51.5%** -- a pure venue effect with quality stripped out.
The playoff decline is genuine home-court weakening, not seed compression.

## 7.2 Spurious correlation from shared trends (and how to detrend)

**The trap, restated from §1.4.** Any two things that drift over four decades will
correlate, related or not. The headline **r = -0.90** between 3-point rate and
home win % is *guaranteed* by the fact that threes rose and HCA fell over the
same 40 years -- on its own it proves nothing about whether threes *do* anything.

**Two ways to remove the shared trend** (the project runs both because they have
different weaknesses):

1. **Control for era inside the model (§2.1).** Compare only games *within the
   same era*. The 3PA effect barely changes (-2.64 -> -2.27 pp), so it's *not*
   just the trend -- higher-3PA games really do have lower home win rates even
   among contemporaries. This survives the trap.

2. **Detrend, then correlate (the parity section).** Strip the time trend out of
   *both* series first, then correlate the leftovers. Two standard recipes:
   - **First differencing:** correlate the *year-to-year changes* (delta-parity vs.
     delta-home-win%) instead of the levels.
   - **Residual-on-year:** fit each series against year, then correlate the
     *residuals* (what's left after the trend).

**Worked example -- parity.** Raw correlation between league parity and HCA:
**r = -0.092, p = 0.56** -- basically nothing, *and* the era table actively
contradicts the parity story. So parity didn't drive the structural decline. But
the detrended checks (**first-diff r = -0.330, p = 0.033**; **residual
r = -0.345, p = 0.023**) find a modest *same-year* wobble: in years the league
gets more equal, HCA dips a little. `RESULTS.md` flags this itself as "interpret
with caution" -- it's a small effect on ~43 points, and first differencing
amplifies measurement noise. The discipline to report it *and* caveat it is the
model to imitate.

![A correlation that is really just a shared trend](generated/tutorial_spurious_detrend.png)

The figure walks the trap end to end (using two illustrative trending series).
Left: both just drift over the decades. Middle: plot one against the other and
you get a tight line, r ~-0.9 -- looks like a strong relationship. Right: strip
each series' own time trend out first and correlate the *leftovers*, and the link
collapses toward zero. **The original correlation was the calendar, not a real
connection.** This is why every "X vs. HCA" correlation in `RESULTS.md` is backed
up either by detrending or by a within-era control.

**The general lesson:** never trust a correlation between two trending series
until the shared trend is removed -- by controlling for era, or by detrending. A
raw r near +/-0.9 between two long-run trends is the *start* of an investigation,
never the conclusion.

## 7.3 Reverse causality and the leave-one-out trick

**The trap.** You think X causes Y, but Y is partly causing X. **Pace** is the
example: faster games (more possessions) correlate with home wins -- but
*blowouts* manufacture extra possessions (garbage time, intentional fouling, no
late-game stalling), and home blowouts are disproportionately home *wins*. So
"more pace -> more home wins" might really be "**winning big -> more pace**," the
arrow pointing backwards.

**The fix -- leave-one-out (LOO) "expected pace."** Don't use a game's *own*
pace (contaminated by its own outcome). Instead, predict each game's pace from
each team's pace in **all its *other* games that season**, and use that. Built
only from *other* games, expected pace can't be inflated by *this* game's blowout
-- the backwards arrow is severed.

**The result.** Realized pace shows a clean, significant **+2.3 pp per 10
possessions (p < 0.001)**. Swap in expected pace and it falls to **+1.5 pp and
goes non-significant (p = 0.227)**. That collapse is the tell: the original effect
was substantially *outcome-driven*, not pace driving outcomes. Pace is ruled out
as a cause of the decline (and, as `STATS_EXPLAINER.md` notes, pace is U-shaped
over time while HCA fell steadily -- they can't even share a trend).

**The lesson:** when an outcome can feed back into a predictor, build the
predictor from data that excludes that outcome. LOO is a simple, powerful way to
do it.

## 7.4 Interaction terms (did an effect *change*?)

**The question:** the home-court decline is real, but the *reason* matters. Did
the known factors (rest, altitude, time zone) get *weaker* and thereby cause the
decline -- or did they hold steady while something else fell away?

**The intuition.** An **interaction term** asks whether a factor's effect *differs
across two regimes* -- here, before vs. after 2014. You add a `factor * post2014`
term; if it's significant, that factor's effect *shifted* at 2014. A `post2014`
*main* effect, separately, captures an overall level drop common to all games.

**The result (the stability test).**

| term | estimate | significant? | reading |
|---|---|---|---|
| rest * post2014 | +0.028 | no (p = 0.14) | rest effect unchanged |
| altitude * post2014 | -0.180 | yes (p = 0.026) | altitude effect weakened |
| tz * post2014 | -0.002 | no (p = 0.92) | time-zone effect unchanged |
| **post2014** (level) | **-0.196** | **yes (p < 0.001)** | **overall -4.7 pp drop** |

The picture is clear: the rest and time-zone effects didn't change, and there's a
large, real, across-the-board **-4.7 pp** level drop after 2014. (Altitude's
home-court edge did weaken -- the lone situational shift -- but it touches only
two teams and is dwarfed by the level drop.) Home teams kept their rest edge at
full strength; they simply started winning less for reasons those factors don't
capture -- pointing the search toward the foul-bias and shot-selection channels
(the eroding mechanisms in the differentials and shot-zone sections). An
interaction test is how you ask "did *this* change?" instead of "does this matter?"

---

## 7.5 Natural experiments (when you can't randomize)

**The question:** almost every rule-out in this report is correlational. We can
see that crowd size moves with HCA (or doesn't), but we never get to *assign* a
team its crowd, so we can't truly prove the crowd causes anything. Without a lab,
can we ever get closer to cause and effect?

**The intuition.** A **natural experiment** is when something outside the system
-- a policy, a disaster, a scheduling quirk -- changes one variable for reasons
unrelated to everything else, mimicking the random assignment of a real
experiment. If whether a game got the "treatment" is decided by an outside force
rather than by the teams, then a difference in outcomes reads as closer to
*causal*, because the usual confounders didn't pick who got treated.

**The example.** COVID did the randomizing. In 2020-21, local health rules -- not
team quality, market, or standings -- left some arenas empty and others partly
full, game to game. Comparing empty-arena games (home win **51.0%**) with
fans-present games (**58.5%**) isolates the crowd's own contribution in a way no
season-long correlation can. That ~7-point gap is the report's one near-direct
measurement of what the crowd is worth.

**The caveats.** It is still not a true randomized trial: a single season, a
small and lumpy set of "doses," and attendance that partly tracks market and
date. So the result is read as *suggestive causal* and weighted accordingly --
but it is the strongest causal evidence in the report, which is why the
empty-arena finding earns more interpretive weight than, say, the pace
correlation. When you can't randomize, you look for a shock that did the
randomizing for you.

---

# Part 8 — Ranking a single team historically

The Knicks analysis (`knicks_2026_historic/`) uses lighter methods than the
home-court analysis -- no regression, no inference across seasons. Its statistical
core is **descriptive comparison**: where does one specific team's playoff run
rank against 43 years of champions? Three tools do all the work.

## 8.1 Empirical percentile rank

**The question:** out of 43 NBA champions, how many had a worse (or better) win
rate / margin / adjusted margin than the 2025-26 Knicks?

**The mechanics.** One formula:

```
percentile = ( number of champions with value <= Knicks' value ) / 43 * 100
```

That's it -- no curve-fitting, no distributional assumptions, just counting. With
43 data points the finest resolution is 1/43 ~2.3 percentage points, and a value
exactly equal to the historical best yields 100th percentile (it's <= itself and
every past champion).

**A worked example.** Win rate 0.842. Count how many of the 43 champions had a
win rate <= 0.842: 38 teams. 38/43 * 100 = **88.4th percentile**. The Knicks
were better than 88% of all champions by win rate.

![How empirical percentile rank works](generated/tutorial_percentile_rank.png)

The left panel is the ranked bar chart -- the same form used in `RESULTS.md`. The
right panel makes the counting explicit: 38 champions are at or below the Knicks,
5 are above, so percentile = 38/43 = 88th. There's no statistical magic here;
the percentile is pure counting.

**How to read it in `RESULTS.md`.** Every "percentile" number in the knicks
results is this same count. "100th percentile" means best ever in the dataset.
"53rd percentile" means right at the historical median. No stars, no confidence
intervals -- these are descriptive facts about the 43-champion dataset, not
inferences about a broader population.

**The limit.** 43 seasons is a respectable but finite sample. A 100th-percentile
result is "best in 43 years," not "best of all possible worlds." And the
resolution of ~2.3 pp means that "88th percentile" and "86th percentile" are
essentially the same rank -- don't over-read small differences.

## 8.2 SRS (Simple Rating System)

**The question:** which teams are strongest, in a way that accounts for schedule
difficulty?

**The intuition.** A team's raw average margin is easy to inflate by playing
weak opponents. SRS corrects for that: it's a simultaneous system where every
team's rating must equal its average margin plus a schedule-strength adjustment,
and the whole league's ratings sum to zero. An SRS of +8 means "this team
outscores a league-average opponent by 8 points per game."

**The mechanics (lightly).** Let r_i = SRS for team i. For every team:

```
r_i  =  avg_margin_i  +  (avg of opponents' SRS values)
```

This is a system of 30 equations in 30 unknowns. Adding the constraint
sum(r_i) = 0 pins down a unique solution, solved by linear algebra. The NBA
uses a similar metric; `compute_srs` in `nbakit/data.py` implements it directly
with numpy.

**Reading SRS values.** The Knicks' four 2025-26 playoff opponents:

| opponent | SRS |
|---|---|
| San Antonio Spurs (Finals) | **+8.28** |
| Cleveland Cavaliers | **+3.77** |
| Atlanta Hawks | **+2.38** |
| Philadelphia 76ers | **-0.27** |

The Spurs at +8.28 were elite -- one of the best teams in the league. The 76ers
at -0.27 were slightly below average. This spread is exactly why average opponent
SRS (§8.3) matters: a team that beats a +8 Finals opponent looks different from
one that beats a +1.

![SRS: strength ratings that account for schedule](generated/tutorial_srs_intuition.png)

**Why regular-season SRS for opponents, not playoff SRS.** Playoff SRS would be
circular -- a team's playoff rating partly reflects games against the Knicks
themselves. Regular-season SRS measures strength on an independent 82-game
baseline, before the Knicks were in the picture.

**How to read it in `RESULTS.md`.** Any row labelled "SRS" is this system. A
team with SRS +5 would be expected to beat a team with SRS -5 by 10 points on a
neutral floor. The conference-gap section uses *average* SRS per conference
(East: -0.20, West: +0.20) to quantify how balanced the conferences were.

## 8.3 Schedule-adjusted margin

**The question:** the Knicks won by an average of +14.9 pts/game. But they played
tough opponents. How dominant would that look against league-average opposition?

**The formula.** One line:

```
adj_margin  =  raw_margin  -  avg_opponent_SRS
```

For the Knicks: 14.89 - 3.54 = **+11.35 pts/game adjusted**.

**Why this adjustment is natural.** SRS is defined in point-differential space:
an SRS +3.54 opponent is expected to beat a 0-SRS opponent by 3.54 pts/game.
So the Knicks' +14.89 margin against +3.54 opponents is equivalent to ~+11.35
against average competition. The subtraction is the exact inverse of what SRS
built in.

**How it compares historically.** Adjusted margin +11.35 ranks 1st of 43
champions -- the highest ever, even after correcting for schedule. The next
closest is the 2016-17 Warriors at +10.20. This is the headline number of the
analysis because it is the most complete single measure of dominance: raw margin
with schedule difficulty stripped out.

**The limitation to keep in mind.** The adjustment assumes one SRS point of
opponent quality costs exactly one point of margin -- a clean linear assumption
that comes from the SRS framework itself. In practice, playoff intensity may
compress or expand margins in ways regular-season SRS doesn't capture. And all
four opponents are weighted equally regardless of series length: a team that
swept a +8 SRS opponent in four games "gets credit" for the same +8 as one that
beat them in seven. A more elaborate model could account for these nuances, but
with 43 data points, the direct subtraction is the right level of complexity.

---

# Quick reference — which method, and why

## Home-court analysis methods

| You see this in `RESULTS.md` | It's doing this | Read more |
|---|---|---|
| log-odds, ~pp, "bivariate / controlling for" | logistic regression on win/loss | §2.1, §2.2 |
| binomial GLM | the rigorous trend on season proportions | §2.3 |
| OLS / HAC, "Trend/yr", R² | a straight-line trend (+ autocorrelation-robust errors) | §1.1, §3.3 |
| z = ..., two-proportion | gap between two win rates | §1.2 |
| chi-sq(k) = ... | are several groups' rates all equal? | §1.3 |
| Pearson r, Spearman rho | do two quantities move together (linear / rank) | §1.4 |
| cluster-robust SEs by season | honest error bars for pooled game data | §3.2 |
| LR test chi-sq(df) | does a *block* of dummies earn its place? | §4.1 |
| McFadden R², delta-R%, Shapley | splitting explained variation across factors | §2.5, §4.2 |
| level / trend decomposition, LPM | accounting the home edge into channels | §2.4, §4.3 |
| channel trend, "3PA absorbs %" | is a channel its own driver or downstream of threes? | §4.3 |
| quantile, Q10...Q90, polarization | how the *distribution shape* changed | §5.1 |
| variance decomposition, shrunken | ranking noisy franchise/referee means | §6.1, §6.2 |
| Benjamini-Hochberg, BH-p | keeping many tests honest | §3.4 |
| quality_diff control | removing a confounder | §7.1 |
| first-differenced, residual-on-year | removing a shared time trend | §7.2 |
| expected pace (LOO) | breaking reverse causality | §7.3 |
| * post2014 interaction | did an effect *change* over time? | §7.4 |
| empty-arena (2020-21) dose-response | a natural experiment isolating cause | §7.5 |

## Knicks historical analysis methods

| You see this in `RESULTS.md` | It's doing this | Read more |
|---|---|---|
| Nth percentile (of 43 champions) | empirical percentile rank -- counting, not inference | §8.1 |
| SRS +X.X | Simple Rating System -- point margin adjusted for schedule | §8.2 |
| SRS gap (West - East) | how balanced the two conferences were | §8.2 |
| avg opp SRS | average regular-season SRS of playoff opponents (schedule difficulty) | §8.3 |
| adj margin = raw - avg opp SRS | schedule-corrected dominance measure | §8.3 |
| clutch rate (games decided <= 5 pts) | fraction of close games -- tests "they just blew teams out" | -- |
| home/away split | separate win rates to test venue fragility | -- |

**The three ideas worth carrying away from the home-court analysis:**

1. **A raw difference is not an effect of a boundary.** HCA fell the whole time,
   so any later period looks lower; only a trend-controlled model (LR test) shows
   whether a rule change *itself* did anything. (§1.2, §4.1)
2. **A correlation between two trends is almost meaningless until the trend is
   removed** -- by controlling for era or detrending. (§1.4, §7.2)
3. **With 47,000 games, significance is cheap -- read the effect size and the CI.**
   A significant p doesn't mean a meaningful effect. (§0.4)

**And from the Knicks analysis:**

4. **Percentile rank is just counting.** "100th percentile" means best in the
   dataset, not statistically proven best ever. Read it as a clean historical
   fact, not an inference. (§8.1)
5. **SRS makes schedule difficulty commensurable.** A +14.9 raw margin and a +11.4
   adjusted margin tell the same story here -- but in a different year against
   weaker opponents, the gap could be large enough to reverse a ranking. Always
   check both. (§8.2, §8.3)
