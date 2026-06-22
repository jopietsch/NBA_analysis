# NBA Home Court Advantage: The Short Version

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

In the 1980s, a weaker team playing at home in the NBA playoffs won 65% of those games, nearly the same rate as the stronger team hosting. Today that number is 47%. Home court used to compensate for being outmatched. It no longer does. This is the short version of a report that asks why, built around three charts and three questions: **Has home court really changed? What makes it an advantage in the first place? And what's driving the decline?**

Yes: the home team’s win rate has fallen. Most of that fall is slow, steady erosion, with two sharper drops layered on top. The structural advantages home teams once relied on have worn away. **Four things drove the decline: fairer officiating, the shift to three-point shooting, the erosion of the home rebounding edge, and the closing turnover gap.**

---

## 1. Yes, it really changed

![Home win % per season, 1983–84 through 2025–26: regular season (top) and playoffs (bottom), with long-run trend fits and rule-change-era shading.](../generated/images/home_court_advantage_season.svg){#fig-advantage-season width=100%}

Home teams used to win about **65%** of regular-season games and nearly **68%** in the playoffs. Today it's about **55%** and **58%**, a drop of roughly 10 percentage points in both. The scoring edge shrank to match: by the mid-1990s home teams outscored visitors by about **3 points per 100 possessions** in the regular season; now it's about **2**. Most of the erosion is a slow, steady drift of about a quarter of a percentage point per year, with two notable drops on top: one in the mid-1990s and one starting around 2018.

The decline of home court advantage in the playoffs, lagged behind the decline in the regular season. Playoff home win rates held near **64%** through the 2000s and 2010s while the regular season was already sliding, then fell to **58%** over the past few seasons. The per-game edge is still real: Games 1 and 2 go to the home team **69%** and **72%** of the time; Game 5, back at the top seed's building after two road games, reaches **74.5%**; even Game 7 still goes to the home team **64%** of the time. But a best-of-7 series flattens this considerably. A team with home court in the 1980s had about a **55%** chance of winning the series; today that has fallen to just under **52%**, barely better than a coin flip.

---

## 2. What home court is made of, and where it changed

![Box-score category shares. Left: what creates the home advantage (level). Right: what share of the 40-year decline each category carries. Regular season and playoffs.](../generated/images/home_court_mediation.svg){#fig-mediation width=100%}

Four categories account for about **95%** of the entire home advantage: **shooting, rebounding, foul calls, and turnover margin**. Shooting is the single biggest piece at more than **40%**, followed by rebounding at **25%**.

The right panel shows where the decline has registered. Rebounding carries the largest share at roughly **30%**, followed by turnovers at about **27%**. Together they account for more than half the drop. Shooting accounts for about **21%** and the narrowing foul gap for about **18%**. The three-point shift reaches across these: it is the whole of the shooting decline, and about half of both the foul decline and the turnover decline. Add those up and the move to the perimeter touches close to half the entire 40-year decline. Rebounding is the part it does not explain: it is the largest single driver, and it barely moves with three-point volume.

The playoff picture is similar in shape, though a larger share of the playoff decline runs through factors not captured by the four box-score categories, consistent with better and lower seeds becoming more evenly matched over time.

---

## 3. What explains the decline, and what doesn't

A live crowd is a real ingredient. In the empty arenas of 2020–21, home teams won just **51%**. With any crowd at all: **58.5%**. But arenas have held near capacity for 25 years while home court fell; crowd presence is a switch that flips with the doors, not a dial that has been slowly turning. Travel distance, time zones, pace of play, and competitive balance each have effects too small and inconsistent to account for a 40-year trend.

Referees are calling fairer games. Home teams once attempted roughly **2 more free throws per game** than visitors; now it's under half a free throw. The 1994–95 hand-checking crackdown is the one rule change that leaves a clear fingerprint in the foul gap. The three-point revolution matters too: as three-point attempts rose, the foul and turnover gaps each shrank by about half. But the two biggest drivers of the decline turned out to be the ones no one was watching.

---

## 4. The biggest surprises

![Four panels on the home rebounding and turnover edges. Far left: home vs. away offensive-rebound rates converging and crossing over time. Center-left: the raw home-minus-away rebound differentials, both declining. Center-right: seasons with a bigger home rebounding edge tend to be seasons home teams win more (association, not causation). Far right: the home turnover edge fading from about 0.4 to near zero.](../generated/images/home_court_rebounding.svg){#fig-rebounding width=100%}

Rebounding and turnovers together account for more than half the 40-year decline, and the obvious culprit doesn't explain most of it. The home rebounding edge has shrunk steadily for four decades, and it isn't the three-point story in disguise. In games with similar three-point rates, the shooting edge disappears; the rebounding edge barely moves. The cleaner measure is the **offensive** share of available rebounds: the home team's rate fell from about **34% to 26%** while the away team's fell only from **31% to 26%**. The lines converge and cross by 2025–26. Home teams no longer crash the offensive boards more aggressively than visitors.

The **turnover** edge faded over the same span. Home teams once committed about **0.4 fewer turnovers per game** than visitors; that gap is now essentially zero. About half of that fade is the perimeter shift (fewer drives, fewer live-ball turnovers); the other half has no clear explanation. So rebounding stands almost entirely apart from the three-point story, and turnovers stand half apart. The playoffs show the same fade on both counts.

Both are approaching their practical limits. Three-point attempts now make up about **40%** of all shots; the offensive-rebound rate has fallen to about **26%** and is close to a floor. If both are leveling off, the pace of decline should slow. The empty-arena result offers a guide to where the long-run trend settles: near **51%**.

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
