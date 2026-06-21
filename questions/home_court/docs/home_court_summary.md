# NBA Home Court Advantage: The Short Version

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

For four decades, NBA home teams have been winning less. This is the one-page version of a long report, built around charts to answer three questions: **Has home court really changed? What makes it an advantage in the first place? And what's driving the decline, and what isn't?**

---

## 1. Yes, it really changed

![Home win % per season, 1983–84 through 2025–26: regular season (top) and playoffs (bottom), with long-run trend fits and rule-change-era shading.](../generated/images/home_court_advantage_season.svg){#fig-advantage-season width=100%}

Home teams used to win about **65%** of regular-season games and nearly **68%** in the playoffs. Today it's about **55%** and **58%**, roughly a 10-point fall in both. The scoring edge shrank to match: home teams used to outscore visitors by about **3 points per 100 possessions** in the regular season, and now closer to **2**. Most of it is a slow, steady erosion of about a quarter of a percentage point a year, with two sharper drops on top: one in the mid-1990s, one after 2017. The playoffs followed the same path with nearly a two-decade lag, holding firm through the 2000s and 2010s before joining the slide.

---

## 2. What home court is made of, and where it broke

![Box-score category shares. Left: what creates the home advantage (level). Right: what share of the 40-year decline each category carries. Regular season and playoffs.](../generated/images/home_court_mediation.svg){#fig-mediation width=100%}

Four categories account for about **95%** of the entire advantage (left panel): **shooting, rebounding, foul calls, and turnover margin**. Shooting is the single biggest piece, more than 40%, followed by rebounding.

The right panel shows where the decline has registered. Rebounding carries the largest share at roughly **30%**, followed by turnovers at about **27%**. Together they account for more than half the drop. Shooting, where the three-point shift registers most directly, accounts for about **21%**, and the narrowing whistle for about **18%**. Three-point shooting also reaches into the foul and turnover categories, so its total footprint is close to half the decline overall. What it does not explain is rebounding: the largest single driver, and the one that barely moves when three-point volume is held constant.

---

## 3. The rebounding and turnover edges eroded

![Four panels on the home rebounding and turnover edges. Far left: home vs. away offensive-rebound rates converging and crossing over time. Center-left: the raw home-minus-away rebound differentials, both declining. Center-right: seasons with a bigger home rebounding edge tend to be seasons home teams win more (association, not causation). Far right: the home turnover edge fading from about 0.4 to near zero.](../generated/images/home_court_rebounding.svg){#fig-rebounding width=100%}

The home rebounding edge has shrunk for 40 years, and it isn't the three-point story in disguise. Hold three-point volume constant and the shooting edge vanishes; the rebounding edge barely moves.

The cleaner measure is the **offensive** share of available rebounds. The home team's offensive-rebound rate fell from **34% to 26%** while the away team's fell only from **31% to 26%**. The lines converge and cross by 2025–26: home teams no longer crash the offensive boards more aggressively than visitors. The home **turnover** edge faded over the same span, contributing nearly as much to the overall decline. Home teams once committed about **0.4 fewer turnovers per game** than visitors; that gap has nearly closed. The playoffs show the same fade on both counts.

---

## 4. The playoff picture

![Playoff home win % for each game in a series (G1 through G7), all eras combined. Game 5, back at the top seed's arena after two road games, is the most lopsided. Road teams show no evidence of adapting as the series goes on.](../generated/images/home_court_series_breakdown.svg){#fig-series-breakdown width=100%}

The decline is real, but home court is still a powerful force in the playoffs. Games 1 and 2 go to the home team **69% and 72%** of the time. Game 5, back at the top seed's building, is the most lopsided at **74.5%**. Even Game 7 still goes to the home team **64%** of the time. Road teams show no evidence of adapting as a series deepens.

When you translate those per-game odds into a seven-game series, the format flattens the edge considerably. A team with home court in the 1980s had about a **55%** chance of winning a best-of-7; today that has fallen to just under **52%**: barely better than a coin flip at the series level, even though the per-game advantage is still real.

---

## What didn't do it

Rule changes (with one exception, 1994–95), travel and time zones, pace of play, competitive balance, and crowd size all fail the test. Arenas have stayed near capacity, setting records in the very years home court hit its lows.

The crowd finding deserves its own moment. In the empty arenas of 2020–21, home teams won just **51%**. With any crowd at all: **58.5%**. A live crowd is a genuine ingredient worth about seven points on the night. But it is a switch that flips with the doors, not a dial that has been slowly turning down for 40 years.

---

## What caused it

![Home-minus-away differentials over time: free throw attempts, FG%, eFG%, 3PA rate, 3P%, and FT%. Each panel shows the per-season gap; a trend toward zero means that component of the home edge is narrowing.](../generated/images/home_court_advantage_differentials.svg){#fig-advantage-differentials width=100%}

Home court is fading because the on-court advantages that built it have worn away. Referees are calling fairer games: home teams once attempted roughly **2 more free throws per game** than visitors; now it's under half a free throw. The league-wide move to the three-point line shrank the home shooting edge, with ripple effects on foul calls and turnovers. And home teams lost their grip on the offensive glass and on the turnover margin, which together account for more than half the decline, separately from the three-point shift.

Both factors driving that half of the decline are approaching their practical limits. Three-point attempts now make up about **40%** of all shots; the offensive-rebound rate has fallen from **33% to 26%** and is close to a floor. If both are leveling off, the pace of decline should slow. The empty-arena data offers the best guide to a lower bound: with no crowd, no foul bias, and no preparation edge, home teams still won **51%**. Something near that is probably where the long-run trend settles.

---

## Appendix A: Companion Documents

::: {.content-visible when-format="html"}
| Document | Description |
|---|---|
| [Full Report](home_court_report.html) | Complete findings with all charts, section-by-section analysis, and the ruled-out factors. |
| [Regression Results](home_court_results.html) | Full statistical output: regression tables, significance tests, and coefficient values. |
| [Stats Explainer](home_court_stats_explainer.html) | Guide to the statistical methods used, written for a general audience. |
| [Stats Tutorial](../../generated/stats_tutorial.html) | Worked examples reproducing key results from the regression output. |
:::

::: {.content-visible when-format="typst"}
All files are in the same folder as this PDF (`generated/`), except the Stats Tutorial which is one level up in `../generated/`.

| Document | File | Description |
|---|---|---|
| Full Report | `home_court_report.pdf` | Complete findings with all charts, section-by-section analysis, and the ruled-out factors. |
| Regression Results | `home_court_results.pdf` | Full statistical output: regression tables, significance tests, and coefficient values. |
| Stats Explainer | `home_court_stats_explainer.pdf` | Guide to the statistical methods used, written for a general audience. |
| Stats Tutorial | `../generated/stats_tutorial.pdf` | Worked examples reproducing key results from the regression output. |
:::
