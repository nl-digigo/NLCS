"""
compare_against_baseline.py
----------------------------
Compares the 5.0 baseline CSV export against a merged split-publication CSV
export (both produced by nlcs_exporter_5-0.py / nlcs_exporter_local.py in this
folder), using compare_csv.py for a key-matched Excel diff per file, and
prints a one-line-per-file summary.

Usage
-----
    python compare_against_baseline.py
    python compare_against_baseline.py --baseline tabellen/split-baseline/5.0 --merged tabellen/split-baseline/merged
"""
import argparse
import logging
import sys
from pathlib import Path

import config

COMPARE_MODULE_DIR = config.REPO_ROOT / "code" / "nlcs" / "split" / "compare"
sys.path.insert(0, str(COMPARE_MODULE_DIR))
from compare_csv import compare  # noqa: E402

log = logging.getLogger(__name__)

DEFAULT_BASELINE = config.REPO_ROOT / "tabellen" / "split-baseline" / "5.0"
DEFAULT_MERGED = config.REPO_ROOT / "tabellen" / "split-baseline" / "merged"
DEFAULT_OUTPUT = config.REPO_ROOT / "tabellen" / "split-baseline" / "comparison"


def find_concept_table_files(baseline_dir: Path, merged_dir: Path) -> list[str]:
    """Concept-table CSVs present in both folders (excludes objectentabellen/ and all_objects-*)."""
    baseline_names = {p.name for p in baseline_dir.glob("*.csv")}
    merged_names = {p.name for p in merged_dir.glob("*.csv")}
    return sorted(baseline_names & merged_names)


def find_hoofdgroepen(merged_dir: Path) -> list[str]:
    """Hoofdgroep codes that have an objects table in the merged output."""
    prefix = f"objecten-{config.VERSION}-"
    codes = []
    for path in (merged_dir / "objectentabellen").glob(f"{prefix}*.csv"):
        codes.append(path.stem[len(prefix):])
    return sorted(codes)


def run(baseline_dir: Path, merged_dir: Path, output_dir: Path) -> dict:
    output_dir.mkdir(parents=True, exist_ok=True)
    results = {}

    for fname in find_concept_table_files(baseline_dir, merged_dir):
        f1, f2 = baseline_dir / fname, merged_dir / fname
        out = output_dir / f"{Path(fname).stem}.xlsx"
        log.info("Comparing %s", fname)
        results[fname] = compare(str(f1), str(f2), str(out))

    for hoofdgroep in find_hoofdgroepen(merged_dir):
        fname = f"objecten-{config.VERSION}-{hoofdgroep}.csv"
        f1 = baseline_dir / "objectentabellen" / fname
        f2 = merged_dir / "objectentabellen" / fname
        if not f1.exists():
            log.warning("No baseline objects table for hoofdgroep '%s' (missing %s) - skipping.", hoofdgroep, f1)
            continue
        out = output_dir / f"{Path(fname).stem}.xlsx"
        log.info("Comparing %s", fname)
        results[fname] = compare(str(f1), str(f2), str(out))

    return results


def print_summary(results: dict) -> None:
    print(f'{"file":<35} {"rows1":>6} {"rows2":>6} {"only1":>6} {"only2":>6} {"diffs":>6} {"same":>6}  key_col (method)')
    for fname, s in results.items():
        print(
            f'{fname:<35} {s["rows1"]:>6} {s["rows2"]:>6} {s["only_in_1"]:>6} '
            f'{s["only_in_2"]:>6} {s["diff_rows"]:>6} {s["identical_rows"]:>6}  '
            f'{s["key_col"]} ({s["key_method"]})'
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--baseline", default=str(DEFAULT_BASELINE), help="Baseline CSV folder (default: %(default)s)")
    parser.add_argument("--merged", default=str(DEFAULT_MERGED), help="Merged-publication CSV folder (default: %(default)s)")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Folder for the per-file Excel diffs (default: %(default)s)")
    return parser.parse_args()


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
    args = parse_args()
    results = run(Path(args.baseline), Path(args.merged), Path(args.output))
    print()
    print_summary(results)


if __name__ == "__main__":
    main()
