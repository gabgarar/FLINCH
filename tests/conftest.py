import pytest

import helpers


@pytest.fixture
def archive(tmp_path, monkeypatch):
    """A synthetic data directory without any flare signal; results and figures go to the temporary folder."""
    table, flares = helpers.build_archive(tmp_path / "data")
    _redirect(tmp_path, monkeypatch)
    return {"root": tmp_path, "table": table, "flares": flares}


@pytest.fixture
def archive_with_signal(tmp_path, monkeypatch):
    """The same, with 1.5 m/s added to the velocity during every flare."""
    table, flares = helpers.build_archive(tmp_path / "data", signal_ms=1.5)
    _redirect(tmp_path, monkeypatch)
    return {"root": tmp_path, "table": table, "flares": flares}


def _redirect(tmp_path, monkeypatch):
    import flinch.__main__ as cli
    import flinch.campaign as campaign

    monkeypatch.setenv("FLINCH_DATA", str(tmp_path / "data"))
    for module in (cli, campaign):
        monkeypatch.setattr(module, "results_dir", lambda: _made(tmp_path / "results"))
    monkeypatch.setattr(cli, "figures_dir", lambda: _made(tmp_path / "figures"))


def _made(path):
    path.mkdir(parents=True, exist_ok=True)
    return path
