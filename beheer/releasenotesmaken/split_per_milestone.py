"""
Splits closed_issues.json op in een bestand per milestone.

Gebruik:
    python beheer/releasenotesmaken/split_per_milestone.py

Output: beheer/releasenotesmaken/milestones/<milestone>.json
"""

import json
import re
from collections import defaultdict
from pathlib import Path

INPUT = Path("beheer/releasenotesmaken/closed_issues.json")
OUTPUT_DIR = Path("beheer/releasenotesmaken/milestones")


def safe_filename(name: str) -> str:
    """Zet een milestone-naam om naar een veilige bestandsnaam."""
    name = name.strip()
    name = re.sub(r'[\\/*?:"<>|]', "_", name)
    return name


def main() -> None:
    with open(INPUT, encoding="utf-8") as f:
        issues = json.load(f)

    # Groepeer per milestone
    per_milestone = defaultdict(list)
    for issue in issues:
        milestone = issue.get("milestone") or "geen_milestone"
        per_milestone[milestone].append(issue)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for milestone, milestone_issues in sorted(per_milestone.items()):
        filename = OUTPUT_DIR / f"{safe_filename(milestone)}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(milestone_issues, f, ensure_ascii=False, indent=2)
        print(f"  {filename.name}: {len(milestone_issues)} issues")

    print(f"\nKlaar: {len(per_milestone)} bestanden in {OUTPUT_DIR}/")


if __name__ == "__main__":
    main()
