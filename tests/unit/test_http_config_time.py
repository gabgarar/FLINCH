"""Unit tests of the small support modules: HTTP helpers, paths and time conversions."""
import datetime as dt
import urllib.error

import numpy as np
import pytest

from flinch import _http, config, timeutil


def test_open_url_retries_transient_errors(monkeypatch):
    calls = []

    def fake(request, timeout, context):
        calls.append(request.full_url)
        if len(calls) < 3:
            raise OSError("connection reset")
        return "ok"

    monkeypatch.setattr(_http.urllib.request, "urlopen", fake)
    monkeypatch.setattr(_http.time, "sleep", lambda seconds: None)
    assert _http.open_url("https://example.org/x", {"query": "a b"}) == "ok"
    assert len(calls) == 3
    assert calls[0] == "https://example.org/x?query=a+b"


def test_open_url_does_not_retry_a_client_error(monkeypatch):
    calls = []

    def fake(request, timeout, context):
        calls.append(1)
        raise urllib.error.HTTPError(request.full_url, 404, "Not Found", {}, None)

    monkeypatch.setattr(_http.urllib.request, "urlopen", fake)
    with pytest.raises(urllib.error.HTTPError):
        _http.open_url("https://example.org/missing")
    assert len(calls) == 1


def test_open_url_gives_up_after_the_retries(monkeypatch):
    def fake(request, timeout, context):
        raise OSError("no route")

    monkeypatch.setattr(_http.urllib.request, "urlopen", fake)
    monkeypatch.setattr(_http.time, "sleep", lambda seconds: None)
    with pytest.raises(ConnectionError, match="could not fetch"):
        _http.open_url("https://example.org/x", retries=2)


def test_download_is_atomic_and_skips_existing_files(tmp_path):
    source = tmp_path / "source.bin"
    source.write_bytes(b"first")
    destination = tmp_path / "sub" / "copy.bin"
    assert _http.download(source.as_uri(), destination) == destination
    assert destination.read_bytes() == b"first"
    assert not list(destination.parent.glob("*.part"))
    source.write_bytes(b"second")
    _http.download(source.as_uri(), destination)
    assert destination.read_bytes() == b"first"  # kept: the file was already there
    _http.download(source.as_uri(), destination, overwrite=True)
    assert destination.read_bytes() == b"second"
    assert _http.fetch_text(source.as_uri()) == "second"


def test_data_dir_follows_the_environment_variable(tmp_path, monkeypatch):
    monkeypatch.setenv("FLINCH_DATA", str(tmp_path / "elsewhere"))
    assert config.data_dir() == tmp_path / "elsewhere"
    assert (tmp_path / "elsewhere").is_dir()
    monkeypatch.delenv("FLINCH_DATA")
    assert config.data_dir() == config.REPO_ROOT / "data"


def test_results_and_figures_live_in_the_repository():
    assert config.results_dir() == config.REPO_ROOT / "results"
    assert config.figures_dir() == config.REPO_ROOT / "docs" / "web" / "img"


def test_julian_date_conversions_round_trip():
    when = dt.datetime(2024, 5, 14, 16, 51)
    jd = timeutil.datetime_to_jd(when)
    assert jd == pytest.approx(2460445.202083, abs=1e-6)
    assert timeutil.jd_to_datetime(jd).round("s") == when
    many = timeutil.jd_to_datetime(np.array([jd, jd + 1.0]))
    assert (many[1] - many[0]).total_seconds() == pytest.approx(86400.0)
    assert timeutil.year_start_jd(2000) == pytest.approx(timeutil.JD_J2000 - 0.5)
    assert timeutil.MINUTE * 1440 == pytest.approx(1.0)
