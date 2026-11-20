# Reproducing the results

Every number and figure of [Results](results.md) comes from a command. Random choices
(controls, bootstrap) use a fixed seed, so the outputs are identical from run to run.

## Velocity

```
python -m flinch download
python -m flinch coverage
python -m flinch replication
python -m flinch robustness
python -m flinch pilot
```

| Output | Made by | Content |
|---|---|---|
| `results/flare_sample.csv` | `coverage` | The 2122 M and X flares and their coverage by NEID |
| `results/velocity_by_instrument.csv` | `replication` | Mean change, shift of an X1 flare and rotation term, by class and instrument, and both together |
| `results/replication_events.csv` | `replication` | Every flare and control of both instruments, with its velocity change |
| `results/replication_profiles.csv` | `replication` | Mean velocity around the peak in 10-minute bins |
| `results/early_window.csv` | `replication` | Mean velocity from 60 to 50 minutes before the peak, by class and instrument |
| `results/robustness.csv` | `robustness` | The table of variants (NEID) |
| `results/injections.csv` | `robustness` | A shift added and measured back (NEID) |
| `results/pilot_*.csv` | `pilot` | The first NEID analysis, including the oscillation power |

`replication` downloads the HARPS-N table (64 MB) the first time. `robustness` downloads the
one-minute X-ray fluxes (380 MB) the first time.

## Spectra

```
python -m flinch campaign --min-class X1.0 --hours 4 --max-files 700
python -m flinch campaign --kind controls --hours 4 --max-files 700
python -m flinch campaign --min-class M5.0 --max-class X1.0 --clear-only --sparse --step 2 --before 26 --after 10
python -m flinch chromosphere
```

The first command fetches the spectra around the X-class flares, strongest first, until the
time or the file budget runs out; the second fetches the same windows on the nearest
flare-free day. The third fetches the flares between M5 and M9, and only those, and only the
spectra, taken with a steady clear sky: the others would be discarded anyway, and each costs
113 MB. All of them skip what is already on disk, so they can be stopped and repeated.
Extracts go to `data/spectra/<date>_<time>_<class>/`.

| Output | Made by | Content |
|---|---|---|
| `results/spectral_response.csv` | `chromosphere` | Response of every flare and control, with its errors |
| `results/spectral_indices.csv` | `chromosphere` | Summary of each index by class band |

A single window:

```
python -m flinch spectra --start 2024-02-22T21:37 --end 2024-02-22T22:45 --name 20240222_2233_X6.3
```

## Figures of the paper

```
python -m flinch paper-figures --out docs/paper/figuras
```

It writes, as vector PDF in journal style, the example of the method, the mean velocity
around the peak for both instruments, the change of each flare against class and position,
and the mean response of the spectra.

## Versions

The exact versions of the packages used are in `requirements-lock.txt`. The data change with
time: the NEID table grows every clear day and the GOES files are reissued with a new end
date, so the counts quoted here are those of 20 November 2026.
