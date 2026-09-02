"""
ot_config.py - Instellingen onthouden tussen sessies.

Slaat de keuzes op in config.json naast het programma (of naast de .exe als
het gebundeld is).

De versienamen (nieuw/oud) en 'openen na genereren' zijn gedeeld. Alle mappen en
bestanden worden één keer opgegeven in het blok 'locations'; per tabelsoort ('obj',
'sym', 'lijn', 'arc') worden alleen de aangevinkte hoofdgroep-codes onthouden.
"""

import copy
import json
import os
import sys


TAB_KEYS = ("obj", "sym", "lijn", "arc")


def _locations() -> dict:
    # Alle mappen/bestanden die de tabbladen delen. Eén keer invullen:
    #   obj_new/obj_old       : map objectentabellen nieuw / vorig
    #   sym_new/sym_old       : map symbolentabellen nieuw / vorig-CSV (één bestand)
    #   dwg_new/dwg_old       : map nieuwe / oude symbolen-.dwg's (aanwezig + hash)
    #   lijn_new/lijn_old     : map lijntypes nieuw / vorig-CSV
    #   arc_new/arc_old       : map arceringen nieuw / vorig-CSV
    #   index_root/base_url/index_output : overzicht ('kaart'): doorzochte map,
    #                           online basis-URL, uitvoerbestand
    #   output_dir            : gedeelde uitvoermap voor de changelog-HTML's
    return {
        "obj_new": "", "obj_old": "",
        "sym_new": "", "sym_old": "",
        "dwg_new": "", "dwg_old": "",
        "lijn_new": "", "lijn_old": "",
        "arc_new": "", "arc_old": "",
        "index_root": "", "base_url": "https://nl-digigo.github.io/NLCS/",
        "index_output": "",
        "output_dir": "",
    }


DEFAULTS = {
    "version_new": "",     # naam van de nieuwe versie (bijv. "5.2") - gedeeld
    "version_old": "",     # naam van de vorige versie (bijv. "5.0") - gedeeld
    "open_after": True,    # eerste HTML openen na genereren - gedeeld
    "locations": _locations(),
    "codes": {key: [] for key in TAB_KEYS},
}


def base_dir() -> str:
    """Map waarin config.json staat: naast de .exe of naast dit script."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def config_file() -> str:
    return os.path.join(base_dir(), "config.json")


# Waar de mappen uit het oude per-tabblad-schema in het nieuwe 'locations'-blok
# terechtkomen: (tab-sleutel, oud-veld) -> nieuwe locations-sleutel.
_TAB_TO_LOC = {
    ("obj", "new_dir"): "obj_new", ("obj", "old_dir"): "obj_old",
    ("sym", "new_dir"): "sym_new", ("sym", "old_dir"): "sym_old",
    ("sym", "symbols_dir"): "dwg_new", ("sym", "symbols_old_dir"): "dwg_old",
    ("lijn", "new_dir"): "lijn_new", ("lijn", "old_dir"): "lijn_old",
    ("arc", "new_dir"): "arc_new", ("arc", "old_dir"): "arc_old",
}


def _migrate_old(cfg: dict, saved: dict) -> None:
    """Vul cfg['locations'] en cfg['codes'] uit het oude per-tabblad-schema
    (tabs.*, index) zodat bestaande config.json's blijven werken."""
    tabs = saved.get("tabs") or {}
    for (tabkey, field), lockey in _TAB_TO_LOC.items():
        val = (tabs.get(tabkey) or {}).get(field, "")
        if val and not cfg["locations"].get(lockey):
            cfg["locations"][lockey] = val
    # symbolen-tabblad had ook 'objecten_dir' (voor de zoekfilter); dat is nu
    # gewoon de nieuwe objectentabellen-map.
    obj_from_sym = (tabs.get("sym") or {}).get("objecten_dir", "")
    if obj_from_sym and not cfg["locations"].get("obj_new"):
        cfg["locations"]["obj_new"] = obj_from_sym
    # eerste niet-lege uitvoermap wint als gedeelde uitvoermap
    for tabkey in TAB_KEYS:
        out = (tabs.get(tabkey) or {}).get("output_dir", "")
        if out:
            cfg["locations"]["output_dir"] = out
            break
    # aangevinkte codes per tabblad
    for tabkey in TAB_KEYS:
        codes = (tabs.get(tabkey) or {}).get("codes")
        if isinstance(codes, list):
            cfg["codes"][tabkey] = codes
    # overzicht-tabblad ('index')
    idx = saved.get("index")
    if isinstance(idx, dict):
        if idx.get("root"):
            cfg["locations"]["index_root"] = idx["root"]
        if idx.get("base_url"):
            cfg["locations"]["base_url"] = idx["base_url"]
        if idx.get("output"):
            cfg["locations"]["index_output"] = idx["output"]


def load() -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    try:
        with open(config_file(), encoding="utf-8") as f:
            saved = json.load(f)
    except (FileNotFoundError, ValueError, OSError):
        saved = {}

    if not isinstance(saved, dict):
        return cfg

    for k in ("version_new", "version_old", "open_after"):
        if k in saved:
            cfg[k] = saved[k]

    # Nieuw schema (locations + codes) heeft voorrang; anders migreren we het oude.
    loc = saved.get("locations")
    codes = saved.get("codes")
    if isinstance(loc, dict) or isinstance(codes, dict):
        if isinstance(loc, dict):
            for kk in cfg["locations"]:
                if kk in loc:
                    cfg["locations"][kk] = loc[kk]
        if isinstance(codes, dict):
            for key in TAB_KEYS:
                if isinstance(codes.get(key), list):
                    cfg["codes"][key] = codes[key]
    else:
        _migrate_old(cfg, saved)
    return cfg


def save(cfg: dict) -> None:
    try:
        with open(config_file(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # opslaan is 'nice to have'; niet fataal
