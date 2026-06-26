
════════════════════════════════════════════════════════════════════════
NBA HOME COURT ADVANTAGE — REGRESSION ANALYSIS
════════════════════════════════════════════════════════════════════════
Game-level logistic regression. Outcome: home_win (1/0) per game.
All data from cache/ — same source as the plots above.


─── THE OVERALL DECLINE — IS IT STATISTICALLY REAL? ────────────────────
   Primary: binomial GLM (events/trials per season, weights by game count).
   Cross-check: OLS with Newey–West HAC SEs (maxlags=1).
   Per-era slopes use same methods on era subsets.

   Regular season  (12 seasons, 1984–2025)
   Binomial GLM: -0.304 pp/yr  95% CI [-0.351, -0.257]  (p = <0.001  ***,  total ≈ -12.5 pp)
   OLS / HAC:    -0.305 pp/yr  95% CI [-0.370, -0.241]  (p = <0.001  ***,  R² = 0.917,  total: -12.5 pp)

   Era              N   GLM pp/yr     GLM p   OLS pp/yr     HAC p     
   ────────────  ────  ──────────  ────────  ──────────  ────────  ───
   1984–94          7      -0.022     0.938      +0.000     0.999     
   1995–01          0   (too few)
   2002–04          0   (too few)
   2005–17          0   (too few)
   2018–22          2   (too few)
   2023–26          3      -1.802     0.073      -1.800     0.158     
                       ⚠ n=3: too few seasons — treat as illustrative only

   Playoffs  (12 seasons, 1984–2025)
   Binomial GLM: -0.257 pp/yr  95% CI [-0.429, -0.085]  (p = 0.003  **,  total ≈ -10.5 pp)
   OLS / HAC:    -0.252 pp/yr  95% CI [-0.442, -0.061]  (p = <0.001  ***,  R² = 0.464,  total: -10.3 pp)

   Era              N   GLM pp/yr     GLM p   OLS pp/yr     HAC p     
   ────────────  ────  ──────────  ────────  ──────────  ────────  ───
   1984–94          7      +0.557     0.593      +0.385     0.661     
   1995–01          0   (too few)
   2002–04          0   (too few)
   2005–17          0   (too few)
   2018–22          2   (too few)
   2023–26          3      -1.191     0.754      -1.190     0.026     
                       ⚠ n=3: too few seasons — treat as illustrative only


─── STRUCTURAL BREAK TEST — WHERE DID THE DECLINE SHIFT? ───────────────
   QLR supremum Chow F: Chow test at every candidate year, outer 15% trimmed.
   Conditional p-values assume the break year is known (single-test reference).
   Andrews (1993) QLR critical values, k=2, π₀=0.15:
   10% → 7.12  |  5% → 8.85  |  1% → 12.37

   Regular season  (N = 12 seasons, candidates: 1987–2022)
   Supremum Chow F = 1.52  at year 1990  [n.s. at 10%]
   Subperiod slopes:  before 1990: +0.362 pp/yr  |  after 1990: -0.279 pp/yr

   Top candidate break years:
     Year    Chow F     Cond. p   Slope before   Slope after
   ──────  ────────  ──────────  ─────────────  ────────────
     1990      1.52       0.275         +0.362        -0.279
     1987      1.44       0.292         -1.220        -0.333
     1988      0.89       0.447         -0.244        -0.339
     1989      0.63       0.559         +0.276        -0.326
     2021      0.51       0.618         +0.000        +0.011

   Bootstrap 95% CI for break year (B=500 residual resamples): [1987, 2022]
   ► Break not significant; CI of [1987, 2022] is wide
     and unreliable — no stable break location to report.

   Playoffs  (N = 12 seasons, candidates: 1987–2022)
   Supremum Chow F = 1.72  at year 1990  [n.s. at 10%]
   Subperiod slopes:  before 1990: -0.876 pp/yr  |  after 1990: -0.501 pp/yr

   Top candidate break years:
     Year    Chow F     Cond. p   Slope before   Slope after
   ──────  ────────  ──────────  ─────────────  ────────────
     1990      1.72       0.240         -0.876        -0.501
     1989      1.08       0.386         +1.904        -0.190
     1988      0.62       0.563         +2.476        -0.254
     1987      0.37       0.703         +2.280        -0.288
     2021      0.18       0.837         +0.385        +0.011

   Bootstrap 95% CI for break year (B=500 residual resamples): [1987, 2022]
   ► Break not significant; CI of [1987, 2022] is wide
     and unreliable — no stable break location to report.


─── CUSUM TEST — PARAMETER STABILITY  (complement to structural break test above) 
   CUSUM (Brown-Durbin-Evans): cumulative recursive residuals from the linear
   trend. Exit from the 5% critical band = structural instability detected.
   QLR (§1b) finds the single strongest break; CUSUM tests global stability.
   Agreement → increased confidence; discrepancy → worth investigating.

   Regular season  (N = 12 seasons)
   Exceeds 5% critical band: no — stable within bounds
   Peak |CUSUM| = 3.390 at year 1989  (5% bound at that point = ±4.996)
   Peak is 68% of the 5% boundary.
   ► CUSUM stays inside bounds even though the structural break test found a break:
     the slope change around 1990 is gradual (+0.36 → -0.28 pp/yr),
     not a sharp level jump — CUSUM has lower power for slope-only breaks.

   Playoffs  (N = 12 seasons)
   Exceeds 5% critical band: no — stable within bounds
   Peak |CUSUM| = 2.598 at year 1989  (5% bound at that point = ±4.996)
   Peak is 52% of the 5% boundary.


─── BAYESIAN CHANGE-POINT MODEL — HOW MANY BREAKS, AND WHERE? ──────────
   Model comparison: k=0 (linear), k=1 (one break), k=2 (two breaks), k=3 (three breaks).
   BIC-based marginal likelihood. Uniform prior over k and break locations.
   Piecewise WLS (weights = game counts); minimum 3 seasons per segment.
   Regular season only.

   N = 12 seasons, 1984–2025
   Candidate break positions: min segment size = 3 seasons

   ─ Posterior model probabilities ─
   (Uniform prior over k ∈ {0,1,2,3} and over all valid break locations)

   Model                       BF vs k=0  Posterior P(k)
   ─────────────────────────  ──────────  ──────────────
   k=0  (no break)                  1.0          74.6%
   k=1  (one break)                 0.3          20.0%
   k=2  (two breaks)                0.1           5.4%
   k=3  (three breaks)              0.0           0.0%

   ─ k=1 posterior over break year ─
   MAP break year:     1990
   95% HPD interval:   1987–2022
   Posterior-weighted slopes:
     Pre-break:  -0.225 pp/yr  (±0.629 posterior SD)
     Post-break: -0.284 pp/yr  (±0.094 posterior SD)

   Top break-year probabilities (k=1):
     Year   P(τ=year | k=1)
   ──────  ────────────────
     1990            32.0%  ███████████████████
     1987            25.4%  ███████████████
     1988            14.4%  ████████
     1989            11.1%  ██████
     2021             9.6%  █████
     2022             7.4%  ████

   ─ k=2 MAP break years: 1987 and 1990 ─

   ► k=0 is the most probable model (P = 74.6%).
   ► BF(k=1 vs k=0) = 0.3: weak evidence for a structural break.
   ► BF(k=2 vs k=1) = 0.3  BF(k=3 vs k=2) = 0.0


─── IS THE DECLINE LEAGUE-WIDE? — PER-FRANCHISE HCA SLOPE DECOMPOSITION 
   Regular-season team-season HCA gap = home win% − road win% (nets out
   each team's overall strength). Each franchise gets its own year-slope
   by OLS; the pooled cluster-robust slope is the league-wide decline.
   A method-of-moments split separates the true between-team spread in
   those slopes from sampling noise (same idiom as franchise HCA and
   referee bias). Near-zero true spread → the decline is league-wide.

   Panel: 317 team-seasons; per-team slopes fit for 19 franchises (≥10 seasons)

   League-wide slope (pooled, cluster-robust):  -0.612 pp/yr  (SE 0.035, p = <0.001  ***)
   Observed SD of per-team slopes:              0.193 pp/yr
   Noise-adjusted true between-team SD:         0.057 pp/yr
   Share of observed spread that is noise:      91%

   Per-franchise raw slopes (extremes; both within noise of the league rate):
   Steepest decline:  -0.863 pp/yr  (Portland Trail Blazers)
   Shallowest/rising: -0.139 pp/yr  (Los Angeles Lakers)
   Franchises with a positive (rising) raw slope: 0/19
   After EB shrinkage every franchise collapses to ≈-0.61 pp/yr.

   ► Once sampling noise is removed, franchises barely differ: most of the
     raw spread in team slopes is noise, and the shrunken slopes collapse
     onto one shared league rate. The decline is broadly league-wide, not
     driven by a handful of franchises losing their edge.
   ► Playoffs are excluded: per-franchise playoff samples are far too small
     for a season-by-season panel; the playoff decline is league-wide (§1, §5).


─── FOUL & SHOOTING DIFFERENTIALS BY ERA  (home minus away, per game) ──
   Negative foul diff = refs call fewer fouls on the home team.
   Positive fta_diff = home team attempted more free throws.
   Trend = slope of trend line (change per season year); pp = percentage points.

   Regular season  (N = 12,842 games)

   Era              Foul diff      FTA diff      FG% (pp)     eFG% (pp) 3PA rate (pp)      3P% (pp)      FT% (pp)
   ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1984–94              -1.25         +2.05         +1.67         +1.63         -0.50         +0.95         +0.32
   1995–01                  —             —             —             —             —             —             —
   2002–04                  —             —             —             —             —             —             —
   2005–17                  —             —             —             —             —             —             —
   2018–22              -0.17         +0.45         +0.54         +0.71         +0.51         +0.45         +0.07
   2023–26              -0.20         +0.43         +0.72         +0.97         +0.37         +0.94         +0.66
   ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
   Trend/yr         +0.029***     -0.044***     -0.027***     -0.020***     +0.026***     -0.001        +0.004   

   Playoffs  (N = 922 games)

   Era              Foul diff      FTA diff      FG% (pp)     eFG% (pp) 3PA rate (pp)      3P% (pp)      FT% (pp)
   ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
   1984–94              -1.40         +1.96         +1.67         +1.57         -0.83         -0.50         +0.93
   1995–01                  —             —             —             —             —             —             —
   2002–04                  —             —             —             —             —             —             —
   2005–17                  —             —             —             —             —             —             —
   2018–22              -0.82         +1.57         +0.85         +1.05         +1.09         +0.10         +0.21
   2023–26              -0.70         +1.11         +1.03         +1.19         -0.11         +1.00         +2.68
   ──────────────────────────────────────────────────────────────────────────────────────────────────────────────
   Trend/yr         +0.018        -0.017        -0.020        -0.013        +0.032  *     +0.030        +0.022   

   No cached referee data — run the analysis first to fetch it.


─── SHOT ZONE DIFFERENTIALS BY ERA  (home minus road % of FGA) ─────────
   Positive = home team takes a higher share of FGA from that zone.
   Trend = slope of trend line (change per season year). Data from 1996–97 onward.


─── MEDIATION — BOX-SCORE CHANNELS AS SHARES OF HCA LEVEL AND TREND ────
   How much of the home edge, and of its decline, flows through the
   measured channels: shooting (eFG%), referee fouls, turnovers, and
   rebounds? Linear-probability model of home_win on the four
   home-minus-away differentials; cluster-robust SEs by season.
   Level identity:  mean win % = intercept + Σ coef × mean diff.
   Trend identity:  total pp/yr = unmediated pp/yr + Σ coef × channel trend/yr.
   Foul diff carries the free-throw-attempt channel; FT% diff is
   excluded (mean ≈ +0.4 pp, negligible). Channels are proximate —
   how HCA expresses itself in the box score — so this is an
   accounting decomposition, not deep causation.

   Regular season  (N = 12,839 games, home win % = 61.0, level above coin flip = +11.0 pp)
   Channel-model R² = 0.602 — share of game-outcome variance the four channels carry.

   Level decomposition  (coef × mean diff):
   Channel            Mean diff   pp per unit   Contribution  % of level
   ────────────────  ──────────  ────────────  ─────────────  ──────────
   eFG% diff (pp)         +1.28      +3.39 ***      +4.3 pp         39%
   Foul diff              -0.75      -1.92 ***      +1.4 pp         13%
   TOV diff               -0.49      -3.24 ***      +1.6 pp         15%
   REB diff               +1.60      +1.67 ***      +2.7 pp         24%
   ────────────────  ──────────  ────────────  ─────────────  ──────────
   Unexplained                                       +1.0 pp          9%

   Trend decomposition  (pp of home win % per year):
   Total trend (home_win ~ year): -0.305 pp/yr  (p = <0.001  ***)

   Channel           Trend in diff/yr     Contribution  % of trend
   ────────────────  ────────────────  ───────────────  ──────────
   eFG% diff (pp)         -0.0198 ***    -0.0672 pp/yr         22%
   Foul diff              +0.0289 ***    -0.0553 pp/yr         18%
   TOV diff               +0.0233 ***    -0.0750 pp/yr         25%
   REB diff               -0.0460 ***    -0.0763 pp/yr         25%
   ────────────────  ────────────────  ───────────────  ──────────
   Sum, channels                         -0.2737 pp/yr         90%
   Unmediated                            -0.0316 pp/yr         10%

   ► Regular season: channels carry 91% of the HCA level and 90% of its decline.

   Playoffs  (N = 922 games, home win % = 63.4, level above coin flip = +13.4 pp)
   Channel-model R² = 0.578 — share of game-outcome variance the four channels carry.

   Level decomposition  (coef × mean diff):
   Channel            Mean diff   pp per unit   Contribution  % of level
   ────────────────  ──────────  ────────────  ─────────────  ──────────
   eFG% diff (pp)         +1.37      +3.17 ***      +4.3 pp         32%
   Foul diff              -1.10      -1.62 ***      +1.8 pp         13%
   TOV diff               -1.23      -3.55 ***      +4.4 pp         32%
   REB diff               +1.83      +1.79 ***      +3.3 pp         24%
   ────────────────  ──────────  ────────────  ─────────────  ──────────
   Unexplained                                       -0.3 pp         -2%

   Trend decomposition  (pp of home win % per year):
   Total trend (home_win ~ year): -0.258 pp/yr  (p = <0.001  ***)

   Channel           Trend in diff/yr     Contribution  % of trend
   ────────────────  ────────────────  ───────────────  ──────────
   eFG% diff (pp)         -0.0127        -0.0401 pp/yr         16%
   Foul diff              +0.0176 *      -0.0280 pp/yr         11%
   TOV diff               +0.0035        -0.0124 pp/yr          5%
   REB diff               -0.0298        -0.0530 pp/yr         21%
   ────────────────  ────────────────  ───────────────  ──────────
   Sum, channels                         -0.1335 pp/yr         52%
   Unmediated                            -0.1241 pp/yr         48%

   ► Playoffs: channels carry 102% of the HCA level and 52% of its decline.
   ► Note: playoff differentials fold in the seed-quality gap (the
     home team is usually the better team) — see the seeding
     decomposition for that control.

   ─ Bootstrap 95% CIs on the shares (season block resample, B=500) ─
   Resamples whole seasons with replacement and recomputes the shares;
   the band is the 2.5–97.5 percentile across resamples. Wide bands
   (especially in the playoffs) mean the point share is loosely pinned.

   Regular season  (B = 500 resamples)
   Channel            % level           95% CI   % trend           95% CI
   ────────────────  ────────  ───────────────  ────────  ───────────────
   eFG% diff (pp)         39%  [  +34,  +47]%       22%  [  +13,  +32]%
   Foul diff              13%  [  +10,  +16]%       18%  [  +15,  +22]%
   TOV diff               15%  [   +9,  +18]%       25%  [  +18,  +32]%
   REB diff               24%  [  +22,  +26]%       25%  [  +21,  +30]%
   ────────────────
   Channels carry 91% of the level (95% CI [87, 96]%) and 90% of the decline (95% CI [80, 100]%).

   Playoffs  (B = 500 resamples)
   Channel            % level           95% CI   % trend           95% CI
   ────────────────  ────────  ───────────────  ────────  ───────────────
   eFG% diff (pp)         32%  [  +23,  +43]%       16%  [  -13,  +40]%
   Foul diff              13%  [   +8,  +18]%       11%  [   +2,  +21]%
   TOV diff               32%  [  +22,  +48]%        5%  [  -23,  +39]%
   REB diff               24%  [  +18,  +32]%       21%  [   -4,  +40]%
   ────────────────
   Channels carry 102% of the level (95% CI [88, 122]%) and 52% of the decline (95% CI [31, 82]%).

   ─ Are the channel trends downstream of the 3-point shift? ─
   Each differential's year-trend, before and after controlling for the
   game's 3PA rate. A trend that survives the control is an independent
   driver; one that collapses faded with the move to the perimeter.

   Regular season  (N = 12,839 games)
   Channel              Trend/yr    Trend/yr | 3PA   Absorbed
   ────────────────  ───────────  ────────────────  ─────────
   eFG% diff (pp)      -0.0198***         +0.0035         118%
   Foul diff           +0.0289***         +0.0208***        28%
   TOV diff            +0.0233***         +0.0173*         25%
   REB diff            -0.0460***         -0.0618**       -34%

   ► Survives the 3PA control: TOV diff, REB diff — not fully
     explained by the shooting revolution.

   Playoffs  (N = 922 games)
   Channel              Trend/yr    Trend/yr | 3PA   Absorbed
   ────────────────  ───────────  ────────────────  ─────────
   eFG% diff (pp)      -0.0127           -0.0375        -196%
   Foul diff           +0.0176*          +0.0262         -49%
   TOV diff            +0.0035           -0.0473        1448%
   REB diff            -0.0298           -0.0298          -0%

   ► With 3PA controlled, neither the rebounding nor the turnover
     trend stays significant — both edges faded with the move to the
     perimeter, not as independent drivers.

   ─ Coefficient stability by era (regular season only) ─
   Re-fitting the LPM within each era to check whether the channel
   coefficients are stable across 43 seasons.
   (pp per unit of each home-minus-away differential)

   Era            N games      eFG%     Fouls       TOV       REB
   ────────────  ────────  ────────  ────────  ────────  ────────
   1984–94          6,844    +3.41    -1.99    -3.18    +1.68
   1995–01              0                             ⚠ too few
   2002–04              0                             ⚠ too few
   2005–17              0                             ⚠ too few
   2018–22          2,310    +3.42    -1.82    -3.34    +1.66
   2023–26          3,685    +3.34    -1.78    -3.28    +1.62

   Pooled (all seasons):  eFG%=+3.39  Fouls=-1.92  TOV=-3.24  REB=+1.67  (pp per unit)
   ► Stable coefficients validate the pooled decomposition.
     Large era-to-era shifts would mean the 'share' percentages are
     a blend of heterogeneous effects and should be interpreted with caution.


─── REST DIFFERENTIAL — WIN % BY BUCKET AND ERA STABILITY ──────────────
   Buckets: away team more rested (rest_diff < 0), equal rest, and home
   team more rested (rest_diff > 0). Games without a prior game to
   compute rest from are excluded.

   Regular season  (N = 12,670, baseline home win % = 61.1%)

   Bucket             N games   Home win %   vs. baseline
   ────────────────  ────────  ───────────  ─────────────
   Away more rest       2,485        58.1%          -3.0 pp
   Equal rest           6,355        60.2%          -0.8 pp
   Home more rest       3,830        64.4%          +3.3 pp

   Chi-square (H0: home win % equal across buckets): χ²(2) = 28.99,  p = <0.001  ***

   Rest effect by era (bivariate logistic within each era):
   Era                 N   log-odds/day   ≈pp/day         p     
   ────────────  ───────  ─────────────  ────────  ────────  ───
   1984–94         6,754         +0.046      +1.0     0.037    *
   2018–22         2,278         +0.090      +2.2     0.022    *
   2023–26         3,638         +0.124      +3.0    <0.001  ***

   Rest × era interaction (LR test): χ²(2) = 3.79,  p = 0.150  
   ► no evidence the rest effect changed across eras.

   Playoffs  (N = 826, baseline home win % = 61.6%)

   Bucket             N games   Home win %   vs. baseline
   ────────────────  ────────  ───────────  ─────────────
   Away more rest          21        52.4%          -9.2 pp
   Equal rest             759        61.3%          -0.4 pp
   Home more rest          46        71.7%         +10.1 pp

   Chi-square (H0: home win % equal across buckets): χ²(2) = 2.79,  p = 0.248  

   Rest effect by era (bivariate logistic within each era):
   Era                 N   log-odds/day   ≈pp/day         p     
   ────────────  ───────  ─────────────  ────────  ────────  ───
   1984–94           444         +0.043      +1.0     0.672     
   2018–22           156         +0.217      +5.3     0.355     
   2023–26           226         +0.115      +2.8     0.404     

   Rest × era interaction (LR test): χ²(2) = 0.55,  p = 0.761  
   ► no evidence the rest effect changed across eras.


─── REST, ALTITUDE, AND TIME ZONE — DO THEY MATTER? ────────────────────
   Bivariate logistic regression — each factor tested independently.
   N regular season: 12,670   N playoffs: 826

   Factor                           ── Regular season ──         ──── Playoffs ────    
                                 log-odds    ≈pp         p       log-odds    ≈pp         p     
   ────────────────────────────  ────────  ─────  ────────  ───  ────────  ─────  ────────  ───
   Rest diff (per day)             +0.088   +2.1    <0.001  ***    +0.086   +2.0     0.264     
                    95% CI (pp)            [+1.3,+2.9]                           [-1.5,+5.6]
   Altitude home (DEN/UTA)         +0.500  +11.9    <0.001  ***    -0.239   -5.6     0.321     
                    95% CI (pp)            [+8.4,+15.3]                           [-16.8,+5.5]
   Time zone diff (per zone)       -0.043   -1.0     0.017    *    +0.082   +1.9     0.334     
                    95% CI (pp)            [-1.9,-0.2]                           [-2.0,+5.9]

   ► Rest matters only in the regular season (+2.1 pp/day).
   ► Altitude home advantage is real in the regular season (+11.9 pp)
     but absent in playoffs — Denver/Utah team strength is a confound.
   ► Time zones matter in the regular season (-1.0 pp/zone)
     but not the playoffs.
     Only 41 coast-to-coast playoff games exist across 12 seasons
     (1,451 regular-season) — too sparse for reliable playoff inference.

   Playoff rest controlling for team quality (N = 826 games):
   quality_diff = home RS win% − away RS win% (same season).
   Predictor                     log-odds     ≈pp         p     
   ────────────────────────────  ────────  ──────  ────────  ───
   rest_diff (per day)             +0.008    +0.2     0.926     
   quality_diff (RS win% gap)      +4.586  +108.5    <0.001  ***

─── LEAGUE-WIDE 3-POINT SHOOTING AND HOME COURT ADVANTAGE ──────────────
   Does more 3-point shooting reduce home court advantage?
   Two angles: season-level correlation and game-level logistic regression.

   Regular season  (n = 12 seasons)
   Season-level Pearson r  = -0.961  (p = <0.001  ***)
   Season-level Spearman ρ = -0.757  (p = 0.004  **)

   Era           Mean 3PA%    Home win%    n seasons
   ---------- ------------ ------------ ------------
   1984–94             5.1%         66.2%            7
   2018–22            39.6%         54.4%            2
   2023–26            40.1%         55.6%            3

   Game-level bivariate logistic  (N = 12,841 games)
   coef = -0.0126 log-odds per pp of 3PA rate
   ≈ -2.99 pp per 10 pp rise in 3PA rate  95% CI [-3.53, -2.45]
   p = <0.001  ***

   Controlling for era (within-era game-level effect):
   coef = +0.0001  (≈ +0.02 pp per 10 pp 3PA)  p = 0.986  
   (If this is small and insignificant, 3PA effect is fully explained
    by the secular trend — higher 3PA and lower HCA happen at the same
    time but 3PA does not predict outcomes within any given era.)

   Playoffs  (n = 12 seasons)
   Season-level Pearson r  = -0.711  (p = 0.009  **)
   Season-level Spearman ρ = -0.566  (p = 0.055  )

   Era           Mean 3PA%    Home win%    n seasons
   ---------- ------------ ------------ ------------
   1984–94             6.9%         67.5%            7
   2018–22            40.4%         58.1%            2
   2023–26            40.0%         58.4%            3

   Game-level bivariate logistic  (N = 922 games)
   coef = -0.0118 log-odds per pp of 3PA rate
   ≈ -2.74 pp per 10 pp rise in 3PA rate  95% CI [-3.98, -1.51]
   p = <0.001  ***

   Controlling for era (within-era game-level effect):
   coef = -0.0057  (≈ -1.33 pp per 10 pp 3PA)  p = 0.645  
   (If this is small and insignificant, 3PA effect is fully explained
    by the secular trend — higher 3PA and lower HCA happen at the same
    time but 3PA does not predict outcomes within any given era.)

   ─ Cointegration check: is the 3PA-HCA correlation genuine or spurious? ─
   ADF unit-root tests  (H0: unit root; p ≥ 0.05 → I(1) / nonstationary):
   3PA rate (regular season)           ADF = -0.553  p = 0.881  → I(1) nonstationary
   Home win %                          ADF = -0.760  p = 0.831  → I(1) nonstationary

   Engle-Granger cointegration  (H0: no long-run relationship):
   t = +0.000  p = 0.986  
   ► Both I(1) but NOT cointegrated — r = -0.961 is likely
     spurious; within-era game-level controls are the reliable evidence.

   ─ Partial correlation: detrend both series, then correlate residuals ─
   Remove the year trend from both 3PA rate and home win %;
   if the residual r collapses, the raw r = -0.90 is a trend artifact.

   Raw Pearson r (season level):        r = -0.961
   Partial r (year-detrended residuals): r = -0.354  p = 0.259     
   ► Residual r non-significant (raw: -0.961 → partial: -0.354,
     63% of raw r explained by shared trend). 3PA does not
     predict HCA within eras after removing the year trend.

   ─ Rolling 10-season Pearson r: stability of the 3PA-HCA relationship ─
   Stable r → genuine relationship; large swings or sign flips → spurious.

   10-season rolling r range: [-0.971, -0.944]  sign flips: 0
   Most negative r = -0.971 centered on season ending 2025
   ► Rolling r consistently negative — correlation appears stable;
     the 3PA-HCA link holds across sub-periods.


─── GRANGER CAUSALITY — DOES 3PA RATE LEAD HOME COURT ADVANTAGE? ───────
   Granger causality: does 3PA rate in year t-1 improve forecasts of HCA in
   year t, beyond what past HCA values predict on their own?
   H0: 3PA lags add no predictive power for HCA (F-test via VAR).
   Both series differenced when I(1) to satisfy stationarity. Max 2 lags.

   Insufficient data (need ≥ 15 seasons).


─── REBOUNDING DECOMPOSITION — WHY THE HOME EDGE FADED  (home minus away) 
   OREB/DREB diff = home minus away offensive/defensive rebounds per game.
   Share edge = home share of available offensive boards minus away share
   (percentage points) — a pace- and volume-free measure of the edge.
   Trend = slope of trend line (change per season year).

   Regular season  (N = 12,842 games)

   Era                OREB diff       DREB diff        REB diff Share edge (pp)
   ────────────────────────────────────────────────────────────────────────────
   1984–94                +0.60           +1.77           +2.37           +2.26
   1995–01                    —               —               —               —
   2002–04                    —               —               —               —
   2005–17                    —               —               —               —
   2018–22                +0.10           +0.62           +0.72           +0.49
   2023–26                +0.04           +0.67           +0.71           +0.39
   ────────────────────────────────────────────────────────────────────────────
   Trend/yr           -0.016***       -0.030***       -0.046***       -0.051***

   Playoffs  (N = 922 games)

   Era                OREB diff       DREB diff        REB diff Share edge (pp)
   ────────────────────────────────────────────────────────────────────────────
   1984–94                +0.65           +1.68           +2.32           +2.27
   1995–01                    —               —               —               —
   2002–04                    —               —               —               —
   2005–17                    —               —               —               —
   2018–22                +0.24           +0.53           +0.78           +0.60
   2023–26                +0.16           +1.41           +1.57           +1.18
   ────────────────────────────────────────────────────────────────────────────
   Trend/yr           -0.012          -0.018          -0.030          -0.036   

   Does the home edge track the league's retreat from the offensive glass?
   Season-level Pearson r (share edge vs league OREB rate) = +0.929  (p = <0.001  ***,  N = 12 seasons)
   League OREB rate: 32.9% → 25.1%   |   Home share edge: +2.74pp → +0.05pp
   ► The home rebounding edge fades in lockstep with the league-wide
     decline in offensive rebounding — the effort-driven offensive boards
     where a home edge could form have largely disappeared.

   ─ Cointegration check: is the OREB-HCA correlation genuine or spurious? ─
   ADF unit-root tests  (H0: unit root; p ≥ 0.05 → I(1) / nonstationary):
   League OREB rate                    ADF = -1.006  p = 0.751  → I(1) nonstationary
   Home rebound share edge             ADF = -0.316  p = 0.923  → I(1) nonstationary

   Engle-Granger cointegration  (H0: no long-run relationship):
   t = -0.000  p = 0.986  
   ► Both I(1) but NOT cointegrated — r = +0.929 is likely
     spurious; within-era game-level controls are the reliable evidence.

   No cached player-tracking data — run the analysis first to fetch it.


─── OUT-OF-SAMPLE FORECAST — DO THE CHANNELS PREDICT THE LATER DECLINE? 
   Freeze the four-channel win model (eFG%, fouls, turnovers, rebounds)
   on the training seasons, then predict each later season's home win %
   from that season's box-score edges. A frozen early mapping that tracks
   the held-out decline means the mechanism is stable, not fitted to
   hindsight. Baselines: extrapolating the training trend line, and a flat
   training-mean forecast. Lower RMSE on the held-out seasons is better.

   Regular season  (train 1984–1990, test 2021–2025)

    Season    Actual   Channel pred   Trend pred
   ───────  ────────  ─────────────  ───────────
      2021     54.4%          54.3%        65.1%
      2022     54.4%          56.0%        65.1%
      2023     58.0%          58.0%        65.1%
      2024     54.3%          56.4%        65.0%
      2025     54.4%          55.3%        65.0%

   Held-out RMSE:  channel = 1.24 pp   trend = 10.06 pp   flat mean = 11.19 pp
   ► The frozen early channel model reconstructs the 2021–2025 decline
     it never saw and beats a naive extension of the early trend line — the box-score mechanism is stable across the
     split, not an artifact of fitting on the full history.

   Playoffs  (train 1984–1990, test 2021–2025)

    Season    Actual   Channel pred   Trend pred
   ───────  ────────  ─────────────  ───────────
      2021     56.5%          60.2%        86.7%
      2022     59.8%          63.2%        87.2%
      2023     59.5%          63.2%        87.8%
      2024     58.5%          63.1%        88.3%
      2025     57.1%          64.1%        88.9%

   Held-out RMSE:  channel = 4.67 pp   trend = 29.54 pp   flat mean = 9.60 pp
   ► The frozen early channel model reconstructs the 2021–2025 decline
     it never saw and beats a naive extension of the early trend line — the box-score mechanism is stable across the
     split, not an artifact of fitting on the full history.


─── RULE-CHANGE ERAS — DO THE ERA BREAKS MATTER BEYOND THE YEAR TREND? ─
   Home win % by rule-change era; pairwise tests between consecutive eras.
   Trend-controlled model: home_win ~ year + C(era).
   LR test: do era dummies jointly add explanatory power beyond the year trend?
   (If not, the decline is a smooth drift; if yes, specific rules caused jumps.)

   Regular season  (N = 12,842 games)

   Era            N games   Home win %
   ────────────  ────────  ───────────
   1984–94          6,847        66.2%
   2018–22          2,310        54.4%
   2023–26          3,685        55.6%

   Consecutive eras — two-proportion z-tests:
    1984–94 → 2018–22   -11.8 pp   (z = +10.18, p = <0.001  ***)
    2018–22 → 2023–26    +1.2 pp   (z = -0.93, p = 0.351  )

   Trend-controlled logistic: home_win ~ year + C(era)
   (reference era = 1984–94)

   Predictor                     log-odds     ≈pp         p     
   ────────────────────────────  ────────  ──────  ────────  ───
   era: 2018–22                    -0.251    -6.0     0.543     
   era: 2023–26                    -0.184    -4.4     0.677     
   year trend (per yr)             -0.007    -0.2     0.550     

   LR test — era dummies jointly vs. year-only model: χ²(2) = 2.57,  p = 0.276  

   ► Era dummies do not add significant explanatory power beyond
     the year trend (p = 0.276) — the decline is well-described
     as a continuous drift without discrete era-level jumps.

   Playoffs  (N = 922 games)

   Era            N games   Home win %
   ────────────  ────────  ───────────
   1984–94            500        67.8%
   2018–22            172        58.1%
   2023–26            250        58.4%

   Consecutive eras — two-proportion z-tests:
    1984–94 → 2018–22    -9.7 pp   (z = +2.30, p = 0.022  *)
    2018–22 → 2023–26    +0.3 pp   (z = -0.05, p = 0.957  )

   Trend-controlled logistic: home_win ~ year + C(era)
   (reference era = 1984–94)

   Predictor                     log-odds     ≈pp         p     
   ────────────────────────────  ────────  ──────  ────────  ───
   era: 2018–22                    -1.163   -27.0     0.458     
   era: 2023–26                    -1.206   -28.0     0.472     
   year trend (per yr)             +0.022    +0.5     0.632     

   LR test — era dummies jointly vs. year-only model: χ²(2) = 0.57,  p = 0.752  

   ► Era dummies do not add significant explanatory power beyond
     the year trend (p = 0.752) — the decline is well-described
     as a continuous drift without discrete era-level jumps.


─── ITS (INTERRUPTED TIME SERIES) — 1994-95 BOUNDARY ───────────────────
   Model: home_pct ~ year + post95 + time_since_break  (season-level WLS)
   post95      = 1 for seasons from 1994-95 onward (immediate level shift)
   time_since  = (year − 1994) × post95           (slope change post-break)
   Weights: game counts per season.

   Regular season  (N = 12 seasons)  R² = 0.927
   Parameter                   Coef        p   Sig
   ──────────────────────  ────────  ───────  ────
   Pre-break trend/yr        -0.022    0.954      
   Level shift (1994-95)    -10.690    0.544      
   Slope change/yr           +0.015    0.984      

   Implied slopes: pre-break = -0.022 pp/yr, post-break = -0.007 pp/yr
   ► Neither level nor slope significant at 1994-95.
     Overall HCA trend drove this context — 1994-95 not a sharp break.

   Playoffs  (N = 12 seasons)  R² = 0.549
   Parameter                   Coef        p   Sig
   ──────────────────────  ────────  ───────  ────
   Pre-break trend/yr        +0.555    0.608      
   Level shift (1994-95)    -13.688    0.780      
   Slope change/yr           -0.545    0.783      

   Implied slopes: pre-break = +0.555 pp/yr, post-break = +0.010 pp/yr
   ► Neither level nor slope significant at 1994-95.
     Overall HCA trend drove this context — 1994-95 not a sharp break.


─── PLACEBO TESTS — IS 1994-95 UNIQUELY SIGNIFICANT? ───────────────────
   For each year t in 1987–2010: OLS on season home win%,
   model pct ~ year + step_t  (step_t = 1 if season >= t).
   A significant NEGATIVE step = discrete drop at that boundary.
   If 1994-95 uniquely stands out, it strengthens the causal claim.

   Regular season  (N = 12 seasons)

     Year   Step coef (pp)     p-value   Sig
   ──────  ───────────────  ──────────  ────
     1987           +2.05       0.182     
     1988           +1.87       0.230     
     1989           +0.73       0.676     
     1990           -1.58       0.474     
     1991          -10.42       0.350     
     1992          -10.42       0.350     
     1993          -10.42       0.350     
     1994          -10.42       0.350     
     1995          -10.42       0.350      ← 1994-95
     1996          -10.42       0.350     
     1997          -10.42       0.350     
     1998          -10.42       0.350     
     1999          -10.42       0.350     
     2000          -10.42       0.350     
     2001          -10.42       0.350     
     2002          -10.42       0.350     
     2003          -10.42       0.350     
     2004          -10.42       0.350     
     2005          -10.42       0.350     
     2006          -10.42       0.350     
     2007          -10.42       0.350     
     2008          -10.42       0.350     
     2009          -10.42       0.350     
     2010          -10.42       0.350     

   Playoffs  (N = 12 seasons)

     Year   Step coef (pp)     p-value   Sig
   ──────  ───────────────  ──────────  ────
     1987           +3.26       0.456     
     1988           +0.66       0.884     
     1989           -2.76       0.586     
     1990          +10.05       0.093     
     1991          -23.71       0.448     
     1992          -23.71       0.448     
     1993          -23.71       0.448     
     1994          -23.71       0.448     
     1995          -23.71       0.448      ← 1994-95
     1996          -23.71       0.448     
     1997          -23.71       0.448     
     1998          -23.71       0.448     
     1999          -23.71       0.448     
     2000          -23.71       0.448     
     2001          -23.71       0.448     
     2002          -23.71       0.448     
     2003          -23.71       0.448     
     2004          -23.71       0.448     
     2005          -23.71       0.448     
     2006          -23.71       0.448     
     2007          -23.71       0.448     
     2008          -23.71       0.448     
     2009          -23.71       0.448     
     2010          -23.71       0.448     


─── CHANNEL EVENT STUDY — WHICH CHANGED FIRST AT 1994-95? ──────────────
   ITS model per channel: diff ~ year + post95 + (year-1994)×post95
   β_level = immediate shift at 1995; β_slope = change in per-year rate.
   If hand-checking is the mechanism, FOUL diff should show the
   strongest IMMEDIATE response; others should be smaller or delayed.

   Regular season  (N = 12 seasons)

   Channel              Pre slope/yr   Level shift   Slope chg/yr     Lev p     Slp p
   ──────────────────  ─────────────  ────────────  ─────────────  ────────  ────────
   Foul diff                  -0.051        +0.372         +0.086     0.825     0.218  /
   eFG% diff (pp)             +0.157        -3.833         -0.088     0.182     0.422  /
   TOV diff                   +0.028        +2.558         -0.094     0.339     0.375  /
   REB diff                   -0.026        +0.601         -0.046     0.853     0.723  /

   Playoffs  (N = 12 seasons)

   Channel              Pre slope/yr   Level shift   Slope chg/yr     Lev p     Slp p
   ──────────────────  ─────────────  ────────────  ─────────────  ────────  ────────
   Foul diff                  -0.064        -1.834         +0.165     0.718     0.422  /
   eFG% diff (pp)             -0.137        +0.158         +0.150     0.983     0.616  /
   TOV diff                   -0.025        +5.818         -0.164     0.355     0.505  /
   REB diff                   -0.103        -4.275         +0.241     0.713     0.604  /

   Note: foul_diff = PF_home − PF_away. Negative values mean away teams
   get MORE fouls called (home court foul advantage). A positive level shift
   means the home foul advantage SHRANK immediately (foul_diff moved toward 0).
   The expected signature of the hand-checking rule change:
   • Foul diff: significant POSITIVE level shift (home foul edge shrinks IMMEDIATELY)
   • Other channels: no significant immediate shift (teams adapt over seasons)


─── TRAVEL DISTANCE — HOME WIN % BY AWAY TEAM FLIGHT MILES ─────────────
   Distance = haversine miles from away team's home arena to game arena.
   Does longer travel reduce the visiting team's winning odds?

   Regular season  (N = 12,842, baseline home win % = 61.0%)

         Bucket         N   Home win %   vs. baseline
   ────────────  ────────  ───────────  ─────────────
          0–500     3,118        60.9%          -0.1 pp
       500–1000     4,204        62.6%          +1.5 pp
      1000–1500     2,439        60.0%          -1.0 pp
          1500+     3,081        59.8%          -1.2 pp

   Bivariate logistic: coef = -0.00006 log-odds/mi  (≈-0.15 pp per 100 mi,  95% CI [-0.25, -0.05]),  p = 0.002  **

   Playoffs  (N = 922, baseline home win % = 63.4%)

         Bucket         N   Home win %   vs. baseline
   ────────────  ────────  ───────────  ─────────────
          0–500       267        61.8%          -1.7 pp
       500–1000       384        65.1%          +1.7 pp
      1000–1500       145        60.0%          -3.4 pp
          1500+       126        65.9%          +2.4 pp

   Bivariate logistic: coef = +0.00002 log-odds/mi  (≈+0.04 pp per 100 mi,  95% CI [-0.38, +0.47]),  p = 0.848  


─── BACK-TO-BACKS — DID FEWER TIRED VISITORS DRIVE THE DECLINE? ────────
   A back-to-back (B2B) is a game on zero days' rest. The 'load
   management' story: visitor B2Bs have grown rarer, so home teams
   face fewer tired opponents. Regular season only (B2Bs are rare
   in the playoffs). Games without a known prior game are excluded.

   Visitor and home B2B frequency by era:
   Era                 N  Visitor B2B   Home B2B   Home win %
   ────────────  ───────  ───────────  ─────────  ───────────
   1984–94         6,754        35.2%      20.2%        66.2%
   2018–22         2,278        21.3%      17.3%        54.3%
   2023–26         3,638        18.9%      16.1%        55.7%

   Home win % by rest situation (all seasons pooled):
   Situation          N games   Home win %
   ────────────────  ────────  ───────────
   Neither on B2B       7,851        59.9%
   Visitor B2B only     2,476        66.8%
   Home B2B only        1,271        54.0%
   Both on B2B          1,072        64.6%

   Shift-share decomposition of the home win % change, 1984–94 → 2023–26:
   Home win %: 66.2% → 55.7%   (total change -10.51 pp)
   Frequency component (schedule: fewer B2Bs)        -0.66 pp  (   6% of change)
   Win-rate component (per-situation edge fading)    -9.59 pp
   Interaction                                       -0.25 pp

   ► Visitor B2Bs have grown much rarer, which does nudge home court
     downward — but the win-rate gap between rested and tired matchups is
     small, so the schedule shift explains only ~6% of the decline.
     The other ~94% is the home edge within each rest situation
     fading — not a scheduling story.


─── PACE AND HOME COURT ADVANTAGE ──────────────────────────────────────
   Does faster-paced play (more possessions per game) reduce home court advantage?
   Season-level correlation plus game-level logistic regression.

   Regular season  (n = 12 seasons)
   Season-level Pearson r  = +0.797  (p = 0.002  **)
   Season-level Spearman ρ = +0.720  (p = 0.008  **)

   Era           Mean pace    Home win%    n seasons
   ---------- ------------ ------------ ------------
   1984–94           104.0          66.2%            7
   2018–22           100.9          54.4%            2
   2023–26           101.2          55.6%            3

   Game-level bivariate logistic  (N = 12,839 games)
   coef = +0.0221 log-odds per possession
   ≈ +5.26 pp per 10 extra possessions  95% CI [+3.40, +7.11]
   p = <0.001  ***

   Controlling for era (within-era game-level effect):
   coef = +0.0152  (≈ +3.60 pp per 10 possessions)  p = <0.001  ***

   Expected pace (LOO)  (N = 12,601 games)
   Bivariate: coef = +0.0588  (≈ +14.00 pp per 10 poss)  p = <0.001  ***
   Within-era: coef = +0.0092  (≈ +2.20 pp per 10 poss)  p = 0.219  

   Playoffs  (n = 12 seasons)
   Season-level Pearson r  = +0.402  (p = 0.195  )
   Season-level Spearman ρ = +0.427  (p = 0.167  )

   Era           Mean pace    Home win%    n seasons
   ---------- ------------ ------------ ------------
   1984–94           100.8          67.5%            7
   2018–22            97.8          58.1%            2
   2023–26            97.1          58.4%            3

   Game-level bivariate logistic  (N = 922 games)
   coef = +0.0168 log-odds per possession
   ≈ +3.89 pp per 10 extra possessions  95% CI [+0.83, +6.95]
   p = 0.013  *

   Controlling for era (within-era game-level effect):
   coef = +0.0096  (≈ +2.23 pp per 10 possessions)  p = 0.135  

   Expected pace (LOO)  (N = 922 games)
   Bivariate: coef = +0.0123  (≈ +2.86 pp per 10 poss)  p = 0.261  
   Within-era: coef = -0.0074  (≈ -1.71 pp per 10 poss)  p = 0.609  


─── COMPETITIVE BALANCE AND HOME COURT ADVANTAGE ───────────────────────
   Hypothesis: more parity (lower team win% std dev) → lower home court advantage.
   Parity = std dev of all-team win percentages for the season.

   N = 12 seasons
   Pearson r  = +0.005  (p = 0.987  )
   Spearman ρ = -0.081  (p = 0.803  )

   Trend line: home_win_pct ~ parity_std_dev
   Slope: +1.839 pp per unit std dev  (p = 0.987  )
   R² = 0.0000

   Era-bucketed averages (disparity ↓ = more parity, home win % ↓ = less advantage):

   Era             Win% std dev    Home win %
   ────────────  ──────────────  ────────────
   1984–94               0.1503         66.2%
   1995–01                    —             —
   2002–04                    —             —
   2005–17                    —             —
   2018–22               0.1401         54.4%
   2023–26               0.1496         55.6%

   ► Near-zero, non-significant correlation — parity (team win% disparity)
     does not independently predict home court advantage across seasons.
     The era-bucketed pattern is mixed: disparity peaked in 1995–01 while
     home win % was already declining, and fell in 2002–04 while home win %
     ticked back up. The two series do not move in lockstep.

   ─ Cointegration check: is the parity-HCA correlation genuine or spurious? ─
   ADF unit-root tests  (H0: unit root; p ≥ 0.05 → I(1) / nonstationary):
   League parity (win% std dev)        ADF = -1.711  p = 0.426  → I(1) nonstationary
   Home win %                          ADF = -1.352  p = 0.605  → I(1) nonstationary

   Engle-Granger cointegration  (H0: no long-run relationship):
   t = -0.000  p = 0.986  
   ► Both I(1) but NOT cointegrated — r = +0.005 is likely
     spurious; within-era game-level controls are the reliable evidence.


   Detrended checks (both series share a downward trend — remove it first):
   First-differenced (Δparity vs. Δhome-win%):
   Pearson r = +0.034  (p = 0.922  )  N = 11 year-pairs
   Residual-on-year (detrended parity vs. detrended home-win%):
   Pearson r = -0.154  (p = 0.634  )  N = 12 seasons

   ► Both detrended tests are non-significant — the raw correlation is
     driven by the shared downward trend, not a causal link.
     Year-to-year changes in parity do not predict year-to-year changes
     in home court advantage.

─── ARENA ATTENDANCE AND HOME COURT ADVANTAGE ──────────────────────────
   Source: Basketball-Reference per-game attendance (~2000 onward).
   Part A: does league attendance track home win % across seasons?
   Part B: 2020-21 dose-response — crowd size varied by local rule.

   Insufficient attendance data for season-trend correlation.


   No usable 2020-21 attendance data for the dose-response.


─── WHAT EXPLAINS THE REGULAR-SEASON DECLINE?  (N = 12,670 games) ──────
   Outcome: home_win. Baseline home win %: 61.1%.
   McFadden R² is analogous to a linear-regression R² but typical values are much smaller;
   the ΔR² column shows how much each block adds over the previous model.
   '≈pp' = approximate marginal effect in percentage points (at mean p).
   p-values and CIs use cluster-robust SEs (clusters = season-year).

   Model                                R²       ΔR²   % of fit
   ──────────────────────────────  ───────  ────────  ─────────
   Era only                         0.0096   +0.0096      69.6%
   + Rest differential              0.0108   +0.0011       8.2%
   + Altitude (DEN/UTA)             0.0133   +0.0026      18.5%
   + Time zone diff                 0.0138   +0.0005       3.7%
   + COVID flag                     0.0138   +0.0000       0.0%

   Full model coefficients  (reference era = 1984–94):

   Predictor                                     log-odds     ≈pp     95% CI (pp)         p     
   ────────────────────────────────────────────  ────────  ──────  ──────────────  ────────  ───
   era: 2018–22                                    -0.486   -11.5  [-12.8,-10.3]    <0.001  ***
   era: 2023–26                                    -0.427   -10.2  [-12.3, -8.0]    <0.001  ***
   rest diff (per day)                             +0.076    +1.8  [ +1.1, +2.5]    <0.001  ***
   altitude home (DEN/UTA)                         +0.486   +11.5  [ +5.6,+17.5]    <0.001  ***
   time zone diff (per zone)                       -0.054    -1.3  [ -2.0, -0.6]    <0.001  ***
   COVID seasons                                   +0.010    +0.2  [ +0.2, +0.3]    <0.001  ***

   ► Era dummies imply a net decline of -10.2 pp from 1984–94 → 2023–26.

   Shapley R² decomposition  (2⁵ = 32 logits, same N = 12,670 games):
   Each block's average marginal R² over all 5! orderings.
   Compare to sequential (order-dependent, era entered first).

   Block                          Shapley   Sequential
   ────────────────────────────  ────────  ───────────
   Era (structural decline)         62.4%        69.6%
   Rest differential                10.3%         8.2%
   Altitude (DEN/UTA)               19.8%        18.5%
   Time zone diff                    3.0%         3.7%
   COVID flag                        4.5%         0.0%

   ► Era Shapley share: 62%  (sequential: 70% — sequential inflated because era is entered first).
   ► Rest + altitude + tz + COVID (Shapley): 38%.

─── PRE/POST-2014 COEFFICIENT STABILITY  (regular season only) ─────────
   Do rest, altitude, and time zone effects change after the 2014 Finals format shift?
   Stable coefficients → those factors didn't drive the post-2014 change.

   Predictor                              Pre-2014   Post-2014     Shift
                                          log-odds    log-odds          
   ───────────────────────────────────  ──────────  ──────────  ────────
   rest diff (per day)                      +0.049      +0.113    +0.064
   altitude home (DEN/UTA)                  +0.550      +0.414    -0.136
   time zone diff (per zone)                -0.057      -0.050    +0.007
   ───────────────────────────────────  ──────────  ──────────  ────────
   Intercept (overall home adv. level)      +0.680      +0.225    -0.455

   N pre-2014:  6,754 games  (home win %: 66.2%)
   N post-2014: 5,916 games  (home win %: 55.2%)

   ► The intercept dropped by 10.8 pp after 2014, confirming the overall decline.
   ► Rest, altitude, and tz coefficients show some change — those factors' effects on winning are largely stable.

   Formal interaction test — pooled logit with post2014 × factor interactions:
   H0: coefficients unchanged before and after 2014.

   Interaction term                log-odds     ≈pp         p     
   ──────────────────────────────  ────────  ──────  ────────  ───
   rest_diff × post2014              +0.064    +1.5     0.064     
   altitude_home × post2014          -0.136    -3.2     0.365     
   tz_diff × post2014                +0.007    +0.2     0.858     
   ──────────────────────────────  ────────  ──────  ────────  ───
   post2014 (level shift)            -0.455   -10.8    <0.001  ***

─── PLAYOFF SERIES STRUCTURE — HOME WIN % BY GAME NUMBER ───────────────
   Does home court advantage vary by game number within a series (G1–G7)?
   G1/G2 at higher seed, G3/G4 at lower seed, then alternates (2-2-1-1-1 format).

     Game   N games   Home win %    vs. G1
   ──────  ────────  ───────────  ────────
       G1       142        68.3%         —
       G2       142        72.5%   +4.2 pp
       G3       139        54.0%  -14.4 pp
       G4       136        57.4%  -11.0 pp
       G5       116        72.4%   +4.1 pp
       G6        84        53.6%  -14.7 pp
       G7        55        61.8%   -6.5 pp

   Chi-square test (H0: home win % uniform across all game numbers):
   χ²(6) = 21.68,  p = 0.001  **

   Weighted trend line across game numbers: -1.39 pp/game  (p = 0.424  )
   (Positive = home win % rises as the series goes deeper)

   ► G7 home win % = 61.8%  (vs. G1 = 68.3%, diff = -6.5 pp)
     G7 n = 55 games (series that went to 7)

─── PLAYOFF HOME WIN % BY ERA — HIGHER SEED vs LOWER SEED AT HOME ──────
   In 2-2-1-1-1 format: G1,G2,G5,G7 = higher seed at home; G3,G4,G6 = lower seed at home.
   (Pre-2014 Finals used 2-3-2; Finals ≈ 1/15 of games — minor effect on pooled figures.)

   Era             Higher seed at home (G1,2,5,7)   Lower seed at home (G3,4,6)     Gap
   ────────────  ────────────────────────────────  ────────────────────────────  ──────
   1984–94         73.7%  ( 224 games)                  62.5%  ( 168 games)       +11.2 pp
   2018–22         68.8%  (  93 games)                  45.6%  (  79 games)       +23.2 pp
   2023–26         64.5%  ( 138 games)                  50.9%  ( 112 games)       +13.6 pp
   ────────────  ────────────────────────────────  ────────────────────────────  ──────
   All eras        69.9%  ( 455 games)                  55.2%  ( 359 games)       +14.7 pp

   ► In the early eras (1984–94, 1995–01) the lower-seeded team won ~65–66% at home,
     nearly matching the higher seed's own home win rate. Home court was a genuine
     equalizer. From 2002 onward the lower-seed home win rate collapsed to ~47–52%,
     while the higher seed's remained at 65–75%. What faded is the boost home court
     gave to the team that needed it most.

─── PLAYOFF SERIES SIMULATION — DOES THE PER-GAME EDGE SURVIVE A BEST-OF-7? 
   Monte Carlo: 200,000 simulated 2-2-1-1-1 series between two
   otherwise-equal teams, home-court team hosting games 1,2,5,6,7. Input is
   the observed single-game home win % per era.

   Era         RS /game  RS series   PO /game  PO series
   ─────────────────────────────────────────────────────
   1984–94        66.2%      55.3%      67.8%      55.9%
   1995–01            —          —          —          —
   2002–04            —          —          —          —
   2005–17            —          —          —          —
   2018–22        54.4%      51.5%      58.1%      52.7%
   2023–26        55.6%      51.9%      58.4%      52.8%

   ► Regular season: per-game home edge fell 10.6 pp across eras,
     but the series edge fell only 3.4 pp (now 51.9%).
   ► Playoffs: per-game edge fell 9.4 pp, series edge fell 3.2 pp (now 52.8%).

   Caveats: the playoff per-game % conflates home court with seeding (better
   teams host more), so the regular-season row is the cleaner pure-venue
   input. The sim assumes games are independent given the per-game edge, so
   it illustrates the format's leverage rather than forecasting a series.


─── PLAYOFF HCA — SEEDING QUALITY DECOMPOSITION ────────────────────────
   Does the playoff HCA decline reflect true home-court weakening, or do
   better seeds simply fail to dominate lower seeds as they once did?
   quality_diff = home RS win% − away RS win% (same season).
   N = 922 playoff games with complete quality data.

   Model comparison — year trend before and after quality control:

   Model                            year (pp/yr)         p   McF. R²
   ──────────────────────────────  ─────────────  ────────  ────────
   Year only                              -0.258     0.003    0.0071
   Quality only                                —         —    0.0690
   Year + quality_diff                    -0.270     0.004    0.0761

   quality_diff (bivariate):  +113.18 pp per unit  (p = <0.001  ***)
   quality_diff (full model): +114.25 pp per unit  (p = <0.001  ***)
   Year trend retained after quality control: 105%
   Absorbed by quality_diff: -5%

   Has the seed-quality gap itself trended over time?
   Trend in mean quality_diff per season: -0.00024 per yr  (p = 0.002  **,  R² = 0.6304)

   Era breakdown — mean quality_diff and playoff home win %:
   Era                N   Mean quality_diff   Home win %
   ────────────  ──────  ──────────────────  ───────────
   1984–94          500             +0.0180        67.8%
   2018–22          172             +0.0070        58.1%
   2023–26          250             +0.0110        58.4%

   Lower-seed-at-home check (G3+G4 where quality_diff < 0):
   N = 218 games  Home win % = 50.9%
   ► Even when the objectively weaker team is at home, they win 51% — pure venue effect.

   ► Quality control barely moves the year coefficient (105% retained) —
     the playoff decline is primarily genuine home-court weakening, not seed compression.

─── TEAM QUALITY ROBUSTNESS — ERA EFFECT WITH HOME/AWAY TEAM FIXED EFFECTS 
   Does the era decline survive adding home- and away-team fixed effects?
   Franchise indicators remove systematic differences in home win rates
   across teams, so the era slope is not confounded by which franchises
   happen to host more games in different periods.

   Era coefficients (pp relative to 1984-94 baseline):

   Era               Baseline    With team FE     Shift
   ────────────  ────────────  ──────────────  ────────
   1995–01                  —               —         —
   2002–04                  —               —         —
   2005–17                  —               —         —
   2018–22           -11.5 pp        -10.8 pp   +0.7 pp
   2023–26           -10.2 pp         -9.3 pp   +0.8 pp

   McFadden R²: baseline = 0.0138  →  with team FE = 0.0629  (Δ = +0.0491)
   Max era coefficient shift across eras: 0.8 pp
   ► Era coefficients are stable under team FE — the decline is
     not explained by which franchises host games.


─── PLAYOFF FORMAT PERIODS — DID THE SCHEDULING CHANGES MATTER? ────────
   Playoff home win % by format period (1985, 2003, 2014 changes).
   Pairwise tests compare consecutive periods; the trend-controlled model
   asks whether format adds a level shift beyond the secular year trend.

   Period       N games   Home win %
   ──────────  ────────  ───────────
   1984              79        64.6%
   1985–02          421        68.4%
   2014–26          422        58.3%

   Consecutive periods — two-proportion z-tests:
       1984 → 1985–02    +3.9 pp   (z = -0.67, p = 0.501  )
    1985–02 → 2014–26   -10.1 pp   (z = +3.05, p = 0.002  **)

   Trend-controlled logistic: home_win ~ year + format_period
   (reference period = 1984)

   Predictor                     log-odds     ≈pp         p     
   ────────────────────────────  ────────  ──────  ────────  ───
   format: 1985–02                 +0.156    +3.6     0.610     
   format: 2014–26                 -0.459   -10.6     0.801     
   year trend (per yr)             +0.005    +0.1     0.914     

   LR test — format dummies jointly vs. year-only model: χ²(2) = 0.79,  p = 0.672  

   ► After controlling for the year trend, the 2014–26 dummy is not significant
     (p = 0.801) — the post-2014 drop is consistent with the secular
     decline passing through, not a distinct format-change effect.

─── FRANCHISE HOME COURT ADVANTAGE — HOME VS. ROAD WIN % ───────────────
   Which franchises benefit most from playing at home?
   HCA = home win% − road win% (controls for overall team quality).

   Regular season  (35 franchises with ≥50 home games)
   Sorted by EB-shrunken HCA.
   CI ± = 95% half-width (binomial SE).

   Franchise                      n_h   home%     n_r   road%     HCA    CI ±  Shrunken
   ────────────────────────── ─────── ─────── ─────── ─────── ─────── ─────── ─────────
   Seattle SuperSonics            287    67.6%     287    28.2%   +39.4 ±    7.5     +36.0 pp
   Washington Bullets             287    63.1%     287    29.3%   +33.8 ±    7.7     +31.3 pp
   Utah Jazz                      487    68.2%     487    36.8%   +31.4 ±    6.0     +30.1 pp
   Denver Nuggets                 487    74.1%     487    42.9%   +31.2 ±    5.9     +29.9 pp
   Kansas City Kings               82    59.8%      82    24.4%   +35.4 ±   14.1     +28.9 pp
   Golden State Warriors          487    61.4%     487    33.3%   +28.1 ±    6.0     +27.2 pp
   New Jersey Nets                287    51.2%     287    22.6%   +28.6 ±    7.5     +27.1 pp
   Phoenix Suns                   487    68.0%     487    40.2%   +27.7 ±    6.0     +26.8 pp
   Houston Rockets                487    60.4%     487    32.9%   +27.5 ±    6.0     +26.6 pp
   Atlanta Hawks                  486    66.9%     488    41.0%   +25.9 ±    6.0     +25.2 pp
   Portland Trail Blazers         487    63.0%     487    37.4%   +25.7 ±    6.1     +25.1 pp
   Cleveland Cavaliers            487    63.2%     487    38.2%   +25.1 ±    6.1     +24.5 pp
   Milwaukee Bucks                488    74.2%     486    49.6%   +24.6 ±    5.9     +24.1 pp
   Los Angeles Clippers           246    41.5%     246    16.7%   +24.8 ±    7.7     +24.0 pp
   Boston Celtics                 487    80.3%     487    57.5%   +22.8 ±    5.6     +22.6 pp
   San Antonio Spurs              486    51.6%     488    29.3%   +22.3 ±    6.0     +22.1 pp
   New York Knicks                487    60.2%     487    38.2%   +22.0 ±    6.1     +21.8 pp
   Indiana Pacers                 486    53.5%     488    31.6%   +21.9 ±    6.1     +21.7 pp
   Chicago Bulls                  487    60.2%     487    38.8%   +21.4 ±    6.1     +21.3 pp
   Dallas Mavericks               486    66.5%     488    45.5%   +21.0 ±    6.1     +20.9 pp
   Philadelphia 76ers             487    68.8%     487    48.0%   +20.7 ±    6.1     +20.7 pp
   Los Angeles Lakers             488    75.4%     486    56.0%   +19.4 ±    5.8     +19.5 pp
   Detroit Pistons                486    59.5%     488    40.6%   +18.9 ±    6.2     +19.1 pp
   Sacramento Kings               405    49.4%     405    33.3%   +16.0 ±    6.7     +16.7 pp
   Toronto Raptors                200    49.5%     200    36.0%   +13.5 ±    9.6     +15.4 pp
   LA Clippers                    200    64.5%     200    52.5%   +12.0 ±    9.6     +14.3 pp
   Orlando Magic                  241    44.0%     241    32.0%   +12.0 ±    8.6     +13.9 pp
   Minnesota Timberwolves         241    55.2%     241    43.6%   +11.6 ±    8.9     +13.7 pp
   New Orleans Pelicans           199    49.7%     201    39.8%    +9.9 ±    9.7     +12.8 pp
   Miami Heat                     282    50.0%     282    39.7%   +10.3 ±    8.2     +12.4 pp
   Oklahoma City Thunder          200    57.0%     200    48.5%    +8.5 ±    9.7     +11.8 pp
   Memphis Grizzlies              200    59.0%     200    51.0%    +8.0 ±    9.7     +11.4 pp
   Charlotte Hornets              282    35.8%     282    28.7%    +7.1 ±    7.7      +9.6 pp
   Brooklyn Nets                  200    51.5%     200    46.0%    +5.5 ±    9.8      +9.6 pp
   Washington Wizards             199    37.2%     201    31.3%    +5.8 ±    9.3      +9.5 pp

   League mean HCA = +20.6 pp  (raw range: +5.5 to +39.4 pp)
   Variance decomposition: observed SD = 9.0 pp, sampling noise = 19%, true between-franchise SD ≈ 8.1 pp
   ► Utah Jazz: raw +31.4 pp, shrunken +30.1 pp  (rank #3/35 by shrunken)
   ► Denver Nuggets: raw +31.2 pp, shrunken +29.9 pp  (rank #4/35 by shrunken)

   Playoffs  (19 franchises with ≥20 home games)
   Sorted by raw HCA (EB shrinkage collapses all to league mean — see variance decomp below).
   CI ± = 95% half-width (binomial SE).

   Franchise                      n_h   home%     n_r   road%     HCA    CI ±  Shrunken
   ────────────────────────── ─────── ─────── ─────── ─────── ─────── ─────── ─────────
   Chicago Bulls                   27    63.0%      31    25.8%   +37.2 ±   23.9     +25.8 pp
   Cleveland Cavaliers             23    56.5%      22    22.7%   +33.8 ±   26.8     +25.8 pp
   Los Angeles Lakers              83    77.1%      69    43.5%   +33.6 ±   14.8     +25.8 pp
   Milwaukee Bucks                 59    64.4%      60    31.7%   +32.7 ±   17.0     +25.8 pp
   Indiana Pacers                  22    68.2%      25    36.0%   +32.2 ±   27.1     +25.8 pp
   New York Knicks                 40    65.0%      42    33.3%   +31.7 ±   20.5     +25.8 pp
   Atlanta Hawks                   33    60.6%      36    30.6%   +30.1 ±   22.5     +25.8 pp
   Golden State Warriors           30    70.0%      35    40.0%   +30.0 ±   23.1     +25.8 pp
   Portland Trail Blazers          29    55.2%      27    25.9%   +29.2 ±   24.5     +25.8 pp
   Utah Jazz                       34    55.9%      32    28.1%   +27.8 ±   22.8     +25.8 pp
   Boston Celtics                 102    73.5%      87    46.0%   +27.6 ±   13.5     +25.8 pp
   Houston Rockets                 28    60.7%      26    34.6%   +26.1 ±   25.7     +25.8 pp
   Detroit Pistons                 52    76.9%      47    51.1%   +25.9 ±   18.3     +25.8 pp
   Dallas Mavericks                44    61.4%      51    37.3%   +24.1 ±   19.6     +25.8 pp
   Denver Nuggets                  56    60.7%      55    38.2%   +22.5 ±   18.1     +25.8 pp
   Phoenix Suns                    49    63.3%      49    42.9%   +20.4 ±   19.3     +25.8 pp
   Philadelphia 76ers              44    59.1%      45    40.0%   +19.1 ±   20.4     +25.8 pp
   Miami Heat                      26    50.0%      28    42.9%    +7.1 ±   26.6     +25.8 pp
   Minnesota Timberwolves          20    50.0%      22    50.0%    +0.0 ±   30.3     +25.8 pp

   League mean HCA = +25.8 pp  (raw range: +0.0 to +37.2 pp)
   Variance decomposition: observed SD = 9.2 pp, sampling noise = 151%, true between-franchise SD ≈ 0.0 pp
   ► Utah Jazz: raw +27.8 pp, shrunken +25.8 pp  (rank #10/19 by shrunken)
   ► Denver Nuggets: raw +22.5 pp, shrunken +25.8 pp  (rank #15/19 by shrunken)


─── FRANCHISE HCA — ERA COMPARISON (split at 2001–02) ──────────────────
   Regular season only. Franchise name changes merged: Bullets→Wizards, LA Clippers→Los Angeles Clippers.
   Min 400 home games in each era required.

   N = 0 franchises with ≥400 home games in both eras (insufficient data for an era comparison)


─── FRANCHISE HCA — REGULAR SEASON VS. PLAYOFFS CONSISTENCY ────────────
   Do franchises that protect home court in the regular season also do
   so in the playoffs? Correlation across franchises with both figures.

   N = 19 franchises with both regular-season and playoff HCA
   Raw HCA:
   Pearson r  = +0.566  (p = 0.012  *)
   Spearman ρ = +0.172  (p = 0.482  )

   Shrunken HCA: true between-franchise variance ≈ 0 in at least one context
   (observed spread across franchises is entirely sampling noise).
   Shrinkage collapses all values to the league mean — shrunken correlation undefined.
   This confirms that franchise-level playoff HCA differences are not reliably
   distinguishable from random variation given typical playoff sample sizes.

   Mean regular-season HCA (shared franchises): +23.0 pp
   Mean playoff HCA (shared franchises):        +25.8 pp
   Mean playoff − regular-season gap:           +2.8 pp (SD 7.4)

   ► Raw correlation positive and significant (r = +0.566) —
     franchises that protect home court in the regular season tend to do so
     in the playoffs too, though playoff sample sizes are too small for
     franchise-level shrinkage to improve on raw estimates.

─── WIN MARGIN TRENDS  (home team point differential per game) ─────────
   Positive = home team winning by more.
   Trend = slope of trend line (change per season year).

   Regular season  (N = 5,995 games)

   Era             All games    Home wins  Home losses
   ───────────────────────────────────────────────────
   1984–94                 —            —            —
   1995–01                 —            —            —
   2002–04                 —            —            —
   2005–17                 —            —            —
   2018–22             +1.35       +12.52       -11.96
   2023–26             +2.11       +12.83       -11.31
   ───────────────────────────────────────────────────
   Trend/yr        +0.181       +0.294  *    +0.049   

   Playoffs  (N = 422 games)

   Era             All games    Home wins  Home losses
   ───────────────────────────────────────────────────
   1984–94                 —            —            —
   1995–01                 —            —            —
   2002–04                 —            —            —
   2005–17                 —            —            —
   2018–22             +3.56       +13.97       -10.89
   2023–26             +4.58       +14.97       -10.00
   ───────────────────────────────────────────────────
   Trend/yr        +0.501       +0.690       +0.241   

   ► Overall reg-season mean margin: +1.82 pts.
   ► Overall playoff mean margin:    +4.17 pts.

─── WIN MARGIN POLARIZATION — UNCONDITIONAL QUANTILE REGRESSION  (checks blowout claim in other findings) 
   home margin ~ year at q = 0.10, 0.25, 0.50, 0.75, 0.90.
   Margin > 0 = home winning. Q10 = big home losses; Q90 = big home wins.
   All quantiles parallel → pure level effect (conditional divergence is artifact).
   Q10↓ with Q90↑ → genuine polarization.

   Regular season  (N = 5,995 games, 2021–2025)

   Quantile   Slope pts/yr                95% CI         p     
   ────────  ─────────────  ────────────────────  ────────  ───
        Q10         -0.009  [-0.552, +0.534]     0.974     
        Q25         +0.000  [-0.321, +0.321]     1.000     
        Q50         +0.000  [-0.376, +0.376]     1.000     
        Q75         +0.250  [-0.081, +0.581]     0.138     
        Q90         +0.278  [-0.187, +0.743]     0.242     

   IQR change rate (Q90 − Q10 slope diff): +0.287 pts/yr
   ► Q90 rises / Q10 falls — genuine variance widening (polarization confirmed).
     The conditional-on-outcome divergence in §6 reflects a real change in
     distribution shape, not just a composition effect.

   Playoffs  (N = 422 games, 2021–2025)

   Quantile   Slope pts/yr                95% CI         p     
   ────────  ─────────────  ────────────────────  ────────  ───
        Q10         -0.006  [-1.467, +1.454]     0.993     
        Q25         +0.334  [-0.858, +1.525]     0.582     
        Q50         +0.002  [-1.503, +1.508]     0.997     
        Q75         +0.333  [-1.048, +1.715]     0.635     
        Q90         +0.325  [-1.555, +2.206]     0.734     

   IQR change rate (Q90 − Q10 slope diff): +0.332 pts/yr
   ► Q90 rises / Q10 falls — genuine variance widening (polarization confirmed).
     The conditional-on-outcome divergence in §6 reflects a real change in
     distribution shape, not just a composition effect.


─── NET RATING SPLIT BY VENUE  (home team pts per 100 possessions) ─────
   Net rating = (home pts − away pts) / avg possessions × 100.
   Positive = home team outscored visitors per 100 possessions.
   Requires pace data; seasons without TOV/OREB data are excluded.

   Regular season  (N = 5,995 games with pace data)

   Era           Net rating (pts/100)
   ──────────────────────────────────
   1984–94                          —
   1995–01                          —
   2002–04                          —
   2005–17                          —
   2018–22                      +1.36
   2023–26                      +2.07
   ──────────────────────────────────
   Trend/yr                 +0.172   

   Playoffs  (N = 422 games with pace data)

   Era           Net rating (pts/100)
   ──────────────────────────────────
   1984–94                          —
   1995–01                          —
   2002–04                          —
   2005–17                          —
   2018–22                      +3.60
   2023–26                      +4.67
   ──────────────────────────────────
   Trend/yr                 +0.506   

   ► Overall reg-season mean net rating: +1.80 pts/100 poss.
   ► Overall playoff mean net rating:    +4.23 pts/100 poss.

─── MULTIPLE COMPARISONS — BH FDR CORRECTION ACROSS PRIMARY TESTS ──────
   BH correction at q = 0.05; threshold for rank i (ascending p): (i/m) × 0.05.
   Tests re-run here on the same data to form a self-contained table.

   m = 14 primary tests.  BH threshold for rank i: (i/14) × 0.05.

   Rank  Test                                         p-value   BH thresh  Survives
   ────  ────────────────────────────────────────  ──────────  ──────────  ────────
      1  RS HCA year trend                             <0.001      0.0036       YES
      2  RS rest differential                          <0.001      0.0071       YES
      3  RS OREB rate vs rebound share edge            <0.001      0.0107       YES
      4  RS altitude (DEN/UTA)                         <0.001      0.0143       YES
      5  RS travel distance                             0.002      0.0179       YES
      6  PO HCA year trend                              0.003      0.0214       YES
      7  RS time zone effect                            0.005      0.0250       YES
      8  RS pace LOO within-era                         0.219      0.0286        no
      9  RS era dummies beyond year trend               0.398      0.0321        no
     10  PO rest differential                           0.419      0.0357        no
     11  PO 3PA within-era effect                       0.645      0.0393        no
     12  RS parity vs HCA (first-diff)                  0.922      0.0429        no
     13  RS 3PA within-era effect                       0.986      0.0464        no
     14  PO era dummies beyond year trend               0.996      0.0500        no

   BH result: 7 / 14 tests survive (q = 0.05).
   Does NOT survive BH: RS pace LOO within-era, RS era dummies beyond year trend, PO rest differential, PO 3PA within-era effect, RS parity vs HCA (first-diff), RS 3PA within-era effect, PO era dummies beyond year trend
   ► Core findings (HCA trends, rest, altitude, era shift, 3PA) survive.
     Marginal factors (travel, parity, time zone) may not — treat as exploratory.


════════════════════════════════════════════════════════════════════════

