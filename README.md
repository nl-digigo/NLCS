# NLCS
Deze repository is de locatie voor technische documentatie en het inbrengen en opvolgen van gebruikerswensen voor NLCS, de Nederlandse CAD standaard van DigiGO.

STATUS: Deze repository is in opbouw.

## Actuele versie

### SQL
De ingang naar de  SQL database is https://www.nlcs-documentatie.nl/NLCS_5.x_5.0.0/NLCS_5.0.0/start.php.
 
Hier zit een database achter en PhP code om dit te benaderen/ beschikbaar te maken in Excel via https://www.bimloket.nl/p/452/Database-NLCS   


### LinkedData
NLCS is bezig met de overgang van een sql database naar een linked data platform. We hebben inmiddels een concept gepubliceerd met deze static URL: https://hub.laces.tech/digitalbuildingdata/nlcs/acceptance/nlcs-acceptatie/versions/v5_0  of deze dynamic url voor als u altijd de laatste versie wilt opvragen: https://hub.laces.tech/digitalbuildingdata/nlcs/acceptance/nlcs-acceptatie. Dit concept zou een weergave moeten zijn van de laatste release van NLCS zoals die in de aloude bekende database stond. Zie ook de [Viewer Concept-publicatie NLCS 5.0]( https://bimloket.github.io/ld-viewer/nlcs/)

We zijn nog bezig een viewer te maken en documentatie over het informatiemodel, welke is gebaseerd op het topmodel in de de NEN 2660-2. We zijn ook voornemens om sparql-queries te publiceren op github, zodat niet iedereen het wiel hoeft uit te vinden.

### CSV
De publicatie van NLCS is ook beschikbaar in CSV tabellen:
* [Laagtabellen](https://github.com/bimloket/NLCS/tree/main/tabellen)

### Symbolen, lijntypes, arceringen, font
De symbolen, lijntypes en arceringen die in de software kunnen worden ingeladen:
* [Symbolen](https://github.com/bimloket/NLCS/tree/main/symbolen)
* [Lijntypes](https://github.com/bimloket/NLCS/tree/main/lijntypes)
* [Arceringen](https://github.com/bimloket/NLCS/tree/main/arcering)
* [Font](https://github.com/bimloket/NLCS/tree/main/font)

### Architectuur
![Architectuur van de standaard](<NLCS architectuur.png>)

## Beheer

* [Beheerdocument DigiGO](https://www.bimloket.nl//documents/Beheerdocument_open_BIM-standaarden_v1_8.pdf)
* [Beheerorganisatie NLCS](https://www.bimloket.nl/p/434/Organisatie-beheer)
* [Releaseprotocol NLCS](https://bimloket.github.io/NLCS/releaseprotocol)

### Gebruikerswensen

Gebruikers kunnen hun wensen of vragen voor aanpssingen of uitbreidingen van NLCS plaatsen door een issue aan te maken of te reageren op issues van anderen.

* [Gebruikerswens indienen](https://github.com/bimloket/NLCS/issues)

Issues worden afgehandeld volgens [dit protocol](https://github.com/bimloket/NLCS/blob/main/instructies/RASCI%20Github%20issues%20NLCS.pdf).

## Technische documentatie
De technische documentatie staat nu nog op de [website van DigiGO](https://www.bimloket.nl/p/429/Documentatie) en zal het komende jaar vervangen worden door ReSpecs op deze repo.

* [Uitleg standaard](https://bimloket.github.io/NLCS/functionalspecification): Functionele specificatie van NLCS met daarin de toelichting op het beoogd doel en de werking van de standaard
* [Toelichting informatiemodel](https://bimloket.github.io/NLCS/code_documentation/): De toelichting op de uitgangspunten en modelleringswijze van het  informatiemodel in linked data
* [Toelichting code, datasets, query's](https://bimloket.github.io/NLCS/howtoquery/): Een gebruikershandleiding voor gebruik van de linked data publicatie, met toelichting op de code van het informatiemodel, query's en beschikbare datasets
* [Relaties tot andere standaarden](https://bimloket.github.io/NLCS/ontologyalignments/): documentatie van de ontology alignments (mappings waar een computer mee kan redeneren) of voorbereidingen daartoe met andere standaarden, waaronder IMGeo (voor BGT kaartinformatie) en het GWSW (Gemeentelijk woordenboek stedelijk water)
* [Uitwisselafspraken](https://bimloket.github.io/NLCS/representations/): Nu nog slechts een gebruikerswens. Een nader te bepalen set afspraken over de uitwisseling van modellen en tekeningen in open formaten, met daaraan toegevoegd objectinformatie

## Implementatie
* [Tekeningen en modellen maken](https://bimloket.github.io/NLCS/requirementscadmodels/)
* [Software-implementatie van NLCS](https://bimloket.github.io/NLCS/requirementssoftware/)
* [Voorbeeldtekeningen](https://www.bimloket.nl/p/432/Leren-van-anderen)

![Documentatie van de standaard](<NLCS documentatie.png>)

Shield: [![CC BY 4.0][cc-by-shield]][cc-by]

This work is licensed under a
[Creative Commons Attribution 4.0 International License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg

