# Player Rating Overview: Analysis Results

Season: 2024–25

```

─── DATA COVERAGE ───────────────────────────────────────────────
Season: 2024–25
Total players in unified table: 569
Qualified players (>= 500 min): 375
Rating systems present: 11
  Game Score: 375 players with data
  PER: 375 players with data
  Win Shares: 375 players with data
  WS/48: 375 players with data
  BPM: 375 players with data
  OBPM: 375 players with data
  DBPM: 375 players with data
  VORP: 375 players with data
  RAPM: 375 players with data
  O-RAPM: 375 players with data
  D-RAPM: 375 players with data
  RAPM players with computed values: 554

─── RAPM — COMPUTED SINGLE-SEASON (NO PRIOR) ────────────────────
  1. Isaiah Joe: RAPM +13.06 per 100
  2. Nikola Vučević: RAPM +9.55 per 100
  3. Pelle Larsson: RAPM +9.47 per 100
  4. Brandon Clarke: RAPM +9.32 per 100
  5. Jabari Smith Jr.: RAPM +9.14 per 100
  Mean rank agreement with box-score systems: 0.22
  RAPM #1 (Isaiah Joe) consensus rank: 178

─── BASIC DISTRIBUTION STATS ────────────────────────────────────

Game Score (n=375):
  Mean: 9.45  Median: 8.18  Std: 4.89
  Min: 2.15  Max: 30.11
  Gini: 0.283  Top-5% share: 11.5%

PER (n=375):
  Mean: 14.78  Median: 14.28  Std: 4.25
  Min: 4.63  Max: 32.33
  Gini: 0.159  Top-5% share: 8.5%

Win Shares (n=375):
  Mean: 3.30  Median: 2.79  Std: 2.28
  Min: 0.02  Max: 14.91
  Gini: 0.363  Top-5% share: 14.8%

WS/48 (n=375):
  Mean: 0.11  Median: 0.09  Std: 0.05
  Min: 0.00  Max: 0.28
  Gini: 0.265  Top-5% share: 11.5%

BPM (n=375):
  Mean: -1.51  Median: -2.19  Std: 9.83
  Min: -24.29  Max: 27.48
  Gini: 0.767  Top-5% share: 32.2%

OBPM (n=375):
  Mean: -7.59  Median: -10.15  Std: 9.78
  Min: -22.71  Max: 26.18
  Gini: 0.881  Top-5% share: 52.7%

DBPM (n=375):
  Mean: 6.08  Median: 4.44  Std: 8.96
  Min: -8.11  Max: 45.81
  Gini: 0.599  Top-5% share: 23.0%

VORP (n=375):
  Mean: 17.50  Median: -1.41  Std: 68.09
  Min: -95.85  Max: 316.67
  Gini: 0.749  Top-5% share: 31.9%

RAPM (n=375):
  Mean: 0.08  Median: -0.16  Std: 4.08
  Min: -11.62  Max: 13.06
  Gini: 0.711  Top-5% share: 25.4%

O-RAPM (n=375):
  Mean: 0.10  Median: 0.04  Std: 3.07
  Min: -8.51  Max: 8.95
  Gini: 0.713  Top-5% share: 27.0%

D-RAPM (n=375):
  Mean: -0.02  Median: 0.12  Std: 2.89
  Min: -10.92  Max: 7.34
  Gini: 0.695  Top-5% share: 24.4%

─── POWER-LAW FIT (VALUE VS RANK, LOG-LOG) ──────────────────────
A system's top-50 value-vs-rank curve is a power law when the
log-log fit clears R^2 >= 0.95 (a straight line on log-log axes).

Game Score (n=50 positive ranks):
  exponent alpha=0.15  R^2=0.971  -> power law

PER (n=50 positive ranks):
  exponent alpha=0.13  R^2=0.959  -> power law

Win Shares (n=50 positive ranks):
  exponent alpha=0.23  R^2=0.978  -> power law

WS/48 (n=50 positive ranks):
  exponent alpha=0.17  R^2=0.918  -> not a power law (bends)

BPM (n=50 positive ranks):
  exponent alpha=0.34  R^2=0.935  -> not a power law (bends)

OBPM (n=50 positive ranks):
  exponent alpha=0.52  R^2=0.878  -> not a power law (bends)

DBPM (n=50 positive ranks):
  exponent alpha=0.31  R^2=0.957  -> power law

VORP (n=50 positive ranks):
  exponent alpha=0.36  R^2=0.973  -> power law

RAPM (n=50 positive ranks):
  exponent alpha=0.24  R^2=0.925  -> not a power law (bends)

O-RAPM (n=50 positive ranks):
  exponent alpha=0.27  R^2=0.910  -> not a power law (bends)

D-RAPM (n=50 positive ranks):
  exponent alpha=0.24  R^2=0.959  -> power law

Power-law systems (R^2 >= 0.95): Game Score, PER, Win Shares, DBPM, VORP, D-RAPM
Bend instead of a straight line: WS/48, BPM, OBPM, RAPM, O-RAPM

─── RANK AGREEMENT (SPEARMAN CORRELATIONS) ──────────────────────
  Game Score vs PER: r=0.831
  Game Score vs Win Shares: r=0.699
  Game Score vs WS/48: r=0.308
  Game Score vs BPM: r=0.469
  Game Score vs OBPM: r=0.869
  Game Score vs DBPM: r=-0.448
  Game Score vs VORP: r=0.505
  Game Score vs RAPM: r=0.189
  Game Score vs O-RAPM: r=0.190
  Game Score vs D-RAPM: r=0.062
  PER vs Win Shares: r=0.759
  PER vs WS/48: r=0.611
  PER vs BPM: r=0.489
  PER vs OBPM: r=0.722
  PER vs DBPM: r=-0.271
  PER vs VORP: r=0.526
  PER vs RAPM: r=0.225
  PER vs O-RAPM: r=0.199
  PER vs D-RAPM: r=0.091
  Win Shares vs WS/48: r=0.695
  Win Shares vs BPM: r=0.640
  Win Shares vs OBPM: r=0.761
  Win Shares vs DBPM: r=-0.094
  Win Shares vs VORP: r=0.653
  Win Shares vs RAPM: r=0.279
  Win Shares vs O-RAPM: r=0.244
  Win Shares vs D-RAPM: r=0.146
  WS/48 vs BPM: r=0.371
  WS/48 vs OBPM: r=0.200
  WS/48 vs DBPM: r=0.183
  WS/48 vs VORP: r=0.394
  WS/48 vs RAPM: r=0.233
  WS/48 vs O-RAPM: r=0.144
  WS/48 vs D-RAPM: r=0.181
  BPM vs OBPM: r=0.560
  BPM vs DBPM: r=0.347
  BPM vs VORP: r=0.972
  BPM vs RAPM: r=0.200
  BPM vs O-RAPM: r=0.166
  BPM vs D-RAPM: r=0.119
  OBPM vs DBPM: r=-0.464
  OBPM vs VORP: r=0.572
  OBPM vs RAPM: r=0.175
  OBPM vs O-RAPM: r=0.214
  OBPM vs D-RAPM: r=0.024
  DBPM vs VORP: r=0.308
  DBPM vs RAPM: r=0.059
  DBPM vs O-RAPM: r=-0.039
  DBPM vs D-RAPM: r=0.132
  VORP vs RAPM: r=0.205
  VORP vs O-RAPM: r=0.172
  VORP vs D-RAPM: r=0.113
  RAPM vs O-RAPM: r=0.695
  RAPM vs D-RAPM: r=0.636
  O-RAPM vs D-RAPM: r=-0.062

─── WHAT EACH SYSTEM UNIQUELY CAPTURES ──────────────────────────
  BPM: unique R² = 1.000
  OBPM: unique R² = 1.000
  DBPM: unique R² = 1.000
  RAPM: unique R² = 1.000
  O-RAPM: unique R² = 1.000
  D-RAPM: unique R² = 1.000
  PER: unique R² = 0.893
  Game Score: unique R² = 0.888
  VORP: unique R² = 0.872
  Win Shares: unique R² = 0.867
  WS/48: unique R² = 0.838

─── CONSENSUS RATING — TOP 20 ───────────────────────────────────
   1. Nikola Jokić                    Consensus z = 2.78
   2. Shai Gilgeous-Alexander         Consensus z = 2.55
   3. Giannis Antetokounmpo           Consensus z = 2.25
   4. Trae Young                      Consensus z = 1.62
   5. Tyrese Haliburton               Consensus z = 1.61
   6. James Harden                    Consensus z = 1.60
   7. Ivica Zubac                     Consensus z = 1.52
   8. LeBron James                    Consensus z = 1.51
   9. Jayson Tatum                    Consensus z = 1.43
  10. Domantas Sabonis                Consensus z = 1.39
  11. Rudy Gobert                     Consensus z = 1.36
  12. Jarrett Allen                   Consensus z = 1.36
  13. Amen Thompson                   Consensus z = 1.32
  14. Karl-Anthony Towns              Consensus z = 1.32
  15. Dyson Daniels                   Consensus z = 1.28
  16. Alperen Sengun                  Consensus z = 1.28
  17. Jalen Duren                     Consensus z = 1.26
  18. Stephen Curry                   Consensus z = 1.24
  19. Josh Hart                       Consensus z = 1.22
  20. Devin Booker                    Consensus z = 1.21

─── WINS-PREDICTIVE RATING — TOP 20 ─────────────────────────────
   1. Shai Gilgeous-Alexander         Wins-predictive z = 3.71
   2. Giannis Antetokounmpo           Wins-predictive z = 3.69
   3. Nikola Jokić                    Wins-predictive z = 3.22
   4. Jayson Tatum                    Wins-predictive z = 2.42
   5. Ivica Zubac                     Wins-predictive z = 2.27
   6. LeBron James                    Wins-predictive z = 2.26
   7. Victor Wembanyama               Wins-predictive z = 2.19
   8. Luka Dončić                     Wins-predictive z = 2.14
   9. Stephen Curry                   Wins-predictive z = 2.10
  10. Jarrett Allen                   Wins-predictive z = 1.98
  11. Nikola Vučević                  Wins-predictive z = 1.94
  12. Evan Mobley                     Wins-predictive z = 1.94
  13. Anthony Davis                   Wins-predictive z = 1.87
  14. Amen Thompson                   Wins-predictive z = 1.83
  15. Trae Young                      Wins-predictive z = 1.82
  16. Rudy Gobert                     Wins-predictive z = 1.82
  17. Tyrese Haliburton               Wins-predictive z = 1.80
  18. Karl-Anthony Towns              Wins-predictive z = 1.74
  19. Franz Wagner                    Wins-predictive z = 1.72
  20. Jaren Jackson Jr.               Wins-predictive z = 1.65

─── COMPARISON: CONSENSUS vs. WINS-PREDICTIVE ───────────────────
  Spearman correlation between consensus and wins-predictive: 0.938 (p=0.000)
  Players rated much higher by wins-predictive than consensus:
    Giannis Antetokounmpo           diff = +1.45
    Victor Wembanyama               diff = +1.25
    Shai Gilgeous-Alexander         diff = +1.15
    Jayson Tatum                    diff = +0.99
    Luka Dončić                     diff = +0.97
  Players rated much lower by wins-predictive than consensus:
    Dillon Jones                    diff = -1.17
    KJ Martin                       diff = -1.16
    Ben Sheppard                    diff = -0.98
    Craig Porter Jr.                diff = -0.95
    Gabe Vincent                    diff = -0.94

─── UBER RATING CONCENTRATION (GINI vs CENTER-ROBUST STEEPNESS) ─
Gini clips negatives to zero, so it inflates 0-centered metrics (the uber
ratings and the BPM family). The power-law exponent alpha does not depend on
where zero sits, so it is the fair cross-system concentration read.

Consensus: Gini=0.754 (inflated), top-5% share=30.0%, alpha=0.31

Wins-Predictive: Gini=0.736 (inflated), top-5% share=29.0%, alpha=0.32

─── POWER-LAW / TAIL ANALYSIS ───────────────────────────────────

Cumulative-value metrics:
  Win Shares: Gini=0.363, top-5% hold 14.8% of value
    Skewness: 1.45 (right-skewed)
  VORP: Gini=0.749, top-5% hold 31.9% of value
    Skewness: 1.54 (right-skewed)

Rate metrics:
  PER: Gini=0.159, top-5% hold 8.5% of value
    Skewness: 0.73 (right-skewed)
  BPM: Gini=0.767, top-5% hold 32.2% of value
    Skewness: 1.05 (right-skewed)

─── WHO EACH SYSTEM LOVES vs. CONSENSUS ─────────────────────────

Game Score loves (vs. consensus):
  +1.96  Joel Embiid
  +1.83  Cam Thomas
  +1.76  Brandon Ingram
Game Score discounts (vs. consensus):
  -1.97  Dwight Powell
  -1.67  John Konchar
  -1.34  Kris Dunn

PER loves (vs. consensus):
  +1.90  Zion Williamson
  +1.60  Giannis Antetokounmpo
  +1.56  Anthony Davis
PER discounts (vs. consensus):
  -1.66  Cam Reddish
  -1.41  Delon Wright
  -1.39  John Konchar

Win Shares loves (vs. consensus):
  +2.66  Domantas Sabonis
  +2.31  Nikola Jokić
  +1.94  Ivica Zubac
Win Shares discounts (vs. consensus):
  -1.31  John Konchar
  -1.15  Dwight Powell
  -1.11  Victor Wembanyama

WS/48 loves (vs. consensus):
  +2.99  Steven Adams
  +2.56  Day'Ron Sharpe
  +2.46  Richaun Holmes
WS/48 discounts (vs. consensus):
  -1.72  Anthony Edwards
  -1.57  Jaren Jackson Jr.
  -1.45  Jayson Tatum

BPM loves (vs. consensus):
  +2.41  Cam Reddish
  +2.27  John Konchar
  +2.19  Dwight Powell
BPM discounts (vs. consensus):
  -1.44  Joel Embiid
  -1.40  Malcolm Brogdon
  -1.25  Immanuel Quickley

OBPM loves (vs. consensus):
  +2.05  Anthony Edwards
  +1.89  Jalen Green
  +1.71  Devin Booker
OBPM discounts (vs. consensus):
  -1.77  John Konchar
  -1.41  Alex Caruso
  -1.39  Cam Reddish

DBPM loves (vs. consensus):
  +4.32  Cam Reddish
  +3.96  John Konchar
  +2.98  Zeke Nnaji
DBPM discounts (vs. consensus):
  -3.32  Giannis Antetokounmpo
  -3.31  Nikola Jokić
  -3.11  Shai Gilgeous-Alexander

VORP loves (vs. consensus):
  +3.09  Dyson Daniels
  +2.66  Anthony Edwards
  +2.36  James Harden
VORP discounts (vs. consensus):
  -1.13  Zion Williamson
  -1.06  Jabari Smith Jr.
  -1.03  Mark Williams

─── RETRODICTION: WHICH RATING REBUILDS TEAM RESULTS ────────────
Each system's player ratings are minutes-weighted to the team level, then
fit to team point differential per game across the 30 teams. R² is the
in-sample fit; CV R² is leave-one-team-out (the honest out-of-sample read).
Systems marked [team-fit] are built using team or lineup point
differential, so a high score is partly mechanical. Systems marked
[outcome-blind] never saw who won; their score is the genuine test.

  [outcome-blind] PER            R²=0.755  CV R²=0.723
  [team-fit]     BPM            R²=0.669  CV R²=0.623
  [team-fit]     VORP           R²=0.610  CV R²=0.551
  [team-fit]     RAPM           R²=0.546  CV R²=0.482
  [team-fit]     Win Shares     R²=0.530  CV R²=0.457
  [team-fit]     OBPM           R²=0.493  CV R²=0.427
  [outcome-blind] Game Score     R²=0.494  CV R²=0.394
  [team-fit]     WS/48          R²=0.325  CV R²=0.201
  [team-fit]     D-RAPM         R²=0.274  CV R²=0.188
  [team-fit]     DBPM           R²=0.260  CV R²=0.169
  [team-fit]     O-RAPM         R²=0.284  CV R²=0.149

Top retrodictor: PER (CV R²=0.723); it rebuilds 72% of the team point-differential
spread out of sample.
PER never uses who won, yet it beats the team-adjusted box
metrics (BPM, VORP, Win Shares) here. Caveat: this project's BPM and
VORP are approximate recomputes, so their lower scores partly reflect a
noisy recompute, not proof PER is the better rating. Rerun once exactly
computed or published impact metrics (EPM, DARKO, RAPTOR) are loaded.

─── NEXT-SEASON RETRODICTION (PREDICTING THIS SEASON FROM LAST) ─
Last season's (2023-24) player ratings are
distributed across this season's rosters (weighted by this season's minutes)
and fit to this season's team point differential. Because each metric's team
adjustment is fit to its own season, predicting the next season removes the
in-sample circularity. Describing the season just played and forecasting the
next are different tests, and they reward different metrics.

Prior-rating coverage: 89% of this season's team minutes
were played by players who also carried a rating last season.

                   describes  predicts
  system           (same yr) (next yr)
  [team-fit]     BPM              0.623     0.501
  [outcome-blind] Game Score       0.394     0.485
  [team-fit]     RAPM             0.482     0.442
  [team-fit]     Win Shares       0.457     0.403
  [team-fit]     VORP             0.551     0.362
  [team-fit]     OBPM             0.427     0.355
  [team-fit]     WS/48            0.201     0.244
  [team-fit]     O-RAPM           0.149     0.229
  [team-fit]     D-RAPM           0.188     0.176
  [outcome-blind] PER              0.723     0.151
  [team-fit]     DBPM             0.169     0.131

Best forecaster of next season: BPM (R²=0.501). Best description of
the season itself: PER.
PER falls from 0.72 describing the season to 0.15
forecasting the next: a strong descriptor, a weak predictor.

─── MULTI-SEASON DESCRIBE vs FORECAST (FULL PANEL) ──────────────
The single pair above is one season. This pools the same two tests
across every season in the cache: 30 seasons
(1996-97 through 2025-26) for the describe test and
the 29 consecutive season-pairs for the forecast test.
Each number below is the average R² across all of those seasons (describe)
or pairs (forecast), with the season-to-season range in brackets. Pooling
this way shows whether the one-season flip is a fluke or a standing pattern.

                     describes    predicts
  system             (same yr)   (next yr)
  [outcome-blind] Game Score      0.385 [0.09,0.62]   0.420 [0.14,0.61]
  [team-fit]     BPM             0.297 [0.02,0.65]   0.354 [0.04,0.52]
  [team-fit]     Win Shares      0.289 [0.01,0.54]   0.329 [0.08,0.52]
  [team-fit]     VORP            0.242 [-0.02,0.55]   0.311 [0.07,0.51]
  [team-fit]     OBPM            0.239 [-0.07,0.52]   0.307 [0.08,0.57]
  [outcome-blind] PER             0.636 [0.17,0.81]   0.252 [0.00,0.50]
  [team-fit]     WS/48           0.130 [-0.11,0.42]   0.187 [0.00,0.51]
  [team-fit]     DBPM            0.020 [-0.15,0.50]   0.067 [0.00,0.30]

Across 30 seasons the best description is PER; across
29 pairs the best forecast is Game Score.
PER averages 0.64 describing but only 0.25 forecasting,
the same collapse the single pair showed, now seen across 29 pairs.
BPM forecasts better than PER in 20 of 29 pairs.

─── IMPACT-ERA PANEL: BOX SCORES vs RAPM (EQUAL SEASONS) ────────
The panel above runs 30 seasons, but RAPM can only be computed for the
13 seasons with cached play-by-play (2013-14 through 2025-26).
This second panel scores the box-score systems AND RAPM over those same
seasons, so the comparison is even. RAPM is built from lineup point
differential, so its DESCRIBE score (rebuilding the same season's team
margin) is partly mechanical; the FORECAST score (prior-season RAPM onto
next season's rosters) is the honest read.

                     describes    predicts
  system             (same yr)   (next yr)
  [outcome-blind] Game Score      0.424       0.446
  [team-fit]     BPM             0.351       0.384
  [team-fit]     Win Shares      0.369       0.367
  [team-fit]     VORP            0.301       0.359
  [team-fit]     OBPM            0.294       0.346
  [outcome-blind] PER             0.641       0.267
  [team-fit]     WS/48           0.244       0.260
  [team-fit]     RAPM            0.339       0.169
  [team-fit]     DBPM            0.024       0.061

Over these 12 pairs RAPM forecasts 8 of 9; the best forecaster is Game Score.

─── PLAYER RATING STABILITY (YEAR OVER YEAR) ────────────────────
A different lens: not how well a rating predicts team results, but how
much a player's own rating carries from one season to the next. For every
pair of seasons, players who qualified (500+ minutes) in both are
matched, and each system gets two numbers: the correlation between a
player's rating this season and next (1.0 = perfectly sticky, 0 = a coin
flip), and the share of the top 20 one season still in the top
20 the next. Stability is persistence, not quality: a rating can be
sticky because it tracks a real, lasting trait or because it is slow to
move. These box scores also share inputs (points, rebounds, assists), so
some of the shared stickiness is mechanical.

  system            year-to-year   top-20 kept
  Game Score          0.847 [0.81,0.89]        68%
  DBPM                0.806 [0.71,0.86]        40%
  PER                 0.803 [0.76,0.85]        64%
  WS/48               0.796 [0.69,0.86]        47%
  OBPM                0.746 [0.63,0.81]        56%
  Win Shares          0.722 [0.65,0.79]        53%
  VORP                0.710 [0.55,0.79]        49%
  BPM                 0.697 [0.59,0.76]        50%

Steadiest year to year: Game Score (corr 0.85). Jumpiest: BPM (corr 0.70).
Best at keeping the same names in the top 20: Game Score (68%), against a chance level near 5%.

─── REGULAR SEASON vs PLAYOFFS (RATE-METRIC DELTAS) ─────────────
Players with >= 150 playoff minutes: 96
Rate metrics compared (each normalized within its season type): PER, WS/48, BPM, OBPM, DBPM
Delta = playoff minus regular season. 'adj' subtracts the average delta
among this qualified pool, so a riser is measured against the other
rotation players who also advanced. The composite shift z averages the
standardized adjusted deltas of PER, WS/48, and BPM, so a riser needs the
three box formulations to agree.
Note: this project's BPM scale is approximate; the rankings carry the
signal, not the raw BPM points.

Biggest playoff RISERS (raised their level above their regular-season form):
   1. Gary Trent Jr.             MIL  shift z = +2.27  (PER +8.2 vs regular season)
   2. Kawhi Leonard              LAC  shift z = +2.18  (PER +6.1 vs regular season)
   3. Paolo Banchero             ORL  shift z = +1.58  (PER +2.5 vs regular season)
   4. Donovan Mitchell           CLE  shift z = +1.54  (PER +7.0 vs regular season)
   5. LeBron James               LAL  shift z = +1.38  (PER +3.6 vs regular season)
   6. Giannis Antetokounmpo      MIL  shift z = +1.34  (PER +2.8 vs regular season)
   7. Max Strus                  CLE  shift z = +1.29  (PER +4.9 vs regular season)
   8. Buddy Hield                GSW  shift z = +1.19  (PER +3.4 vs regular season)
   9. Nicolas Batum              LAC  shift z = +1.07  (PER +3.7 vs regular season)
  10. Dennis Schröder            DET  shift z = +1.05  (PER +4.4 vs regular season)

Biggest playoff FALLERS (dropped below their regular-season form):
   1. Michael Porter Jr.         DEN  shift z = -1.74  (PER -7.0 vs regular season)
   2. Austin Reaves              LAL  shift z = -1.74  (PER -6.1 vs regular season)
   3. Miles McBride              NYK  shift z = -1.35  (PER -3.3 vs regular season)
   4. Nikola Jokić               DEN  shift z = -1.35  (PER -6.4 vs regular season)
   5. Kristaps Porziņģis         BOS  shift z = -1.24  (PER -8.4 vs regular season)
   6. Thomas Bryant              IND  shift z = -1.23  (PER -5.0 vs regular season)
   7. Payton Pritchard           BOS  shift z = -1.16  (PER -2.7 vs regular season)
   8. Draymond Green             GSW  shift z = -1.13  (PER -2.4 vs regular season)
   9. Ty Jerome                  CLE  shift z = -1.11  (PER -3.6 vs regular season)
  10. Mike Conley                MIN  shift z = -1.11  (PER -2.7 vs regular season)

Regular-season consensus #1 Nikola Jokić: playoff shift z = -1.35 (faller rank 4 of 96)
Saved → docs/player_rating_overview_facts_reference.md

```
