//ARRAY MET PROJECTFASEN

  PF=new Array            // volledige naam van projectfase
  i=-1                    // |                        tussen haakjes de lettercode van de projectfase
                          // |                        |
  i++;PF[i]="Initiatie (I)"
  i++;PF[i]="Planstudie (P)"
  i++;PF[i]="Bestek (B)"
  i++;PF[i]="Uitvoering (U)"
  i++;PF[i]="Onderhoud (O)"

//ARRAY MET TEKENINGEN

  T=new Array
  i=-1
//                                                                        scheidingsteken
//                                                                        |voor alle projectfasen een + of - (+=tekening komt voor in projectfase)
//          tekening                                                      ||                 scheidingsteken (-=tekening komt niet voor in projectfase)
//             |                                                          |F F F   | verwijzing naar lijst met aandachtspunten
//             |                                                          |I P B U O | |
//             |                                                          |          | |
  i++;T[i]="Situatie tekening"                                         + ":+ + + + + " + ":situ"
  i++;T[i]="Lengteprofiel"                                             + ":+ + + + + " + ":leng"
  i++;T[i]="Dwarsprofiel"                                              + ":+ + + + + " + ":dwar"
  i++;T[i]="Waterwegen"                                                + ":+ + + + + " + ":watw"
  i++;T[i]="Matenschemas van kunstwerken"                              + ":+ + + + + " + ":mats"
  i++;T[i]="Markeringen waterwegen"                                    + ":+ + + + + " + ":marv"
  i++;T[i]="Grenzentekening"                                           + ":+ + + + + " + ":gren"
  i++;T[i]="Ter visielegging"                                          + ":+ + + + + " + ":terv"
  i++;T[i]="Remmingswerken"                                            + ":+ + + + + " + ":remw"
  i++;T[i]="Grondkerende constructies"                                 + ":+ + + + + " + ":groc"
  i++;T[i]="Oeverbekledingen"                                          + ":+ + + + + " + ":oevb"
  i++;T[i]="Beplantingsplan"                                           + ":+ + + + + " + ":bepl"
  i++;T[i]="Kabels en leidingen (nw)"                                  + ":+ + + + + " + ":kabe"
  i++;T[i]="Dwarsprof. tbv hoeveelheden"                               + ":+ + + + + " + ":dwah"
  i++;T[i]="Grondmech.  onderzoek (situatie)"                          + ":+ + + + + " + ":grmo"
  i++;T[i]="Milieukundig onderzoek (situatie)"                         + ":+ + + + + " + ":milo"
  i++;T[i]="Kadastrale situatietekening"                               + ":+ + + + + " + ":kada"
  i++;T[i]="Baggertekening"		                                       + ":+ + + + + " + ":bagg"

//AANDACHTSPUNTEN

//                            code voor tekening (4 tekens; zie ook array met tekeningen)
//                            |   scheidingsteken
//                            |   |projectfasen (zie bestand tekenverklaring.js voor verklaring tekens)
//                            |   ||            scheidingsteken
//                            |   |C C D E F G H| aandachtspunt
//                            |   |2 3          | |
   AP=new Array  //Voorbeeld "afwa:. . . v v v .:drainage en grindkoffers"

//                            tekst die als eerste hyperlink verschijnt
//                            |             scheidingsteken
//                            |            | tekst die als tweede hyperlink verschijnt etc.
//                            |            | |
   EL=new Array  //Voorbeeld "wh-**-drainage;wh-**-grindkoffer"

//                            bestand dat bij eerste hyperlink hoort
//                            |            scheidingsteken
//                            |           |  bestand dat bij tweede hyperlink hoort etc.
//                            |           |  |
   LI=new Array  //Voorbeeld "S whdrainage;S whgrindkoffer"
//
//     bestandsaanduidingen: "S whdrainage"     = specifieke richtlijn "whdrainage.html"
//                           "A stempel"        = algemene richtlijn "stempel.html"
//                           "A stempel.html#2" = algemene richtlijn "stempel.html", tweede sectie
//                           "og"               = layergroep og
//                           "algaandptn"       = bestand "algaandptn.htm" (directory algemeen)
// Zowel bij EL als BS kan begonnen worden met " ;". In dit geval zakken de hyperlinks een regel.

 i=-1
 
//**** algemene aandachtspunten ****
 i++
 AP[i]="alga:v v v v v:ingevuld titelblok"
 EL[i]="titelblok;tekst"
 LI[i]="A stempel;A tekst"
 i++
 AP[i]="alga:v v v v v:&quotmaten in ...meters, tenzij anders vermeld&quot"
 EL[i]="strook voor aanvullende gegevens;eenheden"
 LI[i]="A stempel.html#3;A eenheden"
 i++
 AP[i]="alga:v v v v v:hoogtematen ten opzichte van NAP"
 EL[i]="tekst;hoogtematen;nauwkeurigheid"
 LI[i]="A tekst;A maten.html#4;A eenheden"
 i++
 AP[i]="alga:- - v v -:besteknummer"
 EL[i]="titelblok"
 LI[i]="A stempel"
 i++
 AP[i]="alga:+ + v + +:kunstwerken en<br>kunstwerknummers"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="alga:v v v v v:legenda en/of verklaring"
 EL[i]="tekst;strook voor aanvullende gegevens"
 LI[i]="A tekst;A stempel.html#3"
 i++
 AP[i]="alga:v v v v v:verwijzingen naar bijbehorende tekeningen"
 EL[i]="titelblok"
 LI[i]="A stempel"
 i++
 AP[i]="alga:v v v v v:schalen"
 EL[i]="titelblok;schalen;onderschriften en schaalaanduidingen"
 LI[i]="A stempel;A schalen;A onderschriften"

//**** algemene aandachtspunten voor dwars- en langsprofielen****
 i++
 AP[i]="algb:v v v v v:plaats profiel<br>(kilometrering en/of profielnummer)"
 EL[i]="tekst"
 LI[i]="tekst"
 i++
 AP[i]="algb:v v v v v:referentielijnen (NAP lijn)"
 EL[i]="in dwarsprofiel;in langsprofiel;bemating"
 LI[i]="S dpNAPlijn;S lpNAPlijn;A maten"
 i++
 AP[i]="algb:v v v v v:positie t.o.v kaartnoorden (tekst)"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="algb:v v v v v:verwijzing naar situatietekening"
 EL[i]="tekst"
 LI[i]="A tekst"
  i++
 AP[i]="algb:v v v v v:vaarwegbenaming"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="algb:+ + + v v:werkgrens en / of projectgrens"
 EL[i]="diversen in dwarsprofiel"
 LI[i]="S dpdiversen"
 i++
 AP[i]="algb:v v v v v: bestaande rijkseigendomsgrens"
 EL[i]="grenzen in dwarsprofiel"
 LI[i]="S dprijksgrens"
 i++
 AP[i]="algb:+ + v v v v: nieuwe rijkseigendomsgrens"
 EL[i]="grenzen in dwarsprofiel"
 LI[i]="S dprijksgrens"
 i++
 AP[i]="algb:v v v v v:matenbalk en maatvoering profielen"
 EL[i]="maatvoering in lp;maatvoering in dp"
 LI[i]="S lpmatenbalk;S dpmatenbalk"

//**** aanvullende aandachtspunten voor overzichts- en situatietekeningen ****
 i++
 AP[i]="aanv:v v v v v:coördinaten"
 EL[i]="informatie tussen kader en afsnijkant;ruitkruisjes & coördinaten"
 LI[i]="A kader;A orientatie.html#2"
 i++
 AP[i]="aanv:v v v v v:noordpijl"
 EL[i]="noordpijl"
 LI[i]="A orientatie.html#1"
 i++
 AP[i]="aanv:v v v v v:(deel)gemeenten"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="aanv:v v v v v v:(deel)gemeentegrenzen"
 EL[i]="grenzen"
 LI[i]="S kdgemeentegrens"
 i++
 AP[i]="aanv:v v v v v:verwijzing naar dwars- en lengteprofielen"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="aanv:v v v v v:vaarwegbenaming etc."
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="aanv:v v v v -:werkgrens en/of projectgrens"
 EL[i]="werkgrens;werkvakgrens"
 LI[i]="S kdwerkgrens;S kdwerkvakgrens"
 i++
 AP[i]="aanv:± v v v v:bestaande rijkseigendomsgrens"
 EL[i]="rijkseigendomsgrens" 
 LI[i]="S kdrijkseigendomsgrens"
 i++
 AP[i]="aanv:± v v v v:nieuwe rijkseigendomsgrens"
 EL[i]="rijkseigendomsgrens"
 LI[i]="S kdrijkseigendomsgrens"  

 
//**** Situatie tekening *****
 i++
 AP[i]="situ:v v v v ±:bestaande situatie"
 EL[i]="ondergronden"
 LI[i]="og"
 i++
 AP[i]="situ:v v v v v:wegen"
 EL[i]="verhardingen;assen"
 LI[i]="vh;as"
 i++
 AP[i]="situ:v v v v v:kunstwerken"
 EL[i]="kunstwerken"
 LI[i]="kw"
 i++
 AP[i]="situ:v v v v v:grondwerk"
 EL[i]="grondwerk"
 LI[i]="gw"
 i++
 AP[i]="situ:± v v v v:natuurvriendelijke oevers"
 EL[i]="faunavoorzieningen"
 LI[i]="fv"
 i++
 AP[i]="situ:± v v v v:beplanting"
 EL[i]="beplanting"
 LI[i]="bp"
 i++
 AP[i]="situ:v v v v v:grondkerende constructies"
 EL[i]="grondkerende constructies"
 LI[i]="gk"
 i++
 AP[i]="situ:v v v v v:oever en bodembescherming"
 EL[i]="waterbouw"
 LI[i]="wb"
 i++
 AP[i]="situ:v v v v v:hoofd(assen)"
 EL[i]="Assen en kilometrering"
 LI[i]="as"
 i++
 AP[i]="situ:± v v v v:askilometrering"
 EL[i]="Assen en kilometrering"
 LI[i]="S askilometrering"
 i++
 AP[i]="situ:n v v v v:aslabels"
 EL[i]="Assen en kilometrering"
 LI[i]="as"
 i++
 AP[i]="situ:v v v v v:raaien en raainummers"
 EL[i]="Assen en kilometrering "
 LI[i]="as"
 i++
 AP[i]="situ:± v v v v:horizontale stralen en tangentpunten"
 EL[i]="Assen en kilometrering "
 LI[i]="as"
 i++
 AP[i]="situ:v v v v v:essentiële grenzen van (bestemmings)plannen van derden"
 EL[i]="Grenzen / kadastrale informatie"
 LI[i]="kd"
 i++
 AP[i]="situ:v v v v v:waterhuishouding"
 EL[i]="waterhuishouding"
 LI[i]="wh"
 i++
 AP[i]="situ:v v v v v:afbakening vaargeul,vaargeulas"
 EL[i]="vaargeul;assen"
 LI[i]="S wwvaargeul;S asvaargeulas"
 i++
 AP[i]="situ:v v v v v:nevengeul"
 EL[i]="nevengeul"
 LI[i]="S wwnevengeul"
 i++
 AP[i]="situ:v v v v v:winterbed"
 EL[i]="winterbed"
 LI[i]="S wwwinterbed"
 i++
 AP[i]="situ:v v v v v:zomerbed"
 EL[i]="zomerbed"
 LI[i]="S wwzomerbed"
 i++
 AP[i]="situ:v v v v v:waterberging"
 EL[i]="waterberging"
 LI[i]="ww"
 i++
 AP[i]="situ:v v v v v:overloopgebied"
 EL[i]="overloopgebied"
 LI[i]="S wwoverloopgebied"
 i++
 AP[i]="situ:v v v v v:normaallijnen"
 EL[i]="waterwegen"
 LI[i]="S wwnormaallijn"
 i++
 AP[i]="situ:v v v v v:polders"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="situ:v v v v v:polderscheidingen en waterschapsgrenzen"
 EL[i]="Grenzen / kadastrale informatie"
 LI[i]="gr"
 i++
 AP[i]="situ:n ± v v v:essentiële elementen uit plannen voor verlichting en signalering"
 EL[i]="waterweginrichting;waterwegmarkering"
 LI[i]="iw;mw"
 i++
 AP[i]="situ:n ± v v v:bebakening, betonning"
 EL[i]="waterwegmarkering"
 LI[i]="mw"
 i++
 AP[i]="situ:± v v v v:ondergrondse infrastructuur"
 EL[i]="kabels en leidingen"
 LI[i]="kl"
 i++
 AP[i]="situ:± v v v v:vaarwegmeubilair steigers ed"
 EL[i]="waterweginrichting"
 LI[i]="iw"
 i++
 AP[i]="situ:v v v v v:afmeerlokaties"
 EL[i]="waterweginrichting"
 LI[i]="iw"
 i++
 AP[i]="situ:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="situ:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"
 
//**** Lengteprofiel *****
 i++
 AP[i]="leng:± ± ± ± ±:profiel van de hoofdas in de eindsituatie"
 EL[i]="lengteprofiel:;assen"
 LI[i]="lp;S lpaslijn"
 i++
 AP[i]="leng:± ± ± ± ±:profiel overige assen"
 EL[i]="lengteprofiel:;assen"
 LI[i]="lp;S lpaslijn"
 i++
 AP[i]="leng:v v v v v:diverse profielen van de eindsituatie"
 EL[i]="lengteprofiel"
 LI[i]="lp"
 i++
 AP[i]="leng:v v v v v:maatvoering van lengteprofielen"
 EL[i]="lengteprofiel:;matenbalk"
 LI[i]="lp;S lpmaatbalk"
 i++
 AP[i]="leng:v v v v v:hoogte referentielijnen (NAP lijn)"
 EL[i]="maataanduidingen"
 LI[i]="A maten"
 i++
 AP[i]="leng:± ± ± ± ±:grondwaterstand/freatisch vlak"
 EL[i]="lengteprofiel:;grondwaterstand"
 LI[i]="lp;S lpgrondwaterstand"
 i++
 AP[i]="leng:± ± ± ± ±:debietlijnen"
 EL[i]="lengteprofiel:;debietlijnen"
 LI[i]="lp;S lpdebietlijnen"
 i++
 AP[i]="leng:v v v v v:waterpeil (hoog/laag)"
 EL[i]="lengteprofiel:;waterpeil"
 LI[i]="lp;S lpwaterlijn"
 i++
 AP[i]="leng:v v v v v:bestaand maaiveld"
 EL[i]="lengteprofiel:;maaiveld"
 LI[i]="lp;S lpmaaiveld"
 i++
 AP[i]="leng:± v v v v:aan te brengen en/of te verwijderen grond/zand"
 EL[i]="lengteprofiel:;grondwerk"
 LI[i]="lp;S lpgrondwerk"
 i++
 AP[i]="leng:± ± ± ± ±:te verwachten zettingslijn"
 EL[i]="lengteprofiel:;zettingslijn"
 LI[i]="lp;S lpzettingslijn"
 i++
 AP[i]="leng:± v v v v:bestorting/bodembescherming"
 EL[i]="lengteprofiel:;bodembescherming"
 LI[i]="lp;S lpbodembescherming"
 i++
 AP[i]="leng:± v v v v:cunetten"
 EL[i]="lengteprofiel:;grondwerk"
 LI[i]="lp;S lpgrondwerk"
 i++
 AP[i]="leng:v v v v v:kunstwerken"
 EL[i]="lengteprofiel:;kunstwerken"
 LI[i]="lp;S lpkunstwerk"
 i++
 AP[i]="leng:v v v v v:kruisingen met wegen, spoorwegen, waterwegen, leidingen etc."
 EL[i]="lengteprofiel:;assen"
 LI[i]="lp;S lpaslijn"
 i++
 AP[i]="leng:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="leng:v v v v v:algemene aandachtspunten voor dwars- en lengteprofiel (tekeningen)"
 EL[i]="klik hier"
 LI[i]="algb"


//**** Dwarsprofiel *****

 i++
 AP[i]="dwar:v v v v v:bestaande profielen"
 EL[i]="bestaande profielen"
 LI[i]="dp"
 i++
 AP[i]="dwar:v v v v v:nieuwe profielen"
 EL[i]="nieuwe profielen"
 LI[i]="dp"
 i++
 AP[i]="dwar:± v v v v:doorvaarthoogte"
 EL[i]="dwarsprofiel:;profiel van vrije ruimte"
 LI[i]="dp;S dpdoorvaarthoogte"
 i++
 AP[i]="dwar:± v v v v:vaarwegassen"
 EL[i]="dwarsprofiel:;assen"
 LI[i]="dp;S dpaslijn"
 i++
 AP[i]="dwar:± v v v v:hoogtematen (nauwkeurigheid kan per (plan)fase verschillen"
 EL[i]="maataanduidingen"
 LI[i]="A maten"
 i++
 AP[i]="dwar:v v v v v:natuurvriendelijke oevers"
 EL[i]="dwarsprofiel:;beplanting / faunav."
 LI[i]="dp;S dpdiversen"
 i++
 AP[i]="dwar:± v v v v:beplanting"
 EL[i]="dwarsprofiel:;beplanting"
 LI[i]="dp;S dpdiversen"
 i++
 AP[i]="dwar:n v v v v:hellingshoeken van taluds"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="dwar:v v v v v:breedte bodem, breedte vaargeul"
 EL[i]="bemating"
 LI[i]="A maten"
 i++
 AP[i]="dwar:v v v v v:aan te brengen en/of te verwijderen grond/zand/bestorting"
 EL[i]="dwarsprofiel:;grondontgraven"
 LI[i]="dp;dp"
 i++
 AP[i]="dwar:± v v v v:aan te brengen en/of te verwijderen oeverconstructies"
 EL[i]="dwarsprofiel:;oeverconstructies"
 LI[i]="dp;S dpdiversen"
 i++
 AP[i]="dwar:± ± ± ± ±:grondwaterstand/freatisch vlak"
 EL[i]="dwarsprofiel:;gws"
 LI[i]="dp;S dpgrondwaterstand"
 i++
 AP[i]="dwar:v v v v v:waterpeil hoog/laag"
 EL[i]="dwarsprofiel:;waterlijn"
 LI[i]="dp;S dpwaterlijn"
 i++
 AP[i]="dwar:± v v v v:geleidewerken"
 EL[i]="dwarsprofiel:;geleidewerken"
 LI[i]="dp;S dpdiversen"
 i++
 AP[i]="dwar:± v v v v:grondkerende constructies"
 EL[i]="dwarsprofiel:;grondkerende constructies"
 LI[i]="dp;S dpgrondkerendeconstructies"
 i++
 AP[i]="dwar:± ± ± ± ±:verlichting"
 EL[i]="dwarsprofiel:;diversen"
 LI[i]="dp;S dpdiversen"
 i++
 AP[i]="dwar:v v v v v:kunstwerken"
 EL[i]="dwarsprofiel:;kunstwerken"
 LI[i]="dp;S dpkunstwerk"
 i++
 AP[i]="dwar:n v v v v:relevante kleine werken, zoals drains, perkoenpalenrijen, beschoeiing"
 EL[i]="dwarsprofiel:;diversen"
 LI[i]="dp;S dpdiversen"
 i++
 AP[i]="dwar:v v v v v:bestorting"
 EL[i]="dwarsprofiel:;bestorting"
 LI[i]="dp;S dpdiversen"
 i++
 AP[i]="dwar:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="dwar:v v v v v:algemene aandachtspunten voor dwars- en lengteprofiel (tekeningen)"
 EL[i]="klik hier"
 LI[i]="algb"

//**** waterwegen *****
 i++
 AP[i]="watw:v v v v v:bestaande situatie"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="watw:v v v v v:vaargeulas + metrering"
 EL[i]="assen:;vaargeul; tekst"
 LI[i]="as;S asvaargeul; A tekst"
 i++
 AP[i]="watw:v v v v v:grens tussen stroomvoerend en bergend winterbed"
 EL[i]="waterwegen:;winterbed"
 LI[i]="ww;S wwwinterbed"
 i++
 AP[i]="watw:v v v v v:grens winterbed"
 EL[i]="waterwegen:;winterbed"
 LI[i]="ww;S wwwinterbed"
 i++
 AP[i]="watw:v v v v v:grens zomerbed"
 EL[i]="waterwegen:;zomerbed"
 LI[i]="ww;S wwzomerbed"
 i++
 AP[i]="watw:n v v v v:nevengeul"
 EL[i]="waterwegen:;nevengeul"
 LI[i]="ww;S wwnevengeul"
 i++
 AP[i]="watw:n v v v v:winterberging"
 EL[i]="waterwegen:;winterberging"
 LI[i]="ww;S wwwinterberging"
 i++
 AP[i]="watw:n v v v v:overloopgebied"
 EL[i]="waterwegen:;overloopgebied"
 LI[i]="ww;S wwoverloopgebied"
 i++
 AP[i]="watw:n v v v v:groene rivier"
 EL[i]="waterwegen:;groene rivier"
 LI[i]="ww;S wwgroene_rivier"
 i++
 AP[i]="watw:n v v v v:vaargeul"
 EL[i]="waterwegen:;vaargeul"
 LI[i]="ww;S wwvaargeul"
 i++
 AP[i]="watw:v v v v v:kenmerkende objecten uit ondergrond"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="watw:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="watw:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"
  i++
 AP[i]="watw:v v v v v:algemene aandachtspunten voor dwars- en lengteprofiel (tekeningen)"
 EL[i]="klik hier"
 LI[i]="algb"


//**** matenschema's van kunstwerken **** 
 i++
 AP[i]="mats:v v v v ±:bestaande situatie"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="mats:v v v v v:nieuwe situatie"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="mats:v v v v v:maatvoering"
 EL[i]="maatvoering"
 LI[i]="A maatvoering"
 i++
 AP[i]="mats:v v v v v:assenschema (langere punten, stralen, kilometrering, asnaam)"
 EL[i]="assen"
 LI[i]="as"
 i++
 AP[i]="mats:± v v v v:coordinaten snijpunt XYZ"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="mats:± v v v v:hoeken"
 EL[i]="maatvoering"
 LI[i]="A maatvoering"
 i++
 AP[i]="mats:± v v v v:profiel van vrije ruimte"
 EL[i]="pvr"
 LI[i]="S kwPVR"
 i++
 AP[i]="mats:± ± ± ± ±:zichtruimte"
 EL[i]="  "
 LI[i]=""
 i++
 AP[i]="mats:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="mats:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"
  i++
 AP[i]="mats:v v v v v:algemene aandachtspunten voor dwars- en lengteprofiel (tekeningen)"
 EL[i]="klik hier"
 LI[i]="algb"


//**** markeringen vaarwegen **** 
 i++
 AP[i]="marv:v v v v v:(bestaande)situatie"
 EL[i]=""
 LI[i]=""
 i++
 AP[i]="marv:v v v v v:assen kilometrering"
 EL[i]="assen"
 LI[i]="as"
 i++
 AP[i]="marv:v v v v v:borden + afmetingen"
 EL[i]="markering waterwegen:;scheepvaart tekens;tekst"
 LI[i]="mw;S mwscheepvaart_tekens;A tekst"
 i++
 AP[i]="marv:n ± v v v:borden locatie"
 EL[i]="bemating"
 LI[i]="A maten"
 i++
 AP[i]="marv:v v v v v:bakens, lichten incl afmetingen"
 EL[i]="markering waterwegen:;bebakening;lichtopstand;tekst"
 LI[i]="mw;S mwbebakening;S mwlichtopstand;A tekst"
 i++
 AP[i]="marv:n ± v v v:lichten, bakens locatie"
 EL[i]="bemating"
 LI[i]="A maten"
 i++
 AP[i]="marv:v v v v v:betonning + afmetingen"
 EL[i]="markering waterwegen:;betonning;tekst"
 LI[i]="mw;S mwbetonning;A tekst"
 i++
 AP[i]="marv:n ± v v v:betonning locatie"
 EL[i]="bemating"
 LI[i]="A maten"
 i++
 AP[i]="marv:v v v v v:doorvaartseinen + afmetingen"
 EL[i]="markering waterwegen:;doorvaartseinen;tekst"
 LI[i]="mw;S mwdoorvaartsein;A tekst"
 i++
 AP[i]="marv:n ± v v v:doorvaartseinen locatie"
 EL[i]="bemating"
 LI[i]="A maten"
 i++
 AP[i]="marv:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="marv:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"
  i++
 AP[i]="marv:v v v v v:algemene aandachtspunten voor dwars- en lengteprofiel (tekeningen)"
 EL[i]="klik hier"
 LI[i]="algb"


//**** grenzentekening **** 
 i++
 AP[i]="gren:. v . . n:ondergrond"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="gren:. v . . v:polders"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="gren:. v . . v:polderpeil, zomerpeil of winterpeil"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="gren:. v . . v:polderscheiding en/of waterschapsgrens"
 EL[i]="grenzen:';waterschapsgrens"
 LI[i]="kd;S kdwaterschapsgrens"
 i++
 AP[i]="gren:. v . . v:kadaster sectiegrens"
 EL[i]="grenzen:;sectiegrens"
 LI[i]="kd;S kdsectiegrens"
 i++
 AP[i]="gren:. v . . v:grens rijkseigendom"
 EL[i]="grenzen:;rijkseigendomgrens"
 LI[i]="kd;S kdrijkseigendomsgrens"
 i++
 AP[i]="gren:. v . . v:beheersgrens algemeen"
 EL[i]="grenzen:;beheersgrens algemeen"
 LI[i]="kd;S kdbeheersgrens_algemeen"
 i++
 AP[i]="gren:. v . . v:beheersgrens gemeente"
 EL[i]="grenzen:;beheersgrens gemeente"
 LI[i]="kd;S kdbeheersgrens_gemeente"
 i++ 
 AP[i]="gren:. v . . v:beheergrens NS"
 EL[i]="grenzen:;beheersgrens NS"
 LI[i]="kd;S kdbeheersgrens_NS"
 i++ 
 AP[i]="gren:. v . . v:beheersgrens provincie"
 EL[i]="grenzen:;beheersgrens provincie"
 LI[i]="kd;kd"
 i++ 
 AP[i]="gren:. v . . v:beheersgrens RWS/RWS"
 EL[i]="grenzen:;beheersgrens RWS/RWS"
 LI[i]="kd;S kdbeheersgrens_RWS-RWS"
 i++ 
 AP[i]="gren:. v . . v:beheergrens RWS/waterschap polder"
 EL[i]="grenzen:;beheersgrens RWS/Water"
 LI[i]="kd;S kdbeheersgrens_RWS-waterschap/polder"
 i++ 
 AP[i]="gren:. v . . v:beheergrens waterschap"
 EL[i]="grenzen:;beheersgrens waterschap"
 LI[i]="kd;S kdbeheersgrens_waterschap"
 i++ 
 AP[i]="gren:. v . . v:beheergrens waterschap / polder"
 EL[i]="grenzen:;beheersgrens waterschap/polder"
 LI[i]="kd;S kdbeheersgrens_waterschap/polder"
 i++ 
 AP[i]="gren:. v . . v:pachtgrens"
 EL[i]="grenzen:;pachtgrens"
 LI[i]="kd;S kdpachtgrens"
 i++ 
 AP[i]="gren:. v . . v:beheer en onderhoudsgrens"
 EL[i]="grenzen:;beheer en onderhoudsgrens"
 LI[i]="kd;S kdbeheers_onderhoudsgrens"
 i++
 AP[i]="gren:. v . . v:onderhoudsgrens"
 EL[i]="grenzen:;onderhoudsgrens"
 LI[i]="kd;S kdonderhoudsgrens"
 i++
 AP[i]="gren:. v . . v:aankoopgrens"
 EL[i]="grondaankoop:;aankoopgrens"
 LI[i]="ga;S gaaankoopgrens"
 i++
 AP[i]="gren:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="gren:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"
 
//**** ter visielegging **** 
 i++
 AP[i]="terv:. v . . .:bestaande situatie"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="terv:. v . . .:nieuwe situatie"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="terv:. v . . .:begin/einde werk"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="terv:. v . . .:hoofdassen + metrering"
 EL[i]="assen"
 LI[i]="as"
 i++
 AP[i]="terv:. v . . .:gemeente aanduiding"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="terv:. v . . .:straatnamen"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="terv:. v . . .:gemeentegrenzen"
 EL[i]="gemeentegrens"
 LI[i]="S kdgemeentegrens"
 i++
 AP[i]="terv:. v . . .:provinciegrens"
 EL[i]="provinciegrens"
 LI[i]="S kdprovinciegrens"
 i++
 AP[i]="terv:. v . . .:kenmerkende lengte- en dwarprofielen"
 EL[i]="lengteprofiel;dwarsprofiel"
 LI[i]="dp;lp"
 i++
 AP[i]="terv:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="terv:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"
  i++
 AP[i]="terv:v v v v v:algemene aandachtspunten voor dwars- en lengteprofiel (tekeningen)"
 EL[i]="klik hier"
 LI[i]="algb"


//**** remmingswerken **** 
 i++
 AP[i]="remw:v v v v v: (bestaande) situatie"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="remw:± ± v v v:assen en metrering"
 EL[i]="assen; tekst"
 LI[i]="as;A tekst"
 i++
 AP[i]="remw:v v v v v:waterpeil"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="remw:v v v v v:functie"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="remw:v v v v v:meerpalen, meerstoelen, ducdalfen"
 EL[i]="inrichting waterwegen:;meerpaal"
 LI[i]="iw;S iwmeerpaal"
 i++
 AP[i]="remw:v v v v v:loopbruggen,steigers"
 EL[i]="inrichting waterwegen:;loopbruggen;steigers"
 LI[i]="iw;S iwloopbrug;S iwsteiger"
 i++
 AP[i]="remw:v v v v v:remmingswerken"
 EL[i]="inrichting waterwegen:;remmingswerken"
 LI[i]="iw;S iwremmingswerk"
 i++
 AP[i]="remw:v v v v v:drijframen"
 EL[i]="inrichting waterwegen:;drijframen"
 LI[i]="iw;S iwdrijfraam"
 i++
 AP[i]="remw:± ± v v v:bolders"
 EL[i]="inrichting waterwegen:;bolders"
 LI[i]="iw;S iwbolder"
 i++ 
 AP[i]="remw:± ± v v v:scheepvaart tekens"
 EL[i]="markering waterwegen:;scheepvaarttekens"
 LI[i]="mw;S mwscheepvaart_tekens"
 i++
 AP[i]="remw:± ± v v v:seinen"
 EL[i]="markering waterwegen:;seinen"
 LI[i]="mw;S mwdoorvaartsein"
 i++
 AP[i]="remw:± ± v v v: verlichting"
 EL[i]="inrichting waterwegen:;verlichting"
 LI[i]="iw;S iwverlichting"
 i++
 AP[i]="remw:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="remw:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"
  i++
 AP[i]="remw:v v v v v:algemene aandachtspunten voor dwars- en lengteprofiel (tekeningen)"
 EL[i]="klik hier"
 LI[i]="algb"


//**** Grondkerende constructies **** 
 i++
 AP[i]="groc:v v v v v:bestaande situatie"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="groc:± v v v v:assen en metrering"
 EL[i]="assen; tekst"
 LI[i]="as;A tekst"
 i++
 AP[i]="groc:v v v v v:waterpeil"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="groc:v v v v v:peil bodem"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="groc:± ± ± ± ±:grondonderzoek"
 EL[i]="grondonderzoek"
 LI[i]="go"
 i++
 AP[i]="groc:v v v v v:grondwaterstand"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="groc:- v v v v:stalen damwand + type"
 EL[i]="grondkereningen:;damwand; tekst"
 LI[i]="gk;S gkdamwand; A tekst"
 i++
 AP[i]="groc:- v v v v:Verankeringsconstructies"
 EL[i]="grondkereningen:;verankeringsconstructies"
 LI[i]="gk;S gkverankering"
 i++
 AP[i]="groc:- v v v v:Overgangsconstructies naar bestaand werk"
 EL[i]="grondkereningen:;overgangsconstructies"
 LI[i]="A gkcontour_zichtbaar"
 i++
 AP[i]="groc:- v v v v:Gording"
 EL[i]="grondkereningen:;gording"
 LI[i]="gk;S gkgording"
 i++
 AP[i]="groc:- v v v v:Deksloof"
 EL[i]="grondkereningen:;deksloof"
 LI[i]="gk;S gkdeksloff"
 i++
 AP[i]="groc:- v v v v:grindkoffer"
 EL[i]="grondkereningen:;grindkoffer"
 LI[i]="gk;S gkcontour_zichtbaar"
 i++
 AP[i]="groc:- v v v v:Houten damwand"
 EL[i]="grondkereningen:;houtendamwand"
 LI[i]="gk;S gkhouten_damwand"
 i++
 AP[i]="groc:- v v v v:Betonnen keerwand"
 EL[i]="grondkereningen:;keerwand"
 LI[i]="gk;S gkkeerwand"
 i++
 AP[i]="groc:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="groc:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"

//**** Oeverbekledingen **** 
 i++
 AP[i]="oevb:v v v v v:bestaande situatie"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="oevb:± v v v v:assen en metrering"
 EL[i]="assen; tekst"
 LI[i]="as;A tekst"
 i++
 AP[i]="oevb:v v v v v:waterpeil (max, min, NAP, MHW)"
 EL[i]="waterpeil;tekst"
 LI[i]="ww;A tekst"
 i++
 AP[i]="oevb:± v v v v:hoogtelijnen"
 EL[i]=""
 LI[i]=""
 i++
 AP[i]="oevb:v v v v v:dwarsprofielen"
 EL[i]="grondwerk"
 LI[i]="gw"
 i++
 AP[i]="oevb:± v v v v:materiaalsoorten"
 EL[i]="tekst;arceringen"
 LI[i]="A tekst;A arceringen"
 i++
 AP[i]="oevb:± v v v v:zinkstukken"
 EL[i]="zinkstukken"
 LI[i]="S wbzinkstukken"
 i++
 AP[i]="oevb:± v v v v:bestortingsvakken"
 EL[i]="bestortingsvakken"
 LI[i]="wb" 
 i++
 AP[i]="oevb:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="oevb:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"

//**** Beplantingsplan **** 
 i++
 AP[i]="bepl:v v v v -:bestaande situatie"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="bepl:. . v v .:plantvakken + nr."
 EL[i]="plantvakken; tekst"
 LI[i]="bp;A tekst"
 i++
 AP[i]="bepl:. . v v v:beplantingstabel"
 EL[i]="tekst"
 LI[i]="tekst"
 i++
 AP[i]="bepl:± v v v v:beheersgrenzen"
 EL[i]="grenzen"
 LI[i]="kd"
 i++
 AP[i]="bepl:. . v v v:plantensoorten"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="bepl:. v v v v:plantdichtheid"
 EL[i]="plantdichtheid"
 LI[i]="A tekst;A arceringen"
 i++
 AP[i]="bepl:. . v v .:plantgaten of sleuven"
 EL[i]="plantgaten"
 LI[i]="S bpdiversen"
 i++
 AP[i]="bepl:. . v v .:planthoogte"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="bepl:. . v v v:stambescherming"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="bepl:. v v v .:verwijderen/verplaatsen planten"
 EL[i]="tekst;arceringen"
 LI[i]="A tekst;A arceringen"
 i++
 AP[i]="bepl:. v v v v:schouwpaden"
 EL[i]="schouwpaden"
 LI[i]="S bpdiversen"
 i++
 AP[i]="bepl:. v v v v:vrije zichtruimte"
 EL[i]="zichtruimte"
 LI[i]="bp" 
 i++
 AP[i]="bepl:v v v v v:kabels en leidingen"
 EL[i]="kabels en leidingen"
 LI[i]="kl"
 i++
 AP[i]="bepl:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="bepl:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"


//**** Kabels en leidingen **** 
 i++
 AP[i]="kabe:. v v v v:bestaande situatie"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="kabe:. v v v v:kabeltracee + omschrijving"
 EL[i]="assen; tekst"
 LI[i]="as;A tekst"
 i++
 AP[i]="kabe:. v v v v:kenmerken"
 EL[i]="lijntype;tekst"
 LI[i]="A lijntypen;A tekst"
 i++
 AP[i]="kabe:. . v v v:zinkers"
 EL[i]="zinkers"
 LI[i]=""
 i++
 AP[i]="kabe:. v v v v:overkluizingen"
 EL[i]="overkluizingen"
 LI[i]="kw"
 i++
 AP[i]="kabe:. v v v v:mantelbuizen, doorvoeringen"
 EL[i]="mantelbuizen, doorvoeringenn"
 LI[i]="kl"
 i++
 AP[i]="kabe:. v v v v:afsluiters, schakelkasten"
 EL[i]="afsluiters, schakelkasten"
 LI[i]="kl"
 i++
 AP[i]="kabe:. v v v v:dwars- en lengtedoorsnede"
 EL[i]="dwarsdoorsnede;lengtedoorsnede"
 LI[i]="dp;lp"
 i++
 AP[i]="kabe:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="kabe:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"


//**** Dwarsprofiel tbv hoeveelheden **** 
 i++
 AP[i]="dwah:. . v ± .:hoogte referentielijn"
 EL[i]="dwarsprofiel:;NAP lijn"
 LI[i]="dp;S dpNAPlijn"
 i++
 AP[i]="dwah:. . v ± .:grondwaterstand"
 EL[i]="dwarsprofiel:;gws"
 LI[i]="dp;S dpgrondwaterstand"
 i++
 AP[i]="dwah:. . v ± .:waterpeil"
 EL[i]="dwarsprofiel:;waterlijn"
 LI[i]="dp;S dpwaterlijn"
 i++
 AP[i]="dwah:. . v ± .:verharding"
 EL[i]="dwarsprofiel:;verharding"
 LI[i]="dp;S dpverharding"
 i++
 AP[i]="dwah:. . v ± .:maaiveld,cunet,overhoogte"
 EL[i]="dwarsprofiel:;maaiveld;cunet;overhoogte"
 LI[i]="dp;S dpmaaiveld;S dpgrondwerk;S dpoverhoogte"
 i++
 AP[i]="dwah:. . v ± .:taludbekleding"
 EL[i]="dwarsprofiel:;taludbekleding"
 LI[i]="dp;S dptaludbekleding"
 i++
 AP[i]="dwah:. . ± ± .:aanvullingen"
 EL[i]="dwarsprofiel:;grondaanvullen;zandaanvullen;kleiaanvullen;overzicht arceringen;tekst"
 LI[i]="dp;S dparcering_grond_aanvullen;S dparcering_zand_aanvullen;S dparcering_klei_aanvullen;arceringen;A tekst"
 i++
 AP[i]="dwah:. . ± ± .:ontgravingen"
 EL[i]="dwarsprofiel:;grondontgraven;zandontgraven;kleiontgraven;overzicht arceringen;tekst"
 LI[i]="dp;S dparcering_grond_ontgraven;S dparcering_zand_ontgraven;S dparcering_klei_ontgraven;arceringen;A tekst"
 i++
 AP[i]="dwah:. . ± ± .:oude funderingen en verhardingen"
 EL[i]="dwarsprofiel:;diversen"
 LI[i]="dp;S dpdiversen" 
 i++
 AP[i]="dwah:. . ± ± .:hoeveelhedenstaat"
 EL[i]="tekst"
 LI[i]="A tekst" 
 i++
 AP[i]="dwah:. . v ± .:kilometrering"
 EL[i]="kilometrering"
 LI[i]="A tekst" 
 i++
 AP[i]="dwah:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="dwah:v v v v v:algemene aandachtspunten voor dwars- en lengteprofiel (tekeningen)"
 EL[i]="klik hier"
 LI[i]="algb"


//**** Grondmech. onderzoek (sit. tek) **** 
 i++
 AP[i]="grmo:v v v v v:(bestaande) situatie"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="grmo:v v v v v:assen, metrering, labels raaien"
 EL[i]="assen;tekst"
 LI[i]="as;A tekst"
 i++
 AP[i]="grmo:v v v v v:boor- en sondeerpunten, nrs."
 EL[i]="grondonderzoek;tekst"
 LI[i]="go;A tekst"
 i++
 AP[i]="grmo:v v v v v:boorstaat of sondering + coordinaten"
 EL[i]="figuur"
 LI[i]="A tekst"
 i++
 AP[i]="grmo:v v v v v:peilbuizen + nr."
 EL[i]="peilbuizen;tekst"
 LI[i]="S gopeilbuis;A tekst"
 i++
 AP[i]="grmo:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="grmo:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"

//**** Milieukundig onderzoek (sit. tek) **** 
 i++
 AP[i]="milo:v v v v v:(bestaande)situatie"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="milo:v v v v v:begrenzing onderzoeksgebied"
 EL[i]="onderzoeksgebied"
 LI[i]="S goonderzoeksgebied"
 i++
 AP[i]="milo:± ± ± ± ±:kadastrale percelen + nr."
 EL[i]="kadastralegrens;tekst"
 LI[i]="S kdkadastralegrens;A tekst"
 i++
 AP[i]="milo:v v v v v:grondwaterstromingsrichting"
 EL[i]="grondonderzoek"
 LI[i]="go"
 i++
 AP[i]="milo:v v v v v:boorpunten + nr."
 EL[i]="boring;tekst"
 LI[i]="S goboring;A tekst"
 i++
 AP[i]="milo:v v v v v:peilbuizen + nr."
 EL[i]="peilbuizen;tekst"
 LI[i]="S gopeilbuis;A tekst"
 i++
 AP[i]="milo:v v v v v:geluidscontouren"
 EL[i]="geluidscontouren"
 LI[i]="mi"
 i++
 AP[i]="milo:v v v v v:begrenzing vervuiling"
 EL[i]="verontreiniging"
 LI[i]="go"
 i++
 AP[i]="milo:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="milo:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"
 
//**** Kadastrale situatietekening **** 
 i++
 AP[i]="kada:. v v . .:situatie"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="kada:. v v . .:aankoopgrens"
 EL[i]="aankoopgrens"
 LI[i]="S gaaankoopgrens"
 i++
 AP[i]="kada:. v v . .:over te dragen gronden"
 EL[i]="overdracht"
 LI[i]="ga"
 i++
 AP[i]="kada:. v v . v:kadastrale begrenzing"
 EL[i]="kadastralegrens"
 LI[i]="S kdkadastralegrens"
 i++
 AP[i]="kada:. v v . v:kadastrale nrs. + sectie"
 EL[i]="tekst"
 LI[i]="S gakadastrale_aanduiding"
 i++
 AP[i]="kada:. v v . .:gemeente aanduiding"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="kada:. v v . .:gemeentegrens"
 EL[i]="gemeentegrens"
 LI[i]="S kdgemeentegrens"
 i++
 AP[i]="kada:. v v . .:aankoopstatus"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="kada:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="kada:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"
 
//**** Baggertekening **** 
 i++
 AP[i]="bagg:v v v v v:(bestaande)situatie"
 EL[i]="ondergrond"
 LI[i]="og"
 i++
 AP[i]="bagg:v v v v v:vaargeulas"
 EL[i]="assen"
 LI[i]="S asvaargeul"
 i++
 AP[i]="bagg:v v v v v:baggervak"
 EL[i]="grondwerk"
 LI[i]="gw"
 i++
 AP[i]="bagg:v v v v v:niet-baggervak"
 EL[i]="grondwerk"
 LI[i]="gw"
 i++
 AP[i]="bagg:v v v v v:stortvak"
 EL[i]="grondwerk"
 LI[i]="gw"
 i++
 AP[i]="bagg:v v v v v:niet-stortvak"
 EL[i]="grondwerk"
 LI[i]="gw"
 i++
 AP[i]="bagg:v v v v v:dieptelijnen"
 EL[i]="dieptelijnen"
 LI[i]="S wwdieptelijnen"
 i++
 AP[i]="bagg:v v v v v:vervuilingsklassen"
 EL[i]="grondonderzoek;tekst"
 LI[i]="S goverontreiniging;A tekst"
 i++
 AP[i]="bagg:v v v v v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="bagg:v v v v v:algemene aandachtspunten voor situatie (tekeningen)"
 EL[i]="klik hier"
 LI[i]="aanv"





