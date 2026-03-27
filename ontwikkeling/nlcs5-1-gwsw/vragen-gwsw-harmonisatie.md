# Vragen GWSW-NLCS harmonisatie

Verzameling van openstaande vragen en aandachtspunten bij de harmonisatie van NLCS 5.1 met GWSW 1.6.

---

## Naamgeving en spelling

- [x] In de meeste gevallen wordt `RIOOLPUT` gebruikt in de laagnamen, incidenteel wordt `PUT` gebruikt. In die gevallen `PUT` wijzigen naar `_RIOOLPUT` om de laagnamen consequent te houden.

- [x] NLCS spelfout: volgens het Groene Boekje is de juiste spelling 'hondenhok' i.p.v. 'hondehok' in de NLCS-laagnaam.

- [ ] Hoe komen we bij de vertaling van 'INFILTRATIEPUT' uit het GWSW naar `RESERVOIR_INFILTRATIERESERVOIR`? Is `RIOOLPUT_INFILTRATIE` niet een meer bij de NLCS passende benaming?

- [ ] Infiltratieriool hernoemen naar ITR-riool (Fysiek object: Leiding > Rioolleiding > Vrijverval riolering > Infiltratieriool)

---

## Classificatie en objecthiërarchie

- [ ] In GWSW is een [aansluitput](https://data.gwsw.nl/?menu_item=classes&item=../../def/1.6.1/Basis/Aansluitput) een andere put dan een [ontstoppingsput](https://data.gwsw.nl/?menu_item=classes&item=../../def/1.6.1/Basis/Ontstoppingsput). Waarom voegen we dit in de NLCS-laagnaam over elkaar heen?

- [ ] Er bestaan lagen voor zowel `VERDEKTEPUT` als `BLINDEPUT`. GWSW kent beide termen, met nagenoeg identieke uitleg:
  - blinde put = Geen opening aan de bovenzijde
  - verdekte put = [NEN 3300:1996] rioolput waarvan de bovenzijde niet zichtbaar is.
  - NLCS kent alleen een symbool voor 'blindeput' maar bij consequent onderscheid in de laagnaam tussen 'verdekt' en 'blind' gaat het goed.
  - Is 'verdekte put' dubbel met 'blinde put'? (ROW 370)

- [ ] In NLCS wordt verzamelterm `AFSCHEIDER` gebruikt, in GWSW gaan we direct van constructieonderdeel naar olie-, slib- of vetafscheider. Is hier echt een harmonicamodel nodig, of zijn drie losse typen afscheider genoeg in de NLCS-laagnamen? En is een objecttype 'afscheider' nodig in de classificatie?

- [ ] Zelfde vraag voor `HULPSTUK`: Is dit een manier om objecten te bossen om voor tekenaars makkelijk te zoeken, of is het wenselijk om een apart hulpstuk te kunnen classificeren? Hier lijken we op twee sporen te zitten: opbossen op één laagnaam voor tekengemak, of objecten onderscheiden.

- [x] Niet alles wat onder `HULPSTUK` valt in NLCS, is ook een hulpstuk in GWSW. Een rioolafsluiter is bijvoorbeeld een constructieonderdeel, maar geen hulpstuk. Om correct te mappen moet 'hulpstuk' in NLCS dus worden gemapt naar 'constructieonderdeel' in GWSW.

- [ ] Is een waterbergende voorziening een verzamelterm / niet te classificeren object? Stipdrain en infiltratiekrat zijn geheel verschillende zaken in het GWSW. Aanvullende categorie 'waterbergende voorziening' nodig? (ROW 147)

- [ ] Is een lozingspunt nodig in de classificatie? Of kies je als ontwerper altijd meteen of het een bodem- of oppervlaktewaterlozingspunt is? Dan is harmonicamodel in tekenstandaard ook niet nodig.

---

## Dubbele / overlappende objecten

- [x] Zijn `ITR_GRINDKIST` en `ITR_RESERVOIR_INFILTRATIERESERVOIR_GRINDKOFFER` niet hetzelfde? In GWSW zijn kist en koffer synoniem.

- [x] Zijn `ITR_RETENTIE_BERGBEZINKBASIN` en `ITR_RESERVOIR_BERGBEZINKBASIN` niet hetzelfde? In GWSW wel.

- [ ] Is infiltratieput dubbel met infiltratiekolk? (ROW 328)

- [ ] Gecombineerde straat-trottoirkolk: is een combinatiekolk (ROW 331, mapping: `_KOLK_COMBIKOLK`)

---

## Ontbrekend in GWSW

- [ ] Wat is een `DRAINAGE_HULPSTUK_SCHOONMAAKSTUK`? Er zit geen schoonmaakstuk tussen de hulpstukken in GWSW 1.6.

- [ ] Wat is een `MONSTERNAMEPUT`? Kan niet gevonden worden in GWSW.

- [x] Wat is een `SPUIKRAAN`? Kan niet gevonden worden in GWSW (wel in IMBOR). In GWSW zit geen SPUIKRAAN.

- [ ] Wat is een `GELEIDEKOLK`? Kan niet gevonden worden in GWSW.

- [ ] Wat is een `TEGELPADKOLK`? Kan niet gevonden worden in GWSW.

- [ ] Wat is een `STIPDRAIN`? Komt niet voor in GWSW.

---

## Leidingen

- [ ] Is een `DRAINAGE_RIOOLLEIDING` een rioolleiding, of kunnen we specifieker zijn en zeggen dat dit een vrijverval rioolleiding is, of is het zelfs een "DT-riool" (Synoniem: "Drainage transportriool")?

- [ ] `VACUUMLEIDING_RIOOLLEIDING_MATERIAAL`: bedoelen we hier een tekstlaag waar je het materiaal in kan zetten? Er is geen indeling in lagen maar wel bij andere leidingtypen.

- [x] Binnenonderkant buis (BOB) is niet gekoppeld aan GWSW-leidingen?

- [ ] Is drukleiding niet hetzelfde als een persleiding? (ROW 261)

- [ ] Zijn bergbezinkleiding, spoelleiding, transportrioolleiding, benedenstrooms eindriool functies van de leiding, of daadwerkelijk andere leidingen? (ROW 266, 285-289)

- [ ] Behoort valleiding niet bij de constructieonderdelen thuis? (ROW 290)

- [ ] Ontluchtingsleiding: is dit onderdeel van 'leiding'? Of een constructieonderdeel? (ROW 249)

- [ ] Mantelbuis: is dit niet een op zichzelf staand object, geen onderdeel van 'leiding', danwel onderdeel van kabels en leidingen? (ROW 248)

---

## Putten

- [ ] IBA valt onder bouwwerk in GWSW, zou deze niet onder aansluitput of rioolput moeten vallen? (ROW 64-69)

- [ ] Hoort septictank ook niet onder aansluitput? (ROW 70)

- [ ] Erfafscheidingsput: onduidelijke definitie, is een functie. Controleput of ontstoppingsstuk? Erfscheidingsput is geen fysiek object. Zou dit niet een controleput moeten zijn? (ROW 317)

- [ ] Pompunit: behoort deze niet in constructieonderdeel? Niet relevant voor NLCS (ROW 360)

- [ ] Rioolput met geleiding: onduidelijk wat hiermee wordt bedoeld (ROW 362)

- [ ] Verdiepte put: onduidelijk wat hiermee wordt bedoeld (ROW 365)

- [ ] Vacuümopslagtank: is dit een put, of een inrichtingselement zoals 'kast'? (ROW 369)

---

## Constructieonderdelen

- [ ] Is een afdekking een constructieonderdeel of zou dit een daadwerkelijk eigen object moeten zijn? (ROW 77)

- [ ] Drainputdeksel: vreemde definitie in GWSW, wordt ook voor slokops, overloopputten e.d. toegepast. Maakt het niet perse drainputdeksel. Ook lang niet alle drainputdeksels hebben een open bovenzijde (ROW 79)

- [ ] Flexibel zettingsstuk: is dit niet een hulpstuk i.p.v. constructieonderdeel? (ROW 111, mapping: `_HULPSTUK_ZETTINGSSTUK`)

- [ ] Waarom is een ontstoppingsstuk een hulpstuk en een controleput niet? (ROW 135)

- [ ] Zadel: wordt hiermee een zadelstuk bedoeld? (ROW 146)

- [ ] Rioolafsluiter: wordt hiermee een tijdelijke afsluiter bedoeld in de wand? (ROW 192)

- [ ] Slibvanger: hoort deze niet in het rijtje van vetvanger e.d. bij de aansluitputten? (ROW 195)

- [ ] Schildmuur: staat hier specifiek als constructieonderdeel in wand, echter heb je ook schildmuren in leidingen hiervoor is nu geen positie beschikbaar (ROW 212)

- [ ] Standpijp: is een hulpstuk van de inlaatconstructie, geen onderdeel van de aansluitleiding (ROW 239)

---

## Bouwwerken en kunstwerken

- [ ] Uitlaatconstructie vs. Inlaat oppervlaktewater: vreemd verschil, waarom de ene onder kunstwerk en de andere onder bouwwerk? (ROW 42)

- [ ] Een uitlaatvoorziening is niet per definitie een uitlaatconstructie, een open doorvoer in een damwand, waar hoort deze thuis? Lozingspunt is het enige topologisch object en geen fysiek object. (ROW 72)

---

## Goten en open leidingen

- [ ] Waarom is een roostergoot een subtype van lijngoot? (ROW 254)

- [ ] Infiltratiegoot: dit is geen eigen object, maar een subobject van een gespecificeerd model (lijngoot/roostergoot) (ROW 252)

- [ ] Taludgoot: definitie onduidelijk. Vrije uitstroom of een element? (ROW 256)

---

## Stelsels en drainage

- [ ] Drain: herschikken, zie overige drainage opmerkingen (ROW 240)

- [ ] Pendelstuk: bestaat dit als fysiek object, of is het een pendelconstructie samengesteld uit diverse elementen? (ROW 258)

- [ ] Drainage transportstelsel: onduidelijk verschil met 'Drainagestelsel' en 'Vrijverval drainagestelsel' (ROW 375)

- [ ] Vrijverval drainagestelsel: zelfde als 'Drainagestelsel'? Of specifieke verdieping, verplaatsen naar vrijverval rioolstelsel? (ROW 384)

- [ ] Drainage/infiltratie transportstelsel: dit lijkt de juiste positie voor 'Drainagestelsel -> drainage transportstelsel' of 'vrijverval drainagestelsel' (ROW 388)

---

## Apparatuur

- [ ] Wat is het verschil tussen de diverse soorten elektriciteitskast (besturingskast, buitenopstellingskast, centrale verdeelkast, centrale voedingskast)? Wat doe je bij een pompput bijvoorbeeld? (ROW 8-12)
