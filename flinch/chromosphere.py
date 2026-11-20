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
    return float(np.sum(weight * x[keep] * y[keep]) / norm), float(1.0 / np.sqrt(norm))


def spearman(a, b) -> float:
    a, b = pd.Series(np.asarray(a, dtype=float)), pd.Series(np.asarray(b, dtype=float))
    keep = a.notna() & b.notna()
    return float(a[keep].rank().corr(b[keep].rank())) if keep.sum() >= 4 else np.nan


def run(window_min: tuple[float, float] = (-8.0, 10.0)) -> dict:
    root = data_dir() / "spectra"
    keep = quality.stable_obsjd(neid.read_solar_table())
    flares = flare_events()
    columns = ["name", "kind", "parent", "jd_start", "jd_peak", "goes_class", "peak_flux", "fluence", "x_norm", "y_norm", "r_norm"]
    measured = response.collect(flares[columns], root, window_min, keep_obsjd=keep)
    controls = control_events(flares, root)
    if len(controls):
        measured = pd.concat([measured, response.collect(controls[columns], root, window_min, keep_obsjd=keep)], ignore_index=True)
    measured["usable"] = usable(measured)
    # Foreshortening: cosine of the angle between the flare and the disc centre (0 at the limb).
    measured["mu"] = np.sqrt(np.clip(1.0 - measured["r_norm"] ** 2, 0.0, 1.0))
    measured["rotation"] = robust.rotation_fraction(measured)
    measured["x_class"] = measured["peak_flux"] / 1.0e-4

    good_flares = measured[measured["usable"] & (measured["kind"] == "flare")]
    good_controls = measured[measured["usable"] & (measured["kind"] == "control")]

    rows = []
    for column, label in INDICES:
        value, error = good_flares[column], good_flares[f"{column}_err"]
        on_disc = good_flares["r_norm"] < 0.9
        row = {
            "index": label,
            "flares": len(good_flares),
            "detected_3sigma": int((value / error > 3.0).sum()),
            "disc_mean": float(value[on_disc].mean()),
            "limb_mean": float(value[~on_disc].mean()) if (~on_disc).any() else np.nan,
            "rho_class": spearman(value, good_flares["peak_flux"]),
            "rho_fluence": spearman(value, good_flares["fluence"]),
            "rho_fluence_mu": spearman(value, good_flares["fluence"] * good_flares["mu"]),
        }
        if len(good_controls):
            row["controls"] = len(good_controls)
            row["control_mean"] = float(good_controls[column].mean())
            row["control_std"] = float(good_controls[column].std(ddof=1)) if len(good_controls) > 1 else np.nan
        rows.append(row)

    # Does the velocity follow the chromospheric response times the rotation at the flare?
    predictor = good_flares["Ha06_1_tellcorr"] * good_flares["rotation"]
    slope, slope_error = weighted_slope(good_flares["rv_ms"], predictor, good_flares["rv_ms_err"])
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
