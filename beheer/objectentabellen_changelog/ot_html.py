"""
ot_html.py - HTML-generatoren voor de objectentabellen-changelog tool.

Twee pagina's in digiGO-huisstijl uit het vergelijkingsresultaat van
ot_compare.compare():

1. build_full_html   - de volledige nieuwe tabel, alfabetisch op de eerste
                       kolom, sorteerbaar EN filterbaar op ALLE kolommen
                       (DataTables, met horizontale scroll voor de 60 kolommen).

2. build_changelog_html - dezelfde rijen, alfabetisch op de eerste kolom, maar
                       als changelog: een gewijzigde cel toont de oude en de
                       nieuwe waarde in BLAUW, geheel nieuwe rijen in GROEN, en
                       vervallen rijen onderaan in ROOD. Met versienaam-labels
                       en een legenda. Statisch (geen DataTables).

DataTables/jQuery via CDN (internet nodig voor de volledige tabel).
"""

import html as _html
import json as _json

from ot_assets import LOGO_DATA_URI, BANNER_DATA_URI


# Objectentabellen: verberg in beide HTML's het blok 'status' t/m 'streepje3'
# (inclusief). De vergelijking zelf gebruikt nog wel alle kolommen; alleen de
# weergave laat dit blok weg.
HIDE_FROM = "status"
HIDE_TO = "streepje3"


def hide_range_indices(headers: list[str], hide_from: str, hide_to: str) -> list[int]:
    """Alle kolomindices behalve het aaneengesloten blok hide_from..hide_to.

    Valt terug op 'alles tonen' als een van de grenskolommen ontbreekt."""
    try:
        i_from = headers.index(hide_from)
        i_to = headers.index(hide_to)
    except ValueError:
        return list(range(len(headers)))
    lo, hi = min(i_from, i_to), max(i_from, i_to)
    return [i for i in range(len(headers)) if not (lo <= i <= hi)]


def show_names_indices(headers: list[str], names) -> list[int]:
    """De kolomindices van alleen de opgegeven kolomnamen, in CSV-volgorde.

    Namen die niet bestaan worden genegeerd."""
    wanted = set(names)
    return [i for i, h in enumerate(headers) if h in wanted]


def show_names_ordered(headers: list[str], names) -> list[int]:
    """De kolomindices van de opgegeven kolomnamen, in de VOLGORDE van `names`
    (dus niet de CSV-volgorde). Namen die niet bestaan worden overgeslagen.

    Zo kun je de weergave-volgorde sturen, bijv. de symboolnaam vooraan en de
    URI-kolom achteraan."""
    idx = {h: i for i, h in enumerate(headers)}
    return [idx[n] for n in names if n in idx]


def _visible_indices(headers: list[str]) -> list[int]:
    """Standaard (objectentabellen): het blok HIDE_FROM..HIDE_TO weg."""
    return hide_range_indices(headers, HIDE_FROM, HIDE_TO)


# ---------------------------------------------------------------------------
# Gedeelde huisstijl
# ---------------------------------------------------------------------------
_STYLE = """
    :root {
        --dg-yellow: #FFE103;
        --dg-black:  #000000;
        --dg-ink:    #1D1D1B;
        --dg-blue:   #009DDB;
        --dg-red:    #FF404B;
        --dg-green:  #3FA534;
        --dg-grey:   #DCDCDC;
        --dg-grey2:  #818181;
    }
    * { box-sizing: border-box; }
    body { font-family: Calibri, "Segoe UI", Candara, Optima, sans-serif;
           margin: 0; background-color: #f4f5f6; color: var(--dg-ink); }

    .site-header { background: var(--dg-black); border-bottom: 6px solid var(--dg-yellow);
                   display: flex; align-items: center; gap: 22px; padding: 16px 28px; }
    .site-header img.logo { height: 46px; width: auto; display: block; }
    .site-header .divider { width: 1px; align-self: stretch; background: #444; }
    .site-header h1 { color: #fff; font-size: 1.35rem; font-weight: 600;
                      margin: 0; letter-spacing: .2px; }

    img.banner { display: block; width: 100%; height: 132px;
                 object-fit: cover; object-position: center bottom; }

    .wrap { max-width: 100%; margin: 0 auto; padding: 22px 28px 40px; }
    .info { color: var(--dg-grey2); margin: 4px 0 18px; font-size: .95rem; }

    table.otab { background-color: #fff; border-collapse: collapse; font-size: .85rem; }
    table.otab thead th { background-color: var(--dg-black); color: #fff;
                    border-bottom: 3px solid var(--dg-yellow); font-weight: 600;
                    white-space: nowrap; padding: 6px 8px; }
    table.otab tbody td { vertical-align: top; white-space: nowrap;
                    padding: 4px 8px; border-bottom: 1px solid var(--dg-grey); }

    .site-footer { border-top: 4px solid var(--dg-yellow); background: var(--dg-black);
                   color: #cfcfcf; padding: 14px 28px; font-size: .85rem; }
    .site-footer strong { color: var(--dg-yellow); }
"""

_HEADER = """<header class="site-header">
  <img class="logo" src="__LOGO__" alt="digiGO">
  <div class="divider"></div>
  <h1>__TITLE__</h1>
</header>
<img class="banner" src="__BANNER__" alt="">
"""

_FOOTER = """<footer class="site-footer">
  <strong>digiGO</strong> &middot; digitaal samenwerken in de Gebouwde Omgeving
</footer>
</body>
</html>
"""


def _esc(text) -> str:
    return _html.escape("" if text is None else str(text), quote=True)


def _shell_head(title: str, extra_style: str = "", cdn: bool = False) -> str:
    cdn_tags = ""
    if cdn:
        cdn_tags = (
            '<link rel="stylesheet" '
            'href="https://cdn.datatables.net/1.13.8/css/jquery.dataTables.min.css">\n'
            '<script src="https://code.jquery.com/jquery-3.7.1.min.js"></script>\n'
            '<script src="https://cdn.datatables.net/1.13.8/js/'
            'jquery.dataTables.min.js"></script>\n')
    header = _HEADER.replace("__LOGO__", LOGO_DATA_URI) \
                    .replace("__BANNER__", BANNER_DATA_URI) \
                    .replace("__TITLE__", _esc(title))
    return (
        "<!DOCTYPE html>\n<html lang=\"nl\">\n<head>\n"
        "<meta charset=\"UTF-8\">\n"
        "<meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">\n"
        f"<title>{_esc(title)}</title>\n"
        f"{cdn_tags}"
        f"<style>{_STYLE}{extra_style}</style>\n"
        "</head>\n<body>\n"
        f"{header}"
    )


# ---------------------------------------------------------------------------
# 1. Volledige tabel (sorteer + filter op alle kolommen)
# ---------------------------------------------------------------------------
_FULL_STYLE = """
    /* Horizontale scroll voor de brede tabel */
    div.dataTables_wrapper { overflow-x: auto; }
    table.dataTable thead th { background-color: var(--dg-black); color: #fff;
                    border-bottom: 3px solid var(--dg-yellow); }
    table.dataTable tbody tr:hover td { background-color: #FFF8CC; }
    thead tr.filters th { padding: 3px 4px; background-color: #ececec;
                    border-bottom: 1px solid var(--dg-grey); }
    thead tr.filters input,
    thead tr.filters select { width: 100%; box-sizing: border-box; padding: 2px;
                    font-size: 0.8em; font-weight: normal; }
    thead tr.filters select { cursor: pointer; }
    /* Extra kolommen (zoekfilter / svg / .dwg) */
    td.svgcell { text-align: center; }
    td.svgcell img { max-height: 46px; max-width: 90px; vertical-align: middle; }
    span.dwg-ja { color: var(--dg-green); font-weight: bold; }
    span.dwg-nee { color: var(--dg-red); font-weight: bold; }
    span.zf-term { font-family: Consolas, "Courier New", monospace; }
    span.zf-geen { color: var(--dg-grey2); font-style: italic; }
    .dataTables_wrapper .dataTables_paginate .paginate_button.current,
    .dataTables_wrapper .dataTables_paginate .paginate_button.current:hover {
        background: var(--dg-yellow) !important; border-color: var(--dg-yellow) !important;
        color: #000 !important; }
"""

def _full_script(no_sort_indices=None, order=None) -> str:
    """Het DataTables-init-script. `no_sort_indices` = kolommen die niet
    sorteerbaar mogen zijn (bijv. de svg-afbeeldingskolom). `order` = de
    standaardsortering ([[kolomindex, 'asc'|'desc'], ...]); None -> [[0,'asc']]."""
    coldefs = ""
    if no_sort_indices:
        coldefs = ("\n        columnDefs: [{ orderable: false, targets: "
                   + _json.dumps(list(no_sort_indices)) + " }],")
    order_js = _json.dumps(order if order else [[0, "asc"]])
    return """
<script>
$(document).ready(function () {
    var table = $('#otab').DataTable({
        pageLength: 25,
        lengthMenu: [[10, 25, 50, 100, -1], [10, 25, 50, 100, "Alle"]],""" + coldefs + """
        order: """ + order_js + """,
        orderCellsTop: true
    });
    // Filters via event-delegatie op de wrapper: blijft werken ongeacht hoe
    // DataTables de kop opnieuw opbouwt. De kolomindex volgt uit de positie
    // van de <th> in de filterrij.
    var $wrap = $('#otab_wrapper');
    // niet sorteren als je in een filtervak klikt
    $wrap.on('click', 'tr.filters th', function (e) { e.stopPropagation(); });
    // vrije-tekstkolommen: zoek terwijl je typt
    $wrap.on('keyup change search', 'tr.filters input', function () {
        var i = $(this).closest('th').index();
        if (table.column(i).search() !== this.value) {
            table.column(i).search(this.value).draw();
        }
    });
    // keuzelijst-kolommen: exact filteren op de gekozen waarde
    $wrap.on('change', 'tr.filters select', function () {
        var i = $(this).closest('th').index();
        var v = this.value;
        var term = v ? '^' + $.fn.dataTable.util.escapeRegex(v) + '$' : '';
        table.column(i).search(term, true, false).draw();
    });
});
</script>
"""


def _default_is_text(header: str) -> bool:
    """Standaard: vrij zoekveld voor omschrijving, laagnaam en alle URI-kolommen;
    de overige kolommen krijgen een keuzelijst."""
    return header in ("omschrijving", "laagnaam") or "uri" in header.lower()


def _filter_cell(index: int, header: str, is_text: bool, rows: list) -> str:
    """De inhoud van één filter-cel: een zoekveld (vrije tekst) of een keuzelijst
    met de voorkomende waarden in die kolom."""
    if is_text:
        return f'<th><input type="text" placeholder="Zoek {_esc(header)}" /></th>'
    # keuzelijst: unieke, niet-lege waarden uit deze kolom, alfabetisch
    seen: list[str] = []
    seen_set: set[str] = set()
    for row in rows:
        v = row["cells"][index]["value"]
        if v and v not in seen_set:
            seen_set.add(v)
            seen.append(v)
    seen.sort(key=str.casefold)
    options = '<option value="">Alle</option>' + "".join(
        f'<option value="{_esc(v)}">{_esc(v)}</option>' for v in seen)
    return f"<th><select>{options}</select></th>"


def _extra_filter_cell(col: dict) -> str:
    """Filter-cel voor een extra kolom (dwg-aanwezigheid / svg)."""
    kind = col.get("filter", "none")
    if kind == "text":
        return f'<th><input type="text" placeholder="Zoek {_esc(col["header"])}" /></th>'
    if kind == "select":
        vals = col.get("filter_values") or []
        seen: list[str] = []
        seen_set: set[str] = set()
        for v in vals:
            if v and v not in seen_set:
                seen_set.add(v)
                seen.append(v)
        seen.sort(key=str.casefold)
        options = '<option value="">Alle</option>' + "".join(
            f'<option value="{_esc(v)}">{_esc(v)}</option>' for v in seen)
        return f"<th><select>{options}</select></th>"
    return "<th></th>"


def build_full_html(result: dict, title: str, version_new: str = "",
                    visible_indices=None, text_columns=None,
                    extra_columns=None, front_columns=None, order=None) -> str:
    """Volledige nieuwe tabel als sorteerbare/filterbare DataTables-pagina.

    text_columns  : kolomnamen die een vrij zoekveld krijgen; alle andere
                    zichtbare kolommen krijgen een keuzelijst. None -> standaard
                    (_default_is_text: omschrijving, laagnaam en URI-kolommen).
    extra_columns : optionele extra kolommen ACHTERAAN (bijv. symbolen: '.dwg
                    aanwezig' + 'svg'). Elk een dict met:
                      header        : koptekst
                      cells         : lijst rauwe-HTML-cellen (op volgorde van
                                      result['rows'])
                      filter        : 'none' | 'select' | 'text'
                      filter_values : lijst platte waarden per rij (voor 'select')
                      orderable     : bool (svg-kolom = False)
                      td_class      : optionele class op de <td>
    front_columns : idem, maar VOORAAN (bijv. symbolen: 'zoekfilter' + 'svg').
                    De eerste front-kolom moet sorteerbaar zijn (order [[0]]).
    order         : DataTables-standaardsortering ([[kolomindex, richting], ...]);
                    None -> [[0, 'asc']]. Symbolen groeperen zo op de zoekfilter-
                    kolom (0) met de symboolnaam-kolom als secundaire sortering."""
    headers = result["headers"]
    rows = result["rows"]
    front = front_columns or []
    extra = extra_columns or []
    vis = _visible_indices(headers) if visible_indices is None else visible_indices

    if text_columns is None:
        text_set = {headers[i] for i in vis if _default_is_text(headers[i])}
    else:
        text_set = set(text_columns)

    # Volgorde overal gelijk: front -> zichtbaar -> extra (de filter-JS koppelt op
    # de DOM-index van de <th>).
    head_cells = "".join(f"<th>{_esc(col['header'])}</th>" for col in front)
    head_cells += "".join(f"<th>{_esc(headers[i])}</th>" for i in vis)
    head_cells += "".join(f"<th>{_esc(col['header'])}</th>" for col in extra)
    filter_cells = "".join(_extra_filter_cell(col) for col in front)
    filter_cells += "".join(
        _filter_cell(i, headers[i], headers[i] in text_set, rows) for i in vis)
    filter_cells += "".join(_extra_filter_cell(col) for col in extra)

    def _cell_td(col, ri):
        cls = col.get("td_class")
        cell = col["cells"][ri] if ri < len(col["cells"]) else ""
        return f'<td class="{cls}">{cell}</td>' if cls else f"<td>{cell}</td>"

    body = []
    for ri, row in enumerate(rows):
        tds = "".join(_cell_td(col, ri) for col in front)
        tds += "".join(f"<td>{_esc(row['cells'][i]['value'])}</td>" for i in vis)
        tds += "".join(_cell_td(col, ri) for col in extra)
        body.append(f"<tr>{tds}</tr>")

    # svg-achtige kolommen niet sorteerbaar maken (front vooraan, extra achteraan)
    no_sort = [j for j, col in enumerate(front) if not col.get("orderable", True)]
    no_sort += [len(front) + len(vis) + j for j, col in enumerate(extra)
                if not col.get("orderable", True)]

    n_text = sum(1 for i in vis if headers[i] in text_set)
    info = (f"{len(rows)} rijen &middot; {len(vis)} van {len(headers)} kolommen"
            + (f" + {len(front) + len(extra)} extra" if (front or extra) else "")
            + (f" &middot; versie {_esc(version_new)}" if version_new else "")
            + f" &middot; {n_text} kolommen met vrij zoekveld, de rest met keuzelijst")

    return (
        _shell_head(title, extra_style=_FULL_STYLE, cdn=True)
        + f'<div class="wrap">\n<p class="info">{info}</p>\n'
        + '<table id="otab" class="otab display" style="width:100%">\n<thead>\n'
        + f"<tr>{head_cells}</tr>\n"
        + f'<tr class="filters">{filter_cells}</tr>\n'
        + "</thead>\n<tbody>\n"
        + "\n".join(body)
        + "\n</tbody>\n</table>\n"
        + _full_script(no_sort, order)
        + "</div>\n"
        + _FOOTER
    )


# ---------------------------------------------------------------------------
# 2. Changelog (statisch, gekleurd)
# ---------------------------------------------------------------------------
_CHANGELOG_STYLE = """
    .tablescroll { overflow-x: auto; }
    table.otab { width: auto; }
    table.otab tbody tr.new-row td { background-color: #e5f5e0; }   /* groen: nieuw */
    table.otab tbody tr.deleted td { background-color: #ffe0e2; }   /* rood: vervallen */
    td.changed { background-color: #e0f3fb; }                       /* blauw: gewijzigd */
    td.changed .old-val { color: var(--dg-grey2); text-decoration: line-through;
                          display: block; font-size: .92em; }
    td.changed .new-val { color: var(--dg-blue); font-weight: 600; display: block; }
    td.changed .lbl { font-weight: 700; font-size: .78em; letter-spacing: .3px; }

    tr.section-header th { background-color: var(--dg-grey); color: var(--dg-ink);
                    text-align: left; padding: 10px 8px; font-size: 1rem;
                    border-top: 3px solid var(--dg-red); }

    .legend { display: flex; flex-wrap: wrap; gap: 18px; margin: 6px 0 20px;
              font-size: .9rem; }
    .legend span { display: inline-flex; align-items: center; gap: 7px; }
    .swatch { width: 16px; height: 16px; border-radius: 3px; display: inline-block;
              border: 1px solid var(--dg-grey2); }
    .sw-new { background-color: #e5f5e0; }
    .sw-changed { background-color: #e0f3fb; }
    .sw-deleted { background-color: #ffe0e2; }

    /* Extra symbolen-kolommen (alleen in de changelog) */
    td.svgcell { text-align: center; }
    td.svgcell img { max-height: 46px; max-width: 90px; vertical-align: middle; }
    span.dwg-ja { color: var(--dg-green); font-weight: bold; }
    span.dwg-nee { color: var(--dg-red); font-weight: bold; }
    span.hash-gelijk { color: var(--dg-green); font-weight: bold; }
    span.hash-wijz { color: var(--dg-blue); font-weight: bold; }
    span.hash-neutraal { color: var(--dg-grey2); }
    span.zf-term { font-family: Consolas, "Courier New", monospace; }
    span.zf-geen { color: var(--dg-grey2); font-style: italic; }

    /* Wees-.dwg's: bestanden zonder regel in deze symbolentabel */
    tr.section-header.wees th { border-top-color: var(--dg-grey2); }
    table.otab tbody tr.orphan td { background-color: #f0f0f0; }
    table.otab tbody tr.orphan td.weespad { color: var(--dg-grey2);
                    white-space: normal; }
    .sw-wees { background-color: #f0f0f0; }

    /* Melding bovenaan als er geen wijzigingen zijn */
    p.geen-wijzigingen { margin: 0 0 14px; padding: 12px 16px;
                    background-color: #eef7ee; border-left: 6px solid var(--dg-green);
                    font-size: 1.05em; font-weight: 600; color: #1f6b23; }
"""


# Kolommen waarvan een waarde uit meerdere puntkomma-gescheiden termen kan bestaan
# (objecten: sobject/aobject verwijzen soms naar tien+ symbolen/arceringen). In de
# changelog tonen we zo'n lange lijst niet letterlijk, maar de tekst 'multiple links'.
_MULTI_LINK_COLS = {"sobject", "aobject"}


def _cl_val(headers: list[str], i: int, value: str) -> str:
    """Celtekst voor de changelog: voor sobject/aobject een lange puntkomma-lijst
    tonen als 'multiple links', anders de (ge-escapete) waarde zelf."""
    if headers and headers[i] in _MULTI_LINK_COLS:
        parts = [p for p in (value or "").split(";") if p.strip()]
        if len(parts) > 1:
            return "multiple links"
    return _esc(value)


def _changelog_row(row: dict, version_new: str, version_old: str,
                   vis: list[int], extra=None, ri: int = 0,
                   headers: list[str] = None) -> str:
    tds = []
    for i in vis:
        cell = row["cells"][i]
        if cell["changed"]:
            old_lbl = f'<span class="lbl">{_esc(version_old or "oud")}:</span> ' \
                      f'{_cl_val(headers, i, cell["old"])}'
            new_lbl = f'<span class="lbl">{_esc(version_new or "nieuw")}:</span> ' \
                      f'{_cl_val(headers, i, cell["value"])}'
            tds.append(f'<td class="changed">'
                       f'<span class="old-val">{old_lbl}</span>'
                       f'<span class="new-val">{new_lbl}</span></td>')
        else:
            tds.append(f"<td>{_cl_val(headers, i, cell['value'])}</td>")
    for col in (extra or []):
        cls = col.get("td_class")
        cell = col["cells"][ri] if ri < len(col["cells"]) else ""
        tds.append(f'<td class="{cls}">{cell}</td>' if cls else f"<td>{cell}</td>")
    cls = ' class="new-row"' if row["status"] == "new" else ""
    return f"<tr{cls}>{''.join(tds)}</tr>"


def build_changelog_html(result: dict, title: str,
                         version_new: str = "", version_old: str = "",
                         visible_indices=None, extra_columns=None,
                         orphans=None) -> str:
    """Changelog-pagina: gewijzigde cellen blauw (oud + nieuw), nieuwe rijen
    groen, vervallen rijen onderaan rood.

    extra_columns : optionele extra kolommen achteraan (symbolen: '.dwg aanwezig'
                    + 'svg'). Elk een dict met header, cells (op volgorde van
                    result['rows']), deleted_cells (op volgorde van
                    result['deleted']) en optioneel td_class.
    orphans       : optionele lijst (bestandsnaam, relatief pad) van .dwg-
                    bestanden die bij GEEN regel in deze symbolentabel horen;
                    onderaan getoond in een aparte 'wees'-sectie."""
    headers = result["headers"]
    rows = result["rows"]
    deleted = result["deleted"]
    stats = result["stats"]
    extra = extra_columns or []
    orphans = orphans or []
    vis = _visible_indices(headers) if visible_indices is None else visible_indices

    head_cells = "".join(f"<th>{_esc(headers[i])}</th>" for i in vis)
    head_cells += "".join(f"<th>{_esc(col['header'])}</th>" for col in extra)
    ncols = len(vis) + len(extra)

    body = [_changelog_row(r, version_new, version_old, vis, extra, ri, headers)
            for ri, r in enumerate(rows)]

    if deleted:
        body.append(
            f'<tr class="section-header"><th colspan="{ncols}">'
            f'Vervallen rijen ({len(deleted)}) &middot; aanwezig in '
            f'{_esc(version_old or "de oude versie")}, niet meer in '
            f'{_esc(version_new or "de nieuwe versie")}</th></tr>')
        for di, drow in enumerate(deleted):
            tds = "".join(f"<td>{_cl_val(headers, i, drow[i])}</td>" for i in vis)
            for col in extra:
                cls = col.get("td_class")
                dcells = col.get("deleted_cells") or []
                cell = dcells[di] if di < len(dcells) else ""
                tds += (f'<td class="{cls}">{cell}</td>' if cls
                        else f"<td>{cell}</td>")
            body.append(f'<tr class="deleted">{tds}</tr>')

    if orphans:
        body.append(
            f'<tr class="section-header wees"><th colspan="{ncols}">'
            f'Wees-.dwg\'s ({len(orphans)}) &middot; .dwg-bestand aanwezig, '
            f'maar geen regel in deze symbolentabel</th></tr>')
        pad_span = ncols - 1 if ncols > 1 else 1
        for naam, pad in orphans:
            body.append(
                f'<tr class="orphan"><td>{_esc(naam)}.dwg</td>'
                f'<td class="weespad" colspan="{pad_span}">{_esc(pad)}</td></tr>')

    versie_txt = ""
    if version_new or version_old:
        versie_txt = (f" &middot; {_esc(version_old or '?')} "
                      f"&rarr; {_esc(version_new or '?')}")
    info = (f"{stats['new']} nieuw &middot; {stats['changed']} gewijzigd &middot; "
            f"{stats['deleted']} vervallen"
            + (f" &middot; {len(orphans)} wees-.dwg" if orphans else "")
            + f" &middot; {len(rows)} rijen totaal"
            + versie_txt)

    legend = (
        '<div class="legend">'
        '<span><span class="swatch sw-new"></span> nieuwe rij</span>'
        '<span><span class="swatch sw-changed"></span> gewijzigde cel '
        '(oud doorgestreept, nieuw in blauw)</span>'
        '<span><span class="swatch sw-deleted"></span> vervallen rij</span>'
        + ('<span><span class="swatch sw-wees"></span> wees-.dwg '
           '(geen tabelregel)</span>' if orphans else "")
        + '</div>')

    # Melding bovenaan wanneer er niets aan de tabel is veranderd (geen nieuwe,
    # gewijzigde of vervallen rijen). Wees-.dwg's tellen niet als tabelwijziging.
    geen_wijzigingen = (stats["new"] == 0 and stats["changed"] == 0
                        and stats["deleted"] == 0)
    banner = ""
    if geen_wijzigingen:
        banner = (f'<p class="geen-wijzigingen">Versie '
                  f'{_esc(version_new or "?")} bevat geen wijzigingen ten '
                  f'opzichte van versie {_esc(version_old or "?")}.</p>\n')

    return (
        _shell_head(title, extra_style=_CHANGELOG_STYLE, cdn=False)
        + f'<div class="wrap">\n{banner}<p class="info">{info}</p>\n{legend}\n'
        + '<div class="tablescroll">\n<table class="otab">\n<thead>\n'
        + f"<tr>{head_cells}</tr>\n</thead>\n<tbody>\n"
        + "\n".join(body)
        + "\n</tbody>\n</table>\n</div>\n</div>\n"
        + _FOOTER
    )


# ---------------------------------------------------------------------------
# 3. Publicatie-overzicht ("kaart"): één blok per hoofdgroep met knoppen
# ---------------------------------------------------------------------------
_INDEX_STYLE = """
    .card-grid { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr));
                 gap: 18px; align-items: start; }
    @media (max-width: 1180px) { .card-grid { grid-template-columns: repeat(3, minmax(0,1fr)); } }
    @media (max-width: 900px)  { .card-grid { grid-template-columns: repeat(2, minmax(0,1fr)); } }
    @media (max-width: 600px)  { .card-grid { grid-template-columns: 1fr; } }

    .card { background:#fff; border:1px solid var(--dg-grey);
            border-top:5px solid var(--dg-yellow); border-radius:6px;
            padding:14px 16px 16px; display:flex; flex-direction:column;
            min-height:210px; box-shadow:0 1px 3px rgba(0,0,0,.06); }
    .card.general { border-top-color: var(--dg-blue); }
    .card h2 { margin:0; font-size:1.2rem; color:var(--dg-ink); }
    .card .subtitle { color:var(--dg-grey2); font-size:.8rem; margin:2px 0 10px; }
    .card .section-lbl { font-size:.7rem; text-transform:uppercase; letter-spacing:.5px;
            color:var(--dg-grey2); font-weight:700; margin:10px 0 5px; }
    .card .section-lbl:first-of-type { margin-top:4px; }
    .card .empty { color:var(--dg-grey2); font-style:italic; font-size:.85rem; }

    .btn { display:block; text-decoration:none; color:var(--dg-ink);
            border:1px solid var(--dg-grey); border-left:4px solid var(--dg-grey2);
            border-radius:4px; padding:6px 9px; margin:4px 0; font-size:.86rem;
            background:#fbfbfb; transition:background .12s, border-color .12s; }
    a.btn:hover { background:#FFF8CC; }
    a.btn.tabel { border-left-color: var(--dg-green); }
    a.btn.changelog { border-left-color: var(--dg-blue); }
    span.btn.nvt { color:var(--dg-grey2); background:#f4f4f4;
            border-style:dashed; border-left-color:var(--dg-grey);
            cursor:default; font-style:italic; }
"""


def build_index_html(groups, general, title: str = "NLCS publicatie-overzicht",
                     version: str = "", base_url: str = "") -> str:
    """Overzichtspagina ('kaart') met één blok per hoofdgroep en knoppen naar de
    gepubliceerde tabellen en changelogs.

    groups  : lijst (code, [entry, ...]) zoals ot_compare.scan_publication levert.
    general : lijst entries voor het algemene blok ('voor alle hoofdgroepen').
    base_url: online basis (bijv. 'https://nl-digigo.github.io/NLCS/'); het
              entry-subpad wordt eraan geplakt. Leeg -> relatieve links.
    Elke entry heeft: filename, subpath, kind ('tabel'|'changelog'), label."""
    base = (base_url or "").strip()
    if base and not base.endswith("/"):
        base += "/"

    def _btn(entry: dict) -> str:
        url = (base + entry["subpath"]) if base else entry["subpath"]
        cls = "changelog" if entry.get("kind") == "changelog" else "tabel"
        return (f'<a class="btn {cls}" href="{_esc(url)}" target="_blank" '
                f'title="{_esc(entry["filename"])}">{_esc(entry["label"])}</a>')

    def _card(heading: str, subtitle: str, entries: list, general: bool) -> str:
        tabellen = [e for e in entries if e.get("kind") != "changelog"]
        changelogs = [e for e in entries if e.get("kind") == "changelog"]
        parts = [f'<div class="card{" general" if general else ""}">',
                 f"<h2>{_esc(heading)}</h2>",
                 f'<p class="subtitle">{_esc(subtitle)}</p>']
        if tabellen:
            parts.append('<div class="section-lbl">Tabellen</div>')
            parts += [_btn(e) for e in tabellen]
        if changelogs:
            parts.append('<div class="section-lbl">Changelogs</div>')
            parts += [_btn(e) for e in changelogs]
        # Per hoofdgroep (niet in het algemene blok): een knop-zonder-link
        # "<categorie> nvt" tonen voor elke categorie waarvoor geen enkel
        # bestand aanwezig is.
        if not general:
            fnames = " ".join(e.get("filename", "").lower() for e in entries)
            ontbreekt = [woord for woord in ("symbolen", "lijntypes", "arceringen")
                         if woord not in fnames]
            if ontbreekt:
                parts.append('<div class="section-lbl">Niet van toepassing</div>')
                parts += [f'<span class="btn nvt">{w} nvt</span>' for w in ontbreekt]
        if not entries:
            parts.append('<p class="empty">geen bestanden</p>')
        parts.append("</div>")
        return "\n".join(parts)

    cards = []
    if general:
        cards.append(_card("Voor alle hoofdgroepen",
                           f"{len(general)} algemeen bestand(en)", general, True))
    for code, entries in groups:
        cards.append(_card(code, f"hoofdgroep {code} &middot; "
                           f"{len(entries)} bestand(en)", entries, False))

    total = sum(len(e) for _c, e in groups) + len(general)
    info = (f"{len(groups)} hoofdgroep(en) &middot; {total} bestand(en)"
            + (f" &middot; versie {_esc(version)}" if version else "")
            + (f' &middot; <a href="{_esc(base)}" target="_blank">{_esc(base)}</a>'
               if base else ""))

    body = ('<p class="empty">Geen gepubliceerde bestanden gevonden voor deze '
            'versie.</p>' if not cards else
            '<div class="card-grid">\n' + "\n".join(cards) + "\n</div>")

    return (
        _shell_head(title, extra_style=_INDEX_STYLE, cdn=False)
        + f'<div class="wrap">\n<p class="info">{info}</p>\n'
        + body + "\n"
        + "</div>\n"
        + _FOOTER
    )


# ---------------------------------------------------------------------------
# 4. Wees-.dwg's: bestanden zonder een regel in de symbolentabel
# ---------------------------------------------------------------------------
_ORPHAN_STYLE = """
    table.otab tbody td { white-space: normal; }
    table.otab tbody tr:nth-child(even) td { background-color: #fafafa; }
    p.leeg { color: var(--dg-green); font-weight: 600; }
"""


def build_orphans_html(orphans, title: str, symbols_dir: str = "",
                       version_new: str = "") -> str:
    """Pagina met de .dwg-bestanden die bij GEEN enkele regel in de
    symbolentabellen horen.

    orphans : lijst (bestandsnaam, relatief pad t.o.v. de symbolenmap),
              alfabetisch op bestandsnaam."""
    src = (f" &middot; map: {_esc(symbols_dir)}" if symbols_dir else "")
    ver = (f" &middot; versie {_esc(version_new)}" if version_new else "")
    info = f"{len(orphans)} .dwg-bestand(en) zonder regel in de symbolentabellen{ver}{src}"

    if orphans:
        head = "<tr><th>#</th><th>bestand (.dwg)</th><th>pad in de map</th></tr>"
        body = "\n".join(
            f"<tr><td>{i}</td><td>{_esc(naam)}.dwg</td><td>{_esc(pad)}</td></tr>"
            for i, (naam, pad) in enumerate(orphans, start=1))
        table = ('<div class="tablescroll">\n<table class="otab">\n<thead>\n'
                 f"{head}\n</thead>\n<tbody>\n{body}\n</tbody>\n</table>\n</div>\n")
    else:
        table = ('<p class="leeg">Alle .dwg-bestanden in de map horen bij een '
                 'regel in de symbolentabellen.</p>\n')

    return (
        _shell_head(title, extra_style=_ORPHAN_STYLE, cdn=False)
        + f'<div class="wrap">\n<p class="info">{info}</p>\n'
        + table
        + "</div>\n"
        + _FOOTER
    )


def build_missing_dwg_html(missing, title: str, symbols_dir: str = "",
                           version_new: str = "") -> str:
    """Pagina met de regels in de symbolentabellen waarvoor GEEN .dwg-bestand in
    de map gevonden is — de omgekeerde controle van build_orphans_html
    (bestand zonder regel <-> regel zonder bestand).

    missing : lijst (symboolnaam, hoofdgroepcode), gesorteerd op hoofdgroep+naam."""
    src = (f" &middot; map: {_esc(symbols_dir)}" if symbols_dir else "")
    ver = (f" &middot; versie {_esc(version_new)}" if version_new else "")
    info = (f"{len(missing)} regel(s) in de symbolentabellen zonder "
            f".dwg-bestand{ver}{src}")

    if missing:
        head = ("<tr><th>#</th><th>symbool (regel)</th><th>hoofdgroep</th>"
                "<th>verwacht bestand</th></tr>")
        body = "\n".join(
            f"<tr><td>{i}</td><td>{_esc(naam)}</td><td>{_esc(code)}</td>"
            f"<td>{_esc(naam)}.dwg</td></tr>"
            for i, (naam, code) in enumerate(missing, start=1))
        table = ('<div class="tablescroll">\n<table class="otab">\n<thead>\n'
                 f"{head}\n</thead>\n<tbody>\n{body}\n</tbody>\n</table>\n</div>\n")
    else:
        table = ('<p class="leeg">Bij elke regel in de symbolentabellen is een '
                 '.dwg-bestand gevonden.</p>\n')

    return (
        _shell_head(title, extra_style=_ORPHAN_STYLE, cdn=False)
        + f'<div class="wrap">\n<p class="info">{info}</p>\n'
        + table
        + "</div>\n"
        + _FOOTER
    )


# ---------------------------------------------------------------------------
# 6. Controle-rapporten (ID-controle en Optie-fase-check) als HTML
# ---------------------------------------------------------------------------
_CHECK_STYLE = """
    .wrap { max-width: 1100px; }
    .card { background:#fff; border:1px solid var(--dg-grey); border-radius:8px;
            padding:16px 18px; margin-bottom:18px; box-shadow:0 1px 3px rgba(0,0,0,.05); }
    .card h2 { margin:0 0 8px; font-size:1.2rem; border-bottom:3px solid var(--dg-yellow);
               padding-bottom:6px; }
    .card h3 { margin:16px 0 6px; font-size:.98rem; color:var(--dg-ink); }
    .kpi { display:flex; gap:14px; flex-wrap:wrap; margin:10px 0 4px; }
    .kpi .box { background:#fafafa; border:1px solid var(--dg-grey); border-radius:6px;
                padding:6px 14px; font-size:.85rem; color:var(--dg-grey2); }
    .kpi .box b { display:block; font-size:1.3rem; font-weight:700; color:var(--dg-ink); }
    .kpi .box.free { border-color:var(--dg-green); background:#f0f8ef; }
    .kpi .box.free b { color:var(--dg-green); }
    p.ok { color:var(--dg-green); font-weight:600; margin:8px 0; }
    p.warn { color:var(--dg-red); font-weight:700; margin:14px 0 4px; }
    p.skip { color:var(--dg-grey2); font-style:italic; }
    table.otab { width:100%; margin:4px 0 10px; }
    table.otab tbody td { white-space:normal; }
    table.otab tbody tr:nth-child(even) td { background:#fafafa; }
    td.num { text-align:right; font-family:Consolas,"Courier New",monospace;
             white-space:nowrap; }
    td.loc { color:var(--dg-grey2); white-space:nowrap; font-size:.8rem; }
    .is-was { font-family:Consolas,"Courier New",monospace; }
    .is-was .is { color:var(--dg-red); }
    .is-was .exp { color:var(--dg-green); font-weight:600; }
"""


def _name_of(rec) -> str:
    """Mensleesbare naam voor een ID-record; valt terug op de URI."""
    return rec.get("name") or rec.get("uri") or "(geen naam)"


def _otab(head_cells: str, rows: list[str]) -> str:
    return ('<table class="otab"><thead><tr>' + head_cells
            + '</tr></thead><tbody>\n' + "\n".join(rows) + '\n</tbody></table>')


def build_id_report_html(sections, title: str = "ID-controle",
                         version_new: str = "", version_old: str = "") -> str:
    """Rapportpagina voor de ID-controle (tabblad 'ID's').

    sections : lijst dicts per soort met
        {"label", "id_col", "woord", "skipped"(bool), "res"(analyze_ids-dict|None)}.
    """
    cards = []
    for s in sections:
        label = s["label"]
        if s.get("skipped") or not s.get("res"):
            cards.append(
                f'<div class="card"><h2>{_esc(label)}</h2>'
                '<p class="skip">Overgeslagen: geen geldige map/bestand ingevuld '
                'bij ‘Locaties’.</p></div>')
            continue
        res = s["res"]
        id_col = s["id_col"]
        parts = [f'<div class="card"><h2>{_esc(label)}</h2>']
        ing = len(res["new"]) + len(res["old"])
        parts.append(
            '<div class="kpi">'
            f'<div class="box"><b>{ing}</b>ingelezen '
            f'({len(res["new"])} nieuw / {len(res["old"])} vorig)</div>'
            f'<div class="box"><b>{res["highest"]}</b>hoogste ID</div>'
            f'<div class="box free"><b>{res["next_free"]}</b>'
            'eerstvolgende vrije ID</div></div>')

        # Rijen zonder ID.
        bn = res["blanks_new"]
        bo = res["blanks_old"]
        if bn or bo:
            parts.append(f'<h3>Zonder {_esc(id_col)}: {len(bn) + len(bo)} '
                         f'({len(bn)} nieuw, {len(bo)} vorig)</h3>')
            rows = []
            for i, rec in enumerate(bn):
                rows.append(
                    f'<tr><td class="num">{res["next_free"] + i}</td>'
                    f'<td>{_esc(_name_of(rec))}</td><td>nieuw</td>'
                    f'<td class="loc">{_esc(rec["file"])} r{rec["row"]}</td></tr>')
            for rec in bo:
                rows.append(
                    '<tr><td class="num">—</td>'
                    f'<td>{_esc(_name_of(rec))}</td><td>vorig</td>'
                    f'<td class="loc">{_esc(rec["file"])} r{rec["row"]}</td></tr>')
            parts.append(_otab(
                '<th>voorgesteld ID</th><th>naam</th><th>publicatie</th>'
                '<th>bestand (rij)</th>', rows))
        else:
            parts.append(f'<p class="ok">✓ Elke rij heeft een {_esc(id_col)}.</p>')

        # Dubbele ID's.
        dups = res["duplicates"]
        if dups:
            parts.append(f'<p class="warn">⚠ {len(dups)} dubbel gebruikte '
                         'ID(’s)</p>')
            rows = []
            for d in dups:
                for rec in d["records"]:
                    rows.append(
                        f'<tr><td class="num">{_esc(d["id"])}</td>'
                        f'<td>{_esc(_name_of(rec))}</td>'
                        f'<td>{_esc(rec["source"])}</td>'
                        f'<td class="loc">{_esc(rec["file"])} r{rec["row"]}</td></tr>')
            parts.append(_otab(
                '<th>ID</th><th>naam</th><th>publicatie</th><th>bestand (rij)</th>',
                rows))
        else:
            parts.append('<p class="ok">✓ Geen dubbel gebruikte ID’s.</p>')

        # Verschillend ID voor dezelfde URI.
        mism = res["mismatches"]
        if mism:
            parts.append(f'<p class="warn">⚠ {len(mism)} met een verschillend '
                         'ID in de vorige en nieuwe publicatie</p>')
            rows = []
            for m in mism:
                naam = m.get("name") or m.get("uri") or "(geen naam)"
                rows.append(
                    f'<tr><td>{_esc(naam)}</td>'
                    f'<td class="num">{_esc(m["new_id"])}</td>'
                    f'<td class="num">{_esc(m["old_id"])}</td></tr>')
            parts.append(_otab('<th>naam</th><th>nieuw ID</th><th>vorig ID</th>', rows))
        else:
            parts.append('<p class="ok">✓ Elke URI heeft in beide publicaties '
                         'hetzelfde ID.</p>')

        # Niet-gehele ID's.
        nonint = res["noninteger"]
        if nonint:
            parts.append(f'<h3>Niet-gehele ID’s genegeerd: {len(nonint)}</h3>')
            rows = [
                f'<tr><td class="num">{_esc(rec["id"])}</td>'
                f'<td>{_esc(_name_of(rec))}</td><td>{_esc(rec["source"])}</td>'
                f'<td class="loc">{_esc(rec["file"])} r{rec["row"]}</td></tr>'
                for rec in nonint]
            parts.append(_otab(
                '<th>ID</th><th>naam</th><th>publicatie</th><th>bestand (rij)</th>',
                rows))
        parts.append('</div>')
        cards.append("\n".join(parts))

    ver = ""
    if version_new or version_old:
        ver = f" &middot; {_esc(version_old or '?')} &rarr; {_esc(version_new or '?')}"
    info = f"Controle van de ID-nummers per soort{ver}"
    body = "\n".join(cards) if cards else '<p class="info">Geen bronnen.</p>'
    return (
        _shell_head(title, extra_style=_CHECK_STYLE, cdn=False)
        + f'<div class="wrap">\n<p class="info">{info}</p>\n{body}\n</div>\n'
        + _FOOTER
    )


def build_fase_optie_html(sections, title: str = "Optie-fase-check",
                          version_new: str = "") -> str:
    """Rapportpagina voor de optie-fase-check (tabblad 'Optie-fase-check').

    sections : lijst dicts per soort met
        {"label", "skipped"(bool), "violations"(lijst check_fase_optie-dicts)}.
    """
    cards = []
    total = 0
    for s in sections:
        label = s["label"]
        if s.get("skipped"):
            cards.append(
                f'<div class="card"><h2>{_esc(label)}</h2>'
                '<p class="skip">Overgeslagen: geen geldige map/bestand ingevuld '
                'bij ‘Locaties’.</p></div>')
            continue
        viol = s.get("violations") or []
        total += len(viol)
        parts = [f'<div class="card"><h2>{_esc(label)}</h2>']
        if not viol:
            parts.append('<p class="ok">✓ Alle ‘fase’ en '
                         '‘optie’ kloppen met de naam.</p>')
        else:
            fase = [v for v in viol if v["kind"] == "fase"]
            optie = [v for v in viol if v["kind"] == "optie"]
            for titel, items, col in (("FASE-afwijkingen", fase, "fase"),
                                      ("OPTIE-afwijkingen", optie, "optie")):
                if not items:
                    continue
                parts.append(f'<p class="warn">⚠ {titel}: {len(items)}</p>')
                rows = []
                for v in items:
                    got = v["got"] or "(leeg)"
                    exp = v["expected"] or "(leeg)"
                    rows.append(
                        f'<tr><td>{_esc(v["name"])}</td>'
                        f'<td class="is-was"><span class="is">{_esc(got)}</span> '
                        f'&rarr; <span class="exp">{_esc(exp)}</span></td>'
                        f'<td class="loc">{_esc(v["file"])} r{v["row"]}</td></tr>')
                parts.append(_otab(
                    f'<th>naam</th><th>{_esc(col)} (is &rarr; verwacht)</th>'
                    '<th>bestand (rij)</th>', rows))
        parts.append('</div>')
        cards.append("\n".join(parts))

    ver = f" &middot; versie {_esc(version_new)}" if version_new else ""
    info = f"{total} afwijking(en) in totaal{ver}"
    body = "\n".join(cards) if cards else '<p class="info">Geen bronnen.</p>'
    return (
        _shell_head(title, extra_style=_CHECK_STYLE, cdn=False)
        + f'<div class="wrap">\n<p class="info">{info}</p>\n{body}\n</div>\n'
        + _FOOTER
    )
