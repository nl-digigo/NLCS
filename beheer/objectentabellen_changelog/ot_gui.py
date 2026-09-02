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
        # oude versie = één grote CSV; scope per bibliotheek zodat 'vervallen'
        # beperkt blijft tot dezelfde hoofdgroep
        "old_is_file": True,
        "scope_col": "sbibliotheek",
        # sbibliotheek = 'S' + hoofdgroepcode: 'S' eraf bij het splitsen van CO
        "scope_strip_s": True,
    },
    {
        "key": "lijn",
        "label": "Lijntypes",
        "match_key": "lijntypeURI",
        "locations": {"new": "lijn_new", "old": "lijn_old"},
        # toon de informatieve kolommen (in CSV-volgorde); id + finalCleanName weg
        "visible": lambda headers: ot_html.show_names_indices(
            headers, ["lijntypeURI", "hoofdgroep", "omschrijving", "fase",
                      "optie", "autocaddef"]),
        # vrij zoekveld voor URI, omschrijving en autocaddef; rest = keuzelijst
        "text_search": lambda h: h in ("omschrijving", "autocaddef")
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
        # oude versie = één grote CSV met alle arceringen; scope op abibliotheek
        # zodat 'vervallen' beperkt blijft tot de vergeleken groep
        "old_is_file": True,
        "scope_col": "abibliotheek",
        # abibliotheek bevat de groepscode al letterlijk (ACO, ...); NIET strippen.
        # CO werkt als één hoofdgroep met groep 'ACO', dus geen split.
        "scope_strip_s": False,
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
        needs_objecten = self.profile.get("needs_objecten", False)
        objecten_col = self.profile.get("objecten_col", "")
        zf_name_col = self.profile.get("zoekfilter_name_col", "")
        zf_scope = self.profile.get("zoekfilter_scope", "per_code")
        front_svg = self.profile.get("front_svg", False)
        objecten_dir = self._loc("objecten")
        symbols_dir = self._loc("dwg_new")
        symbols_old_dir = self._loc("dwg_old")
        new_dir = self._loc("new")
        selected = [(code, self.pairs[code][0], self.pairs[code][1])
                    for code in chosen if code in self.pairs]

        self.gen_btn.config(state="disabled")
        self.log.configure(state="normal")
        self.log.delete("1.0", "end")
        self.log.configure(state="disabled")

        def worker():
            try:
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
                for code, new_path, old_path in selected:
                    orig_base = os.path.splitext(os.path.basename(new_path))[0]
                    full_result = ot_compare.compare(
                        new_path, old_path, key=match_key, scope_col=scope_col,
                        blank_spec=blank_spec)

                    # Verzamelbestand (CO) uiteen laten vallen in aparte
                    # hoofdgroepen; gewone bestanden blijven één geheel.
                    groups = ot_compare.split_result_by_bib(
                        full_result, scope_col, strip_s=scope_strip_s)
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

                        full_html = ot_html.build_full_html(
                            result, title=base, version_new=version_new,
                            visible_indices=vis, text_columns=text_cols,
                            front_columns=front_cols)
                        changelog_html = ot_html.build_changelog_html(
                            result, title=f"Changelog {base}",
                            version_new=version_new, version_old=version_old,
                            visible_indices=vis, extra_columns=extra_cols,
                            orphans=orphans_this)

                        full_path = os.path.join(out_dir, f"{base}.html")
                        changelog_path = os.path.join(
                            out_dir, f"changelog-{base}.html")
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(full_html)
                        with open(changelog_path, "w", encoding="utf-8") as f:
                            f.write(changelog_html)

                        if first is None:
                            first = full_path
                        wees_txt = (f", {len(orphans_this)} wees-.dwg"
                                    if orphans_this else "")
                        self._queue.put(("log",
                            f"[{gcode or code}] {base}: {s['new']} nieuw, "
                            f"{s['changed']} gewijzigd, {s['deleted']} vervallen"
                            f"{hash_summary}{wees_txt} -> {base}.html + "
                            f"changelog-{base}.html"))
                        made += 1
                        files += 2

                # Wees-.dwg's: bestanden zonder een regel in de verwerkte
                # symbolentabellen. Alleen .dwg's van de bibliotheken die in deze
                # run zijn verwerkt tellen mee (bijv. SAM, SAL); .dwg's van andere
                # groepen worden overgeslagen (anders wordt bijv. heel SAL als wees
                # gemeld terwijl die groep niet is vergeleken).
                if needs_files and dwg_map:
                    orphans = []
                    skipped_bibs: set = set()
                    for stem in sorted(dwg_map):
                        # Bib per .dwg via segment-match (prefix-proof: V-SFC-...).
                        bib = _bib_of_stem(stem, processed_bibs)
                        if processed_bibs and not bib:
                            first_seg = (stem.split("-", 1)[0].upper()
                                         if "-" in stem else "?")
                            skipped_bibs.add(first_seg or "?")
                            continue  # andere groep, niet in deze run verwerkt
                        if stem not in all_symbols:
                            orphans.append((stem, dwg_map[stem]))
                    orphan_html = ot_html.build_orphans_html(
                        orphans, title="dwg zonder regel in de symbolentabel",
                        symbols_dir=symbols_dir, version_new=version_new)
                    orphan_path = os.path.join(out_dir, "dwg-zonder-tabelregel.html")
                    with open(orphan_path, "w", encoding="utf-8") as f:
                        f.write(orphan_html)
                    files += 1
                    bibs_txt = ", ".join(sorted(processed_bibs)) or "?"
                    msg = (f"{len(orphans)} .dwg-bestand(en) zonder regel in de "
                           f"tabel (bibliotheken: {bibs_txt}) "
                           f"-> dwg-zonder-tabelregel.html")
                    if skipped_bibs:
                        msg += (f" [{len(skipped_bibs)} andere groep(en) "
                                f"overgeslagen: {', '.join(sorted(skipped_bibs))}]")
                    self._queue.put(("log", msg))

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

        data = ot_compare.scan_publication(root, version)
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

        version = self.app.version_new_var.get().strip()
        base_url = self.app.loc["base_url"].get().strip()
        html_txt = ot_html.build_index_html(
            data["groups"], data["general"],
            title=f"NLCS publicatie-overzicht {version}".strip(),
            version=version, base_url=base_url)
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
        self.app.save_config()
        if self.app.open_after_var.get():
            webbrowser.open(os.path.abspath(output))


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
