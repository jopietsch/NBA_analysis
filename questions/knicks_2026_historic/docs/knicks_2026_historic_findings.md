# Did the 2026 Knicks Have a Historic Playoff Run?

## 1. The Verdict (Up Front)

**Yes: the 2025–26 New York Knicks had a historically dominant playoff run.**

They went 16-3 (88th percentile win rate among all 43 champions since 1983–84)
and outscored opponents by an average of **+14.9 points per game**, the highest
raw playoff margin in the dataset. Across the game-to-game swing of a 19-game
run, that margin could sit anywhere from +7.4 to +22.4: even at the unlucky end,
the run would still rank above the historical average. 2025–26 is the
highest-scoring era since 1984, but that is mostly sharper shooting, not a faster
game: in actual possessions the season runs only about 4% above average, so on a
true pace-neutral basis the raw margin stays #1 (only the cruder scale-by-total-
scoring version drops it to 3rd). After adjusting for opponent
strength, the margin of **+11.2 pts/game** ranks first all-time (though once every
champion's uncertainty is weighed fairly, being the single best is far from
settled, see §10–§11); on the same pace-neutral basis the opponent-adjusted margin is
also first. The East was **not** historically weak: the West-East SRS gap in
2025–26 was only +0.39 pts/game (37th percentile of West dominance); in 63% of
seasons since 1984, the West was even *more* dominant than this. The Knicks earned
this, on a real schedule, against real competition.

There is a possible nuance in the East record: the 76ers and Cavaliers played a
touch *below* their regular-season ratings in their other playoff games, so some
of the rounds 1–3 dominance may reflect opponents underperforming, not just Knicks
excellence, though that gap is small enough to be random (the Hawks played only the
Knicks, so there is no independent read on them; see §5). The Finals tells the
opposite story: the Spurs were the most improved of the Knicks' four opponents,
climbing from a regular-season SRS of +8.28 to a playoff SRS of +15.13 (the
second-biggest rise of any team in the whole 2026 field, behind only the Knicks
themselves; see §6). Winning that series 4-1, even narrowly (+2.4 avg
margin), was the hardest test of the run.

All four opponents were essentially fully healthy when they played the Knicks
(average availability 98%; the Spurs were at 100%), so injuries are not an
explanation for any of it.

![Opponent-adjusted playoff dominance: 2025-26 Knicks rank #1 all-time among 43 champions](../generated/images/knicks_2026_adjusted_margin_ranking.svg){width=100%}

---

## 2. The Raw Numbers

The Knicks went **16-3** in the 2026 playoffs. Among all 43 champions in the
data (1983–84 through 2025–26):

- **Win-rate percentile: 88th**: 0.842, vs. mean 0.752, best (2016–17 Warriors)
  0.941
- **Average margin: 100th percentile**: +14.9 pts/game, best in 43 years

**Round-by-round** (SRS = team quality relative to schedule; higher = stronger):

| Round | Opponent | Record | Avg Margin |
|-------|----------|--------|------------|
| First Round | Atlanta Hawks (SRS +2.38) | 4-2 | +17.5 |
| Second Round | Philadelphia 76ers (SRS -0.27) | 4-0 | +22.2 |
| Conference Finals | Cleveland Cavaliers (SRS +3.77) | 4-0 | +19.2 |
| NBA Finals | San Antonio Spurs (SRS +8.28) | 4-1 | +2.4 |

The two sweeps, against Cleveland (SRS +3.77, a genuine title contender) and
Philadelphia (SRS -0.27), drove the record margin. The Finals were tight: four
of the five games were decided by 4 points or fewer.

![Playoff win rate, all 43 champions ranked](../generated/images/knicks_2026_win_rate_ranking.svg){width=100%}

![Average playoff margin, all 43 champions ranked](../generated/images/knicks_2026_margin_ranking.svg){width=100%}

![2025-26 Knicks: game-by-game margins across 19 playoff games](../generated/images/knicks_2026_game_margins.svg){width=100%}

---

## 3. Was the East Weak?

**No, not historically.** The West-East SRS gap in 2025–26 was only **+0.39
pts/game**: 37th percentile of West dominance, and well within the normal
season-to-season swing. The East inter-conference win rate was 0.487 (near parity). By any
formal measure, the East in 2025–26 was unremarkable (if anything, slightly
more competitive than the 42-year average).

The three most West-dominant seasons on record were 2013–14 (+4.08), 2003–04
(+3.73), and 2000–01 (+3.11), all much larger gaps. The 2025–26 East was
competitive.

**Opponent SRS context:** The games-weighted average SRS of the Knicks' playoff
opponents was **+3.67** (49th percentile among all 43 champions), essentially at
the historical median. The schedule was not unusually easy or hard.

![Conference strength gap (West − East SRS), 2025-26 flagged](../generated/images/knicks_2026_conference_gap.svg){width=100%}

![2025-26 regular-season SRS by team, colored by conference](../generated/images/knicks_2026_team_srs_2026.svg){width=100%}

---

## 4. Opponent-Adjusted Dominance

**Adjusted margin = raw margin − games-weighted opponent SRS.**
(Opponent SRS is weighted by games played in each series, so a 5-game Finals
opponent counts for 5 of 19 data points rather than 1 of 4.)

| Metric | 2025–26 Knicks | Historical rank |
|--------|----------------|-----------------|
| Raw avg margin | +14.9 pts/game | 1st (100th pct) |
| Opp SRS (games-weighted) | +3.67 pts/game | 49th pct |
| **Adjusted margin** | **+11.2 pts/game** | **1st (100th pct)** |

Top 5 adjusted-margin champions:

| Season | Raw | Opp SRS | Adj |
|--------|-----|---------|-----|
| **2025–26 Knicks** | **+14.9** | **+3.67** | **+11.2** |
| 2016–17 Warriors | +13.7 | +3.41 | +10.2 |
| 1986–87 Lakers | +10.8 | +1.32 | +9.5 |
| 1990–91 Bulls | +11.7 | +2.51 | +9.2 |
| 1985–86 Celtics | +10.6 | +2.83 | +7.7 |

All 43 champion seasons are included. For pre-1997 seasons where nba_api returns
null PLUS_MINUS, margins are derived from PTS (both team rows per game).

**Playoff overperformance**, comparing actual margins to what the Knicks' own
regular-season SRS (+6.05) would predict against those opponents (+2.38 expected
per game), gives +12.5 pts/game of outperformance, 2nd all-time (97.7th pct)
behind only the 2000–01 Lakers. Their playoff SRS was +17.53, an elevation of
+11.48 above their regular-season SRS, also 2nd all-time. The Knicks didn't
just face the right opponents: they played far above their regular-season level.

![Strength of schedule, avg opponent SRS per champion](../generated/images/knicks_2026_opponent_srs_ranking.svg){width=100%}

![2025-26 Knicks: playoff opponent SRS by round](../generated/images/knicks_2026_opponent_by_round.svg){width=100%}

---

## 5. Was the East Weak in the Playoffs?

The regular-season SRS numbers say no (§3). But a sharper question is whether
the East teams the Knicks beat in rounds 1–3 actually played *weaker in the
playoffs* than their regular-season ratings suggested, and whether the tight
Finals was because the Spurs were truly the better team in May–June.

The rounds 1–3 answer is a weak maybe; the Finals answer is a clearer yes: the Spurs were the toughest opponent of the run, playing well above their regular-season level.

Each opponent's playoff SRS is computed from their games **excluding** the
Knicks series, so it's an independent measure of their form against other
opponents. The Hawks had no independent playoff games (they only played the
Knicks), so they're excluded from this adjustment.

| Round | Opponent | Raw | Reg-SRS Adj | Playoff-SRS Adj |
|-------|----------|-----|-------------|-----------------|
| R1 | Hawks | +17.5 | +15.1 | n/a (no independent data) |
| R2 | 76ers | +22.2 | +22.5 | +23.7 |
| CF | Cavaliers | +19.2 | +15.5 | +16.9 |
| Finals | Spurs | +2.4 | −5.9 | −12.1 |

The 76ers and Cavaliers rated a touch below their regular-season marks in their
pre-Knicks games (−1.2 and −1.5 pts). Read those two lightly: each rests on only
a handful of independent playoff games, so a gap that small is as likely to be
the random bounce of a short schedule as a real dip. The Spurs are the firmer finding, because their number
comes from a full West bracket: a regular-season SRS of +8.28 but +14.48 in the
playoffs, a +6.2 jump (excluding the Finals; §6 reports +6.85 including it) and
the largest of any Knicks opponent this postseason.
The Knicks beat a team playing well above its own regular-season level.

**Net result:** Adjusting the full run for opponents' actual playoff
performance (excluding the Knicks series) gives a margin of +9.1 pts/game,
narrowly the best on record (the 1986–87 Lakers are +9.0, so the top spot here
is effectively a tie). The Knicks beat East opponents who were at or a bit below
their season-long form, then beat the best playoff-performing team in the field.

![Per-round raw vs. opponent-adjusted margins: adjustment using playoff SRS shifts the Finals story](../generated/images/knicks_2026_round_split.svg){width=100%}

---

## 6. Both Finalists Were the Biggest Risers

The Knicks did not reach the Finals as a polished regular-season team that simply
held form. By team rating (SRS, quality adjusted for schedule), they were only
the fifth-strongest team in the playoff field during the regular season, at
+6.05. In the playoffs they jumped to +17.53. That rise of **+11.48** was the
largest of any team in the 2026 playoffs.

The team they beat in the Finals made the second-biggest jump. The Spurs were a
stronger regular-season team than the Knicks, +8.28, second only to Oklahoma City
(+11.04) among playoff teams. They climbed to +15.13 in the playoffs, a rise of
**+6.85**. The Spurs entered the Finals both very good to begin with and getting
better, which is part of why the series was close. (This +15.13 covers all of
their playoff games, including the Finals against the Knicks, so it sits a little
above the +14.48 in §5, which leaves the Knicks series out to judge the Spurs
independently.)

| Team | Reg-season rating | Playoff rating | Jump |
|------|-------------------|----------------|------|
| **New York Knicks** | +6.05 | +17.53 | **+11.48** |
| **San Antonio Spurs** | +8.28 | +15.13 | **+6.85** |
| Portland Trail Blazers | -0.28 | +2.73 | +3.01 |
| Oklahoma City Thunder | +11.04 | +11.42 | +0.38 |

The regular-season rating leader, Oklahoma City (+11.04),
barely changed in the playoffs (+0.38) and finished well behind both finalists.
And the Finals paired the two teams that had improved the most since October: the
field's two hottest teams, not its two best regular-season teams.

These playoff ratings rest on a few weeks of games, so the exact figures carry
the same small-sample caution as the rest of the run (see §10). The order is
clear, though: both finalists rose further than anyone else.

![Regular-season to playoff jump in team rating: the Knicks rose more than any 2025-26 playoff team, the Spurs second](../generated/images/knicks_2026_field_elevation.svg){width=100%}

---

## 7. Other Context

**Clutch/close games:** 31.6% of Knicks playoff games were decided by 5 points
or fewer (84th percentile, more clutch than average champions). The Finals in
particular were tight: four of five games were decided by 4 points or fewer.

**Home/away splits:**
- Home: 9 games, 77.8% win rate (23rd percentile vs. champions, relatively
  weak at home for a champion)
- Away: 10 games, 90.0% win rate (98th percentile)

The Knicks won 90.0% of their road games, better than all but one champion in the dataset.

---

## 8. What the Betting Market Said

Betting spreads price in public information about each game, so they are a useful
outside benchmark for how good the Knicks looked at the time. The market's view
of the run:

**Overall:** 16-3 ATS (against the spread); their cover record exactly matches
their win-loss record. They beat the spread by an average of **+16.9 pts/game**
across 19 games. Beating the market in 16 of 19 tries is well beyond a coin
flip. Two cautions keep that from being as strong as it looks. First, those 19
games are really four series, and games inside a series move together (same
opponent, same kind of pricing miss), so they are not 19 independent bets:
adjust for that and the effective sample is closer to seven, leaving the result
weaker but still better than chance. Second, ATS margin is just the final margin
minus a near-zero spread, so this is not separate proof of dominance, it is
mostly the same scoreline told from the bookmaker's side. The signal comes
entirely from the first three rounds: 14-0 against the spread vs. East
opponents, with the Finals exactly dead-on (covered 2 of 5).

**But the two halves look nothing alike:**

| Round | Opponent | Avg Spread | Avg Actual | ATS Margin | Cover |
|-------|----------|-----------|------------|------------|-------|
| R1 | Hawks | Knicks -4.0 | +17.5 | +21.5 | **6/6** |
| R2 | 76ers | Knicks -4.0 | +22.2 | +26.2 | **4/4** |
| CF | Cavaliers | Knicks -2.8 | +19.2 | +22.0 | **4/4** |
| **Finals** | **Spurs** | **NYK +2.5** | **+2.4** | **−0.1** | **2/5** |

Against the three East opponents, the Knicks exceeded market expectations by
21–26 points per round. The market priced them as modest favorites (-3 to -4)
and they won by 17-22. Against the Spurs in the Finals, the market had them as
slight underdogs (+2.5) and they won by an average of exactly +2.4, essentially
a coin-flip that they won 4-1 in games.

The market saw the two halves differently before either began: modest East
favorites who then won by 17 to 22 a round, and a near-even Finals against a healthy,
elite Spurs team that the Knicks won by grinding out close games.

![Market expectations vs. actual margins: Knicks badly beat the spread against East opponents, Finals were dead-on](../generated/images/knicks_2026_market_vs_actual.svg){width=100%}

---

## 9. Opponent Health (No Injury Asterisk)

One recurring question about dominant playoff runs is whether key opposing players
were injured. The answer here: **no, they weren't.**

Using player-level game logs to measure how many of each opponent's rotation
players (averaging ≥15 min/game across the playoffs) appeared in each game of
the Knicks' series:

| Round | Opponent | Health |
|-------|----------|--------|
| R1 | Atlanta Hawks | 100% |
| R2 | Philadelphia 76ers | 96% |
| CF | Cleveland Cavaliers | 97% |
| Finals | San Antonio Spurs | **100%** |

Average across all four opponents: **98%**. The Spurs, the most dangerous team
and the one that gave the Knicks the tightest series, were fully intact. The
close Finals margin (+2.4 avg) reflects genuine competition, not a depleted
opponent. This removes the injury asterisk often attached to dominant runs.

![Opponent key-player availability across the 2025-26 Knicks playoff run](../generated/images/knicks_2026_opponent_health.svg){width=100%}

---

## 10. How Solid Is the #1 Ranking?

The "best opponent-adjusted margin of any champion" claim rests on a 19-game
run, and 19 games is a small sample. To see how solid the top spot is, we
re-played the run 20,000 times by re-drawing its 19 games at random (with
replacement) and re-ranked the result against the other 42 champions each time.

The Knicks finish #1 in about 60% of those re-runs, in the top three in 70%, and
in the top five in 82%. Their single most likely finish is #1, but across
re-draws the rank ranges from 1st to roughly 11th, and the opponent-adjusted
margin itself lands anywhere from +5.1 to +17.7 (best estimate +11.2).

A second check pushes the same way. A 19-game number that stands out partly
stands out by luck, so we pulled the Knicks' adjusted margin back toward what
championship runs normally look like (the other 42 champions average about +3
per game). Because playoff margins swing so much, 19 games only pin down about
40% of the estimate; the rest gets pulled toward the pack. That pulled-back
margin lands at **+6.5 per game**, with a plausible range of roughly +1.5 to
+11.5. Even after that haircut it still clears about 83% of champions.

This second test is deliberately tough on the Knicks, but it is also unfair in
their favor: it pulls only the Knicks back toward the average while leaving every
other champion frozen at its exact career number.

We also checked whether not knowing the opponents' exact strength matters: the
opponent ratings come from full regular seasons, and re-running the re-draws
while jostling each opponent's rating by its own margin of error barely moves
the result (the #1 chance stays at about 60%). The wobble in this ranking is
almost entirely the shortness of a 19-game run, not doubt about who the Knicks
played.

![How often the 2025-26 run still ranks #1 when its games are re-drawn](../generated/images/knicks_2026_bootstrap_margin.svg){width=100%}

**The fairest test treats every champion as uncertain, and it humbles the #1
claim.** The checks above froze the other 42 champions at their exact numbers.
But those numbers are noisy too: a champion that looks like +10 might truly be +7
or +13. When we shrink every champion toward the typical level by how shaky its
own number is, and then let all 43 compete while weighing everyone's
uncertainty at once, the Knicks come out as the single best only about **9% of
the time**. They land in the top three about 23% of the time and the top five
about 34%; their most likely spot is the middle of the top ten, with a range
that runs from 1st to deep in the pack.

Why so much lower than the 60% above? Two reasons. The Knicks' run was streaky:
huge blowouts in the sweeps next to a +2.4 Finals. A streaky run is weaker
evidence of a high true level than a steady one, so this test pulls the margin
back harder than the simple shrink above did: from +11.2 down to about +4.7,
rather than the +6.5 of the second check (which ignored streakiness). And several rivals, the 1990-91 Bulls, the
2022-23 Nuggets, the 2016-17 Warriors, were nearly as dominant on steadier
evidence, so once everyone's wobble is in play they overtake the Knicks often.

The honest bottom line across all of these checks: the 2025-26 Knicks own the
best raw opponent-adjusted number of any champion, and they are very likely one
of the best handful of title runs ever, but the data cannot crown them the single
best. Their chance of being the true #1 runs from roughly 60% (with the rest
of history left at its exact numbers) down to about 9% (the fairest test, where every champion is
allowed to be as uncertain as the Knicks).

![After fair shrinkage the champion field bunches together: the Knicks are about 9% to be the true #1](../generated/images/knicks_2026_hierarchical_posterior.svg){width=100%}

---

## 11. A Second Opinion: Other Rating Systems

Every opponent adjustment so far leans on one rating, SRS, which grades teams by
their season-long scoring margins. If the Knicks' #1 hinges on that single
choice, it is shaky. So we re-ran the whole opponent adjustment with two very
different ratings and checked whether the answer held.

**Wins-only (Bradley-Terry).** This system is fit from nothing but who beat whom;
it never sees a single point margin. That makes it the cleanest test of one
worry, that the Knicks' record margins are padded by garbage-time blowouts.
They are not: on a pure wins-only basis the Knicks' opponent-adjusted dominance
still ranks **first of 43**, and it rates their schedule almost exactly as SRS
does. Stripping margins out entirely does not knock them off the top, so the
dominance is real, not a scoreboard illusion.

**Elo (recency-weighted).** Elo, the running rating popularized by
FiveThirtyEight, is also margin-based but weights recent games more heavily. It
rated the Knicks' opponents tougher than SRS did, because the teams New York drew
were playing well down the stretch (Elo pegs the Spurs at +10.7 points above
average, against SRS's +8.3). A tougher-rated schedule means a bigger adjustment,
so the Knicks' Elo-adjusted margin is **+9.4 per game, third-best**, behind the
2016-17 Warriors and 1990-91 Bulls.

Put together, the three systems agree more than they disagree (all rank the
Knicks in the top three, and across champions their adjusted margins move in
near-lockstep). The one thing that moves the Knicks off #1 is not switching from
margins to wins, it is crediting opponents for late-season form: on full-season
opponent quality the Knicks are first, and only when recent form is weighted
heavily do they slip to third. That is the same lesson as §10: clearly elite,
plausibly the best, but not the unambiguous #1 the single SRS number suggests.

---

## 12. How Unlikely Was a 16-3 Run?

One last way to gauge the run: forget what happened and ask what the Knicks'
regular season predicted. We built a simple forecaster that knows only each
team's regular-season strength and who had home court, turns every game into a
win chance, and plays out the four best-of-seven rounds tens of thousands of
times.

The forecast was not kind. Because the Spurs out-rated the Knicks over the
regular season, the model made New York a Finals underdog (about a 31% chance to
win that series) and gave them only about a **15% chance to win the title at
all**. A run as clean as 16-3, losing just three games across four rounds, was
rarer still: only about **7% of the model's championship runs were that tidy**,
and barely **1%** of all simulated seasons produced both a title and three or
fewer losses.

So almost nothing about the Knicks' regular season predicted this. They were
"supposed" to lose around six or seven games on the way to a title they were not
even favored to win; they lost three and were seriously tested only in the
Finals. That is the §4–§5 margin story in win-loss terms: the Knicks played far
above their regular-season level when it counted. (The exact percentages shift a
little under a different assumed game-to-game swing, but the size of the
overperformance does not.)

---

## 13. Limitations

**Small sample and ranking uncertainty:** 19 playoff games produce a wide range
on the margin ([+7.4, +22.4]). The comparison set is also only 43 champions.
Several of the metrics here (adjusted margin, overperformance, elevation) all
measure closely related things; treat them as different angles on one story, not
independent votes. §10 puts numbers on this: with every other champion's number
left unchanged the #1 rank is roughly a 60/40 call, and under the fairer test that lets every
champion be as uncertain as the Knicks it falls to about 1-in-11. Not a settled
fact either way.

**Opponent SRS** for the reg-season-adjusted metrics is from regular-season
performance. For the playoff-adjusted metrics (§5), each opponent's playoff SRS
is computed from games *excluding* the Knicks series to avoid circularity;
the Hawks had no such games and are excluded from that adjustment.

**Era: scoring vs. pace.** The 2025–26 season has the most points per game in the
dataset (115.6 vs. historical mean 103.5), which looks like a reason to discount
the Knicks' margin. But high scoring is not the same as a fast game. Two ways to
adjust for it pull in different directions:

- *Scoring-share* (scale margins by points/game): a deliberately harsh take that
  treats the whole scoring boom as inflation. On this basis the raw margin drops
  from 1st to 3rd (+13.3, behind the 2000–01 Lakers and 2016–17 Warriors).
- *Possessions* (scale by estimated possessions, which isolate pace from
  shooting): the more correct adjustment. By this measure 2025–26 ran only about
  4% faster than average (101.8 possessions vs. 98.0), because the extra points
  come mostly from better three-point shooting, not more trips down the floor.
  Per 100 possessions the Knicks' raw margin (+14.6) and opponent-adjusted margin
  (+11.0) both stay **1st**.

So the era objection is weaker than the scoring-share number suggested: most of
2025–26's scoring is efficiency, not pace, and on a true pace-neutral basis the
margin claim survives at #1. The opponent adjustment also already absorbs some
era effect, since a champion's margins and its opponents' ratings are measured in
the same environment.

**Pre-1997 data:** PLUS_MINUS is null in the older NBA.com data. We derive it
from PTS (both team rows per game), which is algebraically exact for game
margins but may differ if box-score point totals differ from game records.

---

## 14. Methodology

All analysis uses Python (pandas, numpy). Data from NBA.com via nba_api
(LeagueGameFinder for game logs, LeagueStandingsV3 for standings). SRS
(Simple Rating System) is solved as a least-squares linear system
`(I − A) @ srs = mean_margin` constrained to `sum(srs) = 0`.

See `RESULTS.md` for full numerical output and `knicks_2026_analysis.py` for
all computation.
