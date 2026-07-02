# Player Rating Overview: Analysis Results

Season: 2025–26

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
  1. Chet Holmgren: RAPM +11.05 per 100
  2. Derrick White: RAPM +10.17 per 100
  3. Josh Green: RAPM +9.81 per 100
  4. Shai Gilgeous-Alexander: RAPM +9.72 per 100
  5. Victor Wembanyama: RAPM +9.19 per 100
  Mean rank agreement with box-score systems: 0.37
  RAPM #1 (Chet Holmgren) consensus rank: 20

─── RAPM_MY — PRIOR-INFORMED, MULTI-YEAR ────────────────────────
  1. Shai Gilgeous-Alexander: RAPM_MY +11.01 per 100
  2. Nikola Jokić: RAPM_MY +10.87 per 100
  3. Giannis Antetokounmpo: RAPM_MY +10.09 per 100
  4. Victor Wembanyama: RAPM_MY +9.26 per 100
  5. Kawhi Leonard: RAPM_MY +8.12 per 100
  Mean rank agreement with box-score systems: 0.77
  Rank agreement with the consensus: 0.91
  Bare RAPM rank agreement with the consensus: 0.46

─── RAPM RELIABILITY (SPLIT-HALF AND YEAR-OVER-YEAR) ────────────
Split-half: fit bare RAPM on two random halves of the pooled
possessions, then correlate the two estimates. If the lineup signal
is real the halves agree; if it is noise they do not.
  Split-half reliability (279 players, 1000+ min): 0.39
  (near-zero would be noise; a usable metric sits near 0.5-0.7)
  By minutes bin:
       0-500  min: n=423  r=+0.15
     500-1000 min: n= 99  r=+0.12
    1000-1500 min: n=115  r=+0.32
    1500-2000 min: n= 87  r=+0.41
    2000-3500 min: n= 77  r=+0.41

Year-over-year stability (players 1000+ min in both seasons):
  RAPM     +0.40
  RAPM_MY  +0.84
  BPM      +0.79

After the possession-reconstruction fixes, the lineup signal is real,
not noise. A reconstruction bug had been discarding ~60% of games with
complete play-by-play; recovering them took split-half reliability from
about 0.10 to 0.39, and bare single-season RAPM now holds from one
season to the next at 0.40 (it was near zero before).
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
  Mean: 3.91  Median: 3.35  Std: 2.54
  Min: 0.06  Max: 15.66
  Gini: 0.353  Top-5% share: 13.5%
  Skew: +1.11  Excess kurtosis: +1.51  Below zero: 0%

WS/48 (n=378):
  Mean: 0.13  Median: 0.12  Std: 0.06
  Min: 0.00  Max: 0.35
  Gini: 0.260  Top-5% share: 11.4%
  Skew: +0.90  Excess kurtosis: +0.95  Below zero: 0%

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
  Mean: 0.40  Median: 0.24  Std: 3.53
  Min: -10.00  Max: 11.05
  Gini: 0.690  Top-5% share: 24.9%
  Skew: +0.04  Excess kurtosis: +0.12  Below zero: 47%

O-RAPM (n=378):
  Mean: 0.33  Median: 0.40  Std: 2.53
  Min: -8.29  Max: 8.86
  Gini: 0.672  Top-5% share: 25.3%
  Skew: +0.07  Excess kurtosis: +0.34  Below zero: 44%

D-RAPM (n=378):
  Mean: 0.07  Median: 0.17  Std: 2.55
  Min: -8.44  Max: 9.56
  Gini: 0.706  Top-5% share: 27.1%
  Skew: +0.05  Excess kurtosis: +0.69  Below zero: 47%

RAPM+prior (n=378):
  Mean: -0.16  Median: -0.26  Std: 2.72
  Min: -6.96  Max: 11.01
  Gini: 0.756  Top-5% share: 33.0%
  Skew: +0.63  Excess kurtosis: +1.59  Below zero: 54%

O-RAPM+prior (n=378):
  Mean: -0.17  Median: -0.40  Std: 2.23
  Min: -5.92  Max: 10.44
  Gini: 0.777  Top-5% share: 35.1%
  Skew: +0.87  Excess kurtosis: +2.39  Below zero: 57%

D-RAPM+prior (n=378):
  Mean: 0.01  Median: -0.08  Std: 1.39
  Min: -3.58  Max: 5.77
  Gini: 0.736  Top-5% share: 29.3%
  Skew: +0.38  Excess kurtosis: +0.55  Below zero: 52%

RAPM distribution shape, pooled over 29 seasons (n=9820 player-seasons):
  Skew: +0.10  Excess kurtosis: +0.11  Below zero: 47%

─── POWER-LAW FIT (VALUE VS RANK, LOG-LOG) ──────────────────────
A system's top-50 value-vs-rank curve is a power law when the
log-log fit clears R^2 >= 0.95 (a straight line on log-log axes).

Game Score (n=50 positive ranks):
  exponent alpha=0.17  R^2=0.973  -> power law

PER (n=50 positive ranks):
  exponent alpha=0.14  R^2=0.958  -> power law

Win Shares (n=50 positive ranks):
  exponent alpha=0.22  R^2=0.983  -> power law

WS/48 (n=50 positive ranks):
  exponent alpha=0.17  R^2=0.931  -> not a power law (bends)

BPM (n=50 positive ranks):
  exponent alpha=0.43  R^2=0.979  -> power law

OBPM (n=50 positive ranks):
  exponent alpha=0.44  R^2=0.972  -> power law

DBPM (n=50 positive ranks):
  exponent alpha=0.36  R^2=0.968  -> power law

VORP (n=50 positive ranks):
  exponent alpha=0.37  R^2=0.978  -> power law

RAPM (n=50 positive ranks):
  exponent alpha=0.26  R^2=0.966  -> power law

O-RAPM (n=50 positive ranks):
  exponent alpha=0.32  R^2=0.963  -> power law

D-RAPM (n=50 positive ranks):
  exponent alpha=0.31  R^2=0.990  -> power law

RAPM+prior (n=50 positive ranks):
  exponent alpha=0.41  R^2=0.975  -> power law

O-RAPM+prior (n=50 positive ranks):
  exponent alpha=0.41  R^2=0.974  -> power law

D-RAPM+prior (n=50 positive ranks):
  exponent alpha=0.32  R^2=0.937  -> not a power law (bends)

Power-law systems (R^2 >= 0.95): Game Score, PER, Win Shares, BPM, OBPM, DBPM, VORP, RAPM, O-RAPM, D-RAPM, RAPM+prior, O-RAPM+prior
Bend instead of a straight line: WS/48, D-RAPM+prior

─── RANK AGREEMENT (SPEARMAN CORRELATIONS) ──────────────────────
  Game Score vs PER: r=0.862
  Game Score vs Win Shares: r=0.671
  Game Score vs WS/48: r=0.385
  Game Score vs BPM: r=0.739
  Game Score vs OBPM: r=0.806
  Game Score vs DBPM: r=0.102
  Game Score vs VORP: r=0.786
  Game Score vs RAPM: r=0.329
  Game Score vs O-RAPM: r=0.383
  Game Score vs D-RAPM: r=0.057
  Game Score vs RAPM+prior: r=0.696
  Game Score vs O-RAPM+prior: r=0.750
  Game Score vs D-RAPM+prior: r=0.143
  PER vs Win Shares: r=0.764
  PER vs WS/48: r=0.659
  PER vs BPM: r=0.901
  PER vs OBPM: r=0.895
  PER vs DBPM: r=0.288
  PER vs VORP: r=0.891
  PER vs RAPM: r=0.335
  PER vs O-RAPM: r=0.356
  PER vs D-RAPM: r=0.100
  PER vs RAPM+prior: r=0.811
  PER vs O-RAPM+prior: r=0.815
  PER vs D-RAPM+prior: r=0.256
  Win Shares vs WS/48: r=0.781
  Win Shares vs BPM: r=0.716
  Win Shares vs OBPM: r=0.614
  Win Shares vs DBPM: r=0.414
  Win Shares vs VORP: r=0.786
  Win Shares vs RAPM: r=0.415
  Win Shares vs O-RAPM: r=0.374
  Win Shares vs D-RAPM: r=0.191
  Win Shares vs RAPM+prior: r=0.704
  Win Shares vs O-RAPM+prior: r=0.603
  Win Shares vs D-RAPM+prior: r=0.350
  WS/48 vs BPM: r=0.667
  WS/48 vs OBPM: r=0.524
  WS/48 vs DBPM: r=0.485
  WS/48 vs VORP: r=0.617
  WS/48 vs RAPM: r=0.350
  WS/48 vs O-RAPM: r=0.254
  WS/48 vs D-RAPM: r=0.223
  WS/48 vs RAPM+prior: r=0.654
  WS/48 vs O-RAPM+prior: r=0.503
  WS/48 vs D-RAPM+prior: r=0.437
  BPM vs OBPM: r=0.888
  BPM vs DBPM: r=0.498
  BPM vs VORP: r=0.964
  BPM vs RAPM: r=0.389
  BPM vs O-RAPM: r=0.378
  BPM vs D-RAPM: r=0.153
  BPM vs RAPM+prior: r=0.894
  BPM vs O-RAPM+prior: r=0.828
  BPM vs D-RAPM+prior: r=0.381
  OBPM vs DBPM: r=0.089
  OBPM vs VORP: r=0.866
  OBPM vs RAPM: r=0.312
  OBPM vs O-RAPM: r=0.416
  OBPM vs D-RAPM: r=0.003
  OBPM vs RAPM+prior: r=0.774
  OBPM vs O-RAPM+prior: r=0.916
  OBPM vs D-RAPM+prior: r=0.074
  DBPM vs VORP: r=0.466
  DBPM vs RAPM: r=0.253
  DBPM vs O-RAPM: r=0.020
  DBPM vs D-RAPM: r=0.335
  DBPM vs RAPM+prior: r=0.489
  DBPM vs O-RAPM+prior: r=0.111
  DBPM vs D-RAPM+prior: r=0.735
  VORP vs RAPM: r=0.413
  VORP vs O-RAPM: r=0.409
  VORP vs D-RAPM: r=0.161
  VORP vs RAPM+prior: r=0.870
  VORP vs O-RAPM+prior: r=0.815
  VORP vs D-RAPM+prior: r=0.354
  RAPM vs O-RAPM: r=0.682
  RAPM vs D-RAPM: r=0.673
  RAPM vs RAPM+prior: r=0.650
  RAPM vs O-RAPM+prior: r=0.453
  RAPM vs D-RAPM+prior: r=0.523
  O-RAPM vs D-RAPM: r=-0.019
  O-RAPM vs RAPM+prior: r=0.504
  O-RAPM vs O-RAPM+prior: r=0.618
  O-RAPM vs D-RAPM+prior: r=-0.001
  D-RAPM vs RAPM+prior: r=0.391
  D-RAPM vs O-RAPM+prior: r=0.012
  D-RAPM vs D-RAPM+prior: r=0.741
  RAPM+prior vs O-RAPM+prior: r=0.830
  RAPM+prior vs D-RAPM+prior: r=0.570
  O-RAPM+prior vs D-RAPM+prior: r=0.069

─── HOW MUCH EACH SYSTEM OVERLAPS THE OTHERS ────────────────────
Regression R² of each system on all others, with its own algebraic
kin (offense/defense halves, rescalings) held out. High = redundant;
low = carries signal the other systems miss.
  PER: overlap R² = 0.946
  OBPM: overlap R² = 0.946
  RAPM+prior: overlap R² = 0.942
  BPM: overlap R² = 0.937
  O-RAPM+prior: overlap R² = 0.934
  Game Score: overlap R² = 0.892
  VORP: overlap R² = 0.890
  D-RAPM+prior: overlap R² = 0.886
  DBPM: overlap R² = 0.773
  D-RAPM: overlap R² = 0.729
  Win Shares: overlap R² = 0.711
  RAPM: overlap R² = 0.706
  WS/48: overlap R² = 0.660
  O-RAPM: overlap R² = 0.609

─── CONSENSUS RATING — TOP 20 ───────────────────────────────────
   1. Nikola Jokić                    Consensus z = 3.98
   2. Shai Gilgeous-Alexander         Consensus z = 3.35
   3. Victor Wembanyama               Consensus z = 2.80
   4. Giannis Antetokounmpo           Consensus z = 2.68
   5. Luka Dončić                     Consensus z = 2.58
   6. Kawhi Leonard                   Consensus z = 2.33
   7. Jalen Duren                     Consensus z = 2.22
   8. Cade Cunningham                 Consensus z = 1.80
   9. Paul Reed                       Consensus z = 1.77
  10. Alperen Sengun                  Consensus z = 1.74
  11. Donovan Mitchell                Consensus z = 1.70
  12. Karl-Anthony Towns              Consensus z = 1.64
  13. Donovan Clingan                 Consensus z = 1.64
  14. Tyrese Maxey                    Consensus z = 1.55
  15. LaMelo Ball                     Consensus z = 1.52
  16. Neemias Queta                   Consensus z = 1.50
  17. Amen Thompson                   Consensus z = 1.50
  18. Jamal Murray                    Consensus z = 1.49
  19. Mitchell Robinson               Consensus z = 1.48
  20. Chet Holmgren                   Consensus z = 1.48

─── WINS-PREDICTIVE RATING — TOP 20 ─────────────────────────────
   1. Nikola Jokić                    Wins-predictive z = 4.57
   2. Shai Gilgeous-Alexander         Wins-predictive z = 4.21
   3. Giannis Antetokounmpo           Wins-predictive z = 3.64
   4. Victor Wembanyama               Wins-predictive z = 3.57
   5. Luka Dončić                     Wins-predictive z = 3.38
   6. Kawhi Leonard                   Wins-predictive z = 3.15
   7. Jalen Duren                     Wins-predictive z = 2.41
   8. Donovan Mitchell                Wins-predictive z = 2.28
   9. Paul Reed                       Wins-predictive z = 2.14
  10. Cade Cunningham                 Wins-predictive z = 2.08
  11. Tyrese Maxey                    Wins-predictive z = 1.98
  12. Jamal Murray                    Wins-predictive z = 1.91
  13. Stephen Curry                   Wins-predictive z = 1.90
  14. LaMelo Ball                     Wins-predictive z = 1.86
  15. Chet Holmgren                   Wins-predictive z = 1.78
  16. Jaylen Brown                    Wins-predictive z = 1.78
  17. Anthony Edwards                 Wins-predictive z = 1.75
  18. Joel Embiid                     Wins-predictive z = 1.74
  19. Alperen Sengun                  Wins-predictive z = 1.73
  20. Karl-Anthony Towns              Wins-predictive z = 1.72

─── COMPARISON: CONSENSUS vs. WINS-PREDICTIVE ───────────────────
  Spearman correlation between consensus and wins-predictive: 0.981 (p=0.000)
  Players rated much higher by wins-predictive than consensus:
    Giannis Antetokounmpo           diff = +0.96
    Shai Gilgeous-Alexander         diff = +0.86
    Kawhi Leonard                   diff = +0.83
    Luka Dončić                     diff = +0.80
    Victor Wembanyama               diff = +0.76
  Players rated much lower by wins-predictive than consensus:
    Jericho Sims                    diff = -0.62
    Dwight Powell                   diff = -0.58
    Draymond Green                  diff = -0.52
    Steven Adams                    diff = -0.51
    Lonzo Ball                      diff = -0.46

─── UBER RATING CONCENTRATION (GINI vs CENTER-ROBUST STEEPNESS) ─
Gini clips negatives to zero, so it inflates 0-centered metrics (the uber
ratings and the BPM family). The power-law exponent alpha does not depend on
where zero sits, so it is the fair cross-system concentration read.

Consensus: Gini=0.753 (inflated), top-5% share=31.6%, alpha=0.38

Wins-Predictive: Gini=0.753 (inflated), top-5% share=32.8%, alpha=0.42

─── POWER-LAW / TAIL ANALYSIS ───────────────────────────────────

Cumulative-value metrics:
  Win Shares: Gini=0.353, top-5% hold 13.5% of value
    Skewness: 1.11 (right-skewed)
  VORP: Gini=0.611, top-5% hold 24.5% of value
    Skewness: 2.07 (right-skewed)

Rate metrics:
  PER: Gini=0.160, top-5% hold 8.6% of value
    Skewness: 0.83 (right-skewed)
  BPM: Gini=0.767, top-5% hold 34.3% of value
    Skewness: 2.09 (right-skewed)

─── WHO EACH SYSTEM LOVES vs. CONSENSUS ─────────────────────────

Game Score loves (vs. consensus):
  +1.64  Lauri Markkanen
  +1.46  Keyonte George
  +1.25  Zach LaVine
Game Score discounts (vs. consensus):
  -2.06  Paul Reed
  -1.58  Mitchell Robinson
  -1.52  Goga Bitadze

PER loves (vs. consensus):
  +1.09  Giannis Antetokounmpo
  +0.89  Joel Embiid
  +0.88  Lauri Markkanen
PER discounts (vs. consensus):
  -0.87  Dorian Finney-Smith
  -0.85  Cason Wallace
  -0.69  Josh Green

Win Shares loves (vs. consensus):
  +2.14  Amen Thompson
  +1.93  Rudy Gobert
  +1.90  Donovan Clingan
Win Shares discounts (vs. consensus):
  -1.85  Giannis Antetokounmpo
  -1.61  Jayson Tatum
  -1.38  Stephen Curry

WS/48 loves (vs. consensus):
  +2.75  Steven Adams
  +2.29  Mitchell Robinson
  +2.08  Dylan Cardwell
WS/48 discounts (vs. consensus):
  -1.80  Luka Dončić
  -1.79  Kawhi Leonard
  -1.67  Shai Gilgeous-Alexander

BPM loves (vs. consensus):
  +1.14  Giannis Antetokounmpo
  +0.93  Paul Reed
  +0.85  T.J. McConnell
BPM discounts (vs. consensus):
  -0.87  Jericho Sims
  -0.79  Dwight Powell
  -0.76  Draymond Green

OBPM loves (vs. consensus):
  +1.68  Giannis Antetokounmpo
  +1.25  Stephen Curry
  +1.24  Darius Garland
OBPM discounts (vs. consensus):
  -1.46  Ausar Thompson
  -1.43  Lonzo Ball
  -1.18  Dwight Powell

DBPM loves (vs. consensus):
  +2.68  Alex Caruso
  +2.35  Cason Wallace
  +2.33  Dru Smith
DBPM discounts (vs. consensus):
  -2.80  Nikola Jokić
  -2.54  Giannis Antetokounmpo
  -2.23  Lauri Markkanen

VORP loves (vs. consensus):
  +1.77  Shai Gilgeous-Alexander
  +1.62  Nikola Jokić
  +1.45  Luka Dončić
VORP discounts (vs. consensus):
  -0.79  Steven Adams
  -0.78  Giannis Antetokounmpo
  -0.78  Mitchell Robinson

─── RETRODICTION: WHICH RATING REBUILDS TEAM RESULTS ────────────
Each system's player ratings are minutes-weighted to the team level, then
fit to team point differential per game across the 30 teams. R² is the
in-sample fit; CV R² is leave-one-team-out (the honest out-of-sample read).
Systems marked [team-fit] are built using team or lineup point
differential, so a high score is partly mechanical. Systems marked
[outcome-blind] never saw who won; their score is the genuine test.

  [team-fit]     BPM            R²=1.000  CV R²=1.000
  [team-fit]     VORP           R²=0.948  CV R²=0.939
  [team-fit]     RAPM+prior     R²=0.944  CV R²=0.936
  [team-fit]     RAPM           R²=0.904  CV R²=0.887
  [team-fit]     O-RAPM+prior   R²=0.841  CV R²=0.818
  [team-fit]     DBPM           R²=0.834  CV R²=0.815
  [team-fit]     O-RAPM         R²=0.777  CV R²=0.744
  [team-fit]     WS/48          R²=0.773  CV R²=0.743
  [team-fit]     OBPM           R²=0.784  CV R²=0.741
  [team-fit]     D-RAPM+prior   R²=0.765  CV R²=0.739
  [outcome-blind] PER            R²=0.771  CV R²=0.727
  [team-fit]     Win Shares     R²=0.734  CV R²=0.690
  [team-fit]     D-RAPM         R²=0.706  CV R²=0.670
  [outcome-blind] Game Score     R²=0.521  CV R²=0.471

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
  [team-fit]     RAPM+prior       0.936     0.546
  [team-fit]     VORP             0.939     0.519
  [team-fit]     BPM              1.000     0.519
  [team-fit]     O-RAPM+prior     0.818     0.482
  [team-fit]     O-RAPM           0.744     0.421
  [team-fit]     Win Shares       0.690     0.371
  [team-fit]     OBPM             0.741     0.345
  [team-fit]     WS/48            0.743     0.318
  [outcome-blind] Game Score       0.471     0.318
  [team-fit]     RAPM             0.887     0.241
  [outcome-blind] PER              0.727     0.222
  [team-fit]     DBPM             0.815     0.156
  [team-fit]     D-RAPM+prior     0.739     0.092
  [team-fit]     D-RAPM           0.670    -0.092

Best forecaster of next season: RAPM+prior (CV R²=0.546). Best description of
the season itself: BPM.
PER falls from 0.73 describing the season to 0.22
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
  [team-fit]     VORP            0.907 [0.83,0.96]   0.446 [0.17,0.70]
  [team-fit]     BPM             0.999 [1.00,1.00]   0.429 [-0.14,0.70]
  [outcome-blind] Game Score      0.385 [0.09,0.62]   0.334 [0.02,0.55]
  [team-fit]     Win Shares      0.562 [0.29,0.72]   0.324 [0.10,0.54]
  [team-fit]     OBPM            0.614 [0.27,0.79]   0.276 [-0.29,0.64]
  [team-fit]     WS/48           0.573 [0.08,0.81]   0.196 [-0.47,0.59]
  [team-fit]     DBPM            0.490 [0.16,0.82]   0.150 [-0.16,0.48]
  [outcome-blind] PER             0.636 [0.17,0.81]  -2.816 [-65.85,0.44]

Across 30 seasons the best description is BPM; across
29 pairs the best forecast is VORP.
PER averages 0.64 describing but only -2.82 forecasting,
the same collapse the single pair showed, now seen across 29 pairs.
In the typical (median) pair PER describes 0.68 and forecasts 0.10.
BPM forecasts better than PER in 28 of 29 pairs.

─── IMPACT-ERA PANEL: BOX SCORES vs RAPM (EQUAL SEASONS) ────────
The panel above runs 30 seasons, but RAPM can only be computed for the
29 seasons with cached play-by-play (1997-98 through 2025-26).
This second panel scores the box-score systems AND RAPM over those same
seasons, so the comparison is even. RAPM is built from lineup point
differential, so its DESCRIBE score (rebuilding the same season's team
margin) is partly mechanical; the FORECAST score (prior-season RAPM onto
next season's rosters) is the honest read.

                     describes    predicts
  system             (same yr)   (next yr)
  [team-fit]     RAPM+prior      0.908       0.462
  [team-fit]     VORP            0.906       0.446
  [team-fit]     BPM             0.999       0.426
  [outcome-blind] Game Score      0.387       0.332
  [team-fit]     Win Shares      0.560       0.322
  [team-fit]     OBPM            0.610       0.273
  [team-fit]     RAPM            0.820       0.264
  [team-fit]     WS/48           0.571       0.192
  [team-fit]     DBPM            0.482       0.146
  [outcome-blind] PER             0.634      -2.920

Over these 28 pairs RAPM forecasts 7 of 10; the best forecaster is RAPM+prior.
RAPM_MY forecasts 1 of 10 (bare RAPM was 7).

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
  WS/48               0.812 [0.74,0.87]        47%
  PER                 0.803 [0.76,0.85]        64%
  VORP                0.789 [0.71,0.83]        58%
  OBPM                0.763 [0.71,0.81]        62%
  BPM                 0.750 [0.67,0.80]        59%
  Win Shares          0.724 [0.64,0.79]        54%
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
Two reliability guards: the shift is shrunk toward zero by playoff
minutes (half weight at 200 min) so a short, lucky
sample can't top the list, and a game-level bootstrap re-draws each
player's games 1000 times to give a 2.5-97.5 range
([lo, hi], on the shrunk scale). A shift is 'clear' when that range
excludes zero. Risers and fallers below are ranked by the shrunk shift.
Note: BPM here is our recompute, validated against Basketball-Reference
(see the BPM-validation section); the playoff BPM is anchored to each
team's playoff point margin.
Shifts whose range clears zero (not just game noise): 16 of 103.

Biggest playoff RISERS (raised their level above their regular-season form):
   1. OG Anunoby                 NYK  shift = +1.56 [+0.66, +2.43]  (585 po min; raw z +2.09; PER +8.0)
   2. Cason Wallace              OKC  shift = +1.14 [+0.49, +1.75]  (374 po min; raw z +1.75; PER +5.8)
   3. Jayson Tatum               BOS  shift = +1.12 [+0.27, +1.96]  (218 po min; raw z +2.15; PER +8.6)
   4. Karl-Anthony Towns         NYK  shift = +1.03 [+0.08, +2.02]  (577 po min; raw z +1.38; PER +2.5)
   5. Rui Hachimura              LAL  shift = +1.01 [+0.50, +1.52]  (386 po min; raw z +1.53; PER +5.5)
   6. Mike Conley                MIN  shift = +0.89 [+0.25, +1.52]  (167 po min; raw z +1.95; PER +6.2)
   7. Tari Eason                 HOU  shift = +0.87 [-0.13, +2.26]  (195 po min; raw z +1.77; PER +6.8)
   8. Alex Caruso                OKC  shift = +0.85 [-0.15, +1.84]  (352 po min; raw z +1.33; PER +6.5)
   9. Marcus Smart               LAL  shift = +0.81 [-0.36, +2.02]  (344 po min; raw z +1.28; PER +4.7)
  10. Collin Murray-Boyles       TOR  shift = +0.78 [+0.17, +1.45]  (190 po min; raw z +1.60; PER +7.3)

Biggest playoff FALLERS (dropped below their regular-season form):
   1. Jalen Duren                DET  shift = -1.60 [-2.35, -0.79]  (422 po min; raw z -2.35; PER -10.4)
   2. Nikola Jokić               DEN  shift = -1.34 [-2.19, -0.53]  (237 po min; raw z -2.46; PER -7.0)
   3. Nickeil Alexander-Walker   ATL  shift = -1.07 [-1.57, -0.52]  (212 po min; raw z -2.07; PER -7.4)
   4. Jalen Suggs                ORL  shift = -1.02 [-1.90, -0.17]  (248 po min; raw z -1.84; PER -6.5)
   5. Julius Randle              MIN  shift = -0.99 [-1.66, -0.18]  (399 po min; raw z -1.49; PER -6.1)
   6. Jamal Murray               DEN  shift = -0.85 [-1.58, -0.19]  (238 po min; raw z -1.57; PER -5.1)
   7. Keldon Johnson             SAS  shift = -0.83 [-1.58, -0.13]  (410 po min; raw z -1.24; PER -5.0)
   8. James Harden               CLE  shift = -0.83 [-1.71, +0.07]  (671 po min; raw z -1.08; PER -3.9)
   9. Shai Gilgeous-Alexander    OKC  shift = -0.82 [-1.72, +0.15]  (544 po min; raw z -1.12; PER -4.6)
  10. Donovan Mitchell           CLE  shift = -0.77 [-1.63, +0.06]  (652 po min; raw z -1.00; PER -3.1)

Regular-season consensus #1 Nikola Jokić: playoff shift = -1.34 [-2.19, -0.53] (faller rank 2 of 103)

─── SEASON-OVER-SEASON CHANGE (PREVIOUS → CURRENT) ──────────────
Players qualified in both 2024-25 and 2025-26: 290
Consensus rank agreement 2024-25 → 2025-26: 0.75
Mean box-score agreement: 2024-25 0.71, 2025-26 0.75

  2025-26 consensus top 5:
   1. Nikola Jokić
   2. Shai Gilgeous-Alexander
   3. Victor Wembanyama
   4. Giannis Antetokounmpo
   5. Luka Dončić

  2024-25 consensus top 5:
   1. Nikola Jokić
   2. Shai Gilgeous-Alexander
   3. Giannis Antetokounmpo
   4. Luka Dončić
   5. Ivica Zubac

  Biggest consensus risers 2024-25 → 2025-26:
   1. Stephon Castle  +1.41
   2. Micah Potter  +1.37
   3. Kawhi Leonard  +1.33
   4. Victor Wembanyama  +1.28
   5. Neemias Queta  +1.20

  Biggest consensus fallers 2024-25 → 2025-26:
   1. Ivica Zubac  -1.58
   2. Domantas Sabonis  -1.48
   3. Jaren Jackson Jr.  -1.28
   4. Anthony Davis  -1.26
   5. De'Andre Hunter  -1.22

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
Biggest playoff riser (top composite shift): OG Anunoby (shift +1.56 [+0.66, +2.43]).
  Brunson impact ranks: OBPM 12, BPM 29, RAPM 221, RAPM+prior 68 (scoring outruns net on-court impact)
Saved → docs/player_rating_overview_facts_reference.md

```
