"""Configuration for the NLCS 5.0 baseline exporter.

Produces the golden, pre-split reference tables (from the single NLCS 5.0
workspace) that the split-and-merged publication is validated against.
Output is kept under tabellen/split-baseline/5.0/, separate from
tabellen/publicatie (the live 5.1 exporter's output), so running this never
overwrites production publication tables.
"""
import os
from pathlib import Path

VERSION = "5.0"

# Public endpoint - no credentials required. Override via env vars only if
# your Laces instance requires auth.
SPARQL_ENDPOINT = os.environ.get(
    "NLCS_SPARQL_ENDPOINT",
    "https://hub.laces.tech/digitalbuildingdata/nlcs/live/nlcs/versions/5_0_2/sparql",
)
LDP_TOKEN_ID = os.environ.get("LDP_TOKEN_ID", "3dd8c6a6-7a9a-4fdd-9b7e-606b74d492fe")
LDP_PASSWORD = os.environ.get("LDP_PASSWORD", "6MgHRTEde6mHV3YfC74h")

REPO_ROOT = Path(__file__).resolve().parents[4]

PUBLICATIE_QUERY_FOLDER = REPO_ROOT / "code" / "nlcs" / "publicatie"
HOOFDGROEPEN_QUERY_PATH = REPO_ROOT / "code" / "nlcs" / "nlcs_exporter" / "NLCS_Retrieve_Hoofdgroepen.rq"
OBJECTS_TEMPLATE_QUERY_PATH = REPO_ROOT / "code" / "nlcs" / "nlcs_exporter" / "template_objects_per_hoofdgroup.rq"
HOOFDGROUP_PLACEHOLDER = "$hoofdgroup_name"

OUTPUT_ROOT = REPO_ROOT / "tabellen" / "split-baseline" / VERSION
CONCEPT_TABLES_OUTPUT_FOLDER = OUTPUT_ROOT
OBJECTS_OUTPUT_FOLDER = OUTPUT_ROOT / "objectentabellen"
MERGED_OBJECTS_OUTPUT_PATH = OUTPUT_ROOT / f"all_objects-{VERSION}.csv"
