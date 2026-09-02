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
        # toon alleen deze kolommen (in CSV-volgorde)
        "visible": lambda headers: ot_html.show_names_indices(
            headers, ["symboolURI", "sbibliotheek", "fase", "id",
                      "symbool", "optie"]),
        # vrij zoekveld voor URI's, symbool en id; rest (sbibliotheek, fase,
        # optie) = keuzelijst
        "text_search": lambda h: "uri" in h.lower() or h in ("symbool", "id"),
        # symbolen: extra map met de nieuwe .dwg's + svg/.dwg-kolommen in de changelog
        "needs_symbol_files": True,
        "symbol_name_col": "symbool",
        # zoekfilter-kolom: welke sobject-term uit de objectentabel het symbool vindt
        "needs_objecten": True,
        "objecten_col": "sobject",
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
    },
    {
        "key": "arc",
        "label": "Arceringen",
        "match_key": "arceringURI",
        # toon de informatieve kolommen (in CSV-volgorde); searchterm,
        # abibliotheekURI en finalCleanName weglaten
        "visible": lambda headers: ot_html.show_names_indices(
            headers, ["arceringURI", "abibliotheek", "fase", "id", "arcering",
                      "optie", "schaal", "vrkl_kort", "vrkl_lang", "fileURL"]),
        # vrij zoekveld voor URI, arcering, id, de verklaringen en de fileURL;
        # rest (abibliotheek, fase, optie, schaal) = keuzelijst
        "text_search": lambda h: h in ("arcering", "vrkl_kort", "vrkl_lang",
                                       "id", "fileURL") or "uri" in h.lower(),
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
        loc = ttk.LabelFrame(self, text="Locaties", padding=8)
        loc.pack(fill="x")

        ttk.Label(loc, text="Map nieuwe versie:").grid(row=0, column=0, sticky="w")
        self.new_dir_var = tk.StringVar()
        ttk.Entry(loc, textvariable=self.new_dir_var, width=52
                  ).grid(row=0, column=1, sticky="we", padx=4, pady=2)
        ttk.Button(loc, text="Bladeren...",
                   command=lambda: self._browse_dir(self.new_dir_var)
                   ).grid(row=0, column=2, padx=4)

        self.old_is_file = bool(self.profile.get("old_is_file"))
        old_label = ("CSV vorige versie (één groot bestand):"
                     if self.old_is_file else "Map vorige versie:")
        ttk.Label(loc, text=old_label).grid(row=1, column=0, sticky="w")
        self.old_dir_var = tk.StringVar()
        ttk.Entry(loc, textvariable=self.old_dir_var, width=52
                  ).grid(row=1, column=1, sticky="we", padx=4, pady=2)
        old_browse = ((lambda: self._browse_file(self.old_dir_var))
                      if self.old_is_file
                      else (lambda: self._browse_dir(self.old_dir_var)))
        ttk.Button(loc, text="Bladeren...", command=old_browse
                   ).grid(row=1, column=2, padx=4)

        # Alleen symbolen: aparte mappen met de nieuwe en de oude .dwg-symbolen
        # (elk recursief doorzocht). De nieuwe map voedt '.dwg aanwezig' + de
        # wees-controle; nieuw + oud samen voeden de hash-vergelijking.
        self.symbols_dir_var = tk.StringVar()
        self.symbols_old_dir_var = tk.StringVar()
        if self.profile.get("needs_symbol_files"):
            ttk.Label(loc, text="Map nieuwe symbolen (.dwg):"
                      ).grid(row=2, column=0, sticky="w")
            ttk.Entry(loc, textvariable=self.symbols_dir_var, width=52
                      ).grid(row=2, column=1, sticky="we", padx=4, pady=2)
            ttk.Button(loc, text="Bladeren...",
                       command=lambda: self._browse_dir(self.symbols_dir_var)
                       ).grid(row=2, column=2, padx=4)

            ttk.Label(loc, text="Map oude symbolen (.dwg, voor hash):"
                      ).grid(row=3, column=0, sticky="w")
            ttk.Entry(loc, textvariable=self.symbols_old_dir_var, width=52
                      ).grid(row=3, column=1, sticky="we", padx=4, pady=2)
            ttk.Button(loc, text="Bladeren...",
                       command=lambda: self._browse_dir(self.symbols_old_dir_var)
                       ).grid(row=3, column=2, padx=4)

        # Alleen symbolen: map met de nieuwe objectentabellen, voor de zoekfilter-
        # kolom (welke sobject-term uit de objectentabel het symbool vindt).
        self.objecten_dir_var = tk.StringVar()
        if self.profile.get("needs_objecten"):
            ttk.Label(loc, text="Map objectentabellen (nieuw, voor zoekfilter):"
                      ).grid(row=4, column=0, sticky="w")
            ttk.Entry(loc, textvariable=self.objecten_dir_var, width=52
                      ).grid(row=4, column=1, sticky="we", padx=4, pady=2)
            ttk.Button(loc, text="Bladeren...",
                       command=lambda: self._browse_dir(self.objecten_dir_var)
                       ).grid(row=4, column=2, padx=4)
        loc.columnconfigure(1, weight=1)

        groups = ttk.LabelFrame(self, text="Hoofdgroepen (kies wat je vergelijkt)",
                                padding=8)
        groups.pack(fill="both", expand=True, pady=8)
        top = ttk.Frame(groups)
        top.pack(fill="x")
        ttk.Button(top, text="Zoek hoofdgroepen", command=self.on_scan
                   ).pack(side="left")
        self.scan_status_var = tk.StringVar(
            value="Kies beide mappen en klik 'Zoek hoofdgroepen'.")
        ttk.Label(top, textvariable=self.scan_status_var, foreground="#555"
                  ).pack(side="left", padx=10)
        self.code_list = ScrollableChecklist(groups, "Hoofdgroep-codes")
        self.code_list.pack(fill="both", expand=True, pady=(8, 0))

        out = ttk.LabelFrame(self, text="Uitvoer", padding=8)
        out.pack(fill="x")
        ttk.Label(out, text="Uitvoermap:").grid(row=0, column=0, sticky="w")
        self.output_dir_var = tk.StringVar()
        ttk.Entry(out, textvariable=self.output_dir_var, width=52
                  ).grid(row=0, column=1, sticky="we", padx=4, pady=2)
        ttk.Button(out, text="Bladeren...",
                   command=lambda: self._browse_dir(self.output_dir_var)
                   ).grid(row=0, column=2, padx=4)
        self.gen_btn = ttk.Button(out, text="Genereer HTML's",
                                  command=self.on_generate)
        self.gen_btn.grid(row=1, column=2, sticky="e", padx=4, pady=(4, 0))
        out.columnconfigure(1, weight=1)

        logframe = ttk.LabelFrame(self, text="Voortgang", padding=8)
        logframe.pack(fill="both", expand=True, pady=(8, 0))
        self.log = tk.Text(logframe, height=7, wrap="word", state="disabled",
                           font=("Consolas", 9), background="#fbfbfb")
        scroll = ttk.Scrollbar(logframe, orient="vertical", command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")

    # -- config ------------------------------------------------------------
    def load_cfg(self, tabcfg: dict) -> None:
        self.new_dir_var.set(tabcfg.get("new_dir", ""))
        self.old_dir_var.set(tabcfg.get("old_dir", ""))
        self.output_dir_var.set(tabcfg.get("output_dir", ""))
        self.symbols_dir_var.set(tabcfg.get("symbols_dir", ""))
        self.symbols_old_dir_var.set(tabcfg.get("symbols_old_dir", ""))
        self.objecten_dir_var.set(tabcfg.get("objecten_dir", ""))
        self._saved_codes = list(tabcfg.get("codes", []))
        if os.path.isdir(self.new_dir_var.get()) and self._old_ok():
            self.on_scan(silent=True)

    def collect_cfg(self) -> dict:
        return {
            "new_dir": self.new_dir_var.get().strip(),
            "old_dir": self.old_dir_var.get().strip(),
            "codes": self.code_list.checked(),
            "output_dir": self.output_dir_var.get().strip(),
            "symbols_dir": self.symbols_dir_var.get().strip(),
            "symbols_old_dir": self.symbols_old_dir_var.get().strip(),
            "objecten_dir": self.objecten_dir_var.get().strip(),
        }

    # -- helpers -----------------------------------------------------------
    def _browse_dir(self, var: tk.StringVar) -> None:
        path = filedialog.askdirectory(initialdir=var.get() or os.getcwd())
        if path:
            var.set(path)

    def _browse_file(self, var: tk.StringVar) -> None:
        current = var.get().strip()
        initial = os.path.dirname(current) if current else os.getcwd()
        path = filedialog.askopenfilename(
            initialdir=initial,
            filetypes=[("CSV-bestanden", "*.csv"), ("Alle bestanden", "*.*")])
        if path:
            var.set(path)

    def _logmsg(self, msg: str) -> None:
        self.log.configure(state="normal")
        self.log.insert("end", msg + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _old_ok(self) -> bool:
        old = self.old_dir_var.get().strip()
        return os.path.isfile(old) if self.old_is_file else os.path.isdir(old)

    # -- hoofdgroepen zoeken ----------------------------------------------
    def on_scan(self, silent: bool = False) -> None:
        new_dir = self.new_dir_var.get().strip()
        old = self.old_dir_var.get().strip()
        if not (os.path.isdir(new_dir) and self._old_ok()):
            if not silent:
                msg = ("Kies eerst een geldige map voor de nieuwe versie én een "
                       "CSV-bestand voor de vorige versie." if self.old_is_file
                       else "Kies eerst een geldige map voor de nieuwe én de "
                       "vorige versie.")
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
        out_dir = self.output_dir_var.get().strip()
        if not self.pairs:
            self.on_scan()
            if not self.pairs:
                return
        if not out_dir:
            messagebox.showwarning("Geen uitvoermap", "Kies een uitvoermap.")
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
        needs_objecten = self.profile.get("needs_objecten", False)
        objecten_col = self.profile.get("objecten_col", "")
        objecten_dir = self.objecten_dir_var.get().strip()
        symbols_dir = self.symbols_dir_var.get().strip()
        symbols_old_dir = self.symbols_old_dir_var.get().strip()
        new_dir = self.new_dir_var.get().strip()
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

                # Objectentabellen voor de zoekfilter-kolom (sobject-term).
                use_zf = False
                if needs_objecten:
                    if not objecten_dir:
                        self._queue.put(("log",
                            "Geen map objectentabellen gekozen: kolom "
                            "'zoekfilter (sobject)' wordt weggelaten."))
                    elif not os.path.isdir(objecten_dir):
                        self._queue.put(("log",
                            f"Let op: map objectentabellen bestaat niet: "
                            f"{objecten_dir}"))
                    else:
                        use_zf = True
                        self._queue.put(("log",
                            "Zoekfilter: sobject-termen uit de objectentabellen."))

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
                        new_path, old_path, key=match_key, scope_col=scope_col)

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
                        orphans_this = None
                        hash_summary = ""
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

                            zoekfilters = None
                            if use_zf and has_name:
                                # Hoofdgroep(en) uit de sbibliotheek-kolom. Na het
                                # splitsen is dit er één per bestand; termen uit de
                                # bijbehorende objectentabel(len) samenvoegen.
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
                                terms: list = []
                                missing = []
                                for ch in sorted(codes_needed):
                                    ocsv = ot_compare.find_csv_by_code(
                                        objecten_dir, ch)
                                    if ocsv:
                                        terms += ot_compare.column_values(
                                            ocsv, objecten_col)
                                    else:
                                        missing.append(ch)
                                zoekfilters = ot_compare.zoekfilter_map(
                                    names, terms)
                                if missing:
                                    self._queue.put(("log",
                                        f"[{gcode or code}] geen objectentabel "
                                        f"voor: {', '.join(missing)} (zoekfilter "
                                        f"voor die groep leeg)."))

                            extra_cols = _symbol_extra_columns(
                                result, symbol_name_col, dwg_map, hash_status,
                                zoekfilters)

                        full_html = ot_html.build_full_html(
                            result, title=base, version_new=version_new,
                            visible_indices=vis, text_columns=text_cols)
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

        # Tabbladen per tabelsoort
        nb = ttk.Notebook(self)
        nb.pack(fill="both", expand=True, pady=(8, 0))
        self.tabs: dict[str, TableTab] = {}
        for prof in PROFILES:
            tab = TableTab(nb, self, prof)
            nb.add(tab, text=prof["label"])
            tab.load_cfg(self.cfg["tabs"].get(prof["key"], {}))
            self.tabs[prof["key"]] = tab

        master.protocol("WM_DELETE_WINDOW", self._on_close)

    def _collect_config(self) -> dict:
        return {
            "version_new": self.version_new_var.get().strip(),
            "version_old": self.version_old_var.get().strip(),
            "open_after": self.open_after_var.get(),
            "tabs": {key: tab.collect_cfg() for key, tab in self.tabs.items()},
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
