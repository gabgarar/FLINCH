"""Response of the spectrum to one flare: chromospheric indices and shape of the mean line."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import lineshape, spectra
from .timeutil import MINUTE

# Quantities followed through a flare: column, label, and unit of the plotted change.
# Indices are those of the NEID pipeline (telluric-corrected where the two versions differ).
QUANTITIES = (
    ("Ha06_1_tellcorr", "H alpha core (0.6 A)", "ppt"),
    ("CaIIHK", "Ca II H and K", "ppt"),
    ("HeI_1_tellcorr", "He I D3", "ppt"),
    ("NaI_tellcorr", "Na I D", "ppt"),
    ("CaIRT2_tellcorr", "Ca II 8542", "ppt"),
    ("CaI_1_tellcorr", "Ca I 6573 (photospheric reference)", "ppt"),
    ("Ha16_1_tellcorr", "H alpha, 1.6 A band", "ppt"),
    ("CaIRT1_tellcorr", "Ca II 8498", "ppt"),
    ("CaIRT3_tellcorr", "Ca II 8662", "ppt"),
    ("NaINIR_tellcorr", "Na I 8183 and 8195", "ppt"),
    ("PaDelta_tellcorr", "Paschen delta", "ppt"),
    ("Mn539_tellcorr", "Mn I 5395", "ppt"),
    ("Hbeta_core", "H beta core (own index)", "ppt"),
    ("MgIb2_core", "Mg I b2 core (own index)", "ppt"),
    ("CaIIK_core", "Ca II K core (own index)", "ppt"),
    ("ccf_depth", "Depth of the mean line", "ppm"),
    ("ccf_fwhm_kms", "Width of the mean line", "ppm"),
    ("ccf_area_kms", "Area of the mean line", "ppm"),
    ("ccf_bis_ms", "Bisector span", "m/s"),
    ("rv_ms", "Radial velocity", "m/s"),
)
SCALE = {"ppt": 1.0e3, "ppm": 1.0e6}
# Own indices from the saved line windows: window, line centre and half-width of the core, and the
# two reference bands (vacuum wavelengths in Angstrom). Index = mean core flux / mean reference flux.
OWN_INDICES = {
    "Hbeta_core": ("Hbeta", 4862.68, 0.25, (4856.5, 4858.5), (4866.5, 4868.5)),
    "MgIb2_core": ("MgI_b", 5174.13, 0.15, (5176.0, 5178.0), (5180.0, 5182.0)),
    "CaIIK_core": ("CaII_HK", 3934.78, 0.50, (3950.0, 3955.0), (3958.0, 3962.0)),
}


def own_indices(arrays: dict) -> pd.DataFrame:
    """Line-core indices measured on the saved windows of the stitched spectra."""
    out = {}
    for name, (window, centre, half, first, second) in OWN_INDICES.items():
        flux = arrays[f"{window}_flux"]
        if len(flux) == 0:  # every spectrum of the window was rejected
            out[name] = np.array([])
            continue
        wave = arrays[f"{window}_wave"][0]
        core = np.abs(wave - centre) <= half
        reference = ((wave >= first[0]) & (wave <= first[1])) | ((wave >= second[0]) & (wave <= second[1]))
        out[name] = flux[:, core].mean(axis=1) / flux[:, reference].mean(axis=1)
    return pd.DataFrame(out)


def event_table(directory: Path, jd_start: float, jd_peak: float, keep_obsjd=None) -> pd.DataFrame:
    """One row per spectrum of a flare window, with time relative to the flare and the line shape.

    ``keep_obsjd`` is an optional sorted array of exposure start times; spectra not in it (to
    0.2 s) are dropped. Pass ``quality.stable_obsjd`` to leave out those taken through cloud.
    """
    table, arrays = spectra.load_window(directory)
    if keep_obsjd is not None and len(table):
        keep_obsjd = np.asarray(keep_obsjd, dtype=float)
        index = np.clip(np.searchsorted(keep_obsjd, table["obsjd"].to_numpy()), 1, len(keep_obsjd) - 1)
        nearest = np.minimum(
            np.abs(keep_obsjd[index] - table["obsjd"].to_numpy()), np.abs(keep_obsjd[index - 1] - table["obsjd"].to_numpy())
        )
        kept = nearest < 2.0e-6
        table = table[kept].reset_index(drop=True)
        arrays = {key: value[kept] for key, value in arrays.items()}
    with np.load(next(Path(directory).glob("neidL2_*.npz"))) as first:
        ccf_start, ccf_step = float(first["ccfstart"]), float(first["ccfstep"])
    table = pd.concat([table, lineshape.measure(arrays["ccf"], ccf_start, ccf_step), own_indices(arrays)], axis=1)
    table["min_peak"] = (table["jd"] - jd_peak) / MINUTE
    table["min_start"] = (table["jd"] - jd_start) / MINUTE
    return table


def changes(table: pd.DataFrame, baseline_end_min: float = -2.0, detrend: bool = False) -> pd.DataFrame:
    """Change of each quantity with respect to the spectra taken before the flare start.

    Indices and line-shape parameters are relative changes (parts per thousand or per million);
    the bisector span and the velocity are differences in m/s. With ``detrend`` a straight line
    fitted to the pre-flare spectra is removed instead of their mean (the slow drift with the
    height of the Sun), at the price of a larger error when extrapolated through the flare.
    ``<column>_sigma`` is the scatter of the pre-flare values about that baseline.
    """
    before = table["min_start"] < baseline_end_min
    out = table[["jd", "min_peak", "min_start"]].copy()
    out["pre_flare"] = before
    time = table["min_start"].to_numpy()
    for column, _, unit in QUANTITIES:
        values = table[column].to_numpy(dtype=float)
        if before.sum() >= (4 if detrend else 2):
            if detrend:
                baseline = np.polyval(np.polyfit(time[before], values[before], 1), time)
            else:
                baseline = np.full(len(values), values[before].mean())
            change = (values / baseline - 1.0) * SCALE[unit] if unit in SCALE else values - baseline
            out[column] = change
            out[f"{column}_sigma"] = float(np.std(change[before.to_numpy()], ddof=2 if detrend else 1))
        else:
            out[column] = np.nan
            out[f"{column}_sigma"] = np.nan
    return out


def event_response(change: pd.DataFrame, window_min: tuple[float, float] = (-8.0, 10.0)) -> dict:
    """Mean change of each quantity around the X-ray peak, with its error.

    The window is in minutes from the peak. The error combines the scatter of the pre-flare
    spectra over the number of spectra in the window and in the baseline.
    """
    inside = (change["min_peak"] >= window_min[0]) & (change["min_peak"] <= window_min[1]) & ~change["pre_flare"]
    n_window, n_before = int(inside.sum()), int(change["pre_flare"].sum())
    out = {"n_window": n_window, "n_before": n_before}
    for column, _, _ in QUANTITIES:
        sigma = float(change[f"{column}_sigma"].iloc[0])
        if n_window >= 2 and n_before >= 3 and np.isfinite(sigma):
            out[column] = float(change.loc[inside, column].mean())
            out[f"{column}_err"] = sigma * float(np.sqrt(1.0 / n_window + 1.0 / n_before))
        else:
            out[column] = np.nan
            out[f"{column}_err"] = np.nan
    return out


def collect(
    events: pd.DataFrame,
    root: Path,
    window_min: tuple[float, float] = (-8.0, 10.0),
    detrend: bool = False,
    keep_obsjd=None,
) -> pd.DataFrame:
    """Response of every event that has spectra: one row per event.

    ``events`` needs the columns ``name``, ``jd_start`` and ``jd_peak``; its other columns
    (class, flux, position, kind) are carried over.
    """
    rows = []
    for event in events.itertuples(index=False):
        directory = Path(root) / event.name
        if len(list(directory.glob("neidL2_*.npz"))) < 8:
            continue
        table = event_table(directory, event.jd_start, event.jd_peak, keep_obsjd)
        row = event._asdict()
        row["n_spectra"] = len(table)
        if len(table) < 8:
            continue
        row.update(event_response(changes(table, detrend=detrend), window_min))
        rows.append(row)
    return pd.DataFrame(rows)
