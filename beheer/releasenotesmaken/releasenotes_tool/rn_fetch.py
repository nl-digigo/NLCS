"""
rn_fetch.py - Ophaal-kern voor de release notes tool.

Haalt via de GitHub GraphQL API alle issues op (inclusief body, labels,
milestone en comments) in zo min mogelijk API-calls (100 issues per pagina).

Geeft per issue een dict terug:
    {
        "number":    int,
        "title":     str,
        "state":     "OPEN" | "CLOSED",
        "url":       str,          # klikbare link naar het issue
        "milestone": str | None,
        "labels":    list[str],    # ALLE labels van het issue
        "body":      str,          # issue-omschrijving
        "comments":  list[str],    # bodies van de comments (max 100)
    }

Los te testen:
    pip install requests
    python rn_fetch.py --token ghp_xxx --owner nl-digigo --repo NLCS --states OPEN,CLOSED
"""

import requests


# ---------------------------------------------------------------------------
# GraphQL-query: 100 issues per pagina, met labels, milestone en comments
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
        url
        body
        labels(first: 100) {
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


class FetchError(RuntimeError):
    """Fout bij het ophalen van issues (netwerk, auth of GraphQL-fout)."""


def graphql(token: str, query: str, variables: dict) -> dict:
    """Voer een GraphQL-query uit en geef het 'data'-deel terug.

    Gooit FetchError met een leesbare melding bij auth-, netwerk- of
    GraphQL-fouten, zodat de GUI die netjes kan tonen.
    """
    try:
        resp = requests.post(
            "https://api.github.com/graphql",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={"query": query, "variables": variables},
            timeout=30,
        )
    except requests.exceptions.RequestException as exc:
        raise FetchError(f"Netwerkfout bij verbinden met GitHub: {exc}") from exc

    if resp.status_code == 401:
        raise FetchError(
            "Token geweigerd (401). Controleer je Personal Access Token "
            "(classic, met 'repo' scope)."
        )
    if resp.status_code != 200:
        raise FetchError(
            f"GitHub gaf status {resp.status_code} terug: {resp.text[:200]}"
        )

    payload = resp.json()
    if "errors" in payload:
        messages = "; ".join(e.get("message", str(e)) for e in payload["errors"])
        raise FetchError(f"GraphQL-fout: {messages}")
    return payload["data"]


def _parse_node(node: dict, report) -> dict:
    """Zet een GraphQL issue-node om naar ons issue-dict."""
    comments = [c.get("body") or "" for c in node["comments"]["nodes"]]
    if node["comments"]["pageInfo"]["hasNextPage"]:
        report(f"  Let op: issue #{node['number']} heeft >100 comments; "
               "latere comments worden niet meegenomen.")
    return {
        "number": node["number"],
        "title": node["title"],
        "state": node["state"],
        "url": node["url"],
        "milestone": node["milestone"]["title"] if node["milestone"] else None,
        "labels": [lbl["name"] for lbl in node["labels"]["nodes"]],
        "body": node.get("body") or "",
        "comments": comments,
    }


def fetch_all_issues(token: str, owner: str, repo: str,
                     states: list[str], progress=None) -> list[dict]:
    """Haal alle issues op via gepagineerde GraphQL-calls.

    Parameters:
        token:    GitHub Personal Access Token (classic, 'repo' scope).
        owner:    organisatie/eigenaar, bv. "nl-digigo".
        repo:     repository-naam, bv. "NLCS".
        states:   lijst met "OPEN" en/of "CLOSED".
        progress: optionele callback(bericht: str) voor voortgangsmeldingen
                  (bv. om in de GUI te tonen). None = stil.

    Returns:
        Lijst met issue-dicts (zie module-docstring).
    """
    def report(msg: str) -> None:
        if progress is not None:
            progress(msg)

    all_issues: list[dict] = []
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
        repository = data.get("repository")
        if repository is None:
            raise FetchError(
                f"Repository '{owner}/{repo}' niet gevonden of geen toegang. "
                "Controleer owner/repo en de rechten van je token."
            )

        issues_page = repository["issues"]
        nodes = issues_page["nodes"]
        report(f"Pagina {page}: {len(nodes)} issues opgehaald "
               f"(totaal {len(all_issues) + len(nodes)})...")

        for node in nodes:
            all_issues.append(_parse_node(node, report))

        if issues_page["pageInfo"]["hasNextPage"]:
            after = issues_page["pageInfo"]["endCursor"]
        else:
            break

    report(f"Klaar: {len(all_issues)} issues opgehaald.")
    return all_issues


# ---------------------------------------------------------------------------
# Repo-lijsten (milestones + labels) - snel, voor het pre-filteren
# ---------------------------------------------------------------------------
MILESTONES_QUERY = """
query($owner: String!, $repo: String!, $after: String) {
  repository(owner: $owner, name: $repo) {
    milestones(first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes { number title }
    }
  }
}
"""

LABELS_QUERY = """
query($owner: String!, $repo: String!, $after: String) {
  repository(owner: $owner, name: $repo) {
    labels(first: 100, after: $after) {
      pageInfo { hasNextPage endCursor }
      nodes { name }
    }
  }
}
"""


def _fetch_connection(token, owner, repo, query, key):
    """Haal alle nodes uit een gepagineerde connectie (milestones of labels)."""
    nodes = []
    after = None
    while True:
        data = graphql(token, query, {"owner": owner, "repo": repo, "after": after})
        repository = data.get("repository")
        if repository is None:
            raise FetchError(
                f"Repository '{owner}/{repo}' niet gevonden of geen toegang.")
        conn = repository[key]
        nodes.extend(conn["nodes"])
        if conn["pageInfo"]["hasNextPage"]:
            after = conn["pageInfo"]["endCursor"]
        else:
            break
    return nodes


def fetch_repo_lists(token: str, owner: str, repo: str, progress=None) -> tuple:
    """Haal (snel) de milestones en labels van de repo op.

    Returns:
        (milestones, labels) waarbij:
          milestones = lijst van {"number": int, "title": str}, op titel gesorteerd
          labels     = lijst van labelnamen (str), gesorteerd
    """
    def report(msg):
        if progress is not None:
            progress(msg)

    report("Milestones ophalen...")
    ms_nodes = _fetch_connection(token, owner, repo, MILESTONES_QUERY, "milestones")
    milestones = sorted(
        ({"number": n["number"], "title": n["title"]} for n in ms_nodes),
        key=lambda m: m["title"].casefold())

    report("Labels ophalen...")
    lbl_nodes = _fetch_connection(token, owner, repo, LABELS_QUERY, "labels")
    labels = sorted({n["name"] for n in lbl_nodes}, key=str.casefold)

    report(f"{len(milestones)} milestones en {len(labels)} labels geladen.")
    return milestones, labels


# ---------------------------------------------------------------------------
# Gefilterd ophalen (alleen bepaalde milestones/labels) - sneller
# ---------------------------------------------------------------------------
QUERY_FILTERED = """
query($owner: String!, $repo: String!, $after: String, $filterBy: IssueFilters) {
  repository(owner: $owner, name: $repo) {
    issues(first: 100, after: $after, filterBy: $filterBy,
           orderBy: {field: CREATED_AT, direction: ASC}) {
      pageInfo { hasNextPage endCursor }
      nodes {
        number
        title
        state
        url
        body
        labels(first: 100) { nodes { name } }
        milestone { title }
        comments(first: 100) {
          pageInfo { hasNextPage }
          nodes { body }
        }
      }
    }
  }
}
"""


def _paginate_filtered(token, owner, repo, filter_by, report, seen, out):
    """Loop door alle pagina's van één filter en voeg nieuwe issues toe."""
    after = None
    while True:
        variables = {"owner": owner, "repo": repo, "after": after,
                     "filterBy": filter_by}
        data = graphql(token, QUERY_FILTERED, variables)
        repository = data.get("repository")
        if repository is None:
            raise FetchError(
                f"Repository '{owner}/{repo}' niet gevonden of geen toegang.")
        page = repository["issues"]
        for node in page["nodes"]:
            if node["number"] in seen:
                continue
            seen.add(node["number"])
            out.append(_parse_node(node, report))
        if page["pageInfo"]["hasNextPage"]:
            after = page["pageInfo"]["endCursor"]
        else:
            break


def fetch_issues(token: str, owner: str, repo: str, states: list[str],
                 milestone_numbers: list | None = None,
                 label_names: list | None = None,
                 progress=None) -> list[dict]:
    """Haal issues op, optioneel gefilterd op milestones en/of labels.

    Semantiek (OR binnen elke soort, net als het GUI-filter):
      - meerdere milestone_numbers -> issues uit één van die milestones
      - meerdere label_names       -> issues met één van die labels
      - beide gezet                -> combinatie (per milestone x label)
      - niets gezet                -> alle issues (valt terug op fetch_all_issues)

    milestone_numbers zijn de milestone-NUMMERS (uit fetch_repo_lists).
    """
    def report(msg):
        if progress is not None:
            progress(msg)

    if not milestone_numbers and not label_names:
        return fetch_all_issues(token, owner, repo, states, progress)

    ms_jobs = milestone_numbers if milestone_numbers else [None]
    lbl_jobs = label_names if label_names else [None]

    seen: set = set()
    out: list[dict] = []
    for ms in ms_jobs:
        for lbl in lbl_jobs:
            filter_by: dict = {"states": states}
            if ms is not None:
                filter_by["milestoneNumber"] = str(ms)
            if lbl is not None:
                filter_by["labels"] = [lbl]
            beschrijving = ", ".join(
                p for p in [f"milestone#{ms}" if ms is not None else "",
                            f"label '{lbl}'" if lbl is not None else ""] if p)
            report(f"Ophalen ({beschrijving})...")
            _paginate_filtered(token, owner, repo, filter_by, report, seen, out)

    report(f"Klaar: {len(out)} issues opgehaald (na filter).")
    return out


# ---------------------------------------------------------------------------
# Losse test vanaf de command line
# ---------------------------------------------------------------------------

def _main() -> None:
    import argparse

    parser = argparse.ArgumentParser(
        description="Test: haal GitHub-issues op via GraphQL.")
    parser.add_argument("--token", required=True, help="GitHub PAT (classic, repo scope)")
    parser.add_argument("--owner", default="nl-digigo")
    parser.add_argument("--repo", default="NLCS")
    parser.add_argument("--states", default="OPEN,CLOSED",
                        help="OPEN, CLOSED of OPEN,CLOSED")
    parser.add_argument("--out", default=None,
                        help="Sla de opgehaalde issues op als JSON (cache voor tests)")
    args = parser.parse_args()

    states = [s.strip().upper() for s in args.states.split(",") if s.strip()]

    issues = fetch_all_issues(args.token, args.owner, args.repo, states,
                              progress=print)

    if args.out:
        import json
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(issues, f, ensure_ascii=False, indent=2)
        print(f"Opgeslagen als cache: {args.out}")

    # Korte samenvatting zodat je kunt controleren of het klopt
    open_count = sum(1 for i in issues if i["state"] == "OPEN")
    closed_count = sum(1 for i in issues if i["state"] == "CLOSED")
    milestones = {i["milestone"] for i in issues if i["milestone"]}
    labels = {lbl for i in issues for lbl in i["labels"]}

    print()
    print(f"Totaal issues : {len(issues)}  (OPEN {open_count} / CLOSED {closed_count})")
    print(f"Milestones    : {len(milestones)}")
    print(f"Unieke labels : {len(labels)}")
    if issues:
        eerste = issues[0]
        print()
        print("Voorbeeld (eerste issue):")
        print(f"  #{eerste['number']} - {eerste['title']}")
        print(f"  state     : {eerste['state']}")
        print(f"  milestone : {eerste['milestone']}")
        print(f"  labels    : {', '.join(eerste['labels']) or '(geen)'}")
        print(f"  comments  : {len(eerste['comments'])}")


if __name__ == "__main__":
    _main()
