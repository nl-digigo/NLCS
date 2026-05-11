# Release notes maken

## Scripts

### 1. `fetch_issues_releasenotes.py`
Haalt issues op en zoekt naar `[[release note]]` blokken in de tekst.

```
python beheer/releasenotesmaken/fetch_issues_releasenotes.py --token "ghp_xxx" --owner nl-digigo --repo NLCS --states OPEN,CLOSED --csv
```

### 2. `download_closed_issues.py`
Haalt alle **gesloten** issues op met al hun comments (max 100 per issue).
Afbeeldingen en bijlagen worden verwijderd. Bedoeld als invoer voor AI om release notes van te maken.

```
python beheer/releasenotesmaken/download_closed_issues.py --token "ghp_xxx"
```

Output: `beheer/releasenotesmaken/closed_issues.json`

## Token aanmaken
Ga naar GitHub → Settings → Developer settings → Personal access tokens → **Tokens (classic)**.
Geef de scope `repo` (read) mee. Fine-grained tokens werken niet met de GraphQL API van organisaties.
