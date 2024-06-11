;;; ****************************************************************************************
;;; Naam routine: RTW.lsp
;;; Functie: Laad RTW menu
;;; Dienst: Bouwdienst
;;; Naam  : Jan Peter de Smidt 
;;; Datum : 11-02-2000
;;; Versie: 1.0
;;; wijzigingen tov versie ... :
;;; ****************************************************************************************
;;;  
;;;
;;; ****************************************************************************************
;;;
;;;
;;;
(if (/= nil (menucmd "GRTW.ID_RTW=?"))
  (command "menuunload" "RTW")
)

(if (and (/= nil (findfile "rtw.mnu"))
         (= nil (menucmd "GRTW.id_RTW=?"))
    )
  (progn

    (command "menuload" (findfile "rtw.mnu"))
    (menucmd "P20=+RTW.POP1")
  )
)

(princ)