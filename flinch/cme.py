"""Coronal mass ejections from the SOHO/LASCO catalogue of the CDAW Data Center, and their flares.

The association is the usual rough one, by time and position angle. It gives candidates, not
certainties: it does not look at images, and LASCO has data gaps.
"""
from __future__ import annotations

import datetime as dt
from pathlib import Path

import numpy as np
import pandas as pd

from ._http import download
from .config import data_dir
from .timeutil import MINUTE, datetime_to_jd

CATALOGUE_URL = "https://cdaw.gsfc.nasa.gov/CME_list/UNIVERSAL_ver2/text_ver/univ_all.txt"


def read_catalogue(path: Path | None = None, refresh: bool = False) -> pd.DataFrame:
    """The catalogue as a table: time of first appearance, position angles, width, speed, remarks.

    ``halo`` marks the events listed as halo (width 360 degrees). Downloaded (5 MB) if missing.
    """
    path = download(CATALOGUE_URL, Path(path or data_dir() / "cme" / "univ_all.txt"), overwrite=refresh)
    rows = []
    for line in path.read_text(encoding="latin-1").splitlines():
        parts = line.split()
        if len(parts) < 12 or len(parts[0]) != 10 or parts[0][4] != "/":
            continue
        try:
            when = dt.datetime.strptime(f"{parts[0]} {parts[1]}", "%Y/%m/%d %H:%M:%S")
            width = float(parts[3].lstrip("<>"))
        except ValueError:
            continue
        halo = parts[2].lower() == "halo"

        def number(text):
            try:
                return float(text.rstrip("*"))
            except ValueError:
                return np.nan

        rows.append(
            {
                "jd": datetime_to_jd(when),
                "halo": halo,
                "cpa": np.nan if halo else number(parts[2]),
                "width": width,
                "speed": number(parts[4]),
                "mpa": number(parts[11]),
                "remarks": " ".join(parts[12:]),
            }
        )
    return pd.DataFrame(rows).sort_values("jd", ignore_index=True)


def flare_position_angle(x_norm, y_norm) -> np.ndarray:
    """Position angle of a point on the disc, in degrees counterclockwise from solar north.

    East (negative x) is at 90 degrees, as in the catalogue.
    """
    return np.degrees(np.arctan2(-np.asarray(x_norm, dtype=float), np.asarray(y_norm, dtype=float))) % 360.0


def associate(
    flares: pd.DataFrame,
    cmes: pd.DataFrame,
    before_min: float = 15.0,
    after_min: float = 90.0,
    angle_deg: float = 60.0,
    min_width: float = 30.0,
) -> pd.DataFrame:
    """Add the candidate CME of each flare: ``cme`` (found or not), its speed, width and delay.

    A CME is a candidate when it first appears in the coronagraph between ``before_min``
    minutes before the flare start and ``after_min`` after its peak, is at least ``min_width``
    degrees wide, is not marked as poor in the catalogue, and either is a halo or wider than
    120 degrees, or the flare is near the disc centre (r < 0.3), or its position angle is
    within ``angle_deg`` of that of the flare. The fastest candidate is kept.
    """
    usable = cmes[(cmes["width"] >= min_width) & ~cmes["remarks"].str.contains("Poor", case=False)]
    times = usable["jd"].to_numpy()
    start = flares["jd_start"].fillna(flares["jd_peak"] - 10.0 * MINUTE).to_numpy()
    peak = flares["jd_peak"].to_numpy()
    angle = flare_position_angle(flares["x_norm"], flares["y_norm"])
    radius = flares["r_norm"].to_numpy(dtype=float)
    found, speed, width, delay = [], [], [], []
    for k in range(len(flares)):
        first, last = np.searchsorted(times, [start[k] - before_min * MINUTE, peak[k] + after_min * MINUTE])
        window = usable.iloc[first:last]
        if len(window):
            direction = window["mpa"].fillna(window["cpa"]).to_numpy()
            apart = np.abs((direction - angle[k] + 180.0) % 360.0 - 180.0)
            wide = (window["halo"] | (window["width"] >= 120.0)).to_numpy()
            central = bool(np.isfinite(radius[k]) and radius[k] < 0.3)
            window = window[wide | central | (apart <= angle_deg)]
        if len(window):
            best = window.sort_values("speed", ascending=False).iloc[0]
            found.append(True)
            speed.append(best["speed"])
            width.append(best["width"])
            delay.append((best["jd"] - peak[k]) / MINUTE)
        else:
            found.append(False)
            speed.append(np.nan)
            width.append(np.nan)
            delay.append(np.nan)
    out = flares.copy()
    out["cme"], out["cme_speed"], out["cme_width"], out["cme_delay_min"] = found, speed, width, delay
    return out
