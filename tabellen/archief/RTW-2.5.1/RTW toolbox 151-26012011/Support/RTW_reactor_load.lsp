(defun c:RTW_load_reactor_off()
      (if (= (member "RTW_reactor_off.lsp" '(lsp)) nil)
         (progn
            (setq file (strcat #rtw_hfddir "\\support\\RTW_reactor_off.lsp"))
            (if (findfile file)
               (load file)
;;;;;          else
               (progn
                  (princ "\nFile <")(princ file)(princ "> niet gevonden.\n")
               );;endprogn
            );;endif
         );;endprogn
      );;endif
)
(defun c:RTW_load_reactor_on()
      (if (= (member "RTW_reactor_on.lsp" '(lsp)) nil)
         (progn
            (setq file (strcat #rtw_hfddir "\\support\\RTW_reactor_on.lsp"))
            (if (findfile file)
               (load file)
;;;;;          else
               (progn
                  (princ "\nFile <")(princ file)(princ "> niet gevonden.\n")
               );;endprogn
            );;endif
         );;endprogn
      );;endif
)