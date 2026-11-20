"""Locations of data and results."""
from __future__ import annotations

import os
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def data_dir() -> Path:
    """Directory for downloaded data: ``$FLINCH_DATA`` if set, otherwise ``<repo>/data``.

    The flare lists and the velocity table are a few tens of MB. Spectra are much heavier:
    point ``FLINCH_DATA`` to a folder outside any cloud-synchronised directory before
    downloading them.
    """
    path = Path(os.environ.get("FLINCH_DATA", REPO_ROOT / "data"))
    path.mkdir(parents=True, exist_ok=True)
    return path


def figures_dir() -> Path:
    """Directory of the figures, inside the documentation site."""
    path = REPO_ROOT / "docs" / "web" / "img"
    path.mkdir(parents=True, exist_ok=True)
    return path


def results_dir() -> Path:
    """Directory for small derived tables that are kept under version control."""
    path = REPO_ROOT / "results"
    path.mkdir(parents=True, exist_ok=True)
    return path
