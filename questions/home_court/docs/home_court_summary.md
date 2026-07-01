# NBA Home Court Advantage: The Short Version

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

In the 1980s and 1990s, a weaker team playing at home in the NBA playoffs won 65–66% of those games, about as often as the stronger team won at its home.
Today that number is 49%.
Home court used to compensate for being outmatched.
It no longer does.
**Has home court really changed?
What factors create the advantage?
What drove the decline?
And what did not?**

Yes: the home team’s win rate has fallen.
The decline is mostly slow and steady, with two stretches where it briefly sped up.
Home teams have historically **shot better, pulled down more rebounds, committed fewer turnovers, and gotten the benefit of the doubt from the referees**, and those four differences account for about 95% of the advantage.
Two real-world changes stand out: **the shift to three-point shooting** (which alone reaches close to half) **and fairer officiating**.
And the biggest single driver of the decline, **rebounding**, is the one piece neither change explains: the data can measure it but not say why it faded.

These findings held up under a battery of checks built to break them, laid out in the full report.
Because there are more regular-season games, the analysis is more precise; the playoff figures show direction more than precise size.

---

## 1. Yes, It Really Changed

![Home win % per season, 1983–84 through 2025–26: regular season (top) and playoffs (bottom), with long-run trend fits and rule-change-era shading.](../generated/images/home_court_advantage_season.svg){#fig-advantage-season width=100%}

Forty years ago, home teams won about 65% of regular-season games and nearly 68% in the playoffs.
Today it's about 55% and 58%, **a drop of roughly 10 percentage points in both**.
The scoring gap followed the same arc: home teams outscored visitors by about 3 points per 100 possessions through the mid-2010s, and about 2 today, a drop of about a third.
The slide sped up twice, in the mid-1990s and again around 2018, but both bursts are accelerations within the same long trend, not separate drops on top of it.

Home court in the playoffs declined later than in the regular season: playoff home win rates held near 64% from the mid-1990s through the 2010s while the regular season was already sliding, then fell to about 58% in the past few seasons.
The per-game advantage is still real: the home team wins the early games at the top seed's arena and even takes most Game 7s.
But a best-of-7 series flattens it.
A home-court team that would have won the series about 55% of the time in the 1980s now takes it about 52% of the time, barely better than a coin flip.

---

## 2. What Creates Home Court Advantage, and What Changed

Shooting is the largest piece of home court today, but it is not the largest driver of its decline: rebounding and turnovers are.
The table holds both facts at once, what each category contributes to the advantage now and how much of the 40-year decline it explains.

| Box-score category | Share of the advantage | Share of the decline |
|---|---:|---:|
| Shooting (eFG%) | 43% | 21% |
| Rebounding | 25% | 30% |
| Foul calls | 14% | 18% |
| Turnover margin | 13% | 27% |
| **All four together** | **95%** | **96%** |

Regular-season shares; both figures vary somewhat with the game sample.
Together, rebounding and turnovers are more than half the decline.

Two real-world changes are identifiable; together they account for a little over half the 40-year decline.
Referees are calling fairer games: home teams once attempted about 2 more free throws per game than visitors, and now the gap is about 0.5.
The 1994–95 hand-checking crackdown is the one rule change that leaves a clear fingerprint in the foul gap.
The three-point shift reaches further: it accounts for the entire shooting decline and about half of both the foul and turnover declines, so the move to the perimeter touches close to half the 40-year total on its own.
It is the biggest single real-world force, but still not the engine behind the whole decline.

The largest unexplained piece is rebounding.
It sits almost entirely outside the three-point story: in games with similar three-point rates, the shooting advantage disappears while the rebounding advantage barely moves.
The cleaner measure is each team's share of available offensive rebounds, and there the home rate fell about 8 points while the away rate fell about 5.
Home teams no longer crash the offensive boards more aggressively than visitors, and offensive rebounds have gone down for both teams.
The data shows the home rebounding advantage shrank; it cannot say why.

Turnovers faded over the same span: home teams once committed slightly fewer turnovers than visitors, and that gap is now essentially zero.
About half of that fade is the perimeter shift (fewer drives, fewer live-ball turnovers); the other half has no clear explanation.
The playoffs show the same fade on both counts, with far fewer games to pin down the size.

Both rebounding and turnovers are near their practical limits: three-point attempts already make up about 40% of all shots and the offensive-rebound rate is close to a floor, so further declines have less room to run.

The model holds up on data it never saw: built on the four categories, trained only on seasons through 2013 and then left unchanged, it predicts each later regular-season home win rate to within about a point, and still catches the steeper modern playoff drop it was never shown.

The playoff picture has the same shape, but a larger share of its decline falls outside the four categories.
With so few playoff games, where that remainder goes can't be pinned down, and it is not explained by higher and lower seeds becoming more evenly matched.

---


## 3. What Didn't Drive the Change

**Travel distance, time zones, pace of play, and every rule change** except 1994–95 each have effects too small or too inconsistent to bend a 40-year trend.
Competitive balance can't explain the long-run decline either, though parity and home court do wobble together slightly from year to year.
The 2014 playoff format change didn't move the playoff decline.
Rest matters on a given night, but that gap hasn't shifted across eras, and fewer back-to-backs for tired visitors explains only about **8%** of the decline.

Even crowd size misses.
Arenas have held near capacity for 25 years, even in the seasons home court hit bottom.
A live crowd is still a real ingredient: empty 2020–21 arenas dropped home teams to about 51%, and any crowd at all restored about 58%.
But that makes crowd presence a switch that flips with the doors, not a dial slowly turning down.

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
