"""Retrieval of the list of NLCS hoofdgroepen (main groups) from a Laces endpoint."""
from io import StringIO
from pathlib import Path

import pandas as pd

from laces_client import LacesClient
from query_loader import load_query


def retrieve_hoofdgroepen(client: LacesClient, query_path: Path) -> list[str]:
    csv_text = client.query(load_query(query_path))
    df = pd.read_csv(StringIO(csv_text), dtype=str)
    if "hoofdgroup_name" not in df.columns:
        raise ValueError(f"Expected a 'hoofdgroup_name' column, got: {df.columns.tolist()}")
    return sorted(df["hoofdgroup_name"].dropna().tolist())
