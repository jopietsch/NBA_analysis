# How Much of Home Court Advantage Does Our Analysis Explain?

**The question:** Across everything in RESULTS.md, how much of the *total* home court advantage — and how much of its *change over time* — is actually accounted for, in both the regular season and the playoffs?

**The short answer:** The mediation analysis closes the loop. The four box-score channels (shooting, referee fouls, turnovers, rebounds) account for 95% of both the regular-season level and its decline. The picture is less complete for the playoffs — 94% of the level, 65% of the decline — where the trend is noisier and more recent.

---

## The Level: Why Home Teams Win at All

### Regular season

The baseline home win rate is 60.3% across the full sample — a total advantage of about 10.3 points above a coin flip. The mediation analysis converts each box-score differential into a win-percentage share:

| Channel | Mean home edge | Contribution |
|---|---|---|
| Shooting (eFG% diff) | +1.28 pp | +4.4 pp — 43% of level |
| Rebounding | +1.56 boards | +2.6 pp — 25% of level |
| Referee fouls | −0.74 fewer on home team | +1.5 pp — 14% of level |
| Turnovers | −0.38 fewer by home team | +1.3 pp — 13% of level |
| Unexplained | — | +0.5 pp — 5% of level |

Shooting is the biggest single component — nearly half the home edge comes from home teams simply making a higher percentage of their shots. Rebounding is second, referees third.

The remaining drivers measured elsewhere — rest asymmetry (~+1 pp), altitude (+8.2 pp for Denver/Utah across ~7% of games translating to ~+0.5 pp league-wide), and time zones (~0) — fall inside the unexplained 5%, or overlap with the channels above.

### Playoffs

The baseline is 64.3%, or about 14.3 points of edge — higher than the regular season primarily because the home team is usually the better team. The mediation channels carry **94% of the playoff level**:

| Channel | Mean home edge | Contribution |
|---|---|---|
| Shooting (eFG% diff) | +1.48 pp | +4.7 pp — 33% of level |
| Turnovers | −0.92 fewer by home team | +3.1 pp — 22% of level |
| Rebounding | +1.85 boards | +3.1 pp — 22% of level |
| Referee fouls | −1.27 fewer on home team | +2.5 pp — 17% of level |
| Unexplained | — | +0.9 pp — 6% of level |

The referee component is larger in the playoffs (17% vs 14%) because the historical foul bias was steeper — 1.27 fewer per game vs 0.74 in the regular season. Seeding also contributes: the quality-gap analysis shows the home team's record advantage over its opponent adds roughly 1.5–2 points of the playoff premium above the regular season. The Games 3–4 underdog check gives the floor: a weaker team at home still wins 51.8%, meaning the pure venue effect is worth about 2 points even when quality works against you.

---

## The Change: The ~10-Point Decline

### Regular season (−0.245 pp/yr over 42 years)

The mediation trend decomposition splits the total decline across what changed in each channel:

| Channel | Trend in differential | Contribution to decline |
|---|---|---|
| Rebounding | −0.042 boards/yr | −0.070 pp/yr — 29% of decline |
| Turnovers | Home team's turnover edge shrinking (+0.020/yr) | −0.067 pp/yr — 28% of decline |
| Referee fouls | Foul gap narrowing (+0.023/yr) | −0.045 pp/yr — 18% of decline |
| Shooting (eFG%) | Home shooting edge narrowing (−0.015/yr) | −0.051 pp/yr — 21% of decline |
| Unmediated | — | −0.012 pp/yr — 5% of decline |

**The channels carry 95% of the decline.** Rebounding and turnovers together account for more than half — a finding that gets overlooked when the analysis focuses on referees and shooting, which are the most visible. The home rebound advantage has shrunk by 0.042 boards per game per year; over 42 years that's nearly 1.8 boards per game erased. The home team's turnover edge has similarly compressed. These probably both reflect the same underlying shift as the three-point revolution: a more spread-out, perimeter-oriented game gives interior home advantages — the scramble for offensive rebounds, the ball-pressure familiarity of a home crowd — less opportunity to express themselves.

**Ruled out, quantitatively (~0% each):** rest, altitude, and time zone effects are stable across eras. Pace, parity, travel distance, and cross-timezone road trips show no meaningful association with the decline. COVID produced a real −2.3 pp dip but reversed when arenas refilled.

### Playoffs (−0.208 pp/yr over 41 years)

The playoff decline is only 65% explained by the box-score channels:

| Channel | Trend in differential | Contribution to decline |
|---|---|---|
| Rebounding | −0.033 boards/yr | −0.056 pp/yr — 27% of decline |
| Referee fouls | Foul gap narrowing (+0.020/yr) | −0.038 pp/yr — 18% of decline |
| Turnovers | Narrowing (+0.007/yr, not reliable) | −0.024 pp/yr — 12% of decline |
| Shooting (eFG%) | Narrowing (−0.006/yr, not reliable) | −0.018 pp/yr — 9% of decline |
| Unmediated | — | −0.072 pp/yr — 35% of decline |

**Seeding compression: 0%.** Controlling for the quality gap between home and visiting team leaves the year trend fully intact (101% retained). The playoff decline is genuine home-court erosion, not a bookkeeping artifact of closer matchups (see FINDINGS_SEEDING.md).

**Format changes (1985 / 2003 / 2014): 0%** once the underlying year trend is accounted for.

The 35% unmediated playoff trend is real. The playoff decline arrived later and more sharply (mostly post-2018) and the sample is smaller (3,207 games vs 47,879). The channels available — box-score differentials — are noisy at the game level in the postseason. Some of the unmediated share likely reflects crowd-effect compression (playoff road teams are more experienced, better prepared, and playing in front of hostile crowds that motivate rather than rattle) that simply doesn't show up in any single box-score column.

---

## Summary Scorecard

| Question | Regular season | Playoffs |
|---|---|---|
| Total HCA level (~10 pp / ~14 pp) | **95% explained** via four channels: shooting 43%, rebounding 25%, fouls 14%, turnovers 13%; only 0.5 pp unexplained | **94% explained** via same channels; seeding adds ~1.5–2 pp above the RS baseline; pure venue floor ≈ 2 pp (G3/G4 underdog games) |
| Change over time (−10 pp / −8.6 pp) | **95% mediated**: rebounding 29%, turnovers 28%, shooting 21%, fouls 18%; pace/parity/travel/format all ruled out at ~0% | **65% mediated**: rebounding 27%, fouls 18%, turnovers 12%, shooting 9%; seeding and format ruled out at 0%; 35% unmediated (mostly post-2018 decline not yet flowing through measured channels) |
