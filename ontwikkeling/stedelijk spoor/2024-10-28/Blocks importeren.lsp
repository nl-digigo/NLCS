(defun c:nlcsinsertblocks ( / dir lst i )
	(setvar "ATTREQ" 0)
	(setvar "CMDECHO" 0)
	(setq dir (LM:browseforfolder "Select a directory to list drawing files" nil 0))
	(setq lst (LM:directoryfiles dir "*.dwg" t))
	(setq i 0)
	(repeat (length lst)
		(command "-insert" (nth i lst) "S" "1" (list 0 (* i 5) 0) "")
		(setq i (+ 1 i))
	)
	(setvar "CMDECHO" 1)
)


;; Directory Files  -  Lee Mac
;; Retrieves all files of a specified filetype residing in a directory (and subdirectories)
;; dir - [str] Root directory for which to return filenames
;; typ - [str] Optional filetype filter (DOS pattern)
;; sub - [bol] If T, subdirectories of the root directory are included
;; Returns: [lst] List of files matching the filetype criteria, else nil if none are found

(defun LM:directoryfiles ( dir typ sub )
    (setq dir (vl-string-right-trim "\\" (vl-string-translate "/" "\\" dir)))
    (append (mapcar '(lambda ( x ) (strcat dir "\\" x)) (vl-directory-files dir typ 1))
        (if sub
            (apply 'append
                (mapcar
                   '(lambda ( x )
                        (if (not (wcmatch x "`.,`.`."))
                            (LM:directoryfiles (strcat dir "\\" x) typ sub)
                        )
                    )
                    (vl-directory-files dir nil -1)
                )
            )
        )
    )
)

(defun LM:browseforfolder ( msg dir bit / err fld pth shl slf )
    (setq err
        (vl-catch-all-apply
            (function
                (lambda ( / app hwd )
                    (if (setq app (vlax-get-acad-object)
                              shl (vla-getinterfaceobject app "shell.application")
                              hwd (vl-catch-all-apply 'vla-get-hwnd (list app))
                              fld (vlax-invoke-method shl 'browseforfolder (if (vl-catch-all-error-p hwd) 0 hwd) msg bit dir)
                        )
                        (setq slf (vlax-get-property fld 'self)
                              pth (vlax-get-property slf 'path)
                              pth (vl-string-right-trim "\\" (vl-string-translate "/" "\\" pth))
                        )
                    )
                )
            )
        )
    )
    (if slf (vlax-release-object slf))
    (if fld (vlax-release-object fld))
    (if shl (vlax-release-object shl))
    (if (vl-catch-all-error-p err)
        (prompt (vl-catch-all-error-message err))
        pth
    )
)

(princ)