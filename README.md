# NLCS 5.0
Deze repository is de locatie voor technische documentatie en het inbrengen en opvolgen van gebruikerswensen voor NLCS, de Nederlandse CAD standaard van DigiGO.

Links hieronder zijn voor de actuele versie, 5.0
Informatie over de openbare consultatie van concept versie 5.1 van 1 november 2024 t/m 1 maart 2025 staan [hier](https://github.com/nl-digigo/NLCS/blob/main/concept-versie-5.1-readME.md)

## Beheer

* [Beheerdocument DigiGO](https://www.digigo.nu/wp-content/uploads/2024/09/BOMOS-Beheerdocument-Standaarden-digiGO-V1.0.pdf).
* [Beheerorganisatie NLCS](https://www.digigo.nu/standaarden/nlcs/beheer)
* [Beheerhandleiding NLCS](https://nl-digigo.github.io/NLCS/managementmanual)
* [Releaseprotocol NLCS](https://nl-digigo.github.io/NLCS/releaseprotocol)
* [Gebruikerswens / issue indienen](https://github.com/nl-digigo/NLCS/issues)
* [Protocol afhandelen gebruikerswensen](https://nl-digigo.github.io/NLCS/protocolissues)

## Viewer
NLCS 5.0 kan bekeken worden in de [NLCS 5.0 viewer](https://nlcs-viewer.crow.nl)

## Voor ontwerpers en tekenaars
* [Formele specificatie 5.0](https://github.com/nl-digigo/NLCS/blob/main/docs/archive/NLCS%205.0/Formele_beschrijving_NLCS_versie_5_0_V1_0.pdf)
* [Voorbeeldtekeningen](https://github.com/nl-digigo/NLCS/tree/main/docs/voorbeeldtekeningen)

### Zelf applicatie inrichten
Voor gebruikers die zelf hun CAD applicatie inrichten, is de publicatie van NLCS is ook beschikbaar in tabellen:
* [Laagtabellen 5.0](https://github.com/nl-digigo/NLCS/tree/main/tabellen/definitief/5.0)


## Voor softwareleveranciers en ontwikkelaars
* [Formele specificatie 5.0](https://github.com/nl-digigo/NLCS/blob/main/docs/archive/NLCS%205.0/Formele_beschrijving_NLCS_versie_5_0_V1_0.pdf)
* [Toelichting gebruik sparql-endpoint en query's](https://nl-digigo.github.io/NLCS/howtoquery/): Een gebruikershandleiding voor gebruik van de linked data publicatie, met toelichting op de code van het informatiemodel, query's en beschikbare datasets
* [Eisen aan de software-implementatie van NLCS](https://nl-digigo.github.io/NLCS/requirementssoftware/5-0) 
* [Toelichting informatiemodel](https://nl-digigo.github.io/NLCS/code_documentation/5-0-2/): De toelichting op de uitgangspunten en modelleringswijze van het  informatiemodel in linked data

## Relaties tot andere standaarden
* [Relaties tot andere standaarden](https://nl-digigo.github.io/NLCS/ontologyalignments/5-1): documentatie van de ontology alignments (mappings waar een computer mee kan redeneren) of voorbereidingen daartoe met andere standaarden, waaronder IMGeo (voor BGT kaartinformatie) en het GWSW (Gemeentelijk woordenboek stedelijk water)
* [Uitwisselafspraken](https://nl-digigo.github.io/NLCS/representations/5-0-2): Documentatie van hoe binnen NLCS wordt gewerkt met Uitwisseling van 3D objectinformatie; Hoe de uitwisseling tussen NLCS tekeningen en GIS kaarten op basis van IMGeo is geregeld; De openstaande onderzoeksvragen beschreven rondom NLCS en uitwisseling van tekeningen en modellen.

### Actuele versie

#### 5.02 NLCS LinkedData
Voor browsende mensen: haal / sparql uit de linknaam hieronder
De statische URL (het adres) van de NLCS 5.02 publicatie op het sparql-endpoint is: https://hub.laces.tech/digitalbuildingdata/nlcs/live/nlcs/versions/5_0_2/sparql
<br>
De dynamische URL (het adres van de laatst gepubliceerde) definitieve versie is altijd: https://hub.laces.tech/digitalbuildingdata/nlcs/live/nlcs/sparql
<br>
De dynamische url van concepten van NLCS is https://hub.laces.tech/digitalbuildingdata/nlcs/acceptance/nlcs-acceptatie/sparql 

### Symbolen, lijntypes, arceringen, font
De symbolen, lijntypes en arceringen die in de software kunnen worden ingeladen:
* [Symbolen](https://github.com/nl-digigo/NLCS/tree/main/symbolen)
* [Lijntypes](https://github.com/nl-digigo/NLCS/tree/main/lijntypes)
* [Arceringen](https://github.com/nl-digigo/NLCS/tree/main/arcering)
* [Font](https://github.com/nl-digigo/NLCS/tree/main/font)


![Architectuur van de standaard](<NLCS architectuur.png>)



![Documentatie van de standaard](<NLCS documentatie.png>)


Shield: [![CC BY 4.0][cc-by-shield]][cc-by]

This work is licensed under a
[Creative Commons Attribution 4.0 International License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg


