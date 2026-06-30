# NBA Player Rating Resources

A curated reading list of the best blog posts, methodology writeups, forum threads, and reviews of NBA player rating systems.
Organized by topic.
Each entry includes a one-paragraph summary of what it covers and why it is worth reading.

---

## Primary methodology documents

These are the original introductions or official methodology pages for each major metric.
Read these before anything else.

### Box Plus/Minus (BPM): original 2014 introduction
**URL:** <https://www.sports-reference.com/blog/2014/10/introducing-box-plusminus-bpm-2/>  
**Author:** Sports-Reference / Daniel Myers  
**What it covers:** The first public announcement of BPM on Basketball-Reference, with an overview of how the metric works and what problem it was trying to solve. Myers explains that BPM estimates a player's total contribution using only box-score inputs and calibrates it against long-run RAPM data from Jeremias Engelmann. The companion page at <http://godismyjudgeok.com/DStats/box-plusminus/> has Myers's more detailed technical writeup. Required reading before touching the BPM formula.

### BPM 2.0: 2020 revision
**URL:** <https://www.sports-reference.com/blog/2020/02/introducing-bpm-2-0/>  
**Author:** Sports-Reference / Daniel Myers  
**What it covers:** The 2020 overhaul that updated the regression coefficients, improved defensive estimation, and extended coverage further back. BPM 2.0 is what Basketball-Reference publishes today and what our pipeline approximates. The post explains what changed from version 1, which makes it useful for understanding where the original formula fell short.

### BPM 2.0 official about page
**URL:** <https://www.basketball-reference.com/about/bpm2.html>  
**Author:** Basketball-Reference  
**What it covers:** The authoritative technical reference for BPM 2.0. Lists the exact regression coefficients, the per-100 rate inputs, the team adjustment, and the role-adjustment terms. If you need to know what the formula actually is (not a summary of it): this is the page.

### EPM: methodology page
**URL:** <https://dunksandthrees.com/about/epm>  
**Author:** Taylor Snarr, Dunks & Threes  
**What it covers:** The official explanation of Estimated Plus/Minus (EPM). EPM is a RAPM calculation with a statistical plus/minus (SPM) as a Bayesian prior. The prior is built from player-tracking data (available from 2013-14), and the metric optimizes how each underlying stat is weighted by how quickly it stabilizes. Snarr also explains how EPM handles the credit-assignment problem differently than simpler SPM approaches. Arguably the clearest methodology page for any of the modern all-in-one metrics.

### EPM: metric comparison post
**URL:** <https://dunksandthrees.com/blog/metric-comparison>  
**Author:** Taylor Snarr, Dunks & Threes  
**What it covers:** A retrodiction study comparing EPM, RAPTOR, BPM 2.0, PIPM, LEBRON, and RPM on their ability to predict future game outcomes. EPM and RPM, the only two metrics using RAPM with a Bayesian prior at the time, ranked first and second. RAPTOR placed third, and BPM 2.0 placed fourth. This is a widely cited head-to-head benchmark and the most useful single source for understanding which metrics predict game outcomes better than others.

### RAPTOR: introduction
**URL:** <https://fivethirtyeight.com/features/introducing-raptor-our-new-metric-for-the-modern-nba/>  
**Author:** Jay Boice, Neil Paine, Nate Silver (FiveThirtyEight)
**What it covers:** The public debut of RAPTOR in 2019. Explains the two-component structure: a box/tracking "prior" component (similar to SPM) combined with an on/off RAPM component, blended by sample size. RAPTOR also incorporates player-tracking stats (speed, distance, shot quality) that were unavailable to older box-score metrics. FiveThirtyEight shut down in April 2023, so RAPTOR is no longer updated, but historical data (2013-14 to 2022-23) is downloadable from their GitHub.

### RAPTOR: technical methodology
**URL:** <https://fivethirtyeight.com/features/how-our-raptor-metric-works/>  
**Author:** FiveThirtyEight  
**What it covers:** The deeper technical explainer for RAPTOR, covering each variable category (scoring, passing, rebounding, shot creation for offense; rim protection, perimeter defense for defense), how the box and on/off components are blended, and how the metric is regressed to account for small samples. Pairs with the introduction post above.

### LEBRON: introduction
**URL:** <https://www.bball-index.com/lebron-introduction/>  
**Author:** BBall-Index  
**What it covers:** The official introduction of LEBRON (Luck-adjusted player Estimate using a Box prior Regularized ON-OFF). LEBRON uses a luck-adjusted RAPM with a box-score prior derived from PIPM coefficients. The "luck adjustment" removes variance from on/off lineup data that is attributable to shot-making volatility rather than player skill. This is BBall-Index's flagship metric. Still actively updated.

### LEBRON: box prior detail
**URL:** <https://www.bball-index.com/lebron-box-prior/>  
**Author:** BBall-Index  
**What it covers:** A focused explanation of the box-score prior component of LEBRON: which stats get used, how they are weighted, and why the weights were chosen. Useful for understanding how the metric differs from a naive RAPM calculation and how box data stabilizes the on/off signal.

### Win Shares: official methodology
**URL:** <https://www.basketball-reference.com/about/ws.html>  
**Author:** Basketball-Reference  
**What it covers:** The complete formula for offensive Win Shares (OWS) and defensive Win Shares (DWS), derived from Dean Oliver's work in *Basketball on Paper*. Covers the marginal points per win constant, the pace adjustment, and how a player's share is allocated within team totals. The official reference before working with WS/48 or comparing Win Shares to plus/minus-based systems.

### DARKO: Kostya Medvedovsky's blog
**URL:** <https://kmedved.com/>  
**Author:** Kostya Medvedovsky  
**What it covers:** Medvedovsky's personal blog, which includes his original thinking on DARKO (Daily Adjusted and Regressed Kalman Optimized). DARKO is a projection system (closer to Steamer or PECOTA in concept than to a season-average metric) that blends box score, plus/minus, and prior-year data with a Kalman filter that weights recent games more heavily. No single standalone methodology document exists; the blog and the podcast episode below together give the best picture.

---

## Survey and comparison posts

These posts compare multiple metrics head-to-head or survey practitioners on what they actually use.

### "What is the best advanced statistic for basketball? NBA executives weigh in"
**URL:** <https://hoopshype.com/lists/advanced-stats-nba-real-plus-minus-rapm-win-shares-analytics/>  
**Author:** HoopsHype  
**What it covers:** A survey of 29 NBA front-office executives asking which catch-all metric they trust most for player evaluation. DARKO DPM topped the poll (8 votes), followed by EPM, LEBRON, and RAPTOR. The article also includes descriptions of each metric and a predictive-accuracy comparison by RMSE, which independently ranks DPM > EPM > LEBRON. A rare window into which public metrics actually get used inside NBA organizations.

### "The 10 Best NBA Impact Metrics"
**URL:** <https://www.thehalftime.app/p/gia/The-10-Best-NBA-Impact-Metrics>  
**Author:** The Halftime  
**What it covers:** A ranked overview of ten all-in-one player metrics, with brief descriptions of each methodology and their relative strengths. A useful orientation post for someone new to the space, though lighter on technical depth than the primary methodology sources above.

---

## RAPM: the technical backbone

Most modern all-in-one metrics (EPM, LEBRON, DARKO, RPM, RAPTOR) build on RAPM as either a target or a component.
These posts explain RAPM itself.

### Nylon Calculus 101: Plus-Minus and Adjusted Plus-Minus
**URL:** <https://fansided.com/2014/09/25/glossary-plus-minus-adjusted-plus-minus/>  
**Author:** Nylon Calculus / FanSided  
**What it covers:** An accessible introduction to the chain from raw plus/minus to adjusted plus/minus (APM) to regularized adjusted plus/minus (RAPM). Explains why raw plus/minus is misleading (teammate confounding), why APM fixes that but is noisy, and what ridge regression (regularization) adds to stabilize the estimates. A clear plain-language explanation of why RAPM exists and what problem it solves.

### Introduction to RAPM: CMU SCORE module
**URL:** <https://ryurko.github.io/cmu_score_preprints/basketball/nba-rapm.html>  
**Author:** CMU SCORE / Ryan Yurko  
**What it covers:** A semi-technical walkthrough of how to compute RAPM from play-by-play stint data using ridge regression. Shows the math, the regularization parameter selection, and how to interpret the output. More technical than the Nylon Calculus post above, less dense than a pure academic paper. Useful if you want to understand what the formula is actually doing rather than just what RAPM measures.

### Daniel Myers: "A Review of Adjusted Plus/Minus and Stabilization" (2011)
**URL:** <http://godismyjudgeok.com/DStats/2011/nba-stats/a-review-of-adjusted-plusminus-and-stabilization/>  
**Author:** Daniel Myers  
**What it covers:** Myers's early deep-dive on APM and RAPM stability. Covers how quickly the ratings stabilize as sample size grows, how they compare to box-score measures, and why using a box-score prior (the core idea behind BPM, EPM, and LEBRON) helps. This post is the intellectual precursor to BPM.

---

## PIPM: predecessor to LEBRON

### PIPM methodology page
**URL:** <https://www.bball-index.com/player-impact-plus-minus/>  
**Author:** Jacob Goldstein, BBall-Index  
**What it covers:** The methodology for Player Impact Plus/Minus (PIPM), which predates LEBRON. PIPM combined a luck-adjusted RAPM (via a method developed by Nathan Walker) with a box-score component based on 15 years of historical RAPM data. When Goldstein joined the Washington Wizards in 2020, PIPM went dark, but the coefficients lived on inside LEBRON. Understanding PIPM helps explain why LEBRON looks the way it does.

---

## Criticism and limitations

These posts surface where the metrics break down or disagree with each other.

### "Understanding the NBA: Explaining Advanced Comprehensive Stats and Metrics"
**URL:** <https://bleacherreport.com/articles/1040320-understanding-the-nba-explaining-advanced-comprehensive-stats-and-metrics>  
**Author:** Bleacher Report  
**What it covers:** An older but still-cited overview of PER, Win Shares, and adjusted plus/minus, with honest discussion of the limits of each. Covers PER's well-known weaknesses (inflated values for low-minute players, inability to handle negative contributions), Win Shares' team-performance bias, and why APM is noisy for players with limited minutes. A useful starting point for understanding the criticism landscape.

### Win Shares deep dive (Bridge NBA, Substack)
**URL:** <https://substack.com/home/post/p-113123816>  
**Author:** Harry Bridge, Bridge NBA  
**What it covers:** A recent critical examination of Win Shares specifically. Covers three main problems: Win Shares can't go negative (so bad players look neutral), they inflate for players on overperforming teams, and the defensive component systematically favors big men. Pairs well with the BBR methodology page to understand what the formula misses.

### "Is ESPN's Real Plus-Minus For Real?"
**URL:** <https://nbacouchside.net/2017/01/19/from-the-archives-is-espns-real-plus-minus-for-real/>  
**Author:** Kevin Ferrigan, NBA Couchside  
**What it covers:** A skeptical examination of ESPN's RPM in its early years, asking whether the metric's novelty justified the trust practitioners placed in it. Covers sample-size instability, how the metric handles players who switch teams mid-season, and whether the box-score prior Engelmann used was well-calibrated. Useful historical context for why DARKO, EPM, and LEBRON emerged as corrections or alternatives to RPM.

### "The problem with ESPN's Real Plus-Minus"
**URL:** <https://www.poundingtherock.com/2014/4/8/5594238/problem-with-real-plus-minus>  
**Author:** Pounding the Rock / SB Nation  
**What it covers:** A 2014 post written shortly after RPM launched, raising early concerns about collinearity (teammates playing together make individual attribution hard) and the fact that the methodology was not publicly disclosed. Still relevant as a reminder that opacity is a real limitation for proprietary metrics.

### A stakeholder assessment of basketball player evaluation metrics
**URL:** <https://www.researchgate.net/publication/50934255_A_stakeholder_assessment_of_basketball_player_evaluation_metrics>  
**Author:** Academic paper (ResearchGate)  
**What it covers:** A peer-reviewed study asking whether sophisticated metrics actually outperform simpler measures for explaining salary and team wins. The finding, that complex metrics do not reliably outperform simple ones in these specific tasks, is a useful check on overconfidence in any single rating system. More relevant to understanding what the metrics are and are not for than to building them.

---

## Forum discussions

### APBRmetrics: BPM and VORP thread
**URL:** <https://apbr.org/metrics/viewtopic.php?t=9470>  
**Author:** APBRmetrics community  
**What it covers:** A long forum thread on BPM and VORP where Myers and other analysts discuss edge cases, calibration issues, and how BPM compares to other systems. APBRmetrics is the oldest serious basketball analytics community online; the depth of debate here is not matched elsewhere. The index thread at <https://apbr.org/metrics/viewtopic.php?t=250> lists hundreds of other topic threads organized by subject.

### APBRmetrics: eWins, Win Shares, and EWA comparison (2009)
**URL:** <http://apbr.org/metrics/viewtopic.php?f=2&t=70>  
**Author:** APBRmetrics community  
**What it covers:** An early community comparison of Win Shares, Estimated Wins Added, and equivalent metrics. The debate here is historically significant because it captures the moment the community was working out whether box-score metrics could be trusted and under what conditions each was more reliable. More historical interest than practical reference, but shows how the field evolved.

---

## Practitioner context

### Ben Falk: Cleaning the Glass
**URL:** <https://cleaningtheglass.com/>  
**Author:** Ben Falk (former VP of Basketball Strategy, 76ers; Basketball Analytics Manager, Blazers)  
**What it covers:** Not a single post but a subscription analytics platform and blog from a former NBA executive. Falk's public writing focuses on on/off data interpretation, lineup analysis, and shot quality, all of which are inputs into the plus/minus metrics. His "about" page at <https://cleaningtheglass.com/about/> explains his perspective on why on/off data is underused and how he thinks about player impact. Useful as a practitioner's view of what the metrics are actually capturing.

### DRIP: Daily Updated Rating of Individual Performance
**URL:** <https://theanalyst.com/articles/nba-drip-daily-updated-rating-of-individual-performance>  
**Author:** Opta Analyst  
**What it covers:** The introduction of DRIP (2021), Opta's daily-updated all-in-one player metric. Like DARKO, DRIP "now-casts" current player talent rather than averaging over a full season: it uses box score, play-by-play, and lineup data to project each player's contribution to team offensive and defensive ratings, weighting recent games more heavily. The introduction covers how DRIP differs from static seasonal metrics and why daily updating matters for in-season evaluation.

### Medium: "NBA Player Value Models: Calculating RAPM" (John Chen)
**URL:** <https://medium.com/@johnchenmbb/calculating-rapm-steps-1-and-2-of-my-summer-plan-1a78e1476b1f>  
**Author:** John Chen  
**What it covers:** A hands-on walkthrough of actually computing RAPM from play-by-play stint data. Covers data acquisition, the ridge regression setup, and how to validate results against published benchmarks. One of the most practical "how to build this yourself" posts in the public NBA analytics literature. A companion post covers building XGB-PM, a gradient-boosted model that predicts RAPM from box stats.

---

## NBA.com and Basketball-Reference official explainers

These are reference pages rather than opinion pieces, but they belong in any reading list.

| Metric | URL |
|---|---|
| BPM 2.0 | <https://www.basketball-reference.com/about/bpm2.html> |
| Win Shares | <https://www.basketball-reference.com/about/ws.html> |
| EPM | <https://dunksandthrees.com/about/epm> |
| RAPTOR data (GitHub) | <https://github.com/fivethirtyeight/data/tree/master/nba-raptor> |
| DARKO results | <https://darko.basketball> |
| LEBRON | <https://www.bball-index.com/lebron-introduction/> |
| DRIP | <https://theanalyst.com/articles/nba-drip-daily-updated-rating-of-individual-performance> |
