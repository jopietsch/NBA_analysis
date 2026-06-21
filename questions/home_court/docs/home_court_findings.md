# NBA Home Court Advantage: Findings

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

Home court advantage in the NBA has been shrinking for four decades. **Has it really changed?** **What makes it an advantage in the first place?** **And what's driving the decline, and what isn't?**

Yes: the home team's win rate has fallen from about 65% to 55% in the regular season, and from nearly 68% to 58% in the playoffs. **Most of that fall is slow, steady erosion, with two sharper drops layered on top.** The structural advantages home teams once relied on have worn away. **The decline came from the expected factors, the narrowing whistle and the three-point shift, and from the erosion of the home team's rebounding edge, on both sides of the glass.**

![Regular season vs. playoff home win % per season, 1983–84 through 2025–26. Dashed lines are overall linear trends. Background shading marks rule-change eras; red dots mark COVID-impacted seasons.](../generated/images/home_court_advantage_season.svg){#fig-advantage-season}

**Why this matters.** Home court is the prize the regular season is built to award. Seeding, the playoff series format, and the penalty for a hard road draw are all priced on the assumption that playing at home is worth a lot, and it is now worth less than it was. The decline is also a measuring instrument. Tracking which pieces faded shows three real changes in the game: officiating grew more even between home and road teams, the leaguewide move to the three-point line flattened the home shooting edge, and teams walked away from the offensive glass. It also corrects a common assumption. The crowd is not the engine of the decline: arenas are fuller than ever, setting attendance records in the same years home court hit its lows.

**What is NOT** behind it is also interesting: **rule changes, travel, time zones, pace of play, crowd size, and the playoff format changes, including the much-blamed 2014 change.** Each one is tested here and ruled out. Competitive balance is tested too: it can't explain the long-run decline, though year to year, parity and home court wobble together a little, but only a little.

Throughout, the regular season and the playoffs are tracked separately. They share a direction but not a timeline. The analysis covers almost 52,000 regular-season and playoff games; see Appendix A for companion documents including the full statistical tables, and Appendix C for additional findings.

---

## 1. The 40-Year Decline

The decline has two layers: slow erosion of about a quarter of a point per year, with two steeper stretches on top. The first came in the mid-to-late 1990s, when the regular-season rate fell from about 65% to 60%, most likely from the 1994–95 hand-checking crackdown. A brief uptick around 2002–04 followed, visible but resting on only three seasons. The second steepening arrived after 2017, when the share of shots from deep rose from about a quarter to nearly half, pushing the regular-season rate below 56%. The playoffs held near 64% from the mid-1990s through 2017, then joined the slide, falling to 61%, then 58%.

Smaller than it was does not mean gone. In the most recent regular season, nearly every team still won more at home than on the road, with only one exception. Good teams that win everywhere still win more at home; weak teams pick up most of their wins there.

![Each team's home win% (blue) and road win% (grey) for the most recent regular season, sorted by home win%. The bar between the two dots is the home-court gap; a red bar marks the rare team that won more on the road. Reference lines show the league-average home and road win rates. One season is noisy; this is a snapshot of how widespread home court still is, not a franchise ranking.](../generated/images/home_court_team_season_hca.svg){#fig-team-season-hca}

**The decline is league-wide, not a few teams.** A natural worry is that the leaguewide drop hides a split: maybe a handful of franchises lost their home edge while the rest held theirs. They didn't. Fitting each franchise its own trend in the home-minus-road win gap and then separating real differences from the random bounce of a 40-odd-game home schedule, the spread across teams is no bigger than that randomness: the real team-to-team difference in decline rates is about zero. Every franchise's edge faded at roughly the same league-wide rate, about half a point of the home-road gap per year. Once the noise is removed, no team stands apart as the cause. This is a regular-season result; per-team playoff samples are too small to split this way, but the playoff decline is itself leaguewide.

![Each franchise's regular-season home-court trend (the home-minus-road win gap, change per year) with a bar showing the range its true value is likely to sit in, against the league-wide rate (blue line). Nearly every team's bar overlaps the league line, and once the randomness is accounted for the spread between teams is near zero: the decline is shared, not concentrated.](../generated/images/home_court_team_decline_slopes.svg){#fig-team-decline-slopes}

---

## 2. What Creates Home Court Advantage

A handful of concrete things have historically given home teams an edge on any given night: referees calling fewer fouls on them, a shooting advantage, favorable shot selection, and an advantage on the glass and in turnover differential. Rest and altitude add to the picture for specific matchups. Basketball analysts call these the Four Factors: effective field goal percentage, free throw rate, turnover margin, and rebounding. This analysis finds all four matter, and they count for about the same in both the regular season and the playoffs.

**Referee foul calls and free throws.** Across every era and in both regular season and playoffs, referees have called fewer fouls on home teams. In the 1984–94 regular season, home teams averaged about 1.2 fewer foul calls per game, translating to roughly 2 extra free throw attempts per game. In the playoffs the gap was even wider: about 1.6 fewer fouls per game and 2.4 more free throws. With fouls go free throws, and with free throws go points. This is the most consistent component of home court advantage.

The playoff referee data shows how universal this is: 45 of 47 officials with at least 50 playoff games on record show a home-favoring foul differential. Nearly every referee who has worked the postseason has called the game differently depending on which team was at home.

**Shooting advantage.** Home teams have consistently shot better than road teams: typically around a percentage point better in effective field goal percentage across most eras in both regular season and playoffs. The usual explanations are crowd comfort and familiar rims. Our data can only confirm the gap is real, not pin down the cause.

**Shot selection.** Historically, home teams have gotten more of their attempts from close range and fewer from mid-range. A paint shot is more efficient than a mid-range jumper, so home teams have started each possession with a small built-in advantage in expected scoring. This edge was clearest in an era when three-point attempts were rare. As three-point shooting took over, it gradually eroded this home advantage, in ways Section 3 covers.

**Rebounding and turnover differential.** Home teams have historically pulled down more rebounds and committed fewer turnovers: about one and a half extra boards and just over a third of a turnover per game. Neither is dramatic on its own, but both hand the home team extra possessions. Together they rival the shooting advantage in size. As Section 3 will show, this pair turns out to be the single largest driver of the decline.

**It all shows up in the box score.** The Four Factors together account for about 95% of the home advantage in the regular season, and a similar share in the playoffs. Shooting (eFG%) is the largest piece, more than 40%, followed by rebounding. How much each factor counts toward winning has held nearly constant across all six eras, so the overall breakdown isn't distorted by lumping different periods together: the game got fairer, not different in how its components combine.

![Box-score category shares of the home-court advantage, regular season vs. playoffs. The headline at each bar's end (with a range showing how much it could shift on the games available) is how much of the home edge the four categories capture together.](../generated/images/home_court_mediation_level.svg){#fig-mediation-level width=50%}

---

## 3. What's Driving the Decline

The same categories that make up home court advantage are the ones narrowing over time.

The Four Factors together account for roughly **96%** of the regular-season decline. Rebounding and turnovers carry the most at roughly **30%** and **27%**, together more than half the drop. Shooting (eFG%), where the three-point shift registers, accounts for about **21%**, and the narrowing whistle for about **18%**. In free throw terms: home teams once attempted roughly 2 more free throws per game than visitors; that edge has narrowed to under half a free throw. In the playoffs the same four categories capture only about 67% of the decline, with only the foul and rebounding trends standing clearly above the noise; the playoff breakdown is consistent with the regular-season story, not established on its own. (These shares show where the decline registers in the box score, not a claim about ultimate causes.) The sections below trace how each piece works.

These shares carry uncertainty, and how firmly each is pinned down differs by setting. The regular-season figures are tight: rebounding's share of the decline lands between about a quarter and a third, and the four categories together cover essentially all of it. The playoff shares are loose: the 67% could be anywhere from about 40% to all of the decline, which is why the playoff breakdown is read as consistent with the regular season rather than established on its own.

![Box-score category shares of the 40-year home-court decline, regular season vs. playoffs. The headline at each bar's end (with a range showing how much it could shift on the games available) is how much of the decline the four categories capture together; the playoff range is wide. Rebounding here is total boards (offensive + defensive); the OREB and DREB breakdown is in the rebounding chart further below.](../generated/images/home_court_mediation_decline.svg){#fig-mediation-decline width=50%}

![Home minus away differentials over time: free throw attempts per game (the whistle's practical effect), FG%, eFG%, 3PA rate, 3P%, and FT%. Each panel shows the per-season gap; a trend toward zero means that component of the home-team edge is narrowing. The rebounding and turnover differentials are covered below.](../generated/images/home_court_advantage_differentials.svg){#fig-advantage-differentials}

**Three-point shooting shifted shot selection and narrowed the shooting edge.** The league's move to the perimeter changed shot selection in two visible ways. First, away teams have closed the gap in paint attempts: in the 1990s home teams generated about 1.3 percentage points more of their attempts from close range than road teams; by 2023–26 that gap has shrunk to 0.2 points. Second, three-point volume itself rose for everyone. Once three-point volume is held constant, the eFG% convergence disappears: in games with similar three-point rates, the home shooting edge shows no decline at all. The paint gap closing works the same way: **it traces entirely to rising three-point volume, not to any separate cause.** In the playoffs the paint gap narrowed in the late 2010s but has since rebounded close to its old level, making this a regular-season story for now.

![Shot zone differentials (home minus road) over time, regular season vs. playoffs. Four panels: paint, mid-range, corner 3, and above-break 3. The paint panel is the key one: the gap has nearly closed, meaning away teams now get close-range attempts at nearly the same rate as home teams. The three-point panels show little differential throughout.](../generated/images/home_court_shot_zones.svg){#fig-shot-zones}

The league's three-point attempt rate and the home win rate have moved in opposite directions for 40 years. When 7% of shots were threes in the 1980s, home teams won 65%; when 40% are threes today, they win 55%. The timing lines up with the second sharp drop: the three-point share rose from about a quarter to nearly half of all shots in the three seasons after 2017, exactly when that drop began.

That 40-year lockstep looks convincing, but a tighter test exposes its limits. Once you set aside the fact that both lines simply drift over the decades and ask whether they still move together year to year, the link weakens by about half: roughly 40% of that striking visual is two trends heading the same direction over time, not one driving the other.

The reliable evidence is within a single season: games in which both teams collectively attempt more threes are games home teams lose more often, at roughly 2–3 fewer wins per 100 games for every 10-point rise in three-point volume. That link holds within each era, not just across the full 40-year span, and it appears in both the regular season and the playoffs.

The three-point shift registers most directly in the shooting line of the box score. When three-point rates are low, the home shooting advantage holds up; as they rise, the advantage shrinks. Shooting accounts for roughly one-fifth of the regular-season decline. But the perimeter shift reaches past that one category: it also explains about half of the foul decline and about half of the turnover decline. Add those in and three-point shooting touches close to half the decline overall. What it does not explain is the largest single category, rebounding, which barely moves when three-point volume is held constant. The perimeter shift is a major force, then, but not the engine behind the whole decline. In the playoffs the within-season signal is weaker, since team quality swamps stylistic factors, but it still points the same direction.

![Three panels. Left: dual-axis time series showing the 40-year lockstep between rising three-point volume (right axis) and falling home win % (left axis) in the regular season. Center and right: scatter of one season per point for regular season and playoffs, era-colored, showing the same inverse relationship.](../generated/images/home_court_3pa.svg){#fig-3pa}

**Rebounding, the largest driver, separate from the three-point shift.** The home team's rebounding advantage has shrunk steadily for 40 years. Unlike the shooting advantage, it is not the three-point story in disguise. When three-point volume is accounted for, the home shooting advantage vanishes entirely, while the rebounding advantage barely moves.

Both sides of the glass show declining home advantages, and the raw numbers are larger than the offensive-rebound story alone suggests. The home advantage on defensive rebounds fell from +1.64 boards per game in the 1980s to +0.59 today, a drop of about 1.0 board. The home advantage on offensive rebounds fell from +0.61 to slightly below zero, a drop of about 0.7 boards. The defensive side actually fell more in absolute terms.

Some of that defensive decline, though, is a consequence of the shooting improvement already captured in the shooting category: if away teams miss fewer shots, there are simply fewer defensive rebounds available for the home team to grab. Offensive rebounding, measured as each team's share of available offensive boards, is the cleaner test of whether home teams are actually crashing the glass more aggressively, because it does not change just because one team shoots better.

On that cleaner measure, the asymmetry is clear. In the mid-1980s, home teams converted about 34% of their offensive rebounding chances; away teams converted about 31%. Both rates fell as the league moved away from crashing the glass, but the home rate dropped 8 percentage points while the away rate dropped only 5. The two lines converge and cross by 2025–26. The edge didn't close because away teams became better offensive rebounders. Home teams stopped crashing the offensive glass more aggressively than visitors.

**Why home teams retreated faster than visitors is not something this data can answer.** The most commonly offered explanation in basketball circles is strategic: teams increasingly chose transition defense over second chances, and the three-point revolution may have reinforced that calculus since longer shots scatter to less predictable spots. One possibility is that crowd noise and a familiar building historically encouraged extra hustle on the offensive glass, and as the league-wide retreat from crashing took hold regardless of venue, that motivational lift had nowhere to express itself. These are plausible explanations, not conclusions this analysis can establish.

The home turnover advantage has eroded too, and it belongs in the same discussion. In the 1980s, home teams committed about 0.4 fewer turnovers per game than visitors. That gap has nearly closed. About half of the decline is a direct consequence of the perimeter shift: three-point attempts generate fewer live-ball turnovers than drives and post play, so as both teams moved out, the absolute number of turnovers fell league-wide and the home team's edge shrank with it. The other half is separate from three-point volume. Together, turnovers account for about 27% of the regular-season decline, nearly matching rebounding. The data can't explain that other half. Improved scouting and video preparation are the most plausible contributors: visiting teams are better prepared for unfamiliar defensive schemes than they once were. But that is hypothesis, not something this analysis can establish. In the playoffs, the turnover trend is small and too noisy to be sure of; the playoff evidence is consistent with the regular-season story, not established on its own.

The playoffs point the same way on rebounding: the home rebound-share advantage has fallen by roughly three-quarters there too. With a fifteenth as many games, the playoff evidence is consistent with the regular-season story rather than established on its own.

![Why the home rebounding and turnover edges faded. Left: home and away offensive-rebound rates over time; the lines converge and cross, meaning home teams no longer crash the offensive glass more than visitors. Center-left: raw OREB and DREB differentials (home minus away per game) over time; both declined, with the defensive edge falling more in absolute terms. Center-right: seasons with a larger total home rebounding edge tend to be seasons where home teams win more (association, not causation). Right: the home turnover edge (away minus home turnovers per game) has declined from about 0.4 to near zero.](../generated/images/home_court_rebounding.svg){#fig-rebounding}

Player-tracking cameras, deployed in 2013–14, confirm the final chapter. The home advantage in converting offensive-rebound chances kept shrinking through the entire tracking era, falling from about 1.5 percentage points in the mid-2010s to under 0.2 today. Home teams have held no measurable box-out advantage throughout the tracking window. By the time the cameras arrived, most of the decline had already happened; the tracking data confirms the mechanism is still running.

![The modern player-tracking view of the home rebounding advantage (2013–14 on). Left: the home advantage in converting offensive-rebound chances keeps shrinking, falling from about 1.5 percentage points in the mid-2010s to under 0.2 today. Center: home teams hold no measurable box-out advantage. Right: the second-chance-points advantage shows little change across this window. A short window that corroborates the modern mechanism, not the 40-year decline.](../generated/images/home_court_rebounding_tracking.svg){#fig-rebounding-tracking}

**Referee foul bias has narrowed.** The home foul differential in the regular season has dropped from 1.2 fouls per game in the 1980s to roughly a quarter of a foul per game today, an 80% reduction. In free throw terms: home teams once attempted roughly 2 more free throws per game than visitors; now it's under half a free throw. In the playoffs the foul gap fell from 1.6 to 0.7 fouls per game, and the free throw edge from 2.4 to 1.1 attempts. The advantage referees once gave home teams has fallen about 80% in the regular season and more than half in the playoffs.

The playoff referee chart shows the generational shift clearly. The distribution across officials has compressed over time, not just shifted. Newer referees are not only less biased on average; they are also more uniform in their calling. Per-official records are available from 1995 onward; the 1984–94 baseline figures above come from the aggregate box-score foul differential visible in Section 2's differentials chart.

Three-point shooting played a direct role too. Three-point attempts draw fewer fouls than drives to the basket. As both teams moved toward the perimeter, there were simply fewer foul calls to go around, and the home team's absolute gap shrank with it. About half of the foul decline traces to this mechanical shift in shot selection; the other half reflects genuine change in how referees call the game.

![Distribution of per-official home foul bias by era, playoffs. The spread has compressed: newer officials are not only less biased on average but more uniform in their calling. Chart covers 1995 onward, the earliest era with sufficient per-official playoff data.](../generated/images/home_court_referee_era.svg){#fig-referee-era}

Could rebounding and turnovers just be the three-point shift in disguise? No. When games with similar three-point rates are compared directly, the **shooting** decline disappears entirely: with three-point volume held constant, the home team's shooting edge shows no downward trend at all. The observed convergence is entirely the perimeter story. The **rebounding** decline barely moves and stays the surest of the four. Fouls and turnovers each land in between: roughly half of each category's trend is explained by rising three-point volume, leaving the other half separate from the perimeter shift. The categories doing the most work to drag home court down, rebounding and the part of turnovers separate from threes, are doing it for reasons the three-point boom does not explain. (In the playoffs the same comparison is too noisy to read; only the rebounding decline clears the bar. So this is a regular-season verdict.)

![How much of each category's pull on the home-court decline survives once three-point volume is held constant. Each category's contribution is shown in win-percentage-points per decade, before (open dot) and after (filled dot) three-point volume is held constant. A filled dot pulled to the zero line means the three-point shift fully accounts for that category's decline; one that stays put is a separate driver. In the regular season (left) the shooting contribution collapses to the zero line and slightly past it (fully absorbed), rebounding barely moves (it survives), and fouls and turnovers each pull about halfway. The playoff panel (right) is mostly small-sample noise (greyed, too noisy to read); only rebounding stands out clearly, and it survives there too.](../generated/images/home_court_3pa_control.svg){#fig-3pa-control}

The decline is smooth, not a staircase of sudden drops. Testing for the moment the slope bent finds evidence for at least one bend around the late 1990s, consistent with the hand-checking era, but can't pin the year within a decade or say how many bends there are.

![How many times the decline changed pace, and when. Left: season home win % with a fitted line for each number of bends: no bend (grey dashed), one bend (blue solid), two bends (red dash-dot), three bends (green dotted); the most likely bend years are labeled, and the one-bend slopes are shown bottom-left. Right: if the decline has a single bend, which year it most likely happened; 1999 is the best single guess, with a likely range of 1992–2003.](../generated/images/home_court_bayesian_changepoint.svg){#fig-bayesian-changepoint}

**The box-score story predicts the decline it never saw.** A fair worry about any after-the-fact explanation is that it was fit to the whole history, so of course it lines up. To test that, the four-factor win model was trained only on seasons through 2013, then asked to predict each later season's home win rate from that season's box-score edges, with its coefficients frozen. It tracks the 2014–2026 decline closely: its error on seasons it had never seen is about 1 percentage point in the regular season, against more than 5 for a flat guess. It even catches the 2021 dip that a simple extension of the early trend line misses. The same frozen model also reconstructs the steeper modern playoff decline, which a naive trend extension misses entirely because the early playoff slope was nearly flat. The mechanism holds up on data it was not built from.

![Actual home win % across all seasons (regular season left, playoffs right) with the channel-model forecast and a trend extrapolation drawn over the held-out 2014-onward window. The win model was trained only on pre-2014 games, then used to predict each later season from its box-score edges. The frozen forecast tracks the held-out decline, and beats both a flat guess and the extrapolated trend line.](../generated/images/home_court_oos_forecast.svg){#fig-oos-forecast}

The best explanation the data points to is that analytical tools for shot selection, scouting, and preparation have reached every team at roughly the same pace. When all 30 teams land on the same approaches regardless of venue, the home team's preparation edge has nowhere to go but down.

---

## 4. What Didn't Drive the Change

The charts in this report group seasons by the NBA's major rule changes:

| Era | Seasons | Defining rule change |
|-----|---------|----------------------|
| 1984–94 | 1983–84 → 1993–94 | Illegal-defense rules (no zone defense) |
| 1995–01 | 1994–95 → 2000–01 | Hand-checking restrictions; zone still illegal |
| 2002–04 | 2001–02 → 2003–04 | Zone defense legalized; defensive three-seconds added |
| 2005–17 | 2004–05 → 2016–17 | Perimeter hand-checking banned (the pace-and-space era) |
| 2018–22 | 2017–18 → 2021–22 | Freedom-of-movement emphasis |
| 2023–26 | 2022–23 → 2025–26 | Transition take-foul rule |

It would be natural to read those era boundaries as explaining where home court bent. They mostly don't. Check each boundary against the trend line and only 1994–95 registers: a genuine one-time drop of about 2.6 points, most likely from the hand-checking crackdown (though the simultaneously shortened three-point line adds some ambiguity). Hand-checking registered because it directly affected referee discretion, one of the few things that can shift asymmetrically between home and away teams. Every other rule change reshaped how the game looks without reshaping who benefits from playing at home: zone legalization, the 2004-05 perimeter hand-check ban, freedom of movement, and the take-foul rule. In the playoffs, even 1994–95 doesn't register; the postseason slide is steady drift throughout.

Most situational factors either don't matter or haven't changed enough to explain the decline. Travel distance matters at about 0.07 percentage points per 100 miles in the regular season (negligible) and has no measurable effect in the playoffs. Time zones are flat in both. Rest creates genuine variation (home teams win 63% when better-rested, 58% when the visitor has the edge) but that gap hasn't changed across eras. Load management cut back-to-back frequency from 35% to under 20%, which is real, but that schedule change accounts for only 8% of the decline; home advantage eroded within every rest situation alike. Pace of play and the home-vs-away three-point differential show no meaningful relationship to the trend. Competitive balance shows none in the raw season-to-season comparison; a faint link appears only after setting aside each series' long-run drift, on a small sample, so it is best treated as a hint, not a finding.

Crowds have stayed near capacity throughout (record highs in the 2020s, the very years home court hit its lowest), so crowd size is not the dial. Crowd *presence* is different. The 2020-21 pandemic seasons ran an accidental test: with buildings empty, home teams won just 51%; with any crowd at all, they won 58.5%. A crowd is a genuine ingredient of home court, worth about seven points on the night. But it is a switch that flips with the doors, not a 40-year dial slowly turning down. A combined model stacking all situational factors confirms it: after accounting for rest, altitude, time zones, and COVID seasons, the remaining explanatory power belongs entirely to which era the game was played in: the decline itself, not any off-court factor. The full treatment of each hypothesis, including why each seemed plausible and exactly what the data showed, is in [The Investigation](home_court_investigation.html).

![Left: league average attendance per game vs. regular-season home win %, 2000–2026, with crowds holding near capacity (and lately setting records) while home court keeps falling. Right: 2020–21 home win % by game attendance, where an empty arena erases the advantage that even a small crowd restores.](../generated/images/home_court_attendance.svg){#fig-attendance}

---

## 5. The Playoff Picture

The playoffs are not a shrunken version of the regular season. They have their own structure, their own baseline, and their own timeline of decline.

**Home court is the strongest predictor of playoff game outcomes.** Games 1 and 2, at the higher seed's arena, go to the home team 69% and 72% of the time. Games 3 and 4, at the lower seed's arena, are barely better than coin flips for the team playing there (55–56%). Game 5, back at the top seed, is the most lopsided of all: 74.5%. Even Game 7 still goes to the home team 64% of the time. Road teams show no evidence of adapting as a series deepens.

![Two panels. Left: playoff home win % for each game within a series (G1 through G7), all eras combined, with a reference line at the overall playoff average. G5, back at the top seed's arena, is consistently the most lopsided. Right: the same G1–G7 breakdown broken out by era, one line per era.](../generated/images/home_court_series_breakdown.svg){#fig-series-breakdown}

**The playoff decline is real home-court weakening, not weaker seeds.** A natural objection: maybe playoff home teams win less now simply because top seeds no longer outclass their opponents the way they once did. The data says no. Account for the regular-season quality gap between the two teams and the year-by-year playoff decline doesn't budge. None of it is explained by seeds bunching together. The cleanest proof: when the objectively weaker team hosts Games 3 and 4, it still wins 51.5% of the time. Home court alone is still worth a coin-flip-beating advantage, and that advantage is what has been eroding.

![The playoff decline is genuine home-court weakening, not weaker seeds. Left: the yearly playoff decline is the same size before and after removing the regular-season quality gap between the two teams (quality explains essentially none of it). Right: home win % by who hosts, where even the objectively weaker team still wins about 51.5% of its home games (Games 3–4), a pure venue effect above the coin-flip line.](../generated/images/home_court_playoff_quality.svg){#fig-playoff-quality}

**The 2014 format change didn't cause the playoff drop.** The playoffs have been restructured over the years, in four distinct format periods:

| Period | Seasons | Format |
|--------|---------|--------|
| 1984 | 1983–84 | Best-of-5 first round; 2-2-1-1-1 Finals |
| 1985–02 | 1984–85 → 2001–02 | Best-of-5 first round; 2-3-2 Finals |
| 2003–13 | 2002–03 → 2012–13 | Best-of-7 first round; 2-3-2 Finals |
| 2014–26 | 2013–14 → 2025–26 | Best-of-7 first round; 2-2-1-1-1 Finals |

The most recent shift, in 2014, coincided with the sharpest period of playoff HCA decline: a nearly 7-point raw drop from the 2003–13 period to the 2014–26 period. But once the steady year-by-year decline already underway is accounted for, the format change has no effect of its own. The playoff drop would have arrived on roughly the same schedule regardless. Format was not the cause.

![Home win % averaged over each playoff format period, for both the regular season and the playoffs. The regular season never changed format, so the fact that both series decline at similar rates across the same periods means the format change is not driving the playoff drop.](../generated/images/home_court_advantage_format_bars.svg){#fig-advantage-format-bars width=50%}

**A best-of-7 absorbs most of home court, and most of its decline.** A single home game and a seven-game series are very different things. To see how the per-game edge translates into who wins a series, we ran a simulation: take the home win rate for a single game and play out 200,000 best-of-7 series between two otherwise-equal teams, with the home-court team hosting Games 1, 2, 5, 6, and 7. The format flattens the edge hard. In the 1980s a home team won about 65% of individual regular-season games, but that turned into only a 55% chance of winning a series. By the 2020s the per-game rate had fallen to about 56%, and the series edge with it, to under 52%: a home-court team in a series is now barely better than a coin flip. The playoffs tell the same story at a slightly higher level (a series edge near 52.5% today). The drop matters less than the per-game numbers suggest: a roughly 9-point fall in the regular-season per-game edge shows up as only about a 3-point fall at the series level. See RESULTS.md for the full per-era table. Two cautions: the playoff per-game rate mixes home court with seeding (better teams host more games), so the regular-season figures are the cleaner read on pure venue effect, and the simulation assumes each game is a fresh start, unaffected by who won the ones before, so it illustrates how much the format dilutes an edge rather than forecasting any real series.

![Two panels translating the per-game home edge into a best-of-7 series edge via simulation. Left: a single-game home win rate (x-axis) maps to a much smaller series win rate (y-axis) for the home-court team, far below the dashed 1:1 line; era dots sit on the curve and drift toward the 50% coin flip over time. Right: the simulated series-level home edge by era for the regular season and the playoffs, both ending just above 50%, with the per-game rates shown muted above for contrast.](../generated/images/home_court_series_simulation.svg){#fig-series-simulation}

Additional findings, including individual referee rankings, franchise-level comparisons, and the blowout-margin trend, are in Appendix C.

---

## 6. Summary

Home court advantage in the NBA has dropped about 10 percentage points over 40 years. The regular season went from 65% to about 55%; the playoffs from nearly 68% to 58%. In net rating terms, the gap between how home and away teams perform has shrunk from roughly 3 points per 100 possessions in the 1990s–2010s to about 2 points today in the regular season. The playoffs compressed more slowly, from about 4.5 to 4 points per 100 possessions.

The decline is real and one-directional: a slow, four-decade erosion with a documented sharp drop in the mid-to-late 1990s and renewed steepening after 2017, with a brief visible uptick around 2002-04 in between. The first steepening traces to the 1994–95 rule change, most likely the hand-checking crackdown, whose full adjustment played out through the late 1990s. The second coincides with the post-2017 perimeter shift, which shows up in the shooting line of the box score. Neither is the whole story. The data points to four main explanations that together account for about 96% of the regular-season decline:

**Referees are calling fairer games, and three-point shooting is pulling the gap further down.** The systematic home-team foul benefit was 1.2 fouls per game in the regular season and 1.6 in the playoffs in the 1980s; in free throw terms, home teams attempted roughly 2 more free throws per game than visitors (2.4 in the playoffs). Both gaps have mostly closed: the foul edge is now roughly a quarter of a foul per game in the regular season and 0.7 in the playoffs, and the free throw edge is under half an attempt per game. About half of that decline is a direct consequence of three-point shooting: shots from the arc draw fewer fouls than drives to the basket, so as both teams moved to the perimeter, there were fewer foul calls to go around. The other half is genuine change in how referees officiate, and it shows up universally: 45 of 47 playoff officials with at least 50 games on record call fewer fouls on the home team.

**Three-point shooting works through two related effects, and reaches beyond the shooting line.** The first is paint-shot convergence: as three-point volume rose, away teams closed the gap in close-range attempts, erasing a shot-quality edge home teams once carried into every possession. The gap in paint-shot rate fell from 1.3 percentage points in the 1990s to 0.2 today. The second is three-point volume itself: when three-point rates are low, the home shooting advantage holds up; as they rise, the advantage shrinks. The 40-year parallel between three-point volume and home win rate is the most striking visual in the dataset, but the reliable evidence is within a single season: games with more threes go against home teams even among contemporaries, not just across decades. In the box score the shift registers most directly as the shooting category, about 21% of the decline; counting its share of the foul and turnover categories (roughly half of each), three-point shooting reaches close to half the decline overall. Rebounding, the largest single piece, is the part it does not explain.

**The largest driver, separate from the three-point shift: the rebounding advantage eroded on both sides of the glass.** The home team's hold on the boards has slipped over 40 years, separately from the three-point boom. The home advantage on defensive rebounds fell from +1.64 boards per game to +0.59; the home advantage on offensive rebounds fell from +0.61 to slightly below zero. The defensive edge fell more in absolute terms, though part of that decline is a consequence of away teams shooting better over time (fewer misses means fewer defensive boards for the home team). The cleaner measure is the offensive rebounding rate: home teams' share of available offensive boards dropped 8 percentage points (34% to 26%) while away teams' dropped only 5 (31% to 26%). The offensive edge closed because home teams stopped crashing more aggressively, not because away teams improved. The home turnover advantage has partly followed, and the same pattern holds in the playoffs. **What drove these changes is not something this analysis can establish.** Strategic shifts toward transition defense, improvements in visiting-team preparation, and the perimeter revolution are all plausible contributors, but they are hypotheses, not conclusions from this data.

What hasn't driven the decline: rule changes (with the single exception of 1994–95), travel, time zones, pace of play, crowd size, and playoff scheduling format. The data rules each out. Competitive balance is a partial exception: it can't explain the long-run decline (parity bounces up and down from year to year while HCA has fallen steadily for 40 years), but year to year, parity and home court wobble together a little, so parity belongs in the "doesn't drive it" column with an asterisk. Fewer back-to-backs for visiting teams explains only about 8% of the decline. Arenas have stayed near capacity, lately setting records, even as the advantage shrank. The one genuine crowd effect is a blip: in the empty arenas of 2020–21 home teams won just 51%, then snapped back to 58.5% whenever fans returned. Crowd noise is real and measurable, but it's a switch that flips with the doors, not a dial slowly turning down for 40 years.

The playoffs have followed the regular season's path but with nearly a two-decade lag. With roughly 3,300 playoff games over 40 seasons compared with 49,000 in the regular season, the playoff trend is measured with considerably less precision, though its direction is not in doubt. For most of the 2000s and 2010s, postseason home court held firm even as the regular season eroded around it. The internal structure of playoff home court remains stark: Games 1 and 2 go to the home team 69% and 72% of the time; Game 5 is the most lopsided at 74.5%; even Game 7 still goes to the home team 64% of the time. Since 2018 the decline has accelerated. It is genuine home-court erosion, not an illusion of more evenly matched seeds. Even the weaker team, when it hosts, has been winning less.

That raises the natural question of **where the trend goes from here**. Three-point volume and the league-wide retreat from the offensive glass are both near the limits of their effect on home court advantage. Three-point attempts now make up about 40% of shots, a share that can't grow indefinitely. The offensive rebounding rate has fallen from 33% to 26% and is close to a floor where teams can't realistically pull back further. If both are leveling off, the pace of decline should slow. The empty-arena data provides the best guide to a lower bound: with no crowd, no foul bias, and no preparation edge, home teams still won 51%. Something near that is probably where the long-run trend settles. The best explanation the data supports is that analytical tools for shot selection, scouting, and preparation have reached all 30 teams at roughly the same pace. When every team runs the same approaches regardless of venue, the home team's preparation edge compresses. That is not specific to basketball, and every major sport investing in the same analytics is probably on the same path, though the data here can't test it.

---

## Appendix A: Companion Documents

::: {.content-visible when-format="html"}
| Document | Description |
|---|---|
| [Regression Results](home_court_results.html) | Full statistical output from the analysis pipeline: regression tables, significance tests, and coefficient values for every analysis in this report. |
| [The Investigation](home_court_investigation.html) | Full treatment of every ruled-out hypothesis: why each seemed plausible, what was tested, and what the data showed. |
| [One-Page Summary](home_court_summary.html) | Standalone summary built around the three core charts and the three questions. |
| [Stats Explainer](home_court_stats_explainer.html) | Guide to the statistical methods used, written for a general audience. |
| [Stats Tutorial](../../generated/stats_tutorial.html) | Worked examples reproducing key results from the regression output. |
:::

::: {.content-visible when-format="typst"}
All files are in the same folder as this PDF (`generated/`), except the Stats Tutorial which is one level up in `../generated/`.

| Document | File | Description |
|---|---|---|
| Regression Results | `home_court_results.pdf` | Full statistical output: regression tables, significance tests, and coefficient values for every analysis in this report. |
| The Investigation | `home_court_investigation.pdf` | Full treatment of every ruled-out hypothesis: why each seemed plausible, what was tested, and what the data showed. |
| One-Page Summary | `home_court_summary.pdf` | Standalone summary built around the three core charts and the three questions. |
| Stats Explainer | `home_court_stats_explainer.pdf` | Guide to the statistical methods used, written for a general audience. |
| Stats Tutorial | `../generated/stats_tutorial.pdf` | Worked examples reproducing key results from the regression output. |
:::

---

## Appendix B: Independent Corroboration

Sparkle Technologies published an independent analysis of the same question at [sparkletechnologies.com/blog/nba-disappearing-home-court-advantage](https://sparkletechnologies.com/blog/nba-disappearing-home-court-advantage). We checked every number we share in common. Most of them match. The disagreements are instructive.

**Where we agree.** The overall decline, the foul-call story, the irrelevance of travel and pace: all consistent across two independent pipelines. The clearest confirmation that neither analysis is fabricating results: the Sparkle altitude figures for Denver and Utah land within a tenth of a point of ours.

**Where we differ, and why.** The blog names the three-point revolution as the primary cause, drawing on a 40-year near-mirror image: as three-point attempts rose, home win percentage fell. We ran a tighter test and found about 40% of that lockstep is just two trends drifting the same way over time, not one causing the other. The three-point effect is real, showing up within individual seasons too. In the box score it registers most directly as the shooting category, about 21% of the regular-season decline; counting its share of the foul and turnover categories (about half of each), it reaches close to half the decline, still short of the whole story. The category the blog never measures at all, rebounding, is the single largest category and is separate from the three-point shift; turnover-edge erosion adds more on top.

On the mid-1990s drop, the blog attributes it to the shortened three-point line (1994–97); we attribute it to the hand-checking crackdown. Both changes happened in the same seasons. Breaking the decline by category gives some traction: foul calls responded immediately and significantly at the 1994-95 boundary while the shooting category barely moved, pointing more toward hand-checking. The two are not fully separable, but hand-checking is the more consistent explanation with the data.

The empty-arena numbers look different for a methodological reason. The blog's "empty arena" figure (54.4%) is the 2020–21 season average, blending games with zero fans and games with partial crowds. We split those apart: 51.0% with empty buildings, 58.5% with any crowd at all. No real disagreement on the conclusion (crowd presence is a switch, not a dial), but the blog's single number averaged over the whole phenomenon.

**What the blog found that we then tested.** The blog credited the schedule shift, fewer visitors arriving on a back-to-back, with 15–20% of the decline. The premise checks out: back-to-back frequency fell from about 35% to under 20%. The magnitude doesn't hold. Separating the schedule change from the rest puts the schedule effect at roughly 8% of the decline. The other 92% is the home advantage eroding within every rest situation alike, regardless of how tired the visitor is.

**What we found the blog missed.** The rebounding collapse is the biggest gap. The blog's box-score account has no rebounding term; we find it is the largest driver, separate from the three-point shift, carrying 30% of the regular-season decline, and it holds up after accounting for three-point volume. Turnover-edge erosion (another 27%) is also unaccounted for. The blog's decomposition points at something real. It just misses where most of the work is happening.

---

## Appendix C: Additional Findings

A few results surfaced along the way that don't bear directly on the three questions but are worth noting.

**Referees differ in home-court bias, but less than the raw numbers suggest.** Of 47 officials with at least 50 playoff games, 45 call fewer fouls on the home team. The most home-leaning on record, Ron Garretson, Joe Crawford, and Eddie Rush, sit close to a full foul per game apart from the most even-handed, a group that includes Tony Brothers, Josh Tiven, and Joe Forte. About 60% of that raw spread is small-sample noise. Referees genuinely differ, but the gap between them is narrower than the leaderboard suggests. This measures tendencies, not proof that any one official decides games.

![Top/bottom 15 referees ranked by home foul differential (≥50 playoff games). Values are adjusted for how few games each official worked: raw differences are pulled toward the league average so that small samples don't dominate the leaderboard.](../generated/images/home_court_referee_rankings.svg){#fig-referee-rankings}

**Denver and Utah have the largest home-court advantages in the league, likely because of altitude.** Across 40 seasons, the Nuggets and Jazz hold the largest regular-season home advantages of any franchise: about 27 and 26 percentage points above their own road win rates, against a league average near 20. Both play at altitude. The franchise spread is real: roughly 70% of the variation across teams reflects genuine differences, not noise. Altitude sits right at the top of it. With only two high-altitude franchises, elevation can't be fully separated from whatever else is unique to those teams, but it is the most plausible common thread. (The 27-point figure is their full home-minus-road gap; the altitude piece on its own, from Section 4, accounts for about 8 of those points.)

![Franchise home court advantage, regular season and playoffs. Each bar carries a range showing how much the figure could shift on the available games: in the regular season most franchises sit clearly apart, but in the playoffs the ranges are wide and overlapping, so the franchise differences there are mostly noise.](../generated/images/home_court_team_hca.svg){#fig-team-hca}

**The decline is universal, but some franchises fell much further than others.** Splitting the 40-year record at 2001–02, the league average dropped from about 25.6 percentage points to about 17. Every one of the 26 franchises with at least 400 home games in both halves declined. Sacramento and Phoenix fell the most, about 16 and 15 points; both had been near the top of the league in the 1980s and 1990s and are now near the bottom. The Knicks shed 13 points. At the other end, the Los Angeles Lakers barely moved at all (a drop of under 1 point), though they started below the league average and remained there. Denver and Utah both declined substantially (13 and 9 points respectively) but still sit at the top of the late-era rankings. The pattern is consistent with compression: franchises that had the most home-court edge in the early era had more room to lose.

![Franchise HCA in the early era (1984–2001, blue) and recent era (2002–26, green), sorted by early-era HCA. Every franchise shifted left. The dashed vertical lines mark the league average in each era.](../generated/images/home_court_team_hca_era.svg){#fig-team-hca-era}

**In the playoffs, every franchise's home court looks the same.** That real regular-season spread vanishes in the postseason. With fewer than 150 playoff home games on record for most franchises, the apparent gaps are entirely explained by small samples. The true spread between franchises is too small to tell apart from random chance. A team's apparent postseason home-court strength mostly reflects being a good team. Good teams simply play more home games.

**Home court is worth more in the playoffs than in the regular season.** Among franchises with both records, home court is worth about 20 points in the regular season but 27 in the playoffs, a 7-point premium. Teams that protect their building in the regular season tend to do so in the playoffs as well, but only loosely. The crowd, the stakes, and the familiar floor count for more when the games matter most.

**The blowouts are getting bigger, even as home teams win less.** As home court advantage has declined, the margin when the home team *does* win has grown. Home wins are more lopsided; home losses are worse. Track the full spread of margins regardless of who won: the gap between the biggest wins and biggest losses widens by about 0.2 points per year in the regular season and 0.3 in the playoffs. In the regular season blowouts grow in both directions; in the playoffs the spread widens mainly because the big home wins keep getting bigger. Fewer home wins overall, but the ones that happen are more decisive.

![Three panels. Left: mean all-game point margin per season for regular season and playoffs. Center: mean win margin and mean loss margin per season (regular season); the two lines diverging means the average home win is getting bigger while the average home loss is getting worse. Right: the same by era.](../generated/images/home_court_margin.svg){#fig-margin}

**The box-score breakdown has implications for teams on both sides of a matchup.** For a home team, the rebounding category is the most tractable remaining lever: it carries 30% of the regular-season decline, is almost entirely separate from three-point volume, and has not been equalized by the league-wide strategic shift to the perimeter. Player-tracking data confirms the offensive-rebound conversion edge is still declining rather than structurally fixed, meaning effort and roster decisions can still move it. The turnover category (27% of the decline) has a component separate from three-point volume as well; pressure defense at home, where crowd noise compounds visiting teams' communication problems, targets it directly. On crowd: the pandemic data shows that even a few thousand fans restores nearly the full crowd effect, but larger crowds add little beyond that. Engagement matters more than capacity.

For an away team, three-point heavy shot selection has already largely equalized the shooting category, and the data confirms this. The offensive glass is where the road disadvantage persists most and where no current strategic trend is closing the gap. On rest: when the away team enters better-rested than the home team, home win rate falls roughly 3 percentage points below the baseline, a scheduling-available edge the data supports consistently across all eras.

## Appendix D: Caveats
I'm using this project as an exercise to learn Claude Code, statistics, and NBA analytics. I am not a statistician.

- Every calculation and data gathering is done by Python. Claude doesn't have a change to hulicinate data or get a calcuation wrong.
- Claude did come up with what statistics to use, and what they mean.
    - I did make Claude create a page that goes over every statistics, why, and what it means. I'm still making me way through that.
    - I also had Claude create a tutorial based on the statics used, I'm still making my way through that.
- Claude did write almost all the text of this document and others (Except this appendix). I have spend dozens of hours go through and make sure that I understand the text, the graphs, etc. I have forced Claude to make things coherent, corrected logic errors etc. It's like arguing with the dumbest brialliant grad student. It will do want it thinks you want, and sometims much better than you asked, but it doesn't really understand what it's doing.
- All the code, and all the results of the statistics in checked into github

If after all that I still have something wrong, please let me know.