"""Synthetic GOES files, NEID velocity table and NEID spectra for the tests."""
from __future__ import annotations

import h5py
import numpy as np
import pandas as pd

JD_J2000 = 2451545.0
MINUTE = 1.0 / 1440.0
DAY0 = 2460000.5  # 2023-02-25 00:00 UT
CADENCE_S = 83.0
INDEX_NAMES = (
    "CaIIHK", "HeI_1_tellcorr", "NaI_tellcorr", "Ha06_1_tellcorr", "Ha16_1_tellcorr", "CaI_1_tellcorr",
    "CaIRT1_tellcorr", "CaIRT2_tellcorr", "CaIRT3_tellcorr", "NaINIR_tellcorr", "PaDelta_tellcorr", "Mn539_tellcorr",
)


def _strings(handle, name, values):
    handle.create_dataset(name, data=np.array(list(values), dtype=object), dtype=h5py.string_dtype())


def write_flsum(path, flares: pd.DataFrame) -> None:
    """Flare summary with start, peak and end records for each row.

    Columns used: jd_start, jd_peak, jd_end, goes_class, peak_flux and, optionally, flare_id.
    """
    seconds, status, classes, flux, fluence, ids = [], [], [], [], [], []
    for k, row in enumerate(flares.itertuples(), start=1):
        for jd, marker in ((row.jd_start, "EVENT_START"), (row.jd_peak, "EVENT_PEAK"), (row.jd_end, "EVENT_END")):
            seconds.append((jd - JD_J2000) * 86400.0)
            status.append(marker)
            classes.append(row.goes_class if marker == "EVENT_PEAK" else "")
            flux.append(row.peak_flux if marker == "EVENT_PEAK" else row.peak_flux / 10.0)
            fluence.append(0.05 if marker == "EVENT_END" else 0.0)
            ids.append(getattr(row, "flare_id", k))
    with h5py.File(path, "w") as handle:
        handle["time"] = np.array(seconds, dtype="f8")
        _strings(handle, "status", status)
        _strings(handle, "flare_class", classes)
        handle["xrsb_flux"] = np.array(flux, dtype="f4")
        handle["integrated_flux"] = np.array(fluence, dtype="f4")
        handle["flare_id"] = np.array(ids, dtype="i8")


def write_flloc(path, flare_ids, x_norm, y_norm, radius=950.0) -> None:
    """Flare locations; positions outside the disc get no heliographic coordinates, as in the real product."""
    x, y = np.asarray(x_norm, dtype=float), np.asarray(y_norm, dtype=float)
    on_disc = np.hypot(x, y) < 1.0
    lon = np.where(on_disc, np.degrees(np.arcsin(np.clip(x, -1, 1))), -9999.0)
    lat = np.where(on_disc, np.degrees(np.arcsin(np.clip(y, -1, 1))), -9999.0)
    with h5py.File(path, "w") as handle:
        handle["flloc_xy"] = np.column_stack([x, y]).astype("f4") * radius
        handle["solar_radius"] = np.full(len(x), radius, dtype="f4")
        handle["flloc_hg"] = np.column_stack([lon, lat]).astype("f4")
        handle["flloc_car"] = np.column_stack([np.where(on_disc, (lon + 100.0) % 360.0, -9999.0), lat]).astype("f4")
        handle["flare_id"] = np.asarray(flare_ids, dtype="i8")


def write_avg1m(path, jd, flux) -> None:
    with h5py.File(path, "w") as handle:
        handle["time"] = (np.asarray(jd, dtype=float) - JD_J2000) * 86400.0
        handle["xrsb_flux"] = np.asarray(flux, dtype="f4")


def velocity_table(days=40, per_day=250, noise=0.6, seed=0) -> pd.DataFrame:
    """A NEID-like table: clear days observed from 16:30 UT, with a slow daily trend and white noise."""
    rng = np.random.default_rng(seed)
    blocks = []
    for d in range(days):
        obsjd = DAY0 + d + 16.5 / 24.0 + np.arange(per_day) * CADENCE_S / 86400.0
        hours = (obsjd - obsjd.mean()) * 24.0
        rv = -645.0 + rng.normal(0.0, 0.5) * hours - 0.2 * hours**2 + rng.normal(0.0, noise, per_day)
        blocks.append(pd.DataFrame({"obsjd": obsjd, "ccfrvmod": rv / 1000.0}))
    table = pd.concat(blocks, ignore_index=True)
    table["exptime"], table["dvrms"], table["extsnr"] = 55.0, 0.0003, 400.0
    table["sunagl"], table["airmass"], table["rejected"], table["flagged"] = 50.0, 1.2, 0, 0
    table["swversion"] = "v1.5.3"
    table["l2filename"] = ["neidL2_%06d.fits" % k for k in range(len(table))]
    return table


def flare_list(days=40, every=2, first_day=4) -> pd.DataFrame:
    """One flare at 19:00 UT on every other day: 10 min of rise, alternating sides, one in four of class X."""
    rows = []
    for k, d in enumerate(range(first_day, days - 4, every)):
        start = DAY0 + d + 19.0 / 24.0
        x_class = k % 4 == 0
        rows.append(
            {
                "flare_id": 1000 + k,
                "jd_start": start,
                "jd_peak": start + 10 * MINUTE,
                "jd_end": start + 30 * MINUTE,
                "goes_class": "X1.5" if x_class else "M2.0",
                "peak_flux": 1.5e-4 if x_class else 2.0e-5,
                "x_norm": 0.5 if k % 2 else -0.5,
                "y_norm": 0.2,
            }
        )
    return pd.DataFrame(rows)


def add_signal(table: pd.DataFrame, flares: pd.DataFrame, amplitude_ms: float) -> pd.DataFrame:
    """Add a box to the velocities from the start of each flare to 2 min after its peak."""
    out = table.copy()
    mid = out["obsjd"] + 27.5 / 86400.0
    for row in flares.itertuples():
        inside = (mid >= row.jd_start) & (mid <= row.jd_peak + 2 * MINUTE)
        out.loc[inside, "ccfrvmod"] += amplitude_ms / 1000.0
    return out


def build_archive(root, signal_ms=0.0, days=40, seed=0):
    """Write a complete synthetic data directory under ``root``; returns the velocity table and the flares."""
    flares = flare_list(days)
    table = add_signal(velocity_table(days, seed=seed), flares, signal_ms)
    (root / "goes").mkdir(parents=True, exist_ok=True)
    (root / "neid").mkdir(parents=True, exist_ok=True)
    table.to_csv(root / "neid" / "neid_solar_l2.csv.gz", index=False)
    goes = root / "goes"
    write_flsum(goes / "sci_xrsf-l2-flsum_g16_s20170209_e20250407_v2-2-2.nc", flares)
    write_flloc(goes / "sci_xrsf-l2-flloc_g16_s20170209_e20250407_v2-2-2.nc", flares["flare_id"], flares["x_norm"], flares["y_norm"])
    # GOES-18: one of the same flares (a duplicate to be merged away) and a weak flare of its own.
    weak = {
        "flare_id": 9000, "jd_start": DAY0 + 1.2, "jd_peak": DAY0 + 1.21, "jd_end": DAY0 + 1.22,
        "goes_class": "B5.0", "peak_flux": 5e-7, "x_norm": 0.1, "y_norm": 0.1,
    }
    other = pd.concat([flares.iloc[[0]], pd.DataFrame([weak])], ignore_index=True)
    write_flsum(goes / "sci_xrsf-l2-flsum_g18_s20220617_e20261118_v2-2-2.nc", other)
    write_flloc(goes / "sci_xrsf-l2-flloc_g18_s20220617_e20261118_v2-2-2.nc", other["flare_id"], other["x_norm"], other["y_norm"])
    # One-minute fluxes: a rise that is steepest 6 minutes after the start of each flare.
    jd = DAY0 + np.arange(0, days * 1440) * MINUTE
    flux = np.full(len(jd), 1.0e-6)
    for row in flares.itertuples():
        minutes = (jd - row.jd_start) / MINUTE
        rise = (minutes >= 0) & (minutes <= 10)
        flux[rise] += row.peak_flux / (1.0 + np.exp(-(minutes[rise] - 6.0) * 1.5))
        decay = minutes > 10
        flux[decay] += row.peak_flux * np.exp(-(minutes[decay] - 10.0) / 15.0)
    for satellite in (16, 18):
        write_avg1m(goes / f"sci_xrsf-l2-avg1m_g{satellite}_y2023_v2-2-2.nc", jd, flux)
    return table, flares


def write_l2(path, obsjd, halpha=0.20, hbeta_depth=0.6, rv_kms=-0.64) -> None:
    """A small NEID-like level-2 file with the extensions that ``flinch.spectra.extract`` reads."""
    from astropy.io import fits

    primary = fits.PrimaryHDU()
    primary.header["OBSJD"], primary.header["EXPTIME"] = obsjd, 55.0
    primary.header["SUNAGL"], primary.header["AIRMASS"] = 50.0, 1.2
    velocity = -100.0 + 0.25 * np.arange(804)
    line = 1.0 - 0.45 * np.exp(-0.5 * ((velocity - rv_kms) / 3.3) ** 2)
    ccfs = fits.ImageHDU(np.vstack([2.0e9 * line, 1.0e9 * line, np.zeros(804)]), name="CCFS")
    ccfs.header["CCFRVMOD"], ccfs.header["DVRMSMOD"] = rv_kms, 0.0003
    ccfs.header["CCFSTART"], ccfs.header["CCFSTEP"] = -100.0, 0.25
    values = {name: 0.5 for name in INDEX_NAMES}
    values["Ha06_1_tellcorr"] = halpha
    activity = fits.BinTableHDU.from_columns(
        [
            fits.Column(name="INDEX", format="24A", array=np.array(list(values))),
            fits.Column(name="VALUE", format="D", array=np.array(list(values.values()))),
            fits.Column(name="UNCERTAINTY", format="D", array=np.full(len(values), 1.0e-4)),
        ],
        name="ACTIVITY",
    )
    wave = np.arange(3900.0, 8600.0, 0.1)
    flux = np.full(len(wave), 1000.0)
    for centre, depth, width in ((4862.68, hbeta_depth, 0.3), (5174.13, 0.7, 0.15), (3934.78, 0.8, 0.5), (6564.61, 0.8, 0.5)):
        flux *= 1.0 - depth * np.exp(-0.5 * ((wave - centre) / width) ** 2)
    hdus = [
        primary, ccfs, activity,
        fits.ImageHDU(wave, name="SCIWAVESTITCH"),
        fits.ImageHDU(flux, name="SCIFLUXSTITCH"),
        fits.ImageHDU(flux, name="SCIVARSTITCH"),
    ]
    fits.HDUList(hdus).writeto(path, overwrite=True)
