"""
Haal alle GitHub issues op via GraphQL (minimale API calls)
en zoek naar [[release note]] blokken in issue body + comments.

Gebruik:
    pip install requests
    python fetch_issues_releasenotes.py --token ghp_xxx --owner nl-digigo --repo NLCS

Output: issues_releasenotes.json  (en optioneel .csv)
"""

import argparse
import csv
import json
import re
import sys
import requests


# ---------------------------------------------------------------------------
# GraphQL query: haalt 100 issues per page op, inclusief comments
# ---------------------------------------------------------------------------
QUERY = """
query($owner: String!, $repo: String!, $after: String, $states: [IssueState!]) {
  repository(owner: $owner, name: $repo) {
    issues(first: 100, after: $after, states: $states,
           orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo {
        hasNextPage
        endCursor
      }
      nodes {
        number
        title
        state
        body
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
# Hulpfuncties
# ---------------------------------------------------------------------------

def graphql(token: str, query: str, variables: dict) -> dict:
    """Voer een GraphQL-query uit en geef de data terug."""
    resp = requests.post(
        "https://api.github.com/graphql",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"query": query, "variables": variables},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json()
    if "errors" in payload:
        raise RuntimeError(f"GraphQL errors: {payload['errors']}")
    return payload["data"]


def extract_release_notes(text: str) -> list[str]:
    """
    Zoek naar [[release note]] ... [[release note]] of [[release note]] ... einde.
    Geeft een lijst van gevonden teksten terug.
    """
    if not text:
        return []
    # Alles tussen [[release note]] en het volgende [[ of einde tekst
    pattern = r"\[\[release note\]\](.*?)(?=\[\[|$)"
    matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
    return [m.strip() for m in matches if m.strip()]


def fetch_all_issues(token: str, owner: str, repo: str,
                     states: list[str]) -> list[dict]:
    """
    Haalt alle issues op via gepagineerde GraphQL-calls.
    Elke call geeft 100 issues inclusief hun comments terug.
    """
    all_issues = []
    after = None
    page = 0

    while True:
        page += 1
        variables = {
            "owner": owner,
            "repo": repo,
            "after": after,
            "states": states,
        }
        data = graphql(token, QUERY, variables)
        issues_page = data["repository"]["issues"]
        nodes = issues_page["nodes"]

        print(f"  Pagina {page}: {len(nodes)} issues opgehaald...", flush=True)

        for node in nodes:
            # Verzamel alle tekst om in te zoeken
            texts = [node.get("body") or ""]
            comments = node["comments"]["nodes"]
            for c in comments:
                texts.append(c.get("body") or "")

            # Waarschuw als een issue > 100 comments heeft (worden afgekapt)
            if node["comments"]["pageInfo"]["hasNextPage"]:
                print(f"  ⚠  Issue #{node['number']} heeft >100 comments; "
                      "latere comments worden niet doorzocht.")

            release_notes = []
            for text in texts:
                release_notes.extend(extract_release_notes(text))

            all_issues.append({
                "number": node["number"],
                "title": node["title"],
                "state": node["state"],
                "labels": [lbl["name"] for lbl in node["labels"]["nodes"]],
                "milestone": node["milestone"]["title"]
                             if node["milestone"] else None,
                "release_notes": release_notes,
            })

        if issues_page["pageInfo"]["hasNextPage"]:
            after = issues_page["pageInfo"]["endCursor"]
        else:
            break

    return all_issues


# ---------------------------------------------------------------------------
# Opslaan
# ---------------------------------------------------------------------------

def save_json(issues: list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(issues, f, ensure_ascii=False, indent=2)
    print(f"JSON opgeslagen: {path}")


def save_csv(issues: list[dict], path: str) -> None:
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["number", "title", "state", "labels",
                         "milestone", "release_notes"])
        for issue in issues:
            writer.writerow([
                issue["number"],
                issue["title"],
                issue["state"],
                "; ".join(issue["labels"]),
                issue["milestone"] or "",
                " | ".join(issue["release_notes"]),
            ])
    print(f"CSV opgeslagen: {path}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Download GitHub issues + zoek [[release note]] blokken.")
    parser.add_argument("--token", required=True,
                        help="GitHub Personal Access Token (read:org, repo scope)")
    parser.add_argument("--owner", default="nl-digigo",
                        help="GitHub owner/organisatie (default: nl-digigo)")
    parser.add_argument("--repo", default="NLCS",
                        help="Repository naam (default: NLCS)")
    parser.add_argument("--states", default="OPEN,CLOSED",
                        help="OPEN, CLOSED of OPEN,CLOSED (default: beide)")
    parser.add_argument("--output", default="issues_releasenotes",
                        help="Basisnaam voor output (zonder extensie)")
    parser.add_argument("--csv", action="store_true",
                        help="Sla ook op als CSV")
    args = parser.parse_args()

    states = [s.strip().upper() for s in args.states.split(",")]
    valid = {"OPEN", "CLOSED"}
    if not set(states).issubset(valid):
        print(f"Fout: --states moet OPEN, CLOSED of OPEN,CLOSED zijn.")
        sys.exit(1)

    print(f"Ophalen van issues uit {args.owner}/{args.repo} "
          f"(states: {states})...")

    issues = fetch_all_issues(args.token, args.owner, args.repo, states)

    with_notes = [i for i in issues if i["release_notes"]]
    print(f"\nKlaar: {len(issues)} issues, "
          f"{len(with_notes)} met [[release note]].")

    save_json(issues, f"{args.output}.json")
    if args.csv:
        save_csv(issues, f"{args.output}.csv")


if __name__ == "__main__":
    main()
