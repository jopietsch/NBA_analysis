# NBA Player Rating Systems: Inventory

```{=typst}
#align(center)[_Draft_]
```

::: {.content-visible when-format="html"}
<p style="text-align:center"><em>Draft</em></p>
:::

This catalog lists every major NBA player rating system, how each is acquired, what seasons it covers, and what kind of availability it has.
"Recompute" means we run the formula on public data we fetch ourselves.
"Results-only" means we download a published snapshot.
"Proprietary" means neither the data nor the methodology is publicly available.

---

## Tag definitions

| Tag | Meaning |
|---|---|
| **Recompute** | Formula is public; inputs are fetchable from nba_api or Basketball-Reference; we run the computation ourselves |
| **Results-only (auto)** | Published values are downloadable as structured files (CSV/JSON/API); no recompute needed |
| **Results-only (snapshot)** | Values must be scraped or manually captured from a web page; we store the snapshot with date and URL |
| **Proprietary** | Neither the methodology nor the data is publicly accessible; documented here as a blind spot |

---

## Box-score recompute systems

These use standard box-score totals (points, rebounds, assists, steals, blocks, turnovers, field-goal attempts, free-throw attempts, minutes) plus league and team context, all fetchable from nba_api.

The Coverage column below is the era each metric is *defined* for; the Coverage summary near the end of this doc gives the narrower range this project can actually fetch and compute (1983–84 on, where nba_api's box-score totals begin).

| System | Components | Coverage | Source | Notes |
|---|---|---|---|---|
| **Game Score** (Hollinger) | PTS, FGM, FGA, FTA, FTM, OREB, DREB, STL, AST, BLK, TO | 1983–84 to present | nba_api `LeagueDashPlayerStats` | Simple single-game quality measure; per-game average used for season ranking |
| **PER** (Player Efficiency Rating) | Full box totals + league pace + team possessions | 1951–52 to present (box-score era) | nba_api + league-average context | Hollinger formula; league-average PER is always 15; minutes-weighted |
| **TS%** (True Shooting Percentage) | PTS, FGA, FTA | 1983–84 to present | nba_api | `PTS / (2 * (FGA + 0.44 * FTA))`; rate stat, no volume |
| **eFG%** (Effective Field-Goal Percentage) | FGM, 3PM, FGA | 1979–80 to present | nba_api | `(FGM + 0.5 * 3PM) / FGA` |
| **USG%** (Usage Rate) | FGA, FTA, TO, team totals | 1983–84 to present | nba_api | Approximate using `(FGA + 0.44*FTA + TO) / (team_FGA + 0.44*team_FTA + team_TO) * 5` |
| **Win Shares** (OWS / DWS / WS / WS/48) | Full box + team + league | 1946–47 to present | nba_api + Basketball-Reference methodology | Separate offensive and defensive components; WS/48 normalizes for playing time |
| **BPM** (Box Plus/Minus, OBPM / DBPM) | Advanced box-score rates + team point margin | 1973–74 to present | nba_api + weights fit to BBR's published OBPM/DBPM | Two stages: a linear fit to reproduce BBR, then a team-margin anchor so each team's players sum to its point differential. Recomputed and validated against Basketball-Reference (BPM r ≈ 0.930 on 361 players). |
| **VORP** (Value Over Replacement Player) | BPM, minutes, team games | 1973–74 to present | Derived from BPM | `VORP = (BPM - (-2.0)) × (share of team minutes) × (team games / 82)`; recomputed and validated against Basketball-Reference (VORP r ≈ 0.961). |

### Data endpoints used for recompute

| Endpoint | Used for | nba_api quirk |
|---|---|---|
| `LeagueDashPlayerStats` (Totals, Regular Season) | Per-player box totals | `season=` (not `season_nullable=`); returns one row per player |
| `LeagueDashPlayerStats` (Per100Possessions) | Per-100 rates for BPM | Same endpoint, `per_mode_detailed="Per100Possessions"` |
| `LeagueDashTeamStats` | Team totals for USG%, WS, BPM team adjustments | `season=`, `per_mode_detailed="Totals"` |
| `LeagueStandingsV3` | Team wins/losses for WS allocation | `season=` |
| `LeagueDashLineups` or derived | League-average pace, eFG, FT-rate | Derived from summing `LeagueDashTeamStats` |

---

## Results-only systems (auto-download)

Published values are available as structured files.
We download and cache; no recomputation.

| System | Availability | Coverage | Acquisition | Snapshot date |
|---|---|---|---|---|
| **RAPTOR** (FiveThirtyEight) | Results-only (auto) | 2013–14 to 2022–23 (FTE shut down April 2023) | GitHub: `fivethirtyeight/data` → `nba-raptor/` CSVs; one file per season | See source registry below |
| **DARKO DPM** (Kostya Medvedovsky) | Results-only (snapshot) | 2013–14 to present | <https://darko.basketball> public results page; downloadable CSV or API query | Projection system (like PECOTA/Steamer), not a season average: weights recent games more heavily, updates daily. Compare with caution against season-average metrics. |
| **DRIP** (Opta Analyst) | Results-only (auto) | 2021–22 to present | <https://theanalyst.com>, DRIP player ratings page; structured download available | Daily-updated like DARKO: now-casts current true talent rather than averaging the full season. Offensive and defensive components. |

---

## Historical / inactive systems

Systems that are no longer updated but whose methodology influenced current metrics or whose historical data is still downloadable.

| System | Active through | Notes |
|---|---|---|
| **PIPM** (Player Impact Plus/Minus, Jacob Goldstein) | ~2020–21 | No longer public. Goldstein joined the Washington Wizards in 2020 and PIPM went dark. Its box-score prior coefficients and luck-adjustment methodology were inherited by BBall-Index's LEBRON. Historical data partially available via BBall-Index. |
| **ESPN RPM** (Real Plus-Minus, Jeremias Engelmann) | ~2022–23 | ESPN stopped publishing publicly around 2023. Engelmann also built the foundational RAPM dataset most other systems calibrate against; see source registry. |

---

## Results-only systems (snapshot)

Values must be scraped or copied from a web page.
We store the snapshot with acquisition date and URL.

| System | Availability | Coverage | Acquisition | Snapshot date |
|---|---|---|---|---|
| **EPM** (Estimated Plus/Minus, dunksandthrees.com) | Results-only (snapshot, partly paywalled) | 2012–13 to present | Top-N table visible without subscription; full rankings require subscription. Snapshot available values. | TBD at build time |
| **LEBRON** (BBall-Index) | Results-only (snapshot, partly paywalled) | ~2015–16 to present | Methodology documented publicly; summary values visible on site; full export requires subscription. Snapshot available values. | TBD at build time |
| **ESPN RPM** (Real Plus-Minus) | Results-only (snapshot) | 2012–13 to ~2022–23 (ESPN stopped publishing mid-2023) | ESPN player stats page; values were published as a table column. Last archived snapshots available via Wayback Machine. Feasibility: verify at build time. | TBD at build time |

---

## Human / reputation rankings

Awards and media rankings measure perception and reputation, not just on-court production.
Included as a distinct category to compare against model-based systems.

| System | Availability | Coverage | Acquisition | Notes |
|---|---|---|---|---|
| **MVP vote share** | Results-only (auto) | 1955–56 to present | Basketball-Reference award voting pages (scrapeable) | Vote share = first-place points / max possible |
| **All-NBA selections** (1st/2nd/3rd team) | Results-only (auto) | 1946–47 to present | Basketball-Reference (scrapeable) | Encode as points: 1st-team = 5, 2nd-team = 3, 3rd-team = 1 |
| **All-Star selection** | Results-only (auto) | 1950–51 to present | Basketball-Reference (scrapeable) | Binary per season; starter vs. reserve not distinguished in initial pass |
| **ESPN #NBArank** | Results-only (snapshot) | ~2012 to present | Published annually on ESPN as a ranked list; snapshot the top-100 | TBD at build time; years vary |
| **The Ringer Top 100** | Results-only (snapshot) | ~2018 to present | Published annually; snapshot the ranked list | TBD at build time; years vary |

---

## Proprietary systems (blind spot)

These are mentioned for completeness.
We cannot access the data or methodology.
The analysis will note this gap where relevant.

| System | Organization | Why unavailable | Acknowledged blind spot |
|---|---|---|---|
| **Second Spectrum tracking models** | Second Spectrum (NBA official provider) | Full player-tracking data and derived metrics are licensed exclusively to teams; not publicly released | Tracking-based defensive metrics and off-ball movement are not captured by any public system |
| **Team internal models** | Individual NBA franchises | Proprietary; methodologies and outputs are not disclosed | Unknown; likely blends tracking + lineup + matchup data unavailable publicly |
| **Synergy sports tracking** | Synergy Sports | Subscription product; data not available for recompute | Play-type breakdown (e.g., pick-and-roll ball handler efficiency) only partially visible via public summaries |

---

## Source registry

Exact acquisition paths for each auto-download or snapshot source.
Updated as each is pulled.

| Source | URL / path | Acquisition method | Coverage | Last pulled |
|---|---|---|---|---|
| RAPTOR (FiveThirtyEight) | <https://github.com/fivethirtyeight/data/tree/master/nba-raptor> | `wget` or `requests.get` on per-season CSV URLs; filenames: `historical_RAPTOR_by_player.csv`, `modern_RAPTOR_by_player.csv` | 2013–14 to 2022–23 | TBD |
| DARKO DPM | <https://darko.basketball/p/> | CSV export from public results page; or `requests.get` on undocumented JSON endpoint (inspect network tab) | 2013–14 to present | TBD |
| DRIP (Opta Analyst) | <https://theanalyst.com/articles/nba-drip-daily-updated-rating-of-individual-performance> | Download link on the DRIP page; inspect for structured CSV/JSON endpoint | 2021–22 to present | TBD |
| MVP vote share | `https://www.basketball-reference.com/awards/awards_{year}.html` | BBR scrape via `nbakit.bbr.get_soup()` | 1955–56 to present | TBD |
| All-NBA / All-Star | <https://www.basketball-reference.com/awards/> | BBR scrape | 1946–47 to present | TBD |
| EPM (dunksandthrees) | <https://dunksandthrees.com/epm> | Manual snapshot of visible table; paywalled rows excluded | TBD | TBD |
| LEBRON (BBall-Index) | <https://bball-index.com/lebron/> | Manual snapshot of visible rankings | TBD | TBD |
| ESPN RPM | Wayback Machine archives of ESPN player stats | Manual or `requests.get` on archived URLs; verify availability | 2012–13 to ~2022–23 | TBD |
| ESPN #NBArank | ESPN.com annual feature | Manual snapshot | Annual | TBD |
| The Ringer Top 100 | The Ringer annual feature | Manual snapshot | Annual | TBD |

---

## Coverage summary

The analysis focuses on 2025–26 as the primary test season.
Multi-season coverage extends as far back as each source allows.
The crosswalk (player identity reconciliation across systems) is keyed on `(player_normalized_name, season, team_abbr)` with a hand-maintained override table for collisions.

| Recompute systems | Active as of 2025–26 | How far back |
|---|---|---|
| Game Score, PER, TS%, eFG%, USG% | Yes | 1983–84 (nba_api coverage) |
| Win Shares | Yes | 1983–84 (nba_api) |
| BPM 2.0 / VORP | Yes | 1983–84 (nba_api) |

| Results-only systems | Active as of 2025–26 | How far back |
|---|---|---|
| RAPTOR | No (FTE defunct) | 2013–14 to 2022–23 |
| DARKO DPM | Yes (projection-style) | 2013–14 |
| EPM | Yes (partial) | 2012–13 |
| LEBRON | Yes (partial) | ~2015–16 |
| DRIP | Yes | 2021–22 |
| ESPN RPM | No (defunct ~2023) | 2012–13 to ~2022–23 |
| PIPM | No (defunct ~2020) | Historical via BBall-Index |
| MVP vote share, All-NBA, All-Star | Yes | Historical |
| ESPN #NBArank, Ringer Top 100 | Yes (annual) | ~2012 |

---

## Which systems can be split regular season vs playoffs

A separate question from coverage: can a system produce a *playoff-only* value, so you can measure whether a player rose or fell once the postseason started?
Only the box-score recompute family can.
The reason is mechanical, and it splits the inventory cleanly into three groups.

| Group | Playoff split? | Why |
|---|---|---|
| **Box-score recompute** (Game Score, PER, WS/48, BPM/OBPM/DBPM, VORP) | Yes | We run the formula ourselves, so we can run it on postseason totals just as easily as on regular-season totals. Each value is renormalized within its own season type, so a playoff PER is comparable to its regular-season twin. |
| **Impact metrics** (RAPM family, RAPTOR, EPM, LEBRON, DARKO, DRIP) | No | These need thousands of possessions to separate a player from his lineup. A first-round loss is about six games; even a Finals run is far short of what a stable estimate needs. The published third-party versions are season figures with no postseason cut, and DARKO/DRIP are now-cast projections, not a season split at all. |
| **Human / reputation** (MVP, All-NBA, All-Star, media ranks) | No | These are awarded once per regular season. There is no postseason equivalent to difference against. |

So the regular-season-vs-playoff comparison in the findings (Section 8) is box-score-only by necessity, not by choice.
Two guards keep that comparison honest given how small a playoff sample is.
The shift is measured only for players with at least 150 playoff minutes, then pulled toward zero by playoff minutes (half weight at 200), so a short, lucky run can't top the list.
And each shift also carries a range built by re-drawing the player's games at random 1000 times, so a rise only counts as real when that range stays clear of zero.

---

## Open items

- RAPM (Regularized Adjusted Plus/Minus): computed in-house from nba_api play-by-play (PlayByPlayV3) for 1996-97 through 2025-26 (bare RAPM; the prior-informed RAPM+prior starts 1997-98, since it needs a preceding season to pool), reconstructed into five-on-five possessions and fit with cross-validated ridge regression. Two versions: a bare single-season RAPM (zero-mean prior) kept to show the raw noise, and RAPM+prior, which pools three seasons with recency weights and shrinks each player toward a BPM prior (offense toward OBPM, defense toward DBPM). RAPM+prior feeds the consensus. The RAPM family is under repair: the bare possession-based RAPM still surfaces implausible leaders (low-minute players topping the league), a known bug flagged as a separate follow-on. Fixing BPM this session improved RAPM+prior, which shrinks toward the BPM prior, but the bare RAPM underneath still needs its own fix. Still open: that fix, loading a public RAPM snapshot to validate the values, and a luck adjustment / tracking-based prior to approach EPM or LEBRON (the player-tracking inputs are not publicly available).
- Minutes qualifier threshold: TBD. Initial candidate: 500 minutes (roughly 25+ games at 20 min/game) for 2025–26; adjusted for multi-season pools.
