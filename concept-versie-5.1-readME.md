# Concept-versie 5.1 Voor Openbare Consultatie

1 november 2024 is het concept van NLCS 5.1 gepubliceerd voor een openbare consultatie. De bedoeling was dat gebruikers, experts en softwareleveranciers dit concept vier maanden lang konden uitproberen in applicaties. Op verzoek van de NLCS leveranciers wordt een technische commissie opgestart, om te onderzoeken wat er nodig is om de 5.1 versie te kunnen implementeren en te laten testen in applicaties. 

Release notes staan in de [Uitleg standaard](https://nl-digigo.github.io/NLCS/functionalspecification/5-1/).

Iedereen die het afgelopen jaar heeft meegewerkt aan de totstandkoming van deze versie wordt van harte bedankt.

## Reviewen

Reviewwijze:
* Tabellen, database en technische bestanden: via [issues](https://github.com/nl-digigo/NLCS/issues)
* Documentatie in ReSpec: de reviewperiode voor de documentatie met opmerkingen in de kantlijn is **verlopen**. Eventuele review kan altijd worden ingediende via issues. 


## Voor ontwerpers en tekenaars
* [Uitleg standaard](https://nl-digigo.github.io/NLCS/functionalspecification/5-1/)
* [Eisen aan tekeningen en modellen](https://nl-digigo.github.io/NLCS/requirementscadmodels/5-1/) 
* [Voorbeeldtekeningen](https://github.com/nl-digigo/NLCS/tree/main/docs/voorbeeldtekeningen)

## Zelf applicatie inrichten
Voor gebruikers die zelf hun CAD applicatie inrichten, is de publicatie van NLCS is ook beschikbaar in tabellen:
* [NLCS tabellen](https://github.com/nl-digigo/NLCS/tree/main/tabellen)


## Voor softwareleveranciers en ontwikkelaars
* [Eisen aan de software-implementatie van NLCS](https://nl-digigo.github.io/NLCS/requirementssoftware/) 
* [Toelichting informatiemodel](https://nl-digigo.github.io/NLCS/code_documentation/5-1): De toelichting op de uitgangspunten en modelleringswijze van het  informatiemodel in linked data
* [Toelichting gebruik sparql-endpoint en query's](https://nl-digigo.github.io/NLCS/howtoquery/): Een gebruikershandleiding voor gebruik van de linked data publicatie, met toelichting op de code van het informatiemodel, query's en beschikbare datasets.


## Relaties tot andere standaarden
* [Relaties tot andere standaarden](https://nl-digigo.github.io/NLCS/ontologyalignments/5-1): documentatie van de ontology alignments (mappings waar een computer mee kan redeneren) of voorbereidingen daartoe met andere standaarden, waaronder IMGeo (voor BGT kaartinformatie) en het GWSW (Gemeentelijk woordenboek stedelijk water)
* [Uitwisselafspraken](https://nl-digigo.github.io/NLCS/representations/5-1): Documentatie van hoe binnen NLCS wordt gewerkt met Uitwisseling van 3D objectinformatie; Hoe de uitwisseling tussen NLCS tekeningen en GIS kaarten op basis van IMGeo is geregeld; De openstaande onderzoeksvragen beschreven rondom NLCS en uitwisseling van tekeningen en modellen.


### Actuele versie NLCS-publicatie
De NLCS publicatie wordt gepubliceerd op een sparql-endpoint, die benaderbaar is vanuit applicaties. Voor uitleg zie [Toelichting gebruik sparql-endpoint en query's](https://nl-digigo.github.io/NLCS/howtoquery/).
De statische URL (het adres) van de laatste NLCS 5.1 publicatie voor de openbare consultatie is: http://hub.laces.tech/digitalbuildingdata/nlcs/acceptance/nlcs-acceptatie/versions/rv5_1_2/sparql


### Symbolen, lijntypes, arceringen, font
De symbolen, lijntypes en arceringen die in de software kunnen worden ingeladen:
* [Symbolen](https://github.com/nl-digigo/NLCS/tree/main/symbolen)
* [Lijntypes](https://github.com/nl-digigo/NLCS/tree/main/lijntypes)
* [Arceringen](https://github.com/nl-digigo/NLCS/tree/main/arcering)
* [Font](https://github.com/nl-digigo/NLCS/tree/main/font)


## Viewer 5.1

DigiGO heeft nog geen viewer waarin informatiemodellen op basis van de NEN 2660-2 kunnen worden getoond. De makkelijkste manier om door de standaard te browsen zijn de [NLCS tabellen concept 5.1](https://github.com/nl-digigo/NLCS/tree/main/tabellen/concept/5.1).


![Architectuur van de standaard](<NLCS architectuur.png>)



![Documentatie van de standaard](<NLCS documentatie.png>)


Shield: [![CC BY 4.0][cc-by-shield]][cc-by]

This work is licensed under a
[Creative Commons Attribution 4.0 International License][cc-by].

[![CC BY 4.0][cc-by-image]][cc-by]

[cc-by]: http://creativecommons.org/licenses/by/4.0/
[cc-by-image]: https://i.creativecommons.org/l/by/4.0/88x31.png
[cc-by-shield]: https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg


## Totstandkoming
De issues die verwerkt zijn in versie 5.1 zijn gebundeld in de volgende milestones:
* [Inhoudelijke issues voor 5.1](https://github.com/nl-digigo/NLCS/milestone/1)
* [Uitbreiding verkeersborden in 5.1](https://github.com/nl-digigo/NLCS/milestone/8)
* [Uitbreiding Tram voor 5.1](https://github.com/nl-digigo/NLCS/milestone/5)
* [Technische issues voor 5.1](https://github.com/nl-digigo/NLCS/milestone/15)

Reviewcommentaar op de documentatie van NLCS 5.1 is geleverd in de volgende documenten:
* [Uitleg standaard](https://nl-digigo.github.io/NLCS/functionalspecification/reviewversies/CR-NLCS_functionalspecification-20241017.html)
* [Eisen aan tekeningen en modellen](https://nl-digigo.github.io/NLCS/requirementscadmodels/reviewversies/CR-NLCS_requirementscadmodels-20241017.html) was beschikbaar voor review, maar is niet gebruikt.
* [Eisen aan de software-implementatie van NLCS](https://nl-digigo.github.io/NLCS/requirementssoftware/ontwikkeling/reviewversies/CR-NLCS_requirementssoftware_ontwikkeling-20241017.html)



