// file and path  : algemeen/mx_vertoonrichtlijn.js
// version release: 29-07-2002
// designer       : C.J.F. Rothfusz
// company        : Tree C Technology B.V.

function TelRecords(a) {                         //Maak een lijst van records die naar bestand a wijzen...
 var b,c                                         //en tel deze records.
 parent.database.VerzamelGelijkeBestanden(a)
 b=0
 c=parent.database.GeefIndexUitSorteerLijst(b)
 while(c!=-1) {
   b++
   c=parent.database.GeefIndexUitSorteerLijst(b)
 }
 return b
}


function StelMXAanduidingenSamen(a,b) {          //Plak derde deel layernaam achter modelnaam en zet
 var c,d,e,f,g,h,i,j,k,m,n,p,q,r                 //daarachter tussen haakjes de string.
 m=""
 c=parent.database.GeefModel(a)
 if (c!="") {                                    // (er is inderdaad een mx-model)
   n=b.indexOf("-")+1                            // (isoleer derde deel van de layernaam)
   p=b.indexOf("-",n)+1
   q=b.length
   r=b.substring(p,q)
   d=parent.database.GeefString(a)               // (bereid de loop voor waarin gekeken wordt of er...
   e=c.length                                    // (nog meer modellen zijn)
   f=d.length
   g=c.indexOf(",");if (g==-1) g=e
   h=d.indexOf(",");if (h==-1) h=f
   i=0
   j=0
   k=0                                           // (vlag als stopcriterium)
   while (k!=1) {                                // (plak aanduidingen achter elkaar)
    m += c.substring(i,g)+"-"+r+" (string "+d.substring(j,h)+" )<br>"
    if (g==e) k=1                                // (einde van modellenreeks is bereikt)
    i=g+1
    j=h+1
    g=c.indexOf(",",i);if (g==-1) g=e
    h=d.indexOf(",",j);if (h==-1) h=f
   }
  }
  else {                                         // (er is geen mx-model)
   m=" "
  }
 return m
}

function mx_vertoonrichtlijn(a) {                   //Vertoon gegevens van een richtlijn
  var b,c,d,e,f,g,h,i,j,k,m,n,p,q,r,s,t,u,v
  d=parent.database.GeefIndexUitSorteerLijst(a)
  c=parent.database.GeefLayer(d)
  b=StelMXAanduidingenSamen(d,c)
  document.write('<p><hr><p>')
  document.write('<table border=0 cellpadding=5 cellspacing=0>')
  document.write('<colgroup><col width=30%><col width=5%><col width=65%></colgroup>')
  document.write('<tr align=left valign=top><th><font color=black>Naam of omschrijving<td>:<td><font color=black><B>'+parent.database.GeefElement(d))
  document.write('<tr align=left valign=top><th><font color=black>Revisiedatum        <td>:<td><font color=black><B>'+parent.database.GeefDatum(d))
  document.write('<tr align=left valign=top><th><font color=black>MX Layer (String)   <td>:<td><font color=black><B>'+b)
  //wp document.write('<tr align=left valign=top><th><font color=black>AutoCAD Laagnaam    <td>:<td><font color=black><B>'+parent.database.GeefLayer(d))
  document.write('</table>')
  document.write('<p>')
  pos_ster=c.lastIndexOf('*')+1
  document.write('<table border=0 cellpadding=5 cellspacing=0>')
  opm=parent.database.GeefOpmerking(d)
  if (opm != "") {
    document.write('<tr align=left valign=top><th><font color=black>Opmerking           <td>:<td><font color=black>'+opm)
  }
  if (pos_ster != 0) {
    if (pos_ster == 4) {
      document.write('<tr align=left valign=top><th><font color=black>Legenda           <td>:<td><font color=black>Bij de AutoCAD laagnaam moet op de positie van de ster afhankelijk van de situatie, bs (bestaand), vw (verwijderen), nw (nieuw) of xx (algemeen) ingevuld worden')
    }
    if (pos_ster == 3) {
      document.write('<tr align=left valign=top><th><font color=black>Legenda           <td>:<td><font color=black>Bij de AutoCAD laagnaam moet op de positie van de tweede ster afhankelijk van de situatie, bs (bestaand), vw (verwijderen), nw (nieuw) of xx (algemeen) ingevuld worden')
    }
  }
  document.write('</table>')
}
