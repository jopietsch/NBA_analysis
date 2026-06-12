# NBA Home Court Advantage — Findings

Narrative interpretation of the analysis. This file drives the PDF report —
update here and regenerate the PDF to keep them in sync. For regression tables
and coefficient values, see `RESULTS.md` (auto-generated each run).

---

## 1. The Decline

Home court advantage has been consistendly dropping for 40 straight years — through rule changes, labor deals, expansion drafts, and every major shift the game has seen. In 1984, home teams won roughly **65%** of regular-season games. Today it's closer to **55%**.  The playoffs have fallen too, just a little more slowly.

**Why is it happening?** Two forces account for most of it. Referees have been calling the game more neutrally than they used to — in the early 1980s, home teams got more than a full fewer foul per game than road teams; today that gap has nearly disappeared in the regular season and is meaningfully reduced, though still present, in the playoffs. At the same time, the 3-point revolution removed the situation where crowd-influenced officiating mattered most: plays in the paint, where the line between a foul and a no-call is most subjective. Those two trends are probably reinforcing each other. Everything else measured here — rest advantages, altitude, travel distance, pace, competitive balance — shapes how large the home edge is in any given game, but none of it explains why that edge has been falling for four decades. The sections below lay out the evidence for each piece.

The 2020 bubble season (neutral-site playoffs) is excluded from playoff stats. COVID seasons are flagged in the charts as anomalies.

### The numbers are unambiguous

The decline runs at roughly **−0.25 percentage points per year** in the regular season — a number two independent methods agree on. Year after year, era after era, the line bends the same direction. At that pace, you lose another full percentage point every four years. The trend explains 73% of all year-to-year variation in home win rates, which is extraordinary for a sports dataset.

The playoffs decline more slowly (−0.21 pp/year) and with more season-to-season noise — a seven-game series in a small sample can swing things — but the direction is the same.

This isn't a fluke of one bad era or one rule change. The regularity of the decline — not a single step down but a persistent 40-year drift — points to something deep in how the game has changed.

![Figure 1. Home win % per season, 1983–84 through 2024–25. Blue = regular season, green = playoffs. Dashed lines are overall trend fits. Background shading marks rule-change eras.](nba_home_court_advantage_season.png)

---

## 2. Era and Format Period Analysis

The NBA has reinvented itself several times since 1984 — banning zone defense, allowing it back, cracking down on hand-checking, emphasizing freedom of movement, adding the take-foul rule. Each shift changed how the game looks on the floor. None of them reversed the decline. But did any of them cause a discrete jump in it — a step down beyond what the year-by-year trend would predict on its own?

Testing this directly gives a nuanced answer. **In the regular season**, the era breaks do add up to a real combined effect, but the signal comes almost entirely from one transition: the shift into the 1994–95 era, when the NBA tightened hand-checking restrictions, produced a genuine drop of about **2.6 percentage points** beyond what the underlying trend alone would predict. Every other era transition — zone defense legalization in 2001–02, the perimeter hand-checking ban in 2004–05, freedom-of-movement emphasis in 2017–18, the take-foul rule in 2022–23 — shows no real effect once the underlying trend is accounted for. The decline simply passed through those boundaries without a step change.

**In the playoffs**, no era boundary shows any real effect beyond the underlying trend. The postseason decline is a smooth, continuous drift across all rule-change eras — no specific rule produced a step down in playoff home court advantage.

The 2014 Finals format change — switching from 2-3-2 to 2-2-1-1-1 — deserves a closer look. Playoff home win % fell sharply right around that time, from 66.3% in 2003–13 to 59.8% in 2014–25, a drop of 6.4 percentage points. That's a real, reliable difference. But it wasn't the format that caused it. When you account for the long-term year-over-year playoff trend already in motion, the format change adds nothing — the data finds no reliable effect from the scheduling shift itself. The timing was coincidence. The decline was already happening.

![Figure 2. Average home win % by rule-change era. Blue = regular season, green = playoffs.](nba_home_court_advantage_era_bars.png){width=0.5}

![Figure 3. Average home win % by playoff format period (1985, 2003, 2014 format changes). Blue = regular season, green = playoffs.](nba_home_court_advantage_format_bars.png){width=0.5}

---

## 3. Per-Era Trend Lines

The decline isn't perfectly smooth. There are stretches of relative stability and stretches where the floor drops faster. But zoom out and the picture is unmistakable — every era ends lower than the one before it.

The playoffs have consistently given home teams a bigger edge than the regular season. That gap widened through the mid-2000s and has since narrowed back toward where it was in the 1980s.

![Figure 4. Regular-season home win % per season. A separate trend line is fit within each rule-change era. Background shading identifies each era.](nba_home_court_advantage_regular_era.png){height=0.22}

![Figure 5. Playoff home win % per season with a separate trend line per era. Vertical markers indicate playoff format changes (1985, 2003, 2014).](nba_home_court_advantage_playoffs_era.png){height=0.22}

### Rule-Change Eras (regular season and playoffs)

| Era | Seasons | Rule change |
|-----|---------|-------------|
| 1984–94 | 1983–84 through 1993–94 | Illegal defense rules (no zone defense) |
| 1995–01 | 1994–95 through 2000–01 | Hand-checking restrictions; zone still illegal |
| 2002–04 | 2001–02 through 2003–04 | Zone defense legalized, defensive 3-sec added |
| 2005–17 | 2004–05 through 2016–17 | Perimeter hand-checking banned (pace-and-space) |
| 2018–22 | 2017–18 through 2021–22 | Freedom-of-movement emphasis |
| 2023–25 | 2022–23 through 2024–25 | Transition take-foul rule added |

### Playoff Format Periods

| Period | Seasons | Format |
|--------|---------|--------|
| 1984 | 1983–84 | Best-of-5 R1, 2-2-1-1-1 Finals (alternating home court) |
| 1985–02 | 1984–85 through 2001–02 | Best-of-5 R1, 2-3-2 Finals (home court by record) |
| 2003–13 | 2002–03 through 2012–13 | Best-of-7 R1, 2-3-2 Finals |
| 2014–25 | 2013–14 through 2024–25 | Best-of-7 R1, 2-2-1-1-1 Finals |

---

## 4. Win Margin Trends

Here's where it gets counterintuitive.

In the regular season, the overall home-team point margin has declined over time — home teams win by less on average than they used to. But the mechanism is not what you'd expect. Home wins are actually getting **bigger**, not smaller (+0.041 pts/yr). What's pulling the average down is that home **losses** are getting worse: the average home loss margin has grown by nearly a tenth of a point per year.

Home teams are losing more games. And when they lose, they're getting blown out more.

### The spread is widening, not narrowing

You might think: of course home losses look worse — more games are losses now, so you're adding close defeats to the pool. But the data rules that out. Looking at the full distribution of margins across all 34,000+ regular-season games since 1996–97, the biggest home wins (top 10% of margins) are actually growing (+0.045 pts/yr — a reliable finding), while the biggest home losses (bottom 10%) are getting dramatically worse (−0.154 pts/yr — overwhelming evidence). The spread between the two widens by nearly 0.2 pts per year.

When the home team wins, it's increasingly a comfortable victory. When it loses, it's increasingly ugly. The days of the tight home loss that could have gone either way are fading.

### Playoffs show a different pattern

In the playoffs, there's no clear trend in the overall margin. The spread is widening there too (+0.200 pts/yr), but it's driven entirely by big home wins growing — not by home losses getting worse. The net margin is unchanged. Playoff home court still holds, at least in terms of margin when the home team does win.

The regular-season mean home margin (+2.80 pts) is lower than the playoff mean (+4.36 pts), consistent with the higher overall home win rate in the postseason.

![Figure 6. Home team point margin per season. Left: mean margin for all games (regular season and playoffs) with trend lines. Center: mean margin split by home wins vs. losses (regular season). Right: era-bucketed average margin, regular season vs. playoffs.](nba_home_court_margin.png)

---

## 5. Playoff Series Structure

In a seven-game playoff series, not all home games are equal — and the pattern is sharp.

### The home court advantage depends entirely on who's home

When the higher seed plays at home (Games 1, 2, and 5), they win roughly **69–75%** of the time. When the lower seed plays at home (Games 3, 4, and 6), that drops to **55–56%** — barely better than a coin flip. The lower seed's home court advantage is almost completely erased by the simple fact that they're playing a better team.

The alternating pattern isn't subtle. It's one of the sharpest structures in the dataset, and the data confirms it couldn't be explained by chance alone.

### Game 7 is different from what you'd expect

The highest-stakes home game in sports — Game 7 — shows a home win rate of about **65%**, noticeably lower than Games 1 (69%) or 2 (72%). The sample is small (183 games), but the pattern makes sense: only the best road teams survive long enough to force a Game 7. By the time you get there, you're facing a team that has already proven it can win on the road against you. That erodes some of the home edge.

The pattern is not about momentum or pressure or fatigue building through a series. It's simply about who's hosting.

### What this means for the overall decline

Because the gap between higher-seed and lower-seed home games is so large, changing which team hosts which games (as the 2014 format change did) can shift the aggregate playoff home win % mechanically. But once the underlying year-by-year trend is accounted for, the format change adds nothing — the decline was already in progress.

![Figure 7. Home win % by game number within playoff series. Left: pooled G1–G7 home win % with sample sizes and overall playoff baseline. Right: G1–G7 home win % split by era (six lines, era-colored).](nba_home_court_series_breakdown.png)

---

## 6. Box-Score Differentials

If you want to understand *why* home court advantage is shrinking, the box score tells a clear story across four key metrics — all trending in the same direction.

### Foul differential — refs are calling it straight

This is the big one. In the regular season, home teams were called for roughly **1.2 fewer fouls per game** than road teams in the early 1980s. Today that gap has nearly vanished — it's down to about **0.2 fouls per game**. The playoffs show the same pattern: home teams' foul advantage has fallen from **1.6 fewer fouls per game** in 1984–94 to **0.7** today. Referees are calling the game more neutrally than they used to in both contexts. The crowd used to move the whistle. It still does, but far less than it once did. This is almost certainly the single most important driver of the long-run decline.

### Shooting efficiency — the home edge is shrinking

In the regular season, home teams used to shoot meaningfully more efficiently than road teams. That gap has narrowed significantly. This is partly the foul story playing out differently — fewer home free throws means fewer easy points — and partly a broader convergence in shot quality between home and visiting offenses. The playoff shooting-efficiency gap has trended in the same direction, though the smaller postseason sample makes it harder to confirm.

### Shot selection — road teams no longer settle

In the regular season, road teams used to take more 3-point attempts than home teams at the same venue, a sign of being pushed away from the paint. That difference has not just closed but slightly reversed — home teams now take a marginally higher share of 3s. Visiting offenses arrive with the same game plan they run at home. That wasn't true 40 years ago.

### Field goal percentage — confirming the trend

In the regular season, the raw field-goal percentage gap (home minus away) is also closing. It's a cruder measure than weighted shooting efficiency, but it tells the same story. The shooting convergence is real. Free throw percentage and 3-point percentage show no trend — the gap that's closing is at the rim and on 2-point jumpers, where fouls and paint access matter most. In the playoffs, the field-goal efficiency gap moves in the same direction but is too small to confirm given the smaller playoff sample.

![Figure 8. Per-season home-minus-away box-score differentials, 1983–84 through 2024–25. Solid = regular season, dashed = playoffs. Dotted overlays are trend lines. Negative foul diff = home team called for fewer fouls.](nba_home_court_advantage_differentials.png)

---

## 7. Shot Zone Analysis

Zoom in from efficiency to geography and the story sharpens further.

The clearest trend is in **paint access**. Home teams have historically gotten to the restricted area — the highest-percentage shots in basketball — more than road teams. That gap is closing at −0.037 percentage points per year in the regular season. Road defenses are no longer being consistently pushed away from the paint by a more physical home-crowd-fueled officiating environment. They can get inside now.

**Mid-range shots** tell the flip side. In the regular season, road teams used to be pushed to the mid-range more often — the worst shot in modern basketball. That gap is narrowing too (+0.024 pp/yr). Visiting teams are escaping the mid-range at the same rate home teams are. The court is leveling.

In the regular season, corner 3s show no meaningful home/road difference at all. Above-break 3s show a small trend — home teams have gradually taken a slightly larger share of those attempts — but it's minor compared to the paint and mid-range shifts. The 3-point arc isn't where the home advantage story lives. In the playoffs, the shot-zone trends point in the same directions as the regular season, but with fewer games per season the year-to-year swings are larger and the trends are less definitive.

![Figure 9. Home-minus-road shot zone % differentials, 1996–97 through 2024–25. Solid = regular season, dashed = playoffs. RA = restricted area (within ~4 ft of the basket).](nba_home_court_shot_zones.png)

---

## 8. Referee Patterns

Nearly every referee in the NBA has called fewer fouls on the home team than the away team in playoff games, over their entire career. The pattern is nearly universal in the postseason.

### Almost no one is immune

Of 42 officials with at least 50 playoff games in the dataset, **41 show a home-favoring career bias**. The one exception — Joe Forte — is the only qualifying official whose games tilted marginally toward the road team. The league-wide average across all qualifying officials is about **−1.2 fouls per game** in the home team's favor.

The variation across referees is substantial. The most home-favoring officials — Ron Garretson (−2.39 fouls/game, 143 games), Eddie Rush (−2.53, 100 games), and Joe Crawford (−2.29, 160 games) — averaged more than two fewer fouls called on the home team per game across their entire careers. At the other end, Josh Tiven (−0.11, 89 games) is by far the most neutral in the sample.

Nearly all referees tilt the same direction. They just differ in how much.

### The tilt is universal but diminishing

**29 of the 42 qualifying officials show a bias large enough to rule out chance.** A correction for testing all 42 officials at once confirms this isn't just noise — the pattern is real across the board.

The 13 officials without a firmly established bias are those with smaller samples or raw numbers close to zero — not the ones with large home-favoring averages. The directional signal is genuine even where sample size limits what can be detected.

The spread of individual biases has narrowed over time in the raw data. But much of that compression comes from smaller samples in older eras, where a few games can swing an official's career average dramatically. The modern era still shows genuine between-official variance — referees do differ from each other — but the overall level of home-favoring bias has come down across the board.

![Figure 10. Referee home foul bias (playoffs). Left: top/bottom referees ranked by career mean home foul differential. Right: distribution of per-official era-mean foul bias by era (box plots), showing whether the spread of referee biases has narrowed over time.](nba_home_court_referee.png)

---

## 9. 3-Point Shooting and Home Court Advantage

The 3-point revolution and the decline in home court advantage have unfolded on almost exactly the same timeline. That is not a coincidence.

### The lockstep is striking

League-wide 3-point attempt rates have risen from below 10% of all field-goal attempts in the mid-1980s to above 40% today. Over that same period, regular-season home win % has fallen from 65% to 55%. The two track each other almost perfectly over 40 years — as 3-point shooting went up, home court advantage went down, nearly year for year.

The playoffs show the same relationship, though not as tight, likely because fewer games per season add more noise.

### It's not just a coincidence of timing

The deeper test: does a game with more 3-point shooting in a given era still favor the road team more, even after accounting for era? Yes. In the regular season, each 10-percentage-point jump in a game's combined 3-point attempt rate is associated with roughly **−2.3 percentage points** of home win probability — and this holds within any given rule-change era. The 3-point era didn't just happen to coincide with lower home court advantage; higher-3PA games are genuinely harder to win at home.

### Why would this be?

Three things are probably happening simultaneously:

- **Shot selection has equalized.** Road teams used to take worse shots than home teams — pushed to the mid-range, away from the paint. That gap is gone. Both teams now arrive with a 3-point-heavy game plan and run it regardless of venue.
- **More 3s means more variance.** A three-point-heavy game is a higher-variance game. Random outcomes play a bigger role when each possession has a wider range of possible values. The underdog wins more often in high-variance environments — and the road team is usually the underdog.
- **The crowd matters less for catch-and-shoot.** A referee can be swayed by 20,000 screaming fans. A shooter catching and firing a corner 3 in a split second is harder to influence through pressure or biased whistles.

The foul differential trend and the 3-point revolution are probably reinforcing each other. A more neutral whistle enables more 3-point shooting and simultaneously removes the home team's free-throw edge.

![Figure 11. League-wide 3PA rate and home court advantage. Left: dual-axis time series showing 3PA rate (orange, right axis) and home win % (blue, left axis) moving in near-lockstep over 40 years. Center: regular-season scatter (one point per season, era-colored) with trend line. Right: same for playoffs.](nba_home_court_3pa.png)

---

## 10. Pace and Home Court Advantage

Pace was supposed to be part of the story. Faster games, more possessions, smaller samples per game — the theory was that high pace pushes outcomes closer to expected value and erodes the home edge. The data says otherwise.

### Speed has nothing to do with it

At the season level, there is essentially no relationship between league-wide pace and home court advantage — in either the regular season or the playoffs. The era breakdown shows why: pace was **high** in 1984–94 (~102 possessions per team per 48 minutes) when home court advantage was at its peak. It **fell** during the grind-it-out 1990s (~93–94 possessions) while HCA also declined. Then it **rose again** in the modern era (~101 possessions) while HCA continued falling. The relationship is U-shaped across eras. Pace and home court advantage simply don't track each other.

### Game level: faster games actually help the home team

In the regular season, at the individual game level, faster-paced games have **higher** home win probability, not lower — about +2.4 percentage points per 10 extra possessions. But this comes with an important caveat: a blowout produces fast pace because the losing team is fouling and scoring quickly at the end. The pace is partly a result of the home team winning, not a cause of it.

When you use each team's average pace from their *other* games that season — a number that can't be affected by today's outcome — the effect drops substantially and becomes inconclusive. The pre-game pace signal is suggestive at best.

### The bottom line

Pace doesn't explain the decline. The NBA of 1984–94 played at roughly the same speed as today's game, yet home court advantage was 10 percentage points higher. Whatever is causing the decline, it isn't about how many possessions teams get.

![Figure 12. League-wide pace (possessions per 48 min) and home court advantage. Left: dual-axis time series showing pace (purple, right axis) and home win % (blue, left axis) over time, era-shaded. Center: regular-season scatter (one point per season, era-colored) with trend line. Right: same for playoffs.](nba_home_court_pace.png)

---

## 11. Competitive Balance and Parity

Has the league gotten more equal? Yes, slowly. Is that why home court advantage is shrinking? Mostly no — but there's a small wrinkle.

The simple correlation between how spread out teams' win percentages are in a given year and the regular-season home win rate that year is essentially zero. The 1995–01 era, when Jordan, Shaq, and a handful of dynasties dominated, was one of the most unequal stretches in modern NBA history — and regular-season home court advantage was already declining. Parity and HCA just don't move together.

### Strip out the shared trend, and something small appears

Both series trend downward over 40 years. When two things trend in the same direction, they can look related even when they're not. Remove that shared trend and look at year-to-year fluctuations: in years when the league gets slightly more equal, regular-season home court advantage tends to slip a bit too — a modest, consistent signal confirmed by two different methods.

The effect is real but modest. Parity isn't the engine driving the 40-year decline. It's a factor at the margins — a small nudge in the right direction in more equal years, lost in the noise the rest of the time. This parity analysis focuses on regular-season data; the playoff sample is too small — roughly 15 games per season — to run a reliable year-level parity test.

![Figure 13. Competitive balance and home court advantage. Left: home win % (blue, left axis) and team win% std dev (red, right axis) over time — lower std dev = more equal league. Right: scatter of parity std dev vs. home win % per season, colored by era, with trend line.](nba_home_court_parity.png)

---

## 12. Franchise Home Court Advantage

Home court advantage is not the same everywhere. Some arenas have historically been fortresses. Others are closer to playing on a neutral court with a slight scheduling edge.

The right way to measure this is home win% minus road win% — not just home win%, which mostly measures how good the team is. The 1990s Bulls won everywhere. What matters for home court is the *gap* between how they played at home versus on the road.

### Regular Season

Across 39 franchises with at least 50 home games in the dataset, the league mean home-road gap is **+20.2 percentage points**. Every single franchise shows a positive gap — not one team in the dataset has historically been better on the road than at home over a meaningful stretch.

But the range is enormous. At the top, altitude franchises dominate:

- **Denver: +27.3 pp** — ranked #1 in the league, and it's not particularly close
- **Utah: +25.9 pp** — ranked #2

The mile-high advantage is real and measurable. Visiting teams playing their first game at elevation are at a physiological disadvantage that doesn't disappear just because you're a playoff team. Portland (+22.8 pp) and Seattle (+24.4 pp) also rank near the top.

At the other end: the Brooklyn Nets (+13.4 pp) and LA Clippers (+15.3 pp) show the smallest advantages among well-sampled franchises. Playing in markets where opposing fan bases often pack the building can genuinely erode the home edge.

The Kansas City Kings post the highest raw number (+35.4 pp) but played only one season in the dataset. With that little data, the margin of error is enormous — the estimate is not reliable at face value, and after adjusting for sample size, it falls in line with other franchises.

### Playoffs

In the playoffs, the mean home-road gap jumps to **+27.1 pp** — notably higher than the regular season. This isn't a contradiction of the lower overall playoff home win rate. It reflects that playoff home teams are almost always as good as or better than their opponents, amplifying the venue effect relative to the regular season where good teams play bad ones all the time.

Utah (+39.7 pp raw), Portland (+39.3 pp), and Seattle (+37.7 pp) lead the raw playoff table. The Lakers (+31.7 pp) and Celtics (+30.2 pp) also rank highly.

Here's the sobering caveat: **with the playoff sample sizes available per franchise — as few as 20 home games over 42 seasons for some teams — the data simply cannot reliably separate real franchise differences from random variation.** After adjusting for sample size, all playoff franchise HCA estimates collapse toward the league mean. The LA Clippers' apparent negative playoff HCA (−3.6 pp) is a good illustration — it's almost certainly just noise from 28 games.

### Regular Season vs. Playoffs

Teams that protect home court in the regular season tend to do so in the playoffs too — there's a real but modest connection between the two. Denver and Utah are at or near the top of both lists. But the playoff sample is too thin to make strong individual franchise claims — that broad pattern is the most reliable signal available.

![Figure 14. Franchise home court advantage. Left: horizontal bar chart of regular-season HCA by franchise, sorted from largest to smallest, across all seasons. Right: scatter of regular-season HCA vs. playoff HCA (one point per franchise with sufficient data); y=x diagonal shows where the two are equal.](nba_home_court_team_hca.png)

---

## 13. The Usual Suspects: Rest, Travel, Altitude, and Time Zones

Ask a fan why home teams win and you'll hear about tired visitors: the road team flew in last night, crossed two time zones, and is playing its fourth game in five nights. All of that is real. So the question this section answers is whether any of it can explain why home court advantage has been shrinking for 40 years. The short answer: no. Each of these factors shapes how big the home edge is in any given game — but none of them moved over four decades. A factor that never changed can't explain a trend that never stopped.

### Rest is real — and it hasn't changed

When the home team has more rest than the visitor, it wins **62.9%** of regular-season games. When the visitor is more rested, that drops to **57.7%** — about a 5-point swing, worth roughly **+1.5 percentage points per extra day of rest**. That makes rest one of the bigger levers in the sport.

In the playoffs the raw number looks even bigger: home teams with a rest edge win **75.5%** of those games. But playoff rest is mostly a reward for winning quickly — the team that finished its series early gets the extra days off while its next opponent battles seven games. Account for team quality and the playoff rest effect shrinks back to the regular-season level and can no longer be confirmed.

What matters for the decline: the rest effect has stayed stable across all eras, in both the regular season and the playoffs. There's no evidence the per-day advantage has grown or shrunk as scheduling has evolved.

### Travel barely registers

Flying across the country to play should matter. The data says it barely does. Splitting regular-season games into distance buckets — under 500 miles up through 1,500+ — produces home win rates clustered within a point of the overall baseline. The per-mile effect is real but negligible: less than 0.1 percentage point per 100 miles, so even a 2,500-mile coast-to-coast flight is worth only about 2 points. In the playoffs, the effect disappears entirely. Road trips are planned far in advance, teams fly charter and arrive a day early — modern logistics have essentially neutralized distance.

### Altitude and time zones

**Altitude** gives Denver and Utah a clear edge in the regular season — about **+8.2 percentage points** beyond what their records alone would predict. In the playoffs that edge disappears. When those teams make deep runs, they're facing opponents good enough to overcome the thin air.

**Time zones** cost the visitor about 0.6 percentage points per zone crossed in the regular season — small but real, though it only shows up clearly once era and altitude are accounted for. With only 107 coast-to-coast playoff games in 42 seasons, there's no way to detect a postseason effect either way.

### Put them all in one model, and the decline is still standing there

A game-level model that knows each game's rest situation, altitude, time-zone gap, COVID conditions, and era splits its explanatory power roughly in half: **50% to the schedule-and-geography factors combined, 50% to era alone** — meaning *which decade the game was played in* predicts the winner as well as everything else put together.

That "era effect" is not a competing cause. It's the decline itself, measured — the bucket holding everything about the game that changed across four decades: the vanishing foul-call edge (Sections 6 and 8), the disappearing shot-quality advantage (Section 7), the 3-point revolution (Section 9). Home advantage is **8.9 percentage points lower** in 2023–25 than in 1984–94, and almost none of that traces to rest, travel, altitude, or time zones. They're constants; the era effect is the variable. The one discrete break in the regular season is the hand-checking restrictions of 1994–95, worth about a 2.6-point drop beyond the gradual slide — every other rule-change boundary blends into the smooth decline, and in the playoffs no era boundary produces a discrete effect at all.

The cleanest version of the test: compare before and after 2014, when the recent acceleration began. The rest, altitude, and time-zone effects are statistically unchanged — but the baseline home advantage dropped by **4.6 percentage points**. The factors held still while the floor fell.

### So what does explain it?

Not logistics — the game itself. Two forces, reinforcing each other: the whistle got more neutral (Section 8), and the 3-point revolution pulled the game away from the basket, where crowd-influenced calls mattered most (Section 9). You can see their footprint in the box score — the home team's old shot-quality edge, better shooting and better access to the paint, has all but evaporated (Section 7). This model can't see those forces directly — foul calls are part of a game's outcome, and 3-point shooting rose in lockstep with the eras — but it shows exactly where they live: inside the era effect, which is where the rest of this report points.

---

## 14. Summary

Home court advantage has fallen by about **10 percentage points** in the regular season over 40 years, from roughly 65% in 1984 to roughly 55% today. The playoff decline is smaller but follows the same trend. This is one of the most consistent, persistent trends in any major American sports dataset.

The decline isn't about games getting closer — when home teams win, they're actually winning by more than they used to. What's changed is that they lose more often, and when they do, they lose bigger. The spread of outcomes has widened; the overall win rate has dropped.

*How to read these tables: "pp" means percentage points — a fall from 65% to 55% is a drop of 10 pp. The "Evidence" column summarizes the strength of each finding.*

**Regular season — what the prediction model credits** (share of the model's explained variation):

Each factor's share reflects its average contribution across all possible orderings — an order-independent measure. Altitude's outsized 26% share reflects a very large per-game effect (+8.2 pp) concentrated in Denver and Utah home games.

| Factor | Share | Effect | Evidence |
|---|---|---|---|
| Era (structural decline) | 50% (seq: 56%) | Home advantage is 8.9 pp lower in 2023–25 than in 1984–94 | Very strong (p < 0.001) |
| Altitude (Denver / Utah) | 26% (seq: 25%) | +8.2 pp extra home advantage at altitude | Very strong (p < 0.001) |
| Rest differential | 18% (seq: 16%) | +1.5 pp per extra day of rest vs. the visitor | Very strong (p < 0.001) |
| COVID flag | 5% (seq: 1%) | −2.3 pp in COVID-impacted seasons (2020–21) | Significant (p = 0.045) |
| Time-zone differential | 2% (seq: 2%) | −0.6 pp per time zone the visitor crosses | Solid (p = 0.005) |

**Regular season — confirmed mechanisms** (significant contributors to the decline):

| Factor | What changed | Evidence |
|---|---|---|
| Referee fouls (refs more neutral) | Home teams' foul advantage shrank from 1.2 fewer fouls/game in 1984–94 to 0.2 today | Very strong (p < 0.001) |
| Shot quality (shooting + paint access) | Home shooting-efficiency edge fell from +1.6 pp to +1.0 pp; home paint-access edge fell from +1.3 pp to +0.4 pp | Very strong (p < 0.001) |
| League-wide 3-point shooting | Seasons with more 3-point shooting have lower home win % (correlation −0.90); even within an era, higher-3PA games favor the visitor (−2.3 pp per 10 pp of 3PA rate) | Very strong (p < 0.001) |

**Regular season — tested, not a driver** (hypotheses examined and ruled out or negligible):

| Factor | Finding | Evidence |
|---|---|---|
| Travel distance | Statistically real but negligible: −0.08 pp per 100 miles | Not a driver (p = 0.010, effect too small to matter) |
| Game pace (possessions/game) | No season-level correlation with HCA; faster games favor the home team game-by-game, but pace has no common trend with the decline across eras | No effect on the decline (season-level p = 0.07) |
| Competitive balance / parity | Raw cross-season correlation near zero; detrended tests show a weak year-to-year link (r ≈ −0.35, p ≈ 0.02) but parity explains none of the long-run trend | Not a primary driver (weak within-trend association only) |

**Playoffs — what the prediction model credits**:

| Factor | Effect | Evidence |
|---|---|---|
| Era (structural decline) | Every era since 1984–94 has lower home advantage | Strong (GLM p = 0.003, HAC p < 0.001) |
| Rest differential | +2.3 pp/day bivariate; shrinks to +1.5 pp/day and loses significance when same-season win% differential is controlled — effect is confounded by team strength | Confounded: bivariate p = 0.014, quality-controlled p = 0.146 (not significant) |
| Altitude (Denver / Utah) | No altitude edge in the playoffs (−1.8 pp) | No significant effect (p = 0.59) |
| Time-zone / distance | No meaningful effect of either | No significant effect (p = 0.28 and p = 0.71) |

**Playoffs — confirmed mechanisms** (significant contributors to the decline):

| Factor | What changed | Evidence |
|---|---|---|
| Referee fouls (refs more neutral) | Home teams' foul advantage shrank from 1.6 fewer fouls/game in 1984–94 to 0.7 today | Strong (p < 0.01) |
| League-wide 3-point shooting | Playoff seasons with more 3-point shooting have lower home win % (correlation −0.47) | Strong season-level (p = 0.002); marginal within era (p = 0.054) |

**Playoffs — tested, not a driver** (hypotheses examined and ruled out or inconclusive):

| Factor | Finding | Evidence |
|---|---|---|
| Shot quality (shooting + paint access) | Both edges trend downward in the same direction as the regular season, but the playoff sample is too small to reach significance | No significant effect |
| Game pace | No season-level correlation with playoff HCA; pace does not track the playoff decline | No effect on the decline (season-level p = 0.47) |

**Beyond the decline — how home court behaves** (findings about the shape of home advantage, not its trend):

| Finding | What the data shows |
|---|---|
| Playoff home court mostly belongs to the better team | Higher seeds hosting Games 1, 2, and 5 win 69–75%; lower seeds hosting Games 3, 4, and 6 win just 55–56% — barely better than a coin flip. And Game 7 is weaker than you'd guess (about 65%), because only road teams good enough to win away games survive that long |
| The 2014 Finals format change is innocent | Playoff home win % fell 6.4 pp (66.3% to 59.8%) right around the switch from 2-3-2 to 2-2-1-1-1, but the decline already in motion fully explains it — the format itself adds nothing |
| Every arena helps, but some help far more | All 39 franchises have won more at home than on the road — league average gap: +20.2 pp in the regular season, +27.1 pp in the playoffs. Denver (+27.3 pp) and Utah (+25.9 pp) lead the regular-season list, thanks to altitude |
| Playoff margins tell their own story | Regular-season home margins are shrinking on average; playoff margins aren't. The playoff spread widens only because big home wins keep getting bigger — playoff home losses aren't getting worse |

**The short version:** The crowd used to move the whistle. The referee would call a foul on the road player where they might let it go at home, and that 1.2-foul-per-game edge compounded into a 10-point win rate advantage over a full season. Now refs call it straight — or at least straighter — and the 3-point revolution has removed the one situation where crowd influence mattered most: interior contact, where the line between a foul and a no-call is most subjective.

Every other factor — rest, altitude, time zone, travel, pace, parity — explains the level of home advantage or modulates it at the margins. None of them explain why it's been falling for 40 years. The game itself changed — the whistle went neutral and the shooting moved outside. The crowd lost its grip on the outcome.

For specific coefficient values, effect sizes, significance levels, and era breakdowns, see `RESULTS.md`.
