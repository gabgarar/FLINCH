"""Command line: ``python -m flinch download`` and ``python -m flinch coverage``."""
from __future__ import annotations

import argparse

import pandas as pd

from . import coverage, goes, neid
from .config import results_dir


def cmd_download(args: argparse.Namespace) -> int:
    for satellite in goes.SATELLITES:
        for product in goes.PRODUCTS:
            path = goes.download_product(satellite, product, overwrite=args.overwrite)
            print(f"GOES-{satellite} {product}: {path}")
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


def cmd_pilot(args: argparse.Namespace) -> int:
    from . import pilot  # imported here: the other commands do not need the analysis code

    out = pilot.run(per_flare=args.controls, seed=args.seed)
    numbers = out["numbers"]
    print(f"Spectra: {numbers['spectra']}; passing the quality cuts: {numbers['good_spectra']}")
    print(f"Scatter of one spectrum about the daily trend: {numbers['point_sigma_ms']:.2f} m/s")
    print(f"Flares measured: {len(out['flares'])}; controls: {len(out['controls'])}")
    print(f"Noise of one event (scatter of the controls): {numbers['event_noise_ms']:.2f} m/s")
    print(
        f"Injection test: {numbers['injection_efficiency'] * 100:.0f} % of a "
        f"{numbers['injection_ms']:.1f} m/s signal is recovered"
    )
    with pd.option_context("display.width", 200, "display.float_format", "{:.3f}".format):
        print("\nVelocity change, signal window minus pre-flare window (m/s):")
        print(out["summary"].to_string(index=False))
        print("\nSame, with a two-sided baseline (m/s):")
        print(out["summary_two_sided"].to_string(index=False))
        print("\nStatistics against one-control-per-flare null samples:")
        print(out["tests"].to_string(index=False))

    directory = results_dir()
    out["flares"].to_csv(directory / "pilot_flares.csv", index=False)
    out["controls"].to_csv(directory / "pilot_controls.csv", index=False)
    out["summary"].to_csv(directory / "pilot_summary.csv", index=False)
    out["tests"].to_csv(directory / "pilot_tests.csv", index=False)
    out["profiles"].to_csv(directory / "pilot_profiles.csv", index=False)
    from . import plots

    plots.plot_profiles(out["profiles"], directory / "figures" / "pilot_profiles.png")
    plots.plot_events(out["flares"], out["controls"], directory / "figures" / "pilot_events.png")
    print(f"\nTables and figures written to {directory}")
    return 0


def cmd_spectra(args: argparse.Namespace) -> int:
    import datetime as dt

    from . import spectra
    from .timeutil import datetime_to_jd

    jd_from = datetime_to_jd(dt.datetime.fromisoformat(args.start))
    jd_to = datetime_to_jd(dt.datetime.fromisoformat(args.end))
    spectra.fetch_window(jd_from, jd_to, args.name, workers=args.workers, step=args.step)
    return 0


def cmd_campaign(args: argparse.Namespace) -> int:
    from . import campaign

    campaign.run(hours=args.hours, max_files=args.max_files, step=args.step, workers=args.workers, kind=args.kind)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="flinch", description="FLare-INduced CHanges in solar radial velocities")
    commands = parser.add_subparsers(dest="command", required=True)
    download = commands.add_parser("download", help="download the GOES flare lists and the NEID solar table")
    download.add_argument("--overwrite", action="store_true", help="download again files that already exist")
    download.set_defaults(run=cmd_download)
    cover = commands.add_parser("coverage", help="cross-match flares with NEID observations")
    cover.set_defaults(run=cmd_coverage)
    pilot = commands.add_parser("pilot", help="stacked velocity response to flares, against controls")
    pilot.add_argument("--controls", type=int, default=10, help="controls per flare (default 10)")
    pilot.add_argument("--seed", type=int, default=0, help="seed of the random choices (default 0)")
    pilot.set_defaults(run=cmd_pilot)
    spec = commands.add_parser(
        "spectra", help="extract indices and line windows from every spectrum in a time window (113 MB each)"
    )
    spec.add_argument("--start", required=True, help="UTC start, e.g. 2026-01-18T16:40")
    spec.add_argument("--end", required=True, help="UTC end, e.g. 2026-01-18T19:10")
    spec.add_argument("--name", required=True, help="name of the output folder under data/spectra/")
    spec.add_argument("--workers", type=int, default=3, help="simultaneous downloads (default 3)")
    spec.add_argument("--step", type=int, default=1, help="take every n-th spectrum (default 1: all)")
    spec.set_defaults(run=cmd_spectra)
    camp = commands.add_parser("campaign", help="unattended download of spectra around the strongest flares")
    camp.add_argument("--hours", type=float, default=7.5, help="time budget (default 7.5)")
    camp.add_argument("--max-files", type=int, default=600, help="file budget, 113 MB each (default 600)")
    camp.add_argument("--step", type=int, default=3, help="take every n-th spectrum (default 3)")
    camp.add_argument("--workers", type=int, default=3, help="simultaneous downloads (default 3)")
    camp.add_argument("--kind", choices=["flares", "controls"], default="flares", help="flare windows, or flare-free windows for the flares already fetched")
    camp.set_defaults(run=cmd_campaign)
    args = parser.parse_args(argv)
    return args.run(args)


if __name__ == "__main__":
    raise SystemExit(main())
