"""
pm_core.py - laadt de logica uit code/nlcs/split/merger/publication_merger.py.

Het originele publication_merger.py wordt NIET aangepast: we laden het als module
(dev: via het pad in de repo; in de .exe: de meegebundelde kopie) en gebruiken de
functies en de PUBLICATIONS-lijst eruit. Zo is er één bron van waarheid.
"""

import importlib.util
import os
import sys


def _merger_path() -> str:
    """Pad naar publication_merger.py — in de exe de meegebundelde kopie
    (sys._MEIPASS), anders relatief t.o.v. de repo-root."""
    if getattr(sys, "frozen", False):
        return os.path.join(sys._MEIPASS, "publication_merger.py")
    here = os.path.dirname(os.path.abspath(__file__))
    # beheer/publicatie_merger -> repo-root (NLCSdev)
    root = os.path.abspath(os.path.join(here, "..", ".."))
    return os.path.join(root, "code", "nlcs", "split", "merger",
                        "publication_merger.py")


def _load():
    path = _merger_path()
    if not os.path.isfile(path):
        raise FileNotFoundError(
            f"publication_merger.py niet gevonden op: {path}")
    spec = importlib.util.spec_from_file_location("publication_merger", path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules["publication_merger"] = mod
    spec.loader.exec_module(mod)   # draait alleen top-level config (merge is guarded)
    return mod


_pm = _load()

PUBLICATIONS = list(_pm.PUBLICATIONS)
DEFAULT_OUTPUT = _pm.OUTPUT_PATH
fetch_publication_graph = _pm.fetch_publication_graph
merge_publications = _pm.merge_publications
save_graph = _pm.save_graph
