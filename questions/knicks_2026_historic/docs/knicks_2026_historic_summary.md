# Did the 2026 Knicks Have a Historic Playoff Run? The Short Version

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

The 2025–26 New York Knicks went 16-3 in the playoffs. This summary answers four questions: **Was the run historic and against real competition? Does it hold up after adjusting for era and schedule? What made the Finals so different from the first three rounds? And how unlikely was a title run from where the Knicks started the playoffs?**

---

## 1. Yes, it was historic

![Opponent-adjusted playoff dominance: 2025-26 Knicks rank first all-time among 43 champions since 1983-84.](../generated/images/knicks_2026_adjusted_margin_ranking.svg){width=100%}

The Knicks' raw average margin of +14.9 points per game is the highest in 43 years of data. Adjusted for opponent strength, their +11.2 margin ranks first all-time, ahead of the 2016–17 Warriors (+10.2) and the 1986–87 Lakers (+9.5). The one adjustment that dents this is a deliberately harsh one that scales by total scoring (2025–26 has the most points per game in the dataset): it drops the raw margin from first to third. But high scoring is mostly sharper shooting, not a faster game. The more accurate possessions-based version, which isolates actual pace from the three-point scoring boom, keeps the opponent-adjusted margin at +11.0 and clearly first. The win rate of 0.842 ranks 88th percentile. That #1 is the best single guess but not a lock: re-drawing the 19 games leaves them first about 60% of the time when the rest of history is left at its exact numbers. Under the fairest test, which treats every past champion's number as just as uncertain as the Knicks', their chance of being the single best ever falls to about 9% (and roughly a third to be top-five). Swapping out the rating system points the same way: judged purely on who beat whom, with scores ignored entirely, they still rank first, and only when opponents are credited for late-season form do they slip to third. The verdict that survives every test: one of the best handful of title runs ever, most likely the best by the raw numbers, but not provably the single best.

The East was **not historically weak**. The West-East strength gap in 2025–26 was only +0.39 points per game, 37th percentile of West dominance; in 63% of prior seasons, the West held a larger edge. The Knicks' playoff opponents had an average SRS of +3.67, right at the historical median for champions. All four opponents were essentially fully healthy (98% average availability).

---

## 2. Two stories in one run

![Per-round raw margins vs. opponent-adjusted margins using each opponent's playoff form against other teams. The Finals adjustment is large because the Spurs elevated from SRS +8.28 to +14.48 through the West bracket.](../generated/images/knicks_2026_round_split.svg){width=100%}

The run has two distinct halves. Against the East (Hawks, 76ers, Cavaliers) the Knicks went 12-2 with an average margin of +19.4 points. Against the Spurs in the Finals, they won 4-1 with an average margin of +2.4, with four of five games decided by 4 points or fewer.

This split is not just a story about opponent quality. The two teams that improved most from the regular season met in the Finals: the Knicks rose further than any team in the 2026 field, and the Spurs were second, climbing from a regular-season SRS of +8.28 to +15.13 across the playoffs (+14.48 against teams other than the Knicks). The 76ers and Cavaliers played slightly below their regular-season ratings against other opponents. The Knicks dominated East opponents who may have been a touch below their season-long level (the data is too thin to be sure), then beat the best-performing team in the field in a genuine series. The betting market saw the same split before any of it was played: modest Knicks favorites (-3 to -4) in the three East rounds, then slight Knicks underdogs (+2.5) in the Finals. They cleared the East spreads by 21 to 26 points a round, went 14-0 against the spread against the East, and landed dead-on in the Finals (+2.4 actual). The two halves are different in kind, not just in margin.

---

## 3. They weren't even supposed to win

![How rare a 16-3 run was: from the Knicks' regular season the model gave them a 15% title shot, and a run this clean about 1%.](../generated/images/knicks_2026_title_run_rarity.svg){width=100%}

Forget what happened and ask what the Knicks' regular season predicted. A forecaster that knows only each team's regular-season strength and who had home court made New York a Finals underdog: the Spurs out-rated them over 82 games, so the model gave the Knicks about a 31% chance to win that series and only about a **15% chance to win the title at all**. A run as clean as 16-3 was rarer still. Only about 7% of the model's title runs lost three or fewer games, and barely **1%** of all simulated seasons produced both a championship and three or fewer losses.

Almost nothing about the regular season predicted this. The Knicks were "supposed" to lose six or seven games on the way to a title they were not favored to win. They lost three, and were seriously tested only in the Finals. That is the dominance story told in wins and losses: they played far above their regular-season level when it counted.

---

## The bottom line

The 2026 Knicks' playoff run is historically elite by every adjusted measure. The dominant first three rounds were real: the schedule was average rather than soft, opponents were healthy, and the East was competitive. The tight Finals were real too: the Spurs were the best-performing team in the playoffs, and the Knicks won a series that could have gone either way.

---

## Appendix: Companion Documents

::: {.content-visible when-format="html"}
| Document | Description |
|---|---|
| [Full Report](knicks_2026_historic_report.html) | Complete findings with all charts and section-by-section analysis. |
| [Stats Explainer](knicks_2026_historic_stats_explainer.html) | Guide to the statistical methods, written for a general audience. |
:::

::: {.content-visible when-format="typst"}
All files are in the same folder as this PDF (`generated/`).

| Document | File | Description |
|---|---|---|
| Full Report | `knicks_2026_historic_report.pdf` | Complete findings with all charts and section-by-section analysis. |
| Stats Explainer | `knicks_2026_historic_stats_explainer.pdf` | Guide to the statistical methods, written for a general audience. |
:::
