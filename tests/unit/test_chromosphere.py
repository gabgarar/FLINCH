import numpy as np
import pandas as pd
import pytest

from flinch import chromosphere


def test_weighted_slope_through_the_origin():
    x = np.array([1.0, 2.0, 4.0, np.nan])
    slope, error = chromosphere.weighted_slope(0.5 * x, x, np.array([0.1, 0.1, 0.2, 0.1]))
    assert slope == pytest.approx(0.5)
    assert error == pytest.approx(1.0 / np.sqrt(1 / 0.01 + 4 / 0.01 + 16 / 0.04))


def test_weighted_slope_without_information_is_missing():
    slope, error = chromosphere.weighted_slope([1.0, 2.0], [0.0, 0.0], [0.1, 0.1])
    assert np.isnan(slope) and np.isnan(error)
    slope, error = chromosphere.weighted_slope([1.0, 2.0], [1.0, 2.0], [0.0, np.nan])
    assert np.isnan(slope) and np.isnan(error)


def test_spearman_needs_four_points_and_ignores_missing_values():
    assert np.isnan(chromosphere.spearman([1, 2, 3], [1, 2, 3]))
    assert chromosphere.spearman([1, 2, 3, 4, np.nan], [10, 20, 30, 50, 5]) == pytest.approx(1.0)
    assert chromosphere.spearman([1, 2, 3, 4], [4, 3, 2, 1]) == pytest.approx(-1.0)


def test_usable_requires_spectra_before_and_around_the_peak():
    table = pd.DataFrame(
        {"n_before": [5, 4, 9, 9], "n_window": [4, 9, 3, 9], "Ha06_1_tellcorr": [1.0, 1.0, 1.0, np.nan]}
    )
    assert list(chromosphere.usable(table)) == [True, False, False, False]


def test_mean_and_error():
    mean, error = chromosphere.mean_and_error([1.0, 2.0, 3.0, np.nan])
    assert mean == pytest.approx(2.0) and error == pytest.approx(1.0 / np.sqrt(3.0))
    assert chromosphere.mean_and_error([5.0]) == (5.0, pytest.approx(np.nan, nan_ok=True))
    assert all(np.isnan(v) for v in chromosphere.mean_and_error([]))


def test_scatter_of_few_controls_is_itself_uncertain():
    values = np.array([0.1, -0.3, 0.5, 0.2, -0.4])
    scatter, error = chromosphere.scatter_and_error(values)
    assert scatter == pytest.approx(values.std(ddof=1))
    assert error / scatter == pytest.approx(1.0 / np.sqrt(8.0))  # 35 % with five controls
    assert all(np.isnan(v) for v in chromosphere.scatter_and_error([0.1, 0.2]))  # too few


def test_scatter_error_matches_a_simulation():
    rng = np.random.default_rng(0)
    samples = rng.normal(0.0, 1.0, size=(20000, 5)).std(axis=1, ddof=1)
    _, predicted = chromosphere.scatter_and_error(np.array([-1.0, -0.5, 0.0, 0.5, 1.0]) * 1.2649)  # unit scatter
    assert samples.std() == pytest.approx(predicted, rel=0.1)


def test_total_error_adds_the_control_scatter_in_quadrature():
    total = chromosphere.total_error([0.3, 0.4], 0.4)
    assert total == pytest.approx([0.5, np.hypot(0.4, 0.4)])
    assert chromosphere.total_error([0.3, 0.4], np.nan) == pytest.approx([0.3, 0.4])  # no controls: unchanged
