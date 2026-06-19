# NBA Home Court Advantage: The Short Version

For four decades, NBA home teams have been winning less. This is the one-page version of a long report, built around three charts to answer three questions: **Has home court really changed? What makes it an advantage in the first place? And what's driving the decline, and what isn't?**

---

## 1. Yes, it really changed

![Home win % per season, 1983–84 through 2025–26: regular season (top) and playoffs (bottom), with long-run trend fits and rule-change-era shading.](../generated/nba_home_court_advantage_season.png){width=100%}

Home teams used to win about **65%** of regular-season games and nearly **68%** in the playoffs. Today it's about **55%** and **58%**, roughly a 10-point fall in both. Most of it is a slow, steady erosion of about a quarter of a percentage point a year, with two sharper drops layered on top: one in the mid-1990s, one after 2017. The playoffs followed the same path with nearly a two-decade lag, holding firm through the 2000s and 2010s before joining the slide.

---

## 2. What home court is made of, and where it broke

![Box-score category shares. Left: what creates the home advantage. Right: what's eroding it. Regular season and playoffs, bars summing to 100%.](../generated/nba_home_court_mediation.png){width=100%}

Four measurable categories account for about **95%** of the entire advantage (left), in both the regular season and the playoffs: **shooting, rebounding, foul calls, and turnover margin**. Shooting is the single biggest piece.

But the categories that *created* the edge are not the ones that *erased* it (right). The two everyone blames, the narrowing whistle and the three-point shift, explain only about a fifth each of the regular-season decline. **Rebounding and turnovers together carry more than half.** Rebounding is the largest single contributor, and it is largely independent of the three-point shift.

---

## 3. The rebounding edge eroded

![Left: the home team's offensive- and defensive-rebound edges season by season; the offensive edge collapses through zero while the defensive edge only softens. Right: the home rebound-share edge fades alongside the league-wide retreat from offensive rebounding.](../generated/nba_home_court_rebounding.png){width=100%}

The home rebounding edge has shrunk for 40 years, and it isn't the three-point story in disguise. Hold three-point volume constant and the shooting edge vanishes while the rebounding edge barely moves.

The erosion is entirely on the **offensive** glass (left): the home team's offensive-rebound edge fell from more than half a board per game to slightly *below* zero, while its defensive-rebounding edge only softened. Measured as a pace-free share of available rebounds, the advantage shrank roughly **tenfold**. It tracks a league-wide retreat from the offensive boards (right): the offensive-rebound rate fell from **33% to 26%** as teams traded second chances for transition defense. The playoffs show the same fade.

---

## What *didn't* do it

None of the usual explanations hold up: rule changes (with one exception, 1994–95), travel and time zones, pace of play, competitive balance, and crowd size. Arenas have stayed near capacity, setting records in the very years home court hit its lows. The cleanest test came by accident: in the empty arenas of 2020–21, home teams won just **51%**; the moment any crowd returned, **58.5%**. A live crowd is a switch that flips with the doors, not a dial that's been slowly turning down for 40 years.

## What caused it

Home court is fading because the on-court advantages that built it, a friendlier whistle and a rebounding edge, have been worn down by fairer officiating and a league-wide move away from the offensive boards. The crowd still shows up. The game just stopped rewarding it the way it once did.

---

## Appendix A: Companion Documents

::: {.content-visible when-format="html"}
| Document | Description |
|---|---|
| [Full Report](nba_home_court_advantage_report.html) | Complete findings with all charts, section-by-section analysis, and the ruled-out factors. |
| [Regression Results](nba_home_court_results.html) | Full statistical output: regression tables, significance tests, and coefficient values. |
| [Stats Explainer](home_court_stats_explainer.html) | Guide to the statistical methods used, written for a general audience. |
| [Stats Tutorial](../../generated/stats_tutorial.html) | Worked examples reproducing key results from the regression output. |
:::

::: {.content-visible when-format="typst"}
All files are in the same folder as this PDF (`generated/`), except the Stats Tutorial which is one level up in `../generated/`.

| Document | File | Description |
|---|---|---|
| Full Report | `nba_home_court_advantage_report.pdf` | Complete findings with all charts, section-by-section analysis, and the ruled-out factors. |
| Regression Results | `nba_home_court_results.pdf` | Full statistical output: regression tables, significance tests, and coefficient values. |
| Stats Explainer | `home_court_stats_explainer.pdf` | Guide to the statistical methods used, written for a general audience. |
| Stats Tutorial | `../generated/stats_tutorial.pdf` | Worked examples reproducing key results from the regression output. |
:::
