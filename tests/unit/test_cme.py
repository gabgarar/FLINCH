import numpy as np
import pandas as pd

from flinch import cme
from flinch.timeutil import MINUTE

T0 = 2460000.25


def test_position_angle_follows_the_catalogue_convention():
    north, east, south, west = cme.flare_position_angle([0.0, -0.5, 0.0, 0.5], [0.5, 0.0, -0.5, 0.0])
    assert (north, east, south, west) == (0.0, 90.0, 180.0, 270.0)


def test_association_by_time_and_direction():
    cmes = pd.DataFrame(
        {
            "jd": [T0 + 30 * MINUTE, T0 + 30 * MINUTE + 1.0, T0 + 20 * MINUTE + 2.0, T0 + 20 * MINUTE + 3.0, T0 + 400 * MINUTE + 4.0],
            "halo": [False, False, True, False, False],
            "cpa": [95.0, 270.0, np.nan, 90.0, 90.0],
            "mpa": [90.0, 265.0, 120.0, 90.0, 90.0],
            "width": [60.0, 60.0, 360.0, 80.0, 80.0],
            "speed": [700.0, 900.0, 1500.0, 500.0, 500.0],
            "remarks": ["", "", "", "Poor Event", ""],
        }
    )
    days = np.arange(5.0)
    flares = pd.DataFrame(
        {"jd_start": T0 + days, "jd_peak": T0 + 10 * MINUTE + days, "x_norm": -0.8, "y_norm": 0.0, "r_norm": 0.8}
    )
    out = cme.associate(flares, cmes)
    # east flare: CME to the east; CME to the west; halo; poor event; CME six hours later
    assert list(out["cme"]) == [True, False, True, False, False]
    assert out.loc[0, "cme_speed"] == 700.0 and abs(out.loc[0, "cme_delay_min"] - 20.0) < 1e-3
    assert out.loc[2, "cme_width"] == 360.0
