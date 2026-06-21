# Did the 2026 Knicks Have a Historic Playoff Run?

## 1. The Verdict (Up Front)

**Yes: the 2025–26 New York Knicks had a historically dominant playoff run.**

They went 16-3 (88th percentile win rate among all 43 champions since 1983–84)
and outscored opponents by an average of **+14.9 points per game**, the highest
raw playoff margin in the dataset. Across the game-to-game swing of a 19-game
run, that margin could sit anywhere from +7.4 to +22.4: even at the unlucky end,
the run would still rank above the historical average. Note that 2025–26 is the
highest-scoring era since 1984; once margins are scaled to a common scoring
level, the raw margin drops to 3rd all-time (+13.3). After adjusting for opponent
strength, the margin of **+11.2 pts/game** ranks first all-time (though that #1
is a close call, see §9); after both the opponent and the scoring adjustment,
it's +10.1, still first, but essentially tied with the 2016–17 Warriors (+10.0). The East was **not** historically weak: the West-East SRS gap in
2025–26 was only +0.39 pts/game (37th percentile of West dominance); in 63% of
seasons since 1984, the West was even *more* dominant than this. The Knicks earned
this, on a real schedule, against real competition.

There is a real nuance in the East record: the Hawks, 76ers, and Cavaliers all
played *below* their regular-season ratings in the postseason, so some of the
rounds 1–3 dominance reflects opponents underperforming, not just Knicks
excellence. The Finals tells the opposite story: the Spurs elevated from a
regular-season SRS of +8.28 to a playoff SRS of +14.48, the most improved team
in these playoffs. Winning that series 4-1, even narrowly (+2.4 avg margin),
was the hardest test of the run.

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

The Finals answer is a clear yes; the rounds 1–3 answer is a weak maybe.

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
noise as a real dip. The Spurs are the firmer finding, because their number
comes from a full West bracket: a regular-season SRS of +8.28 but +14.5 in the
playoffs, a +6.2 jump and the largest of any Knicks opponent this postseason.
The Knicks beat a team playing well above its own regular-season level.

**Net result:** Adjusting the full run for opponents' actual playoff
performance (excluding the Knicks series) gives a margin of +9.1 pts/game,
narrowly the best on record (the 1986–87 Lakers are +9.0, so the top spot here
is effectively a tie). The Knicks beat East opponents who were at or a bit below
their season-long form, then beat the best playoff-performing team in the field.

![Per-round raw vs. opponent-adjusted margins: adjustment using playoff SRS shifts the Finals story](../generated/images/knicks_2026_round_split.svg){width=100%}

---

## 6. Other Context

**Clutch/close games:** 31.6% of Knicks playoff games were decided by 5 points
or fewer (84th percentile, more clutch than average champions). The Finals in
particular were tight: four of five games were decided by 4 points or fewer.

**Home/away splits:**
- Home: 9 games, 77.8% win rate (23rd percentile vs. champions, relatively
  weak at home for a champion)
- Away: 10 games, 90.0% win rate (98th percentile)

The Knicks won 90.0% of their road games, better than all but one champion in the dataset.

---

## 7. What the Betting Market Said

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
opponents, with the Finals exactly dead-on (2-5).

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
favorites who then blew the doors off, and a near-even Finals against a healthy,
elite Spurs team that the Knicks won by grinding out close games.

![Market expectations vs. actual margins: Knicks badly beat the spread against East opponents, Finals were dead-on](../generated/images/knicks_2026_market_vs_actual.svg){width=100%}

---

## 8. Opponent Health (No Injury Asterisk)

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

## 9. How Solid Is the #1 Ranking?

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

This second test is deliberately tough: it pulls only the Knicks back toward the
average while leaving every other champion at their own (also noisy) number. Read
together, the two checks bracket the answer. At the low end the 2025-26 run is a
clearly above-average championship; at the high end it is the best
opponent-adjusted run on record. The single best guess stays near the top, but
"#1 by a wide margin" is not what the uncertainty supports.

We also checked whether not knowing the opponents' exact strength matters: the
opponent ratings come from full regular seasons, and re-running the re-draws
while jostling each opponent's rating by its own margin of error barely moves
the result (the #1 chance stays at about 60%). The wobble in this ranking is
almost entirely the shortness of a 19-game run, not doubt about who the Knicks
played.

![How often the 2025-26 run still ranks #1 when its games are re-drawn](../generated/images/knicks_2026_bootstrap_margin.svg){width=100%}

---

## 10. Limitations

**Small sample and ranking uncertainty:** 19 playoff games produce a wide range
on the margin ([+7.4, +22.4]). The comparison set is also only 43 champions.
Several of the metrics here (adjusted margin, overperformance, elevation) all
measure closely related things; treat them as different angles on one story, not
independent votes. §9 puts numbers on this: the exact #1 rank is roughly a
60/40 call, not a settled fact.

**Opponent SRS** for the reg-season-adjusted metrics is from regular-season
performance. For the playoff-adjusted metrics (§5), each opponent's playoff SRS
is computed from games *excluding* the Knicks series to avoid circularity;
the Hawks had no such games and are excluded from that adjustment.

**Era / scoring environment:** The 2025–26 season is the highest-scoring era in
the dataset (115.6 pts/team/game vs. historical mean 103.5). What we call the
"pace" adjustment scales each era's margins by its scoring level, so it is really
a share-of-scoring adjustment: a 10-point win is a smaller slice of a 115-point
game than of a 95-point one. It is not a true possessions-based pace adjustment,
which would need possession counts we don't pull here. On that scoring-adjusted
basis the Knicks' raw margin drops from 1st to 3rd (+13.3, behind the 2000–01
Lakers +13.9 and 2016–17 Warriors +13.4). Apply both the opponent and the
scoring adjustment and the Knicks stay first at +10.1, essentially tied with the
2016–17 Warriors (+10.0). The opponent adjustment already absorbs some of the era
effect, since a champion's margins and its opponents' SRS are measured in the
same scoring environment, but the raw-margin claim is clearly era-inflated.

**Pre-1997 data:** PLUS_MINUS is null in the older NBA.com data. We derive it
from PTS (both team rows per game), which is algebraically exact for game
margins but may differ if box-score point totals differ from game records.

---

## 11. Methodology

All analysis uses Python (pandas, numpy). Data from NBA.com via nba_api
(LeagueGameFinder for game logs, LeagueStandingsV3 for standings). SRS
(Simple Rating System) is solved as a least-squares linear system
`(I − A) @ srs = mean_margin` constrained to `sum(srs) = 0`.

See `RESULTS.md` for full numerical output and `knicks_2026_analysis.py` for
all computation.
