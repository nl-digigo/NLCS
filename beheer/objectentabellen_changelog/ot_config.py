"""
ot_config.py - Instellingen onthouden tussen sessies.

Slaat de keuzes op in config.json naast het programma (of naast de .exe als
het gebundeld is).

De versienamen (nieuw/oud) en 'openen na genereren' zijn gedeeld; de mappen,
de aangevinkte codes en de uitvoermap worden per tabblad ('obj', 'sym',
'lijn', 'arc') onthouden.
"""

import copy
import json
import os
import sys


def _tab() -> dict:
    # symbols_dir/symbols_old_dir/objecten_dir worden alleen door het symbolen-
    # tabblad gebruikt (map met de nieuwe .dwg's; map met de oude .dwg's voor de
    # hash-vergelijking; map met de nieuwe objectentabellen voor de zoekfilter-
    # kolom). Voor objecten blijven ze leeg.
    return {"new_dir": "", "old_dir": "", "codes": [], "output_dir": "",
            "symbols_dir": "", "symbols_old_dir": "", "objecten_dir": ""}


TAB_KEYS = ("obj", "sym", "lijn", "arc")

def _index() -> dict:
    # Instellingen van het overzicht-tabblad ('kaart'): de map die doorzocht
    # wordt (docs/changelog), de online basis-URL en het uitvoerbestand.
    return {"root": "", "base_url": "https://nl-digigo.github.io/NLCS/",
            "output": ""}


def _zf() -> dict:
    # Instellingen van het zoekfilter-tabblad: de map met de objectentabellen
    # (bevat de zoekfilters sobject/aobject), de map met de symbolentabellen en
    # de map met de arceringentabellen (namen om onder de zoekfilters te hangen),
    # de aangevinkte hoofdgroep-codes en de uitvoermap.
    return {"objecten_dir": "", "symbols_dir": "", "arceringen_dir": "",
            "codes": [], "output_dir": ""}


DEFAULTS = {
    "version_new": "",     # naam van de nieuwe versie (bijv. "5.2") - gedeeld
    "version_old": "",     # naam van de vorige versie (bijv. "5.0") - gedeeld
    "open_after": True,    # eerste HTML openen na genereren - gedeeld
    "tabs": {key: _tab() for key in TAB_KEYS},
    "index": _index(),
    "zoekfilter": _zf(),
}


def base_dir() -> str:
    """Map waarin config.json staat: naast de .exe of naast dit script."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def config_file() -> str:
    return os.path.join(base_dir(), "config.json")


def load() -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    try:
        with open(config_file(), encoding="utf-8") as f:
            saved = json.load(f)
    except (FileNotFoundError, ValueError, OSError):
        saved = {}

    if not isinstance(saved, dict):
        return cfg

    # Migratie van het oude platte schema (alleen objectentabellen) -> tabs.obj
    if "tabs" not in saved and any(
            k in saved for k in ("new_dir", "old_dir", "codes", "output_dir")):
        saved["tabs"] = {"obj": {
            "new_dir": saved.get("new_dir", ""),
            "old_dir": saved.get("old_dir", ""),
            "codes": saved.get("codes", []),
            "output_dir": saved.get("output_dir", ""),
        }}

    for k in ("version_new", "version_old", "open_after"):
        if k in saved:
            cfg[k] = saved[k]

    tabs = saved.get("tabs") or {}
    for key in TAB_KEYS:
        t = tabs.get(key)
        if isinstance(t, dict):
            for kk in cfg["tabs"][key]:
                if kk in t:
                    cfg["tabs"][key][kk] = t[kk]

    idx = saved.get("index")
    if isinstance(idx, dict):
        for kk in cfg["index"]:
            if kk in idx:
                cfg["index"][kk] = idx[kk]

    zf = saved.get("zoekfilter")
    if isinstance(zf, dict):
        for kk in cfg["zoekfilter"]:
            if kk in zf:
                cfg["zoekfilter"][kk] = zf[kk]
    return cfg


def save(cfg: dict) -> None:
    try:
        with open(config_file(), "w", encoding="utf-8") as f:
            json.dump(cfg, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # opslaan is 'nice to have'; niet fataal
