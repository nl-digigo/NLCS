#!/usr/bin/env bash
#
# Vergelijkt alle symbool-bibliotheken (S* mappen) tussen NLCS v5.0 en v5.2
# en genereert per bibliotheek een HTML-changelog met 4 tabellen:
# nieuw / vervallen / gewijzigd / gelijk gebleven.
#
# Vergelijking gebeurt op basis van SHA256-hashes van de DWG-bytes.
# Tussenbestanden (hash-lijsten) worden na afloop opgeruimd.
#
# Gebruik:   bash compare_libraries.sh

set -uo pipefail

V50_BASE="C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCSmain/NLCS/symbolen/autocad"
V52_BASE="C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCS/symbolen/autocad"
OUT_BASE="C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCS/docs/changelog"

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

human_size() {
    local b="${1:-0}"
    if [[ -z "$b" ]] || [[ "$b" == "0" ]]; then echo "0 B"; return; fi
    awk -v b="$b" 'BEGIN {
        if (b < 1024) printf "%d B", b;
        else if (b < 1048576) printf "%.1f KB", b/1024;
        else printf "%.2f MB", b/1048576;
    }'
}

# Compute hashes (filename<TAB>sha256) for *.dwg in directory.
# Output sorted by filename. Empty if directory missing or no dwg files.
make_hash_list() {
    local dir="$1" out="$2"
    : > "$out"
    [[ -d "$dir" ]] || return 0
    ( cd "$dir" && \
        for f in *.dwg; do
            [[ -e "$f" ]] || continue
            local h
            h=$(sha256sum -- "$f" | awk '{print $1}')
            printf '%s\t%s\n' "$f" "$h"
        done | sort > "$out"
    )
}

# Compute filename<TAB>size for *.dwg
make_size_list() {
    local dir="$1" out="$2"
    : > "$out"
    [[ -d "$dir" ]] || return 0
    ( cd "$dir" && \
        for f in *.dwg; do
            [[ -e "$f" ]] || continue
            local s
            s=$(stat -c %s -- "$f" 2>/dev/null || echo 0)
            printf '%s\t%s\n' "$f" "$s"
        done > "$out"
    )
}

emit_html() {
    local lib="$1" v50_dir="$2" v52_dir="$3" out="$4"

    local hash_v50="$TMP_DIR/${lib}_v50_hash.tsv"
    local hash_v52="$TMP_DIR/${lib}_v52_hash.tsv"
    local size_v50="$TMP_DIR/${lib}_v50_size.tsv"
    local size_v52="$TMP_DIR/${lib}_v52_size.tsv"

    make_hash_list "$v50_dir" "$hash_v50"
    make_hash_list "$v52_dir" "$hash_v52"
    make_size_list "$v50_dir" "$size_v50"
    make_size_list "$v52_dir" "$size_v52"

    # Use awk to compute categories.
    # Output: 4 files: nieuw.txt, vervallen.txt, gewijzigd.txt, gelijk.txt
    # Each contains filenames (one per line) sorted.
    local nieuw_f="$TMP_DIR/${lib}_nieuw.txt"
    local vervallen_f="$TMP_DIR/${lib}_vervallen.txt"
    local gewijzigd_f="$TMP_DIR/${lib}_gewijzigd.txt"
    local gelijk_f="$TMP_DIR/${lib}_gelijk.txt"

    # Use ARGIND (gawk) to distinguish files — NOT FNR==NR, because that fails
    # when the first file is empty (NR never advances past FNR for the 2nd file).
    awk -F'\t' -v out_nieuw="$nieuw_f" -v out_vervallen="$vervallen_f" \
              -v out_gewijzigd="$gewijzigd_f" -v out_gelijk="$gelijk_f" '
        ARGIND==1 { v50[$1]=$2; next }
        ARGIND==2 { v52[$1]=$2; next }
        END {
            for (f in v52) {
                if (!(f in v50)) print f >> out_nieuw
                else if (v50[f] != v52[f]) print f >> out_gewijzigd
                else print f >> out_gelijk
            }
            for (f in v50) {
                if (!(f in v52)) print f >> out_vervallen
            }
        }
    ' "$hash_v50" "$hash_v52"

    # Ensure files exist (awk only creates them when there is output)
    : > "${nieuw_f}.sorted"
    : > "${vervallen_f}.sorted"
    : > "${gewijzigd_f}.sorted"
    : > "${gelijk_f}.sorted"
    [[ -f "$nieuw_f" ]] && sort "$nieuw_f" > "${nieuw_f}.sorted"
    [[ -f "$vervallen_f" ]] && sort "$vervallen_f" > "${vervallen_f}.sorted"
    [[ -f "$gewijzigd_f" ]] && sort "$gewijzigd_f" > "${gewijzigd_f}.sorted"
    [[ -f "$gelijk_f" ]] && sort "$gelijk_f" > "${gelijk_f}.sorted"

    local count_v50 count_v52 count_nieuw count_vervallen count_gewijzigd count_gelijk
    count_v50=$(wc -l < "$hash_v50" | tr -d ' ')
    count_v52=$(wc -l < "$hash_v52" | tr -d ' ')
    count_nieuw=$(wc -l < "${nieuw_f}.sorted" | tr -d ' ')
    count_vervallen=$(wc -l < "${vervallen_f}.sorted" | tr -d ' ')
    count_gewijzigd=$(wc -l < "${gewijzigd_f}.sorted" | tr -d ' ')
    count_gelijk=$(wc -l < "${gelijk_f}.sorted" | tr -d ' ')

    # Build lookups for hash and size as TSV files
    # When emitting rows we'll use awk per row, but easier: join on filename.

    {
cat <<HTML_HEAD
<!DOCTYPE html>
<html lang="nl">
<head>
<meta charset="UTF-8">
<title>Vergelijking ${lib} — NLCS 5.0 vs 5.2</title>
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
  th, td { border: 1px solid #ddd; padding: 6px 10px; text-align: left; vertical-align: top; }
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
<h1>Vergelijking ${lib} — NLCS 5.0 vs 5.2</h1>
HTML_HEAD

        echo "<div class='summary'>"
        echo "<strong>Bronmappen</strong>"
        echo "<table>"
        if [[ -d "$v50_dir" ]]; then
            echo "<tr><td>v5.0:</td><td><code>${v50_dir}</code></td><td>${count_v50} DWG-bestanden</td></tr>"
        else
            echo "<tr><td>v5.0:</td><td colspan='2'><em>bibliotheek niet aanwezig in v5.0 — alle bestanden zijn nieuw</em></td></tr>"
        fi
        if [[ -d "$v52_dir" ]]; then
            echo "<tr><td>v5.2:</td><td><code>${v52_dir}</code></td><td>${count_v52} DWG-bestanden</td></tr>"
        else
            echo "<tr><td>v5.2:</td><td colspan='2'><em>bibliotheek niet aanwezig in v5.2 — alle bestanden zijn vervallen</em></td></tr>"
        fi
        echo "</table>"
        echo "<br><strong>Resultaten</strong>"
        echo "<table>"
        echo "<tr><td>Nieuw (alleen in 5.2):</td><td><strong>${count_nieuw}</strong></td></tr>"
        echo "<tr><td>Vervallen (alleen in 5.0):</td><td><strong>${count_vervallen}</strong></td></tr>"
        echo "<tr><td>Gewijzigd (zelfde naam, andere inhoud):</td><td><strong>${count_gewijzigd}</strong></td></tr>"
        echo "<tr><td>Gelijk gebleven (zelfde naam, identieke inhoud):</td><td><strong>${count_gelijk}</strong></td></tr>"
        echo "</table>"
        echo "<p style='margin-top:1em; font-size:12px; color:#666;'>Gegenereerd: $(date '+%Y-%m-%d %H:%M')</p>"
        echo "</div>"

cat <<'HTML_NOTE'
<div class="note">
<strong>Let op:</strong> de vergelijking is gebaseerd op een SHA256-hash van de volledige DWG-bytes.
DWG-bestanden bevatten een ingebedde "last saved"-tijdstempel en metadata; als iemand een bestand
alleen opent en opnieuw opslaat (zonder de tekening te wijzigen) verandert de hash en verschijnt
het hier als "gewijzigd". Een gewone Windows-kopie verandert de hash niet. Voor zekerheid over
geometrische wijzigingen moet elk "gewijzigd" bestand visueel in AutoCAD worden gecontroleerd, of
eerst geconverteerd naar DXF (tekstueel) zodat metadata-regels uitgefilterd kunnen worden.
</div>
HTML_NOTE

        # --- Nieuw ---
        echo "<h2 class='nieuw'>Nieuw (${count_nieuw})</h2>"
        if (( count_nieuw == 0 )); then
            echo "<p class='empty'>Geen bestanden in deze categorie.</p>"
        else
            echo "<table>"
            echo "<tr><th>Bestandsnaam</th><th class='size'>Grootte</th><th>SHA256</th></tr>"
            # Join filenames with hash_v52 and size_v52
            join -t $'\t' "${nieuw_f}.sorted" "$hash_v52" 2>/dev/null \
                | join -t $'\t' - "$size_v52" 2>/dev/null \
                | while IFS=$'\t' read -r name hash size; do
                    local s; s="$(human_size "$size")"
                    echo "<tr><td>${name}</td><td class='size'>${s}</td><td class='hash'>${hash}</td></tr>"
                done
            echo "</table>"
        fi

        # --- Vervallen ---
        echo "<h2 class='vervallen'>Vervallen (${count_vervallen})</h2>"
        if (( count_vervallen == 0 )); then
            echo "<p class='empty'>Geen bestanden in deze categorie.</p>"
        else
            echo "<table>"
            echo "<tr><th>Bestandsnaam</th><th class='size'>Grootte</th><th>SHA256</th></tr>"
            join -t $'\t' "${vervallen_f}.sorted" "$hash_v50" 2>/dev/null \
                | join -t $'\t' - "$size_v50" 2>/dev/null \
                | while IFS=$'\t' read -r name hash size; do
                    local s; s="$(human_size "$size")"
                    echo "<tr><td>${name}</td><td class='size'>${s}</td><td class='hash'>${hash}</td></tr>"
                done
            echo "</table>"
        fi

        # --- Gewijzigd ---
        echo "<h2 class='gewijzigd'>Gewijzigd (${count_gewijzigd})</h2>"
        if (( count_gewijzigd == 0 )); then
            echo "<p class='empty'>Geen bestanden in deze categorie.</p>"
        else
            echo "<table>"
            echo "<tr><th>Bestandsnaam</th><th class='size'>Grootte 5.0</th><th class='size'>Grootte 5.2</th><th>Hash 5.0</th><th>Hash 5.2</th></tr>"
            # Join: filenames+hash50+size50+hash52+size52
            # First: filename TAB hash50
            join -t $'\t' "${gewijzigd_f}.sorted" "$hash_v50" 2>/dev/null > "$TMP_DIR/_g1.tsv"
            # Then: + size50
            join -t $'\t' "$TMP_DIR/_g1.tsv" "$size_v50" 2>/dev/null > "$TMP_DIR/_g2.tsv"
            # Then: + hash52
            join -t $'\t' "$TMP_DIR/_g2.tsv" "$hash_v52" 2>/dev/null > "$TMP_DIR/_g3.tsv"
            # Then: + size52
            join -t $'\t' "$TMP_DIR/_g3.tsv" "$size_v52" 2>/dev/null > "$TMP_DIR/_g4.tsv"
            while IFS=$'\t' read -r name h50 s50 h52 s52; do
                local hs50 hs52
                hs50="$(human_size "$s50")"
                hs52="$(human_size "$s52")"
                local h50_short="${h50:0:16}…"
                local h52_short="${h52:0:16}…"
                echo "<tr><td>${name}</td><td class='size'>${hs50}</td><td class='size'>${hs52}</td><td class='hash' title='${h50}'>${h50_short}</td><td class='hash' title='${h52}'>${h52_short}</td></tr>"
            done < "$TMP_DIR/_g4.tsv"
            echo "</table>"
        fi

        # --- Gelijk gebleven ---
        echo "<h2 class='gelijk'>Gelijk gebleven (${count_gelijk})</h2>"
        if (( count_gelijk == 0 )); then
            echo "<p class='empty'>Geen bestanden in deze categorie.</p>"
        else
            echo "<details><summary>Klik om de ${count_gelijk} ongewijzigde bestanden te tonen</summary>"
            echo "<table>"
            echo "<tr><th>Bestandsnaam</th><th class='size'>Grootte</th><th>SHA256</th></tr>"
            join -t $'\t' "${gelijk_f}.sorted" "$hash_v52" 2>/dev/null \
                | join -t $'\t' - "$size_v52" 2>/dev/null \
                | while IFS=$'\t' read -r name hash size; do
                    local s; s="$(human_size "$size")"
                    echo "<tr><td>${name}</td><td class='size'>${s}</td><td class='hash'>${hash}</td></tr>"
                done
            echo "</table>"
            echo "</details>"
        fi

        echo "</body></html>"
    } > "$out"

    printf '%-6s  nieuw=%-3d  vervallen=%-3d  gewijzigd=%-3d  gelijk=%-3d  → %s\n' \
        "$lib" "$count_nieuw" "$count_vervallen" "$count_gewijzigd" "$count_gelijk" "$out"
}

# Verzamel union van bibliotheken uit v5.0 en v5.2 (alleen S*-mappen)
declare -A all_libs
for d in "$V50_BASE"/S* "$V52_BASE"/S*; do
    [[ -d "$d" ]] || continue
    all_libs["$(basename "$d")"]=1
done

# Sorted list of library names
mapfile -t libs < <(printf '%s\n' "${!all_libs[@]}" | sort)

echo "Gevonden bibliotheken (${#libs[@]}): ${libs[*]}"
echo ""

for lib in "${libs[@]}"; do
    short="${lib#S}"
    v50_dir="$V50_BASE/$lib"
    v52_dir="$V52_BASE/$lib"
    out_dir="$OUT_BASE/$short"
    out_html="$out_dir/vergelijking_${lib}_5.0_vs_5.2.html"

    mkdir -p "$out_dir"

    emit_html "$lib" "$v50_dir" "$v52_dir" "$out_html"
done

echo ""
echo "Klaar. Tussenbestanden zijn verwijderd."
