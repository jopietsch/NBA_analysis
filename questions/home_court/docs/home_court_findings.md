# NBA Home Court Advantage: Findings

Home court advantage in the NBA has been shrinking for four decades, and this report sets out to answer what has changed and why. **Has it really changed?** **What makes home court an advantage in the first place?** And **what's driving the decline what isn't?**

Yes: the home team's win rate has fallen from about 65% to 55% in the regular season, and from nearly 68% to 58% in the playoffs. **Most of that fall is slow, steady erosion, with two sharper drops layered on top.** The structural advantages home teams once relied on have worn away: at the whistle, in the three-point revolution (which reshaped shot selection with it), and on the glass. The largest share of the decline came not from the expected factors, the narrowing whistle and the three-point shift, but from the erosion of the home team's rebounding edge, on both sides of the glass.

What is *not* behind it is also interesting: **rule changes, travel, time zones, pace of play, competitive balance, crowd size, and the playoff format changes, including the much-blamed 2014 change.** Each one is tested here, and each one is ruled out.

Throughout, the regular season and the playoffs are tracked separately. They share a direction but not a timeline. The analysis covers 52,000 regular-season and playoff games; see Appendix A for companion documents including the full statistical tables, and Appendix C for additional findings.

---

## 1. The 40-Year Decline
The drop unfolded at roughly a quarter of a percentage point per year. The playoffs tell the same story with a slight lag. The postseason home win rate peaked near 68% in the 1980s before sliding to 58% today. That's a 9-to-10-point drop, comparable to the regular season but noisier given fewer games.

![Regular season vs. playoff home win % per season, 1983–84 through 2025–26. Dashed lines are piecewise phase trends: four segments for the regular season reveal the two-drop structure (steep 1990s drop, two-decade plateau, post-2017 drop); two segments for the playoffs show the pre-2018 plateau and later drop. Background shading marks rule-change eras; red dots mark COVID-impacted seasons.](../generated/nba_home_court_advantage_season.png)

Two things are happening at once. The first is a **slow, continuous erosion** of about a quarter of a point per year, driven by the box-score categories in Section 3 grinding down gradually. The second is **two sharp drops** layered on top.

The first sharp drop came in the mid-to-late 1990s, when regular-season home win % fell from about 65% to 60%, the steepest move in the dataset. The line then held roughly flat for nearly two decades before a second drop, beginning after 2017, pushed it below 56%.

Neither drop is a separate cause stacked on top of the trend. Each is a moment when one specific force accelerated the same trend. The first traces to the 1994–95 hand-checking crackdown, the one rule-change boundary that registers in the data and the exception in an otherwise flat rule-change story (Section 4). The second coincides with the three-point revolution: the share of shots from deep rose from about a quarter to nearly half in the three seasons after 2017. That shift accelerated the decline, but it's a marker of a broader move to the perimeter, not the whole explanation.

The playoffs also dropped, but later. Postseason home court held near 64% from the mid-1990s through 2017, even as the regular season eroded below it. It then joined the slide after 2018, falling to 61%, then 58%.

A word on era labels. The charts group seasons by the NBA's major rule changes, since each one reshaped how the game is played:

| Era | Seasons | Defining rule change |
|-----|---------|----------------------|
| 1984–94 | 1983–84 → 1993–94 | Illegal-defense rules (no zone defense) |
| 1995–01 | 1994–95 → 2000–01 | Hand-checking restrictions; zone still illegal |
| 2002–04 | 2001–02 → 2003–04 | Zone defense legalized; defensive three-seconds added |
| 2005–17 | 2004–05 → 2016–17 | Perimeter hand-checking banned (the pace-and-space era) |
| 2018–22 | 2017–18 → 2021–22 | Freedom-of-movement emphasis |
| 2023–26 | 2022–23 → 2025–26 | Transition take-foul rule |

Whether any of these rule changes caused the decline is a separate question, taken up in Section 4. For now they are just the calendar the rest of the report runs on.

---

## 2. What Creates Home Court Advantage

A handful of concrete things have historically given home teams an edge on any given night: referees calling fewer fouls on them, a shooting advantage, favorable shot selection, and an advantage on the glass and in turnover differential. Rest and altitude add to the picture for specific matchups.

**Referee foul calls.** Across every era and in both regular season and playoffs, referees have called fewer fouls on home teams. In the 1984–94 regular season, home teams averaged about 1.2 fewer foul calls per game. In the playoffs the gap was even wider. Referees favored home teams by about 1.6 fouls per game. With fouls go free throws, and with free throws go points. This is the most consistent component of home court advantage.

The playoff referee data shows how universal this is: 45 of 47 officials with at least 50 playoff games on record show a home-favoring foul differential. Nearly every referee who has worked the postseason has called the game differently depending on which team was at home.

**Shooting advantage.** Home teams have consistently shot better than road teams: typically around a percentage point better in effective field goal percentage across most eras in both regular season and playoffs. The usual explanations are crowd comfort and familiar rims. Our data can only confirm the gap is real, not pin down the cause.

**Shot selection.** Historically, home teams have gotten more of their attempts from close range and fewer from mid-range. A paint shot is more efficient than a mid-range jumper, so home teams have started each possession with a small built-in advantage in expected scoring. This edge was clearest in an era when three-point attempts were rare. As three-point shooting took over, it gradually eroded this home advantage, in ways Section 3 covers.

**Rebounding and turnover differential.** Home teams have historically pulled down more rebounds and committed fewer turnovers: about one and a half extra boards and just over a third of a turnover per game. Neither is dramatic on its own, but both hand the home team extra possessions. Together they rival the shooting advantage in size. As Section 3 will show, this pair turns out to be the single largest driver of the decline.

![Home minus away differentials over time for six shooting and foul categories: foul calls per game, FG%, eFG%, 3PA rate, 3P%, and FT%. Each panel includes trend lines; a trend toward zero means that component of the home-team edge is narrowing. The rebounding and turnover differentials are covered in Section 3.](../generated/nba_home_court_advantage_differentials.png)

**It all shows up in the box score.** The four box-score categories, shooting, rebounding, foul calls, and turnover differential, account for about 95% of the entire home advantage in the regular season, and a similar share in the playoffs. Shooting is the single biggest piece, more than 40% of it, followed by rebounding. Whatever the crowd and the familiar rims do, it reaches the scoreboard almost entirely through these measurable categories.

---

## 3. What's Driving the Decline

The same categories that make up home court advantage are the ones lessening over time. 

This chart splits both home court and its 40-year decline across the four box-score categories: shooting, rebounding (offensive and defensive combined), foul calls, and turnover margin. The left panel is what creates the advantage; the right is what's eroding it. The rest of this section walks each category in turn, with the precise shares tallied at the end.

![Box-score category shares of the home-court advantage and of its decline, regular season vs. playoffs. Rebounding here is total boards (offensive + defensive); the OREB and DREB breakdown is in the rebounding chart further below. The left panel is what creates the advantage; the right is what's eroding it. Bars sum to 100% by accounting identity.](../generated/nba_home_court_mediation.png)

**Referee foul bias has narrowed.** The home foul differential in the regular season has dropped from 1.2 fouls per game in the 1980s to roughly a quarter of a foul per game today, an 80% reduction. In the playoffs it has fallen from 1.6 to 0.7. The advantage referees once gave home teams has fallen by about 80% in the regular season and significantly diminished in the playoffs.

The playoff referee chart shows the generational shift clearly. The distribution across officials has compressed over time, not just shifted. Newer referees are not only less biased on average; they are also more uniform in their calling. Per-official records are available from 1995 onward; the 1984–94 baseline figures above come from the aggregate box-score foul differential visible in Section 2's differentials chart.

Three-point shooting played a direct role too. Three-point attempts draw fewer fouls than drives to the basket. As both teams moved toward the perimeter, there were simply fewer foul calls to go around, and the home team's absolute gap shrank with it. About half of the foul decline traces to this mechanical shift in shot selection; the other half reflects genuine change in how referees call the game.

![Distribution of per-official home foul bias by era, playoffs. The spread has compressed: newer officials are not only less biased on average but more uniform in their calling. Chart covers 1995 onward, the earliest era with sufficient per-official playoff data.](../generated/nba_home_court_referee_era.png)

**The shooting line registers the three-point shift.** The league's move to the perimeter changed shot selection in two visible ways. First, away teams have closed the gap in paint attempts: in the 1990s home teams generated about 1.3 percentage points more of their attempts from close range than road teams; by 2023–26 that gap has shrunk to 0.2 points. Second, three-point volume itself rose for everyone. When three-point shooting rates are the same across seasons, both effects disappear: the eFG% convergence reverses, and the shooting channel turns from a decline into an improvement. The paint gap closing is part of the three-point story, not a separate cause on top of it. In the playoffs the paint gap narrowed in the late 2010s but has since rebounded close to its old level, making this a regular-season story for now.

![Shot zone differentials (home minus road) over time, regular season vs. playoffs. Four panels: paint, mid-range, corner 3, and above-break 3. The paint panel is the key one: the gap has nearly closed, meaning away teams now get close-range attempts at nearly the same rate as home teams. The three-point panels show little differential throughout.](../generated/nba_home_court_shot_zones.png)

**The three-point revolution, sized.** The league's three-point attempt rate and the home win rate have moved in opposite directions for 40 years. When 7% of shots were threes in the 1980s, home teams won 65%; when 40% are threes today, they win 55%. The timing lines up with the second sharp drop: the three-point share rose from about a quarter to nearly half of all shots in the three seasons after 2017, exactly when that drop began.

That 40-year lockstep looks convincing, but a tighter test exposes its limits. If three-point volume were actually causing home court to fall, last season's rate should help predict this season's home win rate. It doesn't. After adjusting each series for its own long-run trend, the season-level correlation shrinks from −0.90 to −0.53: roughly 40% of that striking visual is two trends moving in the same direction over time, not one driving the other.

The reliable evidence is within a single season: games in which both teams collectively attempt more threes are games home teams lose more often, at roughly 2–3 fewer wins per 100 games for every 10-point rise in three-point volume. That link holds within each era, not just across the full 40-year span, and it appears in both the regular season and the playoffs.

The three-point shift works through a specific category: the shooting line of the box score. When three-point rates are low, the home shooting advantage holds up; as they rise, the advantage shrinks. Shooting accounts for roughly one-fifth of the regular-season decline. The larger share, more than half, runs through rebounding and turnover differential. After accounting for three-point volume, the rebounding decline barely moves; the turnover decline is about half explained by the perimeter shift. Three-point shooting is a real force on one category, not the engine behind the whole decline. In the playoffs the within-season signal is weaker, since team quality swamps stylistic factors, but it still points the same direction.

![Three panels. Left: dual-axis time series showing the 40-year lockstep between rising three-point volume (right axis) and falling home win % (left axis) in the regular season. Center and right: scatter of one season per point for regular season and playoffs, era-colored, showing the same inverse relationship.](../generated/nba_home_court_3pa.png)

**Rebounding, the biggest contributor.** The home team's rebounding advantage has shrunk steadily for 40 years. Unlike the shooting advantage, it is not the three-point story in disguise. When three-point volume is accounted for, the home shooting advantage vanishes entirely, while the rebounding advantage barely moves.

Both sides of the glass show declining home advantages, and the raw numbers are larger than the offensive-rebound story alone suggests. The home advantage on defensive rebounds fell from +1.64 boards per game in the 1980s to +0.59 today, a drop of about 1.0 board. The home advantage on offensive rebounds fell from +0.61 to slightly below zero, a drop of about 0.7 boards. The defensive side actually fell more in absolute terms.

Some of that defensive decline, though, is a consequence of the shooting improvement already captured in the shooting channel: if away teams miss fewer shots, there are simply fewer defensive rebounds available for the home team to grab. Offensive rebounding, measured as each team's share of available offensive boards, is the cleaner test of whether home teams are actually crashing the glass more aggressively, because it does not change just because one team shoots better.

On that cleaner measure, the asymmetry is clear. In the mid-1980s, home teams converted about 34% of their offensive rebounding chances; away teams converted about 31%. Both rates fell as the league moved away from crashing the glass, but the home rate dropped 8 percentage points while the away rate dropped only 5. The two lines converge and cross by 2025–26. The edge didn't close because away teams became better offensive rebounders. Home teams stopped crashing the offensive glass more aggressively than visitors.

**Why home teams retreated from the offensive glass faster than away teams is not something this data can answer.** The most commonly offered explanation in basketball circles is strategic: teams increasingly chose transition defense over second chances, and the three-point revolution may have reinforced that calculus since longer shots scatter to less predictable spots. One possibility is that crowd noise and a familiar building historically encouraged extra hustle on the offensive glass, and as the league-wide retreat from crashing took hold regardless of venue, that motivational lift had nowhere to express itself. These are plausible explanations, not conclusions this analysis can establish.

The home turnover advantage has eroded too, about half of it independent of the perimeter shift. The data can't explain why. Improved scouting and video preparation are the most plausible contributors: visiting teams are better prepared for unfamiliar defensive schemes than they once were. But that is hypothesis, not something this analysis can establish. The playoffs point the same way: the home rebound-share advantage has fallen by roughly three-quarters there too. With a fifteenth as many games, the playoff evidence is consistent with the regular-season story rather than established on its own.

![Why the home rebounding advantage faded. Left: home and away OREB rates (% of available offensive boards) over time; both fell, but the home rate dropped 8 pp (34% to 26%) while the away rate dropped only 5 (31% to 26%), causing the lines to converge and cross. Center: raw OREB and DREB differentials (home minus away per game) over time; both declined, with the defensive edge falling more in absolute terms. Right: seasons with a larger total home rebounding edge tend to be seasons where home teams win more (association, not causation).](../generated/nba_home_court_rebounding.png)

Player-tracking cameras, deployed in 2013–14, confirm the final chapter. The home advantage in converting offensive-rebound chances kept shrinking through the entire tracking era, falling from about 1.5 percentage points in the mid-2010s to under 0.2 today. Home teams have held no measurable box-out advantage throughout the tracking window. By the time the cameras arrived, most of the decline had already happened; the tracking data confirms the mechanism is still running.

![The modern player-tracking view of the home rebounding advantage (2013–14 on). Left: the home advantage in converting offensive-rebound chances keeps shrinking, falling from about 1.5 percentage points in the mid-2010s to under 0.2 today. Center: home teams hold no measurable box-out advantage. Right: the second-chance-points advantage shows little change across this window. A short window that corroborates the modern mechanism, not the 40-year decline.](../generated/nba_home_court_rebounding_tracking.png)

**Adding it up.** The four box-score categories together account for roughly 96% of the entire regular-season decline. The two most-discussed categories explain about 21% and 18%: shooting (eFG%), where the three-point shift registers, including its effect on paint shot selection, and the narrowing whistle. Rebounding and turnovers carry the most: roughly 30% and 27%, together more than half the drop. In the regular season, almost nothing is left over, and all four trends hold up under statistical testing. (These are accounting shares showing where the decline registers in the box score, not a claim about ultimate causes.)

The playoffs don't close as neatly, and the playoff evidence is thinner throughout. With about 3,300 playoff games across 40 seasons compared with 49,000 in the regular season, the overall playoff trend carries roughly four times the uncertainty of the regular-season estimate. The same four categories capture only about 67% of the decline, leaving roughly a third unaccounted for. Only the foul and rebounding trends are statistically solid; the shooting and turnover trends can't be told apart from noise. The postseason breakdown is best read as consistent with the regular-season story, not independently proven.

Could rebounding and turnovers just be the three-point shift in disguise? No. When games with similar three-point rates are compared directly, the **shooting** decline not only disappears but reverses: in games where three-point volume is similar, the home team's shooting edge was actually improving over the same 40 years. The observed convergence is entirely the perimeter story, and then some. The **rebounding** decline barely moves and stays the surest of the four. Fouls and turnovers each land in between: roughly half of each channel's trend is explained by rising three-point volume, leaving the other half independent of the perimeter shift. The categories doing the most work to drag home court down — rebounding and the three-point-independent half of turnovers — are doing it for reasons the three-point boom does not explain. (In the playoffs the same test is too noisy to read; only the rebounding decline clears the bar. So this is a regular-season verdict.)

![Does each category's decline survive after accounting for three-point volume? Each bar is the share of that category's yearly decline that remains once three-point volume is accounted for: 100% means the decline has nothing to do with three-point shooting, 0% means it is entirely the three-point story, below zero means the advantage actually reverses. In the regular season the shooting decline not only disappears but reverses, while the rebounding decline is essentially untouched; the playoff bars are mostly small-sample noise (greyed), with only rebounding holding up.](../generated/nba_home_court_3pa_control.png)

---

## 4. What Didn't Drive the Change

The Section 1 chart shows six labeled eras, each marking a rule change. It would be natural to read those era boundaries as explaining where home court bent. They mostly don't. Test each boundary against the trend line and only 1994–95 registers: a genuine one-time drop of about 2.6 points, most likely from the hand-checking crackdown (though the simultaneously shortened three-point line adds some ambiguity). The reason only that one boundary registers is specific: hand-checking affected referee discretion, and referee behavior is one of the few things that can shift asymmetrically between home and away teams. Every other rule change — zone legalization, the 2004-05 perimeter hand-check ban, freedom of movement, the take-foul rule — reshaped how the game looks without reshaping who benefits from playing at home. In the playoffs, even 1994–95 doesn't register; the postseason slide is steady drift throughout.

The situational factors test out as flat or too small to carry the explanation. Travel distance matters at about 0.07 percentage points per 100 miles in the regular season — negligible — and has no measurable effect in the playoffs. Time zones are flat in both. Rest creates genuine variation (home teams win 63% when better-rested, 58% when the visitor has the edge) but that gap hasn't changed across eras. Load management cut back-to-back frequency from 35% to under 20%, which is real, but a shift-share decomposition shows that schedule change accounts for only 8% of the decline; home advantage eroded within every rest situation alike. Pace of play, competitive balance, and the home-vs-away three-point differential all show no meaningful relationship to the trend.

Crowds have stayed near capacity throughout — record highs in the 2020s, the very years home court hit its lowest — so crowd size is not the dial. Crowd *presence* is different. The 2020-21 pandemic seasons ran an accidental test: with buildings empty, home teams won just 51%; with any crowd at all, they won 58.5%. A crowd is a genuine ingredient of home court, worth about seven points on the night. But it is a switch that flips with the doors, not a 40-year dial slowly turning down. A combined model stacking all situational factors confirms it: after accounting for rest, altitude, time zones, and COVID seasons, the remaining explanatory power belongs entirely to which era the game was played in — the decline itself, not any off-court factor. The full treatment of each hypothesis, including why each seemed plausible and exactly what the data showed, is in [The Investigation](home_court_investigation.html).

![Left: league average attendance per game vs. regular-season home win %, 2000–2026, with crowds holding near capacity (and lately setting records) while home court keeps falling. Right: 2020–21 home win % by game attendance, where an empty arena erases the advantage that even a small crowd restores.](../generated/nba_home_court_attendance.png)

---

## 5. The Playoff Picture

The playoffs are not a shrunken version of the regular season. They have their own structure, their own baseline, and their own timeline of decline.

**Home court is the strongest predictor of playoff game outcomes.** Across all eras, the single strongest predictor of a playoff game outcome is which team has home court. Games 1 and 2, at the higher seed's arena, go to the home team 69% and 72% of the time. Games 3 and 4, at the lower seed's arena, are barely better than coin flips for the team playing there (55–56%). Game 5, back at the top seed, is the most lopsided of all: 74.5%. Even Game 7 still goes to the home team 64% of the time. Road teams show no evidence of adapting as a series deepens.

![Two panels. Left: playoff home win % for each game within a series (G1 through G7), all eras combined, with a reference line at the overall playoff average. G5, back at the top seed's arena, is consistently the most lopsided. Right: the same G1–G7 breakdown broken out by era, one line per era.](../generated/nba_home_court_series_breakdown.png)

**The playoff decline is real home-court weakening, not weaker seeds.** A natural objection: maybe playoff home teams win less now simply because top seeds no longer outclass their opponents the way they once did. The data says no. Account for the regular-season quality gap between the two teams and the year-by-year playoff decline doesn't budge. None of it is explained by seeds bunching together. The cleanest proof: when the objectively weaker team hosts Games 3 and 4, it still wins 51.5% of the time. Home court alone is still worth a coin-flip-beating advantage, and that advantage is what has been eroding.

![The playoff decline is genuine home-court weakening, not weaker seeds. Left: the yearly playoff decline is the same size before and after removing the regular-season quality gap between the two teams (quality explains essentially none of it). Right: home win % by who hosts, where even the objectively weaker team still wins about 51.5% of its home games (Games 3–4), a pure venue effect above the coin-flip line.](../generated/nba_home_court_playoff_quality.png)

**The 2014 format change didn't cause the playoff drop.** The playoffs have been restructured over the years, in four distinct format periods:

| Period | Seasons | Format |
|--------|---------|--------|
| 1984 | 1983–84 | Best-of-5 first round; 2-2-1-1-1 Finals |
| 1985–02 | 1984–85 → 2001–02 | Best-of-5 first round; 2-3-2 Finals |
| 2003–13 | 2002–03 → 2012–13 | Best-of-7 first round; 2-3-2 Finals |
| 2014–26 | 2013–14 → 2025–26 | Best-of-7 first round; 2-2-1-1-1 Finals |

The most recent shift, in 2014, coincided with the sharpest period of playoff HCA decline: a nearly 7-point raw drop from the 2003–13 period to the 2014–26 period. But when the year-by-year secular trend is accounted for, the format change has no independent effect. The playoff drop would have arrived on roughly the same schedule regardless. Format was not the cause.

![Home win % averaged over each playoff format period, for both the regular season and the playoffs. The regular season never changed format, so the fact that both series decline at similar rates across the same periods means the format change is not driving the playoff drop.](../generated/nba_home_court_advantage_format_bars.png){width=50%}

Additional findings, including individual referee rankings, franchise-level comparisons, and the blowout-margin trend, are in Appendix C.

---

## 6. Summary

Home court advantage in the NBA has dropped about 10 percentage points over 40 years. The regular season went from 65% to about 55%; the playoffs from nearly 68% to 58%.

The decline is real and one-directional: a slow, four-decade erosion with two sharper drops layered on it. The first traces to the 1994–95 rule change, most likely the hand-checking crackdown, whose full adjustment played out through the late 1990s. The second is the post-2017 perimeter shift, which shows up in the shooting line of the box score. Neither is the whole story. The data points to four main explanations that together account for about 96% of the regular-season decline:

**Referees are calling fairer games, and three-point shooting is pulling the gap further down.** The systematic home-team foul benefit was 1.2 fouls per game in the regular season and 1.6 in the playoffs in the 1980s. It has shrunk to roughly a quarter of a foul per game in the regular season and 0.7 in the playoffs. About half of that foul decline is a direct consequence of three-point shooting: shots from the arc draw fewer fouls than drives to the basket, so as both teams moved to the perimeter, there were fewer foul calls to go around. The other half is genuine change in how referees officiate, and it shows up universally: 45 of 47 playoff officials with at least 50 games on record call fewer fouls on the home team.

**Three-point shooting drove about 21% of the decline, through two related effects.** The first is paint-shot convergence: as three-point volume rose, away teams closed the gap in close-range attempts, erasing a shot-quality edge home teams once carried into every possession. The gap in paint-shot rate fell from 1.3 percentage points in the 1990s to 0.2 today. The second is three-point volume itself: when three-point rates are low, the home shooting advantage holds up; as they rise, the advantage shrinks. The 40-year correlation between three-point volume and home win rate is the most striking visual in the dataset, but the reliable evidence is within a single season: games with more threes go against home teams even among contemporaries, not just across decades.

**The biggest driver of all: the rebounding advantage eroded on both sides of the glass.** The home team's hold on the boards has slipped over 40 years, independently of the three-point boom. The home advantage on defensive rebounds fell from +1.64 boards per game to +0.59; the home advantage on offensive rebounds fell from +0.61 to slightly below zero. The defensive edge fell more in absolute terms, though part of that decline is a consequence of away teams shooting better over time (fewer misses means fewer defensive boards for the home team). The cleaner measure is the offensive rebounding rate: home teams' share of available offensive boards dropped 8 percentage points (34% to 26%) while away teams' dropped only 5 (31% to 26%). The offensive edge closed because home teams stopped crashing more aggressively, not because away teams improved. The home turnover advantage has partly followed, and the same pattern holds in the playoffs. **What drove these changes is not something this analysis can establish.** Strategic shifts toward transition defense, improvements in visiting-team preparation, and the perimeter revolution are all plausible contributors, but they are hypotheses, not conclusions from this data.

What hasn't driven the decline: rule changes (with the single exception of 1994–95), travel, time zones, pace of play, competitive balance, crowd size, and playoff scheduling format. The data rules each out. The schedule-spread argument with fewer tired visitors, explains only about 8% of the decline. Arenas have stayed near capacity, lately setting records, even as the advantage shrank. The one genuine crowd effect is a blip: in the empty arenas of 2020–21 home teams won just 51%, then snapped back to 58.5% whenever fans returned. Crowd noise is real and measurable, but it's a switch that flips with the doors, not a dial slowly turning down for 40 years.

The playoffs have followed the regular season's path but with nearly a two-decade lag. With roughly 3,300 playoff games over 40 seasons compared with 49,000 in the regular season, the playoff trend is measured with considerably less precision, though its direction is not in doubt. For most of the 2000s and 2010s, postseason home court held firm even as the regular season eroded around it. The internal structure of playoff home court remains stark: Games 1 and 2 go to the home team 69% and 72% of the time; Game 5 is the most lopsided at 74.5%; even Game 7 still goes to the home team 64% of the time. Since 2018 the decline has accelerated. It is genuine home-court erosion, not an illusion of more evenly matched seeds. Even the weaker team, when it hosts, has been winning less.

---

## Appendix A: Companion Documents

::: {.content-visible when-format="html"}
| Document | Description |
|---|---|
| [Regression Results](nba_home_court_results.html) | Full statistical output from the analysis pipeline: regression tables, significance tests, and coefficient values for every analysis in this report. |
| [The Investigation](home_court_investigation.html) | Full treatment of every ruled-out hypothesis: why each seemed plausible, what was tested, and what the data showed. |
| [One-Page Summary](home_court_summary.html) | Standalone summary built around the three core charts and the three questions. |
| [Stats Explainer](home_court_stats_explainer.html) | Guide to the statistical methods used, written for a general audience. |
| [Stats Tutorial](../../generated/stats_tutorial.html) | Worked examples reproducing key results from the regression output. |
:::

::: {.content-visible when-format="typst"}
All files are in the same folder as this PDF (`generated/`), except the Stats Tutorial which is one level up in `../generated/`.

| Document | File | Description |
|---|---|---|
| Regression Results | `nba_home_court_results.pdf` | Full statistical output: regression tables, significance tests, and coefficient values for every analysis in this report. |
| The Investigation | `home_court_investigation.pdf` | Full treatment of every ruled-out hypothesis: why each seemed plausible, what was tested, and what the data showed. |
| One-Page Summary | `home_court_summary.pdf` | Standalone summary built around the three core charts and the three questions. |
| Stats Explainer | `home_court_stats_explainer.pdf` | Guide to the statistical methods used, written for a general audience. |
| Stats Tutorial | `../generated/stats_tutorial.pdf` | Worked examples reproducing key results from the regression output. |
:::

---

## Appendix B: Independent Corroboration

Sparkle Technologies published an independent analysis of the same question at [sparkletechnologies.com/blog/nba-disappearing-home-court-advantage](https://sparkletechnologies.com/blog/nba-disappearing-home-court-advantage). We checked every number we share in common. Most of them match. The disagreements are instructive.

**Where we agree.** The overall decline, the foul-call story, the irrelevance of travel and pace: all consistent across two independent pipelines. The clearest confirmation that neither analysis is fabricating results: the Sparkle altitude figures for Denver and Utah land within a tenth of a point of ours.

**Where we differ, and why.** The blog names the three-point revolution as the primary cause, drawing on a 40-year correlation of −0.88 between three-point attempt rate and home win percentage. We ran a tighter test and found roughly 40% of that correlation is two trends moving in the same direction over time, not one causing the other. The three-point effect is real, showing up within individual seasons too, but it accounts for about 21% of the regular-season decline, not the majority. The two categories the blog never measures, rebounding and turnovers, carry more than half the decline between them.

On the mid-1990s drop, the blog attributes it to the shortened three-point line (1994–97); we attribute it to the hand-checking crackdown. Both changes happened in the same seasons. The channel event study gives some traction: foul calls responded immediately and significantly at the 1994-95 boundary while the shooting channel showed no significant immediate response, pointing more toward hand-checking. The two are not fully separable, but hand-checking is the more consistent explanation with the data.

The empty-arena numbers look different for a methodological reason. The blog's "empty arena" figure (54.4%) is the 2020–21 season average, blending games with zero fans and games with partial crowds. We split those apart: 51.0% with empty buildings, 58.5% with any crowd at all. No real disagreement on the conclusion (crowd presence is a switch, not a dial), but the blog's single number averaged over the whole phenomenon.

**What the blog found that we then tested.** The blog credited the schedule shift, fewer visitors arriving on a back-to-back, with 15–20% of the decline. The premise checks out: back-to-back frequency fell from about 35% to under 20%. The magnitude doesn't hold. A direct shift-share test puts the schedule effect at roughly 8% of the decline. The other 92% is the home advantage eroding within every rest situation alike, regardless of how tired the visitor is.

**What we found the blog missed.** The rebounding collapse is the biggest gap. The blog's box-score account has no rebounding term; we find it is the single largest category, carrying 30% of the regular-season decline, and it holds up after accounting for three-point volume. Turnover-edge erosion (another 27%) is also unaccounted for. The blog's decomposition points at something real. It just misses where most of the work is happening.

---

## Appendix C: Additional Findings

A few results surfaced along the way that don't bear directly on the three questions but are worth noting.

**Referees differ in home-court bias, but less than the raw numbers suggest.** Of 47 officials with at least 50 playoff games, 45 call fewer fouls on the home team. The most home-leaning on record, Ron Garretson, Joe Crawford, and Eddie Rush, sit close to a full foul per game apart from the most even-handed, a group that includes Tony Brothers, Josh Tiven, and Joe Forte. About 60% of that raw spread is small-sample noise. Referees genuinely differ, but the gap between them is narrower than the leaderboard suggests. This measures tendencies, not proof that any one official decides games.

![Top/bottom 15 referees ranked by home foul differential (≥50 playoff games). Values are shrunken estimates: raw differences shrink toward the league mean to account for sample size.](../generated/nba_home_court_referee_rankings.png)

**Denver and Utah have the largest home-court advantages in the league, likely because of altitude.** Across 40 seasons, the Nuggets and Jazz hold the largest regular-season home advantages of any franchise: about 27 and 26 percentage points above their own road win rates, against a league average near 20. Both play at altitude. The franchise spread is real: roughly 70% of the variation across teams reflects genuine differences, not noise. Altitude sits right at the top of it. With only two high-altitude franchises, elevation can't be fully separated from whatever else is unique to those teams, but it is the most plausible common thread. (The 27-point figure is their full home-minus-road gap; the altitude piece on its own, from Section 4, accounts for about 8 of those points.)

![Franchise home court advantage, regular season and playoffs. Bars and points carry 95% confidence bands: in the regular season most franchises sit clearly apart, but in the playoffs the bands are wide and overlapping, so the franchise differences there are mostly noise.](../generated/nba_home_court_team_hca.png)

**The decline is universal, but some franchises fell much further than others.** Splitting the 40-year record at 2001–02, the league average dropped from about 25.6 percentage points to 17.6. Every one of the 26 franchises with at least 400 home games in both halves declined. Sacramento and Phoenix fell the most, each dropping about 16 points; both had been near the top of the league in the 1980s and 1990s and are now near the bottom. The Knicks shed 13 points. At the other end, the Los Angeles Lakers barely moved at all (a drop of under 1 point), though they started below the league average and remained there. Denver and Utah both declined substantially (11 and 8 points respectively) but still sit at the top of the late-era rankings. The pattern is consistent with compression: franchises that had the most home-court edge in the early era had more room to lose.

![Franchise HCA in the early era (1984–2001, blue) and recent era (2002–24, green), sorted by early-era HCA. Every franchise shifted left. The dashed vertical lines mark the league average in each era.](../generated/nba_home_court_team_hca_era.png)

**In the playoffs, every franchise's home court looks the same.** That real regular-season spread vanishes in the postseason. With fewer than 150 playoff home games on record for most franchises, the apparent gaps are entirely explained by small samples. The true spread between franchises is statistically indistinguishable from zero. A team's apparent postseason home-court strength mostly reflects being a good team. Good teams simply play more home games.

**Home court is worth more in the playoffs than in the regular season.** Among franchises with both records, home court is worth about 20 points in the regular season but 27 in the playoffs, a 7-point premium. Teams that protect their building in the regular season tend to do so in the playoffs as well, but only loosely. The crowd, the stakes, and the familiar floor count for more when the games matter most.

**The blowouts are getting bigger, even as home teams win less.** As home court advantage has declined, the margin when the home team *does* win has grown. Home wins are more lopsided; home losses are worse. Track the full spread of margins regardless of who won: the gap between the biggest wins and biggest losses widens by about 0.2 points per year in the regular season and 0.3 in the playoffs. In the regular season blowouts grow in both directions; in the playoffs the spread widens mainly because the big home wins keep getting bigger. Fewer home wins overall, but the ones that happen are more decisive.

![Three panels. Left: mean all-game point margin per season for regular season and playoffs. Center: mean win margin and mean loss margin per season (regular season); the two lines diverging means the average home win is getting bigger while the average home loss is getting worse. Right: the same by era.](../generated/nba_home_court_margin.png)
