"""
Vergelijk NLCS 5.02 vs 5.2 objecttabel voor EEN hoofdgroep (stuk voor stuk).
Zet de gewenste hoofdgroep in CODE hieronder (bv. "BV") en draai het script.

Output: ontwikkeling/heroverweging-5-2/{CODE}/objecten-vergelijking-{CODE}.html

De HTML toont de volledige 5.2-tabel, alfabetisch gesorteerd op de eerste kolom
(omschrijving), waarbij:
  - nieuwe rijen (id_nummer niet in 5.02)            -> groene rij
  - in bestaande rijen een veranderde cel            -> blauwe cel met "5.02: x / 5.2: y"
  - onderaan een aparte tabel met verdwenen rijen    -> id_nummer wel in 5.02, niet in 5.2

Nieuw/verdwenen wordt bepaald op basis van id_nummer.
Cellen worden alleen vergeleken voor kolommen die in BEIDE bestanden voorkomen
(zelfde kolomnaam).
"""
import csv
import io
import os
import glob
import html as html_module

# --- Instellingen: pas CODE aan om de volgende hoofdgroep te doen -----------
CODE = "BV"

BASE_52 = r"tabellen\publicatie\objectentabellen"
BASE_50 = r"C:\Users\100289\OneDrive - CROW\Documents\GitHub\NLCSmain\NLCS\tabellen\publicatie\objectentabellen-verkort"
OUTPUT_DIR = r"ontwikkeling\heroverweging-5-2"

# id_nummer hoort nooit als "gewijzigde cel" gemarkeerd te worden (het is de sleutel).
SKIP_COMPARE = {"id_nummer"}


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


def generate_html(title, headers_52, rows_52, lookup_50, headers_50, common_cols, id_column):
    idx_52 = {h: i for i, h in enumerate(headers_52)}
    idx_50 = {h: i for i, h in enumerate(headers_50)}
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
    <span class="changed">Gewijzigde cel (5.02 &rarr; 5.2)</span>
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
                        f'<td class="changed" title="5.02: {html_module.escape(ov)}">'
                        f'<span class="old">5.02: {cell(ov)}</span><br>5.2: {cell(v)}</td>'
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

    matches_50 = glob.glob(os.path.join(BASE_50, f"5.02-Objectentabel-{CODE}-*.csv"))
    if not matches_50:
        raise SystemExit(f"5.02-bestand niet gevonden voor {CODE} in {BASE_50}")
    headers_50, rows_50 = parse_50_csv(matches_50[0])

    common_cols = set(headers_52) & set(headers_50)
    id_i_50 = headers_50.index("id_nummer") if "id_nummer" in headers_50 else None
    lookup_50 = {}
    if id_i_50 is not None:
        for r in rows_50:
            rid = r[id_i_50].strip() if id_i_50 < len(r) else ""
            if rid:
                lookup_50[rid] = r

    title = f"Objecten vergelijking 5.02 vs 5.2 - {CODE}"
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
