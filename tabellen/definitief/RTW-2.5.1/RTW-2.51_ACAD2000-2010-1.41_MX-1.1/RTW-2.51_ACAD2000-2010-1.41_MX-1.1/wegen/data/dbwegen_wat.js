//ARRAY MET PROJECTFASEN

  PF=new Array            // volledige naam van projectfase
  i=-1                    // |                        tussen haakjes de lettercode van de projectfase
                          // |                        |
  i++;PF[i]="initiatieffase/verkenningsfase (I)"
  i++;PF[i]="voorstudiefase (P1)"
  i++;PF[i]="studiefase 2D ontwerp (P2a)"
  i++;PF[i]="studiefase 3D ontwerp (P2b)"
  i++;PF[i]="planfase (P3)"
  i++;PF[i]="planuitwerkingsfase (PU)"
  i++;PF[i]="bestekfase (B)"
  i++;PF[i]="uitvoeringsfase (U)"
  i++;PF[i]="overdrachtsfase (O)"


//ARRAY MET TEKENINGEN

  T=new Array
  i=-1
//                                                                        scheidingsteken
//                                                                        |voor alle projectfasen een + of - (+=tekening komt voor in projectfase)
//          tekening                                                      ||                 scheidingsteken (-=tekening komt niet voor in projectfase)
//             |                                                          |I P P P P P B U O     | verwijzing naar lijst met aandachtspunten
//             |                                                          |  1 2 2 3 U           | |
//             |                                                          |    a b               | |
  i++;T[i]="afwatering"                                                + ":- - - - - + + + -" + ":afwa"
  i++;T[i]="calamiteitenplan hulpverlening"                            + ":- - - - - + - - -" + ":cahu"
  i++;T[i]="eigendom, beheer en onderhoud"                             + ":- - - - - + - - +" + ":ebon"
  i++;T[i]="fasering (dwarsprofieltekening per fasering)"              + ":- - - - + + + + -" + ":fadp"
  i++;T[i]="fasering (lengteprofieltekening per fasering)"             + ":- - - - - + + + -" + ":falp"
  i++;T[i]="fasering (situatie)"                                       + ":- - - - + + + - -" + ":fasi"
  i++;T[i]="fasering (verkeersmaatregels binnen fasering)"             + ":- - - - - + + + -" + ":favm"
  i++;T[i]="geleiderail"                                               + ":- - - - - + + + -" + ":glrl"
  i++;T[i]="grenzentekening"                                           + ":- - - - - + - - -" + ":grzn"
  i++;T[i]="inrichting en beplanting"                                  + ":- - - - - - + - -" + ":inbp"
  i++;T[i]="kabels en leidingen (inventarisatie bestaande tracees)"    + ":- - - - + - - - -" + ":kliv"
  i++;T[i]="kabels en leidingen (nieuwe tracees)"                      + ":- - - - - + - - -" + ":klnt"
  i++;T[i]="matenschema kunstwerken"                                   + ":- - - - + + - - -" + ":makw"
  i++;T[i]="portalen (dwarsprofiel voor bewegwijzering en signalering)"+ ":- - - - - + - - -" + ":podp"
  i++;T[i]="portalen (situatie)"                                       + ":- - - - - + - - -" + ":posi"
  i++;T[i]="praatpalen"                                                + ":- - - - - - + - -" + ":prpa"
  i++;T[i]="bebording en RVV"                                          + ":- - - - - + + + -" + ":rvvb"
  i++;T[i]="tervisielegging grondzaken (overzichtstekening)"           + ":- - - - - + - - -" + ":tgov"
  i++;T[i]="tervisielegging grondzaken (situatietekening)"             + ":- - - - - + - - -" + ":tgsi"
  i++;T[i]="verlichtingsplan"                                          + ":- - - - - + - - -" + ":vlpl"
  i++;T[i]="waterhuishouding"                                          + ":- - - - - + - - -" + ":wahu"
  i++;T[i]="wegontwerp (dwarsprofiel)"                                 + ":+ + + + + + + + -" + ":wodp"
  i++;T[i]="wegontwerp (lengteprofiel)"                                + ":+ + + + + + + + -" + ":wolp"
  i++;T[i]="wegontwerp (situatie)"                                     + ":+ + + + + + + + +" + ":wosi"

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
//                           "algaandptn"       = bestand "algaandptn.htm" (directory wegen)
// Zowel bij EL als BS kan begonnen worden met " ;". In dit geval zakken de hyperlinks een regel.

 i=-1

//**** algemene aandachtspunten ****
 i++
 AP[i]="alga:v v v v v v v v v:ingevuld titelblok"
 EL[i]="titelblok;tekst"
 LI[i]="A stempel;A tekst"
 i++
 AP[i]="alga:± ± ± v v v v v v:&quotmaten in ...meters, tenzij anders vermeld&quot"
 EL[i]="strook voor aanvullende gegevens;eenheden"
 LI[i]="A stempel.html#3;A eenheden"
 i++
 AP[i]="alga:± ± ± v v v v v v:hoogtematen ten opzichte van NAP"
 EL[i]="tekst;hoogtematen;nauwkeurigheid"
 LI[i]="A tekst;A maten.html#4;A eenheden"
 i++
 AP[i]="alga:- - - - - - v v -:besteknummer"
 EL[i]="titelblok"
 LI[i]="A stempel"
 i++
 AP[i]="alga:+ + + + + + v + +:kunstwerken en<br>kunstwerknummers"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="alga:v v v v v v v v v:legenda en/of verklaring"
 EL[i]="tekst;strook voor aanvullende gegevens"
 LI[i]="A tekst;A stempel.html#3"
 i++
 AP[i]="alga:v v v v v v v v v:verwijzingen naar bijbehorende tekeningen"
 EL[i]="titelblok"
 LI[i]="A stempel"
 i++
 AP[i]="alga:v v v v v v v v v:schalen"
 EL[i]="titelblok;schalen;onderschriften en schaalaanduidingen"
 LI[i]="A stempel;A schalen;A onderschriften"

//**** aanvullende aandachtspunten voor overzichts- en situatietekeningen ****
 i++
 AP[i]="aanv:v v v v v v v v v:coördinaten"
 EL[i]="informatie tussen kader en afsnijkant;ruitkruisjes en coördinaten"
 LI[i]="A kader;A orientatie.html#2"
 i++
 AP[i]="aanv:v v v v v v v v v:noordpijl"
 EL[i]="noordpijl"
 LI[i]="A orientatie.html#1"
 i++
 AP[i]="aanv:v v v v v v v v v:(deel)gemeenten"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="aanv:v v v v v v v v v:(deel)gemeentegrenzen"
 EL[i]="grenzen"
 LI[i]="S kdgemeentegrens"
 i++
 AP[i]="aanv:+ + + v v v v v v:verwijzing naar dwars- en lengteprofielen"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="aanv:v v v v v v v v v:rijkswegen, nummers en eindbestemmingen"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="aanv:+ + v v v v v v -:werkgrens en/of projectgrens"
 EL[i]="werkgrens;werkvakgrens"
 LI[i]="S kdwerkgrens;S kdwerkvakgrens"
 i++
 AP[i]="aanv:- - - - ± v v v v:bestaande rijkseigendomsgrens"
 EL[i]="rijkseigendomsgrens" 
 LI[i]="S kdrijkseigendomsgrens"
 i++
 AP[i]="aanv:- - - - ± v v v v:nieuwe rijkseigendomsgrens"
 EL[i]="rijkseigendomsgrens"
 LI[i]="S kdrijkseigendomsgrens"  

 i++
//**** afwatering *****
 AP[i]="afwa:. . . . . v v v .:situatie en onderliggend wegennet alsmede diversen (bestaand en nieuw)"
 EL[i]="ondergronden"
 LI[i]="og"
 i++
 AP[i]="afwa:. . . . . v v v .:(hoofd)assen,<br>as(kilo)metrering en<br>aslabels"
 EL[i]="assen;kilometering"
 LI[i]="as;S askilometrering"
 i++
 AP[i]="afwa:. . . . . v v ± .:poldernamen"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="afwa:. . . . . v v ± .:polderpeil, zomerpeil en winterpeil"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="afwa:. . . . . v v ± .:polderscheiding en/of waterschapsgrens"
 EL[i]="grenzen"
 LI[i]="kd"
 i++
 AP[i]="afwa:. . . . . v v v .:drainage en grindkoffers"
 EL[i]="drainage;grindkoffer"
 LI[i]="S whdrainage;S whgrindkoffer"
 i++
 AP[i]="afwa:. . . . . v v v .:riolering (bestaand en nieuw):<br>&nbsp afstroomrichting<br>&nbsp goot<br>&nbsp inspectieput<br>&nbsp kolken<br>&nbsp uitstroombak"
 EL[i]="waterhuishouding;stroomrichting;goot;put;straatkolk;troittoirkolk;uitstroombak"
 LI[i]="wh;S whstroomrichting;S whgoot;S whput;S whstraatkolk;S whtroittoirkolk;S whuitstroombak"
 i++
 AP[i]="afwa:. . . . . v v v .:duiker (bestaand en nieuw)"
 EL[i]="duiker"
 LI[i]="S whduiker"
 i++
 AP[i]="afwa:. . . . . v v v .:flexibele afvoerleiding bij kunstwerken"
 EL[i]="riolering"
 LI[i]="S whriolering"
 i++
 AP[i]="afwa:. . . . . v v v .:elementen waarnaar het water afgevoerd wordt"
 EL[i]="watergang"
 LI[i]="S whwatergang"
 i++
 AP[i]="afwa:. . . . . v v v .:verkanting en<br>verkantingsdraaiing"
 EL[i]="verkanting"
 LI[i]="S vhverkanting"
 i++
 AP[i]="afwa:. . . . . v v v .:obstakels die invloed hebben op de afwatering"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="afwa:. . . . . - ± v .:puttenstaat"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="afwa:. . . . . v v v .:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="afwa:. . . . . v v v .:algemene aandachtspunten voor overzichts- en situatietekeningen"
 EL[i]="klik hier"
 LI[i]="aanv"

 i++
//**** calamiteitenplan hulpverlening *****

 AP[i]="cahu:. . . . . + . . .:Alles in overleg met de regio:<br>hectometrering"
 EL[i]=" ;kilometrering"
 LI[i]=" ;S askilometrering"
 i++
 AP[i]="cahu:. . . . . + . . .:RW-nummers en<br>rijrichting"
 EL[i]="rijrichting"
 LI[i]="S dprijrichting"
 i++
 AP[i]="cahu:. . . . . + . . .:afslagen en richtingen"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="cahu:. . . . . + . . .:kunstwerken"
 EL[i]="ondergronden;kunstwerken"
 LI[i]="og;kw"
 i++
 AP[i]="cahu:. . . . . + . . .:geluidsschermen met vluchtdeuren"
 EL[i]="geluidsschermen"
 LI[i]="S gvscherm"
 i++
 AP[i]="cahu:. . . . . + . . .:sloten en vijvers"
 EL[i]="ondergronden;waterhuishouding"
 LI[i]="og;wh"
 i++
 AP[i]="cahu:. . . . . + . . .:noord/zuid en oost/west baan"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="cahu:. . . . . + . . .:lay-out in overleg met betrokkenen"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="cahu:. . . . . + . . .:uitgave in kleur"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="cahu:. . . . . v . . .:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="cahu:. . . . . v . . .:algemene aandachtspunten voor overzichts- en situatietekeningen"
 EL[i]="klik hier"
 LI[i]="aanv"

 i++
//**** eigendom, beheer en onderhoud *****
 AP[i]="ebon:. . . . . v . . n:situatie:<br>bestaand<br>nieuw"
 EL[i]="ondergronden;"
 LI[i]="og;"
 i++
 AP[i]="ebon:. . . . . v . . v:polders"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="ebon:. . . . . v . . v:polderpeil, zomerpeil of winterpeil"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="ebon:. . . . . v . . v:polderscheiding en/of waterschapsgrens:<br>bestaand<br>nieuw"
 EL[i]="grenzen waterschap;grenzen waterschap/polder"
 LI[i]="S kdbeheersgrens_waterschap;S kdbeheersgrens_waterschap/polder"
 i++
 AP[i]="ebon:. . . . . v .p; . v:kdaster sectiegrens"
 EL[i]="sectiegrens"
 LI[i]="S kdsectiegrens"
 i++
 AP[i]="ebon:. . . . . v . . v:rijkseigendomsgrens:<br>bestaand<br>nieuw<br>toekomstig (plan)"
 EL[i]="rijkseigendomsgrens;rijkseigendomsgrens gepland"
 LI[i]="S kdrijkseigendomsgrens;S kdrijkseigendomsgrens_gepland"
 i++
 AP[i]="ebon:. . . . . v . . v:beheersgrens:<br>bestaand<br>nieuw"
 EL[i]="algemeen;gemeente;NS;provincie;RWS/RWS;RWS/waterschap-polder;waterschap;waterschap/polder"
 LI[i]="S kdbeheersgrens_algemeen;S kdbeheersgrens_gemeente;S kdbeheersgrens_NS;S kdbeheersgrens_provincie;S kdbeheersgrens_RWS-RWS;S kdbeheersgrens_RWS-waterschap/polder;S kdbeheersgrens_waterschap;S kdbeheersgrens_waterschap/polder"              
 i++
 AP[i]="ebon:. . . . . v . . v:beheer- en onderhoudsgrens:<br>bestaand<br>nieuw"
 EL[i]="beheer- en onderhoudsgrens"
 LI[i]="S kdbeheers_onderhoudsgrens"
 i++
 AP[i]="ebon:. . . . . v . . v:onderhoudsgrens:<br>bestaand<br>nieuw"
 EL[i]="onderhoudsgrens"
 LI[i]="S kdonderhoudsgrens"
 i++
 AP[i]="ebon:. . . . . v . . n:over te dragen gronden"
 EL[i]="aankoopgrens"
 LI[i]="S gaaankoopgrens"
 i++
 AP[i]="ebon:. . . . . v . . v:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="ebon:. . . . . v . . v:algemene aandachtspunten voor overzichts- en situatietekeningen"
 EL[i]="klik hier"
 LI[i]="aanv"

 i++
//**** fasering (dwarsprofiel) *****
 AP[i]="fadp:. . . . + v v v .:profiel:<br>bestaand<br>nieuw"
 EL[i]="dwarsprofiel"
 LI[i]="dp"
 i++
 AP[i]="fadp:. . . . v v v v .:wegassen en wegindeling met maatvoering"
 EL[i]="assen"
 LI[i]="S dpaslijn"
 i++
 AP[i]="fadp:. . . . v v v v .:rijrichting"
 EL[i]="rijrichting"
 LI[i]="S dprijrichting"
 i++
 AP[i]="fadp:. . . . v + + + .:positie ten opzichte van kaartnoorden"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="fadp:. . . . - ± v v .:aan te brengen en/of te verwijderen grond of zand"
  EL[i]="grondontgraven;grondaanvullen;zandontgraven;zandaanvullen;kleiontgraven;kleiaanvullen;overzicht arceringen"
  LI[i]="S dparcering_grond_ontgraven;S dparcering_grond_aanvullen;S dparcering_zand_ontgraven;S dparcering_zand_aanvullen;S dparcering_klei_ontgraven;S dparcering_klei_aanvullen;A arceringen"
  i++
 AP[i]="fadp:. . . . - ± + + .:aan te brengen overhoogte"
 EL[i]="overhoogte"
 LI[i]="S dpoverhoogte"
 i++
 AP[i]="fadp:. . . . v v v v .:hoogte referentielijnen"
 EL[i]="eenheden;bemating"
 LI[i]="A eenheden;A maten"
 i++
 AP[i]="fadp:. . . . - ± + + .:verkanting van de weg"
 EL[i]="verkanting"
 LI[i]="S dpverkanting"
 i++
 AP[i]="fadp:. . . . ± v v v .:afwateringsdetails"
 EL[i]="waterhuishuishouding"
 LI[i]="S dpwaterhuishouding"
 i++
 AP[i]="fadp:. . . . - ± v v .:cunet"
 EL[i]="grondwerk"
 LI[i]="S dpgrondwerk"
 i++
 AP[i]="fadp:. . . . ± + v v .:geleiderail"
 EL[i]="geleiderail"
 LI[i]="S dpgeleiderail"
 i++
 AP[i]="fadp:. . . . v v v v .:geluidswerende voorzieningen"
 EL[i]="geluidwerendevoorzieningen"
 LI[i]="S dpgeluidswerende_voorzieningen"
 i++
 AP[i]="fadp:. . . . - ± ± ± .:relevante kleine werken (zoals drains)"
 EL[i]="diversen"
 LI[i]="S dpdiversen"
 i++
 AP[i]="fadp:. . . . + + + + .:verlichting"
 EL[i]="verlichting"
 LI[i]="S dpverlichting"
 i++
 AP[i]="fadp:. . . . v v v v .:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"

 i++
//**** fasering (lengteprofiel) *****
 AP[i]="falp:. . . . . v v v .:profiel van de hoofdas en andere assen (zoals toe- en afritten)"
 EL[i]="assen"
 LI[i]="S lpaslijn"
 i++
 AP[i]="falp:. . . . . v v v .:bestaand maaiveld"
 EL[i]="maaiveld"
 LI[i]="S lpmaaiveld"
 i++
 AP[i]="falp:. . . . . v v v .:maatvoering van lengteprofielen"
 EL[i]="maatbalk"
 LI[i]="S lpmaatbalk"
 i++
 AP[i]="falp:. . . . . v v v .:kruisingen met wegen, spoorwegen, waterwegen en leidingen"
 EL[i]="kunstwerken"
 LI[i]="S lpkunstwerk" 
 i++
 AP[i]="falp:. . . . . v v v .:hoogte referentielijnen"
 EL[i]="eenheden;maataanduidingen"
 LI[i]="A eenheden;A maten"
 i++
 AP[i]="falp:. . . . . + v v .:aan te brengen en/of te verwijderen grond of zand"
 EL[i]="lengteprofiel arcering;arceringen"  
 LI[i]="S lparcering;A arceringen"
 i++
 AP[i]="falp:. . . . . ± + ± .:te verwachten zettingslijn"
 EL[i]="zettingslijn"
 LI[i]="S lpzettingslijn"
 i++
 AP[i]="falp:. . . . . ± v v .:cunet"
 EL[i]="grondwerk"
 LI[i]="S lpgrondwerk"

 i++
 AP[i]="falp:. . . . . ± ± ± .:verticale drainage"
 EL[i]="verticale drainage"
 LI[i]="S whvertikale_drainage"
 i++
 AP[i]="falp:. . . . . v v v .:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"

 i++
//**** fasering (situatie) *****
 AP[i]="fasi:. . . . v v v . .:eindsituatie vorige fase of beginsituatie deze fase"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="fasi:. . . . v v v . .:te bereiken eindsituatie in deze fase"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="fasi:. . . . v v v . .:onderliggend wegennet en diversen"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="fasi:. . . . v v v . .:hoofd(assen),<br>askilometrering en<br>aslabels"
 EL[i]="assen;kilometrering"
 LI[i]="as;S askilometrering"
 i++
 AP[i]="fasi:. . . . v v v . .:polders"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="fasi:. . . . v v v . .:polderpeil, zomerpeil en winterpeil"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="fasi:. . . . v v v . .:polderscheiding en/of waterschapsgrens"
 EL[i]="grenzen"
 LI[i]="kd"
 i++
 AP[i]="fasi:. . . . v v v . .:aangeven waar verkeer rijdt tijdens de uitvoering van de fase"
 EL[i]="omleidingsroute"
 LI[i]="S vmomleidingsroute"
 i++
 AP[i]="fasi:. . . . v + + . .:(schema van) werkvakken die voor de volgende fase klaar moeten zijn"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="fasi:. . . . - + v . .:uit te breken verharding"
 EL[i]="verwijderen verharding;arceringen"
 LI[i]="vh;A arceringen"
 i++
 AP[i]="fasi:. . . . - ± v . .:freesvakken en/of in te zagen asfalt"
 EL[i]="freesvakken;arceringen"
 LI[i]="S vhfreesvak;A arceringen"
 i++
 AP[i]="fasi:. . . . - + v . .:aan te brengen en/of te verwijderen grond of zand"
 EL[i]="grondwerk"
 LI[i]="gw"
 i++
 AP[i]="fasi:. . . . - ± + . .:asfalttypen en andere verhardingen"
 EL[i]="verhardingen;arceringen"
 LI[i]="vh;A arceringen"
 i++
 AP[i]="fasi:. . . . - v v . .:werken van derden:<br>kunstwerken en spoor<br>kabels en leidingen"
 EL[i]="kunstwerken;kabels & leidingen"
 LI[i]="vh;kl"
 i++
 AP[i]="fasi:. . . . - ± ± . .:tijdelijke afwatering en waterhuishouding"
 EL[i]="waterhuishouding"
 LI[i]="wh"
 i++
 AP[i]="fasi:. . . . - + + . .:tijdelijke bewegwijzering"
 EL[i]="bewegwijzering"
 LI[i]="bw"
 i++
 AP[i]="fasi:. . . . - + + . .:relevante zaken die uitgevoerd moeten worden in de betreffende fase"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="fasi:. . . . v v v . .:algemene aandachtspunten voor alle tekeningen"
 EL[i]="klik hier"
 LI[i]="alga"
 i++
 AP[i]="fasi:. . . . v v v . .:algemene aandachtspunten voor overzichts- en situatietekeningen"
 EL[i]="klik hier"
 LI[i]="aanv"

 i++
 //**** fasering (verkeersmaatregels) *****
  AP[i]="favm:. . . . . . . + + v .:topografie"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="favm:. . . . . ± ± v .:geleiderail en/of<br>barrier"
  EL[i]="geleiderail;barrier/beton;barrier/staal"
  LI[i]="gr;S grbarrier_beton;S grbarrier_staal"
  i++
  AP[i]="favm:. . . . . ± ± v .:flexibele reflectiepaal"
  EL[i]="reflectiepaal"
  LI[i]="S wmreflectiepaal"
  i++
  AP[i]="favm:. . . . . ± ± v .:geleidebaken (ook kattenogen)"
  EL[i]="geleidebaken"
  LI[i]="S vmgeleidebaken"
  i++
  AP[i]="favm:. . . . . ± ± v .:tijdelijke markering"
  EL[i]="markeringen"
  LI[i]="mk"
  i++
  AP[i]="favm:. . . . . ± ± v .:alternerende lichten (geleidingslichten, voorwaarschuwing RVI)"
  EL[i]="bebording"
  LI[i]="S vmbebording"
  i++
  AP[i]="favm:. . . . . ± ± v .:anti-verblindingsscherm"
  EL[i]="anti =verblindingsscherm"
  LI[i]="S granti_verblindingsscherm"
  i++
  AP[i]="favm:. . . . . ± ± v .:noodportalen ten behoeve van signalering"
  EL[i]="portaal"
  LI[i]="S bwportaal" 
  i++
  AP[i]="favm:. . . . . ± ± v .:bewegwijzering"
  EL[i]="bewegwijzering"
  LI[i]="bw"
  i++
  AP[i]="favm:. . . . . ± ± v .:kabels en leidingen"
  EL[i]="kabels & leidingen"
  LI[i]="kl"
  i++
  AP[i]="favm:. . . . . v v v .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="favm:. . . . . v v v .:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"
 
  i++
 //**** geleiderail *****
  AP[i]="glrl:. . . . . . . v v v .:bestaande en nieuwe situatie (Bij bestaande situatie alles van vorig WO op één laag plaatsen)"
  EL[i]="ondergronden"
  LI[i]="og"
  i++
  AP[i]="glrl:. . . . . v v v .:onderliggend wegennet"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="glrl:. . . . . v v v .:hoofd(assen),<br>askilometrering en<br>aslabels"
  EL[i]="assen;kilometrering"
  LI[i]="as;S askilometrering"
  i++
  AP[i]="glrl:. . . . . v v v .:geleiderail algemeen (bestaand, te verwijderen en nieuw)"
  EL[i]="geleiderail"
  LI[i]="gr"
  i++
  AP[i]="glrl:. . . . . - v v .:geleiderail gespecificeerd"
  EL[i]="geleiderail"
  LI[i]="gr"
  i++
  AP[i]="glrl:. . . . . + v v .:rimob's en barriers"
  EL[i]="rimob;barrierbeton;barrierstaal"
  LI[i]="S grrimob;S grbarrier_beton;S grbarrier_staal"
  i++
  AP[i]="glrl:. . . . . + v v .:verankeringsconstructie"
  EL[i]="verankeringl_ak;verankeringl_al;verankeringr_ak;verankeringr_al"
  LI[i]="S grverankerl_ak;S grverankerl_al;S grverankerr_ak;S grverankerr_al"
  i++
  AP[i]="glrl:. . . . . v v v .:portalen en andere obstakels"
  EL[i]="bewegwijzering;wegmeubilair"
  LI[i]="bw;wm"
  i++
  AP[i]="glrl:. . . . . - v v .:details, zoals overgangsconstructies"
  EL[i]="diverse"
  LI[i]="gr"
  i++
  AP[i]="glrl:. . . . . - v v .:praatpalen"
  EL[i]="praatpaal"
  LI[i]="S wmpraatpaal"
  i++
  AP[i]="glrl:. . . . . - v v .:overstapconstructie voor praatpalen"
  EL[i]="overstapconstructie"
  LI[i]="S groverstapconstructie"
  i++
  AP[i]="glrl:. . . . . - v v .:schuifconstructies"
  EL[i]="schuifconstructie"
  LI[i]="S grschuifconstructie" 
  i++
  AP[i]="glrl:. . . . . v v v .:anti-verblindingsscherm"
  EL[i]="antiverblindingsscherm"
  LI[i]="S granti_verblindingsscherm"
  i++
  AP[i]="glrl:. . . . . v v v .:bebakening"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="glrl:. . . . . n ± v .:plaatsingstabel"
  EL[i]="tekst"
  LI[i]="A tekst"
  i++
  AP[i]="glrl:. . . . . v v v .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="glrl:. . . . . v v v .:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"
 
  i++
 //**** grenzen *****
  AP[i]="grzn:. . . . . v . . .:bestaande en nieuwe situatie (Bij bestaande situatie alles van vorig WO op één laag plaatsen)"
  EL[i]="ondergronden"
  LI[i]="og"
  i++
  AP[i]="grzn:. . . . . v . . .:(rijks)eigensdomsgrens"
  EL[i]="rijkseigendomsgrens"
  LI[i]="S kdrijkseigendomsgrens"
  i++
  AP[i]="grzn:. . . . . v . . .:gemeentegrens"
  EL[i]="gemeentegrens"
  LI[i]="S kdgemeentegrens"
  i++
  AP[i]="grzn:. . . . . v . . .:kadastrale gegevens"
  EL[i]="kadastrale gegevens; grondaankoop"
  LI[i]="kd;ga"
  i++
  AP[i]="grzn:. . . . . v . . .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="grzn:. . . . . v . . .:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"
 
  i++
 //**** inrichting beplanting *****
  AP[i]="inbp:. . . . . . v . .:situatie (Alles van vorig WO op één laag plaatsen)"
  EL[i]="ondergronden"
  LI[i]="og"
  i++
  AP[i]="inbp:. . . . . . v . .:beheersgrenzen"
  EL[i]="grenzen"
  LI[i]="kd"
  i++
  AP[i]="inbp:. . . . . . v . .:plantensoorten"
  EL[i]="beplanting"
  LI[i]="bp"
  i++
  AP[i]="inbp:. . . . . . v . .:beplantingsgraad (dichtheid)"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="inbp:. . . . . . v . .:oppervlakten met plantensoorten of aantallen bomen"
  EL[i]="beplanting"
  LI[i]="bp"
  i++
  AP[i]="inbp:. . . . . . v . .:plantgaten of sleuven"
  EL[i]="beplanting overig"
  LI[i]="S bpoverig" 
  i++
  AP[i]="inbp:. . . . . . v . .:beplantingshoogte"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="inbp:. . . . . . ± . .:stambescherming"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="inbp:. . . . . . v . .:te verwijderen of te verplaatsen planten"
  EL[i]="beplanting"
  LI[i]="bp"
  i++
  AP[i]="inbp:. . . . . . v . .:(achtergrond)beplanting ten behoeve van bebakening"
  EL[i]="achtergrond beplanting"
  LI[i]="bp"
  i++
  AP[i]="inbp:. . . . . . v . .:aarden wallen of houtwallen ten behoeve van bebakening"
  EL[i]="geluidswal;houtwal"
  LI[i]="gv;S bphoutwal"
  i++
  AP[i]="inbp:. . . . . . v . .:schouwpaden"
  EL[i]=" "
  LI[i]=" " 
  i++
  AP[i]="inbp:. . . . . . v . .:vrije zichtruimte"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="inbp:. . . . . . ± . .:kabels en leidingen"
  EL[i]="kabels & leidingen"
  LI[i]="kl"
  i++
  AP[i]="inbp:. . . . . . v . .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="inbp:. . . . . . v . .:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"
 
  i++
 //**** kabels en leidingen (inventarisatie bestaande tracees) *****
  AP[i]="kliv:. . . . v . . . .:bestaande en nieuwe situatie (Bij bestaande situatie alles van vorig WO op één laag plaatsen)"
  EL[i]="ondergronden"
  LI[i]="og"
  i++
  AP[i]="kliv:. . . . v . . . .:gegevens onderliggend wegennet"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="kliv:. . . . v . . . .:kabel- en leidingentracees met omschrijving van de aanwezige kabels en leidingen"
  EL[i]="kabel & leidingen"
  LI[i]="kl"
  i++
  AP[i]="kliv:. . . . v . . . .:relevante kenmerken, zoals diameter, type enz."
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="kliv:. . . . v . . . .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="kliv:. . . . v . . . .:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"
 
  i++
 //**** kabels en leidingen (nieuwe tracees) *****
  AP[i]="klnt:. . . . . v . . .:bestaande en nieuwe situatie (Bij bestaande situatie alles van vorig WO op één laag plaatsen)"
  EL[i]="ondergronden"
  LI[i]="og"
  i++
  AP[i]="klnt:. . . . . v . . .:gegevens onderliggend wegennet"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="klnt:. . . . . v . . .:nieuwe kabel- en leidingentracees met omschrijving"
  EL[i]="kabels & leidingen"
  LI[i]="kl"
  i++
  AP[i]="klnt:. . . . . v . . .:relevante kenmerken, zoals diameter, type enz."
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="klnt:. . . . . v . . .:overkluizingen"
  EL[i]="overige kunstwerken"
  LI[i]="S kwoverig"
  i++
  AP[i]="klnt:. . . . . v . . .:mantelbuizen, afsluiters, schakelkasten enz."
  EL[i]="mantelbuizen;kabels & leidingen"
  LI[i]="S klmantelbuis;kl"
  i++
  AP[i]="klnt:. . . . . v . . .:dwars- en lengtedoorsnede (met maatvoering) schaal 1:50 of 1:100"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="klnt:. . . . . v . . .:maatvoering (waar nodig)"
  EL[i]="bemating"
  LI[i]="A maten"
  i++
  AP[i]="klnt:. . . . . v . . .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="klnt:. . . . . v . . .:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"
 
 i++
 //**** matenschema kunstwerken *****
  AP[i]="makw:. . . . v v . . .:assenschema van snijdende assen met:<br>tangentpunten<br>stralen<br>kilometrering<br>asnamen (alles ter plaatse van het kunstwerk)"
  EL[i]="assen;kilometrering"
  LI[i]="as;S askilometrering"
  i++
  AP[i]="makw:. . . . ± v . . .:aangeven coördinaten ter plaatse van snijding assen in x,y en z"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="makw:. . . . ± v . . .:hoeken"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="makw:. . . . ± v . . .:profiel van vrije ruimte"
  EL[i]="bemating"
  LI[i]="A maten"
  i++
  AP[i]="makw:. . . . ± v . . .:zichtruimte"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="makw:. . . . ± v . . .:maatgevend punt op de plaats waar de minimale doorrij of vaarhoogte aanwezig moet zijn (in dwarsprofiel)"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="makw:. . . . - v . . .:verkanting en<br>verkantingsdraaiing"
  EL[i]="verkanting"
  LI[i]="S vhverkanting" 
  i++
  AP[i]="makw:. . . . + v . . .:lengteprofielen met tangentpunten, stralen en maatgevend punt"
  EL[i]="lenteprofielen"
  LI[i]="lp"
  i++
  AP[i]="makw:. . . . + v . . .:dwarsprofiel met indeling en maatgevend punt"
  EL[i]="dwarsprofielen"
  LI[i]="dp"
  i++
  AP[i]="makw:. . . . - v . . .:grondwaterpeil"
  EL[i]="waterhuishouding"
  LI[i]="wh"
  i++
  AP[i]="makw:. . . . - ± . . .:geleiderail"
  EL[i]="geleiderail"
  LI[i]="gr"
  i++
  AP[i]="makw:. . . . - ± . . .:vrije uitbuigruimte van geleiderail"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="makw:. . . . - v . . .:geluidswerende voorziening (in dwarsprofiel)"
  EL[i]="geluidswerendevoorzieningen"
  LI[i]="S dpgeluidswerende_voorzieningen"
  i++
  AP[i]="makw:. . . . - ± . . .:verlichting"
  EL[i]="verlichting"
  LI[i]="wm"
  i++
  AP[i]="makw:. . . . - ± . . .:portalen"
  EL[i]="portalen"
  LI[i]="S bwportaal"
  i++
  AP[i]="makw:. . . . v v . . .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
 
  i++
 //**** portalen (dwarsprofiel voor bewegwijzering en signalering) *****
  AP[i]="podp:. . . . . v . . .:bestaand en nieuw profiel"
  EL[i]="dwarsprofiel"
  LI[i]="dp"
  i++
  AP[i]="podp:. . . . . v . . .:wegassen en<br>wegindeling met<br>maatvoering"
  EL[i]="as;markering;bemating"
  LI[i]="S dpaslijn;S dpmarkering;A maten"
  i++
  AP[i]="podp:. . . . . + . . .:verkanting"
  EL[i]="verkanting"
  LI[i]="S dpverkanting"
  i++
  AP[i]="podp:. . . . . + . . .:hoogte asfaltranden"
  EL[i]="verharding"
  LI[i]="S dpverharding"
  i++
  AP[i]="podp:. . . . . v . . .:portaal of uithouder met bewegwijzeringspanelen (afmeting)"
  EL[i]="portaal;uithouder;signalering"
  LI[i]="S dpportaal;S dpuithouder;S dpsignalering"  
  i++
  AP[i]="podp:. . . . . ± . . .:afwatering"
  EL[i]="waterhuishouding"
  LI[i]="S dpwaterhuishouding"
  i++
  AP[i]="podp:. . . . . v . . .:rijrichting"
  EL[i]="rijrichting"
  LI[i]="S dprijrichting"
  i++
  AP[i]="podp:. . . . . + . . .:geleiderail"
  EL[i]="geleiderail"
  LI[i]="S dpgeleiderail"
  i++
  AP[i]="podp:. . . . . + . . .:geluidswerende voorzieningen"
  EL[i]="geluidswerende voorzieningen"
  LI[i]="S dpgeluidswerende_voorzieningen"
  i++
  AP[i]="podp:. . . . . + . . .:damwanden"
  EL[i]="diversen"
  LI[i]="S dpdiversen"
  i++
  AP[i]="podp:. . . . . + . . .:kabels en leidingen"
  EL[i]="diversen"
  LI[i]="S dpdiversen"
  i++
  AP[i]="podp:. . . . . v . . .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
 
  i++
 //**** portalen (situatie) *****
  AP[i]="posi:. . . . . v . . .:bewegwijzeringsportalen<br>(uithouders),<br>metrering en<br>as"
  EL[i]="portaal;uithouder;bewegwijzering(ROA);bewegwijzering(RONA);kilometrering;as"
  LI[i]="S bwportaal;S bwuithouder;S bwroa;S bwrona;S askilometrering;as" 
  i++
  AP[i]="posi:. . . . . v . . .:panelen (eventueel met plaatsnamen) uit het ANWB-bewegwijzeringsplan"
  EL[i]="portaal;uithouder"
  LI[i]="S bwportaal;S bwuithouder"
  i++
  AP[i]="posi:. . . . . v . . .:paneelnummers en verwijzing naar het betreffende bewegwijzeringsplan"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="posi:. . . . . v . . .:E-borden, bordnummers en verwijzingen naar het bewegwijzeringsplan"
  EL[i]="bewegwijzering"
  LI[i]="bw;"
  i++
  AP[i]="posi:. . . . . v . . .:coördinaten van het hart van de poeren ten behoeve van sonderingen"
  EL[i]="poeren"
  LI[i]="S bwpoer"
  i++
  AP[i]="posi:. . . . . v . . .:signaleringsportalen met matrixborden,<br>assen en<br>kilometrering"
  EL[i]="portaal;uithouder;signalering;kilometrering;as"
  LI[i]="S bwportaal;S bwuithouder;S bwsignalering;S askilometrering;as" 
  i++
  AP[i]="posi:. . . . . v . . .:onderstations voor signalering"
  EL[i]="signalering onderstations"
  LI[i]="kl"
  i++
  AP[i]="posi:. . . . . v . . .:kabeltracees van signalering"
  EL[i]="signalering kabels"
  LI[i]="S klsignalering" 
  i++
  AP[i]="posi:. . . . . v . . .:dynamische route informatiepanelen (DRIP's)"
  EL[i]="signalering"
  LI[i]="S bwsignalering"
  i++
  AP[i]="posi:. . . . . ± . . .:funderingsdrukken"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="posi:. . . . . ± . . .:afwatering"
  EL[i]="waterhuishouding"
  LI[i]="wh"
  i++
  AP[i]="posi:. . . . . v . . .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="posi:. . . . . v . . .:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"
 
  i++
 //**** praatpalen *****
  AP[i]="prpa:. . . . . . v . .:eindsituatie"
  EL[i]=" " 
  LI[i]=" "
  i++
  AP[i]="prpa:. . . . . . v . .:hoofd(assen),<br>askilometrering en<br>aslabels"
  EL[i]="assen;kilometrering"
  LI[i]="as;S askilometrering"
  i++
  AP[i]="prpa:. . . . . . v . .:praatpalen"
  EL[i]="praatpalen"
  LI[i]="S wmANWB_praatpaal"
  i++
  AP[i]="prpa:. . . . . . v . .:nummers van de praatpalen"
  EL[i]="tekst"
  LI[i]="A tekst"
  i++
  AP[i]="prpa:. . . . . . v . .:kabeltracees van de praatpalen"
  EL[i]="praatpaal kabels & leidingen"
  LI[i]="S klpraatpaal"
  i++
  AP[i]="prpa:. . . . . . v . .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="prpa:. . . . . . v . .:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"
 
 i++
 //**** bebording en Reglement Verkeersregels en Verkeerstekens *****
  AP[i]="rvvb:. . . . . ± ± v .:bestaande situatie"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="rvvb:. . . . . ± v v .:bordnummers,<br>assen en<br>kilometrering"
  EL[i]="tekst;assen;kilometrering"
  LI[i]="A tekst;as;S askilometrering"
  i++
  AP[i]="rvvb:. . . . . ± ± v .:afbeeldingen op de borden"
  EL[i]="rvv borden"
  LI[i]="S wmverkeersbord"
  i++
  AP[i]="rvvb:. . . . . ± ± v .:afmetingen van de borden"
  EL[i]="tekst"
  LI[i]="A tekst"
  i++
  AP[i]="rvvb:. . . . . ± ± v .:voorwaarschuwingsseinen"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="rvvb:. . . . . ± ± v .:reflecterende voorzieningen"
  EL[i]="reflector paal"
  LI[i]="S wmreflectorpaal"
  i++
  AP[i]="rvvb:. . . . . v v v .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="rvvb:. . . . . v v v .:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"
 
  i++
 //**** tervisielegging grondzaken (overzichtstekening) *****
  
  AP[i]="tgov:. . . . . v . . .:bestaande situatie"
  EL[i]="ondergronden "
  LI[i]="og"
  i++
  AP[i]="tgov:. . . . . v . . .:schaalaanduiding bij voorkeur 1:10.000 of 1:25.000"
  EL[i]="schaal"
  LI[i]="A schalen"
  i++
  AP[i]="tgov:. . . . . v . . .:weggedeelten waarop onteigening betrekking heeft"
  EL[i]="aankoopgrens"
  LI[i]="S gaaankoopgrens"
  i++
  AP[i]="tgov:. . . . . v . . .:gemeentegrenzen"
  EL[i]="gemeentegrenzen"
  LI[i]="S kdgemeentegrens"
  i++
  AP[i]="tgov:. . . . . v . . .:gemeente-aanduidingen"
  EL[i]="tekst"
  LI[i]="A tekst"
  i++
  AP[i]="tgov:. . . . . v . . .:straatnamen"
  EL[i]="tekst"
  LI[i]="A tekst"
  i++
  AP[i]="tgov:. . . . . v . . .:kilometrering"
  EL[i]="kilometrering"
  LI[i]="S askilometrering"
  i++
  AP[i]="tgov:. . . . . v . . .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="tgov:. . . . . v . . .:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"
  i++
//**** tervisielegging grondzaken (situatietekening) *****
 AP[i]="tgsi:. . . . . v . . .:onderliggend  wegennet"
 EL[i]=" "
 LI[i]=" "
 i++
 AP[i]="tgsi:. . . . . v . . .:hoofd(assen),<br>askilometrering en<br>aslabels"
 EL[i]="assen;kilometrering"
 LI[i]="as;S askilometrering"
 i++
 AP[i]="tgsi:. . . . . v . . .:gemeente-aanduidingen (omkaderd)"
 EL[i]="tekst"
 LI[i]="A tekst"
 i++
 AP[i]="tgsi:. . . . . v . . .:(gemeente)grenzen"
 EL[i]="grenzen"
 LI[i]="kd"
 i++
 AP[i]="tgsi:. . . . . v . . .:bestaande en nieuwe rijkseigensdomsgrenzen en onteigeningsgrenzen"
 EL[i]="rijkseigendomsgrens;rijkseigendomsgrens gepland"
 LI[i]="S kdrijkseigendomsgrens;S kdrijkseigendomsgrens_gepland"
 i++
 AP[i]="tgsi:. . . . . v . . .:ter beschikking te stellen gronden"
 EL[i]="grondaankoop"
 LI[i]="ga"
 i++
 AP[i]="tgsi:. . . . . v . . .:nieuwe situatie. Denk ook aan te maken:<br>duikers,<br>fietspaden,<br>voetpaden,<br>taluds en<br>sloten"
  EL[i]="kunstwerken;verharding;grondwerk;waterhuishouding"
  LI[i]="kw;vh;gw;wh"
  i++
  AP[i]="tgsi:. . . . . v . . .:straatnamen"
  EL[i]="tekst"
  LI[i]="A tekst"
  i++
  AP[i]="tgsi:. . . . . v . . .:te maken hoofdrijbanen en toe- en afritten"
  EL[i]="assen;verhardingen"
  LI[i]="as;vh"
  i++
  AP[i]="tgsi:. . . . . v . . .:ontsluiting van percelen"
  EL[i]="verhardingen"
  LI[i]="vh"
  i++
  AP[i]="tgsi:. . . . . v . . .:geluidswerende voorzieningen"
  EL[i]="geluidswerende voorzieningen"
  LI[i]="gv"
  i++
  AP[i]="tgsi:. . . . . v . . .:te verplaatsen kunstwerken/bebouwing"
  EL[i]="kunstwerken;bebouwing"
  LI[i]="kw;ga"
  i++
  AP[i]="tgsi:. . . . . v . . .:kunstwerken"
  EL[i]="kunstwerken"
  LI[i]="kw"
  i++
  AP[i]="tgsi:. . . . . v . . .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="tgsi:. . . . . v . . .:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"
 
  i++
 //**** verlichtingsplan *****
  AP[i]="vlpl:. . . . . v . . .:masten en armaturen"
  EL[i]="lichtmast;lijnverlichting"
  LI[i]="S wmlichtmast;S wmlijnverlichting"
  i++
  AP[i]="vlpl:. . . . . v . . .:kabels (inclusief nummering)"
  EL[i]="kabels & leidingen"
  LI[i]="kl"
  i++
  AP[i]="vlpl:. . . . . v . . .:moffen"
  EL[i]="kabels & leidingen"
  LI[i]="kl"
  i++
  AP[i]="vlpl:. . . . . v . . .:mantelbuizen"
  EL[i]="mantelbuis"
  LI[i]="S klmantelbuis"
  i++
  AP[i]="vlpl:. . . . . v . . .:voedingspunten van energieleverend bedrijf"
  EL[i]="kabels & leidingen"
  LI[i]="kl"
  i++
  AP[i]="vlpl:. . . . . v . . .:laagspanningsverdeelkasten"
  EL[i]="kabels & leidingen"
  LI[i]="kl"
  i++
  AP[i]="vlpl:. . . . . v . . .:trafostations en andere energiestations"
  EL[i]="kabels & leidingen"
  LI[i]="kl"
  i++
  AP[i]="vlpl:. . . . . v . . .:portalen"
  EL[i]="portalen;uithouders"
  LI[i]="S bwportaal;S bwuithouder"
  i++
  AP[i]="vlpl:. . . . . v . . .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="vlpl:. . . . . v . . .:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"
 
  i++
 //**** waterhuishouding ****
  AP[i]="wahu:. . . . . v . . .:grenzen van waterschappen en Hoogheemraadschappen"
  EL[i]="grenzen"
  LI[i]="kd"
  i++
  AP[i]="wahu:. . . . . v . . .:benoemen van vaarten (hoofdwatergangen)"
  EL[i]="ondergronden;tekst"
  LI[i]="og;A tekst"
  i++
  AP[i]="wahu:. . . . . v . . .:polders"
  EL[i]="tekst"
  LI[i]="A tekst"
  i++
  AP[i]="wahu:. . . . . v . . .:polderpeil, zomerpeil en winterpeil"
  EL[i]="tekst"
  LI[i]="A tekst"
  i++
  AP[i]="wahu:. . . . . v . . .:boezempeil of bodempeil"
  EL[i]="tekst "
  LI[i]="A tekst"
  i++
  AP[i]="wahu:. . . . . v . . .:bestaande watergangen,<br>te dempen watergangen en<br>te graven watergangen"
  EL[i]="watergangen;grondwerk;ondergronden"
  LI[i]="S whwatergang;gw;og"
  i++
  AP[i]="wahu:. . . . . ± . . .:te dempen en te graven wateroppervlakken"
  EL[i]="ondergronden;waterhuishouding;grondwerk"
  LI[i]="og;wh;gw"
  i++
  AP[i]="wahu:. . . . . v . . .:breedte op de waterlijn:<br>situatie<br>dwarsprofiel"
  EL[i]="bemating"
  LI[i]="A maten"
  i++
  AP[i]="wahu:. . . . . v . . .:bodemdiepte en bodembreedte:<br>situatie<br>dwarsprofiel"
  EL[i]="bemating"
  LI[i]="A maten"
  i++
  AP[i]="wahu:. . . . . v . . .:afmetingen van sloten en/of vijvers (in dwarsprofiel)"
   EL[i]="bemating"
  LI[i]="A bemating"
  i++
  AP[i]="wahu:. . . . . v . . .:waterverloop en stromingsrichting van sloten"
  EL[i]="stroomrichting"
  LI[i]="S whstroomricht"
  i++
  AP[i]="wahu:. . . . . v . . .:waterkeringen"
  EL[i]="kunstwerken"
  LI[i]="kw"
  i++
  AP[i]="wahu:. . . . . v . . .:bestaande duikers, te maken duikers en<br>type duikers"
  EL[i]="duikers"
  LI[i]="S whduiker"
  i++
  AP[i]="wahu:. . . . . v . . .:type stuw, sluis, pomp en gemaal"
  EL[i]="kunstwerken"
  LI[i]="kw"
  i++
  AP[i]="wahu:. . . . . v . . .:dammen en beren"
  EL[i]="kunstwerken"
  LI[i]="kw"
  i++
  AP[i]="wahu:. . . . . v . . .:taludhelling"
  EL[i]="grondwerk"
  LI[i]="gw"
  i++
  AP[i]="wahu:. . . . . ± . . .:nadere eisen, zoals bekleding en beschoeiing"
  EL[i]="waterbouw"
  LI[i]="wb"
  i++
  AP[i]="wahu:. . . . . ± . . .:asfaltoppervlakken"
  EL[i]="verhardingen"
  LI[i]="vh"
  i++
  AP[i]="wahu:. . . . . v . . .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="wahu:. . . . . v . . .:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"
 
  i++
 //**** wegontwerp (dwarsprofiel) ****
  AP[i]="wodp:- ± ± ± v v v v .:bestaand profiel"
  EL[i]="verharding;maaiveld;maataanduidingen"
  LI[i]="S dpverharding;S dpmaaiveld;A maten"
  i++
  AP[i]="wodp:v v v v v v v v .:nieuw profiel"
  EL[i]="verharding;maaiveld;eenheden;maataanduidingen"
  LI[i]="S dpverharding;S dpmaaiveld;A eenheden;A maten"
  i++
  AP[i]="wodp:v v v v v v v v .:wegassen en wegindeling met maatvoering"
  EL[i]="assen;maatvoering"
  LI[i]="S dpaslijn;A maten"
  i++
  AP[i]="wodp:v v v v v + + + .:positie ten opzichte van het kaartnoorden"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="wodp:- - - - - ± v ± .:hoogtematen"
  EL[i]="maataanduidingen"
  LI[i]="A maten"
  i++
  AP[i]="wodp:- - - v v v v v .:hoogte referentielijnen"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="wodp:- - - - - + + + .:hellingshoeken van taluds"
  EL[i]=" "
  LI[i]=" "
  i++
  AP[i]="wodp:- - - - - ± v ± .:verkanting"
  EL[i]="verkanting"
  LI[i]="S dpverkanting"
  i++
  AP[i]="wodp:v v v v v v v v .:rijrichting"
  EL[i]="rijrichting"
  LI[i]="S dprijrichting"
  i++
  AP[i]="wodp:- - - - - ± v ± .:aan te brengen en/of te verwijderen grond/zand"
  EL[i]="grondontgraven;grondaanvullen;zandontgraven;zandaanvullen;kleiontgraven;kleiaanvullen;overzicht arceringen"
  LI[i]="S dparcering_grond_ontgraven;S dparcering_grond_aanvullen;S dparcering_zand_ontgraven;S dparcering_zand_aanvullen;S dparcering_klei_ontgraven;S dparcering_klei_aanvullen;A arceringen"
  i++
  AP[i]="wodp:- - - - - ± + ± .:aan te brengen overhoogte"
  EL[i]="overhoogte"
  LI[i]="S dpoverhoogte"
  i++
  AP[i]="wodp:- - - - - ± v ± .:aan te brengen en/of uit te breken verharding"
  EL[i]="verharding"
  LI[i]="S dpverharding"
  i++
  AP[i]="wodp:- - - - ± v v ± .:afwateringsdetails"
  EL[i]="waterhuishouding"
  LI[i]="S dpwaterhuishouding"
  i++
  AP[i]="wodp:- - - - - ± v ± .:cunetten"
  EL[i]="grondwerk"
  LI[i]="S dpgrondwerk"
  i++
  AP[i]="wodp:- ± ± ± ± + v ± .:geleiderail"
  EL[i]="geleiderail"
  LI[i]="S dpgeleiderail"
  i++
  AP[i]="wodp:- - - - + + + + .:verlichting"
  EL[i]="verlichting"
  LI[i]="S dpverlichting"
  i++
  AP[i]="wodp:- - v v v v v ± .:geluidswerende voorzieningen"
  EL[i]="geluidwerende voorzieningen"
  LI[i]="S dpgeluidswerende_voorzieningen"
  i++
  AP[i]="wodp:- - ± ± ± v v ± .:kunstwerken"
  EL[i]="kunstwerken"
  LI[i]="kw"
  i++
  AP[i]="wodp:- - - - - ± ± ± .:relevante kleine werken, zoals drains"
  EL[i]="diversen"
  LI[i]="S dpdiversen"
  i++
  AP[i]="wodp:v v v v v v v v .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
 
  i++
 //**** wegontwerp (lengteprofiel) ****
  AP[i]="wolp:- v v v v v v v .:profiel van de hoofdas in de eindsituatie"
  EL[i]="assen"
  LI[i]="S lpaslijn"
  i++
  AP[i]="wolp:- - - ± v v v v .:diverse profielen van de eindsituatie (o.a. toe- en afritten)"
  EL[i]="lengteprofiel"
  LI[i]="lp"
  i++
  AP[i]="wolp:- - - - - v v ± .:maatvoering van lengteprofielen"
  EL[i]="matenbalk;schalen"
  LI[i]="S lpmaatbalk;A schalen"
  i++
  AP[i]="wolp:- ± ± v v v v ± .:hoogte referentielijnen"
  EL[i]="maataanduidingen"
  LI[i]="A maten"
  i++
  AP[i]="wolp:± ± ± v v v v v .:bestaand maaiveld"
  EL[i]="maaiveld"
  LI[i]="S lpmaaiveld"
  i++
  AP[i]="wolp:- - - - - + v ± .:aan te brengen en/of te verwijderen grond/zand"
  EL[i]="arcering;overicht arceringen"
  LI[i]="S lparcering;A arceringen"
  i++
  AP[i]="wolp:- - - - - ± + ± .:te verwachten zettingslijn"
  EL[i]="zettingslijn"
  LI[i]="S lpzettingslijn"
  i++
  AP[i]="wolp:- - - - - ± v v .:cunetten"
  EL[i]="grondwerk"
  LI[i]="S lpgrondwerk"
  i++
  AP[i]="wolp:- - - - - ± v ± .:vertikale drainage"
  EL[i]="vertikale drainage"
  LI[i]="S whvertikale_drainage"
  i++
  AP[i]="wolp:- ± ± ± ± v v ± .:kunstwerken"
  EL[i]="kunstwerken"
  LI[i]="kw"
  i++
  AP[i]="wolp:- ± v v v v v ± .:kruisingen met wegen, spoorwegen, waterwegen, leidingen etc."
  EL[i]="kunstwerken"
  LI[i]="S lpkunstwerk"
  i++
  AP[i]="wolp:v v v v v v v v .:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
 
  i++
 //**** wegontwerp (situatie) ****
  AP[i]="wosi:- - v v v v v ± -:bestaande situatie"
  EL[i]="ondergronden"
  LI[i]="og"
  i++
  AP[i]="wosi:- - v v v v v ± -:nieuwe situatie:<br>verharding<br>kunstwerken<br>grondwerk<br>geleiderail"
  EL[i]=" ;verharding;kunstwerken;grondwerk;geleiderail"
  LI[i]=" ;vh;kw;gw;gr"
  i++
  AP[i]="wosi:- - v v v v v v ±:hoofd(assen),<br>askilometrering en<br>aslabels"
  EL[i]="assen;kilometrering;tekst"
  LI[i]="as;S askilometrering;A tekst"
  i++
  AP[i]="wosi:- - - - ± v ± + +:horizontale stralen"
  EL[i]="assen"
  LI[i]="as"
  i++
  AP[i]="wosi:- - - - ± v ± + +:overgangsbogen"
  EL[i]="tangentpunten;tekst bij tangentpunt"
  LI[i]="S astangentpunten;S astangenttekst"
  i++
  AP[i]="wosi:- - ± v v v v ± n:essentiële grenzen van (bestemmings)plannen van derden"
  EL[i]="grenzen"
  LI[i]="kd"
  i++
  AP[i]="wosi:- - - - + v v ± v:waterhuishouding"
  EL[i]="waterhuishouding"
  LI[i]="wh"
  i++
  AP[i]="wosi:- - - - ± + + + +:verkantingen en<br>verkantingsdraaiingen"
  EL[i]="verkanting"
  LI[i]="S vhverkanting"
  i++
  AP[i]="wosi:- - ± ± v v v ± v:polders"
  EL[i]="tekst"
  LI[i]="A tekst"
  i++
  AP[i]="wosi:- - ± ± v v v ± v:polderscheidingen en waterschapsgrenzen"
  EL[i]="grenzen"
  LI[i]="kd"
  i++
  AP[i]="wosi:- - - - ± ± ± ± ±:essentiële elementen uit het VRI-plan"
  EL[i]="kabels & leidingen;verkeerslichten"
  LI[i]="S klVRI;S wmverkeerslicht"
  i++
  AP[i]="wosi:- - - - ± ± ± ± ±:essentiële elementen uit plannen voor verlichting, bewegwijzering en signalering"
  EL[i]="verlichting;bewegwijzering;wegmeubilair"
  LI[i]="kl;bw;wm"
  i++
  AP[i]="wosi:- - ± ± ± v v ± v:markeringen"
  EL[i]="markeringen"
  LI[i]="mk"
  i++
  AP[i]="wosi:- - ± ± ± ± ± ± ±:ondergrondse infrastructuur"
  EL[i]="kabels & leidingen"
  LI[i]="kl"
  i++
  AP[i]="wosi:- - ± ± + v v ± v:geluidswerende voorzieningen"
  EL[i]="geluidswerende voorzieningen"
  LI[i]="gv"
  i++
  AP[i]="wosi:± ± ± ± ± ± ± ± ±:bladindeling (onder verklaring)"
  EL[i]="tekeningopmaak"
  LI[i]="A hoe_opmaakobjecten"
  i++
  AP[i]="wosi:v v v v v v v v v:algemene aandachtspunten voor alle tekeningen"
  EL[i]="klik hier"
  LI[i]="alga"
  i++
  AP[i]="wosi:v v v v v v v v v:algemene aandachtspunten voor overzichts- en situatietekeningen"
  EL[i]="klik hier"
  LI[i]="aanv"

