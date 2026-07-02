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
  1. Chet Holmgren: RAPM +10.16 per 100
  2. Josh Green: RAPM +9.30 per 100
  3. Victor Wembanyama: RAPM +9.25 per 100
  4. Derrick White: RAPM +9.08 per 100
  5. Shai Gilgeous-Alexander: RAPM +8.66 per 100
  Mean rank agreement with box-score systems: 0.34
  RAPM #1 (Chet Holmgren) consensus rank: 19

─── RAPM_MY — PRIOR-INFORMED, MULTI-YEAR ────────────────────────
  1. Shai Gilgeous-Alexander: RAPM_MY +10.49 per 100
  2. Giannis Antetokounmpo: RAPM_MY +10.07 per 100
  3. Nikola Jokić: RAPM_MY +9.82 per 100
  4. Victor Wembanyama: RAPM_MY +9.11 per 100
  5. Luka Dončić: RAPM_MY +7.88 per 100
  Mean rank agreement with box-score systems: 0.77
  Rank agreement with the consensus: 0.91
  Bare RAPM rank agreement with the consensus: 0.43

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

RAPM distribution shape, pooled over 29 seasons (n=9820 player-seasons):
  Skew: +0.08  Excess kurtosis: +0.10  Below zero: 47%

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
  Game Score vs Win Shares: r=0.671
  Game Score vs WS/48: r=0.385
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
  PER vs Win Shares: r=0.764
  PER vs WS/48: r=0.659
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
  Win Shares vs WS/48: r=0.781
  Win Shares vs BPM: r=0.716
  Win Shares vs OBPM: r=0.614
  Win Shares vs DBPM: r=0.414
  Win Shares vs VORP: r=0.786
  Win Shares vs RAPM: r=0.399
  Win Shares vs O-RAPM: r=0.358
  Win Shares vs D-RAPM: r=0.163
  Win Shares vs RAPM+prior: r=0.706
  Win Shares vs O-RAPM+prior: r=0.601
  Win Shares vs D-RAPM+prior: r=0.344
  WS/48 vs BPM: r=0.667
  WS/48 vs OBPM: r=0.524
  WS/48 vs DBPM: r=0.485
  WS/48 vs VORP: r=0.617
  WS/48 vs RAPM: r=0.325
  WS/48 vs O-RAPM: r=0.248
  WS/48 vs D-RAPM: r=0.178
  WS/48 vs RAPM+prior: r=0.660
  WS/48 vs O-RAPM+prior: r=0.505
  WS/48 vs D-RAPM+prior: r=0.428
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
  PER: overlap R² = 0.946
  OBPM: overlap R² = 0.946
  RAPM+prior: overlap R² = 0.939
  BPM: overlap R² = 0.935
  O-RAPM+prior: overlap R² = 0.933
  Game Score: overlap R² = 0.890
  VORP: overlap R² = 0.889
  D-RAPM+prior: overlap R² = 0.879
  DBPM: overlap R² = 0.766
  Win Shares: overlap R² = 0.712
  D-RAPM: overlap R² = 0.707
  RAPM: overlap R² = 0.684
  WS/48: overlap R² = 0.665
  O-RAPM: overlap R² = 0.602

─── CONSENSUS RATING — TOP 20 ───────────────────────────────────
   1. Nikola Jokić                    Consensus z = 3.95
   2. Shai Gilgeous-Alexander         Consensus z = 3.35
   3. Victor Wembanyama               Consensus z = 2.81
   4. Giannis Antetokounmpo           Consensus z = 2.70
   5. Luka Dončić                     Consensus z = 2.58
   6. Kawhi Leonard                   Consensus z = 2.32
   7. Jalen Duren                     Consensus z = 2.21
   8. Cade Cunningham                 Consensus z = 1.82
   9. Paul Reed                       Consensus z = 1.77
  10. Alperen Sengun                  Consensus z = 1.73
  11. Donovan Mitchell                Consensus z = 1.69
  12. Donovan Clingan                 Consensus z = 1.64
  13. Karl-Anthony Towns              Consensus z = 1.63
  14. Tyrese Maxey                    Consensus z = 1.54
  15. LaMelo Ball                     Consensus z = 1.54
  16. Neemias Queta                   Consensus z = 1.54
  17. Mitchell Robinson               Consensus z = 1.49
  18. Jamal Murray                    Consensus z = 1.46
  19. Chet Holmgren                   Consensus z = 1.46
  20. Jalen Johnson                   Consensus z = 1.46

─── WINS-PREDICTIVE RATING — TOP 20 ─────────────────────────────
   1. Nikola Jokić                    Wins-predictive z = 4.54
   2. Shai Gilgeous-Alexander         Wins-predictive z = 4.20
   3. Giannis Antetokounmpo           Wins-predictive z = 3.64
   4. Victor Wembanyama               Wins-predictive z = 3.59
   5. Luka Dončić                     Wins-predictive z = 3.39
   6. Kawhi Leonard                   Wins-predictive z = 3.14
   7. Jalen Duren                     Wins-predictive z = 2.41
   8. Donovan Mitchell                Wins-predictive z = 2.27
   9. Paul Reed                       Wins-predictive z = 2.14
  10. Cade Cunningham                 Wins-predictive z = 2.10
  11. Tyrese Maxey                    Wins-predictive z = 1.98
  12. Stephen Curry                   Wins-predictive z = 1.88
  13. Jamal Murray                    Wins-predictive z = 1.88
  14. LaMelo Ball                     Wins-predictive z = 1.88
  15. Jaylen Brown                    Wins-predictive z = 1.81
  16. Chet Holmgren                   Wins-predictive z = 1.76
  17. Anthony Edwards                 Wins-predictive z = 1.76
  18. Alperen Sengun                  Wins-predictive z = 1.73
  19. Karl-Anthony Towns              Wins-predictive z = 1.72
  20. Joel Embiid                     Wins-predictive z = 1.72

─── COMPARISON: CONSENSUS vs. WINS-PREDICTIVE ───────────────────
  Spearman correlation between consensus and wins-predictive: 0.982 (p=0.000)
  Players rated much higher by wins-predictive than consensus:
    Giannis Antetokounmpo           diff = +0.95
    Shai Gilgeous-Alexander         diff = +0.85
    Kawhi Leonard                   diff = +0.83
    Luka Dončić                     diff = +0.80
    Victor Wembanyama               diff = +0.77
  Players rated much lower by wins-predictive than consensus:
    Jericho Sims                    diff = -0.62
    Dwight Powell                   diff = -0.57
    Steven Adams                    diff = -0.52
    Draymond Green                  diff = -0.51
    Moussa Diabaté                  diff = -0.45

─── UBER RATING CONCENTRATION (GINI vs CENTER-ROBUST STEEPNESS) ─
Gini clips negatives to zero, so it inflates 0-centered metrics (the uber
ratings and the BPM family). The power-law exponent alpha does not depend on
where zero sits, so it is the fair cross-system concentration read.

Consensus: Gini=0.752 (inflated), top-5% share=31.6%, alpha=0.38

Wins-Predictive: Gini=0.753 (inflated), top-5% share=32.7%, alpha=0.42

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
  +1.47  Keyonte George
  +1.24  Zach LaVine
Game Score discounts (vs. consensus):
  -2.06  Paul Reed
  -1.59  Mitchell Robinson
  -1.55  Goga Bitadze

PER loves (vs. consensus):
  +1.08  Giannis Antetokounmpo
  +0.92  Joel Embiid
  +0.87  Lauri Markkanen
PER discounts (vs. consensus):
  -0.87  Dorian Finney-Smith
  -0.81  Cason Wallace
  -0.69  Josh Green

Win Shares loves (vs. consensus):
  +2.18  Amen Thompson
  +1.92  Rudy Gobert
  +1.89  Donovan Clingan
Win Shares discounts (vs. consensus):
  -1.86  Giannis Antetokounmpo
  -1.60  Jayson Tatum
  -1.38  Stephen Curry

WS/48 loves (vs. consensus):
  +2.75  Steven Adams
  +2.28  Mitchell Robinson
  +2.07  Jericho Sims
WS/48 discounts (vs. consensus):
  -1.80  Luka Dončić
  -1.78  Kawhi Leonard
  -1.66  Shai Gilgeous-Alexander

BPM loves (vs. consensus):
  +1.13  Giannis Antetokounmpo
  +0.92  Paul Reed
  +0.84  T.J. McConnell
BPM discounts (vs. consensus):
  -0.85  Jericho Sims
  -0.77  Dwight Powell
  -0.77  Draymond Green

OBPM loves (vs. consensus):
  +1.66  Giannis Antetokounmpo
  +1.26  Stephen Curry
  +1.24  Darius Garland
OBPM discounts (vs. consensus):
  -1.46  Ausar Thompson
  -1.42  Lonzo Ball
  -1.17  Moussa Cisse

DBPM loves (vs. consensus):
  +2.67  Alex Caruso
  +2.38  Cason Wallace
  +2.33  Dru Smith
DBPM discounts (vs. consensus):
  -2.78  Nikola Jokić
  -2.55  Giannis Antetokounmpo
  -2.23  Lauri Markkanen

VORP loves (vs. consensus):
  +1.77  Shai Gilgeous-Alexander
  +1.64  Nikola Jokić
  +1.44  Luka Dončić
VORP discounts (vs. consensus):
  -0.80  Giannis Antetokounmpo
  -0.79  Mitchell Robinson
  -0.78  Steven Adams

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
  [team-fit]     WS/48          R²=0.773  CV R²=0.743
  [team-fit]     OBPM           R²=0.784  CV R²=0.741
  [outcome-blind] PER            R²=0.771  CV R²=0.727
  [team-fit]     D-RAPM+prior   R²=0.748  CV R²=0.717
  [team-fit]     Win Shares     R²=0.734  CV R²=0.690
  [team-fit]     O-RAPM         R²=0.722  CV R²=0.673
  [team-fit]     D-RAPM         R²=0.649  CV R²=0.603
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
  [team-fit]     RAPM+prior       0.924     0.538
  [team-fit]     VORP             0.939     0.519
  [team-fit]     BPM              1.000     0.519
  [team-fit]     O-RAPM+prior     0.787     0.460
  [team-fit]     O-RAPM           0.673     0.396
  [team-fit]     Win Shares       0.690     0.371
  [team-fit]     OBPM             0.741     0.345
  [team-fit]     WS/48            0.743     0.318
  [outcome-blind] Game Score       0.471     0.318
  [team-fit]     RAPM             0.825     0.291
  [outcome-blind] PER              0.727     0.222
  [team-fit]     DBPM             0.815     0.156
  [team-fit]     D-RAPM+prior     0.717     0.067
  [team-fit]     D-RAPM           0.603    -0.096

Best forecaster of next season: RAPM+prior (CV R²=0.538). Best description of
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
  [team-fit]     RAPM+prior      0.898       0.449
  [team-fit]     VORP            0.906       0.446
  [team-fit]     BPM             0.999       0.426
  [outcome-blind] Game Score      0.387       0.332
  [team-fit]     Win Shares      0.560       0.322
  [team-fit]     OBPM            0.610       0.273
  [team-fit]     RAPM            0.784       0.224
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
   5. Domantas Sabonis

  Biggest consensus risers 2024-25 → 2025-26:
   1. Stephon Castle  +1.41
   2. Micah Potter  +1.37
   3. Kawhi Leonard  +1.33
   4. Victor Wembanyama  +1.29
   5. Neemias Queta  +1.22

  Biggest consensus fallers 2024-25 → 2025-26:
   1. Ivica Zubac  -1.59
   2. Domantas Sabonis  -1.48
   3. Jaren Jackson Jr.  -1.27
   4. Anthony Davis  -1.25
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
  Brunson impact ranks: OBPM 12, BPM 29, RAPM 204, RAPM+prior 64 (scoring outruns net on-court impact)
Saved → docs/player_rating_overview_facts_reference.md

```
