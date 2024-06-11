// file and path  : algemeen/vertoonrichtlijn.js
// version release: 19-03-2003
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


function VertoonRichtlijn(a) {                   //Vertoon gegevens van een richtlijn
  var b,c,d,e,f,g,h,i,j,k,m,n,p,q,r,s,t,u,v
  kn=new Array                                     //array voor kleurnummers

  d=parent.database.GeefIndexUitSorteerLijst(a)
  document.write('<p><hr><p>')
  document.write('<table border=0 cellpadding=5 cellspacing=0>')
  document.write('<colgroup><col width=30%><col width=5%><col width=65%></colgroup>')
  document.write('<tr align=left valign=top><th><font type=arial  color=black>Naam of omschrijving<td>:<td><font color=black><B>'+parent.database.GeefElement(d))
  document.write('<tr align=left valign=top><th><font type=arial  color=black>Revisiedatum        <td>:<td><font color=black><B>'+parent.database.GeefDatum(d))
  document.write('</td></tr>')
  document.write('</table><br>')
  document.write('<table border=1 cellspacing=0 cellpadding=3>')
  document.write('<tr align=left>')
  document.write('<th width=130>&nbsp;')
  document.write('<th width=120 colspan=5><font size=3 type=arial color=black><a href="../../../'+disc+'/richtlijnen/algemeen/lijndikte.html">lijndikte (mm)</a></font>')
  document.write('<th width=120 colspan=5><font size=3 type=arial color=black><a href="../../../algemeen/richtlijnen/algemeen/kleur.html">lijnkleur</a></font>')
  document.write('<th width=120 colspan=5><font size=3 type=arial color=black><a href="../../../'+disc+'/richtlijnen/algemeen/lijnen.html"><font size=3 type=arial>lijntype</a></font>')

                                               
// eerste deel 

  document.write('<tr align=left>')
  document.write('<th width=220 height=40><font size=3 type=arial>bestaand    </font>')
  c=parent.database.GeefLengte7KleurenSchema()
  f=parent.database.GeefPenKleur(d,1)
  h="&nbsp;"
  if (f!="") {                                   // (er is een kleurnummer gedefinieerd)
    g=0
    while (h=="&nbsp;" & g<c) {                       // (loop records van het 7-kleurenschema af)
      i=parent.database.GeefRecord7KleurenSchema(g)
      j=i.length
      k=i.indexOf(":")+1
      n=k-1
      m=0
      while (m!=j & h=="&nbsp;") {                    // (loop kleurnummers uit het record af)
        m=i.indexOf(";",k);if (m==-1) m=j
        p=i.substring(k,m)
        p++;p--                                 // (truukje om van q een getal te maken; q kan een spatie bevatten)
        if (f==p) h=i.substring(0,n)             // (kleurnummer gevonden in record: ken aan i de lijndikte toe)
        k=m+1
      }
      g++
    }
    document.write('<td width=120 colspan=5><font size=3 type=arial>'+h+'</font></td>')
    e=parent.database.GeefKleur(d,1)
    if (e!="") {
      f=parent.database.GeefKleurCode(e)
      g="#"+f.substring(0,5)                      // (isoleer hexadecimale RGB-waarde van de kleur)
      h="";if (f.charAt(6)=="*") h=" color=white" // (ga na of kleurnummer in zwart of wit moet staan)
      e="&nbsp;"
      document.write('<td width=120 colspan=5 bgcolor='+g+'><font size=1 type=arial'+h+'>'+e+'</font></td>')
    }
    else {
      document.write('<td width=120 colspan=5>&nbsp;</td>')           // (er is geen kleur)
    }
    c=parent.database.GeefLijntype(d)
    document.write('<td width=480 colspan=5>')
    g=c.indexOf(",")                             // (Er kunnen meerdere lijnen zijn)
    i=c.length
    if (g!=-1) {
    i=g
  }
    SL=c.substring(0,i)
    if (e!=0) {
      document.write('<img src="../../../images/lijnen/'+SL+'.gif" alt="rtw lijntype">'+SL+'</td>')
    }
    else {
      document.write('&nbsp;</td>')
    }
    f++

// derde deel 

  document.write('<tr align=left>')
  document.write('<th width=220 height=40><font size=3 type=arial>nieuw</font>')
  c=parent.database.GeefLengte7KleurenSchema()
  f=parent.database.GeefPenKleur(d,3)
  h="&nbsp;"
  if (f!="") {                                   // (er is een kleurnummer gedefinieerd)
    g=0
    while (h=="&nbsp;" & g<c) {                       // (loop records van het 7-kleurenschema af)
      i=parent.database.GeefRecord7KleurenSchema(g)
      j=i.length
      k=i.indexOf(":")+1
      n=k-1
      m=0
      while (m!=j & h=="&nbsp;") {                    // (loop kleurnummers uit het record af)
        m=i.indexOf(";",k);if (m==-1) m=j
        p=i.substring(k,m)
        p++;p--                                 // (truukje om van q een getal te maken; q kan een spatie bevatten)
        if (f==p) h=i.substring(0,n)             // (kleurnummer gevonden in record: ken aan i de lijndikte toe)
        k=m+1
      }
      g++
    } 
  }
  document.write('<td width=120 colspan=5><font size=3 type=arial>'+h+'</font></td>')
  e=parent.database.GeefKleur(d,3)
  if (e!="") {
    f=parent.database.GeefKleurCode(e)
    g="#"+f.substring(0,5)                      // (isoleer hexadecimale RGB-waarde van de kleur)
    h="";if (f.charAt(6)=="*") h=" color=white" // (ga na of kleurnummer in zwart of wit moet staan)
    e="&nbsp;"
    document.write('<td width=120 colspan=5 bgcolor='+g+'><font size=1 type=arial'+h+'>'+e+'</font></td>')
    }
    else {
      document.write('<td width=120 colspan=5>&nbsp;</td>')           // (er is geen kleur)
    }
    c=parent.database.GeefLijntype(d)
    document.write('<td width=480 colspan=5>')
    g=c.indexOf(",")                             // (Er kunnen meerdere lijnen zijn)
    i=c.length
    if (g!=-1) {
    i=g
  }
    SL=c.substring(0,i)
    if (e!=0) {
      document.write('<img src="../../../images/lijnen/'+SL+'.gif" alt="rtw lijntype">'+SL+'</td>')
    }
    else {
      document.write('&nbsp;</td>')
    }
    f++

// tweede deel 

  document.write('<tr align=left>')
  document.write('<th width=220 height=40><font size=3 type=arial>verwijderen</font>')
  c=parent.database.GeefLengte7KleurenSchema()
  f=parent.database.GeefPenKleur(d,2)
  h="&nbsp;"
  if (f!="") {                                   // (er is een kleurnummer gedefinieerd)
    g=0
    while (h=="&nbsp;" & g<c) {                       // (loop records van het 7-kleurenschema af)
      i=parent.database.GeefRecord7KleurenSchema(g)
      j=i.length
      k=i.indexOf(":")+1
      n=k-1
      m=0
      while (m!=j & h=="&nbsp;") {                    // (loop kleurnummers uit het record af)
        m=i.indexOf(";",k);if (m==-1) m=j
        p=i.substring(k,m)
        p++;p--                                 // (truukje om van q een getal te maken; q kan een spatie bevatten)
        if (f==p) h=i.substring(0,n)             // (kleurnummer gevonden in record: ken aan i de lijndikte toe)
        k=m+1
      }
      g++
    } 
  }
  document.write('<td width=120 colspan=5><font size=3 type=arial>'+h+'</font></td>')
  e=parent.database.GeefKleur(d,2)
  if (e!="") {
    f=parent.database.GeefKleurCode(e)
    g="#"+f.substring(0,5)                      // (isoleer hexadecimale RGB-waarde van de kleur)
    h="";if (f.charAt(6)=="*") h=" color=white" // (ga na of kleurnummer in zwart of wit moet staan)
    e="&nbsp;"
    document.write('<td width=120 colspan=5 bgcolor='+g+'><font size=1 type=arial'+h+'>'+e+'</font></td>')
  }
  else {
    document.write('<td width=120 colspan=5>&nbsp;</td>')           // (er is geen kleur)
  }
  c=parent.database.GeefLijntype(d)
  SL=new Array
  document.write('<td width=480 colspan=5>')
  g=c.indexOf(",")                             // (Er kunnen meerdere lijnen zijn)
  i=c.length
  aantal=0
  if (g==-1) {
    g=i
    aantal=1
  }
  h=0
  f=0
  while (g!=i) {
    SL[f]=c.substring(h,g)
    f++
    h=g+1
    g=c.indexOf(",",h)
    if (g==-1) g=i
  }
  SL[f]=c.substring(h,g)
  if (e!="") {
    document.write('<img src="../../../images/lijnen/'+SL[f]+'.gif" alt="rtw lijntype">'+SL[f]+'</td>')
  }
  else {
    document.write('&nbsp;</td>')
  }
  f++


// vierde deel 

  document.write('<tr align=left>')
  document.write('<th width=220 height=40><font size=3 type=arial>algemeen</font>')
  c=parent.database.GeefLengte7KleurenSchema()
  f=parent.database.GeefPenKleur(d,4)
  h="&nbsp;"
  if (f!="") {                                   // (er is een kleurnummer gedefinieerd)
    g=0
    while (h=="&nbsp;" & g<c) {                       // (loop records van het 7-kleurenschema af)
      i=parent.database.GeefRecord7KleurenSchema(g)
      j=i.length
      k=i.indexOf(":")+1
      n=k-1
      m=0
      while (m!=j & h=="&nbsp;") {                    // (loop kleurnummers uit het record af)
        m=i.indexOf(";",k);if (m==-1) m=j
        p=i.substring(k,m)
        p++;p--                                 // (truukje om van q een getal te maken; q kan een spatie bevatten)
        if (f==p) h=i.substring(0,n)             // (kleurnummer gevonden in record: ken aan i de lijndikte toe)
        k=m+1
      }
      g++
    } 
  }
  document.write('<td width=120 colspan=5><font size=3 type=arial>'+h+'</font></td>')
  e=parent.database.GeefKleur(d,4)
  if (e!="") {
    f=parent.database.GeefKleurCode(e)
    g="#"+f.substring(0,5)                      // (isoleer hexadecimale RGB-waarde van de kleur)
    h="";if (f.charAt(6)=="*") h=" color=white" // (ga na of kleurnummer in zwart of wit moet staan)
    e="&nbsp;"
    document.write('<td width=120 colspan=5 bgcolor='+g+'><font size=1 type=arial'+h+'>'+e+'</font></td>')
    }
    else {
    document.write('<td width=120 colspan=5>&nbsp;</td>')           // (er is geen kleur)
    }
    c=parent.database.GeefLijntype(d)
    document.write('<td width=480 colspan=5>')
    g=c.indexOf(",")                             // (Er kunnen meerdere lijnen zijn)
    i=c.length
    if (g!=-1) {
    i=g
  }
    SL=c.substring(0,i)
    if (e!="") {
      document.write('<img src="../../../images/lijnen/'+SL+'.gif" alt="rtw lijntype">'+SL+'</td>')
    }
    else {
      document.write('&nbsp;</td>')
    }
    f++
  }
  document.write('</table>')

  c=parent.database.GeefLayer(d)
  b=StelMXAanduidingenSamen(d,c)
  test=0
  cc=parent.database.GeefArceringen(d)
  if (cc!="") test=1
  cc=parent.database.GeefSymbolen(d)
  if (cc!="") test=1
  if (test==1) {
    document.write('<br>')
    document.write('<table border=0 cellpadding=5 cellspacing=0>')
    document.write('<colgroup><col width=30%><col width=5%><col width=65%></colgroup>')
    document.write('<tr align=left valign=top><th><font size=3 type=arial color=black><b>Verschijningsvormen<td>:<td>&nbsp;</font>')
    document.write('</table>')
  }

  document.write('<br>')
  document.write('<table border=1 cellspacing=0 cellpadding=3>')
  c=parent.database.GeefArceringen(d)             // (Zet eventuele arceringen in de tabel)
  if (c!="") {
    document.write('<tr align=left valign=top><th width=115 height=40><a href="../../../algemeen/arceringen.html"><font size=3 type=arial>arcering(en)</font></a>')
    document.write('<td width= 480 colspan=15>')
    e=c.length
    g=0
    i=0
    while (i==0) {
      f=c.indexOf(",",g);if (f==-1) f=e
      h=c.substring(g,f)
      p=parent.database.GeefHatchCode(h)     // (zoek symbool op in tabel met hatchdefinities WP)
      l=p.length
      q=p.substring(0,79)
      document.write('<img src="../../../images/arceringen/'+h+'.gif" alt="Nog nader te bepalen."><br> '+q+'<br>')
      if (f==e) i=1
      g=f+1
    }
  }
  c=parent.database.GeefSymbolen(d)             // (Zet eventuele symbolen in de tabel)
  if (c!="") {
    document.write('<tr align=left valign=top><th width=115 height=40><a href="../../../algemeen/richtlijnen/algemeen/symbolen.html">symbool</font></a>')
    document.write('<td width=480 colspan=15>')
    e=c.length
    g=0
    i=0
    while (i==0) {
      f=c.indexOf(",",g);if (f==-1) f=e
      h=c.substring(g,f)
      p=parent.database.GeefSymboolCode(h)     // (zoek symbool op in tabel met kleurdefinities WP)
      l=p.length
      q=p.substring(3,79)
      document.write('<img src="../../../images/symbolen/'+h+'.gif" alt="Nog nader te bepalen."><br> '+q+'<br>')
      if (f==e) i=1
      g=f+1
    }
  }
  document.write('</table>')

  var lb,lbu
  d=parent.database.GeefIndexUitSorteerLijst(a)
  document.write('<p>')
  document.write('<table border=0 cellpadding=5 cellspacing=0>')
  document.write('<colgroupd><col width=85%><col width=5%><col width=10%></colgroup>')
  opm=parent.database.GeefOpmerking(d)
  if (opm != "") {
    document.write('<tr align=left valign=top><th><font color=black>Opmerkingen     <td> <td><font color=black><b></b>')
    document.write('<tr align=left valign=top><th><font color=black><b>'+opm+'</b>')
  }
  document.write('</table>')
  document.write('<p>')
  document.write('<a href="acad_basis.html"><font type=arial>AutoCAD</font><BR></a>')
  if (b!=" ") {
    //wp document.write('<a href="mx_basis.html"><font type=arial>MX</font></a>')
  }
}


