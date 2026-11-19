import numpy as np
import pytest

from flinch import lineshape

START, STEP, N = -100.0, 0.25, 804
VELOCITY = lineshape.velocity_grid(START, STEP, N)


def line(centre=-0.64, depth=0.45, fwhm=7.5, skew=0.0, level=3.0e9):
    """An absorption line on a continuum of arbitrary level; ``skew`` shifts its upper part."""
    sigma = fwhm / 2.3548200450309493
    core = np.exp(-0.5 * ((VELOCITY - centre) / sigma) ** 2)
    wide = np.exp(-0.5 * ((VELOCITY - centre - skew) / (1.6 * sigma)) ** 2)
    return level * (1.0 - depth * (0.7 * core + 0.3 * wide))


def test_gaussian_parameters_are_recovered():
    table = lineshape.measure(np.vstack([line(), line(centre=-0.63, depth=0.4505)]), START, STEP)
    assert table.loc[0, "ccf_rv_ms"] == pytest.approx(-640.0, abs=0.5)
    assert table.loc[1, "ccf_rv_ms"] - table.loc[0, "ccf_rv_ms"] == pytest.approx(10.0, abs=0.05)
    # a depth change of one part in a thousand is measured to a few parts per million
    assert table.loc[1, "ccf_depth"] / table.loc[0, "ccf_depth"] - 1 == pytest.approx(0.4505 / 0.45 - 1, abs=1e-5)
    assert table.loc[0, "ccf_fwhm_kms"] == pytest.approx(table.loc[1, "ccf_fwhm_kms"], rel=1e-6)


def test_bisector_span_is_zero_for_a_symmetric_line_and_follows_the_asymmetry():
    symmetric, red, blue = lineshape.measure(np.vstack([line(), line(skew=0.3), line(skew=-0.3)]), START, STEP)[
        "ccf_bis_ms"
    ]
    assert symmetric == pytest.approx(0.0, abs=0.1)  # the 0.25 km/s sampling leaves a few cm/s
    assert red > 5.0 and blue == pytest.approx(-red, rel=1e-3)


def test_shifted_profiles_remove_the_velocity_shift():
    grid, profiles = lineshape.shifted_profiles(np.vstack([line(), line(centre=-0.2)]), START, STEP)
    assert grid[0] == -15.0 and grid[-1] == 15.0
    assert np.allclose(profiles[0], profiles[1], atol=1e-5)
    assert profiles[0].min() == pytest.approx(1.0 - 0.45, abs=1e-3)
