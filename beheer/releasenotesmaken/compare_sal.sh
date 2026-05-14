#!/usr/bin/env bash
set -euo pipefail

V50_HASH="C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCS/sal_v50_hashes.txt"
V52_HASH="C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCS/sal_v52_hashes.txt"
V50_DIR="C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCSmain/NLCS/symbolen/autocad/SAL"
V52_DIR="C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCS/symbolen/autocad/SAL"
OUT="C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCS/vergelijking_SAL_5.0_vs_5.2.html"

declare -A v50 v52
declare -A v50_size v52_size

# sha256sum format: "<hash> *<filename>" (binary mode prefixes filename with *)
while IFS= read -r line; do
    hash="${line%% *}"
    name="${line#* }"
    name="${name#\*}"
    v50["$name"]="$hash"
done < "$V50_HASH"

while IFS= read -r line; do
    hash="${line%% *}"
    name="${line#* }"
    name="${name#\*}"
    v52["$name"]="$hash"
done < "$V52_HASH"

# Collect file sizes
while IFS= read -r f; do
    bn=$(basename "$f")
    v50_size["$bn"]=$(stat -c %s "$f" 2>/dev/null || echo 0)
done < <(find "$V50_DIR" -maxdepth 1 -name "*.dwg" -type f)

while IFS= read -r f; do
    bn=$(basename "$f")
    v52_size["$bn"]=$(stat -c %s "$f" 2>/dev/null || echo 0)
done < <(find "$V52_DIR" -maxdepth 1 -name "*.dwg" -type f)

# Build sorted name lists
mapfile -t v50_names < <(printf '%s\n' "${!v50[@]}" | sort)
mapfile -t v52_names < <(printf '%s\n' "${!v52[@]}" | sort)

nieuw=()
vervallen=()
gewijzigd=()
gelijk=()

for n in "${v52_names[@]}"; do
    if [[ -z "${v50[$n]+x}" ]]; then
        nieuw+=("$n")
    elif [[ "${v50[$n]}" != "${v52[$n]}" ]]; then
        gewijzigd+=("$n")
    else
        gelijk+=("$n")
    fi
done

for n in "${v50_names[@]}"; do
    if [[ -z "${v52[$n]+x}" ]]; then
        vervallen+=("$n")
    fi
done

human_size() {
    local b="${1:-0}"
    if [[ -z "$b" ]] || [[ "$b" == "0" ]]; then echo "0 B"; return; fi
    awk -v b="$b" 'BEGIN {
        if (b < 1024) printf "%d B", b;
        else if (b < 1048576) printf "%.1f KB", b/1024;
        else printf "%.2f MB", b/1048576;
    }'
}

# Generate HTML
{
cat <<'HTML_HEAD'
<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<title>Vergelijking SAL — v5.0 vs v5.2</title>
<style>
  :root { font-family: -apple-system, Segoe UI, Roboto, sans-serif; }
  body { max-width: 1200px; margin: 2em auto; padding: 0 1em; color: #222; }
  h1 { border-bottom: 2px solid #333; padding-bottom: .3em; }
  h2 { margin-top: 2em; padding: .4em .6em; border-radius: 4px; color: #fff; }
  h2.nieuw { background: #2e7d32; }
  h2.vervallen { background: #c62828; }
  h2.gewijzigd { background: #ef6c00; }
  h2.gelijk { background: #1565c0; }
  .summary { background: #f5f5f5; padding: 1em; border-radius: 6px; margin: 1em 0; }
  .summary table { border: 0; }
  .summary td { border: 0; padding: .2em 1em .2em 0; }
  table { border-collapse: collapse; width: 100%; font-size: 13px; }
  th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; }
  th { background: #fafafa; font-weight: 600; }
  tr:nth-child(even) { background: #fcfcfc; }
  .hash { font-family: Consolas, monospace; font-size: 11px; color: #555; }
  .size { text-align: right; white-space: nowrap; }
  .note { background: #fff8e1; border-left: 4px solid #ffa000; padding: .8em 1em; margin: 1em 0; font-size: 13px; }
  .empty { color: #999; font-style: italic; padding: 1em; }
  details summary { cursor: pointer; padding: .5em; background: #f0f0f0; border-radius: 4px; user-select: none; }
  details[open] summary { margin-bottom: .5em; }
</style>
</head>
<body>
<h1>Vergelijking SAL-symbolen — NLCS 5.0 vs 5.2</h1>
HTML_HEAD

echo "<div class='summary'>"
echo "<strong>Bronmappen</strong>"
echo "<table>"
echo "<tr><td>v5.0:</td><td><code>$V50_DIR</code></td><td>${#v50_names[@]} DWG-bestanden</td></tr>"
echo "<tr><td>v5.2:</td><td><code>$V52_DIR</code></td><td>${#v52_names[@]} DWG-bestanden</td></tr>"
echo "</table>"
echo "<br><strong>Resultaten</strong>"
echo "<table>"
echo "<tr><td>Nieuw (alleen in 5.2):</td><td><strong>${#nieuw[@]}</strong></td></tr>"
echo "<tr><td>Vervallen (alleen in 5.0):</td><td><strong>${#vervallen[@]}</strong></td></tr>"
echo "<tr><td>Gewijzigd (zelfde naam, andere inhoud):</td><td><strong>${#gewijzigd[@]}</strong></td></tr>"
echo "<tr><td>Gelijk gebleven (zelfde naam, identieke inhoud):</td><td><strong>${#gelijk[@]}</strong></td></tr>"
echo "</table>"
echo "<p style='margin-top:1em; font-size:12px; color:#666;'>Gegenereerd: $(date '+%Y-%m-%d %H:%M')</p>"
echo "</div>"

cat <<'HTML_NOTE'
<div class="note">
<strong>Let op:</strong> de vergelijking is gebaseerd op een SHA256-hash van de volledige DWG-bytes.
DWG-bestanden bevatten een ingebedde "last saved"-tijdstempel en metadata; als iemand een bestand
alleen opent en opnieuw opslaat (zonder de tekening te wijzigen) verandert de hash en verschijnt
het hier als "gewijzigd". Voor zekerheid over de geometrie zou je elk gewijzigd bestand visueel in
AutoCAD moeten openen.
</div>
HTML_NOTE

emit_table() {
    local title="$1" cls="$2" show_compare="$3"
    shift 3
    local arr=("$@")
    echo "<h2 class='$cls'>$title (${#arr[@]})</h2>"
    if [[ ${#arr[@]} -eq 0 ]]; then
        echo "<p class='empty'>Geen bestanden in deze categorie.</p>"
        return
    fi
    echo "<table>"
    if [[ "$show_compare" == "compare" ]]; then
        echo "<tr><th>Bestandsnaam</th><th class='size'>Grootte 5.0</th><th class='size'>Grootte 5.2</th><th>Hash 5.0</th><th>Hash 5.2</th></tr>"
    elif [[ "$show_compare" == "v50only" ]]; then
        echo "<tr><th>Bestandsnaam</th><th class='size'>Grootte</th><th>SHA256</th></tr>"
    elif [[ "$show_compare" == "v52only" ]]; then
        echo "<tr><th>Bestandsnaam</th><th class='size'>Grootte</th><th>SHA256</th></tr>"
    else
        echo "<tr><th>Bestandsnaam</th><th class='size'>Grootte</th><th>SHA256</th></tr>"
    fi
    for n in "${arr[@]}"; do
        if [[ "$show_compare" == "compare" ]]; then
            local s50="$(human_size "${v50_size[$n]:-0}")"
            local s52="$(human_size "${v52_size[$n]:-0}")"
            local h50="${v50[$n]:0:16}…"
            local h52="${v52[$n]:0:16}…"
            echo "<tr><td>$n</td><td class='size'>$s50</td><td class='size'>$s52</td><td class='hash' title='${v50[$n]}'>$h50</td><td class='hash' title='${v52[$n]}'>$h52</td></tr>"
        elif [[ "$show_compare" == "v50only" ]]; then
            local s="$(human_size "${v50_size[$n]:-0}")"
            echo "<tr><td>$n</td><td class='size'>$s</td><td class='hash'>${v50[$n]}</td></tr>"
        elif [[ "$show_compare" == "v52only" ]]; then
            local s="$(human_size "${v52_size[$n]:-0}")"
            echo "<tr><td>$n</td><td class='size'>$s</td><td class='hash'>${v52[$n]}</td></tr>"
        else
            local s="$(human_size "${v52_size[$n]:-0}")"
            echo "<tr><td>$n</td><td class='size'>$s</td><td class='hash'>${v52[$n]}</td></tr>"
        fi
    done
    echo "</table>"
}

emit_table "Nieuw" "nieuw" "v52only" "${nieuw[@]}"
emit_table "Vervallen" "vervallen" "v50only" "${vervallen[@]}"
emit_table "Gewijzigd" "gewijzigd" "compare" "${gewijzigd[@]}"

# Gelijk-gebleven in a collapsed details (often the largest table)
echo "<h2 class='gelijk'>Gelijk gebleven (${#gelijk[@]})</h2>"
if [[ ${#gelijk[@]} -eq 0 ]]; then
    echo "<p class='empty'>Geen bestanden in deze categorie.</p>"
else
    echo "<details><summary>Klik om de ${#gelijk[@]} ongewijzigde bestanden te tonen</summary>"
    echo "<table>"
    echo "<tr><th>Bestandsnaam</th><th class='size'>Grootte</th><th>SHA256</th></tr>"
    for n in "${gelijk[@]}"; do
        s="$(human_size "${v52_size[$n]:-0}")"
        echo "<tr><td>$n</td><td class='size'>$s</td><td class='hash'>${v52[$n]}</td></tr>"
    done
    echo "</table>"
    echo "</details>"
fi

echo "</body></html>"
} > "$OUT"

echo "HTML geschreven naar: $OUT"
echo ""
echo "Samenvatting:"
echo "  Nieuw:           ${#nieuw[@]}"
echo "  Vervallen:       ${#vervallen[@]}"
echo "  Gewijzigd:       ${#gewijzigd[@]}"
echo "  Gelijk gebleven: ${#gelijk[@]}"
