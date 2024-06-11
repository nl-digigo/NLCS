// file and path  : functies.js
// version        : 2.1
// version release: 18-04-2001
// version release: 21-05-2001
// designer       : C.J.F. Rothfusz
// company        : Tree C Technology B.V.

//Dit bestand definieert functies ten behoeve van gegevensuitwisseling tussen website en database.

//Inhoud:  ALGEMENE FUNCTIES
//         FUNCTIES VOOR AUTOCADKLEUREN
//         FUNCTIES VOOR LIJNDIKTE/KLEURSCHEMA'S
//         FUNCTIES VOOR PROJECTFASEN
//         FUNCTIES VOOR TEKENINGEN
//         FUNCTIES VOOR LAYERHOOFDGROEPEN
//         FUNCTIES VOOR MX-MODELLEN
//         FUNCTIES VOOR TEKENINGELEMENTEN
//         FUNCTIES VOOR AANDACHTSPUNTEN


//ALGEMENE FUNCTIES

  function SchrijfCookie(koekje) {               //Bewaar een waarde in een cookie.
    document.cookie=koekje                       // (koekje kan bijvoorbeeld zijn: "keuze=3")
  }

  function LeesCookie(koekje) {                  //Zoek het opgegeven cookie in het cookiebestand
    var i,j                                      //en lees de waarde ervan. (koekje kan bijvoorbeeld
                                                 //zijn: "keuze=". Het resultaat is dan 3).
    var k=""
    if (document.cookie.length > 0) {            // (Als cookiesbestand bestaat,...)
      i=document.cookie.indexOf(koekje)          // (zoek opgegeven cookie.)
      if (i!=-1) {                               // (Als opgegeven cookie bestaat,...)
        i += koekje.length
        j=document.cookie.indexOf(";",i)         // (zoek scheiding met volgende cookie,...)
        if (j==-1) j=document.cookie.length      // (tenzij cookie de laatste in het bestand was.)
        k=document.cookie.substring(i,j)         // (Isoleer de waarde van het cookie.)
      }
    }
    return k
  }


  function GeefAlgemeneLijntypen() {             //Geef de algemene lijntypen.
   return AlgemeneLijntypen
  }  
  
  
//FUNCTIES BIJ ARRAY AUTOCADKLEUREN

  function GeefKleurCode(i) {                    //Zoek kleurnummer in array en geef kleurinformatie terug.
    var x,y,z,u                                  // (GeefKleurCode(3) geeft bijvoorbeeld "00FF00 3").
    x=0
    u=0                                          // (Vlag om er voor te zorgen dat index x niet 'uit array loopt')
    z=KL.length-1
    y=KL[x].length
    while (i!=KL[x].substring(7,y) & u==0) {     // (Zoek kleurnummer in arrayelementen totdat...)
     if (x<z) {x++}                              // (deze gevonden is of het laatste element is...)
       else {u=1}                                // (bereikt).
     y=KL[x].length
    }
    return KL[x]
  }

//FUNCTIES BIJ ARRAY SYMBOLEN

  function GeefSymboolCode(i) {                    //Zoek symbool in array en geef informatie terug.
    var a,x,y,z,u                                  //(GeefSymCode(xxx) geeft bijvoorbeeld "xxxomschrijving   xxx").
    x=0
    u=0                                            // (Vlag om er voor te zorgen dat index x niet 'uit array loopt')
    z=SYM.length-1
    y=SYM[x].length
   while (i!=SYM[x].substring(79,y) & u==0) {      // (Zoek symbool in arrayelementen totdat...)
     if (x<z) {x++}                                // (deze gevonden is of het laatste element is...)
       else {u=1}                                  // (bereikt).
     y=SYM[x].length
    }
    return SYM[x]
  }

//FUNCTIES BIJ ARRAY HATCH

  function GeefHatchCode(i) {                      //Zoek Hatch in array en geef informatie terug.
    var a,x,y,z,u                                  //(GeefHatchCode(xxx) geeft bijvoorbeeld "xxxomschrijving   xxx").
    x=0
    u=0                                            // (Vlag om er voor te zorgen dat index x niet 'uit array loopt')
    z=HATCH.length-1
    y=HATCH[x].length
   while (i!=HATCH[x].substring(79,y) & u==0) {      // (Zoek hatch in arrayelementen totdat...)
     if (x<z) {x++}                                // (deze gevonden is of het laatste element is...)
       else {u=1}                                  // (bereikt).
     y=HATCH[x].length
    }
    return HATCH[x]
  }


//FUNCTIES BIJ LIJNDIKTE/KLEURENSCHEMA'S

//7-kleurenschema
  function GeefLengte7KleurenSchema() {          //Geef het aantal arrayelementen van het 7-kleurenschema.
    var a
    a=K7.length
    return a
  }

  function GeefRecord7KleurenSchema(i) {         //Geef arrayelement i van het 7-kleurenschema.
    return K7[i]
  }
 
//256-kleurenschema

  function GeefLengte256KleurenSchema() {        //Geef het aantal arrayelementen van het 7-kleurenschema.
    var a
    a=K256.length
    return a
  }

  function GeefRecord256KleurenSchema(i) {       //Geef arrayelement i van het 7-kleurenschema.
    return K256[i]
  }


//FUNCTIES BIJ ARRAY PROJECTFASE

  function GeefAantalProjectfasen() {            //Geef aantal arrayelementen van de array met projectfasen.
    var a
    a=PF.length
    return a
  }

  function GeefProjectfase(i) {                  //Geef arrayelement i uit de array met projectfasen.
   return PF[i]
  }


//FUNCTIES BIJ ARRAY TEKENINGEN

  function GeefAantalTekeningen() {              //Geef het aantal arrayelementen van de array met tekeningen.
    var a
    a=T.length
    return a
  }

  function GeefTekening(i) {                     //Geef tekeningnaam uit arrayelement i van
    var x,y                                      //array met tekeningen.
    x=T[i].indexOf(":")
    y=T[i].substring(0,x)                        // (Laat deel na eerste scheidingsteken weg)
    return y
  }

  function GeefTekCode(i) {                      //Geef tekeningcode (ten behoeve van aandachtspunten)
    var x,y,z
    x=T[i].indexOf(":")+1
    y=T[i].indexOf(":",x)+1                      // (zoek achter tweede scheidingsteken)
    z=T[i].length
    x=T[i].substring(y,z)
    return x
  }

  function TekeningInProjectfase(x,y) {          //Beschouw de tekens tussen de twee scheidingstekens ":"
    var i                                        //als een maytrix. Geef het teken op rij x (tekeningnummer)
    var j="+"                                    //en kolom y (projectfase). Een - betekent dat
    if (y!=-1) {                                 //de tekening niet voorkomt in de projectfase.
      i=y*2+T[x].indexOf(":")+1                  //Een + betekent dat de tekening wel voorkomt,
      j=T[x].charAt(i)                           //of dat er geen projectfase was geselecteerd (y=-1).
    }
    return j
  }


//FUNCTIES BIJ ARRAY LAYERHOOFDGROEPEN

  function GeefAantalLayergroepen() {            //Geef het aantal arrayelementen van de array met layerhoofdgroepen.
    var a
    a=G.length
    return a
  }

  function GeefHoofdgroep(i) {                   //Geef arrayelement i uit de array met layerhoofdgroepen.
    return G[i]
  }

  function GeefIndexHoofdgroep(i) {              //Geef de index van het arrayelement dat begint
    var a,b,c                                    //met afkorting i van de hoofdgroep (2 letters).
    c=-1                                         // (GeefIndexHoofdgroep('af') geeft bijvoorbeeld 1)
    a=GeefAantalLayergroepen()
    if (i.charAt(0)=="*") {c=0}                  // (Een speciaal geval is "*" welke staat voor...
     else {                                      // (alle hoofdgroepen. Hierbij gat het niet om...
       for (b=0;b<a;b++) {                       // (2 letters maar om 1 teken)
         if (i==G[b].substring(0,2)) c=b
       }
     }
    return c
  }


//FUNCTIES BIJ ARRAY MX-MODELLEN

  function GeefAantalMxModellen() {              //Geef het aantal arrayelementen van de array met mx-modellen.
    var a
    a=MM.length
    return a
  }

  function GeefMxModel(i) {                      //Geef arrayelement i uit de array met mx-modellen.
   return MM[i]
  }


//FUNCTIES BIJ RECORDS TEKENINGELEMENTEN

 SL=new Array                                    //Array voor sorteeropdrachten. Bevat te sorteren tekst, gevolgd door ":" en recordnummer.

 function GeefAantalRecords() {                  //Geef het aantal records met tekeningelementen.
   var a
   a=E.length
   return a
 }

 function GeefElement(i) {                       //Geef veld met elementnaam uit record i.
   return E[i]
 }

 function GeefBestand(i) {                       //Geef bestandsnaam van element uit record i.
   var x
   x=B[i]+".html"
   return x
 }

 function GeefModel(i) {                         //Geef veld met modelnaam/namen uit record i.
   return M[i]
 }

 function GeefString(i) {                        //Geef veld met string(s) uit record i.
   return S[i]
 }

 function GeefLayer(i) {                         //Geef veld met layernaam uit record i.
   return LA[i]
 }

 function GeefLijntype(i) {                      //Geef lijntype uit record i.
  var a,b
  b=L[i]
  a=b.indexOf(":")
  if (a!=-1) b=L[i].substring(0,a)               // (strip eventuele arceringen en symbolen)
  return b
 }

 function GeefArceringen(i) {                    //Geef eventuele arceringen uit veld L van record i.
  var a,b,c,d
  d=""
  a=L[i]
  b=a.indexOf(":")                               // (zoek begin arceringen)
  if (b!=-1) {
   c=a.indexOf(":",b+1)
   if (c==-1) {c=a.length}
   d=a.substring(b+1,c)
  }
  return d
 }

 function GeefSymbolen(i) {                      //Geef eventuele symbolen uit veld L van record i.
  var a,b,c,d,e
  e=""
  a=L[i]
  b=a.indexOf(":")                               // (zoek begin arceringen)
  if (b!=-1) {
   c=a.indexOf(":",b+1)                          // (zoek begin symbolen)
   if (c!=-1) {
    d=a.length
    e=a.substring(c+1,d)
   }
  }
  return e
 }

 function GeefKleur(i,j) {                       //Geef veld met kleurnummer uit record i.
   var x
   if (j==1) x=Kbs[i]                            // (Als j=1 dan kleurnummer bestaand)
   if (j==2) x=Kvw[i]                            // (Als j=2 dan kleurnummer verwijderen)
   if (j==3) x=Knw[i]                            // (Als j=3 dan kleurnummer nieuw)
   if (j==4) x=Kxx[i]                            // (Als j=4 dan kleurnummer algemeen)
   return x
 }

 function GeefPenKleur(i,j) {                    //Geef veld met pen uit record i.
   var x
   if (j==1) x=Lbs[i]                            // (Als j=1 dan pen bestaand)
   if (j==2) x=Lvw[i]                            // (Als j=2 dan pen verwijderen)
   if (j==3) x=Lnw[i]                            // (Als j=3 dan pen nieuw)
   if (j==4) x=Lxx[i]                            // (Als j=4 dan pen algemeen)
   return x
 }
 
 function GeefDatum(i) {                         //Geef veld met revisiedatum uit record i.
   return D[i]
 }

 function GeefOpmerking(i) {                     //Geef veld met opmerkingen (x) uit record i.
   return X[i]
 }

function GeefOpmerkingAcad(i) {                  //Geef veld met opmerkingen Acad (Y) uit record i.
   return Y[i]
 }
 
function GeefIndexBeginGroep(i) {               //Geef de index van het eerste record waarin
  var x,y                                        //layergroep i voorkomt. Hierbij is i zelf ook
  y=0                                            //een index, die verwijst naar een arrayelement
  if (i!=0) {                                    //uit de array met layergroepen.
    x=G[i].substring(0,2)                        // (Als i=0 dan wordt per definitie het eerste...)
    while (LA[y].substring(0,2)!=x) y++          // (record bedoeld)
  }
  return y
 }

 function GeefIndexEindGroep(i) {                //Geef de index van het laatste record waarin
  var u,v,w                                      //layergroep i voorkomt. Hierbij is i zelf ook
  u=GeefIndexBeginGroep(i)                       //een index, die verwijst naar een arrayelement
  v=LA[u].substring(0,2)                         //uit de array met layergroepen.
  w=GeefAantalRecords()-1
  u++
  while ((u<w) & LA[u].substring(0,2)==v) u++
  if (u<w) u--                                   // (laatste element wordt verondersteld geen...
  return u                                       // (nieuwe groep te zijn. Deze constructie is...
 }                                               // (nodig om te voorkomen dat index u 'uit de array loopt')

 function ZoekStringsVanModel(i) {               //Verzamel de strings van model i in de array
  var h=0                                        //voor sorteeropdrachten en sorteer alfabetisch.
  var a,b,c,d,e,f,g,h,j,k,y,z                    //(i is zelf ook een index die verwijst naar een
  a=MM[i].substring(0,3)                         //arrayelement uit de array met mx-modellen)
  j=GeefAantalRecords()
  for (t=0;t<j;t++) {                            // (Doorzoek alle records...)
   b=M[t].indexOf(a)                             // (kijk of modelnaam in het record voorkomt....)
   if (b!=-1) {                                  // (Modelnaam komt inderdaad voor)
    y=t
    c=0                                          // (Zoek naar bijbehorende string)
    d=0
    e=M[t].length
    f=S[t].length
    g=M[t].indexOf(",");if (g==-1) g=e
    k=S[t].indexOf(",");if (k==-1) k=f
    while (M[t].substring(c,g)!=a) {             // (Zoek modelnaam en bijbehorende string...)
     c=g+1                                       // (ook achter de komma's)
     d=k+1
     g=M[t].indexOf(",",c);if (g==-1) g=e
     k=S[t].indexOf(",",d);if (k==-1) k=f
    }
    z=S[t].substring(d,k)
    SL[h]=z+":"+y                                // (Bewaar string en recordnummer -gescheiden ...
    h++                                          // (met dubbele punt- in sorteerarray)
   }
  }
  x=SL.length
  for (y=h;y<x;y++) SL[y]="~"                    // (Verwijder oude gegevens uit rest sorteerarray...)
  SL.sort()                                      // (en zorg dat dit stuk array ook na sorteren...)
 }                                               // (achteraan blijft staan)

 function VerzamelElementen(i,j) {               //Verzamel de elementnamen van record i t/m j in
  var a,b,c                                      //de sorteerarray en sorteer alfabetisch. 
  for (a=i;a<=j;a++) {
    SL[a-i]=E[a].toLowerCase()+":"+a             // (I.v.m. sorteren alles in kleine letters)
  }
  b=SL.length
  for (c=a-i;c<b;c++) SL[c]="~"                  // (Verwijder oude gegevens uit rest sorteerarray...)
  if (SL[c-1]!="~") SL[c]="~"                    // (en zorg dat dit stuk array ook na sorteren...)
  SL.sort()                                      // (achteraan blijft staan. Laatste gegeven moet...)
 }                                               // (altijd "~" zijn t.b.v. eindmarkering)

 function VerzamelGelijkeBestanden(i) {          //Maak een lijst van alle records die naar bestand i wijzen.
  var a,b,c,d
  a=i.indexOf(".html")
  if (a==-1) i += ".html"
  a=GeefAantalRecords()
  b=0
  for (c=0;c<a;c++) {
   d=GeefBestand(c)
   if (d==i) {
    SL[b]=" :"+c                                // (spatie in dubbele punt is nodig ! Zie GeefIndexUitSorteerLijst)
    b++
   }
  }
  SL[b]="~"
 }

function VerzamelLijntypen() {                  //Verzamel de lijntypen uit de records.
  var a,b,c,d,e,f,g,h,i,j
  j=GeefAlgemeneLijntypen()                      // ( algemene lijntypen worden niet meegenomen)
  a=GeefAantalRecords()
  f=0
  for (b=0;b<a;b++) {
    c=GeefLijntype(b)
    if (c!="") {
      g=c.indexOf(",")                             // (Er kunnen meerdere lijnen zijn)
      i=c.length
      if (g==-1) g=i
      h=0
      while (g!=i) {
        if (j.indexOf(c)==-1) {
          SL[f]=c.substring(h,g)+":"+b
          f++
          h=g+1
          g=c.indexOf(",",h)
          if (g==-1) g=i
        }
      }
	  if (c.substring(0,10) != "continuous") {
        SL[f]=c.substring(h,g)+":"+b
        f++
      }
    }
  }
  d=SL.length
  for (e=f;e<d;e++) SL[e]="~"                    // (Zie VerzamelElementen)
  if (SL[e-1]!="~") SL[e]="~"
  SL.sort()
}

 

 function VerzamelArceringen() {                 //Verzamel de arceringstypen uit de records.
  var a,b,c,d,e,f,g,h,i
  a=GeefAantalRecords()
  f=0
  for (b=0;b<a;b++) {
   c=GeefArceringen(b)
   if (c!="") {
    g=c.indexOf(",")                             // (Er kunnen meerdere arceringen zijn)
    i=c.length
    if (g==-1) g=i
    h=0
    while (g!=i) {
      SL[f]=c.substring(h,g)+":"+b
      f++
      h=g+1
      g=c.indexOf(",",h)
      if (g==-1) g=i
    }
    SL[f]=c.substring(h,g)+":"+b
    f++
   }
  }
  d=SL.length
  for (e=f;e<d;e++) SL[e]="~"                    // (Zie VerzamelElementen)
  if (SL[e-1]!="~") SL[e]="~"
  SL.sort()
 }

 function VerzamelSymbolen() {                   //Verzamel de symbolen uit de records.
  var a,b,c,d,e,f,g,h,i
  a=GeefAantalRecords()
  f=0
  for (b=0;b<a;b++) {
   c=GeefSymbolen(b)
   if (c!="") {
    g=c.indexOf(",")                             // (Er kunnen meerdere arceringen zijn)
    i=c.length
    if (g==-1) g=i
    h=0
    while (g!=i) {
      SL[f]=c.substring(h,g)+":"+b
      f++
      h=g+1
      g=c.indexOf(",",h)
      if (g==-1) g=i
    }
    SL[f]=c.substring(h,g)+":"+b
    f++
   }
  }
  d=SL.length
  for (e=f;e<d;e++) SL[e]="~"                    // (Zie VerzamelElementen)
  if (SL[e-1]!="~") SL[e]="~"
  SL.sort()
 }

 function GeefIndexUitSorteerLijst(i) {          //Geef het recordnummer in arrayelement i van de
  var a,b,c,d                                    //sorteerarray.
  a=SL.length
  b=-1
  if (i<a) {
   if (SL[i]!="~") {
    c=SL[i].indexOf(":")+1                        // (Het recordnummer staat achter het scheidingsteken)
    d=SL[i].length
    b=SL[i].substring(c,d)
   }
  }  
  return b
 }

 function GeefTekstUitSorteerLijst(i) {          //Geef de tekst uit arrayelement i van de
  var a,b,c                                      //sorteerarray.
  a=SL.length
  b=""
  if (i<a) {
   if (SL[i]!="~") {
    c=SL[i].indexOf(":")                         // (De tekst staat voor het scheidingsteken)
    b=SL[i].substring(0,c)
   }
  }
  return b
 }

//FUNCTIES BIJ ARRAY'S AANDACHTSPUNTEN

 function GeefIndexBeginTekening(i) {            //Geef de index van het eerste record waarin
  var x                                          //tekeningcode i voorkomt.
  x=0
  while (AP[x].substring(0,4)!=i) x++
  return x
 }

 function GeefIndexEindTekening(i) {             //Geef de index van het laatste record waarin
  var u,v                                        //tekeningcode i voorkomt.
  u=GeefIndexBeginTekening(i)
  v=AP.length-1
  u++
  while ((u<v) & AP[u].substring(0,4)==i) u++
  if (u<v) u--                                   // (laatste element wordt verondersteld geen...
  return u                                       // (nieuwe groep te zijn. Deze constructie is...
 }                                               // (nodig om te voorkomen dat index u 'uit de array loopt')

 function GeefAandachtspunt(i) {                 //Geef veld AL uit record i van de lijst met aandachtspunten.
  var a,b,c
  a=AP[i].length
  b=AP[i].indexOf(":")+1
  c=AP[i].substring(b,a)                         // (echter zonder tekeningcode)
  return c
 }

 function GeefElementen(i) {                     //Geef veld EL uit record i van de lijst met aandachtspunten.
  return EL[i]
 }

 function GeefLinkInfo(i) {                      //Geef veld BS uit record i van de lijst met aandachtspunten.
  return LI[i]
 }
