"""Export pipeline: NLCS 5.0 publicatie tables, per hoofdgroep and shared concept types."""
import logging
from pathlib import Path
from typing import Optional, Protocol

import config
from csv_io import merge_csv_files, save_csv
from hoofdgroepen import retrieve_hoofdgroepen
from laces_client import LacesClient
from query_loader import load_query, render_query

log = logging.getLogger(__name__)


class SparqlClient(Protocol):
    """Anything that can run a SPARQL query and return CSV text - a live LacesClient or a LocalGraphClient."""

    def query(self, sparql: str, accept: str = "text/csv") -> str: ...


def export_concept_tables(client: SparqlClient, output_folder: Path = config.CONCEPT_TABLES_OUTPUT_FOLDER) -> None:
    """Runs every *.rq query in the publicatie query folder and saves non-empty results as CSV."""
    query_files = sorted(config.PUBLICATIE_QUERY_FOLDER.glob("*.rq"))
    if not query_files:
        log.warning("No concept-table queries found in %s", config.PUBLICATIE_QUERY_FOLDER)
        return

    for query_file in query_files:
        log.info("Running concept-table query: %s", query_file.name)
        result = client.query(load_query(query_file))
        output_path = output_folder / f"{query_file.stem}-{config.VERSION}.csv"
        save_csv(result, output_path)


def export_objects_per_hoofdgroep(
    client: SparqlClient,
    hoofdgroepen: list[str],
    output_folder: Path = config.OBJECTS_OUTPUT_FOLDER,
    template_path: Path = config.OBJECTS_TEMPLATE_QUERY_PATH,
) -> list[Path]:
    """Runs the per-hoofdgroep objects query once per hoofdgroep. Returns the paths actually written."""
    written_paths = []
    for hoofdgroep in hoofdgroepen:
        log.info("Running objects query for hoofdgroep '%s'", hoofdgroep)
        query = render_query(template_path, config.HOOFDGROUP_PLACEHOLDER, hoofdgroep)
        result = client.query(query)
        output_path = output_folder / f"objecten-{config.VERSION}-{hoofdgroep}.csv"
        if save_csv(result, output_path):
            written_paths.append(output_path)
    return written_paths


def run(
    hoofdgroep_filter: Optional[list[str]] = None,
    client: Optional[SparqlClient] = None,
    output_root: Optional[Path] = None,
    objects_template_path: Path = config.OBJECTS_TEMPLATE_QUERY_PATH,
) -> None:
    if client is None:
        client = LacesClient(config.SPARQL_ENDPOINT, config.LDP_TOKEN_ID, config.LDP_PASSWORD)
    output_root = Path(output_root) if output_root else config.CONCEPT_TABLES_OUTPUT_FOLDER
    objects_output_folder = output_root / "objectentabellen"
    merged_objects_output_path = output_root / f"all_objects-{config.VERSION}.csv"

    log.info("Exporting shared concept tables (arceringen, symbolen, lijntypes, ...)")
    export_concept_tables(client, output_root)

    log.info("Retrieving hoofdgroepen")
    hoofdgroepen = retrieve_hoofdgroepen(client, config.HOOFDGROEPEN_QUERY_PATH)
    if hoofdgroep_filter:
        unknown = set(hoofdgroep_filter) - set(hoofdgroepen)
        if unknown:
            log.warning("Requested hoofdgroepen not found in the source graph: %s", ", ".join(sorted(unknown)))
        hoofdgroepen = [hg for hg in hoofdgroepen if hg in hoofdgroep_filter]

    log.info("Exporting objects for %d hoofdgroepen: %s", len(hoofdgroepen), ", ".join(hoofdgroepen))
    written_paths = export_objects_per_hoofdgroep(client, hoofdgroepen, objects_output_folder, objects_template_path)

    merge_csv_files(written_paths, merged_objects_output_path)
