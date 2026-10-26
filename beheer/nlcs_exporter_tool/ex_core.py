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

    def run_csv(self, query: str, timeout: int = 180):
        return requests.post(
            self.endpoint,
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
