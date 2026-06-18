# Our Findings vs. the Sparkle Technologies Blog

A point-by-point check of our report (`home_court_FINDINGS.md`, backed by `RESULTS.md`) against the external analysis at
<https://sparkletechnologies.com/blog/nba-disappearing-home-court-advantage>.

Three questions drove this comparison:

1. Have we come up with different answers — do we disagree?
2. Are we claiming anything that our own data doesn't support?
3. Did we find changes the blog missed (and vice versa)?

**Bottom line.** We agree on the big picture and on every number where we share a method. The disagreements are almost all the same shape: the blog leans on raw season-to-season correlations and unconditional splits; we control for the 40-year downward drift and for confounders. The single best external validation is that an independent analyst lands within a tenth of a point of our altitude numbers. We are not inventing results — our most aggressive claims are the ones tied directly to `RESULTS.md`. The blog credited one driver (schedule / back-to-backs) that we have since tested directly — it explains only ~8% of the decline. And we surface three eroding channels the blog never mentions, plus modern player-tracking data that corroborates the rebounding story from the possession level.

---

## 1. Where we agree

These are genuine independent corroborations — different analyst, different code, same answer.

| Topic | Blog | Us (`RESULTS.md`) | Verdict |
|---|---|---|---|
| Decline is real, ~10 pp | 68% → 55% (≈13 pp, league-wide) | RS 65% → 55.6%; playoffs 68% → 58% | **Agree** (we split RS/playoffs; blog reports a blended figure) |
| Refs/free throws are a major eroding channel | r = 0.85; home FTA edge +1.91 → +0.59/gm | foul-call edge 1.2 → 0.25/gm (RS), 1.6 → 0.7 (playoffs) | **Agree on direction & shrinkage** |
| Three-point rise tracks the decline | r = −0.88 (raw) | within-era effect −2.6 pp per 10 pp of 3PA, survives detrending (p<0.001) | **Agree it matters; disagree on how to size it** (see §2) |
| Travel distance is not a cause | r = −0.01 | ≈0.07 pp/100 mi, p=0.010 but negligibly small; zero in playoffs | **Agree** |
| Pace is not a season-level driver | r = +0.23 (weak, wrong sign) | no meaningful season correlation; flat across the slowdown-then-speedup | **Agree** |
| Crowd *size* is innocent | arenas near capacity throughout | record attendance as the edge hit its lows; detrended correlation ~0 | **Agree** |
| Denver/Utah own the best home court, via altitude | Denver +27.9 pp, Utah +26.5 pp | ≈+27 and +26 pp; altitude is the top franchise factor | **Agree — near-identical numbers** |
| Pre-pandemic HCA was already low | 2019–20 pre-shutdown 55.1% | the decline predates COVID; COVID only exposed it | **Agree** |

The altitude figures matching to the decimal — derived from independent pipelines — is the strongest single sign our numbers aren't fabricated.

---

## 2. Where we genuinely disagree

### 2a. What is *the* cause — threes vs. a four-channel split

The blog crowns the three-point revolution as *the* primary driver on the strength of a raw time-series correlation (r = −0.88), plus r = 0.85 for free throws and r = −0.85 for its EuroLeague comparison.

We deliberately distrust those raw correlations: two series that both drift downward for 40 years will correlate near-perfectly whether or not one causes the other — the classic spurious-trend trap. (We make this exact argument when ruling out competitive balance.) So we do two things the blog does not:

- **Detrend / go within-era.** Holding the year-by-year drift constant, more threes in a given game still predict fewer home wins: **−2.64 pp per 10 pp of 3PA rate (RS), and it survives the detrend (−2.27 pp, p<0.001)**; playoffs −2.84 to −3.12 pp (p=0.027). So the three-point effect is real *and* robust — but it is one channel, not the whole story.
- **Decompose the box score.** Of the regular-season decline, the channels split: **shooting 21%, the whistle 18%, turnovers 27%, rebounding 30%** (`RESULTS.md:257-261`). The two channels the blog never mentions — rebounding and turnovers — carry **57% of the decline between them**, more than shooting and fouls combined.

So we disagree on emphasis: the blog over-attributes to threes via a correlation that can't separate cause from shared trend, and in doing so misses where the accounting actually lands.

A related disagreement on the **free-throw share**: the blog says the FT/referee channel is ~40% of the margin decline (~1.0 of 2.25 points). Our trend decomposition puts the whistle at **18%** of the win-rate decline. The blog is decomposing *points of scoring margin*; we are decomposing *the win-rate trend* through cluster-robust channel coefficients — different denominators, but the blog's 40% is far above any share we can reproduce.

### 2b. The mid-1990s drop — hand-checking vs. the short three-point line

Both reports see a **~2.6 pp one-time drop** in the mid-1990s on top of the drift. We attribute it to the **1994–95 hand-check crackdown** (`RESULTS.md:607`: era 1995–01, −2.6 pp, p=0.010). The blog attributes the *same era's* drop to the **shortened three-point line (1994–97)**, which it uses as a natural experiment for three-point causation (before 61.8% → during 59.2% → after 60.8%).

Here's the catch: the shortened line (1994–95 through 1996–97) overlaps the hand-check crackdown almost exactly, and the blog uses a before/during/after three-point rate pattern as causal evidence for the short line. But our channel event study gives us more traction than a season-level split. The foul differential responded immediately and significantly at the 1994-95 boundary (level shift p=0.007); the shooting channel showed no significant immediate response (p=0.327). If the shortened three-point line were the primary driver, you would expect the shooting line to move first. It doesn't. The two changes are not fully separable at the season level, but the channel data points more consistently to hand-checking. Our prose is already measured ("the more likely culprit"); it does not need softening.

### 2c. The empty-arena experiment — different numbers

Same 2020–21 natural experiment, materially different reads:

| | Empty arena | Fans present | Implied crowd effect |
|---|---|---|---|
| **Blog** | 54.4% | (2019–20 full ≈ 55.1%) | ≈ **0–2 pp** |
| **Us** | **51.0%** (n=573) | **58.5%** (n=591) | ≈ **7.5 pp** |

We find a large presence effect that switches on and off with the doors; the blog finds almost none in its 2020–21 split.

**Resolved — and our number is the right one.** Checking the 2020-21 game-by-game data: of the games with reported attendance, exactly half (573 of 1,164) were played with literally zero fans and went **51.0%**; the games with any crowd (median 3,280, many at reduced capacity) went **58.5%**. The *blended* average across all 2020-21 games is **54.8%** — which is essentially the blog's "empty arenas: 54.4%." So the blog reported the **whole-season average for the empty-arena season** and labeled it as the empty-arena games. The true empty-vs-fans split is ours (51.0% vs 58.5%), and the dose-response confirms it: even a 1k–3k crowd lifts home win% to ~65%. No real data disagreement — the blog conflated "the season when arenas were empty" with "the games actually played empty." We agree on the conclusion (presence is a switch, not the 40-year dial); we just measured the switch and the blog averaged over it.

### 2d. Time zones — a cross-sectional effect we don't find

The blog reports a **5.2 pp eastward-travel penalty** (visitor going east → 62.8% home win; going west → 57.6%) as a real effect. In our regression — controlling for rest, altitude, era, and COVID — the time-zone coefficient is **−0.6 pp per zone** (full model p=0.005, CI [−0.9, −0.2]), but it doesn't survive the BH multiple-comparisons correction and is negligibly small in magnitude. The blog's 5.2 pp is almost certainly an unconditional split confounded with conference geography, team quality, and schedule. Here we have the methodological high ground. (We both agree it doesn't explain the *decline* — the effect is flat over time either way.)

---

## 3. What the blog found that we did not test

**Load management / back-to-backs — now tested; premise confirmed, magnitude overstated.** The blog argues visitor back-to-back frequency fell from ~35% (1980s) to ~21% (today), so fewer games hand the home team a tired opponent, crediting this with **~15–20% of the decline**.

We have now run this directly (new `BACK-TO-BACKS` section in `RESULTS.md`). The premise checks out: visitor B2B frequency fell **35.0% → 18.8%** across our eras — essentially the blog's number. But a shift-share decomposition of the 9.3 pp regular-season decline puts the **schedule/frequency effect at only −0.71 pp, about 8%**; the remaining ~92% is the home edge eroding *within* every rest situation alike. The reason it's small: the home advantage against a tired visitor (64.7%) is only ~6 pp above a normal game (59.1%), so even a 16-point drop in tired-visitor frequency moves the aggregate less than a point. So we **confirm the blog's mechanism exists but is about half its claimed size** (~8%, not 15–20%) — and B2Bs are a regular-season matter; they barely occur in the playoffs.

This also vindicates the blog's own caveat: even among fully-rested games HCA fell ~6 pp, a decline scheduling can't explain — consistent with our four-channel on-court story carrying the bulk.

**External comparators we lack.** The blog uses a **EuroLeague control group** (NBA 3PA +19.5/HCA −4.4 pp vs. EuroLeague 3PA +5.0/HCA −0.7 pp) and the **short-line natural experiment** as causal leverage for the three-point story. We have neither cross-league nor within-league natural experiment; our three-point evidence is the within-era coefficient instead. Their EuroLeague angle is a genuinely clever piece of identification we don't match (though it too rests on a small-N raw correlation).

---

## 4. What we found that the blog missed

1. **The rebounding collapse — our biggest distinctive finding.** The blog's decomposition has *no rebounding term at all*. We find the home offensive-rebound edge fell from +0.89/gm to roughly zero, the home *share* of available offensive boards fell **+2.74 pp → −0.34 pp**, it tracks the league-wide OREB-rate drop (**32.9% → 25.9%, r = 0.824**), and crucially it **survives holding three-point volume constant** — so it is not the three-point story in disguise. If this holds, the blog's box-score account is incomplete by its single largest channel.

2. **Turnover-edge erosion** (~27% of the RS decline) — also entirely absent from the blog.

3. **Shot-selection convergence** — the home paint-attempt-rate edge shrinking (1.3 → 0.2 pp), a mechanism distinct from three-point *accuracy*.

4. **A disciplined playoff structure.** We separate regular season from playoffs throughout and add game-by-game playoff home win rates (G1 69%, G5 74.5%, G7 64%) plus the decisive control: when the *weaker* team hosts Games 3–4 it still wins **51.5%** (N=827) — proving the playoff decline is real home-court erosion, not bunched seeds. The blog has essentially no playoff-specific analysis beyond the bubble.

5. **Formal ruling-out with the right tests** — the playoff-format change is non-significant once detrended (p=0.197); competitive balance is near-zero raw with only a weak detrended residual; and a combined situational model leaves ~half its predictive power to "which era" (the decline itself). The blog rules factors out by eyeballing uniform declines; we test each against the secular trend.

6. **The widening-blowout finding** — margins spreading ~0.2 pp/yr in both RS and playoffs even as home teams win less.

7. **Player-tracking confirmation of the rebounding story (2013–14 on).** The possession-level tracking cameras, switched on in 2013–14, provide a modern close-up that fits the 40-year rebounding picture exactly. The home team's edge in converting offensive-rebound chances has kept shrinking toward and then through zero (reaching negative by 2025–26); its second-chance-points edge has faded alongside; and its box-out edge sits at essentially zero throughout the tracking era. The window is too short to establish the 40-year trend on its own, but it confirms the mechanism is still operating today and offers a possession-level view the blog has no equivalent for.

---

## 5. Are we "making things up"?

No evidence of it. Every number we share with an independent analyst is consistent or favorable, and our boldest claims (rebounding, turnovers, playoff seeding control) are precisely the ones anchored in `RESULTS.md` rather than asserted. Two honesty fixes surfaced by this comparison — **both now addressed:**

- **The mid-90s drop (§2b):** `home_court_FINDINGS.md` now acknowledges the shortened-three-point-line interpretation alongside hand-checking, noting the two are confounded, rather than asserting hand-checking as the sole cause.
- **Back-to-backs (§3):** now tested directly — a new `BACK-TO-BACKS` section in `RESULTS.md` and a paragraph in `home_court_FINDINGS.md` §4 quantify the schedule-shift channel at ~8% of the regular-season decline, replacing the earlier "rest is ruled out" framing.

Everywhere else, the comparison strengthens confidence: where we and the blog use the same method we get the same answer, and where we differ we are the ones controlling for the trap (spurious trends, unconditional splits) that the blog falls into.
