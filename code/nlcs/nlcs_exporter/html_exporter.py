import csv
from io import StringIO
import pandas as pd

def is_bound(value, row):
    if value is None or value.strip() == "":
        return "wrong"   
    return "correct"

def is_bound_and_not_RGB(value, row):
    if value is None or value.strip() == "":
        return "wrong"   
    elif "," in value:
        return "wrong"
    else:
        return "correct"

def is_valid_string(value, row):
    """
    Returns:
      "correct" -> passes all checks
      "wrong"   -> violates rules
      "lower"   -> string is lowercase
    """
    # if value is None or str(value).strip() == "":
    #     return "wrong"  # empty is wrong
    
    val = str(value).strip()

    if val.islower():
        return "lower"

    # Rule 1: "-" allowed only if last part and type is "BEWERKING"
    # We'll check if there is a "-" anywhere not at the end
    # Split by "-" and check all except last
    if "-" in val:
        parts = val.split("-")
        if len(parts) > 1:
            # Only allowed if last part and type is BEWERKING
            if row.get("type", "").upper() != "BEWERKING":
                return "wrong"
            # Also ensure only last part has "-", i.e., all others no "-"
            # Actually split keeps "-" only as separator; so we only check count >1
            # If multiple "-", fail
            if len(parts) > 2:
                return "wrong"

    # Rule 2: no "\" or "/"
    if "\\" in val or "/" in val:
        return "wrong"

    # Rule 3: no ","
    if "," in val:
        return "wrong"

    # Rule 4: no square brackets
    if "[" in val or "]" in val:
        return "wrong"

    # If all passed
    return "correct"

def is_label_reused(value, row):
    df = pd.read_csv("tabellen/controles//NLCS_Query_Vervallen_Objects_Reused_Labels-concept-5.1.csv")

    if "label" not in df.columns:
        raise ValueError("CSV must contain 'label' column")

    # Use a set for fast lookup
    invalid_labels = set(
        df["label"]
        .dropna()
        .astype(str)
        .str.strip()
    )

    if value is None or str(value).strip() == "":
        return "wrong"

    val = str(value).strip()

    if val in invalid_labels:
        return "wrong"
    else:
        return "correct"

def sparql_to_html(
    sparql_text,
    output_file="sparql_results.html",
    delimiter=",",
    column_rules=None
):
    """
    column_rules: dict of column_name -> function(value, row) -> "correct" | "wrong" | None
    """

    # Parse SPARQL text (CSV or TSV)
    reader = csv.DictReader(StringIO(sparql_text), delimiter=delimiter)
    rows = list(reader)

    if not rows:
        print("No data.")
        return

    headers = rows[0].keys()

    # HTML header
    html = """
    <html>
    <head>
    <style>
    table { border-collapse: collapse; font-family: Arial; }
    th, td { border: 1px solid #ccc; padding: 8px; }
    th { background-color: #f2f2f2; }
    .correct { background-color: #c8e6c9; }  /* green */
    .wrong { background-color: #ffcdd2; }    /* red */
    .lower { background-color: #ffe0b2; }    /* orange */
    </style>
    </head>
    <body>
    <h2>SPARQL Results</h2>
    <table>
    <tr>
    """

    # Headers
    for h in headers:
        html += f"<th>{h}</th>"
    html += "</tr>\n"

    # Rows
    for row in rows:
        html += "<tr>"

        for col in headers:
            value = row[col]

            css_class = ""

            if column_rules and col in column_rules:
                result = column_rules[col](value, row)

                if result == "correct":
                    css_class = "correct"
                elif result == "wrong":
                    css_class = "wrong"
                elif result == "lower":
                    css_class = "lower"

            html += f'<td class="{css_class}">{value}</td>'

        html += "</tr>\n"

    html += "</table></body></html>"

    # Save
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"Saved to {output_file}")
