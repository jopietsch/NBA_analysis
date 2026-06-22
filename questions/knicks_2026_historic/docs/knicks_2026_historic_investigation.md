# The Investigation: Objections to a Historic Run

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

*Companion to [Did the 2026 Knicks Have a Historic Playoff Run?](knicks_2026_historic_report.html). The main report argues the run was historically dominant; this one collects the objections to that claim, the reasons people offer for why a 16-3 run might mean less than it looks, and tests each one directly.*

---

A 16-3 playoff run with a +14.9 average margin looks historic on its face. But a record that good invites deflation: maybe the conference was weak, the bracket was soft, the opponents were hurt, or the scoreboard was padded. Each of these is a fair objection, and each is testable rather than something to wave off.

This document records those tests. For every objection we lay out why it seemed plausible, what was measured, what the data showed, and how much of the run it actually explains away. The numerical detail behind each test is in `knicks_2026_historic_results.md`; the charts here are the same ones used in the full analysis pipeline. The honest counterweight, the one thing that genuinely does temper the claim, is in the last section.

---

## "The East was historically weak"

**Why it seemed plausible.** The Knicks came up through the Eastern Conference. The East has spent long stretches as the weaker half of the league, so a path that never touched the West until the Finals could inflate a record without inflating the team behind it.

**The test.** The average team rating gap between the conferences (West SRS minus East SRS) for 2025–26, ranked against every season back to 1983–84, plus the East's regular-season record in games against the West.

**The result.** The gap was +0.39 points per game, the 37th percentile of West dominance. In 63% of seasons since 1984 the West led by more than it did in 2025–26. The East's inter-conference win rate was 0.487, near even. The three most West-tilted seasons on record (2013–14 at +4.08, 2003–04 at +3.73, 2000–01 at +3.11) are several times larger than this one.

![Conference strength gap (West − East SRS), 2025-26 flagged](../generated/images/knicks_2026_conference_gap.svg){width=100%}

**How much it explains away.** Essentially none. By any league-wide measure the 2025–26 East was unremarkable, if anything slightly more balanced than the 42-year average. This objection is the weakest of the set. (Main report, §3.)

---

## "The bracket was soft"

**Why it seemed plausible.** Even a normal conference can hand a champion an easy road. If the specific teams the Knicks drew were below the usual championship caliber, the margins would be padded by the matchups rather than the team.

**The test.** The games-weighted average rating of the Knicks' four playoff opponents (each opponent weighted by how many games the series ran), ranked against all 43 champions since 1983–84.

**The result.** The opponents averaged +3.67, the 49th percentile, essentially the median champion's schedule. Cleveland (+3.77) was a genuine title contender, and the Spurs entered the Finals as one of the strongest teams in the field (+8.28 in the regular season, second only to Oklahoma City among playoff teams).

![Strength of schedule, avg opponent SRS per champion](../generated/images/knicks_2026_opponent_srs_ranking.svg){width=100%}

**How much it explains away.** Nothing. The schedule was neither unusually easy nor unusually hard; it sat at the historical middle. (Main report, §3 and §4.)

---

## "The early-round opponents were fading"

**Why it seemed plausible.** Regular-season ratings describe a team's whole year. If the 76ers and Cavaliers were declining by the time the Knicks met them, the rounds 1–3 blowouts would overstate how good those opponents really were in May.

**The test.** Recompute each opponent's playoff rating from their playoff games *excluding* the Knicks series, an independent read on their form, then re-adjust the Knicks' margins against it. The Hawks played only the Knicks, so there is no independent measure of them.

**The result.** A weak maybe, and only for two opponents. The 76ers and Cavaliers rated about 1.2 and 1.5 points below their regular-season marks in their non-Knicks playoff games. But each of those reads rests on only a handful of games, so a gap that small is about as likely to be the random bounce of a short schedule as a real dip. The Spurs moved the opposite way: from +8.28 in the regular season to +14.48 in their non-Finals playoff games, a +6.2 rise, the largest of any Knicks opponent. Adjusting the whole run for opponents' actual playoff form still leaves the Knicks at +9.1 per game, narrowly the best on record.

![Per-round raw vs. opponent-adjusted margins: adjustment using playoff SRS shifts the Finals story](../generated/images/knicks_2026_round_split.svg){width=100%}

**How much it explains away.** A little, at the edges, and only in the rounds the Knicks won most easily. The toughest opponent of the run went the other way and was playing above its season form. (Main report, §5.)

---

## "The margins are garbage-time padding"

**Why it seemed plausible.** A +14.9 average margin can be inflated by running up the score in games that were already decided. Any rating built on point margins would reward that padding.

**The test.** Re-rank the run with a wins-only rating (Bradley-Terry), which is fit from nothing but who beat whom and never sees a single point margin.

**The result.** On a pure wins-only basis the Knicks' opponent-adjusted dominance still ranks first of 43, and it grades their schedule almost exactly as the margin-based rating does.

![The Knicks rank top-3 under all three rating systems: #1 on season margin and wins-only, #3 once recent form is weighted](../generated/images/knicks_2026_rating_systems.svg){width=100%}

**How much it explains away.** None. Stripping margins out entirely does not knock them off the top, so the dominance lives in who they beat, not just by how much. (Main report, §11.)

---

## "The high-scoring era inflated the margin"

**Why it seemed plausible.** 2025–26 had the most points per game in the dataset (115.6, against a 103.5 historical mean). In a higher-scoring league, the same level of dominance could produce a mechanically larger point margin.

**The test.** Two era adjustments pointing in different directions. A scoring-share version scales each margin by that season's points per game (a deliberately harsh take that treats the whole scoring boom as inflation). A possessions version scales by estimated pace, which separates a fast game from an efficient one.

**The result.** Most of 2025–26's scoring is better shooting, not a faster game: in possessions the season ran only about 4% above average. Per 100 possessions the Knicks' raw margin (+14.6) and opponent-adjusted margin (+11.0) both stay first. Only the harsher scoring-share version moves them, dropping the raw margin to third.

**How much it explains away.** Little, on the more correct measure. On a true pace-neutral basis the #1 claim survives; the opponent adjustment also already absorbs some era effect, since a champion and its opponents are measured in the same environment. (Main report, §14.)

---

## "An opponent was injured"

**Why it seemed plausible.** Dominant playoff runs often carry an injury asterisk: a key opposing star sits, and the margins balloon against a depleted team.

**The test.** For each opponent, the share of their rotation players (those averaging at least 15 minutes a game across the playoffs) who actually appeared in each game of the Knicks series.

**The result.** Average availability was 98% across the four opponents. The Hawks and the Spurs were at 100%. The Spurs, the team that gave the Knicks their tightest series, were fully intact.

![Opponent key-player availability across the 2025-26 Knicks playoff run](../generated/images/knicks_2026_opponent_health.svg){width=100%}

**How much it explains away.** None. The close Finals margin reflects genuine competition against a whole team, not a depleted one. (Main report, §9.)

---

## What actually does temper the claim

None of the objections above survives contact with the data, but one genuine caveat does, and it has nothing to do with the opponents. It is the shortness of the run itself.

The "best opponent-adjusted margin of any champion" claim rests on 19 games. That is a small sample, and the other 42 champions are measured with the same kind of uncertainty. When every champion is allowed to be as uncertain as the Knicks, and the field is judged all at once, the Knicks come out as the single best only about 9% of the time. They still land in the top handful of title runs in the great majority of those comparisons, but the data cannot crown them the outright #1 that a single rating suggests.

So the honest position is not that the run was less dominant than it looked, the objections people raise for that all fail, but that 19 games is too short to settle a first-place tie against 43 years of champions. Clearly elite, plausibly the best, not provably the best. (Main report, §10 and §11.)
