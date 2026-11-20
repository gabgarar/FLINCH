"""Solar velocities of HARPS-N: the public time series of the ten-year data release.

The solar telescope of HARPS-N (Telescopio Nazionale Galileo, La Palma) has observed the Sun
as a star since July 2015, with exposures of five minutes. Dumusque et al. (2026, A&A 706,
A231) released the velocities and activity indices of ten years as one table. It is used here
as a second, independent instrument: it observes during the European day, so it sees other
flares than NEID.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import _http, quality
from .config import data_dir

SERIES_NAME = "harpn_sun_release_timeseries_2015-2025.csv"
SERIES_URL = "https://dace.unige.ch/downloads/open_data/dace-h4s8lp7c/files/timeseries/2015-2025/" + SERIES_NAME
CADENCE_S = 324.0  # one 300 s exposure every 324 s
MIN_QUALITY = 0.99  # of the flag that marks clouds and haze (Collier Cameron et al. 2019)


def series_path() -> Path:
    return data_dir() / "harpsn" / SERIES_NAME


def download_series(overwrite: bool = False) -> Path:
    """Download the time series of the release (64 MB) into the data directory."""
    path = series_path()
    if overwrite or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        _http.download(SERIES_URL, path, overwrite=True)
    return path


def read_series(path: Path | None = None) -> pd.DataFrame:
    """The time series with the columns that the velocity analysis uses.

    ``obsjd``  start of the exposure, Julian date (UTC), from the time stamp in the file name.
    ``jd``     middle of the exposure. The table also has a barycentric date, which must not be
               compared with flare times recorded at the Earth.
    ``rv_ms``  velocity in the heliocentric frame, corrected for differential extinction (m/s).
    """
    table = pd.read_csv(path or series_path())
    stamp = pd.to_datetime(table["file_root"].str.replace("HARPN.", "", regex=False), format="%Y-%m-%dT%H-%M-%S.%f")
    out = pd.DataFrame(
        {
            "obsjd": stamp.map(pd.Timestamp.to_julian_date).to_numpy(),
            "exptime": table["texp"].to_numpy(dtype=float),
            "rv_ms": 1000.0 * table["rv"].to_numpy(dtype=float),
            "rv_err_ms": 1000.0 * table["rv_err"].to_numpy(dtype=float),
            "obs_quality": table["obs_quality"].to_numpy(dtype=float),
            "data_quality": table["data_quality"].to_numpy(dtype=float),
        }
    )
    out["jd"] = out["obsjd"] + 0.5 * out["exptime"] / 86400.0
    return out.sort_values("obsjd", ignore_index=True)


def prepare(
    table: pd.DataFrame,
    min_quality: float = MIN_QUALITY,
    order: int = 2,
    clip: float = 5.0,
    min_points: int = 20,
    max_day_sigma: float = 1.5,
) -> pd.DataFrame:
    """Flag good observations and subtract a polynomial trend from each day, as for NEID.

    The clouds are rejected with the quality flag of the release instead of the signal-to-noise
    ratio; the daily trend, the clipping and the cut on the scatter of the day are those of
    ``quality.prepare``. A day needs ``min_points`` good exposures (20 are 1.8 hours).
    Adds ``day``, ``res``, ``day_sigma`` and ``good``.
    """
    out = table.sort_values("obsjd", ignore_index=True).copy()
    if "jd" not in out:
        out["jd"] = out["obsjd"] + 0.5 * out["exptime"] / 86400.0
    out["day"] = np.floor(out["jd"] - 0.5).astype(np.int64)
    good = np.isfinite(out["rv_ms"]) & (out["obs_quality"] >= min_quality) & (out["data_quality"] == 1.0)
    residual, day_sigma, good = quality.detrend_days(
        out["jd"].to_numpy(), out["rv_ms"].to_numpy(), out["day"].to_numpy(), good.to_numpy(), order, clip, min_points, max_day_sigma
    )
    out["res"], out["day_sigma"], out["good"] = residual, day_sigma, good
    return out
