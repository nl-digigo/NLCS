"""Loading and parameterizing .rq SPARQL query files."""
from pathlib import Path


def load_query(query_path: Path) -> str:
    return Path(query_path).read_text(encoding="utf-8")


def render_query(template_path: Path, placeholder: str, value: str) -> str:
    """Loads a query template and substitutes `placeholder` with `value`."""
    template = load_query(template_path)
    if placeholder not in template:
        raise ValueError(f"Placeholder '{placeholder}' not found in query template: {template_path}")
    return template.replace(placeholder, value)
