"""In de WERKVERSIE:
 1) BSS-rijen hernoemen naar OPENVERHARDING_BETONSTRAATSTEEN_... (5.2: sobject
    SVH-BSS -> OPENVERHARDING_BETONSTRAATSTEEN);
 2) de -SO/-D-suffix strippen uit de omschrijving van meegenomen objecten
    (kolom B = Fysiek/Gebied/Activiteit);
en de segment-kolommen opnieuw splitsen voor elke gewijzigde rij.
"""
import os
import re
import openpyxl
from collections import Counter

FOLDER = "ontwikkeling/classificatie/fase 1 Inhoud classificatie VH"
WV = os.path.join(FOLDER, "Classificatie-NLCS-VH-inhoud-werkversie.xlsx")
SHEET = "objecten-concept-5.1-VH"
MEEGENOMEN = {"Fysiek", "Gebied", "Activiteit"}


def strip_prefix(s):
    s = str(s).strip()
    while True:
        m = re.match(r"^(B|V|N|O)-(.+)$", s)
        if m:
            s = m.group(2); continue
        m = re.match(r"^[AS][A-Z]{2}-(.+)$", s)
        if m:
            s = m.group(1); continue
        return s


try:
    wb = openpyxl.load_workbook(WV)
except PermissionError:
    raise SystemExit("Werkversie is open/gelockt (sluit 'm in Excel).")
ws = wb[SHEET]
hdr = [c.value for c in ws[1]]
col = {v: i + 1 for i, v in enumerate(hdr) if v}
CA = 1
CB = col["Fysiek object of ruimtelijk gebied? "]
SEG = [col["object"], col["subobject01"], col["subobject02"],
       col["subobject03"], col["subobject04"], col["subobject05"]]

bss = 0
stripped = 0
for ri in range(2, ws.max_row + 1):
    a = ws.cell(ri, CA).value
    if not a or not str(a).strip():
        continue
    name = strip_prefix(str(a))
    changed = False
    # 1) BSS -> OPENVERHARDING_BETONSTRAATSTEEN
    parts = name.split("_")
    if parts[0].upper() == "BSS":
        name = "_".join(["OPENVERHARDING", "BETONSTRAATSTEEN"] + parts[1:])
        bss += 1
        changed = True
    # 2) -SO/-D strippen uit alle namen
    new = re.sub(r"-(SO|D)$", "", name, flags=re.I)
    if new != name:
        name = new
        stripped += 1
        changed = True
    if not changed:
        continue
    ws.cell(ri, CA).value = name
    sp = name.split("_")
    if len(sp) > len(SEG):
        sp = sp[:len(SEG) - 1] + ["_".join(sp[len(SEG) - 1:])]
    for i, c in enumerate(SEG):
        ws.cell(ri, c).value = sp[i] if i < len(sp) else None

# duplicaten na strippen melden
names = [str(ws.cell(ri, CA).value).strip() for ri in range(2, ws.max_row + 1)
         if ws.cell(ri, CA).value and str(ws.cell(ri, CA).value).strip()]
dups = [n for n, c in Counter(names).items() if c > 1]

wb.save(WV)
print("BSS hernoemd:", bss)
print("-SO/-D gestript (meegenomen):", stripped)
print("dubbele omschrijvingen na bewerking:", len(dups))
for d in dups[:15]:
    print("   dup:", d)
