(prompt " \nUnload RTW dimension reactors only....Do NOT Run...")
(vl-load-com)

;****************************************
(vlr-command-reactor 
	nil '((:vlr-commandEnded . endCommand)))
(vlr-command-reactor 
	nil '((:vlr-commandCancelled . cancelCommand)))
;******************************************************

;****************************************************

(defun endCommand (calling-reactor endcommandInfo / 
		   thecommandend)
(setq thecommandend (nth 0 endcommandInfo))
(cond
  ((= thecommandend "DIMALIGNED") (princ))
  ((= thecommandend "DIMLINEAR") (princ))
  ((= thecommandend "DIMANGULAR") (princ))
  ((= thecommandend "DIMBASLINE") (princ))
  ((= thecommandend "DIMCENTER") (princ))
  ((= thecommandend "DIMCONTINUE") (princ))
  ((= thecommandend "DIMDIAMETER") (princ))
  ((= thecommandend "DIMRADIUS") (princ))
  ((= thecommandend "DIMORDINATE") (princ))
  ((= thecommandend "LEADER") (princ))
  ((= thecommandend "BHATCH") (princ))
);cond
 (princ)
);defun
;********************************************************
(defun cancelCommand (calling-reactor cancelcommandInfo / 
		      thecommandcancel)
(setq thecommandcancel (nth 0 cancelcommandInfo))
(cond
  ((= thecommandcancel "DIMALIGNED") (princ))
  ((= thecommandcancel "DIMLINEAR") (princ))
  ((= thecommandcancel "DIMANGULAR") (princ))
  ((= thecommandcancel "DIMBASELINE") (princ))
  ((= thecommandcancel "DIMCENTER") (princ))
  ((= thecommandcancel "DIMCONTINUE") (princ))
  ((= thecommandcancel "DIMDIAMETER") (princ))
  ((= thecommandcancel "DIMRADIUS") (princ))
  ((= thecommandcancel "DIMORDINATE") (princ))
  ((= thecommandcancel "LEADER") (princ))
  ((= thecommandcancel "BHATCH") (princ))

);cond
(princ)
);defun
;*********************************************************
(princ) 