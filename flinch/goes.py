"""Solar flare lists from the GOES-R X-ray sensors (science-quality flare summaries, NOAA/NCEI)."""
from __future__ import annotations

import re
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

from ._http import download, fetch_text
from .config import data_dir
from .timeutil import JD_J2000, MINUTE, jd_to_datetime

ARCHIVE = "https://data.ngdc.noaa.gov/platforms/solar-space-observing-satellites/goes"
# GOES-16 covers 2017-02 to 2025-04; GOES-18 from 2022-06 onwards. The first one is the primary list.
SATELLITES = (16, 18)
_CLASS_BASE = {"A": 1e-8, "B": 1e-7, "C": 1e-6, "M": 1e-5, "X": 1e-4}
_MISSION_FILE = re.compile(r'href="(sci_xrsf-l2-flsum_g\d\d_s\d{8}_e\d{8}_v[\d-]+\.nc)"')


def class_to_flux(goes_class: str) -> float:
    """GOES class ("M5.2") to peak flux in the 1-8 Angstrom band, in W m^-2."""
    return _CLASS_BASE[goes_class[0].upper()] * float(goes_class[1:])


def flux_to_class(flux: float) -> str:
    """Peak flux in W m^-2 to GOES class."""
    for letter in "XMCB":
        if flux >= _CLASS_BASE[letter]:
            return f"{letter}{flux / _CLASS_BASE[letter]:.1f}"
    return f"A{flux / _CLASS_BASE['A']:.1f}"


def flsum_directory(satellite: int) -> str:
    return f"{ARCHIVE}/goes{satellite}/l2/data/xrsf-l2-flsum_science/"


def find_flsum_url(satellite: int) -> str:
    """URL of the mission-long flare summary of a satellite (the file name carries its end date)."""
    directory = flsum_directory(satellite)
    names = _MISSION_FILE.findall(fetch_text(directory))
    if not names:
        raise RuntimeError(f"no mission-long flare summary found in {directory}")
    return directory + sorted(names)[-1]


def download_flsum(satellite: int, directory: Path | None = None, overwrite: bool = False) -> Path:
    """Download the mission-long flare summary of ``satellite``; returns the local path."""
    directory = Path(directory or data_dir() / "goes")
    url = find_flsum_url(satellite)
    return download(url, directory / url.rsplit("/", 1)[-1], overwrite=overwrite)


def read_flsum(path: Path, satellite: int | None = None) -> pd.DataFrame:
    """Read a flare summary file into one row per flare.

    The file stores one record per event marker (start, peak, end) sharing a ``flare_id``.
    Times are Julian dates (UTC); fluxes are in W m^-2 (1-8 Angstrom), fluences in J m^-2.
    """
    path = Path(path)
    with h5py.File(path, "r") as handle:
        records = pd.DataFrame(
            {
                "jd": JD_J2000 + handle["time"][:] / 86400.0,
                "status": handle["status"].asstr()[:],
                "goes_class": handle["flare_class"].asstr()[:],
                "flux": handle["xrsb_flux"][:].astype(float),
                "fluence": handle["integrated_flux"][:].astype(float),
                "flare_id": handle["flare_id"][:],
            }
        )
    if satellite is None:
        match = re.search(r"_g(\d\d)_", path.name)
        satellite = int(match.group(1)) if match else 0

    def marker(status: str) -> pd.DataFrame:
        return records[records["status"] == status].drop_duplicates("flare_id").set_index("flare_id")

    peaks, starts, ends = marker("EVENT_PEAK"), marker("EVENT_START"), marker("EVENT_END")
    peaks = peaks[peaks["goes_class"] != ""]
    flares = pd.DataFrame(
        {
            "jd_start": starts["jd"].reindex(peaks.index),
            "jd_peak": peaks["jd"],
            "jd_end": ends["jd"].reindex(peaks.index),
            "goes_class": peaks["goes_class"],
            "peak_flux": peaks["flux"],
            "fluence": ends["fluence"].reindex(peaks.index),
        }
    )
    flares["satellite"] = satellite
    return flares.reset_index().sort_values("jd_peak", ignore_index=True)


def merge_flare_lists(primary: pd.DataFrame, secondary: pd.DataFrame, tolerance_min: float = 3.0) -> pd.DataFrame:
    """The primary list plus the flares of the secondary with no counterpart in the primary.

    Two entries are the same flare when their peaks are closer than ``tolerance_min`` minutes,
    or when the secondary peak falls between the start and the end of a primary flare (the two
    satellites can place the peak of a long, flat flare several minutes apart).
    """
    if primary.empty or secondary.empty:
        return pd.concat([primary, secondary], ignore_index=True).sort_values("jd_peak", ignore_index=True)
    peaks = np.sort(primary["jd_peak"].to_numpy())
    candidates = secondary["jd_peak"].to_numpy()
    index = np.searchsorted(peaks, candidates)
    before = np.abs(candidates - peaks[np.clip(index - 1, 0, len(peaks) - 1)])
    after = np.abs(peaks[np.clip(index, 0, len(peaks) - 1)] - candidates)
    isolated = np.minimum(before, after) > tolerance_min * MINUTE
    if {"jd_start", "jd_end"} <= set(primary.columns):
        windows = primary.dropna(subset=["jd_start", "jd_end"]).sort_values("jd_start")
        if not windows.empty:
            starts, ends = windows["jd_start"].to_numpy(), windows["jd_end"].to_numpy()
            last_started = np.searchsorted(starts, candidates, side="right") - 1
            inside = (last_started >= 0) & (candidates <= ends[np.clip(last_started, 0, len(ends) - 1)])
            isolated &= ~inside
    merged = pd.concat([primary, secondary[isolated]], ignore_index=True)
    return merged.sort_values("jd_peak", ignore_index=True)


def load_flares(directory: Path | None = None, satellites: tuple[int, ...] = SATELLITES) -> pd.DataFrame:
    """Merged flare list from the downloaded summaries (run ``python -m flinch download`` first)."""
    directory = Path(directory or data_dir() / "goes")
    merged = None
    for satellite in satellites:
        files = sorted(directory.glob(f"sci_xrsf-l2-flsum_g{satellite}_*.nc"))
        if not files:
            raise FileNotFoundError(
                f"no GOES-{satellite} flare summary in {directory}; run `python -m flinch download`"
            )
        flares = read_flsum(files[-1])
        merged = flares if merged is None else merge_flare_lists(merged, flares)
    merged["peak"] = jd_to_datetime(merged["jd_peak"])
    return merged
