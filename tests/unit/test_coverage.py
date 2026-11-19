import numpy as np
import pandas as pd

from flinch import coverage
from flinch.timeutil import MINUTE


def flare_table(peaks, starts, classes):
    return pd.DataFrame({"jd_peak": peaks, "jd_start": starts, "goes_class": classes})


def test_count_between_is_inclusive():
    times = np.array([1.0, 2.0, 3.0, 4.0])
    assert coverage.count_between(times, 2.0, 3.0) == 2
    assert coverage.count_between(times, 4.5, 9.0) == 0
    assert list(coverage.count_between(times, np.array([0.0, 2.5]), np.array([1.0, 4.0]))) == [1, 2]


def test_class_band():
    assert coverage.class_band("X8.5") == "X"
    assert coverage.class_band("M5.0") == "M5-M9"
    assert coverage.class_band("M4.9") == "M1-M4"
    assert coverage.class_band("C3.0") == "C"


def test_coverage_flags():
    # One observation every 83 s from one hour before to one hour after t = 100.
    observed = 100.0 + np.arange(-3600.0, 3600.0, 83.0) / 86400.0
    flares = flare_table(
        peaks=[100.0, 100.0 + 58.0 * MINUTE, 300.0, 100.0 - 58.0 * MINUTE],
        starts=[100.0 - 10.0 * MINUTE, 100.0 + 50.0 * MINUTE, 299.99, np.nan],
        classes=["X1.0", "M2.0", "M6.0", "M1.0"],
    )
    out = coverage.add_coverage(flares, observed)
    # Fully covered; observed at the peak but the run ends 2 min later; never observed;
    # observed at the peak but the run started 2 min before it (start unknown -> peak - 10 min).
    assert list(out["at_peak"]) == [True, True, False, True]
    assert list(out["well_covered"]) == [True, False, False, False]
    assert out.loc[0, "n_pre"] >= 20 and out.loc[0, "n_post"] >= 20

    summary = coverage.summarize(out).set_index("band")
    assert summary.loc["X", ["total", "at_peak", "well_covered"]].tolist() == [1, 1, 1]
    assert summary.loc["M1-M4", ["total", "at_peak", "well_covered"]].tolist() == [2, 2, 0]
    assert summary.loc["M5-M9", ["total", "at_peak", "well_covered"]].tolist() == [1, 0, 0]
