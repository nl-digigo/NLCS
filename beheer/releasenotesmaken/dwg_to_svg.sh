#!/usr/bin/env bash
#
# Converteert alle DWG-bestanden in een bronmap naar SVG in een doelmap.
# Workflow:  DWG --[ODA File Converter]--> DXF --[Inkscape]--> SVG
#
# Inkscape gebruikt --export-area-drawing zodat de SVG-viewBox de tekening-
# extents volgt in plaats van een A4-pagina.
#
# Tussenliggende DXF-bestanden komen in een tijdelijke map en worden na
# afloop opgeruimd.
#
# Gebruik:
#   bash dwg_to_svg.sh <bron-dwg-map> <doel-svg-map>
#
# Voorbeeld:
#   bash dwg_to_svg.sh \
#       "C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCS/symbolen/5.2/autocad/SAL" \
#       "C:/Users/100289/OneDrive - CROW/Documents/GitHub/NLCS/symbolen/5.2/svg/SAL"

set -uo pipefail

ODA_EXE="/c/Program Files/ODA/ODAFileConverter 27.1.0/ODAFileConverter.exe"
INKSCAPE_EXE="/c/Program Files/Inkscape/bin/inkscape.exe"
DXF_VERSION="ACAD2010"

if [[ $# -ne 2 ]]; then
    echo "Gebruik: bash $0 <bron-dwg-map> <doel-svg-map>" >&2
    exit 1
fi

SRC_DWG="$1"
DST_SVG="$2"

[[ -d "$SRC_DWG" ]] || { echo "Bronmap niet gevonden: $SRC_DWG" >&2; exit 1; }
[[ -x "$ODA_EXE" ]] || { echo "ODA File Converter niet gevonden op: $ODA_EXE" >&2; exit 1; }
[[ -x "$INKSCAPE_EXE" ]] || { echo "Inkscape niet gevonden op: $INKSCAPE_EXE" >&2; exit 1; }

mkdir -p "$DST_SVG"

dwg_count=$(find "$SRC_DWG" -maxdepth 1 -name "*.dwg" -type f | wc -l)
if (( dwg_count == 0 )); then
    echo "Geen DWG-bestanden gevonden in: $SRC_DWG" >&2
    exit 1
fi
echo "Bron:   $SRC_DWG  (${dwg_count} DWG-bestanden)"
echo "Doel:   $DST_SVG"
echo ""

TMP_DIR="$(mktemp -d)"
TMP_DXF="$TMP_DIR/dxf"
mkdir -p "$TMP_DXF"
trap 'rm -rf "$TMP_DIR"' EXIT

# --- Stap 1: ODA DWG -> DXF ---
echo "[1/4] ODA File Converter: DWG → DXF ..."
SRC_DWG_WIN="$(cygpath -w "$SRC_DWG")"
TMP_DXF_WIN="$(cygpath -w "$TMP_DXF")"
"$ODA_EXE" "$SRC_DWG_WIN" "$TMP_DXF_WIN" "$DXF_VERSION" "DXF" "0" "0" "*.DWG"
oda_status=$?
dxf_count=$(find "$TMP_DXF" -maxdepth 1 -name "*.dxf" -type f | wc -l)
echo "     → ${dxf_count}/${dwg_count} DXF-bestanden gemaakt (ODA exit ${oda_status})"
if (( dxf_count == 0 )); then
    echo "Geen DXF-output — afbreken." >&2
    exit 1
fi

# --- Stap 2: Inkscape DXF -> SVG ---
echo ""
echo "[2/4] Inkscape: DXF → SVG (--export-area-drawing) ..."
# Bash-glob expansion zou met 1000+ files de cmdline kunnen overschrijden.
# Daarom in chunks van 100 verwerken via xargs.
find "$TMP_DXF" -maxdepth 1 -name "*.dxf" -type f -print0 \
    | xargs -0 -n 100 "$INKSCAPE_EXE" --export-type=svg --export-area-drawing 2>&1 \
    | grep -v -E "^(Script Error|\\\$PDMODE|^----|^$)" || true

# Inkscape schrijft de SVG naast de DXF; tel resultaat
svg_count=$(find "$TMP_DXF" -maxdepth 1 -name "*.svg" -type f | wc -l)
echo "     → ${svg_count}/${dxf_count} SVG-bestanden gemaakt"

# --- Stap 3: SVG's naar doelmap ---
echo ""
echo "[3/4] SVG's verplaatsen naar doelmap ..."
moved=0
failed=0
while IFS= read -r svg; do
    if mv "$svg" "$DST_SVG/" 2>/dev/null; then
        moved=$((moved+1))
    else
        failed=$((failed+1))
        echo "  ⚠ kon niet verplaatsen: $(basename "$svg")" >&2
    fi
done < <(find "$TMP_DXF" -maxdepth 1 -name "*.svg" -type f)
echo "     → ${moved} verplaatst, ${failed} mislukt"

# --- Stap 4: width/height eenheid (mm) toevoegen aan root <svg> ---
# Inkscape schrijft width/height zonder eenheid, browsers interpreteren dan
# als pixels (een 19-unit DWG-symbool wordt ~19 pixels = onzichtbaar).
# Door 'mm' toe te voegen krijgen de SVGs hun fysieke afmeting.
# Alleen de root-attributen (3 spaties indent) krijgen mm; nested <pattern>
# elementen (7 spaties) blijven unitless.
echo ""
echo "[4/4] mm-eenheid toevoegen aan root width/height ..."
fixed=0
for svg in "$DST_SVG"/*.svg; do
    [[ -f "$svg" ]] || continue
    if sed -i -E 's|^(   width=")([0-9.]+)("$)|\1\2mm\3|; s|^(   height=")([0-9.]+)("$)|\1\2mm\3|' "$svg" 2>/dev/null; then
        fixed=$((fixed+1))
    fi
done
echo "     → ${fixed} SVGs bijgewerkt"

# --- Samenvatting ---
echo ""
final_count=$(find "$DST_SVG" -maxdepth 1 -name "*.svg" -type f | wc -l)
echo "Klaar. Doelmap bevat nu ${final_count} SVG-bestanden."

# Rapporteer eventuele DWG's zonder bijbehorende SVG
missing=$(comm -23 \
    <(find "$SRC_DWG" -maxdepth 1 -name "*.dwg" -type f -printf "%f\n" | sed 's/\.dwg$//' | sort) \
    <(find "$DST_SVG" -maxdepth 1 -name "*.svg" -type f -printf "%f\n" | sed 's/\.svg$//' | sort))
if [[ -n "$missing" ]]; then
    miss_count=$(echo "$missing" | wc -l)
    echo ""
    echo "⚠ ${miss_count} DWG's zonder bijbehorende SVG:"
    echo "$missing" | sed 's/^/    /' | head -10
    if (( miss_count > 10 )); then echo "    ... (eerste 10 getoond)"; fi
fi
