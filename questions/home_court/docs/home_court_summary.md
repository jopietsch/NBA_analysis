# NBA Home Court Advantage: The Short Version

*Draft — June 2026*

For four decades, NBA home teams have been winning less. This is the one-page version of a long report, built around three charts to answer three questions: **Has home court really changed? What makes it an advantage in the first place? And what's driving the decline, and what isn't?**

---

## 1. Yes, it really changed

![Home win % per season, 1983–84 through 2025–26: regular season (top) and playoffs (bottom), with long-run trend fits and rule-change-era shading.](../generated/nba_home_court_advantage_season.png){width=100%}

Home teams used to win about **65%** of regular-season games and nearly **68%** in the playoffs. Today it's about **55%** and **58%**, roughly a 10-point fall in both. Most of it is a slow, steady erosion of about a quarter of a percentage point a year, with two sharper drops layered on top: one in the mid-1990s, one after 2017. The playoffs followed the same path with nearly a two-decade lag, holding firm through the 2000s and 2010s before joining the slide.

---

## 2. What home court is made of, and where it broke

![Box-score category shares. Left: what creates the home advantage. Right: what's eroding it. Regular season and playoffs.](../generated/nba_home_court_mediation.png){width=100%}

Four measurable categories account for about **95%** of the entire advantage (left), in both the regular season and the playoffs: **shooting, rebounding, foul calls, and turnover margin**. Shooting is the single biggest piece.

But the categories that *created* the edge are not the ones that *erased* it (right). The two everyone blames, the narrowing whistle and the three-point shift, explain only about a fifth each of the regular-season decline directly. **Rebounding and turnovers together carry more than half.** Rebounding is the largest single contributor, and unlike shooting it is not the three-point shift in disguise.

---

## 3. The rebounding edge eroded

![Four panels on the home rebounding and turnover edges. Far left: home vs. away offensive-rebound rates (solid) and defensive-rebound rates (dotted) converging over time. Center-left: the raw home-minus-away rebound differentials, both declining. Center-right: seasons with a bigger home rebounding edge tend to be seasons home teams win more (association, not causation). Far right: the home turnover edge fading from about 0.4 to near zero.](../generated/nba_home_court_rebounding.png){width=100%}

The home rebounding edge has shrunk for 40 years, and it isn't the three-point story in disguise. Hold three-point volume constant and the shooting edge vanishes while the rebounding edge barely moves.

Both sides of the glass show the edge fading, but the clean measure is the **offensive** share of available rebounds, which collapsed roughly **tenfold**. The home team's offensive-rebound edge fell from more than half a board a game to slightly *below* zero: home teams simply stopped crashing the offensive boards harder than visitors do. It tracks a league-wide retreat from the offensive glass, where the offensive-rebound rate fell from **33% to 26%** as teams traded second chances for transition defense. The home **turnover** edge faded over the same span, the next-largest piece of the decline. The playoffs show the same fade.

---

## What *didn't* do it

None of the usual explanations hold up: rule changes (with one exception, 1994–95), travel and time zones, pace of play, competitive balance, and crowd size. Arenas have stayed near capacity, setting records in the very years home court hit its lows. The cleanest test came by accident: in the empty arenas of 2020–21, home teams won just **51%**; the moment any crowd returned, **58.5%**. A live crowd is a switch that flips with the doors, not a dial that's been slowly turning down for 40 years.

## What caused it

Home court is fading because the on-court advantages that built it have worn away: fairer officiating narrowed the whistle, the league-wide move to the three-point line shrank the home shooting edge, and home teams lost their grip on the boards and on the turnover margin. Rebounding is the biggest single piece, and the one the three-point shift doesn't explain. The crowd still shows up. The game just stopped rewarding it the way it once did.

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
