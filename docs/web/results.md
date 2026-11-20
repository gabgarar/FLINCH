# Results

Status: November 2026. The velocity results are complete; the spectral results are
preliminary.

## The velocity of the Sun does not change during flares

With 139 M and X flares, the radial velocity of the Sun seen as a star does not change
detectably during a flare.

![Mean velocity around the flare peak](img/pilot_profiles.png)

| Quantity | Value (m/s) | 95 % limit (m/s) |
|---|---|---|
| Mean change of an M or X flare | −0.035 ± 0.035 | 0.09 |
| Change per X1 flare (scaled with the flux) | −0.010 ± 0.061 | 0.11 |
| Rotation term per X1 flare at the equatorial limb | −0.106 ± 0.082 | 0.24 |

The limit on the mean change is of the order of the 0.09 m/s that the Earth imprints on the
Sun.

There is no trend with the size of the flare or with its position on the disc. Shuffling the
positions among the flares gives a rotation term this large 10 % of the time.

![Velocity change of each flare against its class and its position](img/pilot_events.png)

In physical terms the limit on the rotation term means K · ΔF / F < 1.2 × 10⁻⁴ per X1
flare, with ΔF / F the relative brightening in the visible and K the response of the line
mask (see [Method](method.md#three-estimates)).

## The result does not depend on the analysis choices

| Variant | Flares | Mean change | Per X1 | Rotation per X1 |
|---|---|---|---|---|
| Default | 139 | −0.035 ± 0.035 | −0.010 ± 0.061 | −0.106 ± 0.082 |
| Day polynomial of degree 1 | 137 | −0.022 ± 0.036 | −0.015 ± 0.060 | −0.045 ± 0.080 |
| Day polynomial of degree 3 | 139 | −0.001 ± 0.033 | +0.016 ± 0.049 | −0.079 ± 0.083 |
| Window: 3 min either side of the steepest X-ray rise | 120 | −0.009 ± 0.042 | −0.019 ± 0.061 | −0.108 ± 0.135 |
| Window: first 10 min from the start | 134 | −0.040 ± 0.035 | +0.006 ± 0.045 | −0.004 ± 0.080 |
| Window: 5 min either side of the X-ray peak | 126 | −0.021 ± 0.042 | −0.111 ± 0.085 | −0.134 ± 0.154 |
| Background: straight line fitted on both sides | 93 | −0.008 ± 0.040 | −0.032 ± 0.070 | −0.002 ± 0.113 |
| Bootstrap over 81 active regions instead of 111 days | 139 | −0.035 ± 0.035 | −0.010 ± 0.061 | −0.106 ± 0.082 |
| X-class flares only | 11 | −0.060 ± 0.088 | +0.011 ± 0.065 | −0.051 ± 0.104 |

All in m/s, with errors from the bootstrap over days. Same-day controls exist for 8 flares
and say nothing: +0.07 ± 0.17 m/s.

### Demonstrated sensitivity

| Injected signal | Recovered | Probability of detecting it at 95 % |
|---|---|---|
| 5 cm/s | 4.9 cm/s | 40 % |
| 10 cm/s | 9.8 cm/s | 88 % |
| 20 cm/s | 19.5 cm/s | 100 % |
| 50 cm/s | 48.8 cm/s | 100 % |

## Flares do not raise the amplitude of the solar oscillations

| Quantity | Flares | Null samples | 95 % limit on the excess |
|---|---|---|---|
| ln(power after / before) | −0.068 | 0.001 ± 0.053 | 0.16 |
| The same, weighting high frequencies | −0.013 | −0.009 ± 0.060 | 0.10 |

A mean increase above 8 % in amplitude is ruled out. This tests the proposal of Karoff and
Kjeldsen (2008), with the limitation that the 83 s cadence reaches only 6 mHz.

## The same spectra do see the flares

The null result in velocity is not due to spectra that miss the flares. In the spectra of
the strongest flares the chromospheric indices rise clearly when the flare is on the disc,
while the velocity of the same spectra stays flat.

!!! warning "Preliminary"
    Twelve flares and three control windows. The errors of single flares come from the
    scatter of the spectra before each flare and do not include slow drifts with the height
    of the Sun; the scatter of the controls does.

![Spectral response to the X6.3 flare of 22 February 2024](img/event_20240222_2233_X6.3.png)

Mean change from 8 minutes before the X-ray peak to 10 minutes after it, in parts per
thousand, for the 12 X flares with usable spectra:

| Index | Detected above 3 sigma | Mean on the disc (8 flares) | Mean near the limb (4) | Scatter of the controls |
|---|---|---|---|---|
| H alpha, 0.6 Å core | 9 | +3.3 | +0.8 | 0.6 |
| Ca II H and K | 9 | +5.3 | +1.7 | 0.6 |
| H beta core (own index) | 9 | +2.2 | +0.9 | 0.14 |
| H alpha, 1.6 Å band | 8 | +1.1 | +0.4 | 0.12 |
| Ca II 8542 | 8 | +2.2 | +0.9 | 1.0 |
| Ca I 6573 (photospheric reference) | 1 | 0.0 | +0.2 | 0.17 |

He I D3, Na I D, Na I 8183 and 8195, Paschen delta, Mn I 5395 and Mg I b2 do not respond.
H beta is the cleanest index: it has no telluric lines on it and barely moves without a
flare. The Ca II infrared triplet drifts as much as it responds.

Flare by flare, with the candidate coronal mass ejection from the LASCO catalogue:

| Flare | Distance from disc centre | CME | H alpha core | Velocity (m/s) |
|---|---|---|---|---|
| X1.9, 2026-01-18 | 0.36 | yes | +10.9 ± 0.3 | −1.4 ± 0.4 |
| X1.1, 2026-06-30 | 0.39 | yes | +3.6 ± 0.2 | −0.1 ± 0.3 |
| X1.2, 2025-06-17 | 0.36 | no | +3.0 ± 0.3 | +0.5 ± 0.4 |
| X1.1, 2024-05-09 | 0.53 | yes | +2.8 ± 0.3 | +0.3 ± 0.4 |
| X1.9, 2023-01-09 | 0.97 | no | +2.2 ± 0.4 | 0.0 ± 0.4 |
| X1.3, 2022-03-30 | 0.58 | yes | +2.0 ± 0.3 | −0.4 ± 0.3 |
| X2.8, 2023-12-14 | 0.76 | yes | +1.57 ± 0.09 | −0.4 ± 0.2 |
| X1.0, 2024-06-01 | 0.50 | yes | +1.4 ± 0.3 | +0.2 ± 0.2 |
| X1.1, 2024-05-31 | 0.64 | no | +1.1 ± 0.3 | +0.3 ± 0.3 |
| X1.6, 2023-08-05 | 0.95 | yes | +0.7 ± 0.3 | +0.1 ± 0.2 |
| X8.6, 2024-05-14 | 1.00 | yes | +0.6 ± 0.6 | −0.3 ± 0.7 |
| X1.9, 2025-02-23 | 0.96 | yes | −0.5 ± 0.3 | −0.1 ± 0.4 |

- **All eight flares on the disc are detected in H alpha**; near the limb the response is weak
  or absent.
- **The response follows the energy and the position, not the class.** Its rank correlation
  with the X-ray fluence times the foreshortening is 0.6 to 0.8 depending on the line, and
  negative with the GOES class. With 12 flares this is an indication, not a measurement.
- **Flares without a candidate ejection respond too.**
- **The velocity does not follow the chromospheric response**: fitted against the H alpha
  change times the rotation velocity at the flare, the slope is 0.06 ± 0.07 m/s per part per
  thousand. The −1.4 ± 0.4 m/s of the strongest responder has the sign expected from its
  side of the disc, but it is one case among twelve.

That flares brighten H alpha in Sun-as-a-star spectra is known (Otsu et al. 2022; Ma et al.
2024; Pietrow et al. 2024; see [References](references.md)). Here it is the check that the
flares are in the data.

## What is left

- The control windows of the remaining flares, to replace the single-flare errors by the
  scatter of the controls.
- A comparison with the published analyses of the flares in common.
