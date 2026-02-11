De Chagelog geeft de volgende tabellen:

1. NLCS_Query_NieuweConcepten: de lijst met nieuwe concepten (NLCSObjecten, Symbolen, Arceringen, Lijntypes en meer)

Voorbeeld output:

|  nieuwConcept  |  nieuwConceptName  |  
|  ---  |  ---   |  
|  http://digitalbuildingdata.tech/nlcs/def/c3f2a787-bdce-455c-9210-911247292a7f  |  GRONDSOORTEN_GROND-GRONDWERK  |  

2. NLCS_Query_NieuweProperties: de lijst met nieuwe kenmerken van concepten

Voorbeeld output:

|  nieuwProperty  |  nieuwPropertyName  |  
|  ---  |  ---   |  
|  http://digitalbuildingdata.tech/nlcs/def/85ae245762d56c71eb33351f3dec57e5  |  MicrostationNummer  |  

3. NLCS_Query_VeranderdArceringen: de lijst met arceringen die van naam zijn veranderd (zelfde ID, zelfde URI). Merk op dat er arceringen tussen staan zonder ID's: dit zijn de aan NLCSOBjecten gekoppelde zoektermen waarmee alle arceringen met die zoekterm in de naam gevonden kunnen worden.

Voorbeeld output:

|  NLCSArcering  |  id_nummer  |  oudeNLCSArceringName  |  nieuweNLCSArceringName  |  
|  ---  |  ---   |  ---  |  ---   |  
|  http://digitalbuildingdata.tech/nlcs/def/f3f3f120-ac4d-4bbf-ba68-35fbbd6acf17  |    |  AGW-WERK  |  AGW-GRONDWERK
|  http://digitalbuildingdata.tech/nlcs/def/a1c036af-0012-4810-b45d-3d05322a239b  |  83  |  AGW-WERK_FREZEN_DIEPFREZEN-SOD  |  AGW-GRONDWERK_FREZEN_DIEP-SOD  |  

4. NLCS_Query_VeranderdLinetypes: de lijst met van naam veranderde linetypes

Voorbeeld output:

|  NLCSLijntype  |  id_nummer  |  oudeNLCSLijntypeName  |  nieuweNLCSLijntypeName  |  
|  ---  |  ---   |  ---  |  ---   |  
|  http://digitalbuildingdata.tech/nlcs/def/b62e2a62-090b-46ec-8e9c-baab7250cc47  |  96  |  IE-TERREINAFSCHEIDING_NATUURLIJK-SO  |  GR-HAAG_DRAAD-SO  |  

5. NLCS_Query_VeranderdObjects: de lijst met van naam veranderde NLCSObjecten

Voorbeeld output:

|  objectURI  |  id_nummer  |  oudLaagnaam  |  nieuweLaagnaam  |  
|  ---  |  ---   |  ---  |  ---   |  
|  http://digitalbuildingdata.tech/nlcs/def/e3d65363-f207-402c-b453-26987b0a2be2  |  3014  |  *_**_VH_GESLOTENVERHARDING_ASFALT_DEKLAAG-TRAPSGEWIJSFREZEN  |  *_**_VH_GESLOTENVERHARDING_ASFALT_DEKLAAG  | 

6. NLCS_Query_VeranderdSymbols: De lijst met van naam veranderde symbolen. Merk op dat er symbolen tussen staan zonder ID's: dit zijn de aan NLCSOBjecten gekoppelde zoektermen waarmee alle symbolen met die zoekterm in de naam gevonden kunnen worden.

Voorbeeld output:

|  NLCSSymbool  | id_nummer  | oudeNLCSSymboolName  | nieuweNLCSSymboolName
|  ---  |  ---   |  ---  |  ---   |  
|  http://digitalbuildingdata.tech/nlcs/def/3b5ee973-30b6-4509-a4d5-09ba00e104ea  |     |  SVH-DREMPEL  | SVH-DREMPEL_PREFAB  | 
|  http://digitalbuildingdata.tech/nlcs/def/b988bff3-8fef-4e85-87fe-ca43faa9f210  |  6801  |  SBC-VOORSPANNING  |  SBC-VOORSPANNING_ZONDERAANHECHTING  |  

7. NLCS_Query_Version: geeft aan welke versie in de query is gebruikt als nieuwe versie.

Voorbeeld output:

|nlcs  |  version  |
|  ---  |  ---   |
|  http://digitalbuildingdata.tech/nlcs/def/  | rv5_1_5  |

8. NLCS_Query_VervallenConcepts: Geeft een lijst met vervallen concepten

Voorbeeld output:

|  vervallenConcept  |  vervallenConceptName  |
|  ---  |  ---   |
|  http://digitalbuildingdata.tech/nlcs/def/a2c8f7db-10b6-4ccc-a061-f820842284af  |  V-SIE-WEG_VERKEERSBORD_STRAATNAAMBORD_PAAL-SO  |

9. NLCS_Query_VervallenProperties: Geeft een lijst met vervallen kenmerken van concepten

Voorbeeld output:

|  vervallenProperty  |  vervallenPropertyName  |
|  ---  |  ---   |
|  http://digitalbuildingdata.tech/nlcs/def/231afe47f3f37d3808096b36c28b4ded  |  Element  |

