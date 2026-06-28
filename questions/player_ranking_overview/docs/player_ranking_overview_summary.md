# NBA Player Rating Systems: Summary

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

NBA players can be rated several different ways, each measuring something different. Box-score systems like PER and Win Shares work from the standard statistics and can be computed back to the 1980s. Lineup-based impact metrics like RAPTOR, EPM, and DARKO try to capture what box stats miss, particularly defensive contribution. Human rankings from MVP voting and All-NBA selections measure reputation and narrative.

This project recomputes the box-score systems for the 2024-25 season and compares them; the impact metrics and human rankings are surveyed but not yet folded into the comparison. The core findings:

**The systems mostly agree on the stars.** At the very top, the box-score systems converge. The same handful of players (Nikola Jokić, Shai Gilgeous-Alexander, Giannis Antetokounmpo) rise to the top of nearly every system and of both combined ratings.

**They disagree in the middle.** Win Shares favors efficient big men on good teams (Domantas Sabonis, Ivica Zubac), while PER rewards high-usage scorers (Zion Williamson, Kristaps Porziņģis), so the same player can sit many spots apart in the two. The plus/minus systems, sensitive to steals, can rate a high-steal defender well above where the rate metrics place him (an effect this report's recompute amplifies, see the findings). The systems genuinely see different things outside the very top tier.

**Cumulative metrics concentrate value at the top.** Rate stats like PER are spread fairly evenly among qualified players. Cumulative metrics (Win Shares, and especially VORP) pile much more of their value onto a small number of elite players. The player ranked first is not marginally better than the player ranked tenth; on a cumulative basis, the gap is often several times larger than the distance from tenth to fiftieth. Ordinal rankings hide this.

**A consensus rating and a wins-predictive rating diverge on team context.** When systems are combined into a single number, the two most natural approaches (a straight average of the systems vs. a version weighted to predict team wins) agree strongly at the top but diverge on team context: the wins-predictive rating lifts players on winning teams and discounts players on losing teams, regardless of individual numbers.

Full analysis and exact figures are in `player_ranking_overview_results.md`. Methods are in `player_ranking_overview_stats_explainer.md`.
