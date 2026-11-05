"""bgt_changelog.py - BGT-mapping: tabelpagina (alle kolommen, sorteerbaar/
filterbaar) + changelog tussen twee versies, in digiGO-stijl.

Hergebruikt ot_compare.compare (match op de unieke 'uri'-kolom) en de
ot_html-bouwstenen (build_full_html / build_changelog_html).
"""
import collections
import os
import re

import ot_compare
import ot_html

# Versie-informatie uit een mapping-bestandsnaam. Twee versies: de NLCS-versie en
# de versie van de andere standaard (bv. BGT). Vorm van de naam:
#   NLCS-<nlcs>-<naam>[-<std>]        (CSV; std optioneel)
# bijv. NLCS-5-2-BGT.csv -> (5-2, BGT, '')   NLCS-5-2-BGT-1-2.csv -> (5-2, BGT, 1-2)
MapVer = collections.namedtuple("MapVer", "nlcs naam std")
_RE_MAPNAME = re.compile(
    r"^NLCS[-_ ]*(\d+[.\-]\d+)-(.+?)(?:-(\d+[.\-]\d+))?$", re.IGNORECASE)


def parse_mapping_name(path: str):
    """(nlcs, naam, std) uit de bestandsnaam, of None. 'std' = '' als afwezig."""
    stem = os.path.splitext(os.path.basename(path or ""))[0]
    stem = re.sub(r"(?i)^changelog-", "", stem)
    m = _RE_MAPNAME.match(stem)
    if not m:
        return None
    norm = lambda v: v.replace(".", "-") if v else ""  # noqa: E731
    return MapVer(norm(m.group(1)), m.group(2), norm(m.group(3)))


def _snapshot_name(mv: "MapVer") -> str:
    """NLCS<nlcs>-<naam><std>  (bv. NLCS5-2-BGT1-2 of NLCS5-2-BGT)."""
    return f"NLCS{mv.nlcs}-{mv.naam}{mv.std}"


def _snapshot_label(mv: "MapVer") -> str:
    return f"NLCS {mv.nlcs}" + (f" · {mv.naam} {mv.std}" if mv.std else "")


def changelog_name(new: "MapVer", old: "MapVer") -> str:
    """Bestandsnaam (zonder .html) voor de changelog; detecteert welke as wijzigt:
    NLCS-as (standaard gelijk), standaard-as (NLCS gelijk), of beide."""
    if old.nlcs != new.nlcs and old.std == new.std:
        return f"changelog-NLCS{old.nlcs}-{new.nlcs}-{new.naam}{new.std}"
    if old.std != new.std and old.nlcs == new.nlcs:
        return f"changelog-NLCS{new.nlcs}-{new.naam}{old.std}-{new.std}"
    return f"changelog-{_snapshot_name(old)}-{_snapshot_name(new)}"


KEY = "uri"              # unieke kolom per BGT-object
IGNORE_CHANGE = ["id"]   # doorlopend volgnummer -> nooit als 'wijziging' tellen
_TEXT_FILTER_MIN = 30    # kolommen met >30 unieke waarden -> vrij zoekveld

# Vaste horizontale schuifbalk onderaan het scherm, gekoppeld aan het brede
# DataTables-scrollvenster. De ingebouwde horizontale balk (binnen het
# scrollvenster) wordt verborgen; deze balk staat altijd onderin beeld, zodat je
# bij een brede tabel makkelijk naar rechts kunt voor het overzicht.
_BOTTOM_BAR = """
<style>
  div.dataTables_scrollBody { overflow-x: hidden !important; }
  #hscroll-bar { position: fixed; left: 0; right: 0; bottom: 0; height: 18px;
    overflow-x: auto; overflow-y: hidden; z-index: 9999;
    background: #ececec; border-top: 1px solid var(--dg-grey, #767676);
    display: none; }
  #hscroll-bar > div { height: 1px; }
  body { padding-bottom: 20px; }
</style>
<script>
(function () {
  function setup() {
    var body = document.querySelector('div.dataTables_scrollBody');
    if (!body) { return; }
    var bar = document.getElementById('hscroll-bar');
    if (!bar) {
      bar = document.createElement('div'); bar.id = 'hscroll-bar';
      var inner = document.createElement('div'); bar.appendChild(inner);
      document.body.appendChild(bar);
    }
    var inner = bar.firstChild;
    var lock = false;
    function sync() {
      var sw = body.scrollWidth, cw = body.clientWidth;
      if (sw > cw + 2) { inner.style.width = sw + 'px'; bar.style.display = 'block'; }
      else { bar.style.display = 'none'; }
    }
    bar.addEventListener('scroll', function () {
      if (lock) { return; } lock = true; body.scrollLeft = bar.scrollLeft; lock = false;
    });
    body.addEventListener('scroll', function () {
      if (lock) { return; } lock = true; bar.scrollLeft = body.scrollLeft; lock = false;
    });
    window.addEventListener('resize', sync);
    sync(); setTimeout(sync, 300); setTimeout(sync, 1200);
  }
  if (document.readyState !== 'loading') { setTimeout(setup, 400); }
  else { document.addEventListener('DOMContentLoaded', function () { setTimeout(setup, 400); }); }
})();
</script>
"""


def _with_bottom_bar(html: str) -> str:
    """Voeg de vaste horizontale schuifbalk toe vlak voor </body>."""
    i = html.rfind("</body>")
    return html[:i] + _BOTTOM_BAR + html[i:] if i != -1 else html + _BOTTOM_BAR


def _text_columns(headers, rows, vis):
    out = []
    for i in vis:
        uniq = {(r[i] if i < len(r) else "").strip() for r in rows}
        uniq.discard("")
        if len(uniq) > _TEXT_FILTER_MIN:
            out.append(headers[i])
    return out


def _fallback_mv(path: str) -> "MapVer":
    """Terugval als de naam niet te parsen is: hele stem als 'naam'."""
    stem = os.path.splitext(os.path.basename(path or ""))[0]
    return MapVer("", stem, "")


def build_table_page(csv_path: str, out_dir: str) -> str:
    """Schrijf de volledige mappingtabel (alle kolommen op URI's na, sorteerbaar/
    filterbaar, vaste schuifbalk). Naam = NLCS<nlcs>-<naam><std>.html, afgeleid
    uit de CSV-naam. Geeft het geschreven pad terug."""
    mv = parse_mapping_name(csv_path) or _fallback_mv(csv_path)
    headers, rows = ot_compare.read_table(csv_path)
    result = {"headers": headers,
              "rows": [{"cells": [{"value": (r[i] if i < len(r) else "")}
                                  for i in range(len(headers))]} for r in rows]}
    vis = ot_compare.non_uri_column_indices(headers, rows)   # geen URI-kolommen
    title = f"{mv.naam}-mapping"
    html = ot_html.build_full_html(
        result, title, version_new=_snapshot_label(mv), visible_indices=vis,
        text_columns=_text_columns(headers, rows, vis), paginate=False)
    out_path = os.path.join(out_dir, (_snapshot_name(mv) if mv.nlcs else mv.naam)
                            + ".html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(_with_bottom_bar(html))
    return out_path


def build_changelog_page(new_csv: str, old_csv: str, out_dir: str,
                         key: str = KEY, ignore_change=None):
    """Schrijf de mapping-changelog (toegevoegd/vervallen/gewijzigd op `key`,
    URI-kolommen verborgen, vaste schuifbalk). Naam via changelog_name() op basis
    van de versies in de twee CSV-namen. Geeft (pad, stats-dict) terug.
    `key`/`ignore_change` maken de functie herbruikbaar voor GWSW/RI."""
    mv_new = parse_mapping_name(new_csv) or _fallback_mv(new_csv)
    mv_old = parse_mapping_name(old_csv) or _fallback_mv(old_csv)
    result = ot_compare.compare(new_csv, old_csv, key=key,
                                ignore_change_cols=ignore_change or IGNORE_CHANGE)
    headers = result["headers"]
    _, new_rows = ot_compare.read_table(new_csv)
    vis = ot_compare.non_uri_column_indices(headers, new_rows)  # geen URI-kolommen
    title = f"{mv_new.naam}-mapping — changelog"
    html = ot_html.build_changelog_html(
        result, title, version_new=_snapshot_label(mv_new),
        version_old=_snapshot_label(mv_old), visible_indices=vis, sortable=True,
        separate_deleted=True)
    out_path = os.path.join(out_dir, changelog_name(mv_new, mv_old) + ".html")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(_with_bottom_bar(html))
    return out_path, result["stats"]
