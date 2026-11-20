"""Joint analysis of the spectral response of the flares that have spectra, against controls."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import campaign, goes, neid, quality, response, robust
from .config import data_dir

MIN_BEFORE, MIN_WINDOW = 5, 4
INDICES = (
    ("Ha06_1_tellcorr", "H alpha core"),
    ("CaIIHK", "Ca II H and K"),
    ("CaIRT2_tellcorr", "Ca II 8542"),
    ("HeI_1_tellcorr", "He I D3"),
    ("NaI_tellcorr", "Na I D"),
    ("CaI_1_tellcorr", "Ca I 6573 (reference)"),
    ("Ha16_1_tellcorr", "H alpha, 1.6 A band"),
    ("CaIRT1_tellcorr", "Ca II 8498"),
    ("CaIRT3_tellcorr", "Ca II 8662"),
    ("NaINIR_tellcorr", "Na I 8183 and 8195"),
    ("PaDelta_tellcorr", "Paschen delta"),
    ("Mn539_tellcorr", "Mn I 5395"),
    ("Hbeta_core", "H beta core (own)"),
    ("MgIb2_core", "Mg I b2 core (own)"),
    ("CaIIK_core", "Ca II K core (own)"),
)


def flare_events() -> pd.DataFrame:
    """The flares of the campaign queue, named as their folders, with fluence and impulsive time."""
    events = goes.add_impulsive_time(campaign.select_events())
    events["name"] = [campaign.event_name(row) for row in events.itertuples()]
    events["jd_start"] = events["jd_start"].fillna(events["jd_peak"] - 10.0 / 1440.0)
    events["kind"] = "flare"
    events["parent"] = events["name"]
    return events


def control_events(flares: pd.DataFrame, root: Path) -> pd.DataFrame:
    """The control windows recorded in the manifest, with the properties of their flares."""
    manifest = root / "events.csv"
    if not manifest.exists():
        return pd.DataFrame()
    controls = pd.read_csv(manifest)
    controls = controls[controls["kind"] == "controls"][["name", "parent", "jd_start", "jd_peak"]]
    inherited = flares.set_index("name")[["goes_class", "peak_flux", "fluence", "x_norm", "y_norm", "r_norm"]]
    controls = controls.join(inherited, on="parent")
    controls["kind"] = "control"
    return controls


def usable(table: pd.DataFrame) -> pd.Series:
    """Events with enough clear-sky spectra before the flare and around its peak."""
    return (table["n_before"] >= MIN_BEFORE) & (table["n_window"] >= MIN_WINDOW) & table["Ha06_1_tellcorr"].notna()


def weighted_slope(y, x, sigma) -> tuple[float, float]:
    """Slope through the origin of y against x, weighted by 1/sigma^2, and its formal error."""
    y, x, sigma = (np.asarray(v, dtype=float) for v in (y, x, sigma))
    keep = np.isfinite(y) & np.isfinite(x) & np.isfinite(sigma) & (sigma > 0)
    weight = 1.0 / sigma[keep] ** 2
    norm = np.sum(weight * x[keep] ** 2)
    if not np.isfinite(norm) or norm <= 0.0:  # no usable points, or a predictor that is zero everywhere
        return np.nan, np.nan
    return float(np.sum(weight * x[keep] * y[keep]) / norm), float(1.0 / np.sqrt(norm))


def spearman(a, b) -> float:
    a, b = pd.Series(np.asarray(a, dtype=float)), pd.Series(np.asarray(b, dtype=float))
    keep = a.notna() & b.notna()
    return float(a[keep].rank().corr(b[keep].rank())) if keep.sum() >= 4 else np.nan


MIN_CONTROLS = 3


def mean_and_error(values) -> tuple[float, float]:
    """Mean and standard error of the mean of the finite values (NaN error with fewer than two)."""
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) == 0:
        return np.nan, np.nan
    if len(values) == 1:
        return float(values[0]), np.nan
    return float(values.mean()), float(values.std(ddof=1) / np.sqrt(len(values)))


def scatter_and_error(values) -> tuple[float, float]:
    """Standard deviation of the finite values and its own uncertainty.

    For n values drawn from a normal distribution the standard deviation is known to a
    fraction 1 / sqrt(2 (n - 1)): 35 % with five values, 22 % with eleven. With fewer than
    ``MIN_CONTROLS`` values both are NaN.
    """
    values = np.asarray(values, dtype=float)
    values = values[np.isfinite(values)]
    if len(values) < MIN_CONTROLS:
        return np.nan, np.nan
    scatter = float(values.std(ddof=1))
    return scatter, scatter / float(np.sqrt(2.0 * (len(values) - 1)))


def total_error(own_error, control_scatter: float) -> np.ndarray:
    """Error of the response of a flare: its own error and the scatter of the controls, in quadrature.

    The own error comes from the spectra before the flare and misses the slow drifts with the
    height of the Sun; the scatter of the controls, measured in the same windows on flare-free
    days, contains them. Without a control scatter the own error is returned unchanged.
    """
    own_error = np.asarray(own_error, dtype=float)
    if not np.isfinite(control_scatter):
        return own_error.copy()
    return np.hypot(own_error, control_scatter)


def run(
    window_min: tuple[float, float] = (-8.0, 10.0), min_class: str = "M1.0", max_class: str | None = None
) -> dict:
    """Response of the flares with spectra, of the control windows, and their summary by index.

    ``min_class`` and ``max_class`` (exclusive) select the flares of one band, e.g. ``"X1.0"``
    alone for the X-class flares or ``"M5.0", "X1.0"`` for the strongest M-class ones. The
    control windows are always all of them: their scatter is the noise floor of any flare.
    """
    root = data_dir() / "spectra"
    keep = quality.stable_obsjd(neid.read_solar_table())
    every_flare = flare_events()
    in_band = every_flare["peak_flux"] >= goes.class_to_flux(min_class)
    if max_class is not None:
        in_band &= every_flare["peak_flux"] < goes.class_to_flux(max_class)
    flares = every_flare[in_band]
    columns = ["name", "kind", "parent", "jd_start", "jd_peak", "goes_class", "peak_flux", "fluence", "x_norm", "y_norm", "r_norm"]
    measured = response.collect(flares[columns], root, window_min, keep_obsjd=keep)
    if len(measured) == 0:  # no flare of this band has spectra
        numbers = {"flares_with_spectra": 0, "flares_usable": 0, "controls_usable": 0}
        return {"events": pd.DataFrame(), "indices": pd.DataFrame(), "numbers": numbers}
    controls = control_events(every_flare, root)
    if len(controls):
        measured = pd.concat([measured, response.collect(controls[columns], root, window_min, keep_obsjd=keep)], ignore_index=True)
    measured["usable"] = usable(measured)
    # Foreshortening: cosine of the angle between the flare and the disc centre (0 at the limb).
    measured["mu"] = np.sqrt(np.clip(1.0 - measured["r_norm"] ** 2, 0.0, 1.0))
    measured["rotation"] = robust.rotation_fraction(measured)
    measured["x_class"] = measured["peak_flux"] / 1.0e-4

    good_flares = measured[measured["usable"] & (measured["kind"] == "flare")]
    good_controls = measured[measured["usable"] & (measured["kind"] == "control")]

    flare_rows = measured["usable"] & (measured["kind"] == "flare")
    rows = []
    for column, label in (*INDICES, ("rv_ms", "Radial velocity (m/s)")):
        control_scatter, control_scatter_error = scatter_and_error(good_controls[column]) if len(good_controls) else (np.nan, np.nan)
        measured.loc[flare_rows, f"{column}_total_err"] = total_error(measured.loc[flare_rows, f"{column}_err"], control_scatter)
        value, own = good_flares[column], good_flares[f"{column}_err"]
        total = total_error(own, control_scatter)
        on_disc = (good_flares["r_norm"] < 0.9).to_numpy()
        disc_mean, disc_error = mean_and_error(value[on_disc])
        limb_mean, limb_error = mean_and_error(value[~on_disc])
        rows.append(
            {
                "index": label,
                "flares": len(good_flares),
                "detected_own_error": int((value / own > 3.0).sum()),
                "detected_total_error": int((value / total > 3.0).sum()),
                "disc_mean": disc_mean,
                "disc_mean_err": disc_error,
                "disc_median": float(np.nanmedian(value[on_disc])) if on_disc.any() else np.nan,
                "limb_mean": limb_mean,
                "limb_mean_err": limb_error,
                "rho_class": spearman(value, good_flares["peak_flux"]),
                "rho_fluence": spearman(value, good_flares["fluence"]),
                "rho_fluence_mu": spearman(value, good_flares["fluence"] * good_flares["mu"]),
                "controls": len(good_controls),
                "control_mean": float(good_controls[column].mean()) if len(good_controls) else np.nan,
                "control_std": control_scatter,
                "control_std_err": control_scatter_error,
            }
        )
    good_flares = measured[flare_rows]  # now with the total errors

    # Does the velocity follow the chromospheric response times the rotation at the flare?
    predictor = good_flares["Ha06_1_tellcorr"] * good_flares["rotation"]
    slope, slope_error = weighted_slope(good_flares["rv_ms"], predictor, good_flares["rv_ms_total_err"])
    return {
        "events": measured,
        "indices": pd.DataFrame(rows),
        "numbers": {
            "flares_with_spectra": int((measured["kind"] == "flare").sum()),
            "flares_usable": len(good_flares),
            "controls_usable": len(good_controls),
            "rv_per_halpha_rotation": slope,
            "rv_per_halpha_rotation_err": slope_error,
        },
    }
