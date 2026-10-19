"""Generator: NLCS Objectgericht - VerHardingen.
Per hoofdobject een boom + materialenlegenda; materiaal-segmenten gekleurd.
Publicatie: docs/changelog/VH-objectgericht/index.html
"""
import csv, os, re, shutil, sys, tempfile
import openpyxl
sys.path.insert(0, "beheer/objectentabellen_changelog")
import ot_html as H

XLSX = ("ontwikkeling/classificatie/fase 1 Inhoud classificatie VH/"
        "Classificatie-NLCS-VH-inhoud-werkversie.xlsx")
OUT = "docs/changelog/VH-objectgericht/reviewversie-20261008/index.html"
TITLE = "NLCS Objectgericht - VerHardingen"
SHEET = "objecten-concept-5.1-VH"

# --- Excel lezen (kopie i.v.m. mogelijke lock) ---
tmp = os.path.join(tempfile.gettempdir(), "_vh_cls.xlsx")
shutil.copy2(XLSX, tmp)
wb = openpyxl.load_workbook(tmp, data_only=True)
ws = wb[SHEET]
hdr = [c.value for c in ws[1]]
Hd = {v: i for i, v in enumerate(hdr) if v}
C_OM = Hd["omschrijving"]
C_FYS = Hd["Fysiek object of ruimtelijk gebied? "]
C_OBJ = Hd["object"]
# underscore-markerkolommen: als cel == "Materiaal" is het segment links het materiaal
MARK_COLS = [Hd[u] for u in
             ("underscore4", "underscore5", "underscore6", "underscore7", "underscore8")]

rows = []
for r in ws.iter_rows(min_row=2, values_only=True):
    a = r[C_OM]
    if a is None or not str(a).strip():
        continue
    b = str(r[C_FYS]).strip() if r[C_FYS] is not None else ""
    rows.append((str(a).strip(), b, r))
os.remove(tmp)

# --- indeling op kolom B: Fysiek, Gebied EN Activiteit samen in de objectbomen
#     (gebied- en activiteit-rijen worden als tekst bij hun object getoond);
#     de rest in een lijst ---
BUCKET_MAP = {"Fysiek": "Object", "Gebied": "Object", "Activiteit": "Object"}
tree_rows = {"Object": []}
rest = {}
for name, b, raw in rows:
    hit = BUCKET_MAP.get(b)
    if hit:
        tree_rows[hit].append((name, raw))
    else:
        rest.setdefault(b or "(leeg)", []).append(name)


# --- naam -> sleutel (fase- en bibliotheek-prefix eraf) ---
def norm_key(name):
    s = name.strip()
    while True:
        m = re.match(r"^(B|V|N|O)-(.+)$", s)
        if m:
            s = m.group(2); continue
        m = re.match(r"^[AS][A-Z]{2}-(.+)$", s)
        if m:
            s = m.group(1); continue
        return s


SEP = ("_", "-", " ")


def hoofdobject(name, raw):
    # hoofdobject = eerste segment van de (genormaliseerde) naam. De object-kolom
    # wordt niet vertrouwd: die kan verkeerd staan (bv. 'RAND' i.p.v. BOOMOMRANDING).
    return re.split(r"[_\- ]", norm_key(name).upper(), 1)[0]


def row_material(raw):
    """Materiaal van een rij = alle 'Materiaal'-gemarkeerde segmenten (de waarde
    links van elke marker), links-naar-rechts samengevoegd met '_'. Meerdere
    markers => samengesteld materiaal (bijv. GRANULAAT_BOMEN)."""
    parts = []
    for ci in MARK_COLS:
        v = raw[ci]
        if v is not None and str(v).strip().lower() == "materiaal":
            left = raw[ci - 1]
            if left is not None and str(left).strip():
                parts.append(str(left).strip().upper())
    return "_".join(parts) if parts else None


def row_gebied(raw):
    """Gebied van een rij = alle 'Gebied'-gemarkeerde segmenten (waarde links van
    elke marker), samengevoegd met '_'. Waarden als FREESVAK, 1, 2 zijn gebieden."""
    parts = []
    for ci in MARK_COLS:
        v = raw[ci]
        if v is not None and str(v).strip().lower() == "gebied":
            left = raw[ci - 1]
            if left is not None and str(left).strip():
                parts.append(str(left).strip().upper())
    return "_".join(parts) if parts else None


# --- eigenschappen: afmeting / richting / overig ---
RICHTINGEN = {"LINKS", "RECHTS", "MIDDEN"}
AFM_RE = re.compile(r"^\d+( \d+)?(X\d+)*$")
# symbool-variantsuffix aan het eind van de naam/cel (-SO, -D e.d.) weghalen
SUFFIX_RE = re.compile(r"-[A-Za-z]{1,3}$")


def strip_symbol_suffix(s):
    return SUFFIX_RE.sub("", s.strip())


def display_name(name):
    """Weergavenaam voor in de boom: bibliotheek-prefix (SVH- e.d.) en fase-prefix
    eraf (via norm_key) en de -SO/-D-suffix eraf. Interne naam blijft ongewijzigd
    (voor hierarchie/nesting)."""
    return strip_symbol_suffix(norm_key(name))


def cmp_key(name):
    """Vergelijkingssleutel die 'schijnverschillen' negeert: fase/bibliotheek-prefix,
    -SO/-D, _KL, maat-notatie (spatie tussen cijfers -> X) en de SBS/BSS-hernoeming
    (SBS = OPENVERHARDING_STRAATBAKSTEEN, BSS = OPENVERHARDING_BETONSTRAATSTEEN),
    zodat 5.0/5.2-symbolen matchen met de hernoemde classificatie-rijen."""
    s = norm_key(str(name))
    s = re.sub(r"^SBS(?=_|$)", "OPENVERHARDING_STRAATBAKSTEEN", s, flags=re.I)
    s = re.sub(r"^BSS(?=_|$)", "OPENVERHARDING_BETONSTRAATSTEEN", s, flags=re.I)
    s = re.sub(r"-(SO|D)$", "", s, flags=re.I)
    s = re.sub(r"_KL$", "", s, flags=re.I)
    s = re.sub(r"(?<=\d) +(?=\d)", "X", s)
    return s.strip().upper()


def _read_csv_col(path, names, filt=None):
    out = []
    try:
        with open(path, encoding="utf-8-sig") as f:
            head = f.readline()
            d = ";" if head.count(";") > head.count(",") else ","
            f.seek(0)
            r = csv.DictReader(f, delimiter=d)
            colname = next((c for c in r.fieldnames
                            if c and c.strip().lower() in names), r.fieldnames[0])
            for row in r:
                if filt and not filt(row):
                    continue
                v = row.get(colname)
                if v and str(v).strip():
                    out.append(str(v).strip())
    except FileNotFoundError:
        pass
    return out


def _load_in50():
    """Namen (laagnaam + VH-symbolen) uit de NLCS 5.0-publicatie, genormaliseerd."""
    s = set()
    for x in _read_csv_col(
            "tabellen/publicatie/objectentabellen/5-0/objecten-5-0-VH.csv",
            {"omschrijving"}):
        s.add(cmp_key(x))
    for x in _read_csv_col(
            "tabellen/publicatie/symbolentabellen/5-0/symbolen-5-0.csv",
            {"symbool"},
            filt=lambda r: str(r.get("sbibliotheek", "")).strip().upper() == "SVH"):
        s.add(cmp_key(x))
    return s


IN50 = _load_in50()


def _load_in52():
    """Namen (laagnaam + VH-symbolen) uit de NLCS 5.2-publicatie, genormaliseerd."""
    s = set()
    for x in _read_csv_col(
            "tabellen/publicatie/objectentabellen/5-2/objecten-5-2-VH.csv",
            {"omschrijving"}):
        s.add(cmp_key(x))
    for x in _read_csv_col(
            "tabellen/publicatie/symbolentabellen/5-2/symbolen-5-2-VH.csv",
            {"symbool"}):
        s.add(cmp_key(x))
    return s


IN52 = _load_in52()


def dot50(name):
    """Groen stipje als de naam (schijnverschillen genegeerd) in 5.0 voorkomt."""
    return ('<span class="dot50" title="Komt voor in NLCS 5.0">●</span> '
            if cmp_key(name) in IN50 else "")


def dot52(name):
    """Blauw stipje als de naam (schijnverschillen genegeerd) in 5.2 voorkomt."""
    return ('<span class="dot52" title="Komt voor in NLCS 5.2">●</span> '
            if cmp_key(name) in IN52 else "")


def classify_eig_token(tok):
    t = tok.strip().upper()
    if not t:
        return None
    if t in RICHTINGEN:
        return ("richting", t)
    if AFM_RE.match(t):
        return ("afmeting", t)
    return ("overig", t)


def row_eigenschappen(raw):
    """Eigenschappen van een rij, gesplitst in drie soorten. De markerwaarde (cel
    links van een 'afmeting'/'eigenschap'-marker) kan samengesteld zijn
    (bijv. 1750X1000_LINKS); split op '_' en classificeer elk token."""
    out = {"afmeting": [], "richting": [], "overig": []}
    for ci in MARK_COLS:
        v = raw[ci]
        if v is None:
            continue
        w = str(v).strip().lower()
        if "afmeting" not in w and "eigenschap" not in w:
            continue
        left = raw[ci - 1]
        if left is None:
            continue
        # -SO/-D e.d. weghalen, dan splitsen op _ en elk token classificeren
        for tok in strip_symbol_suffix(str(left)).split("_"):
            res = classify_eig_token(tok)
            if res and res[1] not in out[res[0]]:
                out[res[0]].append(res[1])
    return out


def row_activiteit(raw):
    """Activiteit van een rij (alleen B=Activiteit). Of expliciet via een
    'Activiteit'-marker op een _-segment (OPENVERHARDING_HERSTRATEN -> HERSTRATEN),
    of als streepje-suffix in de naam (..._BUSHALTEBAND-OPNIEUW STELLEN ->
    OPNIEUW STELLEN). Retour None als het geen activiteit-rij is."""
    if raw[C_FYS] is None or str(raw[C_FYS]).strip() != "Activiteit":
        return None
    for ci in MARK_COLS:
        v = raw[ci]
        if v is not None and str(v).strip().lower() == "activiteit":
            left = raw[ci - 1]
            if left is not None and str(left).strip():
                return str(left).strip().upper()
    nm = strip_symbol_suffix(str(raw[C_OM]))
    if "-" in nm:
        return nm.rsplit("-", 1)[1].strip().upper()
    return None


def is_gebied(raw):
    """Kolom B (Fysiek object of ruimtelijk gebied?) bepaalt of het een gebied is."""
    return raw[C_FYS] is not None and str(raw[C_FYS]).strip() == "Gebied"


# --- materiaalkleuren (stabiel over de hele pagina) ---
def collect_materials():
    mats = set()
    for name, raw in tree_rows["Object"]:
        m = row_material(raw)
        if m:
            mats.add(m)
    return sorted(mats)


MATERIALS = collect_materials()


def collect_gebieden():
    s = set()
    for name, raw in tree_rows["Object"]:
        g = row_gebied(raw)
        if g:
            s.add(g)
    return sorted(s)


GEBIEDEN = collect_gebieden()


def collect_activiteiten():
    s = set()
    for name, raw in tree_rows["Object"]:
        a = row_activiteit(raw)
        if a:
            s.add(a)
    return sorted(s)


ACTIVITEITEN = collect_activiteiten()


def mat_hue(mat):
    i = MATERIALS.index(mat)
    return round((i * 137.508) % 360, 1)


def mat_bg(mat):
    return f"hsl({mat_hue(mat)},62%,90%)"


def mat_bd(mat):
    return f"hsl({mat_hue(mat)},50%,45%)"


MATERIAL_COLOR = "#4f8a3d"   # 1 vaste kleur voor materialen
EIG_COLOR = "#c0872e"        # 1 vaste kleur voor eigenschappen


def mark_name(name, mat, eig_tokens):
    """Markeer in de objectnaam het materiaal-deel (1 kleur) en de eigenschap-delen
    (1 kleur). Niet-overlappende spans; materiaal/eigenschap elk hun eigen klasse."""
    spans = []
    if mat:
        spans.append((mat, "mat"))
    for t in eig_tokens:
        spans.append((t, "eig"))
    low = name.lower()
    sepset = set("_- ")

    def find_segment(sub_low):
        """Eerste voorkomen dat een heel segment is (begrensd door _, -, spatie
        of begin/eind) -> voorkomt match midden in een woord (RAND in BOOMOMRANDING)."""
        start = 0
        while True:
            i = low.find(sub_low, start)
            if i < 0:
                return -1
            j = i + len(sub_low)
            before_ok = i == 0 or low[i - 1] in sepset
            after_ok = j == len(low) or low[j] in sepset
            if before_ok and after_ok:
                return i
            start = i + 1

    marks = []
    for sub, kind in spans:
        if not sub:
            continue
        i = find_segment(sub.lower())
        if i >= 0:
            marks.append((i, i + len(sub), kind))
    marks.sort(key=lambda m: (m[0], -(m[1] - m[0])))
    chosen = []
    last = -1
    for s, e, k in marks:
        if s >= last:
            chosen.append((s, e, k))
            last = e
    out = []
    pos = 0
    for s, e, k in chosen:
        out.append(H._esc(name[pos:s]))
        cls = "matword" if k == "mat" else "eigword"
        lab = "Materiaal" if k == "mat" else "Eigenschap"
        out.append(f'<span class="{cls}" title="{lab}: {H._esc(name[s:e])}">'
                   f'{H._esc(name[s:e])}</span>')
        pos = e
    out.append(H._esc(name[pos:]))
    return "".join(out)


# --- boom bouwen binnen een set rijen ---
def build_tree(items):
    """items: list[(name, raw)]. Gebied-rijen (met een Gebied-marker) worden GEEN
    eigen knoop, maar als tekst 'Gebied: X' bij hun bovenliggende object gezet.
    Retour (roots, children, rawmap, gebied_at)."""
    rawmap = {}
    for name, raw in items:
        rawmap.setdefault(name, raw)
    all_names = sorted(rawmap)
    keys = {n: norm_key(n).upper() for n in all_names}

    def find_parent(n, candidates):
        kn = keys[n]
        best = None
        for m in candidates:
            if m == n:
                continue
            km = keys[m]
            if km and len(km) < len(kn) and kn.startswith(km) and kn[len(km)] in SEP:
                if best is None or len(keys[best]) < len(km):
                    best = m
        return best

    def absorb(n):
        return is_gebied(rawmap[n]) or (row_activiteit(rawmap[n]) is not None)

    abset = {n for n in all_names if absorb(n)}
    base = [n for n in all_names if n not in abset]
    gebied_at = {}
    activiteit_at = {}
    extra = []
    for n in sorted(abset):
        raw = rawmap[n]
        p = find_parent(n, base)
        if is_gebied(raw):
            # ruimtelijk gebied: NOOIT een eigen knoop; alleen als tekst bij de ouder
            if p is not None:
                g = row_gebied(raw) or display_name(n).split("_")[-1]
                gebied_at.setdefault(p, [])
                if g not in gebied_at[p]:
                    gebied_at[p].append(g)
            continue
        # activiteit
        a = row_activiteit(raw)
        tgt = p if p is not None else n          # geen ouder -> op zichzelf tonen
        if p is None:
            extra.append(n)
        if a:
            activiteit_at.setdefault(tgt, [])
            if a not in activiteit_at[tgt]:
                activiteit_at[tgt].append(a)
    node_names = base + extra
    nset = set(node_names)
    children = {n: [] for n in node_names}
    roots = []
    for n in node_names:
        p = find_parent(n, node_names)
        if p is None or p not in nset:
            roots.append(n)
        else:
            children[p].append(n)
    return (sorted(roots, key=str.casefold), children, rawmap,
            gebied_at, activiteit_at)


def count_all(roots, children):
    tot = 0

    def walk(n):
        nonlocal tot
        tot += 1
        for c in children.get(n, []):
            walk(c)
    for r in roots:
        walk(r)
    return tot


def render_tree(roots, children, rawmap, gebied_at=None, activiteit_at=None):
    gebied_at = gebied_at or {}
    activiteit_at = activiteit_at or {}

    def node(n):
        kids = sorted(children.get(n, []), key=str.casefold)
        raw = rawmap.get(n)
        mat = row_material(raw) if raw is not None else None
        eig = (row_eigenschappen(raw) if raw is not None
               else {"afmeting": [], "richting": [], "overig": []})
        eig_tokens = eig["afmeting"] + eig["richting"] + eig["overig"]
        label = dot50(n) + dot52(n) + mark_name(display_name(n), mat, eig_tokens)
        # gebied + activiteit: tekst bij dit (bovenliggende) object
        gl = gebied_at.get(n)
        if gl:
            label += f' <span class="geb">Gebied: {H._esc(", ".join(gl))}</span>'
        al = activiteit_at.get(n)
        if al:
            label += f' <span class="act">Activiteit: {H._esc(", ".join(al))}</span>'
        if kids:
            inner = "\n".join(node(k) for k in kids)
            return (f'<li><details class="tree" open>'
                    f'<summary class="node">{label}</summary>\n'
                    f'<ul>\n{inner}\n</ul></details></li>')
        return f'<li class="leaf">{label}</li>'
    if not roots:
        return '<p class="empty">Geen objecten.</p>'
    return ('<ul class="otree">\n' + "\n".join(node(r) for r in roots) + "\n</ul>")


def legend_html(items):
    mats = sorted({m for _n, raw in items if (m := row_material(raw))})
    gebs = sorted({g for _n, raw in items if (g := row_gebied(raw))})
    acts = sorted({a for _n, raw in items if (a := row_activiteit(raw))})
    afm, rch, ovg = [], [], []
    for _n, raw in items:
        e = row_eigenschappen(raw)
        for x in e["afmeting"]:
            if x not in afm:
                afm.append(x)
        for x in e["richting"]:
            if x not in rch:
                rch.append(x)
        for x in e["overig"]:
            if x not in ovg:
                ovg.append(x)

    def sec(title, vals, swcolor=None):
        head = f'<h3>{title} <span class="legend-n">{len(vals)}</span></h3>'
        if not vals:
            body = '<p class="legend-empty">–</p>'
        elif swcolor:
            body = ('<ul class="legend-list">\n' + "\n".join(
                f'<li><span class="sw" style="background:{swcolor}"></span>'
                f'{H._esc(v)}</li>' for v in vals) + '\n</ul>')
        else:
            body = ('<ul class="legend-list">\n' + "\n".join(
                f'<li class="geb-li">{H._esc(v)}</li>' for v in vals) + '\n</ul>')
        return f'<div class="legend-sec">{head}\n{body}</div>'

    # volgorde: Materialen | Afmetingen | Eigenschappen (overig, incl. richting) | Gebieden
    overig = sorted(set(ovg) | set(rch))
    secs = [sec("Materialen", mats, swcolor=MATERIAL_COLOR),
            sec("Afmetingen", sorted(afm), swcolor=EIG_COLOR),
            sec("Eigenschappen (overig)", overig, swcolor=EIG_COLOR),
            sec("Gebieden", gebs),
            sec("Activiteiten", acts)]
    return '<aside class="legend">\n' + "\n".join(secs) + '\n</aside>'


# ===== Object: per hoofdobject een kaart =====
groups = {}
for name, raw in tree_rows["Object"]:
    groups.setdefault(hoofdobject(name, raw), []).append((name, raw))


def _is_node_row(raw):
    return not is_gebied(raw) and row_activiteit(raw) is None


# alleen hoofdobjecten met minstens één echte objectknoop krijgen een kaart;
# gebied-/activiteit-only groepen (bv. MATERIAALGRENS, REPARATIES) niet
order = sorted([h for h in groups
                if any(_is_node_row(raw) for _n, raw in groups[h])],
               key=str.casefold)

nav = ('<nav class="hobj-nav">'
       + '<a class="navmat" href="#mat-index">Materialen &#8595;</a> '
       + " ".join(f'<a href="#h-{re.sub(r"[^A-Za-z0-9]+","-",h)}">{H._esc(h)}</a>'
                  for h in order)
       + "</nav>")

def anchor_of(h):
    return "h-" + re.sub(r"[^A-Za-z0-9]+", "-", h)


VRAGEN_LIST = (
    '<ol>'
    '<li>Zijn dit de objecten die nodig zijn in de classificatie?</li>'
    '<li>Komen deze objecten overeen met de objecten in je calculatiesoftware?</li>'
    '<li>Mis je gangbare maten of materialen? (Niet-gangbare afmetingen kunnen '
    'straks ook worden uitgewisseld, maar zijn niet in de standaard opgenomen.)</li>'
    '<li>Mis je activiteiten? (nb: aanleg / verwijderen is geregeld in de '
    'NLCS Status)</li>'
    '</ol>')

# Opmerkingen per hoofdobject (sleutel = hoofdobjectnaam in hoofdletters).
COMMENTS = {
    "DREMPEL": [
        ("Hoogte", "verschilt per inrit / drempel, dit moet objectinformatie zijn, "
         "maar geen onderliggende objecten in de tekenstandaard of de classificatie."),
        ("Kleur", "idem"),
        ("DREMPEL_BSS", "Kleur, type steen en hoogte zijn relevant"),
    ],
    "FUNDERING": [
        ("Mengsel/verhouding", "moet terugkomen in productpaspoort; geometrie is "
         "niet voldoende voor inkoop/calculatie."),
    ],
    "GEOTEXTIEL": [
        ("Actie", "verdieping toevoegen binnen de NLCS – issue aangemaakt:",
         ("Issue #875", "https://github.com/nl-digigo/NLCS/issues/875")),
    ],
    "ROOSTER": [
        ("Toelichting", "bedoeld wordt Veerooster / Wildrooster."),
    ],
    "GESLOTENVERHARDING": [
        ("ASFALT", "mengsel/verhouding moet terugkomen in productpaspoort; "
         "geometrie is niet voldoende voor inkoop/calculatie."),
        ("BETON", "mengsel/verhouding moet terugkomen in productpaspoort; "
         "geometrie is niet voldoende voor inkoop/calculatie."),
    ],
}


def vragen_html(h):
    cs = COMMENTS.get(h.upper(), [])
    if cs:
        parts = []
        for c in cs:
            k, v = c[0], c[1]
            link = ""
            if len(c) > 2 and c[2]:
                lt, url = c[2]
                link = (f' <a href="{H._esc(url)}" target="_blank" '
                        f'rel="noopener">{H._esc(lt)}</a>')
            parts.append(f'<li><strong>{H._esc(k)}:</strong> {H._esc(v)}{link}</li>')
        items = "".join(parts)
        left = (f'<div class="vg-col vg-comments"><strong>Opmerkingen</strong>'
                f'<ul>{items}</ul></div>')
    else:
        left = '<div class="vg-col vg-comments"></div>'
    right = (f'<div class="vg-col vg-vragen"><strong>Vragen bij deze groep</strong>'
             f'{VRAGEN_LIST}</div>')
    return f'<div class="vragen hobj-vragen vg-grid">{left}{right}</div>'


obj_cards = []
for i, h in enumerate(order):
    items = groups[h]
    roots, children, rawmap, gebied_at, activiteit_at = build_tree(items)
    n = count_all(roots, children)
    anchor = anchor_of(h)
    prev_h = order[i - 1] if i > 0 else None
    next_h = order[i + 1] if i < len(order) - 1 else None
    step = ['<div class="hobj-step">']
    step.append(f'<a class="step prev" href="#{anchor_of(prev_h)}">&#8249; {H._esc(prev_h)}</a>'
                if prev_h else '<span class="step disabled">&#8249; begin</span>')
    step.append('<a class="step top" href="#top" title="Naar boven">&#8593;</a>')
    step.append(f'<a class="step next" href="#{anchor_of(next_h)}">Volgende boom: {H._esc(next_h)} &#8250;</a>'
                if next_h else '<span class="step disabled">einde &#8250;</span>')
    step.append('</div>')
    obj_cards.append(
        f'<div class="card hobj" id="{anchor}">'
        f'<div class="hobj-head"><h2>{H._esc(h)} '
        f'<span class="tree-count">{n} regel(s) &middot; '
        f'{len(roots)} op het eerste niveau</span></h2>\n'
        + "".join(step) + '</div>\n'
        f'<div class="hobj-body">\n'
        f'<div class="hobj-tree">'
        f'{render_tree(roots, children, rawmap, gebied_at, activiteit_at)}</div>\n'
        f'{legend_html(items)}\n</div>\n' + vragen_html(h) + '</div>')

# ===== materialen -> hoofdobjecten (omgekeerde index) =====
mat_groups = {m: [] for m in MATERIALS}
for h in order:
    present = sorted({m for _n, raw in groups[h] if (m := row_material(raw))})
    for m in present:
        mat_groups[m].append(h)
_mi_rows = []
for m in sorted(mat_groups):
    gl = mat_groups[m]
    links = (", ".join(f'<a href="#{anchor_of(h)}">{H._esc(h)}</a>' for h in gl)
             if gl else '<span class="mi-none">–</span>')
    _mi_rows.append(f'<li><span class="matword">{H._esc(m)}</span>'
                    f'<span class="mi-groups">{links}</span></li>')
matindex_card = (
    f'<div class="card" id="mat-index"><h2>Materialen per hoofdobject '
    f'<span class="tree-count">{len(MATERIALS)} materialen</span></h2>\n'
    f'<ul class="matindex">\n' + "\n".join(_mi_rows) + '\n</ul></div>')

# ===== gebieden (ruimtelijk gebied) -> evt. link naar object =====
_order_set = set(order)
_geb_entries = []
for name, raw in tree_rows["Object"]:
    if not is_gebied(raw):
        continue
    disp = display_name(name)
    ho = hoofdobject(name, raw)
    link = ho if ho in _order_set else None
    _geb_entries.append((disp, link))
_geb_entries = sorted(set(_geb_entries), key=lambda e: e[0].casefold())
_gi_rows = []
for disp, link in _geb_entries:
    tail = (f'<span class="mi-groups">&rarr; <a href="#{anchor_of(link)}">'
            f'{H._esc(link)}</a></span>' if link
            else '<span class="mi-none">(geen object)</span>')
    _gi_rows.append(f'<li><span class="matword">{H._esc(disp)}</span>{tail}</li>')
gebied_index_card = (
    f'<div class="card" id="geb-index"><h2>Gebieden (ruimtelijk gebied) '
    f'<span class="tree-count">{len(_geb_entries)} gebieden</span></h2>\n'
    f'<p class="info">Ruimtelijke gebieden zijn geen losse objecten; waar van '
    f'toepassing staat de link naar het bijbehorende object.</p>\n'
    f'<ul class="matindex">\n' + "\n".join(_gi_rows) + '\n</ul></div>')

# ===== rest-lijst =====
rest_total = sum(len(v) for v in rest.values())
rest_parts = [f'<div class="card"><h2>Niet meegenomen (laagnaam/symbool, dubbel) '
              f'<span class="tree-count">{rest_total} regel(s)</span></h2>']
rest_parts.append('<p class="info">Deze regels zijn geen eigen objecttype in een '
                  'van de bomen; gegroepeerd op de reden uit kolom B.</p>')
for reason in sorted(rest, key=str.casefold):
    names = sorted(rest[reason], key=str.casefold)
    its = "\n".join(f'<li class="leaf">{dot50(nm)}{dot52(nm)}{H._esc(nm)}</li>'
                    for nm in names)
    rest_parts.append(f'<h3 class="rest-h">{H._esc(reason)} '
                      f'<span class="tree-count">{len(names)}</span></h3>\n'
                      f'<ul class="otree flat">\n{its}\n</ul>')
rest_parts.append('</div>')

info = (f"Bron: Classificatie-NLCS-VH-inhoud.xlsx &middot; "
        f"{len(order)} hoofdobjecten &middot; "
        f"{len(tree_rows['Object'])} laagnamen &middot; "
        f"niet meegenomen {rest_total} &middot; "
        f"{len(MATERIALS)} materialen &middot; {len(GEBIEDEN)} gebieden &middot; "
        f"{len(ACTIVITEITEN)} activiteiten")

extra = """
    .reviewnote { font-size:1rem; font-weight:700; color:var(--dg-blue);
        margin:0 0 10px; }
    .vragen { background:#fff8e1; border:1px solid #e8d48a; border-radius:6px;
        padding:10px 14px; }
    .vragen ol { margin:4px 0 0; padding-left:20px; }
    .vragen li { margin:3px 0; font-size:.9rem; line-height:1.35; }
    .hobj-vragen { margin-top:14px; font-size:.86rem; }
    .hobj-vragen strong { font-size:.8rem; text-transform:uppercase;
        letter-spacing:.03em; color:var(--dg-grey2); }
    .vg-grid { display:flex; gap:20px; align-items:flex-start; }
    .vg-col { flex:1 1 50%; min-width:0; }
    .vg-comments ul { margin:4px 0 0; padding-left:18px; }
    .vg-comments li { margin:3px 0; font-size:.9rem; line-height:1.35; }
    @media (max-width:700px){ .vg-grid { flex-direction:column; gap:10px; } }
    .matindex { list-style:none; margin:0; padding:0; }
    .matindex li { display:flex; gap:14px; flex-wrap:wrap; align-items:baseline;
        padding:5px 0; border-top:1px solid var(--dg-grey); }
    .matindex .matword { flex:0 0 230px; }
    .mi-groups { flex:1 1 300px; font-size:.86rem; }
    .mi-groups a { color:var(--dg-blue); text-decoration:none; }
    .mi-groups a:hover { text-decoration:underline; }
    .mi-none { color:var(--dg-grey2); }
    .card .tree-count { font-size:.72rem; font-weight:400; color:var(--dg-grey2); }
    .hobj-nav { margin:0 0 18px; line-height:1.9; }
    .hobj-nav a { display:inline-block; font-size:.78rem; padding:1px 8px; margin:0 4px 2px 0;
        border:1px solid var(--dg-grey); border-radius:12px; color:var(--dg-ink);
        text-decoration:none; background:#fff; }
    .hobj-nav a:hover { background:var(--dg-blue); color:#fff; border-color:var(--dg-blue); }
    .hobj-nav a.navmat { background:var(--dg-blue); color:#fff; border-color:var(--dg-blue);
        font-weight:600; }
    .hobj-body { display:flex; gap:22px; align-items:flex-start; }
    .hobj-tree { flex:1 1 auto; min-width:0; }
    .legend { flex:1 1 380px; border-left:1px solid var(--dg-grey); padding-left:16px;
        display:flex; flex-wrap:wrap; gap:6px 16px; align-items:flex-start; }
    .legend-sec { flex:0 0 118px; max-width:160px; }
    .legend h3 { margin:0 0 6px; font-size:.8rem; }
    .legend-n { font-weight:400; color:var(--dg-grey2); font-size:.72rem; }
    .legend-list { list-style:none; margin:0; padding:0; font-size:.78rem; }
    .legend-list li { display:flex; align-items:center; gap:6px; padding:1px 0;
        word-break:break-word; }
    .legend .sw { width:13px; height:13px; border-radius:3px; flex:0 0 auto;
        border:1px solid rgba(0,0,0,.15); }
    .legend-empty { font-size:.8rem; color:var(--dg-grey2); }
    .geb-li { padding-left:2px; }
    .matword { background:#dcebd3; border-left:3px solid #4f8a3d;
        padding:0 5px; border-radius:3px; }
    .eigword { background:#f4e6cf; border-left:3px solid #c0872e;
        padding:0 5px; border-radius:3px; }
    .dot50 { color:#2e9b2e; font-size:.72em; vertical-align:middle; }
    .dot52 { color:#1f6fd0; font-size:.72em; vertical-align:middle; }
    .dotlegend { font-size:.82rem; color:var(--dg-ink); margin:0 0 14px; }
    .dotlegend .dot50, .dotlegend .dot52 { margin-right:4px; }
    .geb { font-size:.78rem; font-style:italic; color:var(--dg-grey2);
        margin-left:6px; }
    .act { font-size:.78rem; font-style:italic; color:#7a5c13;
        margin-left:6px; }
    .hobj-head { display:flex; align-items:baseline; justify-content:space-between;
        gap:16px; flex-wrap:wrap; }
    .hobj-head h2 { margin:0; }
    .hobj-step { display:flex; align-items:center; gap:6px; font-size:.74rem; }
    .hobj-step .step { text-decoration:none; border:1px solid var(--dg-grey);
        border-radius:12px; padding:1px 9px; color:var(--dg-ink); background:#fff;
        max-width:16ch; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
    .hobj-step .step:hover { background:var(--dg-blue); color:#fff; border-color:var(--dg-blue); }
    .hobj-step .step.disabled { color:var(--dg-grey2); background:var(--dg-grey); cursor:default; }
    .intro-fig { margin:0 0 22px; border:1px solid var(--dg-grey); border-radius:6px;
        background:#fff; padding:12px; }
    .intro-fig img { display:block; max-width:100%; height:auto; margin:0 auto; }
    .intro-fig figcaption { font-size:.84rem; color:var(--dg-ink); margin-top:10px;
        text-align:center; }
    h3.rest-h { font-size:.95rem; margin:14px 0 4px; color:var(--dg-ink);
        border-top:1px solid var(--dg-grey); padding-top:8px; }
    .otree.flat { columns:2; }
    @media (max-width:800px){ .hobj-body { flex-direction:column; }
        .legend { flex:1 1 auto; border-left:0; border-top:1px solid var(--dg-grey);
            padding-left:0; padding-top:10px; width:100%; }
        .otree.flat { columns:1; } }
"""

html = (H._shell_head(TITLE, extra_style=H._INDEX_STYLE + H._TREE_STYLE + extra,
                      cdn=False)
        + f'<div class="wrap" id="top">\n'
        + '<p class="reviewnote">Reviewversie voor projectgroep &middot; '
          '8 oktober 2026</p>\n'
        + f'<p class="info">{info}</p>\n'
        + '<p class="dotlegend"><span class="dot50">●</span> komt voor in '
          'NLCS 5.0 &nbsp; <span class="dot52">●</span> komt voor in NLCS 5.2 '
          '(schijnverschillen in notatie genegeerd)</p>\n'
        + '<figure class="intro-fig">'
        + '<img src="NEN2660_mapping_NLCS_Classificatie.png" '
          'alt="NLCS-objecten vertaald naar NEN2660-2">'
        + '<figcaption>De NLCS-Objecten (laagnamen) vertaald naar reële '
          'objecten, activiteiten, materialen, ruimtelijke gebieden en eigenschappen '
          'van de objecten volgens de NEN2660-2.</figcaption></figure>\n'
        + '<h1 class="sect">Objectenbomen Verhardingen</h1>\n' + nav + "\n"
        + "\n".join(obj_cards) + "\n"
        + matindex_card + "\n"
        + gebied_index_card + "\n"
        + "\n".join(rest_parts) + "\n</div>\n"
        + '<script src="https://hypothes.is/embed.js" async></script>\n'
        + H._FOOTER)

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    f.write(html)
print("geschreven:", OUT)
print("hoofdobjecten:", len(order), "| materialen:", len(MATERIALS))
