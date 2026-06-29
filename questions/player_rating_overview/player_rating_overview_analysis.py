"""
player_rating_overview_analysis.py — statistical analysis for the player rating overview.

run() prints all output; the orchestrator captures it to docs/player_rating_overview_results.md.
Sections use the box-drawing header convention: print("─── SECTION " + "─" * 50).
"""

import numpy as np
import pandas as pd
from scipy import stats

from player_rating_overview_data import (
    load_unified_ratings,
    load_team_outcomes,
    load_playoff_deltas,
    MIN_MINUTES_QUALIFIER,
    MIN_PLAYOFF_MINUTES,
    PLAYOFF_DELTA_METRICS,
    powerlaw_fit,
    POWERLAW_R2_THRESHOLD,
)
from player_rating_overview_facts import FACTS, _FACTS_PATH, _GUARDS_PATH

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


# Systems whose construction uses team or lineup point differential (BPM's team
# adjustment, Win Shares' calibration to team wins, the impact metrics' RAPM
# base). For these, reconstructing team point differential is partly mechanical,
# so a high retrodiction score is not evidence of quality. The outcome-blind
# metrics (PER, Game Score) never saw who won, so their score is a genuine read.
OUTCOME_CALIBRATED = {
    "WS", "WS48", "BPM", "OBPM", "DBPM", "VORP",
    "RAPTOR", "RAPTOR_O", "RAPTOR_D", "RAPTOR_WAR",
    "DARKO_DPM", "EPM", "LEBRON", "ESPN_RPM",
}


def _team_mean_z(df: pd.DataFrame, system: str) -> pd.Series | None:
    """Minutes-weighted team mean of a system's player z-scores.

    Z-scores the system across all players who carry it, then takes the
    minutes-weighted average within each team (a small +1 keeps zero-minute rows
    from vanishing). Returns a Series indexed by TEAM_ID, or None if the system
    has no spread.
    """
    if system not in df.columns or "TEAM_ID" not in df.columns or "MIN" not in df.columns:
        return None
    col = df[system]
    std = col.std()
    if not std > 0:
        return None
    z = (col - col.mean()) / std
    t = pd.DataFrame({
        "TEAM_ID": df["TEAM_ID"],
        "z": z,
        "w": df["MIN"].clip(lower=0).fillna(0) + 1,
    }).dropna(subset=["z"])
    return t.groupby("TEAM_ID").apply(
        lambda d: np.average(d["z"], weights=d["w"]), include_groups=False
    )


def retrodiction_scores(df: pd.DataFrame, outcomes: pd.DataFrame,
                        systems: list[str], target: str = "point_diff") -> dict:
    """Grade each system by how well its team aggregate rebuilds team results.

    For each system: minutes-weighted team mean z-rating, then a single-predictor
    line onto the team outcome (point differential per game by default). Reports
    both the in-sample R² and a leave-one-team-out cross-validated R² (the honest
    out-of-sample read on 30 teams). Returns {system: {r2, cv_r2, n}}.
    """
    y_map = outcomes.set_index("TEAM_ID")[target]
    result = {}
    for s in systems:
        tm = _team_mean_z(df, s)
        if tm is None:
            continue
        data = pd.DataFrame({"x": tm, "y": y_map}).dropna()
        if len(data) < 10:
            continue
        x = data["x"].values
        y = data["y"].values
        ss_tot = float(((y - y.mean()) ** 2).sum())
        if ss_tot <= 0:
            continue
        b1, b0 = np.polyfit(x, y, 1)
        yhat = b1 * x + b0
        r2 = 1.0 - float(((y - yhat) ** 2).sum()) / ss_tot
        # Leave-one-team-out cross-validation
        preds = np.empty(len(x))
        for i in range(len(x)):
            mask = np.arange(len(x)) != i
            c1, c0 = np.polyfit(x[mask], y[mask], 1)
            preds[i] = c1 * x[i] + c0
        cv_r2 = 1.0 - float(((y - preds) ** 2).sum()) / ss_tot
        result[s] = {"r2": r2, "cv_r2": cv_r2, "n": int(len(data))}
    return result


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
    FACTS.set("cov.n_total", len(df_full), "{:d}", note="total players in unified table")
    FACTS.set("cov.n_qualified", len(qual), "{:d}", note=f"qualified players (>= {MIN_MINUTES_QUALIFIER} min)")
    FACTS.set("cov.n_systems", len(present), "{:d}", note="rating systems present in data")
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
        FACTS.set(f"dist.{s}.mean", float(vals.mean()), "{:.2f}", note=f"{SYSTEM_LABELS.get(s, s)} mean")
        FACTS.set(f"dist.{s}.median", float(np.median(vals)), "{:.2f}", note=f"{SYSTEM_LABELS.get(s, s)} median")
        FACTS.set(f"dist.{s}.std", float(vals.std()), "{:.2f}", note=f"{SYSTEM_LABELS.get(s, s)} std dev")
        FACTS.set(f"dist.{s}.min", float(vals.min()), "{:.2f}", note=f"{SYSTEM_LABELS.get(s, s)} min")
        FACTS.set(f"dist.{s}.max", float(vals.max()), "{:.2f}", note=f"{SYSTEM_LABELS.get(s, s)} max")
        FACTS.set(f"dist.{s}.gini", float(_gini(vals)), "{:.3f}", note=f"{SYSTEM_LABELS.get(s, s)} Gini coefficient")
        FACTS.set(f"dist.{s}.top5pct", float(_top_share(vals) * 100), "{:.1f}", unit="%",
                  note=f"{SYSTEM_LABELS.get(s, s)} top-5% share of total value")
    # Guard: VORP concentrates value more steeply than Win Shares and PER
    if "VORP" in qual.columns and "WS" in qual.columns:
        _vorp_top5 = _top_share(qual["VORP"].dropna().values, 0.05)
        _ws_top5 = _top_share(qual["WS"].dropna().values, 0.05)
        FACTS.guard("vorp_more_concentrated_than_ws", _vorp_top5 > _ws_top5,
                    "VORP concentrates value more steeply than Win Shares", _vorp_top5)
    if "VORP" in qual.columns and "PER" in qual.columns:
        _vorp_top5 = _top_share(qual["VORP"].dropna().values, 0.05)
        _per_top5 = _top_share(qual["PER"].dropna().values, 0.05)
        FACTS.guard("vorp_more_concentrated_than_per", _vorp_top5 > _per_top5,
                    "VORP top-5% share far exceeds PER", _vorp_top5)

    header("POWER-LAW FIT (VALUE VS RANK, LOG-LOG)")
    print(f"A system's top-{50} value-vs-rank curve is a power law when the")
    print(f"log-log fit clears R^2 >= {POWERLAW_R2_THRESHOLD:.2f} (a straight line on log-log axes).")
    power_law_systems = []
    for s in present:
        vals = qual[s].dropna().sort_values(ascending=False).values
        fit = powerlaw_fit(vals, top_n=50)
        if fit is None:
            continue
        is_power = fit["r2"] >= POWERLAW_R2_THRESHOLD
        verdict = "power law" if is_power else "not a power law (bends)"
        print(f"\n{SYSTEM_LABELS.get(s, s)} (n={fit['n_points']} positive ranks):")
        print(f"  exponent alpha={fit['alpha']:.2f}  R^2={fit['r2']:.3f}  -> {verdict}")
        FACTS.set(f"powerlaw.{s}.alpha", fit["alpha"], "{:.2f}",
                  note=f"{SYSTEM_LABELS.get(s, s)} power-law exponent (value ~ rank^-alpha)")
        FACTS.set(f"powerlaw.{s}.r2", fit["r2"], "{:.2f}",
                  note=f"{SYSTEM_LABELS.get(s, s)} log-log power-law fit R^2")
        if is_power:
            power_law_systems.append(s)
    non_power = [s for s in present
                 if powerlaw_fit(qual[s].dropna().sort_values(ascending=False).values, top_n=50)
                 is not None and s not in power_law_systems]
    label_list = ", ".join(SYSTEM_LABELS.get(s, s) for s in power_law_systems) or "none"
    non_list = ", ".join(SYSTEM_LABELS.get(s, s) for s in non_power) or "none"
    print(f"\nPower-law systems (R^2 >= {POWERLAW_R2_THRESHOLD:.2f}): {label_list}")
    print(f"Bend instead of a straight line: {non_list}")
    FACTS.set("powerlaw.n_systems", len(power_law_systems), "{:d}",
              note="systems whose value-vs-rank curve fits a power law")
    FACTS.set("powerlaw.systems", label_list,
              note="names of systems whose value-vs-rank curve fits a power law")
    FACTS.set("powerlaw.non_systems", non_list,
              note="names of systems whose value-vs-rank curve bends (not a power law)")
    # Guards protecting the findings discussion of which cluster is which.
    _alpha = {s: powerlaw_fit(qual[s].dropna().sort_values(ascending=False).values, top_n=50)
              for s in present}
    if _alpha.get("VORP") and _alpha.get("PER"):
        FACTS.guard("cumulative_steeper_than_rate",
                    _alpha["VORP"]["alpha"] > _alpha["PER"]["alpha"],
                    "cumulative VORP falls off more steeply than rate-metric PER",
                    _alpha["VORP"]["alpha"] - _alpha["PER"]["alpha"])
    if "WS" in power_law_systems and "VORP" in power_law_systems:
        FACTS.guard("cumulative_are_power_laws", True,
                    "the cumulative metrics (Win Shares, VORP) are power laws", non_list)
    if _alpha.get("OBPM"):
        FACTS.guard("obpm_bends", "OBPM" not in power_law_systems,
                    "Offensive BPM bends rather than holding a straight power law",
                    _alpha["OBPM"]["r2"])

    header("RANK AGREEMENT (SPEARMAN CORRELATIONS)")
    if len(present) >= 2:
        ranks = qual[present].rank(pct=True)
        corr = ranks.corr(method="spearman")
        # Guards for key pairs cited in prose
        if "BPM" in corr.index and "VORP" in corr.index:
            bpm_vorp_r = float(corr.loc["BPM", "VORP"])
            FACTS.guard("bpm_vorp_tight", bpm_vorp_r > 0.95,
                        "BPM and VORP are tightly linked (r > 0.95)", bpm_vorp_r)
        if "GAME_SCORE" in corr.index and "PER" in corr.index:
            gs_per_r = float(corr.loc["GAME_SCORE", "PER"])
            FACTS.guard("per_gamescore_close", gs_per_r > 0.75,
                        "PER and Game Score track closely (r > 0.75)", gs_per_r)
        # Print upper triangle and register all correlation facts
        for i, si in enumerate(present):
            for j, sj in enumerate(present):
                if j > i:
                    r = corr.loc[si, sj]
                    label_i = SYSTEM_LABELS.get(si, si)
                    label_j = SYSTEM_LABELS.get(sj, sj)
                    print(f"  {label_i} vs {label_j}: r={r:.3f}")
                    FACTS.set(f"corr.{si}_{sj}", float(r), "{:.3f}",
                              note=f"Spearman rank corr: {label_i} vs {label_j}")

    header("WHAT EACH SYSTEM UNIQUELY CAPTURES")
    uniq = _unique_r2(qual, present)
    for s, r2 in sorted(uniq.items(), key=lambda x: -x[1]):
        print(f"  {SYSTEM_LABELS.get(s, s)}: unique R² = {r2:.3f}")
        FACTS.set(f"uniq.{s}.r2", float(r2), "{:.3f}",
                  note=f"{SYSTEM_LABELS.get(s, s)} unique R²: variance beyond what other systems explain")

    header("CONSENSUS RATING — TOP 20")
    qual["CONSENSUS"] = _build_consensus(qual, present)
    if qual["CONSENSUS"].notna().sum() > 0:
        top = qual.nlargest(20, "CONSENSUS")
        for rank, (_, row) in enumerate(top.iterrows(), 1):
            name = row.get("PLAYER_NAME", "Unknown")
            print(f"  {rank:>2}. {name:<30}  Consensus z = {row['CONSENSUS']:.2f}")
            if rank <= 5:
                FACTS.set(f"consensus.top.{rank}.name", str(name),
                          note=f"consensus rank {rank} player name")
                FACTS.set(f"consensus.top.{rank}.z", float(row["CONSENSUS"]), "{:.2f}",
                          note=f"consensus rank {rank} z-score")
        top_name = top.iloc[0].get("PLAYER_NAME", "") if len(top) > 0 else ""
        FACTS.guard("jokic_tops_consensus", top_name == "Nikola Jokić",
                    "Nikola Jokić tops the consensus rating", top_name)

    header("WINS-PREDICTIVE RATING — TOP 20")
    qual["WINS_PRED"] = _build_wins_predictive(qual, present)
    df_full["WINS_PRED"] = np.nan
    if qual["WINS_PRED"].notna().sum() > 0:
        top = qual.nlargest(20, "WINS_PRED")
        for rank, (_, row) in enumerate(top.iterrows(), 1):
            name = row.get("PLAYER_NAME", "Unknown")
            print(f"  {rank:>2}. {name:<30}  Wins-predictive z = {row['WINS_PRED']:.2f}")
            if rank <= 5:
                FACTS.set(f"wins_pred.top.{rank}.name", str(name),
                          note=f"wins-predictive rank {rank} player name")
                FACTS.set(f"wins_pred.top.{rank}.z", float(row["WINS_PRED"]), "{:.2f}",
                          note=f"wins-predictive rank {rank} z-score")

    header("COMPARISON: CONSENSUS vs. WINS-PREDICTIVE")
    if qual["CONSENSUS"].notna().sum() > 0 and qual["WINS_PRED"].notna().sum() > 0:
        both = qual[["PLAYER_NAME", "CONSENSUS", "WINS_PRED", "MIN"]].dropna()
        if len(both) >= 10:
            r, p = stats.spearmanr(both["CONSENSUS"], both["WINS_PRED"])
            print(f"  Spearman correlation between consensus and wins-predictive: {r:.3f} (p={p:.3f})")
            FACTS.set("cmp.spearman", float(r), "{:.3f}",
                      note="Spearman rank corr between consensus and wins-predictive ratings")
            FACTS.guard("strong_consensus_wins_corr", float(r) > 0.95,
                        "the two ratings agree very closely (r > 0.95)", float(r))
            both["_diff"] = both["WINS_PRED"] - both["CONSENSUS"]
            print("  Players rated much higher by wins-predictive than consensus:")
            for idx, (_, row) in enumerate(both.nlargest(5, "_diff").iterrows(), 1):
                print(f"    {row['PLAYER_NAME']:<30}  diff = +{row['_diff']:.2f}")
                FACTS.set(f"cmp.higher.{idx}.name", str(row["PLAYER_NAME"]),
                          note=f"rank {idx} player rated higher by wins-predictive than consensus")
                FACTS.set(f"cmp.higher.{idx}.diff", float(row["_diff"]), "{:.2f}",
                          note=f"rank {idx} wins-predictive minus consensus diff (positive)")
            print("  Players rated much lower by wins-predictive than consensus:")
            for idx, (_, row) in enumerate(both.nsmallest(5, "_diff").iterrows(), 1):
                print(f"    {row['PLAYER_NAME']:<30}  diff = {row['_diff']:.2f}")
                FACTS.set(f"cmp.lower.{idx}.name", str(row["PLAYER_NAME"]),
                          note=f"rank {idx} player rated lower by wins-predictive than consensus")
                FACTS.set(f"cmp.lower.{idx}.diff", float(row["_diff"]), "{:.2f}",
                          note=f"rank {idx} wins-predictive minus consensus diff (negative)")

    header("UBER RATING CONCENTRATION (GINI vs CENTER-ROBUST STEEPNESS)")
    print("Gini clips negatives to zero, so it inflates 0-centered metrics (the uber")
    print("ratings and the BPM family). The power-law exponent alpha does not depend on")
    print("where zero sits, so it is the fair cross-system concentration read.")
    for s in ("CONSENSUS", "WINS_PRED"):
        if s not in qual.columns or qual[s].notna().sum() < 20:
            continue
        vals = qual[s].dropna().values
        g = _gini(vals)
        t5 = _top_share(vals) * 100
        fit = powerlaw_fit(np.sort(vals)[::-1], top_n=50)
        a = fit["alpha"] if fit else float("nan")
        print(f"\n{SYSTEM_LABELS.get(s, s)}: Gini={g:.3f} (inflated), "
              f"top-5% share={t5:.1f}%, alpha={a:.2f}")
        FACTS.set(f"dist.{s}.gini", float(g), "{:.3f}",
                  note=f"{SYSTEM_LABELS.get(s, s)} Gini coefficient (inflated by centering)")
        FACTS.set(f"dist.{s}.top5pct", float(t5), "{:.1f}", unit="%",
                  note=f"{SYSTEM_LABELS.get(s, s)} top-5% share of positive value")
        if fit:
            FACTS.set(f"powerlaw.{s}.alpha", float(a), "{:.2f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} power-law exponent (center-robust steepness)")
    # Guard: on the center-robust measure the combined ratings sit between the
    # flattest rate metric (PER) and the steepest cumulative metric (VORP).
    _cons = powerlaw_fit(np.sort(qual["CONSENSUS"].dropna().values)[::-1], top_n=50) \
        if "CONSENSUS" in qual.columns and qual["CONSENSUS"].notna().sum() >= 20 else None
    if _cons and _alpha.get("PER") and _alpha.get("VORP"):
        FACTS.guard("uber_concentration_between_rate_and_cumulative",
                    _alpha["PER"]["alpha"] < _cons["alpha"] < _alpha["VORP"]["alpha"],
                    "by center-robust steepness the consensus rating sits between PER and VORP",
                    _cons["alpha"])

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
                FACTS.set(f"tail.{s}.skew", skew, "{:.2f}",
                          note=f"{SYSTEM_LABELS.get(s, s)} skewness (positive values only)")

    header("WHO EACH SYSTEM LOVES vs. CONSENSUS")
    qual["CONSENSUS"] = _build_consensus(qual, present)
    for s in present[:8]:  # top 8 systems only to keep output manageable
        z_s = (qual[s] - qual[s].mean()) / qual[s].std() if qual[s].std() > 0 else 0
        residual = z_s - qual["CONSENSUS"]
        top3 = qual.assign(_res=residual).nlargest(3, "_res")
        bot3 = qual.assign(_res=residual).nsmallest(3, "_res")
        print(f"\n{SYSTEM_LABELS.get(s, s)} loves (vs. consensus):")
        for rank, (_, row) in enumerate(top3.iterrows(), 1):
            print(f"  +{row.get('_res', 0):.2f}  {row.get('PLAYER_NAME', '?')}")
            FACTS.set(f"loves.{s}.{rank}.name", str(row.get("PLAYER_NAME", "?")),
                      note=f"{SYSTEM_LABELS.get(s, s)} loves rank {rank} player vs consensus")
            FACTS.set(f"loves.{s}.{rank}.diff", float(row.get("_res", 0)), "{:.2f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} loves rank {rank} residual vs consensus (positive)")
        print(f"{SYSTEM_LABELS.get(s, s)} discounts (vs. consensus):")
        for rank, (_, row) in enumerate(bot3.iterrows(), 1):
            print(f"  {row.get('_res', 0):.2f}  {row.get('PLAYER_NAME', '?')}")
            FACTS.set(f"discounts.{s}.{rank}.name", str(row.get("PLAYER_NAME", "?")),
                      note=f"{SYSTEM_LABELS.get(s, s)} discounts rank {rank} player vs consensus")
            FACTS.set(f"discounts.{s}.{rank}.diff", float(row.get("_res", 0)), "{:.2f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} discounts rank {rank} residual vs consensus (negative)")

    header("RETRODICTION: WHICH RATING REBUILDS TEAM RESULTS")
    print("Each system's player ratings are minutes-weighted to the team level, then")
    print("fit to team point differential per game across the 30 teams. R² is the")
    print("in-sample fit; CV R² is leave-one-team-out (the honest out-of-sample read).")
    print("Systems marked [team-fit] are built using team or lineup point")
    print("differential, so a high score is partly mechanical. Systems marked")
    print("[outcome-blind] never saw who won; their score is the genuine test.")
    outcomes = load_team_outcomes(end_year)
    retro = retrodiction_scores(df_full, outcomes, present, target="point_diff")
    if retro:
        ranked = sorted(retro.items(), key=lambda kv: -kv[1]["cv_r2"])
        print()
        for s, sc in ranked:
            tag = "[team-fit]    " if s in OUTCOME_CALIBRATED else "[outcome-blind]"
            print(f"  {tag} {SYSTEM_LABELS.get(s, s):<14} "
                  f"R²={sc['r2']:.3f}  CV R²={sc['cv_r2']:.3f}")
            FACTS.set(f"retro.{s}.r2", sc["r2"], "{:.3f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} team point-diff retrodiction R² (in-sample)")
            FACTS.set(f"retro.{s}.cv_r2", sc["cv_r2"], "{:.3f}",
                      note=f"{SYSTEM_LABELS.get(s, s)} retrodiction R² (leave-one-team-out CV)")

        top_sys, top_sc = ranked[0]
        top_label = SYSTEM_LABELS.get(top_sys, top_sys)
        print(f"\nTop retrodictor: {top_label} (CV R²={top_sc['cv_r2']:.3f}); it "
              f"rebuilds {top_sc['cv_r2'] * 100:.0f}% of the team point-differential")
        print("spread out of sample.")
        FACTS.set("retro.top.name", str(top_label),
                  note="system that best retrodicts team point differential (CV)")
        FACTS.set("retro.top.cv_r2", float(top_sc["cv_r2"]), "{:.3f}",
                  note="top system's leave-one-team-out retrodiction R²")
        FACTS.set("retro.top.cv_r2_pct", float(top_sc["cv_r2"] * 100), "{:.0f}",
                  note="top system's retrodiction R² as a percent (append % in prose)")
        if top_sys not in OUTCOME_CALIBRATED:
            print(f"{top_label} never uses who won, yet it beats the team-adjusted box")
            print("metrics (BPM, VORP, Win Shares) here. Caveat: this project's BPM and")
            print("VORP are approximate recomputes, so their lower scores partly reflect a")
            print("noisy recompute, not proof PER is the better rating. Rerun once exactly")
            print("computed or published impact metrics (EPM, DARKO, RAPTOR) are loaded.")
        FACTS.guard("blind_rating_tops_retrodiction",
                    top_sys not in OUTCOME_CALIBRATED,
                    "an outcome-blind box rating tops the team point-differential "
                    "retrodiction, ahead of the team-adjusted metrics",
                    top_label)

    header("REGULAR SEASON vs PLAYOFFS (RATE-METRIC DELTAS)")
    deltas = load_playoff_deltas(end_year)
    if deltas.empty:
        print("  No playoff data available for this season — section skipped.")
    else:
        n_qual = len(deltas)
        metric_list = ", ".join(SYSTEM_LABELS.get(m, m) for m in PLAYOFF_DELTA_METRICS)
        print(f"Players with >= {MIN_PLAYOFF_MINUTES} playoff minutes: {n_qual}")
        print(f"Rate metrics compared (each normalized within its season type): {metric_list}")
        print("Delta = playoff minus regular season. 'adj' subtracts the average delta")
        print("among this qualified pool, so a riser is measured against the other")
        print("rotation players who also advanced. The composite shift z averages the")
        print("standardized adjusted deltas of PER, WS/48, and BPM, so a riser needs the")
        print("three box formulations to agree.")
        print("Note: this project's BPM scale is approximate; the rankings carry the")
        print("signal, not the raw BPM points.")
        FACTS.set("playoff.n_qualified", n_qual, "{:d}",
                  note=f"players with >= {MIN_PLAYOFF_MINUTES} playoff minutes")
        FACTS.set("playoff.min_floor", MIN_PLAYOFF_MINUTES, "{:d}",
                  note="minimum playoff minutes to enter the riser/faller pool")

        risers = deltas.nlargest(10, "SHIFT_Z")
        fallers = deltas.nsmallest(10, "SHIFT_Z")

        def _line(rank, row):
            # PER is the one metric on a trustworthy real scale (normalized to a
            # league average of 15), shown alongside the composite z.
            return (f"  {rank:>2}. {row['PLAYER_NAME']:<26} "
                    f"{row.get('TEAM_ABBREVIATION', ''):>3}  "
                    f"shift z = {row['SHIFT_Z']:+.2f}  "
                    f"(PER {row['PER_delta_adj']:+.1f} vs regular season)")

        print("\nBiggest playoff RISERS (raised their level above their regular-season form):")
        for rank, (_, row) in enumerate(risers.iterrows(), 1):
            print(_line(rank, row))
            if rank <= 3:
                FACTS.set(f"playoff.riser.{rank}.name", str(row["PLAYER_NAME"]),
                          note=f"playoff riser rank {rank} (composite shift)")
                FACTS.set(f"playoff.riser.{rank}.z", float(row["SHIFT_Z"]), "{:.2f}",
                          note=f"playoff riser rank {rank} composite shift z")

        print("\nBiggest playoff FALLERS (dropped below their regular-season form):")
        for rank, (_, row) in enumerate(fallers.iterrows(), 1):
            print(_line(rank, row))
            if rank <= 3:
                FACTS.set(f"playoff.faller.{rank}.name", str(row["PLAYER_NAME"]),
                          note=f"playoff faller rank {rank} (composite shift)")
                FACTS.set(f"playoff.faller.{rank}.z", float(row["SHIFT_Z"]), "{:.2f}",
                          note=f"playoff faller rank {rank} composite shift z")

        top_riser = str(risers.iloc[0]["PLAYER_NAME"])
        top_faller = str(fallers.iloc[0]["PLAYER_NAME"])
        FACTS.guard("playoff_top_riser_positive",
                    float(risers.iloc[0]["SHIFT_Z"]) > 0,
                    f"the top playoff riser ({top_riser}) gained on the pool", top_riser)
        FACTS.guard("playoff_top_faller_negative",
                    float(fallers.iloc[0]["SHIFT_Z"]) < 0,
                    f"the top playoff faller ({top_faller}) lost ground on the pool", top_faller)

        # Did the regular-season consensus #1 hold up in the playoffs?
        if "CONSENSUS" in qual.columns and qual["CONSENSUS"].notna().sum() > 0:
            cons_top = str(qual.nlargest(1, "CONSENSUS")["PLAYER_NAME"].iloc[0])
            match = deltas[deltas["PLAYER_NAME"] == cons_top]
            if not match.empty:
                z = float(match.iloc[0]["SHIFT_Z"])
                order = deltas.sort_values("SHIFT_Z").reset_index(drop=True)
                frank = int(order.index[order["PLAYER_NAME"] == cons_top][0]) + 1
                print(f"\nRegular-season consensus #1 {cons_top}: playoff shift "
                      f"z = {z:+.2f} (faller rank {frank} of {len(deltas)})")
                FACTS.set("playoff.consensus1.name", cons_top,
                          note="regular-season consensus #1 player (playoff shift lookup)")
                FACTS.set("playoff.consensus1.z", z, "{:.2f}",
                          note="regular-season consensus #1 player's composite playoff shift z")
                FACTS.guard("consensus_top_fell_in_playoffs", z < 0,
                            f"the regular-season consensus #1 ({cons_top}) fell in the playoffs", z)

    # Dump all facts and guards to docs/ (+ the dev facts-reference lookup table)
    FACTS.dump(_FACTS_PATH)
    FACTS.dump_guards(_GUARDS_PATH)
    from render_docs import write_reference
    print(f"Saved → {write_reference()}")
