"""
NLCS exporter against a local RDF file (e.g. a merged split publication).

Runs the same NLCS publicatie queries as nlcs_exporter_5-0.py, but against a
local Turtle file instead of a live Laces endpoint - for validating that a
merged split publication reproduces the 5.0 baseline exactly.

Usage
-----
    python nlcs_exporter_local.py <path-to-ttl> [--output tabellen/split-baseline/merged] [--hoofdgroepen HU,BV]
"""
import argparse
import logging
from pathlib import Path

import config
from exporter import run
from local_graph_client import LocalGraphClient

DEFAULT_OUTPUT_ROOT = config.REPO_ROOT / "tabellen" / "split-baseline" / "merged"

# The split stylesheet mints human-readable property URIs (e.g. nlcs:BLineweight) for
# annotation/drawing-attribute properties instead of the pre-split MD5-hash UUIDs - an
# intentional modelling change. Querying a merged split publication needs the adapted
# template, not the original (which still targets the pre-split live endpoint).
DEFAULT_OBJECTS_TEMPLATE = Path(__file__).parent / "template_objects_per_hoofdgroup_merged.rq"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", help="Path to the local RDF file to query (e.g. merged_publications.ttl).")
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT_ROOT),
        help=f"Output folder for the CSV tables (default: {DEFAULT_OUTPUT_ROOT}).",
    )
    parser.add_argument(
        "--hoofdgroepen",
        help="Comma-separated hoofdgroep codes to export (default: all hoofdgroepen found in the file).",
        default=None,
    )
    parser.add_argument(
        "--format",
        default="turtle",
        help="RDF serialization of the source file (default: turtle).",
    )
    parser.add_argument(
        "--objects-template",
        default=str(DEFAULT_OBJECTS_TEMPLATE),
        help="Per-hoofdgroep objects query template (default: the merged-schema variant).",
    )
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()

    client = LocalGraphClient(Path(args.source), rdf_format=args.format)
    hoofdgroep_filter = args.hoofdgroepen.split(",") if args.hoofdgroepen else None
    run(
        hoofdgroep_filter,
        client=client,
        output_root=Path(args.output),
        objects_template_path=Path(args.objects_template),
    )
    logging.info("Done.")


if __name__ == "__main__":
    main()
