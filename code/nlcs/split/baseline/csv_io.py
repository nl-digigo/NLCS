"""CSV persistence helpers for SPARQL query results."""
import logging
from io import StringIO
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)


def save_csv(csv_text: str, output_path: Path) -> bool:
    """Parses `csv_text` and writes it to `output_path`.

    Returns False (and writes nothing) if the result has no data rows.
    """
    output_path = Path(output_path)
    try:
        df = pd.read_csv(StringIO(csv_text), dtype=str)
    except pd.errors.EmptyDataError:
        log.info("No data for %s; skipping.", output_path.name)
        return False

    if df.empty:
        log.info("No data rows for %s; skipping.", output_path.name)
        return False

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    log.info("Saved %s (%d rows)", output_path, len(df))
    return True


def merge_csv_files(csv_paths: list[Path], output_path: Path) -> None:
    """Concatenates CSVs that share a header into one file at `output_path`."""
    frames = []
    for path in csv_paths:
        try:
            frames.append(pd.read_csv(path, dtype=str))
        except pd.errors.EmptyDataError:
            log.warning("Skipping empty file: %s", path)

    if not frames:
        log.warning("Nothing to merge into %s", output_path)
        return

    merged = pd.concat(frames, ignore_index=True)
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.to_csv(output_path, index=False)
    log.info("Merged %d files into %s (%d rows)", len(csv_paths), output_path, len(merged))
