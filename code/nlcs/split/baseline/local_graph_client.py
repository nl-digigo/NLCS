"""SPARQL client backed by a local RDF file instead of a live HTTP endpoint.

Same interface as LacesClient, so it drops into the existing exporter
unchanged - lets the publicatie queries run against a merged publication
Turtle file for validation instead of a Laces workspace endpoint.
"""
import logging
from pathlib import Path

from rdflib import Graph

log = logging.getLogger(__name__)


class LocalGraphClient:
    def __init__(self, source_path: Path, rdf_format: str = "turtle") -> None:
        self.source_path = Path(source_path)
        self.graph = Graph()
        log.info("Loading local graph from %s", self.source_path)
        self.graph.parse(str(self.source_path), format=rdf_format)
        log.info("Loaded %d triples", len(self.graph))

    def query(self, sparql: str, accept: str = "text/csv") -> str:
        """Runs a SPARQL SELECT query, returns CSV text in the same shape LacesClient.query() returns."""
        result = self.graph.query(sparql)
        csv_bytes = result.serialize(format="csv")
        return csv_bytes.decode("utf-8").replace("\r\n", "\n").replace("\n\n", "\n")
