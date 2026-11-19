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
    ("ccf_depth", "Depth of the mean line", "ppm"),
    ("ccf_fwhm_kms", "Width of the mean line", "ppm"),
    ("ccf_area_kms", "Area of the mean line", "ppm"),
    ("ccf_bis_ms", "Bisector span", "m/s"),
    ("rv_ms", "Radial velocity", "m/s"),
)
SCALE = {"ppt": 1.0e3, "ppm": 1.0e6}


def event_table(directory: Path, jd_start: float, jd_peak: float) -> pd.DataFrame:
    """One row per spectrum of a flare window, with time relative to the flare and the line shape."""
    table, arrays = spectra.load_window(directory)
    with np.load(next(Path(directory).glob("neidL2_*.npz"))) as first:
        ccf_start, ccf_step = float(first["ccfstart"]), float(first["ccfstep"])
    table = pd.concat([table, lineshape.measure(arrays["ccf"], ccf_start, ccf_step)], axis=1)
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
