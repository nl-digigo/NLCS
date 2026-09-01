"""
rn_html.py - HTML-generator voor de release notes tool.

Bouwt uit een lijst issue-dicts (van rn_fetch, eventueel gefilterd door
rn_extract.filter_issues) één zelfstandige HTML-pagina met een DataTables-
tabel: klik-op-kop sorteren + per-kolom filteren (dropdown voor State,
Milestone en Labels, zoekvak voor de rest). Bij Labels kies je één label uit
de lijst; rijen die dat label bevatten blijven staan (issues hebben vaak
meerdere labels tegelijk).

DataTables/jQuery worden via CDN geladen (internet nodig om de tabel te
laten werken, zoals afgesproken).

Kolommen: Issue (link) | Titel | State | Milestone | Labels | Release note(s)

Los te testen (met cache-JSON van rn_fetch --out):
    python rn_html.py --in issues.json --tag "[[release note]]" --out preview.html
"""

import html as _html
import json

from rn_extract import issue_tag_blocks
from rn_assets import LOGO_DATA_URI, BANNER_DATA_URI


# Kolomindex van State en Milestone (dropdown met exacte match i.p.v. zoekvak)
_SELECT_COLUMNS = [2, 3]
# Labels-kolom: dropdown met losse labels; match = 'rij bevat dit label'
_LABELS_COLUMN = 4


# ---------------------------------------------------------------------------
# Vaste opmaak + scripting (geen dynamische inhoud -> gewone string)
# ---------------------------------------------------------------------------
_HEAD = """<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>__TITLE__</title>
<link rel="stylesheet" href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css">
<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>
<script src="https://cdn.datatables.net/1.13.8/js/jquery.dataTables.min.js"></script>
<style>
    /* ---- digiGO huisstijl ------------------------------------------------
       geel #FFE103 | zwart #000 | blauw #009DDB | grijs #DCDCDC / #818181 */
    :root {
        --dg-yellow: #FFE103;
        --dg-black:  #000000;
        --dg-ink:    #1D1D1B;
        --dg-blue:   #009DDB;
        --dg-grey:   #DCDCDC;
        --dg-grey2:  #818181;
    }
    * { box-sizing: border-box; }
    body { font-family: Calibri, "Segoe UI", Candara, Optima, sans-serif;
           margin: 0; background-color: #f4f5f6; color: var(--dg-ink); }

    /* Kop: zwarte balk met logo + titel, gele accentlijn eronder */
    .site-header { background: var(--dg-black); border-bottom: 6px solid var(--dg-yellow);
                   display: flex; align-items: center; gap: 22px;
                   padding: 16px 28px; }
    .site-header img.logo { height: 46px; width: auto; display: block; }
    .site-header .divider { width: 1px; align-self: stretch; background: #444; }
    .site-header h1 { color: #fff; font-size: 1.35rem; font-weight: 600;
                      margin: 0; letter-spacing: .2px; }

    /* Skyline-banner in de huisstijl */
    img.banner { display: block; width: 100%; height: 132px;
                 object-fit: cover; object-position: center bottom; }

    .wrap { max-width: 1440px; margin: 0 auto; padding: 22px 28px 40px; }
    .info { color: var(--dg-grey2); margin: 4px 0 18px; font-size: .95rem; }

    /* Tabel */
    table.dataTable { background-color: #fff; border-collapse: collapse; }
    table.dataTable thead th { background-color: var(--dg-black); color: #fff;
                    border-bottom: 3px solid var(--dg-yellow); font-weight: 600; }
    table.dataTable tbody td { vertical-align: top; overflow-wrap: anywhere; }
    td.releasenote { max-width: 520px; }
    td.titel { max-width: 320px; }
    td.labels { max-width: 220px; }
    table.dataTable tbody tr:hover td { background-color: #FFF8CC; }
    a { color: var(--dg-blue); text-decoration: none; font-weight: 600; }
    a:hover { text-decoration: underline; }

    /* Milestone = gele pil (huisstijl-accent); labels = neutrale grijze badges */
    .milestone { display: inline-block; background-color: var(--dg-yellow); color: #000;
                 padding: 2px 10px; border-radius: 12px; font-size: 0.85em; font-weight: 600; }
    .labelcol { display: flex; flex-direction: column; align-items: flex-start; gap: 2px; }
    .label { display: inline-block; padding: 2px 7px; border-radius: 3px; font-size: 0.8em;
             background-color: var(--dg-grey); color: var(--dg-ink); }

    /* Per-kolom filterrij */
    thead tr.filters input, thead tr.filters select { width: 100%; box-sizing: border-box;
             padding: 3px; font-size: 0.85em; font-weight: normal; }
    thead tr.filters th { padding: 4px 6px; background-color: #ececec;
             border-bottom: 1px solid var(--dg-grey); }

    /* DataTables-bediening in de huisstijl */
    .dataTables_wrapper .dataTables_paginate .paginate_button.current,
    .dataTables_wrapper .dataTables_paginate .paginate_button.current:hover {
        background: var(--dg-yellow) !important; border-color: var(--dg-yellow) !important;
        color: #000 !important; }
    .dataTables_wrapper .dataTables_paginate .paginate_button:hover {
        background: var(--dg-black) !important; border-color: var(--dg-black) !important;
        color: #fff !important; }
    .dataTables_wrapper .dataTables_filter input,
    .dataTables_wrapper .dataTables_length select {
        border: 1px solid var(--dg-grey); border-radius: 3px; padding: 2px 6px; }

    /* Voettekst */
    .site-footer { border-top: 4px solid var(--dg-yellow); background: var(--dg-black);
                   color: #cfcfcf; padding: 14px 28px; font-size: .85rem; }
    .site-footer strong { color: var(--dg-yellow); }
</style>
</head>
<body>
<header class="site-header">
  <img class="logo" src="__LOGO__" alt="digiGO">
  <div class="divider"></div>
  <h1>__TITLE__</h1>
</header>
<img class="banner" src="__BANNER__" alt="">
<div class="wrap">
<p class="info">__INFO__</p>
<table id="rn" class="display" style="width:100%">
<thead>
<tr>
<th>Issue</th><th>Titel</th><th>State</th><th>Milestone</th><th>Labels</th><th>Release note</th>
</tr>
<tr class="filters">
<th>Issue</th><th>Titel</th><th>State</th><th>Milestone</th><th>Labels</th><th>Release note</th>
</tr>
</thead>
<tbody>
"""

_FOOT = """</tbody>
</table>
<script>
$(document).ready(function () {
    var selectCols = __SELECT_COLS__;      // exacte-match dropdowns (State, Milestone)
    var labelsCol = __LABELS_COL__;        // Labels: dropdown 'bevat dit label'
    var labelOptions = __LABEL_OPTIONS__;  // losse labelnamen voor die dropdown
    var rowLabels = __ROW_LABELS__;        // labels per rij (zelfde volgorde als tbody)
    var labelFilter = "";                  // huidig gekozen label ("" = geen filter)

    // Bouw per kolom een filter in de tweede kop-rij (dropdown of zoekvak)
    $('#rn thead tr.filters th').each(function (i) {
        var titel = $(this).text();
        if (i === labelsCol || selectCols.indexOf(i) !== -1) {
            $(this).html('<select><option value="">Alle</option></select>');
        } else {
            $(this).html('<input type="text" placeholder="Zoek ' + titel + '" />');
        }
    });

    var table = $('#rn').DataTable({
        pageLength: 10,
        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "Alle"]],
        order: [[3, 'asc'], [0, 'asc']],
        orderCellsTop: true
    });

    // Eigen filter voor de Labels-kolom: een rij blijft staan als haar
    // labellijst het gekozen label bevat (issues hebben vaak meerdere labels).
    $.fn.dataTable.ext.search.push(function (settings, data, dataIndex) {
        if (settings.nTable.id !== 'rn' || !labelFilter) return true;
        var labels = rowLabels[dataIndex] || [];
        return labels.indexOf(labelFilter) !== -1;
    });

    // Voorkom dat klikken in een filterveld de kolom sorteert
    $('#rn thead tr.filters th').on('click', function (e) { e.stopPropagation(); });

    table.columns().every(function (i) {
        var column = this;
        var cell = $('#rn thead tr.filters th').eq(i);
        var select = cell.find('select');
        if (i === labelsCol) {
            labelOptions.forEach(function (text) {
                $('<option>').val(text).text(text).appendTo(select);
            });
            select.on('change', function () {
                labelFilter = $(this).val();
                table.draw();
            });
        } else if (select.length) {
            // Exacte-match dropdown (State, Milestone) uit de kolomwaarden
            column.data().unique().sort().each(function (d) {
                var text = $('<div>').html(d).text().trim();
                if (text) select.append('<option value="' + text + '">' + text + '</option>');
            });
            select.on('change', function () {
                var val = $.fn.dataTable.util.escapeRegex($(this).val());
                column.search(val ? '^' + val + '$' : '', true, false).draw();
            });
        } else {
            cell.find('input').on('keyup change clear', function () {
                if (column.search() !== this.value) {
                    column.search(this.value).draw();
                }
            });
        }
    });
});
</script>
</div>
<footer class="site-footer">
  <strong>digiGO</strong> &middot; digitaal samenwerken in de Gebouwde Omgeving
</footer>
</body>
</html>
"""


def _esc(text: str) -> str:
    """HTML-escape met newlines als <br>."""
    return _html.escape(text or "", quote=True).replace("\n", "<br>")


def _selected_labels(labels: list[str], show_labels) -> list[str]:
    """De labels die getoond mogen worden (show_labels None = alle)."""
    if show_labels is None:
        return list(labels)
    allowed = set(show_labels)
    return [lbl for lbl in labels if lbl in allowed]


def _labels_cell(labels: list[str], show_labels) -> str:
    """De <td> voor de Labels-kolom: de te tonen labels als badges.

    Het filteren gebeurt niet op deze celinhoud maar via een aparte JS-lijst
    (rowLabels) + een eigen DataTables-zoekfunctie; zie _FOOT.
    """
    selected = _selected_labels(labels, show_labels)
    if not selected:
        return '<td class="labels"></td>'
    badges = "".join(f'<span class="label">{_esc(lbl)}</span>' for lbl in selected)
    return f'<td class="labels"><div class="labelcol">{badges}</div></td>'


def _row_html(issue: dict, tag: str, show_labels) -> str:
    number = issue.get("number")
    url = issue.get("url") or ""
    issue_link = f'<a href="{_esc(url)}" target="_blank">#{number}</a>'

    milestone = issue.get("milestone") or ""
    milestone_html = f'<span class="milestone">{_esc(milestone)}</span>' if milestone else ""

    labels_cell = _labels_cell(issue.get("labels") or [], show_labels)

    blocks = issue_tag_blocks(issue, tag) if tag else []
    note_html = "<hr>".join(_esc(b) for b in blocks)

    return (
        "<tr>"
        f"<td>{issue_link}</td>"
        f'<td class="titel">{_esc(issue.get("title") or "")}</td>'
        f"<td>{_esc(issue.get('state') or '')}</td>"
        f"<td>{milestone_html}</td>"
        f"{labels_cell}"
        f'<td class="releasenote">{note_html}</td>'
        "</tr>\n"
    )


def build_html(issues: list[dict], tag: str = "[[release note]]",
               show_labels=None, title: str = "NLCS Release Notes") -> str:
    """Bouw de volledige HTML-pagina als string.

    Parameters:
        issues:      (gefilterde) lijst issue-dicts.
        tag:         tag waarvan de tekst in de Release note-kolom komt.
        show_labels: verzameling labelnamen die getoond mogen worden in de
                     Labels-kolom; None = alle labels tonen.
        title:       titel van de pagina.
    """
    info = (f"{len(issues)} issues | tag: {_esc(tag)} | "
            "sorteer door op een kop te klikken, filter per kolom onderin")

    # Labels per rij (zelfde volgorde als de tbody-rijen) voor de eigen
    # filterfunctie, plus de unieke gesorteerde labels voor de dropdown.
    row_labels = [_selected_labels(issue.get("labels") or [], show_labels)
                  for issue in issues]
    label_set: set[str] = set()
    for labels in row_labels:
        label_set.update(labels)
    label_options = sorted(label_set, key=str.casefold)

    head = (_HEAD.replace("__TITLE__", _esc(title))
                 .replace("__INFO__", info)
                 .replace("__LOGO__", LOGO_DATA_URI)
                 .replace("__BANNER__", BANNER_DATA_URI))
    body_rows = "".join(_row_html(i, tag, show_labels) for i in issues)
    foot = (_FOOT.replace("__SELECT_COLS__", str(_SELECT_COLUMNS))
                 .replace("__LABELS_COL__", str(_LABELS_COLUMN))
                 .replace("__LABEL_OPTIONS__", json.dumps(label_options,
                                                          ensure_ascii=False))
                 .replace("__ROW_LABELS__", json.dumps(row_labels,
                                                       ensure_ascii=False)))
    return head + body_rows + foot


def save_html(issues: list[dict], path: str, tag: str = "[[release note]]",
              show_labels=None, title: str = "NLCS Release Notes") -> None:
    """Bouw en schrijf de HTML naar `path` (UTF-8)."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(build_html(issues, tag=tag, show_labels=show_labels, title=title))


# ---------------------------------------------------------------------------
# Losse test
# ---------------------------------------------------------------------------

def _main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Test: bouw de HTML-tabel uit een cache-JSON.")
    parser.add_argument("--in", dest="infile", required=True,
                        help="JSON-cache van rn_fetch (--out)")
    parser.add_argument("--out", default="preview.html",
                        help="Pad voor de HTML-output")
    parser.add_argument("--tag", default="[[release note]]")
    parser.add_argument("--title", default="NLCS Release Notes")
    parser.add_argument("--milestone", action="append", default=None,
                        help="Filter op milestone (mag meerdere keren)")
    parser.add_argument("--label", action="append", default=None,
                        help="Filter-selectie op label (mag meerdere keren)")
    parser.add_argument("--require-tag", action="store_true",
                        help="Alleen issues waarin de tag voorkomt")
    parser.add_argument("--show-label", action="append", default=None,
                        help="Alleen deze labels tonen in de tabel (mag meerdere keren)")
    args = parser.parse_args()

    with open(args.infile, encoding="utf-8") as f:
        issues = json.load(f)

    from rn_extract import filter_issues
    selection = filter_issues(issues, milestones=args.milestone,
                              labels=args.label, tag=args.tag,
                              require_tag=args.require_tag)

    save_html(selection, args.out, tag=args.tag,
              show_labels=args.show_label, title=args.title)
    print(f"{len(selection)} issues -> {args.out}")


if __name__ == "__main__":
    _main()
