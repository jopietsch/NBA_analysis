# Did the 2026 Knicks Have a Historic Playoff Run?

## 1. The Verdict (Up Front)

**Yes — the 2025–26 New York Knicks had a historically dominant playoff run.**

They went 16-3 (88th percentile win rate among all 43 champions since 1983–84)
and outscored opponents by an average of **+14.9 points per game** — the highest
single-season playoff margin in the dataset. After adjusting for the strength of
their opponents, the adjusted margin of **+11.4 pts/game** still ranks first
all-time. The East was **not** historically weak: the West-East SRS gap in
2025–26 was only +0.39 pts/game (37th percentile of West dominance), meaning the
East was stronger than average relative to the West in 63% of seasons since 1984.
The Knicks earned this — on a real schedule, against real competition.

The main caveat: the dominant margins came in the first three rounds (sweeps of
Philadelphia and Cleveland), while the NBA Finals against a Spurs team with SRS
+8.28 were much closer (4-1, avg margin +2.4 pts/game).

---

## 2. The Raw Numbers

The Knicks went **16-3** in the 2026 playoffs. Among all 43 champions in the
data (1983–84 through 2025–26):

- **Win-rate percentile: 88th** — 0.842, vs. mean 0.752, best (2016–17 Warriors)
  0.941
- **Average margin: 100th percentile** — +14.9 pts/game, best in 43 years

**Round-by-round:**

| Round | Opponent | Record | Avg Margin |
|-------|----------|--------|------------|
| First Round | Atlanta Hawks (SRS +2.38) | 4-2 | +17.5 |
| Second Round | Philadelphia 76ers (SRS -0.27) | 4-0 | +22.2 |
| Conference Finals | Cleveland Cavaliers (SRS +3.77) | 4-0 | +19.2 |
| NBA Finals | San Antonio Spurs (SRS +8.28) | 4-1 | +2.4 |

The two sweeps — which came against legitimate playoff teams, not pushovers —
drove the record margin. The Finals were tight: four of the five games were
decided by 5 points or fewer.

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
| 2022–23 Nuggets | +8.3 | +0.54 | +7.8 |
| 2000–01 Lakers | +12.8 | +5.54 | +7.2 |
| 2017–18 Warriors | +10.0 | +3.35 | +6.7 |

All 43 champion seasons are included. For pre-1997 seasons where nba_api returns
null PLUS_MINUS, margins are derived from PTS (both team rows per game).

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

The road-game dominance is striking. The Knicks were actually a better road team
in this playoff run than any other champion in the dataset.

---

## 6. Limitations

**Opponent SRS** is from regular-season performance, which may not fully reflect
playoff-mode strength. SRS treats all opponents equally regardless of round
(Finals opponent weighted the same as first-round opponent in our simple average
of unique opponents).

**Small sample:** 19 games is a small sample; the playoff margin could fluctuate
by ±2–3 pts/game across realizations of the same team-skill configuration.

**Era/pace:** We do not pace-adjust margins. Scoring in 2025–26 may differ from
1984. However, the SRS-based opponent adjustment partially addresses this because
both the champion's margins and opponents' SRS are measured in the same season's
context.

**Pre-1997 data:** PLUS_MINUS is null in the older NBA.com data. We derive it
from PTS (both team rows per game), which is algebraically exact for game
margins but may differ if box-score point totals differ from game records.

---

## 7. Methodology

All analysis uses Python (pandas, numpy). Data from NBA.com via nba_api
(LeagueGameFinder for game logs, LeagueStandingsV3 for standings). SRS
(Simple Rating System) is solved as a least-squares linear system
`(I − A) @ srs = mean_margin` constrained to `sum(srs) = 0`.

See `RESULTS.md` for full numerical output and `knicks_2026_analysis.py` for
all computation.
