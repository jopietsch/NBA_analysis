# NBA Home Court Advantage — Findings

Home court advantage in the NBA has been shrinking for four decades, and this report sets out to answer three questions about it. **Has it really changed?** **What makes home court an advantage in the first place?** And **what's driving the decline — and, just as important, what isn't?**

The short answers come first; the rest of the report is the evidence behind them. Yes, the change is real and remarkably steady — the home team's win rate has fallen from about 65% to 55% in the regular season, and from nearly 68% to 58% in the playoffs. What makes home court an edge on any given night is a handful of concrete things: referees calling fewer fouls on the home team, a shooting and shot-selection advantage, and smaller boosts from rest and altitude. And what's driving the decline is that the biggest of those edges have worn away — the whistle has gone neutral, shot selection has converged between home and road teams, and the three-point revolution has drained the variance out of the home team's structural advantages.

What is *not* behind the decline matters too, because the usual suspects get blamed constantly: travel, time zones, pace of play, competitive balance, and the 2014 playoff format change. Each one is tested here, and each one is ruled out.

Throughout, the regular season and the playoffs are tracked separately — they share a direction but not a timeline. The analysis runs across 51,000 regular-season and playoff games; the underlying regression tables are in `RESULTS.md`.

---

## 1. The 40-Year Decline

The home team in an NBA game used to win about 65 out of every 100. Today it wins about 55. That 10-point drop unfolded at roughly a quarter of a percentage point per year and the data leaves no room to doubt it.

The playoffs tell the same story with a slight lag. The postseason home win rate peaked near 68% in the 1980s before sliding to 58% today — a drop of close to 10 points, comparable to the regular season but with more year-to-year noise given the smaller number of games.

![Figure 1. Regular season vs. playoff home win % per season, 1983–84 through 2024–25. Dashed lines are overall trend fits; background shading marks rule-change eras.](nba_home_court_advantage_season.png)

---

## 2. How the Drop Unfolded

The regular-season decline came in two waves. The first hit with the 1994–95 hand-checking restrictions — home win % fell from 65% to 60% in a single era transition, the sharpest single drop in the dataset, and the only rule change that left a discrete mark beyond the underlying trend. It then stabilized for the better part of two decades before a second drop, arriving after 2017, pushed it below 56%.

The playoffs behaved differently. Postseason home court held remarkably steady from 1995 through 2017, hovering around 64% for three consecutive eras, even as the regular season eroded beneath it. Since 2018 the playoffs have joined the slide, falling to 61% and then 58% in the most recent seasons.

![Figure 2. Home win % by era, regular season vs. playoffs.](nba_home_court_advantage_era_bars.png)

One counterintuitive wrinkle: even as home teams win less often, the margin when they do win has grown. Home wins are getting bigger, and home losses are getting worse. This is true in both the regular season and the playoffs. The era of close games is becoming an era of blowouts in both directions for the home team — fewer home wins overall, but the ones that do happen are more decisive.

![Figure 3. Home team win margin trends, regular season.](nba_home_court_margin.png)

---

## 3. What Creates Home Court Advantage

Three things have historically given home teams an edge on any given night: referees calling fewer fouls on them, a shooting advantage, and favorable shot selection. Rest and altitude add to the picture for specific matchups.

**Referee foul calls.** Across every era and in both regular season and playoffs, referees have called fewer fouls on home teams than road teams. In the 1984–94 regular season, home teams averaged about 1.2 fewer foul calls per game. In the playoffs the bias was even more pronounced — about 1.6 fewer fouls per game favoring the home team. With fouls go free throws, and with free throws go points. This is the most consistent structural component of home court advantage.

The playoff referee data makes the universality of this clear: 41 of 42 officials with at least 50 playoff games on record show a home-favoring foul differential, and the results hold up under every check applied. Nearly every referee who has worked the postseason has — consciously or not — called the game differently depending on which team was at home.

**Shooting edge.** Home teams have consistently shot the ball better than road teams — better than a percentage point in field goal percentage across the full period, with a similar gap in effective field goal percentage. Part of this reflects psychological comfort, part reflects familiarity with the floor and backdrop of a specific arena. The effect has been consistent across eras in both regular season and playoffs.

**Shot selection.** Historically, home teams have gotten more of their field goal attempts from close range and fewer from the perimeter. A paint shot is more efficient than a jump shot, so home teams have started each possession with a small structural advantage in expected scoring — independent of how well they shoot from any given spot.

![Figure 4. Home vs. away box-score differentials — foul rate, FG%, eFG%, 3PA rate, 3P%, FT%.](nba_home_court_advantage_differentials.png)

**Rest and altitude.** When the home team enters a game better rested than the visitors, they win about 63% of the time — three points above the league baseline. When the road team is the better-rested side, the home win rate drops to 58%. The effect is consistent across all eras; rest has not become more or less important over time. Denver and Utah, playing at altitude, add more than 8 percentage points above the league average to their regular-season home win rates. That altitude effect is real — and largely absent in the playoffs, where opponents have had full series to adjust and team quality effects dominate. Playoff rest is similarly confounded: a team with extra rest between rounds is usually the one that swept or won quickly, which means it's also almost certainly the better team. Control for team quality and the rest edge in the playoffs shrinks to nothing.

---

## 4. What's Driving the Decline

The same three factors that create home court advantage are the three things that have been eroding over 40 years.

**Referee foul bias has narrowed sharply.** The home foul differential in the regular season has dropped from 1.2 fouls per game in the 1980s to just 0.2 fouls per game today — an 83% reduction. In the playoffs it has fallen from 1.6 to 0.7 fouls per game. The structural advantage referees once gave to home teams has nearly vanished in the regular season and is significantly diminished in the postseason.

The playoff referee chart makes the generational shift visible. The officials with the most pronounced home-favoring patterns — Ron Garretson, Joe Crawford, Eddie Rush — all worked primarily in the 1990s and early 2000s. The distribution across individual referees has compressed over time, not just shifted. Newer officials are not only less biased on average; they are also more uniform in their calling.

![Figure 5. Referee home foul bias by official and era, playoffs.](nba_home_court_referee.png)

**The shot zone advantage has evaporated.** In the 1990s, home teams generated about 1.3 percentage points more of their field goal attempts from the paint than road teams. By 2023–25, that gap has shrunk to just 0.4 points in the regular season and has similarly contracted in the playoffs. Away teams now attack the basket nearly as aggressively as home teams. The league-wide shift toward analytics-driven offense has standardized shot selection across venues — whether you're playing at home or on the road, the right shot is the right shot.

![Figure 6. Shot zone differentials (home minus road), regular season vs. playoffs.](nba_home_court_shot_zones.png)

**The three-point revolution.** No stylistic change in league history matches the rise of three-point shooting, and it tracks almost perfectly with the decline in home court advantage. When about 7% of all field goal attempts were threes in the 1980s, home teams won 65% of games. When 40% of attempts are threes today, home teams win 55%.

This is not just a coincidence of timing. Even within any given era — controlling for all the gradual year-by-year drift — games in which teams attempt more threes show measurably lower home win rates. Each 10-percentage-point rise in three-point attempt rate translates to about 2 fewer home wins per 100 games. The more the game spreads to the perimeter, the less the home crowd, the familiar floor, and the referee's subconscious seem to matter.

In the playoffs, the pattern holds directionally but the within-era signal is weaker — in the postseason, team quality dominates game outcomes more than stylistic factors.

![Figure 7. League three-point attempt rate vs. home win %, regular season and playoffs.](nba_home_court_3pa.png)

---

## 5. The Playoff Picture

The playoffs are not a shrunken version of the regular season. They have their own structure, their own baseline, and their own timeline of decline.

**Who is playing at home matters more than anything else.** Across all eras, the single strongest predictor of a playoff game outcome is which team has home court. Games 1 and 2 — played at the higher seed's arena — go to the home team 69% and 72% of the time. Games 3 and 4 — at the lower seed's arena — are barely better than coin flips for the team playing there (55–56%). Game 5, back at the top seed, is the most lopsided of all: 75%. Even Game 7, the highest-pressure game in basketball, still goes to the home team 64% of the time. There is no evidence that road teams adapt as a series deepens. The home-away split explains the pattern entirely.

![Figure 8. Playoff home win % by game number, all eras and by era.](nba_home_court_series_breakdown.png)

**The 2014 format change didn't cause the playoff drop.** The shift in Finals scheduling coincided with the sharpest period of playoff HCA decline — a 6-point raw drop from the 2003–13 period to the 2014–25 period. But when the year-by-year secular trend is accounted for, the format change has no independent effect. The playoff drop would have arrived on roughly the same schedule regardless. Format was not the cause.

![Figure 9. Home win % by playoff format period, regular season vs. playoffs.](nba_home_court_advantage_format_bars.png)

**Franchise differences are real in the regular season, invisible in the playoffs.** Across 40 seasons, Denver and Utah hold the largest home court advantages in the regular season — about 27 and 26 percentage points above their road win rates after accounting for sample size. The spread across franchises is genuine: roughly 70% of the observed variation represents real differences, not statistical noise. Denver's altitude, Utah's long-tenured crowd culture, and Indiana's arena environment are real factors.

In the playoffs, franchise-level differences collapse entirely. With fewer than 150 home games on record for most franchises, statistical noise overwhelms any real signal. All playoff franchises effectively shrink to the league average of 27 percentage points above their road win rate. A team's reputation for being tough to beat at home in the playoffs is mostly a reflection of being a good team — and good teams, by definition, play more home games.

![Figure 10. Franchise home court advantage, regular season and playoffs.](nba_home_court_team_hca.png)

---

## 6. What Didn't Drive the Change

Several popular explanations for the decline turn out not to hold up.

**Travel and time zones.** The effect of travel distance is detectable in the regular season but negligibly small — about 0.08 percentage points per 100 miles of road travel — and it doesn't even point consistently in the intuitive direction. Practically speaking, a team flying cross-country has nearly the same odds of winning as one driving two hours. In the playoffs, travel distance has no measurable effect at all. Time zones are similarly flat in both contexts: crossing from one coast to the other adds essentially nothing to the home team's edge.

**Pace of play.** The game slowed dramatically from the 1980s to the mid-1990s and has sped back up since 2015 — yet home court advantage moved independently of both shifts. Season by season, the pace of play shows no meaningful correlation with home win rates. Faster or slower basketball does not predict whether the home team wins. The same holds in the playoffs.

![Figure 11. Pace of play vs. home win %, regular season and playoffs.](nba_home_court_pace.png)

**Competitive balance.** A widely cited argument holds that more parity compresses game outcomes toward 50-50, reducing home court advantage. The raw correlation across seasons is near zero, and the era breakdown makes a mess of the theory: the most unequal era (1995–01) had already seen HCA fall sharply, while the most balanced era (2002–04) saw it tick back up. The two don't move together. There is a small wrinkle: both series share a downward trend over 40 years, and once that common trend is removed, a weak year-to-year association does emerge — in years when the league gets slightly more equal, HCA tends to dip slightly too. But the effect is modest and doesn't come close to explaining the magnitude of the 40-year decline.

![Figure 12. Competitive balance (team win% spread) vs. home win %, regular season.](nba_home_court_parity.png)

---

## 7. Summary

Home court advantage in the NBA has been cut nearly in half over 40 years. The regular season went from 65% to 55.6%; the playoffs went from nearly 68% to 58%.

The decline is real, steady, and not the artifact of any single rule change. The data supports three explanations:

**Referees are calling fairer games.** The systematic home-team foul benefit — once more than a full call per game — has shrunk to nearly nothing in the regular season and roughly half its former level in the playoffs. This is the largest single measurable change, and it shows up universally across individual officials.

**Shot selection has converged.** Away teams now attack the paint nearly as aggressively as home teams. The structural edge in shot quality that home teams once carried into every possession has nearly disappeared, driven by the league-wide adoption of analytics-driven offense that applies regardless of venue.

**Three-point shooting equalizes outcomes.** The shift to the perimeter introduces more variance into every game. More variance means less predictability, and less predictability hurts home teams — who have historically relied on structural, consistent advantages — more than it hurts road teams. The near-perfect correlation between three-point volume and home win rate is the most striking pattern in the dataset.

What hasn't driven the decline: travel distance, time zones, pace of play, competitive balance, and playoff scheduling format. The data rules each of them out. One temporary exception worth noting: the two COVID-impacted seasons (2020–21 with sharply reduced crowds) showed home win rates about 2 percentage points lower than the underlying trend would predict — a direct signal of how much crowd noise matters. The effect was real but reversed once arenas refilled; it's a blip in the data, not part of the structural decline.

The playoffs have largely followed the regular season's path but with a decade's delay. For most of the 2000s and 2010s, postseason home court held firm even as the regular season eroded around it. Since 2018, the playoffs have accelerated their own decline. The structural advantages of playing at home — crowd noise, familiar surroundings, and the subconscious pull of referee calls — have weakened in both contexts, and there is no sign the trend has bottomed out.
