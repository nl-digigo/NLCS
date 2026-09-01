"""
rn_config.py - Instellingen onthouden tussen sessies.

Slaat de keuzes op in config.json naast het programma (of naast de .exe als
het gebundeld is). Het GitHub-token wordt bewust NOOIT opgeslagen.
"""

import json
import os
import sys


DEFAULTS = {
    "owner": "nl-digigo",
    "repo": "NLCS",
    "oauth_client_id": "",  # Client ID van de GitHub OAuth App (niet geheim)
    "states": ["OPEN", "CLOSED"],
    "tag": "[[release note]]",
    "require_tag": True,
    "milestones": [],       # geselecteerde milestones (filter bij ophalen)
    "show_labels": [],      # labels om te tonen in de tabel (leeg = alle)
    "title": "NLCS Release Notes",
    "output": "",           # laatst gebruikte output-pad
    "open_after": True,     # HTML openen na genereren
}


def base_dir() -> str:
    """Map waarin config.json staat: naast de .exe of naast dit script."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def config_file() -> str:
    return os.path.join(base_dir(), "config.json")


def load() -> dict:
    """Laad de opgeslagen instellingen, aangevuld met de defaults."""
    cfg = dict(DEFAULTS)
    try:
        with open(config_file(), encoding="utf-8") as f:
            saved = json.load(f)
        if isinstance(saved, dict):
            cfg.update(saved)
    except (FileNotFoundError, ValueError, OSError):
        pass
    cfg.pop("token", None)  # nooit een token uit config gebruiken
    return cfg


def save(cfg: dict) -> None:
    """Sla de instellingen op (zonder token)."""
    data = {k: v for k, v in cfg.items() if k != "token"}
    try:
        with open(config_file(), "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except OSError:
        pass  # opslaan is 'nice to have'; niet fataal
