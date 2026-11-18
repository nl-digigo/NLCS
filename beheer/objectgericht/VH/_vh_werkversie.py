"""Maak een WERKVERSIE van de VH-classificatie-Excel waarin de symbolen netjes
worden opgesplitst:
  - SVH- (bibliotheek-prefix, en fase-prefix B-/V-/N-/O-) uit de naam (kolom A);
  - -SO / -D eraf ALS het een fysiek object is (kolom B = 'Fysiek');
  - de schone naam op '_' splitsen naar de segment-kolommen I/K/M/O/Q/S
    (alleen waar object-kolom nog leeg is; bestaande splitsingen blijven staan).
Het origineel wordt NIET gewijzigd; resultaat gaat naar ...-werkversie.xlsx.
"""
import os
import re
import shutil
import openpyxl

FOLDER = "ontwikkeling/classificatie/fase 1 Inhoud classificatie VH"
SRC = os.path.join(FOLDER, "Classificatie-NLCS-VH-inhoud.xlsx")
DST = os.path.join(FOLDER, "Classificatie-NLCS-VH-inhoud-werkversie.xlsx")
SHEET = "objecten-concept-5.1-VH"

shutil.copy2(SRC, DST)
wb = openpyxl.load_workbook(DST)          # stijlen/celkleuren behouden
ws = wb[SHEET]
hdr = [c.value for c in ws[1]]
col = {v: i + 1 for i, v in enumerate(hdr) if v}      # 1-based kolomnummers
CA = 1
CB = col["Fysiek object of ruimtelijk gebied? "]
COBJ = col["object"]
SEG = [col["object"], col["subobject01"], col["subobject02"],
       col["subobject03"], col["subobject04"], col["subobject05"]]


def norm(name):
    """fase-prefix (B-/V-/N-/O-) en bibliotheek-prefix (SVH- e.d.) eraf."""
    s = name.strip()
    while True:
        m = re.match(r"^(B|V|N|O)-(.+)$", s)
        if m:
            s = m.group(2)
            continue
        m = re.match(r"^[AS][A-Z]{2}-(.+)$", s)
        if m:
            s = m.group(1)
            continue
        return s


changed = 0
filled = 0
samples = []
for ri in range(2, ws.max_row + 1):
    a = ws.cell(ri, CA).value
    if not a or not str(a).upper().startswith(("SVH-", "B-SVH", "V-SVH")):
        continue
    b = ws.cell(ri, CB).value
    is_fysiek = b is not None and str(b).strip() == "Fysiek"
    clean = norm(str(a))
    if is_fysiek:
        clean = re.sub(r"-(SO|D)$", "", clean)
    if clean != str(a):
        ws.cell(ri, CA).value = clean
        changed += 1
    # alleen splitsen als de object-kolom nog leeg is
    objv = ws.cell(ri, COBJ).value
    if objv is None or not str(objv).strip():
        parts = clean.split("_")
        if len(parts) > len(SEG):            # meer dan 6 delen -> rest in laatste
            parts = parts[:len(SEG) - 1] + ["_".join(parts[len(SEG) - 1:])]
        for i, c in enumerate(SEG):
            ws.cell(ri, c).value = parts[i] if i < len(parts) else None
        filled += 1
        if len(samples) < 12:
            samples.append((a, clean, parts))

wb.save(DST)
print("werkversie:", DST)
print("namen opgeschoond (SVH-/-SO/-D weg):", changed)
print("rijen gesplitst (object-kolom was leeg):", filled)
print("--- voorbeelden (origineel -> schoon -> segmenten) ---")
for orig, clean, parts in samples:
    print(f"   {orig!r}\n     -> {clean!r}  ->  {parts}")
