"""gen_classificatie_html.py - bouw de interactieve classificatie-pagina uit de
classificatie-export-CSV (NLCS-<versie>-classificatie.csv).

Hergebruikt de digiGO-huisstijlheader + CSS/layout uit classificatie-prototype.html
(alles vóór <div class="app">) en vult de echte boom + relaties in.

Gebruik:  python gen_classificatie_html.py <classificatie.csv> <uitvoer.html> [titel]
"""
import csv
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
PROTO = os.path.join(HERE, "classificatie-prototype.html")

RENDER_JS = r"""
const treeEl=document.getElementById("tree");
const detailEl=document.getElementById("detail");
let current=null;
function hasNlcs(n){return n.nlcs && (n.nlcs.object || n.nlcs.symbool);}
function makeNode(node,parentUl,depth){
  const li=document.createElement("li");
  const kids=node.children&&node.children.length;
  if(kids && depth>=1){ li.classList.add("collapsed"); li.dataset.defcol="1"; }
  const row=document.createElement("button");
  row.className="row"; row.type="button";
  row.innerHTML='<span class="tw'+(kids?'':' leaf')+'">▾</span>'+
    '<span class="dot'+(hasNlcs(node)?' has':'')+'"></span><span class="nm"></span>';
  row.querySelector(".nm").textContent=node.name;
  row.addEventListener("click",function(e){
    if(kids && e.offsetX<18){ li.classList.toggle("collapsed"); return; }
    select(node,row);
  });
  li.appendChild(row);
  li._node=node; li._row=row;
  if(kids){ const ul=document.createElement("ul");
    node.children.forEach(c=>makeNode(c,ul,depth+1)); li.appendChild(ul); }
  parentUl.appendChild(li);
}
function filterTree(q){
  q=(q||"").trim().toLowerCase();
  const roots=treeEl.children;
  const nores=document.getElementById("nores");
  if(!q){
    (function reset(ul){ for(const li of ul.children){
      li.hidden=false; li._row.classList.remove("hit");
      if(li.dataset.defcol) li.classList.add("collapsed");
      const sub=li.querySelector(":scope > ul"); if(sub) reset(sub);
    }})(treeEl);
    if(nores) nores.hidden=true;
    return;
  }
  let any=false;
  (function walk(ul){
    let vis=false;
    for(const li of ul.children){
      const self=li._node.name.toLowerCase().includes(q);
      const sub=li.querySelector(":scope > ul");
      const childVis=sub?walk(sub):false;
      const show=self||childVis;
      li.hidden=!show;
      li._row.classList.toggle("hit",self);
      if(sub){ if(childVis) li.classList.remove("collapsed");
        else if(li.dataset.defcol) li.classList.add("collapsed"); }
      if(show) vis=true;
    }
    return vis;
  })(treeEl);
  for(const li of roots){ if(!li.hidden){ any=true; break; } }
  if(nores) nores.hidden=any;
}
function select(node,row){
  if(current) current.classList.remove("sel");
  current=row; row.classList.add("sel"); renderDetail(node);
}
function esc(s){return (s==null?"":String(s)).replace(/[&<>]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;"}[c]));}
function relList(items){return '<ul class="rel">'+items.map(it=>
  '<li>'+(it[0]?'<span class="k">'+esc(it[0])+'</span>':'')+'<span>'+esc(it[1])+'</span></li>').join('')+'</ul>';}
function renderDetail(node){
  const path=node.name.split("_").join(" › ");
  const gw=(node.gwsw||[]);
  const gwsw= gw.length ? relList(gw.map(g=>["",g])) : '<p class="ph">geen GWSW-relatie</p>';
  let ni=[];
  if(node.nlcs&&node.nlcs.object) ni.push(["laagnaam",node.nlcs.object+(node.nlcs.objectId?"  ("+node.nlcs.objectId+")":"")]);
  if(node.nlcs&&node.nlcs.symbool) ni.push(["symbool",node.nlcs.symbool+(node.nlcs.symboolId?"  ("+node.nlcs.symboolId+")":"")]);
  const nlcs= ni.length ? relList(ni) : '<p class="ph">geen NLCS-relatie</p>';
  const info=relList([["naam",node.name],["URI",node.uri||""]]);
  const imbor=(node.imbor||[]);
  const imborBody= imbor.length ? relList(imbor.map(p=>[p[0],p[1]])) : '<p class="ph">geen IMBOR-relatie</p>';
  function relBox(cls,titel,items){
    const n=items.length;
    const body=n?relList(items.map(x=>["",x])):'<p class="ph">geen</p>';
    return '<div class="box '+cls+'"><h3>'+titel+'<span class="n">'+n+'</span></h3>'+body+'</div>';
  }
  detailEl.innerHTML=
    '<div class="d-head"><p class="d-name"></p><p class="d-path">'+esc(path)+'</p></div>'+
    '<div class="grid4">'+
      '<div class="box gwsw"><h3>GWSW<span class="n">'+gw.length+'</span></h3>'+gwsw+'</div>'+
      '<div class="box nlcs"><h3>NLCS<span class="n">'+ni.length+'</span></h3>'+nlcs+'</div>'+
      relBox('asp','Aspects',node.aspects||[])+
      relBox('part','Parts',node.parts||[])+
      relBox('act','Activiteiten',node.activiteiten||[])+
      relBox('mat','Materiaal',node.materiaal||[])+
      '<div class="box res"><h3>Informatie-attributen<span class="n">2</span></h3>'+info+'</div>'+
      '<div class="box imbor"><h3>IMBOR<span class="n">'+imbor.length+'</span></h3>'+imborBody+'</div>'+
    '</div>'+
    '<div class="legend">'+
      '<span><i style="--c:var(--c-nlcs)"></i>object heeft NLCS-relatie</span>'+
      '<span><i style="--c:var(--line-strong)"></i>geen NLCS-relatie</span>'+
      '<span>klik ▾ om in/uit te klappen</span></div>';
  detailEl.querySelector(".d-name").textContent=node.name;
}
TREE.forEach(n=>makeNode(n,treeEl,0));
const searchEl=document.getElementById("treesearch");
if(searchEl){
  let t=null;
  searchEl.addEventListener("input",function(){
    clearTimeout(t); const v=searchEl.value;
    t=setTimeout(()=>filterTree(v),120);
  });
  searchEl.addEventListener("keydown",function(e){ if(e.key==="Escape"){ searchEl.value=""; filterTree(""); } });
}
detailEl.innerHTML='<p class="d-empty">Selecteer links een object in de boom. '+
  'Rechts verschijnen de relaties in acht vakken: GWSW, NLCS, Aspects, Parts, '+
  'Activiteiten, Materiaal, informatie-attributen (URI, naam) en IMBOR '+
  '(directe def-link + GWSW-URI-brug).</p>';
"""


def build_tree(csv_path):
    rows = list(csv.DictReader(open(csv_path, encoding="utf-8-sig")))
    nodes = {}
    for r in rows:
        nm = (r.get("naam") or "").strip()
        if not nm:
            continue
        def lst(col):
            return [v.strip() for v in (r.get(col) or "").split(";") if v.strip()]
        nodes[nm] = {
            "name": nm,
            "uri": (r.get("URI") or "").strip(),
            "parent": (r.get("subTypeOf") or "").strip(),
            "gwsw": lst("GWSW"),
            "nlcs": {"object": (r.get("NLCSLaagnaam") or "").strip(),
                     "objectId": (r.get("NLCSLaagnaamID") or "").strip(),
                     "symbool": (r.get("NLCSSymbool") or "").strip(),
                     "symboolId": (r.get("NLCSSymboolID") or "").strip()},
            "aspects": lst("aspects"),
            "parts": lst("parts"),
            "activiteiten": lst("activiteiten"),
            "materiaal": lst("materiaal"),
            "imbor": [[nm2, uri2] for nm2, uri2
                      in zip(lst("IMBOR"), lst("IMBORURI"))],
            "children": [],
        }
    roots = []
    for nm, nd in nodes.items():
        p = nd["parent"]
        if p and p in nodes and p != nm:
            nodes[p]["children"].append(nd)
        else:
            roots.append(nd)

    def srt(n):
        n["children"].sort(key=lambda c: c["name"].casefold())
        for c in n["children"]:
            srt(c)
    for r in roots:
        srt(r)
    roots.sort(key=lambda c: c["name"].casefold())
    # 'parent' hoeft niet in de output
    def clean(n):
        n.pop("parent", None)
        for c in n["children"]:
            clean(c)
    for r in roots:
        clean(r)
    return roots, len(nodes)


def build(csv_path, out_path, titel="Classificatie RI", vlabel="5.0"):
    """Lees de classificatie-CSV en schrijf de interactieve HTML-pagina.
    Geeft (aantal objecten, aantal roots) terug."""
    proto = open(PROTO, encoding="utf-8").read()
    prefix = proto.split('<div class="app">')[0]
    # titel in de <h1> vervangen (eerste h1 binnen .site-header)
    prefix = prefix.replace("<h1>Classificatie RI</h1>", "<h1>" + titel + "</h1>")
    prefix = prefix.replace("Prototype · voorbeelddata",
                            "NLCS " + str(vlabel) + " · classificatie")
    roots, n = build_tree(csv_path)
    data = json.dumps(roots, ensure_ascii=False)
    html = (prefix +
            '<div class="app">\n'
            '  <nav class="pane tree-pane" aria-label="Objectboom">\n'
            '    <p class="pane-label">Objecten (' + str(n) + ', op naam)</p>\n'
            '    <input type="search" id="treesearch" class="treesearch" '
            'placeholder="Zoek objectnaam (deel van de naam)…" '
            'autocomplete="off" spellcheck="false" aria-label="Zoek objectnaam">\n'
            '    <p class="nohits" id="nores" hidden>Geen objecten gevonden.</p>\n'
            '    <ul class="tree" id="tree"></ul>\n  </nav>\n'
            '  <section class="pane detail-pane" aria-live="polite">\n'
            '    <div id="detail"></div>\n  </section>\n</div>\n'
            '<script>\nconst TREE=' + data + ';\n' + RENDER_JS + '\n</script>\n'
            '</body>\n</html>\n')
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(html)
    return n, len(roots)


def main():
    csv_path = sys.argv[1]
    out_path = sys.argv[2]
    titel = sys.argv[3] if len(sys.argv) > 3 else "Classificatie RI"
    vlabel = sys.argv[4] if len(sys.argv) > 4 else "5.0"
    n, roots = build(csv_path, out_path, titel, vlabel)
    print("Geschreven:", out_path, "(" + str(n) + " objecten,", roots, "roots)")


if __name__ == "__main__":
    main()
