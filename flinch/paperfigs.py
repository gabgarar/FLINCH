"""Figures of the paper: vector graphics in the style of a journal, at their printed size.

The figures of the documentation (``plots``) are drawn for a web page. These are drawn for a
two-column journal page: white background, no text above the axes (it belongs in the caption),
a serif face of 8 pt, thin lines, ticks pointing in on the four sides, and PDF output at the
width of a column (88 mm) or of the page (180 mm) of Astronomy & Astrophysics.
"""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.ticker import NullLocator  # noqa: E402

COLUMN_MM = 88.0
PAGE_MM = 180.0
# Two colours checked together for colour-vision deficiencies; the two samples also differ in
# the kind of mark (points with error bars against a band), so the figure reads in grey.
FLARES = "#1f5fa8"
CONTROLS = "#c8501e"
GUIDE = "0.45"  # reference lines
BAND = "0.87"  # scatter bands
EARTH_SIGNAL_MS = 0.09  # reflex velocity of the Sun due to the Earth

SUBSET_LABELS = {"M and X": "M- and X-class flares", "M5 and above": "M5 and above", "X": "X-class flares"}

# The quantities of the figure of one flare: four columns by three rows.
EVENT_QUANTITIES = (
    ("Ha06_1_tellcorr", r"H$\alpha$ core", "ppt"),
    ("Hbeta_core", r"H$\beta$ core", "ppt"),
    ("CaIIHK", "Ca II H and K", "ppt"),
    ("CaIRT2_tellcorr", "Ca II 8542 Å", "ppt"),
    ("HeI_1_tellcorr", r"He I D$_3$", "ppt"),
    ("NaI_tellcorr", "Na I D", "ppt"),
    ("Ha16_1_tellcorr", r"H$\alpha$, 1.6 Å band", "ppt"),
    ("CaI_1_tellcorr", "Ca I 6573 Å (reference)", "ppt"),
    ("ccf_depth", "Depth of the mean line", "ppm"),
    ("ccf_fwhm_kms", "Width of the mean line", "ppm"),
    ("ccf_bis_ms", "Bisector span", r"m s$^{-1}$"),
    ("rv_ms", "Radial velocity", r"m s$^{-1}$"),
)


def style() -> dict:
    return {
        "font.family": "STIXGeneral",
        "mathtext.fontset": "stix",
        "font.size": 8.0,
        "axes.labelsize": 8.0,
        "axes.titlesize": 7.5,
        "axes.titleweight": "normal",
        "axes.titlelocation": "left",
        "axes.titlepad": 2.5,
        "xtick.labelsize": 7.5,
        "ytick.labelsize": 7.5,
        "legend.fontsize": 7.5,
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "savefig.facecolor": "white",
        "axes.edgecolor": "black",
        "axes.labelcolor": "black",
        "axes.linewidth": 0.6,
        "axes.grid": False,
        "xtick.direction": "in",
        "ytick.direction": "in",
        "xtick.top": True,
        "ytick.right": True,
        "xtick.minor.visible": True,
        "ytick.minor.visible": True,
        "xtick.major.size": 3.0,
        "ytick.major.size": 3.0,
        "xtick.minor.size": 1.6,
        "ytick.minor.size": 1.6,
        "xtick.major.width": 0.6,
        "ytick.major.width": 0.6,
        "xtick.minor.width": 0.5,
        "ytick.minor.width": 0.5,
        "lines.linewidth": 0.8,
        "lines.markersize": 2.6,
        "errorbar.capsize": 0.0,
        "legend.frameon": False,
        "legend.handlelength": 1.8,
        "legend.borderaxespad": 0.3,
        "pdf.fonttype": 42,
        "savefig.dpi": 300,
    }


def _inches(width_mm: float, height_mm: float) -> tuple[float, float]:
    return width_mm / 25.4, height_mm / 25.4


def _save(fig, path: Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path)
    plt.close(fig)
    return path


def _round_up(value: float, step: float) -> float:
    return float(np.ceil(value / step - 1.0e-9) * step)


def binned_means(x, y, edges) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Centre, mean and standard error of y in bins of x (bins with fewer than three values are left out).

    The centre is the geometric mean of the edges when they are positive (a logarithmic axis)
    and their midpoint otherwise.
    """
    x, y = np.asarray(x, dtype=float), np.asarray(y, dtype=float)
    centres, means, errors = [], [], []
    for low, high in zip(edges[:-1], edges[1:]):
        chosen = y[(x >= low) & (x < high)]
        if len(chosen) >= 3:
            centres.append(np.sqrt(low * high) if low > 0 else 0.5 * (low + high))
            means.append(chosen.mean())
            errors.append(chosen.std(ddof=1) / np.sqrt(len(chosen)))
    return np.array(centres), np.array(means), np.array(errors)


def profiles(table: pd.DataFrame, path: Path) -> Path:
    """Mean velocity around the X-ray peak, flares against controls: one panel per subset, one column wide.

    Each panel has its own vertical scale, because the noise grows as the subset shrinks; the
    dotted lines at plus and minus 9 cm/s (the reflex velocity due to the Earth) give the scale.
    """
    subsets = list(dict.fromkeys(table["subset"]))
    with plt.rc_context(style()):
        fig, axes = plt.subplots(len(subsets), 1, figsize=_inches(COLUMN_MM, 30.0 + 34.0 * len(subsets)), sharex=True)
        axes = np.atleast_1d(axes)
        for ax, subset in zip(axes, subsets):
            chosen = table[table["subset"] == subset]
            controls = chosen[chosen["sample"] == "controls"]
            flares = chosen[chosen["sample"] == "flares"]
            ax.axhline(0.0, color=GUIDE, linewidth=0.5, zorder=1)
            for level in (-EARTH_SIGNAL_MS, EARTH_SIGNAL_MS):
                ax.axhline(level, color=GUIDE, linewidth=0.6, linestyle=(0, (1, 2)), zorder=1)
            ax.axvline(0.0, color=GUIDE, linewidth=0.6, linestyle=(0, (4, 2)), zorder=1)
            ax.fill_between(
                controls["minutes"], controls["mean"] - controls["sem"], controls["mean"] + controls["sem"],
                color=CONTROLS, alpha=0.25, linewidth=0, zorder=2,
            )
            ax.plot(controls["minutes"], controls["mean"], color=CONTROLS, linewidth=0.9, zorder=3,
                    label=f"Controls ({int(controls['events'].iloc[0])})")
            ax.errorbar(
                flares["minutes"], flares["mean"], yerr=flares["sem"], color=FLARES, marker="o", linewidth=0.6,
                elinewidth=0.7, zorder=4, label=f"Flares ({int(flares['events'].iloc[0])})",
            )
            extent = float(np.nanmax(np.abs(np.concatenate([flares["mean"] + flares["sem"], flares["mean"] - flares["sem"]]))))
            limit = _round_up(max(1.25 * extent, 0.2), 0.1)
            ax.set_ylim(-limit, limit)
            ax.text(0.025, 0.93, SUBSET_LABELS.get(subset, str(subset)), transform=ax.transAxes, va="top", ha="left")
            ax.legend(loc="lower left", ncol=2, columnspacing=1.2, handletextpad=0.5)
        axes[0].text(
            88.0, EARTH_SIGNAL_MS, r"$\pm$9 cm s$^{-1}$", va="bottom", ha="right", fontsize=7.0, color="0.25",
        )
        axes[-1].set_xlabel("Time from the X-ray peak (min)")
        axes[-1].set_xlim(-60.0, 90.0)
        axes[-1].set_xticks(np.arange(-60, 91, 30))
        fig.supylabel(r"Velocity change (m s$^{-1}$)", fontsize=8.0, x=0.02)
        fig.subplots_adjust(left=0.155, right=0.985, top=0.99, bottom=0.085, hspace=0.07)
        return _save(fig, path)


def events(flares: pd.DataFrame, controls: pd.DataFrame, path: Path) -> Path:
    """Velocity change of each flare against its class and its position across the disc, one page wide."""
    sigma = float(controls["delta"].std(ddof=1))
    centre = float(controls["delta"].mean())
    flux = flares["peak_flux"].to_numpy()
    delta = flares["delta"].to_numpy()
    on_disc = (flares["r_norm"] < 1.05).to_numpy()
    position = flares["x_norm"].to_numpy()
    with plt.rc_context(style()):
        fig, (left, right) = plt.subplots(1, 2, figsize=_inches(PAGE_MM, 68.0), sharey=True)
        for ax in (left, right):
            ax.axhspan(centre - sigma, centre + sigma, color=CONTROLS, alpha=0.16, linewidth=0, zorder=1,
                       label=r"Controls, mean $\pm$ 1 standard deviation")
            ax.axhline(centre, color=CONTROLS, linewidth=0.9, zorder=2)
        left.scatter(flux, delta, s=7.0, facecolor="none", edgecolor=FLARES, linewidth=0.6, zorder=3, label="One flare")
        x, mean, error = binned_means(flux, delta, np.array([1e-5, 2e-5, 5e-5, 1e-4, 1e-3]))
        left.errorbar(x, mean, yerr=error, fmt="s", color="black", markersize=3.4, elinewidth=0.9, zorder=5, label="Mean in each bin")
        left.set_xscale("log")
        left.set_xlim(8.5e-6, 9.0e-4)
        left.set_xticks([1e-5, 2e-5, 5e-5, 1e-4, 2e-4, 5e-4])
        left.set_xticklabels(["M1", "M2", "M5", "X1", "X2", "X5"])
        left.xaxis.set_minor_locator(NullLocator())
        left.set_xlabel("GOES class")
        left.set_ylabel(r"Velocity change (m s$^{-1}$)")

        right.scatter(position[on_disc], delta[on_disc], s=7.0, facecolor="none", edgecolor=FLARES, linewidth=0.6, zorder=3)
        x, mean, error = binned_means(position[on_disc], delta[on_disc], np.linspace(-1.0, 1.0, 6))
        right.errorbar(x, mean, yerr=error, fmt="s", color="black", markersize=3.4, elinewidth=0.9, zorder=5)
        right.set_xlim(-1.1, 1.1)
        right.set_xticks([-1.0, -0.5, 0.0, 0.5, 1.0])
        right.set_xlabel(r"Position across the disc, $x/R_\odot$")
        limit = _round_up(max(1.2, float(np.nanpercentile(np.abs(delta), 99)) * 1.15), 0.2)
        left.set_ylim(-limit, limit)
        right.text(0.02, 0.04, "east limb, approaching", transform=right.transAxes, ha="left", va="bottom", fontsize=7.0, color="0.25")
        right.text(0.98, 0.04, "west limb, receding", transform=right.transAxes, ha="right", va="bottom", fontsize=7.0, color="0.25")
        handles, labels = left.get_legend_handles_labels()
        order = [labels.index(name) for name in ("One flare", "Mean in each bin", r"Controls, mean $\pm$ 1 standard deviation")]
        fig.legend([handles[i] for i in order], [labels[i] for i in order], loc="upper center", ncol=3, columnspacing=2.5,
                   bbox_to_anchor=(0.53, 1.0))
        fig.subplots_adjust(left=0.07, right=0.99, top=0.915, bottom=0.145, wspace=0.04)
        return _save(fig, path)


def event(changes: pd.DataFrame, path: Path, quantities=EVENT_QUANTITIES, columns: int = 4) -> Path:
    """Change of the spectral quantities through one flare, as small panels on a common time axis, one page wide."""
    rows = int(np.ceil(len(quantities) / columns))
    time = changes["min_peak"].to_numpy()
    start_min = float((changes["min_peak"] - changes["min_start"]).iloc[0])  # start of the flare, minutes from the peak
    with plt.rc_context(style()):
        fig, axes = plt.subplots(rows, columns, figsize=_inches(PAGE_MM, 12.0 + 33.0 * rows), sharex=True)
        axes = np.atleast_1d(axes).ravel()
        for ax, (column, label, unit) in zip(axes, quantities):
            sigma = float(changes[f"{column}_sigma"].iloc[0])
            if np.isfinite(sigma):
                ax.axhspan(-sigma, sigma, color=BAND, linewidth=0, zorder=1)
            ax.axhline(0.0, color=GUIDE, linewidth=0.5, zorder=2)
            ax.axvline(start_min, color=GUIDE, linewidth=0.6, linestyle=(0, (4, 2)), zorder=2)
            ax.axvline(0.0, color=GUIDE, linewidth=0.6, zorder=2)
            ax.plot(time, changes[column], color=FLARES, marker="o", linewidth=0.6, zorder=3)
            ax.set_title(f"{label} ({unit})")
            ax.margins(y=0.12)
        for ax in axes[len(quantities):]:
            ax.set_visible(False)
        for ax in axes[max(0, len(quantities) - columns): len(quantities)]:
            ax.set_xlabel("Time from the X-ray peak (min)")
            ax.tick_params(labelbottom=True)
        axes[0].set_xlim(float(np.nanmin(time)) - 2.0, max(float(np.nanmax(time)), 0.0) + 2.0)
        low, high = axes[0].get_ylim()
        height = high - low
        axes[0].set_ylim(low, high + 0.16 * height)
        axes[0].text(start_min, high + 0.14 * height, " start", fontsize=7.0, color="0.25", va="top", ha="left")
        axes[0].text(0.0, high + 0.14 * height, "peak ", fontsize=7.0, color="0.25", va="top", ha="right")
        fig.subplots_adjust(left=0.05, right=0.99, top=1.0 - 4.5 / (12.0 + 33.0 * rows), bottom=10.5 / (12.0 + 33.0 * rows), wspace=0.24, hspace=0.3)
        return _save(fig, path)


def make_all(directory: Path, event_name: str = "20240222_2233_X6.3") -> list[Path]:
    """Write the figures of the paper from the tables in ``results/`` and the spectra of one flare."""
    from . import neid, quality, response
    from .config import data_dir, results_dir

    directory = Path(directory)
    results = results_dir()
    written = [profiles(pd.read_csv(results / "pilot_profiles.csv"), directory / "profiles.pdf")]
    flares = pd.read_csv(results / "pilot_flares.csv")
    controls = pd.read_csv(results / "pilot_controls.csv")
    flares = flares[flares["measured"] & flares["delta"].notna()]
    controls = controls[controls["measured"] & controls["delta"].notna()]
    written.append(events(flares, controls, directory / "events.pdf"))
    manifest = pd.read_csv(data_dir() / "spectra" / "events.csv").set_index("name")
    row = manifest.loc[event_name]
    keep = quality.stable_obsjd(neid.read_solar_table())
    table = response.event_table(data_dir() / "spectra" / event_name, row["jd_start"], row["jd_peak"], keep_obsjd=keep)
    written.append(event(response.changes(table), directory / f"event_{event_name}.pdf"))
    return written
