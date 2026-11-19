import numpy as np
import pandas as pd
import pytest

from flinch import epoch
from flinch.timeutil import MINUTE

T0 = 2460000.25  # an arbitrary afternoon


def observations(hours=6.0, cadence_s=83.0):
    return T0 + np.arange(0.0, hours * 3600.0, cadence_s) / 86400.0


def test_series_window_counts_and_means():
    series = epoch.Series([3.0, 1.0, 2.0, 4.0], [30.0, 10.0, 20.0, 40.0])
    count, mean = series.window(np.array([1.0, 2.5, 9.0]), np.array([2.0, 4.0, 10.0]))
    assert list(count) == [2, 2, 0]
    assert mean[0] == pytest.approx(15.0) and mean[1] == pytest.approx(35.0) and np.isnan(mean[2])


def test_measure_recovers_a_box_signal():
    jd = observations()
    start, peak = T0 + 120 * MINUTE, T0 + 135 * MINUTE
    values = np.where((jd >= start) & (jd <= peak + 2 * MINUTE), 1.0, 0.0)
    events = pd.DataFrame({"jd_start": [start, np.nan], "jd_peak": [peak, T0 + 900 * MINUTE]})
    out = epoch.measure(events, epoch.Series(jd, values))
    assert out.loc[0, "measured"] and out.loc[0, "measured_two_sided"]
    assert out.loc[0, "delta"] == pytest.approx(1.0)
    assert out.loc[0, "delta_two_sided"] == pytest.approx(1.0)
    assert out.loc[0, "delta_decay"] == pytest.approx(0.0, abs=0.06)  # only the first sample of the window
    assert out.loc[0, "rise_min"] == pytest.approx(15.0)
    assert not out.loc[1, "measured"]  # outside the observed interval


def test_profiles_are_relative_to_the_pre_event_mean():
    jd = observations()
    start, peak = T0 + 120 * MINUTE, T0 + 130 * MINUTE
    values = 5.0 + np.where((jd >= peak) & (jd < peak + 10 * MINUTE), 2.0, 0.0)
    events = pd.DataFrame({"jd_start": [start], "jd_peak": [peak]})
    profile = epoch.profiles(events, epoch.Series(jd, values), edges_min=[-20, -10, 0, 10, 20])
    assert profile.shape == (1, 4)
    assert profile[0] == pytest.approx([0.0, 0.0, 2.0, 0.0])


def test_controls_keep_the_time_of_day_and_avoid_major_flares():
    flares = pd.DataFrame(
        {"jd_start": [T0], "jd_peak": [T0 + 10 * MINUTE], "goes_class": ["X1.0"], "peak_flux": [1e-4], "x_norm": [0.5]}
    )
    major = [T0 + 10 * MINUTE, T0 + 3.0 + 30 * MINUTE, T0 - 2.0 - 100 * MINUTE]
    controls = epoch.draw_controls(flares, major, max_shift_days=5)
    shifts = sorted(controls["shift_days"])
    # +3 days is excluded (a major flare 20 minutes after the control peak); -2 days is kept
    # (the flare there is 100 minutes before the control start, outside the 45-minute margin).
    assert shifts == [-5.0, -4.0, -3.0, -2.0, -1.0, 1.0, 2.0, 4.0, 5.0]
    assert np.allclose((controls["jd_peak"] - controls["jd_start"]) / MINUTE, 10.0)
    assert np.allclose(((controls["jd_peak"] - flares.loc[0, "jd_peak"]) % 1.0 + 0.5) % 1.0, 0.5)
    assert set(controls["goes_class"]) == {"X1.0"}


def test_select_controls_limits_the_number_per_flare():
    controls = pd.DataFrame(
        {"parent": [0, 0, 0, 1, 1], "rank": [0.9, 0.1, 0.5, 0.3, 0.2], "measured": [True, True, True, False, True]}
    )
    chosen = epoch.select_controls(controls, per_flare=2)
    assert list(chosen["parent"]) == [0, 0, 1]
    assert list(chosen["rank"]) == [0.1, 0.5, 0.2]


def test_scaled_amplitude_and_mean():
    weight = np.array([1.0, 2.0, 3.0, np.nan])
    amplitude, error = epoch.scaled_amplitude(0.2 * weight, weight, sigma=0.3)
    assert amplitude == pytest.approx(0.2)
    assert error == pytest.approx(0.3 / np.sqrt(14.0))
    mean, sem, n = epoch.mean_and_error([1.0, 2.0, 3.0, np.nan])
    assert (mean, n) == (pytest.approx(2.0), 3)
    assert sem == pytest.approx(1.0 / np.sqrt(3.0))
