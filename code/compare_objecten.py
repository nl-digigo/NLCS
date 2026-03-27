"""
Compare NLCS 5.0 vs 5.1 object tables per hoofdgroep.
Output: ontwikkeling/heroverweging-5-1/{CODE}/objecten-vergelijking-{CODE}.html
"""
import csv
import io
import os
import glob
import html as html_module

BASE_51 = r"tabellen\publicatie\objectentabellen"
BASE_50 = r"C:\Users\100289\OneDrive - CROW\Documents\GitHub\NLCSmain\NLCS\tabellen\publicatie\objectentabellen-verkort"
OUTPUT_DIR = r"ontwikkeling\heroverweging-5-1"


def parse_50_csv(filepath):
    """Parse 5.0 double-quoted CSV format, also handles semicolon-delimited."""
    with open(filepath, "r", encoding="utf-8-sig") as f:
        raw_lines = f.readlines()

    headers = []
    rows = []

    # Detect format: check if first line looks like semicolon-delimited
    first_line = raw_lines[0].strip() if raw_lines else ""
    if ";" in first_line and not first_line.startswith('"'):
        # Semicolon-delimited format
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
        # Double-quoted format
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


def parse_51_csv(filepath):
    with open(filepath, "r", encoding="utf-8-sig") as f:
        reader = csv.reader(f)
        headers = next(reader)
        headers = [h.strip() for h in headers]
        rows = list(reader)
    return headers, rows


def generate_html(title, headers_51, rows_51, lookup_50, headers_50, common_cols, id_column, has_50=True):
    col_idx_51 = {h: i for i, h in enumerate(headers_51)}
    col_idx_50 = {h: i for i, h in enumerate(headers_50)} if headers_50 else {}
    id_col_51 = col_idx_51.get(id_column)

    change_count = 0
    new_count = 0
    removed_count = 0
    matched_ids = set()

    html_parts = []
    html_parts.append(f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{title}</title>
<style>
    body {{ font-family: Arial, sans-serif; margin: 20px; }}
    h1 {{ color: #333; }}
    .legend {{ margin: 10px 0 20px 0; }}
    .legend span {{ padding: 4px 12px; margin-right: 10px; border-radius: 3px; font-size: 14px; }}
    .changed {{ background-color: #FFDD57; }}
    .new-row {{ background-color: #d4edda; }}
    .removed-row {{ background-color: #f8d7da; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
    th, td {{ border: 1px solid #ccc; padding: 6px 8px; text-align: left; }}
    th {{ background: #f0f0f0; position: sticky; top: 0; z-index: 1; }}
    tr:hover {{ background-color: #f5f5f5; }}
    tr.new-row:hover {{ background-color: #c3e6cb; }}
    tr.removed-row:hover {{ background-color: #f1b0b7; }}
    .stats {{ margin: 10px 0; font-size: 14px; color: #555; }}
</style>
</head>
<body>
<h1>{title}</h1>
<div class="legend">
    <span class="changed">Gewijzigd</span>
    <span class="new-row">Nieuw in 5.1</span>
    <span class="removed-row">Verwijderd (was in 5.0)</span>
</div>
""")

    html_parts.append("<table>\n<thead><tr>")
    for h in headers_51:
        html_parts.append(f"<th>{html_module.escape(h)}</th>")
    html_parts.append("</tr></thead>\n<tbody>\n")

    for row in rows_51:
        row_id = row[id_col_51].strip() if id_col_51 is not None and id_col_51 < len(row) else ""
        old_row = lookup_50.get(row_id) if has_50 else None

        if old_row:
            matched_ids.add(row_id)
            cells = []
            for h in headers_51:
                ci = col_idx_51.get(h)
                cell_val = row[ci].strip() if ci is not None and ci < len(row) else ""
                if h in common_cols and h in col_idx_50:
                    oi = col_idx_50[h]
                    old_val = old_row[oi].strip() if oi < len(old_row) else ""
                    if old_val != cell_val:
                        change_count += 1
                        escaped_old = html_module.escape(old_val) if old_val else "<em>(leeg)</em>"
                        escaped_new = html_module.escape(cell_val) if cell_val else "<em>(leeg)</em>"
                        cells.append(
                            f'<td class="changed" title="5.0: {html_module.escape(old_val)}">'
                            f"5.0 = {escaped_old}<br>5.1 = {escaped_new}</td>"
                        )
                    else:
                        cells.append(f"<td>{html_module.escape(cell_val)}</td>")
                else:
                    cells.append(f"<td>{html_module.escape(cell_val)}</td>")
            html_parts.append("<tr>" + "".join(cells) + "</tr>\n")
        else:
            new_count += 1
            cells = []
            for h in headers_51:
                ci = col_idx_51.get(h)
                cell_val = row[ci].strip() if ci is not None and ci < len(row) else ""
                cells.append(f"<td>{html_module.escape(cell_val)}</td>")
            html_parts.append('<tr class="new-row">' + "".join(cells) + "</tr>\n")

    if has_50:
        for old_id, old_row in lookup_50.items():
            if old_id not in matched_ids:
                removed_count += 1
                cells = []
                for h in headers_51:
                    if h in col_idx_50:
                        oi = col_idx_50[h]
                        val = old_row[oi].strip() if oi < len(old_row) else ""
                        cells.append(f"<td>{html_module.escape(val)}</td>")
                    else:
                        cells.append("<td></td>")
                html_parts.append('<tr class="removed-row">' + "".join(cells) + "</tr>\n")

    html_parts.append("</tbody>\n</table>\n")
    stats_text = f"Gewijzigde cellen: {change_count} | Nieuwe rijen: {new_count} | Verwijderde rijen: {removed_count}"
    html_parts.append(f'\n<div class="stats">{stats_text}</div>\n</body>\n</html>')

    full_html = "".join(html_parts)
    full_html = full_html.replace(
        "</div>\n\n<table>",
        f'</div>\n<div class="stats">{stats_text}</div>\n\n<table>',
        1,
    )
    return full_html, change_count, new_count, removed_count


def main():
    files_51 = sorted(glob.glob(os.path.join(BASE_51, "objecten-concept-5.1-*.csv")))
    print(f"Found {len(files_51)} 5.1 object tables")

    total_changes = 0
    total_new = 0
    total_removed = 0

    for f51 in files_51:
        basename = os.path.basename(f51)
        code = basename.replace("objecten-concept-5.1-", "").replace(".csv", "")
        print(f"\n--- {code} ---")

        headers_51, rows_51 = parse_51_csv(f51)

        # Find 5.0 counterpart
        pattern_50 = os.path.join(BASE_50, f"5.02-Objectentabel-{code}-*.csv")
        matches_50 = glob.glob(pattern_50)

        if matches_50:
            f50 = matches_50[0]
            headers_50, rows_50 = parse_50_csv(f50)
            id_column = "id_nummer"
            if id_column not in headers_50:
                id_column = "id"
            common_cols = set(headers_51) & set(headers_50)
            id_idx_50 = headers_50.index(id_column) if id_column in headers_50 else None
            lookup_50 = {}
            if id_idx_50 is not None:
                for row in rows_50:
                    row_id = row[id_idx_50].strip() if id_idx_50 < len(row) else ""
                    if row_id:
                        lookup_50[row_id] = row
            has_50 = True
        else:
            headers_50 = []
            lookup_50 = {}
            common_cols = set()
            has_50 = False

        title = f"Objecten vergelijking 5.0 vs 5.1 — {code}"
        html_content, changes, new, removed = generate_html(
            title, headers_51, rows_51, lookup_50, headers_50, common_cols, "id_nummer", has_50
        )

        # Output to subdirectory
        out_dir = os.path.join(OUTPUT_DIR, code)
        os.makedirs(out_dir, exist_ok=True)
        filename = f"objecten-vergelijking-{code}.html"
        filepath = os.path.join(out_dir, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)

        print(f"  {code}/{filename}: {changes} changes, {new} new, {removed} removed")
        total_changes += changes
        total_new += new
        total_removed += removed

    print(f"\nTotaal: {total_changes} gewijzigde cellen, {total_new} nieuwe rijen, {total_removed} verwijderde rijen")


if __name__ == "__main__":
    main()
