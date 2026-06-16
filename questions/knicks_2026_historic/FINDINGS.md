# Did the 2026 Knicks Have a Historic Playoff Run?

## 1. The Verdict (Up Front)

**Yes — the 2025–26 New York Knicks had a historically dominant playoff run.**

They went 16-3 (88th percentile win rate among all 43 champions since 1983–84)
and outscored opponents by an average of **+14.9 points per game** — the highest
single-season playoff margin in the dataset. After adjusting for the strength of
their opponents, the adjusted margin of **+11.4 pts/game** still ranks first
all-time. The East was **not** historically weak: the West-East SRS gap in
2025–26 was only +0.39 pts/game (37th percentile of West dominance) — in 63% of
seasons since 1984, the West was even *more* dominant than this. The Knicks earned
this — on a real schedule, against real competition.

The main caveat: the dominant margins came before the Finals — including sweeps
of Philadelphia and Cleveland — while the NBA Finals against a Spurs team with SRS
+8.28 were much closer (4-1, avg margin +2.4 pts/game). But one common asterisk
doesn't apply: all four opponents were essentially fully healthy when they played
the Knicks (average availability 98%; the Spurs were at 100%).

![Opponent-adjusted playoff dominance — 2025-26 Knicks rank #1 all-time among 43 champions](generated/knicks_2026_adjusted_margin_ranking.png){height=0.60}

---

## 2. The Raw Numbers

The Knicks went **16-3** in the 2026 playoffs. Among all 43 champions in the
data (1983–84 through 2025–26):

- **Win-rate percentile: 88th** — 0.842, vs. mean 0.752, best (2016–17 Warriors)
  0.941
- **Average margin: 100th percentile** — +14.9 pts/game, best in 43 years

**Round-by-round** (SRS = team quality relative to schedule; higher = stronger):

| Round | Opponent | Record | Avg Margin |
|-------|----------|--------|------------|
| First Round | Atlanta Hawks (SRS +2.38) | 4-2 | +17.5 |
| Second Round | Philadelphia 76ers (SRS -0.27) | 4-0 | +22.2 |
| Conference Finals | Cleveland Cavaliers (SRS +3.77) | 4-0 | +19.2 |
| NBA Finals | San Antonio Spurs (SRS +8.28) | 4-1 | +2.4 |

The two sweeps — against Cleveland (SRS +3.77, a genuine title contender) and
Philadelphia (SRS -0.27) — drove the record margin. The Finals were tight: four
of the five games were decided by 4 points or fewer.

![Playoff win rate — all 43 champions ranked](generated/knicks_2026_win_rate_ranking.png){height=0.60}

![Average playoff margin — all 43 champions ranked](generated/knicks_2026_margin_ranking.png){height=0.60}

![2025-26 Knicks: game-by-game margins across 19 playoff games](generated/knicks_2026_game_margins.png){height=0.25}

---

## 3. Was the East Weak?

**No, not historically.** The West-East SRS gap in 2025–26 was only **+0.39
pts/game**, placing the season at the **37th percentile of West dominance**. In
63% of seasons since 1984, the West has been *more* dominant relative to the
East than in 2025–26. The East inter-conference win rate was 0.487 (slightly
below 0.500, near parity).

The three most West-dominant seasons on record were 2013–14 (+4.08), 2003–04
(+3.73), and 2000–01 (+3.11) — all much larger gaps. The 2025–26 East was
competitive.

**Opponent SRS context:** The average regular-season SRS of the Knicks' four
playoff opponents was **+3.54** (53rd percentile among all 43 champions), slightly
above the historical median. The schedule was not unusually easy or hard.

![Conference strength gap (West − East SRS) — 2025-26 flagged](generated/knicks_2026_conference_gap.png){height=0.25}

![2025-26 regular-season SRS by team, colored by conference](generated/knicks_2026_team_srs_2026.png){height=0.25}

---

## 4. Opponent-Adjusted Dominance

**Adjusted margin = raw margin − average opponent SRS.**

| Metric | 2025–26 Knicks | Historical rank |
|--------|----------------|-----------------|
| Raw avg margin | +14.9 pts/game | 1st (100th pct) |
| Avg opp SRS | +3.54 pts/game | 53rd pct |
| **Adjusted margin** | **+11.4 pts/game** | **1st (100th pct)** |

Comparison — top 5 adjusted-margin champions:

| Season | Raw | Opp SRS | Adj |
|--------|-----|---------|-----|
| **2025–26 Knicks** | **+14.9** | **+3.54** | **+11.4** |
| 2016–17 Warriors | +13.7 | +3.45 | +10.2 |
| 1986–87 Lakers | +10.8 | +0.75 | +10.1 |
| 1990–91 Bulls | +11.7 | +2.24 | +9.5 |
| 1985–86 Celtics | +10.6 | +2.57 | +8.0 |

All 43 champion seasons are included. For pre-1997 seasons where nba_api returns
null PLUS_MINUS, margins are derived from PTS (both team rows per game).

![Strength of schedule — avg opponent SRS per champion](generated/knicks_2026_opponent_srs_ranking.png){height=0.60}

![2025-26 Knicks: playoff opponent SRS by round](generated/knicks_2026_opponent_by_round.png){height=0.25}

---

## 5. Other Context

**Clutch/close games:** 31.6% of Knicks playoff games were decided by 5 points
or fewer (84th percentile — more clutch than average champions). The Finals in
particular were tight: four of five games were decided by 4 points or fewer.

**Home/away splits:**
- Home: 9 games, 77.8% win rate (23rd percentile vs. champions — relatively
  weak at home for a champion)
- Away: 10 games, 90.0% win rate (98th percentile — extraordinary road
  dominance)

The road-game dominance is striking. In this playoff run the Knicks were a better
road team than all but one champion in the dataset.

---

## 6. What the Betting Market Said

Vegas pricing is the most efficient aggregation of expert opinion available.
The market's verdict on the Knicks' playoff run is striking:

**Overall:** 16-3 ATS (against the spread) — their cover record exactly matches
their win-loss record. They beat the spread by an average of **+16.9 pts/game**
across 19 games, which is extraordinary.

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
slight underdogs (+2.5) and they won by an average of exactly +2.4 — essentially
a coin-flip that they won 4-1 in games.

**What this means:** The market clearly distinguished between the two halves of
this run. The first three rounds were a statement — the Knicks were far better
than anyone expected against East competition. The Finals was exactly the
competitive series the market predicted: a nearly even matchup against a healthy,
elite Spurs team that the Knicks won by grinding out close games.

![Market expectations vs. actual margins: Knicks badly beat the spread against East opponents, Finals were dead-on](generated/knicks_2026_market_vs_actual.png){height=0.45}

---

## 7. Opponent Health (No Injury Asterisk)

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

Average across all four opponents: **98%**. The Spurs — the most dangerous team
and the one that gave the Knicks the tightest series — were fully intact. The
close Finals margin (+2.4 avg) reflects genuine competition, not a depleted
opponent. This removes the injury asterisk often attached to dominant runs.

![Opponent key-player availability across the 2025-26 Knicks playoff run](generated/knicks_2026_opponent_health.png){height=0.25}

---

## 8. Limitations

**Opponent SRS** is from regular-season performance, which may not fully reflect
playoff-mode strength. SRS treats all opponents equally regardless of round
(Finals opponent weighted the same as first-round opponent in our simple average
of unique opponents).

**Small sample:** 19 games is a small sample; the playoff margin could swing
meaningfully across different realizations of the same team-skill configuration.

**Era/pace:** We do not pace-adjust margins. Scoring in 2025–26 may differ from
1984. However, the SRS-based opponent adjustment partially addresses this because
both the champion's margins and opponents' SRS are measured in the same season's
context.

**Pre-1997 data:** PLUS_MINUS is null in the older NBA.com data. We derive it
from PTS (both team rows per game), which is algebraically exact for game
margins but may differ if box-score point totals differ from game records.

---

## 9. Methodology

All analysis uses Python (pandas, numpy). Data from NBA.com via nba_api
(LeagueGameFinder for game logs, LeagueStandingsV3 for standings). SRS
(Simple Rating System) is solved as a least-squares linear system
`(I − A) @ srs = mean_margin` constrained to `sum(srs) = 0`.

See `RESULTS.md` for full numerical output and `knicks_2026_analysis.py` for
all computation.
