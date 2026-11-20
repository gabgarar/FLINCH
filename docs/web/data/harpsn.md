# HARPS-N velocities

The second instrument. It is used to repeat the velocity measurement with data that share
nothing with NEID: another spectrograph, another site, other flares.

## What it is

HARPS-N is a stabilised spectrograph on the Telescopio Nazionale Galileo at La Palma. A small
solar telescope has fed it disc-integrated sunlight every clear day since July 2015, with
exposures of 5 minutes, one every 324 s. Dumusque et al. (2026, A&A 706, A231) released ten
years of these data. The release includes one table with the velocity and the activity
indices of every exposure: 109 466 rows up to May 2025, 64 MB.

`python -m flinch replication` downloads that table into `data/harpsn/` the first time.

## What is expected from it

| | NEID | HARPS-N |
|---|---|---|
| Site | Kitt Peak, Arizona | La Palma |
| Hours observed (UT) | 16:30 to 22:30 | 9 to 17 |
| Years | 2020 to 2026 | 2015 to 2025 |
| Cadence | 83 s | 324 s |
| Scatter of one velocity | 0.81 m/s | 0.44 m/s |
| M and X flares measured | 139 | 115 |

The two watch the Sun at different hours, so they see different flares: only one flare is in
both samples. A response of the Sun to flares has to appear in both; an artefact of one
instrument does not.

## How it is processed

| Step | What is done |
|---|---|
| Time | The UTC time stamp in the name of each file is the start of the exposure; half the exposure is added. The barycentric date of the table is about seven minutes earlier and is not used. |
| Clouds | Exposures with the quality flag of the release below 0.99, or flagged by its pipeline, are dropped. The release recommends 0.9; with it the result is the same (−0.005 ± 0.038 m/s for 126 flares). |
| Daily trend | A polynomial of degree 2 per day, with the same clipping and the same cut on the scatter of the day as for NEID. A day needs 20 kept exposures. |
| Result | 93 593 velocities on 1671 days. |
| Flares | Those of the GOES-16 and GOES-18 lists, which begin in February 2017: 1750 of class M or X, of which 122 have complete windows and 115 at least three controls. |

The windows, the controls and the bootstrap are those of [the method](../method.md); only the
smallest number of points per window changes with the cadence (three exposures before the
flare, one during it).

See `flinch.harpsn` and `flinch.replication` in the [API reference](../api/velocity.md).
