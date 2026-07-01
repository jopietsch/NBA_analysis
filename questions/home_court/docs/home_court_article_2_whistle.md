# The Whistle

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

For forty years the home team in the NBA got the friendlier whistle, and almost nobody worked a playoff game any other way.
Of the 47 officials with at least 50 playoff games on record, 45 called fewer fouls on the home team.
Then the whistle mostly evened out.
The home foul advantage in the regular season fell from about 1.2 fouls a game in the 1980s to roughly a quarter of a foul today, an 80% reduction; in the playoffs it dropped from about 1.6 to 0.7.

This is one thread of a larger story: home-court advantage in the NBA has been shrinking for four decades.
The home team's win rate has fallen from about 65% to 55% in the regular season, and from nearly 68% to 58% in the playoffs.
The referee's whistle is one of the four box-score channels that carry home court, and it has narrowed along with the rest.
Here is how it worked, why it faded, and why a lean this small was ever able to matter.

## The whistle used to lean home, everywhere

In every decade, and in both the regular season and the playoffs, referees have called fewer fouls on home teams.
In the 1980s and early 1990s, home teams averaged about 1.2 fewer foul calls per game in the regular season, worth roughly 2 extra free throw attempts a night.
In the playoffs the lean was wider: about 1.6 fewer fouls and 2.4 more free throws.
With fouls go free throws, and with free throws go points.
Of the four ways home teams have historically come out ahead, better shooting, more rebounds, fewer turnovers, and the whistle, this is the most consistent.

The playoff record shows how universal it was: nearly every referee who has worked the playoffs called the game a little differently depending on which team was at home.

## Then it mostly evened out

The home foul differential in the regular season dropped from 1.2 fouls per game in the 1980s to roughly a quarter of a foul today, an 80% reduction.
In free-throw terms, home teams once attempted about 2 more free throws per game than visitors; now it is just under half a free throw.
The playoffs moved the same way but less: the foul gap fell from 1.6 to about 0.7, the free-throw advantage from 2.4 to 1.1 attempts, the postseason lagging behind as it does on every part of this story.

Two different changes split the work.
Three-point attempts draw fewer fouls than drives to the basket, so as both teams moved to the perimeter there were simply fewer foul calls to go around, and the home team's absolute gap shrank with them.
About half of the foul decline traces to that shift in shot selection; [The Three-Point Suspect](home_court_article_3_threes.html) makes the full case that the move to the arc reaches close to half of the whole decline.
The other half of the foul story is genuine change in how referees call the game.

And that change reads as a generational one.
Newer referees are not only less biased on average; they are also more uniform in their calling.
The spread across officials has compressed, so a game today is called much the same whoever has the whistle.

![Distribution of per-official home foul bias by era, playoffs. The spread has compressed: newer officials are not only less biased on average but more uniform in their calling. Chart covers 1995 onward, the earliest era with sufficient per-official playoff data.](../generated/images/home_court_referee_era.svg){#fig-referee-era}

Per-official records only begin in 1995, so the 1980s and early-1990s baselines above come from the overall foul gap, not from individual referees.

## How a two-attempt advantage ever mattered

Here is the honest problem with everything above.
In the 1980s the home team attempted about 2 more free throws a game than the visitor, worth a bit over a point of scoring.
That is a tiny number to decide anything.

On any single night, it can't.
Free-throw attempts swing wildly from game to game (foul trouble, a hack-a-shaq stretch, a night both teams live at the line), so the average lean toward the home team is nowhere near the biggest thing moving the count in any one game.
In the 1980s, the middle 80% of regular-season games saw the home team attempt anywhere from -12 to +16 more free throws than the visitor, a range many times the width of the +1.97-attempt average sitting inside it.
A game where the home team shot 10 fewer free throws than the visitor is well inside that ordinary range and says nothing about who the referees favored that night.

| | 1984–94 average | 1984–94 typical range* | 2023–26 average | 2023–26 typical range* |
|---|---|---|---|---|
| Regular season | +1.97 | -12 to +16 | +0.46 | -11 to +12 |
| Playoffs | +2.35 | -11 to +16 | +1.09 | -10 to +11 |

*Typical range: excludes the most extreme 10% of games on each end, so it covers the middle 80% of nights.*

The average shrank far faster than the swing around it.
In the regular season, the average free-throw advantage fell 77% while the typical night-to-night range narrowed by only 18%.
The share of games where the home team attempted more free throws than the visitor fell from 56% to 49%, close to a coin flip.
The playoffs show the same shape but move less: the average fell 54%, and the home-favored share only slipped from 57% to 56%, another sign the playoffs lag the regular season.

The foul count behind those free throws tells the identical story.

| | 1984–94 average | 1984–94 typical range* | 2023–26 average | 2023–26 typical range* |
|---|---|---|---|---|
| Regular season | -1.23 | -8 to +6 | -0.25 | -6 to +6 |
| Playoffs | -1.58 | -8 to +5 | -0.68 | -6 to +5 |

The regular-season foul gap fell 80% while its night-to-night range narrowed only 14%; the playoff foul gap fell 57%, again a smaller drop than the regular season.

![Left: the 1983-84 regular season's per-game FTA gap, a wide noisy spread with the season average (red line) sitting well inside it, nowhere near the edge. Right: box plots of the same gap, regular season and playoffs, earliest era vs. latest (diamond = average, box = middle 50%, whiskers = middle 80%). The diamonds slide toward zero era to era while the boxes stay nearly the same size.](../generated/images/home_court_fta_distribution.svg){#fig-fta-distribution .collapsible}

So the whistle's lean was never something you could point to in a single box score.
It only appears once thousands of games are stacked together, and it has faded further than the night-to-night swing ever has.

## The referees themselves

Do some referees lean more than others?
Yes, but by less than a raw leaderboard suggests.
Of 47 officials with at least 50 playoff games, 45 call fewer fouls on the home team.
The most home-leaning on record, Ron Garretson (last worked a playoff game in 2017-18), Joe Crawford (2014-15), and Eddie Rush (2011-12), sit roughly a full foul per game apart from the most even-handed, a group that includes Tony Brothers, Josh Tiven, and Joe Forte.
About 60% of that raw spread, though, is the random bounce of how few games some officials worked.
Referees genuinely differ, and the gap between them is narrower than the leaderboard suggests.
This measures tendencies, not proof that any one official decides games.

![Top/bottom 15 referees ranked by home foul differential (≥50 playoff games). Values are adjusted for how few games each official worked: raw differences are pulled toward the league average so that small samples don't dominate the leaderboard.](../generated/images/home_court_referee_rankings.svg){#fig-referee-rankings .collapsible}

The whistle is the cleanest-cut piece of the home-court story: a real, repeatable lean that nearly every referee shared, that faded for two reasons we can name, and that was always too small to see on any single night.
How much of the decline the move to three-point shooting really carries, foul calls included, is the next piece.

---

Next: [The Three-Point Suspect](home_court_article_3_threes.html)

Back to the series hub: [The Disappearing Home Court](home_court_series.html)
