"""
docs_overview.py - Overzicht van alle gepubliceerde documenten in de docs-map.

Scant een map (standaard de NLCS 'docs'-map) recursief naar HTML-documenten en
maakt daar één overzicht van: per map een blok, met geneste blokken voor
submappen. Elk document krijgt de naam uit de <title> van de HTML; ontbreekt die,
dan de bestandsnaam.

Twee uitvoeren met dezelfde inhoud:
  * build_html()     -> digiGO-huisstijl-pagina (geneste blokken, klikbare links)
  * build_markdown() -> plat Markdown-overzicht (geneste kopjes + lijsten)

De mappen 'changelog' en 'archive' worden standaard overgeslagen (changelog bevat
honderden automatisch gegenereerde detailpagina's; archive bevat oude versies).
"""

from __future__ import annotations

import datetime
import html as _html
import os
import re

import ot_html


# Mappen die standaard niet in het overzicht komen (op naam, elk niveau).
#   changelog/archive : automatisch gegenereerde detailpagina's / oude versies
#   reviewversies     : tussentijdse review-exports, niet de publicatie
DEFAULT_EXCLUDE = {"changelog", "archive", "reviewversies"}

# Alleen deze extensies gelden als 'document'.
_DOC_EXTS = (".html", ".htm")

_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.IGNORECASE | re.DOTALL)

# ReSpec-documenten (stichting-crow/digiGO-profiel) hebben naast de HTML een
# config.js met `specStatus: "XXX"`. Deze code -> (Nederlands label, kleur),
# overgenomen uit het stichting-crow ReSpec-profiel (name_nl + hex).
_STATUS_RE = re.compile(r"""specStatus\s*:\s*['"]([A-Za-z]+)['"]""")

STATUS_MAP = {
    "LD":    ("levend document", "#009de0"),
    "IR":    ("referentieversie", "#007e84"),
    "DRAFT": ("werkdocument", "#409d69"),
    "DOC":   ("document", "#dee4e9"),
    "REG":   ("register", "#dee4e9"),
    "PFB":   ("projectbeschrijving", "#a1c036"),
    "NP":    ("projectvoorstel", "#a1c036"),
    "WD":    ("werkconcept", "#409d69"),
    "CR":    ("in consultatie", "#007e84"),
    "PR":    ("ter vaststelling", "#007e84"),
    "OR":    ("tervisielegging", "#007e84"),
    "DEF":   ("vastgesteld", "#009de0"),
    "REPL":  ("vervangen", "#ff6e1a"),
    "RESC":  ("teruggetrokken", "#ff6e1a"),
    "RQR":   ("niet onderhouden", "#6e6e6e"),
}


# ---------------------------------------------------------------------------
# Scannen
# ---------------------------------------------------------------------------
def extract_title(path: str) -> str:
    """De <title> van een HTML-bestand (ontdaan van tags/witruimte). Leeg als er
    geen bruikbare title is."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            # De <title> staat in de <head>; eerste ~16 kB is ruim voldoende.
            head = f.read(16384)
    except OSError:
        return ""
    m = _TITLE_RE.search(head)
    if not m:
        return ""
    txt = re.sub(r"<[^>]+>", "", m.group(1))        # eventuele tags binnen title
    txt = _html.unescape(txt)
    txt = re.sub(r"\s+", " ", txt).strip()
    return txt


# Versie-herkenning uit een mapnaam of bestandsnaam.
#   - een heel pad-segment dat een versie is: "5", "5-2", "5.2", "5-0-2"
#   - of een versie-token in de bestandsnaam: "...-5-2", "...-5.1"
VERSION_RE = re.compile(r"^v?\d+([.-]\d+)*$", re.IGNORECASE)
VER_TOKEN_RE = re.compile(r"(?<![\d.])(\d+(?:[.-]\d+)+)(?![\d.])")

# Pagina's die in de (uitgesloten) changelog-map staan maar tóch per versie in
# het overzicht horen: het publicatie-overzicht en de (hoofd-)release-notes.
# Let op: de per-hoofdgroep release notes (changelog/<CODE>/releasenotes-...-XX)
# willen we NIET; alleen de hoofd-release-notes in changelog/releasenotes/.
def _is_special(fname: str, dirpath: str) -> bool:
    low = fname.lower()
    if low.startswith("publicatieoverzicht"):
        return True
    if (low.startswith("releasenotes")
            and os.path.basename(dirpath).lower() == "releasenotes"):
        return True
    return False

# Blok voor documenten zonder versie.
HANDLEIDINGEN = "Handleidingen"


def normalize_version(seg: str) -> str:
    """'5-0-2' -> '5.0.2', '5-2' -> '5.2', 'v5.1' -> '5.1'."""
    return seg.lstrip("vV").replace("-", ".")


def _version_tuple(label: str) -> tuple:
    try:
        return tuple(int(x) for x in label.split("."))
    except ValueError:
        return (0,)


def detect_version(rel_posix: str) -> str | None:
    """Versie uit het pad: eerst een heel map-segment dat een versie is, anders
    een versie-token in de bestandsnaam. None als er geen versie in zit."""
    parts = rel_posix.split("/")
    for seg in parts[:-1]:
        if VERSION_RE.match(seg):
            return normalize_version(seg)
    m = VER_TOKEN_RE.search(os.path.splitext(parts[-1])[0])
    if m:
        return normalize_version(m.group(1))
    return None


def extract_status(folder: str, cache: dict) -> str:
    """De ReSpec-specStatus-code (bijv. 'DEF') uit config.js naast het document.
    Leeg als er geen config.js/specStatus is. Gecachet per map."""
    if folder in cache:
        return cache[folder]
    code = ""
    cfg = os.path.join(folder, "config.js")
    if os.path.isfile(cfg):
        try:
            with open(cfg, "r", encoding="utf-8", errors="ignore") as f:
                m = _STATUS_RE.search(f.read(16384))
            if m:
                code = m.group(1).upper()
        except OSError:
            pass
    cache[folder] = code
    return code


def _doc_kind(fname: str) -> str:
    low = fname.lower()
    if low.startswith("publicatieoverzicht"):
        return "publicatieoverzicht"
    if low.startswith("releasenotes"):
        return "releasenotes"
    return "doc"


def _doc_entry(full: str, root: str, out_dir: str, status_cache: dict) -> dict:
    """Eén document-record met titel, status, versie en relatieve links."""
    fname = os.path.basename(full)
    title = extract_title(full) or os.path.splitext(fname)[0]
    rel = os.path.relpath(full, root).replace("\\", "/")
    code = extract_status(os.path.dirname(full), status_cache)
    label, color = STATUS_MAP.get(code, ("", ""))
    return {
        "title": title,
        "filename": fname,
        "href": os.path.relpath(full, out_dir).replace("\\", "/"),
        "rel": rel,
        "version": detect_version(rel),
        "kind": _doc_kind(fname),
        "status": code,
        "status_label": label,
        "status_color": color,
    }


def _doc_sort_key(d: dict):
    # publicatie-overzicht en release notes bovenaan het versieblok, daarna de
    # rest op pad/titel; index.html vóór losse bestanden in dezelfde map.
    kind_order = {"publicatieoverzicht": 0, "releasenotes": 1}.get(d["kind"], 2)
    is_index = 0 if os.path.splitext(d["filename"])[0].lower() == "index" else 1
    return (kind_order, d["rel"].lower(), is_index, d["title"].lower())


def scan(root: str, out_dir: str, exclude=None) -> dict:
    """Scan `root` recursief en groepeer de documenten per versie (uit de
    mapnaam) plus één blok 'Handleidingen' voor documenten zonder versie.

    De mappen in `exclude` (standaard changelog/archive) worden overgeslagen,
    behalve het publicatie-overzicht en de release notes per versie: die staan
    in de changelog-map maar horen wél in het overzicht.

    Geeft terug: {"versions": [(label, [docs]), ...] (nieuw->oud),
                  "handleidingen": [docs], "total": n, "source": naam}."""
    exclude = {e.lower() for e in (exclude if exclude is not None else DEFAULT_EXCLUDE)}
    root = os.path.abspath(root)
    out_dir = os.path.abspath(out_dir)
    status_cache: dict = {}

    docs: list[dict] = []
    for dirpath, dirnames, filenames in os.walk(root):
        rel_dir = os.path.relpath(dirpath, root).replace("\\", "/")
        segs = [] if rel_dir == "." else rel_dir.split("/")
        in_excluded = any(s.lower() in exclude for s in segs)
        # In een uitgesloten tak alleen de 'speciale' pagina's meenemen; de rest
        # overslaan. Buiten een uitgesloten tak: alle documenten.
        for fn in filenames:
            if not fn.lower().endswith(_DOC_EXTS):
                continue
            if in_excluded and not _is_special(fn, dirpath):
                continue
            docs.append(_doc_entry(os.path.join(dirpath, fn), root, out_dir,
                                   status_cache))
        # submappen die zelf uitgesloten zijn niet verder aflopen, tenzij ze
        # mogelijk speciale pagina's bevatten (changelog bevat releasenotes/).
        # We lopen ze wél af (goedkoop) zodat releasenotes-<v>.html gevonden
        # wordt, maar nemen daar alleen speciale pagina's mee (zie hierboven).

    # Groeperen per versie + handleidingen.
    by_ver: dict[str, list] = {}
    handleidingen: list[dict] = []
    for d in docs:
        if d["version"]:
            by_ver.setdefault(d["version"], []).append(d)
        else:
            handleidingen.append(d)
    for lst in by_ver.values():
        lst.sort(key=_doc_sort_key)
    handleidingen.sort(key=_doc_sort_key)

    versions = sorted(by_ver.items(),
                      key=lambda kv: _version_tuple(kv[0]), reverse=True)
    return {
        "versions": versions,
        "handleidingen": handleidingen,
        "total": len(docs),
        "source": os.path.basename(root) or root,
    }


# ---------------------------------------------------------------------------
# HTML (digiGO-huisstijl, blok per versie)
# ---------------------------------------------------------------------------
_OVERVIEW_STYLE = """
    .wrap { max-width: 1100px; }
    .doc-intro { color: var(--dg-grey2); margin: 0 0 20px; font-size: .95rem; }

    /* Versie-blok: witte kaart met gele accent-rand links. */
    section.verblok { background:#fff; border:1px solid var(--dg-grey);
        border-left:6px solid var(--dg-yellow); border-radius:4px;
        padding:14px 18px; margin:0 0 18px; }
    section.verblok.handleidingen { border-left-color:var(--dg-blue); }
    section.verblok > h2 { margin:0 0 10px; color:var(--dg-ink); font-weight:600;
        font-size:1.2rem; }
    section.verblok > h2 .count { color:var(--dg-grey2); font-weight:400;
        font-size:.8rem; margin-left:8px; }

    ul.doclist { list-style:none; margin:0; padding:0;
        display:grid; grid-template-columns:repeat(auto-fill,minmax(300px,1fr));
        gap:10px; }
    ul.doclist li { background:#f7f8f9; border:1px solid #e6e8ea; border-radius:4px;
        padding:9px 11px; }
    ul.doclist li.key { background:#fffdf0; border-color:#f3e7a6; }
    ul.doclist li a { color:#0067a3; text-decoration:none; font-weight:600;
        display:block; margin-top:2px; }
    ul.doclist li a:hover { text-decoration:underline; }
    ul.doclist li .fn { display:block; color:var(--dg-grey2);
        font-family:Consolas,"Courier New",monospace; font-size:.76rem;
        margin-top:3px; word-break:break-all; }

    .status-badge { display:inline-block; font-size:.68rem; font-weight:700;
        padding:1px 8px; border-radius:10px; text-transform:uppercase;
        letter-spacing:.3px; }
"""


def _text_on(hex_color: str) -> str:
    """Zwarte of witte tekst afhankelijk van de helderheid van de badge-kleur."""
    h = hex_color.lstrip("#")
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return "#ffffff"
    lum = 0.2126 * r + 0.7152 * g + 0.0722 * b
    return "#1d1d1b" if lum > 150 else "#ffffff"


def _badge_html(d: dict) -> str:
    if not d["status_label"]:
        return ""
    fg = _text_on(d["status_color"])
    tip = f'{d["status"]} – {d["status_label"]}'
    return (f'<span class="status-badge" title="{ot_html._esc(tip)}" '
            f'style="background:{d["status_color"]};color:{fg}">'
            f'{ot_html._esc(d["status_label"])}</span>')


def _render_block_html(heading: str, docs: list, out: list,
                       handleidingen: bool = False) -> None:
    if not docs:
        return
    cls = "verblok handleidingen" if handleidingen else "verblok"
    n = len(docs)
    out.append(f'<section class="{cls}">')
    out.append(f'  <h2>{ot_html._esc(heading)}'
               f'<span class="count">{n} document{"" if n == 1 else "en"}</span>'
               f'</h2>')
    out.append('  <ul class="doclist">')
    for d in docs:
        li_cls = ' class="key"' if d["kind"] != "doc" else ""
        badge = _badge_html(d)
        badge_line = f'{badge}' if badge else ""
        out.append(
            f'    <li{li_cls}>{badge_line}'
            f'<a href="{ot_html._esc(d["href"])}">{ot_html._esc(d["title"])}</a>'
            f'<span class="fn">{ot_html._esc(d["rel"])}</span></li>')
    out.append('  </ul>')
    out.append('</section>')


def build_html(data: dict, title: str = "Documentenoverzicht NLCS") -> str:
    """Bouw de overzichtspagina (digiGO-huisstijl) uit het scan-resultaat."""
    head = ot_html._shell_head(title, extra_style=_OVERVIEW_STYLE, cdn=False)
    today = datetime.date.today().isoformat()
    total = data["total"]
    parts = [head, '<div class="wrap">',
             f'<p class="doc-intro">Gegenereerd op {today} &middot; '
             f'{total} document{"" if total == 1 else "en"} uit '
             f'<strong>{ot_html._esc(data["source"])}</strong>, gegroepeerd per '
             f'versie. Elk document heet naar zijn HTML-titel; de gekleurde '
             f'badge toont de documentstatus (ReSpec-specStatus).</p>']
    for label, docs in data["versions"]:
        _render_block_html(f"Versie {label}", docs, parts)
    _render_block_html(HANDLEIDINGEN, data["handleidingen"], parts,
                       handleidingen=True)
    parts.append('</div>')
    parts.append(ot_html._FOOTER)
    return "\n".join(parts)


# ---------------------------------------------------------------------------
# Markdown
# ---------------------------------------------------------------------------
def _md_escape(txt: str) -> str:
    return txt.replace("|", "\\|").replace("[", "\\[").replace("]", "\\]")


def _render_block_md(heading: str, docs: list, out: list) -> None:
    if not docs:
        return
    n = len(docs)
    out.append(f'## {heading} ({n} document{"" if n == 1 else "en"})')
    out.append("")
    for d in docs:
        status = f' — {d["status_label"]} ({d["status"]})' if d["status_label"] else ""
        out.append(f'- [{_md_escape(d["title"])}]({d["href"]}){status} '
                   f'· `{d["rel"]}`')
    out.append("")


def build_markdown(data: dict, title: str = "Documentenoverzicht NLCS") -> str:
    today = datetime.date.today().isoformat()
    total = data["total"]
    out = [f"# {title}", "",
           f"_Gegenereerd op {today} · {total} "
           f"document{'' if total == 1 else 'en'} uit `{data['source']}`, "
           f"gegroepeerd per versie._", ""]
    for label, docs in data["versions"]:
        _render_block_md(f"Versie {label}", docs, out)
    _render_block_md(HANDLEIDINGEN, data["handleidingen"], out)
    return "\n".join(out).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Alles-in-één
# ---------------------------------------------------------------------------
def generate(root: str, out_html: str, exclude=None,
             title: str = "Documentenoverzicht NLCS") -> dict:
    """Scan `root` en schrijf <out_html> + hetzelfde pad met .md-extensie.
    Geeft {"html", "md", "count", "versions"} terug."""
    out_dir = os.path.dirname(os.path.abspath(out_html)) or "."
    data = scan(root, out_dir, exclude=exclude)

    os.makedirs(out_dir, exist_ok=True)
    with open(out_html, "w", encoding="utf-8") as f:
        f.write(build_html(data, title=title))
    out_md = os.path.splitext(out_html)[0] + ".md"
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(build_markdown(data, title=title))

    return {"html": out_html, "md": out_md,
            "count": data["total"], "versions": len(data["versions"])}
