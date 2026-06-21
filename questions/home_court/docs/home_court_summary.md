# NBA Home Court Advantage: The Short Version

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

For four decades, NBA home teams have been winning less. This is the short version of a long report, built around three charts to answer three questions: **Has home court really changed? What makes it an advantage in the first place? And what's driving the decline?**

---

## 1. Yes, it really changed

![Home win % per season, 1983–84 through 2025–26: regular season (top) and playoffs (bottom), with long-run trend fits and rule-change-era shading.](../generated/images/home_court_advantage_season.svg){#fig-advantage-season width=100%}

Home teams used to win about **65%** of regular-season games and nearly **68%** in the playoffs. Today it's about **55%** and **58%**, a drop of roughly 10 percentage points in both. The scoring edge shrank to match: by the mid-1990s home teams outscored visitors by about **3 points per 100 possessions** in the regular season; now it's about **2**. Most of the erosion is a slow, steady drift of about a quarter of a percentage point per year, with two notable drops on top: one in the mid-1990s and one starting around 2018.

The playoffs followed a different path. Playoff home win rates held near **64%** through the 2000s and 2010s while the regular season was already sliding, then fell to **58%** over the past few seasons. The per-game edge is still real: Games 1 and 2 go to the home team **69%** and **72%** of the time; Game 5, back at the top seed's building after two road games, reaches **74.5%**; even Game 7 still goes to the home team **64%** of the time. But a best-of-7 series flattens this considerably. A team with home court in the 1980s had about a **55%** chance of winning the series; today that has fallen to just under **52%**, barely better than a coin flip.

In the 1980s and 1990s, the lower-seeded team (the weaker opponent) won **65%** and **61%** of their home playoff games, nearly identical to what the higher seed won at home. Quality barely mattered once you were in your own building. Today the lower seed at home wins about **47%**, while the higher seed's rate is roughly what it always was. The decline is not mainly about better teams winning more at home. It is about worse teams winning less.

---

## 2. What home court is made of, and where it changed

![Box-score category shares. Left: what creates the home advantage (level). Right: what share of the 40-year decline each category carries. Regular season and playoffs.](../generated/images/home_court_mediation.svg){#fig-mediation width=100%}

Four categories account for about **95%** of the entire home advantage: **shooting, rebounding, foul calls, and turnover margin**. Shooting is the single biggest piece at more than **40%**, followed by rebounding at **25%**.

The right panel shows where the decline has registered. Rebounding carries the largest share at roughly **30%**, followed by turnovers at about **27%**. Together they account for more than half the drop. Shooting accounts for about **21%** and the narrowing foul gap for about **18%**. As three-point attempts rose, the foul and turnover gaps each shrank by about half. Rebounding tells a different story: it is the largest single driver of the decline, and it barely moves with three-point volume.

The playoff picture is similar in shape, though a larger share of the playoff decline runs through factors not captured by the four box-score categories, consistent with the quality gap between home and away seeds compressing over time.

---

## 3. The rebounding and turnover edges eroded

![Four panels on the home rebounding and turnover edges. Far left: home vs. away offensive-rebound rates converging and crossing over time. Center-left: the raw home-minus-away rebound differentials, both declining. Center-right: seasons with a bigger home rebounding edge tend to be seasons home teams win more (association, not causation). Far right: the home turnover edge fading from about 0.4 to near zero.](../generated/images/home_court_rebounding.svg){#fig-rebounding width=100%}

The home rebounding edge has shrunk for 40 years, and it isn't the three-point story in disguise. Holding three-point volume constant erases the shooting edge; the rebounding edge barely moves.

The cleaner measure is the **offensive** share of available rebounds. The home team's offensive-rebound rate fell from about **34% to 26%** while the away team's fell only from **31% to 26%**. The lines converge and cross by 2025–26: home teams no longer crash the offensive boards more aggressively than visitors. The home **turnover** edge faded over the same span. Home teams once committed about **0.4 fewer turnovers per game** than visitors; that gap is now essentially zero. The playoffs show the same fade on both counts.

---

## What explains the decline, and what doesn't

A live crowd turns out to be a real ingredient. In the empty arenas of 2020–21, home teams won just **51%**. With any crowd at all: **58.5%**. That seven-point gap reflects something genuine. But arenas have held near capacity for 25 years while home court fell; crowd presence is a switch that flips with the doors, not a dial that has been slowly turning.

Referees are calling fairer games. Home teams once attempted roughly **2 more free throws per game** than visitors; now it's under half a free throw. The 1994–95 hand-checking crackdown is the one rule change that leaves a clear fingerprint in the foul gap. Other rule-change eras show no statistical signature once the underlying year trend is accounted for. Travel distance, time zones, pace of play, and competitive balance each have effects too small and inconsistent to account for a 40-year trend.

The three-point revolution shifted shooting patterns, and the foul and turnover trends move with it. But more than half the decline runs through rebounding and turnovers, channels that move independently of the three-point shift.

Both are approaching their practical limits. Three-point attempts now make up about **40%** of all shots; the offensive-rebound rate has fallen to about **26%** and is close to a floor. If both are leveling off, the pace of decline should slow. The empty-arena result offers a guide to the lower bound: near **51%** is probably where the long-run trend settles.

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
