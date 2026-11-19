"""Figures of the pilot. Static images for the documentation and the paper."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

# Palette: two categorical slots validated together for colour-vision deficiencies
# (blue and orange), on a light surface, with recessive grid and axes.
FLARES = "#2a78d6"
CONTROLS = "#eb6834"
SURFACE = "#fcfcfb"
INK = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
AXIS = "#c3c2b7"
EARTH_SIGNAL_MS = 0.09  # reflex velocity of the Sun due to the Earth


def style() -> dict:
    return {
        "font.family": ["Segoe UI", "DejaVu Sans"],
        "font.size": 10,
        "figure.facecolor": SURFACE,
        "axes.facecolor": SURFACE,
        "savefig.facecolor": SURFACE,
        "axes.edgecolor": AXIS,
        "axes.linewidth": 1.0,
        "axes.labelcolor": INK_SECONDARY,
        "axes.titlecolor": INK,
        "axes.titlesize": 10.5,
        "axes.titleweight": "semibold",
        "axes.titlelocation": "left",
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "axes.axisbelow": True,
        "grid.color": GRID,
        "grid.linewidth": 1.0,
        "grid.linestyle": "-",
        "xtick.color": INK_MUTED,
        "ytick.color": INK_MUTED,
        "xtick.labelcolor": INK_SECONDARY,
        "ytick.labelcolor": INK_SECONDARY,
        "legend.frameon": False,
        "legend.fontsize": 9.5,
        "lines.linewidth": 2.0,
        "lines.solid_capstyle": "round",
        "lines.solid_joinstyle": "round",
    }


def plot_profiles(profiles: pd.DataFrame, path: Path) -> Path:
    """Mean velocity around the flare peak for each subset: flares against their controls."""
    subsets = list(dict.fromkeys(profiles["subset"]))
    with plt.rc_context(style()):
        fig, axes = plt.subplots(1, len(subsets), figsize=(4.1 * len(subsets), 3.9), sharey=True)
        for ax, subset in zip(np.atleast_1d(axes), subsets):
            for sample, colour in (("controls", CONTROLS), ("flares", FLARES)):
                data = profiles[(profiles["subset"] == subset) & (profiles["sample"] == sample)]
                ax.fill_between(data["minutes"], data["mean"] - data["sem"], data["mean"] + data["sem"], color=colour, alpha=0.12, linewidth=0)
                ax.plot(data["minutes"], data["mean"], color=colour, marker="o", markersize=4.5, markeredgecolor=SURFACE, markeredgewidth=1.0, label=f"{sample.capitalize()} ({int(data['events'].iloc[0])})")
            ax.axhline(0.0, color=AXIS, linewidth=1.0, zorder=1)
            ax.axvline(0.0, color=AXIS, linewidth=1.0, zorder=1)
            ax.set_title(f"{subset} flares")
            ax.set_xlabel("Minutes from the X-ray peak")
            ax.set_xlim(-60, 90)
            ax.set_xticks(np.arange(-60, 91, 30))
            ax.legend(loc="lower left", handlelength=1.6)
        first = np.atleast_1d(axes)[0]
        first.set_ylabel("Velocity change (m/s)")
        low, high = first.get_ylim()
        limit = max(abs(low), abs(high), 0.3)
        first.set_ylim(-limit, limit)
        first.annotate(
            "9 cm/s: the pull\nof the Earth",
            xy=(-58, EARTH_SIGNAL_MS), xytext=(-58, EARTH_SIGNAL_MS + 0.33 * limit),
            fontsize=8.5, color=INK_SECONDARY, va="bottom", ha="left",
            arrowprops={"arrowstyle": "-", "color": INK_MUTED, "linewidth": 0.8},
        )
        first.plot([-60, -44], [EARTH_SIGNAL_MS] * 2, color=INK_MUTED, linewidth=1.2)
        fig.suptitle(
            "The velocity of the Sun as a star does not change during flares",
            x=0.012, y=0.99, ha="left", fontsize=12, fontweight="semibold", color=INK,
        )
        fig.text(
            0.012, 0.915,
            "Mean of the NEID velocity residuals in 5-minute bins, relative to the 35 minutes before each flare. "
            "Bands: standard error. Controls: flare-free days at the same time of day.",
            ha="left", va="top", fontsize=8.8, color=INK_SECONDARY,
        )
        fig.tight_layout(rect=(0, 0, 1, 0.9))
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=160)
        plt.close(fig)
    return path


def _binned(ax, x, y, edges, colour):
    """Mean and standard error of y in bins of x, drawn as dark markers with error bars."""
    centres, means, errors = [], [], []
    for low, high in zip(edges[:-1], edges[1:]):
        chosen = y[(x >= low) & (x < high)]
        if len(chosen) >= 3:
            centres.append(np.sqrt(low * high) if low > 0 else 0.5 * (low + high))
            means.append(chosen.mean())
            errors.append(chosen.std(ddof=1) / np.sqrt(len(chosen)))
    ax.errorbar(centres, means, yerr=errors, fmt="o", color=colour, markersize=6.5, markeredgecolor=SURFACE, markeredgewidth=1.2, elinewidth=1.6, capsize=0, zorder=5, label="Mean of the flares in each bin")


def plot_events(flares: pd.DataFrame, controls: pd.DataFrame, path: Path) -> Path:
    """Velocity change of each flare against its X-ray flux and its position across the disc."""
    sigma = float(controls["delta"].std(ddof=1))
    centre = float(controls["delta"].mean())
    with plt.rc_context(style()):
        fig, (left, right) = plt.subplots(1, 2, figsize=(11.0, 4.2), sharey=True)
        flux = flares["peak_flux"].to_numpy()
        delta = flares["delta"].to_numpy()
        for ax in (left, right):
            ax.axhspan(centre - sigma, centre + sigma, color=CONTROLS, alpha=0.12, linewidth=0, label="Controls: mean ± 1 standard deviation")
            ax.axhline(centre, color=CONTROLS, linewidth=1.5)
        left.scatter(flux, delta, s=26, color=FLARES, alpha=0.55, edgecolor=SURFACE, linewidth=0.8, label="One flare", zorder=3)
        _binned(left, flux, delta, np.array([1e-5, 2e-5, 5e-5, 1e-4, 1e-3]), INK)
        left.set_xscale("log")
        left.set_xticks([1e-5, 1e-4])
        left.set_xticklabels(["M1", "X1"])
        left.set_xticks([2e-5, 5e-5, 2e-4, 5e-4], minor=True)
        left.set_xticklabels(["M2", "M5", "X2", "X5"], minor=True, fontsize=8.5)
        left.set_xlabel("Flare class (GOES peak flux)")
        left.set_ylabel("Velocity change during the flare (m/s)")
        left.set_title("No trend with the size of the flare")

        on_disc = flares["r_norm"] < 1.05
        x = flares.loc[on_disc, "x_norm"].to_numpy()
        right.scatter(x, delta[on_disc.to_numpy()], s=26, color=FLARES, alpha=0.55, edgecolor=SURFACE, linewidth=0.8, zorder=3)
        _binned(right, x, delta[on_disc.to_numpy()], np.linspace(-1.0, 1.0, 6), INK)
        right.set_xlim(-1.08, 1.08)
        right.set_xticks([-1, -0.5, 0, 0.5, 1])
        right.set_xticklabels(["East limb\n(approaching)", "", "Disc centre", "", "West limb\n(receding)"])
        right.set_xlabel("Position of the flare across the disc")
        right.set_title("No trend with the position: no rotation signature")
        limit = max(1.2, float(np.nanpercentile(np.abs(delta), 99)) * 1.15)
        left.set_ylim(-limit, limit)
        handles, labels = left.get_legend_handles_labels()
        fig.legend(handles, labels, loc="upper left", bbox_to_anchor=(0.055, 1.0), ncol=3, handlelength=1.4, columnspacing=2.2)
        fig.tight_layout(rect=(0, 0, 1, 0.93))
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=160)
        plt.close(fig)
    return path


def plot_event(changes: pd.DataFrame, title: str, path: Path, quantities=None) -> Path:
    """Change of each spectral quantity through one flare, as small multiples on a common time axis."""
    from .response import QUANTITIES

    quantities = quantities or QUANTITIES
    columns = 4
    rows = int(np.ceil(len(quantities) / columns))
    start_min = float((changes["min_peak"] - changes["min_start"]).iloc[0])  # flare start, in minutes from the peak
    with plt.rc_context(style()):
        fig, axes = plt.subplots(rows, columns, figsize=(3.6 * columns, 2.55 * rows + 0.6), sharex=True)
        axes = np.atleast_1d(axes).ravel()
        for ax, (column, label, unit) in zip(axes, quantities):
            sigma = float(changes[f"{column}_sigma"].iloc[0])
            if np.isfinite(sigma):
                ax.axhspan(-sigma, sigma, color=INK_MUTED, alpha=0.14, linewidth=0)
            ax.axhline(0.0, color=AXIS, linewidth=1.0)
            ax.axvline(start_min, color=AXIS, linewidth=1.0)
            ax.axvline(0.0, color=AXIS, linewidth=1.0)
            ax.plot(changes["min_peak"], changes[column], color=FLARES, linewidth=1.4, marker="o", markersize=4.2, markeredgecolor=SURFACE, markeredgewidth=0.8)
            ax.set_title(f"{label} ({unit})", fontsize=9.5)
        for ax in axes[len(quantities):]:
            ax.set_visible(False)
        for ax in axes[max(0, len(quantities) - columns): len(quantities)]:
            ax.set_xlabel("Minutes from the X-ray peak")
        top = axes[0].get_ylim()[1]
        axes[0].text(start_min, top, " start", fontsize=8, color=INK_SECONDARY, va="top", ha="left")
        axes[0].text(0.0, top, " peak", fontsize=8, color=INK_SECONDARY, va="top", ha="left")
        fig.suptitle(title, x=0.012, y=0.995, ha="left", fontsize=12, fontweight="semibold", color=INK)
        fig.text(
            0.012, 0.955,
            "Change with respect to the spectra before the flare start. Grey band: scatter of those spectra. "
            "ppt: parts per thousand; ppm: parts per million.",
            ha="left", va="top", fontsize=8.8, color=INK_SECONDARY,
        )
        fig.tight_layout(rect=(0, 0, 1, 0.93))
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fig.savefig(path, dpi=130)
        plt.close(fig)
    return path
