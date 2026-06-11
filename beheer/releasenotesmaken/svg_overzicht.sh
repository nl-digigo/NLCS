#!/usr/bin/env bash
#
# Genereert een HTML-overzichtspagina van alle SVG-bestanden in een map.
# De pagina is een 2-koloms tabel: bestandsnaam | gerenderde SVG.
#
# Output: <svg-map>/overzicht.html  (relatieve paden naar de SVGs)
#
# Gebruik:
#   bash svg_overzicht.sh <svg-map> [<titel>]
#
# Voorbeelden:
#   bash svg_overzicht.sh "C:/.../symbolen/5.2/svg/SAL"
#   bash svg_overzicht.sh "C:/.../symbolen/5.2/svg/SAL" "SAL — Aankleding"

set -uo pipefail

if [[ $# -lt 1 ]]; then
    echo "Gebruik: bash $0 <svg-map> [<titel>]" >&2
    exit 1
fi

SVG_DIR="$1"

[[ -d "$SVG_DIR" ]] || { echo "Map niet gevonden: $SVG_DIR" >&2; exit 1; }

# Bepaal titel: gebruik 2e argument indien gegeven, anders zoek de hoofdgroep-
# omschrijving op in de NLCS hoofdgroepen-CSV (canonieke bron, zie memory).
HG_CSV="C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCS/tabellen/publicatie/NLCS_Query_Hoofdgroepen-concept-5.2.csv"
folder_name="$(basename "$SVG_DIR")"
if [[ $# -ge 2 ]]; then
    TITLE="$2"
elif [[ "$folder_name" =~ ^S([A-Z]{2})$ ]] && [[ -f "$HG_CSV" ]]; then
    afk="${BASH_REMATCH[1]}"
    # CSV-formaat: hoofdgroepURI,id,hoofdgroep,afkorting
    hg_name=$(awk -F, -v code="$afk" '$4 == code { print $3; exit }' "$HG_CSV")
    if [[ -n "$hg_name" ]]; then
        TITLE="${folder_name} — ${hg_name} (NLCS 5.2)"
    else
        TITLE="${folder_name} — SVG-overzicht NLCS 5.2"
    fi
else
    TITLE="${folder_name} — SVG-overzicht"
fi

OUT="$SVG_DIR/overzicht.html"
count=$(find "$SVG_DIR" -maxdepth 1 -name "*.svg" -type f ! -name "overzicht.html" | wc -l)

if (( count == 0 )); then
    echo "Geen SVG-bestanden gevonden in: $SVG_DIR" >&2
    exit 1
fi

{
cat <<HEAD
<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<title>${TITLE}</title>
<style>
  body { font-family: -apple-system, Segoe UI, Roboto, sans-serif; margin: 2em; color: #222; }
  h1 { border-bottom: 2px solid #333; padding-bottom: .3em; }
  .info { color: #666; font-size: 14px; margin-bottom: 1.5em; }
  table { border-collapse: collapse; width: 100%; }
  th, td { border: 1px solid #ddd; padding: 10px 14px; text-align: left; vertical-align: middle; }
  th { background: #003865; color: white; }
  tr:nth-child(even) td { background: #fafafa; }
  td.name { font-family: Consolas, monospace; font-size: 13px; width: 50%; word-break: break-all; }
  td.svg { text-align: center; background: #fff !important; }
  td.svg img { max-width: 100%; max-height: 200px; min-width: 40px; min-height: 40px; }
</style>
</head>
<body>
<h1>${TITLE}</h1>
<p class="info">${count} symbolen — gegenereerd $(date '+%Y-%m-%d %H:%M')</p>
<table>
<thead><tr><th>Symboolnaam</th><th>SVG</th></tr></thead>
<tbody>
HEAD

    # Lijst SVGs (skip overzicht.html zelf indien het *.svg zou heten — voor de zekerheid)
    find "$SVG_DIR" -maxdepth 1 -name "*.svg" -type f -printf '%f\n' | sort | while IFS= read -r name; do
        safe=$(printf '%s' "$name" | sed 's/&/\&amp;/g; s/</\&lt;/g; s/"/\&quot;/g')
        printf '  <tr><td class="name">%s</td><td class="svg"><img src="%s" alt="%s"></td></tr>\n' \
            "$safe" "$safe" "$safe"
    done

    cat <<'TAIL'
</tbody></table>
</body></html>
TAIL
} > "$OUT"

echo "geschreven: $OUT"
echo "rijen:      ${count} symbolen"
