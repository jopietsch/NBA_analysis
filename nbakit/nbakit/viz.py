"""
nbakit.viz — shared matplotlib styling for NBA analysis charts.

A common palette plus small drawing helpers (output paths, axis styling,
figure creation, bar annotation, trend lines) so every question's plots module
shares one look. Question-specific accent colors (team colors, era shades) stay
local to each plots module.
"""

import os

import numpy as np
import matplotlib.pyplot as plt


# ── Palette ─────────────────────────────────────────────────────────────────────
BLUE  = "#378add"
GREEN = "#1d9e75"
RED   = "#e24b4a"
GRAY  = "#888780"
LGRAY = "#cccccc"
BG    = "#f9f9f7"   # figure background
PANEL = "#ffffff"   # axes background


# ── Output paths ─────────────────────────────────────────────────────────────────

def output_path(name: str, output_dir: str) -> str:
    """Path for a chart file under output_dir, creating the directory."""
    os.makedirs(output_dir, exist_ok=True)
    return os.path.join(output_dir, name)


def save_chart(name: str, output_dir: str, *, fig=None,
               facecolor: str = BG, close: bool = True) -> str:
    """Save a chart as SVG under output_dir and print the path.

    Renders label text as vector paths (``svg.fonttype='path'``) so it carries
    into the Typst/PDF build with no font dependency, on the shared off-white
    background with a tight bounding box. Saves the current figure unless ``fig``
    is given. Returns the saved path.
    """
    plt.rcParams["svg.fonttype"] = "path"
    path = output_path(name, output_dir)
    (fig or plt).savefig(path, bbox_inches="tight", facecolor=facecolor)
    print(f"Saved → {path}")
    if close:
        plt.close(fig) if fig is not None else plt.close()
    return path


# ── Axis / figure styling ────────────────────────────────────────────────────────

def style_axes(ax: plt.Axes) -> None:
    """Apply the shared panel look: white panel, soft spines, x-grid."""
    ax.set_facecolor(PANEL)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#ddd")
    ax.spines["bottom"].set_color("#ddd")
    ax.tick_params(colors="#555")
    ax.grid(axis="x", color="#e0dfd8", linewidth=0.7, zorder=0)


def new_fig(figsize=(9, 6)):
    """A figure + single axes with the shared background color."""
    fig, ax = plt.subplots(figsize=figsize, facecolor=BG)
    return fig, ax


# ── Drawing helpers ──────────────────────────────────────────────────────────────

def annotate_bars(ax: plt.Axes, bars, color: str,
                  fmt: str = "{:.1f}%", offset: float = 0.3) -> None:
    """Label each bar with its height, centered just above the bar."""
    for bar in bars:
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + offset,
                fmt.format(bar.get_height()),
                ha="center", va="bottom", fontsize=7.5, color=color)


def add_trend_line(
    ax: plt.Axes,
    x: np.ndarray,
    y: np.ndarray,
    color: str,
    *,
    linestyle: str = "--",
    linewidth: float = 1.4,
    alpha: float = 0.5,
    zorder: int = 3,
    x_plot: np.ndarray | None = None,
) -> None:
    """Fit and draw a least-squares line; skips if fewer than 2 finite points."""
    mask = ~np.isnan(y)
    if mask.sum() < 2:
        return
    z = np.polyfit(x[mask], y[mask], 1)
    xp = x if x_plot is None else x_plot
    ax.plot(xp, np.poly1d(z)(xp), linestyle, color=color,
            linewidth=linewidth, alpha=alpha, zorder=zorder)
