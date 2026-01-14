De querys zijn bedoeld voor bij de ontologie NLCS Rioleringen.

1. retrieve-concepts.rq

Output voorbeeld: 
|  uri  |  "name"  |  "seeAlso"  |  "parentUri"  |  "parentName"  |  "sameAs"  | 
|  ---  |  ---  |  ---  |  ---  |  ---  |  ---  | 
|  http://digitalbuildingdata.tech/nlcs-class/def/GWA_TRANSPORTLEIDING_BETON_EI  |  "GWA_TRANSPORTLEIDING_BETON_EI"  |  "http://digitalbuildingdata.tech/nlcs/def/b0c91813-8f81-4802-be54-bba38b76ea63"  |  "http://digitalbuildingdata.tech/nlcs-class/def/GWA_TRANSPORTLEIDING"  |  "GWA_TRANSPORTLEIDING"  |  ""  |

2. GWSW-NLCS mapping tabel.rq

Output voorbeeld: 
|  "nameGWSWStelselType"  |  "GwswStelselType"  |  "nameGWSWType"  |  "GwswType"  |  "nameStelselType"  |  "nameNLCSLaagnaam" | "NLCSLaagnaam" | "nameNLCSSymbool"  | "NLCSSymbool"  | 
|  ---  |  ---  |  ---  |  ---  |  ---  |  ---  | 
| Drainagestelsel	| http://data.gwsw.nl/1.6/totaal/Drainagestelsel |	Hulpstuk |	http://data.gwsw.nl/1.6/totaal/Hulpstuk |	DRAINAGE |	DRAINAGE_HULPSTUK |	http://digitalbuildingdata.tech/nlcs/def/69a1128e-1a85-4d08-97db-2abc6d313804 |	SRI-HULP |	http://digitalbuildingdata.tech/nlcs/def/47df2747-2f14-478d-a38b-78850d160fe4 |

* Note that GWSW labels are not retrieved via the graph but parsed from the human readible URIs!

