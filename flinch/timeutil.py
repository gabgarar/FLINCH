"""Time conversions. Julian dates (UTC) are the internal time axis of the package."""
from __future__ import annotations

import datetime as dt

import numpy as np
import pandas as pd

JD_UNIX_EPOCH = 2440587.5  # 1970-01-01 00:00 UTC
JD_J2000 = 2451545.0  # 2000-01-01 12:00 UTC, the epoch of the GOES-R time axis
MINUTE = 1.0 / 1440.0  # one minute in days


def jd_to_datetime(jd):
    """Julian date(s) to pandas timestamps (UTC, timezone-naive)."""
    seconds = (np.asarray(jd, dtype=float) - JD_UNIX_EPOCH) * 86400.0
    if seconds.ndim == 0:
        return pd.to_datetime(float(seconds), unit="s")
    return pd.to_datetime(seconds, unit="s")


def datetime_to_jd(when: dt.datetime) -> float:
    """A timezone-naive UTC datetime to Julian date."""
    return (when - dt.datetime(1970, 1, 1)).total_seconds() / 86400.0 + JD_UNIX_EPOCH


def year_start_jd(year: int) -> float:
    """Julian date of 1 January, 00:00 UTC, of ``year``."""
    return datetime_to_jd(dt.datetime(year, 1, 1))
