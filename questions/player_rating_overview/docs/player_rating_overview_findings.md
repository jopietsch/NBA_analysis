# NBA Player Rating Systems: Survey, Comparison, and Combination

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

## 1. Introduction

Every "top players" list puts names in order. But ordinal rank is a compression: the gap between the best player in the league and the tenth-best is not the same as the gap between the tenth and the twentieth. The numbers beneath the ranks tell a different story than the ranks themselves.

This report surveys how NBA players get rated, compares what each system actually measures, and builds two combined ratings designed to answer two different questions: what do all the systems agree on, and which combination of them best explains which teams win? It also grades the systems one at a time, by how well each rebuilds which teams outscored their opponents and how well last season's ratings forecast this one, and recomputes the box-score metrics for the playoffs to show who rose and who fell.

The testbed is the 2024-25 season, built on the eight box-score systems that can be recomputed directly from public data: Game Score, PER, Win Shares, WS/48, BPM, Offensive BPM, Defensive BPM, and VORP. The lineup-based impact metrics and human rankings described next are surveyed as part of the landscape, but are not recomputed or included in the comparison here. The architecture extends to earlier seasons, and to those other systems, as data allows.

## 2. The landscape of player rating

### Box-score systems

The oldest and most available systems work entirely from the standard box score: points, rebounds, assists, steals, blocks, turnovers, and shot attempts. They can be computed for any season back to the 1980s.

**Player Efficiency Rating (PER)** was John Hollinger's attempt to fold everything into one per-minute number normalized so the league average is always 15. A 20 PER is well above average; 30 or above is an all-time great season.

**Win Shares (WS)** takes a different angle. Rather than measuring efficiency per minute, it allocates the team's actual wins back to individual players based on their offensive production and a defensive credit. The cumulative version (total Win Shares) grows with playing time; WS/48 normalizes it back to a per-minute rate.

**Box Plus/Minus (BPM)** tries to estimate what a player's presence adds per 100 possessions compared to an average player, derived from box-score rates and adjusted for team quality. It splits into Offensive BPM and Defensive BPM. VORP extends it into a cumulative value by multiplying by playing time and comparing to a replacement-level player rather than an average one. BPM exists in two versions; this report uses the current one, BPM 2.0 (see Appendix B).

**Game Score** (also Hollinger) is a simpler per-game summary that weights each box-score category by its approximate value. It is not normalized.

### Impact metrics

Box-score systems share a blind spot: they do not directly measure whether a player made their team better or worse. A prolific scorer who forces bad shots and plays poor defense can rate well on PER and WS. Lineup-based "impact" metrics try to fix this by measuring how the team's scoring margin changes when a player is on the floor versus off it, with various forms of smoothing to handle the noise.

All of the major impact metrics share the same technical backbone: Regularized Adjusted Plus/Minus (RAPM). The basic idea is to ignore individual stats entirely and look only at the scoreboard. Every time a lineup is on the floor, track whether the team outscores or gets outscored. Do that for every lineup combination across an entire season, then use a statistical model to work backward and assign each player their share of credit or blame, adjusting for the quality of teammates and opponents. The result is a per-possession estimate of how much the scoring margin changes when a player is on the floor versus an average player.

RAPM is considered the best available signal for true player impact for three reasons. First, it measures the right thing: winning is about outscoring the opponent, and RAPM captures everything that contributes to that (off-ball movement, defensive positioning, communication), not just what shows up in the box score. A player who creates open shots for teammates without recording the assist, or whose defensive presence deters drives two passes away from the ball, shows up in RAPM but not in PER or Win Shares. Second, it passes predictive tests better than box-score metrics: in studies comparing how well first-half stats predict second-half game outcomes, RAPM-based metrics consistently outperform box-score-only approaches. Third, it does not assume what matters. Box-score metrics assign fixed weights to assists, steals, rebounds, and so on based on historical averages. RAPM does not; it lets actual game outcomes determine each player's value.

The catch is noise. One season of lineup data is not enough to reliably separate a player's true impact from the randomness of which lineups they happened to share court time with. Raw RAPM estimates for bench players or players in unusual lineup situations can swing wildly. Every serious system handles this by adding a "prior": a box-score estimate of what a player should be worth, used to pull noisy RAPM estimates toward something stable. The systems mostly differ in how that prior is built and what data feeds it.

**RAPTOR** (FiveThirtyEight, 2013-14 through 2022-23) combined on/off lineup data with player-tracking data (speed, distance, shot quality). FiveThirtyEight shut down its sports coverage in April 2023, so RAPTOR has no 2024-25 values. Historical data is downloadable from their GitHub.

**EPM** (dunksandthrees) uses a RAPM calculation with a Bayesian prior built from a highly optimized Statistical Plus/Minus model that incorporates player-tracking data. EPM is the only public metric that directly optimizes the weighting of each underlying stat by how quickly it stabilizes, which is one reason it tends to perform well in retrodiction tests.

**LEBRON** (BBall-Index) also uses a luck-adjusted RAPM with a box-score prior. "Luck adjustment" means the on/off data strips out the swing from whether shots happened to fall, rather than crediting the player for it. The prior weights come from PIPM (Player Impact Plus/Minus), an earlier metric by Jacob Goldstein that is no longer updated.

**DARKO DPM** is best thought of as a projection system rather than a season average. Like baseball projection systems (PECOTA, Steamer), DARKO weights recent games more heavily and updates daily, so it answers "what is this player's current true talent?" more than "how did this player perform this season?" That distinction matters when comparing across systems.

**DRIP** (Daily Updated Rating of Individual Performance, Opta Analyst) is similar to DARKO in structure: it now-casts current player talent by weighting recent performance more heavily, rather than averaging over the full season.

**ESPN RPM** used RAPM with a box-score prior from Jeremias Engelmann, who also created the foundational RAPM dataset that most other systems calibrate against. ESPN stopped publishing RPM publicly around 2023.

The core limitation across all these systems is sample size: a player's on/off data in one season is much noisier than their box-score totals. That smoothing pulls noisy estimates toward the box-score baseline, which means the baseline's assumptions matter a great deal, especially for players with limited minutes.

The prior-plus-RAPM structure is a form of Bayesian reasoning applied to a noisy measurement problem. The box-score prior is a starting belief about a player's value before seeing the lineup data. The on/off data is the evidence that updates that belief. The final estimate blends the two, with the weight on the data side growing as the sample of lineup possessions grows. A player with 3,000 possessions of lineup data gets pulled strongly toward what the data shows; a bench player with 400 possessions barely moves from the prior. This is why the best-performing metrics in retrodiction tests outperform simpler ones: the improvement comes not from more variables in the box-score formula, but from more carefully balancing how much to trust the prior versus the data.

The one thing this framework does not yet deliver is uncertainty. Every metric publishes a single number ("EPM: +8.2 per 100"), with no range around it. A fully Bayesian treatment would produce something like "+8.2, likely between +6.8 and +9.6, with the range reflecting how much one season of lineup data can vary by chance." That range would make visible what is currently hidden: the apparent disagreements between systems about who ranks 8th versus 12th are often smaller than the uncertainty band of any single metric. The rankings are noisier than they look.

**Which metrics do practitioners trust?** A HoopsHype survey of 29 NBA front-office executives (2021) found DARKO DPM was the most preferred catch-all metric (8 respondents), followed by EPM and LEBRON. A retrodiction study by Dunks & Threes, comparing how well each metric predicts future game outcomes, put EPM first, followed by RPM, RAPTOR, and BPM 2.0 in that order. EPM and RPM were the only two metrics using RAPM directly with a Bayesian prior at the time of that study, which appears to be the structural feature behind their edge over box-score-only approaches. (Both the survey and the retrodiction study are external published work, not recomputed here; full citations are in the [resources bibliography](player_rating_resources.md).)

### Human rankings

MVP vote share, All-NBA selections, and media top-100 lists measure something neither box nor impact models capture directly: reputation and narrative. A player with a great story can receive more MVP votes than their on-court numbers warrant; a player on a losing team can be underrated.

Human rankings sit outside this report's current testbed: the pipeline was narrowed to systems that can be recomputed directly from box-score data. They are described here because they are part of how players actually get rated, and adding a reputation dataset to compare model-based and reputation-based consensus is a natural extension.

## 3. Do the systems agree?

![Agreement between each pair of systems: darker squares mean stronger rank correlation.](../generated/images/rank_agreement_heatmap.svg){#fig-agreement}

The box-score systems mostly move in the same direction, but how tightly varies a lot by pair. PER and Game Score track closely (0.83 on a 0-to-1 scale, among qualified 2024-25 players). PER and Win Shares agree fairly well too (0.76), as do Win Shares and WS/48 (0.70). The loosest pairings are between the per-minute rate metrics and the plus/minus family: PER and BPM move together only moderately (0.49), and Game Score and BPM about the same (0.47). The tightest pair is BPM and VORP (0.97), which is no surprise, since VORP is built directly from BPM.

Even the pairs that agree overall still hand out value differently player by player. Win Shares, which divides a team's actual wins among its players, favors efficient bigs on good teams: Domantas Sabonis and Ivica Zubac both rate well above their consensus rank in it. PER, a per-minute efficiency score, leans toward high-usage scorers, with Zion Williamson and Kristaps Porziņģis among its biggest risers. Two systems can land near each other in the overall order while still disagreeing about which individual players to credit.

The exact figures are in `docs/player_rating_overview_results.md`.

## 4. What the field has learned about evaluating these metrics

Not all player rating systems are equally trusted, and the analytics community has developed two main ways to test whether a metric is actually measuring what it claims to measure.

**Retrodiction** uses the first half of a season's games to predict game outcomes in the second half. A metric that genuinely captures player impact should let you predict which team wins when you know each team's lineup. This is the test used in the Dunks & Threes comparison study, which found EPM and RPM at the top, followed by RAPTOR and BPM 2.0. The top metrics shared a structural feature the others lacked: both used RAPM with a box-score prior, while lower-ranked metrics either skipped the prior or used only box-score data without the RAPM step.

**Team wins prediction** aggregates player ratings to the team level and asks how well the total predicts actual wins. This is the logic behind the wins-predictive rating built in this report.

Both tests reward the same thing: a RAPM backbone stabilized by a well-calibrated box-score prior. That combination handles the two main failure modes: pure box-score metrics miss what a player does off the ball, and pure RAPM is too noisy with one season of data.

One important result from the academic literature runs against the intuition that more sophisticated is better: peer-reviewed research has found that complex metrics do not reliably outperform simpler ones when used to predict salaries or wins. That is not a flaw in the metrics themselves. They are built to estimate player impact per possession, not to serve as inputs in every downstream analysis. The lesson is that a metric's predictive accuracy in a retrodiction test is not the same as its usefulness for a specific application, and the right tool depends on the question being asked.

### A direct test on the systems here

A related test grades the systems one at a time rather than combining them. Add up a single system's player ratings across a team's roster, weighted by minutes played, and check how closely that total matches which teams actually outscored their opponents over 2024-25. Each system is graded on teams held out of the calculation, so it cannot score well just by fitting this exact season.

The outcome is a useful surprise. PER, the oldest and simplest per-minute box score, rebuilt about 72% of the differences between teams, more than the plus/minus metrics that are explicitly built to track team results. Two cautions apply before reading that as a verdict. The recomputed BPM and VORP here are approximations (see the note on the recomputed formulas below), so part of their weaker showing is a noisy recompute. And rebuilding the season just played is only half the test.

![How well each system, summed to the team, rebuilds 2024-25 team point differential. Blue systems never use who won; grey systems are built from team or lineup results, where a high score is partly mechanical.](../generated/images/retrodiction.svg){#fig-retrodiction}

The other half is forecasting. Take each player's rating from the prior season (2023-24), spread it across this season's rosters, and see how well that predicts which teams outscored their opponents in 2024-25. This is a stricter test: a metric's team adjustment is tuned to its own season, so it earns nothing for predicting a season it has not seen. The order flips. PER, the best description of the season, becomes one of the weakest forecasts of the next, falling from about 72% to roughly 15%. In this one pair the plus/minus family holds up best, with BPM on top at about 50%. (About 89% of this season's minutes came from players who also rated the year before; rookies have no prior mark.)

The lesson is the one every projection system runs into: describing what happened and forecasting what comes next are different jobs. PER is a faithful scoreboard of a finished season but a poor crystal ball. Which rating is "better" depends on the question.

![Each system's same-season fit (grey) against how well its prior-season version forecasts this season (blue). PER describes best but forecasts worst; the plus/minus metrics hold more of their predictive signal.](../generated/images/next_season_retrodiction.svg){#fig-next-season}

One pair of seasons could be a fluke, so we ran the same two tests on every season back to 2010-11: 16 seasons for the describe test and 15 year-to-year handoffs for the forecast test. The shape repeats. PER describes best every era, averaging about 65% of the gaps between teams, and forecasts near the bottom, about 26%. The best forecaster across all those handoffs is not a plus/minus metric at all but Game Score, at about 45%, another plain box score that never looks at who won. The 2024-25 result where BPM led was one season's order; BPM still beats PER as a forecaster in 12 of the 15 handoffs. What holds across fifteen years is the gap itself: the rating that best sums up a finished season is consistently not the one to bet the next season on.

![Average same-season fit (grey) against next-season forecast (blue) for each box-score system, pooled over 16 seasons and 15 season-pairs. Whiskers span the season-to-season range. PER's describe-forecast gap is the widest and never closes.](../generated/images/panel_describe_vs_forecast.svg){#fig-panel-describe-forecast}

## 5. What each system uniquely sees

Not all systems add independent information. Measuring what each one adds beyond the others shows the eight box-score systems overlap heavily: most of what any single system says can be rebuilt from the rest. Offensive and Defensive BPM are the clearest case, since regular BPM is just their sum, so once you have two of the three the third tells you nothing new. Win Shares and WS/48 hold the most signal of their own, but even they share the large majority of their ranking with the field. The eight are closer to several views of one underlying thing than to eight independent opinions (see results for the full breakdown).

The "system outliers" chart shows the players each system rates most above and below the consensus. This is where methodological differences become visible: a system that captures defensive value heavily will love rim protectors; a system that penalizes inefficient volume scoring will discount high-usage players with middling true shooting.

![Players each system rates most above or below the consensus.](../generated/images/system_outliers.svg){#fig-outliers}

## 6. The two uber ratings

Two combined ratings are built from the systems present in the data.

Each system uses a different scale (PER is centered around 15, BPM around 0, Win Shares in the single digits), so you cannot average them directly. Putting every system on one common scale fixes that, by asking of each player: how many typical-player gaps above or below average is this? A 0 means exactly average; +2 is well into star territory; −1 is a step below average. Once every system is on this common scale, they can be combined.

**Consensus rating:** the average normalized score across all systems. This measures what the crowd of methodologies agrees on, not what is best-supported by any one theory. The 2024-25 consensus top five: Nikola Jokić, Shai Gilgeous-Alexander, Giannis Antetokounmpo, James Harden, and Trae Young.

**Wins-predictive rating:** a combination of those scores weighted by how well each system (aggregated to team level) predicts actual team wins. The two ratings agree very closely (0.98 on a 0-to-1 scale): they reach the same conclusions about the very best players. The wins-predictive rating pushes the stars on winning teams higher still. Shai Gilgeous-Alexander rises the most, with Giannis Antetokounmpo close behind, and Daniel Gafford, Victor Wembanyama, and Alex Caruso also move up. Players on losing teams slide the other way: Vasilije Micic and other deep-rotation players on poor teams rate lower on the wins-predictive scale than on the consensus, because their on-court production did not translate into team wins.

![Consensus versus wins-predictive rating: each dot is a player; distance from the diagonal marks where the two approaches disagree.](../generated/images/uber_rating_comparison.svg){#fig-uber}

Aggregating across systems is not unique to this report. HoopsHype publishes periodic "Analytics MVP" posts that combine EPM, LEBRON, DARKO, RAPTOR, and BPM into a single ranking, typically using a simple equal-weighted average. ESPN's #NBArank is a different kind of aggregate: journalists vote rather than models, making it closer to the human-reputation category than to a model combination. Some metrics do the aggregation internally: LEBRON, for example, blends a box-score prior with luck-adjusted on/off data as part of its own formula rather than publishing both separately and combining them downstream. What distinguishes the wins-predictive rating here is that the system weights are estimated from data (how well each system actually predicted team wins) rather than assigned by hand. The practical difference is small (the two ratings agree at 0.98 on a 0-to-1 scale), but the weights tell you which systems carried the most predictive signal for 2024-25, which is worth knowing.

The 2024-25 season shows how this plays out. Nikola Jokić tops both ratings, with Shai Gilgeous-Alexander close behind in each (the consensus puts them at 3.13 and 2.72; the wins-predictive rating at 3.90 and 3.87). Gilgeous-Alexander gains more than any other player when the rating shifts to wins-predictive, because Oklahoma City had the league's best record and that rating rewards strong individual production that lines up with team success. The deep-rotation players on losing teams move the opposite way: solid rate metrics, but no team wins behind them.

## 7. Stars matter more than rank implies

![Rating systems normalized to the same scale: value falls steeply in the top tier for every methodology, but at very different rates.](../generated/images/all_systems_distributions.svg){#fig-all-dist}

PER spreads relatively evenly among qualified 2024-25 players: the top 5% account for only 8.5% of total value. The gap between the 50th and 95th percentile player in PER is smaller than it looks on a ranked list.

Win Shares and VORP tell a different story. The top 5% of players hold about 15% of total Win Shares, and VORP concentrates far more steeply still: its top 5% hold about 32% of all positive value. Both lean toward the top because they multiply a rate by minutes played, and the best players lead in both.

These drop-offs are sometimes called power laws. The term has a precise meaning: value falls by a roughly constant percentage with each step down the ranks, so the drop from rank 1 to rank 2 is proportionally the same as from rank 10 to rank 20. When that holds there is no natural place to split "stars" from everyone else; the order just keeps shrinking at the same rate. The test is simple. Stretch both axes onto a log scale, and a power law turns into a straight line.

By that test the systems fall into two groups, and the split lines up with the cumulative-versus-rate divide already described. Holding close to a straight line: Game Score, PER, Win Shares, DBPM, VORP. Bending instead: WS/48, BPM, OBPM.

Win Shares and VORP are the steep power laws. Because they multiply a rate by minutes, value compounds: the best players lead in both, so their totals pull far ahead and the top stays heavy all the way down. PER and Game Score are power laws too, but so shallow that the line is nearly flat, which is the same reason their top 50 sit bunched close together in value.

The benders are the plus/minus rate metrics: WS/48, BPM, OBPM. These measure how far above average a player is per possession, a quantity that is roughly even on both sides of the middle and has a natural size to it. Their best player is not a runaway: the top of the curve sits below where a straight power law would put it, and OBPM bends the most.

So the shape tells you what the metric measures. A metric that piles up accumulated value tilts toward a few players at the top; a metric that scores distance from average has a built-in size and does not run away. The small panels below make the difference visible: the blue curves hold a straight line, the grey ones bow.

![One small panel per system: blue curves are power laws (a straight line on a log scale), grey curves bend. Ordered by how steeply value falls, steepest first.](../generated/images/powerlaw_small_multiples.svg){#fig-powerlaw-sm}

Two cautions. The cutoff between "power law" and "bends" is a convention, and the systems sitting right at it (DBPM just clears the line, BPM just misses) are really the same shape. And this is a description of 50 players in one season, not a formal test: it shows which curves are straight and which bend, not a proven law. The reliable read is the two groups and their order, not the label on any single borderline system.

![Every system on one log-log chart, with each fitted power law drawn through it. Useful for comparing the slopes directly.](../generated/images/powerlaw_fits.svg){#fig-powerlaw .collapsible}

An older, more familiar way to put a single number on concentration is the Gini coefficient (0 means everyone is rated the same, 1 means one player holds all the value). It is kept here only as a cross-check, because it has a real limit: it works for metrics that pile up a quantity that cannot drop below zero, like Win Shares or VORP, but not for the 0-centered metrics. On those (the BPM family and the two combined ratings) it counts every below-average player as a zero and inflates the score, which is why Consensus shows a Gini of 0.763, above Win Shares at 0.363, an ordering that is not real. The steepness read above is the one to trust. By it the combined ratings land in the middle of the pack: Consensus at 0.31 and Wins-Predictive at 0.28, steeper than PER at 0.13 but flatter than VORP at 0.36.

![Gini coefficient by system, kept as a cross-check. It ranks the 0-centered metrics (the BPM family and the two combined ratings, outlined) near the top, but that is an artifact of how Gini handles below-average players, not real top-heaviness.](../generated/images/gini_by_system.svg){#fig-gini .collapsible}

![Each line shows a system's value as a percentage of its rank-1 player. Win Shares and VORP fall steeply; PER and BPM stay much flatter.](../generated/images/rank_value_distributions.svg){#fig-distributions}

![The gap between rank 1 and rank 10 is far larger than rank 10 to rank 50 in value-based systems.](../generated/images/ordinal_vs_value_gap.svg){#fig-gap}

The visual gap between rank 1 and rank 10 looks like 10 spots on a list. The numerical gap is often several times larger than the gap between rank 10 and rank 50.

The data is consistent with the explanation that elite talent is worth more than rank implies: having the best player on the roster matters more to winning than being one step ahead of the second-best, and a ranked list treats every step between players as equal.

## 8. Who lands in the top 20

The table below shows the top 20 players under each system and their raw score. The gap between rank 1 and rank 20 is the most direct read on how concentrated value is: a large gap means the top player is in a different tier from the rest; a small gap means the list is relatively flat.

![Top 20 players and their raw scores under each of the eight rating systems. Blue row is rank 1, red row is rank 20.](../generated/images/top20_by_system.svg){#fig-top20}

## 9. Who rose and fell in the playoffs

The box-score rate metrics can be computed a second time using only playoff games, which makes a direct before-and-after read possible: did a player's production climb or sink once the postseason started? This works only for the box-score systems. The impact metrics need far more games than a playoff run provides (a first-round loss is about six games), so they cannot be split this way.

Among the 96 players who logged at least 150 playoff minutes in 2024-25, each player's change is measured against the rest of that group. That strips out the leaguewide dip that comes from tougher defense and facing the same opponent night after night, so what is left is who rose or fell relative to the other rotation players who also advanced.

The biggest risers were Gary Trent Jr., Kawhi Leonard, and Paolo Banchero. The biggest fallers were Michael Porter Jr., Austin Reaves, and Miles McBride. The fallers also include the regular-season consensus number one, Nikola Jokić, whose box-score rates slipped as Denver lost in the second round. The list rewards players whose game travels into a grind-it-out playoff series and marks down those who leaned on production that dried up against a focused defense. It describes one postseason, not proof that any of these players is reliably better or worse when the stakes rise: playoff samples are small, and only half the league is in them.

![Who rose and who fell in the 2024-25 playoffs, by box-score rate metrics, for players with at least 150 playoff minutes. Green rose, red fell.](../generated/images/playoff_shift.svg){#fig-playoff-shift}

## 10. A note on the recomputed formulas

The box-score recompute engines (PER, Win Shares, BPM, VORP) implement the published methodologies from Hollinger and Basketball-Reference, but they are approximations. The most precisely recomputed metric is PER: the league-average normalization produces values in the expected range (mean ~15, Nikola Jokić in the low 30s). The Win Shares and BPM formulas use simplified versions of the defensive credit and team-context adjustments, and the resulting absolute values differ from Basketball-Reference's published figures. The relative rankings within each system are directionally correct.

A Phase 3 planned improvement is to spot-check the recomputed values against BBR for 5-10 known players, and to tighten the BPM per-100-possession rate computation (currently using player-possession-based denominators rather than the team-possession-based denominators BBR uses). For comparison purposes (which system ranks whom higher or lower), the current implementation is sufficient. For absolute values, treat the recomputed BPM/VORP as approximations.

One consequence is visible in the data: VORP rates Dyson Daniels further above the consensus than any other player, placing him near the very top, far above where he lands in any other system. On Basketball-Reference's published figures, Daniels ranks well outside the top 10. The difference traces to steals: Daniels led the league in steals in 2024-25, and the DBPM formula credits steals heavily. Our approximation amplifies that credit further because it uses player-possession denominators rather than team-possession denominators, inflating per-100 steal rates. His more modest standing in the rate metrics tells a more representative story of a strong defensive specialist whose overall value does not place him among the very best players in the league.

The same inflation affects other high-steal defenders in 2024-25: Keon Ellis (121 steals across the season), Cason Wallace, and Kris Dunn all carry VORP values in this dataset that exceed their BBR equivalents. Their Win Shares figures (typically 3-4, about right for a productive reserve) are the more representative number. This is not a separate bug from the Daniels case; it is the same per-100 denominator approximation applied to any player with a high steal rate relative to their minutes.

## 11. Limitations

The cross-system comparison (rank agreement, the two combined ratings, the playoff risers and fallers) is built on the 2024-25 season alone. The describe-versus-forecast test reaches further: it now runs across 16 seasons back to 2010-11. Player-level stability (do the same names rate highly season after season?) uses the same multi-season cache but is not yet built, and is a natural next step.

The crosswalk matching rate for each third-party source is reported in `docs/player_rating_overview_results.md`. Players who could not be matched are listed there; they are excluded from the cross-system comparison but retained in the unified table.

RAPM (regularized adjusted plus/minus) is the technical backbone of every serious modern impact metric (EPM, LEBRON, DARKO, RAPTOR, and RPM all build on it), but it is not recomputed here. Computing RAPM requires play-by-play data broken into stints (which lineup was on the floor for each possession), then a single statistical model that estimates every player's contribution to the scoring margin at once. That data volume and the modeling setup push beyond what this project tackles in its current form. The practical consequence: the only impact signal in our system comes through BPM, which estimates what RAPM would say using box-score inputs. BPM is a reasonable proxy but known to miss things that only appear in the lineup data, particularly for players whose impact on team defense does not show up in personal stats. A public RAPM snapshot can be dropped into the cache schema when one is available.

The tracking-based and team-internal systems (Second Spectrum, franchise models, Synergy) are documented in the inventory but not accessible. The blind spot is acknowledged.

Comparing playoff performance to regular season performance is done for the box-score systems in Section 9, where the rate metrics are recomputed from postseason games and compared directly. The limit is the impact metrics: RAPM-based systems cannot do this reliably. A first-round exit provides roughly 6 games of lineup data; even a Finals run provides only 20 to 24 games. That sample is too small for the lineup regression to stabilize, regardless of how good the prior is. The small-sample problem is not a solvable data-engineering issue; it is a fundamental limit of how RAPM works.

## 12. What a Bayesian lens would add

The impact metrics already apply Bayesian reasoning in one place. The box-score prior is a starting belief about what a player should be worth, derived from their individual stats. The lineup on/off data is the evidence that updates that belief. A player with many lineup possessions gets pulled strongly toward what the data shows; a bench player with few possessions barely moves from the prior. That structure is the skeleton of EPM, LEBRON, DARKO, and every other serious impact metric.

Two things a more complete Bayesian treatment would add:

**Uncertainty ranges.** Every metric publishes a single number (EPM: +8.2 per 100 possessions), with no range, no width. With one season of lineup data, the true uncertainty band around any RAPM-based estimate is roughly 2-3 points per 100 possessions. Publishing that range would make visible what the single number hides: the apparent disagreements between metrics about who ranks 8th versus 12th are often smaller than the uncertainty around any individual estimate. This does not mean the metrics are unreliable. It means the precision they imply is a display choice, not a statistical one.

**Playoff versus regular season.** Section 9 already compares regular season and playoffs for the box-score rate metrics directly, which is the practical version. The Bayesian addition is for the RAPM-based metrics, where the right approach is different: treat the full-season estimate as the prior and update it with playoff lineup data. The updated estimate barely shifts for a player who exits in the first round (roughly 6 games of new evidence), and moves more for a player who reaches the Finals (20-24 games). The shift (in which direction and by how much) is the honest answer to "did this player hold up in the playoffs?" without pretending there is more data than there is. A player whose updated estimate barely moves showed results consistent with the regular-season picture. A player whose updated estimate shifts meaningfully showed something different.

**Better consensus weighting.** The wins-predictive rating in this report is a step toward what is sometimes called model averaging: instead of treating all systems as equally reliable, weight them by how well they predicted team wins. A more fully Bayesian version would estimate those weights from retrodiction performance across multiple seasons and update them as new data arrives. The practical difference at the top of the rankings is small, because the systems that predict team wins best already carry the most weight. But the principled foundation matters when choosing which metrics to trust for a specific question, particularly for players at the margins of the top tier.

## Appendix A: Companion Documents

- [Full analysis output](player_rating_overview_results.md)
- [System inventory and acquisition paths](player_rating_overview_inventory.md)
- [Methods and statistics](player_rating_overview_stats_explainer.md)
- [Source bibliography for the third-party metrics and studies](player_rating_resources.md)

## Appendix B: The two versions of Box Plus/Minus

Box Plus/Minus comes in two versions, both built by Daniel Myers for Basketball-Reference. The original, BPM 1.0, was published in 2014 and was the first widely available attempt to estimate a player's plus/minus impact from the box score alone. Basketball-Reference later replaced it with a revised version, BPM 2.0, and recomputed every season in its database with the new formula. The "BPM" throughout this report is BPM 2.0, the version in current use.

The two differ in method, not just in tuning. BPM 1.0 first guessed each player's position (point guard through center) and offensive role from their stats, then applied weights that shifted with that position and role. BPM 2.0 reworked how it infers role and recalibrated its weights against a larger set of lineup plus/minus data, a revision meant to improve accuracy, particularly for players whose value comes from defense or from a role the box score describes poorly. Because 2.0 is the version Basketball-Reference now publishes, and the one its BPM and VORP figures reflect, it is the one this report recomputes.

We looked at adding BPM 1.0 alongside it, to show how much a single system's verdicts move when only the formula changes, but did not. Basketball-Reference retired the original and no longer publishes its values, so there is nothing to import. And the position-and-role part of the formula is not cleanly documented in public sources: the reconstructions that circulate drop it, which collapses the metric into something close to a minutes-played ranking rather than a measure of skill. A faithful recompute would need the original full specification. If that becomes available, BPM 1.0 versus 2.0 is a natural addition.
