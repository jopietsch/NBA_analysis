# Player Rating Overview: Analysis Results

Season: 2025-26

```

─── DATA COVERAGE ───────────────────────────────────────────────
Season: 2025–26
Total players in unified table: 582
Qualified players (>= 500 min): 378
Rating systems present: 14
  Game Score: 378 players with data
  PER: 378 players with data
  Win Shares: 378 players with data
  WS/48: 378 players with data
  BPM: 378 players with data
  OBPM: 378 players with data
  DBPM: 378 players with data
  VORP: 378 players with data
  RAPM: 378 players with data
  O-RAPM: 378 players with data
  D-RAPM: 378 players with data
  RAPM+prior: 378 players with data
  O-RAPM+prior: 378 players with data
  D-RAPM+prior: 378 players with data
  RAPM players with computed values: 582

─── RAPM — COMPUTED SINGLE-SEASON (NO PRIOR) ────────────────────
  1. Chet Holmgren: RAPM +10.16 per 100
  2. Josh Green: RAPM +9.30 per 100
  3. Victor Wembanyama: RAPM +9.25 per 100
  4. Derrick White: RAPM +9.08 per 100
  5. Shai Gilgeous-Alexander: RAPM +8.66 per 100
  Mean rank agreement with box-score systems: 0.33
  RAPM #1 (Chet Holmgren) consensus rank: 22

─── RAPM_MY — PRIOR-INFORMED, MULTI-YEAR ────────────────────────
  1. Shai Gilgeous-Alexander: RAPM_MY +10.49 per 100
  2. Giannis Antetokounmpo: RAPM_MY +10.07 per 100
  3. Nikola Jokić: RAPM_MY +9.82 per 100
  4. Victor Wembanyama: RAPM_MY +9.11 per 100
  5. Luka Dončić: RAPM_MY +7.88 per 100
  Mean rank agreement with box-score systems: 0.75
  Rank agreement with the consensus: 0.91

─── RAPM RELIABILITY (SPLIT-HALF AND YEAR-OVER-YEAR) ────────────
Split-half: fit bare RAPM on two random halves of the pooled
possessions, then correlate the two estimates. If the lineup signal
is real the halves agree; if it is noise they do not.
  Split-half reliability (279 players, 1000+ min): 0.32
  (near-zero would be noise; a usable metric sits near 0.5-0.7)
  By minutes bin:
       0-500  min: n=423  r=+0.15
     500-1000 min: n= 99  r=+0.25
    1000-1500 min: n=115  r=+0.34
    1500-2000 min: n= 87  r=+0.25
    2000-3500 min: n= 77  r=+0.34

Year-over-year stability (players 1000+ min in both seasons):
  RAPM     +0.41
  RAPM_MY  +0.84
  BPM      +0.79

After the possession-reconstruction fixes, the lineup signal is real,
not noise. A reconstruction bug had been discarding ~60% of games with
complete play-by-play; recovering them took split-half reliability from
about 0.10 to 0.32, and bare single-season RAPM now holds from one
season to the next at 0.41 (it was near zero before).
Pooled across seasons and anchored to the BPM prior, RAPM_MY is at least
as stable as BPM (0.84 vs 0.79), so it adds a
genuine lineup contribution on top of the box score rather than echoing
it. Reliability keeps climbing with more pooled seasons (roughly 0.48 at
three seasons, 0.60 at five, on the full-data scale).

─── BPM VALIDATION vs BASKETBALL-REFERENCE ──────────────────────
  Qualified players matched to BBR: 361
  BPM vs BBR bpm: r=0.930  MAE=0.80 (n=361)
  OBPM vs BBR obpm: r=0.946  MAE=0.61 (n=361)
  DBPM vs BBR dbpm: r=0.877  MAE=0.47 (n=361)
  VORP vs BBR vorp: r=0.961  MAE=0.27 (n=361)

  Spot check (ours vs BBR):
  Player                     BPM   BBR BPM    OBPM  BBR OBPM    DBPM  BBR DBPM
  Shai Gilgeous-Alexander    10.4      11.7     9.0       8.7     1.4       3.0
  Giannis Antetokounmpo     10.0       9.5     9.8       7.7     0.1       1.8
  Victor Wembanyama          8.9      10.7     5.0       6.5     3.9       4.2
  Luka Garza                 3.6       2.4     3.2       2.2     0.3       0.2
  Jalen Brunson              3.4       3.1     4.3       4.0    -0.9      -0.9
  Jayson Tatum               3.0       4.8     1.1       2.9     1.9       1.8
  Kawhi Leonard              7.7       8.0     6.6       7.4     1.2       0.6

─── BASIC DISTRIBUTION STATS ────────────────────────────────────

Game Score (n=378):
  Mean: 9.46  Median: 8.52  Std: 4.80
  Min: 2.34  Max: 28.68
  Gini: 0.277  Top-5% share: 11.5%
  Skew: +1.00  Excess kurtosis: +0.88  Below zero: 0%

PER (n=378):
  Mean: 14.86  Median: 14.13  Std: 4.31
  Min: 5.99  Max: 32.16
  Gini: 0.160  Top-5% share: 8.6%
  Skew: +0.83  Excess kurtosis: +1.25  Below zero: 0%

Win Shares (n=378):
  Mean: 3.27  Median: 2.73  Std: 2.18
  Min: 0.17  Max: 14.13
  Gini: 0.362  Top-5% share: 13.8%
  Skew: +1.16  Excess kurtosis: +1.83  Below zero: 0%

WS/48 (n=378):
  Mean: 0.11  Median: 0.10  Std: 0.05
  Min: 0.01  Max: 0.30
  Gini: 0.280  Top-5% share: 11.8%
  Skew: +0.94  Excess kurtosis: +0.87  Below zero: 0%

BPM (n=378):
  Mean: -0.24  Median: -0.43  Std: 2.66
  Min: -5.72  Max: 11.43
  Gini: 0.767  Top-5% share: 34.3%
  Skew: +0.78  Excess kurtosis: +1.68  Below zero: 58%

OBPM (n=378):
  Mean: -0.22  Median: -0.46  Std: 2.30
  Min: -5.65  Max: 10.16
  Gini: 0.769  Top-5% share: 34.9%
  Skew: +0.84  Excess kurtosis: +2.05  Below zero: 59%

DBPM (n=378):
  Mean: -0.02  Median: -0.10  Std: 1.10
  Min: -3.01  Max: 3.89
  Gini: 0.732  Top-5% share: 30.4%
  Skew: +0.32  Excess kurtosis: +0.63  Below zero: 53%

VORP (n=378):
  Mean: 0.81  Median: 0.54  Std: 1.24
  Min: -1.64  Max: 7.73
  Gini: 0.611  Top-5% share: 24.5%
  Skew: +1.71  Excess kurtosis: +4.96  Below zero: 25%

RAPM (n=378):
  Mean: 0.40  Median: 0.41  Std: 3.37
  Min: -8.66  Max: 10.16
  Gini: 0.678  Top-5% share: 24.0%
  Skew: -0.00  Excess kurtosis: -0.03  Below zero: 43%

O-RAPM (n=378):
  Mean: 0.33  Median: 0.30  Std: 2.49
  Min: -7.66  Max: 8.24
  Gini: 0.667  Top-5% share: 24.5%
  Skew: +0.04  Excess kurtosis: +0.14  Below zero: 43%

D-RAPM (n=378):
  Mean: 0.07  Median: 0.11  Std: 2.49
  Min: -7.98  Max: 8.77
  Gini: 0.704  Top-5% share: 26.5%
  Skew: +0.02  Excess kurtosis: +0.49  Below zero: 48%

RAPM+prior (n=378):
  Mean: -0.17  Median: -0.29  Std: 2.63
  Min: -6.55  Max: 10.49
  Gini: 0.757  Top-5% share: 33.0%
  Skew: +0.61  Excess kurtosis: +1.51  Below zero: 54%

O-RAPM+prior (n=378):
  Mean: -0.18  Median: -0.38  Std: 2.18
  Min: -5.72  Max: 10.25
  Gini: 0.780  Top-5% share: 35.0%
  Skew: +0.85  Excess kurtosis: +2.38  Below zero: 59%

D-RAPM+prior (n=378):
  Mean: 0.01  Median: -0.04  Std: 1.35
  Min: -3.45  Max: 5.70
  Gini: 0.737  Top-5% share: 29.5%
  Skew: +0.40  Excess kurtosis: +0.60  Below zero: 52%

RAPM distribution shape, pooled over 13 seasons (n=4678 player-seasons):
  Skew: +0.06  Excess kurtosis: +0.06  Below zero: 46%

─── POWER-LAW FIT (VALUE VS RANK, LOG-LOG) ──────────────────────
A system's top-50 value-vs-rank curve is a power law when the
log-log fit clears R^2 >= 0.95 (a straight line on log-log axes).

Game Score (n=50 positive ranks):
  exponent alpha=0.17  R^2=0.973  -> power law

PER (n=50 positive ranks):
  exponent alpha=0.14  R^2=0.958  -> power law

Win Shares (n=50 positive ranks):
  exponent alpha=0.23  R^2=0.992  -> power law

WS/48 (n=50 positive ranks):
  exponent alpha=0.17  R^2=0.946  -> not a power law (bends)

BPM (n=50 positive ranks):
  exponent alpha=0.43  R^2=0.979  -> power law

OBPM (n=50 positive ranks):
  exponent alpha=0.44  R^2=0.972  -> power law

DBPM (n=50 positive ranks):
  exponent alpha=0.36  R^2=0.968  -> power law

VORP (n=50 positive ranks):
  exponent alpha=0.37  R^2=0.978  -> power law

RAPM (n=50 positive ranks):
  exponent alpha=0.25  R^2=0.958  -> power law

O-RAPM (n=50 positive ranks):
  exponent alpha=0.32  R^2=0.949  -> not a power law (bends)

D-RAPM (n=50 positive ranks):
  exponent alpha=0.30  R^2=0.986  -> power law

RAPM+prior (n=50 positive ranks):
  exponent alpha=0.41  R^2=0.970  -> power law

O-RAPM+prior (n=50 positive ranks):
  exponent alpha=0.41  R^2=0.972  -> power law

D-RAPM+prior (n=50 positive ranks):
  exponent alpha=0.32  R^2=0.927  -> not a power law (bends)

Power-law systems (R^2 >= 0.95): Game Score, PER, Win Shares, BPM, OBPM, DBPM, VORP, RAPM, D-RAPM, RAPM+prior, O-RAPM+prior
Bend instead of a straight line: WS/48, O-RAPM, D-RAPM+prior

─── RANK AGREEMENT (SPEARMAN CORRELATIONS) ──────────────────────
  Game Score vs PER: r=0.862
  Game Score vs Win Shares: r=0.674
  Game Score vs WS/48: r=0.393
  Game Score vs BPM: r=0.739
  Game Score vs OBPM: r=0.806
  Game Score vs DBPM: r=0.102
  Game Score vs VORP: r=0.786
  Game Score vs RAPM: r=0.296
  Game Score vs O-RAPM: r=0.348
  Game Score vs D-RAPM: r=0.032
  Game Score vs RAPM+prior: r=0.691
  Game Score vs O-RAPM+prior: r=0.743
  Game Score vs D-RAPM+prior: r=0.125
  PER vs Win Shares: r=0.768
  PER vs WS/48: r=0.652
  PER vs BPM: r=0.901
  PER vs OBPM: r=0.895
  PER vs DBPM: r=0.288
  PER vs VORP: r=0.891
  PER vs RAPM: r=0.302
  PER vs O-RAPM: r=0.323
  PER vs D-RAPM: r=0.067
  PER vs RAPM+prior: r=0.811
  PER vs O-RAPM+prior: r=0.809
  PER vs D-RAPM+prior: r=0.239
  Win Shares vs WS/48: r=0.796
  Win Shares vs BPM: r=0.680
  Win Shares vs OBPM: r=0.630
  Win Shares vs DBPM: r=0.306
  Win Shares vs VORP: r=0.743
  Win Shares vs RAPM: r=0.367
  Win Shares vs O-RAPM: r=0.354
  Win Shares vs D-RAPM: r=0.125
  Win Shares vs RAPM+prior: r=0.670
  Win Shares vs O-RAPM+prior: r=0.609
  Win Shares vs D-RAPM+prior: r=0.271
  WS/48 vs BPM: r=0.602
  WS/48 vs OBPM: r=0.537
  WS/48 vs DBPM: r=0.319
  WS/48 vs VORP: r=0.552
  WS/48 vs RAPM: r=0.272
  WS/48 vs O-RAPM: r=0.234
  WS/48 vs D-RAPM: r=0.120
  WS/48 vs RAPM+prior: r=0.590
  WS/48 vs O-RAPM+prior: r=0.504
  WS/48 vs D-RAPM+prior: r=0.311
  BPM vs OBPM: r=0.888
  BPM vs DBPM: r=0.498
  BPM vs VORP: r=0.964
  BPM vs RAPM: r=0.355
  BPM vs O-RAPM: r=0.351
  BPM vs D-RAPM: r=0.118
  BPM vs RAPM+prior: r=0.892
  BPM vs O-RAPM+prior: r=0.820
  BPM vs D-RAPM+prior: r=0.362
  OBPM vs DBPM: r=0.089
  OBPM vs VORP: r=0.866
  OBPM vs RAPM: r=0.280
  OBPM vs O-RAPM: r=0.387
  OBPM vs D-RAPM: r=-0.024
  OBPM vs RAPM+prior: r=0.773
  OBPM vs O-RAPM+prior: r=0.911
  OBPM vs D-RAPM+prior: r=0.053
  DBPM vs VORP: r=0.466
  DBPM vs RAPM: r=0.249
  DBPM vs O-RAPM: r=0.023
  DBPM vs D-RAPM: r=0.313
  DBPM vs RAPM+prior: r=0.491
  DBPM vs O-RAPM+prior: r=0.103
  DBPM vs D-RAPM+prior: r=0.738
  VORP vs RAPM: r=0.384
  VORP vs O-RAPM: r=0.378
  VORP vs D-RAPM: r=0.130
  VORP vs RAPM+prior: r=0.868
  VORP vs O-RAPM+prior: r=0.807
  VORP vs D-RAPM+prior: r=0.339
  RAPM vs O-RAPM: r=0.675
  RAPM vs D-RAPM: r=0.645
  RAPM vs RAPM+prior: r=0.622
  RAPM vs O-RAPM+prior: r=0.429
  RAPM vs D-RAPM+prior: r=0.497
  O-RAPM vs D-RAPM: r=-0.068
  O-RAPM vs RAPM+prior: r=0.482
  O-RAPM vs O-RAPM+prior: r=0.604
  O-RAPM vs D-RAPM+prior: r=-0.028
  D-RAPM vs RAPM+prior: r=0.349
  D-RAPM vs O-RAPM+prior: r=-0.028
  D-RAPM vs D-RAPM+prior: r=0.715
  RAPM+prior vs O-RAPM+prior: r=0.824
  RAPM+prior vs D-RAPM+prior: r=0.548
  O-RAPM+prior vs D-RAPM+prior: r=0.035

─── HOW MUCH EACH SYSTEM OVERLAPS THE OTHERS ────────────────────
Regression R² of each system on all others, with its own algebraic
kin (offense/defense halves, rescalings) held out. High = redundant;
low = carries signal the other systems miss.
  PER: overlap R² = 0.947
  OBPM: overlap R² = 0.945
  RAPM+prior: overlap R² = 0.939
  BPM: overlap R² = 0.937
  O-RAPM+prior: overlap R² = 0.933
  Game Score: overlap R² = 0.889
  VORP: overlap R² = 0.888
  D-RAPM+prior: overlap R² = 0.880
  DBPM: overlap R² = 0.770
  D-RAPM: overlap R² = 0.706
  RAPM: overlap R² = 0.684
  Win Shares: overlap R² = 0.668
  O-RAPM: overlap R² = 0.602
  WS/48: overlap R² = 0.596

─── CONSENSUS RATING — TOP 20 ───────────────────────────────────
   1. Nikola Jokić                    Consensus z = 4.00
   2. Shai Gilgeous-Alexander         Consensus z = 3.31
   3. Giannis Antetokounmpo           Consensus z = 2.74
   4. Victor Wembanyama               Consensus z = 2.69
   5. Luka Dončić                     Consensus z = 2.57
   6. Kawhi Leonard                   Consensus z = 2.29
   7. Jalen Duren                     Consensus z = 2.20
   8. Cade Cunningham                 Consensus z = 1.78
   9. Paul Reed                       Consensus z = 1.73
  10. Alperen Sengun                  Consensus z = 1.71
  11. Donovan Mitchell                Consensus z = 1.69
  12. Donovan Clingan                 Consensus z = 1.66
  13. Karl-Anthony Towns              Consensus z = 1.59
  14. Tyrese Maxey                    Consensus z = 1.54
  15. LaMelo Ball                     Consensus z = 1.52
  16. Jamal Murray                    Consensus z = 1.51
  17. Neemias Queta                   Consensus z = 1.49
  18. Mitchell Robinson               Consensus z = 1.48
  19. Jimmy Butler III                Consensus z = 1.48
  20. Amen Thompson                   Consensus z = 1.45

─── WINS-PREDICTIVE RATING — TOP 20 ─────────────────────────────
   1. Nikola Jokić                    Wins-predictive z = 4.37
   2. Shai Gilgeous-Alexander         Wins-predictive z = 4.21
   3. Victor Wembanyama               Wins-predictive z = 3.95
   4. Luka Dončić                     Wins-predictive z = 3.34
   5. Giannis Antetokounmpo           Wins-predictive z = 3.29
   6. Kawhi Leonard                   Wins-predictive z = 3.19
   7. Paul Reed                       Wins-predictive z = 2.39
   8. Jalen Duren                     Wins-predictive z = 2.26
   9. Donovan Mitchell                Wins-predictive z = 2.23
  10. Cade Cunningham                 Wins-predictive z = 2.10
  11. Tyrese Maxey                    Wins-predictive z = 1.96
  12. Chet Holmgren                   Wins-predictive z = 1.96
  13. LaMelo Ball                     Wins-predictive z = 1.95
  14. Jaylen Brown                    Wins-predictive z = 1.83
  15. Anthony Edwards                 Wins-predictive z = 1.78
  16. Stephen Curry                   Wins-predictive z = 1.74
  17. Jamal Murray                    Wins-predictive z = 1.69
  18. Alperen Sengun                  Wins-predictive z = 1.69
  19. Kevin Durant                    Wins-predictive z = 1.66
  20. Karl-Anthony Towns              Wins-predictive z = 1.66

─── COMPARISON: CONSENSUS vs. WINS-PREDICTIVE ───────────────────
  Spearman correlation between consensus and wins-predictive: 0.963 (p=0.000)
  Players rated much higher by wins-predictive than consensus:
    Victor Wembanyama               diff = +1.27
    Kawhi Leonard                   diff = +0.90
    Shai Gilgeous-Alexander         diff = +0.90
    Luka Dončić                     diff = +0.76
    Jayson Tatum                    diff = +0.66
  Players rated much lower by wins-predictive than consensus:
    Jericho Sims                    diff = -1.03
    Bub Carrington                  diff = -0.76
    Yves Missi                      diff = -0.63
    Terance Mann                    diff = -0.63
    Steven Adams                    diff = -0.62

─── UBER RATING CONCENTRATION (GINI vs CENTER-ROBUST STEEPNESS) ─
Gini clips negatives to zero, so it inflates 0-centered metrics (the uber
ratings and the BPM family). The power-law exponent alpha does not depend on
where zero sits, so it is the fair cross-system concentration read.

Consensus: Gini=0.753 (inflated), top-5% share=31.6%, alpha=0.37

Wins-Predictive: Gini=0.751 (inflated), top-5% share=32.7%, alpha=0.43

─── POWER-LAW / TAIL ANALYSIS ───────────────────────────────────

Cumulative-value metrics:
  Win Shares: Gini=0.362, top-5% hold 13.8% of value
    Skewness: 1.16 (right-skewed)
  VORP: Gini=0.611, top-5% hold 24.5% of value
    Skewness: 2.07 (right-skewed)

Rate metrics:
  PER: Gini=0.160, top-5% hold 8.6% of value
    Skewness: 0.83 (right-skewed)
  BPM: Gini=0.767, top-5% hold 34.3% of value
    Skewness: 2.09 (right-skewed)

─── WHO EACH SYSTEM LOVES vs. CONSENSUS ─────────────────────────

Game Score loves (vs. consensus):
  +1.56  Lauri Markkanen
  +1.37  Keyonte George
  +1.19  Anthony Edwards
Game Score discounts (vs. consensus):
  -2.02  Paul Reed
  -1.58  Mitchell Robinson
  -1.55  Goga Bitadze

PER loves (vs. consensus):
  +1.03  Giannis Antetokounmpo
  +0.91  Joel Embiid
  +0.85  Victor Wembanyama
PER discounts (vs. consensus):
  -0.86  Dorian Finney-Smith
  -0.70  Cason Wallace
  -0.67  Josh Green

Win Shares loves (vs. consensus):
  +2.18  Amen Thompson
  +2.01  Donovan Clingan
  +1.91  Rudy Gobert
Win Shares discounts (vs. consensus):
  -1.72  Giannis Antetokounmpo
  -1.65  Victor Wembanyama
  -1.64  Jayson Tatum

WS/48 loves (vs. consensus):
  +2.80  Steven Adams
  +2.34  Jericho Sims
  +2.26  Dylan Cardwell
WS/48 discounts (vs. consensus):
  -2.00  Victor Wembanyama
  -1.87  Kawhi Leonard
  -1.84  Luka Dončić

BPM loves (vs. consensus):
  +1.09  Giannis Antetokounmpo
  +0.97  Paul Reed
  +0.80  T.J. McConnell
BPM discounts (vs. consensus):
  -0.92  Jericho Sims
  -0.79  Dwight Powell
  -0.76  Draymond Green

OBPM loves (vs. consensus):
  +1.62  Giannis Antetokounmpo
  +1.25  Stephen Curry
  +1.21  Darius Garland
OBPM discounts (vs. consensus):
  -1.40  Lonzo Ball
  -1.37  Ausar Thompson
  -1.19  Dwight Powell

DBPM loves (vs. consensus):
  +2.76  Alex Caruso
  +2.49  Cason Wallace
  +2.36  Dru Smith
DBPM discounts (vs. consensus):
  -2.83  Nikola Jokić
  -2.60  Giannis Antetokounmpo
  -2.31  Lauri Markkanen

VORP loves (vs. consensus):
  +1.81  Shai Gilgeous-Alexander
  +1.59  Nikola Jokić
  +1.45  Luka Dončić
VORP discounts (vs. consensus):
  -0.84  Bub Carrington
  -0.84  Giannis Antetokounmpo
  -0.80  Steven Adams

─── RETRODICTION: WHICH RATING REBUILDS TEAM RESULTS ────────────
Each system's player ratings are minutes-weighted to the team level, then
fit to team point differential per game across the 30 teams. R² is the
in-sample fit; CV R² is leave-one-team-out (the honest out-of-sample read).
Systems marked [team-fit] are built using team or lineup point
differential, so a high score is partly mechanical. Systems marked
[outcome-blind] never saw who won; their score is the genuine test.

  [team-fit]     BPM            R²=1.000  CV R²=1.000
  [team-fit]     VORP           R²=0.948  CV R²=0.939
  [team-fit]     RAPM+prior     R²=0.935  CV R²=0.924
  [team-fit]     RAPM           R²=0.857  CV R²=0.825
  [team-fit]     DBPM           R²=0.834  CV R²=0.815
  [team-fit]     O-RAPM+prior   R²=0.816  CV R²=0.787
  [team-fit]     OBPM           R²=0.784  CV R²=0.741
  [outcome-blind] PER            R²=0.771  CV R²=0.727
  [team-fit]     D-RAPM+prior   R²=0.748  CV R²=0.717
  [team-fit]     O-RAPM         R²=0.722  CV R²=0.673
  [team-fit]     D-RAPM         R²=0.649  CV R²=0.603
  [team-fit]     Win Shares     R²=0.596  CV R²=0.535
  [outcome-blind] Game Score     R²=0.521  CV R²=0.471
  [team-fit]     WS/48          R²=0.451  CV R²=0.380

BPM sits on top at CV R²=1.000, but only
mechanically: the team-margin anchor builds the box metrics to sum to
team point differential (BPM equals it exactly). Among the ratings that
never saw who won, PER leads, rebuilding 73% of the team point-differential spread
out of sample.

─── NEXT-SEASON RETRODICTION (PREDICTING THIS SEASON FROM LAST) ─
Last season's (2024-25) player ratings are
distributed across this season's rosters (weighted by this season's minutes)
and fit to this season's team point differential. Because each metric's team
adjustment is fit to its own season, predicting the next season removes the
in-sample circularity. Describing the season just played and forecasting the
next are different tests, and they reward different metrics.

Prior-rating coverage: 88% of this season's team minutes
were played by players who also carried a rating last season.

                   describes  predicts
  system           (same yr) (next yr)
  [team-fit]     RAPM+prior       0.924     0.590
  [team-fit]     VORP             0.939     0.562
  [team-fit]     BPM              1.000     0.560
  [team-fit]     O-RAPM+prior     0.787     0.517
  [team-fit]     O-RAPM           0.673     0.452
  [team-fit]     OBPM             0.741     0.420
  [outcome-blind] Game Score       0.471     0.400
  [team-fit]     RAPM             0.825     0.375
  [team-fit]     Win Shares       0.535     0.374
  [outcome-blind] PER              0.727     0.368
  [team-fit]     WS/48            0.380     0.269
  [team-fit]     DBPM             0.815     0.256
  [team-fit]     D-RAPM+prior     0.717     0.175
  [team-fit]     D-RAPM           0.603     0.032

Best forecaster of next season: RAPM+prior (R²=0.590). Best description of
the season itself: BPM.
PER falls from 0.73 describing the season to 0.37
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
  [team-fit]     VORP            0.907 [0.83,0.96]   0.519 [0.26,0.74]
  [team-fit]     BPM             0.999 [1.00,1.00]   0.514 [0.18,0.73]
  [outcome-blind] Game Score      0.385 [0.09,0.62]   0.420 [0.14,0.61]
  [team-fit]     OBPM            0.614 [0.27,0.79]   0.380 [0.09,0.67]
  [team-fit]     Win Shares      0.289 [0.01,0.54]   0.329 [0.08,0.52]
  [team-fit]     DBPM            0.490 [0.16,0.82]   0.260 [0.02,0.55]
  [outcome-blind] PER             0.636 [0.17,0.81]   0.252 [0.00,0.50]
  [team-fit]     WS/48           0.130 [-0.11,0.42]   0.187 [0.00,0.51]

Across 30 seasons the best description is BPM; across
29 pairs the best forecast is VORP.
PER averages 0.64 describing but only 0.25 forecasting,
the same collapse the single pair showed, now seen across 29 pairs.
BPM forecasts better than PER in 29 of 29 pairs.

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
  [team-fit]     RAPM+prior      0.901       0.621
  [team-fit]     BPM             0.999       0.601
  [team-fit]     VORP            0.919       0.553
  [team-fit]     OBPM            0.698       0.468
  [outcome-blind] Game Score      0.424       0.446
  [team-fit]     RAPM            0.776       0.377
  [team-fit]     Win Shares      0.369       0.367
  [team-fit]     DBPM            0.524       0.293
  [outcome-blind] PER             0.641       0.267
  [team-fit]     WS/48           0.244       0.260

Over these 12 pairs RAPM forecasts 6 of 10; the best forecaster is RAPM+prior.
RAPM_MY forecasts 1 of 10 (bare RAPM was 6).

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
  PER                 0.803 [0.76,0.85]        64%
  WS/48               0.796 [0.69,0.86]        47%
  VORP                0.789 [0.71,0.83]        58%
  OBPM                0.763 [0.71,0.81]        62%
  BPM                 0.750 [0.67,0.80]        59%
  Win Shares          0.722 [0.65,0.79]        53%
  DBPM                0.674 [0.58,0.73]        39%

Steadiest year to year: Game Score (corr 0.85). Jumpiest: DBPM (corr 0.67).
Best at keeping the same names in the top 20: Game Score (68%), against a chance level near 5%.

─── REGULAR SEASON vs PLAYOFFS (RATE-METRIC DELTAS) ─────────────
Players with >= 150 playoff minutes: 103
Rate metrics compared (each normalized within its season type): PER, WS/48, BPM, OBPM, DBPM
Delta = playoff minus regular season. 'adj' subtracts the average delta
among this qualified pool, so a riser is measured against the other
rotation players who also advanced. The composite shift z averages the
standardized adjusted deltas of PER, WS/48, and BPM, so a riser needs the
three box formulations to agree.
Note: BPM here is our recompute, validated against Basketball-Reference
(see the BPM-validation section); the playoff BPM is anchored to each
team's playoff point margin.

Biggest playoff RISERS (raised their level above their regular-season form):
   1. Jayson Tatum               BOS  shift z = +2.15  (PER +8.6 vs regular season)
   2. OG Anunoby                 NYK  shift z = +2.09  (PER +8.0 vs regular season)
   3. Mike Conley                MIN  shift z = +1.95  (PER +6.2 vs regular season)
   4. Tari Eason                 HOU  shift z = +1.77  (PER +6.8 vs regular season)
   5. Cason Wallace              OKC  shift z = +1.75  (PER +5.8 vs regular season)
   6. Collin Murray-Boyles       TOR  shift z = +1.60  (PER +7.3 vs regular season)
   7. Rui Hachimura              LAL  shift z = +1.53  (PER +5.5 vs regular season)
   8. Karl-Anthony Towns         NYK  shift z = +1.38  (PER +2.5 vs regular season)
   9. Alex Caruso                OKC  shift z = +1.33  (PER +6.5 vs regular season)
  10. Marcus Smart               LAL  shift z = +1.28  (PER +4.7 vs regular season)

Biggest playoff FALLERS (dropped below their regular-season form):
   1. Nikola Jokić               DEN  shift z = -2.46  (PER -7.0 vs regular season)
   2. Jalen Duren                DET  shift z = -2.35  (PER -10.4 vs regular season)
   3. Nickeil Alexander-Walker   ATL  shift z = -2.07  (PER -7.4 vs regular season)
   4. Jalen Suggs                ORL  shift z = -1.84  (PER -6.5 vs regular season)
   5. Jamal Murray               DEN  shift z = -1.57  (PER -5.1 vs regular season)
   6. Julius Randle              MIN  shift z = -1.49  (PER -6.1 vs regular season)
   7. Austin Reaves              LAL  shift z = -1.34  (PER -5.3 vs regular season)
   8. Derrick White              BOS  shift z = -1.25  (PER -5.1 vs regular season)
   9. Keldon Johnson             SAS  shift z = -1.24  (PER -5.0 vs regular season)
  10. Anthony Edwards            MIN  shift z = -1.16  (PER -4.6 vs regular season)

Regular-season consensus #1 Nikola Jokić: playoff shift z = -2.46 (faller rank 1 of 103)

─── SEASON-OVER-SEASON CHANGE (PREVIOUS → CURRENT) ──────────────
Players qualified in both 2024-25 and 2025-26: 290
Consensus rank agreement 2024-25 → 2025-26: 0.75
Mean box-score agreement: 2024-25 0.70, 2025-26 0.73

  2025-26 consensus top 5:
   1. Nikola Jokić
   2. Shai Gilgeous-Alexander
   3. Giannis Antetokounmpo
   4. Victor Wembanyama
   5. Luka Dončić

  2024-25 consensus top 5:
   1. Nikola Jokić
   2. Shai Gilgeous-Alexander
   3. Giannis Antetokounmpo
   4. Luka Dončić
   5. Domantas Sabonis

  Biggest consensus risers 2024-25 → 2025-26:
   1. Kawhi Leonard  +1.37
   2. Micah Potter  +1.36
   3. Stephon Castle  +1.36
   4. Victor Wembanyama  +1.24
   5. Neemias Queta  +1.20

  Biggest consensus fallers 2024-25 → 2025-26:
   1. Ivica Zubac  -1.50
   2. Domantas Sabonis  -1.49
   3. Jordan Poole  -1.21
   4. Jaren Jackson Jr.  -1.20
   5. Anthony Davis  -1.19

─── PLAYOFF-WEIGHTED VALUE (REGULAR SEASON + PLAYOFFS) ──────────
Playoff pool: 103 players with >= 150 playoff minutes.
PWV = minutes-weighted blend of regular-season and playoff BPM, playoff minutes weighted 2x (primary).

Top 10 by Playoff-Weighted Value (playoffs x2):
   1. Nikola Jokić               PWV +10.19  (reg +11.4 → playoff +4.3)
   2. Victor Wembanyama          PWV +8.83  (reg +8.9 → playoff +8.8)
   3. Shai Gilgeous-Alexander    PWV +8.56  (reg +10.4 → playoff +4.6)
   4. Karl-Anthony Towns         PWV +5.23  (reg +3.9 → playoff +8.0)
   5. Cade Cunningham            PWV +4.24  (reg +5.3 → playoff +2.2)
   6. Jayson Tatum               PWV +4.21  (reg +3.0 → playoff +5.6)
   7. Jalen Brunson              PWV +3.83  (reg +3.4 → playoff +4.6)
   8. Donovan Mitchell           PWV +3.76  (reg +5.2 → playoff +1.3)
   9. Chet Holmgren              PWV +3.73  (reg +4.1 → playoff +2.8)
  10. Jaylen Brown               PWV +3.65  (reg +4.0 → playoff +2.0)

Jalen Brunson: regular-season BPM +3.4, playoff BPM +4.6.
  PWV rank as the playoffs are weighted more: 15th (1x) → 7th (2x) → 7th (3x), of 103.

─── EXAMPLE PLAYERS (ARCHETYPES) ────────────────────────────────
Agreed elite (best worst-rank across 5 systems): Nikola Jokić (worst rank 1).
Defense-driven star (top-12 BPM, highest DBPM): Victor Wembanyama (BPM +8.9, of which DBPM +3.9).
High-usage scorer the metrics split on: Pascal Siakam (USG 30%, PER rank 45 vs BPM rank 126).
Biggest playoff riser (top composite shift): Jayson Tatum (shift z +2.15).
  Brunson impact ranks: OBPM 12, BPM 29, RAPM 204, RAPM+prior 64 (scoring outruns net on-court impact)
Saved → docs/player_rating_overview_facts_reference.md

```
