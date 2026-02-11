Hier staan query's voor de beheerder van de NLCS database.De volgende controles worden uitgedraaid bij gebruik van de nlcs-exporter:


De volgende controles worden uitgedraaid bij gebruik van de nlcs-exporter:
- [query: afwijkendeURIs](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/afwijkendeURIs.rq) controleert of er afwijkende URI's worden gebruikt, alle URI's moeten binnen de namespace "http://digitalbuildingdata.tech/nlcs/def/" passen.
- [query: controle_arceringsymbool_zonder_objectRelatie](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_arceringsymbool_zonder_objectRelatie.rq) controleert of er symbolen of arceringen zijn zonder relatie naar een object. Wanneer een arcering/symbool zelf geen relatie heeft maar zijn parent wel, dat dit voldoende is en deze arcering/symbool niet in de output genoemd hoeft te worden. Bijvoorbeeld 'SAL-AANKLEDING_AUTO1_ACHTERAANZICHT-D' heeft zelf geen directe relatie met een object, maar erft er wel een over vanuit zijn parent 'SAL-AANKLEDING'. Dit zijn de 'zoektermen' waar de objecten naar verwijzen om in de software-implementatie symbolen of arceringen te kunnen vinden waarin deze zoekterm voorkomt. 
- [query: controle_laagnaam_relaties_parentchild_saobject](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_laagnaam_relaties_parentchild_saobject.rq) controleert of er niet zowel een kind als een ouder - relatie zit tusen NLCS-object en symbool dan wel arcering. 
- [query: controle_lijntypes_zonder_objectRelatie](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_lijntypes_zonder_objectRelatie.rq) controleert of alle lijntypes zijn gekoppeld aan een object, zo niet het lijntype verwijderen. In de beheeromgeving zijn de lijntypes niet gekoppeld aan de objecten.
- [query: controle_nietBestaande_lijntype_in_object](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_nietBestaande_lijntype_in_object.rq) controleert of er verwezen wordt naar een niet-bestaand lijntype.
- [query: controle_nlcs-objecten_te_veel_subobjecten](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_nlcs-objecten_te_veel_subobjecten.rq) checkt of er NLCS-objecten met meer dan 5 subobjecten zijn. Meer mogen er niet in een laagnaam staan.
- [query: identiekenamen](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/identiekenamen.rq) draaien om te controleren of er dubbele namen voorkomen bij concepten. Bij de symbolen is dit soms zo, doordat we refereren aan groepen en een bestand soms dezelfde naam heeft als de groep. Andere dubbelingen moeten worden verwijderd in de publicatie. 


- [controle_abibliotheken.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_abibliotheken.rq) Checks existence and uniqueness of ID property of Arcering

- [controle_arceringen.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_arceringen.rq) 
    Checks:
    - existence & availability of ?id ?schaal ?vrkl_lang and ?fileURL
    - if omschrijving (name) starts with B-, V-, N-, O- or T, this value should be available as separate value as fase
    - if omschrijving (name) ends with -SO, -SOD, -SODMM , this value should be available as separate value as optie 

- [controle_arcering_name_length.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_arcering_name_length.rq)  Check if all arcerings has less than 31 character long string

- [controle_disciplines.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_disciplines.rq) Check existence & availability of ?id ?code ?omschrijving ?verklaring

- [controle_hoofdgroepen.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_hoofdgroepen.rq) Check existence & availability of ?id ?afkorting ?hoodgroep (name and definition)

- [controle_identiekenamen.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_identiekenamen.rq) Detects duplicate object names with the same uri (uniek voor hoofdgroep en topconcept)

- [controle_id_uniqueness_hoofdklassen.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_id_uniqueness_hoofdklassen.rq) Check if ID is unique within the category for following categories: Abibliotheek, Sbibliotheek, Hoofdgroepen, Discipline

- [controle_id_uniqueness_subklassen.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_id_uniqueness_subklassen.rq) Check if ID is unique within the category for following categories: NLCS-object, Arcering, Symbool, Lijnkleur, Lijnweight, Lijntype

- [controle_laagnaam_relaties_parentchild_saobject.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_laagnaam_relaties_parentchild_saobject.rq) Retrieves NLCS-objects with relations to both parent & child Symbolen and/or Arceringen. The listed saobject is the parent of which also children are linked

- [controle_lijnkleuren.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_lijnkleuren.rq) Checks if id, hex and R,G,B values exist & are available, and if R,G,B is in range [0-255]

- [controle_lijntype_optie_fase.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_lijntype_optie_fase.rq) Checks if the ID, fase and optie correctly exist for a lijntype 

- [controle_linetypes.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_linetypes.rq) Check if line type exists when associated color exists 
    - If this line type is missing, this can mean two things: the line type wasn't filled in at all for the NLCS object, or a line type that doesn't exist was filled in

- [controle_lineweights.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_lineweights.rq) VCheck if line weight exists when associated color exists.
    - If this lineweight is missing, this can mean two things: the lineweight wasn't filled in at all for the NLCS object, or a lineweight that doesn't exist was filled in

- [controle_missing_sub-objects_underscore.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_missing_sub-objects_underscore.rq) Detects missing sub-objects indicated by underscore naming conventions

- [controle_nlcs-objecten_te_veel_subobjecten.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_nlcs-objecten_te_veel_subobjecten.rq) Checks for NLCS objects that contain too many (more than 5) sub-objects 

- [controle_objects_missing_ids.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_objects_missing_ids.rq) Detects objects that are missing mandatory ID properties

- [controle_object_bewerking.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_object_bewerking.rq) Validates if in the name, after the subobject, is a "-" available, then it should have a corresponding domain value from aspect bewerkingen

- [controle_object_multiple_arcering.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_object_multiple_arcering.rq) Detects objects linked to multiple Arceringen where only one is allowed

- [controle_object_multiple_symbol.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_object_multiple_symbol.rq) Detects objects linked to multiple Symbolen where only one is allowed

- [controle_property_afwijkendeURIs.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_property_afwijkendeURIs.rq) Detects properties using non-conforming or afwijkende URIs

- [controle_sbibliotheek.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_sbibliotheek.rq) Checks existence and correctness of S-bibliotheek id and definition

- [controle_symbolen.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/controle_symbolen.rq) Checks:
    - existence & availability of ?id
    - if omschrijving (name) starts with B-, V-, N-, O- or T, this value should be available as separate value as fase
    - if omschrijving (name) ends with -S, -SO, -D, - DMM,-MM, -SOD, -SODMM, -SOMM, this value should be available as separate value as optie

- [objectenmetlijntypesmetscraps.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/objectenmetlijntypesmetscraps.rq) Lists objects that use line types defined as "verwijderen" in Autocad definition


Following queries are not used in the exporter since they are for laces schema, not for the publication.
- [laces-controle_arceringsymbool_zonder_objectRelatie.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/laces-controle_arceringsymbool_zonder_objectRelatie.rq) Detects Arcering or Symbol definitions without required object relations

- [laces-controle_lijntypes_zonder_objectRelatie.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/laces-controle_lijntypes_zonder_objectRelatie.rq) Detects Lijntypes that are not linked to any NLCS object

- [laces-controle_nietBestaande_lijntype_in_object.rq](https://github.com/nl-digigo/NLCS/blob/acceptance/code/nlcs/controlesdatabase/laces-controle_nietBestaande_lijntype_in_object.rq) Detects references to non-existing Lijntypes within objects