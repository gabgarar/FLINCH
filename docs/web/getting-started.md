# Getting started

## Installation

FLINCH needs Python 3.10 or later.

```
git clone https://github.com/gabgarar/FLINCH.git
cd FLINCH
python -m venv venv
venv/Scripts/python -m pip install -e ".[analysis,dev]"     # Windows
venv/bin/python -m pip install -e ".[analysis,dev]"         # Linux and macOS
```

The distribution is called `flinch-rv` (the name `flinch` is taken on PyPI by an unrelated
package); the import name is `flinch`.

| Extra | Adds | Needed for |
|---|---|---|
| `analysis` | SciPy, Matplotlib, Astropy | Figures, line shapes, reading the spectra |
| `dev` | pytest | The tests |
| `docs` | mkdocs-material, mkdocstrings | Building this site |
| `notebooks` | ipykernel | Notebooks |

## The commands

Everything runs through `python -m flinch <command>`.

| Command | What it does | Time | Download |
|---|---|---|---|
| `download` | Flare lists and positions (GOES) and the velocity table (NEID) | 1 min | 22 MB |
| `coverage` | Which flares happened while NEID was observing | seconds | none |
| `pilot` | Stacked velocity response against controls, tables and figures | 10 s | none |
| `robustness` | The velocity result under other estimators, backgrounds and controls | 1 min | 380 MB the first time (one-minute X-ray fluxes) |
| `spectra` | Extracts of every spectrum in a time window | 10 s per spectrum | 113 MB per spectrum |
| `campaign` | Unattended `spectra` for the strongest flares, or for their control windows | hours | 113 MB per spectrum |

A first session:

```
python -m flinch download
python -m flinch coverage
python -m flinch pilot
python -m pytest
```

## Where the data go

Downloads go to `data/` inside the repository, or to the folder named by the environment
variable `FLINCH_DATA`. Tables go to `results/` and figures to `docs/web/img/`.

!!! warning "Spectra are heavy to download"
    A level-2 NEID spectrum is 113 MB and the archive does not serve byte ranges, so each one
    is downloaded whole, reduced to a 0.2 MB extract and deleted. A campaign of 700 spectra
    moves 80 GB through the network and keeps 140 MB. The computer must stay awake: on a
    laptop, keep it plugged in and with the lid open.

## Tests

```
python -m pytest
```

The tests use synthetic data and do not touch the network.
