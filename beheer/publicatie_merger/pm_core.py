"""
pm_core.py - laadt de logica uit code/nlcs/split/merger/publication_merger.py.

Het originele publication_merger.py wordt NIET aangepast: we laden het als module
(dev: via het pad in de repo; in de .exe: de meegebundelde kopie) en gebruiken de
functies en de PUBLICATIONS-lijst eruit. Zo is er één bron van waarheid.
"""

import importlib.util
import logging
import os
import sys
from collections import Counter, defaultdict
from itertools import combinations

_log = logging.getLogger("pm_core")

# publication_merger.py wordt dynamisch (via pad) geladen, dus PyInstaller ziet
# zijn imports niet. Door requests en rdflib hier statisch te importeren worden ze
# (met hun volledige dependency-tree: urllib3/certifi/idna/charset_normalizer resp.
# pyparsing) wel mee in de .exe gebundeld. Niet verwijderen.
import requests  # noqa: F401
import rdflib  # noqa: F401

_PREFLABEL = rdflib.URIRef("http://www.w3.org/2004/02/skos/core#prefLabel")


def _merger_path() -> str:
    """Pad naar publication_merger.py — in de exe de meegebundelde kopie
    (sys._MEIPASS), anders relatief t.o.v. de repo-root."""
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "publication_merger.py")
    here = os.path.dirname(os.path.abspath(__file__))
    # beheer/publicatie_merger -> repo-root (NLCSdev)
    root = os.path.abspath(os.path.join(here, "..", ".."))
    return os.path.join(root, "code", "nlcs", "split", "merger",
                        "publication_merger.py")


def _load():
    path = _merger_path()
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"publication_merger.py niet gevonden op: {path}")
    spec = importlib.util.spec_from_file_location("publication_merger", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["publication_merger"] = mod
    spec.loader.exec_module(mod)   # draait alleen top-level config (merge is guarded)
    return mod


_pm = _load()

PUBLICATIONS = list(_pm.PUBLICATIONS)
DEFAULT_OUTPUT = _pm.OUTPUT_PATH
fetch_publication_graph = _pm.fetch_publication_graph
save_graph = _pm.save_graph


def _check_credentials(token_id, password):
    """HTTP Basic-auth codeert token:wachtwoord als latin-1. Geef een duidelijke
    melding als er een niet-codeerbaar teken in zit (vaak door plakken)."""
    for label, val in (("Token-ID", token_id), ("wachtwoord/secret", password)):
        try:
            str(val).encode("latin-1")
        except UnicodeEncodeError as e:
            bad = str(val)[e.start]
            raise RuntimeError(
                f"Het veld '{label}' bevat een teken dat niet in een HTTP-login "
                f"past (positie {e.start}: {bad!r}). Dit komt meestal door plakken "
                f"(een slim aanhalingsteken, en-dash of niet-afbreekbare spatie). "
                f"Typ of plak het token opnieuw zonder speciale tekens.")


def _pub_label(url):
    """Korte publicatienaam uit een URL (laatste padsegment, zonder /versions/…)."""
    path = urlsplit(url).path.rstrip("/").split("/versions/", 1)[0].rstrip("/")
    return path.rsplit("/", 1)[-1] or url


def _report_overlap(name_pubs, name_uris):
    """Log de ECHTE dubbelingen: concept-namen die in de merge méér dan één
    distinct URI hebben (die vallen dus niet samen). Namen die meerdere publicaties
    met DEZELFDE URI delen, mergen netjes tot één en worden niet als probleem
    geteld. Het pair-/per-publicatie-overzicht wijst de overlappende selectie aan."""
    # harmless: in >1 publicatie maar met één gedeelde URI -> dedupe lost het op
    harmless = sum(1 for nm, p in name_pubs.items()
                   if len(p) > 1 and len(name_uris[nm]) == 1)
    # cross: >1 distinct URI én uit >1 publicatie -> overlappende selectie
    cross = {nm: sorted(p) for nm, p in name_pubs.items()
             if len(name_uris[nm]) > 1 and len(p) > 1}
    # within: >1 distinct URI maar uit één publicatie -> dubbel in de bron zelf
    within = sorted(nm for nm, p in name_pubs.items()
                    if len(name_uris[nm]) > 1 and len(p) == 1)

    _log.info("--- Overlap-rapport ---")
    _log.info("%d naam(en) worden met dezelfde URI door meerdere publicaties "
              "gedeeld en vallen netjes samen (geen probleem).", harmless)
    if within:
        _log.info("%d naam(en) hebben meerdere URI's binnen één publicatie: %s%s",
                  len(within), ", ".join(within[:15]),
                  " …" if len(within) > 15 else "")
    if not cross:
        _log.info("Geen namen met verschillende URI's uit meerdere publicaties — "
                  "geen overlappende selectie gevonden.")
        _log.info("--- einde overlap-rapport ---")
        return
    _log.info("%d naam(en) komen met VERSCHILLENDE URI's uit meerdere publicaties "
              "(echte dubbeling door overlappende selectie):", len(cross))

    pair = Counter()
    for pubs in cross.values():
        for a, b in combinations(pubs, 2):
            pair[(a, b)] += 1
    _log.info("Publicatieparen met de meeste echt-dubbele namen:")
    for (a, b), n in pair.most_common(15):
        _log.info("  %s  +  %s : %d naam(en)", a, b, n)

    per_pub = Counter()
    for pubs in cross.values():
        for p in pubs:
            per_pub[p] += 1
    _log.info("Per publicatie, aantal echt-dubbele namen (hoog = kandidaat om weg "
              "te laten):")
    for p, n in per_pub.most_common():
        _log.info("  %s : %d", p, n)

    top = pair.most_common(1)
    if top:
        (a, b), _ = top[0]
        ex = sorted(nm for nm, pubs in cross.items() if a in pubs and b in pubs)
        _log.info("Voorbeelden gedeeld door %s + %s: %s%s", a, b,
                  ", ".join(ex[:25]), " …" if len(ex) > 25 else "")
    _log.info("--- einde overlap-rapport ---")


def merge_publications(publication_urls, token_id, password):
    """Fouttolerante merge: haalt elke publicatie apart op, slaat mislukkingen over
    (met logregel) en voegt de rest samen (zelfde dedup/namespace-logica als
    publication_merger). Zo breekt één ontbrekende publicatie het testen niet af.
    Houdt per publicatie de concept-namen bij en logt daarna een overlap-rapport."""
    _check_credentials(token_id, password)
    merged = rdflib.Graph()
    ok, failed = 0, []
    name_pubs = defaultdict(set)
    name_uris = defaultdict(set)
    for url in publication_urls:
        try:
            graph = _pm.fetch_publication_graph(url, token_id, password)
        except Exception as e:  # noqa: BLE001
            _log.warning("Publicatie overgeslagen: %s (%s)", url, e)
            failed.append(url)
            continue
        for prefix, namespace in graph.namespace_manager.namespaces():
            existing = dict(merged.namespace_manager.namespaces()).get(prefix)
            if existing is None:
                merged.bind(prefix, namespace, override=False)
        merged += graph
        ok += 1
        label = _pub_label(url)
        for s, _p, o in graph.triples((None, _PREFLABEL, None)):
            name_pubs[str(o)].add(label)
            name_uris[str(o)].add(str(s))
    _log.info("Samengevoegd: %d publicatie(s) OK, %d overgeslagen, %d triples.",
              ok, len(failed), len(merged))
    if failed:
        _log.warning("Niet opgehaald (%d): %s", len(failed), ", ".join(failed))
    _report_overlap(name_pubs, name_uris)
    return merged


# ---------------------------------------------------------------------------
# Publicatienamen ophalen uit de Laces-hub (REST-API v4, met v3 als fallback)
# ---------------------------------------------------------------------------
import re  # noqa: E402
from urllib.parse import urlsplit  # noqa: E402


def _api_host(base_url: str) -> str:
    s = urlsplit(base_url)
    return f"{s.scheme}://{s.netloc}"


class _AuthError(Exception):
    """401/403 — login geweigerd voor dit endpoint."""


def _get_json(url, auth, timeout=30):
    """GET + JSON. None bij 404 (API-versie niet aanwezig); _AuthError bij 401/403."""
    r = requests.get(url, auth=auth, headers={"Accept": "application/json"},
                     timeout=timeout)
    if r.status_code == 404:
        return None
    if r.status_code in (401, 403):
        raise _AuthError(f"{r.status_code} bij {url}")
    r.raise_for_status()
    return r.json()


def _as_list(data):
    """Haal de lijst met items uit een v3- (lijst) of v4-respons ({contents:[...]})."""
    if data is None:
        return []
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("contents", "publications", "repositories", "items"):
            if isinstance(data.get(key), list):
                return data[key]
    return []


def _fetch_list(url, auth):
    """Haal een lijst-respons op en volg paginering: als 'total' groter is dan het
    aantal 'contents', probeer alles in één keer op te halen via een grote
    size/limit-parameter. Retour (items, total). (items None => 404.)"""
    data = _get_json(url, auth)
    if data is None:
        return None, None
    items = _as_list(data)
    total = data.get("total") if isinstance(data, dict) else None
    if isinstance(total, int) and total > len(items):
        sep = "&" if "?" in url else "?"
        for param in ("size", "limit", "pageSize", "count", "max", "perPage"):
            try:
                d2 = _get_json(f"{url}{sep}{param}={total}", auth)
            except Exception:            # 400 e.d. op onbekende param -> volgende
                d2 = None
            it2 = _as_list(d2)
            if len(it2) > len(items):
                items = it2
            if len(items) >= total:
                break
    return items, total


def _list_all_publications(host, auth):
    """Alle publicaties (dicts met o.a. 'uri'/'name') over de toegankelijke
    repositories. Probeert API v4 → v3 → v2; slaat een versie die 401/403 geeft
    over (credentials kunnen op een andere versie wél geldig zijn)."""
    versions = (
        ("v4", f"{host}/api/v4/repositories",
         lambda rid: f"{host}/api/v4/publications?repositoryId={rid}"),
        ("v3", f"{host}/api/v3/repositories",
         lambda rid: f"{host}/api/v3/repositories/{rid}/publications"),
        ("v2", f"{host}/api/v2/repositories",
         lambda rid: f"{host}/api/v2/repositories/{rid}/publications"),
    )
    auth_errs = []
    for ver, repos_url, pubs_url in versions:
        try:
            repos, rtotal = _fetch_list(repos_url, auth)
        except _AuthError as e:
            auth_errs.append(f"{ver}: {e}")
            continue
        if repos is None:
            continue
        out = []
        skipped = 0
        for repo in repos:
            rid = repo.get("id") if isinstance(repo, dict) else None
            if not rid:
                continue
            try:
                pubs, _ptotal = _fetch_list(pubs_url(rid), auth)
            except Exception:            # noqa: BLE001 - repo overslaan bij fout
                skipped += 1
                continue
            out.extend(pubs or [])
        _log.info("Laces API %s: %d repository(s) doorzocht, %d publicatie(s)%s.",
                  ver, len(repos), len(out),
                  f" ({skipped} overgeslagen)" if skipped else "")
        return out
    if auth_errs:
        raise RuntimeError(
            "Inloggen geweigerd door de Laces REST-API (" + "; ".join(auth_errs)
            + "). Let op: de SPARQL-endpoints van gepubliceerde data kunnen "
            "openbaar zijn (merge werkt dan zonder geldige login), maar de "
            "REST-API vereist een geldig Laces access-token (Token-ID + "
            "token-secret) met minstens viewer-rechten op de repositories.")
    raise RuntimeError("Kon de publicatielijst niet ophalen "
                       "(geen Laces REST-API v4/v3/v2 beschikbaar).")


def _pub_path(p):
    """Relatief pad van een publicatie uit een API-item (publicationUri/uri/id/url).
    De API geeft paden terug zonder host (bijv. /digitalbuildingdata/nlcs/test/…)."""
    if not isinstance(p, dict):
        return ""
    for k in ("publicationUri", "uri", "id", "url"):
        v = p.get(k)
        if isinstance(v, str) and v.strip():
            s = urlsplit(v)
            path = s.path if s.scheme else v
            if path.startswith("/"):
                return path.rstrip("/")
    return ""


def fetch_publication_names(base_url, token_id, password):
    """Namen (1e padsegment ná de basis-URL) van publicaties waarvan het pad onder
    base_url valt. Vergelijkt op PAD — host, scheme en /versions/… maken niet uit."""
    _check_credentials(token_id, password)
    base_path = urlsplit(base_url.rstrip("/")).path.rstrip("/")
    auth = (token_id, password)
    pubs = _list_all_publications(_api_host(base_url.rstrip("/")), auth)
    names = []
    for p in pubs:
        path = _pub_path(p)
        if path and path.startswith(base_path + "/"):
            name = path[len(base_path) + 1:].split("/")[0]
            if name and name not in names:
                names.append(name)
    _log.info("%d publicatie(s) onder %s: %s", len(names), base_path,
              ", ".join(sorted(names)) if names else "(geen)")
    return sorted(names)


# ---------------------------------------------------------------------------
# Versie-resolver: kies per publicatie de hoogste versie die matcht met een
# ingevulde prefix (bijv. "5-2" -> "5-2-14"), en bouw versioned SPARQL-URL's.
# ---------------------------------------------------------------------------
def _vernums(label):
    """Versielabel -> tuple ints voor vergelijken: '5-2-14' -> (5, 2, 14)."""
    return tuple(int(x) for x in re.findall(r"\d+", str(label)))


def _base_path_of(path):
    """Pad zonder host en zonder '/versions/<label>' -> het publicatie-basispad."""
    s = urlsplit(path)
    p = s.path if s.scheme else path
    return p.split("/versions/", 1)[0].rstrip("/")


def _pub_ids_by_base(host, auth):
    """{basispad: publicatie-id} over alle toegankelijke publicaties. Het id dient
    om via /api/v4/publications/{id}/versions álle versies op te vragen."""
    m = {}
    for p in _list_all_publications(host, auth):
        if not isinstance(p, dict):
            continue
        pid = p.get("id")
        path = _pub_path(p)
        if not pid or not path:
            continue
        m.setdefault(_base_path_of(path), pid)
    return m


def _version_labels(host, pub_id, auth):
    """Alle versielabels van een publicatie via /api/v4/publications/{id}/versions.
    Elke entry heeft een 'uri' …/versions/<label>; het label parsen we daaruit."""
    labels = []
    page = 0
    while page <= 200:
        url = (f"{host}/api/v4/publications/{pub_id}/versions"
               f"?page={page}&pageSize=100&sortBy=uri&sortDirection=ASC")
        try:
            data = _get_json(url, auth)
        except _AuthError:
            break
        if not data:
            break
        items = _as_list(data)
        if not items:
            break
        for it in items:
            uri = it.get("uri") if isinstance(it, dict) else ""
            if isinstance(uri, str) and "/versions/" in uri:
                lab = uri.split("/versions/", 1)[1].split("/")[0]
                if lab and lab not in labels:
                    labels.append(lab)
        total = data.get("total") if isinstance(data, dict) else None
        page += 1
        if len(items) < 100 or (isinstance(total, int) and page * 100 >= total):
            break
    return labels


def resolve_versioned(urls, version_prefix, token_id, password):
    """Vervang elke (versieloze) publicatie-URL door de HOOGSTE versie die matcht
    met version_prefix (bijv. '5-2' -> '…/versions/5-2-14'). Een URL die al een
    '/versions/…' bevat blijft ongewijzigd. Retour (nieuwe_urls, logregels)."""
    version_prefix = (version_prefix or "").strip()
    if not version_prefix or not urls:
        return list(urls), []
    _check_credentials(token_id, password)
    pnums = _vernums(version_prefix)
    host = _api_host(urls[0])
    auth = (token_id, password)
    ids = _pub_ids_by_base(host, auth)
    out, notes = [], []
    for u in urls:
        u = u.rstrip("/")
        if "/versions/" in u:
            out.append(u)
            notes.append(f"{u} -> heeft al een versie; ongewijzigd")
            continue
        base_path = _base_path_of(u)
        pid = ids.get(base_path)
        if not pid:
            out.append(u)
            notes.append(f"{base_path} -> publicatie niet in hub-lijst; "
                         f"versieloos gebruikt")
            continue
        labels = _version_labels(host, pid, auth)
        cand = [v for v in labels if _vernums(v)[:len(pnums)] == pnums]
        if cand:
            best = max(cand, key=_vernums)
            out.append(f"{u}/versions/{best}")
            notes.append(f"{base_path} -> versie {best} "
                         f"(uit {len(labels)} versie(s))")
        else:
            shown = ", ".join(sorted(labels)) if labels else "geen"
            out.append(u)
            notes.append(f"{base_path} -> GEEN {version_prefix}-versie "
                         f"({len(labels)} versie(s): {shown}); versieloos gebruikt")
    return out, notes
