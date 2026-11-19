import h5py
import numpy as np
import pandas as pd
import pytest

from flinch import goes
from flinch.timeutil import JD_J2000, MINUTE


def write_flsum(path, records):
    """Write a minimal flare summary file: records are (seconds, status, class, flux, fluence, id)."""
    seconds, status, classes, flux, fluence, ids = zip(*records)
    with h5py.File(path, "w") as handle:
        handle["time"] = np.array(seconds, dtype="f8")
        handle.create_dataset("status", data=np.array(status, dtype=object), dtype=h5py.string_dtype())
        handle.create_dataset("flare_class", data=np.array(classes, dtype=object), dtype=h5py.string_dtype())
        handle["xrsb_flux"] = np.array(flux, dtype="f4")
        handle["integrated_flux"] = np.array(fluence, dtype="f4")
        handle["flare_id"] = np.array(ids, dtype="i8")


def test_class_flux_round_trip():
    assert goes.class_to_flux("M5.2") == pytest.approx(5.2e-5)
    assert goes.class_to_flux("X8.5") == pytest.approx(8.5e-4)
    assert goes.flux_to_class(8.5e-4) == "X8.5"
    assert goes.flux_to_class(1.0e-5) == "M1.0"
    assert goes.flux_to_class(3.7e-7) == "B3.7"


def test_read_flsum_pairs_start_peak_end(tmp_path):
    path = tmp_path / "sci_xrsf-l2-flsum_g16_s20170209_e20250407_v2-2-2.nc"
    write_flsum(
        path,
        [
            (0.0, "EVENT_START", "", 1e-6, 0.0, 1),
            (600.0, "EVENT_PEAK", "M2.0", 2e-5, 0.0, 1),
            (1800.0, "EVENT_END", "", 5e-6, 0.03, 1),
            (86400.0, "EVENT_START", "", 1e-6, 0.0, 2),
            (86700.0, "EVENT_PEAK", "X1.5", 1.5e-4, 0.0, 2),  # no end marker: still running
        ],
    )
    flares = goes.read_flsum(path)
    assert list(flares["goes_class"]) == ["M2.0", "X1.5"]
    assert set(flares["satellite"]) == {16}
    first = flares.iloc[0]
    assert first["jd_start"] == pytest.approx(JD_J2000)
    assert first["jd_peak"] == pytest.approx(JD_J2000 + 600.0 / 86400.0)
    assert first["jd_end"] == pytest.approx(JD_J2000 + 1800.0 / 86400.0)
    assert first["fluence"] == pytest.approx(0.03)
    assert np.isnan(flares.iloc[1]["jd_end"])


def test_merge_keeps_primary_and_adds_only_new_flares():
    primary = pd.DataFrame({"jd_peak": [100.0, 200.0], "goes_class": ["M1.0", "X1.0"], "satellite": 16})
    secondary = pd.DataFrame(
        {
            "jd_peak": [100.0 + 1.0 * MINUTE, 150.0, 200.0 - 2.0 * MINUTE],
            "goes_class": ["M1.1", "M3.0", "X1.1"],
            "satellite": 18,
        }
    )
    merged = goes.merge_flare_lists(primary, secondary)
    assert list(merged["goes_class"]) == ["M1.0", "M3.0", "X1.0"]
    assert list(merged["satellite"]) == [16, 18, 16]


def test_merge_drops_a_peak_inside_a_primary_flare_window():
    # A long flare: the secondary satellite places its peak 20 minutes later than the primary.
    primary = pd.DataFrame(
        {"jd_start": [100.0], "jd_peak": [100.0 + 10 * MINUTE], "jd_end": [100.0 + 60 * MINUTE], "goes_class": ["M2.0"]}
    )
    secondary = pd.DataFrame(
        {
            "jd_start": [100.0, 101.0],
            "jd_peak": [100.0 + 30 * MINUTE, 101.0 + 5 * MINUTE],
            "jd_end": [100.0 + 60 * MINUTE, 101.0 + 20 * MINUTE],
            "goes_class": ["M2.1", "C5.0"],
        }
    )
    merged = goes.merge_flare_lists(primary, secondary)
    assert list(merged["goes_class"]) == ["M2.0", "C5.0"]
