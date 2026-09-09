"""
ot_compare.py - Twee versies van een objectentabel (CSV) inlezen en vergelijken.

De CSV's zijn komma-gescheiden, met alle velden tussen dubbele quotes en een
kop-rij. Rijen worden gematcht op de kolom `id_nummer`. Alle gemeenschappelijke
kolommen worden LETTERLIJK vergeleken (alleen omringende spaties worden
genegeerd); er zijn geen semantische uitzonderingen.

Resultaat per (nieuwe) rij:
  - 'new'     : id_nummer komt niet voor in de oude versie
  - 'changed' : zelfde id, minstens één andere celwaarde
  - 'same'    : zelfde id, geen verschillen

Daarnaast de 'deleted' rijen: id_nummer wel in de oude, niet in de nieuwe versie.

Los te testen:
    python ot_compare.py nieuw.csv oud.csv
"""

import csv
import glob
import hashlib
import os
import re

KEY = "objectURI"          # kolom waarop rijen gematcht worden (stabiele unieke URI;
                           # id_nummer is in oudere versies leeg)
SORT_COLUMN = 0            # eerste kolom (omschrijving) -> alfabetische sortering


def hoofdgroep_code(path: str) -> str:
    """De laatste code uit een bestandsnaam, bijv. 'objecten-5-2-AL.csv' -> 'AL'.

    Puur het laatste stuk na het laatste koppelteken (voor de extensie); het
    versienummer in de naam wordt genegeerd. Hoofdletter-ongevoelig vergeleken
    (teruggegeven in hoofdletters)."""
    stem = os.path.splitext(os.path.basename(path))[0]
    last = stem.split("-")[-1]
    return last.strip().upper()


def pair_folders(new_dir: str, old_dir: str) -> tuple[list[tuple[str, str, str]],
                                                        list[str], list[str]]:
    """Koppel CSV's uit twee mappen op hun laatste code (hoofdgroep).

    Geeft terug:
      pairs        : lijst (code, nieuw_pad, oud_pad) voor codes in beide mappen
      only_new     : codes die alleen in de nieuwe map zitten
      only_old     : codes die alleen in de oude map zitten
    """
    def index(folder: str) -> dict[str, str]:
        out: dict[str, str] = {}
        for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
            out.setdefault(hoofdgroep_code(path), path)
        return out

    new_idx = index(new_dir)
    old_idx = index(old_dir)
    pairs = [(code, new_idx[code], old_idx[code])
             for code in sorted(new_idx) if code in old_idx]
    only_new = sorted(c for c in new_idx if c not in old_idx)
    only_old = sorted(c for c in old_idx if c not in new_idx)
    return pairs, only_new, only_old


def pair_folder_to_file(new_dir: str, old_file: str) -> tuple[
        list[tuple[str, str, str]], list[str], list[str]]:
    """Koppel elke nieuwe CSV (per hoofdgroep) aan één groot oud CSV-bestand.

    Gebruikt voor symbolen: de oude versie zit in één grote CSV, de nieuwe per
    hoofdgroep. Geeft (pairs, [], []) waarbij pairs = (code, nieuw_pad, oud_bestand).
    """
    pairs = [(hoofdgroep_code(path), path, old_file)
             for path in sorted(glob.glob(os.path.join(new_dir, "*.csv")))]
    return pairs, [], []


def dwg_index(folder: str, ext: str = ".dwg") -> dict:
    """Verzamel recursief alle bestanden met de gegeven extensie onder `folder`.

    Geeft een dict terug: {bestandsnaam-zonder-extensie-in-kleine-letters:
    relatief pad t.o.v. `folder`} (eerste voorkomen wint). Zo kun je per symbool
    controleren of `<symbool>.dwg` aanwezig is (via `stem in index`) én weten waar
    een wees-bestand staat. Bestaat de map niet, dan een lege dict."""
    index: dict = {}
    if not folder or not os.path.isdir(folder):
        return index
    ext = ext.lower()
    for root, _dirs, files in os.walk(folder):
        for name in files:
            stem, e = os.path.splitext(name)
            if e.lower() == ext:
                key = stem.strip().lower()
                if key and key not in index:
                    index[key] = os.path.relpath(os.path.join(root, name), folder)
    return index


def collect_column_values(folder: str, column: str) -> set:
    """Verzamel de (niet-lege, kleine-letter) waarden van kolom `column` uit alle
    CSV's in `folder`. Voor symbolen levert dit alle symboolnamen die in de tabel
    voorkomen; wat daar niet in staat is een 'wees'-bestand."""
    values: set = set()
    if not folder or not os.path.isdir(folder):
        return values
    for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        headers, rows = read_table(path)
        if column not in headers:
            continue
        ci = headers.index(column)
        for r in rows:
            if ci < len(r):
                v = r[ci].strip().lower()
                if v:
                    values.add(v)
    return values


def file_sha256(path: str) -> str:
    """SHA-256 (hex) van een bestand, in blokken gelezen. "" bij leesfouten."""
    try:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return ""


def dwg_hash_status(names, new_abs: dict, old_abs: dict) -> dict:
    """Bepaal per symboolnaam of het .dwg-bestand inhoudelijk gewijzigd is.

    Parameters:
      names   : iterable van symboolnamen (originele schrijfwijze uit de tabel)
      new_abs : dict {stem.lower(): absoluut pad} van de nieuwe versie
      old_abs : dict {stem.lower(): absoluut pad} van de oude versie

    Geeft een dict {stem.lower(): status}, met status:
      'identiek'      : bestand in beide versies, zelfde hash
      'gewijzigd'     : bestand in beide versies, andere hash
      'alleen nieuw'  : bestand alleen in de nieuwe versie
      'alleen oud'    : bestand alleen in de oude versie
      ''              : in geen van beide versies gevonden
    Hashes worden gecachet zodat elk bestand hooguit één keer wordt gelezen."""
    cache: dict = {}

    def h(path: str) -> str:
        if path not in cache:
            cache[path] = file_sha256(path)
        return cache[path]

    out: dict = {}
    for naam in names:
        key = (naam or "").strip().lower()
        if not key or key in out:
            continue
        np = new_abs.get(key)
        op = old_abs.get(key)
        if np and op:
            hn, ho = h(np), h(op)
            out[key] = "identiek" if (hn and hn == ho) else "gewijzigd"
        elif np:
            out[key] = "alleen nieuw"
        elif op:
            out[key] = "alleen oud"
        else:
            out[key] = ""
    return out


def find_csv_by_code(folder: str, code: str) -> str:
    """Zoek in `folder` de CSV waarvan de hoofdgroep-code gelijk is aan `code`
    (bijv. code 'AM' -> 'objecten-5-2-AM.csv'). "" als er niets past."""
    if not folder or not os.path.isdir(folder) or not code:
        return ""
    code = code.strip().upper()
    for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        if hoofdgroep_code(path) == code:
            return path
    return ""


# ---------------------------------------------------------------------------
# Publicatie-overzicht ("kaart"): gepubliceerde HTML's per hoofdgroep vinden
# ---------------------------------------------------------------------------
def version_variants(version: str) -> set:
    """Alle schrijfwijzen van een versie die in bestandsnamen voorkomen.

    De versie staat soms met punt ('objecten-concept-5.2-AL.html') en soms met
    koppelteken ('changelog-lijntypes-5-2-AM.html'). Geef daarom beide vormen
    terug: '5.2' -> {'5.2', '5-2'}. Lege invoer -> lege set."""
    v = (version or "").strip()
    if not v:
        return set()
    return {v, v.replace(".", "-"), v.replace("-", ".")}


def docs_root_of(folder: str) -> str:
    """De 'docs'-map boven `folder`, waarvan de online-URL de basis is.

    De site wordt vanaf de docs-map gepubliceerd, dus het online sub-pad van een
    bestand is zijn pad t.o.v. deze map. Zoekt omhoog naar een map met de naam
    'docs'; valt terug op de oudermap van `folder` als die niet bestaat."""
    cur = os.path.abspath(folder)
    while True:
        if os.path.basename(cur).lower() == "docs":
            return cur
        parent = os.path.dirname(cur)
        if parent == cur:
            break
        cur = parent
    return os.path.dirname(os.path.abspath(folder))


def index_kind(filename: str) -> str:
    """'changelog' voor changelog-/vergelijkingspagina's, anders 'tabel'."""
    low = filename.lower()
    if low.startswith("changelog") or "vergelijking" in low:
        return "changelog"
    return "tabel"


def nice_index_label(filename: str, group_code: str = "") -> str:
    """Leesbaar knop-label uit een bestandsnaam.

    'changelog-lijntypes-5-2-AM.html' -> 'Changelog lijntypes' (in de AM-kaart).
    Weggelaten: het 'NLCS_'-voorvoegsel, versienummers (5, 2, 5.2), het woordje
    'vs', de groepscode zelf en de bibliotheek-varianten daarvan (de kaart toont
    de hoofdgroep al): de code 'AL' én 'SAL'/'ACO' e.d. (de code met één
    bibliotheek-letter ervoor) worden allemaal weggelaten."""
    stem = os.path.splitext(filename)[0]
    if stem.lower().startswith("nlcs_"):
        stem = stem[5:]
    code = (group_code or "").strip().upper()

    def _is_code(tok: str) -> bool:
        # De hoofdgroepcode zelf (AL) of een bibliotheek-variant: de code met één
        # letter ervoor (SAL, ACO, SBC). Alleen op hoofdletter-tokens.
        tu = tok.upper()
        return bool(code) and (tu == code
                               or (len(tu) == len(code) + 1 and tu.endswith(code)))

    out = []
    for t in re.split(r"[-_ ]+", stem):
        if not t:
            continue
        if re.fullmatch(r"\d+(\.\d+)?", t):   # 5, 2, 5.2, 5.0 -> weg
            continue
        if t.lower() == "vs":
            continue
        if _is_code(t):                        # groepscode + bib-variant -> weg
            continue
        out.append(t)
    label = " ".join(out).strip()
    if label:
        label = label[0].upper() + label[1:]
    return label or os.path.splitext(filename)[0]


def scan_publication(root: str, version: str, exclude_names=None) -> dict:
    """Doorzoek `root` (bijv. docs/changelog) recursief naar HTML-bestanden
    waarvan de bestandsnaam een versie-variant bevat (zowel '5.2' als '5-2').

    Groepeer op de eerste submap onder `root` (de hoofdgroep-code, bijv. 'AM');
    bestanden direct in `root` komen in de algemene groep ('voor alle
    hoofdgroepen'). Twee uitzonderingen:
      * `releasenotes.html` (waar dan ook onder `root`) komt ALTIJD in de
        algemene groep, ook zonder versienummer in de naam.
      * publicatie-overzichten (het bestand dat deze functie voedt) worden NOOIT
        opgenomen: bestanden die met 'publicatieoverzicht' beginnen of waarvan de
        naam in `exclude_names` staat, worden overgeslagen.

    Geeft:
      {"groups": [(code, [entry, ...]), ...],   # gesorteerd op code
       "general": [entry, ...],
       "docs_root": <pad>, "count": <int>}
    entry = {"filename", "subpath", "kind", "label"} waarbij subpath het pad is
    t.o.v. de docs-map (posix, voor de online-URL). Per groep staan de tabellen
    vooraan, dan de changelogs, elk alfabetisch op label."""
    variants = version_variants(version)
    docs_root = docs_root_of(root)
    exclude = {n.strip().lower() for n in (exclude_names or ()) if n and n.strip()}
    groups: dict = {}
    general: list = []
    count = 0
    if variants and os.path.isdir(root):
        for dirpath, _dirs, files in os.walk(root):
            for name in sorted(files):
                low = name.lower()
                if not low.endswith((".html", ".htm")):
                    continue
                # Het overzicht zelf (deze pagina) nooit opnemen.
                if low in exclude or low.startswith("publicatieoverzicht") \
                        or low.startswith("publicatie-overzicht"):
                    continue
                is_releasenotes = low.startswith("releasenotes")
                if not is_releasenotes and not any(v in name for v in variants):
                    continue
                full = os.path.join(dirpath, name)
                rel_parts = os.path.relpath(full, root).replace("\\", "/").split("/")
                entry = {
                    "filename": name,
                    "subpath": os.path.relpath(full, docs_root).replace("\\", "/"),
                    "kind": index_kind(name),
                }
                # releasenotes én bestanden direct in root -> algemene groep.
                if is_releasenotes or len(rel_parts) == 1:
                    entry["label"] = ("Release notes" if is_releasenotes
                                      else nice_index_label(name, ""))
                    general.append(entry)
                else:
                    code = rel_parts[0].strip().upper()
                    entry["label"] = nice_index_label(name, code)
                    groups.setdefault(code, []).append(entry)
                count += 1

    def _sortkey(e: dict) -> tuple:
        return (0 if e["kind"] == "tabel" else 1, e["label"].casefold())

    for lst in groups.values():
        lst.sort(key=_sortkey)
    general.sort(key=_sortkey)
    return {
        "groups": sorted(groups.items()),
        "general": general,
        "docs_root": docs_root,
        "count": count,
    }


def sbib_to_code(sbib: str) -> str:
    """Hoofdgroep-code bij een `sbibliotheek`-waarde: de leidende 'S' eraf.

    De symbolen-bibliotheek is 'S' + de objecten-hoofdgroepcode (SAM->AM,
    SAL->AL, SBV->BV, SBC->BC, SFC->FC, SGC->GC). Zo vind je bij elk symbool de
    juiste objectentabel. Nodig voor CO: dat symbolenbestand bevat meerdere
    bibliotheken (SBC/SFC/SGC), dus meerdere hoofdgroepen. Lege invoer -> ""."""
    s = (sbib or "").strip().upper()
    if len(s) > 1 and s.startswith("S"):
        return s[1:]
    return s


def split_result_by_bib(result: dict, scope_col: str = "sbibliotheek",
                         strip_s: bool = True) -> list:
    """Splits een compare()-resultaat op in deelresultaten per hoofdgroep.

    De hoofdgroep-code wordt afgeleid uit de `scope_col`-kolom. Bij symbolen is
    dat de `sbibliotheek` (SBC), waar `strip_s=True` de leidende 'S' afhaalt
    (SBC->BC). Bij lijntypes is `scope_col` de kolom `hoofdgroep` die de code al
    letterlijk bevat (BV, BC, ...); geef daar `strip_s=False` zodat een code als
    'SB' niet foutief tot 'B' wordt gestript. Nodig voor CO: dat verzamelbestand
    bevat meerdere hoofdgroepen en moet uiteenvallen in aparte bestanden.

    Geeft een lijst (code, deelresultaat), gesorteerd op code. Ontbreekt de
    kolom of is er maar één code, dan één paar (die code, het originele
    resultaat) zodat gewone bestanden onveranderd blijven. Elk deelresultaat
    heeft dezelfde headers; rows/deleted zijn gefilterd en stats herberekend."""
    headers = result["headers"]
    if not scope_col or scope_col not in headers:
        return [("", result)]
    bi = headers.index(scope_col)

    def code_of(value: str) -> str:
        return sbib_to_code(value) if strip_s else (value or "").strip().upper()

    def rcode(row: dict) -> str:
        return code_of(row["cells"][bi]["value"])

    def dcode(drow: list) -> str:
        return code_of(drow[bi] if bi < len(drow) else "")

    codes = sorted({rcode(r) for r in result["rows"] if rcode(r)}
                   | {dcode(d) for d in result["deleted"] if dcode(d)})
    if len(codes) <= 1:
        return [(codes[0] if codes else "", result)]

    out = []
    for c in codes:
        rows = [r for r in result["rows"] if rcode(r) == c]
        deleted = [d for d in result["deleted"] if dcode(d) == c]
        out.append((c, {
            "headers": headers,
            "rows": rows,
            "deleted": deleted,
            "stats": {
                "new": sum(1 for x in rows if x["status"] == "new"),
                "changed": sum(1 for x in rows if x["status"] == "changed"),
                "deleted": len(deleted),
                "total_new": len(rows),
            },
        }))
    return out


def column_values(path: str, column: str) -> list:
    """Distinct, niet-lege waarden van kolom `column` uit één CSV, in
    oorspronkelijke schrijfwijze en op volgorde van eerste voorkomen."""
    headers, rows = read_table(path)
    if column not in headers:
        return []
    ci = headers.index(column)
    seen: set = set()
    out: list = []
    for r in rows:
        v = r[ci].strip() if ci < len(r) else ""
        if v and v not in seen:
            seen.add(v)
            out.append(v)
    return out


def _match_stem(name: str) -> str:
    """De symboolnaam vanaf de bibliotheekcode, zodat een variant-voorvoegsel
    (bijv. 'V-', 'B-', 'N-', 'R-', 'T-') niet meetelt bij het zoekfilter-matchen.
    De bibliotheekcode is het eerste naamsegment dat met 'S' begint:
    'V-SGR-BOOM_17' -> 'SGR-BOOM_17', 'SGR-BOOM_17' -> 'SGR-BOOM_17'. Zit er geen
    S-segment in, dan blijft de naam ongewijzigd."""
    segs = name.split("-")
    for i, s in enumerate(segs):
        if s[:1].upper() == "S" and len(s) > 1:
            return "-".join(segs[i:])
    return name


def zoekfilter_map(names, terms) -> dict:
    """Bepaal per symboolnaam de zoekfilter-term waarmee het symbool gevonden
    wordt: de langste `terms`-waarde die een voorvoegsel is van de symboolnaam.

    Parameters:
      names : iterable van symboolnamen (bijv. 'SAM-ASPUNTNUMMER-SO')
      terms : iterable van zoekfilter-termen (de `sobject`-kolom uit de
              objectentabel, bijv. 'SAM-AS', 'SAM-ASPUNTNUMMER')

    Een eventueel variant-voorvoegsel ('V-', 'B-', 'N-', 'R-', 'T-', ...) telt
    NIET mee: er wordt gematcht vanaf de bibliotheekcode, zodat bijv.
    'V-SGR-BOOM_17' door de term 'SGR-BOOM' gevonden wordt.

    Geeft {naam.lower(): term} (lege string als geen enkele term past).
    Bij meerdere passende termen wint de langste (meest specifieke)."""
    terms_sorted = sorted({t.strip() for t in terms if t and t.strip()},
                          key=len, reverse=True)
    out: dict = {}
    for nm in names:
        s = (nm or "").strip()
        if not s:
            continue
        key = s.lower()
        if key in out:
            continue
        stem = _match_stem(s)
        out[key] = ""
        for t in terms_sorted:
            if stem == t or stem.startswith(t):
                out[key] = t
                break
    return out


def collect_column_values_list(folder: str, column: str) -> list:
    """Distinct, niet-lege waarden van kolom `column` uit ALLE CSV's in `folder`,
    in oorspronkelijke schrijfwijze en op volgorde van eerste voorkomen (over de
    bestanden heen, alfabetisch op bestandsnaam). Anders dan
    `collect_column_values` (set, kleine letters) blijft de schrijfwijze behouden;
    nodig om bijv. alle arceringnamen te tonen. Lege map -> lege lijst."""
    out: list = []
    seen: set = set()
    if not folder or not os.path.isdir(folder):
        return out
    for path in sorted(glob.glob(os.path.join(folder, "*.csv"))):
        for v in column_values(path, column):
            key = v.lower()
            if key not in seen:
                seen.add(key)
                out.append(v)
    return out


def read_table(path: str) -> tuple[list[str], list[list[str]]]:
    """Lees een CSV in als (headers, rijen). Elke rij is een lijst strings met
    dezelfde lengte als headers (aangevuld/afgekapt waar nodig). UTF-8, BOM-ok."""
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        raw = [row for row in csv.reader(f) if any(c.strip() for c in row)]
    if not raw:
        return [], []
    headers = [h.strip() for h in raw[0]]
    n = len(headers)
    rows = []
    for r in raw[1:]:
        vals = list(r) + [""] * (n - len(r))
        rows.append(vals[:n])
    return headers, rows


def _collect_id_records(source_path: str, source: str,
                        id_col: str = "id_nummer",
                        uri_col: str = KEY, exclude: dict = None,
                        name_col: str = "") -> list[dict]:
    """Lees per rij het ID en de URI uit `source_path`.

    `source_path` mag een MAP zijn (dan worden alle *.csv erin gelezen, bijv. de
    per-hoofdgroep objectentabellen/symbolentabellen) OF één CSV-BESTAND (bijv. de
    ene grote oude symbolen-/arceringen-/lijntypes-CSV).

    `exclude` : optioneel {"match_col": <kolom>, "values": {<waarde>, ...}}. Rijen
                waarvan `match_col` (hoofdletterongevoelig) in `values` zit worden
                helemaal overgeslagen — bijv. de generieke lijntypes CONTINUOUS/
                V-CONTINUOUS-SO die uit een andere publicatie komen en geen eigen
                ID-reeks hebben.

    `name_col` : optionele kolom met een mensleesbare naam (bijv. 'omschrijving',
                 'symbool', 'arcering'); komt als "name" in elk record (leeg als
                 de kolom ontbreekt). Handig omdat de URI slecht leesbaar is.

    Geeft een lijst dicts terug:
      {"uri": <URI>, "id": <ID, ruwe string>, "name": <mensleesbare naam>,
       "file": <bestandsnaam>, "row": <rijnummer in het bestand, 1-based
                incl. kop>, "source": <source-label>}
    Rijen zonder ID hebben "id": "" (nieuwe objecten die nog een nummer nodig
    hebben). Bestaat de bron niet, dan een lege lijst."""
    out: list[dict] = []
    if not source_path:
        return out
    if os.path.isdir(source_path):
        paths = sorted(glob.glob(os.path.join(source_path, "*.csv")))
    elif os.path.isfile(source_path):
        paths = [source_path]
    else:
        return out
    ex_col = (exclude or {}).get("match_col", "")
    ex_vals = {(v or "").strip().upper() for v in (exclude or {}).get("values", [])}
    for path in paths:
        headers, rows = read_table(path)
        if id_col not in headers:
            continue
        ci = headers.index(id_col)
        ui = headers.index(uri_col) if uri_col in headers else -1
        xi = headers.index(ex_col) if ex_col and ex_col in headers else -1
        mi = headers.index(name_col) if name_col and name_col in headers else -1
        name = os.path.basename(path)
        for n, r in enumerate(rows, start=2):   # +1 kop, +1 want 1-based
            if 0 <= xi < len(r) and r[xi].strip().upper() in ex_vals:
                continue
            idv = r[ci].strip() if ci < len(r) else ""
            uri = r[ui].strip() if 0 <= ui < len(r) else ""
            nm = r[mi].strip() if 0 <= mi < len(r) else ""
            out.append({"uri": uri, "id": idv, "name": nm, "file": name,
                        "row": n, "source": source})
    return out


def _is_int_id(value: str) -> bool:
    """True als `value` een geheel getal is (evt. met min-teken)."""
    return bool(value) and value.lstrip("-").isdigit()


def analyze_ids(new_src: str, old_src: str,
                id_col: str = "id_nummer", uri_col: str = KEY,
                exclude: dict = None, name_col: str = "") -> dict:
    """Analyseer de ID's (kolom `id_col`) uit de nieuwe en de vorige publicatie.

    `new_src`/`old_src` mogen een MAP (CSV's per hoofdgroep) of één CSV-BESTAND
    zijn (de oude symbolen-/arceringen-/lijntypes-CSV is één groot bestand).
    Voor objecten is `id_col="id_nummer"`, `uri_col="objectURI"`; voor symbolen/
    arceringen/lijntypes `id_col="id"` met de bijbehorende URI-kolom.

    `exclude` : optioneel {"match_col", "values"} — rijen die hierop matchen
    worden volledig buiten de analyse gehouden (bijv. de generieke lijntypes
    CONTINUOUS/V-CONTINUOUS-SO, die uit een andere publicatie komen).

    Geeft een dict terug met:
      new / old         : lijst records per publicatie (zie _collect_id_records)
      highest           : hoogste gehele ID over beide publicaties (0 als geen)
      next_free         : eerstvolgende vrije ID (highest + 1), altijd hoger dan
                          elk bestaand geheel ID
      duplicates        : lijst {"id", "uris":[...], "records":[...]} waar één ID
                          aan meer dan één verschillende URI hangt (over beide
                          publicaties heen) — dubbel gebruikte ID's
      mismatches        : lijst {"uri", "new_id", "old_id", ...} waar dezelfde URI
                          in de vorige én nieuwe publicatie een ander ID heeft
      blanks_new / blanks_old : records zonder ID (nieuwe objecten zonder nummer)
      noninteger        : records met een niet-geheel ID (uitgesloten van 'highest')
    """
    new_recs = _collect_id_records(new_src, "nieuw", id_col, uri_col, exclude, name_col)
    old_recs = _collect_id_records(old_src, "vorig", id_col, uri_col, exclude, name_col)
    all_recs = new_recs + old_recs

    # Hoogste gehele ID -> eerstvolgende vrije nummer.
    ints = [int(rec["id"]) for rec in all_recs if _is_int_id(rec["id"])]
    highest = max(ints) if ints else 0

    # Dubbele ID's: één ID gekoppeld aan >1 verschillende URI (over beide
    # publicaties heen). Dezelfde URI met hetzelfde ID in oud én nieuw telt
    # NIET als dubbel (dat is juist correct). Rijen ZONDER URI worden hierbij
    # genegeerd: een lege URI is geen echte identiteit en mag geen dubbele-ID-
    # melding veroorzaken (anders zou bijv. eenzelfde symbool met dezelfde URI
    # in 5.0 en 5.2 tóch als dubbel gemeld worden zodra ergens een regel met dat
    # ID maar zonder URI staat).
    id_to_uris: dict[str, set] = {}
    id_to_recs: dict[str, list] = {}
    for rec in all_recs:
        if not rec["id"] or not rec["uri"]:
            continue
        id_to_uris.setdefault(rec["id"], set()).add(rec["uri"])
        id_to_recs.setdefault(rec["id"], []).append(rec)
    duplicates = [
        {"id": idv, "uris": sorted(uris), "records": id_to_recs[idv]}
        for idv, uris in id_to_uris.items() if len(uris) > 1
    ]
    duplicates.sort(key=lambda d: (not _is_int_id(d["id"]),
                                   int(d["id"]) if _is_int_id(d["id"]) else 0,
                                   d["id"]))

    # URI-mismatch: dezelfde URI in oud én nieuw, maar met een ander ID.
    def uri_ids(recs):
        m: dict[str, set] = {}
        for rec in recs:
            if rec["uri"] and rec["id"]:
                m.setdefault(rec["uri"], set()).add(rec["id"])
        return m
    # mensleesbare naam per URI (nieuwe publicatie eerst, anders de oude).
    uri_name: dict[str, str] = {}
    for rec in old_recs + new_recs:
        if rec["uri"] and rec.get("name"):
            uri_name[rec["uri"]] = rec["name"]
    new_uri_ids = uri_ids(new_recs)
    old_uri_ids = uri_ids(old_recs)
    mismatches = []
    for uri in sorted(set(new_uri_ids) & set(old_uri_ids)):
        n_ids = new_uri_ids[uri]
        o_ids = old_uri_ids[uri]
        if n_ids != o_ids:
            mismatches.append({
                "uri": uri,
                "name": uri_name.get(uri, ""),
                "new_id": ", ".join(sorted(n_ids)),
                "old_id": ", ".join(sorted(o_ids)),
            })

    return {
        "new": new_recs,
        "old": old_recs,
        "highest": highest,
        "next_free": highest + 1,
        "duplicates": duplicates,
        "mismatches": mismatches,
        "blanks_new": [r for r in new_recs if not r["id"]],
        "blanks_old": [r for r in old_recs if not r["id"]],
        "noninteger": [r for r in all_recs
                       if r["id"] and not _is_int_id(r["id"])],
    }


# Geldige optie-codes: het achtervoegsel achteraan de naam (zonder '-'). Staat er
# achteraan iets uit deze set, dan hoort dat in de kolom 'optie'; staat er niets
# uit deze set, dan hoort 'optie' leeg te zijn.
FASE_OPTIE_CODES = ("S", "SO", "SOMM", "SOD", "SODMM", "D", "MM", "DMM")


def _expected_fase_optie(name: str) -> tuple[str, str]:
    """Leidt uit een gecodeerde naam af wat er in 'fase' en 'optie' hoort te staan.

    Voorvoegsel: het eerste '-'-segment als dat één letter is (V, B, …) — dat
    hoort de fase te zijn (bibliotheek-/hoofdgroepcodes zijn altijd ≥2 tekens:
    SAL, SFC, AL, AM, ACO, …). Geen zo'n voorvoegsel → fase hoort leeg te zijn.
    Achtervoegsel: het laatste '-'-segment als dat een geldige optie-code is
    (FASE_OPTIE_CODES) — dat hoort de optie te zijn, zónder '-'. Anders → optie
    hoort leeg te zijn."""
    segs = name.split("-")
    pref = ""
    if len(segs) > 1 and len(segs[0]) == 1 and segs[0].isalpha():
        pref = segs[0].upper()
    suf = ""
    if len(segs) > 1 and segs[-1].strip().upper() in FASE_OPTIE_CODES:
        suf = segs[-1].strip().upper()
    return pref, suf


def check_fase_optie(src: str, name_col: str, exclude_names=()) -> list[dict]:
    """Controleer per rij of de kolommen 'fase' en 'optie' kloppen met de naam.

    `src` mag een MAP (CSV's per hoofdgroep) of één CSV-BESTAND zijn. `name_col`
    is de kolom met de gecodeerde naam: 'symbool' (symbolen), 'omschrijving'
    (lijntypes) of 'arcering' (arceringen). `exclude_names` : namen die worden
    overgeslagen (bijv. de generieke lijntypes CONTINUOUS/V-CONTINUOUS-SO uit een
    andere publicatie, met bewust lege fase/optie).

    Geeft een lijst afwijkingen terug — dicts {"kind": 'fase'|'optie', "name",
    "got", "expected", "file", "row"} — één per verkeerd gevulde kolom. Rijen
    zonder naam of zonder de betreffende kolom leveren niets op."""
    out: list[dict] = []
    if not src:
        return out
    if os.path.isdir(src):
        paths = sorted(glob.glob(os.path.join(src, "*.csv")))
    elif os.path.isfile(src):
        paths = [src]
    else:
        return out
    skip = {(n or "").strip().upper() for n in exclude_names}
    for path in paths:
        headers, rows = read_table(path)
        if name_col not in headers:
            continue
        ni = headers.index(name_col)
        fi = headers.index("fase") if "fase" in headers else -1
        oi = headers.index("optie") if "optie" in headers else -1
        name = os.path.basename(path)
        for n, r in enumerate(rows, start=2):   # +1 kop, +1 want 1-based
            nm = (r[ni] if ni < len(r) else "").strip()
            if not nm or nm.upper() in skip:
                continue
            ef, eo = _expected_fase_optie(nm)
            if fi >= 0:
                fa = (r[fi] if fi < len(r) else "").strip()
                if fa.upper() != ef:
                    out.append({"kind": "fase", "name": nm, "got": fa,
                                "expected": ef, "file": name, "row": n})
            if oi >= 0:
                op = (r[oi] if oi < len(r) else "").strip()
                if op.upper() != eo:
                    out.append({"kind": "optie", "name": nm, "got": op,
                                "expected": eo, "file": name, "row": n})
    return out


def _name_segments(name: str) -> list[str]:
    """Splits een objectnaam in segmenten op de scheidingstekens '-' en '_'.
    Lege segmenten (dubbele scheidingstekens) worden weggelaten."""
    return [s for s in re.split(r"[-_]", (name or "").strip()) if s]


def check_object_tree(src: str, name_col: str = "omschrijving",
                      id_col: str = "id_nummer",
                      parent_col: str = "kind_van") -> dict:
    """Controleer de boomstructuur van de objecten.

    De objecten vormen een boom: `parent_col` (standaard 'kind_van') bevat het
    `id_col` (standaard 'id_nummer') van het bovenliggende object; is dat leeg,
    dan staat het object bovenaan (root). De naam (`name_col`, standaard
    'omschrijving') bestaat uit segmenten gescheiden door '-' en '_'. Regel: een
    onderliggend object heeft *precies één* segment meer dan zijn ouder — niet
    meer en niet minder — en de naam van de ouder is exact het begin van de naam
    van het kind (het kind = ouder + één toevoeging).

    `src` mag een MAP met CSV's per hoofdgroep of één CSV-bestand zijn.

    Geeft een dict terug:
      {
        "count":   totaal aantal objecten,
        "roots":   [id, ...]  (op naam gesorteerd),
        "nodes":   {id: {"id","name","parent","children":[...],"depth","segs"}},
        "max_depth": grootste diepte,
        "errors":  [ {"type","id","name","parent","parent_name","got",
                      "expected","detail"} , ... ],
      }
    Fouttypes: 'orphan' (ouder-id onbekend), 'count' (geen +1 segment),
    'prefix' (naam is geen uitbreiding van de oudernaam),
    'separator' (segmenten kloppen wel, maar de oudernaam staat niet exact
    vooraan mét hetzelfde scheidingsteken '-'/'_'),
    'root_multi' (root met meer dan één segment: mogelijk ontbrekende ouder),
    'subobjecten' (het deel vóór het eerste koppelteken '-' — de laagnaam
    zonder fase/optie-achtervoegsel — bevat meer dan 5 subobjecten, d.w.z.
    meer dan 5 scheidingstekens '_'; komt overeen met de SPARQL-controle
    controle_nlcs-objecten_te_veel_subobjecten)."""
    empty = {"count": 0, "roots": [], "nodes": {}, "max_depth": 0, "errors": []}
    if not src:
        return empty
    if os.path.isdir(src):
        paths = sorted(glob.glob(os.path.join(src, "*.csv")))
    elif os.path.isfile(src):
        paths = [src]
    else:
        return empty

    nodes: dict[str, dict] = {}
    for path in paths:
        headers, rows = read_table(path)
        if name_col not in headers or id_col not in headers:
            continue
        ni = headers.index(name_col)
        ii = headers.index(id_col)
        pi = headers.index(parent_col) if parent_col in headers else -1
        fn = os.path.basename(path)
        for r in rows:
            idn = (r[ii] if ii < len(r) else "").strip()
            if not idn:
                continue
            name = (r[ni] if ni < len(r) else "").strip()
            parent = (r[pi] if pi >= 0 and pi < len(r) else "").strip()
            # eerste voorkomen wint (zoals elders in de tool)
            nodes.setdefault(idn, {
                "id": idn, "name": name, "parent": parent,
                "children": [], "segs": _name_segments(name),
                "depth": 0, "file": fn,
            })

    # kinderen koppelen + diepte bepalen
    errors: list[dict] = []
    roots: list[str] = []
    for idn, nd in nodes.items():
        p = nd["parent"]
        if not p:
            roots.append(idn)
        elif p in nodes:
            nodes[p]["children"].append(idn)
        else:
            roots.append(idn)   # wees: behandel als top zodat hij zichtbaar blijft
            errors.append({
                "type": "orphan", "id": idn, "name": nd["name"],
                "parent": p, "parent_name": "",
                "got": "", "expected": "",
                "detail": f"bovenliggend id '{p}' niet gevonden",
            })

    # diepte via iteratieve afdaling vanaf de roots (cyclus-veilig)
    max_depth = 0
    for rid in roots:
        stack = [(rid, 0)]
        seen = set()
        while stack:
            cur, depth = stack.pop()
            if cur in seen:
                continue
            seen.add(cur)
            nodes[cur]["depth"] = depth
            max_depth = max(max_depth, depth)
            for ch in nodes[cur]["children"]:
                stack.append((ch, depth + 1))

    # naamregels controleren
    for idn, nd in nodes.items():
        # te veel subobjecten: neem het deel van de naam vóór het eerste
        # koppelteken '-' (de laagnaam zonder fase/optie-achtervoegsel) en tel
        # de scheidingstekens '_'. Meer dan 5 subobjecten (= meer dan 5 '_')
        # mag niet in een laagnaam staan. Gelijk aan de SPARQL-controle
        # controle_nlcs-objecten_te_veel_subobjecten.
        clean = nd["name"].split("-", 1)[0]
        n_sub = clean.count("_")
        if n_sub > 5:
            errors.append({
                "type": "subobjecten", "id": idn, "name": nd["name"],
                "parent": nd["parent"], "parent_name": "",
                "got": n_sub, "expected": 5,
                "detail": f"{n_sub} subobjecten in de laagnaam '{clean}' "
                          f"(meer dan 5 mag niet)",
            })
        p = nd["parent"]
        if not p:
            if len(nd["segs"]) > 1:
                errors.append({
                    "type": "root_multi", "id": idn, "name": nd["name"],
                    "parent": "", "parent_name": "",
                    "got": len(nd["segs"]), "expected": 1,
                    "detail": "object zonder bovenliggend id heeft meer dan "
                              "één segment",
                })
            continue
        if p not in nodes:
            continue   # al als wees gemeld
        par = nodes[p]
        ps, cs = par["segs"], nd["segs"]
        count_ok = len(cs) == len(ps) + 1
        prefix_ok = cs[:len(ps)] == ps
        if not count_ok:
            errors.append({
                "type": "count", "id": idn, "name": nd["name"],
                "parent": p, "parent_name": par["name"],
                "got": len(cs), "expected": len(ps) + 1,
                "detail": f"{len(cs)} segmenten; ouder heeft er {len(ps)} "
                          f"(verwacht {len(ps) + 1})",
            })
        if not prefix_ok:
            errors.append({
                "type": "prefix", "id": idn, "name": nd["name"],
                "parent": p, "parent_name": par["name"],
                "got": nd["name"], "expected": par["name"] + "_…",
                "detail": "naam is geen uitbreiding van de oudernaam",
            })
        # scheidingsteken: de oudernaam moet LETTERLIJK (mét eigen '-'/'_')
        # vooraan in de kindnaam staan, gevolgd door precies één scheidingsteken
        # en de toevoeging. Alleen zinvol als segment-inhoud + aantal al kloppen;
        # anders is 'count'/'prefix' de relevante melding.
        elif count_ok and par["name"]:
            pn = par["name"]
            ok = (nd["name"].startswith(pn)
                  and len(nd["name"]) > len(pn)
                  and nd["name"][len(pn)] in "-_")
            if not ok:
                errors.append({
                    "type": "separator", "id": idn, "name": nd["name"],
                    "parent": p, "parent_name": pn,
                    "got": nd["name"], "expected": f"{pn}- / {pn}_",
                    "detail": "scheidingsteken klopt niet: de oudernaam moet "
                              "exact vooraan staan, gevolgd door '-' of '_'",
                })

    roots.sort(key=lambda i: nodes[i]["name"].casefold())
    for nd in nodes.values():
        nd["children"].sort(key=lambda i: nodes[i]["name"].casefold())
    return {
        "count": len(nodes), "roots": roots, "nodes": nodes,
        "max_depth": max_depth, "errors": errors,
    }


# Kolommen in de objectentabel die naar een lijntype-naam verwijzen
# (per variant: bestaand/nieuw/vervallen/tijdelijk).
LIJNTYPE_REF_COLS = ("lt_b", "lt_n", "lt_v", "lt_t")

# Visualisatie-velden per fase in de objectentabel: lijngewicht (lw), de kleuren
# (kl*) en het lijntype (lt). Een object "heeft een visualisatie" voor een fase
# als minstens één van deze velden gevuld is.
FASE_VELDEN = {
    "B": ("lw_b", "kl_b", "kl_b_a", "kl_b_gd", "kl_b_gn", "kl_b_v", "lt_b"),
    "N": ("lw_n", "kl_n", "kl_n_a", "kl_n_gd", "kl_n_gn", "kl_n_v", "lt_n"),
    "V": ("lw_v", "kl_v", "kl_v_a", "kl_v_gd", "kl_v_gn", "kl_v_v", "lt_v"),
    "T": ("lw_t", "kl_t", "kl_t_a", "kl_t_gd", "kl_t_gn", "kl_t_v", "lt_t"),
}
FASE_LABELS = {"B": "Bestaand", "N": "Nieuw", "V": "Vervallen", "T": "Tijdelijk"}
FASE_VOLGORDE = ("B", "N", "V", "T")
# Hoofdgroepen die alleen een visualisatie voor de bestaande situatie (fase B)
# hebben; voor deze codes worden N/V/T niet verwacht.
FASE_ALLEEN_B_CODES = ("AL", "ZZ")


def check_lijntype_usage(lijn_src: str, obj_src: str,
                         name_col: str = "omschrijving",
                         obj_name_col: str = "omschrijving",
                         ref_cols=LIJNTYPE_REF_COLS,
                         exclude_names=()) -> dict:
    """Controleer of elk lijntype ook in de objectentabel wordt gebruikt.

    Detectie op NAAM: de objectentabel verwijst in de kolommen `ref_cols`
    (standaard lt_b/lt_n/lt_v/lt_t) naar de naam van een lijntype (kolom
    `name_col`, standaard 'omschrijving'). `lijn_src` en `obj_src` mogen elk een
    MAP met CSV's of één CSV-bestand zijn. `exclude_names` : lijntype-namen die
    buiten beschouwing blijven (bijv. generieke lijnen uit een andere publicatie).

    Geeft een dict terug:
      {
        "lijn_total":     aantal unieke lijntypes,
        "used":           [naam, ...]  (lijntypes die in objecten voorkomen),
        "unused":         [ {name, hoofdgroep, file} ]  (bestaat wel, niet gebruikt),
        "obj_refs_total": aantal unieke verwezen namen in de objecten,
        "missing":        [ {name, count, objects[]} ]  (objecten verwijzen naar
                          een naam die geen bestaand lijntype is),
      }
    """
    def _paths(src):
        if not src:
            return []
        if os.path.isdir(src):
            return sorted(glob.glob(os.path.join(src, "*.csv")))
        if os.path.isfile(src):
            return [src]
        return []

    skip = {(n or "").strip().upper() for n in exclude_names}

    # bestaande lijntypes: naam -> (hoofdgroep, bestand) — eerste voorkomen wint
    lijn: dict[str, dict] = {}
    for path in _paths(lijn_src):
        headers, rows = read_table(path)
        if name_col not in headers:
            continue
        ni = headers.index(name_col)
        hi = headers.index("hoofdgroep") if "hoofdgroep" in headers else -1
        fn = os.path.basename(path)
        for r in rows:
            nm = (r[ni] if ni < len(r) else "").strip()
            if not nm or nm.upper() in skip:
                continue
            lijn.setdefault(nm, {
                "name": nm,
                "hoofdgroep": (r[hi] if hi >= 0 and hi < len(r) else "").strip(),
                "file": fn,
            })

    # verwijzingen vanuit de objecten: naam -> lijst object-omschrijvingen
    refs: dict[str, list[str]] = {}
    for path in _paths(obj_src):
        headers, rows = read_table(path)
        idxs = [headers.index(c) for c in ref_cols if c in headers]
        oi = headers.index(obj_name_col) if obj_name_col in headers else -1
        for r in rows:
            oname = (r[oi] if oi >= 0 and oi < len(r) else "").strip()
            for i in idxs:
                v = (r[i] if i < len(r) else "").strip()
                if not v or v.upper() in skip:
                    continue
                refs.setdefault(v, [])
                if oname and oname not in refs[v]:
                    refs[v].append(oname)

    used = sorted((n for n in lijn if n in refs), key=str.casefold)
    unused = [lijn[n] for n in sorted(lijn, key=str.casefold) if n not in refs]
    missing = [
        {"name": n, "count": len(refs[n]), "objects": sorted(refs[n], key=str.casefold)}
        for n in sorted(refs, key=str.casefold) if n not in lijn
    ]
    return {
        "lijn_total": len(lijn),
        "used": used,
        "unused": unused,
        "obj_refs_total": len(refs),
        "missing": missing,
    }


def check_searchterm_coverage(name_src: str, obj_src: str,
                              name_col: str, obj_col: str) -> dict:
    """Controleer of elk symbool/elke arcering via een zoekterm in de
    objectentabel gevonden wordt.

    De zoekterm is een `obj_col`-waarde (sobject voor symbolen, aobject voor
    arceringen) uit de objectentabel. Een symbool/arcering wordt GEVONDEN als
    zo'n zoekterm als string (substring) in de naam (`name_col`: 'symbool' resp.
    'arcering') voorkomt. `name_src` en `obj_src` mogen elk een MAP met CSV's of
    één CSV-bestand zijn.

    Geeft terug:
      {
        "total":       aantal namen,
        "term_count":  aantal unieke zoektermen (obj_col-waarden),
        "found":       aantal gevonden,
        "not_found":   [ {name, file} ]  (op naam gesorteerd, uniek),
      }
    """
    def _paths(src):
        if not src:
            return []
        if os.path.isdir(src):
            return sorted(glob.glob(os.path.join(src, "*.csv")))
        if os.path.isfile(src):
            return [src]
        return []

    # zoektermen verzamelen uit de objectentabel
    terms: set[str] = set()
    for path in _paths(obj_src):
        headers, rows = read_table(path)
        if obj_col not in headers:
            continue
        ci = headers.index(obj_col)
        for r in rows:
            v = (r[ci] if ci < len(r) else "").strip()
            if v:
                terms.add(v)
    # langste eerst zodat een 'gevonden'-treffer de meest specifieke term is
    terms_sorted = sorted(terms, key=len, reverse=True)

    total = 0
    found = 0
    not_found: list[dict] = []
    seen: set[str] = set()
    for path in _paths(name_src):
        headers, rows = read_table(path)
        if name_col not in headers:
            continue
        ni = headers.index(name_col)
        fn = os.path.basename(path)
        for r in rows:
            name = (r[ni] if ni < len(r) else "").strip()
            if not name or name in seen:
                continue
            seen.add(name)
            total += 1
            if any(t in name for t in terms_sorted):
                found += 1
            else:
                not_found.append({"name": name, "file": fn})
    not_found.sort(key=lambda d: d["name"].casefold())
    return {
        "total": total, "term_count": len(terms),
        "found": found, "not_found": not_found,
    }


def check_searchterm_min(obj_src: str, name_src: str,
                         obj_col: str, name_col: str) -> dict:
    """Controleer of elke zoekterm uit de objectentabel minstens één symbool/
    arcering vindt (minimaal 1 vereist).

    De zoekterm is een `obj_col`-waarde (sobject voor symbolen, aobject voor
    arceringen) uit de objectentabel. Een symbool/arcering wordt GEVONDEN als de
    zoekterm als string (substring) in de naam (`name_col`: 'symbool' resp.
    'arcering') voorkomt. Dit is de omgekeerde richting van
    `check_searchterm_coverage`: dáár moet elke naam een term hebben, hier moet
    elke term een naam vinden. `obj_src` en `name_src` mogen elk een MAP met
    CSV's of één CSV-bestand zijn.

    Geeft terug:
      {
        "total":      aantal unieke zoektermen (obj_col-waarden),
        "name_count": aantal namen (symbolen/arceringen),
        "ok":         aantal zoektermen met >=1 treffer,
        "empty":      [ {term, files} ]  (zoektermen zonder treffer, gesorteerd;
                       'files' = objectbestanden waarin de term voorkomt),
      }
    """
    def _paths(src):
        if not src:
            return []
        if os.path.isdir(src):
            return sorted(glob.glob(os.path.join(src, "*.csv")))
        if os.path.isfile(src):
            return [src]
        return []

    # zoektermen verzamelen uit de objectentabel (met bronbestanden)
    term_files: dict[str, set] = {}
    for path in _paths(obj_src):
        headers, rows = read_table(path)
        if obj_col not in headers:
            continue
        ci = headers.index(obj_col)
        fn = os.path.basename(path)
        for r in rows:
            v = (r[ci] if ci < len(r) else "").strip()
            if v:
                term_files.setdefault(v, set()).add(fn)

    # alle namen (symbolen/arceringen) verzamelen
    names: list[str] = []
    for path in _paths(name_src):
        headers, rows = read_table(path)
        if name_col not in headers:
            continue
        ni = headers.index(name_col)
        for r in rows:
            nm = (r[ni] if ni < len(r) else "").strip()
            if nm:
                names.append(nm)

    ok = 0
    empty: list[dict] = []
    for term in term_files:
        if any(term in nm for nm in names):
            ok += 1
        else:
            empty.append({
                "term": term,
                "files": sorted(term_files[term]),
            })
    empty.sort(key=lambda d: d["term"].casefold())
    return {
        "total": len(term_files), "name_count": len(names),
        "ok": ok, "empty": empty,
    }


# Tekens die in CAD-laag-/symboolnamen niet zijn toegestaan, met de reden.
# Samengesteld uit de restricties van AutoCAD (symboolnaam / EXTNAMES / snvalid),
# MicroStation (level names) en AutoLISP. Spatie, punt (decimaalteken), '-' en
# '_' zijn WEL toegestaan (die worden in NLCS-namen bewust gebruikt).
FORBIDDEN_NAME_CHARS = {
    "\\": "backslash — tekenscheiding, niet toegestaan (AutoCAD, MicroStation)",
    "/": "schuine streep — tekenscheiding, niet toegestaan (AutoCAD, MicroStation)",
    ",": "komma — niet toegestaan (AutoCAD, MicroStation); gebruik een punt als decimaalteken",
    "[": "blokhaak openen — niet toegestaan",
    "]": "blokhaak sluiten — niet toegestaan",
    "<": "kleiner-dan — niet toegestaan (AutoCAD, MicroStation)",
    ">": "groter-dan — niet toegestaan (AutoCAD, MicroStation)",
    '"': "dubbele aanhalingstekens — niet toegestaan (AutoCAD, MicroStation, LISP)",
    "'": "apostrof — niet toegestaan (MicroStation, LISP)",
    ":": "dubbele punt — niet toegestaan (AutoCAD)",
    ";": "puntkomma — niet toegestaan (AutoCAD; commentaarteken in LISP)",
    "?": "vraagteken — jokerteken, niet toegestaan (AutoCAD, MicroStation)",
    "*": "asterisk — jokerteken, niet toegestaan (AutoCAD)",
    "|": "verticale streep — xref-scheiding, niet toegestaan (AutoCAD)",
    "=": "is-gelijkteken — niet toegestaan (AutoCAD, MicroStation)",
    "`": "accent grave — niet toegestaan (AutoCAD)",
    "(": "haakje openen — breekt LISP-expressies",
    ")": "haakje sluiten — breekt LISP-expressies",
}


def check_special_chars(src: str, name_col: str,
                        forbidden: dict = None) -> dict:
    """Controleer namen op tekens die in CAD-laag-/symboolnamen niet zijn
    toegestaan (zie FORBIDDEN_NAME_CHARS). Spaties, de punt (decimaalteken), '-'
    en '_' zijn WEL toegestaan. `src` mag een MAP met CSV's of één CSV zijn.

    Geeft terug:
      {
        "total":      aantal gecontroleerde namen,
        "ok":         aantal namen zonder verboden teken,
        "violations": [ {name, file, row, chars:[verboden tekens, uniek]} ]
                      (gesorteerd op (file, name)),
        "lowercase":  [ {name, file, row} ]  (namen met een kleine letter;
                      INFORMATIEF — kleine letters zijn toegestaan voor bv.
                      eenheden (mm/Mm) en elementsymbolen (Cu), dus geen fout),
      }
    """
    fb = forbidden if forbidden is not None else FORBIDDEN_NAME_CHARS
    empty = {"total": 0, "ok": 0, "violations": [], "lowercase": []}
    if not src:
        return empty
    if os.path.isdir(src):
        paths = sorted(glob.glob(os.path.join(src, "*.csv")))
    elif os.path.isfile(src):
        paths = [src]
    else:
        return empty

    total = 0
    ok = 0
    violations: list[dict] = []
    lowercase: list[dict] = []
    for path in paths:
        headers, rows = read_table(path)
        if name_col not in headers:
            continue
        ni = headers.index(name_col)
        fn = os.path.basename(path)
        for i, r in enumerate(rows):
            name = (r[ni] if ni < len(r) else "").strip()
            if not name:
                continue
            total += 1
            found = [ch for ch in fb if ch in name]
            if found:
                violations.append({"name": name, "file": fn, "row": i + 2,
                                   "chars": found})
            else:
                ok += 1
            if any(c.islower() for c in name):
                lowercase.append({"name": name, "file": fn, "row": i + 2})
    violations.sort(key=lambda d: (d["file"], d["name"].casefold()))
    lowercase.sort(key=lambda d: (d["file"], d["name"].casefold()))
    return {"total": total, "ok": ok, "violations": violations,
            "lowercase": lowercase}


def check_fase_visualisatie(src: str, name_col: str = "omschrijving",
                            hoofdgroep_col: str = "hoofdgroep",
                            only_b_codes=FASE_ALLEEN_B_CODES) -> dict:
    """Controleer of elk object voor alle fasen een visualisatie heeft.

    Elke fase (B=bestaand, N=nieuw, V=vervallen, T=tijdelijk) heeft in de
    objectentabel een groep velden (lijngewicht `lw`, kleuren `kl*`, lijntype
    `lt`, zie `FASE_VELDEN`). Een object "heeft een visualisatie" voor een fase
    als minstens één van die velden gevuld is. Verwacht worden alle vier de
    fasen, BEHALVE voor de hoofdgroepen in `only_b_codes` (standaard AL en ZZ):
    die hebben alleen een visualisatie voor de bestaande situatie (fase B).

    De hoofdgroep wordt per rij uit kolom `hoofdgroep_col` gelezen (valt terug op
    de code in de bestandsnaam). `src` mag een MAP met CSV's of één CSV-bestand
    zijn.

    Geeft een dict terug:
      {
        "total":      aantal gecontroleerde objecten,
        "ok":         aantal objecten zonder afwijking,
        "missing":    [ {name, hoofdgroep, file, missing:[fase-labels],
                         expected:[fase-labels]} ]  (verwachte fase ontbreekt),
        "unexpected": [ {name, hoofdgroep, file, extra:[fase-labels]} ]
                      (alleen-B-hoofdgroep met N/V/T gevuld),
      }
    """
    empty = {"total": 0, "ok": 0, "missing": [], "unexpected": []}
    if not src:
        return empty
    if os.path.isdir(src):
        paths = sorted(glob.glob(os.path.join(src, "*.csv")))
    elif os.path.isfile(src):
        paths = [src]
    else:
        return empty

    only_b = {(c or "").strip().upper() for c in only_b_codes}
    total = 0
    ok = 0
    missing: list[dict] = []
    unexpected: list[dict] = []
    for path in paths:
        headers, rows = read_table(path)
        if name_col not in headers:
            continue
        ni = headers.index(name_col)
        hi = headers.index(hoofdgroep_col) if hoofdgroep_col in headers else -1
        # kolomindex per fase-veld (alleen bestaande kolommen)
        fase_idx = {
            fase: [headers.index(c) for c in cols if c in headers]
            for fase, cols in FASE_VELDEN.items()
        }
        code_fn = hoofdgroep_code(path)
        fn = os.path.basename(path)
        for r in rows:
            name = (r[ni] if ni < len(r) else "").strip()
            if not name:
                continue
            total += 1
            code = ((r[hi] if hi >= 0 and hi < len(r) else "").strip()
                    or code_fn).upper()
            expected = ("B",) if code in only_b else FASE_VOLGORDE

            def _has(fase: str) -> bool:
                return any((r[i] if i < len(r) else "").strip()
                           for i in fase_idx.get(fase, ()))

            miss = [f for f in expected if not _has(f)]
            # onverwachte fasen: alleen-B-hoofdgroep met N/V/T ingevuld
            extra = ([f for f in FASE_VOLGORDE
                      if f not in expected and _has(f)]
                     if code in only_b else [])
            if miss:
                missing.append({
                    "name": name, "hoofdgroep": code, "file": fn,
                    "missing": [FASE_LABELS[f] for f in miss],
                    "expected": [FASE_LABELS[f] for f in expected],
                })
            if extra:
                unexpected.append({
                    "name": name, "hoofdgroep": code, "file": fn,
                    "extra": [FASE_LABELS[f] for f in extra],
                })
            if not miss and not extra:
                ok += 1

    missing.sort(key=lambda d: (d["hoofdgroep"], d["name"].casefold()))
    unexpected.sort(key=lambda d: (d["hoofdgroep"], d["name"].casefold()))
    return {"total": total, "ok": ok,
            "missing": missing, "unexpected": unexpected}


def check_duplicate_names(src: str, name_col: str) -> dict:
    """Zoek namen die binnen één hoofdgroep meer dan één keer voorkomen.

    Verzamelt alle waarden van `name_col` over alle CSV's in de map `src` (of het
    losse CSV-bestand) en rapporteert de namen die binnen HETZELFDE bestand
    (= één hoofdgroep) in meer dan één rij voorkomen. Exacte vergelijking (alleen
    omringende spaties worden gestript). Komt overeen met de SPARQL-controle
    `identiekenamen`, die per naam telt hoeveel URI's er binnen dezelfde
    hoofdgroep zijn (GROUP BY ?name ?hoofdNames, HAVING > 1). Dezelfde naam in
    verschillende hoofdgroepen is dus GEEN dubbele naam (bijv. objecten die in
    meerdere constructie-hoofdgroepen voorkomen, of de generieke lijn CONTINUOUS
    die in elk hoofdgroepbestand staat).

    Naamkolom per soort: objecten/lijntypes 'omschrijving', symbolen 'symbool',
    arceringen 'arcering'.

    Geeft terug:
      {
        "total":      aantal (niet-lege) namen,
        "unique":     aantal unieke (bestand, naam)-combinaties,
        "duplicates": [ {name, file, count, rows:[rijnummers]} ]
                      (op bestand + naam gesorteerd),
      }
    """
    def _paths(s):
        if not s:
            return []
        if os.path.isdir(s):
            return sorted(glob.glob(os.path.join(s, "*.csv")))
        if os.path.isfile(s):
            return [s]
        return []

    # (bestand, naam) -> lijst rijnummers
    occ: dict[tuple, list[int]] = {}
    total = 0
    for path in _paths(src):
        headers, rows = read_table(path)
        if name_col not in headers:
            continue
        ni = headers.index(name_col)
        fn = os.path.basename(path)
        for i, r in enumerate(rows):
            name = (r[ni] if ni < len(r) else "").strip()
            if not name:
                continue
            total += 1
            # rij-nummer in het bestand: kopregel = 1, eerste datarij = 2
            occ.setdefault((fn, name), []).append(i + 2)

    duplicates = [
        {"name": name, "file": fn, "count": len(rws), "rows": rws}
        for (fn, name), rws in occ.items() if len(rws) > 1
    ]
    duplicates.sort(key=lambda d: (d["file"], d["name"].casefold()))
    return {"total": total, "unique": len(occ), "duplicates": duplicates}


def check_element_object_link(src: str, name_col: str = "omschrijving",
                              element_col: str = "element",
                              sobject_col: str = "sobject",
                              aobject_col: str = "aobject") -> dict:
    """Controleer de koppeling tussen de `element`-kolom en sobject/aobject.

    De `element`-kolom van de objectentabel bevat `/`-gescheiden tokens
    (G=geometrie, S=symbool, A=arcering). De regel is tweezijdig:
      * bevat `element` het token S, dan moet `sobject` gevuld zijn (en omgekeerd);
      * bevat `element` het token A, dan moet `aobject` gevuld zijn (en omgekeerd).

    `src` mag een MAP met CSV's of één CSV-bestand zijn.

    Geeft een dict terug:
      {
        "total":      aantal gecontroleerde objecten,
        "ok":         aantal objecten zonder afwijking,
        "violations": [ {name, element, file, row, problems:[labels]} ],
      }
    """
    empty = {"total": 0, "ok": 0, "violations": []}
    if not src:
        return empty
    if os.path.isdir(src):
        paths = sorted(glob.glob(os.path.join(src, "*.csv")))
    elif os.path.isfile(src):
        paths = [src]
    else:
        return empty

    total = 0
    ok = 0
    violations: list[dict] = []
    for path in paths:
        headers, rows = read_table(path)
        if name_col not in headers or element_col not in headers:
            continue
        ni = headers.index(name_col)
        ei = headers.index(element_col)
        si = headers.index(sobject_col) if sobject_col in headers else -1
        ai = headers.index(aobject_col) if aobject_col in headers else -1
        fn = os.path.basename(path)
        for i, r in enumerate(rows):
            name = (r[ni] if ni < len(r) else "").strip()
            if not name:
                continue
            total += 1
            element = (r[ei] if ei < len(r) else "").strip()
            tokens = {t.strip().upper() for t in element.split("/") if t.strip()}
            has_s = "S" in tokens
            has_a = "A" in tokens
            so = (r[si] if 0 <= si < len(r) else "").strip()
            ao = (r[ai] if 0 <= ai < len(r) else "").strip()

            problems = []
            if has_s and not so:
                problems.append("element bevat S maar sobject is leeg")
            if not has_s and so:
                problems.append("sobject is ingevuld maar element bevat geen S")
            if has_a and not ao:
                problems.append("element bevat A maar aobject is leeg")
            if not has_a and ao:
                problems.append("aobject is ingevuld maar element bevat geen A")

            if problems:
                violations.append({
                    "name": name, "element": element, "file": fn,
                    "row": i + 2, "problems": problems,
                })
            else:
                ok += 1

    violations.sort(key=lambda d: (d["file"], d["name"].casefold()))
    return {"total": total, "ok": ok, "violations": violations}


def check_arcering_verklaring(src: str, name_col: str = "arcering",
                              verklaring_col: str = "vrkl_lang") -> dict:
    """Controleer of elke arcering een (lange) verklaring heeft.

    De arceringentabel bevat een kolom `vrkl_lang` (verklaring lang) die de
    tekst voor de legenda/verklaring bevat. Elke arcering moet die gevuld
    hebben; regels met een lege `vrkl_lang` worden gemeld.

    `src` mag een MAP met CSV's of één CSV-bestand zijn.

    Geeft een dict terug:
      {
        "total":   aantal gecontroleerde arceringen,
        "ok":      aantal met een gevulde verklaring,
        "missing": [ {name, file, row} ],   # zonder verklaring
      }
    """
    empty = {"total": 0, "ok": 0, "missing": []}
    if not src:
        return empty
    if os.path.isdir(src):
        paths = sorted(glob.glob(os.path.join(src, "*.csv")))
    elif os.path.isfile(src):
        paths = [src]
    else:
        return empty

    total = 0
    ok = 0
    missing: list[dict] = []
    for path in paths:
        headers, rows = read_table(path)
        if name_col not in headers or verklaring_col not in headers:
            continue
        ni = headers.index(name_col)
        vi = headers.index(verklaring_col)
        fn = os.path.basename(path)
        for i, r in enumerate(rows):
            name = (r[ni] if ni < len(r) else "").strip()
            if not name:
                continue
            total += 1
            vl = (r[vi] if vi < len(r) else "").strip()
            if vl:
                ok += 1
            else:
                missing.append({"name": name, "file": fn, "row": i + 2})

    missing.sort(key=lambda d: (d["file"], d["name"].casefold()))
    return {"total": total, "ok": ok, "missing": missing}


def check_lijntype_autocaddef(src: str, name_col: str = "omschrijving",
                              def_col: str = "autocaddef",
                              exclude_names=()) -> dict:
    """Controleer of elk lijntype een AutoCAD-definitie heeft.

    De lijntypetabel bevat een kolom `autocaddef` met de AutoCAD-definitiestring
    (bijv. `A,4,-.8,.8,-.8`). Elk lijntype moet die gevuld hebben; regels met
    een lege `autocaddef` worden gemeld.

    `exclude_names` : namen die worden overgeslagen — de generieke lijnen
    CONTINUOUS/V-CONTINUOUS-SO komen uit een andere publicatie en hebben bewust
    geen definitiestring (CONTINUOUS is een ingebouwde AutoCAD-lijn).

    `src` mag een MAP met CSV's of één CSV-bestand zijn.

    Geeft een dict terug:
      {
        "total":   aantal gecontroleerde lijntypes (exclusief overgeslagen),
        "ok":      aantal met een gevulde autocaddef,
        "missing": [ {name, file, row} ],   # zonder autocaddef
      }
    """
    empty = {"total": 0, "ok": 0, "missing": []}
    if not src:
        return empty
    if os.path.isdir(src):
        paths = sorted(glob.glob(os.path.join(src, "*.csv")))
    elif os.path.isfile(src):
        paths = [src]
    else:
        return empty

    skip = {(n or "").strip().upper() for n in exclude_names}
    total = 0
    ok = 0
    missing: list[dict] = []
    for path in paths:
        headers, rows = read_table(path)
        if name_col not in headers or def_col not in headers:
            continue
        ni = headers.index(name_col)
        di = headers.index(def_col)
        fn = os.path.basename(path)
        for i, r in enumerate(rows):
            name = (r[ni] if ni < len(r) else "").strip()
            if not name or name.upper() in skip:
                continue
            total += 1
            ad = (r[di] if di < len(r) else "").strip()
            if ad:
                ok += 1
            else:
                missing.append({"name": name, "file": fn, "row": i + 2})

    missing.sort(key=lambda d: (d["file"], d["name"].casefold()))
    return {"total": total, "ok": ok, "missing": missing}


def bib_of_stem(stem: str, known_bibs) -> str:
    """De bibliotheek-code die als los hyphen-segment in een bestands-/symboolnaam
    staat. Symboolnamen kunnen een prefix hebben (bijv. 'V-SFC-PAAL...', 'B-SGC-…'),
    dus het EERSTE naam-segment is geen betrouwbare bibliotheek. We zoeken welke
    bekende bibliotheek (uit de `sbibliotheek`-kolom, bijv. SFC/SGC/SAM) als segment
    in de naam voorkomt; het eerste passende segment wint. Geeft "" als geen enkele
    bekende bibliotheek in de naam zit (dan hoort het .dwg-bestand niet bij een
    verwerkte hoofdgroep)."""
    if not stem or not known_bibs:
        return ""
    known = {b.upper() for b in known_bibs if b}
    for seg in stem.upper().split("-"):
        if seg in known:
            return seg
    return ""


def check_dwg_symbols(sym_src: str, dwg_dir: str, name_col: str = "symbool",
                      bib_col: str = "sbibliotheek") -> dict:
    """Controleer de koppeling tussen symbooltabelregels en .dwg-bestanden, TWEE
    kanten op:
      - regel zonder bestand: elke symbooltabelregel moet een <symbool>.dwg in de
        .dwg-map hebben (recursief);
      - bestand zonder regel (wees): elk .dwg-bestand van een VERWERKTE bibliotheek
        moet een tabelregel hebben.

    De wees-detectie is gescoped op de bibliotheken die daadwerkelijk in de
    symbolentabellen voorkomen (kolom `sbibliotheek`): de .dwg-map bevat álle
    bibliotheken, dus een .dwg van een niet-verwerkte bibliotheek is géén wees.
    Bib per .dwg wordt prefix-proof bepaald via `bib_of_stem` (V-/B-voorvoegsels).

    `sym_src` mag een MAP met symbolen-CSV's of één CSV zijn; `dwg_dir` is de map
    met .dwg-bestanden (recursief doorzocht).

    Geeft een dict terug:
      {
        "total":    aantal gecontroleerde tabelregels,
        "ok":       aantal regels met een .dwg-bestand,
        "missing":  [ {name, file, hoofdgroep} ],  # regel zonder .dwg
        "orphans":  [ {name, file, hoofdgroep} ],  # .dwg zonder regel
        "dwg_count": aantal .dwg-bestanden in de map,
        "bibs":     gesorteerde lijst verwerkte bibliotheken,
      }
    Als er geen symbolenbron of geen .dwg-map is, wordt None teruggegeven (de
    controle is dan niet van toepassing/overgeslagen)."""
    if not sym_src or not dwg_dir or not os.path.isdir(dwg_dir):
        return None
    if os.path.isdir(sym_src):
        paths = sorted(glob.glob(os.path.join(sym_src, "*.csv")))
    elif os.path.isfile(sym_src):
        paths = [sym_src]
    else:
        return None

    dwg_map = dwg_index(dwg_dir)          # {stem.lower(): relpad}
    all_symbols: set = set()
    processed_bibs: set = set()
    missing: list[dict] = []
    total = 0
    ok = 0
    have_names = False
    for path in paths:
        headers, rows = read_table(path)
        if name_col not in headers:
            continue
        have_names = True
        ni = headers.index(name_col)
        bi = headers.index(bib_col) if bib_col in headers else -1
        fn = os.path.basename(path)
        code = hoofdgroep_code(path)
        for r in rows:
            nm = (r[ni] if ni < len(r) else "").strip()
            if not nm:
                continue
            total += 1
            all_symbols.add(nm.lower())
            if bi >= 0:
                sb = (r[bi] if bi < len(r) else "").strip().upper()
                if sb:
                    processed_bibs.add(sb)
            if nm.lower() in dwg_map:
                ok += 1
            else:
                missing.append({"name": nm, "file": fn, "hoofdgroep": code})
    if not have_names:
        return None

    orphans = [
        {"name": stem, "file": dwg_map[stem],
         "hoofdgroep": sbib_to_code(bib_of_stem(stem, processed_bibs))}
        for stem in dwg_map
        if bib_of_stem(stem, processed_bibs) and stem not in all_symbols
    ]
    missing.sort(key=lambda d: (d["hoofdgroep"], d["name"].casefold()))
    orphans.sort(key=lambda d: (d["hoofdgroep"], d["name"].casefold()))
    return {"total": total, "ok": ok, "missing": missing, "orphans": orphans,
            "dwg_count": len(dwg_map), "bibs": sorted(processed_bibs)}


def _sort_key(row: list[str]) -> str:
    return (row[SORT_COLUMN] if len(row) > SORT_COLUMN else "").casefold()


def compare(new_path: str, old_path: str, key: str = KEY,
            scope_col: str = "", blank_spec: dict = None,
            suppress_change: dict = None) -> dict:
    """Vergelijk twee CSV-versies en geef een resultaat-dict terug.

    Parameters:
      key        : kolom waarop rijen gematcht worden (standaard 'objectURI'; voor
                   symbolentabellen bijv. 'symboolURI').
      scope_col  : optioneel. Als de oude CSV meer bevat dan de nieuwe (bijv. één
                   grote symbolen-CSV voor alle bibliotheken), beperk de oude rijen
                   dan tot de waarden van deze kolom die ook in de nieuwe versie
                   voorkomen (bijv. 'sbibliotheek'). Zo blijven 'vervallen' rijen
                   beperkt tot dezelfde bibliotheek/hoofdgroep.
      blank_spec : optioneel. Maakt bepaalde kolommen leeg (aan BEIDE kanten) voor
                   rijen die uit een andere publicatie komen, zodat die kolommen
                   niet als 'wijziging' tellen. Vorm:
                   {"match_col": <kolom>, "values": {<waarde>, ...},
                    "columns": [<kolom>, ...]}. Voor lijntypes: de generieke lijnen
                   'CONTINUOUS' en 'V-CONTINUOUS-SO' (uit een andere publicatie)
                   met blanco fase/optie/autocaddef.
      suppress_change : optioneel {"match_col": <kolom>, "values": {<waarde>, ...}}.
                   Rijen waarvan `match_col` in `values` zit tonen in de changelog
                   NOOIT wijzigingen: geen enkele cel wordt als gewijzigd
                   gemarkeerd, de rij krijgt status 'same' (nooit 'nieuw'/groen) en
                   ze verschijnen niet in de vervallen-lijst. Voor lijntypes: de
                   generieke lijnen 'CONTINUOUS'/'V-CONTINUOUS-SO' — die willen we
                   in de changelog helemaal niet als wijziging zien.

    Keys in het resultaat:
      headers       : koppen van de nieuwe versie (bepalen de kolomindeling)
      rows          : lijst dicts {status, id, cells:[{value, changed, old}]}
                      alfabetisch gesorteerd op de eerste kolom
      deleted       : lijst rijen (lijst strings in nieuwe-kolomindeling),
                      alfabetisch gesorteerd op de eerste kolom
      stats         : {new, changed, deleted, total_new}
    """
    new_headers, new_rows = read_table(new_path)
    if not old_path or not os.path.isfile(old_path):
        # Geen vorige versie beschikbaar (deze hoofdgroep bestond nog niet):
        # lege oude kant, zodat elke nieuwe rij als 'nieuw' telt en er een
        # changelog met alleen nieuwe (groene) regels uitkomt.
        old_headers, old_rows = list(new_headers), []
    else:
        old_headers, old_rows = read_table(old_path)

    nidx = {h: i for i, h in enumerate(new_headers)}
    oidx = {h: i for i, h in enumerate(old_headers)}
    if key not in nidx:
        raise ValueError(f"Kolom '{key}' ontbreekt in {os.path.basename(new_path)}")
    if key not in oidx:
        raise ValueError(f"Kolom '{key}' ontbreekt in {os.path.basename(old_path)}")

    # Andere-publicatie-rijen: bepaalde kolommen aan BEIDE kanten leegmaken zodat
    # ze niet als wijziging tellen (bijv. lijntypes CONTINUOUS/V-CONTINUOUS-SO met
    # blanco fase/optie/autocaddef). Match op de waarde in 'match_col'.
    if blank_spec:
        mcol = blank_spec.get("match_col", "")
        vals = {(v or "").strip().upper() for v in blank_spec.get("values", [])}
        cols = blank_spec.get("columns", [])

        def _blank(rows, idx):
            if not mcol or mcol not in idx:
                return
            mi = idx[mcol]
            cis = [idx[c] for c in cols if c in idx]
            for r in rows:
                if mi < len(r) and r[mi].strip().upper() in vals:
                    for ci in cis:
                        if ci < len(r):
                            r[ci] = ""

        _blank(new_rows, nidx)
        _blank(old_rows, oidx)

    # Scope: beperk de oude rijen tot de bibliotheken/waarden die ook in de
    # nieuwe versie voorkomen (voor de grote gedeelde symbolen-/lijntypes-CSV).
    # Heeft de nieuwe versie ook rijen met een LEGE scope-waarde (bijv. generieke
    # lijntypes als CONTINUOUS zonder hoofdgroep), dan tellen de oude lege-scope-
    # rijen ook mee, zodat die matchen i.p.v. onterecht 'nieuw' te lijken.
    if scope_col and scope_col in nidx and scope_col in oidx:
        allowed = {r[nidx[scope_col]].strip() for r in new_rows
                   if r[nidx[scope_col]].strip()}
        allow_empty = any(not r[nidx[scope_col]].strip() for r in new_rows)
        old_rows = [r for r in old_rows
                    if r[oidx[scope_col]].strip() in allowed
                    or (allow_empty and not r[oidx[scope_col]].strip())]

    # Rijen waarvoor GEEN wijzigingen getoond mogen worden (changelog): match op
    # een kolomwaarde (bijv. omschrijving = CONTINUOUS/V-CONTINUOUS-SO).
    sup = suppress_change or {}
    sup_col = sup.get("match_col", "")
    sup_vals = {(v or "").strip().upper() for v in sup.get("values", [])}
    sup_ni = nidx.get(sup_col, -1) if sup_col and sup_col in nidx else -1
    sup_oi = oidx.get(sup_col, -1) if sup_col and sup_col in oidx else -1

    # Oude rijen op id (eerste voorkomen wint).
    old_by_id: dict[str, list[str]] = {}
    for r in old_rows:
        rid = r[oidx[key]].strip()
        if rid:
            old_by_id.setdefault(rid, r)

    new_sorted = sorted(new_rows, key=_sort_key)

    rows_out = []
    matched: set[str] = set()
    for r in new_sorted:
        rid = r[nidx[key]].strip()
        old = old_by_id.get(rid)
        is_new = old is None
        if not is_new:
            matched.add(rid)

        # Onderdruk wijzigingen voor deze rij? (generieke lijntypes)
        suppressed = (sup_ni >= 0 and sup_ni < len(r)
                      and r[sup_ni].strip().upper() in sup_vals)

        cells = []
        changed_any = False
        for h in new_headers:
            value = r[nidx[h]]
            changed = False
            old_value = None
            if not is_new and not suppressed and h != key and h in oidx:
                ov = old[oidx[h]]
                if value.strip() != ov.strip():
                    changed = True
                    changed_any = True
                    old_value = ov
            cells.append({"value": value, "changed": changed, "old": old_value})

        if suppressed:
            status = "same"
        else:
            status = "new" if is_new else ("changed" if changed_any else "same")
        rows_out.append({"status": status, "id": rid, "cells": cells})

    # Vervallen rijen: id wel in oud, niet gematcht. In nieuwe-kolomindeling zetten.
    # Onderdrukte rijen (generieke lijntypes) tellen nooit als vervallen.
    deleted_rows = [r for r in old_rows
                    if r[oidx[key]].strip() and r[oidx[key]].strip() not in matched
                    and not (sup_oi >= 0 and sup_oi < len(r)
                             and r[sup_oi].strip().upper() in sup_vals)]
    deleted_rows.sort(key=_sort_key)
    deleted_out = []
    for r in deleted_rows:
        deleted_out.append([r[oidx[h]] if h in oidx else "" for h in new_headers])

    stats = {
        "new": sum(1 for x in rows_out if x["status"] == "new"),
        "changed": sum(1 for x in rows_out if x["status"] == "changed"),
        "deleted": len(deleted_out),
        "total_new": len(new_rows),
    }
    return {
        "headers": new_headers,
        "rows": rows_out,
        "deleted": deleted_out,
        "stats": stats,
    }


def _main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Vergelijk twee objectentabel-CSV's.")
    parser.add_argument("new", help="pad naar de nieuwe CSV")
    parser.add_argument("old", help="pad naar de oude CSV")
    args = parser.parse_args()
    result = compare(args.new, args.old)
    s = result["stats"]
    print(f"kolommen: {len(result['headers'])}")
    print(f"nieuw: {s['new']} | gewijzigd: {s['changed']} | "
          f"vervallen: {s['deleted']} | totaal nieuw: {s['total_new']}")


if __name__ == "__main__":
    _main()
