# NBA Player Rating Systems: Summary

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

Among the ratings that never use who won, the one that best describes a finished NBA season is one of the worst at predicting the next: across the 30 seasons tested, PER rebuilds about 64% of the gaps between teams in a season just played but forecasts the next at only about 25%.
That is one sign of a larger truth: there is no single best way to rate NBA players, and the systems disagree in ways that matter for players on losing teams, defensive specialists, and high-usage scorers.

This report recomputes the box-score systems for 2025-26, adds a from-scratch RAPM built from a full season of play-by-play, and puts three questions to them:

1. **Do the systems agree?**
2. **What does each system uniquely capture?**
3. **How should they be combined into one rating?**

**Do they agree?
At the top, closely; below it, less than their reputations suggest.** The same handful of players (Nikola Jokić, Shai Gilgeous-Alexander, Giannis Antetokounmpo) rise to the top of nearly every system and of both combined ratings.
Below the top tier they part: Win Shares favors efficient big men on good teams (Amen Thompson) while PER rewards high-usage scorers (Giannis Antetokounmpo), so the same player can sit many spots apart.
The from-scratch RAPM, built only from which lineups outscored their opponents, barely moves with the box scores (about 0.18 on a 0-to-1 scale), which is the point of an impact metric, though one season of it is too noisy to trust raw: its raw 2025-26 list puts a reserve, Moussa Cisse, on top.

**What does each uniquely capture?
It depends.** Each system tilts toward a player type, but the all-in-one summaries (PER, Game Score, and the now-validated BPM and VORP) are nearly reconstructable from the others, while Defensive BPM carries the most of its own, picking up defense the scoring-heavy systems miss.
BPM is recomputed and validated against Basketball-Reference here (rank-and-value agreement 0.93), which makes it accurate but no less redundant; the RAPM family is still an approximate recompute under repair, so part of its apparent independence may be noise.

**How should they be combined?
Into two ratings that answer different questions.** A plain consensus averages every system; a wins-predictive blend weights each by how well it tracked team wins.
They agree almost exactly (0.96 on a 0-to-1 scale) on the best players and part mainly on players whose production did not turn into team wins.
Beyond those two, a playoff-weighted version of BPM (blending each player's regular-season and playoff value) follows one more thread the report picked up: Jalen Brunson did raise his game in the postseason (BPM +3.4 to +4.6), which lifts him to 7th of the 103 playoff players, a real step up but short of the top five.

One pattern runs under all three answers: value is top-heavy.
Cumulative metrics like Win Shares and VORP pile most of their value onto a few elite players, so the gap from the best player to the tenth is often several times the gap from tenth to fiftieth, something a ranked list hides.

The cross-system comparison rests on the 2025-26 season alone, so its exact orderings are a snapshot: year to year the top holds (Nikola Jokić and Shai Gilgeous-Alexander lead both 2024-25 and 2025-26) while the order below it churns.
The describe-versus-forecast and stability findings span 30 seasons and are the firmer results.

Full analysis and exact figures are in `player_rating_overview_results.md`.
Methods are in `player_rating_overview_stats_explainer.md`.
