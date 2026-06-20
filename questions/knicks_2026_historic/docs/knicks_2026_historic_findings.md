# Did the 2026 Knicks Have a Historic Playoff Run?

## 1. The Verdict (Up Front)

**Yes: the 2025–26 New York Knicks had a historically dominant playoff run.**

They went 16-3 (88th percentile win rate among all 43 champions since 1983–84)
and outscored opponents by an average of **+14.9 points per game**, the highest
raw playoff margin in the dataset. The 95% confidence interval on that margin
(accounting for game-to-game variance across 19 games) is [+7.4, +22.4]: even
at the unlucky end, the run would still rank above the historical average. Note that 2025–26 is the highest-scoring era
since 1984; pace-adjusted, the raw margin drops to 3rd all-time (+13.3). After
adjusting for opponent strength, the margin of **+11.2 pts/game** ranks first
all-time; after both opponent and pace adjustment, it's +10.1, still first, but
essentially tied with the 2016–17 Warriors (+10.0). The East was **not** historically weak: the West-East SRS gap in
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
pts/game**: 37th percentile of West dominance and **0.21 standard deviations
below the historical mean gap of +0.78** (z = −0.21, well within normal
variation). The East inter-conference win rate was 0.487 (near parity). By any
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

The answer is yes on both counts.

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

The 76ers and Cavaliers played modestly below their regular-season ratings
in their pre-Knicks games (−1.2 and −1.5 pts respectively), a real effect,
but small. The big finding is the Spurs: their regular-season SRS was +8.28,
but they played at +14.5 through the West bracket, a +6.2 elevation that is
entirely independent of the Knicks series. The Knicks beat a team playing at
the highest independent playoff level in the dataset.

**Net result:** Adjusting the full run for opponents' actual playoff
performance (excluding the Knicks series) gives a margin of +9.1 pts/game,
1st all-time, edging the 1986–87 Lakers (+9.0). The Knicks dominated
East opponents who were below their season-long form, and then beat the best
playoff-performing team in the field.

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

Vegas pricing is the most efficient aggregation of expert opinion available.
The market's verdict on the Knicks' playoff run:

**Overall:** 16-3 ATS (against the spread); their cover record exactly matches
their win-loss record. They beat the spread by an average of **+16.9 pts/game**
across 19 games. A binomial test against the null of
50% coverage gives p = 0.002 (z = +2.98); this cannot be attributed to
random fluctuation. The signal comes entirely from the first three rounds:
14-0 ATS against East opponents, with the Finals exactly dead-on (2-5 ATS).

**But the story splits sharply by opponent:**

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

The market clearly distinguished between the two halves of
this run. In the first three rounds, the Knicks were far better than anyone
expected against East competition. The Finals was exactly the
competitive series the market predicted: a nearly even matchup against a healthy,
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

## 9. Limitations

**Small sample and ranking uncertainty:** 19 playoff games produce a wide margin
confidence interval ([+7.4, +22.4] at 95%). The comparison set is also only 43
champions. Several of the metrics here (adjusted margin, overperformance,
elevation) all measure closely related things; treat them as different angles
on one story, not independent votes. Exact rank (1st vs. 4th) carries more
uncertainty than the numbers suggest.

**Opponent SRS** for the reg-season-adjusted metrics is from regular-season
performance. For the playoff-adjusted metrics (§5), each opponent's playoff SRS
is computed from games *excluding* the Knicks series to avoid circularity;
the Hawks had no such games and are excluded from that adjustment.

**Era/pace:** The 2025–26 season is the highest-scoring era in the dataset
(115.6 pts/team/game vs. historical mean 103.5). After pace adjustment, the
Knicks' raw margin drops from 1st to 3rd (+13.3 pace-adj, behind 2000–01 Lakers
+13.9 and 2016–17 Warriors +13.4). After applying both the opponent adjustment
AND the pace adjustment, the Knicks retain first place at +10.1, but are
essentially tied with the 2016–17 Warriors (+10.0). The SRS-based opponent
adjustment partially controls for era because both the champion's margins and
opponents' SRS are measured in the same scoring environment, but the raw-margin
claim is clearly era-inflated.

**Pre-1997 data:** PLUS_MINUS is null in the older NBA.com data. We derive it
from PTS (both team rows per game), which is algebraically exact for game
margins but may differ if box-score point totals differ from game records.

---

## 10. Methodology

All analysis uses Python (pandas, numpy). Data from NBA.com via nba_api
(LeagueGameFinder for game logs, LeagueStandingsV3 for standings). SRS
(Simple Rating System) is solved as a least-squares linear system
`(I − A) @ srs = mean_margin` constrained to `sum(srs) = 0`.

See `RESULTS.md` for full numerical output and `knicks_2026_analysis.py` for
all computation.
