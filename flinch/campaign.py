"""Unattended download of the spectra around the strongest flares, in order of peak flux."""
from __future__ import annotations

import ctypes
import datetime as dt
import sys
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

from . import coverage, goes, neid, spectra
from .config import data_dir
from .timeutil import MINUTE, jd_to_datetime


def event_name(row) -> str:
    """Folder name of a flare: date, time of the peak and class, e.g. ``20260118_1809_X1.9``."""
    return f"{jd_to_datetime(row.jd_peak):%Y%m%d_%H%M}_{row.goes_class}"


def select_events(min_class: str = "M1.0") -> pd.DataFrame:
    """Flares observed at the peak or during the rise, strongest first."""
    observations = neid.read_solar_table()
    jd = np.sort(observations["obsjd"].to_numpy())
    flares = goes.load_flares()
    flares = flares[(flares["jd_peak"] >= jd.min()) & (flares["jd_peak"] <= jd.max())]
    flares = flares[flares["peak_flux"] >= goes.class_to_flux(min_class)].reset_index(drop=True)
    covered = coverage.add_coverage(flares, jd)
    # Spectra between the start and the peak: a flare peaking just after the end of the
    # observing day still has its impulsive phase on record.
    start = covered["jd_start"].fillna(covered["jd_peak"] - 10.0 * MINUTE)
    covered["n_rise"] = coverage.count_between(jd, start.to_numpy(), covered["jd_peak"].to_numpy())
    covered = covered[covered["at_peak"] | (covered["n_rise"] >= 3)]
    return covered.sort_values("peak_flux", ascending=False, ignore_index=True)


def keep_awake(enable: bool) -> None:
    """Ask Windows not to sleep while the campaign runs (no effect elsewhere)."""
    if sys.platform != "win32":
        return
    continuous, system_required = 0x80000000, 0x00000001
    ctypes.windll.kernel32.SetThreadExecutionState(continuous | (system_required if enable else 0))


def log(message: str) -> None:
    print(f"{dt.datetime.now():%Y-%m-%d %H:%M:%S}  {message}", flush=True)


def run(
    hours: float = 7.5,
    max_files: int = 600,
    step: int = 3,
    before_min: float = 30.0,
    after_min: float = 45.0,
    workers: int = 3,
    min_class: str = "M1.0",
    core_before_min: float = 10.0,
    core_after_min: float = 15.0,
) -> None:
    """Fetch spectrum extracts flare by flare until the time or the file budget runs out.

    Each flare gets the window from ``before_min`` minutes before its start to ``after_min``
    minutes after its peak. Every spectrum is taken in the core of the flare (from
    ``core_before_min`` minutes before the start to ``core_after_min`` after the peak, where
    things change within a minute) and every ``step``-th one outside it. Extracts already on
    disk are skipped, so the campaign can be stopped and run again.
    """
    deadline = time.monotonic() + hours * 3600.0
    events = select_events(min_class)
    root = data_dir() / "spectra"
    scratch = Path(tempfile.gettempdir()) / "flinch_spectra"
    scratch.mkdir(parents=True, exist_ok=True)
    fetched = 0
    keep_awake(True)
    log(f"campaign: {len(events)} flares, budget {hours} h / {max_files} files, step {step}")
    try:
        for row in events.itertuples():
            if time.monotonic() > deadline or fetched >= max_files:
                break
            name = event_name(row)
            start = row.jd_start if row.jd_start == row.jd_start else row.jd_peak - 10.0 * MINUTE
            try:
                files = spectra.list_files(start - before_min * MINUTE, row.jd_peak + after_min * MINUTE)
                core = (files["obsjd"] >= start - core_before_min * MINUTE) & (
                    files["obsjd"] <= row.jd_peak + core_after_min * MINUTE
                )
                files = files[core | (np.arange(len(files)) % step == 0)]
            except Exception as exc:  # noqa: BLE001  (network trouble: go on with the next flare)
                log(f"{name}: could not list files ({type(exc).__name__}: {exc})")
                continue
            directory = root / name
            directory.mkdir(parents=True, exist_ok=True)
            todo = [f for f in files.itertuples() if not (directory / (Path(f.l2filename).stem + ".npz")).exists()]
            todo = todo[: max(0, max_files - fetched)]

            def task(item) -> bool:
                if time.monotonic() > deadline:
                    return False
                try:
                    spectra.fetch_one(item.l2filepath, item.l2filename, directory, scratch)
                    return True
                except Exception as exc:  # noqa: BLE001
                    log(f"{name}: {item.l2filename} failed ({type(exc).__name__}: {exc})")
                    return False

            began = time.monotonic()
            with ThreadPoolExecutor(max_workers=workers) as pool:
                done = sum(pool.map(task, todo))
            fetched += done
            have = len(list(directory.glob("neidL2_*.npz")))
            rate = (time.monotonic() - began) / max(done, 1)
            log(f"{name}: +{done} (now {have} of {len(files)}), {rate:.0f} s per file, total fetched {fetched}")
    finally:
        keep_awake(False)
        log(f"campaign finished: {fetched} files fetched")
