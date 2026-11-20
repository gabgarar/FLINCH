# Reproducing the results

Every number and figure of [Results](results.md) comes from a command. Random choices
(controls, bootstrap) use a fixed seed, so the outputs are identical from run to run.

## Velocity

```
python -m flinch download
python -m flinch coverage
python -m flinch pilot
python -m flinch robustness
```

| Output | Made by | Content |
|---|---|---|
| `results/flare_sample.csv` | `coverage` | The 2122 M and X flares and their coverage by NEID |
| `results/pilot_flares.csv` | `pilot` | The 140 flares measured, with their velocity changes |
| `results/pilot_controls.csv` | `pilot` | Up to 10 controls per flare |
| `results/pilot_summary.csv` | `pilot` | Mean change per class band, flares and controls |
| `results/pilot_tests.csv` | `pilot` | Statistics against null samples, including the oscillation power |
| `results/pilot_profiles.csv` | `pilot` | Stacked velocity in 5-minute bins |
| `results/robustness.csv` | `robustness` | The table of variants |
| `results/injections.csv` | `robustness` | Injection and recovery |
| `docs/web/img/pilot_profiles.png` | `pilot` | Mean velocity around the peak |
| `docs/web/img/pilot_events.png` | `pilot` | Change of each flare against class and position |

## Spectra

```
python -m flinch campaign --hours 4 --max-files 700
python -m flinch campaign --kind controls --hours 4 --max-files 700
```

The first command fetches the spectra around the strongest flares, strongest first, until
the time or the file budget runs out; the second fetches the same windows on the nearest
flare-free day. Both skip what is already on disk, so they can be stopped and repeated.
Extracts go to `data/spectra/<date>_<time>_<class>/`.

A single window:

```
python -m flinch spectra --start 2024-02-22T21:37 --end 2024-02-22T22:45 --name 20240222_2233_X6.3
```

The response of each flare is computed with `flinch.response.collect` and written to
`results/spectral_response.csv`.

## Versions

The exact versions of the packages used are in `requirements-lock.txt`. The data change with
time: the NEID table grows every clear day and the GOES files are reissued with a new end
date, so the counts quoted here are those of 20 November 2026.
