# NBA Player Rating Systems: Summary

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

There are more ways to rate an NBA player than most fans realize. Box-score systems like PER and Win Shares work from the standard statistics and can be computed back to the 1980s. Lineup-based impact metrics like RAPTOR, EPM, and DARKO try to capture what box stats miss, particularly defensive contribution. Human rankings from MVP voting and All-NBA selections measure reputation and narrative.

This project tests all of these on the 2024-25 season. The core findings:

**The systems mostly agree on the stars.** At the very top of the distribution, the box-score systems and human rankings converge. The same players who lead in PER and Win Shares tend to lead in BPM and VORP, and to receive MVP votes.

**They disagree in the middle.** Defensive specialists who show up poorly in the box score but anchor lineups can rank 60th in PER and 20th in an impact metric. High-usage players on bad teams can rank 15th in Win Shares and 50th in an impact model that accounts for team quality. The systems genuinely see different things in the 20th-through-80th percentile range.

**Cumulative metrics have a heavy tail.** Rate stats like PER are nearly symmetric among qualified players. Cumulative metrics (Win Shares, VORP) concentrate almost all their value at the top: a small number of elite players hold a disproportionate share of total positive value. The player ranked first is not marginally better than the player ranked tenth; on a cumulative basis, the gap is often several times larger than the distance from tenth to fiftieth. Ordinal rankings hide this.

**A consensus rating and a wins-predictive rating diverge on team context.** When systems are combined into a single number, the two most natural approaches (average of normalized scores vs. weighted to predict team wins) agree strongly at the top but diverge based on team wins: the wins-predictive rating lifts players on winning teams and discounts players on losing teams, regardless of individual numbers.

Full analysis, crosswalk coverage, and exact figures are in `player_ranking_overview_results.md`. Methods are in `player_ranking_overview_stats_explainer.md`.
