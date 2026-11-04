"""ex_core.py - draait de 'publicatie'-SPARQL-queries RECHTSTREEKS tegen een Laces
SPARQL-endpoint en schrijft CSV's. GEBRUIKT NIET nlcs_exporter.py; alleen de
.rq-bestanden uit code/nlcs/publicatie/ (die worden live uit de repo-map gelezen,
zodat aanpassingen aan de queries meteen meetellen).

Naamgeving van de output:
  - onderwerp-tabellen  : <onderwerp>-<versie>.csv            (plat in de uitvoermap)
  - objecten per hoofdgroep: objectentabellen/objecten-<HG>-<versie>.csv

De onderwerp-slug komt uit de bestandsnaam: NLCS_Query_Symbolen.rq -> 'symbolen'.
De objectentabel komt uit 'query objects classic.rq' met de placeholder
"?hoofdgroepCode" die per hoofdgroep wordt vervangen.
"""
import csv
import glob
import io
import os
import sys

import requests  # enige externe dependency

DEFAULT_VERSION = "5-2"

# objecten-query (per hoofdgroep) + placeholder die we per hoofdgroep vervangen
OBJECT_QUERY_FILE = "query objects classic.rq"
OBJECT_PLACEHOLDER = '"?hoofdgroepCode"'
HOOFDGROEPEN_QUERY_FILE = "NLCS_Query_Hoofdgroepen.rq"
OBJECTEN_SUBDIR = "objectentabellen"

# LIN/PAT-generatie (los te draaien): queries uit beheer/generateLIN-PATfiles/
LIN_QUERY_REL = os.path.join("beheer", "generateLIN-PATfiles", "resources",
                             "retrieveLinetypeInfo.rq")
PAT_QUERY_REL = os.path.join("beheer", "generateLIN-PATfiles", "resources",
                             "retrieveArceringInfo.rq")
ARCERINGEN_SUBDIR = "arceringen"


def publicatie_dir(repo_root: str) -> str:
    return os.path.join(repo_root, "code", "nlcs", "publicatie")


def default_repo_root() -> str:
    """Zoek omhoog naar de map die code/nlcs/publicatie bevat (de repo-root)."""
    if getattr(sys, "frozen", False):
        start = os.path.dirname(os.path.abspath(sys.executable))
    else:
        start = os.path.dirname(os.path.abspath(__file__))
    d = start
    for _ in range(8):
        if os.path.isdir(os.path.join(d, "code", "nlcs", "publicatie")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    return start


# -- SPARQL-client ---------------------------------------------------------
class LacesClient:
    """Minimalistische SPARQL-client: POST de query, krijg CSV terug."""

    def __init__(self, endpoint: str, username: str, password: str):
        self.endpoint = endpoint
        self.auth = (username, password)

    def run_csv(self, query: str, timeout: int = 180, params=None):
        return requests.post(
            self.endpoint,
            params=params,
            data=query.encode("utf-8"),
            headers={"Content-type": "application/sparql-query",
                     "Accept": "text/csv"},
            auth=self.auth,
            timeout=timeout,
        )


def normalize_endpoint(endpoint: str) -> str:
    """Trailing slash eraf, http->https (301-redirect gooit anders de POST-body
    weg -> HTTP 400), en /sparql toevoegen als het ontbreekt."""
    ep = (endpoint or "").strip().rstrip("/")
    if ep.lower().startswith("http://"):
        ep = "https://" + ep[len("http://"):]
    if ep and not ep.lower().endswith("/sparql"):
        ep += "/sparql"
    return ep


# -- helpers ---------------------------------------------------------------
def _read_text(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def _write_csv(text: str, out_path: str) -> int:
    """Schrijf CSV-tekst (zoals Laces hem teruggeeft) en geef het aantal
    datarijen terug (regels minus header)."""
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        f.write(text)
    rows = max(0, sum(1 for _ in io.StringIO(text)) - 1)
    return rows


def _subject_slug(filename: str) -> str:
    """NLCS_Query_Symbolen.rq -> 'symbolen'."""
    stem = os.path.splitext(os.path.basename(filename))[0]
    if stem.lower().startswith("nlcs_query_"):
        stem = stem[len("nlcs_query_"):]
    return stem.lower()


def _parse_hoofdgroep_codes(csv_text: str) -> list:
    """Haal de hoofdgroep-codes (kolom 'afkorting', anders 'hoofdgroep') uit de
    hoofdgroepen-CSV. Dit is de waarde die in de objecten-FILTER hoort."""
    reader = csv.DictReader(io.StringIO(csv_text))
    cols = reader.fieldnames or []
    col = "afkorting" if "afkorting" in cols else (
        "hoofdgroep" if "hoofdgroep" in cols else (cols[-1] if cols else None))
    if not col:
        return []
    codes = []
    for row in reader:
        v = (row.get(col) or "").strip()
        if v and v not in codes:
            codes.append(v)
    return sorted(codes)


def subject_query_files(repo_root: str) -> list:
    """Alle 'klaar'-onderwerpqueries: NLCS_Query_*.rq in publicatie/. De objecten-
    queries (NLCS_Query_Objects / _Verkort, zonder .rq) vallen hier vanzelf buiten;
    'query objects classic.rq' begint niet met NLCS_Query_ en valt dus ook buiten."""
    pat = os.path.join(publicatie_dir(repo_root), "NLCS_Query_*.rq")
    return sorted(glob.glob(pat))


# -- hoofdfunctie ----------------------------------------------------------
def run_export(endpoint, token, password, version, repo_root, out_root,
               do_subjects=True, do_objects=True, hoofdgroep_filter=None,
               log=print):
    """Draait de geselecteerde queries en schrijft de CSV's."""
    repo_root = repo_root or default_repo_root()
    out_root = out_root or repo_root
    version = (version or DEFAULT_VERSION).strip() or DEFAULT_VERSION
    endpoint = normalize_endpoint(endpoint)
    pubdir = publicatie_dir(repo_root)

    log(f"Repo-map (queries): {repo_root}")
    log(f"Uitvoermap        : {out_root}")
    log(f"SPARQL-endpoint   : {endpoint}")
    log(f"Versielabel       : {version}")
    if not os.path.isdir(pubdir):
        raise RuntimeError(
            f"Query-map niet gevonden: {pubdir}. Kies de repo-map waarin "
            f"code/nlcs/publicatie staat.")

    client = LacesClient(endpoint, token, password)

    # preflight: endpoint/login controleren vóór de hele run
    try:
        r = client.run_csv("SELECT ?s WHERE { ?s ?p ?o } LIMIT 1", timeout=30)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Kan het SPARQL-endpoint niet bereiken ({endpoint}): {e}")
    if r.status_code != 200:
        snip = (r.text or "")[:160].replace("\n", " ")
        raise RuntimeError(
            f"SPARQL-endpoint gaf HTTP {r.status_code}. Controleer endpoint "
            f"(moet op /sparql eindigen) en login/rechten. Antwoord: {snip}")
    log("Endpoint OK (test-query -> 200).\n")

    ok = fail = 0

    if do_subjects:
        files = subject_query_files(repo_root)
        log(f"=== Onderwerp-tabellen ({len(files)}) ===")
        for qf in files:
            slug = _subject_slug(qf)
            try:
                resp = client.run_csv(_read_text(qf))
                if resp.status_code != 200:
                    log(f"  FOUT {slug}: HTTP {resp.status_code}")
                    fail += 1
                    continue
                out = os.path.join(out_root, f"{slug}-{version}.csv")
                n = _write_csv(resp.text, out)
                log(f"  {slug}-{version}.csv  ({n} rijen)")
                ok += 1
            except Exception as e:  # noqa: BLE001
                log(f"  FOUT {slug}: {e}")
                fail += 1

    if do_objects:
        log("\n=== Objectentabellen per hoofdgroep ===")
        obj_path = os.path.join(pubdir, OBJECT_QUERY_FILE)
        hg_path = os.path.join(pubdir, HOOFDGROEPEN_QUERY_FILE)
        if not os.path.isfile(obj_path):
            log(f"  Objecten-query ontbreekt: {obj_path} — overgeslagen.")
        else:
            template = _read_text(obj_path)
            if OBJECT_PLACEHOLDER not in template:
                log(f"  LET OP: placeholder {OBJECT_PLACEHOLDER} niet gevonden in "
                    f"{OBJECT_QUERY_FILE}; alleen de hardgecodeerde hoofdgroep "
                    f"wordt gedraaid.")
            # hoofdgroep-codes ophalen
            codes = []
            try:
                hg_resp = client.run_csv(_read_text(hg_path), timeout=60)
                if hg_resp.status_code == 200:
                    codes = _parse_hoofdgroep_codes(hg_resp.text)
            except Exception as e:  # noqa: BLE001
                log(f"  Kon hoofdgroepen niet ophalen: {e}")
            if hoofdgroep_filter:
                wanted = {h.strip().upper() for h in hoofdgroep_filter if h.strip()}
                codes = [c for c in codes if c.upper() in wanted]
            if not codes:
                log("  Geen hoofdgroepen gevonden/geselecteerd — overgeslagen.")
            else:
                log(f"  Hoofdgroepen: {', '.join(codes)}")
                all_header = None          # header van de 1e tabel
                all_body: list[str] = []   # datarijen van álle hoofdgroepen
                for hg in codes:
                    q = template.replace(OBJECT_PLACEHOLDER, f'"{hg}"')
                    try:
                        resp = client.run_csv(q)
                        if resp.status_code != 200:
                            log(f"  FOUT objecten-{hg}: HTTP {resp.status_code}")
                            fail += 1
                            continue
                        out = os.path.join(out_root, OBJECTEN_SUBDIR,
                                           f"objecten-{hg}-{version}.csv")
                        n = _write_csv(resp.text, out)
                        log(f"  {OBJECTEN_SUBDIR}/objecten-{hg}-{version}.csv  "
                            f"({n} rijen)")
                        ok += 1
                        # verzamel voor het gecombineerde all-objects-bestand
                        lines = resp.text.splitlines()
                        if lines:
                            if all_header is None:
                                all_header = lines[0]
                            all_body.extend(l for l in lines[1:] if l)
                    except Exception as e:  # noqa: BLE001
                        log(f"  FOUT objecten-{hg}: {e}")
                        fail += 1
                # Alle objectentabellen samen in één document. NIET in de map
                # 'objectentabellen/' (anders leest de changelog-tool dit dubbel),
                # maar in de uitvoermap-root.
                if all_header is not None:
                    combined = os.path.join(out_root, f"all-objects-{version}.csv")
                    with open(combined, "w", encoding="utf-8", newline="") as f:
                        f.write(all_header + "\n")
                        f.write("\n".join(all_body))
                        if all_body:
                            f.write("\n")
                    log(f"  all-objects-{version}.csv  ({len(all_body)} rijen "
                        f"uit {len(codes)} hoofdgroep(en))")
                    ok += 1

    log(f"\nKlaar. {ok} bestand(en) geschreven, {fail} fout(en).")


# -- LIN/PAT-generatie (los te draaien) ------------------------------------
def _clean_csv(text: str) -> str:
    """Zelfde opschoning als het originele processing.py (convert_response)."""
    return text.replace("\r\n", "\n").replace("\n\n", "\n")


def _derive_type_version(endpoint: str, fallback_version: str = ""):
    """('concept'|'definitief', versielabel) uit een versioned endpoint-URL.
    test/acceptance -> concept, anders definitief. Versie = segment vóór /sparql
    (… /versions/<ver>/sparql), met '_' -> '.' zoals het originele script."""
    type_publication = "definitief"
    try:
        repo = endpoint.split("digitalbuildingdata/nlcs/", 1)[1].split("/", 1)[0]
        if repo in ("test", "acceptance"):
            type_publication = "concept"
    except Exception:  # noqa: BLE001
        pass
    version = fallback_version
    parts = endpoint.rstrip("/").split("/")
    if parts:
        seg = parts[-2] if (parts[-1].lower() == "sparql" and len(parts) >= 2) \
            else parts[-1]
        if seg and seg.lower() != "sparql":
            version = seg.replace("_", ".")
    return type_publication, (version or fallback_version or "onbekend")


def _gen_lin(client, repo_root, out_root, type_pub, version, log) -> None:
    qpath = os.path.join(repo_root, LIN_QUERY_REL)
    if not os.path.isfile(qpath):
        raise RuntimeError(f"LIN-query niet gevonden: {qpath}")
    resp = client.run_csv(_read_text(qpath))
    if resp.status_code != 200:
        raise RuntimeError(f"LIN-query gaf HTTP {resp.status_code}")
    rows = list(csv.DictReader(io.StringIO(_clean_csv(resp.text))))
    # GEEN headerregel ("Lin bestand gegenereerd uit…") en geen lege regels
    # bovenaan: het bestand begint direct met de eerste *lijntype-regel.
    lines = []
    for r in rows:
        name = (r.get("tgtLinetypeName") or "").strip()
        lid = (r.get("tgtLinetypeID") or "").strip()
        lines.append(f"\n*{name},{lid}")
        info = (r.get("tgtLinetypeInfo") or "").replace("\\", "")
        info = (info.replace("“", '"').replace("”", '"')
                    .replace("‘", "'").replace("’", "'"))
        info = ",".join(p.strip() for p in info.split(","))
        lines.append(info)
    out = os.path.join(out_root,
                       f"NLCS-{type_pub}-{version.replace('.', '-')}_linetypes.lin")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8") as f:
        f.write("\n".join(lines).lstrip("\n"))
    log(f"LIN: {os.path.basename(out)}  ({len(rows)} lijntypes)")


def _gen_pat(client, repo_root, out_root, type_pub, version, log) -> None:
    qpath = os.path.join(repo_root, PAT_QUERY_REL)
    if not os.path.isfile(qpath):
        raise RuntimeError(f"PAT-query niet gevonden: {qpath}")
    resp = client.run_csv(_read_text(qpath))
    if resp.status_code != 200:
        raise RuntimeError(f"PAT-query gaf HTTP {resp.status_code}")
    rows = list(csv.DictReader(io.StringIO(_clean_csv(resp.text))))
    head = (f";;\n;;pat definitie/bestand gegenereerd uit de NLCS database versie "
            f"{type_pub}-{version}\n;;")
    allpat = head
    pat_dir = os.path.join(out_root, ARCERINGEN_SUBDIR)
    os.makedirs(pat_dir, exist_ok=True)
    n = 0
    for r in rows:
        name = (r.get("tgtArceringName") or "").strip()
        kort = (r.get("tgtArceringVRKL_KORT") or "").strip()
        lang = (r.get("tgtArceringVRKL_LANG") or "").strip()
        if not name:
            continue
        # spaties -> regeleindes (zoals het originele script): elke dash-regel apart
        block = f"\n*{name},{kort}\n{lang}\n".replace(" ", "\n")
        allpat += block
        safe = name.replace("/", "_").replace("\\", "_")
        with open(os.path.join(pat_dir, f"{safe}.pat"), "w", encoding="utf-8") as f:
            f.write(head + block)
        n += 1
    out = os.path.join(out_root, "NLCS-allPatInOne.pat")
    with open(out, "w", encoding="utf-8") as f:
        f.write(allpat)
    log(f"PAT: NLCS-allPatInOne.pat + {n} losse .pat in {ARCERINGEN_SUBDIR}/")


def generate_lin_pat(endpoint, token, password, repo_root, out_root,
                     do_lin=True, do_pat=True, version_fallback="", log=print):
    """Genereer .lin en/of .pat uit een versioned NLCS SPARQL-endpoint. Los te
    draaien, los van de tabel-export. Repliceert beheer/generateLIN-PATfiles."""
    repo_root = repo_root or default_repo_root()
    out_root = out_root or repo_root
    endpoint = normalize_endpoint(endpoint)
    type_pub, version = _derive_type_version(endpoint, version_fallback)
    log(f"SPARQL-endpoint   : {endpoint}")
    log(f"Uitvoermap        : {out_root}")
    log(f"Type/versie       : {type_pub}-{version}\n")

    client = LacesClient(endpoint, token, password)
    try:
        r = client.run_csv("SELECT ?s WHERE { ?s ?p ?o } LIMIT 1", timeout=30)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Kan het SPARQL-endpoint niet bereiken ({endpoint}): {e}")
    if r.status_code != 200:
        snip = (r.text or "")[:160].replace("\n", " ")
        raise RuntimeError(
            f"SPARQL-endpoint gaf HTTP {r.status_code}. Controleer endpoint "
            f"(versioned, op /sparql) en login/rechten. Antwoord: {snip}")
    log("Endpoint OK (test-query -> 200).\n")

    if do_lin:
        _gen_lin(client, repo_root, out_root, type_pub, version, log)
    if do_pat:
        _gen_pat(client, repo_root, out_root, type_pub, version, log)
    log("\nKlaar (LIN/PAT).")


# -- BGT-mapping-export ----------------------------------------------------
# De BGT→NLCS mapping-query (code/bgt-nlcs/queryNLCS_BGT.rq) draait tegen een
# ANDERE dataset dan NLCS 5.2 (eigen endpoint + eigen credentials) en koppelt de
# BGT-objecten via skos:related aan NLCS-objecten/symbolen in een named graph.
DEFAULT_NLCS_GRAPH = ("http://hub.laces.tech/digitalbuildingdata/nlcs/live/"
                      "nlcs/versions/5_0_2")

# De kolomvolgorde van de opgeslagen mapping-CSV (NLCS-<versie>-BGT.csv), met de
# twee extra kolommen NLCSHoofdgroep en NLCSSbib.
BGT_COLUMNS = [
    "object", "bgt_type", "function", "class", "plus_type",
    "plus_functieWegdeel", "plusfunctieSpoor", "surfaceMaterial",
    "bgt_fysiekVoorkomen", "plus_typeGebouwInstallatie", "plus_fysiekVoorkomen",
    "plus_fysiekVoorkomenWegdeel", "plus_fysiekVoorkomenOndersteunendWegdeel",
    "NLCSObjectURI", "NLCSObjectID", "NLCSHoofdgroep", "layerInfo",
    "NLCSSymbolURI", "NLCSSymbolID", "NLCSSbib", "symbolInfo", "uri", "id",
]


def _bgt_prepare_query(query: str, nlcs_graph: str) -> str:
    """Pas de BGT-query aan voor de tool, zonder het bronbestand te wijzigen:
    (1) de named graph variabel maken — vervang de URI uit `FROM NAMED <…>`
        (en dus ook de GRAPH <…>-blokken met dezelfde URI) door `nlcs_graph`;
    (2) de kolom NLCSHoofdgroep toevoegen (graph-lookup) als die nog niet in de
        query zit: extra SELECT-variabele + een OPTIONAL-blok dat de hoofdgroep
        (de directe subklasse van 'NLCS-object') als prefLabel ophaalt."""
    import re
    q = query
    if nlcs_graph:
        m = re.search(r"FROM\s+NAMED\s+<([^>]+)>", q, re.IGNORECASE)
        if m and m.group(1) != nlcs_graph:
            q = q.replace(m.group(1), nlcs_graph)
    if "?NLCSHoofdgroep" not in q:
        q2 = q.replace("?NLCSObjectURI ?NLCSObjectID",
                       "?NLCSObjectURI ?NLCSObjectID ?NLCSHoofdgroep", 1)
        anchor = "?NLCSObjectURI skos:prefLabel ?layerInfo ."
        if anchor in q2:
            add = (anchor + "\n"
                   "            OPTIONAL {\n"
                   "                ?NLCSObjectURI rdfs:subClassOf+ ?hoofdgroepURI .\n"
                   "                ?hoofdgroepURI rdfs:subClassOf ?NLCSObjectTopConcept .\n"
                   "                ?hoofdgroepURI skos:prefLabel ?NLCSHoofdgroep .\n"
                   "            }")
            q = q2.replace(anchor, add, 1)
    return q


def run_bgt_mapping_export(endpoint, token, password, nlcs_graph, version,
                           query_path, out_dir, log=print):
    """Draai de BGT→NLCS mapping-query tegen `endpoint` en schrijf
    NLCS-<versie>-BGT.csv in `out_dir` (kolomvolgorde = BGT_COLUMNS, met de
    afgeleide kolommen NLCSHoofdgroep [uit de query] en NLCSSbib [uit symbolInfo])."""
    endpoint = normalize_endpoint(endpoint)
    version = (version or "5-0").strip() or "5-0"
    vdash = version.replace(".", "-")
    nlcs_graph = (nlcs_graph or DEFAULT_NLCS_GRAPH).strip()
    if not query_path or not os.path.isfile(query_path):
        raise RuntimeError(f"BGT-query niet gevonden: {query_path}")

    query = _bgt_prepare_query(_read_text(query_path), nlcs_graph)
    log(f"BGT-endpoint : {endpoint}")
    log(f"NLCS graph   : {nlcs_graph}")
    log(f"Query        : {query_path}")
    log(f"Uitvoermap   : {out_dir}")

    client = LacesClient(endpoint, token, password)
    try:
        r = client.run_csv("SELECT ?s WHERE { ?s ?p ?o } LIMIT 1", timeout=30)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Kan het endpoint niet bereiken ({endpoint}): {e}")
    if r.status_code != 200:
        snip = (r.text or "")[:160].replace("\n", " ")
        raise RuntimeError(
            f"Endpoint gaf HTTP {r.status_code}. Controleer endpoint/login/"
            f"rechten. Antwoord: {snip}")
    log("Endpoint OK (test-query -> 200).")

    resp = client.run_csv(query, timeout=300)
    if resp.status_code != 200:
        snip = (resp.text or "")[:200].replace("\n", " ")
        raise RuntimeError(f"BGT-query gaf HTTP {resp.status_code}: {snip}")

    rows = list(csv.DictReader(io.StringIO(resp.text)))
    out_path = os.path.join(out_dir, f"NLCS-{vdash}-BGT.csv")
    os.makedirs(out_dir, exist_ok=True)
    n_sym = 0
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(BGT_COLUMNS)
        for row in rows:
            sym = (row.get("symbolInfo") or "").strip()
            row["NLCSSbib"] = sym.split("-")[0] if sym else ""
            if sym:
                n_sym += 1
            w.writerow([row.get(c, "") for c in BGT_COLUMNS])
    log(f"Geschreven: NLCS-{vdash}-BGT.csv  ({len(rows)} rijen, "
        f"{n_sym} met symbool)")
    return out_path


# -- GWSW-mapping-export ---------------------------------------------------
# De GWSW→NLCS mapping-query (code/gwsw-nlcs/GWSW-NLCS mapping tabel.rq) draait
# tegen de classificatie-publicatie (bijv. nlcs-classificatie-ri---kern op test).
# Anders dan BGT gaat de NLCS-graph hier via de URL-parameter
# `default-graph-uri` (nodig voor de NLCS-prefLabels in de OPTIONAL-blokken),
# NIET via FROM NAMED in de query. De query blijft ongewijzigd.
GWSW_QUERY_REL = os.path.join("code", "gwsw-nlcs",
                              "GWSW-NLCS mapping tabel met NLCS-ID.rq")


GWSW_RI_QUERY_REL = os.path.join(
    "code", "gwsw-nlcs",
    "GWSW-NLCS mapping via classificatie-RI (overerving).rq")


def default_gwsw_query(repo_root: str = "") -> str:
    """Pad naar de GWSW-mapping-query in de repo (leeg als niet gevonden)."""
    root = repo_root or default_repo_root()
    p = os.path.join(root, GWSW_QUERY_REL)
    return p if os.path.isfile(p) else ""


def default_gwsw_ri_query(repo_root: str = "") -> str:
    """Pad naar de GWSW-mapping-query via de classificatie-RI (met overerving)."""
    root = repo_root or default_repo_root()
    p = os.path.join(root, GWSW_RI_QUERY_REL)
    return p if os.path.isfile(p) else ""


def run_gwsw_mapping_export(endpoint, token, password, nlcs_graph, version,
                            query_path, out_dir, out_name="GWSW", log=print):
    """Draai de GWSW→NLCS mapping-query tegen `endpoint` (met de NLCS-graph als
    `default-graph-uri`) en schrijf NLCS-<versie>-<out_name>.csv in `out_dir`. De
    query-output wordt ongewijzigd weggeschreven (kolommen zoals de query ze
    levert)."""
    endpoint = normalize_endpoint(endpoint)
    version = (version or "5-0").strip() or "5-0"
    vdash = version.replace(".", "-")
    nlcs_graph = (nlcs_graph or DEFAULT_NLCS_GRAPH).strip()
    if not query_path or not os.path.isfile(query_path):
        raise RuntimeError(f"GWSW-query niet gevonden: {query_path}")

    query = _read_text(query_path)
    log(f"GWSW-endpoint : {endpoint}")
    log(f"NLCS graph    : {nlcs_graph}  (via default-graph-uri)")
    log(f"Query         : {query_path}")
    log(f"Uitvoermap    : {out_dir}")

    client = LacesClient(endpoint, token, password)
    try:
        r = client.run_csv("SELECT ?s WHERE { ?s ?p ?o } LIMIT 1", timeout=30)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Kan het endpoint niet bereiken ({endpoint}): {e}")
    if r.status_code != 200:
        snip = (r.text or "")[:160].replace("\n", " ")
        raise RuntimeError(
            f"Endpoint gaf HTTP {r.status_code}. Controleer endpoint/login/"
            f"rechten. Antwoord: {snip}")
    log("Endpoint OK (test-query -> 200).")

    params = {"default-graph-uri": nlcs_graph} if nlcs_graph else None
    resp = client.run_csv(query, timeout=300, params=params)
    if resp.status_code != 200:
        snip = (resp.text or "")[:200].replace("\n", " ")
        raise RuntimeError(f"GWSW-query gaf HTTP {resp.status_code}: {snip}")

    out_path = os.path.join(out_dir, f"NLCS-{vdash}-{out_name}.csv")
    n = _write_csv(resp.text, out_path)
    log(f"Geschreven: NLCS-{vdash}-{out_name}.csv  ({n} rijen)")
    return out_path


# NLCS-symbolen ophalen (naam/URI/ID) uit de NLCS-graph, voor de symbool-keuze.
_GWSW_SYMBOOL_QUERY = """PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
SELECT DISTINCT ?symURI ?symName ?symID WHERE {
  ?symURI rdfs:subClassOf+/skos:prefLabel "Symbool" .
  ?symURI skos:prefLabel ?symName .
  OPTIONAL { ?symURI ?idp ?symID . ?idp a owl:AnnotationProperty ; skos:prefLabel "ID" . }
}"""

# Kolommen die één mapping-rij identificeren (zonder de symbool-/sobject-kolommen).
GWSW_RI_KEYCOLS = [
    "GwswStelselType", "GwswStelselTypeName", "GwswType", "GwswTypeName",
    "nameStelselType", "nameType",
    "nameNLCSLaagnaam", "NLCSLaagnaam", "NLCSLaagnaamID",
]
# Kolommen van de GWSW-RI-outputtabel (symbool-kolommen door de tool ingevuld).
GWSW_RI_COLUMNS = GWSW_RI_KEYCOLS + [
    "nameNLCSSymbool", "NLCSSymbool", "NLCSSymboolID",
]


def _symbol_fase(name: str) -> str:
    """Fase uit de symboolnaam-prefix: 'B-…'->B, 'V-…'->V, enz.; anders ''."""
    seg = (name or "").split("-", 1)[0]
    return seg if seg in ("B", "V", "N", "T") else ""


def _pick_symbol(sobjects, symbols: list):
    """Kies ÉÉN symbool voor de zoekterm(en) (sobject) van een object: symbolen
    waarvan de naam een sobject bevat; eerst zonder fase, anders fase B; bij
    meerdere de kortste naam. Alleen symbolen MET een ID tellen mee (een ID
    betekent dat er een bestand/tekenbaar symbool is; het zoekterm-concept zelf
    heeft geen ID). `sobjects` is één string of een verzameling. Geeft
    (naam, uri, id) of ("","","")."""
    if isinstance(sobjects, str):
        sobjects = [sobjects]
    terms = [str(s).strip() for s in sobjects if str(s).strip()]
    if not terms:
        return "", "", ""
    cand = [s for s in symbols
            if str(s.get("id") or "").strip()
            and any(t in s["name"] for t in terms)]
    fase_geen = [s for s in cand if _symbol_fase(s["name"]) == ""]
    fase_b = [s for s in cand if _symbol_fase(s["name"]) == "B"]
    pool = fase_geen or fase_b   # zonder fase eerst, anders fase B
    if not pool:
        return "", "", ""
    pool.sort(key=lambda s: (len(s["name"]), s["name"]))
    best = pool[0]
    return best["name"], best["uri"], best["id"]


def run_gwsw_ri_mapping_export(endpoint, token, password, nlcs_graph, version,
                               query_path, out_dir, out_name="GWSW-RI",
                               log=print):
    """GWSW→NLCS mapping via de classificatie-RI-publicatie, MET overerving en
    met ÉÉN gekozen symbool per rij. De mapping-query levert per rij de zoekterm
    `sobject`; de tool haalt alle NLCS-symbolen op en kiest er één per sobject
    (fase B > zonder fase > kortste naam). Schrijft NLCS-<versie>-<out_name>.csv."""
    endpoint = normalize_endpoint(endpoint)
    version = (version or "5-0").strip() or "5-0"
    vdash = version.replace(".", "-")
    nlcs_graph = (nlcs_graph or DEFAULT_NLCS_GRAPH).strip()
    if not query_path or not os.path.isfile(query_path):
        raise RuntimeError(f"GWSW-query niet gevonden: {query_path}")
    query = _read_text(query_path)
    params = {"default-graph-uri": nlcs_graph} if nlcs_graph else None
    log(f"Endpoint    : {endpoint}")
    log(f"NLCS graph  : {nlcs_graph}  (via default-graph-uri)")
    log(f"Query       : {query_path}")
    log(f"Uitvoermap  : {out_dir}")

    client = LacesClient(endpoint, token, password)
    try:
        r = client.run_csv("SELECT ?s WHERE { ?s ?p ?o } LIMIT 1", timeout=30)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Kan het endpoint niet bereiken ({endpoint}): {e}")
    if r.status_code != 200:
        snip = (r.text or "")[:160].replace("\n", " ")
        raise RuntimeError(f"Endpoint gaf HTTP {r.status_code}. Antwoord: {snip}")
    log("Endpoint OK (test-query -> 200).")

    # 1) mapping-query (met ?sobject per rij)
    resp = client.run_csv(query, timeout=300, params=params)
    if resp.status_code != 200:
        snip = (resp.text or "")[:200].replace("\n", " ")
        raise RuntimeError(f"Mapping-query gaf HTTP {resp.status_code}: {snip}")
    rows = list(csv.DictReader(io.StringIO(resp.text)))

    # 2) alle NLCS-symbolen ophalen
    sresp = client.run_csv(_GWSW_SYMBOOL_QUERY, timeout=120, params=params)
    if sresp.status_code != 200:
        raise RuntimeError(f"Symbool-query gaf HTTP {sresp.status_code}")
    symbols = [{"uri": r2.get("symURI", ""), "name": r2.get("symName", ""),
                "id": r2.get("symID", "")}
               for r2 in csv.DictReader(io.StringIO(sresp.text))
               if r2.get("symName")]
    log(f"Symbolen opgehaald: {len(symbols)}")

    # 3) rijen groeperen tot één rij per mapping-combinatie (de ?sobject-OPTIONAL
    #    kan een object meerdere zoektermen geven -> meerdere ruwe rijen); per
    #    groep de zoektermen verzamelen en ÉÉN symbool kiezen.
    from collections import OrderedDict
    groups = OrderedDict()
    for row in rows:
        key = tuple(row.get(c, "") for c in GWSW_RI_KEYCOLS)
        g = groups.setdefault(key, set())
        so = (row.get("sobject") or "").strip()
        if so:
            g.add(so)

    n_sym = 0
    out_rows = []
    cache = {}
    for key, sobjects in groups.items():
        ck = frozenset(sobjects)
        if ck not in cache:
            cache[ck] = _pick_symbol(sobjects, symbols)
        nm, uri, sid = cache[ck]
        if nm:
            n_sym += 1
        out_rows.append(list(key) + [nm, uri, sid])

    out_path = os.path.join(out_dir, f"NLCS-{vdash}-{out_name}.csv")
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(GWSW_RI_COLUMNS)
        w.writerows(out_rows)
    log(f"Geschreven: NLCS-{vdash}-{out_name}.csv  ({len(out_rows)} rijen, "
        f"{n_sym} met symbool)")
    return out_path


# -- Classificatie-export (voeding voor de classificatie-pagina) -----------
# Per fysiek object één regel: naam, URI, ouder (subtype-of, voor de boom),
# GWSW-type(s), NLCS-objectlaag + ID, en één gekozen NLCS-symbool. Dit is de
# volledige boom (ook objecten zonder NLCS-relatie, als tussenknoop).
CLASSIFICATIE_QUERY_REL = os.path.join("code", "gwsw-nlcs",
                                       "classificatie-export.rq")
CLASSIFICATIE_COLUMNS = [
    "naam", "URI", "subTypeOf", "GWSW",
    "NLCSLaagnaam", "NLCSLaagnaamID", "NLCSSymbool", "NLCSSymboolID",
    "aspects", "parts", "activiteiten", "materiaal",
    "IMBOR", "IMBORURI",
]

# IMBOR-koppeling via de token-vrije CombiGraph (bevat het GWSW 1.6-model + de
# IMBOR-defs). Twee bronnen, gecombineerd per object:
#   1) directe IMBOR-def-link op het object (exactMatch/isDescribedBy -> imbor/def)
#   2) brug via de GWSW-URI: een imbor/def is rdfs:subClassOf de GWSW-klasse, of
#      andersom (beide richtingen) -> levert de IMBOR-(ouder)term.
IMBOR_COMBIGRAPH_EP = ("https://hub.laces.tech/crow/imbor/2025/p/"
                       "volledig-combigraph/sparql")


def _sparql_csv_noauth(endpoint, query, timeout=120):
    """POST een SPARQL-query zonder authenticatie en geef de CSV-tekst terug."""
    resp = requests.post(
        endpoint, data=query.encode("utf-8"),
        headers={"Content-type": "application/sparql-query",
                 "Accept": "text/csv"}, timeout=timeout)
    if resp.status_code != 200:
        snip = (resp.text or "")[:160].replace("\n", " ")
        raise RuntimeError(f"CombiGraph gaf HTTP {resp.status_code}: {snip}")
    return resp.text


def _imbor_maps(gwsw_uris, direct_uris, log=print):
    """Vraag de CombiGraph: (gwsw_uri -> [(imbor_uri, naam)], imbor_uri -> naam).
    gwsw2imbor via rdfs:subClassOf (beide richtingen); direct_label voor de
    IMBOR-def-URI's die al op de objecten staan."""
    P = ("PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#> "
         "PREFIX skos: <http://www.w3.org/2004/02/skos/core#> ")
    gwsw2imbor = {}
    gwsw_uris = sorted(u for u in gwsw_uris if u)
    if gwsw_uris:
        vals = " ".join("<%s>" % u for u in gwsw_uris)
        q = (P + "SELECT ?g ?i ?l WHERE { VALUES ?g { " + vals + " } "
             "{ ?g rdfs:subClassOf ?i } UNION { ?i rdfs:subClassOf ?g } "
             "FILTER(CONTAINS(STR(?i),\"/imbor/def/\")) "
             "OPTIONAL { ?i skos:prefLabel ?l } }")
        for r in csv.DictReader(io.StringIO(_sparql_csv_noauth(
                IMBOR_COMBIGRAPH_EP, q))):
            g = (r.get("g") or "").strip()
            i = (r.get("i") or "").strip()
            lab = (r.get("l") or "").strip() or i.rsplit("/", 1)[-1]
            if g and i:
                gwsw2imbor.setdefault(g, {})[i] = lab
    direct_label = {}
    direct_uris = sorted(u for u in direct_uris if u)
    if direct_uris:
        vals = " ".join("<%s>" % u for u in direct_uris)
        q = (P + "SELECT ?i ?l WHERE { VALUES ?i { " + vals + " } "
             "OPTIONAL { ?i skos:prefLabel ?l } }")
        for r in csv.DictReader(io.StringIO(_sparql_csv_noauth(
                IMBOR_COMBIGRAPH_EP, q))):
            i = (r.get("i") or "").strip()
            if i:
                direct_label[i] = (r.get("l") or "").strip() or i.rsplit("/", 1)[-1]
    log(f"IMBOR: {sum(len(v) for v in gwsw2imbor.values())} GWSW->IMBOR-links "
        f"voor {len(gwsw2imbor)} GWSW-URI's, {len(direct_label)} directe def-links")
    return gwsw2imbor, direct_label

# Per-object relatie-query's (SHACL-shapes in de classificatie-publicatie).
# Elk geeft (?obj = objectnaam, ?name = relatienaam); de export aggregeert per
# objectnaam. Aspect geeft ook een optionele ?val.
_CL_REL_PREFIX = """PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX sh: <http://www.w3.org/ns/shacl#>
PREFIX nen2660: <https://w3id.org/nen2660/def#>
"""
_CL_MATTER_Q = _CL_REL_PREFIX + """
SELECT DISTINCT ?obj ?name WHERE {
  ?o a owl:Class ; rdfs:subClassOf+ nen2660:RealObject .
  FILTER(CONTAINS(STR(?o),"nlcs-class/")) ?o skos:prefLabel ?obj .
  ?s a sh:NodeShape ; sh:targetClass ?o ; sh:property ?b .
  ?b sh:path nen2660:consistsOf ; sh:qualifiedValueShape/sh:class ?m .
  ?m skos:prefLabel ?name . }"""
_CL_PART_Q = _CL_REL_PREFIX + """
SELECT DISTINCT ?obj ?name WHERE {
  ?o a owl:Class ; rdfs:subClassOf+ nen2660:RealObject .
  FILTER(CONTAINS(STR(?o),"nlcs-class/")) ?o skos:prefLabel ?obj .
  ?s a sh:NodeShape ; sh:targetClass ?o ; sh:property ?b .
  ?b sh:path nen2660:hasPart ; sh:qualifiedValueShape/sh:class ?p .
  ?p skos:prefLabel ?name . }"""
_CL_ACT_Q = _CL_REL_PREFIX + """
SELECT DISTINCT ?obj ?name WHERE {
  ?sh a sh:NodeShape ; sh:targetClass ?a ; sh:property ?b .
  ?b sh:path nen2660:transforms ; sh:qualifiedValueShape/sh:class ?o .
  ?o a owl:Class ; rdfs:subClassOf+ nen2660:RealObject .
  FILTER(CONTAINS(STR(?o),"nlcs-class/")) ?o skos:prefLabel ?obj .
  ?a skos:prefLabel ?name . }"""
_CL_ASPECT_Q = _CL_REL_PREFIX + """
SELECT DISTINCT ?obj ?name ?val WHERE {
  ?o a owl:Class ; rdfs:subClassOf+ nen2660:RealObject .
  FILTER(CONTAINS(STR(?o),"nlcs-class/")) ?o skos:prefLabel ?obj .
  ?s a sh:NodeShape ; sh:targetClass ?o ; sh:property ?b . ?b sh:path ?prop .
  FILTER(?prop NOT IN (nen2660:consistsOf, nen2660:hasPart, nen2660:transforms))
  ?prop skos:prefLabel ?name .
  OPTIONAL { ?b sh:hasValue ?v . OPTIONAL { ?v skos:prefLabel ?vl }
             BIND(COALESCE(?vl, STR(?v)) AS ?val) } }"""


def _rel_map(client, query, params, value=False):
    """Draai een per-object relatie-query en geef {objectnaam: sorted[list]}."""
    import io as _io
    resp = client.run_csv(query, timeout=180, params=params)
    if resp.status_code != 200:
        raise RuntimeError(f"Relatie-query gaf HTTP {resp.status_code}")
    out = {}
    for r in csv.DictReader(_io.StringIO(resp.text)):
        o = (r.get("obj") or "").strip()
        nm = (r.get("name") or "").strip()
        if not o or not nm:
            continue
        if value:
            v = (r.get("val") or "").strip()
            if v:
                nm = f"{nm} = {v}"
        out.setdefault(o, set()).add(nm)
    return {k: sorted(v) for k, v in out.items()}


def default_classificatie_query(repo_root: str = "") -> str:
    """Pad naar de classificatie-export-query in de repo (leeg als niet gevonden)."""
    root = repo_root or default_repo_root()
    p = os.path.join(root, CLASSIFICATIE_QUERY_REL)
    return p if os.path.isfile(p) else ""


def run_classificatie_export(endpoint, token, password, nlcs_graph, version,
                             query_path, out_dir, out_name="classificatie",
                             log=print):
    """Classificatie-boom + relaties: per fysiek object één regel met ouder
    (subtype-of), GWSW-type(s), NLCS-objectlaag + ID en één gekozen symbool
    (zonder fase > fase B > kortste naam, alleen symbolen met ID). Schrijft
    NLCS-<versie>-<out_name>.csv in `out_dir`."""
    endpoint = normalize_endpoint(endpoint)
    version = (version or "5-0").strip() or "5-0"
    vdash = version.replace(".", "-")
    nlcs_graph = (nlcs_graph or DEFAULT_NLCS_GRAPH).strip()
    if not query_path or not os.path.isfile(query_path):
        raise RuntimeError(f"Classificatie-query niet gevonden: {query_path}")
    query = _read_text(query_path)
    params = {"default-graph-uri": nlcs_graph} if nlcs_graph else None
    log(f"Endpoint    : {endpoint}")
    log(f"NLCS graph  : {nlcs_graph}  (via default-graph-uri)")
    log(f"Query       : {query_path}")
    log(f"Uitvoermap  : {out_dir}")

    client = LacesClient(endpoint, token, password)
    try:
        r = client.run_csv("SELECT ?s WHERE { ?s ?p ?o } LIMIT 1", timeout=30)
    except Exception as e:  # noqa: BLE001
        raise RuntimeError(f"Kan het endpoint niet bereiken ({endpoint}): {e}")
    if r.status_code != 200:
        snip = (r.text or "")[:160].replace("\n", " ")
        raise RuntimeError(f"Endpoint gaf HTTP {r.status_code}. Antwoord: {snip}")
    log("Endpoint OK (test-query -> 200).")

    resp = client.run_csv(query, timeout=300, params=params)
    if resp.status_code != 200:
        snip = (resp.text or "")[:200].replace("\n", " ")
        raise RuntimeError(f"Classificatie-query gaf HTTP {resp.status_code}: {snip}")
    rows = list(csv.DictReader(io.StringIO(resp.text)))

    sresp = client.run_csv(_GWSW_SYMBOOL_QUERY, timeout=120, params=params)
    if sresp.status_code != 200:
        raise RuntimeError(f"Symbool-query gaf HTTP {sresp.status_code}")
    symbols = [{"uri": r2.get("symURI", ""), "name": r2.get("symName", ""),
                "id": r2.get("symID", "")}
               for r2 in csv.DictReader(io.StringIO(sresp.text))
               if r2.get("symName")]
    log(f"Symbolen opgehaald: {len(symbols)}")

    # Per-object relaties (op objectnaam): aspects / parts / activiteiten /
    # materiaal — los opgehaald om een cross-product in de hoofdquery te
    # voorkomen.
    rel_mat = _rel_map(client, _CL_MATTER_Q, params)
    rel_part = _rel_map(client, _CL_PART_Q, params)
    rel_act = _rel_map(client, _CL_ACT_Q, params)
    rel_asp = _rel_map(client, _CL_ASPECT_Q, params, value=True)
    log(f"Relaties: materiaal {len(rel_mat)}, parts {len(rel_part)}, "
        f"activiteiten {len(rel_act)}, aspects {len(rel_asp)} objecten")

    # Ontdubbelen per object (uri): naam, ouder, GWSW-set, NLCS-object+ID,
    # zoekterm-set. GWSW/sobject kunnen meerdere waarden hebben.
    from collections import OrderedDict
    objs = OrderedDict()
    for row in rows:
        uri = (row.get("uri") or "").strip()
        if not uri:
            continue
        o = objs.get(uri)
        if o is None:
            o = objs[uri] = {"naam": (row.get("name") or "").strip(),
                             "parent": "", "gwsw": set(), "gwswuris": set(),
                             "nlcs": "", "nlcsid": "", "sobjects": set(),
                             "imbordirect": set()}
        if not o["parent"] and (row.get("subTypeOfName") or "").strip():
            o["parent"] = row["subTypeOfName"].strip()
        if (row.get("gwsw") or "").strip():
            o["gwsw"].add(row["gwsw"].strip())
        if (row.get("gwswUri") or "").strip():
            o["gwswuris"].add(row["gwswUri"].strip())
        if (row.get("imborDirect") or "").strip():
            o["imbordirect"].add(row["imborDirect"].strip())
        if not o["nlcs"] and (row.get("nameNLCSLaagnaam") or "").strip():
            o["nlcs"] = row["nameNLCSLaagnaam"].strip()
            o["nlcsid"] = (row.get("NLCSLaagnaamID") or "").strip()
        if (row.get("sobject") or "").strip():
            o["sobjects"].add(row["sobject"].strip())

    # IMBOR-koppeling via de CombiGraph (token-vrij): GWSW-URI-brug + directe
    # def-links, in één aanroep per bron voor alle objecten.
    all_gwsw_uris = set().union(*(o["gwswuris"] for o in objs.values())) \
        if objs else set()
    all_direct = set().union(*(o["imbordirect"] for o in objs.values())) \
        if objs else set()
    try:
        gwsw2imbor, direct_label = _imbor_maps(all_gwsw_uris, all_direct, log)
    except Exception as e:  # noqa: BLE001
        log(f"IMBOR-koppeling overgeslagen (CombiGraph niet bereikbaar): {e}")
        gwsw2imbor, direct_label = {}, {}

    n_sym = 0
    n_imbor = 0
    out_rows = []
    for uri, o in objs.items():
        nm, _uri, sid = _pick_symbol(o["sobjects"], symbols)
        if nm:
            n_sym += 1
        naam = o["naam"]
        # IMBOR: directe def-links eerst (specifiek), daarna de GWSW-brug
        # (vaak generieke oudertermen); ontdubbeld per IMBOR-URI, volgorde vast.
        imbor_pairs = []
        seen = set()
        for iuri in sorted(o["imbordirect"]):
            if iuri not in seen:
                seen.add(iuri)
                imbor_pairs.append((direct_label.get(iuri, iuri.rsplit("/", 1)[-1]),
                                    iuri))
        for guri in sorted(o["gwswuris"]):
            for iuri, lab in sorted(gwsw2imbor.get(guri, {}).items(),
                                    key=lambda kv: kv[1].casefold()):
                if iuri not in seen:
                    seen.add(iuri)
                    imbor_pairs.append((lab, iuri))
        if imbor_pairs:
            n_imbor += 1
        out_rows.append([naam, uri, o["parent"],
                         "; ".join(sorted(o["gwsw"])),
                         o["nlcs"], o["nlcsid"], nm, sid,
                         "; ".join(rel_asp.get(naam, [])),
                         "; ".join(rel_part.get(naam, [])),
                         "; ".join(rel_act.get(naam, [])),
                         "; ".join(rel_mat.get(naam, [])),
                         "; ".join(p[0] for p in imbor_pairs),
                         "; ".join(p[1] for p in imbor_pairs)])
    out_rows.sort(key=lambda r2: r2[0].casefold())

    out_path = os.path.join(out_dir, f"NLCS-{vdash}-{out_name}.csv")
    os.makedirs(out_dir, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(CLASSIFICATIE_COLUMNS)
        w.writerows(out_rows)
    log(f"Geschreven: NLCS-{vdash}-{out_name}.csv  ({len(out_rows)} objecten, "
        f"{n_sym} met symbool, {n_imbor} met IMBOR)")
    return out_path
