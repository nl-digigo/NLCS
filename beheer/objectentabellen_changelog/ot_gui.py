"""
ot_gui.py - tkinter-venster voor de NLCS tabellen-changelog tool.

Twee tabbladen met dezelfde werkwijze, voor verschillende tabelsoorten:
  - Objectentabellen (match op objectURI; verbergt de kolommen status..streepje3)
  - Symbolentabellen (match op symboolURI; toont alleen symboolURI, sbibliotheek,
    fase, id, symbool, optie)

De versienamen (nieuw/oud) vul je maar één keer in; ze gelden voor beide
tabbladen. Per tabblad kies je de map met de nieuwe en de vorige versie, klik je
'Zoek hoofdgroepen' en vink je aan welke je vergelijkt (één, een paar of alle).
Per gekozen paar komen er twee HTML's:
  - <naam-inputfile>.html            : volledige tabel, sorteer/filter alle kolommen
  - changelog-<naam-inputfile>.html  : changelog met gekleurde wijzigingen

Instellingen worden onthouden via ot_config.
"""

import html
import os
import queue
import threading
import webbrowser
from urllib.parse import quote

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

import ot_compare
import ot_config
import ot_html


# ---------------------------------------------------------------------------
# Profielen: wat verschilt er per tabelsoort
# ---------------------------------------------------------------------------
PROFILES = [
    {
        "key": "obj",
        "label": "Objectentabellen",
        "match_key": "objectURI",
        # gedeelde mappen (blok 'Locaties'): rol -> sleutel in app.loc
        "locations": {"new": "obj_new", "old": "obj_old"},
        # verberg het blok status..streepje3
        "visible": lambda headers: ot_html.hide_range_indices(
            headers, "status", "streepje3"),
        # vrij zoekveld voor omschrijving, laagnaam en URI's; rest = keuzelijst
        "text_search": lambda h: h in ("omschrijving", "laagnaam")
        or "uri" in h.lower(),
        # markeer in de changelog elk vervallen object waarvan de naam
        # (deze kolom) ook voorkomt in de nieuwe release (waarschijnlijk
        # hernoemd/vervangen: nieuwe URI + ID)
        "deleted_name_check": "omschrijving",
        # volledige tabel op één pagina tonen (geen paginering van 25 rijen);
        # alle rijen scrollen in het venster met bevroren kop
        "single_page": True,
    },
    {
        "key": "sym",
        "label": "Symbolentabellen",
        "match_key": "symboolURI",
        "locations": {"new": "sym_new", "old": "sym_old",
                      "dwg_new": "dwg_new", "dwg_old": "dwg_old",
                      "objecten": "obj_new"},
        # toon deze kolommen; URI's achteraan (de zoekfilter/svg-kolommen komen
        # vooraan als front_columns in de volledige tabel)
        "visible": lambda headers: ot_html.show_names_ordered(
            headers, ["sbibliotheek", "fase", "id", "symbool", "optie",
                      "symboolURI"]),
        # vrij zoekveld voor URI's, symbool en id; rest (sbibliotheek, fase,
        # optie) = keuzelijst
        "text_search": lambda h: "uri" in h.lower() or h in ("symbool", "id"),
        # symbolen: extra map met de nieuwe .dwg's + svg/.dwg-kolommen in de changelog
        "needs_symbol_files": True,
        "symbol_name_col": "symbool",
        # zoekfilter-kolom (vooraan in de volledige tabel): welke sobject-term uit
        # de objectentabel het symbool vindt; svg-kolom erbij.
        "needs_objecten": True,
        "objecten_col": "sobject",
        "zoekfilter_name_col": "symbool",
        "zoekfilter_scope": "per_code",
        "front_svg": True,
        # rijen groeperen per zoekfilter (sobject-term) en binnen die groep
        # alfabetisch op symboolnaam, zowel in de volledige tabel als de changelog
        "group_by_zoekfilter": True,
        # oude versie = één grote CSV; scope per bibliotheek zodat 'vervallen'
        # beperkt blijft tot dezelfde hoofdgroep
        "old_is_file": True,
        "scope_col": "sbibliotheek",
        # sbibliotheek = 'S' + hoofdgroepcode: 'S' eraf bij het splitsen van CO
        "scope_strip_s": True,
        # in de HTML-tabellen de kolomkop 'fase' tonen als 'status'
        "header_labels": {"fase": "status"},
        # volledige tabel op één pagina tonen (geen paginering van 25 rijen)
        "single_page": True,
    },
    {
        "key": "lijn",
        "label": "Lijntypes",
        "match_key": "lijntypeURI",
        "locations": {"new": "lijn_new", "old": "lijn_old"},
        # toon de informatieve kolommen (in CSV-volgorde); finalCleanName weg.
        # id blijft zichtbaar (elke tabel toont het ID-nummer).
        "visible": lambda headers: ot_html.show_names_indices(
            headers, ["lijntypeURI", "id", "hoofdgroep", "omschrijving", "fase",
                      "optie", "autocaddef"]),
        # vrij zoekveld voor URI, id, omschrijving en autocaddef; rest = keuzelijst
        "text_search": lambda h: h in ("omschrijving", "autocaddef", "id")
        or "uri" in h.lower(),
        # oude versie = één grote CSV met alle lijntypes; scope op hoofdgroep zodat
        # 'vervallen' beperkt blijft tot de vergeleken hoofdgroep
        "old_is_file": True,
        "scope_col": "hoofdgroep",
        # hoofdgroep bevat de code al letterlijk (BV, BC, ...); NIET de 'S' strippen
        # (anders wordt bijv. 'SB' foutief 'B'). Verzamelbestand CO valt zo net als
        # bij symbolen uiteen in aparte hoofdgroep-bestanden.
        "scope_strip_s": False,
        # De generieke lijnen 'CONTINUOUS' en 'V-CONTINUOUS-SO' komen uit een andere
        # publicatie; neem ze op met blanco fase/optie/autocaddef (die kolommen aan
        # beide kanten leegmaken zodat ze niet als wijziging tellen).
        "blank_spec": {
            "match_col": "omschrijving",
            "values": {"CONTINUOUS", "V-CONTINUOUS-SO"},
            "columns": ["fase", "optie", "autocaddef"],
        },
        # In de changelog helemaal GEEN wijzigingen tonen voor deze generieke
        # lijnen (geen gewijzigde cellen, niet groen 'nieuw', niet 'vervallen').
        "suppress_change": {
            "match_col": "omschrijving",
            "values": {"CONTINUOUS", "V-CONTINUOUS-SO"},
        },
        # Verzamelbestand (CO): de generieke lijntypes (lege hoofdgroep) vallen
        # bij het splitsen buiten de hoofdgroep-bestanden. Draai ze dan toch uit
        # als eigen bestand onder de bestandscode (bijv. lijntypes-5-2-CO), en
        # sla voor een uitdraai met alleen generieke lijntypes de changelog over.
        "generic_fallback": True,
        # in de HTML-tabellen de kolomkop 'fase' tonen als 'status'
        "header_labels": {"fase": "status"},
        # volledige tabel op één pagina tonen (geen paginering van 25 rijen)
        "single_page": True,
    },
    {
        "key": "arc",
        "label": "Arceringen",
        "match_key": "arceringURI",
        "locations": {"new": "arc_new", "old": "arc_old",
                      "objecten": "obj_new"},
        # toon de informatieve kolommen (in CSV-volgorde); searchterm,
        # abibliotheekURI en finalCleanName weglaten
        "visible": lambda headers: ot_html.show_names_indices(
            headers, ["arceringURI", "abibliotheek", "fase", "id", "arcering",
                      "optie", "schaal", "vrkl_kort", "vrkl_lang", "fileURL"]),
        # vrij zoekveld voor URI, arcering, id, de verklaringen en de fileURL;
        # rest (abibliotheek, fase, optie, schaal) = keuzelijst
        "text_search": lambda h: h in ("arcering", "vrkl_kort", "vrkl_lang",
                                       "id", "fileURL") or "uri" in h.lower(),
        # zoekfilter-kolom (vooraan in de volledige tabel): welke aobject-term uit
        # de objectentabellen de arcering vindt. Arceringen zijn één gedeelde groep,
        # dus de termen komen uit ALLE objectentabellen samen.
        "needs_objecten": True,
        "objecten_col": "aobject",
        "zoekfilter_name_col": "arcering",
        "zoekfilter_scope": "all",
        "front_svg": False,
        # rijen groeperen per zoekfilter (aobject-term) en binnen die groep
        # alfabetisch op arceringnaam; DataTables sorteert op de zoekfilter-kolom
        "group_by_zoekfilter": True,
        # oude versie = één grote CSV met alle arceringen; scope op abibliotheek
        # zodat 'vervallen' beperkt blijft tot de vergeleken groep
        "old_is_file": True,
        "scope_col": "abibliotheek",
        # abibliotheek bevat de groepscode al letterlijk (ACO, ...); NIET strippen.
        # CO werkt als één hoofdgroep met groep 'ACO', dus geen split.
        "scope_strip_s": False,
        # in de HTML-tabellen de kolomkop 'fase' tonen als 'status'
        "header_labels": {"fase": "status"},
        # volledige tabel op één pagina tonen (geen paginering van 25 rijen)
        "single_page": True,
    },
]


def _dwg_cell(naam: str, dwg_stems: set) -> str:
    present = bool(naam) and naam.lower() in dwg_stems
    return ('<span class="dwg-ja">ja</span>' if present
            else '<span class="dwg-nee">nee</span>')


def _svg_cell(naam: str) -> str:
    if not naam:
        return ""
    # De svg's staan in een submap per bibliotheek, genoemd naar de bibliotheek-
    # code (SAM/SAL/SFC...). Die code is het eerste naamsegment dat met 'S'
    # begint: 'SAM-ASPUNTNUMMER-SO' -> ./SAM/. Symboolnamen kunnen een prefix
    # 'V-'/'B-' hebben ('V-SFC-PAAL_BETON_PREFAB_01-SO'); die segmenten beginnen
    # nooit met 'S', dus 'V-SFC-...' -> ./SFC/ (niet ./V/). De svg-BESTANDSnaam
    # blijft de volledige symboolnaam (incl. eventueel voorvoegsel).
    segs = naam.split("-")
    prefix = next((s for s in segs if s[:1].upper() == "S" and len(s) > 1), "")
    if not prefix:
        prefix = segs[0] if len(segs) > 1 else ""
    folder = ("./" + quote(prefix) + "/") if prefix else "./"
    href = folder + quote(naam + ".svg")
    alt = html.escape(naam, quote=True)
    return (f'<a href="{href}" target="_blank">'
            f'<img src="{href}" alt="{alt}" loading="lazy" '
            f'onerror="this.parentNode.style.display=\'none\'"></a>')


# Weergave van de hash-vergelijking (oude .dwg t.o.v. nieuwe .dwg).
_HASH_LABEL = {
    "identiek": '<span class="hash-gelijk">identiek</span>',
    "gewijzigd": '<span class="hash-wijz">inhoudelijk gewijzigd</span>',
    "alleen nieuw": '<span class="hash-neutraal">alleen nieuw</span>',
    "alleen oud": '<span class="hash-neutraal">alleen oud</span>',
}


def _hash_cell(naam: str, hash_status: dict) -> str:
    if not naam:
        return ""
    return _HASH_LABEL.get(hash_status.get(naam.lower(), ""), "")


def _zoekfilter_cell(naam: str, zoekfilters: dict) -> str:
    if not naam:
        return ""
    term = zoekfilters.get(naam.lower(), "")
    if not term:
        return '<span class="zf-geen">(geen)</span>'
    return f'<span class="zf-term">{html.escape(term)}</span>'


def _leftover_generic(result: dict, scope_col: str):
    """Deelresultaat met alleen de rijen zonder hoofdgroep (lege `scope_col`):
    de generieke lijntypes CONTINUOUS/V-CONTINUOUS-SO uit een verzamelbestand die
    bij het splitsen per hoofdgroep buiten de boot vallen. Geeft None als er geen
    zulke rijen zijn."""
    headers = result["headers"]
    if scope_col not in headers:
        return None
    bi = headers.index(scope_col)

    def empty_r(r):
        return not (r["cells"][bi]["value"] or "").strip()

    def empty_d(d):
        return not ((d[bi] if bi < len(d) else "") or "").strip()

    rows = [r for r in result["rows"] if empty_r(r)]
    deleted = [d for d in result["deleted"] if empty_d(d)]
    if not rows and not deleted:
        return None
    return {
        "headers": headers,
        "rows": rows,
        "deleted": deleted,
        "stats": {
            "new": sum(1 for x in rows if x["status"] == "new"),
            "changed": sum(1 for x in rows if x["status"] == "changed"),
            "deleted": len(deleted),
            "total_new": len(rows),
        },
    }


def _is_generic_only(result: dict, scope_col: str) -> bool:
    """True als geen enkele (gewone of vervallen) rij een hoofdgroep heeft: een
    uitdraai met uitsluitend generieke lijntypes. Voor zo'n uitdraai is geen
    changelog nodig."""
    headers = result["headers"]
    if scope_col not in headers or not (result["rows"] or result["deleted"]):
        return False
    bi = headers.index(scope_col)
    if any((r["cells"][bi]["value"] or "").strip() for r in result["rows"]):
        return False
    if any(((d[bi] if bi < len(d) else "") or "").strip()
           for d in result["deleted"]):
        return False
    return True


def _base_for_code(stem: str, code: str) -> str:
    """Vervang de laatste code in een bestandsnaam-stam door `code`.

    'symbolen-5-2-CO' + 'BC' -> 'symbolen-5-2-BC'. Gebruikt om bij het
    uiteenvallen van een verzamelbestand (CO) een naam per hoofdgroep te maken."""
    if not code:
        return stem
    left, sep, _last = stem.rpartition("-")
    return f"{left}-{code}" if sep else code


def _bib_of_stem(stem: str, known_bibs) -> str:
    """De bibliotheek-code die als los segment in een bestands-/symboolnaam staat.

    Symboolnamen kunnen een prefix hebben (bijv. 'V-SFC-PAAL...', 'B-SGC-...'),
    dus het EERSTE naam-segment is geen betrouwbare bibliotheek. We zoeken daarom
    welke bekende bibliotheek (uit de `sbibliotheek`-kolom, bijv. SFC/SGC/SAM) als
    hyphen-segment in de naam voorkomt; het eerste passende segment wint. Geeft ""
    als geen enkele bekende bibliotheek in de naam zit (dan hoort het .dwg-bestand
    niet bij een verwerkte hoofdgroep)."""
    if not stem or not known_bibs:
        return ""
    known = {b.upper() for b in known_bibs if b}
    for seg in stem.upper().split("-"):
        if seg in known:
            return seg
    return ""


def _symbol_extra_columns(result: dict, name_col: str, dwg_stems: set,
                          hash_status: dict = None,
                          zoekfilters: dict = None) -> list:
    """Bouw de extra changelog-kolommen voor de symbolen:
      1. 'zoekfilter'      : de sobject-term uit de objectentabel waarmee het
                             symbool gevonden wordt (langste voorvoegsel-match).
                             Alleen als `zoekfilters` is meegegeven.
      2. '.dwg aanwezig'   : ja/nee, of <symbool>.dwg in de nieuwe map (recursief)
                             gevonden is.
      3. '.dwg t.o.v. oud' : identiek / inhoudelijk gewijzigd (op basis van een
                             SHA-256 hash van het oude en nieuwe .dwg-bestand),
                             of 'alleen nieuw'/'alleen oud'. Alleen als
                             `hash_status` is meegegeven.
      4. 'svg'             : de svg als klikbare afbeelding via een relatief pad
                             (./<PREFIX>/<symbool>.svg, verondersteld naast de HTML).
    De bestandsnaam komt uit de kolom `name_col` (doorgaans 'symbool'). Elke kolom
    levert cellen voor de gewone rijen én voor de vervallen rijen (beide in de
    nieuwe-kolomindeling)."""
    headers = result["headers"]
    if name_col not in headers:
        return []
    ni = headers.index(name_col)

    def naam_of(row):      # gewone rij: cells[i]["value"]
        return (row["cells"][ni]["value"] or "").strip()

    def naam_of_del(drow):  # vervallen rij: platte lijst in nieuwe-indeling
        return (drow[ni] if ni < len(drow) else "" or "").strip()

    rows = result["rows"]
    deleted = result["deleted"]

    cols = []
    if zoekfilters is not None:
        cols.append({
            "header": "zoekfilter (sobject)",
            "cells": [_zoekfilter_cell(naam_of(r), zoekfilters) for r in rows],
            "deleted_cells": [_zoekfilter_cell(naam_of_del(d), zoekfilters)
                              for d in deleted],
        })

    cols.append({
        "header": ".dwg aanwezig",
        "cells": [_dwg_cell(naam_of(r), dwg_stems) for r in rows],
        "deleted_cells": [_dwg_cell(naam_of_del(d), dwg_stems) for d in deleted],
    })

    if hash_status is not None:
        cols.append({
            "header": ".dwg t.o.v. oud",
            "cells": [_hash_cell(naam_of(r), hash_status) for r in rows],
            "deleted_cells": [_hash_cell(naam_of_del(d), hash_status)
                              for d in deleted],
        })

    cols.append({
        "header": "svg",
        "cells": [_svg_cell(naam_of(r)) for r in rows],
        "deleted_cells": [_svg_cell(naam_of_del(d)) for d in deleted],
        "td_class": "svgcell",
    })
    return cols


def _front_columns(result: dict, name_col: str, zoekfilters: dict,
                   objecten_col: str, want_svg: bool) -> list:
    """Kolommen die VOORAAN in de volledige (basis-)tabel komen:
      1. 'zoekfilter (<objecten_col>)' : de sobject/aobject-term waarmee het
         symbool/de arcering gevonden wordt (langste voorvoegsel-match). Keuzelijst.
      2. 'svg' (alleen `want_svg`)      : de svg als klikbare afbeelding.
    De eerste kolom (zoekfilter) is sorteerbaar zodat DataTables' standaardsortering
    (kolom 0) blijft werken; de svg-kolom is niet sorteerbaar."""
    headers = result["headers"]
    if name_col not in headers:
        return []
    ni = headers.index(name_col)

    def naam(row):
        return (row["cells"][ni]["value"] or "").strip()

    rows = result["rows"]
    cols = []
    if zoekfilters is not None:
        cols.append({
            "header": f"zoekfilter ({objecten_col})",
            "cells": [_zoekfilter_cell(naam(r), zoekfilters) for r in rows],
            "filter": "select",
            "filter_values": [zoekfilters.get(naam(r).lower(), "") for r in rows],
        })
    if want_svg:
        cols.append({
            "header": "svg",
            "cells": [_svg_cell(naam(r)) for r in rows],
            "orderable": False,
            "td_class": "svgcell",
            "filter": "none",
        })
    return cols


# ---------------------------------------------------------------------------
# Herbruikbaar: scrollbare lijst met aanvinkvakjes
# ---------------------------------------------------------------------------
class ScrollableChecklist(ttk.Frame):
    """Een aanvinklijst met scrollbalk en 'Alles'/'Niets'-knoppen."""

    def __init__(self, master, title: str, height: int = 130):
        super().__init__(master)

        header = ttk.Frame(self)
        header.pack(fill="x")
        ttk.Label(header, text=title, font=("Segoe UI", 9, "bold")).pack(side="left")
        ttk.Button(header, text="Niets", width=6,
                   command=lambda: self.set_all(False)).pack(side="right")
        ttk.Button(header, text="Alles", width=6,
                   command=lambda: self.set_all(True)).pack(side="right")

        container = ttk.Frame(self)
        container.pack(fill="both", expand=True)
        self.canvas = tk.Canvas(container, height=height, highlightthickness=1,
                                highlightbackground="#c8ccd0")
        scrollbar = ttk.Scrollbar(container, orient="vertical",
                                  command=self.canvas.yview)
        self.inner = ttk.Frame(self.canvas)
        self.inner.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.create_window((0, 0), window=self.inner, anchor="nw")
        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Enter>",
                         lambda e: self.canvas.bind_all("<MouseWheel>", self._wheel))
        self.canvas.bind("<Leave>",
                         lambda e: self.canvas.unbind_all("<MouseWheel>"))

        self.vars: dict[str, tk.BooleanVar] = {}

    def _wheel(self, event) -> None:
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def set_items(self, items: list[str], checked=None) -> None:
        checked = set(checked or [])
        for widget in self.inner.winfo_children():
            widget.destroy()
        self.vars = {}
        for item in items:
            var = tk.BooleanVar(value=(item in checked))
            ttk.Checkbutton(self.inner, text=item, variable=var).pack(anchor="w")
            self.vars[item] = var

    def checked(self) -> list[str]:
        return [name for name, var in self.vars.items() if var.get()]

    def set_all(self, value: bool) -> None:
        for var in self.vars.values():
            var.set(value)


# ---------------------------------------------------------------------------
# Eén tabblad voor één tabelsoort
# ---------------------------------------------------------------------------
class TableTab(ttk.Frame):
    def __init__(self, master, app: "App", profile: dict):
        super().__init__(master, padding=10)
        self.app = app
        self.profile = profile
        self._queue: queue.Queue = queue.Queue()
        self.pairs: dict[str, tuple[str, str]] = {}   # code -> (nieuw, oud)

        self._build()

    # -- opbouw ------------------------------------------------------------
    def _build(self) -> None:
        self.old_is_file = bool(self.profile.get("old_is_file"))

        # De mappen staan in het gedeelde tabblad 'Locaties'; hier alleen een
        # korte herinnering welke velden dit tabblad gebruikt.
        info = ttk.Frame(self)
        info.pack(fill="x")
        ttk.Label(
            info, foreground="#555",
            text="Vul de mappen in op het tabblad 'Locaties'; kies hier de "
                 "hoofdgroepen en klik 'Genereer'.").pack(anchor="w")

        groups = ttk.LabelFrame(self, text="Hoofdgroepen (kies wat je vergelijkt)",
                                padding=8)
        groups.pack(fill="both", expand=True, pady=8)
        top = ttk.Frame(groups)
        top.pack(fill="x")
        ttk.Button(top, text="Zoek hoofdgroepen", command=self.on_scan
                   ).pack(side="left")
        self.scan_status_var = tk.StringVar(
            value="Vul de mappen in bij 'Locaties' en klik 'Zoek hoofdgroepen'.")
        ttk.Label(top, textvariable=self.scan_status_var, foreground="#555"
                  ).pack(side="left", padx=10)
        self.code_list = ScrollableChecklist(groups, "Hoofdgroep-codes")
        self.code_list.pack(fill="both", expand=True, pady=(8, 0))

        out = ttk.Frame(self)
        out.pack(fill="x")
        self.gen_btn = ttk.Button(out, text="Genereer HTML's",
                                  command=self.on_generate)
        self.gen_btn.pack(side="right")

        logframe = ttk.LabelFrame(self, text="Voortgang", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=7, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    # -- config ------------------------------------------------------------
    def load_cfg(self, codes) -> None:
        """Alleen de aangevinkte hoofdgroep-codes worden per tabblad onthouden;
        de mappen komen uit het gedeelde 'Locaties'-tabblad (app.loc)."""
        self._saved_codes = list(codes or [])
        if os.path.isdir(self._loc("new")) and self._old_ok():
            self.on_scan(silent=True)

    def collect_cfg(self) -> dict:
        return {"codes": self.code_list.checked()}

    # -- helpers -----------------------------------------------------------
    def _loc(self, role: str) -> str:
        """De gedeelde locatie voor een rol ('new'/'old'/'dwg_new'/...) van dit
        profiel, uit app.loc. Lege string als de rol niet bestaat."""
        key = self.profile.get("locations", {}).get(role)
        return self.app.loc[key].get().strip() if key else ""

    def _logmsg(self, msg: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _old_ok(self) -> bool:
        old = self._loc("old")
        return os.path.isfile(old) if self.old_is_file else os.path.isdir(old)

    # -- hoofdgroepen zoeken ----------------------------------------------
    def on_scan(self, silent: bool = False) -> None:
        new_dir = self._loc("new")
        old = self._loc("old")
        if not (os.path.isdir(new_dir) and self._old_ok()):
            if not silent:
                msg = ("Vul bij 'Locaties' een geldige map voor de nieuwe versie "
                       "én een CSV-bestand voor de vorige versie in."
                       if self.old_is_file
                       else "Vul bij 'Locaties' een geldige map voor de nieuwe "
                       "én de vorige versie in.")
                messagebox.showwarning("Locaties ontbreken", msg)
            return

        if self.old_is_file:
            pairs, only_new, only_old = ot_compare.pair_folder_to_file(new_dir, old)
        else:
            pairs, only_new, only_old = ot_compare.pair_folders(new_dir, old)
        self.pairs = {code: (npath, opath) for code, npath, opath in pairs}

        # Hoofdgroepen die alleen in de nieuwe versie bestaan (nog niet in de
        # vorige, bijv. nieuw in 5.2): toch meenemen met een lege oude kant, zodat
        # er een changelog met alleen nieuwe (groene) regels uit komt. Geldt voor
        # de map-koppeling (objecten); bij een groot oud bestand (symbolen/
        # lijntypes) is only_new leeg en levert de scope dat vanzelf al op.
        new_only_added = []
        if not self.old_is_file:
            for code in only_new:
                np = ot_compare.find_csv_by_code(new_dir, code)
                if np:
                    self.pairs[code] = (np, "")
                    new_only_added.append(code)
        codes = sorted(self.pairs)

        saved = set(getattr(self, "_saved_codes", []) or [])
        checked = [c for c in codes if c in saved] if saved else codes
        self.code_list.set_items(codes, checked=checked or codes)

        msg = f"{len(codes)} hoofdgroep(en) gevonden."
        self.scan_status_var.set(msg)
        if not silent:
            self._logmsg(msg + (" (" + ", ".join(codes) + ")" if codes else ""))
            if new_only_added:
                self._logmsg(
                    "Nieuw in deze versie (geen vorige) -> changelog met alleen "
                    "nieuwe regels: " + ", ".join(new_only_added))
            if only_old:
                self._logmsg("Alleen in vorige map (geen paar): "
                             + ", ".join(only_old))
            if not codes:
                messagebox.showinfo(
                    "Niets gekoppeld",
                    "Geen CSV's met een gedeelde hoofdgroep-code in beide mappen.")

    # -- genereren (in aparte thread) -------------------------------------
    def on_generate(self) -> None:
        out_dir = self.app.loc["output_dir"].get().strip()
        if not self.pairs:
            self.on_scan()
            if not self.pairs:
                return
        if not out_dir:
            messagebox.showwarning(
                "Geen uitvoermap",
                "Vul bij 'Locaties' een uitvoermap in.")
            return

        chosen = self.code_list.checked()
        if not chosen:
            messagebox.showwarning(
                "Niets aangevinkt",
                "Vink minstens één hoofdgroep aan (of klik 'Alles').")
            return

        os.makedirs(out_dir, exist_ok=True)
        version_new = self.app.version_new_var.get().strip()
        version_old = self.app.version_old_var.get().strip()
        open_after = self.app.open_after_var.get()
        match_key = self.profile["match_key"]
        visible_fn = self.profile["visible"]
        text_search_fn = self.profile["text_search"]
        needs_files = self.profile.get("needs_symbol_files", False)
        symbol_name_col = self.profile.get("symbol_name_col", "")
        scope_col = self.profile.get("scope_col", "")
        scope_strip_s = self.profile.get("scope_strip_s", True)
        blank_spec = self.profile.get("blank_spec")
        suppress_change = self.profile.get("suppress_change")
        generic_fallback = self.profile.get("generic_fallback", False)
        needs_objecten = self.profile.get("needs_objecten", False)
        objecten_col = self.profile.get("objecten_col", "")
        zf_name_col = self.profile.get("zoekfilter_name_col", "")
        zf_scope = self.profile.get("zoekfilter_scope", "per_code")
        front_svg = self.profile.get("front_svg", False)
        group_by_zf = self.profile.get("group_by_zoekfilter", False)
        objecten_dir = self._loc("objecten")
        symbols_dir = self._loc("dwg_new")
        symbols_old_dir = self._loc("dwg_old")
        new_dir = self._loc("new")
        # Publicatie-overzichtmap (docs/changelog). Staat die ingevuld, dan komt
        # elk hoofdgroep-bestand in de bijbehorende hoofdgroep-submap daarvan
        # (docs/changelog/<HG>) — dezelfde plek waar het overzicht de bestanden
        # vindt en waar de svg-submappen (S<HG>/A<HG>) al staan. Anders vallen ze
        # in de platte uitvoermap.
        pub_root = self.app.loc["index_root"].get().strip()
        selected = [(code, self.pairs[code][0], self.pairs[code][1])
                    for code in chosen if code in self.pairs]

        self.gen_btn.config(state="disabled")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

        def dest_dir_for(hg: str) -> str:
            """Doelmap voor de HTML van hoofdgroep `hg`. Is er een publicatie-
            overzichtmap ingevuld, dan de hoofdgroep-submap daarvan
            (docs/changelog/<HG>, aangemaakt als die nog niet bestaat); anders de
            platte uitvoermap."""
            hgu = (hg or "").strip().upper()
            if pub_root and os.path.isdir(pub_root) and hgu:
                d = os.path.join(pub_root, hgu)
                os.makedirs(d, exist_ok=True)
                return d
            return out_dir

        def worker():
            try:
                if pub_root and os.path.isdir(pub_root):
                    self._queue.put(("log",
                        f"Bestanden gaan naar de hoofdgroep-submappen van "
                        f"{pub_root}."))
                self._queue.put(("log", f"{len(selected)} hoofdgroep(en) verwerken: "
                                 + ", ".join(c for c, _, _ in selected)))
                # Symbolen-.dwg's uit twee aparte mappen (elk recursief). De nieuwe
                # map voedt '.dwg aanwezig' + wees-controle; nieuw + oud samen
                # voeden de hash-vergelijking.
                dwg_map = {}            # {stem: relpad} in de nieuwe map
                new_abs = {}            # {stem: absoluut pad} nieuwe map
                old_abs = {}            # {stem: absoluut pad} oude map
                do_hash = False
                if needs_files:
                    if not symbols_dir:
                        self._queue.put(("log",
                            "Geen map met nieuwe symbolen gekozen: '.dwg aanwezig' "
                            "wordt overal 'nee', geen hash-vergelijking en geen "
                            "wees-controle."))
                    elif not os.path.isdir(symbols_dir):
                        self._queue.put(("log",
                            f"Let op: map nieuwe symbolen bestaat niet: {symbols_dir}"))
                    else:
                        dwg_map = ot_compare.dwg_index(symbols_dir)
                        new_abs = {k: os.path.join(symbols_dir, v)
                                   for k, v in dwg_map.items()}
                        self._queue.put(("log",
                            f"{len(dwg_map)} nieuwe .dwg-bestand(en) gevonden."))

                    if not symbols_old_dir:
                        self._queue.put(("log",
                            "Geen map met oude symbolen gekozen: geen "
                            "hash-vergelijking (kolom '.dwg t.o.v. oud' vervalt)."))
                    elif not os.path.isdir(symbols_old_dir):
                        self._queue.put(("log",
                            f"Let op: map oude symbolen bestaat niet: "
                            f"{symbols_old_dir}"))
                    else:
                        old_map = ot_compare.dwg_index(symbols_old_dir)
                        old_abs = {k: os.path.join(symbols_old_dir, v)
                                   for k, v in old_map.items()}
                        do_hash = bool(new_abs)
                        self._queue.put(("log",
                            f"{len(old_map)} oude .dwg-bestand(en) gevonden."))

                # Objectentabellen voor de zoekfilter-kolom (sobject/aobject-term).
                use_zf = False
                if needs_objecten:
                    if not objecten_dir:
                        self._queue.put(("log",
                            f"Geen map objectentabellen gekozen: kolom "
                            f"'zoekfilter ({objecten_col})' wordt weggelaten."))
                    elif not os.path.isdir(objecten_dir):
                        self._queue.put(("log",
                            f"Let op: map objectentabellen bestaat niet: "
                            f"{objecten_dir}"))
                    else:
                        use_zf = True
                        self._queue.put(("log",
                            f"Zoekfilter: {objecten_col}-termen uit de "
                            f"objectentabellen."))

                made = 0
                files = 0
                first = None
                # Voor de wees-controle: symbolen uit de VERWERKTE nieuwe tabellen
                # en de bijbehorende bibliotheek-voorvoegsels (bijv. SAM, SAL).
                all_symbols: set = set()
                processed_bibs: set = set()
                # Andere kant op: regels waarvoor GEEN .dwg-bestand bestaat.
                # (naam, hoofdgroepcode), run-breed verzameld.
                missing_dwg: list = []
                for code, new_path, old_path in selected:
                    orig_base = os.path.splitext(os.path.basename(new_path))[0]
                    full_result = ot_compare.compare(
                        new_path, old_path, key=match_key, scope_col=scope_col,
                        blank_spec=blank_spec, suppress_change=suppress_change)

                    # Verzamelbestand (CO) uiteen laten vallen in aparte
                    # hoofdgroepen; gewone bestanden blijven één geheel.
                    groups = ot_compare.split_result_by_bib(
                        full_result, scope_col, strip_s=scope_strip_s)
                    # Generieke lijntypes (lege hoofdgroep) vallen bij het splitsen
                    # buiten de hoofdgroep-bestanden. Zet ze vooraan in ELKE
                    # hoofdgroep-uitdraai (BC, MC, ...) én draai ze apart uit onder
                    # de bestandscode (bijv. CO), zodat de generieke lijntypes
                    # overal zichtbaar zijn en CO niet zonder lijntypes komt.
                    if generic_fallback and len(groups) > 1:
                        leftover = _leftover_generic(full_result, scope_col)
                        if leftover:
                            for _c, r in groups:
                                r["rows"] = leftover["rows"] + r["rows"]
                                r["deleted"] = leftover["deleted"] + r["deleted"]
                                r["stats"] = {
                                    "new": sum(1 for x in r["rows"]
                                               if x["status"] == "new"),
                                    "changed": sum(1 for x in r["rows"]
                                                   if x["status"] == "changed"),
                                    "deleted": len(r["deleted"]),
                                    "total_new": len(r["rows"]),
                                }
                            groups = groups + [(code, leftover)]
                    multi = len(groups) > 1
                    if multi:
                        # Per hoofdgroep het aantal rijen tonen, zodat direct
                        # zichtbaar is welke hoofdgroepen in het verzamelbestand
                        # zitten (bijv. CO: BC/FC/GC/HC/KC/MC/SC).
                        per = ", ".join(
                            f"{c} ({len(r['rows'])})" for c, r in groups)
                        self._queue.put(("log",
                            f"[{code}] verzameling hoofdgroepen -> {per}: "
                            f"{len(groups)} aparte bestanden."))
                        # Waarschuw als rijen geen herkenbare hoofdgroep hadden
                        # en dus niet in een uitvoerbestand terechtkomen.
                        assigned = sum(len(r["rows"]) + len(r["deleted"])
                                       for _c, r in groups)
                        total_in = (len(full_result["rows"])
                                    + len(full_result["deleted"]))
                        if assigned < total_in:
                            self._queue.put(("log",
                                f"[{code}] LET OP: {total_in - assigned} rij(en) "
                                f"zonder herkenbare hoofdgroep (kolom "
                                f"'{scope_col}') vallen buiten de uitvoer."))

                    for gcode, result in groups:
                        base = _base_for_code(orig_base, gcode) if multi else orig_base
                        vis = visible_fn(result["headers"])
                        text_cols = [h for h in result["headers"]
                                     if text_search_fn(h)]
                        s = result["stats"]

                        extra_cols = None
                        front_cols = None
                        orphans_this = None
                        hash_summary = ""

                        # Zoekfilter-map (langste voorvoegsel-match) voor de
                        # front-kolom in de volledige tabel; symbolen gebruiken 'm
                        # ook in de changelog. Werkt voor symbolen (per hoofdgroep-
                        # code) én arceringen (termen uit ALLE objectentabellen).
                        zoekfilters = None
                        if use_zf and zf_name_col in result["headers"]:
                            zni = result["headers"].index(zf_name_col)
                            zf_names = (
                                [r["cells"][zni]["value"] for r in result["rows"]]
                                + [d[zni] if zni < len(d) else ""
                                   for d in result["deleted"]])
                            if zf_scope == "all":
                                terms = ot_compare.collect_column_values_list(
                                    objecten_dir, objecten_col)
                            else:
                                # Hoofdgroep(en) uit de sbibliotheek-kolom; na het
                                # splitsen één per bestand. Termen uit de bijbe-
                                # horende objectentabel(len) samenvoegen.
                                codes_needed: set = set()
                                if scope_col in result["headers"]:
                                    bi = result["headers"].index(scope_col)
                                    for r in result["rows"]:
                                        ch = ot_compare.sbib_to_code(
                                            r["cells"][bi]["value"])
                                        if ch:
                                            codes_needed.add(ch)
                                if not codes_needed:
                                    codes_needed = {gcode or code}
                                terms = []
                                missing = []
                                for ch in sorted(codes_needed):
                                    ocsv = ot_compare.find_csv_by_code(
                                        objecten_dir, ch)
                                    if ocsv:
                                        terms += ot_compare.column_values(
                                            ocsv, objecten_col)
                                    else:
                                        missing.append(ch)
                                if missing:
                                    self._queue.put(("log",
                                        f"[{gcode or code}] geen objectentabel "
                                        f"voor: {', '.join(missing)} (zoekfilter "
                                        f"voor die groep leeg)."))
                            zoekfilters = ot_compare.zoekfilter_map(
                                zf_names, terms)

                        # Rijen groeperen per zoekfilter en binnen die groep
                        # alfabetisch op symboolnaam. Eén keer op result['rows']
                        # (en de vervallen rijen) sorteren, VÓÓR de front-/extra-
                        # kolommen worden gebouwd, zodat alle afgeleide cellen
                        # (die positioneel met de rijen meelopen) mee sorteren.
                        # Zelfde volgorde als DataTables in de volledige tabel
                        # (tekstsortering op de zoekfilter-kolom): een lege
                        # zoekfilter sorteert vooraan.
                        gname_col = zf_name_col or symbol_name_col
                        if (group_by_zf and zoekfilters is not None
                                and gname_col in result["headers"]):
                            gni = result["headers"].index(gname_col)

                            def _grp_key_row(r, _i=gni):
                                nm = (r["cells"][_i]["value"] or "").strip()
                                term = zoekfilters.get(nm.lower(), "")
                                return (term.casefold(), nm.casefold())

                            def _grp_key_del(d, _i=gni):
                                nm = (d[_i] if _i < len(d) else "" or "").strip()
                                term = zoekfilters.get(nm.lower(), "")
                                return (term.casefold(), nm.casefold())

                            result["rows"].sort(key=_grp_key_row)
                            result["deleted"].sort(key=_grp_key_del)

                        # Front-kolommen (zoekfilter [+ svg]) voor de basis-tabel.
                        if needs_objecten or front_svg:
                            front_cols = _front_columns(
                                result, zf_name_col or symbol_name_col,
                                zoekfilters, objecten_col, front_svg) or None

                        if needs_files:
                            has_name = symbol_name_col in result["headers"]
                            # symboolnamen (gewone + vervallen rijen) verzamelen
                            names = []
                            this_symbols: set = set()
                            this_bibs: set = set()
                            if has_name:
                                ni = result["headers"].index(symbol_name_col)
                                row_names = [r["cells"][ni]["value"]
                                             for r in result["rows"]]
                                names = row_names + [d[ni] if ni < len(d) else ""
                                                     for d in result["deleted"]]
                                # Wees-scope: alleen de symbolen uit de VERWERKTE
                                # nieuwe tabellen tellen mee (exacte namen, incl.
                                # eventueel prefix). Vervallen rijen niet: een
                                # achtergebleven .dwg van een vervallen symbool is
                                # juist een wees.
                                for nm in row_names:
                                    stem = (nm or "").strip().lower()
                                    if stem:
                                        this_symbols.add(stem)
                                # Bibliotheek uit de sbibliotheek-kolom (betrouw-
                                # baar). De symboolnaam kan een prefix hebben
                                # (V-SFC-..., B-SGC-...), dus het eerste naam-
                                # segment deugt NIET als bibliotheek.
                                if scope_col and scope_col in result["headers"]:
                                    bcol = result["headers"].index(scope_col)
                                    for r in result["rows"]:
                                        sb = (r["cells"][bcol]["value"]
                                              or "").strip().upper()
                                        if sb:
                                            this_bibs.add(sb)
                                all_symbols |= this_symbols
                                processed_bibs |= this_bibs
                                # Andere kant op: regels van DEZE hoofdgroep
                                # waarvoor geen <symbool>.dwg in de map staat.
                                # Alleen zinvol als er een .dwg-map gekozen is.
                                if dwg_map:
                                    for nm in row_names:
                                        disp = (nm or "").strip()
                                        if disp and disp.lower() not in dwg_map:
                                            missing_dwg.append(
                                                (disp, gcode or code))

                            # Wezen van DEZE hoofdgroep (bibliotheek) voor de
                            # changelog: .dwg's van dezelfde bib(s) zonder regel.
                            # Bib per .dwg via segment-match (prefix-proof).
                            if has_name and dwg_map and this_bibs:
                                orphans_this = sorted(
                                    ((stem, dwg_map[stem]) for stem in dwg_map
                                     if _bib_of_stem(stem, this_bibs)
                                     and stem not in this_symbols),
                                    key=lambda t: t[0])

                            hash_status = None
                            if do_hash and has_name:
                                hash_status = ot_compare.dwg_hash_status(
                                    names, new_abs, old_abs)
                                gew = sum(1 for v in hash_status.values()
                                          if v == "gewijzigd")
                                ident = sum(1 for v in hash_status.values()
                                            if v == "identiek")
                                hash_summary = (f", .dwg: {ident} identiek/"
                                                f"{gew} gewijzigd")

                            extra_cols = _symbol_extra_columns(
                                result, symbol_name_col, dwg_map, hash_status,
                                zoekfilters)

                        # Groeperen in de volledige tabel: DataTables sorteert op
                        # de zoekfilter-kolom (front[0]) en, binnen die groep, op
                        # de symboolnaam-kolom (DOM-index = #front + positie in
                        # de zichtbare kolommen).
                        full_order = None
                        if (group_by_zf and zoekfilters is not None
                                and front_cols and gname_col in result["headers"]):
                            gidx = result["headers"].index(gname_col)
                            if gidx in vis:
                                symb_dom = len(front_cols) + vis.index(gidx)
                                full_order = [[0, "asc"], [symb_dom, "asc"]]

                        full_html = ot_html.build_full_html(
                            result, title=base, version_new=version_new,
                            visible_indices=vis, text_columns=text_cols,
                            front_columns=front_cols, order=full_order,
                            paginate=not self.profile.get("single_page", False),
                            header_labels=self.profile.get("header_labels"))

                        dest_dir = dest_dir_for(gcode or code)
                        full_path = os.path.join(dest_dir, f"{base}.html")
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(full_html)

                        # Een uitdraai met uitsluitend generieke lijntypes (geen
                        # hoofdgroep-specifieke rijen) krijgt geen changelog.
                        skip_changelog = (generic_fallback
                                          and _is_generic_only(result, scope_col))
                        # Vervallen objecten met een naamgenoot in de nieuwe
                        # release markeren (waarschijnlijk hernoemd/vervangen:
                        # nieuwe URI + ID). Naamvergelijking hoofdletter-ongevoelig.
                        deleted_notes = None
                        dnc = self.profile.get("deleted_name_check")
                        if dnc and dnc in result["headers"] and result["deleted"]:
                            ncol = result["headers"].index(dnc)
                            new_names = {
                                row["cells"][ncol]["value"].strip().casefold()
                                for row in result["rows"]
                                if ncol < len(row["cells"])
                                and row["cells"][ncol]["value"].strip()}
                            label = (f"naamgenoot in {version_new}"
                                     if version_new
                                     else "naamgenoot in de nieuwe release")
                            deleted_notes = [
                                label if (ncol < len(drow) and drow[ncol].strip()
                                          and drow[ncol].strip().casefold()
                                          in new_names)
                                else None
                                for drow in result["deleted"]]

                        if not skip_changelog:
                            changelog_html = ot_html.build_changelog_html(
                                result, title=f"Changelog {base}",
                                version_new=version_new, version_old=version_old,
                                visible_indices=vis, extra_columns=extra_cols,
                                orphans=orphans_this, deleted_notes=deleted_notes,
                                header_labels=self.profile.get("header_labels"))
                            changelog_path = os.path.join(
                                dest_dir, f"changelog-{base}.html")
                            with open(changelog_path, "w", encoding="utf-8") as f:
                                f.write(changelog_html)

                        if first is None:
                            first = full_path
                        wees_txt = (f", {len(orphans_this)} wees-.dwg"
                                    if orphans_this else "")
                        ngn = sum(1 for n in (deleted_notes or []) if n)
                        naamgenoot_txt = (f", {ngn} met naamgenoot" if ngn
                                          else "")
                        if skip_changelog:
                            self._queue.put(("log",
                                f"[{gcode or code}] {base}: alleen generieke "
                                f"lijntypes ({s['new'] + s['changed'] + s['deleted']}"
                                f" wijziging(en)) -> {base}.html "
                                f"(geen changelog nodig)"))
                            files += 1
                        else:
                            self._queue.put(("log",
                                f"[{gcode or code}] {base}: {s['new']} nieuw, "
                                f"{s['changed']} gewijzigd, {s['deleted']} vervallen"
                                f"{naamgenoot_txt}{hash_summary}{wees_txt} -> "
                                f"{base}.html + changelog-{base}.html"))
                            files += 2
                        made += 1

                # De losse run-brede pagina's 'dwg-zonder-tabelregel.html' en
                # 'regel-zonder-dwg.html' worden NIET meer geschreven: die twee
                # controles staan al in het gecombineerde kwaliteitscontroles-
                # rapport (tabblad 'Controles'). De wees-.dwg-sectie ONDERAAN elke
                # hoofdgroep-changelog (orphans_this) blijft wel bestaan.

                self._queue.put(("done", (made, files, first, open_after)))
            except Exception as exc:  # noqa: BLE001 - tonen in de GUI
                self._queue.put(("error", str(exc)))

        threading.Thread(target=worker, daemon=True).start()
        self.after(100, self._poll_queue)

    def _poll_queue(self) -> None:
        try:
            while True:
                kind, payload = self._queue.get_nowait()
                if kind == "log":
                    self._logmsg(payload)
                elif kind == "done":
                    made, files, first, open_after = payload
                    self._logmsg(f"Klaar: {made} hoofdgroep(en) verwerkt "
                                 f"({files} HTML-bestanden).")
                    self.gen_btn.config(state="normal")
                    self.app.save_config()
                    if open_after and first:
                        webbrowser.open(os.path.abspath(first))
                    return
                elif kind == "error":
                    messagebox.showerror("Fout", payload)
                    self._logmsg("FOUT: " + payload)
                    self.gen_btn.config(state="normal")
                    return
        except queue.Empty:
            pass
        self.after(100, self._poll_queue)


# ---------------------------------------------------------------------------
# Tabblad 'Overzicht': een kaart-pagina met knoppen naar de gepubliceerde HTML's
# ---------------------------------------------------------------------------
class IndexTab(ttk.Frame):
    """Doorzoekt een map (docs/changelog) naar gepubliceerde HTML's van een
    gekozen versie en maakt daar één overzichtspagina van: per hoofdgroep een
    blok met knoppen naar de tabellen en changelogs, plus een algemeen blok."""

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._last = None       # laatste scan-resultaat (ot_compare.scan_publication)
        self._build()

    def _build(self) -> None:
        info = ttk.Frame(self)
        info.pack(fill="x")
        ttk.Label(
            info, foreground="#555",
            text="Bron-map (docs/changelog), basis-URL en uitvoerbestand staan "
                 "op het tabblad 'Locaties'; de versie komt uit 'Versies'. Klik "
                 "hier 'Zoek bestanden' en 'Genereer overzicht'.").pack(anchor="w")

        btns = ttk.Frame(self)
        btns.pack(fill="x", pady=8)
        ttk.Button(btns, text="Zoek bestanden", command=self.on_scan
                   ).pack(side="left", padx=(0, 4))
        self.gen_btn = ttk.Button(btns, text="Genereer overzicht",
                                  command=self.on_generate)
        self.gen_btn.pack(side="left", padx=4)

        logframe = ttk.LabelFrame(self, text="Voortgang", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=12, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    # -- helpers -----------------------------------------------------------
    def _logmsg(self, msg: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    # -- zoeken + genereren ------------------------------------------------
    def on_scan(self):
        root = self.app.loc["index_root"].get().strip()
        version = self.app.version_new_var.get().strip()
        if not os.path.isdir(root):
            messagebox.showwarning(
                "Geen map", "Vul bij 'Locaties' een geldige map in om te "
                "doorzoeken (bijv. de map docs/changelog).")
            return None
        if not version:
            messagebox.showwarning(
                "Geen versie", "Vul bij 'Versies' een nieuwe versie in "
                "(bijv. 5.2).")
            return None

        # Het overzicht dat we zelf genereren nooit in de lijst opnemen: sluit
        # de basisnaam van het uitvoerbestand uit (naast de generieke
        # 'publicatieoverzicht*'-filter in scan_publication).
        out = self.app.loc["index_output"].get().strip()
        if os.path.isdir(out) or out.endswith(("/", "\\")):
            out = os.path.join(out, "index.html")
        exclude = {os.path.basename(out)} if out else set()
        data = ot_compare.scan_publication(root, version, exclude_names=exclude)
        self._last = data
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")
        self._logmsg(f"{data['count']} bestand(en) gevonden voor versie "
                     f"{version} ({', '.join(ot_compare.version_variants(version))}).")
        if data["general"]:
            self._logmsg(f"  (algemeen, voor alle hoofdgroepen): "
                         f"{len(data['general'])} bestand(en)")
        for code, entries in data["groups"]:
            self._logmsg(f"  {code}: {len(entries)} bestand(en)")
        self._logmsg(f"online basis-map (docs): {data['docs_root']}")
        if data["count"] == 0:
            self._logmsg("Geen bestanden met deze versie in de bestandsnaam "
                         "gevonden. Controleer map en versie.")
        return data

    def _quality_checkmarks(self, version: str, groups):
        """Lees het kwaliteitsrapport uit de changelog-map en bepaal per
        hoofdgroep (met objectentabel-CSV) het aantal foutregels. Retourneert
        de dict voor build_index_html/-markdown, of None als er geen rapport
        is (dan geen vinkjes; niet-blokkerend)."""
        root = self.app.loc["index_root"].get().strip()
        vdash = version.replace(".", "-")
        rep_name = (f"kwaliteitscontroles-{vdash}.html" if vdash
                    else "kwaliteitscontroles.html")
        rep_path = os.path.join(root, rep_name)
        if not os.path.isfile(rep_path):
            self._logmsg(
                f"Geen kwaliteitsrapport ({rep_name}) in de map — overzicht "
                "zonder vinkjes. Genereer het eerst via het tabblad 'Controles'.")
            return None
        try:
            with open(rep_path, encoding="utf-8") as f:
                report_html = f.read()
        except OSError as exc:
            self._logmsg("Kon kwaliteitsrapport niet lezen: " + str(exc)
                         + " — overzicht zonder vinkjes.")
            return None
        codes = [code for code, _entries in groups]
        marks = ot_compare.quality_checkmarks(
            report_html, self.app.loc["obj_new"].get().strip(), codes)
        if not marks:
            self._logmsg(
                f"Kwaliteitsrapport gevonden ({rep_name}), maar geen enkele "
                "hoofdgroep in het overzicht heeft een objectentabel-CSV in de "
                "map bij 'Locaties' — geen vinkjes.")
            return marks
        n_ok = sum(1 for m in marks.values() if not m["errors"])
        n_err = len(marks) - n_ok
        self._logmsg(
            f"Kwaliteitsrapport gebruikt ({rep_name}): {n_ok} hoofdgroep(en) "
            f"zonder fouten (groen vinkje), {n_err} met foutmeldingen (rood kruis).")
        return marks

    def on_generate(self) -> None:
        data = self._last or self.on_scan()
        if not data:
            return
        if data["count"] == 0:
            messagebox.showinfo(
                "Niets gevonden",
                "Geen gepubliceerde bestanden met deze versie in de map.")
            return
        output = self.app.loc["index_output"].get().strip()
        if not output:
            messagebox.showwarning(
                "Geen uitvoerbestand",
                "Vul bij 'Locaties' een uitvoerbestand voor het overzicht in.")
            return
        # Is er een MAP ingevuld i.p.v. een bestand (of een pad dat op een
        # separator eindigt)? Dan zou open(output,'w') een map openen ->
        # '[Errno 13] Permission denied' op Windows. Vul 'index.html' aan.
        if os.path.isdir(output) or output.endswith(("/", "\\")):
            output = os.path.join(output, "index.html")
            self._logmsg(f"Map ingevuld; overzicht wordt geschreven naar: {output}")

        version = self.app.version_new_var.get().strip()
        base_url = self.app.loc["base_url"].get().strip()

        # Het kwaliteitsrapport (Controles-tab) als input: hoofdgroepen met een
        # objectentabel-CSV krijgen een vinkje op basis van de foutregels in het
        # rapport. Het rapport staat in dezelfde docs/changelog-map (index_root).
        checkmarks = self._quality_checkmarks(version, data["groups"])

        html_txt = ot_html.build_index_html(
            data["groups"], data["general"],
            title=f"NLCS publicatie-overzicht {version}".strip(),
            version=version, base_url=base_url, checkmarks=checkmarks)
        try:
            parent = os.path.dirname(os.path.abspath(output))
            os.makedirs(parent, exist_ok=True)
            with open(output, "w", encoding="utf-8") as f:
                f.write(html_txt)
        except OSError as exc:
            messagebox.showerror("Fout", str(exc))
            self._logmsg("FOUT: " + str(exc))
            return

        self._logmsg(f"Overzicht geschreven: {output}")

        # Naast de HTML ook een Markdown-versie (kop per hoofdgroep + links)
        # voor gebruik in GitHub-issues; zelfde basisnaam, extensie .md.
        md_path = os.path.splitext(output)[0] + ".md"
        md_txt = ot_html.build_index_markdown(
            data["groups"], data["general"],
            title=f"NLCS publicatie-overzicht {version}".strip(),
            version=version, base_url=base_url, checkmarks=checkmarks)
        try:
            with open(md_path, "w", encoding="utf-8") as f:
                f.write(md_txt)
            self._logmsg(f"Markdown geschreven: {md_path}")
        except OSError as exc:
            self._logmsg("FOUT bij Markdown: " + str(exc))

        self.app.save_config()
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(output))


# ---------------------------------------------------------------------------
# Tabblad 'ID's': eerstvolgende vrije ID per soort + controles
# ---------------------------------------------------------------------------
# Elke soort heeft zijn EIGEN ID-reeks (gehele getallen, beginnend bij 1). Per
# soort: (sleutel, label, loc-key nieuw, loc-key vorig, ID-kolom, URI-kolom, het
# woord voor de rij-eenheid in de log, exclude-dict of None, naamkolom). De naam-
# kolom (omschrijving/symbool/arcering) toont een mensleesbare naam i.p.v. alleen
# de URI. De generieke lijntypes CONTINUOUS/V-CONTINUOUS-SO komen uit een andere
# publicatie en horen niet bij de eigen ID-reeks -> buiten de ID-analyse laten.
_LIJN_ID_EXCLUDE = {"match_col": "omschrijving",
                    "values": {"CONTINUOUS", "V-CONTINUOUS-SO"}}
_ID_PROFILES = [
    ("obj",  "Objecten",   "obj_new",  "obj_old",  "id_nummer", "objectURI",   "objecten",  None,            "omschrijving"),
    ("sym",  "Symbolen",   "sym_new",  "sym_old",  "id",        "symboolURI",  "symbolen",  None,            "symbool"),
    ("arc",  "Arceringen", "arc_new",  "arc_old",  "id",        "arceringURI", "arceringen", None,            "arcering"),
    ("lijn", "Lijntypes",  "lijn_new", "lijn_old", "id",        "lijntypeURI", "lijntypes", _LIJN_ID_EXCLUDE, "omschrijving"),
]

# Naam ↔ URI-controle: dubbele namen (binnen een hoofdgroep) die aan >1 URI hangen,
# over beide publicaties heen. Per soort: (key, new_key, old_key, name_col, uri_col,
# hoofd_col, exclude). hoofd_col wordt gebruikt om de hoofdgroep te bepalen wanneer
# de oude bron één gecombineerd bestand is (symbolen/arceringen/lijntypes); voor
# objecten staat oud per hoofdgroep en komt de hoofdgroep uit de bestandsnaam.
_NAME_URI_PROFILES = [
    ("obj",  "obj_new",  "obj_old",  "omschrijving", "objectURI",   "",             None),
    ("sym",  "sym_new",  "sym_old",  "symbool",      "symboolURI",  "sbibliotheek", None),
    ("arc",  "arc_new",  "arc_old",  "arcering",     "arceringURI", "abibliotheek", None),
    ("lijn", "lijn_new", "lijn_old", "omschrijving", "lijntypeURI", "hoofdgroep",   _LIJN_ID_EXCLUDE),
]


class IdTab(ttk.Frame):
    """Bepaalt PER soort (objecten, symbolen, arceringen, lijntypes) — elk met
    een eigen ID-reeks van gehele getallen vanaf 1 — het eerstvolgende vrije ID
    op basis van de nieuwe én de vorige publicatie. Toont ook de rijen zonder ID
    en controleert op dubbel gebruikte ID's en op URI's met een verschillend ID
    in beide publicaties. Mappen/bestanden komen van het tabblad 'Locaties'."""

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self.next_vars: dict[str, tk.StringVar] = {}
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555",
            text="Bepaalt per soort (objecten, symbolen, arceringen, lijntypes) "
                 "het eerstvolgende vrije ID-nummer — elke soort heeft een eigen "
                 "reeks gehele getallen vanaf 1. Gebaseerd op de nieuwe én vorige "
                 "publicatie (mappen/bestanden op 'Locaties'). Controleert ook op "
                 "dubbel gebruikte ID's en op URI's met een verschillend ID.").pack(
            anchor="w")

        # Bovenaan per soort een readonly 'eerstvolgende vrije ID' + kopieer-knop.
        summary = ttk.LabelFrame(self, text="Eerstvolgende vrije ID per soort",
                                 padding=8)
        summary.pack(fill="x", pady=8)
        for row, (key, label, *_rest) in enumerate(_ID_PROFILES):
            ttk.Label(summary, text=f"{label}:").grid(
                row=row, column=0, sticky="w", pady=1)
            var = tk.StringVar(value="—")
            self.next_vars[key] = var
            ttk.Entry(summary, textvariable=var, width=10, state="readonly",
                      font=("Consolas", 11, "bold")).grid(
                row=row, column=1, sticky="w", padx=(8, 4), pady=1)
            ttk.Button(summary, text="Kopieer",
                       command=lambda k=key: self._copy(k)).grid(
                row=row, column=2, padx=2)

        btns = ttk.Frame(self)
        btns.pack(anchor="w")
        ttk.Button(btns, text="Analyseer ID's", command=self.on_analyze
                   ).pack(side="left")
        ttk.Button(btns, text="Bewaar als HTML", command=self.on_save_html
                   ).pack(side="left", padx=(8, 0))

        logframe = ttk.LabelFrame(self, text="Resultaat", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=16, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    # -- helpers -----------------------------------------------------------
    def _logmsg(self, msg: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clearlog(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _copy(self, key: str) -> None:
        val = self.next_vars[key].get().strip()
        if val and val != "—":
            self.clipboard_clear()
            self.clipboard_append(val)

    @staticmethod
    def _valid(path: str) -> bool:
        return bool(path) and (os.path.isdir(path) or os.path.isfile(path))

    # -- analyse -----------------------------------------------------------
    def _run(self) -> tuple[list, bool]:
        """Voer de analyse per soort uit. Geeft (sections, any_source) terug;
        elke section = {key,label,id_col,woord,skipped,res}. Zet ook de
        'eerstvolgende vrije ID'-velden."""
        sections = []
        any_source = False
        for (key, label, new_key, old_key, id_col, uri_col, woord, exclude,
             name_col) in _ID_PROFILES:
            new_src = self.app.loc[new_key].get().strip()
            old_src = self.app.loc[old_key].get().strip()
            if not self._valid(new_src) and not self._valid(old_src):
                self.next_vars[key].set("—")
                sections.append({"key": key, "label": label, "id_col": id_col,
                                 "woord": woord, "skipped": True, "res": None})
                continue
            any_source = True
            res = ot_compare.analyze_ids(new_src, old_src, id_col, uri_col,
                                         exclude=exclude, name_col=name_col)
            self.next_vars[key].set(str(res["next_free"]))
            sections.append({"key": key, "label": label, "id_col": id_col,
                             "woord": woord, "skipped": False, "res": res})
        return sections, any_source

    def on_analyze(self) -> None:
        self._clearlog()
        sections, any_source = self._run()
        if not any_source:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' minstens één map/bestand in "
                "voor objecten, symbolen, arceringen of lijntypes.")
            return
        for s in sections:
            if s["skipped"]:
                self._logmsg(f"══ {s['label']} ══")
                self._logmsg("  Overgeslagen: geen geldige map/bestand ingevuld "
                             "bij 'Locaties'.")
                self._logmsg()
                continue
            self._report(s["label"], s["id_col"], s["woord"], s["res"])
        self.app.save_config()

    def on_save_html(self) -> None:
        out_dir = self.app.loc["output_dir"].get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Geen uitvoermap", "Vul bij 'Locaties' een geldige uitvoermap in "
                "om de HTML op te slaan.")
            return
        sections, any_source = self._run()
        if not any_source:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' minstens één map/bestand in "
                "voor objecten, symbolen, arceringen of lijntypes.")
            return
        html = ot_html.build_id_report_html(
            sections, title="ID-controle",
            version_new=self.app.version_new_var.get().strip(),
            version_old=self.app.version_old_var.get().strip())
        path = os.path.join(out_dir, "id-controle.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._logmsg(f"HTML opgeslagen: {path}")
        self.app.save_config()
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(path))

    def _report(self, label: str, id_col: str, woord: str, res: dict) -> None:
        self._logmsg(f"══ {label} ══")
        self._logmsg(f"{label} ingelezen: {len(res['new'])} (nieuw) + "
                     f"{len(res['old'])} (vorig) = "
                     f"{len(res['new']) + len(res['old'])}.")
        self._logmsg(f"Hoogste bestaande ID: {res['highest']}")
        self._logmsg(f"EERSTVOLGENDE VRIJE ID: {res['next_free']}")
        self._logmsg()

        # Rijen zonder ID (beide publicaties).
        blanks_new = res["blanks_new"]
        blanks_old = res["blanks_old"]
        total_blanks = len(blanks_new) + len(blanks_old)
        if total_blanks == 0:
            self._logmsg(f"{woord.upper()} ZONDER {id_col}: geen.")
            self._logmsg()
        else:
            self._logmsg(f"{woord.upper()} ZONDER {id_col}: {total_blanks} "
                         f"({len(blanks_new)} nieuw, {len(blanks_old)} vorig).")
            if blanks_new:
                self._logmsg(f"  Nieuwe publicatie ({len(blanks_new)}) — voorstel: "
                             f"ken achtereenvolgens {res['next_free']} t/m "
                             f"{res['next_free'] + len(blanks_new) - 1} toe:")
                for i, rec in enumerate(blanks_new):
                    self._logmsg(f"   {res['next_free'] + i:>6}  "
                                 f"{self._name_of(rec)}  "
                                 f"[{rec['file']} r{rec['row']}]")
            if blanks_old:
                self._logmsg(f"  Vorige publicatie ({len(blanks_old)}):")
                for rec in blanks_old:
                    self._logmsg(f"          {self._name_of(rec)}  "
                                 f"[{rec['file']} r{rec['row']}]")
            self._logmsg()

        # Controle 1: dubbel gebruikte ID's.
        dups = res["duplicates"]
        if dups:
            self._logmsg(f"⚠ DUBBELE ID'S: {len(dups)} ID('s) worden door meer "
                         f"dan één {woord[:-1] if woord.endswith('en') else woord}"
                         f" gebruikt:")
            for d in dups:
                self._logmsg(f"   ID {d['id']} -> {len(d['uris'])} stuks:")
                for rec in d["records"]:
                    self._logmsg(f"        {rec['source']}: {self._name_of(rec)}  "
                                 f"[{rec['file']} r{rec['row']}]")
        else:
            self._logmsg("✓ Geen dubbel gebruikte ID's gevonden.")
        self._logmsg()

        # Controle 2: zelfde URI, ander ID in oud vs. nieuw.
        mism = res["mismatches"]
        if mism:
            self._logmsg(f"⚠ VERSCHILLEND ID: {len(mism)} met dezelfde URI hebben "
                         f"in de vorige en nieuwe publicatie een ander ID:")
            for m in mism:
                naam = m.get("name") or m["uri"] or "(geen naam)"
                self._logmsg(f"   {naam}: nieuw={m['new_id']}  "
                             f"vorig={m['old_id']}")
        else:
            self._logmsg("✓ Elke URI die in beide publicaties voorkomt heeft "
                         "hetzelfde ID.")

        # Niet-gehele ID's (uitgesloten van de 'hoogste'-berekening).
        nonint = res["noninteger"]
        if nonint:
            self._logmsg()
            self._logmsg(f"Let op: {len(nonint)} niet-geheel ID('s) genegeerd bij "
                         f"het bepalen van het hoogste nummer:")
            for rec in nonint[:20]:
                self._logmsg(f"   '{rec['id']}'  {self._name_of(rec)}  "
                             f"[{rec['source']}: {rec['file']} r{rec['row']}]")
            if len(nonint) > 20:
                self._logmsg(f"   … en nog {len(nonint) - 20}.")
        self._logmsg()

    @staticmethod
    def _name_of(rec: dict) -> str:
        """Mensleesbare naam voor een ID-record; valt terug op de URI."""
        return rec.get("name") or rec.get("uri") or "(geen naam)"


# ---------------------------------------------------------------------------
# Tabblad 'Optie-fase-check': fase/optie consistent met de gecodeerde naam
# ---------------------------------------------------------------------------
# Per soort: (sleutel, label, loc-key nieuw, naamkolom, over te slaan namen).
# Alleen symbolen, lijntypes en arceringen (NIET de objectentabellen). De
# generieke lijntypes CONTINUOUS/V-CONTINUOUS-SO komen uit een andere publicatie
# met bewust lege fase/optie -> overslaan.
_NAME_PROFILES = [
    ("sym",  "Symbolen",   "sym_new",  "symbool",      ()),
    ("lijn", "Lijntypes",  "lijn_new", "omschrijving", ("CONTINUOUS", "V-CONTINUOUS-SO")),
    ("arc",  "Arceringen", "arc_new",  "arcering",     ()),
]


class OptieFaseCheckTab(ttk.Frame):
    """Controleert voor symbolen, lijntypes en arceringen of de kolommen 'fase'
    en 'optie' kloppen met de gecodeerde naam. Voorvoegsel V-/B-/… hoort als
    die letter in 'fase' te staan; een achtervoegsel -SO/-SOMM/-SOD/-SODMM/-D/
    -MM/-DMM hoort (zonder '-') in 'optie' te staan. Leest de nieuwe publicatie
    uit het tabblad 'Locaties'."""

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555", justify="left",
            text="Controleert symbolen, lijntypes en arceringen op een 'fase' en "
                 "'optie' die klopt met de naam. Voorvoegsel V-/B-/… → die letter "
                 "hoort in 'fase'; achtervoegsel -S/-SO/-SOMM/-SOD/-SODMM/-D/-MM/"
                 "-DMM → dat (zonder '-') hoort in 'optie'. Gebaseerd op de nieuwe "
                 "publicatie (mappen op 'Locaties').").pack(anchor="w")

        btns = ttk.Frame(self)
        btns.pack(anchor="w", pady=(8, 0))
        ttk.Button(btns, text="Analyseer optie/fase", command=self.on_analyze
                   ).pack(side="left")
        ttk.Button(btns, text="Bewaar als HTML", command=self.on_save_html
                   ).pack(side="left", padx=(8, 0))

        logframe = ttk.LabelFrame(self, text="Resultaat", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=18, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _logmsg(self, msg: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clearlog(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    @staticmethod
    def _valid(path: str) -> bool:
        return bool(path) and (os.path.isdir(path) or os.path.isfile(path))

    def _run(self) -> tuple[list, bool]:
        """Voer de optie/fase-controle per soort uit. Geeft (sections,
        any_source) terug; elke section = {label, skipped, violations}."""
        sections = []
        any_source = False
        for key, label, new_key, name_col, excl in _NAME_PROFILES:
            src = self.app.loc[new_key].get().strip()
            if not self._valid(src):
                sections.append({"label": label, "skipped": True,
                                 "violations": []})
                continue
            any_source = True
            viol = ot_compare.check_fase_optie(src, name_col, exclude_names=excl)
            sections.append({"label": label, "skipped": False, "violations": viol})
        return sections, any_source

    def on_analyze(self) -> None:
        self._clearlog()
        sections, any_source = self._run()
        if not any_source:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' minstens één map in voor "
                "symbolen, lijntypes of arceringen.")
            return
        total = 0
        for s in sections:
            self._logmsg(f"══ {s['label']} ══")
            if s["skipped"]:
                self._logmsg("  Overgeslagen: geen geldige map/bestand ingevuld "
                             "bij 'Locaties'.")
                self._logmsg()
                continue
            total += len(s["violations"])
            self._report(s["violations"])
        if total == 0:
            self._logmsg("Geen afwijkingen gevonden — alle 'fase' en 'optie' "
                         "kloppen met de naam.")

    def on_save_html(self) -> None:
        out_dir = self.app.loc["output_dir"].get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Geen uitvoermap", "Vul bij 'Locaties' een geldige uitvoermap in "
                "om de HTML op te slaan.")
            return
        sections, any_source = self._run()
        if not any_source:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' minstens één map in voor "
                "symbolen, lijntypes of arceringen.")
            return
        html = ot_html.build_fase_optie_html(
            sections, title="Optie-fase-check",
            version_new=self.app.version_new_var.get().strip())
        path = os.path.join(out_dir, "optie-fase-check.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._logmsg(f"HTML opgeslagen: {path}")
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(path))

    def _report(self, viol: list) -> None:
        if not viol:
            self._logmsg("  ✓ Alle 'fase' en 'optie' kloppen met de naam.")
            self._logmsg()
            return
        fase = [v for v in viol if v["kind"] == "fase"]
        optie = [v for v in viol if v["kind"] == "optie"]

        def dump(titel: str, items: list, col: str) -> None:
            if not items:
                return
            self._logmsg(f"  {titel}: {len(items)}")
            for v in items:
                got = v["got"] or "(leeg)"
                exp = v["expected"] or "(leeg)"
                self._logmsg(f"     {v['name']}")
                self._logmsg(f"        {col}: is '{got}'  →  verwacht '{exp}'  "
                             f"[{v['file']} r{v['row']}]")

        dump("FASE-afwijkingen", fase, "fase")
        dump("OPTIE-afwijkingen", optie, "optie")
        self._logmsg()


# ---------------------------------------------------------------------------
# Tabblad 'Objectenboom': controleert de hiërarchie van de objecten
# ---------------------------------------------------------------------------
_TREE_ERR_LABELS = {
    "count": "verkeerd aantal segmenten (geen +1 t.o.v. ouder)",
    "prefix": "naam is geen uitbreiding van de oudernaam",
    "separator": "scheidingsteken klopt niet (oudernaam niet exact vooraan)",
    "orphan": "bovenliggend id onbekend",
    "root_multi": "hoofdobject met meer dan één segment",
    "subobjecten": "meer dan 5 subobjecten in de laagnaam",
}


class ObjectTreeTab(ttk.Frame):
    """Controleert de boomstructuur van de objecten. De objecten vormen een boom
    via 'kind_van' (= id_nummer van het bovenliggende object; leeg = bovenaan).
    Regel: een onderliggend object heeft precies één segment (gescheiden door
    '-'/'_') méér dan zijn ouder, en de oudernaam is het begin van de kindnaam.
    Leest de nieuwe objectenmap uit het tabblad 'Locaties'."""

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555", justify="left",
            text="Controleert de boomstructuur van de objecten. De boom volgt "
                 "uit 'kind_van' (het id_nummer van het bovenliggende object; "
                 "leeg = bovenaan). Een onderliggend object hoort precies één "
                 "segment méér te hebben dan zijn ouder — niet meer, niet "
                 "minder — en de oudernaam hoort het begin van de kindnaam te "
                 "zijn. Ook wordt gecontroleerd of een laagnaam niet meer dan "
                 "5 subobjecten bevat. Gebaseerd op de nieuwe objectenmap "
                 "(tabblad 'Locaties').").pack(anchor="w")

        btns = ttk.Frame(self)
        btns.pack(anchor="w", pady=(8, 0))
        ttk.Button(btns, text="Controleer boomstructuur", command=self.on_analyze
                   ).pack(side="left")
        ttk.Button(btns, text="Bewaar als HTML", command=self.on_save_html
                   ).pack(side="left", padx=(8, 0))

        logframe = ttk.LabelFrame(self, text="Resultaat", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=18, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _logmsg(self, msg: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clearlog(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    @staticmethod
    def _valid(path: str) -> bool:
        return bool(path) and (os.path.isdir(path) or os.path.isfile(path))

    def _run(self) -> dict | None:
        src = self.app.loc["obj_new"].get().strip()
        if not self._valid(src):
            return None
        return ot_compare.check_object_tree(src)

    def on_analyze(self) -> None:
        self._clearlog()
        res = self._run()
        if res is None:
            messagebox.showwarning(
                "Geen bron", "Vul bij 'Locaties' een geldige map voor de nieuwe "
                "objectentabellen in.")
            return
        n_layers = (res["max_depth"] + 1) if res["nodes"] else 0
        self._logmsg(f"Objecten ingelezen: {res['count']}")
        self._logmsg(f"Hoofdobjecten (roots): {len(res['roots'])}")
        self._logmsg(f"Aantal lagen: {n_layers}")
        self._logmsg()
        errors = res["errors"]
        if not errors:
            self._logmsg("✓ Geen fouten gevonden — elk onderliggend object heeft "
                         "precies één segment meer dan zijn bovenliggende object.")
            return
        self._logmsg(f"⚠ {len(errors)} fout(en) gevonden:")
        self._logmsg()
        # groeperen per type voor een leesbaar rapport
        by_type: dict[str, list] = {}
        for e in errors:
            by_type.setdefault(e["type"], []).append(e)
        for t, items in by_type.items():
            self._logmsg(f"── {t}: {_TREE_ERR_LABELS.get(t, t)} ({len(items)}) ──")
            for e in items:
                par = (f"ouder '{e['parent_name']}' (#{e['parent']})"
                       if e.get("parent") else "geen ouder")
                self._logmsg(f"   {e['name']} (#{e['id']}) — {par}")
                self._logmsg(f"      {e['detail']}")
            self._logmsg()

    def on_save_html(self) -> None:
        out_dir = self.app.loc["output_dir"].get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Geen uitvoermap", "Vul bij 'Locaties' een geldige uitvoermap in "
                "om de HTML op te slaan.")
            return
        res = self._run()
        if res is None:
            messagebox.showwarning(
                "Geen bron", "Vul bij 'Locaties' een geldige map voor de nieuwe "
                "objectentabellen in.")
            return
        html = ot_html.build_object_tree_html(
            res, title="Objectenboom",
            version_new=self.app.version_new_var.get().strip())
        path = os.path.join(out_dir, "objectenboom.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._logmsg(f"HTML opgeslagen: {path}")
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(path))


# ---------------------------------------------------------------------------
# Tabblad 'Lijntype-gebruik': wordt elk lijntype ook in de objecten gebruikt?
# ---------------------------------------------------------------------------
class LijntypeUsageTab(ttk.Frame):
    """Controleert of elk bestaand lijntype ook in de objectentabel wordt
    gebruikt. Detectie op NAAM: de objecten verwijzen in de kolommen
    lt_b/lt_n/lt_v/lt_t naar de naam ('omschrijving') van een lijntype. Leest de
    nieuwe lijntypes- én objectenmap uit het tabblad 'Locaties'."""

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555", justify="left",
            text="Controleert of elk lijntype ook in de objectentabel wordt "
                 "gebruikt. De objecten verwijzen op naam (kolommen "
                 "lt_b/lt_n/lt_v/lt_t) naar een lijntype. Welke lijntypes "
                 "bestaan wel maar worden nergens gebruikt? Gebaseerd op de "
                 "nieuwe lijntypes- en objectenmap (tabblad "
                 "'Locaties').").pack(anchor="w")

        btns = ttk.Frame(self)
        btns.pack(anchor="w", pady=(8, 0))
        ttk.Button(btns, text="Controleer lijntype-gebruik", command=self.on_analyze
                   ).pack(side="left")
        ttk.Button(btns, text="Bewaar als HTML", command=self.on_save_html
                   ).pack(side="left", padx=(8, 0))

        logframe = ttk.LabelFrame(self, text="Resultaat", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=18, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _logmsg(self, msg: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clearlog(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    @staticmethod
    def _valid(path: str) -> bool:
        return bool(path) and (os.path.isdir(path) or os.path.isfile(path))

    def _run(self) -> dict | None:
        lijn = self.app.loc["lijn_new"].get().strip()
        obj = self.app.loc["obj_new"].get().strip()
        if not self._valid(lijn) or not self._valid(obj):
            return None
        return ot_compare.check_lijntype_usage(lijn, obj)

    def on_analyze(self) -> None:
        self._clearlog()
        res = self._run()
        if res is None:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' een geldige map in voor "
                "zowel de nieuwe lijntypes als de nieuwe objectentabellen.")
            return
        self._logmsg(f"Lijntypes: {res['lijn_total']}  "
                     f"(gebruikt: {len(res['used'])}, "
                     f"niet gebruikt: {len(res['unused'])})")
        self._logmsg()
        unused = res["unused"]
        if not unused:
            self._logmsg("✓ Elk lijntype wordt in de objectentabel gebruikt.")
        else:
            self._logmsg(f"⚠ {len(unused)} lijntype(s) niet gebruikt in de "
                         "objecten:")
            for u in unused:
                self._logmsg(f"   {u['name']}   [hoofdgroep {u['hoofdgroep']}, "
                             f"{u['file']}]")

    def on_save_html(self) -> None:
        out_dir = self.app.loc["output_dir"].get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Geen uitvoermap", "Vul bij 'Locaties' een geldige uitvoermap in "
                "om de HTML op te slaan.")
            return
        res = self._run()
        if res is None:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' een geldige map in voor "
                "zowel de nieuwe lijntypes als de nieuwe objectentabellen.")
            return
        html = ot_html.build_lijntype_usage_html(
            res, title="Lijntype-gebruik",
            version_new=self.app.version_new_var.get().strip())
        path = os.path.join(out_dir, "lijntype-gebruik.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._logmsg(f"HTML opgeslagen: {path}")
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(path))


class SearchtermTab(ttk.Frame):
    """Controleert of elk symbool/elke arcering via een zoekterm in de
    objectentabel gevonden wordt. De zoekterm is de sobject-waarde (symbolen)
    resp. aobject-waarde (arceringen) uit de objecten; een naam is 'gevonden' als
    zo'n waarde als tekst in de symbool-/arceringnaam voorkomt. Leest de nieuwe
    symbolen-, arceringen- en objectenmap uit het tabblad 'Locaties'."""

    # (naam-map-sleutel, naam-kolom, objecten-kolom, label)
    _SOORTEN = [
        ("sym_new", "symbool", "sobject", "symbolen"),
        ("arc_new", "arcering", "aobject", "arceringen"),
    ]

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555", justify="left",
            text="Controleert of elk symbool/elke arcering via een zoekterm in "
                 "de objectentabel wordt gevonden. De zoekterm is de sobject- "
                 "(symbolen) resp. aobject-waarde (arceringen) uit de objecten; "
                 "een naam telt als 'gevonden' als zo'n waarde als tekst in de "
                 "naam voorkomt. Gebaseerd op de nieuwe symbolen-, arceringen- en "
                 "objectenmap (tabblad 'Locaties').").pack(anchor="w")

        btns = ttk.Frame(self)
        btns.pack(anchor="w", pady=(8, 0))
        ttk.Button(btns, text="Controleer zoektermen", command=self.on_analyze
                   ).pack(side="left")
        ttk.Button(btns, text="Bewaar als HTML", command=self.on_save_html
                   ).pack(side="left", padx=(8, 0))

        logframe = ttk.LabelFrame(self, text="Resultaat", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=18, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _logmsg(self, msg: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clearlog(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    @staticmethod
    def _valid(path: str) -> bool:
        return bool(path) and (os.path.isdir(path) or os.path.isfile(path))

    def _run(self) -> list | None:
        obj = self.app.loc["obj_new"].get().strip()
        if not self._valid(obj):
            return None
        sections = []
        for name_key, name_col, obj_col, label in self._SOORTEN:
            src = self.app.loc[name_key].get().strip()
            if not self._valid(src):
                continue
            res = ot_compare.check_searchterm_coverage(src, obj, name_col, obj_col)
            res["label"] = label
            res["obj_col"] = obj_col
            sections.append(res)
        return sections or None

    def on_analyze(self) -> None:
        self._clearlog()
        sections = self._run()
        if sections is None:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' een geldige objectenmap in "
                "en minstens één van de symbolen- of arceringenmap.")
            return
        for s in sections:
            self._logmsg(f"{s['label'].capitalize()}: {s['total']}  "
                         f"(gevonden: {s['found']}, "
                         f"niet gevonden: {len(s['not_found'])}; "
                         f"{s['term_count']} zoektermen)")
            nf = s["not_found"]
            if not nf:
                self._logmsg("   ✓ Elke naam bevat een zoekterm.")
            else:
                for d in nf:
                    self._logmsg(f"   {d['name']}   [{d['file']}]")
            self._logmsg()

    def on_save_html(self) -> None:
        out_dir = self.app.loc["output_dir"].get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Geen uitvoermap", "Vul bij 'Locaties' een geldige uitvoermap in "
                "om de HTML op te slaan.")
            return
        sections = self._run()
        if sections is None:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' een geldige objectenmap in "
                "en minstens één van de symbolen- of arceringenmap.")
            return
        html = ot_html.build_searchterm_html(
            sections, title="Zoekterm-controle",
            version_new=self.app.version_new_var.get().strip())
        path = os.path.join(out_dir, "zoekterm-controle.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._logmsg(f"HTML opgeslagen: {path}")
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(path))


class SearchtermMinTab(ttk.Frame):
    """Controleert de omgekeerde richting van SearchtermTab: vindt elke zoekterm
    (sobject-waarde voor symbolen, aobject-waarde voor arceringen) uit de
    objectentabel minstens één symbool/arcering? Er moet er minimaal 1 zijn.
    Leest de nieuwe symbolen-, arceringen- en objectenmap uit 'Locaties'."""

    # (naam-map-sleutel, naam-kolom, objecten-kolom, label)
    _SOORTEN = [
        ("sym_new", "symbool", "sobject", "symbolen"),
        ("arc_new", "arcering", "aobject", "arceringen"),
    ]

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555", justify="left",
            text="Controleert of elke zoekterm uit de objectentabel minstens één "
                 "symbool/arcering vindt (minimaal 1 vereist). De zoekterm is de "
                 "sobject-waarde (symbolen) resp. aobject-waarde (arceringen) uit "
                 "de objecten; een symbool/arcering telt als 'gevonden' als de "
                 "zoekterm als tekst in de naam voorkomt. Gebaseerd op de nieuwe "
                 "symbolen-, arceringen- en objectenmap (tabblad 'Locaties').").pack(
                     anchor="w")

        btns = ttk.Frame(self)
        btns.pack(anchor="w", pady=(8, 0))
        ttk.Button(btns, text="Controleer zoektermen", command=self.on_analyze
                   ).pack(side="left")
        ttk.Button(btns, text="Bewaar als HTML", command=self.on_save_html
                   ).pack(side="left", padx=(8, 0))

        logframe = ttk.LabelFrame(self, text="Resultaat", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=18, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _logmsg(self, msg: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clearlog(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    @staticmethod
    def _valid(path: str) -> bool:
        return bool(path) and (os.path.isdir(path) or os.path.isfile(path))

    def _run(self) -> list | None:
        obj = self.app.loc["obj_new"].get().strip()
        if not self._valid(obj):
            return None
        sections = []
        for name_key, name_col, obj_col, label in self._SOORTEN:
            src = self.app.loc[name_key].get().strip()
            if not self._valid(src):
                continue
            res = ot_compare.check_searchterm_min(obj, src, obj_col, name_col)
            res["label"] = label
            res["obj_col"] = obj_col
            sections.append(res)
        return sections or None

    def on_analyze(self) -> None:
        self._clearlog()
        sections = self._run()
        if sections is None:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' een geldige objectenmap in "
                "en minstens één van de symbolen- of arceringenmap.")
            return
        for s in sections:
            self._logmsg(f"{s['obj_col']}: {s['total']} zoektermen  "
                         f"(met treffer: {s['ok']}, "
                         f"zonder treffer: {len(s['empty'])}; "
                         f"{s['name_count']} {s['label']})")
            empty = s["empty"]
            if not empty:
                self._logmsg(f"   ✓ Elke zoekterm vindt minstens één {s['label']}.")
            else:
                for d in empty:
                    files = ", ".join(d.get("files", []))
                    self._logmsg(f"   {d['term']}   [{files}]")
            self._logmsg()

    def on_save_html(self) -> None:
        out_dir = self.app.loc["output_dir"].get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Geen uitvoermap", "Vul bij 'Locaties' een geldige uitvoermap in "
                "om de HTML op te slaan.")
            return
        sections = self._run()
        if sections is None:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' een geldige objectenmap in "
                "en minstens één van de symbolen- of arceringenmap.")
            return
        html = ot_html.build_searchterm_min_html(
            sections, title="Zoekterm-treffers",
            version_new=self.app.version_new_var.get().strip())
        path = os.path.join(out_dir, "zoekterm-treffers.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._logmsg(f"HTML opgeslagen: {path}")
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(path))


class FaseVisualisatieTab(ttk.Frame):
    """Controleert of elk object voor alle fasen (Bestaand/Nieuw/Vervallen/
    Tijdelijk) een visualisatie heeft. De hoofdgroepen AL en ZZ hebben alleen
    een bestaande-situatie-visualisatie (fase B). Leest de nieuwe objectenmap
    uit het tabblad 'Locaties'."""

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555", justify="left",
            text="Controleert of elk object voor alle fasen een visualisatie "
                 "heeft: Bestaand, Nieuw, Vervallen en Tijdelijk (velden "
                 "lw/kl*/lt per fase). De hoofdgroepen AL en ZZ hebben alleen "
                 "een visualisatie voor de bestaande situatie (fase B). "
                 "Gebaseerd op de nieuwe objectenmap (tabblad "
                 "'Locaties').").pack(anchor="w")

        btns = ttk.Frame(self)
        btns.pack(anchor="w", pady=(8, 0))
        ttk.Button(btns, text="Controleer fase-visualisatie",
                   command=self.on_analyze).pack(side="left")
        ttk.Button(btns, text="Bewaar als HTML", command=self.on_save_html
                   ).pack(side="left", padx=(8, 0))

        logframe = ttk.LabelFrame(self, text="Resultaat", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=18, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _logmsg(self, msg: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clearlog(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    @staticmethod
    def _valid(path: str) -> bool:
        return bool(path) and (os.path.isdir(path) or os.path.isfile(path))

    def _run(self) -> dict | None:
        obj = self.app.loc["obj_new"].get().strip()
        if not self._valid(obj):
            return None
        return ot_compare.check_fase_visualisatie(obj)

    def on_analyze(self) -> None:
        self._clearlog()
        res = self._run()
        if res is None:
            messagebox.showwarning(
                "Geen bron", "Vul bij 'Locaties' een geldige map in voor de "
                "nieuwe objectentabellen.")
            return
        self._logmsg(f"Objecten: {res['total']}  "
                     f"(volledig: {res['ok']}, "
                     f"fase ontbreekt: {len(res['missing'])})")
        self._logmsg()
        missing = res["missing"]
        if not missing:
            self._logmsg("✓ Elk object heeft voor alle verwachte fasen een "
                         "visualisatie.")
        else:
            self._logmsg(f"⚠ {len(missing)} object(en) missen een fase-"
                         "visualisatie:")
            for m in missing:
                self._logmsg(f"   {m['name']}   [hoofdgroep {m['hoofdgroep']}] "
                             f"ontbreekt: {', '.join(m['missing'])}")
        unexpected = res["unexpected"]
        if unexpected:
            self._logmsg()
            self._logmsg(f"⚠ {len(unexpected)} object(en) in AL/ZZ met een "
                         "onverwachte fase-visualisatie:")
            for u in unexpected:
                self._logmsg(f"   {u['name']}   [hoofdgroep {u['hoofdgroep']}] "
                             f"onverwacht: {', '.join(u['extra'])}")

    def on_save_html(self) -> None:
        out_dir = self.app.loc["output_dir"].get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Geen uitvoermap", "Vul bij 'Locaties' een geldige uitvoermap in "
                "om de HTML op te slaan.")
            return
        res = self._run()
        if res is None:
            messagebox.showwarning(
                "Geen bron", "Vul bij 'Locaties' een geldige map in voor de "
                "nieuwe objectentabellen.")
            return
        html = ot_html.build_fase_visualisatie_html(
            res, title="Fase-visualisatie",
            version_new=self.app.version_new_var.get().strip())
        path = os.path.join(out_dir, "fase-visualisatie.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._logmsg(f"HTML opgeslagen: {path}")
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(path))


class DuplicateNamesTab(ttk.Frame):
    """Controleert of er binnen één hoofdgroep dubbele namen voorkomen, voor
    objecten, symbolen, lijntypes en arceringen. Een dubbele naam is dezelfde
    naam die binnen hetzelfde bestand (= één hoofdgroep) meer dan eens voorkomt;
    dezelfde naam in verschillende hoofdgroepen telt niet als dubbel. Leest de
    nieuwe mappen uit het tabblad 'Locaties'."""

    # (naam-map-sleutel, naam-kolom, label)
    _SOORTEN = [
        ("obj_new", "omschrijving", "objecten"),
        ("sym_new", "symbool", "symbolen"),
        ("lijn_new", "omschrijving", "lijntypes"),
        ("arc_new", "arcering", "arceringen"),
    ]

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555", justify="left",
            text="Controleert of er binnen één hoofdgroep dubbele namen "
                 "voorkomen, voor objecten, symbolen, lijntypes en arceringen. "
                 "Een dubbele naam is dezelfde naam die binnen hetzelfde bestand "
                 "(één hoofdgroep) meer dan eens voorkomt; dezelfde naam in "
                 "verschillende hoofdgroepen telt niet als dubbel. Gebaseerd op "
                 "de nieuwe mappen (tabblad 'Locaties').").pack(anchor="w")

        btns = ttk.Frame(self)
        btns.pack(anchor="w", pady=(8, 0))
        ttk.Button(btns, text="Controleer dubbele namen", command=self.on_analyze
                   ).pack(side="left")
        ttk.Button(btns, text="Bewaar als HTML", command=self.on_save_html
                   ).pack(side="left", padx=(8, 0))

        logframe = ttk.LabelFrame(self, text="Resultaat", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=18, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _logmsg(self, msg: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clearlog(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    @staticmethod
    def _valid(path: str) -> bool:
        return bool(path) and (os.path.isdir(path) or os.path.isfile(path))

    def _run(self) -> list | None:
        sections = []
        for name_key, name_col, label in self._SOORTEN:
            src = self.app.loc[name_key].get().strip()
            if not self._valid(src):
                continue
            res = ot_compare.check_duplicate_names(src, name_col)
            res["label"] = label
            res["name_col"] = name_col
            sections.append(res)
        return sections or None

    def on_analyze(self) -> None:
        self._clearlog()
        sections = self._run()
        if sections is None:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' minstens één geldige map in "
                "voor objecten, symbolen, lijntypes of arceringen.")
            return
        for s in sections:
            dups = s["duplicates"]
            self._logmsg(f"{s['label'].capitalize()}: {s['total']}  "
                         f"(uniek per hoofdgroep: {s['unique']}, "
                         f"dubbel: {len(dups)})")
            if not dups:
                self._logmsg("   ✓ Geen dubbele namen binnen een hoofdgroep.")
            else:
                for d in dups:
                    self._logmsg(f"   {d['name']}  {d['count']}×   "
                                 f"[{d['file']}]  rij(en) "
                                 f"{', '.join(str(r) for r in d['rows'])}")
            self._logmsg()

    def on_save_html(self) -> None:
        out_dir = self.app.loc["output_dir"].get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Geen uitvoermap", "Vul bij 'Locaties' een geldige uitvoermap in "
                "om de HTML op te slaan.")
            return
        sections = self._run()
        if sections is None:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' minstens één geldige map in "
                "voor objecten, symbolen, lijntypes of arceringen.")
            return
        html = ot_html.build_duplicate_names_html(
            sections, title="Dubbele namen",
            version_new=self.app.version_new_var.get().strip())
        path = os.path.join(out_dir, "dubbele-namen.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._logmsg(f"HTML opgeslagen: {path}")
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(path))


class ElementLinkTab(ttk.Frame):
    """Controleert in de objectentabel de koppeling tussen de `element`-kolom en
    sobject/aobject: bevat `element` het token S dan moet er een sobject zijn (en
    omgekeerd), bevat het A dan moet er een aobject zijn (en omgekeerd). Leest de
    nieuwe objectenmap uit het tabblad 'Locaties'."""

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555", justify="left",
            text="Controleert in de objectentabel of de element-kolom (tokens "
                 "S=symbool, A=arcering) overeenkomt met sobject/aobject: een S "
                 "vereist een sobject en omgekeerd, een A vereist een aobject en "
                 "omgekeerd. Gebaseerd op de nieuwe objectenmap (tabblad "
                 "'Locaties').").pack(anchor="w")

        btns = ttk.Frame(self)
        btns.pack(anchor="w", pady=(8, 0))
        ttk.Button(btns, text="Controleer element-koppeling",
                   command=self.on_analyze).pack(side="left")
        ttk.Button(btns, text="Bewaar als HTML", command=self.on_save_html
                   ).pack(side="left", padx=(8, 0))

        logframe = ttk.LabelFrame(self, text="Resultaat", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=18, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _logmsg(self, msg: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clearlog(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    @staticmethod
    def _valid(path: str) -> bool:
        return bool(path) and (os.path.isdir(path) or os.path.isfile(path))

    def _run(self) -> dict | None:
        obj = self.app.loc["obj_new"].get().strip()
        if not self._valid(obj):
            return None
        return ot_compare.check_element_object_link(obj)

    def on_analyze(self) -> None:
        self._clearlog()
        res = self._run()
        if res is None:
            messagebox.showwarning(
                "Geen bron", "Vul bij 'Locaties' een geldige map in voor de "
                "nieuwe objectentabellen.")
            return
        self._logmsg(f"Objecten: {res['total']}  "
                     f"(correct: {res['ok']}, "
                     f"afwijkend: {len(res['violations'])})")
        self._logmsg()
        violations = res["violations"]
        if not violations:
            self._logmsg("✓ Elk object heeft een consistente element-koppeling.")
        else:
            self._logmsg(f"⚠ {len(violations)} object(en) met een afwijkende "
                         "koppeling:")
            for v in violations:
                self._logmsg(f"   {v['name']}  [element {v['element']}]  "
                             f"{'; '.join(v['problems'])}   "
                             f"[{v['file']} r{v['row']}]")

    def on_save_html(self) -> None:
        out_dir = self.app.loc["output_dir"].get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Geen uitvoermap", "Vul bij 'Locaties' een geldige uitvoermap in "
                "om de HTML op te slaan.")
            return
        res = self._run()
        if res is None:
            messagebox.showwarning(
                "Geen bron", "Vul bij 'Locaties' een geldige map in voor de "
                "nieuwe objectentabellen.")
            return
        html = ot_html.build_element_link_html(
            res, title="Element-koppeling",
            version_new=self.app.version_new_var.get().strip())
        path = os.path.join(out_dir, "element-koppeling.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._logmsg(f"HTML opgeslagen: {path}")
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(path))


class SpecialCharsTab(ttk.Frame):
    """Controleert namen van objecten/symbolen/lijntypes/arceringen op tekens die
    in CAD-laag-/symboolnamen niet zijn toegestaan (AutoCAD, MicroStation, LISP).
    Spatie, punt, '-' en '_' zijn toegestaan. Leest de vier nieuwe mappen uit
    'Locaties'. Kleine letters worden apart, informatief, getoond (geen fout)."""

    # (map-sleutel, naam-kolom, label)
    _SOORTEN = [
        ("obj_new", "omschrijving", "objecten"),
        ("sym_new", "symbool", "symbolen"),
        ("lijn_new", "omschrijving", "lijntypes"),
        ("arc_new", "arcering", "arceringen"),
    ]

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555", justify="left",
            text="Controleert de namen op tekens die in CAD-laag- of "
                 "symboolnamen niet werken (AutoCAD, MicroStation) of LISP-tools "
                 "breken, bijv. \\ / , [ ] ( ) < > \" ' : ; ? * | = `. Spaties, "
                 "de punt (decimaalteken), - en _ zijn toegestaan. Kleine letters "
                 "worden apart en informatief getoond (toegestaan voor eenheden "
                 "als mm/Mm en elementsymbolen als Cu). Gebaseerd op de vier "
                 "nieuwe mappen (tabblad 'Locaties').").pack(anchor="w")

        btns = ttk.Frame(self)
        btns.pack(anchor="w", pady=(8, 0))
        ttk.Button(btns, text="Controleer speciale tekens",
                   command=self.on_analyze).pack(side="left")
        ttk.Button(btns, text="Bewaar als HTML", command=self.on_save_html
                   ).pack(side="left", padx=(8, 0))

        logframe = ttk.LabelFrame(self, text="Resultaat", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=18, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _logmsg(self, msg: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clearlog(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    @staticmethod
    def _valid(path: str) -> bool:
        return bool(path) and (os.path.isdir(path) or os.path.isfile(path))

    def _run(self) -> list | None:
        sections = []
        for name_key, name_col, label in self._SOORTEN:
            src = self.app.loc[name_key].get().strip()
            if not self._valid(src):
                continue
            res = ot_compare.check_special_chars(src, name_col)
            res["label"] = label
            res["name_col"] = name_col
            sections.append(res)
        return sections or None

    def on_analyze(self) -> None:
        self._clearlog()
        sections = self._run()
        if sections is None:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' minstens één geldige map in "
                "(objecten/symbolen/lijntypes/arceringen).")
            return
        for s in sections:
            self._logmsg(f"{s['label'].capitalize()}: {s['total']}  "
                         f"(zonder verboden teken: {s['ok']}, "
                         f"met verboden teken: {len(s['violations'])}; "
                         f"kleine letter: {len(s['lowercase'])})")
            viol = s["violations"]
            if not viol:
                self._logmsg("   ✓ Geen niet-toegestane tekens.")
            else:
                for d in viol:
                    chars = " ".join(d.get("chars", []))
                    self._logmsg(f"   {d['name']}   [{chars}]   "
                                 f"[{d['file']} r{d['row']}]")
            self._logmsg()

    def on_save_html(self) -> None:
        out_dir = self.app.loc["output_dir"].get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Geen uitvoermap", "Vul bij 'Locaties' een geldige uitvoermap in "
                "om de HTML op te slaan.")
            return
        sections = self._run()
        if sections is None:
            messagebox.showwarning(
                "Geen bronnen", "Vul bij 'Locaties' minstens één geldige map in "
                "(objecten/symbolen/lijntypes/arceringen).")
            return
        html = ot_html.build_special_chars_html(
            sections, title="Speciale tekens",
            forbidden=ot_compare.FORBIDDEN_NAME_CHARS,
            version_new=self.app.version_new_var.get().strip())
        path = os.path.join(out_dir, "speciale-tekens.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._logmsg(f"HTML opgeslagen: {path}")
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(path))


class ArceringVerklaringTab(ttk.Frame):
    """Controleert of elke arcering een (lange) verklaring heeft in de kolom
    `vrkl_lang`. Leest de nieuwe arceringenmap uit het tabblad 'Locaties'."""

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555", justify="left",
            text="Controleert of elke arcering een verklaring heeft in de kolom "
                 "vrkl_lang (de tekst voor de legenda/verklaring). Gebaseerd op "
                 "de nieuwe arceringenmap (tabblad 'Locaties').").pack(anchor="w")

        btns = ttk.Frame(self)
        btns.pack(anchor="w", pady=(8, 0))
        ttk.Button(btns, text="Controleer verklaring",
                   command=self.on_analyze).pack(side="left")
        ttk.Button(btns, text="Bewaar als HTML", command=self.on_save_html
                   ).pack(side="left", padx=(8, 0))

        logframe = ttk.LabelFrame(self, text="Resultaat", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=18, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _logmsg(self, msg: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clearlog(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    @staticmethod
    def _valid(path: str) -> bool:
        return bool(path) and (os.path.isdir(path) or os.path.isfile(path))

    def _run(self) -> dict | None:
        arc = self.app.loc["arc_new"].get().strip()
        if not self._valid(arc):
            return None
        return ot_compare.check_arcering_verklaring(arc)

    def on_analyze(self) -> None:
        self._clearlog()
        res = self._run()
        if res is None:
            messagebox.showwarning(
                "Geen bron", "Vul bij 'Locaties' een geldige map in voor de "
                "nieuwe arceringen.")
            return
        self._logmsg(f"Arceringen: {res['total']}  "
                     f"(met verklaring: {res['ok']}, "
                     f"zonder: {len(res['missing'])})")
        self._logmsg()
        missing = res["missing"]
        if not missing:
            self._logmsg("✓ Elke arcering heeft een verklaring.")
        else:
            self._logmsg(f"⚠ {len(missing)} arcering(en) zonder verklaring:")
            for m in missing:
                self._logmsg(f"   {m['name']}   [{m['file']} r{m['row']}]")

    def on_save_html(self) -> None:
        out_dir = self.app.loc["output_dir"].get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Geen uitvoermap", "Vul bij 'Locaties' een geldige uitvoermap in "
                "om de HTML op te slaan.")
            return
        res = self._run()
        if res is None:
            messagebox.showwarning(
                "Geen bron", "Vul bij 'Locaties' een geldige map in voor de "
                "nieuwe arceringen.")
            return
        html = ot_html.build_arcering_verklaring_html(
            res, title="Verklaring",
            version_new=self.app.version_new_var.get().strip())
        path = os.path.join(out_dir, "arcering-verklaring.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._logmsg(f"HTML opgeslagen: {path}")
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(path))


# Generieke lijnen die uit een andere publicatie komen en bewust geen
# autocaddef hebben (CONTINUOUS = ingebouwde AutoCAD-lijn) -> overslaan.
_LIJN_DEF_EXCLUDE = ("CONTINUOUS", "V-CONTINUOUS-SO")


class LijntypeDefTab(ttk.Frame):
    """Controleert of elk lijntype een AutoCAD-definitie heeft in de kolom
    `autocaddef`. Leest de nieuwe lijntypesmap uit het tabblad 'Locaties'."""

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555", justify="left",
            text="Controleert of elk lijntype een AutoCAD-definitie heeft in de "
                 "kolom autocaddef. De generieke lijnen CONTINUOUS en "
                 "V-CONTINUOUS-SO worden overgeslagen (die hebben bewust geen "
                 "definitie). Gebaseerd op de nieuwe lijntypesmap (tabblad "
                 "'Locaties').").pack(anchor="w")

        btns = ttk.Frame(self)
        btns.pack(anchor="w", pady=(8, 0))
        ttk.Button(btns, text="Controleer AutoCAD-definitie",
                   command=self.on_analyze).pack(side="left")
        ttk.Button(btns, text="Bewaar als HTML", command=self.on_save_html
                   ).pack(side="left", padx=(8, 0))

        logframe = ttk.LabelFrame(self, text="Resultaat", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=18, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _logmsg(self, msg: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clearlog(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    @staticmethod
    def _valid(path: str) -> bool:
        return bool(path) and (os.path.isdir(path) or os.path.isfile(path))

    def _run(self) -> dict | None:
        lijn = self.app.loc["lijn_new"].get().strip()
        if not self._valid(lijn):
            return None
        return ot_compare.check_lijntype_autocaddef(
            lijn, exclude_names=_LIJN_DEF_EXCLUDE)

    def on_analyze(self) -> None:
        self._clearlog()
        res = self._run()
        if res is None:
            messagebox.showwarning(
                "Geen bron", "Vul bij 'Locaties' een geldige map in voor de "
                "nieuwe lijntypes.")
            return
        self._logmsg(f"Lijntypes: {res['total']}  "
                     f"(met definitie: {res['ok']}, "
                     f"zonder: {len(res['missing'])})")
        self._logmsg("(CONTINUOUS en V-CONTINUOUS-SO worden overgeslagen.)")
        self._logmsg()
        missing = res["missing"]
        if not missing:
            self._logmsg("✓ Elk lijntype heeft een AutoCAD-definitie.")
        else:
            self._logmsg(f"⚠ {len(missing)} lijntype(s) zonder definitie:")
            for m in missing:
                self._logmsg(f"   {m['name']}   [{m['file']} r{m['row']}]")

    def on_save_html(self) -> None:
        out_dir = self.app.loc["output_dir"].get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Geen uitvoermap", "Vul bij 'Locaties' een geldige uitvoermap in "
                "om de HTML op te slaan.")
            return
        res = self._run()
        if res is None:
            messagebox.showwarning(
                "Geen bron", "Vul bij 'Locaties' een geldige map in voor de "
                "nieuwe lijntypes.")
            return
        html = ot_html.build_lijntype_autocaddef_html(
            res, title="AutoCAD-definitie",
            version_new=self.app.version_new_var.get().strip())
        path = os.path.join(out_dir, "lijntype-autocaddef.html")
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._logmsg(f"HTML opgeslagen: {path}")
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(path))


# ---------------------------------------------------------------------------
# Tabblad 'Controles': draait ALLE kwaliteitscontroles in één keer en schrijft
# één gecombineerd rapport (controles.html), ingedeeld per tabel in de volgorde
# van docs/managementmanual/2.md. Vervangt de losse controle-tabbladen.
# ---------------------------------------------------------------------------
class ControlesTab(ttk.Frame):
    """Eén knop die alle kwaliteitscontroles draait op de mappen uit 'Locaties'
    en het resultaat in één HTML zet (controles.html), per tabel in de volgorde
    van de managementhandleiding. Elke findings-tabel heeft een sorteerbare
    kolom 'hoofdgroep'. Hergebruikt de _run()-logica van de controle-tabs."""

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555", justify="left",
            text="Draait in één keer alle kwaliteitscontroles (objecten, "
                 "symbolen, arceringen, lijntypes) op de mappen uit het tabblad "
                 "'Locaties' en schrijft het resultaat in één HTML-rapport "
                 "(kwaliteitscontroles-<versie>.html) direct in de changelog-map "
                 "(docs/changelog), ingedeeld per tabel in de volgorde van de "
                 "managementhandleiding. Elke findings-tabel heeft een "
                 "sorteerbare kolom 'hoofdgroep' — klik op een kolomkop om te "
                 "sorteren.").pack(anchor="w")

        btns = ttk.Frame(self)
        btns.pack(anchor="w", pady=(8, 0))
        ttk.Button(btns, text="Draai alle controles → HTML",
                   command=self.on_generate).pack(side="left")

        logframe = ttk.LabelFrame(self, text="Resultaat", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=18, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    def _logmsg(self, msg: str = "") -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _clearlog(self) -> None:
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

    def _gather(self) -> dict:
        """Verzamel de ruwe resultaten van alle controles via hun _run()."""
        app = self.app
        id_sections, _ = app.id_tab._run()
        opt_sections, _ = app.optiefase_tab._run()

        def by_label(lst) -> dict:
            return {s["label"].lower(): s for s in (lst or [])}

        def valid_src(p: str) -> bool:
            return bool(p) and (os.path.isdir(p) or os.path.isfile(p))

        def name_uri(nk, ok, name_col, uri_col, hcol, exc):
            ns = app.loc[nk].get().strip()
            os_ = app.loc[ok].get().strip()
            if not valid_src(ns) and not valid_src(os_):
                return None
            return ot_compare.analyze_name_uri(ns, os_, name_col, uri_col,
                                               hoofd_col=hcol, exclude=exc)

        return {
            "tree": app.objecttree_tab._run(),
            "fasevis": app.fasevis_tab._run(),
            "elemlink": app.elemlink_tab._run(),
            "lijnusage": app.lijnusage_tab._run(),
            "arcverkl": app.arceringverklaring_tab._run(),
            "arclen": ot_compare.check_arcering_name_length(
                app.loc["arc_new"].get().strip()),
            "lijndef": app.lijntypedef_tab._run(),
            "dwg": ot_compare.check_dwg_symbols(
                app.loc["sym_new"].get().strip(),
                app.loc["dwg_new"].get().strip()),
            "id": {s["key"]: s for s in id_sections},
            "optie": {s["label"].lower(): s for s in opt_sections},
            "nameuri": {key: name_uri(nk, ok, name_col, uri_col, hcol, exc)
                        for (key, nk, ok, name_col, uri_col, hcol, exc)
                        in _NAME_URI_PROFILES},
            "searchcov": by_label(app.searchterm_tab._run()),
            "searchmin": by_label(app.searchtermmin_tab._run()),
            "dup": by_label(app.dupnames_tab._run()),
            "special": by_label(app.specialchars_tab._run()),
        }

    def on_generate(self) -> None:
        self._clearlog()
        # Het rapport wordt direct in de changelog-map (docs/changelog) geplaatst,
        # zodat het meelift met de publicatie; die map staat bij 'Locaties' als
        # 'Map om te doorzoeken (docs/changelog)' (index_root).
        out_dir = self.app.loc["index_root"].get().strip()
        if not out_dir or not os.path.isdir(out_dir):
            messagebox.showwarning(
                "Geen changelog-map", "Vul bij 'Locaties' een geldige map "
                "'docs/changelog' (Overzicht) in om het rapport op te slaan.")
            return
        self._logmsg("Controles draaien…")
        version = self.app.version_new_var.get().strip()
        data = self._gather()
        html = ot_html.build_all_checks_html(data, version_new=version)
        # Bestandsnaam met versienummer in koppelteken-vorm (5.2 -> 5-2);
        # zonder versie een nette terugval.
        vdash = version.replace(".", "-")
        fname = f"kwaliteitscontroles-{vdash}.html" if vdash else "kwaliteitscontroles.html"
        path = os.path.join(out_dir, fname)
        with open(path, "w", encoding="utf-8") as f:
            f.write(html)
        self._logmsg(f"Rapport opgeslagen: {path}")
        self.app.save_config()
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(path))


# ---------------------------------------------------------------------------
# Tabblad 'Locaties': alle mappen/bestanden die de tabbladen delen, één keer
# ---------------------------------------------------------------------------
# Velden in het Locaties-tabblad, gegroepeerd. Elke regel:
#   (sleutel in app.loc, label, soort) waarbij soort = "dir" (map),
#   "csv" (bestaand CSV-bestand) of "html" (op te slaan HTML-bestand).
_LOC_GROUPS = [
    ("Objectentabellen", [
        ("obj_new", "Map nieuwe versie:", "dir"),
        ("obj_old", "Map vorige versie:", "dir"),
    ]),
    ("Symbolentabellen", [
        ("sym_new", "Map nieuwe versie:", "dir"),
        ("sym_old", "CSV vorige versie (één bestand):", "csv"),
    ]),
    ("Symbolen .dwg-bestanden", [
        ("dwg_new", "Map nieuwe .dwg's:", "dir"),
        ("dwg_old", "Map oude .dwg's:", "dir"),
    ]),
    ("Lijntypes", [
        ("lijn_new", "Map nieuwe versie:", "dir"),
        ("lijn_old", "CSV vorige versie (één bestand):", "csv"),
    ]),
    ("Arceringen", [
        ("arc_new", "Map nieuwe versie:", "dir"),
        ("arc_old", "CSV vorige versie (één bestand):", "csv"),
    ]),
    ("Overzicht (kaart)", [
        ("index_root", "Map om te doorzoeken (docs/changelog):", "dir"),
        ("base_url", "Basis-URL (online publicatie):", "text"),
        ("index_output", "Uitvoerbestand (HTML):", "html"),
    ]),
    ("Uitvoer", [
        ("output_dir", "Uitvoermap voor de changelog-HTML's:", "dir"),
    ]),
]


class LocationsTab(ttk.Frame):
    """Eerste tabblad: alle gedeelde mappen/bestanden één keer invullen. De
    waarden staan in app.loc (StringVars) zodat de andere tabbladen ze lezen."""

    def __init__(self, master, app: "App"):
        super().__init__(master, padding=10)
        self.app = app
        self._build()

    def _build(self) -> None:
        ttk.Label(
            self, foreground="#555",
            text="Vul de mappen en bestanden hier één keer in; de tabbladen "
                 "hierboven gebruiken ze allemaal. Kies daarna per tabblad de "
                 "hoofdgroepen en klik 'Genereer'.").pack(anchor="w", pady=(0, 8))

        canvas = tk.Canvas(self, highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical", command=canvas.yview)
        inner = ttk.Frame(canvas)
        inner.bind("<Configure>",
                   lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        win = canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.bind("<Configure>",
                    lambda e: canvas.itemconfigure(win, width=e.width))
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        canvas.bind("<Enter>", lambda e: canvas.bind_all(
            "<MouseWheel>", lambda ev: canvas.yview_scroll(
                int(-ev.delta / 120), "units")))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        for title, fields in _LOC_GROUPS:
            frame = ttk.LabelFrame(inner, text=title, padding=8)
            frame.pack(fill="x", pady=(0, 8))
            frame.columnconfigure(1, weight=1)
            for row, (key, label, kind) in enumerate(fields):
                ttk.Label(frame, text=label).grid(row=row, column=0, sticky="w")
                ttk.Entry(frame, textvariable=self.app.loc[key], width=52
                          ).grid(row=row, column=1, sticky="we", padx=4, pady=2)
                if kind != "text":
                    ttk.Button(
                        frame, text="Bladeren...",
                        command=lambda k=key, t=kind: self._browse(k, t)
                    ).grid(row=row, column=2, padx=4)

    def _browse(self, key: str, kind: str) -> None:
        var = self.app.loc[key]
        cur = var.get().strip()
        if kind == "dir":
            path = filedialog.askdirectory(initialdir=cur or os.getcwd())
        elif kind == "csv":
            path = filedialog.askopenfilename(
                initialdir=os.path.dirname(cur) if cur else os.getcwd(),
                filetypes=[("CSV-bestand", "*.csv"), ("Alle bestanden", "*.*")])
        else:  # html: op te slaan bestand
            path = filedialog.asksaveasfilename(
                initialdir=os.path.dirname(cur) if cur else os.getcwd(),
                initialfile=os.path.basename(cur) or "overzicht.html",
                defaultextension=".html",
                filetypes=[("HTML-bestand", "*.html"), ("Alle bestanden", "*.*")])
        if path:
            var.set(path)


# ---------------------------------------------------------------------------
# Hoofdvenster
# ---------------------------------------------------------------------------
class App(ttk.Frame):
    def __init__(self, master: tk.Tk):
        super().__init__(master, padding=10)
        self.master = master
        self.pack(fill="both", expand=True)

        self.cfg = ot_config.load()

        # Gedeeld: versienamen + 'openen na genereren'
        shared = ttk.LabelFrame(self, text="Versies (voor alle vergelijkingen)",
                                padding=8)
        shared.pack(fill="x")
        ttk.Label(shared, text="Naam nieuwe versie:").pack(side="left")
        self.version_new_var = tk.StringVar(value=self.cfg["version_new"])
        ttk.Entry(shared, textvariable=self.version_new_var, width=12
                  ).pack(side="left", padx=(4, 18))
        ttk.Label(shared, text="Naam vorige versie:").pack(side="left")
        self.version_old_var = tk.StringVar(value=self.cfg["version_old"])
        ttk.Entry(shared, textvariable=self.version_old_var, width=12
                  ).pack(side="left", padx=4)
        self.open_after_var = tk.BooleanVar(value=bool(self.cfg["open_after"]))
        ttk.Checkbutton(shared, text="eerste HTML openen na genereren",
                        variable=self.open_after_var).pack(side="left", padx=(24, 0))

        # Gedeelde locaties (alle mappen/bestanden): één StringVar per sleutel,
        # gevuld uit config. De tabbladen lezen deze via app.loc.
        loc_cfg = self.cfg["locations"]
        self.loc: dict[str, tk.StringVar] = {
            key: tk.StringVar(value=loc_cfg.get(key, ""))
            for key in ot_config._locations()
        }

        # Tabbladen
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, pady=(8, 0))

        # Eerste tabblad: de gedeelde locaties.
        self.locations_tab = LocationsTab(nb, self)
        nb.add(self.locations_tab, text="Locaties")

        # Tabblad 'Controles': draait alle kwaliteitscontroles in één keer en
        # schrijft één gecombineerd rapport (controles.html), per tabel in de
        # volgorde van de managementhandleiding.
        self.controles_tab = ControlesTab(nb, self)
        nb.add(self.controles_tab, text="Controles")

        # Per tabelsoort een vergelijk-tabblad; die lezen de mappen uit app.loc.
        self.tabs: dict[str, TableTab] = {}
        for prof in PROFILES:
            tab = TableTab(nb, self, prof)
            nb.add(tab, text=prof["label"])
            tab.load_cfg(self.cfg["codes"].get(prof["key"], []))
            self.tabs[prof["key"]] = tab

        # Laatste tabblad: het publicatie-overzicht ('kaart') met knoppen naar de
        # gepubliceerde HTML's. Geen vergelijking, dus een eigen tabblad-klasse.
        self.index_tab = IndexTab(nb, self)
        nb.add(self.index_tab, text="Overzicht")

        # De losse controle-tabbladen worden niet meer als tab getoond; de
        # instanties blijven bestaan zodat ControlesTab hun _run()-logica kan
        # hergebruiken voor het gecombineerde rapport.
        self.id_tab = IdTab(nb, self)
        self.optiefase_tab = OptieFaseCheckTab(nb, self)
        self.objecttree_tab = ObjectTreeTab(nb, self)
        self.lijnusage_tab = LijntypeUsageTab(nb, self)
        self.searchterm_tab = SearchtermTab(nb, self)
        self.searchtermmin_tab = SearchtermMinTab(nb, self)
        self.fasevis_tab = FaseVisualisatieTab(nb, self)
        self.dupnames_tab = DuplicateNamesTab(nb, self)
        self.elemlink_tab = ElementLinkTab(nb, self)
        self.specialchars_tab = SpecialCharsTab(nb, self)
        self.arceringverklaring_tab = ArceringVerklaringTab(nb, self)
        self.lijntypedef_tab = LijntypeDefTab(nb, self)

        master.protocol("WM_DELETE_WINDOW", self._on_close)

    def _collect_config(self) -> dict:
        return {
            "version_new": self.version_new_var.get().strip(),
            "version_old": self.version_old_var.get().strip(),
            "open_after": self.open_after_var.get(),
            "locations": {key: var.get().strip()
                          for key, var in self.loc.items()},
            "codes": {key: tab.collect_cfg()["codes"]
                      for key, tab in self.tabs.items()},
        }

    def save_config(self) -> None:
        ot_config.save(self._collect_config())

    def _on_close(self) -> None:
        self.save_config()
        self.master.destroy()


def run() -> None:
    root = tk.Tk()
    root.title("NLCS Tabellen changelog")
    root.geometry("860x760")
    root.minsize(720, 660)
    App(root)
    root.mainloop()


if __name__ == "__main__":
    run()
