"""ex_core.py - laadt code/nlcs/nlcs_exporter/nlcs_exporter.py (ONGEWIJZIGD) en
draait de export-pipeline tegen een gekozen SPARQL-endpoint.

De exporter gebruikt relatieve paden: queries uit ./code/nlcs/... en uitvoer naar
tabellen/... en ./html/. Daarom:
  - de REPO-map (met ./code/nlcs/...) wordt de werkmap (voor het lezen van queries);
  - de UITVOER-map bepaalt waar tabellen/ en html/ worden weggeschreven (we
    overschrijven daarvoor de output-folderconstantes van de exporter).
publication/nlcs_exporter zelf wordt niet aangepast.
"""
import os
import sys

# requests en pandas statisch importeren zodat PyInstaller ze (met numpy e.d.)
# meebundelt: nlcs_exporter wordt dynamisch via sys.path geladen en valt buiten
# de statische analyse. Niet verwijderen.
import requests  # noqa: F401
import pandas  # noqa: F401


def _exporter_dir() -> str:
    """Map met nlcs_exporter.py + html_exporter.py + utils.py."""
    if getattr(sys, "frozen", False):
        return sys._MEIPASS
    here = os.path.dirname(os.path.abspath(__file__))
    root = os.path.abspath(os.path.join(here, "..", ".."))   # beheer/..tool -> repo
    return os.path.join(root, "code", "nlcs", "nlcs_exporter")


_EXDIR = _exporter_dir()
if _EXDIR not in sys.path:
    sys.path.insert(0, _EXDIR)

import nlcs_exporter as ex   # noqa: E402  (trekt html_exporter/utils mee)

DEFAULT_ENDPOINT = ex.SPARQL_ENDPOINT

# (sleutel, label) - volgorde zoals het __main__ van de exporter
STEPS = [
    ("controles", "Controles (+ increasing IDs, vervallen labels)"),
    ("publicatie", "Publicatie-queries"),
    ("objecten", "Objecten per hoofdgroep + samenvoegen"),
    ("changelog", "Changelog-queries"),
    ("html", "HTML per hoofdgroep"),
]

HG_QUERY = "./code/nlcs/nlcs_exporter/NLCS_Retrieve_Hoofdgroepen.rq"


def default_repo_root() -> str:
    if getattr(sys, "frozen", False):
        return os.getcwd()
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.abspath(os.path.join(here, "..", ".."))


def _apply_output_root(out_root: str) -> str:
    """Zet de output-folders van de exporter onder out_root; retour html-basismap."""
    ex.PUBLICATIE_OUTPUT_FOLDER = os.path.join(out_root, "tabellen", "publicatie")
    ex.OBJECTS_OUTPUT_FOLDER = os.path.join(
        out_root, "tabellen", "publicatie", "objectentabellen")
    ex.CONTROL_OUTPUT_FOLDER = os.path.join(out_root, "tabellen", "controles")
    ex.CHANGELOG_OUTPUT_FOLDER = os.path.join(out_root, "tabellen", "changelog")
    return os.path.join(out_root, "html")


def run_export(endpoint, token, password, steps, repo_root, out_root):
    """Draait de gekozen stappen. `steps` = dict {sleutel: bool}."""
    repo_root = repo_root or default_repo_root()
    out_root = out_root or repo_root
    os.chdir(repo_root)
    ex.SPARQL_ENDPOINT = endpoint
    html_base = _apply_output_root(out_root)

    print(f"Repo-map (queries): {repo_root}")
    print(f"Uitvoermap        : {out_root}")
    print(f"SPARQL-endpoint   : {endpoint}")

    client = ex.LacesRequest(config={
        "url": endpoint, "username": token, "password": password})
    ex.client = client            # sommige functies gebruiken de module-global
    version = ex.version

    if steps.get("controles"):
        print("\n=== Controles ===")
        ex.run_queries_in_folder(client, ex.CONTROL_QUERY_FOLDER,
                                 ex.CONTROL_OUTPUT_FOLDER)
        for name, fn in (("increasing IDs", ex.check_increasing_ids),
                         ("vervallen labels", ex.check_vervallen_object_labels)):
            try:
                fn()
            except Exception as e:   # noqa: BLE001
                print(f"ERROR ({name}): {e}")

    if steps.get("publicatie"):
        print("\n=== Publicatie-queries ===")
        ex.run_queries_in_folder(client, ex.PUBLICATIE_QUERY_FOLDER,
                                 ex.PUBLICATIE_OUTPUT_FOLDER)

    if steps.get("objecten"):
        print("\n=== Objecten per hoofdgroep ===")
        for hg in ex.retrieve_hoofdgroepen(client, HG_QUERY):
            try:
                q = ex.build_parameterized_query(
                    ex.TEMPLATE_QUERY_PATH, "$hoofdgroup_name", hg)
                out = os.path.join(ex.OBJECTS_OUTPUT_FOLDER,
                                   f"objecten-concept-{version}-{hg}.csv")
                ex.save_csv_results(client.run_query_clean_result(q), out)
            except Exception as e:   # noqa: BLE001
                print(f"ERROR (hoofdgroep {hg}): {e}")
        merged = os.path.join(ex.PUBLICATIE_OUTPUT_FOLDER,
                              f"all_objects-concept-{version}.csv")
        ex.merge_csv_files(ex.OBJECTS_OUTPUT_FOLDER, merged)

    if steps.get("changelog"):
        print("\n=== Changelog-queries ===")
        ex.run_queries_in_folder(client, ex.CHANGELOG_QUERY_FOLDER,
                                 ex.CHANGELOG_OUTPUT_FOLDER)

    if steps.get("html"):
        print("\n=== HTML per hoofdgroep ===")
        os.makedirs(html_base, exist_ok=True)
        for hg in ex.retrieve_hoofdgroepen(client, HG_QUERY):
            try:
                q = ex.build_parameterized_query(
                    ex.TEMPLATE_QUERY_PATH, "$hoofdgroup_name", hg)
                out = os.path.join(html_base,
                                   f"objecten-concept-{version}-{hg}.html")
                ex.sparql_to_html(client.run_query_clean_result(q), out,
                                  column_rules=ex.COLUMN_RULES)
            except Exception as e:   # noqa: BLE001
                print(f"ERROR (HTML {hg}): {e}")

    print("\nKlaar.")
