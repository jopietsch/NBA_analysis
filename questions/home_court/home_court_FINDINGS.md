# NBA Home Court Advantage — Findings

Home court advantage in the NBA has been shrinking for four decades, and this report sets out to answer what has changed and why. **Has it really changed?** **What makes home court an advantage in the first place?** And **what's driving the decline — and, just as important, what isn't?**

Yes: the home team's win rate has fallen from about 65% to 55% in the regular season, and from nearly 68% to 58% in the playoffs. Most of that fall is slow, steady erosion, with two sharper drops layered on top. The structural advantages home teams once relied on have worn away: at the whistle, in shot selection, in the move to the three-point line, and on the glass. The biggest surprise is where the largest share of the decline came from: not the expected factors, the narrowing whistle and the three-point shift, but the collapse of the home team's grip on the offensive boards.

What is *not* behind it is also interesting: rule changes, travel, time zones, pace of play, competitive balance, crowd size, and the playoff format changes, including the much-blamed 2014 change. Each one is tested here, and each one is ruled out.

Throughout, the regular season and the playoffs are tracked separately. They share a direction but not a timeline. The analysis covers 52,000 regular-season and playoff games; the underlying statistical tables are in the appendix.

---

## 1. The 40-Year Decline
The drop unfolded at roughly a quarter of a percentage point per year. The playoffs tell the same story with a slight lag. The postseason home win rate peaked near 68% in the 1980s before sliding to 58% today. That's a 9-to-10-point drop, comparable to the regular season but noisier given fewer games.

![Figure 1. Regular season vs. playoff home win % per season, 1983–84 through 2025–26. Dashed lines are overall trend fits; background shading marks rule-change eras.](generated/nba_home_court_advantage_season.png)

Two things are happening at once. The first is a **slow, continuous erosion** of about a quarter of a point per year, driven by the box-score categories in Section 3 grinding down gradually. The second is **two sharp drops** layered on top.

The first sharp drop came in the mid-to-late 1990s, when regular-season home win % fell from about 65% to 60%, the steepest move in the dataset. The line then held roughly flat for nearly two decades before a second drop, beginning after 2017, pushed it below 56%.

Neither drop is a separate cause stacked on top of the trend. Each is a moment when one specific force shoved the same trend harder. The first traces to the 1994–95 rule change (Section 4). The second coincides with the three-point revolution: the share of shots from deep leapt from about a quarter to nearly half in the three seasons after 2017. That shift accelerated the decline, but it's a marker of a broader move to the perimeter, not the whole explanation.

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

A handful of concrete things have historically given home teams an edge on any given night: referees calling fewer fouls on them, a shooting advantage, favorable shot selection, and an underrated advantage on the glass and in turnover differential. Rest and altitude add to the picture for specific matchups.

**Referee foul calls.** Across every era and in both regular season and playoffs, referees have called fewer fouls on home teams. In the 1984–94 regular season, home teams averaged about 1.2 fewer foul calls per game. In the playoffs the gap was even wider. Referees favored home teams by about 1.6 fouls per game. With fouls go free throws, and with free throws go points. This is the most consistent component of home court advantage.

The playoff referee data shows how universal this is: 45 of 47 officials with at least 50 playoff games on record show a home-favoring foul differential. Nearly every referee who has worked the postseason has, consciously or not, called the game differently depending on which team was at home.

**Shooting advantage.** Home teams have consistently shot better than road teams: better than a percentage point in field goal percentage, with a similar gap in effective field goal percentage, across all eras in both regular season and playoffs. The usual explanations are crowd comfort and familiar rims. Our data can only confirm the gap is real, not pin down the cause.

**Shot selection.** Historically, home teams have gotten more of their attempts from close range and fewer from mid-range. A paint shot is more efficient than a mid-range jumper, so home teams have started each possession with a small built-in advantage in expected scoring, independent of how well they shoot from any given spot.

**Rebounding and turnover differential.** Home teams have historically pulled down more rebounds and committed fewer turnovers: about one and a half extra boards and just over a third of a turnover per game. Neither is dramatic on its own, but both hand the home team extra possessions. Together they rival the shooting advantage in size. As Section 3 will show, this unglamorous pair turns out to be the single largest driver of the decline.

![Figure 3. Home vs. away box-score differentials — foul rate, FG%, eFG%, 3PA rate, 3P%, FT%.](generated/nba_home_court_advantage_differentials.png)

**It all shows up in the box score.** The four box-score categories — shooting, rebounding, foul calls, and turnover differential — account for about 95% of the entire home advantage in the regular season, and a similar share in the playoffs. Shooting is the single biggest piece, more than 40% of it, followed by rebounding. Whatever the crowd and the familiar rims do, it reaches the scoreboard almost entirely through these measurable channels.

**Rest and altitude.** When the home team enters a game better rested, they win about 63% of the time, three points above the league baseline. When the visitor is better rested, the home win rate drops to 58%. This effect has been consistent across all eras. Denver and Utah, playing at altitude, add nearly 8 percentage points above the league average to their regular-season home win rates. That altitude edge is real, and largely absent in the playoffs, where opponents have had a full series to adjust. Playoff rest is similarly muddled: a team with extra rest between rounds is usually the one that swept or won quickly, meaning it's probably also the better team. Control for team quality and the rest advantage shrinks to nothing.

![Figure 4. The two situational advantages. Left: home win % by rest situation — in the regular season home teams win about 63% when they are the better-rested side and 58% when the visitor is (the playoff buckets are small-sample and confounded by team quality, as the text notes). Right: the two altitude franchises, Denver and Utah, beat the league's home win rate by roughly 8 points in the regular season — an advantage that disappears in the playoffs.](generated/nba_home_court_rest_altitude.png)

---

## 3. What's Driving the Decline

The same advantages that create home court advantage are the ones eroding over time. Three changes lead the story — and the one carrying the most weight is the one that never made the headlines.

**Referee foul bias has narrowed sharply.** The home foul differential in the regular season has dropped from 1.2 fouls per game in the 1980s to roughly a quarter of a foul per game today, an 80% reduction. In the playoffs it has fallen from 1.6 to 0.7. The advantage referees once gave home teams has nearly vanished in the regular season and significantly diminished in the playoffs.

The playoff referee chart shows the generational shift clearly. The distribution across officials has compressed over time, not just shifted. Newer referees are not only less biased on average; they are also more uniform in their calling.

![Figure 5. Referee home foul bias by official and era, playoffs.](generated/nba_home_court_referee.png)

**The shot zone advantage has evaporated.** In the 1990s, home teams generated about 1.3 percentage points more of their attempts from the paint than road teams. By 2023–26, that gap has shrunk to 0.2 points. Away teams now attack the basket nearly as aggressively as home teams. Our data can confirm the gap closed, not why. In the playoffs the gap narrowed in the late 2010s but has since rebounded close to its old level. Shot-selection convergence is, for now, a regular-season story.

![Figure 6. Shot zone differentials (home minus road), regular season vs. playoffs.](generated/nba_home_court_shot_zones.png)

**The three-point revolution.** The league's three-point attempt rate and the home win rate have moved in opposite directions for 40 years. When 7% of shots were threes in the 1980s, home teams won 65%; when 40% are threes today, they win 55%. The timing lines up with the second sharp drop: the three-point share leapt from about a quarter to nearly half of all shots in the three seasons after 2017, exactly when that drop began.

That 40-year lockstep looks convincing, but two long-run trends will always correlate strongly whether or not one causes the other. Statistical tests suggest this one is likely spurious at the season level. The reliable evidence is within a single season: games in which both teams collectively attempt more threes are games home teams lose more often, at roughly 2–3 fewer wins per 100 games for every 10-point rise in three-point volume. That link holds even after the long-run trend is stripped away, and it appears in both the regular season and the playoffs.

The three-point shift works through a specific channel: the shooting line of the box score. Hold three-point volume constant and the home shooting advantage holds up; let volume rise and it shrinks. Shooting accounts for roughly one-fifth of the regular-season decline. The larger share, more than half, runs through rebounding and turnover differential, which barely move when three-point volume is controlled. Three-point shooting is a real force on one channel, not the engine behind the whole decline. In the playoffs the within-season signal is weaker, since team quality swamps stylistic factors, but it still points the same direction.

![Figure 7. League three-point attempt rate vs. home win %, regular season and playoffs.](generated/nba_home_court_3pa.png)

**The fourth strand — and the biggest driver: the glass.** The home team's rebounding advantage has shrunk steadily for 40 years. Unlike the shooting advantage, it is not the three-point story in disguise. Hold three-point volume constant and the home shooting advantage vanishes entirely, while the rebounding advantage barely moves. The answer is in the split between offensive and defensive boards.

The home advantage on the **defensive** glass has only softened. The advantage on the **offensive** glass has collapsed. It fell from about six-tenths of a rebound per game in the 1980s to slightly below zero today. Home teams no longer attack the offensive boards harder than visitors.

This isn't a trick of pace or shot volume. Measured as the home team's share of available rebounds, the advantage shrank roughly tenfold, from about two percentage points to a fifth of one. It lines up with a well-documented strategic shift: the league-wide offensive-rebound rate fell from 33% to 26% over the same span, and the season-by-season correlation between the two is 0.82. Teams stopped crashing the boards to get back on defense, and the home advantage faded with that retreat. The frantic scramble for offensive boards, exactly the kind of effort a roaring crowd might once have fueled, has largely been coached out of the game.

The home turnover advantage has eroded too, about half of it independent of the perimeter shift. The playoffs point the same way: the home rebound-share advantage has fallen by roughly three-quarters there too. With a fifteenth as many games, the playoff evidence is consistent with the regular-season story rather than established on its own. Player-tracking data from the last decade confirms the picture: home teams hold no measurable box-out advantage today, and their advantage in converting offensive-rebound chances has kept shrinking.

![Figure 8. Why the home rebounding advantage faded. Left: offensive and defensive rebound edges season by season — the offensive edge collapses toward (and through) zero while the defensive edge only softens, for both regular season and playoffs. Right: the home rebound-share edge fades in lockstep with the league-wide retreat from offensive rebounding (r = 0.82).](generated/nba_home_court_rebounding.png)

**Adding it up.** The four box-score categories together account for roughly 96% of the entire regular-season decline. The two that get the headlines explain about 21% and 18%: shooting, where converging shot selection and the three-point shift register, and the narrowing whistle. Rebounding and turnovers carry the most: roughly 30% and 27%, together more than half the drop. In the regular season, almost nothing is left over. (These are accounting shares showing where the decline registers in the box score, not a claim about ultimate causes.)

The playoffs don't close as neatly. The same four categories capture only about 67% of the decline, leaving roughly a third unaccounted for. With a fifteenth as many games as the regular season, only the foul and rebounding trends are statistically solid; the shooting and turnover trends can't be told apart from noise. The postseason breakdown is best read as consistent with the regular-season story, not independently proven.

![Figure 9. Box-score category shares of the home-court advantage and of its decline, regular season vs. playoffs. The left panel is what creates the advantage; the right is what's eroding it. Bars sum to 100% by accounting identity.](generated/nba_home_court_mediation.png)

Could rebounding and turnovers just be the three-point shift in disguise? No. Hold each game's three-point volume fixed and the **shooting** fade disappears completely. It really was the perimeter story all along. The **rebounding** fade barely moves and stays the surest of the four. Fouls and turnovers land in between. The categories doing the most work to drag home court down are doing it independently of the three-point boom. (In the playoffs the same test is too noisy to read; only the rebounding fade clears the bar. So this is a regular-season verdict.)

![Figure 10. Does each category's fade survive holding three-point volume constant? Each bar is the share of that category's yearly decline left after the control: 100% means the fade has nothing to do with the three-point shift, 0% means it is entirely the three-point story, below zero means the advantage actually reverses. In the regular season the shooting fade is fully the three-point story while the rebounding fade is essentially untouched; the playoff bars are mostly small-sample noise (greyed), with only rebounding holding up.](generated/nba_home_court_3pa_control.png)

---

## 4. What Didn't Drive the Change

Several popular explanations for the decline turn out not to hold up.

**Rule changes — the most obvious suspect of all.** The NBA has rewritten its rulebook many times since 1984: outlawing and re-legalizing zone defense, cracking down on hand-checking, emphasizing freedom of movement, adding the take-foul rule. It would be natural to pin the decline on these. But test each rule-change boundary against the year-by-year trend and almost none left a mark.

Exactly one season did: 1994–95, worth a genuine one-time drop of about 2.6 points beyond the ongoing drift. Two things changed that year: the league cracked down on hand-checking and, for three years, shortened the three-point line. Season-by-season data can't fully separate the two, but hand-checking is the more likely culprit; it bears directly on the fouls and defense at the core of home court. The shorter three-point line briefly spiked three-point volume and may have added to the drop.

The adjustment played out over several seasons. The decline stayed steep, about −0.65 points per year, through the late 1990s. It then settled into the gentler −0.26 that has held since. A formal break-point test places that settling in the late 1990s, several seasons after the rule change. That lag is the downstream consequence of the same event: referees retrained, rosters rebuilt, players adapted. It is not a separate cause.

Every other change — zone legalization, the perimeter hand-check ban, freedom of movement, the take-foul rule — the decline passed straight through with no step up or down. In the playoffs, neither 1994–95 change registers; the postseason slide is pure, smooth drift. Rule changes reshaped how the game looks. With that one exception, they did not bend the home-court trend.

**Travel and time zones.** Travel distance has a detectable effect in the regular season but a negligibly small one, about 0.07 percentage points per 100 miles. A team flying cross-country has nearly the same odds of winning as one driving two hours. In the playoffs, travel distance has no measurable effect at all. Time zones are equally flat in both contexts.

**Load management and the back-to-back.** The share of games where the visitor was playing on a second consecutive night has fallen from about 35% in the 1980s to under 20% today. But the payoff for home teams is small. When the visitor is on a back-to-back, the home team wins about 65%; when neither side is tired, 59%. The shrinking supply of tired visitors accounts for less than a percentage point of the decline, about 8% of it. The other 92% is the home advantage eroding within every rest situation alike: fresh visitor or tired, home court has weakened the same way. Scheduling nudged home court; it didn't drive it down. (Back-to-backs barely exist in the playoffs, so this is a regular-season question.)

![Figure 11. The load-management story, tested. Left: the share of games in which the visitor is on a back-to-back has fallen from about 35% to under 20% — the premise is true. Right: a shift-share split of the regular-season home win % decline shows only about 8% comes from that schedule change; the other 92% is the home advantage eroding within every rest situation alike.](generated/nba_home_court_back_to_back.png)

**Pace of play.** The game slowed dramatically from the 1980s to the mid-1990s, then sped back up after 2015. Home court advantage moved independently of both shifts. Season by season, pace shows no meaningful correlation with home win rates. Whatever pace does within a single game, it didn't drive the four-decade decline. The same holds in the playoffs.

![Figure 12. Pace of play vs. home win %, regular season and playoffs.](generated/nba_home_court_pace.png)

**Whether home teams take more or fewer threes than their opponents.** The three-point story in Section 3 is about both teams taking more threes, not home teams outgunning visitors from deep. In reality, home and away teams have always attempted threes at nearly identical rates. Through most of the last 40 years, home teams actually took slightly *fewer* threes per shot attempt than road teams; today home teams take about 0.4 percentage points more. The home-vs-away three-point differential is tiny, trends the wrong direction, and is not the mechanism.

**Competitive balance.** The idea: more parity compresses outcomes toward 50-50, dragging down home court. The raw correlation across seasons is near zero. The era breakdown makes a mess of the theory: the most unequal era (1995–01) had already seen HCA fall sharply, while the most balanced era (2002–04) saw it tick back up. There is a small wrinkle: once the shared long-run downtrend is removed, a weak year-to-year association emerges. But the effect is modest and nowhere near large enough to explain the 40-year decline.

![Figure 13. Competitive balance (team win% spread) vs. home win %, regular season.](generated/nba_home_court_parity.png)

**Crowd size — the obvious thing to blame, and it's innocent.** If a thinning crowd were draining home court, attendance should have fallen alongside it. It hasn't. NBA arenas have run at or near capacity across the 27 seasons with reliable gate figures — roughly 17,000 a night in the early 2000s, climbing to record highs above 18,000 in the 2020s, the very years home win rates hit their lowest. Season to season the two are unrelated; if anything they drift in opposite directions. In the playoffs the point is cleaner still: postseason games are near-guaranteed sellouts, so crowd size barely varies, yet postseason home court has eroded right alongside the regular season.

**The empty-arena experiment.** Crowd presence is a different question from crowd size, and the pandemic ran an accidental test. In 2020–21, local health rules left some arenas empty and others partly filled. The result was stark: with the building empty, home teams won just 51%, a coin flip. With any crowd at all, they won 58.5%, right back at the modern norm. The jump comes from presence itself, not the exact count. Going from a few thousand to a full house adds little beyond what those first fans restore. Then the whole effect vanished the moment buildings refilled. A live crowd is a genuine ingredient of home court, worth the better part of seven points on the night. But it's a switch that flips with the doors, not a dial slowly turning down for 40 years.

![Figure 14. Left: league average attendance per game vs. regular-season home win %, 2000–2026 — crowds hold near capacity (and lately set records) while home court keeps falling. Right: 2020–21 home win % by game attendance — an empty arena erases the advantage that even a small crowd restores.](generated/nba_home_court_attendance.png)

**Put it all together, and the decline still stands alone.** Feed a single model every situational factor at once: rest, altitude, time zones, even the COVID empty-arena seasons. Ask what's left to explain. Roughly half the model's predictive power belongs to those factors combined. The other half belongs to *which era the game was played in*. That era effect is just the decline itself, measured. Home advantage is about 9 points lower in 2023–26 than in 1984–94 after every factor gets its due.

The cleanest version of the test compares seasons on either side of 2014. The rest and time-zone effects are statistically unchanged; altitude's two-team boost weakened somewhat. Yet the baseline home advantage dropped about 4.7 points anyway. The situational factors held still while the floor fell. The decline traces to the on-court changes of Sections 2 and 3: the neutral whistle and the move to the perimeter.

---

## 5. The Playoff Picture

The playoffs are not a shrunken version of the regular season. They have their own structure, their own baseline, and their own timeline of decline.

**Who is playing at home matters more than anything else.** Across all eras, the single strongest predictor of a playoff game outcome is which team has home court. Games 1 and 2, at the higher seed's arena, go to the home team 69% and 72% of the time. Games 3 and 4, at the lower seed's arena, are barely better than coin flips for the team playing there (55–56%). Game 5, back at the top seed, is the most lopsided of all: 74.5%. Even Game 7 still goes to the home team 64% of the time. Road teams show no evidence of adapting as a series deepens.

![Figure 15. Playoff home win % by game number, all eras and by era.](generated/nba_home_court_series_breakdown.png)

**The playoff decline is real home-court weakening, not weaker seeds.** A natural objection: maybe playoff home teams win less now simply because top seeds no longer outclass their opponents the way they once did. The data says no. Account for the regular-season quality gap between the two teams and the year-by-year playoff decline doesn't budge. None of it is explained by seeds bunching together. The cleanest proof: when the objectively weaker team hosts Games 3 and 4, it still wins 51.5% of the time. Home court alone is still worth a coin-flip-beating advantage, and that advantage is what has been eroding.

![Figure 16. The playoff decline is genuine home-court weakening, not weaker seeds. Left: the yearly playoff decline is the same size before and after removing the regular-season quality gap between the two teams — quality explains essentially none of it. Right: home win % by who hosts — even the objectively weaker team still wins about 51.5% of its home games (Games 3–4), a pure venue effect above the coin-flip line.](generated/nba_home_court_playoff_quality.png)

**The 2014 format change didn't cause the playoff drop.** The playoffs have been restructured over the years, in four distinct format periods:

| Period | Seasons | Format |
|--------|---------|--------|
| 1984 | 1983–84 | Best-of-5 first round; 2-2-1-1-1 Finals |
| 1985–02 | 1984–85 → 2001–02 | Best-of-5 first round; 2-3-2 Finals |
| 2003–13 | 2002–03 → 2012–13 | Best-of-7 first round; 2-3-2 Finals |
| 2014–26 | 2013–14 → 2025–26 | Best-of-7 first round; 2-2-1-1-1 Finals |

The most recent shift, in 2014, coincided with the sharpest period of playoff HCA decline: a nearly 7-point raw drop from the 2003–13 period to the 2014–26 period. But when the year-by-year secular trend is accounted for, the format change has no independent effect. The playoff drop would have arrived on roughly the same schedule regardless. Format was not the cause.

![Figure 17. Home win % by playoff format period, regular season vs. playoffs.](generated/nba_home_court_advantage_format_bars.png){width=0.5}

---

## 6. Other Findings

A few results surfaced along the way that don't bear directly on the three questions but are too interesting to leave buried in the appendix.

**Some referees favor the home team more than others — but less than the raw numbers suggest.** Of 47 officials with at least 50 playoff games, 45 call fewer fouls on the home team. The most home-leaning on record, Ron Garretson, Joe Crawford, and Eddie Rush, sit close to a full foul per game apart from the most even-handed, a group that includes Tony Brothers, Josh Tiven, and Joe Forte. About 60% of that raw spread is small-sample noise. Referees genuinely differ, but the gap between them is narrower than the leaderboard suggests. This measures tendencies, not proof that any one official decides games.

**Denver and Utah own the best home court in the league — and altitude is the likely reason.** Across 40 seasons, the Nuggets and Jazz hold the largest regular-season home advantages of any franchise: about 27 and 26 percentage points above their own road win rates, against a league average near 20. Both play at altitude. The franchise spread is real: roughly 70% of the variation across teams reflects genuine differences, not noise. Altitude sits right at the top of it. With only two high-altitude franchises, elevation can't be fully separated from whatever else is unique to those teams, but it is the most plausible common thread. (The 27-point figure is their full home-minus-road gap; the altitude piece on its own, from Section 2, accounts for about 8 of those points.)

![Figure 18. Franchise home court advantage, regular season and playoffs. Bars and points carry 95% confidence bands: in the regular season most franchises sit clearly apart, but in the playoffs the bands are wide and overlapping — the franchise differences there are mostly noise.](generated/nba_home_court_team_hca.png)

**In the playoffs, every franchise's home court looks the same — the differences are an illusion.** That real regular-season spread vanishes in the postseason. With fewer than 150 playoff home games on record for most franchises, the apparent gaps are entirely explained by small samples. The true spread between franchises is statistically indistinguishable from zero. A team's reputation as a postseason fortress mostly reflects being a good team. Good teams simply play more home games.

**Home court is worth more in the playoffs than in the regular season.** Among franchises with both records, home court is worth about 20 points in the regular season but 27 in the playoffs, a 7-point premium. Teams that protect their building in the regular season tend to do so in the playoffs as well, but only loosely. The crowd, the stakes, and the familiar floor count for more when the games matter most.

**Player-tracking data caught the final chapter of the rebounding fade.** The high-resolution cameras the NBA deployed in 2013–14 arrived too late to document most of the story. The home team's grip on the offensive boards had already been collapsing for two decades. But the final chapter is visible: the home team's advantage in converting offensive-rebound chances kept shrinking through the entire tracking era, falling from about 1.5 percentage points in the mid-2010s to below zero by 2025–26. The box-out advantage has been essentially zero throughout the whole tracking window. The cameras confirmed a fade that was already nearly complete before they could see it.

![Figure 19. The modern player-tracking view of the home rebounding advantage (2013–14 on). Left: the home advantage in converting offensive-rebound chances keeps shrinking, slipping below zero by 2025–26. Center: home teams hold no measurable box-out advantage. Right: the second-chance-points advantage shows little change across this window. A short window that corroborates the modern mechanism, not the 40-year decline.](generated/nba_home_court_rebounding_tracking.png)

**The blowouts are getting bigger — even as home teams win less.** As home court advantage has faded, the margin when the home team *does* win has grown. Home wins are more lopsided; home losses are worse. Track the full spread of margins regardless of who won: the gap between the biggest wins and biggest losses widens by about 0.2 points per year in the regular season and 0.3 in the playoffs. In the regular season blowouts grow in both directions; in the playoffs the spread widens mainly because the big home wins keep getting bigger. Fewer home wins overall, but the ones that happen are more decisive.

![Figure 20. Home team win margin trends — mean margin per season and by era (regular season and playoffs), with the win-only vs. loss-only split for the regular season.](generated/nba_home_court_margin.png)

---

## 7. Summary

Home court advantage in the NBA has been cut nearly in half over 40 years. The regular season went from 65% to about 55%; the playoffs from nearly 68% to 58%.

The decline is real and one-directional: a slow, four-decade erosion with two sharper drops layered on it. The first traces to the 1994–95 rule change, most likely the hand-checking crackdown, whose full adjustment played out through the late 1990s. The second is the post-2017 perimeter shift, which shows up in the shooting line of the box score. Neither is the whole story. The data points to four main explanations that together account for about 96% of the regular-season decline:

**Referees are calling fairer games.** The systematic home-team foul benefit was 1.2 fouls per game in the regular season and 1.6 in the playoffs in the 1980s. It has shrunk to roughly a quarter of a foul per game in the regular season and 0.7 in the playoffs. This is the largest single measurable change, and it shows up universally: 45 of 47 playoff officials with at least 50 games on record call fewer fouls on the home team.

**Shot selection has converged.** Away teams now attack the paint nearly as aggressively as home teams. The built-in shot-quality advantage that home teams once carried into every possession has nearly disappeared. Our data confirms only that the gap closed, not why.

**Three-point shooting equalizes outcomes.** The shift to the perimeter erodes home court through a specific channel: the shooting line of the box score. Hold three-point volume constant and the home shooting advantage holds up; let it rise and the advantage shrinks. The 40-year lockstep between three-point volume and home win rate is the most striking visual in the dataset, though the reliable evidence is within a single season: games with more threes have lower home win rates even among contemporaries, independent of the long-run drift.

**And the biggest driver of all: the rebounding advantage died on the offensive glass.** The home team's hold on the boards has slipped over 40 years, independently of the three-point boom. The slide is concentrated in offensive rebounding, where the advantage has fallen from about six-tenths of a board per game to slightly below zero. It shows up even as a pace-free share of available rebounds, so it's no statistical artifact. The league-wide offensive-rebound rate fell from 33% to 26% over the same span, and the home advantage tracked that retreat. The effort-driven offensive board, the kind a home crowd might once have spurred, has been coached out of the game. The home turnover advantage has partly followed, and the same pattern holds in the playoffs.

What hasn't driven the decline: rule changes (with the single exception of 1994–95), travel, time zones, pace of play, competitive balance, crowd size, and playoff scheduling format. The data rules each out. The schedule-spread argument — fewer tired visitors — explains only about 8% of the decline. Arenas have stayed near capacity, lately setting records, even as the advantage shrank. The one genuine crowd effect is a blip: in the empty arenas of 2020–21 home teams won just 51%, then snapped back to 58.5% whenever fans returned. Crowd noise is real and measurable, but it's a switch that flips with the doors, not a dial slowly turning down for 40 years.

The playoffs have followed the regular season's path but with nearly a two-decade lag. For most of the 2000s and 2010s, postseason home court held firm even as the regular season eroded around it. The internal structure of playoff home court remains stark: Games 1 and 2 go to the home team 69% and 72% of the time; Game 5 is the most lopsided at 74.5%; even Game 7 still goes to the home team 64% of the time. Since 2018 the decline has accelerated. It is genuine home-court erosion, not an illusion of more evenly matched seeds. Even the weaker team, when it hosts, has been winning less.

