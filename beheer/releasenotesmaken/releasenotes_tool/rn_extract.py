"""
rn_extract.py - Extractie en verzameling voor de release notes tool.

Werkt op de issue-dicts die rn_fetch.fetch_all_issues() teruggeeft.

Twee soorten werk:
  1. Tag-extractie: de tekst achter een tag zoals [[release note]] uit de
     body + comments halen (de eigenlijke release note).
  2. Verzamelen/filteren: unieke milestones en labels verzamelen voor de
     GUI-lijsten, en issues filteren op milestone/label/tag.

Conventie voor tags: dubbele blokhaken, bv. [[release note]]. Alles NA de tag
tot de volgende [[...]]-tag (of einde tekst) telt als de inhoud van die tag.

Los te testen (met cache-JSON van rn_fetch --out):
    python rn_extract.py --in issues.json --tag "[[release note]]"
"""

import re


# ---------------------------------------------------------------------------
# 1. Tag-extractie
# ---------------------------------------------------------------------------

def find_tag_blocks(text: str, tag: str) -> list[str]:
    """Geef alle tekstblokken terug die achter `tag` staan.

    Een blok loopt vanaf net na de tag tot de volgende [[...]]-tag of het
    einde van de tekst. Hoofdletterongevoelig. Lege blokken worden overgeslagen.
    """
    if not text or not tag:
        return []
    # Vind posities van de tag, pak daarna tot het volgende "[[" of einde.
    pattern = re.escape(tag) + r"(.*?)(?=\[\[|$)"
    matches = re.findall(pattern, text, flags=re.IGNORECASE | re.DOTALL)
    return [m.strip() for m in matches if m.strip()]


def issue_texts(issue: dict) -> list[str]:
    """Alle doorzoekbare tekst van een issue: body + alle comments."""
    texts = [issue.get("body") or ""]
    texts.extend(issue.get("comments") or [])
    return texts


def issue_tag_blocks(issue: dict, tag: str) -> list[str]:
    """Alle tag-blokken van een issue (uit body én comments), in volgorde."""
    blocks: list[str] = []
    for text in issue_texts(issue):
        blocks.extend(find_tag_blocks(text, tag))
    return blocks


def issue_has_tag(issue: dict, tag: str) -> bool:
    """True als de tag ergens in body of comments voorkomt (ook zonder inhoud)."""
    if not tag:
        return False
    needle = tag.lower()
    return any(needle in (t or "").lower() for t in issue_texts(issue))


# ---------------------------------------------------------------------------
# 2. Verzamelen voor de GUI-lijsten
# ---------------------------------------------------------------------------

def collect_milestones(issues: list[dict]) -> list[str]:
    """Gesorteerde lijst met unieke milestone-titels (zonder None)."""
    found = {i["milestone"] for i in issues if i.get("milestone")}
    return sorted(found, key=str.casefold)


def collect_labels(issues: list[dict]) -> list[str]:
    """Gesorteerde lijst met alle unieke labelnamen over alle issues."""
    found = {lbl for i in issues for lbl in (i.get("labels") or [])}
    return sorted(found, key=str.casefold)


# ---------------------------------------------------------------------------
# 3. Filteren (welke issues komen in de output)
# ---------------------------------------------------------------------------

def filter_issues(issues: list[dict], *,
                  milestones: list[str] | None = None,
                  labels: list[str] | None = None,
                  tag: str | None = None,
                  require_tag: bool = False) -> list[dict]:
    """Filter issues op selectiecriteria. Leeg/None criterium = niet filteren.

    Parameters:
        milestones:  alleen issues met een milestone uit deze lijst.
        labels:      alleen issues met minstens één label uit deze lijst.
        tag:         de tag waarop we (optioneel) filteren en extraheren.
        require_tag: als True, alleen issues waarin `tag` voorkomt.

    Het filteren is AND tussen de criteria, OR binnen een criterium
    (bv. milestone A OF B; label X OF Y).
    """
    milestone_set = set(milestones) if milestones else None
    label_set = set(labels) if labels else None

    result = []
    for issue in issues:
        if milestone_set is not None and issue.get("milestone") not in milestone_set:
            continue
        if label_set is not None and not (label_set & set(issue.get("labels") or [])):
            continue
        if require_tag and tag and not issue_has_tag(issue, tag):
            continue
        result.append(issue)
    return result


# ---------------------------------------------------------------------------
# Losse test
# ---------------------------------------------------------------------------

def _main() -> None:
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Test: extractie en verzameling op opgehaalde issues.")
    src = parser.add_mutually_exclusive_group(required=True)
    src.add_argument("--in", dest="infile",
                     help="JSON-cache van rn_fetch (--out)")
    src.add_argument("--token", help="GitHub PAT om live op te halen")
    parser.add_argument("--owner", default="nl-digigo")
    parser.add_argument("--repo", default="NLCS")
    parser.add_argument("--states", default="OPEN,CLOSED")
    parser.add_argument("--tag", default="[[release note]]",
                        help="Tag om op te filteren/extraheren")
    args = parser.parse_args()

    if args.infile:
        with open(args.infile, encoding="utf-8") as f:
            issues = json.load(f)
        print(f"Ingelezen uit cache: {len(issues)} issues ({args.infile})")
    else:
        import rn_fetch
        states = [s.strip().upper() for s in args.states.split(",") if s.strip()]
        issues = rn_fetch.fetch_all_issues(args.token, args.owner, args.repo,
                                           states, progress=print)

    milestones = collect_milestones(issues)
    labels = collect_labels(issues)
    with_tag = [i for i in issues if issue_has_tag(i, args.tag)]
    with_note = [i for i in issues if issue_tag_blocks(i, args.tag)]

    print()
    print(f"Milestones ({len(milestones)}):")
    for m in milestones:
        print(f"  - {m}")
    print()
    print(f"Labels ({len(labels)}):")
    for lbl in labels:
        print(f"  - {lbl}")
    print()
    print(f"Issues met tag '{args.tag}'          : {len(with_tag)}")
    print(f"Issues met tekst achter die tag      : {len(with_note)}")

    # Toon een paar voorbeelden van geëxtraheerde release notes
    print()
    print("Voorbeelden van geëxtraheerde tekst (max 3):")
    shown = 0
    for issue in with_note:
        for block in issue_tag_blocks(issue, args.tag):
            snippet = block.replace("\n", " ")
            if len(snippet) > 160:
                snippet = snippet[:160] + "..."
            print(f"  #{issue['number']}: {snippet}")
            shown += 1
            break
        if shown >= 3:
            break


if __name__ == "__main__":
    _main()
