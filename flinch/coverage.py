"""Which flares happened while the spectrograph was observing the Sun."""
from __future__ import annotations

import numpy as np
import pandas as pd

from .timeutil import MINUTE

BANDS = ("M1-M4", "M5-M9", "X")


def count_between(sorted_times: np.ndarray, low, high) -> np.ndarray:
    """Number of elements of ``sorted_times`` in the closed interval [low, high] (vectorised)."""
    return np.searchsorted(sorted_times, high, side="right") - np.searchsorted(sorted_times, low, side="left")


def class_band(goes_class: str) -> str:
    """Coarse class band used in the summary tables."""
    letter = goes_class[0].upper()
    if letter == "X":
        return "X"
    if letter == "M":
        return "M5-M9" if float(goes_class[1:]) >= 5.0 else "M1-M4"
    return letter


def add_coverage(
    flares: pd.DataFrame,
    observation_jd,
    peak_tolerance_min: float = 2.0,
    baseline_min: float = 30.0,
    min_points: int = 5,
) -> pd.DataFrame:
    """Add coverage columns to a flare table.

    ``n_peak``: observations within ``peak_tolerance_min`` of the flare peak.
    ``n_pre``: observations in the ``baseline_min`` minutes before the flare start.
    ``n_post``: observations in the ``baseline_min`` minutes after the peak.
    ``at_peak``: the instrument was observing at the peak.
    ``well_covered``: at the peak, with at least ``min_points`` observations before and after.

    A flare without a recorded start is assumed to start 10 minutes before its peak.
    """
    times = np.sort(np.asarray(observation_jd, dtype=float))
    out = flares.copy()
    peak = out["jd_peak"].to_numpy(dtype=float)
    start = out["jd_start"].to_numpy(dtype=float)
    start = np.where(np.isfinite(start), start, peak - 10.0 * MINUTE)
    out["n_peak"] = count_between(times, peak - peak_tolerance_min * MINUTE, peak + peak_tolerance_min * MINUTE)
    out["n_pre"] = count_between(times, start - baseline_min * MINUTE, start)
    out["n_post"] = count_between(times, peak, peak + baseline_min * MINUTE)
    out["at_peak"] = out["n_peak"] > 0
    out["well_covered"] = out["at_peak"] & (out["n_pre"] >= min_points) & (out["n_post"] >= min_points)
    return out


def summarize(flares: pd.DataFrame) -> pd.DataFrame:
    """Number of flares per class band: total, observed at the peak, and well covered."""
    bands = flares["goes_class"].map(class_band)
    rows = []
    for band in BANDS:
        selected = flares[bands == band]
        rows.append(
            {
                "band": band,
                "total": len(selected),
                "at_peak": int(selected["at_peak"].sum()),
                "well_covered": int(selected["well_covered"].sum()),
            }
        )
    return pd.DataFrame(rows)
