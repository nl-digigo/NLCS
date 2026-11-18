# NLCS Objectgericht — Verhardingen (VH)

Hulpscripts om uit de **VH-classificatie-werk-Excel** een reviewpagina met
objectenbomen te genereren. De scripts bewerken stapsgewijs een *werkversie* van
de classificatie-Excel en bouwen daar ten slotte een HTML-pagina van.

## Draaien

Draai alles **vanuit de repo-root** (niet vanuit deze map). De scripts gebruiken
paden relatief aan de root, bijv.:

```
python beheer/objectgericht/VH/_vh_werkversie.py
```

**Vereisten:** Python 3.12 + `openpyxl`. `_mkbomen.py` hergebruikt daarnaast
`ot_html` uit `beheer/objectentabellen_changelog/` (wordt via `sys.path` ingeladen).
Sluit de werk-Excel in Excel voordat je een script draait (anders file-lock).

## Bestanden

| Bron / doel | Pad |
|---|---|
| Origineel (ongewijzigd) | `ontwikkeling/classificatie/fase 1 Inhoud classificatie VH/Classificatie-NLCS-VH-inhoud.xlsx` |
| Werkversie (wordt bewerkt) | `…/Classificatie-NLCS-VH-inhoud-werkversie.xlsx` |
| Uitvoerpagina | `docs/changelog/VH-objectgericht/reviewversie-20261008/index.html` |

Tabblad: `objecten-concept-5.1-VH`.

## Pijplijn (volgorde)

1. **`_vh_werkversie.py`** — maakt de **werkversie** uit het origineel: strip de
   bibliotheek-prefix (`SVH-`) en fase-prefix (`B-/V-/N-/O-`) uit kolom A, haal
   `-SO/-D` eraf bij fysieke objecten, en splits de schone naam op `_` naar de
   segment-kolommen (object/subobject01..05). Origineel blijft ongemoeid.
2. **`_vh_place52.py`** — voeg de **NLCS 5.2**-objecten/symbolen toe en plaats ze
   onder hun hoofdobject via de `sobject`-kolom (zoekfilter) in
   `objecten-5-2-VH.csv`. Verwijdert eerder toegevoegde 5.2-rijen en zet ze
   opnieuw; nieuwe rijen krijgen een oranje markering (`uit 5.2`).
   *(`_vh_add52.py` is de eenvoudiger voorganger — voegt 5.2-namen toe zónder de
   sobject-plaatsing; `_vh_place52.py` vervangt die aanpak.)*
3. **`_vh_resplit.py`** — herstel de segment-kolommen voor rijen waar een
   segment-cel een (niet-werkende) formule bevat of nog een `_`-gecombineerde
   waarde heeft: splitst kolom A opnieuw.
4. **`_vh_sbs.py`** — hernoem **SBS**-rijen naar
   `OPENVERHARDING_STRAATBAKSTEEN_…` (5.2: `SVH-SBS` → straatbaksteen) en splits
   de segmenten opnieuw.
5. **`_vh_fix.py`** — hernoem **BSS**-rijen naar
   `OPENVERHARDING_BETONSTRAATSTEEN_…`, strip resterende `-SO/-D` uit de
   omschrijving van meegenomen objecten (kolom B = Fysiek/Gebied/Activiteit), en
   split de segmenten opnieuw.
6. **`_mkbomen.py`** — bouwt de **reviewpagina**: per hoofdobject een objectenboom
   met materialen/gebieden/activiteiten/eigenschappen (afgeleid uit de
   underscore-markerkolommen), groene/blauwe stipjes voor voorkomen in NLCS 5.0 /
   5.2, een materialen- en gebieden-index en een "niet meegenomen"-lijst. Schrijft
   de HTML naar de uitvoerpagina hierboven.

De stappen 2–5 zijn **idempotent** (herhaald draaien verandert niets extra). Pas
na een nieuwe `_vh_werkversie.py` begin je weer bij stap 1.
