"""Shape of the mean photospheric line (the cross-correlation function) through a flare.

The cross-correlation function (CCF) of a spectrum with a line mask is an average line profile
built from thousands of lines, so its shape is known to a few parts in 10^5 per spectrum. A
flare can change that shape (weaker or filled-in lines in the flaring area) without moving its
centre, which is what the radial velocity measures.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.optimize import least_squares

CONTINUUM_KMS = (20.0, 60.0)  # distance from the line centre used as continuum
FIT_HALF_WIDTH_KMS = 12.0


def velocity_grid(start: float, step: float, n: int) -> np.ndarray:
    return start + step * np.arange(n)


def normalize(velocity: np.ndarray, ccf: np.ndarray) -> np.ndarray:
    """CCF divided by its continuum, taken as the mean of both wings."""
    centre = velocity[np.argmin(ccf)]
    distance = np.abs(velocity - centre)
    wings = (distance >= CONTINUUM_KMS[0]) & (distance <= CONTINUUM_KMS[1])
    return ccf / ccf[wings].mean()


def gaussian_fit(velocity: np.ndarray, profile: np.ndarray) -> tuple[float, float, float]:
    """Centre (km/s), depth and full width at half maximum (km/s) of an inverted Gaussian."""
    guess = velocity[np.argmin(profile)]
    use = np.abs(velocity - guess) <= FIT_HALF_WIDTH_KMS
    v, y = velocity[use], profile[use]

    def residual(parameters):
        centre, depth, sigma, level = parameters
        return level - depth * np.exp(-0.5 * ((v - centre) / sigma) ** 2) - y

    fit = least_squares(residual, [guess, 1.0 - y.min(), 3.5, 1.0])
    centre, depth, sigma, _ = fit.x
    return float(centre), float(depth), float(2.3548200450309493 * abs(sigma))


def bisector_span(velocity: np.ndarray, profile: np.ndarray, top=(0.10, 0.40), bottom=(0.60, 0.90)) -> float:
    """Bisector inverse slope in m/s: mean bisector near the top of the line minus near the bottom.

    The levels are fractions of the line depth, measured from the continuum.
    """
    i_min = int(np.argmin(profile))
    depth = 1.0 - profile[i_min]
    levels = 1.0 - depth * np.linspace(0.05, 0.95, 91)
    blue_v, blue_p = velocity[: i_min + 1][::-1], profile[: i_min + 1][::-1]  # from the core outwards
    red_v, red_p = velocity[i_min:], profile[i_min:]
    # Keep the monotonic part of each wing, so that np.interp gets increasing abscissae.
    blue_end = int(np.argmax(blue_p >= levels[0])) + 1 if np.any(blue_p >= levels[0]) else len(blue_p)
    red_end = int(np.argmax(red_p >= levels[0])) + 1 if np.any(red_p >= levels[0]) else len(red_p)
    bisector = 0.5 * (
        np.interp(levels, blue_p[:blue_end], blue_v[:blue_end]) + np.interp(levels, red_p[:red_end], red_v[:red_end])
    )
    fraction = (1.0 - levels) / depth
    upper = bisector[(fraction >= top[0]) & (fraction <= top[1])].mean()
    lower = bisector[(fraction >= bottom[0]) & (fraction <= bottom[1])].mean()
    return float((upper - lower) * 1000.0)


def measure(ccfs: np.ndarray, start: float, step: float) -> pd.DataFrame:
    """Shape parameters of each CCF: centre (m/s), depth, width (km/s), area (km/s) and bisector span (m/s)."""
    velocity = velocity_grid(start, step, ccfs.shape[1])
    rows = []
    for ccf in ccfs:
        profile = normalize(velocity, ccf)
        centre, depth, fwhm = gaussian_fit(velocity, profile)
        near = np.abs(velocity - centre) <= CONTINUUM_KMS[0]
        rows.append(
            {
                "ccf_rv_ms": centre * 1000.0,
                "ccf_depth": depth,
                "ccf_fwhm_kms": fwhm,
                "ccf_area_kms": float(np.sum(1.0 - profile[near]) * step),
                "ccf_bis_ms": bisector_span(velocity, profile),
            }
        )
    return pd.DataFrame(rows)


def shifted_profiles(ccfs: np.ndarray, start: float, step: float, half_width_kms: float = 15.0):
    """Normalized CCFs resampled on a common grid centred on each line (removes velocity shifts).

    Returns the grid (km/s from the line centre) and the array (spectra, grid points).
    """
    velocity = velocity_grid(start, step, ccfs.shape[1])
    grid = np.arange(-half_width_kms, half_width_kms + 0.5 * step, step)
    out = np.empty((len(ccfs), len(grid)))
    for k, ccf in enumerate(ccfs):
        profile = normalize(velocity, ccf)
        centre, _, _ = gaussian_fit(velocity, profile)
        out[k] = np.interp(centre + grid, velocity, profile)
    return grid, out
