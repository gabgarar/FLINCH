"""Unit tests of the campaign bookkeeping, the figures and the command line."""
import numpy as np
import pandas as pd
import pytest

from flinch import campaign, plots, response
from flinch.__main__ import main
from flinch.timeutil import MINUTE, datetime_to_jd

import datetime as dt


def test_event_and_control_names():
    row = pd.Series({"jd_peak": datetime_to_jd(dt.datetime(2026, 1, 18, 18, 9)), "goes_class": "X1.9"})
    assert campaign.event_name(row) == "20260118_1809_X1.9"
    control = pd.Series({"parent": "20260118_1809_X1.9", "shift_days": -2.0})
    assert campaign.control_name(control) == "20260118_1809_X1.9_control-2d"
    assert campaign.control_name(pd.Series({"parent": "x", "shift_days": 1.0})) == "x_control+1d"


def test_manifest_accumulates_and_replaces_by_name(archive):
    campaign.write_manifest([{"name": "a", "kind": "flares", "jd_peak": 1.0}, {"name": "b", "kind": "flares", "jd_peak": 2.0}])
    campaign.write_manifest([{"name": "b", "kind": "flares", "jd_peak": 3.0}, {"name": "c", "kind": "controls", "jd_peak": 4.0}])
    manifest = pd.read_csv(archive["root"] / "data" / "spectra" / "events.csv").set_index("name")
    assert list(manifest.index) == ["a", "b", "c"] and manifest.loc["b", "jd_peak"] == 3.0


def test_select_events_lists_the_observed_flares_strongest_first(archive):
    events = campaign.select_events()
    assert len(events) == len(archive["flares"])  # every synthetic flare happens while observing
    assert events["peak_flux"].is_monotonic_decreasing
    assert events["at_peak"].all() and (events["n_rise"] >= 3).all()
    assert campaign.select_events(min_class="X1.0")["goes_class"].str[0].eq("X").all()


def test_control_events_are_quiet_days_at_the_same_time(archive):
    events = campaign.select_events().head(5)
    controls = campaign.control_events(events)
    assert len(controls) == 5
    majors = archive["flares"]["jd_peak"].to_numpy()
    for control in controls.itertuples():
        assert abs(control.shift_days) == 1  # flares fall on every other day: the next day is free
        assert np.abs(majors - control.jd_peak).min() > 60 * MINUTE
        assert (control.jd_peak - control.jd_start) / MINUTE == pytest.approx(10.0)
        assert campaign.control_name(control).startswith(control.parent)


def test_keep_awake_does_not_fail():
    campaign.keep_awake(True)
    campaign.keep_awake(False)


def _is_png(path):
    return path.exists() and path.stat().st_size > 2000 and path.read_bytes()[:4] == b"\x89PNG"


def test_velocity_figures(tmp_path):
    rng = np.random.default_rng(0)
    minutes = np.arange(-57.5, 90, 5.0)
    profiles = pd.concat(
        [
            pd.DataFrame({"subset": subset, "sample": sample, "events": 20, "minutes": minutes, "mean": rng.normal(0, 0.05, len(minutes)), "sem": 0.04, "n": 20})
            for subset in ("M and X", "X")
            for sample in ("flares", "controls")
        ]
    )
    assert _is_png(plots.plot_profiles(profiles, tmp_path / "a" / "profiles.png"))
    flares = pd.DataFrame(
        {"peak_flux": 10 ** rng.uniform(-5, -3.5, 60), "delta": rng.normal(0, 0.4, 60), "x_norm": rng.uniform(-1, 1, 60), "r_norm": rng.uniform(0, 1, 60)}
    )
    controls = pd.DataFrame({"delta": rng.normal(0, 0.4, 300)})
    assert _is_png(plots.plot_events(flares, controls, tmp_path / "events.png"))


def test_data_and_event_figures(tmp_path):
    rng = np.random.default_rng(1)
    jd = 2460000.9 + np.arange(150) * MINUTE
    flare = {"jd_start": jd[40], "jd_impulsive": jd[55], "jd_peak": jd[60], "goes_class": "X1.0", "peak": pd.Timestamp("2023-02-25")}
    assert _is_png(plots.plot_goes_example(jd, 1e-6 + 1e-4 * np.exp(-0.5 * ((np.arange(150) - 60) / 10.0) ** 2), flare, tmp_path / "goes.png"))
    day = pd.DataFrame({"jd": 2460000.2 + np.arange(200) * 83.0 / 86400.0, "rv_ms": -645 + rng.normal(0, 0.8, 200), "good": rng.random(200) > 0.2})
    assert _is_png(plots.plot_neid_day(day, tmp_path / "day.png"))
    wave = np.linspace(6558.0, 6571.0, 400)
    assert _is_png(plots.plot_contrast(wave, 0.005 * np.exp(-0.5 * ((wave - 6564.61) / 0.4) ** 2), np.full(400, 0.001), 6564.61, "H alpha", tmp_path / "contrast.png"))
    time = np.arange(-30.0, 30.0, 3.0)
    change = pd.DataFrame({"min_peak": time - 5.0, "min_start": time})
    for column, _, _ in response.QUANTITIES:
        change[column] = rng.normal(0, 1, len(time))
        change[f"{column}_sigma"] = 1.0
    assert _is_png(plots.plot_event(change, "A synthetic flare", tmp_path / "event.png"))


def test_command_line_parsing(capsys):
    with pytest.raises(SystemExit) as stop:
        main(["--help"])
    assert stop.value.code == 0
    listed = capsys.readouterr().out
    for command in ("download", "coverage", "pilot", "robustness", "spectra", "campaign"):
        assert command in listed
    with pytest.raises(SystemExit) as stop:
        main([])  # a command is required
    assert stop.value.code == 2
    with pytest.raises(SystemExit):
        main(["campaign", "--kind", "nonsense"])


def test_coverage_command_writes_the_sample(archive, capsys):
    assert main(["coverage"]) == 0
    printed = capsys.readouterr().out
    assert f"M and X flares in the NEID era: {len(archive['flares'])}" in printed
    sample = pd.read_csv(archive["root"] / "results" / "flare_sample.csv")
    assert len(sample) == len(archive["flares"]) and sample["well_covered"].all()


def test_select_events_with_a_class_ceiling(archive):
    below = campaign.select_events(min_class="M1.0", max_class="X1.0")
    above = campaign.select_events(min_class="X1.0")
    assert len(below) and below["goes_class"].str[0].eq("M").all()
    assert len(below) + len(above) == len(campaign.select_events())


def test_clear_sky_needs_steady_spectra_before_the_start_and_around_the_peak():
    cadence = 83.0 / 86400.0
    start, peak = 2460000.5, 2460000.5 + 12 * MINUTE
    events = pd.DataFrame({"jd_start": [start, start + 1.0, np.nan], "jd_peak": [peak, peak + 1.0, peak + 2.0]})
    steady = np.concatenate(
        [
            np.arange(start - 30 * MINUTE, peak + 15 * MINUTE, cadence),  # first flare: clear throughout
            np.arange(start + 1.0 - 30 * MINUTE, start + 1.0, cadence),  # second: cloud from its start on
            np.arange(peak + 2.0 - 3 * MINUTE, peak + 2.0 + 15 * MINUTE, cadence),  # third (no start time): nothing before
        ]
    )
    assert list(campaign.clear_sky(events, np.sort(steady))) == [True, False, False]


def _is_pdf(path):
    return path.exists() and path.stat().st_size > 5000 and path.read_bytes()[:5] == b"%PDF-"


def test_paper_figures_are_vector_files_at_the_size_of_the_page(tmp_path):
    from flinch import paperfigs

    rng = np.random.default_rng(2)
    minutes = np.arange(-55.0, 90, 10.0)
    profiles = pd.concat(
        [
            pd.DataFrame({"instrument": instrument, "subset": subset, "sample": sample, "events": 20, "minutes": minutes,
                          "mean": rng.normal(0, 0.05, len(minutes)), "sem": 0.04, "n": 20})
            for instrument in ("NEID", "HARPS-N")
            for subset in ("M and X", "X")
            for sample in ("flares", "controls")
        ]
    )
    assert _is_pdf(paperfigs.profiles(profiles, tmp_path / "a" / "profiles.pdf"))
    assert _is_pdf(paperfigs.profiles(profiles, tmp_path / "a" / "profiles_x.pdf", subset="X"))
    flares = pd.DataFrame(
        {"instrument": np.where(rng.random(60) < 0.5, "NEID", "HARPS-N"), "sample": "flare", "peak_flux": 10 ** rng.uniform(-5, -3.0, 60),
         "d": rng.normal(0, 0.4, 60), "delta": rng.normal(0, 0.4, 60), "x_norm": rng.uniform(-1, 1, 60), "r_norm": rng.uniform(0, 1, 60)}
    )
    controls = pd.DataFrame({"instrument": "NEID", "sample": "control", "delta": rng.normal(0, 0.4, 300)})
    assert _is_pdf(paperfigs.events(pd.concat([flares, controls], ignore_index=True), tmp_path / "events.pdf"))
    curves = pd.concat(
        [
            pd.DataFrame({"group": group, "quantity": column, "events": 8, "minutes": np.arange(-37.0, 45, 6.0),
                          "mean": rng.normal(0, 1, 14), "sem": 0.5, "n": 8})
            for group in ("disc flares", "limb flares", "controls")
            for column, _ in paperfigs.CURVE_PANELS
        ]
    )
    assert _is_pdf(paperfigs.light_curves(curves, tmp_path / "curves.pdf"))
    time = np.arange(-30.0, 30.0, 3.0)
    change = pd.DataFrame({"min_peak": time - 5.0, "min_start": time})
    for column, _, _ in paperfigs.EVENT_QUANTITIES:
        change[column] = rng.normal(0, 1, len(time))
        change[f"{column}_sigma"] = 1.0
    assert _is_pdf(paperfigs.event(change, tmp_path / "event.pdf"))
    assert {column for column, _, _ in paperfigs.EVENT_QUANTITIES} <= {column for column, _, _ in response.QUANTITIES}
    assert paperfigs.style()["font.size"] <= 9 and paperfigs.COLUMN_MM == 88.0 and paperfigs.PAGE_MM == 180.0


def test_binned_means_leave_out_sparse_bins():
    from flinch import paperfigs

    x = np.array([0.1, 0.2, 0.3, 0.4, 1.5, 2.2, 2.4, 2.6])
    y = np.array([1.0, 2.0, 3.0, 2.0, 9.0, 4.0, 5.0, 6.0])
    centres, means, errors = paperfigs.binned_means(x, y, np.array([0.0, 1.0, 2.0, 3.0]))
    # The middle bin has one point only; a bin with positive edges is centred on their geometric mean.
    assert centres == pytest.approx([0.5, np.sqrt(6.0)])
    assert list(means) == [2.0, 5.0] and errors[1] == pytest.approx(1.0 / np.sqrt(3.0))


def test_method_example_figure(tmp_path):
    from flinch import paperfigs

    rng = np.random.default_rng(3)
    time = np.arange(-60.0, 30.0, 1.4)
    day = {
        "title": "A synthetic day", "start_min": -15.0, "before": (-55.0, -20.0), "during": (-15.0, 2.0),
        "xray_min": np.arange(-60.0, 30.0), "xray_flux": 1.0e-6 + 1.0e-4 * np.exp(-0.5 * (np.arange(-60.0, 30.0) / 8.0) ** 2),
        "min": time, "velocity": rng.normal(0.0, 0.8, len(time)),
    }
    assert _is_pdf(paperfigs.method_example({"flare": day, "control": dict(day, title="A synthetic control")}, tmp_path / "method.pdf"))
