"""Minimal SPARQL-over-HTTP client for a Laces workspace/publication endpoint."""
from typing import Optional

import requests
from requests.auth import HTTPBasicAuth


class LacesClient:
    def __init__(self, endpoint: str, token_id: str = "", password: str = "") -> None:
        self.endpoint = endpoint
        self.auth: Optional[HTTPBasicAuth] = (
            HTTPBasicAuth(token_id, password) if token_id and password else None
        )

    def query(self, sparql: str, accept: str = "text/csv") -> str:
        """Runs a SPARQL query and returns the response body, normalized to '\\n' line endings."""
        response = requests.post(
            self.endpoint,
            data=sparql.encode("utf-8"),
            headers={"Content-Type": "application/sparql-query", "Accept": accept},
            auth=self.auth,
            timeout=120,
        )
        response.raise_for_status()
        return response.text.replace("\r\n", "\n").replace("\n\n", "\n")
