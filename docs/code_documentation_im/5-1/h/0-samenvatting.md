
<table>
  <tr>
    <td><figure>
<img src="../../media/NLCS - logo klein.png" alt="NLCS logo" width="50%">
</figure></td>
    <td>Deze pagina beschrijft de technische documentatie van het objectgerichte informatiemodel van de NLCS. 
Het objectgerichte informatiemodel van de NLCS uniformeert begrippen voor het vakgebied ‘ontwerp en realisatie van openbare ruimte en bovengrondse en ondergrondse infrastructuur’ en voorziet in een ontologie die geschikt is voor zowel mens en machine.</td>
  </tr>
</table>



Het objectgerichte informatiemodel van de NLCS bestaat uit twee delen:
* Het NLCS Vocabulaire is het begrippenkader dat gebruikt wordt tijdens ontwerp en aanleg van de openbare ruimte en infrastructuur. De vocabulaire is een invulling van het 'model van begrippen' zoals dat gehanteerd wordt in het MIM. Het is tevens de invulling van het 'Toepassingstype 1' vanuit de [[NEN_2660_2_2022]] (afstemming van termen en definities). De uitdrukking is volledig in [skos-primer].
* De NLCS Ontologie is het daadwerkelijke informatiemodel. Het betreft hier het logische informatiemodel zoals MIM dat erkend. De [[NEN_2660_2_2022]] is volledig toegepast en daarmee is het de invulling van het 'Toepassingstype 3 (gegevensintegratie en innovatie). Vandaar dat de LinkedData expressie ook met [rdf-schema] en [shacl] gedaan wordt. De relatie tussen de vocabulaire en de ontologie ligt middels een rdfs:seeAlso systematiek zoals de [[NEN_2660_2_2022]] dat voorschrijft. Elke concept in de ontologie heeft zodoende een definiëring in de vocabulaire.
* De NLCS-NLCS ontology alignment naar de "klassieke" publicatie van de NLCS standaard waarin de laagnamen en visualisatie in CAD worden gedefinieerd zorgt ervoor dat deze in samenhang gebruikt kunnen worden, waarbij van elke laagnaam en symbool bekend is welk objecttype en met welke attributen en welke waardes erbij hoort.
* de NLCS-IMBOR en NLCS-GWSW alignments zorgen ervoor dat beheerdata op basis van IMBOR en GWSW kan worden uitgedrukt in de NLCS en vice versa, zodat projecten en beheerder informatie kunnen uitwisselen. 

Het objectgerichte informatiemodel van de NLCS wordt gedistribueerd in LinkedData.


