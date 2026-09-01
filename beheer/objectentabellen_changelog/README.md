# NLCS Objectentabellen changelog

Genereert per objectentabel twee HTML-pagina's in digiGO-huisstijl door twee
versies te vergelijken:

1. **`<naam-inputfile>.html`** — de volledige nieuwe tabel, alfabetisch op de
   eerste kolom, sorteerbaar én filterbaar op alle kolommen (DataTables).
2. **`changelog-<naam-inputfile>.html`** — dezelfde rijen als changelog:
   - gewijzigde cel: oude waarde (doorgestreept) + nieuwe waarde in **blauw**;
   - geheel nieuwe rij: **groen**;
   - vervallen rij: onderaan in **rood**.

## Gebruik (.exe)

Dubbelklik `dist\NLCS-Objectchangelog.exe`:

1. Kies de map met de **nieuwe** versie en de map met de **vorige** versie
   (mappen met de objecten-CSV's).
2. Vul de **versienamen** in die vergeleken worden (bijv. `5.2` en `5.0`) —
   deze verschijnen als label bij de gewijzigde cellen.
3. Kies de **uitvoermap** en klik **Genereer HTML's**.

CSV's worden per **hoofdgroep-code** gekoppeld: het laatste stuk van de
bestandsnaam (bijv. `objecten-5-2-AL` → `AL`). Het versienummer in de naam
wordt genegeerd. Codes die maar in één map zitten worden overgeslagen en in het
logvenster gemeld.

## Vergelijking

- Rijen worden gekoppeld op de kolom **`objectURI`** (stabiele unieke URI;
  `id_nummer` is in oudere versies leeg). Zie `KEY` in `ot_compare.py`.
- Alle gemeenschappelijke kolommen worden **letterlijk** vergeleken (alleen
  omringende spaties worden genegeerd) — geen semantische uitzonderingen.
- Sortering: alfabetisch (hoofdletter-ongevoelig) op de eerste kolom
  (`omschrijving`).

## Modules

| Bestand | Rol |
|---|---|
| `main.py` | startpunt, opent het venster |
| `ot_gui.py` | tkinter-venster + koppelen/genereren in een aparte thread |
| `ot_compare.py` | CSV inlezen, koppelen per map, versies vergelijken |
| `ot_html.py` | de twee HTML-generatoren (volledige tabel + changelog) |
| `ot_config.py` | instellingen onthouden in `config.json` naast de .exe |
| `ot_assets.py` | logo + skyline-banner als base64 (huisstijl, self-contained) |
| `digigo.ico` | pictogram voor de .exe |

## Zelf bouwen

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

Resultaat: `dist\NLCS-Objectchangelog.exe` (`--onefile --windowed`). `dist\`
blijft bij een herbouw staan zodat `config.json` bewaard blijft; alleen de oude
.exe wordt vervangen.

## Losse test (zonder GUI)

```powershell
& "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe" ot_compare.py nieuw.csv oud.csv
```

Toont het aantal kolommen en de tellingen nieuw/gewijzigd/vervallen.
