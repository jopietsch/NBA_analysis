# NBA Home Court Advantage: The Short Version

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

In the 1980s and 1990s, a weaker team playing at home in the NBA playoffs won 65–66% of those games, nearly the same rate as the stronger team hosting. Today that number is 49%. Home court used to compensate for being outmatched. It no longer does. This is the short version of a report that asks why, built around three charts and three questions: **Has home court really changed? What factors create the advantage? And what's driving the decline?**

Yes: the home team’s win rate has fallen. Most of that fall is slow, steady erosion, with two sharper drops layered on top. The structural advantages home teams once relied on have worn away. **Four things drove the decline: fairer officiating, the shift to three-point shooting, the erosion of the home rebounding edge, and the closing turnover gap.**

---

## 1. Yes, It Really Changed

![Home win % per season, 1983–84 through 2025–26: regular season (top) and playoffs (bottom), with long-run trend fits and rule-change-era shading.](../generated/images/home_court_advantage_season.svg){#fig-advantage-season width=100%}

40 years ago, home teams used to win about **65%** of regular-season games and nearly **68%** in the playoffs. Today it's about **55%** and **58%**, a drop of roughly 10 percentage points in both. The scoring edge shrank to match: by the mid-1990s home teams outscored visitors by about **3 points per 100 possessions** in the regular season; now it's about **2**. Most of the erosion is a slow, steady drift of about a quarter of a percentage point per year, with two notable drops on top: one in the mid-1990s and one starting around 2018.

The decline of home court advantage in the playoffs, lagged behind the decline in the regular season. Playoff home win rates held near **64%** through the 2000s and 2010s while the regular season was already sliding, then fell to **58%** over the past few seasons. The per-game edge is still real: Games 1 and 2 go to the home team **69%** and **72%** of the time; Game 5, back at the top seed's building after two road games, reaches **74.5%**; even Game 7 still goes to the home team **64%** of the time. But a best-of-7 series flattens this considerably. A team with home court in the 1980s had about a **55%** chance of winning the series; today that has fallen to just under **52%**, barely better than a coin flip.

---

## 2. What Creates Home Court Advantage, and What Changed

![Box-score category shares. Left: what creates the home advantage (level). Right: what share of the 40-year decline each category carries. Regular season and playoffs.](../generated/images/home_court_mediation.svg){#fig-mediation width=100%}

Four categories account for about **95%** of the entire home advantage: **shooting, rebounding, foul calls, and turnover margin**. Shooting is the single biggest piece at more than **40%**, followed by rebounding at **25%**.

The decline splits across the same four. Rebounding carries the largest share at roughly **30%** of the decline in the regular season, followed by turnovers at about **27%**: together more than half the drop. Shooting accounts for about **21%** and the narrowing foul gap for about **18%**.

Two of these are the part most people expect. Referees are calling fairer games: home teams once attempted roughly **2 more free throws per game** than visitors, and now it's under half a free throw. The 1994–95 hand-checking crackdown is the one rule change that leaves a clear fingerprint in the foul gap, and it's the only one that does. The three-point shift reaches across categories too: it is the whole of the shooting decline, and about half of both the foul decline and the turnover decline, so the move to the perimeter touches close to half the entire 40-year decline. The two biggest single drivers, rebounding and turnovers, are more surprising: rebounding barely moves with three-point volume at all. They get their own section below.

The playoff picture is similar in shape, though a larger share of the playoff decline falls outside the four box-score categories; the playoff samples are too small to pin down where that remainder goes, and it is not explained by better and lower seeds becoming more evenly matched.

---

## 3. What Didn't Drive the Change

Most readers arrive with a theory, and most of those theories don't survive the data. Travel distance, time zones, pace of play, competitive balance, and every rule change except 1994–95 each have effects too small or too inconsistent to bend a 40-year trend. The much-blamed 2014 playoff format change didn't move the playoff decline. Rest matters on a given night (home teams win **63%** when better-rested, **58%** when the visitor has the edge), but that gap hasn't shifted across eras, and fewer back-to-backs for tired visitors explains only about **8%** of the decline. Even crowd size misses: arenas have held near capacity for 25 years, setting records in the very seasons home court hit bottom. A live crowd is still a real ingredient (empty 2020–21 arenas dropped home teams to **51%**, any crowd at all restored **58.5%**), but that makes crowd presence a switch that flips with the doors, not a dial slowly turning down.

---

## 4. The Biggest Surprises

![Four panels on the home rebounding and turnover edges. Far left: home vs. away offensive-rebound rates converging and crossing over time. Center-left: the raw home-minus-away rebound differentials, both declining. Center-right: seasons with a bigger home rebounding edge tend to be seasons home teams win more (association, not causation). Far right: the home turnover edge fading from about 0.4 to near zero.](../generated/images/home_court_rebounding.svg){#fig-rebounding width=100%}

**Rebounding and turnovers together account for more than half** the 40-year decline. The home rebounding edge has shrunk steadily for four decades, and it isn't the three-point story in disguise. In games with similar three-point rates, the shooting edge disappears; the rebounding edge barely moves. The cleaner measure is the **offensive** share of available rebounds: the home team's rate fell from about **34% to 26%** while the away team's fell only from **31% to 26%**. The lines converge and cross by 2025–26. Home teams no longer crash the offensive boards more aggressively than visitors.

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
