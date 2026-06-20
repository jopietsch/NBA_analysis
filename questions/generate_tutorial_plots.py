#!/usr/bin/env python3
"""Generate illustrative tutorial diagrams for stats_tutorial.md."""

import numpy as np
import matplotlib.pyplot as plt
import os

OUT = "generated/images"
os.makedirs(OUT, exist_ok=True)


def save(name):
    plt.tight_layout()
    plt.savefig(f"{OUT}/{name}", dpi=150, bbox_inches="tight")
    plt.close()
    print(f"  {OUT}/{name}")


# ── 1. tutorial_logistic_curve.png ──────────────────────────────────────────
def plot_logistic_curve():
    lo = np.linspace(-4, 4, 400)
    p = 1 / (1 + np.exp(-lo))

    fig, ax = plt.subplots(figsize=(7, 4))
    ax.plot(lo, p, color="#2563eb", lw=2.5)
    ax.axhline(0.5, color="gray", lw=0.8, ls="--")
    ax.axvline(0, color="gray", lw=0.8, ls="--")

    lo_c, lo_r = 0.0, 1.0
    p_c = 1 / (1 + np.exp(-lo_c))
    p_r = 1 / (1 + np.exp(-lo_r))
    ax.annotate(
        f"+1 log-odd ~{(p_r - p_c)*100:.0f} pp near 50/50",
        xy=(lo_r, p_r), xytext=(1.4, 0.42),
        arrowprops=dict(arrowstyle="->", color="#16a34a"),
        color="#16a34a", fontsize=9,
    )
    lo_t, lo_t2 = 3.0, 4.0
    p_t = 1 / (1 + np.exp(-lo_t))
    p_t2 = 1 / (1 + np.exp(-lo_t2))
    ax.annotate(
        f"+1 log-odd ~{(p_t2 - p_t)*100:.0f} pp in the tail",
        xy=(lo_t2, p_t2), xytext=(1.8, 0.92),
        arrowprops=dict(arrowstyle="->", color="#16a34a"),
        color="#16a34a", fontsize=9,
    )

    ax.set_xlabel("Log-odds (favors road  <--  0  -->  favors home)")
    ax.set_ylabel("P(home win)")
    ax.set_title("The Logistic Curve: Log-Odds Map to Probability")
    ax.set_ylim(-0.02, 1.02)
    ax.set_yticks([0, 0.25, 0.50, 0.75, 1.0])
    ax.set_yticklabels(["0%", "25%", "50%", "75%", "100%"])
    save("tutorial_logistic_curve.png")


# ── 2. tutorial_quantile_diagnostic.png ─────────────────────────────────────
def plot_quantile_diagnostic():
    years = np.arange(1980, 2024)
    n = len(years)
    t = np.linspace(0, 1, n)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4), sharey=True)

    base = 6 - 2.5 * t
    ax = axes[0]
    for q, label, color in [
        (2.5,  "Q90", "#2563eb"),
        (0.0,  "Q50", "#059669"),
        (-2.5, "Q10", "#dc2626"),
    ]:
        ax.plot(years, base + q, color=color, lw=1.8, label=label)
    ax.set_title("Pure Level Shift\n(parallel -- only the mean moved)")
    ax.set_xlabel("Season")
    ax.set_ylabel("Home margin (pts)")
    ax.legend(fontsize=9)

    ax = axes[1]
    q90 = 3.5 + 1.5 * t
    q50 = 6.5 - 2.5 * t
    q10 = 2.5 - 5.0 * t
    for series, label, color in [
        (q90, "Q90", "#2563eb"),
        (q50, "Q50", "#059669"),
        (q10, "Q10", "#dc2626"),
    ]:
        ax.plot(years, series, color=color, lw=1.8, label=label)
    ax.fill_between(years, q10, q90, alpha=0.08, color="#6366f1")
    ax.set_title("Genuine Polarization\n(lines fan apart)")
    ax.set_xlabel("Season")
    ax.legend(fontsize=9)

    fig.suptitle("Quantile Regression Diagnostics", fontsize=12, y=1.01)
    save("tutorial_quantile_diagnostic.png")


# ── 3. tutorial_shrinkage.png ────────────────────────────────────────────────
def plot_shrinkage():
    league_mean = 20.0
    teams = [
        ("Kansas City Kings", 35.4, 82),
        ("Memphis Grizzlies",  14.3, 410),
        ("Charlotte Hornets",  18.7, 820),
        ("Boston Celtics",     22.1, 1640),
        ("Denver Nuggets",     27.9, 1730),
    ]
    true_var = 4.1 ** 2

    names, raw, shrunken, errors = [], [], [], []
    for team, r, n in teams:
        se = np.sqrt(0.25 / n) * 100
        samp_var = se ** 2
        w = true_var / (true_var + samp_var)
        s = league_mean + w * (r - league_mean)
        names.append(team)
        raw.append(r)
        shrunken.append(s)
        errors.append(se)

    y = np.arange(len(names))
    fig, ax = plt.subplots(figsize=(8, 4))

    ax.errorbar(raw, y, xerr=errors, fmt="o", color="#dc2626",
                label="Raw estimate +/- 1 SE", capsize=4, zorder=3)
    ax.scatter(shrunken, y, color="#2563eb", zorder=4, s=60,
               label="Shrunken estimate")

    for i, (r, s) in enumerate(zip(raw, shrunken)):
        ax.annotate("", xy=(s, i), xytext=(r, i),
                    arrowprops=dict(arrowstyle="->", color="#6366f1", lw=1.5))

    ax.axvline(league_mean, color="gray", ls="--", lw=1,
               label=f"League mean ({league_mean:.0f} pp)")
    ax.set_yticks(y)
    ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("Home court advantage (pp)")
    ax.set_title("Shrinkage Pulls Noisy Estimates Toward the League Mean")
    ax.legend(fontsize=9)
    save("tutorial_shrinkage.png")


# ── 4. tutorial_spurious_detrend.png ────────────────────────────────────────
def plot_spurious_detrend():
    np.random.seed(42)
    n = 43
    t = np.arange(n)
    noise = np.random.randn(n) * 0.15

    hca    = 2.0 - 0.035 * t + noise
    parity = 0.15 + 0.004 * t + np.random.randn(n) * 0.02

    def detrend(x):
        fit = np.polyfit(t, x, 1)
        return x - np.polyval(fit, t)

    hca_d = detrend(hca)
    par_d = detrend(parity)

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))

    ax = axes[0]
    ax2 = ax.twinx()
    ax.plot(1980 + t, hca, color="#2563eb", lw=1.8, label="HCA")
    ax2.plot(1980 + t, parity, color="#dc2626", lw=1.8, ls="--",
             label="Parity index")
    ax.set_title("Two Trending Series")
    ax.set_xlabel("Season")
    ax.set_ylabel("HCA (pp)", color="#2563eb")
    ax2.set_ylabel("Parity index", color="#dc2626")

    ax = axes[1]
    r_raw = np.corrcoef(hca, parity)[0, 1]
    ax.scatter(parity, hca, color="#6366f1", s=20, alpha=0.7)
    m, b = np.polyfit(parity, hca, 1)
    x_fit = np.linspace(parity.min(), parity.max(), 100)
    ax.plot(x_fit, m * x_fit + b, color="#dc2626", lw=1.5)
    ax.set_title(f"Raw correlation: r = {r_raw:.2f}\n(looks strong!)")
    ax.set_xlabel("Parity index")
    ax.set_ylabel("HCA (pp)")

    ax = axes[2]
    r_dt = np.corrcoef(hca_d, par_d)[0, 1]
    ax.scatter(par_d, hca_d, color="#6366f1", s=20, alpha=0.7)
    m2, b2 = np.polyfit(par_d, hca_d, 1)
    x_fit2 = np.linspace(par_d.min(), par_d.max(), 100)
    ax.plot(x_fit2, m2 * x_fit2 + b2, color="#dc2626", lw=1.5)
    ax.set_title(f"After detrending: r = {r_dt:.2f}\n(correlation collapses)")
    ax.set_xlabel("Parity index (detrended)")
    ax.set_ylabel("HCA (detrended)")

    fig.suptitle("Spurious Correlation from a Shared Trend", fontsize=12, y=1.01)
    save("tutorial_spurious_detrend.png")


# ── 5. tutorial_percentile_rank.png ─────────────────────────────────────────
def plot_percentile_rank():
    np.random.seed(7)
    # Illustrative champion win rates, mean ~0.75, range roughly matching reality
    wr = np.array([
        0.615, 0.636, 0.652, 0.667, 0.667, 0.680, 0.692, 0.700,
        0.706, 0.714, 0.720, 0.727, 0.733, 0.739, 0.742, 0.750,
        0.750, 0.750, 0.750, 0.758, 0.762, 0.765, 0.769, 0.773,
        0.778, 0.783, 0.786, 0.789, 0.793, 0.800, 0.800, 0.808,
        0.808, 0.810, 0.813, 0.813, 0.818, 0.824, 0.833, 0.840,
        0.842, 0.875, 0.941,
    ])
    wr.sort()
    knicks_wr = 0.842
    n = len(wr)
    pct = (wr <= knicks_wr).mean() * 100   # 88.4

    y = np.arange(n)
    colors = ["#2563eb" if v == knicks_wr else "#94a3b8" for v in wr]

    fig, axes = plt.subplots(1, 2, figsize=(11, 5),
                             gridspec_kw={"width_ratios": [2, 1]})

    # Left: ranked bar chart
    ax = axes[0]
    ax.barh(y, wr, color=colors, height=0.8)
    knicks_idx = list(wr).index(knicks_wr)
    ax.annotate(
        f"2025-26 Knicks\n{knicks_wr:.3f} | {pct:.0f}th percentile",
        xy=(knicks_wr, knicks_idx), xytext=(0.80, knicks_idx - 6),
        arrowprops=dict(arrowstyle="->", color="#2563eb"),
        color="#2563eb", fontsize=9, fontweight="bold",
    )
    ax.set_yticks([])
    ax.set_xlabel("Playoff win rate")
    ax.set_title("All 43 champions ranked by win rate\n(blue = 2025-26 Knicks)")
    ax.set_xlim(0.57, 0.98)

    # Right: explain the count
    ax = axes[1]
    below = (wr <= knicks_wr).sum()
    ax.bar(["<= Knicks", "> Knicks"], [below, n - below],
           color=["#94a3b8", "#f87171"], edgecolor="white")
    ax.set_title(f"Percentile =\n{below}/{n} = {pct:.0f}th")
    ax.set_ylabel("Number of champions")
    for i, v in enumerate([below, n - below]):
        ax.text(i, v + 0.3, str(v), ha="center", fontsize=11, fontweight="bold")

    fig.suptitle("How Empirical Percentile Rank Works", fontsize=12, y=1.01)
    save("tutorial_percentile_rank.png")


# ── 6. tutorial_srs_intuition.png ───────────────────────────────────────────
def plot_srs_intuition():
    np.random.seed(3)
    n_teams = 8
    names = ["Team A", "Team B", "Team C", "Team D",
             "Team E", "Team F", "Team G", "Team H"]
    true_srs = np.array([8.0, 4.5, 2.0, 0.5, -0.5, -2.0, -4.5, -8.0])
    raw_margins = true_srs + np.random.randn(n_teams) * 0.8

    fig, axes = plt.subplots(1, 2, figsize=(10, 4))

    # Left: raw margin vs SRS
    ax = axes[0]
    y = np.arange(n_teams)[::-1]
    ax.barh(y, raw_margins, color="#94a3b8", height=0.6, label="Raw avg margin")
    ax.barh(y, true_srs, color="#2563eb", height=0.3, label="SRS")
    ax.set_yticks(y)
    ax.set_yticklabels(names)
    ax.axvline(0, color="black", lw=0.8)
    ax.set_xlabel("Points per game")
    ax.set_title("Raw margin vs SRS\n(SRS adjusts for strength of schedule)")
    ax.legend(fontsize=9)

    # Right: SRS identity illustration
    ax = axes[1]
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 6)
    ax.axis("off")
    ax.set_title("The SRS identity")

    lines = [
        "SRS = avg point margin",
        "      + schedule adjustment",
        "",
        "SRS +8: beats avg opponent by 8 pts",
        "SRS  0: exactly average",
        "SRS -5: loses to avg opponent by 5 pts",
        "",
        "Sum of all SRS = 0 (zero-sum league)",
    ]
    for i, line in enumerate(lines):
        ax.text(0.5, 5.2 - i * 0.65, line, fontsize=10,
                family="monospace" if line.startswith(" ") else "sans-serif",
                color="#1e293b" if line else "white")

    fig.suptitle("SRS (Simple Rating System) Intuition", fontsize=12, y=1.01)
    save("tutorial_srs_intuition.png")


if __name__ == "__main__":
    print("Generating tutorial diagrams...")
    plot_logistic_curve()
    plot_quantile_diagnostic()
    plot_shrinkage()
    plot_spurious_detrend()
    plot_percentile_rank()
    plot_srs_intuition()
    print("Done.")
