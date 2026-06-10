# NBA Home Court Advantage — Key Findings

Analysis covers 1983-84 through 2024-25. All data from NBA.com via `nba_api`.
Regression uses game-level logistic regression (outcome: home win). McFadden R² reported.

---

## The Decline

Home court advantage has been falling for 40 years in both the regular season and playoffs, but the drop is steeper in the playoffs.

| Context        | ~1984–94 home win % | ~2023–25 home win % | Change |
|----------------|---------------------|---------------------|--------|
| Regular season | ~65%                | ~56–57%             | −8–9 pp |
| Playoffs       | ~68–70%             | ~57–59%             | −10–12 pp |

The 2020 NBA bubble (all neutral-site games) is excluded from playoff stats. COVID seasons (2019-20, 2020-21) are flagged as anomalies.

---

## What Explains It (Regular Season)

Sequential R² decomposition — each block added to the previous model:

| Factor added      | Explains (% of total model fit) |
|-------------------|---------------------------------|
| Era (structural)  | **56%** |
| Rest differential | 16% |
| Altitude (DEN/UTA)| 25% |
| Time zone diff    | 2% |
| COVID flag        | 1% |

**The era effect dominates.** The structural decline across eras is not explained by rest, altitude, or travel — it is a real, independent trend, likely driven by changes in officiating, player travel conditions, and broader league parity.

---

## Factor-by-Factor: What Matters and How Much

### 1. Era (Structural Decline) — Most Important
- Net decline: **−8.9 percentage points** from 1984–94 → 2023–25.
- Each successive era shows a statistically significant further decline (all p < 0.001).
- Accounts for 56% of the variance explained by the full model.

### 2. Rest Differential — Significant in Both Contexts

| Context        | Effect per day of rest advantage | Significance |
|----------------|----------------------------------|--------------|
| Regular season | +1.5 pp                          | *** |
| Playoffs       | +2.3 pp                          | * |

When the home team has more rest, they win more often — and the effect is larger in the playoffs. Schedule balance matters more when the stakes are higher.

### 3. Altitude (Denver / Utah) — Regular Season Only

| Context        | Effect        | Significance |
|----------------|---------------|--------------|
| Regular season | **+8.2 pp**   | *** |
| Playoffs       | −1.8 pp (n.s.)| not sig. |

High-elevation arenas (Nuggets and Jazz) carry a significant disadvantage for road teams in the regular season. The effect disappears in the playoffs — team strength confounds it (when Denver is good, they host better opponents).

### 4. Time Zone Differences — Not Significant

| Context        | Effect per zone crossed | Significance |
|----------------|-------------------------|--------------|
| Regular season | −0.4 pp                 | not sig. |
| Playoffs       | +1.2 pp                 | not sig. |

Time zone travel does not show a statistically reliable effect in either context. There are only ~107 coast-to-coast playoff matchups across 42 seasons — too sparse for reliable inference.

---

## Mechanism: Why Is Home Court Advantage Shrinking?

The box-score differential analysis (home minus away, per game) reveals three converging trends:

### Foul Differential — Referees Are Calling It More Evenly

| Era     | Home team foul advantage (fewer fouls called) |
|---------|-----------------------------------------------|
| 1984–94 | −1.23 fouls/game (regular season); −1.58 (playoffs) |
| 2023–25 | −0.20 fouls/game (regular season); −0.70 (playoffs) |

Trend: **+0.023 fouls/yr** (regular season, p < 0.001), **+0.020 fouls/yr** (playoffs, p < 0.01).

Home teams used to get called for far fewer fouls than road teams. That gap has nearly closed in the regular season and roughly halved in the playoffs. This is likely the single most important mechanism — refs are less influenced by crowd noise today than they were 40 years ago.

### eFG% Differential — Home Shooting Edge Is Shrinking

| Era     | Home eFG% advantage |
|---------|---------------------|
| 1984–94 | +1.56 pp (regular season); +1.47 pp (playoffs) |
| 2023–25 | +0.97 pp (regular season); +1.19 pp (playoffs) |

Trend: **−0.015 pp/yr** (regular season, p < 0.001).

Home teams used to shoot significantly more efficiently than road teams. That edge is narrowing — probably partly driven by the foul differential (fewer free throws for home teams) and partly by better road team preparation.

### 3-Point Attempt Rate — Shot Selection Is Converging

| Era     | Home 3PA-rate advantage (home 3PA/FGA − away 3PA/FGA) |
|---------|--------------------------------------------------------|
| 1984–94 | −0.35 pp (road teams took proportionally more 3s) |
| 2023–25 | +0.37 pp (now reversed — home teams take slightly more) |

Trend: **+0.017 pp/yr** (regular season, p < 0.001), **+0.031 pp/yr** (playoffs, p < 0.05).

In the early era, road teams took relatively more 3-pointers — likely a function of being forced into harder shots by home-court pressure. As the 3-point revolution normalized high-volume 3-point shooting league-wide, both home and away teams now take similar rates. The shot-selection disadvantage for road teams has been eliminated.

### FG% and FT% Differentials — Smaller Story

FG% differential (not eFG%) is also narrowing (−0.020 pp/yr, p < 0.001), consistent with the eFG% finding. FT% differential shows no significant trend in either direction — not a meaningful factor.

---

## Shot Zone Analysis (Since ~1996-97)

Using `LeagueDashTeamShotLocations` data (restricted area, non-RA paint, mid-range, corner 3, above-break 3):

**Paint access gap is closing:** Home teams used to have a 2–3 pp higher share of shots from the paint (combined RA + non-RA) compared to road teams in the same game. By the 2020s, that gap has shrunk to roughly 0.5–1 pp. This is consistent with both the eFG% narrowing (paint shots are the highest-efficiency shots) and the foul differential trend (getting to the paint means drawing fouls).

**Mid-range:** Road teams consistently take a higher share of mid-range shots (~1–1.5 pp more), a less efficient shot type. This gap has not changed dramatically — road teams are still being pushed to worse spots, just less so in recent years.

**Corner 3 and above-break 3:** No systematic home/road difference; both lines hover near zero. Shot location at the 3-point line is not a meaningful home court advantage.

---

## Summary Ranking: Most to Least Important

| Rank | Factor | Regular Season | Playoffs |
|------|--------|---------------|----------|
| 1 | **Structural era decline** | Very large (−8.9 pp over 40 yr) | Very large |
| 2 | **Foul differential** (refs more neutral) | Large, highly significant | Large, highly significant |
| 3 | **Altitude** (DEN/UTA) | +8.2 pp, highly significant | Not significant |
| 4 | **eFG% edge shrinking** | Significant decline trend | Smaller decline |
| 5 | **Rest differential** | +1.5 pp/day | +2.3 pp/day (larger!) |
| 6 | **3PA rate convergence** | Significant trend | Significant trend |
| 7 | **Paint access** (shot zones) | Declining but limited history | Noisy |
| 8 | **Time zone** | Not significant | Not significant |

The core story: home court advantage has eroded because **referees call the game more neutrally** than they did 40 years ago, **home teams no longer generate a disproportionate shooting edge**, and **road teams have adopted the same shot profile** (especially 3-point volume) as home teams. The structural shift across eras accounts for more than half of all explained variance; rest, altitude, and travel are secondary effects.
