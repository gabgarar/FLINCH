import numpy as np
import pandas as pd

from flinch import quality


def synthetic_day(day_jd=2460000.2, n=250, noise=0.5, seed=1):
    rng = np.random.default_rng(seed)
    jd = day_jd + np.arange(n) * 83.0 / 86400.0
    hours = (jd - jd.mean()) * 24.0
    rv = -645.0 + 0.8 * hours - 0.3 * hours**2 + rng.normal(0.0, noise, n)
    return pd.DataFrame(
        {"obsjd": jd, "exptime": 55.0, "rv_ms": rv, "rv_err_ms": 0.3, "extsnr": np.full(n, 400.0)}
    )


def test_prepare_removes_the_daily_trend():
    out = quality.prepare(synthetic_day())
    assert out["good"].all()
    assert abs(out["res"].mean()) < 0.05
    assert 0.4 < out["res"].std() < 0.6
    # mid-exposure time: half of the 55 s exposure after its start
    assert np.allclose((out["jd"] - out["obsjd"]) * 86400.0, 27.5, atol=1e-3)


def test_prepare_rejects_clouds_outliers_and_invalid_errors():
    table = synthetic_day()
    table.loc[100:104, "extsnr"] = 300.0  # a passing cloud...
    table.loc[100:104, "rv_ms"] += 30.0  # ...that biases the velocity
    table.loc[180, "rv_ms"] += 20.0  # an outlier with a normal signal-to-noise ratio
    table.loc[30, "rv_err_ms"] = -1.0  # sentinel value of the archive
    out = quality.prepare(table)
    assert not out.loc[100:104, "good"].any()
    assert not out.loc[180, "good"]
    assert not out.loc[30, "good"]
    assert out["good"].sum() >= 240
    assert 0.4 < out.loc[out["good"], "res"].std() < 0.6


def test_prepare_drops_days_with_too_few_points():
    short = synthetic_day(n=20)
    full = synthetic_day(day_jd=2460001.2)
    out = quality.prepare(pd.concat([short, full], ignore_index=True))
    first_day = out["day"] == out["day"].min()
    assert not out.loc[first_day, "good"].any()
    assert out.loc[first_day, "res"].isna().all()
    assert out.loc[~first_day, "good"].all()


def test_prepare_drops_days_with_large_scatter():
    quiet = synthetic_day()
    noisy = synthetic_day(day_jd=2460001.2, noise=5.0, seed=2)  # broken cloud all day
    out = quality.prepare(pd.concat([quiet, noisy], ignore_index=True))
    first_day = out["day"] == out["day"].min()
    assert out.loc[first_day, "good"].all()
    assert not out.loc[~first_day, "good"].any()
    assert out.loc[~first_day, "day_sigma"].iloc[0] > 1.5


def test_matches_finds_exposures_to_a_fraction_of_a_second():
    keep = np.array([10.0, 10.001, 10.002])
    found = quality.matches([10.0 + 1e-6, 10.0005, 10.002 - 1e-6, 9.0, 11.0], keep)
    assert list(found) == [True, False, True, False, False]
    assert not quality.matches([10.0], np.array([])).any()  # nothing to match against
