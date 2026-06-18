# The Investigation: What We Ruled Out

*Companion to [NBA Home Court Advantage: Findings](nba_home_court_advantage_report.html). That report covers what drove the decline; this one covers what didn't, and why each hypothesis seemed reasonable before the data ruled it out.*

---

NBA home court advantage has been falling for 40 years. Several explanations are compelling on their face: the rules changed, travel improved, tired visitors became rarer, bigger crowds made arenas louder, more parity compressed outcomes. Each deserves a direct test rather than an assumption.

This document records those tests. For each hypothesis, we lay out why it seemed plausible, what was measured, what the data showed, and where the intuition went wrong. The statistical detail behind every test is in `RESULTS.md`; the charts here are the same ones used in the full analysis pipeline.

---

## Rule Changes and the Era Labels

**Why it seemed plausible.** The main findings chart opens with six labeled eras, each marking a rule change: the hand-checking crackdown, zone legalization, the perimeter-hand-check ban, freedom-of-movement emphasis, the take-foul rule. The era shading makes each boundary visible. It would be natural to read one or more of those transitions as explaining where home court bent.

**The test.** A piecewise regression with indicator variables at each rule-change boundary, asking whether any boundary caused a statistically significant one-time shift in home win percentage beyond the ongoing secular trend.

**The result.** Exactly one boundary registers: 1994-95, worth a genuine one-time drop of about 2.6 points beyond the trend (p=0.010). Every other change — zone legalization, the 2004-05 perimeter hand-check ban, freedom of movement, the take-foul rule — passed through the trend line with no significant step. In the playoffs, even 1994-95 doesn't register; the postseason slide is steady drift throughout.

**Why the intuition failed.** Rule changes alter how the game looks, but most of them change things for both teams equally. If zone defense is legalized, both home and away teams can run it and face it. If hand-checking is restricted, both teams stop using it. The rule reshapes the game; it doesn't reshape who benefits from playing in their own building.

The 1994-95 exception works for a specific reason. Hand-checking affected referee discretion, and referee behavior toward home teams is one of the few things that can shift asymmetrically. When referees were directed to call tighter games, the home-favoring foul bias compressed — not because home teams were less protected by the rule, but because tighter calling narrowed the gap across all calls. Foul calls responded immediately at the 1994-95 boundary (p=0.007). The shooting channel showed no significant immediate response (p=0.327). That asymmetry is the fingerprint of referee behavior, not shot-selection rules.

One complication: the three-point line was also shortened in 1994-95 through 1996-97, and the two changes can't be fully separated at the season level. The channel data points more toward hand-checking, but the shortened line may have contributed. See RESULTS.md for the full event-study output.

The practical implication for reading the main chart: the era labels tell you when the rules changed. They do not tell you that those changes bent home court. The shading is a calendar, not a causal map. Only one era boundary corresponds to a detectable break in the trend, and even that one mostly accelerated an erosion that was already underway.

---

## Travel and Time Zones

**Why it seemed plausible.** Air travel has improved dramatically since 1984. Teams now charter private planes, travel with larger staffs, and follow more sophisticated recovery protocols. If away teams in 1984 arrived meaningfully more fatigued, better travel conditions should have gradually closed part of the home-court gap.

**The test.** We regressed game outcomes on great-circle travel distance between the two cities and on time-zone crossings, controlling for era, rest, and altitude.

**The result.** Travel distance has a measurable but negligibly small effect in the regular season: about 0.07 percentage points per 100 miles. A team flying coast-to-coast (roughly 2,500 miles) faces about the same odds as one driving two hours — a difference of about 1.8 percentage points. In the playoffs, travel distance has no measurable effect at all. Time zones are flat in both contexts.

**Why the intuition failed.** Two reasons. First, home teams travel too. Away teams fly in; home teams flew back from their previous road trip. Better planes benefit both sides, so the relative disadvantage of arriving in a specific building doesn't shrink just because the flight got more comfortable. Second, the raw travel effect was always smaller than intuition suggests. Even a cross-country trip is worth less than 2 percentage points of home court in the model — against a baseline advantage of 7 to 10 points. Travel is a real but minor factor, and it hasn't changed over time in a way that explains the trend.

---

## Rest and Altitude

**Why it seemed plausible.** Rest should matter: a well-rested team outperforms a fatigued one, and home teams may systematically enter games fresher. Altitude should matter too: Denver and Utah play at elevation, which visibly taxes visiting teams. If either factor grew more prominent over time, it could explain part of the trend.

**The test.** We categorized each game by which team was better-rested and compared home win rates across categories. We measured altitude's effect by isolating Denver and Utah in a regression that includes era and rest.

**The result.** Rest creates genuine variation. Home teams win about 63% of regular-season games when they enter better-rested, and 58% when the visitor has the rest edge. That 5-point gap is real. Denver and Utah add about 8 percentage points to their regular-season home win rates, the largest franchise-level effect in the dataset.

![Left: home win % by rest situation. Right: altitude franchises (Denver and Utah) vs. league average, regular season and playoffs.](../generated/nba_home_court_rest_altitude.png)

**Why neither explains the decline.** The rest gap has stayed roughly constant across all eras. It existed in the 1980s and it exists now; it did not shrink as home court eroded. Altitude's effect is confined to two franchises and has actually weakened somewhat in recent years; it can't explain a league-wide trend. In the playoffs, rest is confounded with team quality: extra days between rounds almost always mean you swept the previous series, making you likely the stronger team regardless. Control for team quality and the playoff rest advantage largely disappears. Neither factor moved in the direction or at the scale needed to drive the decline.

---

## Load Management and the Back-to-Back

**Why it seemed plausible.** This is the most specific and testable version of the rest argument. The NBA scheduling office has been reducing back-to-back games for over a decade. Visiting teams arriving on the second night of a back-to-back were always likely to be fatigued. If fewer tired visitors means fewer easy home wins, the schedule change alone could account for part of the decline.

**The test.** A shift-share decomposition: measure how home win rates changed *within* each rest situation (both teams fresh vs. visitor on a back-to-back), then measure how much of the overall trend comes from the *mix* shifting (fewer back-to-backs) versus the rate changing within each bucket.

**The result.** The premise is correct: visitor back-to-back frequency fell from about 35% in the 1980s to under 20% today. But the schedule change accounts for only about 0.7 percentage points of the 9-10 point regular-season decline, roughly 8%. The other 92% comes from home court eroding within every rest situation alike. In games with no back-to-back, home teams win less than they used to. In games with a tired visitor, home teams also win less than they used to. The schedule shift nudged home court; it didn't drive it down.

![Left: visitor back-to-back frequency over time (the premise is correct). Right: shift-share decomposition showing 8% from schedule change, 92% from within-situation erosion.](../generated/nba_home_court_back_to_back.png)

**Why the intuition overshot.** The home advantage against a tired visitor (about 65%) is only 6 points above the baseline (about 59%). Even a 16-point drop in back-to-back frequency moves the league-wide average by less than a full percentage point. The mechanism is real; the magnitude is just too small to carry the story. And crucially: if tired visitors were the main driver, you would expect the advantage to hold steady in games with rested visitors and only fall in back-to-back games. The data shows it fell equally in both.

---

## Pace of Play

**Why it seemed plausible.** The NBA slowed dramatically from the 1980s to the mid-2010s, then sped back up after 2015. Either shift could plausibly affect home court. A slower game means fewer possessions and less opportunity for the crowd to affect repeated moments. A faster game might amplify energy. Either way, the pace swings were large and visible.

**The test.** Season-by-season plots of pace (possessions per game) against home win rate, plus within-era regressions for both regular season and playoffs.

**The result.** No meaningful relationship in either direction. Pace fell for two decades and home court held roughly flat, then fell; pace rose sharply after 2015 and home court kept falling. The two series move independently. Within any given era, higher-pace seasons do not consistently produce higher or lower home win rates. The same holds in the playoffs.

![Pace vs. home win % over time, regular season and playoffs.](../generated/nba_home_court_pace.png)

**Why the intuition failed.** Pace changes the number of opportunities in a game, but it doesn't systematically advantage one venue over the other. More possessions means more chances for crowd effects to operate — but also more chances for the better-shooting team to assert itself, and more possessions for an efficient away offense to score. The effects run in multiple directions and wash out. The data confirms there's no net signal.

---

## Home vs. Away Three-Point Differential

**Why it seemed plausible.** Section 3 of the main report establishes that the league-wide shift to three-point shooting hurt home court. A natural follow-on question: maybe home teams are being outgunned from the perimeter specifically? If away teams now take meaningfully more threes, they might be neutralizing the home crowd effect by operating at distance rather than attacking the basket.

**The test.** Season-by-season measurement of the home-minus-away three-point attempt rate differential.

**The result.** Home and away teams have always attempted threes at nearly identical rates. For most of the last 40 years, home teams actually took slightly *fewer* threes per shot attempt than road teams. Today home teams take about 0.4 percentage points more. The differential is tiny, trends in the wrong direction to explain the decline, and shows no relationship to the home win rate trend.

**Why the intuition failed.** The three-point story in the main report is about *both* teams taking more threes, not home teams being outgunned. When both teams shift together toward the perimeter, the eFG% gap closes because three-point shooting is taken from spots where crowd and familiarity effects are smaller than on interior attempts. It is a compositional shift that compresses the advantage, not a home-vs-away imbalance.

---

## Competitive Balance

**Why it seemed plausible.** If the NBA has become more equal, games should be more evenly contested on talent alone. More evenly matched teams should produce more coin-flip outcomes, which would naturally push the home win rate toward 50%. It is a reasonable structural argument.

**The test.** We measured competitive balance as the standard deviation of team win percentages each season and plotted it against home win rate. We then ran a regression after removing the shared long-run trend from both series to avoid spurious correlation.

**The result.** The raw season-level correlation between parity and home court advantage is near zero. The era breakdown actually contradicts the theory: the most unequal era (1995-01) had already seen HCA fall sharply from its 1980s peak, while the most balanced era (2002-04) saw HCA tick back up briefly. After removing the shared downtrend from both series, a small year-to-year association does emerge, but the effect is modest and nowhere near large enough to explain the 40-year decline.

![Competitive balance vs. home win % per season, regular season.](../generated/nba_home_court_parity.png)

**Why the intuition failed.** Competitive balance compresses outcomes symmetrically. More parity means both home and away teams face more evenly matched opponents — but it can't create an asymmetric disadvantage specifically for the home team. If anything, greater parity should make home court *more* influential, not less, since the teams are closer in talent and venue effects are more likely to be decisive. The structural argument runs the wrong direction.

---

## Crowd Size

**Why it seemed plausible.** The NBA expanded significantly over this period, adding franchises in smaller markets with younger fan bases. Older arenas in established markets were sometimes loud in ways newer buildings haven't replicated. If average crowd intensity or size fell, the noise advantage should have weakened.

**The test.** We plotted league-average attendance per game against home win percentage across the 27 seasons with reliable gate figures.

**The result.** NBA arenas have been near capacity throughout: roughly 17,000 per night in the early 2000s, climbing to record highs above 18,000 in the 2020s — the very years home win rates hit their lowest. Season to season, attendance and home court advantage are unrelated and if anything drift in opposite directions. In the playoffs the point is cleaner still: postseason games are near-guaranteed sellouts throughout the entire 40-year window, yet postseason home court eroded right alongside the regular season.

![Left: league average attendance vs. regular-season home win %, 2000–2026. Right: 2020–21 home win % by game attendance.](../generated/nba_home_court_attendance.png)

**Why the intuition failed.** The dial didn't turn. Arenas stayed full. If anything, the crowd has been getting bigger in the years home court advantage has been weakest, which is the opposite of what the hypothesis predicts.

---

## The Empty-Arena Experiment

The pandemic provided a natural experiment that separates crowd *presence* from crowd *size*. In 2020-21, local health rules left some arenas completely empty while others had partial crowds in the same season.

**The result.** With buildings completely empty (573 games), home teams won just 51% — a coin flip. With any crowd at all (591 games, median attendance 3,280), they won 58.5%, right back at the modern norm. Even a few thousand fans in an empty building restored nearly the full crowd effect. The dose-response is front-loaded: the jump comes from the first fans through the door, not from filling the last thousand seats.

This has two implications. First, crowd presence is a genuine ingredient of home court advantage — worth about 7 percentage points when you compare completely empty buildings to any crowd at all. Second, the relationship is a switch, not a dial. The full crowd effect restores with minimal attendance; larger crowds add little beyond what those first fans provide.

**Why this rules out crowds as the 40-year explanation.** Buildings refilled the moment health rules allowed it, and the advantage snapped back immediately. Crowd presence creates home court; since arenas have been full throughout the decline, it is not what has been eroding. The pandemic experiment isolates the crowd component cleanly — and that component is stable. The change is elsewhere.

---

## The Combined Situational Model

To verify that no combination of situational factors can collectively explain the decline, we built a single model stacking all of them at once: rest, altitude, travel, time zones, and the COVID empty-arena indicator.

**The result.** After accounting for all those factors, roughly half the model's explanatory power belongs to the situational variables combined. The other half belongs to which era the game was played in. That era effect is the decline itself, measured directly. Home advantage is about 9 percentage points lower in 2023-26 than in 1984-94 after every situational factor gets its due.

The cleanest version of the test compares seasons on either side of 2014. The rest and time-zone coefficients are statistically unchanged between the two periods. Altitude's boost weakened somewhat. Yet the baseline home advantage still dropped about 4.7 points. The situational factors held still; the baseline eroded beneath them.

**What this confirms.** By elimination, the decline lives in what happens between two evenly-situated teams on the court. The on-court changes — the narrowing whistle, the three-point shift, the rebounding collapse, the turnover edge erosion — are what remains once every off-court factor is fully accounted for. That is the Section 3 story, confirmed by subtraction.
