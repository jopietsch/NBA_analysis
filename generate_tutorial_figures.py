"""Teaching figures for STATS_TUTORIAL.md.

Standalone and pedagogical — deliberately NOT part of the analysis pipeline in
nba_home_court_advantage.py. These illustrate statistical *concepts*; some use
real numbers lifted from RESULTS.md, others are schematic. Run directly:

    MPLBACKEND=Agg python3 generate_tutorial_figures.py
"""

import os

import numpy as np
import matplotlib.pyplot as plt

DPI = 120
OUTPUT_DIR = "generated"


def _output_path(name: str) -> str:
    """Return the path under OUTPUT_DIR for a figure file, creating the dir."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    return os.path.join(OUTPUT_DIR, name)


def logistic_curve():
    """§2.1 / §2.2 — log-odds map to probability via the S-curve."""
    z = np.linspace(-4.5, 4.5, 500)
    p = 1.0 / (1.0 + np.exp(-z))

    fig, ax = plt.subplots(figsize=(7.5, 4.6))
    ax.plot(z, p, color="#1f77b4", lw=2.5)

    # Coin-flip reference lines.
    ax.axhline(0.5, color="grey", ls=":", lw=1)
    ax.axvline(0.0, color="grey", ls=":", lw=1)

    # The real home-win point: log-odds +0.418 -> p = 0.603.
    z0, p0 = 0.418, 0.603
    ax.plot([z0], [p0], "o", color="#d62728", ms=9, zorder=5)
    ax.annotate(
        "NBA home win\nlog-odds +0.42  →  60.3%",
        xy=(z0, p0), xytext=(1.3, 0.42),
        arrowprops=dict(arrowstyle="->", color="#d62728"),
        fontsize=10, color="#d62728",
    )

    # Equal log-odds steps -> unequal probability steps (squeezing in the tails).
    for zc in (0.0, 2.5):
        pa = 1 / (1 + np.exp(-zc))
        pb = 1 / (1 + np.exp(-(zc + 1.0)))
        ax.annotate(
            "", xy=(zc + 1.0, pb), xytext=(zc, pa),
            arrowprops=dict(arrowstyle="-", color="#2ca02c", lw=6, alpha=0.35),
        )
        ax.text(zc + 0.5, (pa + pb) / 2 - 0.06,
                f"+1 log-odds\n= +{(pb - pa) * 100:.0f} pp",
                fontsize=8.5, color="#2ca02c", ha="center")

    ax.set_xlabel("log-odds  (the modeling scale — 0 = coin flip)")
    ax.set_ylabel("P(home win)")
    ax.set_title("Logistic regression models a straight line in log-odds,\n"
                 "then bends it into a valid 0–1 probability", fontsize=11)
    ax.set_ylim(-0.02, 1.02)
    ax.text(-4.3, 0.55, "favors\nroad", fontsize=8.5, color="grey")
    ax.text(3.6, 0.30, "favors\nhome", fontsize=8.5, color="grey")
    fig.tight_layout()
    fig.savefig(_output_path("tutorial_logistic_curve.png"), dpi=DPI)
    plt.close(fig)


def shrinkage():
    """§6.1 / §6.2 — empirical-Bayes shrinkage pulls noisy estimates to the mean."""
    league_mean = 20.2
    true_sd = 4.1
    true_var = true_sd ** 2

    # (name, raw HCA, 95% CI half-width) — real regular-season values from RESULTS.md.
    teams = [
        ("Kansas City Kings\n(82 games)", 35.4, 14.1),
        ("Denver Nuggets\n(1,689 games)", 28.5, 3.2),
        ("Washington Bullets\n(574 games)", 26.5, 5.5),
        ("Boston Celtics\n(1,687 games)", 18.4, 3.3),
        ("Vancouver Grizzlies\n(230 games)", 13.5, 7.5),
        ("Brooklyn Nets\n(523 games)", 9.6, 6.0),
    ]

    fig, ax = plt.subplots(figsize=(8.2, 5.0))
    ys = np.arange(len(teams))[::-1]

    for y, (name, raw, ci) in zip(ys, teams):
        se = ci / 1.96
        sampling_var = se ** 2
        weight = true_var / (true_var + sampling_var)
        shrunk = league_mean + weight * (raw - league_mean)

        # Raw estimate with its 95% CI (wide CI = noisy = small sample).
        ax.errorbar(raw, y, xerr=ci, fmt="o", color="#1f77b4",
                    mfc="white", ms=8, capsize=4, lw=1.4, zorder=3)
        # Arrow from raw to shrunken.
        ax.annotate("", xy=(shrunk, y), xytext=(raw, y),
                    arrowprops=dict(arrowstyle="->", color="#d62728", lw=1.6))
        ax.plot([shrunk], [y], "o", color="#d62728", ms=8, zorder=4)
        ax.text(raw + ci + 0.4, y + 0.12,
                f"pull {abs(raw - shrunk):.1f} pp", fontsize=8, color="#d62728")

    ax.axvline(league_mean, color="grey", ls="--", lw=1.2)
    ax.text(league_mean + 0.2, ys[0] + 0.6, f"league mean {league_mean:.1f}",
            fontsize=9, color="grey")
    ax.set_yticks(ys)
    ax.set_yticklabels([t[0] for t in teams], fontsize=8.5)
    ax.set_xlabel("Home-court advantage (home% − road%, pp)")
    ax.set_title("Empirical-Bayes shrinkage: noisy small-sample estimates (wide CIs)\n"
                 "get pulled hard toward the mean; precise ones barely move",
                 fontsize=11)
    ax.set_ylim(-0.8, ys[0] + 1.2)

    # Legend proxies.
    ax.plot([], [], "o", color="#1f77b4", mfc="white", label="raw estimate (± 95% CI)")
    ax.plot([], [], "o", color="#d62728", label="shrunken estimate")
    ax.legend(loc="lower right", fontsize=9, framealpha=0.9)
    fig.tight_layout()
    fig.savefig(_output_path("tutorial_shrinkage.png"), dpi=DPI)
    plt.close(fig)


def quantile_diagnostic():
    """§5.1 — pure level shift vs. genuine polarization."""
    yrs = np.arange(1997, 2026)
    t = yrs - 1997
    # Quantile intercepts (≈ home-margin distribution shape at 1997).
    base = {"Q90": 20.0, "Q75": 9.0, "Q50": 2.5, "Q25": -4.0, "Q10": -13.0}
    # Real regular-season slopes from RESULTS.md.
    real_slope = {"Q90": +0.045, "Q75": -0.000, "Q50": -0.056,
                  "Q25": -0.091, "Q10": -0.154}
    median_slope = -0.056  # left panel: every quantile slides at the median rate
    colors = {"Q90": "#d62728", "Q75": "#ff7f0e", "Q50": "#2ca02c",
              "Q25": "#1f77b4", "Q10": "#9467bd"}

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(11, 4.8), sharey=True)

    for q in base:
        axL.plot(yrs, base[q] + median_slope * t, color=colors[q], lw=2)
        axR.plot(yrs, base[q] + real_slope[q] * t, color=colors[q], lw=2,
                 label=f"{q}  ({real_slope[q]:+.3f}/yr)")
        axL.text(yrs[-1] + 0.3, base[q] + median_slope * t[-1], q,
                 fontsize=8.5, color=colors[q], va="center")

    for ax in (axL, axR):
        ax.axhline(0, color="grey", ls=":", lw=1)
        ax.set_xlabel("season")
    axL.set_ylabel("home margin (pts)")
    axL.set_title("HYPOTHETICAL: pure level shift\n"
                  "all quantiles slide in parallel → shape unchanged", fontsize=10.5)
    axR.set_title("ACTUAL DATA: polarization\n"
                  "Q10 falls while Q90 rises → distribution widens", fontsize=10.5)
    axR.legend(loc="center left", fontsize=8, title="real slope", title_fontsize=8.5)
    # Spread annotation on the right panel.
    axR.annotate("", xy=(yrs[-1], base["Q90"] + real_slope["Q90"] * t[-1]),
                 xytext=(yrs[-1], base["Q10"] + real_slope["Q10"] * t[-1]),
                 arrowprops=dict(arrowstyle="<->", color="black", lw=1.2))
    axR.text(yrs[-1] - 6, 4, "Q90−Q10 spread\ngrows +0.20 pts/yr", fontsize=8.5)
    fig.tight_layout()
    fig.savefig(_output_path("tutorial_quantile_diagnostic.png"), dpi=DPI)
    plt.close(fig)


def spurious_detrend():
    """§7.2 — two trending series correlate; detrending removes the illusion."""
    rng = np.random.default_rng(7)
    yrs = np.arange(1984, 2026)
    t = yrs - 1984
    n = len(yrs)

    # Series A: 3PA rate rising ~7% -> ~40%.  Series B: HCA falling ~65% -> ~55%.
    a = 7 + 0.80 * t + rng.normal(0, 1.5, n)
    b = 65 - 0.24 * t + rng.normal(0, 1.2, n)  # independent noise -> trend is all the link

    # Detrend each by its own linear year fit; keep residuals.
    a_res = a - np.poly1d(np.polyfit(t, a, 1))(t)
    b_res = b - np.poly1d(np.polyfit(t, b, 1))(t)

    r_raw = np.corrcoef(a, b)[0, 1]
    r_det = np.corrcoef(a_res, b_res)[0, 1]

    fig, (ax1, ax2, ax3) = plt.subplots(1, 3, figsize=(13, 4.3))

    # Panel 1: both series over time (twin axes).
    ax1.plot(yrs, a, color="#1f77b4", lw=2)
    ax1.set_ylabel("3PA rate (%)", color="#1f77b4")
    ax1.tick_params(axis="y", labelcolor="#1f77b4")
    ax1b = ax1.twinx()
    ax1b.plot(yrs, b, color="#d62728", lw=2)
    ax1b.set_ylabel("home win %", color="#d62728")
    ax1b.tick_params(axis="y", labelcolor="#d62728")
    ax1.set_xlabel("season")
    ax1.set_title("Both series just trend over time", fontsize=10.5)

    # Panel 2: raw scatter.
    ax2.scatter(a, b, s=22, color="#555")
    m, c = np.polyfit(a, b, 1)
    xs = np.array([a.min(), a.max()])
    ax2.plot(xs, m * xs + c, color="black", lw=1.5)
    ax2.set_xlabel("3PA rate (%)")
    ax2.set_ylabel("home win %")
    ax2.set_title(f"RAW correlation looks strong\nr = {r_raw:+.2f}", fontsize=10.5)

    # Panel 3: detrended scatter.
    ax3.scatter(a_res, b_res, s=22, color="#555")
    ax3.axhline(0, color="grey", ls=":", lw=1)
    ax3.axvline(0, color="grey", ls=":", lw=1)
    ax3.set_xlabel("3PA rate (detrended)")
    ax3.set_ylabel("home win % (detrended)")
    ax3.set_title(f"DETRENDED: the link evaporates\nr = {r_det:+.2f}", fontsize=10.5)

    fig.suptitle("Two series that both drift over 40 years will correlate — "
                 "until you remove the shared trend", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(_output_path("tutorial_spurious_detrend.png"), dpi=DPI)
    plt.close(fig)


def main():
    logistic_curve()
    shrinkage()
    quantile_diagnostic()
    spurious_detrend()
    print(f"Wrote to {OUTPUT_DIR}/: tutorial_logistic_curve.png, tutorial_shrinkage.png, "
          "tutorial_quantile_diagnostic.png, tutorial_spurious_detrend.png")


if __name__ == "__main__":
    main()
