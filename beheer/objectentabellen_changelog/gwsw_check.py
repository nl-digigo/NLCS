"""gwsw_check.py - controleer of de GWSW-URI's in een mapping-/tabel-CSV bestaan
in een GWSW-ontologie (TTL, bv. het 'Totaal'-model van een release).

Werkt voor ELKE CSV die naar GWSW-URI's verwijst: alle cellen met
'data.gwsw.nl' worden automatisch als GWSW-URI herkend (ongeacht de kolom).
Match op de volledige URI. Schrijft een Excel met per unieke URI of hij bestaat.
"""
import logging
import os

import ot_compare

GWSW_HOST = "data.gwsw.nl"


def load_gwsw_concepts(ttl_path):
    """Verzameling GWSW-concept-URI's (subjecten met 'data.gwsw.nl') uit de TTL."""
    logging.disable(logging.CRITICAL)          # rdflib-waarschuwingen dempen
    try:
        from rdflib import Graph, URIRef
        g = Graph()
        g.parse(ttl_path, format="turtle")
        return {str(s) for s in set(g.subjects())
                if isinstance(s, URIRef) and GWSW_HOST in str(s)}, len(g)
    finally:
        logging.disable(logging.NOTSET)


def gwsw_uris_in_csv(csv_path):
    """{uri: {'cols': set, 'count': n}} voor alle cellen met een GWSW-URI."""
    headers, rows = ot_compare.read_mapping(csv_path)   # scheidingsteken-sniffing
    occ = {}
    for row in rows:
        for ci, h in enumerate(headers):
            v = (row[ci] if ci < len(row) else "").strip()
            if GWSW_HOST in v:
                e = occ.setdefault(v, {"cols": set(), "count": 0})
                e["cols"].add(h)
                e["count"] += 1
    return occ


def check(csv_path, ttl_path):
    """Geeft (resultaatlijst, aantal_concepten, aantal_triples). Resultaat =
    lijst dicts {uri, localname, exists, cols, count}, ontbrekende eerst."""
    concepts, n_triples = load_gwsw_concepts(ttl_path)
    occ = gwsw_uris_in_csv(csv_path)
    out = []
    for uri, e in occ.items():
        out.append({"uri": uri,
                    "localname": uri.rsplit("/", 1)[-1],
                    "exists": uri in concepts,
                    "cols": ", ".join(sorted(e["cols"])),
                    "count": e["count"]})
    out.sort(key=lambda r: (r["exists"], r["localname"].casefold()))  # ontbrekend eerst
    return out, len(concepts), n_triples


def write_excel(result, out_path, titel=""):
    """Schrijf de checkresultaten als Excel (alle cellen tekst)."""
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.utils import get_column_letter
    wb = Workbook()
    ws = wb.active
    ws.title = "gwsw-uri-check"
    cols = ["GWSW-URI", "concept", "bestaat in ontologie", "kolom(men)", "aantal regels"]
    ws.append(cols)
    for c in ws[1]:
        c.font = Font(bold=True)
    rood = PatternFill(fgColor="F4CCCC", fill_type="solid")
    for r in result:
        ws.append([r["uri"], r["localname"], "ja" if r["exists"] else "NEE",
                   r["cols"], str(r["count"])])
        if not r["exists"]:
            for c in ws[ws.max_row]:
                c.fill = rood
    for row in ws.iter_rows():
        for c in row:
            c.number_format = "@"
    widths = [52, 34, 20, 26, 14]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[get_column_letter(i)].width = w
    ws.freeze_panes = "A2"
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    wb.save(out_path)
    return out_path
