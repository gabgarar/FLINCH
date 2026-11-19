"""Stacked response of the solar radial velocity to M and X flares, against flare-free controls."""
from __future__ import annotations

import numpy as np
import pandas as pd

from . import coverage, epoch, goes, neid, quality
from .timeutil import MINUTE

X1_FLUX = 1.0e-4  # W m^-2
PROFILE_EDGES_MIN = np.arange(-60.0, 90.1, 5.0)
BANDS = ("M1-M4", "M5-M9", "X")
# Subsets shown as stacked profiles: label and minimum peak flux.
PROFILE_SUBSETS = (("M and X", 1.0e-5), ("M5 and above", 5.0e-5), ("X", 1.0e-4))


def major_flare_sample(flares: pd.DataFrame, observation_jd: np.ndarray) -> pd.DataFrame:
    """M and X flares inside the time span of the observations."""
    in_era = (flares["jd_peak"] >= observation_jd.min()) & (flares["jd_peak"] <= observation_jd.max())
    major = flares["goes_class"].str[0].isin(["M", "X"])
    return flares[in_era & major].reset_index(drop=True)


def matched_null(controls: pd.DataFrame, statistic, draws: int = 2000, seed: int = 0) -> np.ndarray:
    """Distribution of ``statistic`` over samples made of one random control per flare."""
    rng = np.random.default_rng(seed)
    groups = [group for _, group in controls.groupby("parent")]
    out = np.empty(draws)
    for k in range(draws):
        rows = [group.index[rng.integers(len(group))] for group in groups]
        out[k] = statistic(controls.loc[rows])
    return out


def flux_weight(events: pd.DataFrame) -> np.ndarray:
    return events["peak_flux"].to_numpy(dtype=float) / X1_FLUX


def rotation_weight(events: pd.DataFrame) -> np.ndarray:
    """Flux times position across the disc (west positive); NaN outside the disc."""
    x = events["x_norm"].where(events["r_norm"] < 1.05).to_numpy(dtype=float)
    return flux_weight(events) * x


def summarize(flares: pd.DataFrame, controls: pd.DataFrame, column: str = "delta") -> pd.DataFrame:
    """Mean of ``column`` for flares and controls, per class band and for the whole sample."""
    rows = []
    bands_f = flares["goes_class"].map(coverage.class_band)
    bands_c = controls["goes_class"].map(coverage.class_band)
    for band in (*BANDS, "all"):
        f = flares[column] if band == "all" else flares.loc[bands_f == band, column]
        c = controls[column] if band == "all" else controls.loc[bands_c == band, column]
        mean_f, sem_f, n_f = epoch.mean_and_error(f)
        mean_c, sem_c, n_c = epoch.mean_and_error(c)
        difference = mean_f - mean_c
        error = float(np.hypot(sem_f, sem_c))
        rows.append(
            {
                "band": band,
                "n_flares": n_f,
                "flare_mean": mean_f,
                "flare_sem": sem_f,
                "flare_std": float(np.nanstd(f, ddof=1)) if n_f > 1 else np.nan,
                "n_controls": n_c,
                "control_mean": mean_c,
                "control_sem": sem_c,
                "control_std": float(np.nanstd(c, ddof=1)) if n_c > 1 else np.nan,
                "difference": difference,
                "error": error,
                "z": difference / error if error > 0 else np.nan,
            }
        )
    return pd.DataFrame(rows)


def stacked_profile(events: pd.DataFrame, series: epoch.Series, subset: str, sample: str) -> pd.DataFrame:
    matrix = epoch.profiles(events, series, PROFILE_EDGES_MIN)
    centres = 0.5 * (PROFILE_EDGES_MIN[:-1] + PROFILE_EDGES_MIN[1:])
    count = np.sum(np.isfinite(matrix), axis=0)
    with np.errstate(invalid="ignore"):
        mean = np.nanmean(matrix, axis=0)
        sem = np.nanstd(matrix, axis=0, ddof=1) / np.sqrt(np.maximum(count, 1))
    return pd.DataFrame(
        {"subset": subset, "sample": sample, "events": len(events), "minutes": centres, "mean": mean, "sem": sem, "n": count}
    )


def inject(observations: pd.DataFrame, events: pd.DataFrame, amplitude_ms: float) -> pd.DataFrame:
    """Copy of the raw table with a box of ``amplitude_ms`` added in the signal window of each event."""
    out = observations.copy()
    jd = (out["obsjd"] + 0.5 * quality.DEFAULT_EXPOSURE_S / 86400.0).to_numpy()
    order = np.argsort(jd)
    start, peak = epoch.event_times(events)
    first = np.searchsorted(jd[order], start, side="left")
    last = np.searchsorted(jd[order], peak + epoch.Windows().signal_after_peak * MINUTE, side="right")
    added = np.zeros(len(out))
    for a, b in zip(first, last):
        added[order[a:b]] = amplitude_ms
    out["rv_ms"] = out["rv_ms"] + added
    return out


def run(per_flare: int = 10, seed: int = 0, injection_ms: float = 1.0) -> dict:
    """Run the pilot; returns the tables that the command line prints and writes."""
    raw = neid.read_solar_table()
    observations = quality.prepare(raw)
    good = observations[observations["good"]]
    series = epoch.Series(good["jd"], good["res"])
    squares, differences = epoch.power_series(good["jd"], good["res"])

    all_flares = goes.load_flares()
    sample = major_flare_sample(all_flares, raw["obsjd"].to_numpy())
    flares = epoch.measure(sample, series)
    flares = flares[flares["measured"]].reset_index(drop=True)
    flares = epoch.measure_power(flares, squares, differences)

    candidates = epoch.draw_controls(flares, sample["jd_peak"].to_numpy(), seed=seed)
    controls = epoch.select_controls(epoch.measure(candidates, series), per_flare=per_flare)
    controls = epoch.measure_power(controls, squares, differences)

    noise = float(controls["delta"].std(ddof=1))

    def power(column):
        return lambda e: float(e.loc[e["power_measured"], column].mean())

    statistics = {
        "mean change (m/s)": lambda e: float(e["delta"].mean()),
        "change per X1 flare (m/s)": lambda e: epoch.scaled_amplitude(e["delta"], flux_weight(e), noise)[0],
        "rotation term per X1 at the limb (m/s)": lambda e: epoch.scaled_amplitude(
            e["delta"], rotation_weight(e), noise
        )[0],
        "mean change in the decay phase (m/s)": lambda e: float(e["delta_decay"].mean()),
        "log power ratio after/before": power("log_power"),
        "log power ratio, high frequency": power("log_power_hf"),
    }
    tests = []
    for name, statistic in statistics.items():
        null = matched_null(controls, statistic, seed=seed)
        value = statistic(flares)
        centre, spread = float(null.mean()), float(null.std(ddof=1))
        tests.append(
            {
                "statistic": name,
                "flares": value,
                "null_mean": centre,
                "null_std": spread,
                "excess": value - centre,
                "z": (value - centre) / spread,
                "p_two_sided": float(np.mean(np.abs(null - centre) >= abs(value - centre))),
                "limit_95": abs(value - centre) + 1.645 * spread,  # one-sided 95 % limit on the size of the excess
            }
        )

    # Injection test: add a known box to the raw velocities at one control epoch per day (so that
    # no injected box falls in the baseline of another) and measure it back through the whole chain.
    control_day = np.floor(controls["jd_peak"] - 0.5)
    isolated = controls.groupby(control_day).sample(1, random_state=seed)
    injected = quality.prepare(inject(raw, isolated, injection_ms))
    injected_good = injected[injected["good"]]
    recovered = epoch.measure(isolated, epoch.Series(injected_good["jd"], injected_good["res"]))
    kept = recovered["measured"].to_numpy()
    efficiency = float((recovered.loc[kept, "delta"].mean() - isolated.loc[kept, "delta"].mean()) / injection_ms)

    profiles = []
    for label, minimum in PROFILE_SUBSETS:
        profiles.append(stacked_profile(flares[flares["peak_flux"] >= minimum], series, label, "flares"))
        profiles.append(stacked_profile(controls[controls["peak_flux"] >= minimum], series, label, "controls"))
    return {
        "observations": observations,
        "flares": flares,
        "controls": controls,
        "summary": summarize(flares, controls),
        "summary_two_sided": summarize(
            flares[flares["measured_two_sided"]], controls[controls["measured_two_sided"]], "delta_two_sided"
        ),
        "tests": pd.DataFrame(tests),
        "profiles": pd.concat(profiles, ignore_index=True),
        "numbers": {
            "spectra": len(observations),
            "good_spectra": int(observations["good"].sum()),
            "point_sigma_ms": quality.robust_sigma(good["res"].to_numpy()),
            "event_noise_ms": noise,
            "injection_ms": injection_ms,
            "injection_efficiency": efficiency,
        },
    }
