"""
Download alle CLOSED issues uit nl-digigo/NLCS met hun comments (max 100 per issue).
Afbeeldingen en bijlagen worden verwijderd uit de tekst.
Bedoeld als invoer voor AI om release notes van te maken.

Gebruik:
    python beheer/releasenotesmaken/download_closed_issues.py --token "ghp_xxx"

Output: beheer/releasenotesmaken/closed_issues.json
"""

import argparse
import json
import re
import sys
import requests


# ---------------------------------------------------------------------------
# GraphQL query
# ---------------------------------------------------------------------------
QUERY = """
query($owner: String!, $repo: String!, $after: String) {
  repository(owner: $owner, name: $repo) {
    issues(first: 100, after: $after, states: [CLOSED],
           orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        body
        closedAt
        labels(first: 20) {
          nodes { name }
        }
        milestone {
          title
        }
        comments(first: 100) {
          pageInfo { hasNextPage }
          nodes { body }
        }
      }
    }
  }
}
"""


# ---------------------------------------------------------------------------
# Tekst opschonen
# ---------------------------------------------------------------------------

def strip_images_and_attachments(text: str) -> str:
    """
    Verwijder afbeeldingen en bijlagen uit markdown-tekst:
      - Markdown afbeeldingen:  ![alt](url)
      - HTML img-tags:          <img ...>
      - GitHub bijlagen-links:  https://github.com/.../assets/...
      - GitHub user-images:     https://user-images.githubusercontent.com/...
      - HTML-opmerkingen:       <!-- ... -->
    Daarna worden lege regels die overblijven opgeschoond.
    """
    if not text:
        return ""

    # Markdown afbeeldingen
    text = re.sub(r"!\[.*?\]\(.*?\)", "", text)

    # HTML img tags (ook meerdere regels)
    text = re.sub(r"<img\b[^>]*>", "", text, flags=re.IGNORECASE)

    # GitHub bijlagen (volledige Markdown-link of losse URL)
    text = re.sub(
        r"\[.*?\]\(https://github\.com/[^)]*?/assets/[^)]*?\)", "", text
    )
    text = re.sub(
        r"https://github\.com/\S+/assets/\S+", "", text
    )

    # GitHub user-images (oud formaat)
    text = re.sub(
        r"\[.*?\]\(https://user-images\.githubusercontent\.com[^)]*?\)", "", text
    )
    text = re.sub(
        r"https://user-images\.githubusercontent\.com\S+", "", text
    )

    # HTML-opmerkingen
    text = re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)

    # Meer dan 2 lege regels achter elkaar terugbrengen naar 1 witregel
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ---------------------------------------------------------------------------
# GraphQL aanroep
# ---------------------------------------------------------------------------

def graphql(token: str, variables: dict) -> dict:
    resp = requests.post(
        "https://api.github.com/graphql",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"query": QUERY, "variables": variables},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if "errors" in payload:
        raise RuntimeError(f"GraphQL fouten: {payload['errors']}")
    return payload["data"]


# ---------------------------------------------------------------------------
# Hoofdfunctie
# ---------------------------------------------------------------------------

def fetch_closed_issues(token: str, owner: str, repo: str) -> list[dict]:
    all_issues = []
    after = None
    page = 0

    while True:
        page += 1
        data = graphql(token, {"owner": owner, "repo": repo, "after": after})
        page_data = data["repository"]["issues"]
        nodes = page_data["nodes"]

        print(f"  Pagina {page}: {len(nodes)} issues...", flush=True)

        for node in nodes:
            body = strip_images_and_attachments(node.get("body") or "")

            comments = []
            for c in node["comments"]["nodes"]:
                cleaned = strip_images_and_attachments(c.get("body") or "")
                if cleaned:
                    comments.append(cleaned)

            if node["comments"]["pageInfo"]["hasNextPage"]:
                print(
                    f"  Waarschuwing: issue #{node['number']} heeft >100 comments; "
                    "de rest wordt overgeslagen."
                )

            all_issues.append({
                "number": node["number"],
                "title": node["title"],
                "closed_at": node["closedAt"],
                "labels": [lbl["name"] for lbl in node["labels"]["nodes"]],
                "milestone": node["milestone"]["title"]
                             if node["milestone"] else None,
                "body": body,
                "comments": comments,
            })

        if page_data["pageInfo"]["hasNextPage"]:
            after = page_data["pageInfo"]["endCursor"]
        else:
            break

    return all_issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download closed GitHub issues (zonder afbeeldingen) voor AI-verwerking."
    )
    parser.add_argument("--token", required=True,
                        help='GitHub Personal Access Token, bijv. "ghp_xxx"')
    parser.add_argument("--owner", default="nl-digigo",
                        help="GitHub eigenaar (default: nl-digigo)")
    parser.add_argument("--repo", default="NLCS",
                        help="Repository (default: NLCS)")
    parser.add_argument("--output",
                        default="beheer/releasenotesmaken/closed_issues.json",
                        help="Pad naar output JSON-bestand")
    args = parser.parse_args()

    print(f"Ophalen van gesloten issues uit {args.owner}/{args.repo}...")
    issues = fetch_closed_issues(args.token, args.owner, args.repo)

    print(f"\nKlaar: {len(issues)} issues opgehaald.")

    with open(args.output, "w", encoding="utf-8") as f:
        json.dump(issues, f, ensure_ascii=False, indent=2)

    print(f"Opgeslagen in: {args.output}")


if __name__ == "__main__":
    main()
