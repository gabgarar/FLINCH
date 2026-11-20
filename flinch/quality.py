"""Quality cuts and removal of the slow daily trend in the solar radial velocities."""
from __future__ import annotations

import numpy as np
import pandas as pd

# OBSJD is the start of the exposure (FITS keyword DATE-OBS); solar exposures last 55 s.
DEFAULT_EXPOSURE_S = 55.0


def robust_sigma(values: np.ndarray) -> float:
    """Standard deviation estimated from the median absolute deviation."""
    values = np.asarray(values, dtype=float)
    return float(1.4826 * np.median(np.abs(values - np.median(values))))


def stable_obsjd(table: pd.DataFrame, snr_tolerance: float = 0.01) -> np.ndarray:
    """Exposure start times (sorted) of the spectra taken through a steady, clear sky.

    These are the spectra with a valid velocity error and a signal-to-noise ratio within
    ``snr_tolerance`` of its running median. Unlike ``good`` it does not drop whole days, so it
    suits the spectral indices, which a passing cloud ruins just as it ruins the velocity.
    """
    prepared = table if "snr_rel" in table else prepare(table)
    steady = (prepared["snr_rel"] - 1.0).abs() <= snr_tolerance
    return np.sort(prepared.loc[steady, "obsjd"].to_numpy())


def matches(obsjd, keep_obsjd, tolerance: float = 2.0e-6) -> np.ndarray:
    """Which exposure start times are in the sorted array ``keep_obsjd``, to 0.2 s by default."""
    obsjd = np.asarray(obsjd, dtype=float)
    keep_obsjd = np.asarray(keep_obsjd, dtype=float)
    if len(keep_obsjd) == 0:
        return np.zeros(len(obsjd), dtype=bool)
    after = np.clip(np.searchsorted(keep_obsjd, obsjd), 0, len(keep_obsjd) - 1)
    before = np.clip(after - 1, 0, len(keep_obsjd) - 1)
    nearest = np.minimum(np.abs(keep_obsjd[after] - obsjd), np.abs(keep_obsjd[before] - obsjd))
    return nearest < tolerance


def prepare(
    table: pd.DataFrame,
    snr_window: int = 31,
    snr_tolerance: float = 0.01,
    max_rv_err_ms: float = 1.0,
    min_snr: float = 50.0,
    order: int = 2,
    clip: float = 5.0,
    min_points: int = 40,
    max_day_sigma: float = 1.5,
) -> pd.DataFrame:
    """Flag good observations and subtract a polynomial trend from each day.

    Added columns:

    ``jd``      mid-exposure Julian date (UTC).
    ``day``     integer UT day number.
    ``snr_rel`` signal-to-noise ratio divided by its running median over ``snr_window`` spectra.
    ``res``     velocity minus the polynomial of degree ``order`` fitted to the good points of the day (m/s).
    ``day_sigma`` robust scatter of the good residuals of the day (m/s).
    ``good``    passes every cut.

    Cuts: a valid velocity error below ``max_rv_err_ms``; a signal-to-noise ratio above
    ``min_snr`` and within ``snr_tolerance`` of its running median (passing clouds lower it and
    bias the velocity); a residual within ``clip`` robust sigmas of the daily fit; at least
    ``min_points`` good spectra in the day; and a daily scatter below ``max_day_sigma`` (the
    median day has 0.8 m/s; days of broken cloud reach tens of m/s and are dropped whole).
    """
    out = table.sort_values("obsjd", ignore_index=True).copy()
    exposure = out["exptime"].where(out["exptime"] > 0, DEFAULT_EXPOSURE_S) if "exptime" in out else DEFAULT_EXPOSURE_S
    out["jd"] = out["obsjd"] + 0.5 * exposure / 86400.0
    out["day"] = np.floor(out["jd"] - 0.5).astype(np.int64)

    valid = (
        np.isfinite(out["rv_ms"])
        & (out["rv_err_ms"] > 0.0)
        & (out["rv_err_ms"] < max_rv_err_ms)
        & (out["extsnr"] > min_snr)
    )
    snr = out["extsnr"].where(valid)
    reference = snr.groupby(out["day"]).transform(
        lambda s: s.rolling(snr_window, center=True, min_periods=max(3, snr_window // 4)).median()
    )
    out["snr_rel"] = snr / reference
    good = np.array(valid & ((out["snr_rel"] - 1.0).abs() <= snr_tolerance), dtype=bool)  # writable copy

    jd = out["jd"].to_numpy()
    rv = out["rv_ms"].to_numpy()
    residual = np.full(len(out), np.nan)
    day_sigma = np.full(len(out), np.nan)
    days = out["day"].to_numpy()
    boundaries = np.flatnonzero(np.diff(days)) + 1
    for lo, hi in zip(np.r_[0, boundaries], np.r_[boundaries, len(days)]):
        mask = good[lo:hi].copy()
        if mask.sum() < min_points:
            good[lo:hi] = False
            continue
        hours = (jd[lo:hi] - jd[lo:hi][mask].mean()) * 24.0
        velocity = rv[lo:hi]
        for _ in range(6):
            fit = np.polyfit(hours[mask], velocity[mask], order)
            r = velocity - np.polyval(fit, hours)
            sigma = robust_sigma(r[mask])
            updated = good[lo:hi] & (np.abs(r) < clip * sigma)
            if updated.sum() < min_points or np.array_equal(updated, mask):
                mask = updated
                break
            mask = updated
        if mask.sum() < min_points:
            good[lo:hi] = False
            continue
        day_sigma[lo:hi] = robust_sigma(r[mask])
        if day_sigma[lo] > max_day_sigma:
            good[lo:hi] = False
            continue
        residual[lo:hi] = r
        good[lo:hi] = mask
    out["res"] = residual
    out["day_sigma"] = day_sigma
    out["good"] = good
    return out
