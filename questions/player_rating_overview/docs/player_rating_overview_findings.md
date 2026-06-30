# NBA Player Rating Systems: Survey, Comparison, and Combination

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

The rating that best describes a finished NBA season is one of the worst at predicting the next one.
Averaged across the 30 seasons tested, PER, the oldest and simplest box score, rebuilds about 64% of the gaps between teams in a season just played, more than the plus/minus metrics built to track exactly that, yet it forecasts the next at only about 25%.
That split is one thread of a larger problem: every "top players" list uses a different method, and they disagree in ways that matter for players on losing teams, defensive specialists, and high-usage scorers.

This report surveys how NBA players get rated and puts three questions to the systems:

1. **Do the systems agree?**
2. **What does each system uniquely capture?**
3. **How should they be combined into one rating?**

A few things to settle up front:

- Is there a single best system? No: the one that best sums up a finished season (PER) is among the weakest at forecasting the next, so "best" depends on the question you are asking.
- Do the systems agree? At the very top, closely; below the top tier they diverge enough to change who you would pick.
- Is a higher rank a proportionally bigger gap? No: value is top-heavy, so the gap from the best player to the tenth is far larger than from the tenth to the fiftieth.

The short answers run through the report.
The box-score systems move together but only loosely track the lineup-based impact metrics, and the from-scratch RAPM sits apart from all of them, agreeing with the box scores at about 0.14 on a 0-to-1 scale.
Each system tilts toward a player type, and the simplest box scores (PER, Game Score) prove largely redundant, nearly rebuilt from the others, while the metrics built for defense and lineup impact carry more of their own.
And two combined ratings, a plain consensus and a wins-predictive blend, agree almost exactly (0.95 on a 0-to-1 scale) on the best players while parting on role players whose production did not turn into team wins.

The testbed is the 2025-26 season, built on the eight box-score systems that can be recomputed directly from public data: Game Score, PER, Win Shares, WS/48, BPM, Offensive BPM, Defensive BPM, and VORP.
It also includes a lineup-based impact metric computed from scratch for this report, RAPM, in two forms: a bare single-season version that shows how noisy raw plus/minus is, and a prior-informed, multi-year version (RAPM+prior) built the way the published metrics are.
Two findings reach beyond the single season, across 30 seasons back to 1996-97: the describe-versus-forecast test above and each rating's year-to-year stability.
Because the cross-system comparison rests on one season while those panels span decades, treat the single-season orderings as a snapshot and the panel findings as the firmer, repeated pattern.
The other impact metrics and the human rankings are surveyed as part of the landscape (Section 1) but are not recomputed or included in the comparison here.

## 1. The landscape of player rating

### Box-score systems

The oldest and most available systems work entirely from the standard box score: points, rebounds, assists, steals, blocks, turnovers, and shot attempts.
They can be computed for any season back to the 1980s.

**Player Efficiency Rating (PER)** was John Hollinger's attempt to fold everything into one per-minute number normalized so the league average is always 15.
A 20 PER is well above average; 30 or above is an all-time great season.

**Win Shares (WS)** takes a different angle.
Rather than measuring efficiency per minute, it allocates the team's actual wins back to individual players based on their offensive production and a defensive credit.
The cumulative version (total Win Shares) grows with playing time; WS/48 normalizes it back to a per-minute rate.

**Box Plus/Minus (BPM)** tries to estimate what a player's presence adds per 100 possessions compared to an average player, derived from box-score rates and adjusted for team quality.
It splits into Offensive BPM and Defensive BPM.
VORP extends it into a cumulative value by multiplying by playing time and comparing to a replacement-level player rather than an average one.
BPM exists in two versions; this report uses the current one, BPM 2.0 (see Appendix B).

**Game Score** (also Hollinger) is a simpler per-game summary that weights each box-score category by its approximate value.
It is not normalized.

### Impact metrics

Box-score systems share a blind spot: they do not directly measure whether a player made their team better or worse.
A prolific scorer who forces bad shots and plays poor defense can rate well on PER and WS.
Lineup-based "impact" metrics try to fix this by measuring how the team's scoring margin changes when a player is on the floor versus off it, with various forms of smoothing to handle the noise.

All of the major impact metrics share the same technical backbone: Regularized Adjusted Plus/Minus (RAPM).
The basic idea is to ignore individual stats entirely and look only at the scoreboard.
Every time a lineup is on the floor, track whether the team outscores or gets outscored.
Do that for every lineup combination across an entire season, then use a statistical model to work backward and assign each player their share of credit or blame, adjusting for the quality of teammates and opponents.
The result is a per-possession estimate of how much the scoring margin changes when a player is on the floor versus an average player.

RAPM is considered the best available signal for true player impact for three reasons.
First, it measures the right thing: winning is about outscoring the opponent, and RAPM captures everything that contributes to that (off-ball movement, defensive positioning, communication), not just what shows up in the box score.
A player who creates open shots for teammates without recording the assist, or whose defensive presence deters drives two passes away from the ball, shows up in RAPM but not in PER or Win Shares.
Second, it passes predictive tests better than box-score metrics: in studies comparing how well first-half stats predict second-half game outcomes, RAPM-based metrics consistently outperform box-score-only approaches.
Third, it does not assume what matters.
Box-score metrics assign fixed weights to assists, steals, rebounds, and so on based on historical averages.
RAPM does not; it lets actual game outcomes determine each player's value.

The catch is noise.
One season of lineup data is not enough to reliably separate a player's true impact from the randomness of which lineups they happened to share court time with.
Raw RAPM estimates for bench players or players in unusual lineup situations can swing wildly.
Every serious system handles this by adding a "prior": a box-score estimate of what a player should be worth, used to pull noisy RAPM estimates toward something stable.
The systems mostly differ in how that prior is built and what data feeds it.

**RAPTOR** (FiveThirtyEight, 2013-14 through 2022-23) combined on/off lineup data with player-tracking data (speed, distance, shot quality).
FiveThirtyEight shut down its sports coverage in April 2023, so RAPTOR has no 2025-26 values.
Historical data is downloadable from their GitHub.

**EPM** (dunksandthrees) uses a RAPM calculation with a prior built from a highly optimized Statistical Plus/Minus model that incorporates player-tracking data.
EPM is the only public metric that directly optimizes the weighting of each underlying stat by how quickly it stabilizes, which is one reason it tends to perform well in retrodiction tests (checking each rating against games it has not yet seen).

**LEBRON** (BBall-Index) also uses a luck-adjusted RAPM with a box-score prior.
"Luck adjustment" means the on/off data strips out the swing from whether shots happened to fall, rather than crediting the player for it.
The prior weights come from PIPM (Player Impact Plus/Minus), an earlier metric by Jacob Goldstein that is no longer updated.

**DARKO DPM** is best thought of as a projection system rather than a season average.
Like baseball projection systems (PECOTA, Steamer), DARKO weights recent games more heavily and updates daily, so it answers "what is this player's current true talent?" more than "how did this player perform this season?" That distinction matters when comparing across systems.

**DRIP** (Daily Updated Rating of Individual Performance, Opta Analyst) is similar to DARKO in structure: it now-casts current player talent by weighting recent performance more heavily, rather than averaging over the full season.

**ESPN RPM** used RAPM with a box-score prior from Jeremias Engelmann, who also created the foundational RAPM dataset that most other systems calibrate against.
ESPN stopped publishing RPM publicly around 2023.

The core limitation across all these systems is sample size: a player's on/off data in one season is much noisier than their box-score totals.
That smoothing pulls noisy estimates toward the box-score baseline, which means the baseline's assumptions matter a great deal, especially for players with limited minutes.

The prior-plus-RAPM structure is a form of Bayesian reasoning applied to a noisy measurement problem.
The box-score prior is a starting belief about a player's value before seeing the lineup data.
The on/off data is the evidence that updates that belief.
The final estimate blends the two, with the weight on the data side growing as the sample of lineup possessions grows.
A player with 3,000 possessions of lineup data gets pulled strongly toward what the data shows; a bench player with 400 possessions barely moves from the prior.
This is why the best-performing metrics in retrodiction tests outperform simpler ones: the improvement comes not from more variables in the box-score formula, but from more carefully balancing how much to trust the prior versus the data.

The one thing this framework does not yet deliver is uncertainty.
Every metric publishes a single number ("EPM: +8.2 per 100"), with no range around it.
A fully Bayesian treatment would produce something like "+8.2, likely between +6.8 and +9.6, with the range reflecting how much one season of lineup data can vary by chance." That range would make visible what is currently hidden: the apparent disagreements between systems about who ranks 8th versus 12th are often smaller than the uncertainty band of any single metric.
The rankings are noisier than they look.

**Which metrics do practitioners trust?** A HoopsHype survey of 29 NBA front-office executives (2021) found DARKO DPM was the most preferred catch-all metric (8 respondents), followed by EPM and LEBRON.
A retrodiction study by Dunks & Threes, comparing how well each metric predicts future game outcomes, put EPM first, followed by RPM, RAPTOR, and BPM 2.0 in that order.
EPM and RPM were the only two metrics using RAPM directly with a Bayesian prior at the time of that study, which appears to be the structural feature behind their edge over box-score-only approaches.
(Both the survey and the retrodiction study are external published work, not recomputed here; full citations are in the [resources bibliography](player_rating_resources.md).)

### Human rankings

MVP vote share, All-NBA selections, and media top-100 lists measure something neither box nor impact models capture directly: reputation and narrative.
A player with a great story can receive more MVP votes than their on-court numbers warrant; a player on a losing team can be underrated.

Human rankings sit outside this report's current testbed: the pipeline was narrowed to systems that can be recomputed directly from box-score data.
They are described here because they are part of how players actually get rated, and adding a reputation dataset to compare model-based and reputation-based consensus is a natural extension.

## 2. Do the systems agree?

![Agreement between each pair of systems: darker squares mean the two systems rank players more alike.](../generated/images/rank_agreement_heatmap.svg){#fig-agreement}

The box-score systems mostly move in the same direction, but how tightly varies a lot by pair.
PER and Game Score track closely (0.86 on a 0-to-1 scale, among qualified 2025-26 players).
PER and Win Shares agree fairly well too (0.77), as do Win Shares and WS/48 (0.80).
The loosest pairings are between the per-minute rate metrics and the plus/minus family: PER and BPM move together only moderately (0.51), and Game Score and BPM about the same (0.43).
The tightest pair is BPM and VORP (0.97), which is no surprise, since VORP is built directly from BPM.

Even the pairs that agree overall still hand out value differently player by player.
Win Shares, which divides a team's actual wins among its players, favors efficient bigs on good teams: Donovan Clingan and Nikola Jokić both rate well above their consensus rank in it.
PER, a per-minute efficiency score, leans toward high-usage scorers, with Giannis Antetokounmpo and Joel Embiid among its biggest risers.
Two systems can land near each other in the overall order while still disagreeing about which individual players to credit.

RAPM, the one impact metric computed here, sits apart from all of them.
It is built only from which lineups outscored their opponents, with no box-score inputs at all, so it shares little with the rest: its rank order agrees with the box-score systems at about 0.14 on the same 0-to-1 scale, well below how tightly those systems track each other.
That distance is the whole point of an impact metric, since it is meant to catch what the box score misses.
But a single season of lineup data is noisy, and it shows.
The bare 2025-26 RAPM puts reserves and rookies near the top, led by Moussa Cisse, who lands at number 37 in the consensus that the box-score systems build.
This is why every published impact metric (EPM, LEBRON, DARKO) pulls its RAPM toward a box-score prior rather than using it raw.

The report also builds that fixed version.
RAPM+prior pools three seasons of lineup data and anchors each player to a box-score prior (their BPM), the same recipe the published metrics use.
The effect shows up in the aggregate: its order agrees with the consensus at about 0.48, up from 0.25 for the bare version measured against that same consensus, nearly double.
The lift is in the broad order, not a clean top tier: in 2025-26 a few low-minute players, Moussa Cisse among them, still spike above the established stars.
It is RAPM+prior, not the bare version, that feeds the consensus rating.
How it is built is in Section 12; whether it forecasts team results any better is tested in Section 3.

The exact figures are in `docs/player_rating_overview_results.md`.

## 3. What the field has learned about evaluating these metrics

Not all player rating systems are equally trusted, and the analytics community has developed two main ways to test whether a metric is actually measuring what it claims to measure.

**Retrodiction** uses the first half of a season's games to predict game outcomes in the second half.
A metric that genuinely captures player impact should let you predict which team wins when you know each team's lineup.
This is the test used in the Dunks & Threes comparison study, which found EPM and RPM at the top, followed by RAPTOR and BPM 2.0.
The top metrics shared a structural feature the others lacked: both used RAPM with a box-score prior, while lower-ranked metrics either skipped the prior or used only box-score data without the RAPM step.

**Team wins prediction** aggregates player ratings to the team level and asks how well the total predicts actual wins.
This is the logic behind the wins-predictive rating built in this report.

Both tests reward the same thing: a RAPM backbone stabilized by a well-calibrated box-score prior.
That combination handles the two main failure modes: pure box-score metrics miss what a player does off the ball, and pure RAPM is too noisy with one season of data.

One important result from the academic literature runs against the intuition that more sophisticated is better: peer-reviewed research has found that complex metrics do not reliably outperform simpler ones when used to predict salaries or wins.
That is not a flaw in the metrics themselves.
They are built to estimate player impact per possession, not to serve as inputs in every downstream analysis.
The lesson is that a metric's predictive accuracy in a retrodiction test is not the same as its usefulness for a specific application, and the right tool depends on the question being asked.

### A direct test on the systems here

A related test grades the systems one at a time rather than combining them.
Add up a single system's player ratings across a team's roster, weighted by minutes played, and check how closely that total matches which teams actually outscored their opponents over 2025-26.
Each system is graded on teams held out of the calculation, so it cannot score well just by fitting this exact season.

The outcome is a useful surprise.
PER, the oldest and simplest per-minute box score, rebuilt about 73% of the differences between teams, more than the plus/minus metrics that are explicitly built to track team results.
Two cautions apply before reading that as a verdict.
The recomputed BPM and VORP here are approximations (see the note on the recomputed formulas below), so part of their weaker showing is a noisy recompute.
And rebuilding the season just played is only half the test.

![How well each system, summed to the team, rebuilds 2025-26 team point differential. Blue systems never use who won; grey systems are built from team or lineup results, where a high score is partly mechanical.](../generated/images/retrodiction.svg){#fig-retrodiction}

The other half is forecasting.
Take each player's rating from the prior season (2024-25), spread it across this season's rosters, and see how well that predicts which teams outscored their opponents in 2025-26.
This is a stricter test: a metric's team adjustment is tuned to its own season, so it earns nothing for predicting a season it has not seen.
The order flips.
PER, the best description of the season, becomes one of the weakest forecasts of the next, falling from about 73% to roughly 37%.
In this one pair the plus/minus family holds up best, with Game Score on top at about 40%.
(About 88% of this season's minutes came from players who also rated the year before; rookies have no prior mark.)

The lesson is the one every projection system runs into: describing what happened and forecasting what comes next are different jobs.
PER is a faithful scoreboard of a finished season but a poor crystal ball.
Which rating is "better" depends on the question.

![Each system's same-season fit (grey) against how well its prior-season version forecasts this season (blue). PER describes best but forecasts among the worst; the plus/minus metrics hold more of their predictive signal.](../generated/images/next_season_retrodiction.svg){#fig-next-season}

One pair of seasons could be a fluke, so we ran the same two tests on every season back to 1996-97: 30 seasons for the describe test and 29 year-to-year handoffs for the forecast test.
The shape repeats.
PER describes best every era, averaging about 64% of the gaps between teams, and forecasts near the bottom, about 25%.
The best forecaster across all those handoffs is not a plus/minus metric at all but Game Score, at about 42%, another plain box score that never looks at who won.
The single 2025-26 handoff agrees: Game Score forecasts best there too, and across the full panel BPM still beats PER as a forecaster in 20 of the 29 handoffs.
What holds across every era in the data is the gap itself: the rating that best sums up a finished season is consistently not the one to bet the next season on.

![Average same-season fit (grey) against next-season forecast (blue) for each box-score system, pooled over 30 seasons and 29 season-pairs. Whiskers span the season-to-season range. PER's describe-forecast gap is the widest and never closes.](../generated/images/panel_describe_vs_forecast.svg){#fig-panel-describe-forecast}

RAPM can only be computed back to 2013-14, the seasons with play-by-play, so a fair test scores it against the box scores on those same 13 seasons rather than against their full 30-year history.
On that even footing the bare single-season RAPM is a weak forecaster of next-season team results: it ranks 9 of 10, rebuilding about 17% of the gaps between teams, behind every box score but one.
The plain box scores again lead, with Game Score on top at about 45%.
This is the same lesson the single-season noise pointed to: without a box-score prior to steady it, one year of RAPM carries too much randomness to forecast the next.
Its same-season describe score is mid-pack (about 34%), but for RAPM that number reads high for a mechanical reason, since RAPM is built from the very lineup margins the describe test rebuilds.

RAPM+prior does better than the bare version on the same test, forecasting 8 of 10 at about 24%, but it still lands below the box scores.
Pooling three seasons and leaning on a box-score prior sharpen which players rate highly (Section 12), yet they do not make the lineup signal a better forecaster of team results than a plain box score already is.

![The same describe-versus-forecast test on the 13 seasons where RAPM can be computed, box scores and both RAPM versions scored together. Sorted by forecast strength: the bare single-season RAPM and the prior-informed RAPM+prior both sit toward the right, forecasting next-season team results below the plain box scores, with RAPM+prior edging ahead of the bare version.](../generated/images/impact_panel_describe_vs_forecast.svg){#fig-impact-panel}

### Which ratings hold steady year to year

There is a third way to judge a rating: how much a player's own number carries from one season to the next.
Match the players who logged real minutes in back-to-back seasons, and ask how many of the top 20 by each system one year are still in the top 20 the next.
The simplest box scores are the stickiest.
Game Score keeps 68% of its top 20 from one year to the next, and PER keeps 64%, against a chance level near 5%.
On a 0-to-1 stickiness scale, where 1 would mean a player's rating repeats exactly, Game Score is the steadiest at 0.85 and BPM the jumpiest at 0.70, pooled over 29 season-to-season handoffs.

Stickiness is not the same as quality.
A rating can repeat year to year because it captures a real, lasting skill or because it is slow to notice a player changing.
What stands out is how this lens cuts against the forecasting one.
PER is among the stickiest individual ratings yet one of the weakest forecasters of team results; BPM is the jumpiest yet forecasts team point differential better than PER does.
The plain reading is that the box-score rate metrics measure a stable individual trait, the scoring and production a player carries with them, while the plus/minus metrics move around more because they fold in team and role, the very context that helps them forecast a team.
Only Game Score sits near the top of both lists, steady and predictive at once.

![Left: how much a player's rating carries from one season to the next, on a 0-to-1 scale. Right: the share of each system's top 20 who are still top 20 the next season, with the chance level marked. Pooled over 29 season-pairs among players who qualified in both.](../generated/images/rating_stability.svg){#fig-rating-stability}

## 4. What each system uniquely sees

Not all systems add independent information, and they split sharply on how much.
The simplest all-in-one box scores are the most redundant: about 90% of PER and 89% of Game Score can be rebuilt from the other systems, so each mostly repeats what the field already says.
The metrics built to isolate defense and lineup impact carry the most of their own: Defensive BPM and BPM leave roughly half of their ranking unexplained by the rest, and the RAPM family carries somewhat less of its own, in the 30-40% range.
One caveat keeps that from being a clean verdict: this report's BPM, VORP, and RAPM are approximate recomputes, and a noisy rating looks independent simply because its noise lines up with nothing, so part of their low overlap may be recompute slack rather than real signal.
The measure holds each metric's own components out of the comparison, so BPM is never counted as "explained" by its own offensive and defensive halves (see results for the full breakdown).

The "system outliers" chart shows the players each system rates most above and below the consensus.
This is where methodological differences become visible: a system that captures defensive value heavily will love rim protectors; a system that penalizes inefficient volume scoring will discount high-usage players with middling true shooting.

![Players each system rates most above or below the consensus.](../generated/images/system_outliers.svg){#fig-outliers}

## 5. The two uber ratings

Two combined ratings are built from the systems present in the data.

Each system uses a different scale (PER is centered around 15, BPM around 0, Win Shares in the single digits), so you cannot average them directly.
Putting every system on one common scale fixes that, by asking of each player: how many typical-player gaps above or below average is this?
A 0 means exactly average; +2 is well into star territory; −1 is a step below average.
Once every system is on this common scale, they can be combined.

**Consensus rating:** the average normalized score across all systems.
This measures what the crowd of methodologies agrees on, not what is best-supported by any one theory.
The 2025-26 consensus top five: Nikola Jokić, Shai Gilgeous-Alexander, Mitchell Robinson, Luka Dončić, and Victor Wembanyama.

**Wins-predictive rating:** a combination of those scores weighted by how well each system (aggregated to team level) predicts actual team wins.
The two ratings agree very closely (0.95 on a 0-to-1 scale): they reach the same conclusions about the very best players.
The wins-predictive rating pushes the stars on winning teams higher still.
Nikola Jokić rises the most, with Giannis Antetokounmpo close behind, and Victor Wembanyama, Jalen Duren, and Paul Reed also move up.
Players on losing teams slide the other way: Kam Jones and other deep-rotation players on poor teams rate lower on the wins-predictive scale than on the consensus, because their on-court production did not translate into team wins.

![Consensus versus wins-predictive rating: each dot is a player; distance from the diagonal marks where the two approaches disagree.](../generated/images/uber_rating_comparison.svg){#fig-uber}

Aggregating across systems is not unique to this report.
HoopsHype publishes periodic "Analytics MVP" posts that combine EPM, LEBRON, DARKO, RAPTOR, and BPM into a single ranking, typically using a simple equal-weighted average.
ESPN's #NBArank is a different kind of aggregate: journalists vote rather than models, making it closer to the human-reputation category than to a model combination.
Some metrics do the aggregation internally: LEBRON, for example, blends a box-score prior with luck-adjusted on/off data as part of its own formula rather than publishing both separately and combining them downstream.
What distinguishes the wins-predictive rating here is that the system weights are estimated from data (how well each system actually predicted team wins) rather than assigned by hand.
The practical difference is small (the two ratings agree at 0.95 on a 0-to-1 scale), but the weights tell you which systems carried the most predictive signal for 2025-26, which is worth knowing.

The 2025-26 season shows how this plays out.
Nikola Jokić tops both ratings and pulls away under the wins-predictive weighting: the consensus puts him at 2.79, the wins-predictive rating at 4.56.
He also gains more than any other player when the rating shifts to wins-predictive (+1.76 versus his consensus rating), because Denver was one of the league's stronger teams and that rating rewards strong individual production that lines up with team success.
The deep-rotation players on losing teams move the opposite way: solid rate metrics, but no team wins behind them.

## 6. Stars matter more than rank implies

![Rating systems normalized to the same scale: value falls steeply in the top tier for every methodology, but at very different rates.](../generated/images/all_systems_distributions.svg){#fig-all-dist}

PER spreads relatively evenly among qualified 2025-26 players: the top 5% account for only 8.6% of total value.
The gap between the 50th and 95th percentile player in PER is smaller than it looks on a ranked list.

Win Shares and VORP tell a different story.
The top 5% of players hold 13.8% of total Win Shares, and VORP concentrates far more steeply still: its top 5% hold 29.1% of all positive value.
Both lean toward the top because they multiply a rate by minutes played, and the best players lead in both.

These drop-offs are sometimes called power laws.
The term has a precise meaning: value falls by a roughly constant percentage with each step down the ranks, so the drop from rank 1 to rank 2 is proportionally the same as from rank 10 to rank 20.
When that holds there is no natural place to split "stars" from everyone else; the order just keeps shrinking at the same rate.
The test is simple.
Stretch both axes onto a log scale, and a power law turns into a straight line.

By that test the systems fall into two groups, and the split lines up with the cumulative-versus-rate divide already described.
Holding close to a straight line: Game Score, PER, Win Shares, BPM, O-RAPM, D-RAPM+prior.
Bending instead: WS/48, OBPM, DBPM, VORP, RAPM, D-RAPM, RAPM+prior, O-RAPM+prior.

Win Shares is the steep power law, and VORP concentrates value just as hard, though its top-50 curve bends rather than holding the straight line.
Because they multiply a rate by minutes, value compounds: the best players lead in both, so their totals pull far ahead and the top stays heavy all the way down.
PER and Game Score are power laws too, but so shallow that the line is nearly flat, which is the same reason their top 50 sit bunched close together in value.

Most of the benders are per-possession metrics.
They measure how far above average a player is per possession, a quantity that is roughly even on both sides of the middle and has a natural size to it, so their best player is not a runaway: the top of the curve sits below where a straight power law would put it, and OBPM bends the most.
VORP is the exception in this group: it concentrates value as hard as a power law, but its top-50 curve still bends just short of a clean straight line.

RAPM, the impact metric built for this report, is the clearest case, and it answers a natural question: no, RAPM is not a power law.
The log-log test above only reads the top 50 players, but RAPM's whole distribution settles it.
Pooled across all 13 seasons with play-by-play (4678 player-seasons, enough to read the shape cleanly), it is a symmetric hump centered on zero, about as many players below average as above (49% sit below zero), and it tracks a plain bell curve closely.
A power law needs a long one-sided tail of standout values.
RAPM has none, because a per-possession impact is scored against the average player and runs about as far into the minus as the plus.
VORP, set beside it, leans to the right: a handful of stars trail a long tail above the pack.
That lean toward the top, not a hump centered on zero, is the precondition a power law needs, the one RAPM lacks entirely; VORP has it, even though its own top-50 curve bends just short of a clean line.

![RAPM's full distribution against VORP's. RAPM is a symmetric bell with no heavy tail, so it cannot be a power law at all; VORP leans right, with the one-sided tail of stars a power law's shape needs.](../generated/images/distribution_shape.svg){#fig-distribution-shape}

So the shape tells you what the metric measures.
A metric that piles up accumulated value tilts toward a few players at the top; a metric that scores distance from average has a built-in size and does not run away.
The small panels below make the difference visible: the blue curves hold a straight line, the grey ones bow.

![One small panel per system: blue curves are power laws (a straight line on a log scale), grey curves bend. Ordered by how steeply value falls, steepest first.](../generated/images/powerlaw_small_multiples.svg){#fig-powerlaw-sm}

Two cautions.
The cutoff between "power law" and "bends" is a convention, and the systems sitting right at it (BPM just clears the line, DBPM just misses) are really the same shape.
And this is a description of 50 players in one season, not a formal test: it shows which curves are straight and which bend, not a proven law.
The reliable read is the two groups and their order, not the label on any single borderline system.

![Every system on one log-log chart, with each fitted power law drawn through it. Useful for comparing the slopes directly.](../generated/images/powerlaw_fits.svg){#fig-powerlaw .collapsible}

An older, more familiar way to put a single number on concentration is the Gini coefficient (0 means everyone is rated the same, 1 means one player holds all the value).
It is kept here only as a cross-check, because it has a real limit: it works for metrics that pile up a quantity that cannot drop below zero, like Win Shares or VORP, but not for the 0-centered metrics.
On those (the BPM family and the two combined ratings) it counts every below-average player as a zero and inflates the score, which is why Consensus shows a Gini of 0.736, above Win Shares at 0.362, an ordering that is not real.
The steepness read above is the one to trust.
By it the combined ratings sit in the upper-middle of the pack: Consensus at 0.31 and Wins-Predictive at 0.34, steeper than PER at 0.14 and a touch steeper than VORP at 0.30.

![Gini coefficient by system, kept as a cross-check. It ranks the 0-centered metrics (the BPM family and the two combined ratings, outlined) near the top, but that is an artifact of how Gini handles below-average players, not real top-heaviness.](../generated/images/gini_by_system.svg){#fig-gini .collapsible}

![Each line shows a system's value as a percentage of its rank-1 player. Win Shares and VORP fall steeply; PER and BPM stay much flatter.](../generated/images/rank_value_distributions.svg){#fig-distributions}

![The gap between rank 1 and rank 10 is far larger than rank 10 to rank 50 in value-based systems.](../generated/images/ordinal_vs_value_gap.svg){#fig-gap}

The visual gap between rank 1 and rank 10 looks like 10 spots on a list.
The numerical gap is often several times larger than the gap between rank 10 and rank 50.

The data is consistent with the explanation that elite talent is worth more than rank implies: having the best player on the roster matters more to winning than being one step ahead of the second-best, and a ranked list treats every step between players as equal.

## 7. Who lands in the top 20

The raw top 20 makes Section 6's split concrete: under VORP and Win Shares the rank-1 player sits far above rank 20, while under PER the twenty bunch close in value.
The gap between rank 1 and rank 20 is the most direct read on how concentrated value is: a large gap means the top player is in a different tier from the rest; a small gap means the list is relatively flat.

![Top 20 players and their raw scores under each rating system, grouped by family, with the bare RAPM trio and the RAPM+prior trio on their own rows. Blue row is rank 1, red row is rank 20.](../generated/images/top20_by_system.svg){#fig-top20}

## 8. Who rose and fell in the playoffs

Recompute the box-score rate metrics on playoff games only, and a direct before-and-after read falls out: who climbed once the postseason started, and who sank.
The biggest risers were Jayson Tatum, Tari Eason, and Max Strus.
The biggest fallers were Jalen Duren, Nikola Jokić, and Mitchell Robinson.
The drop reached even the regular-season consensus number one, Nikola Jokić, whose box-score rates slipped as Denver lost in the first round.

This read works only for the box-score systems.
The impact metrics need far more games than a playoff run provides (a first-round loss is about six games), so they cannot be split this way.
Among the 103 players who logged at least 150 playoff minutes in 2025-26, each player's change is measured against the rest of that group.
That strips out the leaguewide dip that comes from tougher defense and facing the same opponent night after night, so what is left is who rose or fell relative to the other rotation players who also advanced.

The list rewards players whose game travels into a grind-it-out playoff series and marks down those who leaned on production that dried up against a focused defense.
It describes one postseason, not proof that any of these players is reliably better or worse when the stakes rise: playoff samples are small, and only half the league is in them.

![Who rose and who fell in the 2025-26 playoffs, by box-score rate metrics, for players with at least 150 playoff minutes. Green rose, red fell.](../generated/images/playoff_shift.svg){#fig-playoff-shift}

## 9. What changed from 2024-25 to 2025-26

The whole cross-system comparison rests on one season, so it is fair to ask how much of it survives when the season turns over.
The top barely moves, the middle churns, and the systems disagree by about the same amount as before.

Across the 290 players who qualified in both seasons, the consensus order agrees from 2024-25 to 2025-26 at about 0.67 on a 0-to-1 scale: a steady spine with a moving body.
Nikola Jokić and Shai Gilgeous-Alexander hold the top two spots in both seasons, but only 2 of the top five carry over; Mitchell Robinson, Luka Dončić, and Victor Wembanyama move up to take the other three.

The biggest one-year swings are exactly what a single season cannot tell apart from real change.
Kawhi Leonard climbed the most in standardized standing (+1.52) and Jayson Tatum fell the most (-1.79); injuries, role changes, and roster moves drive most of these, and the rating systems only record them.
This is why the report treats the single-season orderings as a snapshot and rests its findings on the 30-season panels instead.

![Who climbed and who slid in the consensus rating from 2024-25 to 2025-26, among players qualified in both seasons. Green rose, red fell.](../generated/images/season_comparison.svg){#fig-season-comparison}

What did not change is how much the systems agree with one another: the mean rank agreement among the box-score systems was 0.59 in 2024-25 and 0.61 in 2025-26.
The disagreement this report describes is built into how the metrics are made, not an accident of one season.

## 10. Summary

**Do the systems agree?** On the best handful of players, closely; below the top tier, less than their reputations suggest.
The box-score systems move together but only moderately track the lineup-based impact metrics, and the from-scratch RAPM sits apart from all of them (agreeing with the box scores at about 0.14 on a 0-to-1 scale), which is the point of an impact metric and also why one season of it is too noisy to trust raw.
No system is best at everything: PER describes a finished season better than any other (about 64% of the gaps between teams) yet forecasts the next among the worst (about 25%), a split that holds across all 30 seasons tested.

**What does each system uniquely capture?** It depends on the system.
Each tilts toward a player type, Win Shares toward efficient bigs on winning teams, PER toward high-usage scorers, the impact metrics toward off-ball and defensive value the box score misses.
But how much each adds beyond the rest splits sharply: the simplest all-in-one box scores, PER and Game Score, are nearly reconstructable from the other systems, while BPM, Defensive BPM, and the RAPM family hold the most of their own, with the caveat that this report's approximate recomputes can look independent partly because they are noisy.

**How should they be combined?** Into two ratings that answer different questions.
A plain consensus averages every system; a wins-predictive blend weights each by how well it tracked team wins.
They agree almost exactly (0.95 on a 0-to-1 scale) on the best players and part mainly on role players whose production did not turn into team wins.

One pattern runs under all three answers: value is top-heavy.
The gap between the best player and the tenth dwarfs the gap from the tenth to the fiftieth, so a ranked list understates how much a single elite player is worth.

The cross-system comparison rests on the 2025-26 season alone, so its exact orderings are a snapshot; year to year the order holds at the top (Nikola Jokić and Shai Gilgeous-Alexander lead both seasons, rank agreement about 0.67) but churns below it, while the describe-versus-forecast and stability findings span 30 seasons and are the firmer results.
The recomputed BPM and VORP are approximations (Section 11), so read them for rank, not exact value.

## 11. A note on the recomputed formulas

The box-score recompute engines (PER, Win Shares, BPM, VORP) implement the published methodologies from Hollinger and Basketball-Reference, but they are approximations.
The most precisely recomputed metric is PER: the league-average normalization produces values in the expected range (mean ~15, Nikola Jokić in the low 30s).
The Win Shares and BPM formulas use simplified versions of the defensive credit and team-context adjustments, and the resulting absolute values differ from Basketball-Reference's published figures.
The relative rankings within each system are directionally correct.

A planned improvement is to spot-check the recomputed values against Basketball-Reference (BBR) for 5-10 known players, and to tighten the BPM per-100-possession rate computation (currently using player-possession-based denominators rather than the team-possession-based denominators BBR uses).
For comparison purposes (which system ranks whom higher or lower), the current implementation is sufficient.
For absolute values, treat the recomputed BPM/VORP as approximations.

One consequence is visible in the data: VORP rates Cason Wallace further above the consensus than any other player, placing him near the very top, far above where he lands in any other system.
On Basketball-Reference's published VORP, he ranks nowhere near the top of the league.
The difference traces to steals: Wallace led the league in steals in 2025-26, and the DBPM formula credits steals heavily.
Our approximation amplifies that credit further because it uses player-possession denominators rather than team-possession denominators, inflating per-100 steal rates.
His more modest standing in the rate metrics tells a more representative story of a strong defensive specialist whose overall value does not place him among the very best players in the league.

The same inflation affects other high-steal defenders in 2025-26: Ausar Thompson (146 steals across the season) and Kris Dunn (131) both carry VORP values in this dataset that exceed their BBR equivalents.
Their Win Shares figures (around 4 to 5, about right for a productive role player) are the more representative number.
This is not a separate bug from the Wallace case; it is the same per-100 denominator approximation applied to any player with a high steal rate relative to their minutes.

## 12. Limitations

The cross-system comparison (rank agreement, the two combined ratings, the playoff risers and fallers) is built on the 2025-26 season alone.
Two tests reach further, both across 30 seasons back to 1996-97: the describe-versus-forecast panel and the year-over-year stability of each rating.
Extending the cross-system comparison itself across all those seasons, rather than the single testbed year, is the natural next step.

The crosswalk matching rate for each third-party source is reported in `docs/player_rating_overview_results.md`.
Players who could not be matched are listed there; they are excluded from the cross-system comparison but retained in the unified table.

RAPM (regularized adjusted plus/minus) is the technical backbone of every serious modern impact metric (EPM, LEBRON, DARKO, RAPTOR, and RPM all build on it).
This report now computes it directly from play-by-play, for 2025-26 and back through 2013-14.
Within a season, every possession is reconstructed into the five-on-five lineup that was on the floor, and a single statistical model estimates all the players' contributions to the scoring margin at once (572 players in 2025-26).
Two things make this version weaker than the published metrics.
It uses one season of lineup data with no box-score prior, so it is noisy: bench players who shared the floor with strong lineups can rate near the top, which is what puts Moussa Cisse at the head of the raw 2025-26 list (Section 2), and across the seasons it forecasts next-season team results worse than the plain box scores (Section 3).
And the bare version's offensive and defensive halves are kept out of the consensus, so one noisy single-season split cannot swing the order at the top.

The report also computes the stabilized version, RAPM+prior.
It pools three seasons of possessions, weighting recent ones more heavily, and shrinks each player toward a box-score prior: the offensive half toward Offensive BPM, the defensive half toward Defensive BPM.
A player with few possessions stays near his box score, while a heavy-minute player moves toward what the lineup data shows.
This is the prior-plus-RAPM recipe the published metrics use, and it helps where expected: its order agrees with the consensus at 0.48, up from 0.25 for the bare version, nearly double the agreement.
The gain is in the overall order; at the very top, low-minute players like Moussa Cisse can still post inflated values, a reminder that this is an approximate in-house recompute.
RAPM+prior, combined only, is the version that feeds the consensus.
What it does not do is turn RAPM into a strong forecaster of team results: across the seasons it still predicts next-season point differential below the box scores (Section 3), and heavy-minute role players who spend their court time in strong lineups, the hardest case for any plus/minus method, can still rate too high.
Matching a published metric like EPM or LEBRON would need the player-tracking data they use and we do not have.
A public RAPM snapshot can be dropped into the cache schema to validate the computed values when one is available.

The tracking-based and team-internal systems (Second Spectrum, franchise models, Synergy) are documented in the inventory but not accessible.
The blind spot is acknowledged.

Comparing playoff performance to regular season performance is done for the box-score systems in Section 8, where the rate metrics are recomputed from postseason games and compared directly.
The limit is the impact metrics: RAPM-based systems cannot do this reliably.
A first-round exit provides roughly 6 games of lineup data; even a Finals run provides only 20 to 24 games.
That sample is too small for the lineup-based estimate to stabilize, regardless of how good the prior is.
The small-sample problem is not a solvable data-engineering issue; it is a fundamental limit of how RAPM works.

## 13. What a Bayesian lens would add

The impact metrics already apply Bayesian reasoning in one place.
The box-score prior is a starting belief about what a player should be worth, derived from their individual stats.
The lineup on/off data is the evidence that updates that belief.
A player with many lineup possessions gets pulled strongly toward what the data shows; a bench player with few possessions barely moves from the prior.
That structure is the skeleton of EPM, LEBRON, DARKO, and every other serious impact metric.

Two things a more complete Bayesian treatment would add:

**Uncertainty ranges.** Every metric publishes a single number (EPM: +8.2 per 100 possessions), with no range, no width.
With one season of lineup data, the true uncertainty band around any RAPM-based estimate is roughly 2-3 points per 100 possessions.
Publishing that range would make visible what the single number hides: the apparent disagreements between metrics about who ranks 8th versus 12th are often smaller than the uncertainty around any individual estimate.
This does not mean the metrics are unreliable.
It means the precision they imply is a display choice, not a statistical one.

**Playoff versus regular season.** Section 8 already compares regular season and playoffs for the box-score rate metrics directly, which is the practical version.
The Bayesian addition is for the RAPM-based metrics, where the right approach is different: treat the full-season estimate as the prior and update it with playoff lineup data.
The updated estimate barely shifts for a player who exits in the first round (roughly 6 games of new evidence), and moves more for a player who reaches the Finals (20-24 games).
The shift (in which direction and by how much) is the honest answer to "did this player hold up in the playoffs?" without pretending there is more data than there is.
A player whose updated estimate barely moves showed results consistent with the regular-season picture.
A player whose updated estimate shifts meaningfully showed something different.

**Better consensus weighting.** The wins-predictive rating in this report is a step toward what is sometimes called model averaging: instead of treating all systems as equally reliable, weight them by how well they predicted team wins.
A more fully Bayesian version would estimate those weights from retrodiction performance across multiple seasons and update them as new data arrives.
The practical difference at the top of the rankings is small, because the systems that predict team wins best already carry the most weight.
But the principled foundation matters when choosing which metrics to trust for a specific question, particularly for players at the margins of the top tier.

## Appendix A: Companion Documents

- [Full analysis output](player_rating_overview_results.md)
- [System inventory and acquisition paths](player_rating_overview_inventory.md)
- [Methods and statistics](player_rating_overview_stats_explainer.md)
- [Source bibliography for the third-party metrics and studies](player_rating_resources.md)

## Appendix B: The two versions of Box Plus/Minus

Box Plus/Minus comes in two versions, both built by Daniel Myers for Basketball-Reference.
The original, BPM 1.0, was published in 2014 and was the first widely available attempt to estimate a player's plus/minus impact from the box score alone.
Basketball-Reference later replaced it with a revised version, BPM 2.0, and recomputed every season in its database with the new formula.
The "BPM" throughout this report is BPM 2.0, the version in current use.

The two differ in method, not just in tuning.
BPM 1.0 first guessed each player's position (point guard through center) and offensive role from their stats, then applied weights that shifted with that position and role.
BPM 2.0 reworked how it infers role and recalibrated its weights against a larger set of lineup plus/minus data, a revision meant to improve accuracy, particularly for players whose value comes from defense or from a role the box score describes poorly.
Because 2.0 is the version Basketball-Reference now publishes, and the one its BPM and VORP figures reflect, it is the one this report recomputes.

We looked at adding BPM 1.0 alongside it, to show how much a single system's verdicts move when only the formula changes, but did not.
Basketball-Reference retired the original and no longer publishes its values, so there is nothing to import.
And the position-and-role part of the formula is not cleanly documented in public sources: the reconstructions that circulate drop it, which collapses the metric into something close to a minutes-played ranking rather than a measure of skill.
A faithful recompute would need the original full specification.
If that becomes available, BPM 1.0 versus 2.0 is a natural addition.
