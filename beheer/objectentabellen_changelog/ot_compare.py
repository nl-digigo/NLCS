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


def zoekfilter_map(names, terms) -> dict:
    """Bepaal per symboolnaam de zoekfilter-term waarmee het symbool gevonden
    wordt: de langste `terms`-waarde die een voorvoegsel is van de symboolnaam.

    Parameters:
      names : iterable van symboolnamen (bijv. 'SAM-ASPUNTNUMMER-SO')
      terms : iterable van zoekfilter-termen (de `sobject`-kolom uit de
              objectentabel, bijv. 'SAM-AS', 'SAM-ASPUNTNUMMER')

    Geeft {stem.lower(): term} (lege string als geen enkele term past).
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
        out[key] = ""
        for t in terms_sorted:
            if s == t or s.startswith(t):
                out[key] = t
                break
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


def _sort_key(row: list[str]) -> str:
    return (row[SORT_COLUMN] if len(row) > SORT_COLUMN else "").casefold()


def compare(new_path: str, old_path: str, key: str = KEY,
            scope_col: str = "", blank_spec: dict = None) -> dict:
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

        cells = []
        changed_any = False
        for h in new_headers:
            value = r[nidx[h]]
            changed = False
            old_value = None
            if not is_new and h != key and h in oidx:
                ov = old[oidx[h]]
                if value.strip() != ov.strip():
                    changed = True
                    changed_any = True
                    old_value = ov
            cells.append({"value": value, "changed": changed, "old": old_value})

        status = "new" if is_new else ("changed" if changed_any else "same")
        rows_out.append({"status": status, "id": rid, "cells": cells})

    # Vervallen rijen: id wel in oud, niet gematcht. In nieuwe-kolomindeling zetten.
    deleted_rows = [r for r in old_rows
                    if r[oidx[key]].strip() and r[oidx[key]].strip() not in matched]
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
