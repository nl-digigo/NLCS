"""
nlcs_split_by_hoofdgroep.py
----------------------------
Retrieves NLCS v5.0 data from the Laces SPARQL endpoint and exports one TTL
file per hoofdgroep per concept type, ready for re-import into separate Laces
workspaces.

Shared concept types (lijnkleuren, lijnweights, bewerkingen, disciplines,
statussen) are exported once to the shared/ sub-folder.

Usage
-----
    python nlcs_split_by_hoofdgroep.py

Configuration
-------------
Edit the constants at the top of the file as needed.  The v5.0 live endpoint
is public; set LDP_TOKEN_ID / LDP_PASSWORD to empty strings if no auth is
required, or provide credentials if your organisation's Laces instance is
protected.
"""

import os
import glob
import logging
from io import StringIO
from typing import Optional

import pandas as pd
import requests
from requests.auth import HTTPBasicAuth

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SPARQL_ENDPOINT = (
    "https://hub.laces.tech/digitalbuildingdata/nlcs/live/nlcs/versions/5_0_2/sparql"
)

# Leave empty strings if the endpoint is public
LDP_TOKEN_ID = ""
LDP_PASSWORD = ""

VERSION = "5.0"

QUERY_FOLDER = "./code/nlcs/split"
HOOFDGROEPEN_QUERY_PATH = "./code/nlcs/nlcs_exporter/NLCS_Retrieve_Hoofdgroepen.rq"

OUTPUT_ROOT = "output/split"
SHARED_OUTPUT_FOLDER = os.path.join(OUTPUT_ROOT, "shared")

# Queries that are run once per hoofdgroep (parameterised with $hoofdgroup_name)
PARAMETERIZED_QUERIES = [
    "construct_objects_per_hoofdgroep.rq",
    # "construct_arceringen_per_hoofdgroep.rq",
    "construct_symbolen_per_hoofdgroep.rq",
    "construct_lijntypes_per_hoofdgroep.rq",
    "construct_lijnkleuren_lijnweights_per_hoofdgroep.rq",
]

HOOFDGROUP_PLACEHOLDER = "$hoofdgroup_name"

# Query that converts OWL/SKOS endpoint data to Laces OTL format (shared concepts).
OTL_CONSTRUCT_QUERY = "construct_shared_as_laces_otl.rq"

# ---------------------------------------------------------------------------
# Run configuration — edit these before running
# ---------------------------------------------------------------------------

# Which hoofdgroepen to export.  Set to None to retrieve all from the endpoint.
# Example single:  RUN_HOOFDGROEPEN = ["AL"]
# Example subset:  RUN_HOOFDGROEPEN = ["AL", "AS", "BC"]
RUN_HOOFDGROEPEN = ["AL"]

# Set to True to also export shared concepts (lijnkleuren, statussen, etc.)
RUN_SHARED = False

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

class LacesClient:
    """Thin SPARQL-over-HTTP client for Laces endpoints."""

    def __init__(self, endpoint: str, token_id: str = "", password: str = "") -> None:
        self.endpoint = endpoint
        self.auth: Optional[HTTPBasicAuth] = None
        if token_id and password:
            self.auth = HTTPBasicAuth(token_id, password)

    def _post(self, query: str, accept: str) -> requests.Response:
        resp = requests.post(
            self.endpoint,
            data=query.encode("utf-8"),
            headers={
                "Content-Type": "application/sparql-query",
                "Accept": accept,
            },
            auth=self.auth,
            timeout=120,
        )
        resp.raise_for_status()
        return resp

    def select(self, query: str) -> str:
        """Run a SELECT query, return result as CSV text."""
        resp = self._post(query, accept="text/csv")
        text = resp.text.replace("\r\n", "\n").replace("\n\n", "\n")
        return text

    def construct(self, query: str) -> str:
        """Run a CONSTRUCT query, return result as Turtle text."""
        resp = self._post(query, accept="text/turtle")
        return resp.text


# ---------------------------------------------------------------------------
# Query / IO helpers
# ---------------------------------------------------------------------------

def load_query(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()


def parameterize(query: str, placeholder: str, value: str) -> str:
    if placeholder not in query:
        log.warning("Placeholder '%s' not found in query.", placeholder)
    return query.replace(placeholder, value)


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def save_ttl(ttl_text: str, output_path: str) -> bool:
    """Save Turtle content to a file, skip if empty."""
    stripped = ttl_text.strip()
    if not stripped or stripped in ("@prefix .", ""):
        log.info("  (empty result — skipping %s)", os.path.basename(output_path))
        return False
    ensure_dir(os.path.dirname(output_path))
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(ttl_text)
    log.info("  Saved → %s", output_path)
    return True


# ---------------------------------------------------------------------------
# Core retrieval functions
# ---------------------------------------------------------------------------

def retrieve_hoofdgroepen(client: LacesClient, query_path: str) -> list[str]:
    log.info("Retrieving hoofdgroepen from %s", query_path)
    try:
        csv_text = client.select(load_query(query_path))
        df = pd.read_csv(StringIO(csv_text), dtype=str)
    except Exception as exc:
        log.error("Failed to retrieve hoofdgroepen: %s", exc)
        return []

    if df.empty or "hoofdgroup_name" not in df.columns:
        log.warning(
            "Hoofdgroepen query returned no 'hoofdgroup_name' column. "
            "Columns: %s", df.columns.tolist()
        )
        return []

    hoofdgroepen = df["hoofdgroup_name"].dropna().tolist()
    log.info("Found %d hoofdgroepen: %s", len(hoofdgroepen), hoofdgroepen)
    return hoofdgroepen


def retrieve_common_concepts(client: LacesClient, query_path: str) -> str:
    """Run the shared-concepts OTL CONSTRUCT query against the Laces endpoint."""
    return client.construct(load_query(query_path))


def run_shared_otl_export(client: LacesClient) -> None:
    """Run construct_shared_as_laces_otl.rq and write the result to shared/."""
    query_path = os.path.join(QUERY_FOLDER, OTL_CONSTRUCT_QUERY)
    output_path = os.path.join(SHARED_OUTPUT_FOLDER, f"shared_concepts_otl-{VERSION}.ttl")
    log.info("\n--- Generating shared concepts in Laces OTL format ---")
    log.info("Running %s ...", OTL_CONSTRUCT_QUERY)
    try:
        ttl = retrieve_common_concepts(client, query_path)
        save_ttl(ttl, output_path)
    except Exception as exc:
        log.error("Error running %s: %s", OTL_CONSTRUCT_QUERY, exc)

def run_per_hoofdgroep_queries(client: LacesClient, hoofdgroepen: list[str]) -> None:
    """For each hoofdgroep, run all parameterised CONSTRUCT queries."""
    log.info("\n--- Running per-hoofdgroep queries ---")
    for hg in hoofdgroepen:
        log.info("\nHoofdgroep: %s", hg)
        hg_folder = os.path.join(OUTPUT_ROOT, hg)
        ensure_dir(hg_folder)
        for query_file in PARAMETERIZED_QUERIES:
            query_path = os.path.join(QUERY_FOLDER, query_file)
            stem = os.path.splitext(query_file)[0]
            output_path = os.path.join(hg_folder, f"{stem}-{VERSION}-{hg}.ttl")
            log.info("  %s ...", query_file)
            try:
                template = load_query(query_path)
                query = parameterize(template, HOOFDGROUP_PLACEHOLDER, hg)
                ttl = client.construct(query)
                save_ttl(ttl, output_path)
            except Exception as exc:
                log.error("  Error running %s for '%s': %s", query_file, hg, exc)


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    client = LacesClient(SPARQL_ENDPOINT, LDP_TOKEN_ID, LDP_PASSWORD)

    if RUN_SHARED:
        run_shared_otl_export(client)

    if RUN_HOOFDGROEPEN is None:
        hoofdgroepen = retrieve_hoofdgroepen(client, HOOFDGROEPEN_QUERY_PATH)
        if not hoofdgroepen:
            log.error("No hoofdgroepen found — aborting.")
            raise SystemExit(1)
    else:
        hoofdgroepen = RUN_HOOFDGROEPEN

    run_per_hoofdgroep_queries(client, hoofdgroepen)

    log.info("\nDone.  Output written to: %s", OUTPUT_ROOT)
