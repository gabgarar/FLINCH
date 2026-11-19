# FLINCH

**FL**are-**IN**duced **CH**anges in Sun-as-a-star radial velocities.

*Does the Sun flinch when it flares?*

Spectrographs built to find exoplanets measure the velocity of a star to a few tens of
centimetres per second. One of them, NEID (Kitt Peak, Arizona), also observes the Sun every
day as if it were a distant star, one spectrum every 83 seconds. FLINCH uses those data to
measure what a solar flare does to the disc-integrated radial velocity: whether it is
detectable, from which flare size, and what that implies for planet searches around other
Sun-like stars.

**Status: early stage.** The data layer and the flare sample exist; the measurement itself is
the next step. The working plan (in Spanish) is in [docs/plan.md](docs/plan.md).

## The sample

Between December 2020 and November 2026 the Sun produced 2122 flares of GOES class M or X.
NEID was observing the Sun at the peak of 279 of them:

| GOES class | Flares | NEID observing at the peak | ...with 30 min of data before and after |
|---|---|---|---|
| M1 to M4 | 1833 | 236 | 208 |
| M5 to M9 | 185 | 24 | 21 |
| X | 104 | 19 | 19 |

The table is produced by `python -m flinch coverage`, which also writes the sample to
[results/flare_sample.csv](results/flare_sample.csv).

## Data

Both sources are public and need no registration.

| Data | Source | Size |
|---|---|---|
| Flare list (start, peak, end, class) | GOES-16 and GOES-18 XRS science-quality flare summaries, NOAA/NCEI | 12 MB |
| Solar radial velocities | NEID solar archive (NExScI), table `neidsolarl2` through its TAP service | 8 MB |

GOES-16 is the primary flare list; GOES-18 fills its gaps and continues after April 2025.
The class of a flare differs by a few per cent between the two satellites.

## Quick start

```
python -m venv <somewhere>/venv
<somewhere>/venv/Scripts/python -m pip install -e ".[analysis,dev]"
python -m flinch download     # flare lists and velocity table, about 20 MB, into data/
python -m flinch coverage     # the table above and results/flare_sample.csv
python -m pytest              # tests, no network needed
```

Downloads go to `data/` inside the repository, or to the folder named by the environment
variable `FLINCH_DATA`.

## Layout

| Path | Content |
|---|---|
| `flinch/goes.py` | Download and parsing of the GOES flare summaries |
| `flinch/neid.py` | Queries to the NEID solar archive |
| `flinch/coverage.py` | Cross-match of flares and observations |
| `tests/` | Unit tests |
| `docs/plan.md` | Research plan |
| `results/` | Small derived tables kept under version control |

## Licence

BSD 3-Clause, see [LICENSE](LICENSE).
