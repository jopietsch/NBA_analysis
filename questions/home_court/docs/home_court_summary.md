# NBA Home Court Advantage: The Short Version

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

In the 1980s and 1990s, a weaker team playing at home in the NBA playoffs won 65–66% of those games, nearly the same rate as the stronger team hosting. Today that number is 49%. Home court used to compensate for being outmatched. It no longer does.  **Has home court really changed? What factors create the advantage? What drove the decline? And what did not, even though people often assume it did?**

Yes: the home team’s win rate has fallen. The fall is mostly a slow, steady fade, with two stretches where it briefly sped up. **We measure the edge through four box-score factors: shooting, rebounding, foul calls, and turnover margin. Shooting builds the biggest part of the edge; rebounding did the most to erase it.** Two real-world changes account for much of the decline: the shift to three-point shooting, which alone reaches close to half of it, and fairer officiating. Rebounding, the largest single driver, is the one neither change explains.

Because there are more regular-season games, that analysis is more precise. There are far fewer playoff games, so it shows direction more than precise size.

---

## 1. Yes, It Really Changed

![Home win % per season, 1983–84 through 2025–26: regular season (top) and playoffs (bottom), with long-run trend fits and rule-change-era shading.](../generated/images/home_court_advantage_season.svg){#fig-advantage-season width=100%}

Forty years ago, home teams won about 65% of regular-season games and nearly 68% in the playoffs. Today it's about 55% and 58%, **a drop of roughly 10 percentage points in both**. The scoring edge shrank to match: home teams outscored visitors by about 3 points per 100 possessions in the regular season through the mid-2010s, and about 2 today. The drop is mostly one continuous fade that accounts for nearly the whole decline, with two stretches where it briefly sped up: one in the mid-1990s and one starting around 2018. Both are accelerations within the trend, not extra drops on top of it.

Home court in the playoffs declined later than in the regular season: playoff home win rates held near 64% through the 2000s and 2010s while the regular season was already sliding, then fell to about 58% in the past few seasons. The per-game edge is still real, the home team takes the early games at the top seed's arena comfortably and even wins most Game 7s, but a best-of-7 series flattens it. A home-court team that would have won the series about 55% of the time in the 1980s is now barely better than a coin flip.

---

## 2. What Creates Home Court Advantage, and What Changed

We measure home court through the Four Factors that decide possessions, developed by Dean Oliver: shooting, rebounding, foul calls, and turnover margin. The table shows how much of the home edge each one accounts for, and how much of the 40-year decline each one carries.

| Box-score factor | Share of the edge | Share of the decline |
|---|---:|---:|
| Shooting (eFG%) | 43% | 21% |
| Rebounding | 25% | 30% |
| Foul calls | 14% | 18% |
| Turnover margin | 13% | 27% |
| **All four together** | **95%** | **96%** |

Regular-season shares; both columns shift somewhat on the games available, and the playoffs run a similar shape. Two things stand out. Shooting builds the biggest single part of the edge, but rebounding and turnovers together do the most to erase it, more than half the decline. And these four are where the advantage shows up, not why it exists: the real-world causes behind them, a home crowd, familiar rims, referee tendencies, are the next question.

Then we get to the most interesting: why are these changes happening.  Referees are calling fairer games: home teams once attempted roughly 2 more free throws per game than visitors, and now it's under half a free throw. The 1994–95 hand-checking crackdown is the one rule change that leaves a clear fingerprint in the foul gap, and it's the only one that does. The three-point shift reaches across categories too: it is the whole of the shooting decline, and about half of both the foul decline and the turnover decline, so the move to the perimeter touches close to half the entire 40-year decline. Rebounding and turnovers, the two biggest single drivers, are the ones the three-point shift does not explain: rebounding barely moves with three-point volume at all. 

This account is not just fit to the past. A model built on the four categories and trained only on seasons through 2013, then left unchanged, predicts each later season's home win rate to within about a point, catching the post-2017 slide it was never shown and the steeper modern playoff drop too.

The playoff picture is similar in shape, though a larger share of the playoff decline falls outside the four box-score categories; there are too few playoff games to pin down where that remainder goes, and it is not explained by better and lower seeds becoming more evenly matched.

---

### 2.1 The Biggest Surprises

---

**Rebounding and turnovers together account for more than half** the 40-year decline. The home rebounding edge has shrunk steadily for four decades, and it isn't the three-point story in disguise: in games with similar three-point rates, the shooting edge disappears while the rebounding edge barely moves. The cleaner measure is each team's share of available offensive rebounds, and there the home rate fell much further than the away rate. Home teams no longer crash the offensive boards more aggressively than visitors, and offensive rebounds have gone down for both teams.

The turnover edge faded over the same span: home teams once committed slightly fewer turnovers than visitors, and that gap is now essentially zero. About half of the fade is the perimeter shift (fewer drives, fewer live-ball turnovers); the other half has no clear explanation. So rebounding stands almost entirely apart from the three-point story, and turnovers stand half apart. The playoffs show the same fade on both counts, though with far fewer games it reads as direction rather than precise size.

How far can these trends continue? Both are near their practical limits. Three-point attempts already make up about 40% of all shots, and the offensive-rebound rate is close to a floor. If both are leveling off, the pace of decline should slow. The empty-arena result offers a guide to where the long-run trend settles: near 51%.

---


## 3. What Didn't Drive the Change

**Travel distance, time zones, pace of play, and every rule change** except 1994–95 each have effects too small or too inconsistent to bend a 40-year trend. Competitive balance can't explain the long-run decline either, though parity and home court do wobble together slightly from year to year. The much-blamed 2014 playoff format change didn't move the playoff decline. Rest matters on a given night, but that gap hasn't shifted across eras, and fewer back-to-backs for tired visitors explains only about **8%** of the decline. Even crowd size misses: arenas have held near capacity for 25 years, setting records in the very seasons home court hit bottom. A live crowd is still a real ingredient (empty 2020–21 arenas dropped home teams to about 51%, any crowd at all restored about 58%), but that makes crowd presence a switch that flips with the doors, not a dial slowly turning down.

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
