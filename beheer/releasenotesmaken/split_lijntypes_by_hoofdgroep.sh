#!/usr/bin/env bash
#
# Splitst NLCS_Query_Lijntypes-concept-5.2.html op naar één HTML per
# hoofdgroep, met vier secties: nieuw / vervallen / gewijzigd / bestaande.
# Bron-rijopmaak (class="new-row", class="deleted", class="changed" cellen)
# wordt behouden.
#
# Per hoofdgroep XX wordt geschreven naar:
#   docs/changelog/XX/vergelijking_lijntypes_XX_5.0_vs_5.2.html
#
# Gebruik:   bash split_lijntypes_by_hoofdgroep.sh

set -uo pipefail

SRC="C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCS/docs/changelog/NLCS_Query_Lijntypes-concept-5.2.html"
OUT_BASE="C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCS/docs/changelog"

[[ -f "$SRC" ]] || { echo "Bron niet gevonden: $SRC" >&2; exit 1; }

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

# Per categorie + hoofdgroep produceren we een bestand met de rauwe rijregels.
# awk leest alle <tr>...</tr>-regels en classificeert ze, dan schrijft hij naar
# $TMP_DIR/rows_<categorie>_<hoofdgroep>.html
# Daarnaast schrijft hij $TMP_DIR/hoofdgroepen.txt met alle voorkomende codes.

awk -v tmp="$TMP_DIR" '
function trim(s) { sub(/^[[:space:]]+/, "", s); sub(/[[:space:]]+$/, "", s); return s }

# Extract effective v5.2 hoofdgroep from cell HTML.
# Either plain "<td>XX</td>" or "<td class=\"changed\"><div class=\"old-val\">...</div><div class=\"new-val\">5.2&#58; XX</div></td>"
function extract_hoofdgroep(cell,    out) {
    if (match(cell, /<div class="new-val">5\.2&#58;[[:space:]]*[^<]*<\/div>/)) {
        out = substr(cell, RSTART, RLENGTH)
        sub(/^<div class="new-val">5\.2&#58;[[:space:]]*/, "", out)
        sub(/<\/div>$/, "", out)
        return trim(out)
    }
    # Plain cell: take inner text between first "<td...>" and end
    out = cell
    sub(/^<td[^>]*>/, "", out)
    return trim(out)
}

# Split a <tr>...</tr> line into cells by "</td>" delimiter.
# Returns the n-th cell (with its opening <td...> still present).
function get_cell(line, n,   parts, count) {
    count = split(line, parts, /<\/td>/)
    if (n > count) return ""
    return parts[n]
}

/<tr/ {
    line = $0

    # Determine row category
    cat = ""
    if (line ~ /class="section-header"/) next
    else if (line ~ /<tr[^>]*class="new-row"/) cat = "nieuw"
    else if (line ~ /<tr[^>]*class="deleted"/) cat = "vervallen"
    else if (line ~ /class="changed"/) cat = "gewijzigd"
    else cat = "bestaande"

    # Extract hoofdgroep (3rd cell)
    hg_cell = get_cell(line, 3)
    if (hg_cell == "") next
    hg = extract_hoofdgroep(hg_cell)
    if (hg == "") next   # skip rows without hoofdgroep (CONTINUOUS, BYLAYER, ...)
    if (hg !~ /^[A-Z]{2}$/) next   # only accept clean 2-letter codes

    out_file = tmp "/rows_" cat "_" hg ".html"
    print line >> out_file
    seen[hg] = 1
}

END {
    out = tmp "/hoofdgroepen.txt"
    for (h in seen) print h | "sort > " out
    close("sort > " out)
}
' "$SRC"

mapfile -t HOOFDGROEPEN < "$TMP_DIR/hoofdgroepen.txt"
echo "Gevonden hoofdgroepen (${#HOOFDGROEPEN[@]}): ${HOOFDGROEPEN[*]}"
echo ""

# Helper: count lines in file (0 if missing)
count_rows() {
    local f="$1"
    if [[ -f "$f" ]]; then wc -l < "$f" | tr -d ' '; else echo 0; fi
}

# Emit table section
emit_section() {
    local title="$1" cls="$2" rows_file="$3" details="$4"
    local count
    count=$(count_rows "$rows_file")

    echo "<h2 class='${cls}'>${title} (${count})</h2>"
    if (( count == 0 )); then
        echo "<p class='empty'>Geen lijntypes in deze categorie.</p>"
        return
    fi
    if [[ "$details" == "yes" ]]; then
        echo "<details><summary>Klik om de ${count} rijen te tonen</summary>"
    fi
    cat <<TABLE_HEAD
<table>
  <thead><tr><th>lijntypeURI</th><th>id</th><th>hoofdgroep</th><th>omschrijving</th><th>finalCleanName</th><th>fase</th><th>optie</th><th>autocaddef</th></tr></thead>
  <tbody>
TABLE_HEAD
    cat "$rows_file"
    echo "  </tbody>"
    echo "</table>"
    if [[ "$details" == "yes" ]]; then
        echo "</details>"
    fi
}

for hg in "${HOOFDGROEPEN[@]}"; do
    out_dir="$OUT_BASE/$hg"
    mkdir -p "$out_dir"
    out_html="$out_dir/vergelijking_lijntypes_${hg}_5.0_vs_5.2.html"

    rows_nieuw="$TMP_DIR/rows_nieuw_${hg}.html"
    rows_vervallen="$TMP_DIR/rows_vervallen_${hg}.html"
    rows_gewijzigd="$TMP_DIR/rows_gewijzigd_${hg}.html"
    rows_bestaande="$TMP_DIR/rows_bestaande_${hg}.html"

    count_n=$(count_rows "$rows_nieuw")
    count_v=$(count_rows "$rows_vervallen")
    count_w=$(count_rows "$rows_gewijzigd")
    count_b=$(count_rows "$rows_bestaande")

    {
cat <<HTML_HEAD
<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<title>Vergelijking lijntypes ${hg} — NLCS 5.0.2 vs 5.2</title>
<style>
  :root { font-family: -apple-system, Segoe UI, Roboto, sans-serif; }
  body { max-width: 1400px; margin: 2em auto; padding: 0 1em; color: #222; font-size: 13px; }
  h1 { border-bottom: 2px solid #333; padding-bottom: .3em; }
  h2 { margin-top: 2em; padding: .4em .6em; border-radius: 4px; color: #fff; }
  h2.nieuw { background: #2e7d32; }
  h2.vervallen { background: #c62828; }
  h2.gewijzigd { background: #ef6c00; }
  h2.bestaande { background: #1565c0; }
  .summary { background: #f5f5f5; padding: 1em; border-radius: 6px; margin: 1em 0; }
  .summary table { border: 0; width: auto; }
  .summary td { border: 0; padding: .2em 1em .2em 0; }
  table { border-collapse: collapse; width: 100%; }
  th { background-color: #003865; color: white; text-align: left; padding: 6px 8px; white-space: nowrap; }
  td { border: 1px solid #ccc; padding: 4px 8px; vertical-align: top; }
  tbody tr:nth-child(even) td { background-color: #f2f2f2; }
  tbody tr:hover td { background-color: #dde8f0; }
  .new-row td    { background-color: #d4edda !important; }
  .new-row:hover td { background-color: #b8dfc4 !important; }
  .changed       { background-color: #cce5ff !important; }
  .old-val { color: #555; font-size: 0.85em; }
  .new-val { font-weight: normal; }
  .deleted td    { background-color: #d0d0d0 !important; }
  .deleted:hover td { background-color: #b8b8b8 !important; }
  .empty { color: #999; font-style: italic; padding: 1em; }
  details summary { cursor: pointer; padding: .5em; background: #f0f0f0; border-radius: 4px; user-select: none; }
  details[open] summary { margin-bottom: .5em; }
  .legend { margin: .5em 0 1em; font-size: 12px; display:flex; gap:12px; flex-wrap:wrap; }
  .legend span { padding: 2px 8px; border-radius: 3px; border: 1px solid #ccc; }
</style>
</head>
<body>
<h1>Vergelijking lijntypes — hoofdgroep ${hg}</h1>
<div class="summary">
<strong>Bron</strong>
<table>
<tr><td>Bestand:</td><td><code>NLCS_Query_Lijntypes-concept-5.2.html</code></td></tr>
<tr><td>Versies:</td><td>NLCS 5.0.2 → 5.2</td></tr>
</table>
<br><strong>Resultaten voor hoofdgroep ${hg}</strong>
<table>
<tr><td>Nieuw (alleen in 5.2):</td><td><strong>${count_n}</strong></td></tr>
<tr><td>Vervallen (alleen in 5.0.2):</td><td><strong>${count_v}</strong></td></tr>
<tr><td>Gewijzigd (zelfde URI of id, andere waarden):</td><td><strong>${count_w}</strong></td></tr>
<tr><td>Bestaande (ongewijzigd):</td><td><strong>${count_b}</strong></td></tr>
</table>
<p style='margin-top:1em; font-size:12px; color:#666;'>Gegenereerd: $(date '+%Y-%m-%d %H:%M')</p>
</div>
<div class="legend">
  <span style="background:#d4edda;">Nieuwe rij</span>
  <span style="background:#cce5ff;">Gewijzigde cel (oude → nieuwe waarde)</span>
  <span style="background:#d0d0d0;">Vervallen rij</span>
</div>
HTML_HEAD

        emit_section "Nieuw" "nieuw" "$rows_nieuw" "no"
        emit_section "Vervallen" "vervallen" "$rows_vervallen" "no"
        emit_section "Gewijzigd" "gewijzigd" "$rows_gewijzigd" "no"
        emit_section "Bestaande" "bestaande" "$rows_bestaande" "yes"

        echo "</body></html>"
    } > "$out_html"

    printf '%-3s  nieuw=%-3d  vervallen=%-3d  gewijzigd=%-3d  bestaande=%-4d → %s\n' \
        "$hg" "$count_n" "$count_v" "$count_w" "$count_b" "$out_html"
done

echo ""
echo "Klaar. Tussenbestanden zijn verwijderd."
