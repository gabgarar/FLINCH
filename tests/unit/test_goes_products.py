"""Unit tests of the GOES products beyond the flare summary: positions, one-minute fluxes, merged list."""
import numpy as np
import pytest

import helpers
from flinch import goes
from flinch.timeutil import MINUTE


def test_read_flloc_normalises_positions_and_blanks_the_limb(tmp_path):
    path = tmp_path / "flloc.nc"
    helpers.write_flloc(path, [1, 2, 3], x_norm=[0.5, -0.8, 0.95], y_norm=[0.0, 0.3, 0.6])
    table = goes.read_flloc(path).set_index("flare_id")
    assert table.loc[1, "x_norm"] == pytest.approx(0.5, abs=1e-4)
    assert table.loc[1, "lon"] == pytest.approx(30.0, abs=0.01)
    assert table.loc[2, "r_norm"] == pytest.approx(np.hypot(0.8, 0.3), abs=1e-4)
    # the third flare is beyond the limb: a position on the sky but no heliographic coordinates
    assert table.loc[3, "r_norm"] > 1.0
    assert np.isnan(table.loc[3, "lon"]) and np.isnan(table.loc[3, "car_lon"])


def test_find_product_url_takes_the_file_with_the_latest_end_date(monkeypatch):
    listing = (
        '<a href="sci_xrsf-l2-flsum_g18_s20220617_e20260101_v2-2-2.nc">a</a>'
        '<a href="sci_xrsf-l2-flsum_g18_s20220617_e20261118_v2-2-2.nc">b</a>'
        '<a href="sci_xrsf-l2-flsum_g18_y2025_v2-2-2.nc">yearly</a>'
    )
    monkeypatch.setattr(goes, "fetch_text", lambda url: listing)
    url = goes.find_product_url(18, "flsum")
    assert url.endswith("goes18/l2/data/xrsf-l2-flsum_science/sci_xrsf-l2-flsum_g18_s20220617_e20261118_v2-2-2.nc")
    monkeypatch.setattr(goes, "fetch_text", lambda url: "<html>nothing here</html>")
    with pytest.raises(RuntimeError, match="no mission-long"):
        goes.find_product_url(18, "flsum")


def test_load_flares_merges_the_two_satellites(archive):
    flares = goes.load_flares()
    expected = archive["flares"]
    major = flares[flares["goes_class"].str[0].isin(["M", "X"])]
    assert len(major) == len(expected)  # the GOES-18 copy of the first flare is merged away
    assert set(major["satellite"]) == {16}
    assert (flares["goes_class"] == "B5.0").sum() == 1  # the flare that only GOES-18 saw
    assert np.allclose(np.sort(major["x_norm"].abs()), 0.5, atol=1e-4)
    assert {"jd_start", "jd_peak", "jd_end", "peak_flux", "fluence", "r_norm", "car_lon", "peak"} <= set(flares.columns)


def test_load_flares_needs_the_downloads(tmp_path):
    with pytest.raises(FileNotFoundError, match="flinch download"):
        goes.load_flares(tmp_path)


def test_impulsive_time_is_the_steepest_rise(archive):
    flares = goes.add_impulsive_time(goes.load_flares())
    major = flares[flares["goes_class"].str[0].isin(["M", "X"])]
    delay = (major["jd_impulsive"] - major["jd_start"]) / MINUTE
    # the synthetic light curves rise fastest 6 minutes after the start
    assert major["jd_impulsive"].notna().all()
    assert np.all(np.abs(delay - 6.0) <= 1.6)
    assert (major["jd_impulsive"] < major["jd_peak"]).all()


def test_impulsive_time_is_missing_without_one_minute_data(archive, tmp_path, monkeypatch):
    def offline(url):
        raise ConnectionError("no network in the tests")

    monkeypatch.setattr(goes, "fetch_text", offline)  # an empty folder and no archive to download from
    flares = goes.add_impulsive_time(goes.load_flares(), directory=tmp_path)
    assert flares["jd_impulsive"].isna().all()
