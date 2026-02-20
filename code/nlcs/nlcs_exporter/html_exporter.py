import csv
from io import StringIO
import pandas as pd

# For attributes to check if they are filled
attribute_columns = [
"lw_b","kl_b","kl_b_a","kl_b_gd","kl_b_gn","kl_b_v","lt_b",
"lw_n","kl_n","kl_n_a","kl_n_gd","kl_n_gn","kl_n_v","lt_n",
"lw_v","kl_v","kl_v_a","kl_v_gd","kl_v_gn","kl_v_v","lt_v",
"lw_t","kl_t","kl_t_a","kl_t_gd","kl_t_gn","kl_t_v","lt_t",
"id_nummer"
]

def is_bound(value, row):
    if value is None or value.strip() == "":
        return "wrong"   
    return "correct"


# For colors to check if they are either RGB or one of the predefined values
non_v_colors = [
"kl_b","kl_b_a","kl_b_gd","kl_b_gn",
"kl_n","kl_n_a","kl_n_gd","kl_n_gn",
"kl_v","kl_v_a","kl_v_gd","kl_v_gn",
"kl_t","kl_t_a","kl_t_gd","kl_t_gn",
]

def is_bound_and_not_RGB(value, row):
    if value is None or value.strip() == "":
        return "wrong"   
    elif "," in value:
        return "wrong"
    else:
        return "correct"



columns_to_validate = [
"omschrijving","status","discipline","hoofdgroep",
"object","subobject01","subobject02","subobject03",
"subobject04","subobject05","bewerking",
"schaal","laagnaam",
"vrkl_kort","vrkl_lang","id_nummer","kind_van"
]

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
            if row.get("bewerking", "") != parts[-1]:
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


# For object label
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


# For line types to check if they have correct status and companions based on issue #790
linetype_df = pd.read_csv("./tabellen/controles/controle_lijntypes_extensive-concept-5.1.csv")

LINETYPE_RULES = {
    r["object"]: {
        "lt_b": r["line_type_b"],
        "lt_n": r["line_type_n"],
        "lt_t": r["line_type_t"],
        "lt_v": r["line_type_v"],
    }
    for _, r in linetype_df.iterrows()
}

def is_linetype_correct(value, row, column_name):
    obj = row.get("objectURI")

    # If object not in rules → ignore
    if obj not in LINETYPE_RULES:
        return "correct"
    
    expected = LINETYPE_RULES[obj].get(column_name)
    if pd.isna(expected) or expected is None or str(expected).strip() == "":
        return "wrong"
    
    # Normalize values
    val = str(value).strip()
    exp = str(expected).strip()

    if val == exp:
        return "correct"
    else:
        return "wrong"

linetype_columns = [ "lt_b", "lt_n", "lt_v", "lt_t"]
linetype_rule_wrappers = {
    col: (lambda c: lambda v, r: is_linetype_correct(v, r, c))(col)
    for col in linetype_columns
}  


# Combine all rules here
COLUMN_RULES = {col: is_bound for col in attribute_columns} | {col: is_bound_and_not_RGB for col in non_v_colors} | {col: is_valid_string for col in columns_to_validate} | {"omschrijving" : is_label_reused}
COLUMN_RULES |= linetype_rule_wrappers

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
