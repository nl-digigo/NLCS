"""
publication_merger.py
----------------------------
Retrieves the full RDF graph from multiple Laces publications (via their
SPARQL endpoints) and merges them into a single Turtle file, deduplicating
triples, prefixes and namespace declarations.

Usage
-----
    python publication_merger.py

Configuration
-------------
Edit PUBLICATIONS and OUTPUT_PATH below. Each publication entry is the base
publication URL (without the trailing /sparql) as shown in the Laces hub.
"""

import logging
import os

import requests
from rdflib import Graph
from requests.auth import HTTPBasicAuth

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LDP_TOKEN_ID = ""
LDP_PASSWORD = ""

# Base publication URLs (the script appends "/sparql" to each).
# One entry per hoofdgroep, except the "C"-suffixed ones (BC, FC, GC, HC, KC, MC, SC),
# which are combined into the single "constructie" publication.
PUBLICATIONS = [
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-aspects-lijnkleur-lijnweight-and-shared-lijntypes",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---al",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---am",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---bv",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---es",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---fv",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---gk",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---gr",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---gw",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---hu",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---ie",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---is",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---iv",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---iw",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---kg",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---kl",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---kw",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---mo",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---mw",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---ob",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---og",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---ov",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---ri",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---sb",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---vh",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---vv",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---vw",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---wh",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---zz",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/test/nlcs-split---constructie",
]

CONSTRUCT_ALL_QUERY = "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"

OUTPUT_PATH = "./code/nlcs/split/merger/merged_publications.ttl"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Retrieval
# ---------------------------------------------------------------------------

def fetch_publication_graph(publication_url: str, token_id: str, password: str) -> Graph:
    """Runs a CONSTRUCT-all query against a publication's SPARQL endpoint
    and parses the result into an rdflib Graph."""
    if publication_url.startswith("http://"):
        publication_url = "https://" + publication_url[len("http://"):]
    endpoint = publication_url.rstrip("/") + "/sparql"
    log.info("Fetching graph from %s", endpoint)

    response = requests.post(
        endpoint,
        data=CONSTRUCT_ALL_QUERY.encode("utf-8"),
        headers={
            "Content-Type": "application/sparql-query",
            "Accept": "text/turtle",
        },
        auth=HTTPBasicAuth(token_id, password),
        timeout=120,
    )
    response.raise_for_status()

    graph = Graph()
    graph.parse(data=response.text, format="turtle")
    log.info("  Parsed %d triples", len(graph))
    return graph


def merge_publications(publication_urls: list[str], token_id: str, password: str) -> Graph:
    """Fetches each publication's graph and merges them into one Graph.

    rdflib's Graph is triple-set based, so merging via `+=` naturally
    deduplicates identical triples. Namespace bindings are merged onto the
    first graph, skipping prefixes already bound to avoid duplicate/clashing
    @prefix declarations in the serialized output.
    """
    merged = Graph()

    for url in publication_urls:
        graph = fetch_publication_graph(url, token_id, password)

        for prefix, namespace in graph.namespace_manager.namespaces():
            existing = dict(merged.namespace_manager.namespaces()).get(prefix)
            if existing is None:
                merged.bind(prefix, namespace, override=False)
            elif str(existing) != str(namespace):
                log.warning(
                    "  Prefix '%s' bound to '%s' in a previous publication; "
                    "keeping that binding and ignoring '%s' from %s",
                    prefix, existing, namespace, url,
                )

        merged += graph

    log.info("Merged graph contains %d triples total.", len(merged))
    return merged


def save_graph(graph: Graph, output_path: str) -> None:
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    graph.serialize(destination=output_path, format="turtle")
    log.info("Saved merged Turtle file to %s", output_path)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    merged_graph = merge_publications(PUBLICATIONS, LDP_TOKEN_ID, LDP_PASSWORD)
    save_graph(merged_graph, OUTPUT_PATH)
    log.info("Done.")
