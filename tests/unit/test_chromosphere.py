import numpy as np
import pandas as pd
import pytest

from flinch import chromosphere


def test_weighted_slope_through_the_origin():
    x = np.array([1.0, 2.0, 4.0, np.nan])
    slope, error = chromosphere.weighted_slope(0.5 * x, x, np.array([0.1, 0.1, 0.2, 0.1]))
    assert slope == pytest.approx(0.5)
    assert error == pytest.approx(1.0 / np.sqrt(1 / 0.01 + 4 / 0.01 + 16 / 0.04))


def test_spearman_needs_four_points_and_ignores_missing_values():
    assert np.isnan(chromosphere.spearman([1, 2, 3], [1, 2, 3]))
    assert chromosphere.spearman([1, 2, 3, 4, np.nan], [10, 20, 30, 50, 5]) == pytest.approx(1.0)
    assert chromosphere.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)


def test_usable_requires_spectra_before_and_around_the_peak():
    table = pd.DataFrame(
        {"n_before": [5, 4, 9, 9], "n_window": [4, 9, 3, 9], "Ha06_1_tellcorr": [1.0, 1.0, 1.0, np.nan]}
    )
    assert list(chromosphere.usable(table)) == [True, False, False, False]
