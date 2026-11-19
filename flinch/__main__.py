"""Command line: ``python -m flinch download`` and ``python -m flinch coverage``."""
from __future__ import annotations

import argparse

from . import coverage, goes, neid
from .config import results_dir


def cmd_download(args: argparse.Namespace) -> int:
    for satellite in goes.SATELLITES:
        path = goes.download_flsum(satellite, overwrite=args.overwrite)
        print(f"GOES-{satellite} flare summary: {path}")
    path = neid.download_solar_table(overwrite=args.overwrite)
    print(f"NEID solar table: {path}")
    return 0


def cmd_coverage(args: argparse.Namespace) -> int:
    flares = goes.load_flares()
    observations = neid.read_solar_table()
    jd = observations["obsjd"].to_numpy()
    in_era = (flares["jd_peak"] >= jd.min()) & (flares["jd_peak"] <= jd.max())
    major = flares["goes_class"].str[0].isin(["M", "X"])
    sample = coverage.add_coverage(flares[in_era & major].reset_index(drop=True), jd)

    print(f"NEID solar observations: {len(observations)}")
    print(f"M and X flares in the NEID era: {len(sample)}")
    print(coverage.summarize(sample).to_string(index=False))
    x_class = sample[sample["at_peak"] & (sample["goes_class"].str[0] == "X")]
    print("X-class flares observed at the peak:")
    for row in x_class.itertuples():
        note = "" if row.well_covered else "  (partial baseline)"
        print(f"  {row.goes_class:5s} {row.peak:%Y-%m-%d %H:%M}{note}")

    destination = results_dir() / "flare_sample.csv"
    sample.to_csv(destination, index=False)
    print(f"Sample written to {destination}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="flinch", description="FLare-INduced CHanges in solar radial velocities")
    commands = parser.add_subparsers(dest="command", required=True)
    download = commands.add_parser("download", help="download the GOES flare lists and the NEID solar table")
    download.add_argument("--overwrite", action="store_true", help="download again files that already exist")
    download.set_defaults(run=cmd_download)
    cover = commands.add_parser("coverage", help="cross-match flares with NEID observations")
    cover.set_defaults(run=cmd_coverage)
    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
