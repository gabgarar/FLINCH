"""Superposed epoch analysis of the velocity residuals around flares and control epochs."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from .timeutil import MINUTE


@dataclass(frozen=True)
class Windows:
    """Time windows of the measurement, in minutes.

    ``pre`` is relative to the flare start; ``post`` and ``decay`` are relative to the peak.
    The signal window runs from the start to ``signal_after_peak`` minutes after the peak: it
    contains the impulsive phase, when the lower atmosphere is heated.
    """

    pre: tuple[float, float] = (-40.0, -5.0)
    signal_after_peak: float = 2.0
    post: tuple[float, float] = (7.0, 42.0)
    decay: tuple[float, float] = (2.0, 30.0)
    min_pre: int = 10
    min_signal: int = 3
    min_post: int = 10
    min_fraction: float = 0.7  # of the spectra expected in a window at the nominal cadence
    cadence_s: float = 83.0


class Series:
    """Time-sorted values with prefix sums, for fast means over many windows."""

    def __init__(self, jd, values):
        jd = np.asarray(jd, dtype=float)
        values = np.asarray(values, dtype=float)
        order = np.argsort(jd, kind="stable")
        self.jd = jd[order]
        self._cumulative = np.r_[0.0, np.cumsum(values[order])]

    def window(self, low, high) -> tuple[np.ndarray, np.ndarray]:
        """Number of points and mean value in each closed interval [low, high] (NaN if empty)."""
        first = np.searchsorted(self.jd, low, side="left")
        last = np.searchsorted(self.jd, high, side="right")
        count = last - first
        total = self._cumulative[last] - self._cumulative[first]
        with np.errstate(invalid="ignore", divide="ignore"):
            mean = np.where(count > 0, total / np.maximum(count, 1), np.nan)
        return count, mean


def event_times(events: pd.DataFrame) -> tuple[np.ndarray, np.ndarray]:
    """Start and peak Julian dates; a missing start is taken as 10 minutes before the peak."""
    peak = events["jd_peak"].to_numpy(dtype=float)
    start = events["jd_start"].to_numpy(dtype=float)
    return np.where(np.isfinite(start), start, peak - 10.0 * MINUTE), peak


def measure(events: pd.DataFrame, series: Series, windows: Windows = Windows()) -> pd.DataFrame:
    """Velocity change of each event (m/s) with respect to its own pre-event baseline.

    ``delta``            mean in the signal window minus mean in the pre-event window.
    ``delta_two_sided``  the same, with the average of the pre and post windows as baseline
                         (cancels a linear trend, but is biased if the response outlasts the peak).
    ``delta_decay``      mean in the decay window minus mean in the pre-event window.
    ``measured``         enough points before and during the event: the minimum number and at
                         least ``min_fraction`` of those expected, so that windows riddled
                         with rejected spectra (passing clouds) are left out.
    """
    start, peak = event_times(events)
    n_pre, pre = series.window(start + windows.pre[0] * MINUTE, start + windows.pre[1] * MINUTE)
    n_signal, signal = series.window(start, peak + windows.signal_after_peak * MINUTE)
    n_post, post = series.window(peak + windows.post[0] * MINUTE, peak + windows.post[1] * MINUTE)
    n_decay, decay = series.window(peak + windows.decay[0] * MINUTE, peak + windows.decay[1] * MINUTE)
    out = events.copy()
    out["rise_min"] = (peak - start) / MINUTE
    out["n_pre"], out["n_signal"], out["n_post"], out["n_decay"] = n_pre, n_signal, n_post, n_decay
    out["baseline"] = pre
    out["delta"] = signal - pre
    out["delta_two_sided"] = signal - 0.5 * (pre + post)
    out["delta_decay"] = decay - pre
    per_minute = windows.min_fraction * 60.0 / windows.cadence_s
    need_pre = np.maximum(windows.min_pre, per_minute * (windows.pre[1] - windows.pre[0]))
    need_signal = np.maximum(windows.min_signal, per_minute * ((peak - start) / MINUTE + windows.signal_after_peak))
    need_post = np.maximum(windows.min_post, per_minute * (windows.post[1] - windows.post[0]))
    out["measured"] = (n_pre >= need_pre) & (n_signal >= need_signal)
    out["measured_two_sided"] = out["measured"] & (n_post >= need_post)
    return out


def profiles(events: pd.DataFrame, series: Series, edges_min, windows: Windows = Windows()) -> np.ndarray:
    """Mean residual of each event in time bins relative to its peak, minus its pre-event mean.

    Returns an array (events, bins); empty bins are NaN.
    """
    start, peak = event_times(events)
    _, pre = series.window(start + windows.pre[0] * MINUTE, start + windows.pre[1] * MINUTE)
    edges = np.asarray(edges_min, dtype=float)
    out = np.full((len(events), len(edges) - 1), np.nan)
    for k in range(len(edges) - 1):
        # Half-open bins: nudge the upper edge so that a point is never counted twice.
        _, mean = series.window(peak + edges[k] * MINUTE, peak + edges[k + 1] * MINUTE - 1e-9)
        out[:, k] = mean - pre
    return out


def draw_controls(
    flares: pd.DataFrame,
    major_peaks_jd,
    max_shift_days: int = 15,
    margin_min: float = 45.0,
    seed: int = 0,
) -> pd.DataFrame:
    """Candidate flare-free epochs for each flare, at the same time of day on nearby days.

    Every flare is shifted by whole days (so that the Sun is at the same height and the
    instrument in the same state of its daily cycle) up to ``max_shift_days`` either way. A
    candidate is kept when no major flare peaks between ``margin_min`` minutes before its start
    and ``margin_min`` minutes after its peak. ``rank`` is a random order within each flare.
    """
    rng = np.random.default_rng(seed)
    start, peak = event_times(flares)
    shifts = np.r_[-np.arange(1, max_shift_days + 1), np.arange(1, max_shift_days + 1)].astype(float)
    major = np.sort(np.asarray(major_peaks_jd, dtype=float))
    shifted_start = (start[:, None] + shifts[None, :]).ravel()
    shifted_peak = (peak[:, None] + shifts[None, :]).ravel()
    parent = np.repeat(np.arange(len(flares)), len(shifts))
    low = shifted_start - margin_min * MINUTE
    high = shifted_peak + margin_min * MINUTE
    quiet = np.searchsorted(major, high, side="right") == np.searchsorted(major, low, side="left")
    controls = pd.DataFrame(
        {
            "parent": parent[quiet],
            "shift_days": np.tile(shifts, len(flares))[quiet],
            "jd_start": shifted_start[quiet],
            "jd_peak": shifted_peak[quiet],
            "rank": rng.random(int(quiet.sum())),
        }
    )
    for column in ("goes_class", "peak_flux", "x_norm", "y_norm", "r_norm"):
        if column in flares:
            controls[column] = flares[column].to_numpy()[controls["parent"].to_numpy()]
    return controls


def select_controls(controls: pd.DataFrame, per_flare: int = 10) -> pd.DataFrame:
    """At most ``per_flare`` measured controls per flare, chosen by their random rank."""
    measured = controls[controls["measured"]].sort_values(["parent", "rank"])
    return measured.groupby("parent").head(per_flare).reset_index(drop=True)


def mean_and_error(values) -> tuple[float, float, int]:
    """Mean, standard error of the mean and number of finite values."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < 2:
        return (float(values.mean()) if len(values) else np.nan, np.nan, len(values))
    return float(values.mean()), float(values.std(ddof=1) / np.sqrt(len(values))), len(values)


def scaled_amplitude(delta, weight, sigma: float) -> tuple[float, float]:
    """Least-squares amplitude ``a`` of the model ``delta = a * weight`` and its error.

    ``sigma`` is the noise of one measurement (taken from the control sample). With
    ``weight`` = peak flux in units of an X1 flare, ``a`` is the response to an X1 flare; with
    ``weight`` = flux times the position across the disc, it is the rotational signature.
    """
    delta = np.asarray(delta, dtype=float)
    weight = np.asarray(weight, dtype=float)
    keep = np.isfinite(delta) & np.isfinite(weight)
    norm = float(np.sum(weight[keep] ** 2))
    if norm == 0.0:
        return np.nan, np.nan
    return float(np.sum(weight[keep] * delta[keep]) / norm), float(sigma / np.sqrt(norm))


def power_series(jd, values, max_gap_s: float = 125.0) -> tuple[Series, Series]:
    """Series of squared residuals and of squared differences between consecutive spectra.

    The mean square over a window measures the power of the fluctuations, which at this
    cadence is dominated by the solar five-minute oscillations. The squared difference of two
    consecutive spectra (kept only when they are less than ``max_gap_s`` apart, and dated at
    their mid-point) weights the high-frequency end, up to the Nyquist frequency of 6 mHz.
    """
    jd = np.asarray(jd, dtype=float)
    values = np.asarray(values, dtype=float)
    order = np.argsort(jd, kind="stable")
    jd, values = jd[order], values[order]
    consecutive = np.diff(jd) * 86400.0 < max_gap_s
    return (
        Series(jd, values**2),
        Series(0.5 * (jd[1:] + jd[:-1])[consecutive], np.diff(values)[consecutive] ** 2),
    )


def measure_power(
    events: pd.DataFrame, squares: Series, differences: Series, windows: Windows = Windows()
) -> pd.DataFrame:
    """Change of the fluctuation power of each event, as natural logarithms of power ratios.

    ``log_power``     mean square after the peak (the ``post`` window) over the pre-event one.
    ``log_power_hf``  the same for the squared differences of consecutive spectra.
    ``power_measured`` enough points in both windows.
    """
    start, peak = event_times(events)
    out = events.copy()
    need = max(windows.min_pre, windows.min_post)
    measured = np.ones(len(events), dtype=bool)
    for column, series in (("log_power", squares), ("log_power_hf", differences)):
        n_pre, pre = series.window(start + windows.pre[0] * MINUTE, start + windows.pre[1] * MINUTE)
        n_post, post = series.window(peak + windows.post[0] * MINUTE, peak + windows.post[1] * MINUTE)
        with np.errstate(invalid="ignore", divide="ignore"):
            out[column] = np.log(post / pre)
        measured &= (n_pre >= need) & (n_post >= need)
    out["power_measured"] = measured & np.isfinite(out["log_power"]) & np.isfinite(out["log_power_hf"])
    return out
