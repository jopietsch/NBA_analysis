# Player Rating Overview: Analysis Results

Season: 2024–25

```

─── DATA COVERAGE ───────────────────────────────────────────────
Season: 2024–25
Total players in unified table: 569
Qualified players (>= 500 min): 375
Rating systems present: 8
  Game Score: 375 players with data
  PER: 375 players with data
  Win Shares: 375 players with data
  WS/48: 375 players with data
  BPM: 375 players with data
  OBPM: 375 players with data
  DBPM: 375 players with data
  VORP: 375 players with data

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

Power-law systems (R^2 >= 0.95): Game Score, PER, Win Shares, DBPM, VORP
Bend instead of a straight line: WS/48, BPM, OBPM

─── RANK AGREEMENT (SPEARMAN CORRELATIONS) ──────────────────────
  Game Score vs PER: r=0.831
  Game Score vs Win Shares: r=0.699
  Game Score vs WS/48: r=0.308
  Game Score vs BPM: r=0.469
  Game Score vs OBPM: r=0.869
  Game Score vs DBPM: r=-0.448
  Game Score vs VORP: r=0.505
  PER vs Win Shares: r=0.759
  PER vs WS/48: r=0.611
  PER vs BPM: r=0.489
  PER vs OBPM: r=0.722
  PER vs DBPM: r=-0.271
  PER vs VORP: r=0.526
  Win Shares vs WS/48: r=0.695
  Win Shares vs BPM: r=0.640
  Win Shares vs OBPM: r=0.761
  Win Shares vs DBPM: r=-0.094
  Win Shares vs VORP: r=0.653
  WS/48 vs BPM: r=0.371
  WS/48 vs OBPM: r=0.200
  WS/48 vs DBPM: r=0.183
  WS/48 vs VORP: r=0.394
  BPM vs OBPM: r=0.560
  BPM vs DBPM: r=0.347
  BPM vs VORP: r=0.972
  OBPM vs DBPM: r=-0.464
  OBPM vs VORP: r=0.572
  DBPM vs VORP: r=0.308

─── WHAT EACH SYSTEM UNIQUELY CAPTURES ──────────────────────────
  BPM: unique R² = 1.000
  OBPM: unique R² = 1.000
  DBPM: unique R² = 1.000
  PER: unique R² = 0.892
  Game Score: unique R² = 0.888
  VORP: unique R² = 0.871
  Win Shares: unique R² = 0.864
  WS/48: unique R² = 0.837

─── CONSENSUS RATING — TOP 20 ───────────────────────────────────
   1. Nikola Jokić                    Consensus z = 3.13
   2. Shai Gilgeous-Alexander         Consensus z = 2.72
   3. Giannis Antetokounmpo           Consensus z = 2.29
   4. James Harden                    Consensus z = 1.84
   5. Trae Young                      Consensus z = 1.70
   6. Tyrese Haliburton               Consensus z = 1.67
   7. LeBron James                    Consensus z = 1.57
   8. Dyson Daniels                   Consensus z = 1.57
   9. Domantas Sabonis                Consensus z = 1.54
  10. Anthony Edwards                 Consensus z = 1.51
  11. Karl-Anthony Towns              Consensus z = 1.50
  12. Alperen Sengun                  Consensus z = 1.49
  13. Cade Cunningham                 Consensus z = 1.49
  14. Ivica Zubac                     Consensus z = 1.47
  15. Devin Booker                    Consensus z = 1.45
  16. Jalen Duren                     Consensus z = 1.43
  17. Jayson Tatum                    Consensus z = 1.42
  18. Walker Kessler                  Consensus z = 1.39
  19. Jarrett Allen                   Consensus z = 1.34
  20. Josh Hart                       Consensus z = 1.32

─── WINS-PREDICTIVE RATING — TOP 20 ─────────────────────────────
   1. Nikola Jokić                    Wins-predictive z = 3.90
   2. Shai Gilgeous-Alexander         Wins-predictive z = 3.87
   3. Giannis Antetokounmpo           Wins-predictive z = 3.30
   4. James Harden                    Wins-predictive z = 2.15
   5. Dyson Daniels                   Wins-predictive z = 2.05
   6. Anthony Edwards                 Wins-predictive z = 1.98
   7. Karl-Anthony Towns              Wins-predictive z = 1.97
   8. LeBron James                    Wins-predictive z = 1.96
   9. Daniel Gafford                  Wins-predictive z = 1.93
  10. Anthony Davis                   Wins-predictive z = 1.92
  11. Goga Bitadze                    Wins-predictive z = 1.89
  12. Tyrese Haliburton               Wins-predictive z = 1.88
  13. Jayson Tatum                    Wins-predictive z = 1.88
  14. Jalen Duren                     Wins-predictive z = 1.87
  15. Jarrett Allen                   Wins-predictive z = 1.86
  16. Cade Cunningham                 Wins-predictive z = 1.83
  17. Victor Wembanyama               Wins-predictive z = 1.79
  18. Luke Kornet                     Wins-predictive z = 1.78
  19. Walker Kessler                  Wins-predictive z = 1.78
  20. Alperen Sengun                  Wins-predictive z = 1.74

─── COMPARISON: CONSENSUS vs. WINS-PREDICTIVE ───────────────────
  Spearman correlation between consensus and wins-predictive: 0.978 (p=0.000)
  Players rated much higher by wins-predictive than consensus:
    Shai Gilgeous-Alexander         diff = +1.14
    Giannis Antetokounmpo           diff = +1.00
    Daniel Gafford                  diff = +0.92
    Victor Wembanyama               diff = +0.82
    Alex Caruso                     diff = +0.80
  Players rated much lower by wins-predictive than consensus:
    Vasilije Micic                  diff = -0.99
    AJ Johnson                      diff = -0.97
    Cody Williams                   diff = -0.90
    Jett Howard                     diff = -0.75
    Nick Smith Jr.                  diff = -0.69

─── UBER RATING CONCENTRATION (GINI vs CENTER-ROBUST STEEPNESS) ─
Gini clips negatives to zero, so it inflates 0-centered metrics (the uber
ratings and the BPM family). The power-law exponent alpha does not depend on
where zero sits, so it is the fair cross-system concentration read.

Consensus: Gini=0.763 (inflated), top-5% share=30.9%, alpha=0.31

Wins-Predictive: Gini=0.743 (inflated), top-5% share=28.1%, alpha=0.28

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
  +1.92  Joel Embiid
  +1.82  Cam Thomas
  +1.78  Brandon Ingram
Game Score discounts (vs. consensus):
  -2.06  Dwight Powell
  -1.68  John Konchar
  -1.41  Luke Kornet

PER loves (vs. consensus):
  +1.85  Zion Williamson
  +1.55  Giannis Antetokounmpo
  +1.43  Kristaps Porziņģis
PER discounts (vs. consensus):
  -1.78  Cam Reddish
  -1.40  John Konchar
  -1.37  Delon Wright

Win Shares loves (vs. consensus):
  +2.51  Domantas Sabonis
  +1.98  Ivica Zubac
  +1.96  Nikola Jokić
Win Shares discounts (vs. consensus):
  -1.32  John Konchar
  -1.24  Dwight Powell
  -1.22  Cam Reddish

WS/48 loves (vs. consensus):
  +3.13  Steven Adams
  +2.49  Richaun Holmes
  +2.45  Day'Ron Sharpe
WS/48 discounts (vs. consensus):
  -2.04  Anthony Edwards
  -1.67  Dyson Daniels
  -1.57  Jaren Jackson Jr.

BPM loves (vs. consensus):
  +2.29  Cam Reddish
  +2.26  John Konchar
  +2.10  Dwight Powell
BPM discounts (vs. consensus):
  -1.48  Joel Embiid
  -1.35  Malcolm Brogdon
  -1.22  Cam Thomas

OBPM loves (vs. consensus):
  +1.73  Anthony Edwards
  +1.73  Jalen Green
  +1.47  Devin Booker
OBPM discounts (vs. consensus):
  -1.78  John Konchar
  -1.51  Cam Reddish
  -1.42  Alex Caruso

DBPM loves (vs. consensus):
  +4.20  Cam Reddish
  +3.95  John Konchar
  +2.86  Zeke Nnaji
DBPM discounts (vs. consensus):
  -3.66  Nikola Jokić
  -3.37  Giannis Antetokounmpo
  -3.28  Shai Gilgeous-Alexander

VORP loves (vs. consensus):
  +2.81  Dyson Daniels
  +2.34  Anthony Edwards
  +2.11  James Harden
VORP discounts (vs. consensus):
  -1.18  Zion Williamson
  -1.11  Mark Williams
  -1.00  Aaron Gordon

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
Saved → docs/player_rating_overview_facts_reference.md

```
