"""
player_ranking_overview_analysis.py — statistical analysis for the player ranking overview.

run() prints all output; the orchestrator captures it to docs/player_ranking_overview_results.md.
Sections use the box-drawing header convention: print("─── SECTION " + "─" * 50).
"""

import numpy as np
import pandas as pd
from scipy import stats

from player_ranking_overview_data import load_unified_ratings, MIN_MINUTES_QUALIFIER

# Rating systems included in the cross-system comparison
# (all systems that may be present; silently skipped if absent in the data)
ALL_SYSTEMS = [
    "GAME_SCORE", "PER", "WS", "WS48", "BPM", "OBPM", "DBPM", "VORP",
    "RAPTOR", "RAPTOR_WAR", "RAPTOR_O", "RAPTOR_D",
    "DARKO_DPM", "EPM", "LEBRON", "ESPN_RPM",
]

SYSTEM_LABELS = {
    "GAME_SCORE": "Game Score",
    "PER": "PER",
    "TS_PCT": "TS%",
    "EFG_PCT": "eFG%",
    "USG_PCT": "USG%",
    "WS": "Win Shares",
    "WS48": "WS/48",
    "OWS": "Offensive Win Shares",
    "DWS": "Defensive Win Shares",
    "BPM": "BPM",
    "OBPM": "OBPM",
    "DBPM": "DBPM",
    "VORP": "VORP",
    "RAPTOR": "RAPTOR",
    "RAPTOR_O": "RAPTOR-O",
    "RAPTOR_D": "RAPTOR-D",
    "RAPTOR_WAR": "RAPTOR WAR",
    "DARKO_DPM": "DARKO DPM",
    "EPM": "EPM",
    "LEBRON": "LEBRON",
    "ESPN_RPM": "ESPN RPM",
    "MVP_SHARE": "MVP Vote Share",
    "ALL_NBA_PTS": "All-NBA Points",
    "CONSENSUS": "Consensus",
    "WINS_PRED": "Wins-Predictive",
}


def _present_systems(df: pd.DataFrame, systems: list[str]) -> list[str]:
    """Return the subset of `systems` that have at least 10 non-null values in df."""
    return [s for s in systems if s in df.columns and df[s].notna().sum() >= 10]


def _gini(values: np.ndarray) -> float:
    """Gini coefficient for a 1-D array of non-negative values."""
    v = np.sort(np.maximum(values, 0))
    n = len(v)
    if n == 0 or v.sum() == 0:
        return 0.0
    idx = np.arange(1, n + 1)
    return float((2 * np.dot(idx, v) / (n * v.sum())) - (n + 1) / n)


def _top_share(values: np.ndarray, top_pct: float = 0.05) -> float:
    """Fraction of total (positive) value held by the top_pct of players."""
    v = np.sort(values)[::-1]
    total = v[v > 0].sum()
    if total == 0:
        return 0.0
    top_n = max(1, int(np.ceil(len(v) * top_pct)))
    return float(v[:top_n].sum() / total)


def _build_consensus(df: pd.DataFrame, systems: list[str]) -> pd.Series:
    """Mean z-score across all present systems (qualified players only)."""
    present = _present_systems(df, systems)
    if not present:
        return pd.Series(np.nan, index=df.index)
    z_cols = []
    for s in present:
        col = df[s].copy()
        std = col.std()
        if std > 0:
            df[f"_z_{s}"] = (col - col.mean()) / std
            z_cols.append(f"_z_{s}")
    if not z_cols:
        return pd.Series(np.nan, index=df.index)
    consensus = df[z_cols].mean(axis=1)
    # Clean up temp columns
    df.drop(columns=z_cols, inplace=True)
    return consensus


def _build_wins_predictive(df: pd.DataFrame, systems: list[str]) -> pd.Series:
    """Wins-predictive rating: ridge regression of system z-scores onto team wins.

    Aggregates player ratings to team level (minutes-weighted), fits a
    non-negative constrained ridge to predict team W (from MIN and TEAM_ID),
    then reads back per-player weights.

    Falls back to consensus if not enough team-win data.
    """
    present = _present_systems(df, systems)
    if len(present) < 2 or "TEAM_ID" not in df.columns or "MIN" not in df.columns:
        return _build_consensus(df, present)

    # Z-score each system
    z_df = pd.DataFrame(index=df.index)
    for s in present:
        col = df[s].copy()
        std = col.std()
        z_df[s] = (col - col.mean()) / std if std > 0 else 0

    # Minutes-weighted team average for each system
    df2 = df[["TEAM_ID", "MIN"]].copy()
    for s in present:
        df2[s] = z_df[s]

    team_ratings = (
        df2.groupby("TEAM_ID")
        .apply(lambda g: pd.Series(
            {s: np.average(g[s].fillna(0), weights=g["MIN"].clip(lower=0).fillna(0) + 1)
             for s in present}
        ))
        .reset_index()
    )

    # Team wins: look for TEAM_W (merged from team_totals) or W column
    win_col = "TEAM_W" if "TEAM_W" in df.columns else ("W" if "W" in df.columns else None)
    if win_col is None:
        return _build_consensus(df, present)

    team_wins = df.groupby("TEAM_ID")[win_col].max().reset_index().rename(columns={win_col: "W"})

    team_data = team_ratings.merge(team_wins, on="TEAM_ID", how="inner")
    if len(team_data) < 5:
        return _build_consensus(df, present)

    X = team_data[present].fillna(0).values
    y = team_data["W"].values.astype(float)

    # Non-negative ridge (sklearn if available, else OLS)
    try:
        from sklearn.linear_model import Ridge
        from sklearn.preprocessing import StandardScaler
        scaler = StandardScaler()
        X_s = scaler.fit_transform(X)
        ridge = Ridge(alpha=5.0, fit_intercept=True, positive=False)
        ridge.fit(X_s, y)
        coef = ridge.coef_
    except ImportError:
        coef, _, _, _ = np.linalg.lstsq(X, y, rcond=None)

    # Per-player wins-predictive score = weighted combination, then normalize to z-space
    wp = pd.Series(0.0, index=df.index)
    for i, s in enumerate(present):
        std = df[s].std()
        z = (df[s] - df[s].mean()) / std if std > 0 else 0
        wp += coef[i] * z.fillna(0)

    wp_std = wp.std()
    if wp_std > 0:
        wp = (wp - wp.mean()) / wp_std
    return wp


def _unique_r2(df: pd.DataFrame, systems: list[str]) -> dict[str, float]:
    """For each system, estimate unique variance it explains beyond the others.

    Method: regress each system on all others; the residual R² is the
    unique signal. Returns {system: unique_r2}.
    """
    present = _present_systems(df, systems)
    if len(present) < 3:
        return {}

    result = {}
    for s in present:
        others = [o for o in present if o != s]
        sub = df[present].dropna()
        if len(sub) < 20:
            result[s] = 0.0
            continue
        X = sub[others].values
        y = sub[s].values
        coef, _, _, _ = np.linalg.lstsq(
            np.column_stack([np.ones(len(X)), X]), y, rcond=None
        )
        y_hat = np.column_stack([np.ones(len(X)), X]) @ coef
        ss_res = ((y - y_hat) ** 2).sum()
        ss_tot = ((y - y.mean()) ** 2).sum()
        result[s] = float(1 - ss_res / ss_tot) if ss_tot > 0 else 0.0

    return result


def run(end_year: int = 2025) -> None:
    """Run all analysis sections and print results to stdout."""
    df_full = load_unified_ratings(end_year)
    qual = df_full[df_full["QUALIFIED"] == True].copy() if "QUALIFIED" in df_full.columns else df_full.copy()
    present = _present_systems(qual, ALL_SYSTEMS)

    header = lambda title: print(f"\n{'─' * 3} {title} {'─' * max(0, 60 - len(title))}")

    header("DATA COVERAGE")
    print(f"Season: {end_year - 1}–{str(end_year)[-2:]}")
    print(f"Total players in unified table: {len(df_full)}")
    print(f"Qualified players (>= {MIN_MINUTES_QUALIFIER} min): {len(qual)}")
    print(f"Rating systems present: {len(present)}")
    for s in present:
        n_valid = qual[s].notna().sum()
        print(f"  {SYSTEM_LABELS.get(s, s)}: {n_valid} players with data")

    header("BASIC DISTRIBUTION STATS")
    for s in present:
        vals = qual[s].dropna().values
        if len(vals) < 5:
            continue
        print(f"\n{SYSTEM_LABELS.get(s, s)} (n={len(vals)}):")
        print(f"  Mean: {vals.mean():.2f}  Median: {np.median(vals):.2f}  "
              f"Std: {vals.std():.2f}")
        print(f"  Min: {vals.min():.2f}  Max: {vals.max():.2f}")
        print(f"  Gini: {_gini(vals):.3f}  Top-5% share: {_top_share(vals)*100:.1f}%")

    header("RANK AGREEMENT (SPEARMAN CORRELATIONS)")
    if len(present) >= 2:
        ranks = qual[present].rank(pct=True)
        corr = ranks.corr(method="spearman")
        # Print upper triangle only
        for i, si in enumerate(present):
            for j, sj in enumerate(present):
                if j > i:
                    r = corr.loc[si, sj]
                    label_i = SYSTEM_LABELS.get(si, si)
                    label_j = SYSTEM_LABELS.get(sj, sj)
                    print(f"  {label_i} vs {label_j}: r={r:.3f}")

    header("WHAT EACH SYSTEM UNIQUELY CAPTURES")
    uniq = _unique_r2(qual, present)
    for s, r2 in sorted(uniq.items(), key=lambda x: -x[1]):
        print(f"  {SYSTEM_LABELS.get(s, s)}: unique R² = {r2:.3f}")

    header("CONSENSUS RATING — TOP 20")
    qual["CONSENSUS"] = _build_consensus(qual, present)
    if qual["CONSENSUS"].notna().sum() > 0:
        top = qual.nlargest(20, "CONSENSUS")
        for rank, (_, row) in enumerate(top.iterrows(), 1):
            name = row.get("PLAYER_NAME", "Unknown")
            print(f"  {rank:>2}. {name:<30}  Consensus z = {row['CONSENSUS']:.2f}")

    header("WINS-PREDICTIVE RATING — TOP 20")
    qual["WINS_PRED"] = _build_wins_predictive(qual, present)
    df_full["WINS_PRED"] = np.nan
    if qual["WINS_PRED"].notna().sum() > 0:
        top = qual.nlargest(20, "WINS_PRED")
        for rank, (_, row) in enumerate(top.iterrows(), 1):
            name = row.get("PLAYER_NAME", "Unknown")
            print(f"  {rank:>2}. {name:<30}  Wins-predictive z = {row['WINS_PRED']:.2f}")

    header("COMPARISON: CONSENSUS vs. WINS-PREDICTIVE")
    if qual["CONSENSUS"].notna().sum() > 0 and qual["WINS_PRED"].notna().sum() > 0:
        both = qual[["PLAYER_NAME", "CONSENSUS", "WINS_PRED", "MIN"]].dropna()
        if len(both) >= 10:
            r, p = stats.spearmanr(both["CONSENSUS"], both["WINS_PRED"])
            print(f"  Spearman correlation between consensus and wins-predictive: {r:.3f} (p={p:.3f})")
            both["_diff"] = both["WINS_PRED"] - both["CONSENSUS"]
            print("  Players rated much higher by wins-predictive than consensus:")
            for _, row in both.nlargest(5, "_diff").iterrows():
                print(f"    {row['PLAYER_NAME']:<30}  diff = +{row['_diff']:.2f}")
            print("  Players rated much lower by wins-predictive than consensus:")
            for _, row in both.nsmallest(5, "_diff").iterrows():
                print(f"    {row['PLAYER_NAME']:<30}  diff = {row['_diff']:.2f}")

    header("POWER-LAW / TAIL ANALYSIS")
    cumulative_metrics = [s for s in present if s in ("WS", "VORP", "RAPTOR_WAR")]
    rate_metrics = [s for s in present if s in ("PER", "BPM", "RAPTOR", "DARKO_DPM", "EPM")]

    for group_label, group in [("Cumulative-value metrics", cumulative_metrics),
                                 ("Rate metrics", rate_metrics)]:
        print(f"\n{group_label}:")
        for s in group:
            vals = qual[s].dropna().values
            if len(vals) < 10:
                continue
            pos_vals = vals[vals > 0]
            gini = _gini(vals)
            top5 = _top_share(vals, 0.05)
            print(f"  {SYSTEM_LABELS.get(s, s)}: Gini={gini:.3f}, top-5% hold {top5*100:.1f}% of value")
            if len(pos_vals) >= 10:
                # Skewness
                skew = float(stats.skew(pos_vals))
                print(f"    Skewness: {skew:.2f} ({'right-skewed' if skew > 0.5 else 'near-symmetric'})")

    header("WHO EACH SYSTEM LOVES vs. CONSENSUS")
    qual["CONSENSUS"] = _build_consensus(qual, present)
    for s in present[:8]:  # top 8 systems only to keep output manageable
        z_s = (qual[s] - qual[s].mean()) / qual[s].std() if qual[s].std() > 0 else 0
        residual = z_s - qual["CONSENSUS"]
        top3 = qual.assign(_res=residual).nlargest(3, "_res")
        bot3 = qual.assign(_res=residual).nsmallest(3, "_res")
        print(f"\n{SYSTEM_LABELS.get(s, s)} loves (vs. consensus):")
        for _, row in top3.iterrows():
            print(f"  +{row.get('_res', 0):.2f}  {row.get('PLAYER_NAME', '?')}")
        print(f"{SYSTEM_LABELS.get(s, s)} discounts (vs. consensus):")
        for _, row in bot3.iterrows():
            print(f"  {row.get('_res', 0):.2f}  {row.get('PLAYER_NAME', '?')}")
