# NLCS Release Notes tool

Een klein Windows-programma (tkinter) waarmee je GitHub-issues ophaalt, selecteert
op **milestone**, **label** en een **tag** in de tekst (bv. `[[release note]]`), en er
één nette **HTML-pagina** van maakt met een sorteerbare en filterbare tabel.

## Wat het doet

1. **Inloggen** – klik *Inloggen via GitHub*: je browser opent, je logt in met je
   eigen GitHub-account (wachtwoord + 2FA) en typt de getoonde code. De tool krijgt
   dan automatisch toegang — geen token plakken. (Een token plakken kan nog steeds
   als alternatief.) Daarna klik je *Verbinden*: de milestones en labels van de repo
   worden snel geladen (zonder alle issues op te halen).
2. **Selecteren** – vink aan welke milestones en/of labels je wilt ophalen.
   Alleen die selectie wordt bij GitHub opgevraagd, dus het ophalen gaat sneller.
   Klik *Ophalen*.
3. **Genereren** – kies welke labels je in de tabel wilt tónen, vul de tag in
   (standaard `[[release note]]`), en klik *Genereer HTML*. Het bestand wordt
   opgeslagen en (optioneel) meteen geopend in je browser.

De HTML-tabel heeft kolommen: **Issue** (link) · **Titel** · **State** · **Milestone**
· **Labels** · **Release note**. Je kunt op elke kolom sorteren en per kolom filteren
(dropdown voor State/Milestone, zoekveld voor de rest). Max. 10 rijen per pagina.

> De HTML gebruikt DataTables + jQuery via een CDN, dus voor het **bekijken** van de
> pagina is internet nodig.

## Instellingen onthouden

Alles behalve het token wordt onthouden in `config.json` (naast het programma / de .exe):
owner, repo, states, tag, aangevinkte milestones/labels, titel en output-pad.
Het **token wordt bewust nooit opgeslagen** en moet je elke sessie opnieuw invoeren.

## Draaien vanuit de broncode

Python 3.12 met `requests`:

```powershell
$py = "$env:LOCALAPPDATA\Programs\Python\Python312\python.exe"
& $py -m pip install requests
& $py main.py
```

## Een .exe bouwen

```powershell
powershell -ExecutionPolicy Bypass -File .\build.ps1
```

Resultaat: `dist\NLCS-Releasenotes.exe` — dubbelklikbaar, geen console-venster.

## Bestanden

| Bestand | Rol |
|---------|-----|
| `main.py` | startpunt (opent het venster) |
| `rn_gui.py` | het tkinter-venster en de flow |
| `rn_auth.py` | inloggen via GitHub (OAuth Device Flow, browser-login) |
| `rn_assets.py` | digiGO-huisstijl (logo + banner) als base64 |
| `rn_fetch.py` | ophalen via GitHub GraphQL (lijsten + gefilterde issues) |
| `rn_extract.py` | tags/milestones/labels uit issues halen en filteren |
| `rn_html.py` | de HTML-pagina met de DataTables-tabel maken |
| `rn_config.py` | instellingen onthouden (`config.json`, zonder token) |
| `build.ps1` | de .exe bouwen met PyInstaller |

## Inloggen via GitHub (browser / OAuth)

GitHub ondersteunt **geen wachtwoord-login** meer voor de API. In plaats daarvan
gebruikt de tool de **OAuth Device Flow**: je logt in de browser in met je gewone
GitHub-account en de tool krijgt een tijdelijk token. Dat token wordt **niet**
opgeslagen; je logt elke sessie opnieuw in.

**Eenmalige setup — een OAuth App aanmaken (levert een Client ID):**

1. GitHub → **Settings** → **Developer settings** → **OAuth Apps** → **New OAuth App**.
2. Vul een naam in (bv. "NLCS Release Notes"). Voor Homepage- en Authorization
   callback URL mag je `https://github.com` invullen.
3. Klik **Register application**, open de app en zet onderaan
   **Enable Device Flow** AAN.
4. Kopieer de **Client ID** en plak die in het veld *OAuth client-id* in de tool.

De **Client ID is niet geheim** en wordt onthouden in `config.json`. Er is geen
client-secret nodig voor de Device Flow.

### Alternatief: token plakken

Je kunt ook een **classic Personal Access Token** met de **`repo`**-scope gebruiken
(GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic))
en dat in het veld *of token* plakken. Bewaar het token veilig; deel het nooit in
bestanden, screenshots of chatlogs.

Elke module (`rn_fetch.py`, `rn_extract.py`, `rn_html.py`) is ook los te testen —
zie de docstring bovenaan het bestand.
