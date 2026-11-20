# Method

The measurement is a superposed epoch analysis: the velocity around many flares is averaged
and compared with the same average around flare-free epochs. This page fixes every choice.

## The sample

| Step | Flares |
|---|---|
| M and X flares between December 2020 and November 2026 | 2122 |
| NEID observing at the X-ray peak | 279 |
| With complete windows before and during the flare, after the quality cuts | 140 |
| With at least three controls | 139 |

Of the 279 flares observed at the peak, 53 fall on days dropped by the quality cuts and 89
have incomplete windows, 38 of them because the flare started within 45 minutes of the
first spectrum of the day. Three more flares have no spectrum within 2 minutes of the peak
but still have a complete window, which gives 140.

## The velocity change of one flare

The change is the mean residual velocity in a signal window minus the mean in a baseline
window.

| Window | Limits |
|---|---|
| Baseline | From 40 to 5 minutes before the start of the flare |
| Signal (default) | From the start to 2 minutes after the X-ray peak |
| Signal (alternatives) | 3 minutes either side of the steepest X-ray rise; the first 10 minutes; 5 minutes either side of the peak |

A window counts only if it holds at least 70 % of the spectra expected at the nominal
cadence, so that windows riddled with rejected spectra are left out. The residuals are the
velocities minus the polynomial of the day (see [NEID velocities](data/neid-velocities.md)).

The five-minute oscillations are not filtered. The windows average several spectra, and the
noise that the oscillations leave is part of what the controls measure.

## Controls

For each flare, controls are the same windows on other days at the same time of day, up to
15 days before and after, with no M or X flare from 45 minutes before the shifted start to
45 minutes after the shifted peak. Shifting by whole days keeps the height of the Sun and
the daily cycle of the instrument.

The analysis is paired: the change of each flare minus the mean change of its own controls.

A second family, on the day of the flare 2 and 3 hours earlier or later, exists for only 8
flares: the shifted windows usually fall outside the observing day or near another flare.

## Three estimates

With *d* the paired change of a flare, *f* its peak flux in units of an X1 flare and *v* the
line-of-sight rotation velocity at its position as a fraction of the equatorial one:

| Estimate | Definition | What it tests |
|---|---|---|
| Mean change | Mean of *d* | Any coherent shift |
| Change per X1 flare | Σ *f d* / Σ *f*² | A shift proportional to the size of the flare |
| Rotation term | Σ (*f v*) *d* / Σ (*f v*)² | A shift with the sign of the side of the disc |

The rotation term is the signed test. A flare is a bright patch on a rotating disc, so the
expected shift is

ΔRV ≈ (ΔF / F) · v_rot · K

with ΔF / F the relative brightening in the visible, v_rot the projected rotation velocity
(up to 1983 m/s at the equatorial limb) and K the response of the line mask to that patch.
East and west flares cancel in a plain mean and add in this fit. The rotation law is that of
Snodgrass and Ulrich (1990), with the sine of the latitude taken as the height on the disc.

## Errors

Flares of the same day share the sky, the instrument and the active regions; up to 6 flares
of the sample fall on one day. Errors come from a bootstrap that resamples whole observing
days, 4000 times. For the rotation term, a permutation test shuffles the positions among the
flares.

## Sensitivity

A box of known amplitude is added to the raw velocities in the signal window of one control
epoch per day, and the whole chain (quality cuts, daily trend, windows) is run again. The
ratio of recovered to injected amplitude is the efficiency. The probability of detecting a
signal at 95 % confidence follows from the efficiency and the error of the mean.

## Oscillation power

The mean square of the residuals in the 35 minutes after the peak (from 7 to 42 minutes) is
compared with that of the baseline window, as the logarithm of their ratio. A second version
uses the squared difference of consecutive spectra, which weights the high-frequency end up
to the Nyquist frequency of 6 mHz. The null distribution comes from samples of one control
per flare.

## What was fixed when

The quality cuts were chosen from the noise of the controls and the number of flares, never
from the result. The windows and the estimates were fixed after a first pilot, not before
it. The [robustness table](results.md#the-result-does-not-depend-on-the-analysis-choices)
shows that the result does not depend on them.
