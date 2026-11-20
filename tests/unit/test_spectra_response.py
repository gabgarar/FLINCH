"""Unit tests of the spectrum extraction and of the response of single events."""
import shutil

import numpy as np
import pandas as pd
import pytest

import helpers
from flinch import response, spectra
from flinch.timeutil import MINUTE

T0 = 2460004.29


@pytest.fixture
def window(tmp_path):
    """Twelve synthetic spectra, 83 s apart; the H alpha index and the H beta core rise in the last six."""
    directory = tmp_path / "event"
    directory.mkdir()
    times = T0 + np.arange(12) * 83.0 / 86400.0
    for k, obsjd in enumerate(times):
        raw = tmp_path / f"neidL2_{k:02d}.fits"
        flaring = k >= 6
        helpers.write_l2(raw, obsjd, halpha=0.21 if flaring else 0.20, hbeta_depth=0.57 if flaring else 0.60)
        np.savez_compressed(directory / f"neidL2_{k:02d}.npz", **spectra.extract(raw))
    return directory, times


def test_extract_keeps_headers_indices_ccf_and_line_windows(tmp_path):
    raw = tmp_path / "neidL2_x.fits"
    helpers.write_l2(raw, T0, halpha=0.2072)
    out = spectra.extract(raw)
    assert float(out["obsjd"]) == pytest.approx(T0, abs=1e-8) and float(out["exptime"]) == 55.0
    assert float(out["ccfrvmod"]) == pytest.approx(-0.64) and float(out["ccfstep"]) == 0.25
    names = [str(n) for n in out["activity_names"]]
    assert out["activity_values"][names.index("Ha06_1_tellcorr")] == pytest.approx(0.2072)
    assert out["ccf"].shape == (804,) and out["ccf"].argmin() == np.argmin(np.abs(-100 + 0.25 * np.arange(804) + 0.64))
    for name, (low, high) in spectra.LINE_WINDOWS.items():
        wave = out[f"{name}_wave"]
        assert low <= wave.min() and wave.max() < high and len(out[f"{name}_flux"]) == len(wave)


def test_load_window_stacks_the_extracts(window):
    directory, times = window
    table, arrays = spectra.load_window(directory)
    assert len(table) == 12 and np.allclose(table["obsjd"], times, atol=1e-8)
    assert np.allclose(table["jd"] - table["obsjd"], 27.5 / 86400.0)
    assert table["rv_ms"].iloc[0] == pytest.approx(-640.0)
    assert arrays["ccf"].shape == (12, 804)
    assert arrays["Halpha_flux"].shape[0] == 12 and arrays["Halpha_wave"].shape == arrays["Halpha_flux"].shape


def test_retry_waits_for_a_locked_file(monkeypatch):
    monkeypatch.setattr(spectra.time, "sleep", lambda seconds: None)
    attempts = []

    def action():
        attempts.append(1)
        if len(attempts) < 3:
            raise PermissionError("in use")
        return "done"

    assert spectra._retry(action) == "done" and len(attempts) == 3
    with pytest.raises(PermissionError):
        spectra._retry(lambda: (_ for _ in ()).throw(PermissionError("always")), attempts=2)


def test_fetch_one_extracts_deletes_the_file_and_skips_what_exists(tmp_path, monkeypatch):
    remote = tmp_path / "remote"
    remote.mkdir()
    helpers.write_l2(remote / "neidL2_a.fits", T0)
    calls = []

    def fake_download(url, destination, overwrite=False):
        calls.append(url)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(remote / destination.name, destination)
        return destination

    monkeypatch.setattr(spectra, "download", fake_download)
    out, scratch = tmp_path / "out", tmp_path / "scratch"
    out.mkdir()
    extract = spectra.fetch_one("sci/2024/x/neidL2_a.fits", "neidL2_a.fits", out, scratch)
    assert extract == out / "neidL2_a.npz" and extract.exists()
    assert not (scratch / "neidL2_a.fits").exists()  # the 113 MB file is not kept
    assert calls == [f"{spectra.FILE_URL}?filehand=sci/2024/x/neidL2_a.fits&solar"]
    spectra.fetch_one("sci/2024/x/neidL2_a.fits", "neidL2_a.fits", out, scratch)
    assert len(calls) == 1  # already extracted: no second download


def test_event_table_changes_and_response(window):
    directory, times = window
    start = times[6] - 20.0 / 86400.0  # the flare starts just before the seventh spectrum
    peak = start + 5 * MINUTE
    table = response.event_table(directory, start, peak)
    assert len(table) == 12 and {"ccf_depth", "ccf_bis_ms", "Hbeta_core", "MgIb2_core", "min_start"} <= set(table.columns)
    change = response.changes(table)
    assert change["pre_flare"].sum() == 4  # the next two are within 2 minutes of the start: not baseline
    after = change["min_start"] > 0
    assert change.loc[after, "Ha06_1_tellcorr"].to_numpy() == pytest.approx(50.0, abs=1e-6)  # +5 % in parts per thousand
    assert change.loc[after, "Hbeta_core"].mean() > 20.0  # a shallower line: a brighter core
    assert change.loc[after, "CaI_1_tellcorr"].abs().max() == pytest.approx(0.0, abs=1e-9)
    assert change.loc[after, "rv_ms"].abs().max() == pytest.approx(0.0, abs=1e-9)
    measured = response.event_response(change, window_min=(-8.0, 10.0))
    # the window holds the two spectra just before the start (no change) and the six after it
    assert measured["n_before"] == 4 and measured["n_window"] == 8
    assert measured["Ha06_1_tellcorr"] == pytest.approx(50.0 * 6 / 8, abs=1e-6)


def test_event_table_keeps_only_the_listed_spectra(window):
    directory, times = window
    keep = np.sort(times[::2])
    table = response.event_table(directory, times[0], times[3], keep_obsjd=keep)
    assert len(table) == 6 and np.allclose(table["obsjd"], keep, atol=1e-8)
    empty = response.event_table(directory, times[0], times[3], keep_obsjd=np.array([1.0, 2.0]))
    assert len(empty) == 0


def test_changes_can_remove_a_linear_drift():
    time = np.arange(-30.0, 20.0, 2.0)
    table = pd.DataFrame({"jd": time, "min_start": time, "min_peak": time - 5.0})
    for column, _, _ in response.QUANTITIES:
        table[column] = 1.0 + 0.001 * time  # a slow drift and nothing else
    table.loc[table["min_start"] > 0, "Ha06_1_tellcorr"] += 0.01
    flat = response.changes(table, detrend=True)
    after = flat["min_start"] > 0
    assert flat.loc[after, "CaIIHK"].abs().max() < 0.05  # the drift is gone, in parts per thousand
    assert flat.loc[after, "Ha06_1_tellcorr"].mean() == pytest.approx(10.0, rel=0.05)
    drifting = response.changes(table, detrend=False)
    assert drifting.loc[after, "CaIIHK"].mean() > 10.0  # without detrending the drift looks like a response


def test_response_needs_enough_spectra():
    time = np.array([-20.0, -10.0, 4.0])
    table = pd.DataFrame({"jd": time, "min_start": time, "min_peak": time - 5.0})
    for column, _, _ in response.QUANTITIES:
        table[column] = 1.0
    measured = response.event_response(response.changes(table))
    assert measured["n_window"] == 1 and np.isnan(measured["Ha06_1_tellcorr"])


def test_collect_measures_the_events_that_have_spectra(window, tmp_path):
    directory, times = window
    start = times[6] - 20.0 / 86400.0
    events = pd.DataFrame(
        {"name": ["event", "missing"], "jd_start": [start, start], "jd_peak": [start + 5 * MINUTE] * 2, "goes_class": ["X1.0", "M1.0"]}
    )
    out = response.collect(events, tmp_path)
    assert list(out["name"]) == ["event"] and out.loc[0, "goes_class"] == "X1.0"
    assert out.loc[0, "n_spectra"] == 12 and out.loc[0, "Ha06_1_tellcorr"] == pytest.approx(50.0 * 6 / 8, abs=1e-6)
