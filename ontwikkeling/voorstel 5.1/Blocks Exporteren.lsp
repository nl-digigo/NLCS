(defun C:MAAKBLOCKS ( / allblocks item blockname blocklist fn )
	(princ "\nBlocks verzamelen... ")
	(setvar "CMDDIA" 0)
	(setvar "CMDECHO" 0)
	(if (not allblocks)(setq allblocks (ssget "_X" (list (cons 0 "INSERT")(cons 410 "Model")))))
	(if allblocks
		(progn
			(princ "Done!\n")
			(command "_resetblock" allblocks "")

			(setq item (tblnext "BLOCK" T))
			(while (/= item nil)
				(setq blockname (cdr (assoc 2 item)))

				(if (not (wcmatch blockname "*[*]*,*[|]*,_*"))
					(setq blocklist (cons blockname blocklist))
				)

			(setq item (tblnext "BLOCK"))
			)

			(if blocklist
				(progn
					(setq blocklist (acad_strlsort blocklist))
					(foreach blk blocklist
						(setq fn (strcat "C:\\Users\\mht\\OneDrive - GP Groot B.V\\Bureaublad\\Definitief werkpakket NLCS 5.1 Vastgesteld EC\\" blk))
						(princ (strcat "\nZoeken naar: " blk "..." ))
						(if (not (ssget "_X" (list (cons 0 "INSERT")(cons 410 "Model")(cons 2 blk))))
							(progn
								(princ (strcat "Block: " blk " is niet aanwezig in tekening, overslaan..."))
							)
							(progn
								(princ "Block gevonden!")
								(if (findfile (strcat fn ".dwg"))
									(command "WBLOCK" fn "_Y" blk "N")
									(command "WBLOCK" fn blk "N")
								)
							)
						)
					)
				)
			)
			(command "_ZOOM" "E")
			(princ "\nDone!")
		)
		(progn
			(alert "De tekening bevat geen blocks...")
		)
	)
	(setvar "CMDDIA" 1)
	(setvar "CMDECHO" 1)
)

;;--------------------------------------------;;
;;--------------------------------------------;;

(princ)

;;--------------------------------------------;;
;;--------------------------------------------;;