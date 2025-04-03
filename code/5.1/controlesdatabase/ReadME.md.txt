Hier staan query's voor de beheerdwer van de NLCS database.


* Query om een lijst te maken van lijntypes die wel in de database voorkomen, maar géén link hebben met een object
* andersom, lijntype wordt genoemd bij het object maar bestaat niet
* Query om een lijst te maken van symbolen die wel in de database voorkomen, maar géén link hebben met een object
* Query om een lijst te maken van arceringen die wel in de database voorkomen, maar géén link hebben met een object

Bij de query voor de arceringen/symbolen zonder link met een object heb ik de aanname gedaan dat wanneer een arcering/symbool zelf geen relatie heeft maar zijn parent wel, dat dit voldoende is en deze arcering/symbool niet in de output genoemd hoeft te worden. Bijvoorbeeld 'SAL-AANKLEDING_AUTO1_ACHTERAANZICHT-D' heeft zelf geen directe relatie met een object, maar erft er wel een over vanuit zijn parent 'SAL-AANKLEDING'

Het toepassen van de queries is het snelst door eerst een publicatie te maken in het Laces schema (dus zonder stylesheet toe te voegen) en deze queries vervolgens te gebruiken op die publicatie. Als de queries direct in de Laces Apps omgeving worden toegepast om een export te genereren, zal de data per query eerst achter de schermen omgezet worden in Linked Data. Met 3 controle queries wordt dan dus eigenlijk 3x achter de schermen een publicatie gemaakt en voor de NLCS zal dit veel extra tijd kosten.