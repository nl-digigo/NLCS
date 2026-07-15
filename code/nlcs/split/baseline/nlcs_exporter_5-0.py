"""
NLCS 5.0 baseline exporter.

Runs the NLCS publicatie queries against the pre-split NLCS 5.0 endpoint and
writes CSV tables under tabellen/split-baseline/5.0/. This is the golden
reference used to validate that the split-and-merged publication reproduces
the pre-split data exactly.

Usage
-----
    python nlcs_exporter_5-0.py
    python nlcs_exporter_5-0.py --hoofdgroepen HU,BV
"""
import argparse
import logging

from exporter import run


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument(
        "--hoofdgroepen",
        help="Comma-separated hoofdgroep codes to export (default: all hoofdgroepen).",
        default=None,
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()
    hoofdgroep_filter = args.hoofdgroepen.split(",") if args.hoofdgroepen else None
    run(hoofdgroep_filter)
    logging.info("Done.")


if __name__ == "__main__":
    main()
