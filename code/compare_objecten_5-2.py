"""
Vergelijk NLCS 5.0 vs 5.2 objecttabel voor EEN hoofdgroep (stuk voor stuk).
Zet de gewenste hoofdgroep in CODE hieronder (bv. "BV") en draai het script.

Output: ontwikkeling/heroverweging-5-2/{CODE}/objecten-vergelijking-{CODE}.html

De HTML toont de volledige 5.2-tabel, alfabetisch gesorteerd op de eerste kolom
(omschrijving), waarbij:
  - nieuwe rijen (id_nummer niet in 5.0)             -> groene rij
  - in bestaande rijen een veranderde cel            -> blauwe cel met "5.0: x / 5.2: y"
  - onderaan een aparte tabel met verdwenen rijen    -> id_nummer wel in 5.0, niet in 5.2

Nieuw/verdwenen wordt bepaald op basis van id_nummer.

Referentie (5.0): bij voorkeur de volledige export NLCS-OBJECTEN-{CODE}-5.0.csv
(puntkomma-gescheiden, met SYMBOOL/ARCERING e.d.); valt anders terug op de
verkorte 5.02-tabel. De 5.0-kolomnamen worden via HEADER_MAP omgezet naar de
5.2-namen, zodat ook kolommen als sobject (SYMBOOL) en aobject (ARCERING)
vergeleken worden. Cellen worden vergeleken voor alle kolommen die na die
omzetting in BEIDE bestanden voorkomen.
"""
import csv
import io
import os
import glob
import html as html_module

# --- Instellingen: pas CODE aan om de volgende hoofdgroep te doen -----------
CODE = "BV"

BASE_52 = r"tabellen\publicatie\objectentabellen"
# Volledige 5.0-export per hoofdgroep (voorkeursreferentie). {CODE} wordt ingevuld.
OLD_FILE = os.path.join(os.path.expanduser("~"), "Downloads", "NLCS-OBJECTEN-{CODE}-5.0.csv")
# Terugval: verkorte 5.02-tabellen als de export hierboven niet bestaat.
BASE_50 = r"C:\Users\100289\OneDrive - CROW\Documents\GitHub\NLCSmain\NLCS\tabellen\publicatie\objectentabellen-verkort"
OUTPUT_DIR = r"ontwikkeling\heroverweging-5-2"
OLD_LABEL = "5.0"

# id_nummer hoort nooit als "gewijzigde cel" gemarkeerd te worden (het is de sleutel).
SKIP_COMPARE = {"id_nummer"}

# Kolomnamen in de 5.0-export -> kolomnamen in 5.2. Niet-gemapte koppen blijven
# ongewijzigd (en matchen dan simpelweg niet met een 5.2-kolom). Koppen die al
# 5.2-stijl zijn (verkorte 5.02-tabel) staan niet in de map en blijven dus heel.
HEADER_MAP = {
    "OMSCHRIJVING": "omschrijving", "STATUS": "status", "DISCIPLINE": "discipline",
    "HOOFDGROEP": "hoofdgroep", "OBJECT": "object",
    "SUBOBJECT01": "subobject01", "SUBOBJECT02": "subobject02", "SUBOBJECT03": "subobject03",
    "SUBOBJECT04": "subobject04", "SUBOBJECT05": "subobject05",
    "BEWERKING": "bewerking", "ELEMENT": "element", "SCHAAL": "schaal",
    "ARCERING": "aobject", "SYMBOOL": "sobject", "LAAGNAAM": "laagnaam",
    "B lineweight": "lw_b", "B color": "kl_b", "B color A": "kl_b_a", "B color GD": "kl_b_gd",
    "B color GN": "kl_b_gn", "B color V": "kl_b_v", "B linetype": "lt_b",
    "N lineweight": "lw_n", "N color": "kl_n", "N color A": "kl_n_a", "N color GD": "kl_n_gd",
    "N color GN": "kl_n_gn", "N color V": "kl_n_v", "N linetype": "lt_n",
    "V lineweight": "lw_v", "V color": "kl_v", "V color A": "kl_v_a", "V color GD": "kl_v_gd",
    "V color GN": "kl_v_gn", "V color V": "kl_v_v", "V linetype": "lt_v",
    "T lineweight": "lw_t", "T color": "kl_t", "T color A": "kl_t_a", "T color GD": "kl_t_gd",
    "T color GN": "kl_t_gn", "T color V": "kl_t_v", "T linetype": "lt_t",
    "VRKL_kort": "vrkl_kort", "VRKL_lang": "vrkl_lang", "ID": "id_nummer", "KIND_VAN": "kind_van",
}


def parse_50_csv(filepath):
    """Parse 5.02 dubbel-gequote CSV (elke regel staat tussen "..."), ook
    semicolon-gescheiden wordt afgehandeld."""
    with open(filepath, "r", encoding="utf-8-sig") as f:
        raw_lines = f.readlines()

    headers, rows = [], []
    first_line = raw_lines[0].strip() if raw_lines else ""
    if ";" in first_line and not first_line.startswith('"'):
        for i, line in enumerate(raw_lines):
            line = line.strip()
            if not line:
                continue
            parts = line.split(";")
            if i == 0:
                headers = [h.strip().strip('"') for h in parts]
            else:
                rows.append([p.strip().strip('"') for p in parts])
    else:
        for i, line in enumerate(raw_lines):
            line = line.strip()
            if not line:
                continue
            if line.startswith('"') and line.endswith('"'):
                line = line[1:-1]
            line = line.replace('""', '"')
            reader = csv.reader(io.StringIO(line))
            for row in reader:
                if i == 0:
                    headers = [h.strip() for h in row]
                else:
                    rows.append(row)
                break
    return headers, rows


def parse_52_csv(filepath):
    """Parse 5.2 (gewone komma-gescheiden CSV)."""
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = [h.strip() for h in next(reader)]
        rows = list(reader)
    return headers, rows


def cell(val):
    return html_module.escape(val) if val else "<em>(leeg)</em>"


def check_field_count(label, headers, rows):
    """Waarschuw bij rijen die niet evenveel velden hebben als de kop.
    Zo'n rij heeft meestal een komma te veel/te weinig, waardoor kolommen
    (zoals id_nummer) verschuiven en een rij ten onrechte als nieuw of
    verdwenen wordt gezien. Geeft het aantal probleemrijen terug."""
    expected = len(headers)
    bad = []
    for i, r in enumerate(rows):
        if len(r) != expected:
            naam = r[0].strip() if r else ""
            bad.append((i + 2, len(r), naam))  # +2: kop is regel 1, data start regel 2
    if bad:
        print(f"  LET OP: {len(bad)} rij(en) in {label} hebben niet {expected} velden:")
        for lineno, n, naam in bad:
            print(f"    regel {lineno}: {n} velden (verwacht {expected})  {naam}")
    return len(bad)


def first_index(headers):
    """Kolomnaam -> eerste kolomindex. Bij dubbele koppen (de 5.0-export heeft
    bv. twee keer STATUS) wint zo de EERSTE kolom; de tweede STATUS is de
    wijzigingsstatus en hoort niet met 5.2 'status' vergeleken te worden."""
    idx = {}
    for i, h in enumerate(headers):
        idx.setdefault(h, i)
    return idx


def generate_html(title, headers_52, rows_52, lookup_50, headers_50, common_cols, id_column):
    idx_52 = first_index(headers_52)
    idx_50 = first_index(headers_50)
    id_i_52 = idx_52.get(id_column)
    id_i_50 = idx_50.get(id_column)

    # alfabetisch op eerste kolom
    rows_52 = sorted(rows_52, key=lambda r: (r[0].strip().lower() if r else ""))

    change_count = new_count = removed_count = 0
    matched_ids = set()

    out = [f"""<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="utf-8">
<title>{html_module.escape(title)}</title>
<style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    h1, h2 {{ color: #333; }}
    .legend {{ margin: 10px 0 16px 0; }}
    .legend span {{ padding: 4px 12px; margin-right: 10px; border-radius: 3px; font-size: 14px; border: 1px solid #bbb; }}
    .changed {{ background-color: #cfe2ff; }}
    .new-row {{ background-color: #d4edda; }}
    .removed {{ background-color: #f8d7da; }}
    .stats {{ margin: 10px 0; font-size: 14px; color: #555; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 12px; margin-bottom: 30px; }}
    th, td {{ border: 1px solid #ccc; padding: 5px 7px; text-align: left; vertical-align: top; }}
    th {{ background: #f0f0f0; position: sticky; top: 0; z-index: 1; }}
    td.changed {{ white-space: nowrap; }}
    .old {{ color: #666; }}
    tr:hover td {{ background-color: #f5f5f5; }}
    tr.new-row:hover td {{ background-color: #c3e6cb; }}
</style>
</head>
<body>
<h1>{html_module.escape(title)}</h1>
<div class="legend">
    <span class="new-row">Nieuw in 5.2</span>
    <span class="changed">Gewijzigde cel ({OLD_LABEL} &rarr; 5.2)</span>
    <span class="removed">Verdwenen in 5.2</span>
</div>
<!--STATS-->
"""]

    # --- Hoofdtabel: de 5.2-tabel ---
    out.append("<table>\n<thead><tr>")
    out += [f"<th>{html_module.escape(h)}</th>" for h in headers_52]
    out.append("</tr></thead>\n<tbody>\n")

    for row in rows_52:
        row_id = row[id_i_52].strip() if id_i_52 is not None and id_i_52 < len(row) else ""
        old_row = lookup_50.get(row_id)

        cells = []
        is_new = old_row is None
        if not is_new:
            matched_ids.add(row_id)
        for h in headers_52:
            ci = idx_52.get(h)
            v = row[ci].strip() if ci is not None and ci < len(row) else ""
            comparable = (not is_new) and h in common_cols and h not in SKIP_COMPARE
            if comparable:
                ov = old_row[idx_50[h]].strip() if idx_50[h] < len(old_row) else ""
                if ov != v:
                    change_count += 1
                    cells.append(
                        f'<td class="changed" title="{OLD_LABEL}: {html_module.escape(ov)}">'
                        f'<span class="old">{OLD_LABEL}: {cell(ov)}</span><br>5.2: {cell(v)}</td>'
                    )
                    continue
            cells.append(f"<td>{html_module.escape(v)}</td>")

        if is_new:
            new_count += 1
            out.append('<tr class="new-row">' + "".join(cells) + "</tr>\n")
        else:
            out.append("<tr>" + "".join(cells) + "</tr>\n")

    out.append("</tbody>\n</table>\n")

    # --- Aparte tabel onderaan: verdwenen rijen (wel in 5.02, niet in 5.2) ---
    removed = [r for r in lookup_50.values()
               if (r[id_i_50].strip() if id_i_50 is not None and id_i_50 < len(r) else "") not in matched_ids]
    removed.sort(key=lambda r: (r[idx_50["omschrijving"]].strip().lower() if "omschrijving" in idx_50 else ""))
    removed_count = len(removed)

    out.append(f"<h2>Verdwenen in 5.2 ({removed_count})</h2>\n")
    if removed:
        out.append('<table class="removed">\n<thead><tr>')
        out += [f"<th>{html_module.escape(h)}</th>" for h in headers_50]
        out.append("</tr></thead>\n<tbody>\n")
        for r in removed:
            cells = [f"<td>{html_module.escape(r[i].strip() if i < len(r) else '')}</td>"
                     for i in range(len(headers_50))]
            out.append('<tr class="removed">' + "".join(cells) + "</tr>\n")
        out.append("</tbody>\n</table>\n")
    else:
        out.append("<p>Geen.</p>\n")

    stats = f"Gewijzigde cellen: {change_count} | Nieuwe rijen: {new_count} | Verdwenen rijen: {removed_count}"
    out.append("\n</body>\n</html>")
    full = "".join(out).replace("<!--STATS-->", f'<div class="stats">{stats}</div>')
    return full, change_count, new_count, removed_count


def main():
    f52 = os.path.join(BASE_52, f"objecten-concept-5.2-{CODE}.csv")
    if not os.path.exists(f52):
        raise SystemExit(f"5.2-bestand niet gevonden: {f52}")
    headers_52, rows_52 = parse_52_csv(f52)
    check_field_count(f"5.2-{CODE}", headers_52, rows_52)

    # Referentie kiezen: eerst de volledige 5.0-export, anders de verkorte 5.02-tabel.
    old_path = OLD_FILE.format(CODE=CODE)
    if not os.path.exists(old_path):
        matches_50 = glob.glob(os.path.join(BASE_50, f"5.02-Objectentabel-{CODE}-*.csv"))
        if not matches_50:
            raise SystemExit(
                f"Geen 5.0-referentie gevonden: noch {old_path}, noch "
                f"5.02-Objectentabel-{CODE}-*.csv in {BASE_50}"
            )
        old_path = matches_50[0]
    print(f"Referentie 5.0: {old_path}")
    headers_50, rows_50 = parse_50_csv(old_path)
    # 5.0-kolomnamen omzetten naar 5.2-namen (verkorte 5.02-koppen blijven heel).
    headers_50 = [HEADER_MAP.get(h, h) for h in headers_50]
    check_field_count(f"5.0-{CODE}", headers_50, rows_50)

    common_cols = set(headers_52) & set(headers_50)
    id_i_50 = headers_50.index("id_nummer") if "id_nummer" in headers_50 else None
    lookup_50 = {}
    if id_i_50 is not None:
        for r in rows_50:
            rid = r[id_i_50].strip() if id_i_50 < len(r) else ""
            if rid:
                lookup_50[rid] = r

    title = f"Objecten vergelijking {OLD_LABEL} vs 5.2 - {CODE}"
    html_content, changes, new, removed = generate_html(
        title, headers_52, rows_52, lookup_50, headers_50, common_cols, "id_nummer"
    )

    out_dir = os.path.join(OUTPUT_DIR, CODE)
    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, f"objecten-vergelijking-{CODE}.html")
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"{filepath}: {changes} gewijzigde cellen, {new} nieuwe rijen, {removed} verdwenen rijen")


if __name__ == "__main__":
    main()
