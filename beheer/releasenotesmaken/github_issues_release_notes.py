"""
GitHub Issues Release Notes Query Tool
=======================================
Dit script haalt alle gesloten issues op van de nl-digigo/NLCS GitHub repository
en doorzoekt de comments op release note informatie.

Output: een HTML-tabel en een CSV-bestand in beheer/changelog/

Gebruik:
    1. Stel je GitHub token in als environment variable:
       set GITHUB_TOKEN=jouw_token_hier        (Windows cmd)
       $env:GITHUB_TOKEN="jouw_token_hier"      (PowerShell)
    2. Draai het script:
       python beheer/changelog/github_issues_release_notes.py
"""

import csv
import os
import sys
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# =============================================================================
# CONFIGURATIE
# =============================================================================

# GitHub repository gegevens
REPO_OWNER = "nl-digigo"
REPO_NAME = "NLCS"
BASE_URL = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"

# Output bestanden (relatief aan dit script)
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
OUTPUT_CSV = os.path.join(SCRIPT_DIR, "release_notes_issues.csv")
OUTPUT_HTML = os.path.join(SCRIPT_DIR, "release_notes_issues.html")

# Zoekteksten voor release notes in comments
RELEASE_NOTE_TAG = "[Release note]"
NO_CHANGE_TAG = "[release note: no change from issue]"


# =============================================================================
# STAP 1: GitHub API verbinding opzetten
# =============================================================================

def get_github_token():
    """
    Leest het GitHub Personal Access Token uit de environment variable GITHUB_TOKEN.
    Stopt het script met een duidelijke foutmelding als het token niet is ingesteld.
    """
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("FOUT: Environment variable GITHUB_TOKEN is niet ingesteld.")
        print("")
        print("Stel deze in voordat je het script draait:")
        print('  Windows cmd:    set GITHUB_TOKEN=jouw_token_hier')
        print('  PowerShell:     $env:GITHUB_TOKEN="jouw_token_hier"')
        sys.exit(1)
    return token


def create_session(token):
    """
    Maakt een requests Session aan met:
    - Authenticatie headers voor de GitHub API
    - Automatische retry bij tijdelijke fouten (SSL errors, timeouts, 5xx fouten)
    
    Een Session hergebruikt de TCP/SSL-verbinding, wat sneller is dan
    elke keer een nieuwe verbinding opzetten met requests.get().
    
    De retry-strategie probeert het automatisch opnieuw (max 5 keer) bij:
    - Connectiefouten (bijv. SSL handshake mislukt)
    - Timeouts
    - Server fouten (status 500, 502, 503, 504)
    """
    session = requests.Session()

    # Headers instellen op de session (worden bij elk request meegestuurd)
    session.headers.update({
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github.v3+json",
    })

    # Retry-strategie configureren
    retry_strategy = Retry(
        total=5,                          # Maximaal 5 pogingen
        backoff_factor=1,                 # Wachttijd: 1s, 2s, 4s, 8s, 16s
        status_forcelist=[500, 502, 503, 504],  # Retry bij deze HTTP statussen
        allowed_methods=["GET"],          # Alleen retry bij GET requests
    )

    # Koppel de retry-strategie aan zowel HTTP als HTTPS
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    return session


# =============================================================================
# STAP 2: Alle gesloten issues ophalen (met paginering)
# =============================================================================

def fetch_all_closed_issues(session):
    """
    Haalt ALLE gesloten issues op uit de repository.
    
    De GitHub API geeft maximaal 100 issues per keer terug (per 'pagina').
    We moeten dus meerdere pagina's ophalen totdat er geen resultaten meer zijn.
    Dit heet 'paginering'.
    
    Parameters:
        session: de requests Session met authenticatie en retry-logica
    
    Returns:
        Een lijst met alle gesloten issues (als dictionaries)
    """
    all_issues = []
    page = 1

    print(f"Issues ophalen van {REPO_OWNER}/{REPO_NAME}...")

    while True:
        # Bouw de URL met parameters:
        # - state=closed  -> alleen gesloten issues
        # - per_page=100  -> maximaal 100 per pagina (het maximum van de API)
        # - page=N        -> welke pagina we willen
        url = f"{BASE_URL}/issues"
        params = {
            "state": "closed",
            "per_page": 100,
            "page": page,
        }

        response = session.get(url, params=params, timeout=30)

        # Controleer of de API-call succesvol was
        if response.status_code != 200:
            print(f"FOUT: API gaf status {response.status_code} terug.")
            print(f"Bericht: {response.text}")
            sys.exit(1)

        issues_on_page = response.json()

        # Als de pagina leeg is, zijn we klaar
        if not issues_on_page:
            break

        # Filter pull requests eruit - de GitHub Issues API geeft ook PRs terug.
        # Een issue is een PR als het een "pull_request" veld heeft.
        real_issues = [
            issue for issue in issues_on_page
            if "pull_request" not in issue
        ]

        all_issues.extend(real_issues)
        print(f"  Pagina {page}: {len(real_issues)} issues opgehaald "
              f"(totaal: {len(all_issues)})")

        page += 1

        # Korte pauze om de API niet te overbelasten
        time.sleep(0.3)

    print(f"Totaal: {len(all_issues)} gesloten issues gevonden.\n")
    return all_issues


# =============================================================================
# STAP 3: Comments ophalen en doorzoeken per issue
# =============================================================================

def fetch_comments_for_issue(issue_number, session):
    """
    Haalt alle comments op voor een specifiek issue nummer.
    
    Parameters:
        issue_number: het nummer van de issue
        session: de requests Session met authenticatie en retry-logica
    
    Returns:
        Een lijst met comment dictionaries
    """
    all_comments = []
    page = 1

    while True:
        url = f"{BASE_URL}/issues/{issue_number}/comments"
        params = {
            "per_page": 100,
            "page": page,
        }

        try:
            response = session.get(url, params=params, timeout=30)
        except requests.exceptions.RequestException as e:
            print(f"  WAARSCHUWING: Netwerkfout bij ophalen comments voor "
                  f"issue #{issue_number}: {e}")
            return all_comments

        if response.status_code != 200:
            print(f"  WAARSCHUWING: Kon comments niet ophalen voor issue "
                  f"#{issue_number} (status {response.status_code})")
            return all_comments

        comments_on_page = response.json()

        if not comments_on_page:
            break

        all_comments.extend(comments_on_page)
        page += 1

        # Korte pauze
        time.sleep(0.2)

    return all_comments


def search_comments_for_release_notes(comments):
    """
    Doorzoekt de comments van een issue op release note informatie.
    
    Zoekt naar:
    1. Een comment die '[Release note]' bevat         -> release_note_text
    2. Een comment die '[release note: no change from issue]' bevat -> no_change_text
    3. De laatste comment (als fallback)              -> last_comment_text
    
    Parameters:
        comments: lijst met comment dictionaries van de GitHub API
    
    Returns:
        Een tuple: (release_note_text, no_change_text, last_comment_text)
    """
    release_note_text = ""
    no_change_text = ""
    last_comment_text = ""

    # Doorloop alle comments
    for comment in comments:
        body = comment.get("body", "") or ""

        # Zoek naar [Release note] (case-insensitive)
        if RELEASE_NOTE_TAG.lower() in body.lower():
            release_note_text = body.strip()

        # Zoek naar [release note: no change from issue] (case-insensitive)
        if NO_CHANGE_TAG.lower() in body.lower():
            no_change_text = body.strip()

    # De laatste comment (als er comments zijn)
    if comments:
        last_body = comments[-1].get("body", "") or ""
        last_comment_text = last_body.strip()

    # Fallback logica: de laatste comment wordt alleen gebruikt als BEIDE
    # release_note_text EN no_change_text leeg zijn
    if release_note_text or no_change_text:
        last_comment_text = ""

    return release_note_text, no_change_text, last_comment_text


# =============================================================================
# STAP 4: Data verzamelen voor alle issues
# =============================================================================

def process_all_issues(issues, session):
    """
    Verwerkt alle issues: haalt comments op en bouwt de data-rijen op.
    
    Parameters:
        issues: lijst met issue dictionaries
        session: de requests Session met authenticatie en retry-logica
    
    Returns:
        Een lijst met dictionaries, één per issue, met alle kolom-data
    """
    rows = []
    total = len(issues)

    for index, issue in enumerate(issues, start=1):
        issue_number = issue["number"]
        issue_url = issue["html_url"]

        # Milestone (kan None zijn als er geen milestone is)
        milestone = ""
        if issue.get("milestone"):
            milestone = issue["milestone"]["title"]

        # Labels: gescheiden door ' | ' (pipe)
        labels = " | ".join(label["name"] for label in issue.get("labels", []))

        # Voortgang tonen
        print(f"  [{index}/{total}] Issue #{issue_number} verwerken...")

        # Comments ophalen
        comments = fetch_comments_for_issue(issue_number, session)

        # Comments doorzoeken op release note patronen
        release_note, no_change, last_comment = search_comments_for_release_notes(comments)

        # Data-rij toevoegen
        rows.append({
            "issue_number": issue_number,
            "issue_url": issue_url,
            "milestone": milestone,
            "labels": labels,
            "release_note": release_note,
            "no_change": no_change,
            "last_comment": last_comment,
        })

    return rows


# =============================================================================
# STAP 5: Sorteren
# =============================================================================

def sort_rows(rows):
    """
    Sorteert de rijen op:
    1. Milestone (alfabetisch, issues ZONDER milestone komen onderaan)
    2. Issue nummer (oplopend)
    
    Parameters:
        rows: lijst met data-dictionaries
    
    Returns:
        Gesorteerde lijst
    """
    def sort_key(row):
        # Issues zonder milestone krijgen een hoge sorteerwaarde
        # zodat ze onderaan komen
        milestone = row["milestone"]
        if not milestone:
            milestone_sort = (1, "")  # 1 = onderaan
        else:
            milestone_sort = (0, milestone.lower())  # 0 = bovenaan

        return (milestone_sort, row["issue_number"])

    return sorted(rows, key=sort_key)


# =============================================================================
# STAP 6: CSV genereren
# =============================================================================

def generate_csv(rows, filepath):
    """
    Genereert een CSV-bestand met puntkomma als scheidingsteken.
    Puntkomma wordt gebruikt zodat het bestand correct opent in Excel
    (komma's kunnen in de data voorkomen).
    
    Parameters:
        rows: gesorteerde lijst met data-dictionaries
        filepath: pad waar het CSV-bestand wordt opgeslagen
    """
    with open(filepath, "w", newline="", encoding="utf-8-sig") as csvfile:
        # utf-8-sig voegt een BOM (Byte Order Mark) toe zodat Excel
        # het bestand correct als UTF-8 herkent
        writer = csv.writer(csvfile, delimiter=";", quoting=csv.QUOTE_ALL)

        # Header rij
        writer.writerow([
            "Issue",
            "Milestone",
            "Labels",
            "Release Note",
            "No Change",
            "Laatste Comment",
        ])

        # Data rijen
        for row in rows:
            writer.writerow([
                f'#{row["issue_number"]}',
                row["milestone"],
                row["labels"],
                row["release_note"],
                row["no_change"],
                row["last_comment"],
            ])

    print(f"CSV opgeslagen: {filepath}")


# =============================================================================
# STAP 7: HTML tabel genereren
# =============================================================================

def escape_html(text):
    """
    Vervangt speciale HTML-tekens zodat ze correct worden weergegeven.
    Bijvoorbeeld: < wordt &lt; zodat het niet als HTML-tag wordt gezien.
    """
    return (text
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
            .replace("\n", "<br>"))


def generate_html(rows, filepath):
    """
    Genereert een HTML-bestand met een gestileerde tabel.
    Issue nummers worden als klikbare links weergegeven.
    
    Parameters:
        rows: gesorteerde lijst met data-dictionaries
        filepath: pad waar het HTML-bestand wordt opgeslagen
    """
    html_parts = []

    # HTML header met styling
    html_parts.append("""<!DOCTYPE html>
<html lang="nl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>NLCS GitHub Issues - Release Notes</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
            margin: 20px;
            background-color: #f6f8fa;
        }
        h1 {
            color: #24292e;
        }
        .info {
            color: #586069;
            margin-bottom: 20px;
        }
        table {
            border-collapse: collapse;
            width: 100%;
            background-color: white;
            box-shadow: 0 1px 3px rgba(0,0,0,0.12);
        }
        th {
            background-color: #24292e;
            color: white;
            padding: 10px 12px;
            text-align: left;
            position: sticky;
            top: 0;
        }
        td {
            padding: 8px 12px;
            border-bottom: 1px solid #e1e4e8;
            vertical-align: top;
            max-width: 400px;
            overflow-wrap: break-word;
        }
        tr:hover {
            background-color: #f1f8ff;
        }
        a {
            color: #0366d6;
            text-decoration: none;
        }
        a:hover {
            text-decoration: underline;
        }
        .milestone {
            background-color: #e1e4e8;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.85em;
        }
        .label {
            display: inline-block;
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 0.8em;
            background-color: #d1ecf1;
            margin: 1px;
        }
    </style>
</head>
<body>
    <h1>NLCS GitHub Issues - Release Notes</h1>
    <p class="info">Totaal: """ + str(len(rows)) + """ gesloten issues | 
    Gesorteerd op milestone, daarna op issue nummer</p>
    <table>
        <thead>
            <tr>
                <th>Issue</th>
                <th>Milestone</th>
                <th>Labels</th>
                <th>Release Note</th>
                <th>No Change</th>
                <th>Laatste Comment</th>
            </tr>
        </thead>
        <tbody>
""")

    # Tabel rijen
    for row in rows:
        issue_link = (f'<a href="{row["issue_url"]}" target="_blank">'
                      f'#{row["issue_number"]}</a>')

        milestone_html = ""
        if row["milestone"]:
            milestone_html = (f'<span class="milestone">'
                              f'{escape_html(row["milestone"])}</span>')

        # Labels als individuele badges
        labels_html = ""
        if row["labels"]:
            label_list = row["labels"].split(" | ")
            labels_html = " ".join(
                f'<span class="label">{escape_html(l)}</span>'
                for l in label_list
            )

        html_parts.append(f"""            <tr>
                <td>{issue_link}</td>
                <td>{milestone_html}</td>
                <td>{labels_html}</td>
                <td>{escape_html(row["release_note"])}</td>
                <td>{escape_html(row["no_change"])}</td>
                <td>{escape_html(row["last_comment"])}</td>
            </tr>
""")

    # HTML afsluiten
    html_parts.append("""        </tbody>
    </table>
</body>
</html>
""")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("".join(html_parts))

    print(f"HTML opgeslagen: {filepath}")


# =============================================================================
# HOOFDPROGRAMMA
# =============================================================================

def main():
    """
    Hoofdfunctie die alle stappen uitvoert:
    1. Token lezen
    2. Session aanmaken (met retry-logica)
    3. Gesloten issues ophalen
    4. Comments verwerken
    5. Sorteren
    6. CSV en HTML genereren
    """
    print("=" * 60)
    print("NLCS GitHub Issues - Release Notes Generator")
    print("=" * 60)
    print()

    # Stap 1: Token ophalen
    token = get_github_token()

    # Stap 2: Session aanmaken met retry-logica
    session = create_session(token)

    # Stap 3: Alle gesloten issues ophalen
    issues = fetch_all_closed_issues(session)

    if not issues:
        print("Geen gesloten issues gevonden. Script stopt.")
        sys.exit(0)

    # Stap 4: Comments verwerken per issue
    print("Comments ophalen en doorzoeken...")
    rows = process_all_issues(issues, session)

    # Stap 5: Sorteren
    print("\nResultaten sorteren...")
    sorted_rows = sort_rows(rows)

    # Stap 6: CSV genereren
    print("\nOutput genereren...")
    generate_csv(sorted_rows, OUTPUT_CSV)

    # Stap 7: HTML genereren
    generate_html(sorted_rows, OUTPUT_HTML)

    print()
    print("=" * 60)
    print("Klaar!")
    print(f"  CSV:  {OUTPUT_CSV}")
    print(f"  HTML: {OUTPUT_HTML}")
    print("=" * 60)


# Dit zorgt ervoor dat main() alleen wordt uitgevoerd als je het script
# direct draait (niet als je het importeert vanuit een ander script)
if __name__ == "__main__":
    main()
