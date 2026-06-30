# NBA Player Rating Systems: Summary

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

NBA players can be rated several different ways, each measuring something different. Box-score systems like PER and Win Shares work from the standard statistics and can be computed back to the 1980s. Lineup-based impact metrics like RAPTOR, EPM, and DARKO try to capture what box stats miss, particularly defensive contribution. Human rankings from MVP voting and All-NBA selections measure reputation and narrative.

This project recomputes the box-score systems for the 2024-25 season, adds a from-scratch RAPM built from a full season of play-by-play, and compares them; the other impact metrics and human rankings are surveyed but not folded into the comparison. The core findings:

**The systems mostly agree on the stars.** At the very top, the box-score systems converge. The same handful of players (Nikola Jokić, Shai Gilgeous-Alexander, Giannis Antetokounmpo) rise to the top of nearly every system and of both combined ratings.

**They disagree in the middle.** Win Shares favors efficient big men on good teams (Domantas Sabonis, Ivica Zubac), while PER rewards high-usage scorers (Zion Williamson, Kristaps Porziņģis), so the same player can sit many spots apart in the two. The plus/minus systems, sensitive to steals, can rate a high-steal defender well above where the rate metrics place him (an effect this report's recompute amplifies, see the findings). The systems genuinely see different things outside the very top tier.

**The impact metric sees something the box scores don't.** RAPM, built only from which lineups outscored their opponents, barely moves together with the box-score systems (about 0.22 on a 0-to-1 scale, where those systems sit far higher with each other). That gap is the point: RAPM is meant to catch the off-ball and defensive value the box score misses. But one season of it is noisy, so the raw 2024-25 list puts a reserve, Isaiah Joe, on top, which is why every published version leans on a box-score starting point. Building that fixed version here (RAPM_MY: three pooled seasons anchored to a box-score prior) pulls the stars back to the top, led by Shai Gilgeous-Alexander and Giannis Antetokounmpo, and it is the version folded into the consensus.

**Cumulative metrics concentrate value at the top.** Rate stats like PER are spread fairly evenly among qualified players. Cumulative metrics (Win Shares, and especially VORP) pile much more of their value onto a small number of elite players. The player ranked first is not marginally better than the player ranked tenth; on a cumulative basis, the gap is often several times larger than the distance from tenth to fiftieth. Ordinal rankings hide this.

**A consensus rating and a wins-predictive rating diverge on team context.** When systems are combined into a single number, the two most natural approaches (a straight average of the systems vs. a version weighted to predict team wins) agree strongly at the top but diverge on team context: the wins-predictive rating lifts players on winning teams and discounts players on losing teams, regardless of individual numbers.

**Describing a season and forecasting the next are different jobs.** Grading each system by how well its player ratings rebuild which teams outscored their opponents, PER describes the 2024-25 season best, rebuilding about 72% of the spread between teams. But the order flips when last season's ratings are used to forecast this one: PER falls to roughly 15%, one of the weakest, while the plus/minus family holds up best, led by BPM at about 50%. PER is a faithful scoreboard of a finished season but a poor crystal ball. Pooling the same two tests across 30 seasons back to 1996-97 holds the gap steady: PER averages about 64% describing a season but only 25% forecasting the next, so the flip is the standing pattern, not one year's bounce.

Full analysis and exact figures are in `player_rating_overview_results.md`. Methods are in `player_rating_overview_stats_explainer.md`.
